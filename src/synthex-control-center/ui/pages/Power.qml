import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: powerPage
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
            width: powerPage.width - 56
            spacing: 22

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: powerPage.accentColor
                    Text { text: "󰁹"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Power & Battery"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: powerPage.textColor }
                    Text { text: "Power saving modes, battery health diagnostics, and screen sleep timers"; font.family: "Inter"; font.pixelSize: 12; color: powerPage.mutedText }
                }
            }

            // Power Profiles Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: powerPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: profCol.implicitHeight + 32

                ColumnLayout {
                    id: profCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Text { text: "HARDWARE POWER PROFILES"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: powerPage.accentColor }

                    Repeater {
                        model: [
                            { key: "balanced", name: "Balanced Mode", desc: "Dynamic CPU frequency scaling based on workload demand", icon: "󰾆" },
                            { key: "performance", name: "High Performance", desc: "Unrestricted CPU clocks & high GPU boost states for intense workloads", icon: "󰓅" },
                            { key: "powersave", name: "Power Saver", desc: "Optimizes thermal dissipation and battery lifetime for travel", icon: "󰌪" }
                        ]

                        Rectangle {
                            Layout.fillWidth: true
                            height: 60
                            radius: 8
                            color: ((typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === modelData.key) ? "#207aa2f7" : powerPage.itemBg)
                            border.color: ((typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === modelData.key) ? powerPage.accentColor : "#15ffffff")

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 14

                                Text { text: modelData.icon; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: powerPage.accentColor }
                                ColumnLayout {
                                    spacing: 1
                                    Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                                    Text { text: modelData.desc; font.family: "Inter"; font.pixelSize: 11; color: powerPage.mutedText }
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    visible: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === modelData.key)
                                    text: "󰄬 ACTIVE"
                                    font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: powerPage.accentColor
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setPerformanceMode(modelData.key)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
