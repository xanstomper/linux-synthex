import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"
    readonly property color okColor: "#43A047"
    readonly property color warnColor: "#FB8C00"
    readonly property color surfaceColor: "#1A1A2E"
    property int activeMode: 1

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        Text { text: "Performance"; font.pixelSize: 24; font.bold: true; color: textColor }

        // Performance modes
        Text { text: "Performance Profiles"; font.pixelSize: 16; font.bold: true; color: textColor }
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Repeater {
                model: [
                    { name: "Gaming", icon: "🎮", desc: "Max performance, VRR, GameMode", color: dangerColor },
                    { name: "Balanced", icon: "⚖️", desc: "Smart defaults, power-aware", color: accentColor },
                    { name: "Battery", icon: "🔋", desc: "Extended battery, powersave", color: "#1E88E5" },
                    { name: "Creator", icon: "🎨", desc: "Rendering, encoding, compilation", color: "#9B59B6" }
                ]
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 70; radius: 10
                    color: index === activeMode ? Qt.rgba(0.608,0.741,0.361,0.1) : surfaceColor
                    border.color: index === activeMode ? accentColor : "#2A2A3E"; border.width: index === activeMode ? 2 : 1
                    MouseArea { anchors.fill: parent; onClicked: activeMode = index; cursorShape: Qt.PointingHandCursor }
                    RowLayout { anchors.centerIn: parent; spacing: 12
                        Text { text: modelData.icon; font.pixelSize: 22 }
                        ColumnLayout { spacing: 2
                            Text { text: modelData.name; font.pixelSize: 14; font.bold: true; color: textColor }
                            Text { text: modelData.desc; font.pixelSize: 11; color: mutedText }
                        }
                    }
                }
            }
        }

        // Hardware tuning details
        RowLayout {
            Layout.fillWidth: true; spacing: 16

            Rectangle {
                Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                    Text { text: "⚡ CPU"; font.pixelSize: 14; font.bold: true; color: textColor }
                    GridLayout { columns: 2; columnSpacing: 24
                        Text { text: "Governor:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "performance"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Scheduler:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "BORE (EEVDF)"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Energy Pref:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "performance"; color: okColor; font.pixelSize: 12; font.bold: true }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                    Text { text: "🧠 Memory"; font.pixelSize: 14; font.bold: true; color: textColor }
                    GridLayout { columns: 2; columnSpacing: 24
                        Text { text: "ZRAM:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "Enabled (lz4)"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Swappiness:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "10 (low)"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Huge Pages:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "Transparent"; color: okColor; font.pixelSize: 12; font.bold: true }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                    Text { text: "🎮 Gaming"; font.pixelSize: 14; font.bold: true; color: textColor }
                    GridLayout { columns: 2; columnSpacing: 24
                        Text { text: "GameMode:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "Active"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Gamescope:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "Ready"; color: okColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "VRR:"; color: mutedText; font.pixelSize: 12 }
                        Text { text: "Auto"; color: okColor; font.pixelSize: 12; font.bold: true }
                    }
                }
            }
        }

        // I/O and power
        RowLayout {
            Layout.fillWidth: true; spacing: 16
            Rectangle {
                Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16
                    Text { text: "💾 I/O Scheduler"; font.pixelSize: 14; font.bold: true; color: textColor }
                    Text { text: "mq-deadline (NVMe) / bfq (HDD)"; font.pixelSize: 12; color: okColor }
                }
            }
            Rectangle {
                Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16
                    Text { text: "🔋 TDP"; font.pixelSize: 14; font.bold: true; color: textColor }
                    Text { text: "65W (auto-managed)"; font.pixelSize: 12; color: okColor }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
