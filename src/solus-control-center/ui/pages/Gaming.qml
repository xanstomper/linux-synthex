import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"
    readonly property color okColor: "#43A047"; readonly property color warnColor: "#FB8C00"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Gaming"; font.pixelSize: 24; font.bold: true; color: textColor }
        GridLayout {
            Layout.fillWidth: true; columns: 3; rowSpacing: 12; columnSpacing: 14
            StatCard { label: "Steam"; value: "Ready"; icon: "🎮"; iconColor: okColor }
            StatCard { label: "Proton-GE"; value: "Latest"; icon: "🍺"; iconColor: okColor }
            StatCard { label: "GameMode"; value: "Active"; icon: "🎯"; iconColor: okColor }
            StatCard { label: "MangoHUD"; value: "Installed"; icon: "📊"; iconColor: okColor }
            StatCard { label: "Gamescope"; value: "Installed"; icon: "🔭"; iconColor: okColor }
            StatCard { label: "DXVK"; value: "Installed"; icon: "💿"; iconColor: okColor }
        }
        Card {
            Layout.fillWidth: true; title: "Launchers"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Repeater {
                model: [
                    { name: "Steam", icon: "🎮" },
                    { name: "Heroic", icon: "🦸" },
                    { name: "Lutris", icon: "🏹" },
                    { name: "Bottles", icon: "🍾" }
                ]
                delegate: Rectangle {
                    width: 120; height: 44; radius: 8; color: "#2A2A3E"
                    RowLayout { anchors.centerIn: parent; spacing: 8 }
                    Text { text: modelData.icon; font.pixelSize: 18 }
                    Text { text: modelData.name; color: textColor; font.pixelSize: 13 }
                }
            }
        }
        Card {
            Layout.fillWidth: true; title: "Quick Actions"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Button { text: "Launch Steam"; palette.buttonText: textColor; background: Rectangle { color: accentColor; radius: 8 } }
            Button { text: "ProtonUp-Qt"; palette.buttonText: textColor; background: Rectangle { color: "#1E88E5"; radius: 8 } }
        }
    }
}
