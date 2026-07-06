import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Snapshots"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "BTRFS Snapshots"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Text { text: "Snapper: configured for root filesystem"; color: textColor; font.pixelSize: 14 }
            Text { text: "Timeshift: hourly snapshots active"; color: textColor; font.pixelSize: 14 }
            Button {
                text: "Create Snapshot"; Layout.fillWidth: true
                palette.buttonText: "#FFFFFF"
                background: Rectangle { color: accentColor; radius: 8 }
                onClicked: console.log("Create snapshot")
            }
        }
        Card {
            Layout.fillWidth: true; title: "Bootloader Integration"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "grub-btrfs: snapshots in GRUB menu"; color: textColor; font.pixelSize: 14 }
            Text { text: "Rollback: one-click from GRUB or Timeshift"; color: mutedText; font.pixelSize: 12 }
        }
    }
}
