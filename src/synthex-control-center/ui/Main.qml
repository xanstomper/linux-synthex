import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: mainWindow
    visible: true
    width: 1040
    height: 760
    minimumWidth: 840
    minimumHeight: 600
    title: "System Settings"
    color: "#2f343f"

    property string currentPage: "home"
    property string currentTitle: "System Settings"
    property string searchQuery: ""

    readonly property color mintGreen: "#92b15e"
    readonly property color mintDark: "#2f343f"
    readonly property color mintHeader: "#262a33"
    readonly property color mintCard: "#383c4a"
    readonly property color mintCardHover: "#404552"
    readonly property color mintBorder: "#434857"
    readonly property color textColor: "#FFFFFF"
    readonly property color textMuted: "#9aa7b8"

    function openModule(pageFile, title) {
        currentPage = pageFile
        currentTitle = title
        pageLoader.source = "pages/" + pageFile
    }

    function showHome() {
        currentPage = "home"
        currentTitle = "System Settings"
        pageLoader.source = ""
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── 1. Linux Mint Style Header Bar ─────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            color: mintHeader
            border.color: "#20000000"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                // Back to All Settings Button
                Button {
                    id: backBtn
                    visible: currentPage !== "home"
                    text: "◀ All Settings"
                    contentItem: Text {
                        text: parent.text
                        font.family: "Ubuntu, Inter, sans-serif"
                        font.pixelSize: 12
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    background: Rectangle {
                        color: parent.hovered ? mintCardHover : mintCard
                        border.color: mintBorder
                        radius: 4
                        implicitWidth: 100
                        implicitHeight: 28
                    }
                    onClicked: showHome()
                }

                Text {
                    text: currentTitle
                    font.family: "Ubuntu, Inter, sans-serif"
                    font.pixelSize: 14
                    font.bold: true
                    color: textColor
                }

                Item { Layout.fillWidth: true }

                // Search Bar
                Rectangle {
                    visible: currentPage === "home"
                    width: 220
                    height: 28
                    radius: 4
                    color: "#1e2229"
                    border.color: searchInput.activeFocus ? mintGreen : mintBorder

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 6

                        Text { text: "🔍"; font.pixelSize: 11; color: textMuted }
                        TextInput {
                            id: searchInput
                            Layout.fillWidth: true
                            font.family: "Ubuntu, Inter, sans-serif"
                            font.pixelSize: 12
                            color: "#FFFFFF"
                            selectByMouse: true
                            onTextChanged: searchQuery = text.toLowerCase()
                            Text {
                                text: "Search..."
                                font.family: "Ubuntu, Inter, sans-serif"
                                font.pixelSize: 12
                                color: textMuted
                                visible: !searchInput.text && !searchInput.activeFocus
                            }
                        }
                    }
                }
            }
        }

        // ── 2. Content Area: Main Categorized Grid OR Active Module ────────
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // HOME VIEW: Categorized Grid (Linux Mint Cinnamon Settings Style)
            ScrollView {
                id: homeScroll
                anchors.fill: parent
                anchors.margins: 20
                visible: currentPage === "home"
                clip: true

                ColumnLayout {
                    width: mainWindow.width - 40
                    spacing: 24

                    // Category: Appearance
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: "APPEARANCE"
                            font.family: "Ubuntu, Inter, sans-serif"
                            font.pixelSize: 11
                            font.bold: true
                            color: mintGreen
                        }

                        GridLayout {
                            columns: 6
                            rowSpacing: 12
                            columnSpacing: 12
                            Layout.fillWidth: true

                            Repeater {
                                model: [
                                    { name: "Backgrounds", icon: "🖼️", color: "#406852", file: "Displays.qml" },
                                    { name: "Themes", icon: "🎨", color: "#3d6c82", file: "DesktopCustomization.qml" },
                                    { name: "Effects", icon: "✨", color: "#5c548a", file: "DesktopCustomization.qml" },
                                    { name: "Font Selection", icon: "🔤", color: "#7b6348", file: "DesktopCustomization.qml" }
                                ]

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 84
                                    radius: 6
                                    color: mintTileArea.containsMouse ? mintCardHover : mintCard
                                    border.color: mintTileArea.containsMouse ? mintGreen : mintBorder
                                    visible: searchQuery === "" || modelData.name.toLowerCase().indexOf(searchQuery) !== -1

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 38; height: 38; radius: 6
                                            color: modelData.color
                                            Layout.alignment: Qt.AlignHCenter
                                            Text { text: modelData.icon; font.pixelSize: 18; anchors.centerIn: parent }
                                        }

                                        Text {
                                            text: modelData.name
                                            font.family: "Ubuntu, Inter, sans-serif"
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: textColor
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }

                                    MouseArea {
                                        id: mintTileArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: openModule(modelData.file, modelData.name)
                                    }
                                }
                            }
                        }
                    }

                    // Category: Preferences
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: "PREFERENCES"
                            font.family: "Ubuntu, Inter, sans-serif"
                            font.pixelSize: 11
                            font.bold: true
                            color: mintGreen
                        }

                        GridLayout {
                            columns: 6
                            rowSpacing: 12
                            columnSpacing: 12
                            Layout.fillWidth: true

                            Repeater {
                                model: [
                                    { name: "Account Details", icon: "👤", color: "#3f51b5", file: "About.qml" },
                                    { name: "Date & Time", icon: "🕒", color: "#e65100", file: "About.qml" },
                                    { name: "Notifications", icon: "🔔", color: "#c2185b", file: "Apps.qml" },
                                    { name: "Preferred Apps", icon: "⭐", color: "#00838f", file: "Apps.qml" },
                                    { name: "Privacy", icon: "🔒", color: "#4e342e", file: "Security.qml" },
                                    { name: "Startup Apps", icon: "🚀", color: "#558b2f", file: "Apps.qml" }
                                ]

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 84
                                    radius: 6
                                    color: prefArea.containsMouse ? mintCardHover : mintCard
                                    border.color: prefArea.containsMouse ? mintGreen : mintBorder
                                    visible: searchQuery === "" || modelData.name.toLowerCase().indexOf(searchQuery) !== -1

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 38; height: 38; radius: 6
                                            color: modelData.color
                                            Layout.alignment: Qt.AlignHCenter
                                            Text { text: modelData.icon; font.pixelSize: 18; anchors.centerIn: parent }
                                        }

                                        Text {
                                            text: modelData.name
                                            font.family: "Ubuntu, Inter, sans-serif"
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: textColor
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }

                                    MouseArea {
                                        id: prefArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: openModule(modelData.file, modelData.name)
                                    }
                                }
                            }
                        }
                    }

                    // Category: Hardware
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: "HARDWARE"
                            font.family: "Ubuntu, Inter, sans-serif"
                            font.pixelSize: 11
                            font.bold: true
                            color: mintGreen
                        }

                        GridLayout {
                            columns: 6
                            rowSpacing: 12
                            columnSpacing: 12
                            Layout.fillWidth: true

                            Repeater {
                                model: [
                                    { name: "Bluetooth", icon: "ᛒ", color: "#1565c0", file: "Bluetooth.qml" },
                                    { name: "Display", icon: "🖥️", color: "#6a1b9a", file: "Displays.qml" },
                                    { name: "Graphics", icon: "🎮", color: "#2e7d32", file: "Gaming.qml" },
                                    { name: "Network", icon: "📶", color: "#0277bd", file: "Network.qml" },
                                    { name: "Power", icon: "🔋", color: "#f57f17", file: "Power.qml" },
                                    { name: "Sound", icon: "🔊", color: "#ad1457", file: "Sound.qml" },
                                    { name: "System Info", icon: "ℹ️", color: "#00695c", file: "About.qml" }
                                ]

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 84
                                    radius: 6
                                    color: hwArea.containsMouse ? mintCardHover : mintCard
                                    border.color: hwArea.containsMouse ? mintGreen : mintBorder
                                    visible: searchQuery === "" || modelData.name.toLowerCase().indexOf(searchQuery) !== -1

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 38; height: 38; radius: 6
                                            color: modelData.color
                                            Layout.alignment: Qt.AlignHCenter
                                            Text { text: modelData.icon; font.pixelSize: 18; anchors.centerIn: parent }
                                        }

                                        Text {
                                            text: modelData.name
                                            font.family: "Ubuntu, Inter, sans-serif"
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: textColor
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }

                                    MouseArea {
                                        id: hwArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: openModule(modelData.file, modelData.name)
                                    }
                                }
                            }
                        }
                    }

                    // Category: Administration
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: "ADMINISTRATION"
                            font.family: "Ubuntu, Inter, sans-serif"
                            font.pixelSize: 11
                            font.bold: true
                            color: mintGreen
                        }

                        GridLayout {
                            columns: 6
                            rowSpacing: 12
                            columnSpacing: 12
                            Layout.fillWidth: true

                            Repeater {
                                model: [
                                    { name: "Backup / Snaps", icon: "💾", color: "#283593", file: "Snapshots.qml" },
                                    { name: "Driver Manager", icon: "🔧", color: "#d84315", file: "Drivers.qml" },
                                    { name: "Firewall", icon: "🧱", color: "#c62828", file: "Security.qml" },
                                    { name: "Update Manager", icon: "🔄", color: "#2e7d32", file: "Updates.qml" }
                                ]

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 84
                                    radius: 6
                                    color: adminArea.containsMouse ? mintCardHover : mintCard
                                    border.color: adminArea.containsMouse ? mintGreen : mintBorder
                                    visible: searchQuery === "" || modelData.name.toLowerCase().indexOf(searchQuery) !== -1

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 38; height: 38; radius: 6
                                            color: modelData.color
                                            Layout.alignment: Qt.AlignHCenter
                                            Text { text: modelData.icon; font.pixelSize: 18; anchors.centerIn: parent }
                                        }

                                        Text {
                                            text: modelData.name
                                            font.family: "Ubuntu, Inter, sans-serif"
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: textColor
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }

                                    MouseArea {
                                        id: adminArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: openModule(modelData.file, modelData.name)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // MODULE VIEW: Loaded Sub-Page
            Loader {
                id: pageLoader
                anchors.fill: parent
                visible: currentPage !== "home"
            }
        }
    }
}
