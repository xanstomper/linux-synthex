import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: bluetoothPage
    anchors.fill: parent

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color cardBg: "#161C24"
    readonly property color itemBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property bool bluetoothEnabled: true
    property bool isScanning: true

    ScrollView {
        anchors.fill: parent
        anchors.margins: 28
        clip: true

        ColumnLayout {
            width: bluetoothPage.width - 56
            spacing: 22

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: bluetoothPage.accentColor
                    Text { text: "󰂯"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Bluetooth & Devices"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: bluetoothPage.textColor }
                    Text { text: "Pair headphones, mice, keyboards, game controllers, and audio receivers"; font.family: "Inter"; font.pixelSize: 12; color: bluetoothPage.mutedText }
                }

                Item { Layout.fillWidth: true }

                Switch {
                    checked: bluetoothPage.bluetoothEnabled
                    onToggled: bluetoothPage.bluetoothEnabled = checked
                }
            }

            // Paired Devices List
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: bluetoothPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: pairedCol.implicitHeight + 32
                visible: bluetoothPage.bluetoothEnabled

                ColumnLayout {
                    id: pairedCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text { text: "PAIRED & CONNECTED DEVICES"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: bluetoothPage.accentColor }

                    Repeater {
                        model: [
                            { name: "Sony WH-1000XM5", type: "󰋋", connected: true, battery: 85, profile: "LDAC Audio (Hi-Res)" },
                            { name: "Logitech MX Master 3S", type: "󰍽", connected: true, battery: 92, profile: "HID Pointer Device" },
                            { name: "Keychron Q1 Pro", type: "󰌌", connected: true, battery: 70, profile: "HID Keyboard" },
                            { name: "Xbox Wireless Controller", type: "󰊴", connected: false, battery: 0, profile: "Game Controller" }
                        ]

                        Rectangle {
                            Layout.fillWidth: true
                            height: 52
                            radius: 8
                            color: modelData.connected ? "#1a7aa2f7" : bluetoothPage.itemBg
                            border.color: modelData.connected ? bluetoothPage.accentColor : "#15ffffff"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 12

                                Text { text: modelData.type; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: bluetoothPage.accentColor }

                                ColumnLayout {
                                    spacing: 1
                                    Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 13; font.bold: modelData.connected; color: "#FFFFFF" }
                                    Text { text: modelData.profile + (modelData.connected ? (" • " + modelData.battery + "% Battery") : " • Disconnected"); font.family: "Inter"; font.pixelSize: 11; color: bluetoothPage.mutedText }
                                }

                                Item { Layout.fillWidth: true }

                                Button {
                                    text: modelData.connected ? "Disconnect" : "Connect"
                                    contentItem: Text { text: parent.text; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: modelData.connected ? "#F7768E" : "#FFFFFF" }
                                    background: Rectangle { color: modelData.connected ? "#1af7768e" : "#257aa2f7"; border.color: modelData.connected ? "#F7768E" : bluetoothPage.accentColor; radius: 6; implicitWidth: 90; implicitHeight: 28 }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
