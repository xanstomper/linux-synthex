import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 320
    height: 112
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: "#a612161f" // Translucent liquid glass
    border.color: "#28ffffff"
    border.width: 1

    property string location: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherCity : "Ajmer"
    property string condition: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherCond : "Clouds"
    property string temperature: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherTemp : "34°"
    property string windSpeed: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherWind : "4.49 m/s"
    property string humidity: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherHumidity : "49%"
    property string weatherIcon: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherIcon : "󰖐"

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

    RowLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // Weather Icon & Temp
        RowLayout {
            spacing: 10
            Layout.alignment: Qt.AlignVCenter

            Text {
                text: root.weatherIcon
                font.family: "Symbols Nerd Font"
                font.pixelSize: 38
                color: "#E5A84B"
                Layout.alignment: Qt.AlignVCenter
            }

            Text {
                text: root.temperature
                font.family: "Inter"
                font.pixelSize: 34
                font.bold: true
                color: "#FFFFFF"
                Layout.alignment: Qt.AlignVCenter
                style: Text.Raised
                styleColor: "#40000000"
            }
        }

        // Details
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 3

            Text {
                text: root.location + " is now " + root.condition + "."
                font.family: "Inter"
                font.pixelSize: 13
                font.bold: true
                color: "#FFFFFF"
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: "Wind speed is " + root.windSpeed
                font.family: "Inter"
                font.pixelSize: 12
                color: "#A0AAB8"
            }

            Text {
                text: "And Humidity is " + root.humidity
                font.family: "Inter"
                font.pixelSize: 12
                color: "#A0AAB8"
            }
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
