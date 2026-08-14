// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Gaming Center — Main Window
// Provides: game library, launcher, performance overlay, per-game profiles

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

Kirigami.ApplicationWindow {
    id: root
    title: "SynthOS Gaming Center"
    minimumWidth: 1100
    minimumHeight: 720

    // ── Theming ──────────────────────────────────────────────────────────────
    readonly property color bgBase:    "#08080F"
    readonly property color bgCard:    "#111118"
    readonly property color accent:    "#6C88A8"
    readonly property color accentDim: "#99700A"
    readonly property color textPrim:  "#FFFFFF"
    readonly property color textMuted: "#9AA1AB"
    readonly property color green:     "#00EE88"
    readonly property color red:       "#FF4444"

    // ── State ────────────────────────────────────────────────────────────────
    property string currentPage: "library"
    property bool gamemodeActive: false
    property string searchQuery: ""

    // Poll gamemode status via synthex-gaming-mode IPC every 3 s
    Timer {
        interval: 3000; running: true; repeat: true
        onTriggered: {
            gamemodeSocket.send("STATUS")
        }
    }

    // Lightweight Unix-socket client for synthex-gaming-mode
    // Reads: "active\n" → gamemodeActive = true; "inactive\n" → false
    // Falls back gracefully if the socket isn't present (no gaming features).
    property var _gamemodeSocket: null
    Component.onCompleted: {
        gamemodeSocket.open()
    }
    Component.onDestruction: {
        gamemodeSocket.close()
    }

    // QML LocalSocket (Qt5/Qt6)
    LocalSocket {
        id: gamemodeSocket
        serverName: "/run/synthex/gaming-mode.sock"

        onConnected:    send("STATUS")
        onDisconnected: gamemodeActive = false
        onError:        gamemodeActive = false   // socket not available → show as OFF

        onReadyRead: {
            var reply = String(readAll()).trim()
            if (reply === "active")   gamemodeActive = true
            else                       gamemodeActive = false
        }

        function send(msg) {
            if (state === LocalSocket.ConnectedState) {
                write(msg + "\n")
            } else {
                // Reconnect and retry
                open()
            }
        }
    }

    // ── Header ───────────────────────────────────────────────────────────────
    pageStack.globalToolBar.style: Kirigami.ApplicationHeaderStyle.ToolBar

    globalDrawer: Kirigami.GlobalDrawer {
        title: "Gaming Center"
        titleIcon: "applications-games"
        isMenu: false
        modal: false
        width: 200

        Kirigami.Theme.colorSet: Kirigami.Theme.Window

        actions: [
            Kirigami.Action {
                text: i18n("Library")
                icon.name: "folder-games"
                checked: currentPage === "library"
                onTriggered: { currentPage = "library"; pageStack.replace(libraryPage) }
            },
            Kirigami.Action {
                text: i18n("Store")
                icon.name: "applications-internet"
                checked: currentPage === "store"
                onTriggered: { currentPage = "store"; pageStack.replace(storePage) }
            },
            Kirigami.Action {
                text: i18n("Performance")
                icon.name: "preferences-system"
                checked: currentPage === "performance"
                onTriggered: { currentPage = "performance"; pageStack.replace(performancePage) }
            },
            Kirigami.Action {
                text: i18n("Controllers")
                icon.name: "input-gamepad"
                checked: currentPage === "controllers"
                onTriggered: { currentPage = "controllers"; pageStack.replace(controllersPage) }
            },
            Kirigami.Action {
                text: i18n("Proton")
                icon.name: "system-software-install"
                checked: currentPage === "proton"
                onTriggered: { currentPage = "proton"; pageStack.replace(protonPage) }
            },
            Kirigami.Action {
                text: i18n("Settings")
                icon.name: "configure"
                checked: currentPage === "settings"
                onTriggered: { currentPage = "settings"; pageStack.replace(settingsPage) }
            }
        ]

        // GameMode badge at bottom of drawer
        footer: Rectangle {
            width: parent.width; height: 48
            color: gamemodeActive ? Qt.rgba(0,0.8,0.4,0.15) : Qt.rgba(1,1,1,0.04)
            border.color: gamemodeActive ? "#00AA55" : "#333344"
            border.width: 1

            RowLayout {
                anchors.centerIn: parent; spacing: 8
                Rectangle {
                    width: 8; height: 8; radius: 4
                    color: gamemodeActive ? root.green : "#555566"
                }
                Label {
                    text: gamemodeActive ? "GameMode ON" : "GameMode OFF"
                    color: gamemodeActive ? root.green : root.textMuted
                    font.pixelSize: 12; font.bold: gamemodeActive
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    // Optimistically flip the indicator, then confirm via IPC
                    var desired = !gamemodeActive
                    gamemodeSocket.send(desired ? "ENABLE" : "DISABLE")
                    // The timer poll will correct the UI if the IPC call fails
                }
            }
        }
    }

    // ── Pages ─────────────────────────────────────────────────────────────────
    Component {
        id: libraryPage
        Kirigami.ScrollablePage {
            title: i18n("Game Library")

            header: ToolBar {
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                    spacing: 8

                    TextField {
                        placeholderText: "Search games…"
                        Layout.fillWidth: true
                        leftInset: 8; leftPadding: 36
                        onTextChanged: searchQuery = text

                        Kirigami.Icon {
                            anchors.left: parent.left; anchors.leftMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            source: "search"
                            width: 18; height: 18
                            color: root.textMuted
                        }
                    }

                    ComboBox {
                        model: ["All Games", "Steam", "Lutris", "Heroic", "Native", "Flatpak"]
                        Layout.preferredWidth: 140
                    }

                    ComboBox {
                        model: ["Recently Played", "A–Z", "Play Time", "Rating"]
                        Layout.preferredWidth: 150
                    }

                    ToolButton {
                        icon.name: "view-list-icons"
                        checkable: true; checked: true
                    }
                    ToolButton {
                        icon.name: "view-list-details"
                        checkable: true
                    }
                }
            }

            // Game grid
            GridLayout {
                columns: Math.max(1, Math.floor(parent.width / 220))
                columnSpacing: 12; rowSpacing: 12

                Repeater {
                    model: gameLibraryModel
                    delegate: GameCard {
                        name:       model.name
                        cover:      model.cover
                        launcher:   model.launcher
                        playtime:   model.playtime
                        lastPlayed: model.lastPlayed
                    }
                }
            }

            // Empty state
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                visible: gameLibraryModel.count === 0
                icon.name: "folder-games"
                text: i18n("No games in library")
                explanation: i18n("Install Steam, Lutris, or Heroic to start building your library.")
                helpfulAction: Kirigami.Action {
                    text: i18n("Open App Manager")
                    icon.name: "system-software-install"
                    onTriggered: Qt.openUrlExternally("synthex://apps")
                }
            }
        }
    }

    Component {
        id: performancePage
        Kirigami.ScrollablePage {
            title: i18n("Gaming Performance")

            ColumnLayout {
                spacing: Kirigami.Units.largeSpacing

                // Live metrics row
                RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Layout.fillWidth: true

                    Repeater {
                        model: [
                            { label: "CPU",   icon: "cpu",              value: "—%" },
                            { label: "GPU",   icon: "video-display",    value: "—%" },
                            { label: "RAM",   icon: "memory",           value: "— GB" },
                            { label: "VRAM",  icon: "video-display",    value: "— MB" },
                            { label: "FPS",   icon: "chronometer",      value: "—" },
                            { label: "Temp",  icon: "temperature-warm", value: "—°C" }
                        ]

                        Rectangle {
                            Layout.fillWidth: true; height: 72
                            radius: 8
                            color: Qt.rgba(1,1,1,0.05)
                            border.color: Kirigami.Theme.separatorColor

                            ColumnLayout {
                                anchors.centerIn: parent; spacing: 4
                                Kirigami.Icon {
                                    source: modelData.icon
                                    width: 22; height: 22
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label { text: modelData.value; font.bold: true; font.pixelSize: 14; Layout.alignment: Qt.AlignHCenter }
                                Label { text: modelData.label; font.pixelSize: 10; color: root.textMuted; Layout.alignment: Qt.AlignHCenter }
                            }
                        }
                    }
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true
                    Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("GameMode") }

                    RowLayout {
                        Kirigami.FormData.label: i18n("Enable GameMode daemon:")
                        Switch {
                            id: gmdSwitch
                            checked: gamemodeActive
                            onToggled: {
                                // Forward the toggle to the gaming-mode IPC socket.
                                // gamemodeSocket is defined near the top of the file;
                                // the timer poll will reconcile the UI if IPC fails.
                                gamemodeSocket.send(checked ? "ENABLE" : "DISABLE")
                            }
                        }
                    }

                    RowLayout {
                        Kirigami.FormData.label: i18n("CPU governor (game launch):")
                        ComboBox {
                            model: ["performance", "schedutil", "powersave"]
                            currentIndex: 0
                        }
                    }

                    Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("MangoHud Overlay") }

                    RowLayout {
                        Kirigami.FormData.label: i18n("Enable MangoHud overlay:")
                        Switch { checked: false }
                    }

                    RowLayout {
                        Kirigami.FormData.label: i18n("Overlay preset:")
                        ComboBox { model: ["Full", "Performance", "FPS Only", "Minimal"] }
                    }

                    Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("GPU Optimization") }

                    RowLayout {
                        Kirigami.FormData.label: i18n("Wayland explicit sync:")
                        Switch { checked: true }
                    }

                    RowLayout {
                        Kirigami.FormData.label: i18n("PipeWire quantum (ms latency):")
                        ComboBox { model: ["32 (1ms)", "64 (1.3ms)", "128 (2.6ms)", "256 (5.3ms)"] }
                    }
                }
            }
        }
    }

    Component {
        id: storePage
        Kirigami.ScrollablePage {
            title: i18n("Game Store")
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                icon.name: "applications-internet"
                text: i18n("Game Store")
                explanation: i18n("Browse Steam, itch.io, and GOG.\nOpens in your default browser.")
                helpfulAction: Kirigami.Action {
                    text: i18n("Open Steam Store")
                    icon.name: "applications-internet"
                    onTriggered: Qt.openUrlExternally("https://store.steampowered.com")
                }
            }
        }
    }

    Component { id: controllersPage; GamingControllers {} }
    Component { id: protonPage;      ProtonManager {} }
    Component { id: settingsPage;    GamingSettings {} }

    // ── Models ────────────────────────────────────────────────────────────────
    ListModel {
        id: gameLibraryModel
        // Populated at runtime by synthex-gaming-center backend
    }

    // ── Initial page ──────────────────────────────────────────────────────────
    Component.onCompleted: pageStack.push(libraryPage)
}
