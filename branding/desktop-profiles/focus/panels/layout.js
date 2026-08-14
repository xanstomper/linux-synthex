// ╔══════════════════════════════════════════════════════════════╗
// ║  SynthOS Nova — Plasma panel layout (Synthex Focus profile)  ║
// ║  Floating centered bottom panel · real Plasma 6 widgets      ║
// ╚══════════════════════════════════════════════════════════════╝
// Applied via: plasma-apply-desktoptheme / look-and-feel import

var plasma = getApi("plasma");

// Remove all existing panels
var existing = panelIds();
for (var i = 0; i < existing.length; i++) {
    removePanel(existing[i]);
}

// ─── Single floating panel, bottom, centered ───────────────────────────
var panel = new Panel("org.kde.plasma.panel");
panel.location = "bottom";
panel.height = 44;          // compact
panel.floating = true;      // Nova floating look (Plasma 6)

// Left: application launcher + window buttons
panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.marginsseparator");
var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.konsole.desktop",
    "applications:org.kde.dolphin.desktop",
    "applications:firefox.desktop",
    "applications:systemsettings.desktop"
].join(","));
tasks.writeConfig("groupingStrategy", "1");   // group by app
tasks.writeConfig("maxStripes", "1");
tasks.writeConfig("showToolbars", "false");

// Center: media controls (real MPRIS)
panel.addSpacer();
panel.addWidget("org.kde.plasma.mediacontroller");
panel.addSpacer();

// Right: system tray + clock
var tray = panel.addWidget("org.kde.plasma.systemtray");
tray.currentConfigGroup = ["General"];
tray.writeConfig("pin", "org.kde.plasma.volume,org.kde.plasma.networkmanagement,org.kde.plasma.battery,org.kde.plasma.bluetooth,org.kde.plasma.notifications,org.kde.plasma.nightcolor");
tray.writeConfig("scaleIconsToFit", "true");

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "custom");
clock.writeConfig("customDateFormat", "ddd  d  HH:mm");
clock.writeConfig("fontFamily", "Inter");

panel.addWidget("org.kde.plasma.marginsseparator");

print("SynthOS Nova panel layout applied");
