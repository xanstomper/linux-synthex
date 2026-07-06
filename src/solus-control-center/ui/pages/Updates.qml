import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Updates"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "System Updates"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Text { text: "Last update: today"; color: textColor; font.pixelSize: 14 }
            Text { text: "DNF5 + RPM-OSTree-compatible update stack"; color: mutedText; font.pixelSize: 12 }
            Button {
                text: "Update System"; Layout.fillWidth: true
                palette.buttonText: "#FFFFFF"
                background: Rectangle { color: accentColor; radius: 8 }
                onClicked: console.log("Update triggered")
            }
        }
        Card {
            Layout.fillWidth: true; title: "Flatpak Updates"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Text { text: "Flatpak apps auto-update from Flathub"; color: textColor; font.pixelSize: 14 }
            Button {
                text: "Update Flatpaks"; Layout.fillWidth: true
                palette.buttonText: "#FFFFFF"
                background: Rectangle { color: "#1E88E5"; radius: 8 }
                onClicked: console.log("Flatpak update triggered")
            }
        }
    }
}
