import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    property alias title: titleText.text
    property alias content: contentCol
    color: "#1A1A2E"
    radius: 12
    border.color: "#2A2A3E"
    border.width: 1

    ColumnLayout {
        id: contentCol
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        Text {
            id: titleText
            font.pixelSize: 16
            font.bold: true
            color: "#FFFFFF"
        }
    }
}
