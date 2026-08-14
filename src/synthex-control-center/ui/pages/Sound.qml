import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: soundPage
    anchors.fill: parent

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color cardBg: "#161C24"
    readonly property color itemBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    ScrollView {
        anchors.fill: parent
        anchors.margins: 28
        clip: true

        ColumnLayout {
            width: soundPage.width - 56
            spacing: 22

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: soundPage.accentColor
                    Text { text: "󰕾"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Sound & Audio Routing"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: soundPage.textColor }
                    Text { text: "PipeWire output devices, master volume, input microphones, and app streams"; font.family: "Inter"; font.pixelSize: 12; color: soundPage.mutedText }
                }
            }

            // Output Devices Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: soundPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: outCol.implicitHeight + 32

                ColumnLayout {
                    id: outCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Text { text: "AUDIO OUTPUT DEVICE"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: soundPage.accentColor }

                    Repeater {
                        model: [
                            { id: "@DEFAULT_AUDIO_SINK@", name: "Headphones (Sony WH-1000XM5 LDAC)", icon: "󰋋", active: true },
                            { id: "alsa_output.pci.analog-stereo", name: "Built-in Realtek HD Audio (Speakers)", icon: "󰕾", active: false },
                            { id: "alsa_output.pci.hdmi-stereo", name: "HDMI / DisplayPort Audio (NVIDIA GeForce)", icon: "󰍹", active: false }
                        ]

                        Rectangle {
                            Layout.fillWidth: true
                            height: 48
                            radius: 8
                            color: modelData.active ? "#207aa2f7" : soundPage.itemBg
                            border.color: modelData.active ? soundPage.accentColor : "#15ffffff"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 12

                                Text { text: modelData.icon; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: soundPage.accentColor }
                                Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 13; font.bold: modelData.active; color: "#FFFFFF"; Layout.fillWidth: true }
                                Text { visible: modelData.active; text: "󰄬 ACTIVE SINK"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: soundPage.accentColor }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setAudioOutput(modelData.id)
                                }
                            }
                        }
                    }

                    // Master Volume Slider
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Layout.topMargin: 8

                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Master Volume"; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.volumePct : 82) + "%"
                                font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: soundPage.accentColor
                            }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0; to: 100; stepSize: 1
                            value: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.volumePct : 82
                            onMoved: {
                                if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setVolume(value)
                            }
                        }
                    }
                }
            }

            // Input Microphone Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: soundPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: inCol.implicitHeight + 32

                ColumnLayout {
                    id: inCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text { text: "AUDIO INPUT (MICROPHONE)"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: soundPage.accentColor }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "󰍬"; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: soundPage.accentColor }
                        Text { text: "Internal Studio Dual-Array Microphone"; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.fillWidth: true }
                        Text { text: "Noise Suppression Active"; font.family: "Inter"; font.pixelSize: 11; color: "#73DACA" }
                    }
                }
            }
        }
    }
}
