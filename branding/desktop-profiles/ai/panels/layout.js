// Synthex Synthex AI — Panel layout
// Installed via: plasma-apply-desktoptheme

var plasma = getApi("plasma");

// Remove all existing panels
var existing = panelIds();
for (var i = 0; i < existing.length; i++) {
    removePanel(existing[i]);
}

// Create panels
var panels = [];
var panelConfigs = {
  "top": {
    "type": "panel",
    "height": 32,
    "opacity": 0.85,
    "blur": true,
    "widgets": [
      "launcher",
      "ai-search",
      "spacer",
      "clock",
      "tray"
    ]
  },
  "left": {
    "type": "sidebar",
    "width": 320,
    "opacity": 0.95,
    "blur": true,
    "floating": true,
    "widgets": [
      "ai-chat",
      "ai-context",
      "ai-agents",
      "ai-models"
    ]
  }
};

for (var loc in panelConfigs) {
    var cfg = panelConfigs[loc];
    var panel = new Panel("org.kde.panel");
    panel.location = loc;
    if (cfg.height) panel.height = cfg.height;
    if (cfg.width) panel.width = cfg.width;
    if (cfg.floating) panel.floating = true;
    if (cfg.opacity < 1.0 && !cfg.blur) panel.opacity = cfg.opacity;
    
    // Add widgets
    for (var w = 0; w < cfg.widgets.length; w++) {
        var wid = cfg.widgets[w];
        if (wid == 'spacer') panel.addSpacer();
        else panel.addWidget("org.kde.plasma." + wid);
    }
    
    panels.push(panel);
}

print("Synthex Synthex AI panels applied");
