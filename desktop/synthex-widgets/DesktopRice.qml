import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    width: 1920
    height: 1080
    visible: true

    property bool showLauncher: false
    property bool showCustomizer: false

    // ── Background Wallpaper ───────────────────────────────────────────────
    Image {
        id: bgWallpaper
        anchors.fill: parent
        source: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.wallpaperPath : "file:///home/jewboy420/linux-synthex/branding/wallpaper/synthex-dark-4k.svg"
        fillMode: Image.PreserveAspectCrop

        // Subtle dark gradient overlay
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#660a0e14" }
                GradientStop { position: 0.5; color: "#400a0e14" }
                GradientStop { position: 1.0; color: "#a60a0e14" }
            }
        }
    }

    // ── Top Center Status Pill ─────────────────────────────────────────────
    Rectangle {
        id: topPill
        width: 340
        height: 38
        radius: 19
        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.dockColor : "#e612161f"
        border.color: "#14ffffff"
        border.width: 1
        anchors.horizontalCenter: parent.horizontalCenter
        y: 18
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["topPill"] !== false)

        RowLayout {
            anchors.centerIn: parent
            spacing: 10

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
            }

            Text {
                text: (new Date().toLocaleDateString(Qt.locale(), "ddd, dd MMMM yyyy")) + "   " + (new Date().toLocaleTimeString(Qt.locale(), "hh:mm AP"))
                font.family: "Inter"
                font.pixelSize: 13
                font.bold: true
                color: "#DDE3EB"
            }
        }
    }

    // ── Top Left: Clock & Weather Widgets ──────────────────────────────────
    ColumnLayout {
        x: 48
        y: 48
        spacing: 16

        ClockWidget {
            id: clockWidget
            visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["clock"] !== false)
        }

        WeatherWidget {
            id: weatherWidget
            visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["weather"] !== false)
        }
    }

    // ── Middle Left: Terminal Rice Widget ──────────────────────────────────
    TerminalRiceWidget {
        id: terminalWidget
        x: 48
        y: 300
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["terminalRice"] !== false)
    }

    // ── Center: Application Launcher Menu ──────────────────────────────────
    LauncherWidget {
        id: launcherWidget
        anchors.centerIn: parent
        visible: root.showLauncher
        opacity: root.showLauncher ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 180 } }
    }

    // ── Center: Rice & Desktop Customizer Panel ────────────────────────────
    RiceSettingsWidget {
        id: customizerWidget
        anchors.centerIn: parent
        visible: root.showCustomizer
        opacity: root.showCustomizer ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 180 } }
        onCloseRequested: root.showCustomizer = false
    }

    // ── Top Right: Quick Settings Widget ───────────────────────────────────
    QuickSettingsWidget {
        id: quickSettingsWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 48
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["quickSettings"] !== false)
    }

    // ── Middle Right: Media Player / Media Center ──────────────────────────
    MediaWidget {
        id: mediaWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 310
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["mediaPlayer"] !== false)
    }

    // ── Bottom Right: System Monitor Widget ────────────────────────────────
    SystemMonitorWidget {
        id: systemMonitorWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 520
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["systemMonitor"] !== false)
    }

    // ── Bottom Center: Floating Island Dock ────────────────────────────────
    Rectangle {
        id: bottomDock
        width: 1040
        height: (typeof systemBridge !== "undefined" && systemBridge) ? (systemBridge.dockSize + 24) : 64
        radius: height / 2
        color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.dockColor : "#e612161f"
        border.color: "#14ffffff"
        border.width: 1
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        visible: (!systemBridge || !systemBridge.widgetsConfig || systemBridge.widgetsConfig["dock"] !== false)

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 20

            // Left Section (Launcher, Search, Workspaces, Customizer, Notifications)
            RowLayout {
                spacing: 12

                Rectangle {
                    width: 36
                    height: 36
                    radius: 18
                    color: root.showLauncher ? "#337aa2f7" : "transparent"
                    Text { text: "󰀻"; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: root.showLauncher ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#9AA1AB"; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.showCustomizer = false
                            root.showLauncher = !root.showLauncher
                        }
                    }
                }

                Text { text: "󰍉"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "󰹟"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }

                // Customizer Toggle Button
                Rectangle {
                    width: 36
                    height: 36
                    radius: 18
                    color: root.showCustomizer ? "#337aa2f7" : "transparent"
                    Text { text: "󰒓"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: root.showCustomizer ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#9AA1AB"; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.showLauncher = false
                            root.showCustomizer = !root.showCustomizer
                        }
                    }
                }

                Text { text: "󰂚"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }
            }

            Item { Layout.fillWidth: true }

            // Center Pinned Apps
            RowLayout {
                spacing: 18

                Repeater {
                    model: [
                        { name: "Firefox", icon: "󰈹", bg: "#FF7139", cmd: "firefox" },
                        { name: "VS Code", icon: "󰨞", bg: "#007ACC", cmd: "code" },
                        { name: "Terminal", icon: "󰆍", bg: "#24292E", cmd: "kitty || alacritty" },
                        { name: "Files", icon: "󰉋", bg: "#4A90E2", cmd: "dolphin || nautilus || thunar" },
                        { name: "SysMon", icon: "󰍹", bg: "#30D158", cmd: "plasma-systemmonitor || btop" },
                        { name: "Spotify", icon: "󰓇", bg: "#1DB954", cmd: "spotify" },
                        { name: "Discord", icon: "󰙯", bg: "#5865F2", cmd: "discord || vesktop" }
                    ]

                    Rectangle {
                        width: 40
                        height: 40
                        radius: 10
                        color: modelData.bg

                        Text {
                            text: modelData.icon
                            font.family: "Symbols Nerd Font"
                            font.pixelSize: 20
                            color: "#FFFFFF"
                            anchors.centerIn: parent
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            onEntered: parent.scale = 1.15
                            onExited: parent.scale = 1.0
                            onClicked: {
                                if (typeof systemBridge !== "undefined" && systemBridge) {
                                    systemBridge.launchApp(modelData.cmd)
                                }
                            }
                        }

                        Behavior on scale { NumberAnimation { duration: 120 } }
                    }
                }
            }

            Item { Layout.fillWidth: true }

            // Right Status Section
            RowLayout {
                spacing: 14

                Text { text: "󰤨"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "󰂯"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "󰕾"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "󰁹"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#9AA1AB" }

                Text {
                    text: (new Date().toLocaleTimeString(Qt.locale(), "hh:mm AP"))
                    font.family: "Inter"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#DDE3EB"
                    Layout.leftMargin: 4
                }
            }
        }
    }
}
