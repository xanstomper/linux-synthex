// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Control Center — Controllers & Input Page
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import SynthOS.Control 1.0

Kirigami.ScrollablePage {
    id: controllersPage
    title: i18n("Controllers & Input")

    property var connectedControllers: []
    property bool xpadneoLoaded: false
    property bool hidPlaystationLoaded: false

    Timer {
        interval: 3000; running: true; repeat: true
        onTriggered: {
            var raw = SynthexBackend.execOutput(
                "ls /sys/class/input/ 2>/dev/null | xargs -I{} sh -c 'cat /sys/class/input/{}/device/name 2>/dev/null' | sort -u | grep -v '^$' | head -20"
            )
            connectedControllers = raw.split("\n").filter(x => x.trim())
            xpadneoLoaded     = SynthexBackend.execOutput("lsmod | grep -c xpadneo").trim()     !== "0"
            hidPlaystationLoaded = SynthexBackend.execOutput("lsmod | grep -c hid_playstation").trim() !== "0"
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        // ── Connected controllers ─────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Connected Devices") }
        }

        Rectangle {
            Layout.fillWidth: true
            height: Math.max(connectedControllers.length * 40, 60)
            radius: 8
            color: Qt.rgba(1,1,1,0.04)
            border.color: Kirigami.Theme.separatorColor

            ColumnLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 4

                Repeater {
                    model: connectedControllers.length > 0
                           ? connectedControllers
                           : ["No controllers detected — plug in a device"]
                    delegate: RowLayout {
                        spacing: 8
                        Kirigami.Icon {
                            source: "input-gamepad"
                            width: 20; height: 20
                            color: connectedControllers.length === 0 ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.textColor
                        }
                        Label {
                            text: modelData
                            color: connectedControllers.length === 0 ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.textColor
                        }
                    }
                }
            }
        }

        Button {
            text: i18n("Refresh Device List")
            icon.name: "view-refresh"
            onClicked: {
                var raw = SynthexBackend.execOutput(
                    "ls /sys/class/input/ | xargs -I{} sh -c 'cat /sys/class/input/{}/device/name 2>/dev/null' | sort -u | grep -v '^$'"
                )
                connectedControllers = raw.split("\n").filter(x => x.trim())
            }
        }

        // ── Xbox / xpadneo ────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Xbox Controllers (xpadneo)") }

            RowLayout {
                Kirigami.FormData.label: i18n("xpadneo driver:")
                Kirigami.Icon {
                    source: xpadneoLoaded ? "emblem-ok-symbolic" : "emblem-warning-symbolic"
                    width: 16; height: 16
                }
                Label { text: xpadneoLoaded ? "✓ Loaded" : "Not loaded" }
                Button {
                    text: xpadneoLoaded ? i18n("Unload") : i18n("Load")
                    onClicked: {
                        if (xpadneoLoaded)
                            SynthexBackend.execAsRoot("modprobe -r xpadneo")
                        else
                            SynthexBackend.execAsRoot("modprobe xpadneo")
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Load xpadneo on boot:")
                Switch {
                    checked: SynthexBackend.fileExists("/etc/modules-load.d/xpadneo.conf")
                    onToggled: {
                        if (checked)
                            SynthexBackend.execAsRoot("echo 'xpadneo' > /etc/modules-load.d/xpadneo.conf")
                        else
                            SynthexBackend.execAsRoot("rm -f /etc/modules-load.d/xpadneo.conf")
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Rumble strength:")
                Slider {
                    id: rumbleSlider; from: 0; to: 100; value: 80; stepSize: 5
                    Layout.preferredWidth: 180
                }
                Label { text: rumbleSlider.value + "%" }
                Button {
                    text: i18n("Apply")
                    onClicked: SynthexBackend.execAsRoot(
                        "find /sys/bus/hid/drivers/xpadneo -name 'rumble_attenuation' -exec sh -c 'echo " +
                        Math.round((100 - rumbleSlider.value) * 0.15) + " > {}' \; 2>/dev/null || true"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Deadzone (left stick):")
                Slider {
                    id: deadzoneSlider; from: 0; to: 32767; value: 3000; stepSize: 100
                    Layout.preferredWidth: 180
                }
                Label { text: deadzoneSlider.value }
            }
        }

        // ── PlayStation / DualSense ───────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("PlayStation Controllers (hid-playstation)") }

            RowLayout {
                Kirigami.FormData.label: i18n("hid-playstation driver:")
                Kirigami.Icon {
                    source: hidPlaystationLoaded ? "emblem-ok-symbolic" : "emblem-warning-symbolic"
                    width: 16; height: 16
                }
                Label { text: hidPlaystationLoaded ? "✓ Loaded" : "Not loaded" }
                Button {
                    text: hidPlaystationLoaded ? i18n("Unload") : i18n("Load")
                    onClicked: {
                        if (hidPlaystationLoaded)
                            SynthexBackend.execAsRoot("modprobe -r hid_playstation")
                        else
                            SynthexBackend.execAsRoot("modprobe hid_playstation")
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("DualSense LED brightness:")
                Slider {
                    id: ledBrightness; from: 0; to: 255; value: 128; stepSize: 1
                    Layout.preferredWidth: 180
                }
                Label { text: ledBrightness.value }
                Button {
                    text: i18n("Apply")
                    onClicked: SynthexBackend.execAsRoot(
                        "find /sys/class/leds/ -name '*playstation*brightness' -exec sh -c 'echo " +
                        ledBrightness.value + " > {}' \; 2>/dev/null || true"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Adaptive triggers:")
                Switch {
                    checked: true
                    onToggled: SynthexBackend.execAsRoot(
                        "find /sys/bus/hid/drivers/playstation -name 'trigger_*' -exec sh -c 'echo " +
                        (checked ? "1" : "0") + " > {}' \; 2>/dev/null || true"
                    )
                }
            }
        }

        // ── Nintendo / Switch Pro ─────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Nintendo (hid-nintendo)") }

            RowLayout {
                Kirigami.FormData.label: i18n("hid-nintendo:")
                Label { text: SynthexBackend.execOutput("lsmod | grep -c hid_nintendo").trim() !== "0" ? "✓ Loaded" : "Not loaded" }
                Button {
                    text: i18n("Load Driver")
                    onClicked: SynthexBackend.execAsRoot("modprobe hid_nintendo")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Joycon support (joycond):")
                Label { text: SynthexBackend.isServiceActive("joycond.service") ? "✓ Running" : "Stopped" }
                Switch {
                    checked: SynthexBackend.isServiceEnabled("joycond.service")
                    onToggled: SynthexBackend.setServiceEnabled("joycond.service", checked)
                }
            }
        }

        // ── Input Remapper ────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Input Remapper") }

            RowLayout {
                Kirigami.FormData.label: i18n("Input Remapper:")
                Label { text: SynthexBackend.which("input-remapper-gtk") !== "" ? "✓ Installed" : "Not installed" }
                Button {
                    text: "Open Input Remapper"
                    icon.name: "configure"
                    visible: SynthexBackend.which("input-remapper-gtk") !== ""
                    onClicked: SynthexBackend.exec("input-remapper-gtk")
                }
                Button {
                    text: "Install"
                    visible: SynthexBackend.which("input-remapper-gtk") === ""
                    onClicked: SynthexBackend.execAsRoot("dnf install -y input-remapper")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("AntiMicroX:")
                Label { text: SynthexBackend.which("antimicrox") !== "" ? "✓ Installed" : "Not installed" }
                Button {
                    text: "Open"
                    visible: SynthexBackend.which("antimicrox") !== ""
                    onClicked: SynthexBackend.exec("antimicrox")
                }
                Button {
                    text: "Install Flatpak"
                    visible: SynthexBackend.which("antimicrox") === ""
                    onClicked: SynthexBackend.execAsRoot("flatpak install -y flathub io.github.antimicrox.antimicrox")
                }
            }
        }

        // ── Bluetooth ─────────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Bluetooth") }

            RowLayout {
                Kirigami.FormData.label: i18n("Bluetooth service:")
                Label {
                    text: SynthexBackend.isServiceActive("bluetooth.service") ? "✓ Running" : "Stopped"
                    color: SynthexBackend.isServiceActive("bluetooth.service")
                           ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.disabledTextColor
                }
                Switch {
                    checked: SynthexBackend.isServiceEnabled("bluetooth.service")
                    onToggled: SynthexBackend.setServiceEnabled("bluetooth.service", checked)
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Pair new device:")
                Button {
                    text: i18n("Open Bluetooth Manager")
                    icon.name: "preferences-system-bluetooth"
                    onClicked: SynthexBackend.exec("bluedevil-wizard || bluetooth-sendto || dolphin")
                }
            }
        }

        // ── udev rules ────────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("udev Rules") }

            RowLayout {
                Kirigami.FormData.label: i18n("steam-devices rules:")
                Kirigami.Icon {
                    source: SynthexBackend.fileExists("/usr/lib/udev/rules.d/70-steam-input.rules")
                            ? "emblem-ok-symbolic" : "emblem-warning-symbolic"
                    width: 16; height: 16
                }
                Button {
                    text: i18n("Reinstall Rules")
                    onClicked: SynthexBackend.execAsRoot(
                        "dnf reinstall -y steam-devices 2>/dev/null || flatpak run --command=true com.valvesoftware.Steam 2>/dev/null || true"
                    )
                }
                Button {
                    text: i18n("Reload udev")
                    onClicked: SynthexBackend.execAsRoot("udevadm control --reload-rules && udevadm trigger")
                }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }
}
