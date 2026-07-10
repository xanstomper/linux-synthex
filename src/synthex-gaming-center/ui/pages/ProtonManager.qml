// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

Kirigami.ScrollablePage {
    title: i18n("Proton & Wine Manager")

    property var installedVersions: []
    property string downloadStatus: ""

    function refreshVersions() {
        var raw = [
            // Check Steam compat tools
            "ls ~/.steam/steam/compatibilitytools.d/ 2>/dev/null",
            "ls ~/snap/steam/common/.local/share/Steam/compatibilitytools.d/ 2>/dev/null"
        ].join("; ")
        var out = Qt.platform.os === "linux"
                  ? "" // Would call SynthexBackend.execOutput(raw) in real build
                  : ""
        installedVersions = out.split("\n").filter(x => x.trim())
    }

    Component.onCompleted: refreshVersions()

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: true
            type: Kirigami.MessageType.Information
            text: i18n("Proton GE versions add support for more games and fix compatibility issues. Install alongside the official Steam Proton.")
        }

        // ── Installed versions ────────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Installed Proton Versions") }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 200; radius: 8
            color: "#0D0D15"; border.color: "#222233"

            ScrollView {
                anchors.fill: parent; anchors.margins: 8

                ListView {
                    model: installedVersions.length > 0 ? installedVersions : ["Proton Experimental (Steam built-in)", "Proton 9.0 (Steam built-in)"]
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        icon.name: "application-x-executable"
                        text: modelData
                        highlighted: false
                    }
                }
            }
        }

        Button {
            text: i18n("Refresh")
            icon.name: "view-refresh"
            onClicked: refreshVersions()
        }

        // ── Proton GE installer ───────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Install Proton GE") }

            RowLayout {
                Kirigami.FormData.label: i18n("ProtonUp-Qt:")
                Button {
                    text: i18n("Open ProtonUp-Qt")
                    icon.name: "system-software-install"
                    onClicked: Qt.openUrlExternally("net.davidotek.pupgui2") // Flatpak app ID
                }
                Button {
                    text: i18n("Install ProtonUp-Qt")
                    onClicked: {} // flatpak install net.davidotek.pupgui2
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Quick install latest GE:")
                Button {
                    text: i18n("Install Proton-GE Latest")
                    icon.name: "list-add"
                    onClicked: geDialog.open()
                }
                Label {
                    text: downloadStatus
                    color: "#FFB300"
                    visible: downloadStatus !== ""
                }
            }
        }

        // ── Wine standalone ───────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Wine / Wine-GE") }

            RowLayout {
                Kirigami.FormData.label: i18n("Wine installed:")
                Label { text: "wine --version 2>/dev/null | head -1" }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("DXVK version:")
                Label { text: "Check via winecfg" }
                Button { text: i18n("winecfg"); onClicked: {} }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Winetricks:")
                Button { text: i18n("Open Winetricks"); icon.name: "configure"; onClicked: {} }
            }
        }

        // ── Lutris Wine builds ────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Lutris Wine Runners") }

            RowLayout {
                Kirigami.FormData.label: i18n("Lutris runners path:")
                Label { text: "~/.local/share/lutris/runners/"; font.pixelSize: 11; color: "#8899AA" }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Manage via Lutris:")
                Button { text: i18n("Open Lutris"); icon.name: "applications-games"; onClicked: {} }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }

    Dialog {
        id: geDialog
        title: i18n("Install Proton-GE")
        width: 450; standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            spacing: 8
            Label { text: i18n("This will download the latest Proton-GE from GitHub\nand install it to ~/.steam/steam/compatibilitytools.d/"); wrapMode: Text.WordWrap }
            Label { text: i18n("Requires: curl, jq"); color: "#8899AA"; font.pixelSize: 11 }
        }

        onAccepted: {
            downloadStatus = "Downloading Proton-GE…"
            // In real build: SynthexBackend.exec("protonup-qt" or script)
        }
    }
}
