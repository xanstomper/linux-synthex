import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: aboutPage
    anchors.fill: parent

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color cardBg: "#161C24"
    readonly property color itemBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    ScrollView {
        anchors.fill: parent
        anchors.margins: 28
        clip: true

        ColumnLayout {
            width: aboutPage.width - 56
            spacing: 22

            // Header Banner Card
            Rectangle {
                Layout.fillWidth: true
                height: 120
                radius: 12
                color: "#18202c"
                border.color: "#25ffffff"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20

                    Rectangle {
                        width: 60; height: 60; radius: 14
                        color: aboutPage.accentColor
                        Text { text: "󰌽"; font.family: "Symbols Nerd Font"; font.pixelSize: 32; color: "#0C1116"; anchors.centerIn: parent }
                    }

                    ColumnLayout {
                        spacing: 2
                        Text { text: "SynthOS Linux 2026.10 LTS"; font.family: "Inter"; font.pixelSize: 22; font.bold: true; color: "#FFFFFF" }
                        Text { text: "High-Performance Modern Linux Operating System"; font.family: "Inter"; font.pixelSize: 13; color: aboutPage.mutedText }
                        Text { text: "Kernel: Linux 6.13.0-cachyos-gaming • Arch: x86_64"; font.family: "Inter"; font.pixelSize: 11; color: aboutPage.accentColor }
                    }
                }
            }

            // Hardware Specification Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: aboutPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: hwCol.implicitHeight + 32

                ColumnLayout {
                    id: hwCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Text { text: "HARDWARE SPECIFICATIONS"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: aboutPage.accentColor }

                    GridLayout {
                        columns: 2
                        rowSpacing: 14
                        columnSpacing: 20
                        Layout.fillWidth: true

                        // Processor
                        RowLayout {
                            spacing: 12
                            Text { text: "󰍛"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: aboutPage.accentColor }
                            ColumnLayout {
                                spacing: 1
                                Text { text: "Processor"; font.family: "Inter"; font.pixelSize: 11; color: aboutPage.mutedText }
                                Text { text: "AMD Ryzen 9 / Intel Core Ultra (x86_64)"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            }
                        }

                        // Memory
                        RowLayout {
                            spacing: 12
                            Text { text: "󰘚"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: aboutPage.accentColor }
                            ColumnLayout {
                                spacing: 1
                                Text { text: "Memory (RAM)"; font.family: "Inter"; font.pixelSize: 11; color: aboutPage.mutedText }
                                Text { text: "32.0 GB High-Speed DDR5"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            }
                        }

                        // Graphics
                        RowLayout {
                            spacing: 12
                            Text { text: "󰢮"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: aboutPage.accentColor }
                            ColumnLayout {
                                spacing: 1
                                Text { text: "Graphics Processor"; font.family: "Inter"; font.pixelSize: 11; color: aboutPage.mutedText }
                                Text { text: "NVIDIA GeForce RTX 4080 (Driver 570.86)"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            }
                        }

                        // Storage
                        RowLayout {
                            spacing: 12
                            Text { text: "󰋊"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: aboutPage.accentColor }
                            ColumnLayout {
                                spacing: 1
                                Text { text: "System Drive"; font.family: "Inter"; font.pixelSize: 11; color: aboutPage.mutedText }
                                Text { text: "2.0 TB NVMe PCIe 4.0 (Btrfs Rootfs)"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            }
                        }
                    }
                }
            }
        }
    }
}
