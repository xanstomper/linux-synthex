import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Reusable Status Card Component
Rectangle {
    property string title: ""
    property string value: ""
    property string icon: ""
    property string color: "#7FBF8A"
    
    width: 140
    height: 100
    radius: 12
    color: "#171D24"
    border.color: "#1E242F"
    border.width: 1
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 6
        
        Text {
            text: icon
            font.pixelSize: 24
        }
        
        Text {
            text: value
            color: "#FFFFFF"
            font.pixelSize: 20
            font.bold: true
        }
        
        Text {
            text: title
            color: "#AAAAAA"
            font.pixelSize: 11
        }
    }
}
