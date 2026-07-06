import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: studioWindow
    visible: true
    width: 1200
    height: 800
    minimumWidth: 960
    minimumHeight: 640
    title: "Solus Studio"
    color: "#0B0F1A"

    readonly property color accentColor: "#FFB300"
    readonly property color bgColor: "#0B0F1A"
    readonly property color surfaceColor: "#1A1A2E"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"

    property int activeTab: 0

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Left side: Tabs + Content
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: bgColor

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Tab bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    color: "#121624"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        spacing: 4

                        Repeater {
                            model: ["Themes", "Layouts", "Fonts", "Icons", "Presets", "Blueprint"]

                            delegate: Rectangle {
                                Layout.preferredHeight: 36
                                Layout.preferredWidth: 80
                                radius: 8
                                color: activeTab === index ? accentColor : "transparent"

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData
                                    font.pixelSize: 12
                                    font.bold: activeTab === index
                                    color: activeTab === index ? "#0B0F1A" : mutedText
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: activeTab = index
                                }
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }
                }

                // Tab Content
                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: activeTab

                    // Themes tab
                    Item {
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 24
                            spacing: 16

                            Text { text: "Theme Mixer"; font.pixelSize: 22; font.bold: true; color: textColor }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 3
                                rowSpacing: 12
                                columnSpacing: 12

                                Repeater {
                                    model: [
                                        { label: "Window Theme", items: ["Solus Dark", "Solus Light", "Solus Neon", "Minimal"] },
                                        { label: "Icon Theme", items: ["Solus Icons", "Papirus", "Tela Circle", "Numix"] },
                                        { label: "Cursor Theme", items: ["Solus Cursor", "Bibata Modern", "Bibata Classic", "Adwaita"] }
                                    ]

                                    delegate: ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 6
                                        Text { text: modelData.label; font.pixelSize: 13; font.bold: true; color: textColor }
                                        ComboBox {
                                            Layout.fillWidth: true
                                            model: modelData.items
                                            currentIndex: 0
                                            font.pixelSize: 12
                                            background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }
                                            contentItem: Text { text: parent.currentText; color: textColor; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 10 }
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }
                        }
                    }

                    // Layouts tab
                    Item {
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 24
                            spacing: 16

                            Text { text: "Layout Presets"; font.pixelSize: 22; font.bold: true; color: textColor }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 3
                                rowSpacing: 12
                                columnSpacing: 12

                                Repeater {
                                    model: ["Solus Default", "Traditional", "Modern", "macOS Style", "Windows Style", "Minimal"]
                                    delegate: Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 100
                                        radius: 10
                                        color: surfaceColor
                                        border.color: "#2A2A3E"
                                        border.width: 1
                                        ColumnLayout {
                                            anchors.centerIn: parent; spacing: 6
                                            Text { text: "\u{1F4CB}"; font.pixelSize: 24; anchors.horizontalCenter: parent.horizontalCenter }
                                            Text { text: modelData; font.pixelSize: 12; color: textColor; anchors.horizontalCenter: parent.horizontalCenter }
                                        }
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: {} }
                                    }
                                }
                            }
                        }
                    }

                    // Fonts tab
                    Item {
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 24; spacing: 16
                            Text { text: "Font Settings"; font.pixelSize: 22; font.bold: true; color: textColor }
                            GridLayout {
                                Layout.fillWidth: true; columns: 2; rowSpacing: 12; columnSpacing: 16
                                Repeater {
                                    model: [
                                        { label: "Interface Font", value: "Inter", sizes: ["9","10","11","12","13","14","15"] },
                                        { label: "Monospace Font", value: "JetBrains Mono", sizes: ["9","10","11","12","13","14"] },
                                        { label: "Document Font", value: "Noto Serif", sizes: ["10","11","12","13","14"] },
                                        { label: "Window Title Font", value: "Inter", sizes: ["10","11","12","13"] }
                                    ]
                                    delegate: Rectangle {
                                        Layout.fillWidth: true; Layout.preferredHeight: 80; color: surfaceColor; radius: 10; border.color: "#2A2A3E"; border.width: 1
                                        RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12
                                            ColumnLayout { Layout.fillWidth: true; spacing: 4
                                                Text { text: modelData.label; font.pixelSize: 13; color: textColor }
                                                RowLayout { spacing: 8; Layout.fillWidth: true
                                                    ComboBox { Layout.fillWidth: true; model: [modelData.value]; currentIndex: 0; font.pixelSize: 11; background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }; contentItem: Text { text: parent.currentText; color: textColor; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 8 } }
                                                    ComboBox { Layout.preferredWidth: 60; model: modelData.sizes; currentIndex: 2; font.pixelSize: 11; background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }; contentItem: Text { text: parent.currentText; color: textColor; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 8 } }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Icons tab
                    Item {
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 24; spacing: 16
                            Text { text: "Icon Theme"; font.pixelSize: 22; font.bold: true; color: textColor }
                            GridLayout {
                                Layout.fillWidth: true; columns: 4; rowSpacing: 16; columnSpacing: 16
                                Repeater {
                                    model: ["Papirus", "Tela Circle", "Tela", "Numix", "ePapirus", "Adwaita", "Breeze", "Solus Icons"]
                                    delegate: Rectangle {
                                        Layout.fillWidth: true; Layout.preferredHeight: 100; radius: 10; color: surfaceColor; border.color: "#2A2A3E"; border.width: 1
                                        ColumnLayout { anchors.centerIn: parent; spacing: 6
                                            Text { text: "\u{1F5BC}"; font.pixelSize: 28; anchors.horizontalCenter: parent.horizontalCenter }
                                            Text { text: modelData; font.pixelSize: 12; color: textColor; anchors.horizontalCenter: parent.horizontalCenter }
                                        }
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: {} }
                                    }
                                }
                            }
                        }
                    }

                    // Presets tab (loads from separate file)
                    Presets {}

                    // Blueprint tab
                    Item {
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 24; spacing: 16
                            Text { text: "Blueprint Manager"; font.pixelSize: 22; font.bold: true; color: textColor }
                            Text { text: "Export or import complete theme configurations"; font.pixelSize: 13; color: mutedText }
                            RowLayout { Layout.fillWidth: true; spacing: 12
                                Button { Layout.fillWidth: true; Layout.preferredHeight: 44; flat: true; background: Rectangle { color: "#2A2A3E"; radius: 8; border.color: "#3A3A4E" }; contentItem: Text { text: "\u{1F4E4} Export Blueprint"; color: textColor; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter } }
                                Button { Layout.fillWidth: true; Layout.preferredHeight: 44; flat: true; background: Rectangle { color: "#2A2A3E"; radius: 8; border.color: "#3A3A4E" }; contentItem: Text { text: "\u{1F4E5} Import Blueprint"; color: textColor; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter } }
                            }
                            ListView {
                                Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                model: ListModel {
                                    ListElement { name: "my-setup", date: "2025-07-04", apps: "Themes + Icons + Fonts" }
                                    ListElement { name: "gaming-rig", date: "2025-07-01", apps: "Themes + Layout + Icons" }
                                    ListElement { name: "dev-config", date: "2025-06-28", apps: "Fonts + Icons" }
                                }
                                delegate: Rectangle {
                                    width: parent.width; height: 40; color: index % 2 === 0 ? "#1E1E32" : "transparent"
                                    RowLayout { anchors.fill: parent; anchors.margins: 8; spacing: 12
                                        Text { text: "\u{1F4C4}"; font.pixelSize: 14 }
                                        Text { text: name; font.pixelSize: 13; color: textColor; font.bold: true; Layout.preferredWidth: 140 }
                                        Text { text: date; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 100 }
                                        Text { text: apps; font.pixelSize: 11; color: mutedText }
                                        Item { Layout.fillWidth: true }
                                        Text { text: "\u{1F519} Apply"; font.pixelSize: 11; color: accentColor }
                                    }
                                }
                            }
                        }
                    }
                }

                // Bottom Action Bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: "#121624"

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        Button {
                            text: "Export Setup"
                            flat: true
                            font.pixelSize: 12
                            Layout.preferredHeight: 36
                            background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }
                            contentItem: Text { text: "\u{1F4E4} Export Setup"; color: textColor; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }

                        Button {
                            text: "Import Setup"
                            flat: true
                            font.pixelSize: 12
                            Layout.preferredHeight: 36
                            background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }
                            contentItem: Text { text: "\u{1F4E5} Import Setup"; color: textColor; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            text: "Apply & Create Snapshot"
                            flat: true
                            font.pixelSize: 13
                            Layout.preferredHeight: 40
                            Layout.preferredWidth: 200
                            background: Rectangle { color: accentColor; radius: 8 }
                            contentItem: Text { text: "\u{1F504} Apply & Create Snapshot"; color: "#0B0F1A"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            onClicked: { console.log("Theme applied, snapshot created"); }
                        }
                    }
                }
            }
        }

        // Right side: Live Preview
        Rectangle {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
            color: "#0D1117"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: "Live Preview"
                    font.pixelSize: 14
                    font.bold: true
                    color: textColor
                }

                // Preview window mockup
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: "#1A1A2E"
                    border.color: "#2A2A3E"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 0
                        spacing: 0
                        clip: true

                        // Pretend title bar
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 32
                            color: "#121624"
                            radius: 12

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 6
                                Rectangle { width: 10; height: 10; radius: 5; color: "#E53935" }
                                Rectangle { width: 10; height: 10; radius: 5; color: accentColor }
                                Rectangle { width: 10; height: 10; radius: 5; color: "#43A047" }
                                Item { Layout.fillWidth: true }
                                Text { text: "Preview"; font.pixelSize: 10; color: mutedText }
                            }
                        }

                        // Preview content area
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#0B0F1A"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 8

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 60
                                    radius: 8; color: "#1A1A2E"
                                    Rectangle { width: 40; height: 40; radius: 8; color: accentColor; anchors.left: parent.left; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter }
                                    Text { text: "Sample Window"; font.pixelSize: 13; color: "#FFFFFF"; anchors.left: parent.left; anchors.leftMargin: 60; anchors.verticalCenter: parent.verticalCenter }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 80
                                    radius: 8; color: "#1A1A2E"
                                    RowLayout { anchors.fill: parent; anchors.margins: 12; spacing: 8
                                        Repeater {
                                            model: ["#E53935", "#1E88E5", "#43A047", accentColor]
                                            delegate: Rectangle { Layout.fillWidth: true; height: 40; radius: 6; color: modelData }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    radius: 8; color: "#1A1A2E"
                                    Rectangle { width: 120; height: 16; radius: 4; color: "#3A3A4E"; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 12 }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
