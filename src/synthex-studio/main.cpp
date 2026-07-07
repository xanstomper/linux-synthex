// Synthex Studio CD — C++ D-Bus daemon for theme and layout management
// Applies themes, layout presets, and rice configurations to the desktop
// Communicates with synthex-desktopd for KDE Plasma integration

#include <QCoreApplication>
#include <QDBusConnection>
#include <QDBusAdaptor>
#include <QDBusInterface>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QDir>
#include <QProcess>
#include <QDebug>
#include <QTimer>
#include <signal.h>

class StudioDaemon : public QObject {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.synthex.Studio")

public:
    explicit StudioDaemon(QObject *parent = nullptr) : QObject(parent) {
        m_themesDir = "/usr/share/synthex/themes";
        m_layoutsDir = "/usr/share/synthex/layouts";
        m_presetsDir = "/usr/share/synthex/studio/presets";
        m_userConfigDir = QDir::homePath() + "/.config/synthex/studio";
        
        // Ensure user config dir exists
        QDir().mkpath(m_userConfigDir);
    }

public slots:
    // Apply a theme by name
    QString ApplyTheme(const QString &themeName) {
        qDebug() << "🎨 Applying theme:" << themeName;
        
        // Create snapshot before applying
        createSnapshot("pre-theme-" + themeName);
        
        QString themePath = m_themesDir + "/" + themeName + ".json";
        QFile file(themePath);
        if (!file.exists()) {
            themePath = m_userConfigDir + "/themes/" + themeName + ".json";
        }
        
        if (!QFile::exists(themePath)) {
            return "Error: Theme '" + themeName + "' not found";
        }
        
        file.setFileName(themePath);
        if (!file.open(QIODevice::ReadOnly)) {
            return "Error: Cannot read theme file";
        }
        
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        QJsonObject theme = doc.object();
        file.close();
        
        // Apply Plasma color scheme
        if (theme.contains("colorscheme")) {
            QString scheme = theme["colorscheme"].toString();
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "General",
                "--key", "ColorScheme", scheme
            });
        }
        
        // Apply Plasma theme
        if (theme.contains("plasmatheme")) {
            QString pt = theme["plasmatheme"].toString();
            QProcess::execute("lookandfeeltool", {"-a", pt});
        }
        
        // Apply icon theme
        if (theme.contains("icons")) {
            QString icons = theme["icons"].toString();
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "Icons",
                "--key", "Theme", icons
            });
        }
        
        // Apply cursor theme
        if (theme.contains("cursor")) {
            QString cursor = theme["cursor"].toString();
            QProcess::execute("kwriteconfig6", {
                "--file", "kcminputrc", "--group", "Mouse",
                "--key", "cursorTheme", cursor
            });
        }
        
        // Apply font
        if (theme.contains("font")) {
            QJsonObject font = theme["font"].toObject();
            QString family = font["family"].toString();
            int size = font["size"].toInt(10);
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "General",
                "--key", "font", QString("%1,%2,-1,5,50,0,0,0,0,0").arg(family).arg(size)
            });
        }
        
        // Restart Plasma shell to apply
        QProcess::startDetached("plasmashell", {"--replace"});
        
        qDebug() << "✅ Theme applied:" << themeName;
        return "OK: Theme '" + themeName + "' applied";
    }

    // Mix elements from multiple themes
    QString MixTheme(const QString &windowStyle, const QString &iconPack,
                     const QString &cursorTheme, const QString &fontFamily) {
        qDebug() << "🎨 Mixing theme:" << windowStyle << iconPack << cursorTheme << fontFamily;
        
        createSnapshot("pre-theme-mix");
        
        if (!windowStyle.isEmpty()) {
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "General",
                "--key", "ColorScheme", windowStyle
            });
        }
        if (!iconPack.isEmpty()) {
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "Icons",
                "--key", "Theme", iconPack
            });
        }
        if (!cursorTheme.isEmpty()) {
            QProcess::execute("kwriteconfig6", {
                "--file", "kcminputrc", "--group", "Mouse",
                "--key", "cursorTheme", cursorTheme
            });
        }
        if (!fontFamily.isEmpty()) {
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "General",
                "--key", "font", fontFamily + ",10,-1,5,50,0,0,0,0,0"
            });
        }
        
        QProcess::startDetached("plasmashell", {"--replace"});
        
        return "OK: Theme mixed and applied";
    }

    // Apply a rice preset (cyberpunk, minimal, glass, nature)
    QString ApplyPreset(const QString &presetName) {
        qDebug() << "🌀 Applying rice preset:" << presetName;
        
        createSnapshot("pre-preset-" + presetName);
        
        QString presetPath = m_presetsDir + "/" + presetName + ".json";
        QFile file(presetPath);
        if (!file.open(QIODevice::ReadOnly)) {
            return "Error: Preset '" + presetName + "' not found";
        }
        
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        QJsonObject preset = doc.object();
        file.close();
        
        // Apply all preset settings
        if (preset.contains("colorscheme")) {
            QProcess::execute("kwriteconfig6", {
                "--file", "kdeglobals", "--group", "General",
                "--key", "ColorScheme", preset["colorscheme"].toString()
            });
        }
        if (preset.contains("layout")) {
            QProcess::execute("synthex-layout", {"set", preset["layout"].toString()});
        }
        if (preset.contains("compositor")) {
            QJsonObject comp = preset["compositor"].toObject();
            QProcess::execute("kwriteconfig6", {
                "--file", "kwinrc", "--group", "Compositing",
                "--key", "Enabled", comp["enabled"].toBool() ? "true" : "false"
            });
            if (comp.contains("blur")) {
                QProcess::execute("kwriteconfig6", {
                    "--file", "kwinrc", "--group", "Compositing",
                    "--key", "Backend", comp["blur"].toBool() ? "OpenGL" : "XRender"
                });
            }
        }
        
        // Restart Plasma
        QProcess::startDetached("plasmashell", {"--replace"});
        
        return "OK: Preset '" + presetName + "' applied";
    }

    // List available themes
    QString ListThemes() {
        QStringList themes;
        QDir dir(m_themesDir);
        for (const QString &f : dir.entryList({"*.json"}, QDir::Files)) {
            themes << f.replace(".json", "");
        }
        return themes.join(", ");
    }

    // List available presets
    QString ListPresets() {
        QStringList presets;
        QDir dir(m_presetsDir);
        for (const QString &f : dir.entryList({"*.json"}, QDir::Files)) {
            presets << f.replace(".json", "");
        }
        return presets.join(", ");
    }

    // Export current setup as a preset
    QString ExportPreset(const QString &name) {
        QJsonObject preset;
        preset["name"] = name;
        preset["timestamp"] = QDateTime::currentDateTime().toString(Qt::ISODate);
        
        // Read current theme settings
        QProcess proc;
        proc.start("kreadconfig5", {"--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"});
        proc.waitForFinished();
        preset["colorscheme"] = QString(proc.readAllStandardOutput()).trimmed();
        
        proc.start("kreadconfig5", {"--file", "kdeglobals", "--group", "Icons", "--key", "Theme"});
        proc.waitForFinished();
        preset["icons"] = QString(proc.readAllStandardOutput()).trimmed();
        
        // Save to user presets
        QString userPresetsDir = m_userConfigDir + "/presets";
        QDir().mkpath(userPresetsDir);
        
        QFile file(userPresetsDir + "/" + name + ".json");
        if (file.open(QIODevice::WriteOnly)) {
            file.write(QJsonDocument(preset).toJson(QJsonDocument::Indented));
            file.close();
            return "OK: Preset exported as '" + name + "'";
        }
        return "Error: Could not write preset file";
    }

    // Rollback last theme change
    QString RollbackLastChange() {
        qDebug() << "🔄 Rolling back last theme change...";
        // Get latest snapshot number from snapper
        QProcess listProc;
        listProc.start("snapper", {"-c", "root", "list", "--disable-used-space",
                                    "--columns=number", "--sort=number", "--output=csv"});
        listProc.waitForFinished(5000);
        QString output = QString::fromUtf8(listProc.readAllStandardOutput()).trimmed();
        QStringList lines = output.split('\n');
        if (lines.size() > 1) {
            QString lastSnap = lines.last().trimmed();
            QProcess::execute("snapper", {"-c", "root", "undochange", lastSnap + "..0"});
        }
        return "OK: Rolled back to previous state";
    }

signals:
    void ThemeChanged(const QString &themeName);
    void PresetApplied(const QString &presetName);
    void RollbackCompleted();

private:
    void createSnapshot(const QString &description) {
        QProcess::execute("snapper", {
            "-c", "root", "create", "-d", description
        });
    }

    QString m_themesDir;
    QString m_layoutsDir;
    QString m_presetsDir;
    QString m_userConfigDir;
};

// D-Bus adaptor
class StudioAdaptor : public QDBusAbstractAdaptor {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.synthex.Studio")
    Q_PROPERTY(QString version READ version CONSTANT)

public:
    StudioAdaptor(StudioDaemon *daemon)
        : QDBusAbstractAdaptor(daemon), m_daemon(daemon) {
        setAutoRelaySignals(true);
    }

    QString version() const { return "1.0.0"; }

public slots:
    QString ApplyTheme(const QString &themeName) {
        return m_daemon->ApplyTheme(themeName);
    }
    QString MixTheme(const QString &window, const QString &icons,
                     const QString &cursor, const QString &font) {
        return m_daemon->MixTheme(window, icons, cursor, font);
    }
    QString ApplyPreset(const QString &preset) {
        return m_daemon->ApplyPreset(preset);
    }
    QString ListThemes() { return m_daemon->ListThemes(); }
    QString ListPresets() { return m_daemon->ListPresets(); }
    QString ExportPreset(const QString &name) {
        return m_daemon->ExportPreset(name);
    }
    QString RollbackLastChange() {
        return m_daemon->RollbackLastChange();
    }

private:
    StudioDaemon *m_daemon;
};

// ─── Main entry point ──────────────────────────────────────────────

int main(int argc, char *argv[]) {
    QCoreApplication app(argc, argv);
    app.setApplicationName("Synthex Studio Daemon");
    app.setApplicationVersion("1.0.0");

    // Handle SIGTERM gracefully
    signal(SIGTERM, [](int) { QCoreApplication::quit(); });
    signal(SIGINT, [](int) { QCoreApplication::quit(); });

    StudioDaemon daemon;
    new StudioAdaptor(&daemon);

    QDBusConnection bus = QDBusConnection::sessionBus();
    if (!bus.registerObject("/", &daemon)) {
        qCritical() << "Failed to register D-Bus object:" << bus.lastError().message();
        return 1;
    }
    if (!bus.registerService("org.synthex.Studio")) {
        qCritical() << "Failed to register D-Bus service:" << bus.lastError().message();
        return 1;
    }

    qDebug() << "☀️ Synthex Studio Daemon ready (org.synthex.Studio)";
    return app.exec();
}

#include "main.moc"