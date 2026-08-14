import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: displaysPage
    anchors.fill: parent

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color cardBg: "#161C24"
    readonly property color itemBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property string currentResolution: "3840 x 2160 (4K UHD)"
    property string currentRefresh: "144 Hz"
    property int currentScale: 150
    property bool vrrEnabled: true
    property bool nightLightEnabled: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.nightLight : false

    ScrollView {
        anchors.fill: parent
        anchors.margins: 28
        clip: true

        ColumnLayout {
            width: displaysPage.width - 56
            spacing: 22

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: displaysPage.accentColor
                    Text { text: "󰍹"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Displays & Monitors"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: displaysPage.textColor }
                    Text { text: "Monitor arrangement, resolution, refresh rate, fractional scaling, and Night Light"; font.family: "Inter"; font.pixelSize: 12; color: displaysPage.mutedText }
                }
            }

            // Visual Monitor Layout Canvas
            Rectangle {
                Layout.fillWidth: true
                height: 170
                radius: 12
                color: displaysPage.cardBg
                border.color: "#1fffffff"

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 16

                    // Display 1 (Primary)
                    Rectangle {
                        width: 220; height: 124; radius: 8
                        color: "#257aa2f7"
                        border.color: displaysPage.accentColor
                        border.width: 2

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            Text { text: "󰍹"; font.family: "Symbols Nerd Font"; font.pixelSize: 28; color: displaysPage.accentColor; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Display 1 (Primary)"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "3840×2160 @ 144Hz"; font.family: "Inter"; font.pixelSize: 10; color: displaysPage.mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                }
            }

            // Display Properties Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: displaysPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: propCol.implicitHeight + 32

                ColumnLayout {
                    id: propCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Text { text: "DISPLAY SETTINGS & SCALING"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: displaysPage.accentColor }

                    // Resolution Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "Resolution"; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.preferredWidth: 160 }
                        Item { Layout.fillWidth: true }
                        ComboBox {
                            model: ["3840 x 2160 (16:9 4K UHD)", "2560 x 1440 (16:9 QHD)", "1920 x 1080 (16:9 FHD)"]
                            Layout.preferredWidth: 260
                        }
                    }

                    // Refresh Rate Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "Refresh Rate"; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.preferredWidth: 160 }
                        Item { Layout.fillWidth: true }
                        ComboBox {
                            model: ["144 Hz (Variable / VRR)", "120 Hz", "60 Hz (Standard)"]
                            Layout.preferredWidth: 260
                        }
                    }

                    // Fractional Scale Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "Scale"; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.preferredWidth: 160 }
                        Item { Layout.fillWidth: true }
                        RowLayout {
                            spacing: 8
                            Repeater {
                                model: [100, 125, 150, 175, 200]
                                Rectangle {
                                    width: 48; height: 32; radius: 6
                                    color: displaysPage.currentScale === modelData ? "#307aa2f7" : displaysPage.itemBg
                                    border.color: displaysPage.currentScale === modelData ? displaysPage.accentColor : "#15ffffff"
                                    Text { text: modelData + "%"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: "#FFFFFF"; anchors.centerIn: parent }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: displaysPage.currentScale = modelData }
                                }
                            }
                        }
                    }

                    // VRR Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        ColumnLayout {
                            spacing: 1
                            Text { text: "Variable Refresh Rate (VRR / FreeSync)"; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF" }
                            Text { text: "Dynamically matches display refresh rate to GPU framerate to eliminate tearing"; font.family: "Inter"; font.pixelSize: 11; color: displaysPage.mutedText }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            checked: displaysPage.vrrEnabled
                            onToggled: displaysPage.vrrEnabled = checked
                        }
                    }
                }
            }

            // Night Light Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: displaysPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: nlCol.implicitHeight + 32

                ColumnLayout {
                    id: nlCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "󰖔"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: "#E5A84B" }
                        ColumnLayout {
                            spacing: 1
                            Text { text: "Night Light (Blue Light Filter)"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            Text { text: "Reduces blue light radiation in the evening to reduce eye strain"; font.family: "Inter"; font.pixelSize: 11; color: displaysPage.mutedText }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            checked: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.nightLight : false
                            onToggled: {
                                if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.toggleNightLight(checked)
                            }
                        }
                    }
                }
            }
        }
    }
}
