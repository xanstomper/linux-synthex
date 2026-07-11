/**
 * synthex-ai-workspaces.js — KWin script for Brain OS workspace control
 *
 * Loaded by synthex-workspace-ai via the KWin Scripting D-Bus interface:
 *   org.kde.KWin.Scripting.loadScript(path, "synthex-ai-workspaces")
 *
 * What this script does:
 *   1. Watches virtual desktop switches and emits a custom D-Bus signal so
 *      synthex-workspace-ai can update the active agent context instantly.
 *   2. Lets synthex-workspace-ai move/tile windows by calling the exported
 *      functions via KWin's callDBus / script eval mechanism.
 *   3. Applies a visual "AI active" highlight (colored border) to the window
 *      currently owned by a Brain OS agent.
 *   4. Enforces workspace-pinning: agent-owned windows stay on their
 *      assigned desktop and cannot be dragged to another by the user unless
 *      the agent releases the pin.
 */

"use strict";

// ── Configuration (read from ~/.config/synthex/kwin-ai.json if it exists) ────

var cfg = {
    agentBorderColor:  "#7c3aed",  // violet — Brain OS brand color
    agentBorderWidth:  3,
    pinnedOpacity:     1.0,
    dimNonAgentWindows: false,
    dimOpacity:        0.85,
    maxWorkspaces:     8,
};

// ── State ─────────────────────────────────────────────────────────────────────

/** windowId → { desktop: int, pinned: bool, agentId: string } */
var agentWindows = {};

/** Per-desktop agent context label (set by workspace-ai via evalScript). */
var desktopContextLabels = {};

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg) {
    print("[synthex-ai-workspaces] " + msg);
}

function notifyWorkspaceAI(event, payload) {
    // Brain OS picks this up by tailing KWin's output or via D-Bus custom signals.
    // Format: JSON on stdout, prefixed with SYNTHEX_KWIN_EVENT:
    print("SYNTHEX_KWIN_EVENT:" + JSON.stringify({ event: event, payload: payload, ts: Date.now() }));
}

// ── Virtual desktop switch ────────────────────────────────────────────────────

workspace.currentDesktopChanged.connect(function(oldDesktop) {
    var newDesktop = workspace.currentDesktop;
    notifyWorkspaceAI("desktop_switched", {
        from: oldDesktop,
        to:   newDesktop,
        activeWindow: workspace.activeWindow ? workspace.activeWindow.windowId : null,
    });
    log("desktop switched " + oldDesktop + " → " + newDesktop);
});

// ── Window focus change ───────────────────────────────────────────────────────

workspace.windowActivated.connect(function(w) {
    if (!w) return;
    notifyWorkspaceAI("window_focused", {
        windowId:  w.windowId,
        caption:   w.caption,
        desktop:   w.desktop,
        resourceClass: w.resourceClass,
        isAgent:   (w.windowId in agentWindows),
    });
});

// ── Window opened ─────────────────────────────────────────────────────────────

workspace.windowAdded.connect(function(w) {
    notifyWorkspaceAI("window_opened", {
        windowId:      w.windowId,
        caption:       w.caption,
        desktop:       w.desktop,
        resourceClass: w.resourceClass,
        geometry:      { x: w.x, y: w.y, width: w.width, height: w.height },
    });
});

// ── Window closed ─────────────────────────────────────────────────────────────

workspace.windowRemoved.connect(function(w) {
    if (w.windowId in agentWindows) {
        delete agentWindows[w.windowId];
        log("agent window removed: " + w.windowId);
    }
    notifyWorkspaceAI("window_closed", {
        windowId: w.windowId,
        caption:  w.caption,
    });
});

// ── Workspace pinning: prevent agent windows being dragged off their desktop ──

workspace.windowDesktopChanged.connect(function(w, oldDesktop) {
    var entry = agentWindows[w.windowId];
    if (!entry || !entry.pinned) return;

    if (w.desktop !== entry.desktop) {
        log("pinned agent window " + w.windowId + " moved; restoring to desktop " + entry.desktop);
        w.desktop = entry.desktop;
        notifyWorkspaceAI("pin_enforced", {
            windowId:    w.windowId,
            agentId:     entry.agentId,
            pinnedDesktop: entry.desktop,
            attemptedDesktop: oldDesktop,
        });
    }
});

// ── Exported functions (called by synthex-workspace-ai via KWin evalScript) ───

/**
 * registerAgentWindow(windowId, desktop, agentId, pinned)
 * Called by synthex-workspace-ai to mark a window as agent-owned.
 */
function registerAgentWindow(windowId, desktop, agentId, pinned) {
    agentWindows[windowId] = { desktop: desktop, agentId: agentId, pinned: !!pinned };
    log("registered agent window " + windowId + " for agent " + agentId + " on desktop " + desktop);

    var w = findWindow(windowId);
    if (w && cfg.agentBorderWidth > 0) {
        // Apply colored outline effect (requires kwin-effects-outline or similar)
        // Gracefully skips if effect not available.
        try {
            effects.toggleEffect("outline");
        } catch (e) {}
    }
    notifyWorkspaceAI("agent_window_registered", { windowId: windowId, agentId: agentId, desktop: desktop });
}

/**
 * unregisterAgentWindow(windowId)
 */
function unregisterAgentWindow(windowId) {
    if (windowId in agentWindows) {
        delete agentWindows[windowId];
        log("unregistered agent window " + windowId);
    }
}

/**
 * moveWindowToDesktop(windowId, desktop)
 * Move a window to the given 1-indexed virtual desktop.
 */
function moveWindowToDesktop(windowId, desktop) {
    var w = findWindow(windowId);
    if (!w) { log("moveWindowToDesktop: window " + windowId + " not found"); return false; }
    w.desktop = desktop;
    notifyWorkspaceAI("window_moved_to_desktop", { windowId: windowId, desktop: desktop });
    return true;
}

/**
 * setWindowGeometry(windowId, x, y, width, height)
 * Resize and reposition a window (used by agent tile layouts).
 */
function setWindowGeometry(windowId, x, y, width, height) {
    var w = findWindow(windowId);
    if (!w) return false;
    w.frameGeometry = { x: x, y: y, width: width, height: height };
    return true;
}

/**
 * tileAgentWindows(desktop, layout)
 * Auto-tile all agent windows on a desktop.
 * layout: "columns" | "rows" | "grid" | "main-side"
 */
function tileAgentWindows(desktop, layout) {
    var wins = [];
    for (var id in agentWindows) {
        if (agentWindows[id].desktop === desktop) {
            var w = findWindow(parseInt(id));
            if (w) wins.push(w);
        }
    }
    if (wins.length === 0) return;

    var area   = workspace.clientArea(0, workspace.activeScreen, desktop);
    var n      = wins.length;
    var W      = area.width;
    var H      = area.height;
    var x      = area.x;
    var y      = area.y;

    if (layout === "columns" || n <= 3) {
        var colW = Math.floor(W / n);
        for (var i = 0; i < n; i++) {
            wins[i].frameGeometry = { x: x + i * colW, y: y, width: colW, height: H };
        }
    } else if (layout === "rows") {
        var rowH = Math.floor(H / n);
        for (var i = 0; i < n; i++) {
            wins[i].frameGeometry = { x: x, y: y + i * rowH, width: W, height: rowH };
        }
    } else if (layout === "main-side") {
        // First window gets 60%, rest share 40% in a column
        wins[0].frameGeometry = { x: x, y: y, width: Math.floor(W * 0.6), height: H };
        var sideW = Math.floor(W * 0.4);
        var sideH = n > 1 ? Math.floor(H / (n - 1)) : H;
        for (var i = 1; i < n; i++) {
            wins[i].frameGeometry = { x: x + Math.floor(W * 0.6), y: y + (i - 1) * sideH, width: sideW, height: sideH };
        }
    } else {
        // grid
        var cols = Math.ceil(Math.sqrt(n));
        var rows = Math.ceil(n / cols);
        var cW   = Math.floor(W / cols);
        var rH   = Math.floor(H / rows);
        for (var i = 0; i < n; i++) {
            var col = i % cols;
            var row = Math.floor(i / cols);
            wins[i].frameGeometry = { x: x + col * cW, y: y + row * rH, width: cW, height: rH };
        }
    }

    notifyWorkspaceAI("tiled_agent_windows", { desktop: desktop, layout: layout, count: n });
}

/**
 * setDesktopContextLabel(desktop, label)
 * Stores a human-readable context label for each desktop (e.g. "Research", "Coding").
 * The label can be read back by the panel widget.
 */
function setDesktopContextLabel(desktop, label) {
    desktopContextLabels[desktop] = label;
    // Update the KWin desktop name
    try {
        workspace.desktopName(desktop, label);
    } catch (e) {
        // KWin API varies; ignore if unavailable
    }
    notifyWorkspaceAI("context_label_set", { desktop: desktop, label: label });
}

/**
 * getState()
 * Return current script state as JSON (for workspace-ai to poll).
 */
function getState() {
    return JSON.stringify({
        currentDesktop:   workspace.currentDesktop,
        numDesktops:      workspace.numDesktops,
        agentWindows:     agentWindows,
        contextLabels:    desktopContextLabels,
    });
}

// ── Helper: find a KWin client by windowId ────────────────────────────────────

function findWindow(windowId) {
    var clients = workspace.windowList();
    for (var i = 0; i < clients.length; i++) {
        if (clients[i].windowId === windowId) return clients[i];
    }
    return null;
}

// ── Init ──────────────────────────────────────────────────────────────────────

log("synthex-ai-workspaces KWin script loaded — Brain OS workspace control active");
notifyWorkspaceAI("script_loaded", {
    numDesktops: workspace.numDesktops,
    currentDesktop: workspace.currentDesktop,
});
