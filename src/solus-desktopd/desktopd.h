#ifndef SOLUS_DESKTOPD_H
#define SOLUS_DESKTOPD_H

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QProcess>
#include <QFile>
#include <QDir>
#include <QTimer>
#include <QDebug>
#include <QJsonDocument>
#include <QJsonArray>

/**
 * @brief DesktopDaemon — core D-Bus service for Solus desktop customization.
 *
 * Listens for SetLayout, SetTheme, SetMode calls via D-Bus and applies
 * KDE Plasma configuration changes, system performance tuning, and
 * service management.
 */
class DesktopDaemon : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString currentLayout READ currentLayout NOTIFY LayoutChanged)
    Q_PROPERTY(QString currentTheme READ currentTheme NOTIFY ThemeChanged)
    Q_PROPERTY(QString currentMode READ currentMode NOTIFY ModeChanged)

public:
    explicit DesktopDaemon(QObject *parent = nullptr);
    ~DesktopDaemon() override;

    QString currentLayout() const { return m_currentLayout; }
    QString currentTheme()  const { return m_currentTheme; }
    QString currentMode()   const { return m_currentMode; }

public slots:
    /** D-Bus: Set desktop layout by name (gaming, minimal, macos, windows, dev, balanced) */
    QString SetLayout(const QString &name);

    /** D-Bus: Apply theme by name */
    QString SetTheme(const QString &name);

    /** D-Bus: Switch performance profile (gaming, dev, battery, balanced) */
    QString SetMode(const QString &mode);

    /** D-Bus: Get current layout name */
    QString GetCurrentLayout();

    /** D-Bus: Get current theme name */
    QString GetCurrentTheme();

    /** D-Bus: Get current mode string */
    QString GetCurrentMode();

    /** D-Bus: Set a full performance profile (combines layout + theme + mode) */
    QString SetPerformanceProfile(const QString &profileName);

    /** D-Bus: Create a snapshot of current desktop state */
    QString CreateSnapshot();

    /** D-Bus: Rollback to a snapshot by index */
    QString RollbackToSnapshot(quint32 snapshotId);

signals:
    /** Emitted when the desktop mode changes */
    void ModeChanged(const QString &mode);

    /** Emitted when the layout changes */
    void LayoutChanged(const QString &layout);

    /** Emitted when the theme changes */
    void ThemeChanged(const QString &theme);

    /** Emitted after a snapshot is created */
    void SnapshotCreated(quint32 id, const QString &description);

private slots:
    /** Apply a layout JSON definition */
    bool applyLayout(const QString &name);

    /** Apply a theme JSON definition */
    bool applyTheme(const QString &name);

    /** Switch system performance mode */
    bool setMode(const QString &mode);

    /** Gaming-optimised mode: compositor off, performance governor, gamemode */
    bool applyGamingMode();

    /** Development mode: containers, balanced governor */
    bool applyDevMode();

    /** Battery-saver mode: powersave governor, GPU throttling */
    bool applyBatteryMode();

    /** Balanced/default mode: restore defaults */
    bool applyBalancedMode();

private:
    /** Run a KConfig tool command */
    bool runKConfig(const QString &key, const QString &value, const QString &file = QString());

    /** Write a Plasma config file */
    bool writePlasmaConfig(const QString &section, const QJsonObject &settings);

    /** Enable/disable a systemd user service */
    bool setServiceEnabled(const QString &service, bool enabled);

    /** Set CPU governor via cpupower */
    bool setCpuGovernor(const QString &governor);

    /** Check if a file exists and is readable */
    bool validatePath(const QString &path) const;

    /** Path to layout definitions */
    QString m_layoutDir;

    /** Path to theme definitions */
    QString m_themeDir;

    /** Current active layout name */
    QString m_currentLayout;

    /** Current active theme name */
    QString m_currentTheme;

    /** Current performance mode */
    QString m_currentMode;

    /** Snapshots directory */
    QString m_snapshotDir;
};

#endif // SOLUS_DESKTOPD_H