import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Developer Tools"; font.pixelSize: 24; font.bold: true; color: textColor }
        GridLayout {
            Layout.fillWidth: true; columns: 3; rowSpacing: 12; columnSpacing: 14
            StatCard { label: "Git"; value: "Installed"; icon: "📦"; iconColor: "#F05032" }
            StatCard { label: "Python"; value: "3.x"; icon: "🐍"; iconColor: "#3776AB" }
            StatCard { label: "Rust"; value: "Installed"; icon: "🦀"; iconColor: "#DEA584" }
            StatCard { label: "Go"; value: "Installed"; icon: "🔵"; iconColor: "#00ADD8" }
            StatCard { label: "Podman"; value: "Ready"; icon: "🐳"; iconColor: "#6A0DAD" }
            StatCard { label: "Distrobox"; value: "Ready"; icon: "📦"; iconColor: accentColor }
        }
        Card {
            Layout.fillWidth: true; title: "Containers"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Podman + Distrobox installed"; color: textColor; font.pixelSize: 14 }
            Text { text: "Run distrobox-create to spin up containers"; color: mutedText; font.pixelSize: 12 }
        }
    }
}
