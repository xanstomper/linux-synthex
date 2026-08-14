import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 290
    height: 240
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: "#a612161f" // Translucent liquid glass
    border.color: "#28ffffff"
    border.width: 1

    property int brightnessPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.brightness : 52
    property int volumePct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.volume : 100

    // Liquid Glass Specular Top Highlight
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22ffffff" }
            GradientStop { position: 0.08; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        // ── 1. Sliders (Backlight & Volume) ────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            // Backlight Slider
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Text { text: "󰃠"; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: "#E5A84B" }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    radius: 4
                    color: "#1E2633"

                    Rectangle {
                        width: parent.width * (root.brightnessPct / 100.0)
                        height: parent.height
                        radius: 4
                        color: "#E5A84B"
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var pct = Math.max(5, Math.min(100, Math.round((mouse.x / width) * 100)))
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setBrightness(pct)
                            else root.brightnessPct = pct
                        }
                    }
                }

                Text { text: root.brightnessPct + "%"; font.family: "Inter"; font.pixelSize: 11; color: "#A0AAB8"; Layout.preferredWidth: 32 }
            }

            // Volume Slider
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Text { text: "󰕾"; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: "#2AC3DE" }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    radius: 4
                    color: "#1E2633"

                    Rectangle {
                        width: parent.width * (root.volumePct / 100.0)
                        height: parent.height
                        radius: 4
                        color: "#2AC3DE"
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var pct = Math.max(0, Math.min(100, Math.round((mouse.x / width) * 100)))
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setVolume(pct)
                            else root.volumePct = pct
                        }
                    }
                }

                Text { text: root.volumePct + "%"; font.family: "Inter"; font.pixelSize: 11; color: "#A0AAB8"; Layout.preferredWidth: 32 }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#0affffff"
        }

        // ── 2. Quick Hardware Action Tiles ─────────────────────────────────
        GridLayout {
            columns: 3
            rowSpacing: 8
            columnSpacing: 8
            Layout.fillWidth: true

            // Wi-Fi Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: "#207aa2f7"
                border.color: "#7AA2F7"
                border.width: 1

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "󰤨"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#7AA2F7"; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "SynthNet"; font.family: "Inter"; font.pixelSize: 10; font.bold: true; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                }
            }

            // Bluetooth Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: "#207aa2f7"
                border.color: "#7AA2F7"
                border.width: 1

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "󰂯"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#7AA2F7"; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "Bluetooth"; font.family: "Inter"; font.pixelSize: 10; font.bold: true; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                }
            }

            // Game Mode Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === "gaming") ? "#30e5a84b" : "#08ffffff"
                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === "gaming") ? "#E5A84B" : "transparent"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "⚡"; font.pixelSize: 14; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "Game Mode"; font.family: "Inter"; font.pixelSize: 10; font.bold: true; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                }

                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof systemBridge !== "undefined" && systemBridge) {
                            var target = (systemBridge.performanceMode === "gaming") ? "balanced" : "gaming"
                            systemBridge.setPerformanceMode(target)
                        }
                    }
                }
            }

            // Night Light Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.nightLight) ? "#30e5a84b" : "#08ffffff"
                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.nightLight) ? "#E5A84B" : "transparent"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "󰛨"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.nightLight) ? "#E5A84B" : "#9AA1AB"; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "Night Light"; font.family: "Inter"; font.pixelSize: 10; color: "#DDE3EB"; Layout.alignment: Qt.AlignHCenter }
                }

                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof systemBridge !== "undefined" && systemBridge) {
                            systemBridge.toggleNightLight(!systemBridge.nightLight)
                        }
                    }
                }
            }

            // DND Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dnd) ? "#30f7768e" : "#08ffffff"
                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dnd) ? "#F7768E" : "transparent"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "󰂛"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dnd) ? "#F7768E" : "#9AA1AB"; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "DND"; font.family: "Inter"; font.pixelSize: 10; color: "#DDE3EB"; Layout.alignment: Qt.AlignHCenter }
                }

                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof systemBridge !== "undefined" && systemBridge) {
                            systemBridge.toggleDND(!systemBridge.dnd)
                        }
                    }
                }
            }

            // VPN Tile
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                radius: 10
                color: "#08ffffff"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: "󰖂"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#73DACA"; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "VPN Secure"; font.family: "Inter"; font.pixelSize: 10; color: "#DDE3EB"; Layout.alignment: Qt.AlignHCenter }
                }
            }
        }
    }
}
