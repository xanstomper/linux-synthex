import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 480
    height: 560
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.surfaceColor : "#141923"
    border.color: "#1fffffff"
    border.width: 1

    signal closeRequested()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // ── Header ─────────────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "󰒓  Rice & Desktop Customizer"
                font.family: "Inter"
                font.pixelSize: 16
                font.bold: true
                color: "#FFFFFF"
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                width: 28
                height: 28
                radius: 14
                color: "#0fffffff"

                Text {
                    text: "✕"
                    font.pixelSize: 12
                    color: "#9AA1AB"
                    anchors.centerIn: parent
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.closeRequested()
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#0fffffff"
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: root.width - 40
                spacing: 18

                // ── 1. Preset Themes ───────────────────────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "THEME PRESETS"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                    }

                    GridLayout {
                        columns: 3
                        rowSpacing: 8
                        columnSpacing: 8
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "nova", name: "Nova Dark", color: "#141923", accent: "#7AA2F7" },
                                { key: "tokyonight", name: "Tokyo Night", color: "#1A1B26", accent: "#7AA2F7" },
                                { key: "catppuccin", name: "Catppuccin", color: "#1E1E2E", accent: "#89B4FA" },
                                { key: "nord", name: "Nord Frost", color: "#2E3440", accent: "#88C0D0" },
                                { key: "cyberpunk", name: "Cyberpunk", color: "#0D0D18", accent: "#00F0FF" },
                                { key: "oled", name: "OLED Midnight", color: "#0A0A0A", accent: "#60A5FA" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                radius: 8
                                color: modelData.color
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? modelData.accent : "#1fffffff"
                                border.width: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? 2 : 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 8

                                    Rectangle {
                                        width: 12
                                        height: 12
                                        radius: 6
                                        color: modelData.accent
                                    }

                                    Text {
                                        text: modelData.name
                                        font.family: "Inter"
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: "#FFFFFF"
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) {
                                            systemBridge.setTheme(modelData.key)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ── 2. Accent Color Palette ────────────────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "ACCENT COLOR"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                    }

                    RowLayout {
                        spacing: 12

                        Repeater {
                            model: ["#7AA2F7", "#BB9AF7", "#73DACA", "#E5A84B", "#F7768E", "#9ECE6A", "#00F0FF", "#FF9E64"]

                            Rectangle {
                                width: 28
                                height: 28
                                radius: 14
                                color: modelData
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.accentColor === modelData) ? "#FFFFFF" : "transparent"
                                border.width: 2

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) {
                                            systemBridge.setAccentColor(modelData)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ── 3. Widget Visibility Toggles ───────────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "DESKTOP WIDGETS"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                    }

                    GridLayout {
                        columns: 2
                        rowSpacing: 8
                        columnSpacing: 12
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "clock", name: "Clock Widget" },
                                { key: "weather", name: "Weather Widget" },
                                { key: "quickSettings", name: "Quick Settings" },
                                { key: "mediaPlayer", name: "Media Center" },
                                { key: "systemMonitor", name: "System Monitor" },
                                { key: "terminalRice", name: "Terminal Rice" },
                                { key: "dock", name: "Floating Dock" },
                                { key: "topPill", name: "Top Status Pill" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                radius: 8
                                color: "#08ffffff"
                                border.color: "#0fffffff"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10

                                    Text {
                                        text: modelData.name
                                        font.family: "Inter"
                                        font.pixelSize: 12
                                        color: "#FFFFFF"
                                        Layout.fillWidth: true
                                    }

                                    Rectangle {
                                        width: 18
                                        height: 18
                                        radius: 4
                                        color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key]) ? systemBridge.accentColor : "#1E2633"

                                        Text {
                                            text: "✔"
                                            font.pixelSize: 10
                                            color: "#FFFFFF"
                                            anchors.centerIn: parent
                                            visible: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key])
                                        }
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) {
                                            var cur = systemBridge.widgetsConfig ? systemBridge.widgetsConfig[modelData.key] : true
                                            systemBridge.toggleWidget(modelData.key, !cur)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ── 4. Corner Radius & Card Opacity ────────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: "GEOMETRY & TRANSPARENCY"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Corner Radius: " + ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18) + "px"; font.family: "Inter"; font.pixelSize: 12; color: "#9AA1AB"; Layout.preferredWidth: 150 }
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 8; radius: 4; color: "#1E2633"
                            Rectangle {
                                width: parent.width * (((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18) / 32.0)
                                height: parent.height; radius: 4; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                            }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var r = Math.round((mouse.x / width) * 32)
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setCornerRadius(r)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
