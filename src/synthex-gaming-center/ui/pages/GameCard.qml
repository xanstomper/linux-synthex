// Game library card component
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

Rectangle {
    id: card
    width:  200
    height: 280
    radius: 10
    color:  "#111118"
    border.color: hoverArea.containsMouse ? "#FFB300" : "#222233"
    border.width: hoverArea.containsMouse ? 2 : 1
    clip: true

    property string name:       ""
    property string cover:      ""
    property string launcher:   "steam"
    property string playtime:   "0h"
    property string lastPlayed: ""

    // Cover image
    Image {
        id: coverImg
        anchors.top: parent.top
        width: parent.width; height: 190
        source: cover || "qrc:/images/game-placeholder.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
        clip: true

        // Gradient overlay
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 80
            gradient: Gradient {
                GradientStop { position: 0; color: "transparent" }
                GradientStop { position: 1; color: "#111118" }
            }
        }
    }

    // Launcher badge
    Rectangle {
        anchors.top: parent.top; anchors.right: parent.right
        anchors.margins: 6
        width: 28; height: 28; radius: 6
        color: Qt.rgba(0,0,0,0.7)
        Label {
            anchors.centerIn: parent
            text: launcher === "steam" ? "🎮" : launcher === "heroic" ? "⚡" : launcher === "lutris" ? "🍷" : "🕹"
            font.pixelSize: 14
        }
    }

    ColumnLayout {
        anchors.left: parent.left; anchors.right: parent.right
        anchors.top: coverImg.bottom; anchors.bottom: parent.bottom
        anchors.margins: 10; spacing: 4

        Label {
            text: name
            font.bold: true
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        RowLayout {
            spacing: 4
            Label {
                text: "⏱ " + (playtime !== "0h" ? playtime : "Not played")
                font.pixelSize: 10
                color: "#8899AA"
            }
            Item { Layout.fillWidth: true }
        }

        // Play button (shown on hover)
        Button {
            visible: hoverArea.containsMouse
            text: "▶  Play"
            font.bold: true
            font.pixelSize: 12
            Layout.fillWidth: true
            Layout.preferredHeight: 32

            background: Rectangle {
                radius: 6
                color: parent.pressed ? "#CC8800" : "#FFB300"
            }
            contentItem: Text {
                text: parent.text
                color: "#000000"
                font: parent.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment:   Text.AlignVCenter
            }

            onClicked: {
                // Launch via appropriate launcher
                switch(launcher) {
                    case "steam":   Qt.openUrlExternally("steam://rungameid/" + name); break
                    case "heroic":  Qt.openUrlExternally("heroic://launch/" + name);   break
                    case "lutris":  Qt.openUrlExternally("lutris:rungameid/" + name);  break
                    default:        Qt.openUrlExternally(launcher);                    break
                }
            }
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.RightButton | Qt.LeftButton

        // Context menu
        onClicked: if (mouse.button === Qt.RightButton) contextMenu.popup()
    }

    Menu {
        id: contextMenu
        MenuItem { text: "▶  Play";          onTriggered: {} }
        MenuItem { text: "⚙  Manage";        onTriggered: {} }
        MenuItem { text: "📊  Performance";  onTriggered: {} }
        MenuItem { text: "🗂  Show in files"; onTriggered: {} }
        MenuSeparator {}
        MenuItem { text: "🗑  Remove from library"; onTriggered: {} }
    }

    Behavior on border.color { ColorAnimation { duration: 120 } }
    Behavior on scale { NumberAnimation { duration: 100 } }
    states: State { when: hoverArea.containsMouse; PropertyChanges { target: card; scale: 1.02 } }
}
