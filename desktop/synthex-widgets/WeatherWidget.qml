import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 320
    height: 110
    radius: 18
    color: "#141923"
    border.color: "rgba(255, 255, 255, 0.08)"
    border.width: 1

    property string location: "Ajmer"
    property string condition: "Clouds"
    property string temperature: "34°"
    property string windSpeed: "4.49 m/s"
    property string humidity: "49%"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // Weather Icon & Temp
        RowLayout {
            spacing: 8
            Layout.alignment: Qt.AlignVCenter

            // Cloud with sun icon representation
            Item {
                width: 44
                height: 44
                Layout.alignment: Qt.AlignVCenter

                // Sun glow
                Rectangle {
                    width: 22
                    height: 22
                    radius: 11
                    color: "#E5A84B"
                    x: 20
                    y: 2
                }

                // Cloud body
                Rectangle {
                    width: 36
                    height: 24
                    radius: 12
                    color: "#DDE3EB"
                    x: 2
                    y: 16
                }
                Rectangle {
                    width: 20
                    height: 20
                    radius: 10
                    color: "#DDE3EB"
                    x: 10
                    y: 8
                }
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
