import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 250
    height: 112
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: "#a612161f" // Translucent liquid glass base
    border.color: "#28ffffff"
    border.width: 1

    property string currentTime: (typeof systemBridge !== "undefined" && systemBridge) ? (new Date().toLocaleTimeString(Qt.locale(), "hh:mm")) : "04:44"
    property string ampm: (typeof systemBridge !== "undefined" && systemBridge) ? (new Date().toLocaleTimeString(Qt.locale(), "AP")) : "PM"
    property string currentDate: (typeof systemBridge !== "undefined" && systemBridge) ? (new Date().toLocaleDateString(Qt.locale(), "ddd, dd MMMM yyyy")) : "Tue, 09 August 2022"

    // Liquid Glass Specular Top Highlight
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22ffffff" }
            GradientStop { position: 0.08; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            var d = new Date()
            root.currentTime = d.toLocaleTimeString(Qt.locale(), "hh:mm")
            root.ampm = d.toLocaleTimeString(Qt.locale(), "AP")
            root.currentDate = d.toLocaleDateString(Qt.locale(), "ddd, dd MMMM yyyy")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 2

        RowLayout {
            spacing: 6
            Layout.alignment: Qt.AlignLeft

            Text {
                text: root.currentTime
                font.family: "Inter"
                font.pixelSize: 40
                font.bold: true
                color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                style: Text.Raised
                styleColor: "#40000000"
            }

            Text {
                text: root.ampm
                font.family: "Inter"
                font.pixelSize: 15
                font.bold: true
                color: "#6C88A8"
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 8
            }
        }

        Text {
            text: root.currentDate
            font.family: "Inter"
            font.pixelSize: 13
            font.weight: Font.Medium
            color: "#A0AAB8"
        }
    }

    // Elastic Gooey Hover Interaction
    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }

    scale: hoverArea.pressed ? 0.97 : (hoverArea.containsMouse ? 1.025 : 1.0)
    Behavior on scale {
        NumberAnimation {
            duration: 250
            easing.type: Easing.OutBack
            easing.overshoot: 1.3
        }
    }
}
