import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Synthex Control Center — Sidebar Navigation Component
Rectangle {
    property int currentIndex: 0
    signal pageSelected(int index, string pageName)
    
    id: sidebar
    width: 180
    color: "#171D24"
    
    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 16
        spacing: 2
        
        // Brand header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: "transparent"
            Text {
                anchors.centerIn: parent
                text: "☀️ Synthex"
                font.pixelSize: 20
                font.bold: true
                color: "#6C88A8"
            }
        }
        
        Item { Layout.preferredHeight: 16 }
        
        // Navigation items
        Repeater {
            model: ListModel {
                ListElement { name: "Dashboard";     icon: "🏠"; page: "dashboard" }
                ListElement { name: "System";        icon: "🖥"; page: "system" }
                ListElement { name: "Performance";   icon: "⚡"; page: "performance" }
                ListElement { name: "Gaming";        icon: "🎮"; page: "gaming" }
                ListElement { name: "Developer";     icon: "💻"; page: "developer" }
                ListElement { name: "Themes";        icon: "🎨"; page: "themes" }
                ListElement { name: "Updates";       icon: "📦"; page: "updates" }
                ListElement { name: "Security";      icon: "🔒"; page: "security" }
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                Layout.leftMargin: 8
                Layout.rightMargin: 8
                radius: 8
                color: sidebar.currentIndex === index ? "#6C88A8" : "transparent"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    spacing: 12
                    Text {
                        text: model.icon
                        font.pixelSize: 16
                    }
                    Text {
                        text: model.name
                        color: sidebar.currentIndex === index ? "#0C1116" : "#FFFFFF"
                        font.pixelSize: 13
                        font.bold: sidebar.currentIndex === index
                    }
                    Item { Layout.fillWidth: true }
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: if (sidebar.currentIndex !== index) color = "#1E242F"
                    onExited: if (sidebar.currentIndex !== index) color = "transparent"
                    onClicked: {
                        sidebar.currentIndex = index
                        sidebar.pageSelected(index, model.page)
                    }
                }
            }
        }
        
        Item { Layout.fillHeight: true }
        
        // Version info
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            color: "transparent"
            Text {
                anchors.centerIn: parent
                text: "Synthex 2026.10"
                color: "#666666"
                font.pixelSize: 10
            }
        }
    }
}
