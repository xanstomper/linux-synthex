import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 540
    height: 620
    radius: 20
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property int activeCategoryIndex: 0
    property string username: "xanstomper"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // ── 1. Search Bar ──────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            radius: 12
            color: "#0affffff"
            border.color: searchInput.activeFocus ? "#7AA2F7" : "#0fffffff"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10

                Text {
                    text: "🔍"
                    font.pixelSize: 14
                    color: "#9AA1AB"
                }

                TextInput {
                    id: searchInput
                    Layout.fillWidth: true
                    font.family: "Inter"
                    font.pixelSize: 14
                    color: "#FFFFFF"
                    clip: true

                    Text {
                        text: "Search apps, files, settings..."
                        font.family: "Inter"
                        font.pixelSize: 14
                        color: "#67707D"
                        visible: !searchInput.text && !searchInput.activeFocus
                    }
                }
            }
        }

        // ── 2. Two-Column Layout (Categories + App List) ────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            // Left Category Sidebar
            ColumnLayout {
                Layout.preferredWidth: 170
                Layout.fillHeight: true
                spacing: 2

                ListModel {
                    id: categoriesModel
                    ListElement { name: "Favorites"; icon: "⭐" }
                    ListElement { name: "All Applications"; icon: "🪟" }
                    ListElement { name: "Development"; icon: "🛠" }
                    ListElement { name: "Graphics"; icon: "🎨" }
                    ListElement { name: "Internet"; icon: "🌐" }
                    ListElement { name: "Multimedia"; icon: "🎵" }
                    ListElement { name: "Office"; icon: "📄" }
                    ListElement { name: "Settings"; icon: "⚙️" }
                    ListElement { name: "System"; icon: "💻" }
                    ListElement { name: "Utilities"; icon: "🧰" }
                }

                ListView {
                    id: categoryList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: categoriesModel
                    clip: true
                    spacing: 2

                    delegate: Rectangle {
                        width: categoryList.width
                        height: 36
                        radius: 8
                        color: root.activeCategoryIndex === index ? "#386c88a8" : "transparent"
                        border.color: root.activeCategoryIndex === index ? "#4d7aa2f7" : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 8

                            Text {
                                text: model.icon
                                font.pixelSize: 13
                            }

                            Text {
                                text: model.name
                                font.family: "Inter"
                                font.pixelSize: 13
                                font.weight: root.activeCategoryIndex === index ? Font.DemiBold : Font.Normal
                                color: root.activeCategoryIndex === index ? "#7AA2F7" : "#9AA1AB"
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeCategoryIndex = index
                        }
                    }
                }

                // Divider
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: "#0fffffff"
                    Layout.topMargin: 4
                    Layout.bottomMargin: 4
                }

                // User Profile & Power Actions
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    spacing: 8

                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        Text {
                            text: "👤"
                            font.pixelSize: 14
                        }

                        Text {
                            text: root.username
                            font.family: "Inter"
                            font.pixelSize: 12
                            font.bold: true
                            color: "#DDE3EB"
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        spacing: 8
                        Text { text: "🔒"; font.pixelSize: 13; color: "#9AA1AB" }
                        Text { text: "🔄"; font.pixelSize: 13; color: "#9AA1AB" }
                        Text { text: "⏻"; font.pixelSize: 13; color: "#D97C82" }
                    }
                }
            }

            // Vertical Divider
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: "#0fffffff"
            }

            // Right Application Items List
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ListModel {
                    id: appsModel
                    ListElement { name: "Firefox"; category: "Web Browser"; icon: "🌐"; color: "#FF7139" }
                    ListElement { name: "Visual Studio Code"; category: "Code Editor"; icon: "💻"; color: "#007ACC" }
                    ListElement { name: "Spotify"; category: "Music Player"; icon: "🎵"; color: "#1DB954" }
                    ListElement { name: "Files"; category: "File Manager"; icon: "📁"; color: "#4A90E2" }
                    ListElement { name: "Terminal"; category: "System Terminal"; icon: "⌨️"; color: "#333333" }
                    ListElement { name: "Discord"; category: "Internet Messenger"; icon: "💬"; color: "#5865F2" }
                    ListElement { name: "Settings"; category: "System Settings"; icon: "⚙️"; color: "#8E8E93" }
                    ListElement { name: "System Monitor"; category: "Resource Monitor"; icon: "📊"; color: "#30D158" }
                }

                ListView {
                    id: appsList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: appsModel
                    clip: true
                    spacing: 6

                    delegate: Rectangle {
                        width: appsList.width
                        height: 52
                        radius: 12
                        color: "#05ffffff"
                        border.color: "#0affffff"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 12

                            Rectangle {
                                width: 34
                                height: 34
                                radius: 8
                                color: model.color

                                Text {
                                    text: model.icon
                                    font.pixelSize: 18
                                    anchors.centerIn: parent
                                }
                            }

                            ColumnLayout {
                                spacing: 2
                                Layout.fillWidth: true

                                Text {
                                    text: model.name
                                    font.family: "Inter"
                                    font.pixelSize: 13
                                    font.bold: true
                                    color: "#FFFFFF"
                                }

                                Text {
                                    text: model.category
                                    font.family: "Inter"
                                    font.pixelSize: 11
                                    color: "#9AA1AB"
                                }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: parent.color = "#0fffffff"
                            onExited: parent.color = "#05ffffff"
                        }
                    }
                }
            }
        }
    }
}
