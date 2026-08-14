import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#6C88A8"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"
    readonly property color okColor: "#7FBF8A"
    readonly property color warnColor: "#D9B47E"
    readonly property color surfaceColor: "#171D24"

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        RowLayout {
            Layout.fillWidth: true
            Text { text: "Driver Manager"; font.pixelSize: 24; font.bold: true; color: textColor; Layout.fillWidth: true }
            Button {
                text: "🔍 Scan Hardware"
                background: Rectangle { color: accentColor; radius: 8 }
                contentItem: Text { text: parent.text; color: "#0C1116"; font.pixelSize: 13; font.bold: true }
            }
        }

        // GPU section
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12
                Text { text: "🖥️ GPU Drivers"; font.pixelSize: 16; font.bold: true; color: textColor }
                Repeater {
                    model: ListModel {
                        ListElement { vendor: "NVIDIA"; driver: "nvidia-560.70"; status: "active"; vulkan: true; openSource: false }
                    }
                    delegate: Rectangle { Layout.fillWidth: true; height: 80; color: "#121624"; radius: 8
                        RowLayout { anchors.fill: parent; anchors.margins: 12; spacing: 16
                            Rectangle { width: 48; height: 48; radius: 8; color: "#1E88E5"
                                Text { anchors.centerIn: parent; text: "🎮"; font.pixelSize: 24 }
                            }
                            ColumnLayout { spacing: 4
                                Text { text: modelData.vendor + " — " + modelData.driver; font.pixelSize: 14; font.bold: true; color: textColor }
                                Text { text: "Vulkan: ✓  |  Open Source: " + (modelData.openSource ? "Yes" : "No") + "  |  Status: " + modelData.status; font.pixelSize: 11; color: mutedText }
                            }
                            Item { Layout.fillWidth: true }
                            Button { text: "Reinstall"; background: Rectangle { color: "#12FFFFFF"; radius: 6 }
                                contentItem: Text { text: parent.text; color: textColor; font.pixelSize: 12 }
                            }
                            Button { text: "Switch"; background: Rectangle { color: "#1E88E5"; radius: 6 }
                                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 12 }
                            }
                        }
                    }
                }
            }
        }

        // Other hardware
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "📡 Other Hardware"; font.pixelSize: 16; font.bold: true; color: textColor }
                Repeater {
                    model: [
                        { name: "Wi-Fi (Intel AX210)", driver: "iwlwifi", status: "active" },
                        { name: "Bluetooth (Intel AX210)", driver: "btintel", status: "active" },
                        { name: "Audio (Realtek ALC1220)", driver: "snd-hda-intel", status: "active" },
                        { name: "Printer (HP LaserJet)", driver: "hplip", status: "active" }
                    ]
                    RowLayout { Layout.fillWidth: true; spacing: 12
                        Rectangle { width: 8; height: 8; radius: 4; color: okColor }
                        Text { text: modelData.name; font.pixelSize: 13; color: textColor; Layout.fillWidth: true }
                        Text { text: modelData.driver; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 120 }
                        Rectangle { width: 50; height: 18; radius: 9; color: okColor
                            Text { anchors.centerIn: parent; text: "OK"; font.pixelSize: 9; font.bold: true; color: "#FFFFFF" }
                        }
                    }
                }
            }
        }

        // Firmware
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "📦 Firmware"; font.pixelSize: 16; font.bold: true; color: textColor }
                RowLayout { spacing: 16
                    Text { text: "linux-firmware: up to date"; font.pixelSize: 12; color: okColor }
                    Text { text: "NVIDIA firmware: v560.70"; font.pixelSize: 12; color: mutedText }
                    Button { text: "Update All Firmware"; background: Rectangle { color: accentColor; radius: 6 }
                        contentItem: Text { text: parent.text; color: "#0C1116"; font.pixelSize: 12; font.bold: true }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
