import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 460
    height: 280
    radius: 18
    color: "#12161F"
    border.color: "rgba(255, 255, 255, 0.08)"
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Window Title Bar (Mac-style traffic dots + Title) ──────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            color: "rgba(255, 255, 255, 0.02)"
            radius: 18

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14

                // Window Controls
                RowLayout {
                    spacing: 8
                    Rectangle { width: 12; height: 12; radius: 6; color: "#FF5F56" }
                    Rectangle { width: 12; height: 12; radius: 6; color: "#FFBD2E" }
                    Rectangle { width: 12; height: 12; radius: 6; color: "#27C93F" }
                }

                Item { Layout.preferredWidth: 16 }

                // Prompt Title
                Text {
                    text: "~  xanstomper@synth"
                    font.family: "JetBrains Mono"
                    font.pixelSize: 12
                    color: "#9AA1AB"
                    Layout.alignment: Qt.AlignVCenter
                }

                Item { Layout.fillWidth: true }
            }
        }

        // ── Terminal Body (rxfetch Output) ─────────────────────────────────
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                // Command invocation
                Text {
                    text: "rxfetch"
                    font.family: "JetBrains Mono"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#7AA2F7"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 24

                    // ASCII Art Logo ("S")
                    ColumnLayout {
                        spacing: 2
                        Text { text: "       .---.       "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#7AA2F7" }
                        Text { text: "     /       \\     "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#7AA2F7" }
                        Text { text: "    |   .--.  |    "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#82A0BE" }
                        Text { text: "    `--'   / /     "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#ABA2E4" }
                        Text { text: "          / /      "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#BB9AF7" }
                        Text { text: "     .---' /       "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#BB9AF7" }
                        Text { text: "    |  .--'        "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#D97C82" }
                        Text { text: "     \\       /     "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#F7768E" }
                        Text { text: "      `-----'      "; font.family: "JetBrains Mono"; font.pixelSize: 11; color: "#F7768E" }
                    }

                    // System Specs
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Repeater {
                            model: [
                                { k: "os", v: "synth OS", color: "#F7768E" },
                                { k: "ker", v: "6.3.9-synth", color: "#FF9E64" },
                                { k: "pkgs", v: "1247", color: "#E0AF68" },
                                { k: "sh", v: "fish", color: "#9ECE6A" },
                                { k: "wm", v: "Hyprland", color: "#73DACA" },
                                { k: "term", v: "alacritty", color: "#7AA2F7" },
                                { k: "ram", v: "5.21G / 15.6G", color: "#BB9AF7" },
                                { k: "disk", v: "82G / 232G", color: "#F7768E" }
                            ]

                            RowLayout {
                                spacing: 14
                                Text {
                                    text: modelData.k
                                    font.family: "JetBrains Mono"
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: modelData.color
                                    Layout.preferredWidth: 36
                                }
                                Text {
                                    text: modelData.v
                                    font.family: "JetBrains Mono"
                                    font.pixelSize: 12
                                    color: "#DDE3EB"
                                }
                            }
                        }
                    }
                }

                // Rainbow color blocks strip
                RowLayout {
                    spacing: 0
                    Layout.alignment: Qt.AlignRight
                    Layout.rightMargin: 12

                    Repeater {
                        model: ["#F7768E", "#FF9E64", "#E0AF68", "#9ECE6A", "#73DACA", "#7AA2F7", "#BB9AF7", "#C0CAF5"]
                        Rectangle {
                            width: 24
                            height: 6
                            color: modelData
                            radius: (index === 0) ? 3 : ((index === 7) ? 3 : 0)
                        }
                    }
                }
            }
        }
    }
}
