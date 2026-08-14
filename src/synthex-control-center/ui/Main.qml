import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: mainWindow
    visible: true
    width: 1200
    height: 800
    minimumWidth: 980
    minimumHeight: 640
    title: "SynthOS System Settings"
    color: "#0D1117"

    property int activeNavIndex: 0
    property string currentPage: "Desktop"
    property string searchQuery: ""

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color bgColor: "#0D1117"
    readonly property color sidebarBg: "#141A22"
    readonly property color surfaceColor: "#161C24"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ── 1. Left Sidebar Navigation ─────────────────────────────────────
        Rectangle {
            id: sidebar
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            color: sidebarBg

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Header Logo & Branding
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
                    color: "transparent"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 18
                        anchors.rightMargin: 18
                        spacing: 12

                        Rectangle {
                            width: 36
                            height: 36
                            radius: 9
                            color: accentColor

                            Text {
                                text: "󰒓"
                                font.family: "Symbols Nerd Font"
                                font.pixelSize: 20
                                color: "#0C1116"
                                anchors.centerIn: parent
                            }
                        }

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text: "System Settings"
                                font.family: "Inter"
                                font.pixelSize: 15
                                font.bold: true
                                color: textColor
                            }
                            Text {
                                text: "SynthOS Linux 2026"
                                font.family: "Inter"
                                font.pixelSize: 11
                                color: mutedText
                            }
                        }
                    }
                }

                // Search Bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                    Layout.bottomMargin: 10
                    radius: 8
                    color: "#1c232e"
                    border.color: "#25ffffff"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8

                        Text { text: "🔍"; font.pixelSize: 12; color: mutedText }
                        TextInput {
                            id: searchInput
                            Layout.fillWidth: true
                            font.family: "Inter"
                            font.pixelSize: 12
                            color: "#FFFFFF"
                            selectByMouse: true
                            onTextChanged: searchQuery = text.toLowerCase()
                            Text {
                                text: "Search settings..."
                                font.family: "Inter"
                                font.pixelSize: 12
                                color: mutedText
                                visible: !searchInput.text && !searchInput.activeFocus
                            }
                        }
                    }
                }

                // Navigation ListView
                ListView {
                    id: navList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    model: ListModel {
                        // Connectivity
                        ListElement { name: "Network"; label: "Wi-Fi & Internet"; icon: "󰤨"; category: "CONNECTIVITY" }
                        ListElement { name: "Bluetooth"; label: "Bluetooth & Devices"; icon: "󰂯"; category: "CONNECTIVITY" }

                        // Personalization
                        ListElement { name: "Desktop"; label: "Desktop & Themes"; icon: "󰒓"; category: "PERSONALIZATION" }
                        ListElement { name: "Displays"; label: "Displays & Monitors"; icon: "󰍹"; category: "PERSONALIZATION" }
                        ListElement { name: "Sound"; label: "Sound & Audio"; icon: "󰕾"; category: "PERSONALIZATION" }

                        // System & Power
                        ListElement { name: "Power"; label: "Power & Battery"; icon: "󰁹"; category: "SYSTEM" }
                        ListElement { name: "Apps"; label: "Applications & Defaults"; icon: "󰀻"; category: "SYSTEM" }
                        ListElement { name: "Gaming"; label: "Gaming & Performance"; icon: "󰊴"; category: "SYSTEM" }
                        ListElement { name: "Snapshots"; label: "Storage & Snapshots"; icon: "󰁯"; category: "SYSTEM" }

                        // Security & Upgrades
                        ListElement { name: "Security"; label: "Privacy & Security"; icon: "󰒃"; category: "MAINTENANCE" }
                        ListElement { name: "Updates"; label: "System Updates"; icon: "󰚰"; category: "MAINTENANCE" }
                        ListElement { name: "Drivers"; label: "Hardware & Drivers"; icon: "󰄛"; category: "MAINTENANCE" }
                        ListElement { name: "About"; label: "About SynthOS"; icon: "󰋼"; category: "INFO" }
                    }

                    delegate: ItemDelegate {
                        width: parent ? parent.width : 260
                        height: 42
                        highlighted: ListView.isCurrentItem
                        visible: searchQuery === "" || model.label.toLowerCase().indexOf(searchQuery) !== -1

                        background: Rectangle {
                            color: highlighted ? "#257aa2f7" : (hovered ? "#1a222c" : "transparent")
                            radius: 8
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            Behavior on color { ColorAnimation { duration: 120 } }

                            Rectangle {
                                visible: highlighted
                                width: 3
                                height: 20
                                color: accentColor
                                radius: 1.5
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                            }
                        }

                        contentItem: RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 20
                            anchors.rightMargin: 16
                            spacing: 12

                            Text {
                                text: model.icon
                                font.family: "Symbols Nerd Font"
                                font.pixelSize: 17
                                color: highlighted ? accentColor : mutedText
                            }

                            Text {
                                text: model.label
                                font.family: "Inter"
                                font.pixelSize: 13
                                font.bold: highlighted
                                color: highlighted ? textColor : "#C0CAD6"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }

                        onClicked: {
                            navList.currentIndex = index
                            activeNavIndex = index
                            currentPage = model.name
                            pageLoader.source = "pages/" + (model.name === "Desktop" ? "DesktopCustomization.qml" : (model.name + ".qml"))
                        }
                    }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: "#18ffffff"
        }

        // ── 2. Content View Area ───────────────────────────────────────────
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Loader {
                id: pageLoader
                anchors.fill: parent
                source: "pages/DesktopCustomization.qml"
            }
        }
    }
}
