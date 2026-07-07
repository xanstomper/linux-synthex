import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Synthex Software Center — Linux Mint-inspired design
// Category-based browsing, clean cards, green accents

ApplicationWindow {
    id: softwareCenter
    visible: true
    width: 960
    height: 680
    title: "Software Manager"
    color: "#F5F5F7"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header — Mint-style green bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "#9BBD5C"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 4
                Text {
                    text: "📦 Software Manager"
                    font.pixelSize: 22
                    font.bold: true
                    color: "#FFFFFF"
                    Layout.alignment: Qt.AlignHCenter
                }
                // Search bar
                Rectangle {
                    Layout.preferredWidth: 400
                    Layout.preferredHeight: 34
                    radius: 17
                    color: "#FFFFFF"
                    Layout.alignment: Qt.AlignHCenter

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 4
                        Text { text: "🔍"; font.pixelSize: 14 }
                        TextInput {
                            Layout.fillWidth: true
                            color: "#2A2A2E"
                            font.pixelSize: 13
                            placeholderText: "Search applications..."
                            clip: true
                        }
                    }
                }
            }
        }

        // Category grid — Mint-style cards
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 16

                Text {
                    text: "Categories"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#2A2A2E"
                }

                GridLayout {
                    columns: 4
                    columnSpacing: 12
                    rowSpacing: 12
                    Layout.fillWidth: true

                    Repeater {
                        model: ListModel {
                            ListElement { name: "Internet"; icon: "🌐"; color: "#4A90D9"; count: "42 apps" }
                            ListElement { name: "Office"; icon: "📊"; color: "#E67E22"; count: "28 apps" }
                            ListElement { name: "Graphics"; icon: "🎨"; color: "#9B59B6"; count: "35 apps" }
                            ListElement { name: "Games"; icon: "🎮"; color: "#27AE60"; count: "56 apps" }
                            ListElement { name: "Audio/Video"; icon: "🎵"; color: "#E74C3C"; count: "48 apps" }
                            ListElement { name: "Development"; icon: "💻"; color: "#3498DB"; count: "67 apps" }
                            ListElement { name: "System Tools"; icon: "⚙"; color: "#95A5A6"; count: "39 apps" }
                            ListElement { name: "Accessories"; icon: "🔧"; color: "#1ABC9C"; count: "24 apps" }
                        }

                        Rectangle {
                            width: 200
                            height: 90
                            radius: 8
                            color: "#FFFFFF"
                            border.color: "#E0E0E0"
                            border.width: 1

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 4
                                RowLayout {
                                    spacing: 8
                                    Rectangle {
                                        width: 36; height: 36; radius: 8
                                        color: model.color
                                        Text { anchors.centerIn: parent; text: model.icon; font.pixelSize: 18 }
                                    }
                                    ColumnLayout {
                                        spacing: 2
                                        Text { text: model.name; font.pixelSize: 14; font.bold: true; color: "#2A2A2E" }
                                        Text { text: model.count; font.pixelSize: 11; color: "#888888" }
                                    }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: parent.border.color = "#9BBD5C"
                                onExited: parent.border.color = "#E0E0E0"
                            }
                        }
                    }
                }

                // Featured apps section
                Text {
                    text: "Featured Applications"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#2A2A2E"
                    Layout.topMargin: 8
                }

                RowLayout {
                    spacing: 12
                    Repeater {
                        model: ListModel {
                            ListElement { name: "Firefox"; desc: "Web Browser"; icon: "🦊"; rating: "5" }
                            ListElement { name: "VS Code"; desc: "Code Editor"; icon: "💻"; rating: "5" }
                            ListElement { name: "Steam"; desc: "Gaming"; icon: "🎮"; rating: "5" }
                            ListElement { name: "Blender"; desc: "3D Creation"; icon: "🎨"; rating: "4" }
                        }
                        Rectangle {
                            width: 210; height: 60; radius: 8
                            color: "#FFFFFF"
                            border.color: "#E0E0E0"; border.width: 1
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 12; spacing: 10
                                Text { text: model.icon; font.pixelSize: 24 }
                                ColumnLayout {
                                    spacing: 2
                                    Text { text: model.name; font.pixelSize: 13; font.bold: true; color: "#2A2A2E" }
                                    Text { text: model.desc; font.pixelSize: 11; color: "#888888" }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: parent.border.color = "#9BBD5C"
                                onExited: parent.border.color = "#E0E0E0"
                            }
                        }
                    }
                }
            }
        }

        // Status bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            color: "#E8E8E8"
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                text: "339 applications available"
                font.pixelSize: 11
                color: "#888888"
            }
        }
    }
}
