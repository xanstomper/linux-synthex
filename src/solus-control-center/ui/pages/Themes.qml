import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Appearance"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card { Layout.fillWidth: true; title: "Theme"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Repeater {
                model: [
                    { label: "Light", id: "light" },
                    { label: "Dark", id: "dark" },
                    { label: "Mint", id: "mint" }
                ]
                delegate: ModeToggle { label: modelData.label; icon: ""; active: modelData.id === "dark" }
            }
        }
        Card { Layout.fillWidth: true; title: "Accent Color"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Repeater {
                model: ["#9BBD5C", "#FFB300", "#1E88E5", "#E53935", "#8E24AA"]
                delegate: Rectangle {
                    width: 36; height: 36; radius: 18; color: modelData
                    border.color: modelData === "#9BBD5C" ? "#FFFFFF" : "transparent"; border.width: 2
                }
            }
        }
    }
}
