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

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        Text { text: "Kernel Manager"; font.pixelSize: 24; font.bold: true; color: textColor }

        // Current kernel info
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: accentColor; border.width: 2
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "▶ Running Kernel"; font.pixelSize: 16; font.bold: true; color: accentColor }
                GridLayout { columns: 4; columnSpacing: 24
                    Text { text: "Version:"; color: mutedText; font.pixelSize: 12 }
                    Text { text: "6.14.6-300.fc42.x86_64"; color: textColor; font.pixelSize: 12; font.bold: true }
                    Text { text: "Scheduler:"; color: mutedText; font.pixelSize: 12 }
                    Text { text: "BORE (EEVDF)"; color: okColor; font.pixelSize: 12; font.bold: true }
                    Text { text: "Arch:"; color: mutedText; font.pixelSize: 12 }
                    Text { text: "x86_64"; color: textColor; font.pixelSize: 12 }
                    Text { text: "Compiler:"; color: mutedText; font.pixelSize: 12 }
                    Text { text: "GCC 14.2"; color: textColor; font.pixelSize: 12 }
                }
            }
        }

        // Available kernels
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "📦 Installed Kernels"; font.pixelSize: 16; font.bold: true; color: textColor }
                Repeater {
                    model: ListModel {
                        ListElement { ver: "6.14.6-300.fc42"; label: "Stable + BORE"; active: true }
                        ListElement { ver: "6.14.4-200.fc42"; label: "Previous stable"; active: false }
                        ListElement { ver: "6.12.10-200.fc42"; label: "LTS"; active: false }
                    }
                    Rectangle { Layout.fillWidth: true; height: 56; color: modelData.active ? "#1A2E1A" : "#121624"; radius: 8
                        RowLayout { anchors.fill: parent; anchors.margins: 12; spacing: 12
                            Rectangle { width: 8; height: 8; radius: 4; color: modelData.active ? accentColor : "#555" }
                            ColumnLayout { spacing: 2
                                Text { text: modelData.ver; font.pixelSize: 13; font.bold: true; color: textColor }
                                Text { text: modelData.label; font.pixelSize: 11; color: mutedText }
                            }
                            Item { Layout.fillWidth: true }
                            Text { text: modelData.active ? "▶ RUNNING" : ""; font.pixelSize: 11; font.bold: true; color: accentColor }
                            Button { visible: !modelData.active; text: "Boot"; background: Rectangle { color: "#2A2A3E"; radius: 6 }
                                contentItem: Text { text: parent.text; color: textColor; font.pixelSize: 11 }
                            }
                            Button { visible: !modelData.active; text: "Remove"; background: Rectangle { color: dangerColor; radius: 6 }
                                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 11 }
                            }
                        }
                    }
                }
            }
        }

        // Available to install
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "📥 Available to Install"; font.pixelSize: 16; font.bold: true; color: textColor }
                Repeater {
                    model: [
                        { ver: "kernel-zen", label: "Linux Zen (CachyOS performance)" },
                        { ver: "kernel-rt", label: "Real-Time (low latency)" },
                        { ver: "kernel-ml", label: "Mainline (bleeding edge)" }
                    ]
                    RowLayout { Layout.fillWidth: true; spacing: 12
                        Text { text: "📦"; font.pixelSize: 16 }
                        ColumnLayout { spacing: 2; Layout.fillWidth: true
                            Text { text: modelData.ver; font.pixelSize: 13; font.bold: true; color: textColor }
                            Text { text: modelData.label; font.pixelSize: 11; color: mutedText }
                        }
                        Button { text: "Install"; background: Rectangle { color: accentColor; radius: 6 }
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 11; font.bold: true }
                        }
                    }
                }
            }
        }

        // Actions
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Button { text: "Cleanup Old Kernels"; Layout.fillWidth: true; background: Rectangle { color: warnColor; radius: 8 }
                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 13 }
            }
            Button { text: "Rebuild initramfs"; Layout.fillWidth: true; background: Rectangle { color: "#1E88E5"; radius: 8 }
                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 13 }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
