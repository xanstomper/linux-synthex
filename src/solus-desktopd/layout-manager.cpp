#include "layout-manager.h"
#include <QFileInfo>

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

LayoutManager::LayoutManager(const QString &layoutDir)
    : m_layoutDir(layoutDir)
{
}

// ---------------------------------------------------------------------------
// Load a layout definition from JSON
// ---------------------------------------------------------------------------

LayoutConfig LayoutManager::loadLayout(const QString &name) const
{
    QString path = m_layoutDir + QDir::separator() + name + QStringLiteral(".json");

    if (!QFileInfo::exists(path)) {
        qWarning("Layout '%s' not found at %s — using built-in default",
                 qPrintable(name), qPrintable(path));
        return defaultLayout(name);
    }

    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning("Cannot open layout file '%s': %s",
                 qPrintable(path), qPrintable(file.errorString()));
        return defaultLayout(name);
    }

    QByteArray data = file.readAll();
    file.close();

    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(data, &parseError);

    if (parseError.error != QJsonParseError::NoError) {
        qWarning("JSON parse error in '%s': %s",
                 qPrintable(path), qPrintable(parseError.errorString()));
        return defaultLayout(name);
    }

    if (!doc.isObject()) {
        qWarning("Layout '%s' is not a JSON object", qPrintable(path));
        return defaultLayout(name);
    }

    LayoutConfig config = parseLayoutJson(doc.object());
    if (!validateLayout(config)) {
        qWarning("Layout '%s' failed validation — using built-in default", qPrintable(name));
        return defaultLayout(name);
    }

    qInfo("Loaded layout '%s' from %s", qPrintable(name), qPrintable(path));
    return config;
}

// ---------------------------------------------------------------------------
// Parse JSON → LayoutConfig
// ---------------------------------------------------------------------------

LayoutConfig LayoutManager::parseLayoutJson(const QJsonObject &json) const
{
    LayoutConfig config;

    // Panel settings
    QJsonObject panel = json.value(QStringLiteral("panel")).toObject();
    config.panelPosition = panel.value(QStringLiteral("position")).toString(QStringLiteral("bottom"));
    config.panelHeight   = panel.value(QStringLiteral("height")).toInt(36);
    config.dockEnabled   = panel.value(QStringLiteral("dockEnabled")).toBool(false);

    // Compositor settings
    QJsonObject compositor = json.value(QStringLiteral("compositor")).toObject();
    config.compositorBlur     = compositor.value(QStringLiteral("blur")).toBool(true);
    config.compositorVsync    = compositor.value(QStringLiteral("vsync")).toString(QStringLiteral("full"));
    config.compositorLatency  = compositor.value(QStringLiteral("latency")).toString(QStringLiteral("normal"));

    // Service blacklist
    QJsonArray blacklist = json.value(QStringLiteral("serviceBlacklist")).toArray();
    for (const QJsonValue &svc : blacklist) {
        config.serviceBlacklist.append(svc.toString());
    }

    // Shortcuts
    config.shortcuts = json.value(QStringLiteral("shortcuts")).toObject();

    // Wallpaper
    config.wallpaper = json.value(QStringLiteral("wallpaper")).toString();

    // Theme
    config.theme = json.value(QStringLiteral("theme")).toString();

    return config;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

bool LayoutManager::validateLayout(const LayoutConfig &config) const
{
    if (config.panelPosition.isEmpty()) {
        qWarning("Layout validation failed: panelPosition is required");
        return false;
    }

    QStringList validPositions = {
        QStringLiteral("bottom"),
        QStringLiteral("top"),
        QStringLiteral("left"),
        QStringLiteral("right")
    };
    if (!validPositions.contains(config.panelPosition)) {
        qWarning("Layout validation failed: invalid panelPosition '%s'",
                 qPrintable(config.panelPosition));
        return false;
    }

    if (config.panelHeight < 20 || config.panelHeight > 200) {
        qWarning("Layout validation: panelHeight %d is outside reasonable range",
                 config.panelHeight);
        // Not fatal, but warn
    }

    return true;
}

// ---------------------------------------------------------------------------
// List available layouts
// ---------------------------------------------------------------------------

QStringList LayoutManager::listAvailableLayouts() const
{
    QDir dir(m_layoutDir);
    QStringList result;

    if (!dir.exists()) {
        qWarning("Layout directory '%s' does not exist", qPrintable(m_layoutDir));
        return result;
    }

    // Find all .json files and strip extensions
    QStringList entries = dir.entryList(QStringList() << QStringLiteral("*.json"),
                                        QDir::Files | QDir::Readable,
                                        QDir::Name);
    for (const QString &entry : entries) {
        result.append(entry.remove(QStringLiteral(".json")));
    }

    return result;
}

// ---------------------------------------------------------------------------
// Built-in default layouts
// ---------------------------------------------------------------------------

LayoutConfig LayoutManager::defaultLayout(const QString &name)
{
    LayoutConfig cfg;

    if (name == QLatin1String("gaming")) {
        cfg.panelPosition     = QStringLiteral("bottom");
        cfg.panelHeight       = 32;
        cfg.dockEnabled       = false;
        cfg.compositorBlur    = false;
        cfg.compositorVsync   = QStringLiteral("none");
        cfg.compositorLatency = QStringLiteral("low");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/gaming.jpg");
        cfg.theme             = QStringLiteral("breeze-dark");
        cfg.serviceBlacklist  = { QStringLiteral("solus-stored.service"),
                                  QStringLiteral("packagekit.service") };
    } else if (name == QLatin1String("minimal")) {
        cfg.panelPosition     = QStringLiteral("top");
        cfg.panelHeight       = 28;
        cfg.dockEnabled       = false;
        cfg.compositorBlur    = false;
        cfg.compositorVsync   = QStringLiteral("full");
        cfg.compositorLatency = QStringLiteral("low");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/minimal.jpg");
        cfg.theme             = QStringLiteral("breeze");
        cfg.serviceBlacklist  = { QStringLiteral("kactivitymanagerd") };
    } else if (name == QLatin1String("macos")) {
        cfg.panelPosition     = QStringLiteral("top");
        cfg.panelHeight       = 36;
        cfg.dockEnabled       = true;
        cfg.compositorBlur    = true;
        cfg.compositorVsync   = QStringLiteral("full");
        cfg.compositorLatency = QStringLiteral("normal");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/macos.jpg");
        cfg.theme             = QStringLiteral("macOS");
    } else if (name == QLatin1String("windows")) {
        cfg.panelPosition     = QStringLiteral("bottom");
        cfg.panelHeight       = 40;
        cfg.dockEnabled       = false;
        cfg.compositorBlur    = true;
        cfg.compositorVsync   = QStringLiteral("full");
        cfg.compositorLatency = QStringLiteral("normal");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/windows.jpg");
        cfg.theme             = QStringLiteral("breeze");
    } else if (name == QLatin1String("dev")) {
        cfg.panelPosition     = QStringLiteral("bottom");
        cfg.panelHeight       = 36;
        cfg.dockEnabled       = false;
        cfg.compositorBlur    = true;
        cfg.compositorVsync   = QStringLiteral("full");
        cfg.compositorLatency = QStringLiteral("low");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/dev.jpg");
        cfg.theme             = QStringLiteral("breeze-dark");
    } else { // balanced (default)
        cfg.panelPosition     = QStringLiteral("bottom");
        cfg.panelHeight       = 36;
        cfg.dockEnabled       = false;
        cfg.compositorBlur    = true;
        cfg.compositorVsync   = QStringLiteral("full");
        cfg.compositorLatency = QStringLiteral("normal");
        cfg.wallpaper         = QStringLiteral("/usr/share/solus/wallpapers/default.jpg");
        cfg.theme             = QStringLiteral("breeze");
    }

    cfg.shortcuts = QJsonObject();

    return cfg;
}