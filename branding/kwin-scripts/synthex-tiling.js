// Synthex Tiling — KWin script for smart window tiling
// Inspired by Hyprland + GNOME simplicity

// Layout: Master-stack
// Master is left 60%, stack is right 40%

var layouts = [
    { name: "Focus",       masterRatio: 0.70, gap: 4 },
    { name: "Balanced",    masterRatio: 0.60, gap: 6 },
    { name: "Wide",        masterRatio: 0.50, gap: 8 },
];
var currentLayout = 1;

function tile(desktop) {
    var clients = workspace.clientList().filter(function(c) {
        return c.desktop == desktop && c.normalWindow;
    });
    
    if (clients.length === 0) return;
    if (clients.length === 1) {
        clients[0].geometry = workspace.clientArea(KWin.FullScreenArea, desktop, workspace.currentActivity);
        return;
    }
    
    var layout = layouts[currentLayout];
    var area = workspace.clientArea(KWin.FullScreenArea, desktop, workspace.currentActivity);
    var gap = layout.gap;
    var masterW = Math.floor(area.width * layout.masterRatio);
    var stackW = area.width - masterW - gap;
    
    // Master window (left)
    clients[0].geometry = {
        x: area.x + gap/2,
        y: area.y + gap/2,
        width: masterW - gap,
        height: area.height - gap
    };
    
    // Stack windows (right)
    var numStack = clients.length - 1;
    var stackH = (area.height - (numStack + 1) * gap) / numStack;
    for (var i = 1; i < clients.length; i++) {
        clients[i].geometry = {
            x: masterW + gap,
            y: area.y + gap/2 + (i-1) * (stackH + gap),
            width: stackW - gap/2,
            height: stackH
        };
    }
}

// Connect signals
workspace.clientAdded.connect(function(client) {
    tile(workspace.currentDesktop);
});
workspace.clientRemoved.connect(function(client) {
    tile(workspace.currentDesktop);
});

print("Synthex Tiling loaded - Layout: " + layouts[currentLayout].name);
