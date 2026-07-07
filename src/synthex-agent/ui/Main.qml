import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import Qt.labs.platform 1.1

// ═══ Synthex Hermes — Native Desktop AI Agent ═══════════════════════════
// Full native Qt6/QML app. Taskbar integration. State icons. Distro-aware.
// Design: Synthex Mint (#9BBD5C), frameless, dark glass, native OS feel.

Window {
    id: hermes
    visible: false
    width: 580; height: 520
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SkipTaskbar
    color: "transparent"

    // ═══ Color palette (Synthex Mint) ═══════════════════════════════════════
    readonly property color accent: "#9BBD5C"
    readonly property color accentHover: "#A8CC6A"
    readonly property color bg: "#1A1A2E"
    readonly property color card: "#222240"
    readonly property color inputBg: "#2A2A4E"
    readonly property color text: "#FFFFFF"
    readonly property color textSec: "#8899AA"
    readonly property color textMuted: "#667788"
    readonly property color border: "#3A3A5E"
    readonly property color success: "#4CAF50"
    readonly property color danger: "#E53935"
    readonly property color warning: "#FFA726"

    // ═══ State machine ═══════════════════════════════════════════════════
    property string agentState: "ready"  // ready | thinking | working | needs_permission
    property var pendingAction: null
    property var chatHistory: []

    Component.onCompleted: {
        x = (Screen.width - width) / 2
        y = Screen.height * 0.12
        updateState()
    }

    function updateState() {
        var con = new QDBusConnection("session")
        var msg = con.call("org.synthex.Hermes", "/org/synthex/Hermes", "org.synthex.Hermes", "GetStatus", [], 2000)
        if (msg.type === 1) {
            try {
                var s = JSON.parse(msg.arguments[0])
                agentState = s.status || "ready"
                stateIndicator.text = statusIcon()
                stateIndicator.color = statusColor()
            } catch(e) {}
        }
    }

    function statusIcon() {
        return agentState === "ready" ? "🟢" :
               agentState === "thinking" ? "🟡" :
               agentState === "working" ? "🔵" :
               agentState === "needs_permission" ? "🔴" : "🟢"
    }
    function statusColor() {
        return agentState === "ready" ? success :
               agentState === "thinking" ? warning :
               agentState === "working" ? "#42A5F5" :
               agentState === "needs_permission" ? danger : textSec
    }

    // ═══ Background ══════════════════════════════════════════════════════
    Rectangle {
        anchors.fill: parent; radius: 16; color: bg; opacity: 0.97
        border.color: border; border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 10; spacing: 6

        // ─── Title Bar ───────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 36
            color: "transparent"
            RowLayout {
                anchors.fill: parent; spacing: 6
                Text { id: stateIndicator; text: "🟢"; font.pixelSize: 14 }
                Text { text: "Hermes"; color: accent; font.pixelSize: 13; font.bold: true }
                Text { text: "— Desktop AI Agent"; color: textSec; font.pixelSize: 10 }
                Item { Layout.fillWidth: true }
                Text { text: modelLabel.text; color: textMuted; font.pixelSize: 9 }
                Text { text: "✕"; color: textMuted; font.pixelSize: 13
                    MouseArea { anchors.fill: parent; onClicked: hermes.hide()
                        onEntered: parent.color = "#FFF"; onExited: parent.color = textMuted } }
            }
            MouseArea {
                anchors.fill: parent
                property point clickPos: "0,0"
                onPressed: clickPos = Qt.point(mouse.x, mouse.y)
                onPositionChanged: {
                    var d = Qt.point(mouse.x - clickPos.x, mouse.y - clickPos.y)
                    hermes.x += d.x; hermes.y += d.y
                }
            }
        }

        // ─── Search / Input Bar ──────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 44; radius: 10
            color: inputBg; border.color: searchInput.activeFocus ? accent : "transparent"
            border.width: searchInput.activeFocus ? 2 : 0

            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 6; spacing: 8
                Text { text: "🔍"; font.pixelSize: 16 }
                TextInput {
                    id: searchInput; Layout.fillWidth: true; verticalAlignment: TextInput.AlignVCenter
                    color: text; font.pixelSize: 14; clip: true
                    placeholderText: "Ask anything... Install Steam, fix Wi-Fi, update system..."
                    Keys.onReturnPressed: submit()
                    Keys.onEscapePressed: hermes.hide()
                }
                Rectangle {
                    width: 28; height: 28; radius: 14; color: accent; visible: searchInput.text.length > 0
                    Text { anchors.centerIn: parent; text: "→"; color: "#FFF"; font.bold: true; font.pixelSize: 14 }
                    MouseArea { anchors.fill: parent; onClicked: submit(); cursorShape: Qt.PointingHandCursor }
                }
            }
        }

        // ─── Content Area ────────────────────────────────────────────────
        Item { Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            ListView {
                id: chatList; anchors.fill: parent; spacing: 4; clip: true
                model: chatModel; delegate: chatDelegate
                visible: chatModel.count > 0
            }

            // Welcome screen when empty
            ColumnLayout {
                anchors.centerIn: parent; spacing: 8; visible: chatModel.count === 0
                Text { text: "🟢 Hermes"; color: accent; font.pixelSize: 18; font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter }
                Text { text: "Desktop AI Agent for SynthOS"; color: textSec; font.pixelSize: 11
                    anchors.horizontalCenter: parent.horizontalCenter }
                Item { height: 8 }
                ColumnLayout {
                    anchors.horizontalCenter: parent.horizontalCenter; spacing: 4
                    Repeater {
                        model: ["🎮  \"Install Steam\"", "🌐  \"Why is my Wi-Fi slow?\"",
                                "🖥️  \"Fix my NVIDIA drivers\"", "📦  \"Update my system\"",
                                "🔍  \"Check system health\""]
                        Text { text: modelData; color: textMuted; font.pixelSize: 11
                            anchors.horizontalCenter: parent.horizontalCenter
                            MouseArea { anchors.fill: parent
                                onClicked: { searchInput.text = modelData.slice(3, -1); searchInput.forceActiveFocus() } } }
                    }
                }
                Item { height: 8 }
                // Quick action chips
                Flow { anchors.horizontalCenter: parent.horizontalCenter; spacing: 6
                    Repeater {
                        model: ["📦 Install","🔄 Update","🎮 Gaming","🛡️ Status","📋 Logs","⚡ Doctor"]
                        Rectangle {
                            height: 28; radius: 14; color: card; border.color: border
                            Text { anchors.centerIn: parent; text: modelData; color: textSec; font.pixelSize: 10
                                leftPadding: 12; rightPadding: 12 }
                            MouseArea { anchors.fill: parent
                                onClicked: quickAction(modelData) }
                        }
                    }
                }
            }
        }

        // ─── Permission bar (visible when needs approval) ───────────────
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 40
            color: agentState === "needs_permission" ? "#3E2723" : "transparent"
            radius: 8; visible: agentState === "needs_permission"

            RowLayout {
                anchors.fill: parent; anchors.margins: 10; spacing: 8
                Text { text: "🔴 Hermes wants to:"; color: "#FFF"; font.pixelSize: 11 }
                Text { id: pendingText; text: ""; color: "#FFA726"; font.pixelSize: 11; Layout.fillWidth: true }
                Rectangle { width: 60; height: 24; radius: 12; color: accent
                    Text { anchors.centerIn: parent; text: "✓ Allow"; color: "#FFF"; font.pixelSize: 10; font.bold: true }
                    MouseArea { anchors.fill: parent; onClicked: approveAction() } }
                Rectangle { width: 60; height: 24; radius: 12; color: "#3A3A5E"
                    Text { anchors.centerIn: parent; text: "✕ Deny"; color: textSec; font.pixelSize: 10 }
                    MouseArea { anchors.fill: parent; onClicked: denyAction() } }
            }
        }

        // ─── Footer — Status bar ────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 24; color: "transparent"
            RowLayout { anchors.fill: parent; spacing: 8
                Text { text: modelLabel.text; color: textMuted; font.pixelSize: 9 }
                Text { text: "·"; color: textMuted; font.pixelSize: 9 }
                Rectangle { width: 6; height: 6; radius: 3; color: statusColor() }
                Text { text: agentState; color: textMuted; font.pixelSize: 9 }
                Item { Layout.fillWidth: true }
                Text { text: "Super+Space"; color: textMuted; font.pixelSize: 8 }
                Text { text: "Esc close"; color: textMuted; font.pixelSize: 8 }
            }
        }
    }

    // ═══ Models ══════════════════════════════════════════════════════════
    ListModel { id: chatModel }
    Text { id: modelLabel; text: "Hermes"; function update() {
        var con = new QDBusConnection("session")
        var msg = con.call("org.synthex.Hermes", "/org/synthex/Hermes", "org.synthex.Hermes", "GetStatus", [], 2000)
        if (msg.type === 1) { try { var s = JSON.parse(msg.arguments[0]); modelLabel.text = s.model || "Hermes" } catch(e) {} }
    } }

    Component {
        id: chatDelegate
        Rectangle {
            width: chatList.width; height: msgHeight + 24; radius: 8
            color: model.isUser ? accent : card
            property real msgHeight: msgText.contentHeight
            Text {
                id: msgText; anchors.left: parent.left; anchors.leftMargin: 10
                anchors.right: parent.right; anchors.rightMargin: 10
                anchors.top: parent.top; anchors.topMargin: 8
                text: model.message || ""; color: model.isUser ? "#FFF" : text
                font.pixelSize: 12; wrapMode: Text.WordWrap; textFormat: Text.RichText
            }
        }
    }

    // ═══ Core Functions ══════════════════════════════════════════════════
    function submit() {
        var text = searchInput.text.trim()
        if (!text) return
        chatModel.append({ message: text, isUser: true })
        searchInput.text = ""
        chatModel.append({ message: "🟡 Thinking...", isUser: false })
        agentState = "thinking"; updateState()

        var con = new QDBusConnection("session")
        var msg = con.call("org.synthex.Hermes", "/org/synthex/Hermes", "org.synthex.Hermes", "Chat", [text], 30000)
        chatModel.remove(chatModel.count - 1)
        if (msg.type === 1) {
            try {
                var data = JSON.parse(msg.arguments[0])
                var resp = data.response || "No response"
                chatModel.append({ message: resp, isUser: false })
                if (data.needs_approval) {
                    agentState = "needs_permission"
                    pendingText.text = data.plan || data.tool || "execute action"
                    pendingAction = data.tool
                } else {
                    agentState = "ready"
                }
            } catch(e) {
                chatModel.append({ message: msg.arguments[0] || "⚠️ Error", isUser: false })
                agentState = "ready"
            }
        } else {
            chatModel.append({ message: "⚠️ Daemon not running. Start: hermesd", isUser: false })
            agentState = "ready"
        }
        updateState()
        chatList.positionViewAtEnd()
    }

    function approveAction() {
        var con = new QDBusConnection("session")
        var msg = con.call("org.synthex.Hermes", "/org/synthex/Hermes", "org.synthex.Hermes", "ApproveAction", [pendingAction || ""], 10000)
        if (msg.type === 1) {
            try {
                var r = JSON.parse(msg.arguments[0])
                chatModel.append({ message: "✅ Action approved — " + JSON.stringify(r.result || {}), isUser: false })
            } catch(e) {}
        }
        agentState = "ready"; pendingAction = null; updateState()
    }

    function denyAction() {
        chatModel.append({ message: "⏹ Action denied", isUser: false })
        agentState = "ready"; pendingAction = null; updateState()
    }

    function quickAction(action) {
        var q = action.toLowerCase()
        var map = {
            "📦 install": "Install ",
            "🔄 update": "Update my system",
            "🎮 gaming": "Enable gaming mode",
            "🛡️ status": "Check system status",
            "📋 logs": "Show me system logs",
            "⚡ doctor": "Run system doctor",
        }
        searchInput.text = map[action] || action
        submit()
    }

    function show() { hermes.visible = true; hermes.raise(); hermes.requestActivate(); searchInput.forceActiveFocus(); modelLabel.update(); updateState() }
    function hide() { hermes.visible = false }
    function toggle() { if (visible) hide(); else show() }
}
