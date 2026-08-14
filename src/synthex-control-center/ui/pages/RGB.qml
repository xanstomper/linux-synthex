// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Control Center — RGB & Peripherals Page
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import SynthOS.Control 1.0

Kirigami.ScrollablePage {
    id: rgbPage
    title: i18n("RGB & Peripherals")

    property var detectedDevices: []
    property string openrgbStatus: SynthexBackend.isServiceActive("openrgb.service") ? "running" : "stopped"
    property color selectedColor: "#6C88A8"

    Timer {
        interval: 3000; running: true; repeat: true
        onTriggered: {
            openrgbStatus = SynthexBackend.isServiceActive("openrgb.service") ? "running" : "stopped"
            var raw = SynthexBackend.execOutput("openrgb --list-devices 2>/dev/null | grep -E '^[0-9]' | head -16")
            detectedDevices = raw.split("\n").filter(x => x.trim())
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            type: openrgbStatus === "running" ? Kirigami.MessageType.Positive : Kirigami.MessageType.Warning
            text: openrgbStatus === "running"
                  ? "✓  OpenRGB daemon is running — devices are managed"
                  : "OpenRGB daemon is stopped. Start it to control RGB lighting."
            visible: true
            actions: [
                Kirigami.Action {
                    text: openrgbStatus === "running" ? i18n("Stop") : i18n("Start")
                    icon.name: openrgbStatus === "running" ? "media-playback-stop" : "media-playback-start"
                    onTriggered: {
                        if (openrgbStatus === "running")
                            SynthexBackend.execAsRoot("systemctl stop openrgb.service")
                        else
                            SynthexBackend.execAsRoot("systemctl start openrgb.service")
                    }
                }
            ]
        }

        // ── OpenRGB ──────────────────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("OpenRGB") }

            RowLayout {
                Kirigami.FormData.label: i18n("Autostart on boot:")
                Switch {
                    checked: SynthexBackend.isServiceEnabled("openrgb.service")
                    onToggled: SynthexBackend.setServiceEnabled("openrgb.service", checked)
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("SDK server port:")
                SpinBox { from: 1000; to: 65535; value: 6742
                    onValueChanged: SynthexBackend.execAsRoot(
                        "sed -i 's/--server-port [0-9]*/--server-port " + value + "/' /etc/openrgb/openrgb.service.d/override.conf 2>/dev/null || true"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Detected devices:")
                Label {
                    text: detectedDevices.length > 0 ? detectedDevices.length + " device(s)" : "None detected / daemon stopped"
                    color: detectedDevices.length > 0 ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.disabledTextColor
                }
                Button {
                    text: i18n("Open OpenRGB UI")
                    icon.name: "preferences-desktop-color"
                    onClicked: SynthexBackend.exec("openrgb")
                }
            }
        }

        // Device list
        ListView {
            Layout.fillWidth: true
            height: Math.min(detectedDevices.length * 36, 200)
            model: detectedDevices
            visible: detectedDevices.length > 0
            clip: true

            delegate: ItemDelegate {
                width: ListView.view.width
                text: modelData
                icon.name: "input-gaming"
                highlighted: false
            }
        }

        // ── Color picker ─────────────────────────────────────────────────────
        Kirigami.Separator {}
        Label { text: i18n("Quick Color Picker"); font.bold: true; font.pixelSize: 14 }

        GridLayout {
            columns: 12
            rowSpacing: 4; columnSpacing: 4

            Repeater {
                model: [
                    "#FF0000","#FF4400","#FF8800","#FFBB00","#FFFF00","#88FF00",
                    "#00FF00","#00FFAA","#00FFFF","#0088FF","#8800FF","#FF00FF",
                    "#FFFFFF","#CCCCCC","#888888","#444444","#222222","#000000",
                    "#FF6600","#FFBA00","#99FF00","#00FF66","#00CCFF","#CC00FF"
                ]
                Rectangle {
                    width: 28; height: 28; radius: 4
                    color: modelData
                    border.color: modelData === selectedColor.toString() ? "white" : "transparent"
                    border.width: 2
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            selectedColor = modelData
                            colorHex.text = modelData.replace("#","")
                        }
                    }
                }
            }
        }

        RowLayout {
            Label { text: "#" }
            TextField {
                id: colorHex
                text: "6C88A8"
                maximumLength: 6
                Layout.preferredWidth: 80
                validator: RegularExpressionValidator { regularExpression: /[0-9A-Fa-f]{0,6}/ }
                onEditingFinished: selectedColor = "#" + text
            }
            Rectangle {
                width: 32; height: 32; radius: 4
                color: "#" + colorHex.text
                border.color: "#666"; border.width: 1
            }
            Button {
                text: i18n("Apply to All Devices")
                icon.name: "color-picker"
                onClicked: SynthexBackend.execAsRoot(
                    "openrgb --color " + colorHex.text + " 2>/dev/null || true"
                )
            }
            Button {
                text: i18n("Apply to Device…")
                icon.name: "configure"
                onClicked: deviceDialog.open()
            }
        }

        // ── Profiles ─────────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Lighting Profiles") }

            RowLayout {
                Kirigami.FormData.label: i18n("Load profile:")
                ComboBox {
                    id: profileCombo
                    model: {
                        var raw = SynthexBackend.execOutput("ls ~/.config/OpenRGB/*.orp 2>/dev/null")
                        return raw.split("\n").filter(x=>x).map(x=>x.replace(/.*\//,"").replace(".orp",""))
                                  .concat(["— no profiles found —"])
                    }
                }
                Button {
                    text: i18n("Load")
                    onClicked: SynthexBackend.execAsRoot(
                        "openrgb --profile ~/.config/OpenRGB/" + profileCombo.currentText + ".orp 2>/dev/null"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Save current as:")
                TextField { id: newProfileName; placeholderText: "my-profile"; Layout.preferredWidth: 140 }
                Button {
                    text: i18n("Save")
                    onClicked: SynthexBackend.exec(
                        "openrgb --save-profile ~/.config/OpenRGB/" + newProfileName.text + " 2>/dev/null"
                    )
                }
            }
        }

        // ── Piper (Razer/mouse) ───────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Piper (Razer / Gaming Mice)") }

            RowLayout {
                Kirigami.FormData.label: i18n("Piper installed:")
                Kirigami.Icon {
                    source: SynthexBackend.which("piper") !== "" ? "emblem-ok-symbolic" : "emblem-error-symbolic"
                    width: 16; height: 16
                }
                Label { text: SynthexBackend.which("piper") !== "" ? "Yes" : "No" }
                Button {
                    text: "Install Piper"
                    visible: SynthexBackend.which("piper") === ""
                    onClicked: SynthexBackend.execAsRoot("dnf install -y piper")
                }
                Button {
                    text: "Open Piper"
                    visible: SynthexBackend.which("piper") !== ""
                    onClicked: SynthexBackend.exec("piper")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("ratbagd service:")
                Label {
                    text: SynthexBackend.isServiceActive("ratbagd.service") ? "✓ Running" : "Stopped"
                    color: SynthexBackend.isServiceActive("ratbagd.service")
                           ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.disabledTextColor
                }
                Switch {
                    checked: SynthexBackend.isServiceEnabled("ratbagd.service")
                    onToggled: SynthexBackend.setServiceEnabled("ratbagd.service", checked)
                }
            }
        }

        // ── Solaar ────────────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Solaar (Logitech Unifying)") }

            RowLayout {
                Kirigami.FormData.label: i18n("Solaar installed:")
                Label { text: SynthexBackend.which("solaar") !== "" ? "✓ Yes" : "Not installed" }
                Button {
                    text: "Open Solaar"
                    visible: SynthexBackend.which("solaar") !== ""
                    icon.name: "input-mouse"
                    onClicked: SynthexBackend.exec("solaar")
                }
                Button {
                    text: "Install Solaar"
                    visible: SynthexBackend.which("solaar") === ""
                    onClicked: SynthexBackend.execAsRoot("dnf install -y solaar")
                }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }

    Dialog {
        id: deviceDialog
        title: i18n("Apply Color to Device")
        width: 380; height: 160
        standardButtons: Dialog.Ok | Dialog.Cancel
        ColumnLayout {
            spacing: 8
            Label { text: i18n("Device index (0-based):") }
            SpinBox { id: deviceIdx; from: 0; to: 15; value: 0 }
        }
        onAccepted: SynthexBackend.execAsRoot(
            "openrgb --device " + deviceIdx.value + " --color " + colorHex.text + " 2>/dev/null"
        )
    }
}
