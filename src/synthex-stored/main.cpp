/**
 * synthex-stored — Synthex Software Center Daemon
 *
 * D-Bus activated system service (org.synthex.SoftwareCenter).
 * Manages application installation across Flatpak, RPM/DNF, and WebApp backends.
 * systemd service type: dbus
 *
 * Licensed under GPL-2.0-or-later
 * Copyright (c) Synthex Project
 */

#include <QCoreApplication>
#include <QDebug>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusError>
#include <QDBusAbstractAdaptor>
#include <QTimer>
#include <QProcess>
#include <QStringList>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDir>
#include <QDateTime>
#include <QMutex>
#include <QMutexLocker>
#include <QThread>
#include <csignal>
#include <cstdlib>
#include <unistd.h>

// ---------------------------------------------------------------------------
// AppModel — unified representation across package backends
// ---------------------------------------------------------------------------

struct AppModel {
    QString id;           // Unique identifier
    QString name;         // Human-readable name
    QString summary;      // Short description
    QString version;      // Installed/available version
    QString backend;      // "flatpak", "rpm", "webapp"
    QString icon;         // Icon name or path
    bool installed = false;

    QJsonObject toJson() const {
        QJsonObject obj;
        obj["id"]        = id;
        obj["name"]      = name;
        obj["summary"]   = summary;
        obj["version"]   = version;
        obj["backend"]   = backend;
        obj["icon"]      = icon;
        obj["installed"] = installed;
        return obj;
    }
};

// ---------------------------------------------------------------------------
// Transaction guard — prevents concurrent install/remove operations
// ---------------------------------------------------------------------------

class TransactionGuard
{
public:
    bool tryLock() {
        QMutexLocker lock(&m_mutex);
        if (m_locked) return false;
        m_locked = true;
        return true;
    }

    void unlock() {
        QMutexLocker lock(&m_mutex);
        m_locked = false;
    }

    bool isLocked() const {
        QMutexLocker lock(&m_mutex);
        return m_locked;
    }

private:
    mutable QMutex m_mutex;
    bool m_locked = false;
};

// ---------------------------------------------------------------------------
// Snapshot manager — creates btrfs / LVM snapshots before system operations
// ---------------------------------------------------------------------------

class SnapshotManager
{
public:
    static QString createSnapshot(const QString &label)
    {
        QString ts = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
        QString snapId = QStringLiteral("synthex-stored-%1").arg(
            QDateTime::currentSecsSinceEpoch());

        qInfo("SnapshotManager: creating snapshot '%s' (%s)",
              qPrintable(snapId), qPrintable(label));

        // Try btrfs snapshot
        QProcess proc;
        proc.start(QStringLiteral("btrfs"), QStringList()
                   << QStringLiteral("subvolume")
                   << QStringLiteral("snapshot")
                   << QStringLiteral("/")
                   << QStringLiteral("/.snapshots/%1").arg(snapId));
        proc.waitForFinished(30000);

        if (proc.exitCode() == 0) {
            qInfo("SnapshotManager: btrfs snapshot '%s' created", qPrintable(snapId));
            return snapId;
        }

        // Try LVM snapshot fallback
        proc.start(QStringLiteral("lvcreate"), QStringList()
                   << QStringLiteral("--snapshot")
                   << QStringLiteral("--size") << QStringLiteral("10G")
                   << QStringLiteral("--name") << snapId
                   << QStringLiteral("synthex/root"));
        proc.waitForFinished(30000);

        if (proc.exitCode() == 0) {
            qInfo("SnapshotManager: LVM snapshot '%s' created", qPrintable(snapId));
            return snapId;
        }

        qWarning("SnapshotManager: no snapshot mechanism available — continuing without snapshot");
        return QString();
    }
};

// ---------------------------------------------------------------------------
// SoftwareCenter class — core logic
// ---------------------------------------------------------------------------

class SoftwareCenter : public QObject
{
    Q_OBJECT
public:
    explicit SoftwareCenter(QObject *parent = nullptr);
    ~SoftwareCenter() override;

    // D-Bus method implementations
    QString SearchApp(const QString &query);
    QString InstallApp(const QString &appId);
    QString RemoveApp(const QString &appId);
    QString GetAppInfo(const QString &appId);
    QString InstallFlatpak(const QString &flatpakRef);
    QString InstallRPM(const QString &packageName);
    QString InstallWebApp(const QString &url, const QString &name);
    QString GetUpdates();
    QString InstallUpdates();
    QString GetCategories();

signals:
    void InstallProgress(const QString &appId, int percent, const QString &status);
    void InstallComplete(const QString &appId, bool success, const QString &message);
    void UpdatesAvailable(uint count);
    void TransactionLockChanged(bool locked);

private:
    // Backend helpers
    QJsonArray searchFlatpak(const QString &query);
    QJsonArray searchRPM(const QString &query);
    bool runFlatpakInstall(const QString &ref);
    bool runRPMInstall(const QString &pkg);
    bool runRPMRemove(const QString &pkg);
    QJsonObject getRpmInfo(const QString &pkg);
    QJsonObject getFlatpakInfo(const QString &ref);

    // Transaction safety
    TransactionGuard m_txGuard;
};

// ---------------------------------------------------------------------------
// SoftwareCenter implementation
// ---------------------------------------------------------------------------

SoftwareCenter::SoftwareCenter(QObject *parent)
    : QObject(parent)
{
    qInfo("SoftwareCenter initialised");
}

SoftwareCenter::~SoftwareCenter()
{
    qInfo("SoftwareCenter shutting down");
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

QString SoftwareCenter::SearchApp(const QString &query)
{
    qInfo("SearchApp: query='%s'", qPrintable(query));

    QJsonArray results;

    // Search Flatpak
    QJsonArray fpResults = searchFlatpak(query);
    for (const QJsonValue &v : fpResults)
        results.append(v);

    // Search RPM
    QJsonArray rpmResults = searchRPM(query);
    for (const QJsonValue &v : rpmResults)
        results.append(v);

    QJsonDocument doc(results);
    return QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
}

QJsonArray SoftwareCenter::searchFlatpak(const QString &query)
{
    QJsonArray results;

    QProcess proc;
    proc.start(QStringLiteral("flatpak"), QStringList()
               << QStringLiteral("search")
               << QStringLiteral("--columns=application,name,summary,version")
               << query);
    if (!proc.waitForFinished(30000) || proc.exitCode() != 0)
        return results;

    QByteArray output = proc.readAllStandardOutput();
    QList<QByteArray> lines = output.split('\n');
    bool first = true;

    for (const QByteArray &line : lines) {
        if (first) { first = false; continue; } // skip header
        if (line.trimmed().isEmpty()) continue;

        QList<QByteArray> cols = line.split('\t');
        if (cols.size() < 3) continue;

        AppModel app;
        app.id      = QString::fromUtf8(cols[0].trimmed());
        app.name    = QString::fromUtf8(cols[1].trimmed());
        app.summary = QString::fromUtf8(cols[2].trimmed());
        app.backend = QStringLiteral("flatpak");
        if (cols.size() >= 4)
            app.version = QString::fromUtf8(cols[3].trimmed());

        results.append(app.toJson());
    }

    return results;
}

QJsonArray SoftwareCenter::searchRPM(const QString &query)
{
    QJsonArray results;

    QProcess proc;
    proc.start(QStringLiteral("dnf"), QStringList()
               << QStringLiteral("repoquery")
               << QStringLiteral("--qf=%{name}\t%{summary}\t%{version}")
               << QStringLiteral("--all")
               << QStringLiteral("*%1*").arg(query));
    if (!proc.waitForFinished(60000) || proc.exitCode() != 0) {
        // Try rpm fallback
        proc.start(QStringLiteral("rpm"), QStringList()
                   << QStringLiteral("-qa")
                   << QStringLiteral("--qf=%{NAME}\t%{SUMMARY}\t%{VERSION}\n")
                   << QStringLiteral("*%1*").arg(query));
        if (!proc.waitForFinished(30000))
            return results;
    }

    QByteArray output = proc.readAllStandardOutput();
    QList<QByteArray> lines = output.split('\n');

    for (const QByteArray &line : lines) {
        if (line.trimmed().isEmpty()) continue;

        QList<QByteArray> cols = line.split('\t');
        if (cols.size() < 1) continue;

        AppModel app;
        app.id      = QString::fromUtf8(cols[0].trimmed());
        app.name    = app.id;
        app.summary = (cols.size() >= 2) ? QString::fromUtf8(cols[1].trimmed()) : QString();
        app.version = (cols.size() >= 3) ? QString::fromUtf8(cols[2].trimmed()) : QString();
        app.backend = QStringLiteral("rpm");
        app.installed = true; // rpm -qa only returns installed

        results.append(app.toJson());
    }

    return results;
}

// ---------------------------------------------------------------------------
// Install/Remove
// ---------------------------------------------------------------------------

QString SoftwareCenter::InstallApp(const QString &appId)
{
    qInfo("InstallApp: %s", qPrintable(appId));

    if (!m_txGuard.tryLock()) {
        emit TransactionLockChanged(true);
        return QStringLiteral("error: another transaction is in progress");
    }

    emit TransactionLockChanged(true);
    QString result;

    // Determine backend from appId prefix
    if (appId.startsWith(QStringLiteral("app/"))) {
        result = InstallFlatpak(appId);
    } else {
        result = InstallRPM(appId);
    }

    m_txGuard.unlock();
    emit TransactionLockChanged(false);
    return result;
}

QString SoftwareCenter::RemoveApp(const QString &appId)
{
    qInfo("RemoveApp: %s", qPrintable(appId));

    if (!m_txGuard.tryLock()) {
        return QStringLiteral("error: another transaction is in progress");
    }

    emit TransactionLockChanged(true);
    QString result;

    // Create snapshot before removal
    SnapshotManager::createSnapshot(QStringLiteral("remove-%1").arg(appId));

    if (appId.startsWith(QStringLiteral("app/"))) {
        QProcess proc;
        proc.start(QStringLiteral("flatpak"), QStringList()
                   << QStringLiteral("uninstall") << QStringLiteral("-y") << appId);
        proc.waitForFinished(120000);
        result = (proc.exitCode() == 0)
            ? QStringLiteral("ok")
            : QStringLiteral("error: %1").arg(QString::fromUtf8(proc.readAllStandardError()).trimmed());
    } else {
        result = runRPMRemove(appId)
            ? QStringLiteral("ok")
            : QStringLiteral("error: removal failed");
    }

    emit InstallComplete(appId, result == QStringLiteral("ok"), result);
    m_txGuard.unlock();
    emit TransactionLockChanged(false);
    return result;
}

// ---------------------------------------------------------------------------
// GetAppInfo
// ---------------------------------------------------------------------------

QString SoftwareCenter::GetAppInfo(const QString &appId)
{
    QJsonObject info;

    if (appId.startsWith(QStringLiteral("app/"))) {
        info = getFlatpakInfo(appId);
    } else {
        info = getRpmInfo(appId);
    }

    info["id"] = appId;
    QJsonDocument doc(info);
    return QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
}

QJsonObject SoftwareCenter::getRpmInfo(const QString &pkg)
{
    QJsonObject info;
    QProcess proc;
    proc.start(QStringLiteral("rpm"), QStringList()
               << QStringLiteral("-qi") << pkg);
    if (!proc.waitForFinished(10000))
        return info;

    QByteArray output = proc.readAllStandardOutput();
    for (const QByteArray &line : output.split('\n')) {
        if (line.contains(':')) {
            int colon = line.indexOf(':');
            QString key = QString::fromUtf8(line.left(colon)).trimmed();
            QString val = QString::fromUtf8(line.mid(colon + 1)).trimmed();
            info[key.toLower()] = val;
        }
    }

    info["backend"]   = QStringLiteral("rpm");
    info["installed"] = (proc.exitCode() == 0);
    return info;
}

QJsonObject SoftwareCenter::getFlatpakInfo(const QString &ref)
{
    QJsonObject info;
    QProcess proc;
    proc.start(QStringLiteral("flatpak"), QStringList()
               << QStringLiteral("info") << ref);
    if (!proc.waitForFinished(15000))
        return info;

    QByteArray output = proc.readAllStandardOutput();
    QStringList lines = QString::fromUtf8(output).split('\n');
    for (const QString &line : lines) {
        if (line.contains(':')) {
            int colon = line.indexOf(':');
            QString key = line.left(colon).trimmed();
            QString val = line.mid(colon + 1).trimmed();
            info[key.toLower()] = val;
        }
    }

    info["backend"]   = QStringLiteral("flatpak");
    info["installed"] = true;
    return info;
}

// ---------------------------------------------------------------------------
// Backend-specific installers
// ---------------------------------------------------------------------------

QString SoftwareCenter::InstallFlatpak(const QString &flatpakRef)
{
    qInfo("InstallFlatpak: %s", qPrintable(flatpakRef));
    emit InstallProgress(flatpakRef, 0, QStringLiteral("starting"));

    SnapshotManager::createSnapshot(QStringLiteral("flatpak-install-%1").arg(flatpakRef));

    if (runFlatpakInstall(flatpakRef)) {
        emit InstallProgress(flatpakRef, 100, QStringLiteral("complete"));
        emit InstallComplete(flatpakRef, true, QStringLiteral("installed successfully"));
        return QStringLiteral("ok");
    }

    emit InstallComplete(flatpakRef, false, QStringLiteral("installation failed"));
    return QStringLiteral("error: flatpak install failed");
}

QString SoftwareCenter::InstallRPM(const QString &packageName)
{
    qInfo("InstallRPM: %s", qPrintable(packageName));
    emit InstallProgress(packageName, 0, QStringLiteral("starting"));

    SnapshotManager::createSnapshot(QStringLiteral("rpm-install-%1").arg(packageName));

    if (runRPMInstall(packageName)) {
        emit InstallProgress(packageName, 100, QStringLiteral("complete"));
        emit InstallComplete(packageName, true, QStringLiteral("installed successfully"));
        return QStringLiteral("ok");
    }

    emit InstallComplete(packageName, false, QStringLiteral("installation failed"));
    return QStringLiteral("error: rpm install failed");
}

QString SoftwareCenter::InstallWebApp(const QString &url, const QString &name)
{
    qInfo("InstallWebApp: name='%s' url='%s'", qPrintable(name), qPrintable(url));

    // Create a .desktop file for the web app using a browser
    QString desktopPath = QStringLiteral("/usr/share/applications/synthex-web-%1.desktop")
                              .arg(name.toLower().replace(QChar(' '), QChar('-')));

    QFile file(desktopPath);
    if (!file.open(QIODevice::WriteOnly)) {
        return QStringLiteral("error: cannot create desktop entry");
    }

    QByteArray content;
    content.append("[Desktop Entry]\n");
    content.append("Type=Application\n");
    content.append(QStringLiteral("Name=%1\n").arg(name).toUtf8());
    content.append(QStringLiteral("Exec=xdg-open %1\n").arg(url).toUtf8());
    content.append("Terminal=false\n");
    content.append("Categories=Network;WebBrowser;\n");
    content.append("Icon=web-browser\n");
    file.write(content);
    file.close();

    qInfo("WebApp '%s' installed at %s", qPrintable(name), qPrintable(desktopPath));
    return QStringLiteral("ok");
}

// ---------------------------------------------------------------------------
// Updates
// ---------------------------------------------------------------------------

QString SoftwareCenter::GetUpdates()
{
    QJsonArray updates;

    // Check Flatpak updates
    QProcess fpProc;
    fpProc.start(QStringLiteral("flatpak"), QStringList()
                 << QStringLiteral("remote-ls") << QStringLiteral("--updates")
                 << QStringLiteral("--columns=application,name,version"));
    if (fpProc.waitForFinished(30000)) {
        QList<QByteArray> lines = fpProc.readAllStandardOutput().split('\n');
        bool first = true;
        for (const QByteArray &line : lines) {
            if (first) { first = false; continue; }
            if (line.trimmed().isEmpty()) continue;
            updates.append(QString::fromUtf8(line.trimmed()));
        }
    }

    // Check DNF updates
    QProcess dnfProc;
    dnfProc.start(QStringLiteral("dnf"), QStringList()
                  << QStringLiteral("check-update")
                  << QStringLiteral("--quiet"));
    if (dnfProc.waitForFinished(60000)) {
        QList<QByteArray> lines = dnfProc.readAllStandardOutput().split('\n');
        for (const QByteArray &line : lines) {
            if (line.trimmed().isEmpty()) continue;
            updates.append(QString::fromUtf8(line.trimmed()));
        }
    }

    uint count = (uint)updates.size();
    if (count > 0)
        emit UpdatesAvailable(count);

    QJsonDocument doc(updates);
    return QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
}

QString SoftwareCenter::InstallUpdates()
{
    qInfo("InstallUpdates");

    if (!m_txGuard.tryLock())
        return QStringLiteral("error: transaction in progress");

    emit TransactionLockChanged(true);
    SnapshotManager::createSnapshot(QStringLiteral("pre-update"));

    // Flatpak updates
    QProcess fpProc;
    fpProc.start(QStringLiteral("flatpak"), QStringList()
                 << QStringLiteral("update") << QStringLiteral("-y"));
    fpProc.waitForFinished(300000);

    // DNF updates
    QProcess dnfProc;
    dnfProc.start(QStringLiteral("dnf"), QStringList()
                  << QStringLiteral("upgrade") << QStringLiteral("-y"));
    dnfProc.waitForFinished(300000);

    m_txGuard.unlock();
    emit TransactionLockChanged(false);

    return QStringLiteral("ok");
}

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------

QString SoftwareCenter::GetCategories()
{
    QJsonArray categories;
    categories << QStringLiteral("AudioVideo")
               << QStringLiteral("Development")
               << QStringLiteral("Education")
               << QStringLiteral("Game")
               << QStringLiteral("Graphics")
               << QStringLiteral("Network")
               << QStringLiteral("Office")
               << QStringLiteral("Science")
               << QStringLiteral("Settings")
               << QStringLiteral("System")
               << QStringLiteral("Utility");

    QJsonDocument doc(categories);
    return QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
}

// ---------------------------------------------------------------------------
// Backend helpers
// ---------------------------------------------------------------------------

bool SoftwareCenter::runFlatpakInstall(const QString &ref)
{
    QProcess proc;
    proc.start(QStringLiteral("flatpak"), QStringList()
               << QStringLiteral("install") << QStringLiteral("-y")
               << QStringLiteral("--noninteractive")
               << ref);
    proc.waitForFinished(300000);
    return (proc.exitCode() == 0);
}

bool SoftwareCenter::runRPMInstall(const QString &pkg)
{
    QProcess proc;
    proc.start(QStringLiteral("dnf"), QStringList()
               << QStringLiteral("install") << QStringLiteral("-y") << pkg);
    proc.waitForFinished(300000);
    return (proc.exitCode() == 0);
}

bool SoftwareCenter::runRPMRemove(const QString &pkg)
{
    QProcess proc;
    proc.start(QStringLiteral("dnf"), QStringList()
               << QStringLiteral("remove") << QStringLiteral("-y") << pkg);
    proc.waitForFinished(120000);
    return (proc.exitCode() == 0);
}

// ---------------------------------------------------------------------------
// D-Bus adaptor
// ---------------------------------------------------------------------------

class SoftwareCenterAdaptor : public QDBusAbstractAdaptor
{
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.synthex.SoftwareCenter")

public:
    explicit SoftwareCenterAdaptor(SoftwareCenter *sc)
        : QDBusAbstractAdaptor(sc)
        , m_sc(sc)
    {
        setAutoRelaySignals(true);

        QObject::connect(m_sc, &SoftwareCenter::InstallProgress,
                         this, &SoftwareCenterAdaptor::InstallProgress);
        QObject::connect(m_sc, &SoftwareCenter::InstallComplete,
                         this, &SoftwareCenterAdaptor::InstallComplete);
        QObject::connect(m_sc, &SoftwareCenter::UpdatesAvailable,
                         this, &SoftwareCenterAdaptor::UpdatesAvailable);
        QObject::connect(m_sc, &SoftwareCenter::TransactionLockChanged,
                         this, &SoftwareCenterAdaptor::TransactionLockChanged);
    }

public slots:
    QString SearchApp(const QString &query) { return m_sc->SearchApp(query); }
    QString InstallApp(const QString &appId) { return m_sc->InstallApp(appId); }
    QString RemoveApp(const QString &appId) { return m_sc->RemoveApp(appId); }
    QString GetAppInfo(const QString &appId) { return m_sc->GetAppInfo(appId); }
    QString InstallFlatpak(const QString &ref) { return m_sc->InstallFlatpak(ref); }
    QString InstallRPM(const QString &pkg) { return m_sc->InstallRPM(pkg); }
    QString InstallWebApp(const QString &url, const QString &name) { return m_sc->InstallWebApp(url, name); }
    QString GetUpdates() { return m_sc->GetUpdates(); }
    QString InstallUpdates() { return m_sc->InstallUpdates(); }
    QString GetCategories() { return m_sc->GetCategories(); }

signals:
    void InstallProgress(const QString &appId, int percent, const QString &status);
    void InstallComplete(const QString &appId, bool success, const QString &message);
    void UpdatesAvailable(uint count);
    void TransactionLockChanged(bool locked);

private:
    SoftwareCenter *m_sc;
};

// ---------------------------------------------------------------------------
// Signal handlers
// ---------------------------------------------------------------------------

static QCoreApplication *g_app = nullptr;

static void signalHandler(int sig)
{
    const char *name = nullptr;
    switch (sig) {
    case SIGTERM: name = "SIGTERM"; break;
    case SIGINT:  name = "SIGINT"; break;
    default:      name = "unknown"; break;
    }
    qInfo("Received %s — shutting down", name);
    if (g_app)
        QTimer::singleShot(0, g_app, &QCoreApplication::quit);
}

static void setupSignals()
{
    struct sigaction sa;
    sa.sa_handler = signalHandler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    sigaction(SIGTERM, &sa, nullptr);
    sigaction(SIGINT, &sa, nullptr);
    signal(SIGPIPE, SIG_IGN);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("synthex-stored"));
    app.setOrganizationName(QStringLiteral("Synthex"));
    app.setApplicationVersion(QStringLiteral("1.0.0"));

    g_app = &app;
    setupSignals();

    SoftwareCenter sc;
    SoftwareCenterAdaptor adaptor(&sc);

    QDBusConnection bus = QDBusConnection::sessionBus();
    if (!bus.isConnected()) {
        qCritical("Cannot connect to session D-Bus");
        return EXIT_FAILURE;
    }

    const QString serviceName = QStringLiteral("org.synthex.SoftwareCenter");
    if (!bus.registerService(serviceName)) {
        qCritical("Failed to register service '%s': %s",
                  qPrintable(serviceName),
                  qPrintable(bus.lastError().message()));
        return EXIT_FAILURE;
    }

    const QString objPath = QStringLiteral("/org/synthex/SoftwareCenter");
    if (!bus.registerObject(objPath, &sc)) {
        qCritical("Failed to register object at '%s'", qPrintable(objPath));
        return EXIT_FAILURE;
    }

    qInfo("synthex-stored started — service '%s' on '%s'",
          qPrintable(serviceName), qPrintable(objPath));

    int ret = app.exec();

    bus.unregisterObject(objPath);
    bus.unregisterService(serviceName);
    qInfo("synthex-stored shut down (exit %d)", ret);
    return ret;
}

#include "main.moc"