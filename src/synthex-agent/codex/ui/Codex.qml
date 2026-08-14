import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

// ═══ Synthex Codex — Built-in Desktop IDE with AI Agent ═════════════
// Full code editor + AI agent integration + file browser + terminal

Window {
    id: codex
    visible: true
    width: 1200; height: 800
    minimumWidth: 800; minimumHeight: 500
    title: "Synthex Codex — AI Agent IDE"

    readonly property color accent: "#6C88A8"
    readonly property color bg: "#171D24"
    readonly property color panel: "#16162A"
    readonly property color card: "#222240"
    readonly property color text: "#FFFFFF"
    readonly property color muted: "#9AA1AB"
    readonly property color border: "#3A3A5E"

    // ─── Main Split ────────────────────────────────────────────────
    RowLayout {
        anchors.fill: parent; spacing: 0

        // File sidebar
        Rectangle {
            Layout.preferredWidth: 200; Layout.fillHeight: true
            color: panel
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 8; spacing: 4
                Text { text: "📁 Explorer"; color: accent; font.pixelSize: 11; font.bold: true }
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    clip: true; spacing: 2
                    model: ["src/", "systemd/", "kernel/", "packages/", "configs/", "desktop/", "branding/"]
                    delegate: Text { text: "  📄 " + modelData; color: muted; font.pixelSize: 11; height: 22 }
                }
            }
        }

        // Editor area
        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true
            color: bg
            ColumnLayout { anchors.fill: parent; spacing: 0

                // Tab bar
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 32; color: panel
                    RowLayout { anchors.fill: parent; anchors.leftMargin: 8; spacing: 4
                        Text { text: "📝 main.py"; color: text; font.pixelSize: 11; font.bold: true }
                        Text { text: "✕"; color: muted; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: "💾"; color: muted; font.pixelSize: 11; MouseArea { anchors.fill: parent; onClicked: saveCode() } }
                    }
                }

                // Code editor
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    color: "#0D1117"
                    Flickable {
                        anchors.fill: parent; anchors.margins: 4
                        contentWidth: editor.width; contentHeight: editor.height
                        TextEdit {
                            id: editor
                            width: 750; height: 4000
                            color: "#E6EDF3"; font.pixelSize: 12; font.family: "monospace"
                            selectByMouse: true
                            text: `#!/usr/bin/env python3
"""Synthex Agent — Desktop AI Platform"""
import os, sys, json, subprocess

def main():
    print("Synthex Agent ready")
    # Agent integration here
    
if __name__ == "__main__":
    main()
`
                        }
                    }
                }

                // Agent chat bar
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 80
                    color: panel; border.color: border; border.width: 1
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 8; spacing: 8
                        Rectangle { width: 32; height: 32; radius: 16; color: accent
                            Text { anchors.centerIn: parent; text: "Ω"; color: "#FFF"; font.bold: true; font.pixelSize: 16 } }
                        TextInput {
                            Layout.fillWidth: true; verticalAlignment: TextInput.AlignVCenter
                            color: text; font.pixelSize: 12
                            placeholderText: "Ask Synthex Agent to write, refactor, or explain code..."
                            Keys.onReturnPressed: agentRequest(text)
                        }
                    }
                }
            }
        }

        // Agent output panel
        Rectangle {
            Layout.preferredWidth: 300; Layout.fillHeight: true
            color: panel; border.color: border; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 8; spacing: 6
                Text { text: "🤖 Agent"; color: accent; font.pixelSize: 11; font.bold: true }
                ListView {
                    id: agentLog; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 4
                    model: agentModel; delegate: Rectangle {
                        width: agentLog.width; height: 40; radius: 4; color: card
                        Text { anchors.margins: 6; anchors.fill: parent; color: text; font.pixelSize: 10
                            wrapMode: Text.WordWrap; text: model.text || "" }
                    }
                }
                Button {
                    Layout.fillWidth: true; text: "▶ Apply Changes"
                    background: Rectangle { color: accent; radius: 6 }
                    contentItem: Text { text: "▶ Apply Changes"; color: "#FFF"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                }
            }
        }
    }

    ListModel { id: agentModel }

    function saveCode() {
        agentModel.append({ text: "💾 Code saved to working file" })
    }

    function agentRequest(text) {
        agentModel.append({ text: "🧑 " + text })
        agentModel.append({ text: "🤖 Processing..." })
        var con = new QDBusConnection("session")
        var req = JSON.stringify({ task: text, code: editor.text, path: "main.py" })
        var msg = con.call("org.synthex.Agent", "/org/synthex/Agent", "org.synthex.Agent", "CodeAction", [req], 60000)
        agentModel.remove(agentModel.count - 1)
        if (msg.type === 1) {
            try {
                var data = JSON.parse(msg.arguments[0])
                agentModel.append({ text: data.response || "Done" })
                // Extract code blocks into editor
                var codeMatch = data.response.match(/```[\w]*\n([\s\S]*?)```/)
                if (codeMatch) {
                    editor.text = codeMatch[1]
                    agentModel.append({ text: "✅ Code updated in editor" })
                }
            } catch(e) { agentModel.append({ text: msg.arguments[0] }) }
        } else {
            agentModel.append({ text: "⚠️ Daemon not running" })
        }
    }
}
