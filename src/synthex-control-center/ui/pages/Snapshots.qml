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
    readonly property color dangerColor: "#D97C82"
    readonly property color surfaceColor: "#171D24"

    property var snapshots: []
    property int selectedSnapshot: -1

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        RowLayout {
            Layout.fillWidth: true
            Text { text: "Snapshots & Recovery"; font.pixelSize: 24; font.bold: true; color: textColor; Layout.fillWidth: true }
            Button {
                text: "+ Create Snapshot"
                background: Rectangle { color: accentColor; radius: 8 }
                contentItem: Text { text: parent.text; color: "#0C1116"; font.pixelSize: 13; font.bold: true }
            }
        }

        // Status row
        RowLayout {
            Layout.fillWidth: true; spacing: 16
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80
                color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 12
                    Text { text: "Btrfs Snapshots"; font.pixelSize: 12; color: mutedText }
                    Text { text: "Auto: Hourly"; font.pixelSize: 18; font.bold: true; color: okColor }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80
                color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 12
                    Text { text: "Compression"; font.pixelSize: 12; color: mutedText }
                    Text { text: "zstd"; font.pixelSize: 18; font.bold: true; color: okColor }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80
                color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 12
                    Text { text: "GRUB Integration"; font.pixelSize: 12; color: mutedText }
                    Text { text: "grub-btrfs active"; font.pixelSize: 18; font.bold: true; color: okColor }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80
                color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 12
                    Text { text: "Disk Usage"; font.pixelSize: 12; color: mutedText }
                    Text { text: "2.3 GB"; font.pixelSize: 18; font.bold: true; color: warnColor }
                }
            }
        }

        // Safety features
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                Text { text: "🛡️ Safety Features"; font.pixelSize: 16; font.bold: true; color: textColor }
                GridLayout { columns: 3; columnSpacing: 24
                    Text { text: "✅ Pre-update snapshots"; color: okColor; font.pixelSize: 13 }
                    Text { text: "✅ Boot verification"; color: okColor; font.pixelSize: 13 }
                    Text { text: "✅ One-click rollback"; color: okColor; font.pixelSize: 13 }
                    Text { text: "✅ GRUB menu entries"; color: okColor; font.pixelSize: 13 }
                    Text { text: "✅ Automatic cleanup"; color: okColor; font.pixelSize: 13 }
                    Text { text: "✅ Initramfs rebuild"; color: okColor; font.pixelSize: 13 }
                }
            }
        }

        // Snapshot list
        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true
            color: surfaceColor; radius: 12; border.color: "#12FFFFFF"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12
                Text { text: "Recent Snapshots"; font.pixelSize: 16; font.bold: true; color: textColor }

                // Header
                RowLayout { Layout.fillWidth: true
                    Text { text: "#"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 40 }
                    Text { text: "Date"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 160 }
                    Text { text: "Type"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 80 }
                    Text { text: "Description"; font.pixelSize: 11; color: mutedText; Layout.fillWidth: true }
                    Text { text: "Action"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 80 }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#12FFFFFF" }

                Repeater {
                    model: ListModel {
                        ListElement { num: "42"; date: "2026-07-06 05:00"; type: "pre-update"; desc: "Before system update" }
                        ListElement { num: "41"; date: "2026-07-06 04:00"; type: "hourly"; desc: "Automatic hourly snapshot" }
                        ListElement { num: "40"; date: "2026-07-06 03:00"; type: "hourly"; desc: "Automatic hourly snapshot" }
                        ListElement { num: "39"; date: "2026-07-05 22:30"; type: "manual"; desc: "Before driver update" }
                        ListElement { num: "38"; date: "2026-07-05 18:00"; type: "pre-update"; desc: "Before system update" }
                        ListElement { num: "37"; date: "2026-07-05 12:00"; type: "boot"; desc: "Boot verification snapshot" }
                    }
                    delegate: RowLayout {
                        Layout.fillWidth: true; height: 36
                        Text { text: model.num; font.pixelSize: 12; color: textColor; Layout.preferredWidth: 40 }
                        Text { text: model.date; font.pixelSize: 12; color: mutedText; Layout.preferredWidth: 160 }
                        Rectangle {
                            Layout.preferredWidth: 80; height: 20; radius: 4
                            color: model.type === "manual" ? "#1E88E5" : model.type === "pre-update" ? "#D9B47E" : "#12FFFFFF"
                            Text { anchors.centerIn: parent; text: model.type; font.pixelSize: 10; color: "#FFFFFF" }
                        }
                        Text { text: model.desc; font.pixelSize: 12; color: textColor; Layout.fillWidth: true }
                        Button {
                            text: "Restore"; Layout.preferredWidth: 70
                            background: Rectangle { color: dangerColor; radius: 4 }
                            contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 11 }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
