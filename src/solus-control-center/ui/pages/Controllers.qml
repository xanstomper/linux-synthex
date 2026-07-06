import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Controllers"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "Gamepads"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Xbox (xpadneo): connected"; color: textColor; font.pixelSize: 14 }
            Text { text: "DualSense / DualShock 4: supported via hid-playstation"; color: textColor; font.pixelSize: 14 }
            Text { text: "Nintendo Switch Pro: supported"; color: textColor; font.pixelSize: 14 }
            Text { text: "steam-devices udev rules: active"; color: mutedText; font.pixelSize: 12 }
        }
        Card {
            Layout.fillWidth: true; title: "Input Remapping"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Input Remapper: re-map any controller/joystick"; color: textColor; font.pixelSize: 14 }
            Text { text: "AntiMicroX / sc-controller: available via OOBE bundle"; color: mutedText; font.pixelSize: 12 }
        }
    }
}
