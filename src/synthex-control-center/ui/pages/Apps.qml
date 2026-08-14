import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: appsPage
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
            width: appsPage.width - 56
            spacing: 22

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: appsPage.accentColor
                    Text { text: "󰀻"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Applications & Defaults"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: appsPage.textColor }
                    Text { text: "Default application handlers, autostart programs, and Flatpak permissions"; font.family: "Inter"; font.pixelSize: 12; color: appsPage.mutedText }
                }
            }

            // Default Applications Card
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: appsPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: defCol.implicitHeight + 32

                ColumnLayout {
                    id: defCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    Text { text: "DEFAULT APPLICATIONS"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: appsPage.accentColor }

                    Repeater {
                        model: [
                            { role: "Web Browser", current: "Firefox", icon: "󰈹", options: ["Firefox", "Chromium", "Brave"] },
                            { role: "Mail Client", current: "Thunderbird", icon: "󰇮", options: ["Thunderbird", "None"] },
                            { role: "File Manager", current: "COSMIC Files", icon: "󰉋", options: ["COSMIC Files", "Nautilus", "Thunar"] },
                            { role: "Terminal Emulator", current: "Kitty", icon: "󰆍", options: ["Kitty", "Alacritty", "Foot"] },
                            { role: "Text / Code Editor", current: "Helix", icon: "󰨞", options: ["Helix", "VS Code", "Neovim"] }
                        ]

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14

                            Text { text: modelData.icon; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: appsPage.accentColor }
                            Text { text: modelData.role; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.preferredWidth: 160 }
                            Item { Layout.fillWidth: true }
                            ComboBox {
                                model: modelData.options
                                Layout.preferredWidth: 200
                            }
                        }
                    }
                }
            }
        }
    }
}
