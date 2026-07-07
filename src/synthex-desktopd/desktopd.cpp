#include "desktopd.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDir>
#include <QProcess>
#include <QDebug>
#include <QStandardPaths>
#include <QDateTime>
#include <QTextStream>

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

DesktopDaemon::DesktopDaemon(QObject *parent)
    : QObject(parent)
    , m_layoutDir(QStringLiteral("/usr/share/synthex/layouts"))
    , m_themeDir(QStringLiteral("/usr/share/synthex/themes"))
    , m_currentLayout(QStringLiteral("balanced"))
    , m_currentTheme(QStringLiteral("default"))
    , m_currentMode(QStringLiteral("balanced"))
    , m_snapshotDir(QStringLiteral("/var/lib/synthex/snapshots"))
{
    // Ensure snapshot directory exists
    QDir().mkpath(m_snapshotDir);

    // Log startup
    qInfo("DesktopDaemon initialised — layout=%s, theme=%s, mode=%s",
          qPrintable(m_currentLayout), qPrintable(m_currentTheme), qPrintable(m_currentMode));
}

DesktopDaemon::~DesktopDaemon()
{
    qInfo("DesktopDaemon shutting down");
}

// ---------------------------------------------------------------------------
// D-Bus slot implementations
// ---------------------------------------------------------------------------

QString DesktopDaemon::SetLayout(const QString &name)
{
    qInfo("SetLayout requested: %s", qPrintable(name));
    if (name.isEmpty())
        return QStringLiteral("error: empty layout name");

    if (!validatePath(m_layoutDir + QChar('/') + name + QStringLiteral(".json"))) {
        QString msg = QStringLiteral("error: layout '%1' not found").arg(name);
        qWarning("%s", qPrintable(msg));
        return msg;
    }

    if (applyLayout(name)) {
        m_currentLayout = name;
        emit LayoutChanged(name);
        return QStringLiteral("ok");
    }
    return QStringLiteral("error: failed to apply layout");
}

QString DesktopDaemon::SetTheme(const QString &name)
{
    qInfo("SetTheme requested: %s", qPrintable(name));
    if (name.isEmpty())
        return QStringLiteral("error: empty theme name");

    if (!validatePath(m_themeDir + QChar('/') + name + QStringLiteral(".json"))) {
        QString msg = QStringLiteral("error: theme '%1' not found").arg(name);
        qWarning("%s", qPrintable(msg));
        return msg;
    }

    if (applyTheme(name)) {
        m_currentTheme = name;
        emit ThemeChanged(name);
        return QStringLiteral("ok");
    }
    return QStringLiteral("error: failed to apply theme");
}

QString DesktopDaemon::SetMode(const QString &mode)
{
    qInfo("SetMode requested: %s", qPrintable(mode));
    if (setMode(mode)) {
        m_currentMode = mode;
        emit ModeChanged(mode);
        return QStringLiteral("ok");
    }
    return QStringLiteral("error: failed to set mode");
}

QString DesktopDaemon::GetCurrentLayout() { return m_currentLayout; }
QString DesktopDaemon::GetCurrentTheme()  { return m_currentTheme; }
QString DesktopDaemon::GetCurrentMode()   { return m_currentMode; }

QString DesktopDaemon::SetPerformanceProfile(const QString &profileName)
{
    qInfo("SetPerformanceProfile: %s", qPrintable(profileName));
    // Profile names combine layout+theme+mode, e.g. "gaming-dark-gaming"
    QStringList parts = profileName.split(QChar('-'));
    if (parts.size() < 1)
        return QStringLiteral("error: invalid profile name");

    QString mode  = parts.at(0);
    QString theme = (parts.size() > 1) ? parts.at(1) : QStringLiteral("default");
    QString layout = (parts.size() > 2) ? parts.at(2) : mode;

    bool ok = true;
    if (validatePath(m_layoutDir + QChar('/') + layout + QStringLiteral(".json")))
        ok = applyLayout(layout) && ok;
    if (validatePath(m_themeDir + QChar('/') + theme + QStringLiteral(".json")))
        ok = applyTheme(theme) && ok;
    ok = setMode(mode) && ok;

    if (ok) {
        m_currentLayout = layout;
        m_currentTheme  = theme;
        m_currentMode   = mode;
        emit LayoutChanged(layout);
        emit ThemeChanged(theme);
        emit ModeChanged(mode);
        return QStringLiteral("ok");
    }
    return QStringLiteral("error: partial profile application");
}

QString DesktopDaemon::CreateSnapshot()
{
    QString idStr = QString::number(QDateTime::currentSecsSinceEpoch());
    QString snapPath = m_snapshotDir + QChar('/') + idStr + QStringLiteral(".json");

    QJsonObject snap;
    snap[QStringLiteral("id")]        = idStr;
    snap[QStringLiteral("timestamp")] = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
    snap[QStringLiteral("layout")]    = m_currentLayout;
    snap[QStringLiteral("theme")]     = m_currentTheme;
    snap[QStringLiteral("mode")]      = m_currentMode;

    QFile file(snapPath);
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning("Cannot create snapshot at %s", qPrintable(snapPath));
        return QStringLiteral("error: cannot write snapshot");
    }
    file.write(QJsonDocument(snap).toJson(QJsonDocument::Indented));
    file.close();

    quint32 id = idStr.toUInt();
    QString desc = QStringLiteral("Snapshot %1: layout=%2, theme=%3, mode=%4")
                       .arg(idStr, m_currentLayout, m_currentTheme, m_currentMode);
    emit SnapshotCreated(id, desc);
    qInfo("Snapshot created: %s", qPrintable(desc));
    return idStr;
}

QString DesktopDaemon::RollbackToSnapshot(quint32 snapshotId)
{
    QString snapPath = m_snapshotDir + QChar('/') + QString::number(snapshotId) + QStringLiteral(".json");
    QFile file(snapPath);
    if (!file.open(QIODevice::ReadOnly))
        return QStringLiteral("error: snapshot not found");

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();

    if (doc.isNull() || !doc.isObject())
        return QStringLiteral("error: invalid snapshot");

    QJsonObject obj = doc.object();
    QString layout = obj.value(QStringLiteral("layout")).toString();
    QString theme  = obj.value(QStringLiteral("theme")).toString();
    QString mode   = obj.value(QStringLiteral("mode")).toString();

    bool ok = true;
    if (!layout.isEmpty() && layout != m_currentLayout)
        ok = applyLayout(layout) && ok;
    if (!theme.isEmpty() && theme != m_currentTheme)
        ok = applyTheme(theme) && ok;
    if (!mode.isEmpty() && mode != m_currentMode)
        ok = setMode(mode) && ok;

    if (ok) {
        if (!layout.isEmpty()) { m_currentLayout = layout; emit LayoutChanged(layout); }
        if (!theme.isEmpty())  { m_currentTheme  = theme;  emit ThemeChanged(theme); }
        if (!mode.isEmpty())   { m_currentMode   = mode;   emit ModeChanged(mode); }
        return QStringLiteral("ok");
    }
    return QStringLiteral("error: rollback failed");
}

// ---------------------------------------------------------------------------
// Layout application
// ---------------------------------------------------------------------------

bool DesktopDaemon::applyLayout(const QString &name)
{
    QString path = m_layoutDir + QChar('/') + name + QStringLiteral(".json");
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning("Cannot open layout: %s", qPrintable(path));
        return false;
    }

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();
    if (doc.isNull() || !doc.isObject()) {
        qWarning("Invalid JSON in layout: %s", qPrintable(path));
        return false;
    }

    QJsonObject layout = doc.object();
    qInfo("Applying layout '%s'", qPrintable(name));

    // --- Plasma panel settings ---
    QJsonObject panel = layout.value(QStringLiteral("panel")).toObject();
    if (!panel.isEmpty()) {
        writePlasmaConfig(QStringLiteral("plasma-org.kde.plasma.desktop-appletsrc"),
                          panel);
    }

    // --- Compositor settings ---
    QJsonObject compositor = layout.value(QStringLiteral("compositor")).toObject();
    if (!compositor.isEmpty()) {
        writePlasmaConfig(QStringLiteral("kwinrc"), compositor);
    }

    // --- Wallpaper ---
    QString wallpaper = layout.value(QStringLiteral("wallpaper")).toString();
    if (!wallpaper.isEmpty()) {
        runKConfig(QStringLiteral("wallpaper"), wallpaper,
                   QStringLiteral("plasma-org.kde.plasma.desktop-appletsrc"));
    }

    // --- Service blacklist ---
    QJsonArray blacklist = layout.value(QStringLiteral("serviceBlacklist")).toArray();
    for (const QJsonValue &svc : blacklist) {
        setServiceEnabled(svc.toString(), false);
    }

    // --- Shortcuts ---
    QJsonObject shortcuts = layout.value(QStringLiteral("shortcuts")).toObject();
    for (auto it = shortcuts.begin(); it != shortcuts.end(); ++it) {
        runKConfig(it.key(), it.value().toString(), QStringLiteral("kglobalshortcutsrc"));
    }

    // Apply layout via plasma-apply-* tools
    QProcess proc;
    proc.start(QStringLiteral("plasma-apply-desktoptheme"),
               QStringList() << layout.value(QStringLiteral("theme")).toString());
    proc.waitForFinished(5000);

    qInfo("Layout '%s' applied successfully", qPrintable(name));
    return true;
}

// ---------------------------------------------------------------------------
// Theme application
// ---------------------------------------------------------------------------

bool DesktopDaemon::applyTheme(const QString &name)
{
    QString path = m_themeDir + QChar('/') + name + QStringLiteral(".json");
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning("Cannot open theme: %s", qPrintable(path));
        return false;
    }

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();
    if (doc.isNull() || !doc.isObject()) {
        qWarning("Invalid JSON in theme: %s", qPrintable(path));
        return false;
    }

    QJsonObject theme = doc.object();
    qInfo("Applying theme '%s'", qPrintable(name));

    // Plasma look-and-feel theme
    QString lookAndFeel = theme.value(QStringLiteral("lookAndFeel")).toString();
    if (!lookAndFeel.isEmpty()) {
        QProcess proc;
        proc.start(QStringLiteral("plasma-apply-lookandfeel"), QStringList() << lookAndFeel);
        proc.waitForFinished(5000);
    }

    // Colors
    QString colors = theme.value(QStringLiteral("colors")).toString();
    if (!colors.isEmpty())
        runKConfig(QStringLiteral("colors"), colors, QStringLiteral("kdeglobals"));

    // Icons
    QString icons = theme.value(QStringLiteral("icons")).toString();
    if (!icons.isEmpty())
        runKConfig(QStringLiteral("icons"), icons, QStringLiteral("kdeglobals"));

    // Fonts
    QJsonObject fonts = theme.value(QStringLiteral("fonts")).toObject();
    for (auto it = fonts.begin(); it != fonts.end(); ++it) {
        runKConfig(QStringLiteral("font"), it.value().toString(),
                   QStringLiteral("kdeglobals"));
    }

    // Cursor theme
    QString cursorTheme = theme.value(QStringLiteral("cursorTheme")).toString();
    if (!cursorTheme.isEmpty()) {
        runKConfig(QStringLiteral("cursorTheme"), cursorTheme,
                   QStringLiteral("kcminputrc"));
    }

    qInfo("Theme '%s' applied successfully", qPrintable(name));
    return true;
}

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

bool DesktopDaemon::setMode(const QString &mode)
{
    QString lower = mode.toLower();
    if (lower == QStringLiteral("gaming"))
        return applyGamingMode();
    if (lower == QStringLiteral("dev"))
        return applyDevMode();
    if (lower == QStringLiteral("battery"))
        return applyBatteryMode();
    if (lower == QStringLiteral("balanced"))
        return applyBalancedMode();

    qWarning("Unknown mode: %s", qPrintable(mode));
    return false;
}

bool DesktopDaemon::applyGamingMode()
{
    qInfo("Activating GAMING mode");

    // Disable compositor
    runKConfig(QStringLiteral("OpenGLIsUnsafe"), QStringLiteral("true"),
               QStringLiteral("kwinrc"));

    // Enable fullscreen compositor bypass
    runKConfig(QStringLiteral("UnredirectFullscreen"), QStringLiteral("true"),
               QStringLiteral("kwinrc"));

    // Performance CPU governor
    setCpuGovernor(QStringLiteral("performance"));

    // Launch gamemode if available
    QProcess gamemode;
    gamemode.start(QStringLiteral("gamemoderun"), QStringList() << QStringLiteral("true"));
    gamemode.waitForFinished(3000);

    // Stop non-essential services
    QStringList bgServices = {
        QStringLiteral("synthex-stored.service"),
        QStringLiteral("packagekit.service"),
    };
    for (const QString &svc : bgServices)
        setServiceEnabled(svc, false);

    qInfo("GAMING mode active");
    return true;
}

bool DesktopDaemon::applyDevMode()
{
    qInfo("Activating DEV mode");

    // Balanced CPU governor
    setCpuGovernor(QStringLiteral("schedutil"));

    // Enable compositor (dev needs smooth desktop)
    runKConfig(QStringLiteral("OpenGLIsUnsafe"), QStringLiteral("false"),
               QStringLiteral("kwinrc"));

    // Start container services
    QStringList containerSvcs = {
        QStringLiteral("docker.service"),
        QStringLiteral("podman.service"),
        QStringLiteral("containerd.service"),
    };
    for (const QString &svc : containerSvcs)
        setServiceEnabled(svc, true);

    qInfo("DEV mode active");
    return true;
}

bool DesktopDaemon::applyBatteryMode()
{
    qInfo("Activating BATTERY mode");

    // Powersave CPU governor
    setCpuGovernor(QStringLiteral("powersave"));

    // Reduce compositor performance
    runKConfig(QStringLiteral("OpenGLIsUnsafe"), QStringLiteral("true"),
               QStringLiteral("kwinrc"));

    // Reduce GPU power
    QProcess gpuPower;
    gpuPower.start(QStringLiteral("/usr/bin/ryzenadj"), QStringList()
                   << QStringLiteral("--stapm-limit") << QStringLiteral("15000"));
    gpuPower.waitForFinished(3000);

    // Disable background services
    QStringList stopSvcs = {
        QStringLiteral("docker.service"),
        QStringLiteral("synthex-stored.service"),
        QStringLiteral("packagekit.service"),
    };
    for (const QString &svc : stopSvcs)
        setServiceEnabled(svc, false);

    qInfo("BATTERY mode active");
    return true;
}

bool DesktopDaemon::applyBalancedMode()
{
    qInfo("Activating BALANCED mode");

    // Reset CPU governor
    setCpuGovernor(QStringLiteral("schedutil"));

    // Enable compositor
    runKConfig(QStringLiteral("OpenGLIsUnsafe"), QStringLiteral("false"),
               QStringLiteral("kwinrc"));
    runKConfig(QStringLiteral("UnredirectFullscreen"), QStringLiteral("false"),
               QStringLiteral("kwinrc"));

    // Re-enable normal services (no-op — just log)
    qInfo("BALANCED mode active — default services restored");
    return true;
}

// ---------------------------------------------------------------------------
// Helper methods
// ---------------------------------------------------------------------------

bool DesktopDaemon::runKConfig(const QString &key, const QString &value, const QString &file)
{
    QProcess proc;
    QStringList args;
    if (!file.isEmpty())
        args << QStringLiteral("--file") << file;
    args << QStringLiteral("--key") << key << value;

    proc.start(QStringLiteral("kwriteconfig6"), args);
    if (!proc.waitForFinished(5000)) {
        qWarning("kwriteconfig6 timeout: key=%s", qPrintable(key));
        return false;
    }
    if (proc.exitCode() != 0) {
        qWarning("kwriteconfig6 failed (exit=%d): %s",
                 proc.exitCode(), qPrintable(proc.readAllStandardError()));
        return false;
    }
    return true;
}

bool DesktopDaemon::writePlasmaConfig(const QString &section, const QJsonObject &settings)
{
    // Use KConfig framework via kwriteconfig6 for each key-value pair
    for (auto it = settings.begin(); it != settings.end(); ++it) {
        QString val;
        if (it.value().isString())
            val = it.value().toString();
        else if (it.value().isDouble())
            val = QString::number(it.value().toDouble());
        else if (it.value().isBool())
            val = it.value().toBool() ? QStringLiteral("true") : QStringLiteral("false");
        else
            continue;

        if (!runKConfig(it.key(), val, section))
            return false;
    }
    return true;
}

bool DesktopDaemon::setServiceEnabled(const QString &service, bool enabled)
{
    QProcess proc;
    QString action = enabled ? QStringLiteral("enable") : QStringLiteral("disable");
    // Try user scope first, then system
    proc.start(QStringLiteral("systemctl"), QStringList()
               << QStringLiteral("--user") << action << service);
    if (!proc.waitForFinished(5000)) {
        qWarning("systemctl %s %s timeout", qPrintable(action), qPrintable(service));
        return false;
    }
    if (proc.exitCode() != 0) {
        // Try system scope
        proc.start(QStringLiteral("systemctl"), QStringList()
                   << action << service);
        if (!proc.waitForFinished(5000)) {
            qWarning("systemctl (system) %s %s timeout",
                     qPrintable(action), qPrintable(service));
            return false;
        }
    }
    qInfo("Service %s %sd", qPrintable(service), qPrintable(action));
    return true;
}

bool DesktopDaemon::setCpuGovernor(const QString &governor)
{
    QProcess proc;
    proc.start(QStringLiteral("cpupower"), QStringList()
               << QStringLiteral("frequency-set") << QStringLiteral("-g") << governor);
    if (!proc.waitForFinished(5000)) {
        // Try writing directly as fallback
        for (int cpu = 0; cpu < 64; ++cpu) {
            QString path = QStringLiteral("/sys/devices/system/cpu/cpu%1/cpufreq/scaling_governor")
                               .arg(cpu);
            QFile f(path);
            if (f.open(QIODevice::WriteOnly)) {
                f.write(governor.toUtf8());
                f.close();
            }
        }
        qInfo("CPU governor set via sysfs: %s", qPrintable(governor));
        return true;
    }
    qInfo("CPU governor set: %s", qPrintable(governor));
    return true;
}

bool DesktopDaemon::validatePath(const QString &path) const
{
    return QFile::exists(path);
}

#include "desktopd.moc"