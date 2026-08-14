import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: root
    visible: true
    width: Screen.width > 0 ? Screen.width : 1920
    height: Screen.height > 0 ? Screen.height : 1080
    title: "SynthOS Desktop Rice"
    flags: Qt.FramelessWindowHint
    color: "transparent"

    property bool showLauncher: true

    // ── Wallpaper Backdrop ─────────────────────────────────────────────────
    Image {
        id: bgImage
        anchors.fill: parent
        source: "file:///home/jewboy420/linux-synthex/branding/wallpaper/synthex-dark-4k.svg"
        fillMode: Image.PreserveAspectCrop

        // Subtle dark gradient overlay
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: "rgba(10, 14, 20, 0.40)" }
                GradientStop { position: 0.5; color: "rgba(10, 14, 20, 0.25)" }
                GradientStop { position: 1.0; color: "rgba(10, 14, 20, 0.65)" }
            }
        }
    }

    // ── Top Center Status Pill ─────────────────────────────────────────────
    Rectangle {
        id: topPill
        width: 320
        height: 38
        radius: 19
        color: "rgba(18, 22, 31, 0.90)"
        border.color: "rgba(255, 255, 255, 0.08)"
        border.width: 1
        anchors.horizontalCenter: parent.horizontalCenter
        y: 18

        RowLayout {
            anchors.centerIn: parent
            spacing: 10

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: "#7AA2F7"
            }

            Text {
                text: "Tue, 09 August 2022   04:44 PM"
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
        }

        WeatherWidget {
            id: weatherWidget
        }
    }

    // ── Middle Left: Terminal Rice Widget ──────────────────────────────────
    TerminalRiceWidget {
        id: terminalWidget
        x: 48
        y: 300
    }

    // ── Center: Application Launcher Menu ──────────────────────────────────
    LauncherWidget {
        id: launcherWidget
        anchors.centerIn: parent
        visible: root.showLauncher
        opacity: root.showLauncher ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 180 } }
    }

    // ── Top Right: Quick Settings Widget ───────────────────────────────────
    QuickSettingsWidget {
        id: quickSettingsWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 48
    }

    // ── Middle Right: Media Player Widget ──────────────────────────────────
    MediaWidget {
        id: mediaWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 250
    }

    // ── Bottom Right: System Monitor Widget ────────────────────────────────
    SystemMonitorWidget {
        id: systemMonitorWidget
        anchors.right: parent.right
        anchors.rightMargin: 48
        y: 420
    }

    // ── Bottom Center: Floating Island Dock ────────────────────────────────
    Rectangle {
        id: bottomDock
        width: 1000
        height: 64
        radius: 32
        color: "rgba(18, 22, 31, 0.90)"
        border.color: "rgba(255, 255, 255, 0.08)"
        border.width: 1
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 20

            // Left Section (Launcher, Search, Workspaces, Notifications)
            RowLayout {
                spacing: 14

                Rectangle {
                    width: 36
                    height: 36
                    radius: 18
                    color: root.showLauncher ? "rgba(122, 162, 247, 0.2)" : "transparent"
                    Text { text: "⊞"; font.pixelSize: 18; color: root.showLauncher ? "#7AA2F7" : "#9AA1AB"; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.showLauncher = !root.showLauncher
                    }
                }

                Text { text: "🔍"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "🗔"; font.pixelSize: 16; color: "#9AA1AB" }
                Text { text: "🔔"; font.pixelSize: 16; color: "#9AA1AB" }
            }

            Item { Layout.fillWidth: true }

            // Center Pinned Apps
            RowLayout {
                spacing: 18

                Repeater {
                    model: [
                        { name: "Firefox", icon: "🌐", bg: "#FF7139" },
                        { name: "VS Code", icon: "💻", bg: "#007ACC" },
                        { name: "Terminal", icon: "⌨️", bg: "#333333" },
                        { name: "Files", icon: "📁", bg: "#4A90E2" },
                        { name: "SysMon", icon: "📊", bg: "#30D158" },
                        { name: "Spotify", icon: "🎵", bg: "#1DB954" },
                        { name: "Discord", icon: "💬", bg: "#5865F2" }
                    ]

                    Rectangle {
                        width: 40
                        height: 40
                        radius: 10
                        color: modelData.bg

                        Text {
                            text: modelData.icon
                            font.pixelSize: 20
                            anchors.centerIn: parent
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            onEntered: parent.scale = 1.15
                            onExited: parent.scale = 1.0
                        }

                        Behavior on scale { NumberAnimation { duration: 120 } }
                    }
                }
            }

            Item { Layout.fillWidth: true }

            // Right Status Section
            RowLayout {
                spacing: 14

                Text { text: "📶"; font.pixelSize: 15; color: "#9AA1AB" }
                Text { text: "󰂯"; font.pixelSize: 15; color: "#9AA1AB" }
                Text { text: "🔊"; font.pixelSize: 15; color: "#9AA1AB" }
                Text { text: "🔋"; font.pixelSize: 15; color: "#9AA1AB" }

                Text {
                    text: "04:44 PM"
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
