/**
 * synthex-desktopd — Synthex Desktop Customization Daemon
 *
 * D-Bus activated system service (org.synthex.Desktop).
 * Provides SetLayout, SetTheme, SetMode methods for desktop customisation.
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
#include <QDBusInterface>
#include <QDBusAdaptor>
#include <QTimer>
#include <QStringList>
#include <csignal>
#include <cstdlib>
#include <unistd.h>

#include "desktopd.h"

// ---------------------------------------------------------------------------
// D-Bus adaptor — auto-generated from introspection XML
// ---------------------------------------------------------------------------

/**
 * @brief Adaptor class that marshals D-Bus method calls to DesktopDaemon slots.
 *
 * Generated pattern from org.synthex.Desktop.xml interface definition.
 * Maps D-Bus method names to DesktopDaemon C++ methods.
 */
class DesktopAdaptor : public QDBusAbstractAdaptor
{
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.synthex.Desktop")
    Q_CLASSINFO("D-Bus Introspection", "")

    Q_PROPERTY(QString currentLayout READ currentLayout NOTIFY LayoutChanged)
    Q_PROPERTY(QString currentTheme READ currentTheme NOTIFY ThemeChanged)
    Q_PROPERTY(QString currentMode READ currentMode NOTIFY ModeChanged)

public:
    explicit DesktopAdaptor(DesktopDaemon *daemon)
        : QDBusAbstractAdaptor(daemon)
        , m_daemon(daemon)
    {
        setAutoRelaySignals(true);
        connectSignals();
    }

    // ---- D-Bus methods ----
public slots:

    /** Set desktop layout by name */
    QString SetLayout(const QString &name)
    {
        return m_daemon->SetLayout(name);
    }

    /** Apply theme by name */
    QString SetTheme(const QString &name)
    {
        return m_daemon->SetTheme(name);
    }

    /** Switch performance profile (gaming / dev / battery / balanced) */
    QString SetMode(const QString &mode)
    {
        return m_daemon->SetMode(mode);
    }

    /** Return the current layout name */
    QString GetCurrentLayout()
    {
        return m_daemon->GetCurrentLayout();
    }

    /** Return the current mode string */
    QString GetCurrentMode()
    {
        return m_daemon->GetCurrentMode();
    }

    /** Return the current theme name */
    QString GetCurrentTheme()
    {
        return m_daemon->GetCurrentTheme();
    }

    /** Apply a full performance profile (layout-theme-mode) */
    QString SetPerformanceProfile(const QString &profileName)
    {
        return m_daemon->SetPerformanceProfile(profileName);
    }

    /** Snapshot the current desktop state, return snapshot ID */
    QString CreateSnapshot()
    {
        return m_daemon->CreateSnapshot();
    }

    /** Roll back to a previous snapshot by ID */
    QString RollbackToSnapshot(quint32 snapshotId)
    {
        return m_daemon->RollbackToSnapshot(snapshotId);
    }

signals:
    /** Emitted when performance mode changes */
    void ModeChanged(const QString &mode);

    /** Emitted when desktop layout changes */
    void LayoutChanged(const QString &layout);

    /** Emitted when theme changes */
    void ThemeChanged(const QString &theme);

    /** Emitted when a snapshot is created */
    void SnapshotCreated(quint32 id, const QString &description);

private:
    void connectSignals()
    {
        QObject::connect(m_daemon, &DesktopDaemon::ModeChanged,
                         this, &DesktopAdaptor::ModeChanged);
        QObject::connect(m_daemon, &DesktopDaemon::LayoutChanged,
                         this, &DesktopAdaptor::LayoutChanged);
        QObject::connect(m_daemon, &DesktopDaemon::ThemeChanged,
                         this, &DesktopAdaptor::ThemeChanged);
        QObject::connect(m_daemon, &DesktopDaemon::SnapshotCreated,
                         this, &DesktopAdaptor::SnapshotCreated);
    }

    DesktopDaemon *m_daemon;
};

// ---------------------------------------------------------------------------
// Signal handler for graceful shutdown
// ---------------------------------------------------------------------------

static QCoreApplication *g_app = nullptr;

static void signalHandler(int sig)
{
    const char *sigName = nullptr;
    switch (sig) {
    case SIGTERM: sigName = "SIGTERM"; break;
    case SIGINT:  sigName = "SIGINT";  break;
    case SIGHUP:  sigName = "SIGHUP";  break;
    default:      sigName = "unknown"; break;
    }

    qInfo("Received signal %s (%d) — initiating graceful shutdown", sigName, sig);

    if (g_app) {
        // Allow 3 seconds for clean shutdown
        QTimer::singleShot(0, g_app, [sig]() {
            qInfo("Shutdown complete after signal %d", sig);
            g_app->quit();
        });
    }
}

static void setupSignalHandlers()
{
    struct sigaction sa;
    sa.sa_handler = signalHandler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;

    sigaction(SIGTERM, &sa, nullptr);
    sigaction(SIGINT,  &sa, nullptr);
    sigaction(SIGHUP,  &sa, nullptr);

    // Ignore SIGPIPE
    signal(SIGPIPE, SIG_IGN);
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("synthex-desktopd"));
    app.setOrganizationName(QStringLiteral("Synthex"));
    app.setApplicationVersion(QStringLiteral("1.0.0"));

    g_app = &app;
    setupSignalHandlers();

    // --- Create the daemon core ---
    DesktopDaemon daemon;

    // --- Register D-Bus adaptor ---
    DesktopAdaptor adaptor(&daemon);

    // --- Connect to session bus ---
    QDBusConnection bus = QDBusConnection::sessionBus();
    if (!bus.isConnected()) {
        qCritical("Cannot connect to D-Bus session bus — is dbus-daemon running?");
        return EXIT_FAILURE;
    }

    // --- Register service name ---
    const QString serviceName = QStringLiteral("org.synthex.Desktop");
    if (!bus.registerService(serviceName)) {
        qCritical("Failed to register D-Bus service '%s': %s",
                  qPrintable(serviceName),
                  qPrintable(bus.lastError().message()));
        return EXIT_FAILURE;
    }

    // --- Register object path ---
    const QString objectPath = QStringLiteral("/org/synthex/Desktop");
    if (!bus.registerObject(objectPath, &daemon)) {
        qCritical("Failed to register D-Bus object at '%s': %s",
                  qPrintable(objectPath),
                  qPrintable(bus.lastError().message()));
        return EXIT_FAILURE;
    }

    qInfo("synthex-desktopd started — D-Bus service '%s' on '%s'",
          qPrintable(serviceName), qPrintable(objectPath));

    // --- Enter event loop ---
    int ret = app.exec();

    // --- Cleanup ---
    bus.unregisterObject(objectPath);
    bus.unregisterService(serviceName);

    qInfo("synthex-desktopd shut down (exit code %d)", ret);
    return ret;
}

#include "main.moc"