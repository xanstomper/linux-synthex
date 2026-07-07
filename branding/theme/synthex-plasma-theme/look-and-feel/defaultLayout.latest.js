// Synthex default Plasma layout
// Thin top bar + floating dock + smart sidebar

var plasma = getApi("plasma");
var activities = getApi("activity");

// Remove default panels
var panels = panelIds();
for (var i = 0; i < panels.length; i++) {
    if (panels[i] != 1) removePanel(panels[i]);
}

// ─── Top Bar (thin, GNOME-like, 32px) ───
var topBar = new Panel("org.kde.panel");
topBar.location = "top";
topBar.height = 32;
topBar.alignment = "center";
topBar.addWidget("org.kde.plasma.kickoff");       // App launcher
widgets = topBar.widgets();
widgets[0].currentConfigTree = {
    "General": {
        "icon": "synthex-logo",
        "favoriteApps": [
            "org.kde.dolphin.desktop",
            "org.kde.konsole.desktop",
            "firefox.desktop",
            "steam.desktop",
            "code.desktop",
            "org.synthex.ControlCenter.desktop"
        ]
    }
};

topBar.addWidget("org.kde.plasma.pager");         // Virtual desktops
topBar.addWidget("org.kde.plasma.systemmonitor.cpu");  // CPU widget
topBar.addSpacer();
topBar.addWidget("org.kde.plasma.search");        // Search
topBar.addWidget("org.kde.plasma.notifications");  // Notifications
topBar.addWidget("org.kde.plasma.analogclock");    // Clock
topBar.addWidget("org.kde.plasma.systemtray");     // System tray

// ─── Floating Dock ───
var dock = new Panel("org.kde.panel");
dock.location = "bottom";
dock.height = 48;
dock.floating = true;
dock.alignment = "center";
dock.addWidget("org.kde.plasma.icons");            // Task manager
dock.addWidget("org.kde.plasma.showdesktop");      // Show desktop

// ─── Smart Sidebar ───
var sidebar = new Panel("org.kde.panel");
sidebar.location = "right";
sidebar.width = 280;
sidebar.floating = true;
sidebar.addWidget("org.kde.plasma.systemmonitor");  // System monitor
sidebar.addWidget("org.kde.plasma.weather");        // Weather
sidebar.addWidget("org.kde.plasma.mediacontroller"); // Media
sidebar.addWidget("org.kde.plasma.calculator");     // Calculator

// Enable blur on all panels
for (var i = 0; i < panelIds().length; i++) {
    var p = getPanel(panelIds()[i]);
    p.backgroundHints = "AlwaysBlur";
}

// Set default wallpapers
activities.currentActivity.wallpaperPlugin = "org.kde.image";
activities.currentActivity.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
activities.currentActivity.writeConfig("Image", "/usr/share/wallpapers/synthex-graphite.png");

print("Synthex Desktop layout applied");
