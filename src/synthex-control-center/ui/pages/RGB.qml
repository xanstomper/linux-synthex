import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "RGB & Peripherals"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "RGB Devices"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "OpenRGB: daemon managed"; color: textColor; font.pixelSize: 14 }
            Text { text: "Piper (Razer): configure mouse macros"; color: mutedText; font.pixelSize: 12 }
            Text { text: "Solaar (Logitech): manage peripherals"; color: mutedText; font.pixelSize: 12 }
        }
        Card {
            Layout.fillWidth: true; title: "Controllers"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "xpadneo (Xbox): installed"; color: textColor; font.pixelSize: 14 }
            Text { text: "DualSense / DualShock: supported"; color: textColor; font.pixelSize: 14 }
            Text { text: "Nintendo Pro / Switch controllers: supported"; color: mutedText; font.pixelSize: 12 }
        }
    }
}
