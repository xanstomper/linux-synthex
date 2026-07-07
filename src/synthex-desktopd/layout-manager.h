#ifndef SYNTHEX_LAYOUT_MANAGER_H
#define SYNTHEX_LAYOUT_MANAGER_H

#include <QString>
#include <QStringList>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QFile>
#include <QDir>
#include <QDebug>

/**
 * @brief Describes a complete desktop layout configuration.
 *
 * Populated from JSON layout definitions stored under
 * /usr/share/synthex/layouts/<name>.json
 */
struct LayoutConfig {
    /** Panel position: "bottom", "top", "left", "right" */
    QString panelPosition;

    /** Panel height in pixels */
    int panelHeight = 36;

    /** Whether a dock (like Latte or Plasma dock) is enabled */
    bool dockEnabled = false;

    /** Compositor blur setting */
    bool compositorBlur = true;

    /** Compositor VSync: "full" (default), "partial", "none" */
    QString compositorVsync = QStringLiteral("full");

    /** Compositor latency mode: "low", "normal", "high" */
    QString compositorLatency = QStringLiteral("normal");

    /** List of systemd services to disable in this layout */
    QStringList serviceBlacklist;

    /** Keyboard shortcut overrides (action → shortcut) */
    QJsonObject shortcuts;

    /** Wallpaper file path or colour */
    QString wallpaper;

    /** Plasma desktop theme to apply */
    QString theme;

    /** Validate that required fields are present */
    bool isValid() const {
        return !panelPosition.isEmpty();
    }
};

/**
 * @brief LayoutManager handles reading, validating, and enumerating
 *        desktop layout definitions from JSON files.
 */
class LayoutManager
{
public:
    explicit LayoutManager(const QString &layoutDir = QStringLiteral("/usr/share/synthex/layouts"));

    /** Load and parse a layout definition by name */
    LayoutConfig loadLayout(const QString &name) const;

    /** Validate a loaded layout for required fields */
    bool validateLayout(const LayoutConfig &config) const;

    /** List all available layout names */
    QStringList listAvailableLayouts() const;

    /** Return the default layout configs as built-in presets */
    static LayoutConfig defaultLayout(const QString &name);

private:
    /** Parse a JSON object into a LayoutConfig struct */
    LayoutConfig parseLayoutJson(const QJsonObject &json) const;

    /** Directory where layout JSON files are stored */
    QString m_layoutDir;
};

#endif // SYNTHEX_LAYOUT_MANAGER_H