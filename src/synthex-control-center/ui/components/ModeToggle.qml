import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Mode Toggle Button Component
Rectangle {
    property string label: ""
    property string icon: ""
    property bool active: false
    signal clicked()
    
    width: 130
    height: 60
    radius: 10
    color: active ? "#6C88A8" : "#171D24"
    border.color: active ? "#6C88A8" : "#1E242F"
    border.width: active ? 2 : 1
    
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 4
        Text {
            text: icon
            font.pixelSize: 22
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            text: label
            color: active ? "#0C1116" : "#FFFFFF"
            font.pixelSize: 11
            font.bold: active
            Layout.alignment: Qt.AlignHCenter
        }
    }
    
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: if (!active) parent.color = "#1E242F"
        onExited: if (!active) parent.color = "#171D24"
        onClicked: parent.clicked()
    }
}
