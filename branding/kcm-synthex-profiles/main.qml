// Synthex Desktop Profile Switcher — KCM Module
// Integrates with KDE System Settings

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kcm 1.2

SimpleKCM {
    title: "Synthex Desktop Profiles"
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        
        Label {
            text: "Choose your desktop experience"
            font.pixelSize: 18
            font.bold: true
        }
        
        GridLayout {
            columns: 4
            columnSpacing: 12
            rowSpacing: 12
            
            Repeater {
                model: [
                    { name: "Focus", desc: "Minimal & keyboard-driven" },
                    { name: "Gaming", desc: "Console-like experience" },
                    { name: "Pro", desc: "Developer cockpit" },
                    { name: "Touch", desc: "Tablet & handheld" },
                    { name: "Classic", desc: "Windows-style" },
                    { name: "Lite", desc: "Old hardware" },
                    { name: "Studio", desc: "Content creator" },
                    { name: "AI", desc: "AI-first desktop" }
                ]
                
                delegate: Button {
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 100
                    
                    contentItem: ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        Text { text: modelData.name; font.bold: true; font.pixelSize: 14 }
                        Text { text: modelData.desc; font.pixelSize: 10; opacity: 0.7 }
                    }
                    
                    onClicked: {
                        // Apply profile via D-Bus
                        var cmd = "synthex-desktop apply " + modelData.name.toLowerCase()
                        console.log("Applying:", cmd)
                    }
                }
            }
        }
    }
}
