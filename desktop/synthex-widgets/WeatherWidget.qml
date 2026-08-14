import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 320
    height: 110
    radius: 18
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property string location: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherCity : "Ajmer"
    property string condition: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherCond : "Clouds"
    property string temperature: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherTemp : "34°"
    property string windSpeed: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherWind : "4.49 m/s"
    property string humidity: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherHumidity : "49%"
    property string weatherIcon: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.weatherIcon : "󰖐"

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
                font.pixelSize: 36
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
                color: "#9AA1AB"
            }

            Text {
                text: "And Humidity is " + root.humidity
                font.family: "Inter"
                font.pixelSize: 12
                color: "#9AA1AB"
            }
        }
    }
}
