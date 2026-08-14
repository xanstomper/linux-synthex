import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 540
    height: 620
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 20
    color: "#d012161f" // Translucent liquid glass
    border.color: "#30ffffff"
    border.width: 1

    property int activeCategoryIndex: 0
    property string username: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.username : "user"

    // Liquid Glass Specular Top Highlight
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22ffffff" }
            GradientStop { position: 0.06; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // ── 1. Search Bar ──────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            radius: 12
            color: "#14ffffff"
            border.color: searchInput.activeFocus ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#1fffffff"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10

                Text {
                    text: "󰍉"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 16
                    color: "#9AA1AB"
                }

                TextInput {
                    id: searchInput
                    Layout.fillWidth: true
                    font.family: "Inter"
                    font.pixelSize: 14
                    color: "#FFFFFF"
                    clip: true
                    onAccepted: {
                        if (text.length > 0) {
                            if (typeof systemBridge !== "undefined" && systemBridge) {
                                systemBridge.launchApp(text)
                            }
                        }
                    }

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
                    ListElement { name: "Favorites"; icon: "󰓎" }
                    ListElement { name: "All Applications"; icon: "󰀻" }
                    ListElement { name: "Development"; icon: "󰅩" }
                    ListElement { name: "Graphics"; icon: "󰹑" }
                    ListElement { name: "Internet"; icon: "󰖟" }
                    ListElement { name: "Multimedia"; icon: "󰝚" }
                    ListElement { name: "Office"; icon: "󰈙" }
                    ListElement { name: "Settings"; icon: "󰒓" }
                    ListElement { name: "System"; icon: "󰍹" }
                    ListElement { name: "Utilities"; icon: "󰆍" }
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
                        color: root.activeCategoryIndex === index ? "#357aa2f7" : (catMouse.containsMouse ? "#10ffffff" : "transparent")
                        border.color: root.activeCategoryIndex === index ? "#7AA2F7" : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 8

                            Text {
                                text: model.icon
                                font.family: "Symbols Nerd Font"
                                font.pixelSize: 14
                                color: root.activeCategoryIndex === index ? "#FFFFFF" : "#9AA1AB"
                            }

                            Text {
                                text: model.name
                                font.family: "Inter"
                                font.pixelSize: 13
                                font.weight: root.activeCategoryIndex === index ? Font.DemiBold : Font.Normal
                                color: root.activeCategoryIndex === index ? "#FFFFFF" : "#A0AAB8"
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            id: catMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeCategoryIndex = index
                        }

                        Behavior on color { ColorAnimation { duration: 140 } }
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
                            text: "󰄬"
                            font.family: "Symbols Nerd Font"
                            font.pixelSize: 14
                            color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
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
                        spacing: 10
                        Text {
                            text: "󰌾"
                            font.family: "Symbols Nerd Font"
                            font.pixelSize: 15
                            color: "#9AA1AB"
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.powerAction("lock") }
                            }
                        }
                        Text {
                            text: "󰜉"
                            font.family: "Symbols Nerd Font"
                            font.pixelSize: 15
                            color: "#9AA1AB"
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.powerAction("reboot") }
                            }
                        }
                        Text {
                            text: "󰐥"
                            font.family: "Symbols Nerd Font"
                            font.pixelSize: 15
                            color: "#D97C82"
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.powerAction("poweroff") }
                            }
                        }
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
                    ListElement { name: "Firefox"; category: "Web Browser"; icon: "󰈹"; color: "#FF7139"; cmd: "firefox" }
                    ListElement { name: "Visual Studio Code"; category: "Code Editor"; icon: "󰨞"; color: "#007ACC"; cmd: "code" }
                    ListElement { name: "Spotify"; category: "Music Player"; icon: "󰓇"; color: "#1DB954"; cmd: "spotify" }
                    ListElement { name: "Files"; category: "File Manager"; icon: "󰉋"; color: "#4A90E2"; cmd: "dolphin || nautilus || thunar" }
                    ListElement { name: "Terminal"; category: "System Terminal"; icon: "󰆍"; color: "#333333"; cmd: "kitty || alacritty" }
                    ListElement { name: "Discord"; category: "Internet Messenger"; icon: "󰙯"; color: "#5865F2"; cmd: "discord || vesktop" }
                    ListElement { name: "Settings"; category: "System Settings"; icon: "󰒓"; color: "#8E8E93"; cmd: "synthex-control-center || systemsettings" }
                    ListElement { name: "System Monitor"; category: "Resource Monitor"; icon: "󰍹"; color: "#30D158"; cmd: "plasma-systemmonitor || btop" }
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
                        color: appMouse.containsMouse ? "#1affffff" : "#08ffffff"
                        border.color: appMouse.containsMouse ? "#30ffffff" : "#10ffffff"

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
                                    font.family: "Symbols Nerd Font"
                                    font.pixelSize: 18
                                    color: "#FFFFFF"
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
                                    color: "#A0AAB8"
                                }
                            }
                        }

                        MouseArea {
                            id: appMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (typeof systemBridge !== "undefined" && systemBridge) {
                                    systemBridge.launchApp(model.cmd)
                                }
                            }
                        }

                        Behavior on color { ColorAnimation { duration: 140 } }
                    }
                }
            }
        }
    }
}
