import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    property string label: ""
    property string value: ""
    property string icon: ""
    property color iconColor: "#9BBD5C"

    Layout.preferredWidth: 180
    Layout.preferredHeight: 100
    color: "#1A1A2E"
    radius: 10
    border.color: "#2A2A3E"
    border.width: 1

    RowLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Rectangle {
            width: 40; height: 40
            radius: 8
            color: iconColor
            Text { anchors.centerIn: parent; text: icon; font.pixelSize: 20; color: "#0B0F1A" }
        }

        ColumnLayout {
            spacing: 2
            Text { text: value; font.pixelSize: 18; font.bold: true; color: "#FFFFFF" }
            Text { text: label; font.pixelSize: 11; color: "#8899AA" }
        }
    }
}
