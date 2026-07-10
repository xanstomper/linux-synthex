// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Control Center — Gaming Page
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import SynthOS.Control 1.0

Kirigami.ScrollablePage {
    id: gamingPage
    title: i18n("Gaming")

    property bool gamemodeActive: false
    property bool mangohudActive: false
    property bool gamemodeSvc: false

    // Poll gamemode status
    Timer {
        interval: 2000; running: true; repeat: true
        onTriggered: {
            gamemodeActive = SynthexBackend.isServiceActive("gamescoped.service")
                || SynthexBackend.execOutput("gamemoderun --status 2>/dev/null | grep -c active || echo 0").trim() !== "0"
            mangohudActive = SynthexBackend.fileExists("/etc/MangoHud/MangoHud.conf")
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        // ── Status bar ──────────────────────────────────────────────────────
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            type: gamemodeActive
                  ? Kirigami.MessageType.Positive
                  : Kirigami.MessageType.Information
            text: gamemodeActive
                  ? "🎮  GameMode is active — CPU/GPU boosted for gaming"
                  : "GameMode is ready. Launch any game with GameMode to boost performance."
            visible: true
        }

        // ── Game Mode ───────────────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("GameMode") }

            RowLayout {
                Kirigami.FormData.label: i18n("Enable GameMode service:")
                Switch {
                    id: gamemodeSwitch
                    checked: SynthexBackend.isServiceEnabled("gamemode.service")
                    onToggled: SynthexBackend.setServiceEnabled("gamemode.service", checked)
                }
                Label {
                    text: gamemodeSwitch.checked ? i18n("Enabled") : i18n("Disabled")
                    color: gamemodeSwitch.checked ? Kirigami.Theme.positiveTextColor
                                                  : Kirigami.Theme.disabledTextColor
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("CPU Governor on game launch:")
                ComboBox {
                    id: cpuGovCombo
                    model: ["performance", "schedutil", "powersave", "ondemand"]
                    currentIndex: {
                        var gov = SynthexBackend.readFile("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").trim()
                        var idx = model.indexOf(gov)
                        return idx >= 0 ? idx : 0
                    }
                    onActivated: SynthexBackend.execAsRoot(
                        "for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo " + currentText + " > $f; done"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Process renice (niceness):")
                Slider {
                    id: reniceSlider
                    from: -20; to: 19; stepSize: 1; value: -10
                    Layout.preferredWidth: 180
                }
                Label { text: reniceSlider.value }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("MangoHud Overlay") }

            RowLayout {
                Kirigami.FormData.label: i18n("MangoHud installed:")
                Kirigami.Icon {
                    source: SynthexBackend.which("mangohud") !== ""
                            ? "emblem-ok-symbolic" : "emblem-error-symbolic"
                    width: 16; height: 16
                }
                Label { text: SynthexBackend.which("mangohud") !== "" ? i18n("Yes") : i18n("Not installed") }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Enable overlay globally:")
                Switch {
                    id: mangohudSwitch
                    checked: {
                        var env = SynthexBackend.readFile("/etc/environment")
                        return env.indexOf("MANGOHUD=1") >= 0
                    }
                    onToggled: {
                        if (checked)
                            SynthexBackend.execAsRoot("grep -q MANGOHUD /etc/environment || echo 'MANGOHUD=1' >> /etc/environment")
                        else
                            SynthexBackend.execAsRoot("sed -i '/^MANGOHUD/d' /etc/environment")
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Preset:")
                ComboBox {
                    model: ["Full", "Performance", "Minimal", "FPS Only"]
                    onActivated: {
                        var presets = {
                            "Full":        "full",
                            "Performance": "cpu_temp,gpu_temp,fps,frametime,ram,vram",
                            "Minimal":     "fps,frametime",
                            "FPS Only":    "fps"
                        }
                        var preset = presets[currentText]
                        SynthexBackend.execAsRoot(
                            "mkdir -p /etc/MangoHud && echo 'legacy_layout=false\n" + preset + "' > /etc/MangoHud/MangoHud.conf"
                        )
                    }
                }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("GPU Configuration") }

            RowLayout {
                Kirigami.FormData.label: i18n("GPU Vendor:")
                Label {
                    text: {
                        var out = SynthexBackend.execOutput("lspci | grep -E 'VGA|3D' | head -1")
                        if (out.indexOf("NVIDIA") >= 0) return "NVIDIA  (proprietary driver available)"
                        if (out.indexOf("AMD")    >= 0) return "AMD  (open-source amdgpu)"
                        if (out.indexOf("Intel")  >= 0) return "Intel  (i915)"
                        return "Unknown"
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("NVIDIA Frame Pacing:")
                Switch {
                    checked: {
                        var env = SynthexBackend.readFile("/etc/environment")
                        return env.indexOf("__GL_YIELD=USLEEP") >= 0
                    }
                    onToggled: {
                        if (checked)
                            SynthexBackend.execAsRoot("grep -q __GL_YIELD /etc/environment || echo '__GL_YIELD=USLEEP' >> /etc/environment")
                        else
                            SynthexBackend.execAsRoot("sed -i '/^__GL_YIELD/d' /etc/environment")
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Wayland (explicit sync):")
                Switch {
                    checked: {
                        var env = SynthexBackend.readFile("/etc/environment")
                        return env.indexOf("ENABLE_EXPLICIT_SYNC=1") >= 0
                    }
                    onToggled: {
                        if (checked)
                            SynthexBackend.execAsRoot("grep -q ENABLE_EXPLICIT_SYNC /etc/environment || echo 'ENABLE_EXPLICIT_SYNC=1' >> /etc/environment")
                        else
                            SynthexBackend.execAsRoot("sed -i '/^ENABLE_EXPLICIT_SYNC/d' /etc/environment")
                    }
                }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Steam & Proton") }

            RowLayout {
                Kirigami.FormData.label: i18n("Steam installed:")
                Label {
                    text: SynthexBackend.which("steam") !== "" ? "✓ Steam" : "✗ Not found"
                    color: SynthexBackend.which("steam") !== ""
                           ? Kirigami.Theme.positiveTextColor
                           : Kirigami.Theme.disabledTextColor
                }
                Button {
                    text: "Install Steam"
                    visible: SynthexBackend.which("steam") === ""
                    onClicked: SynthexBackend.execAsRoot("flatpak install -y flathub com.valvesoftware.Steam")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Default Proton version:")
                ComboBox {
                    id: protonCombo
                    model: {
                        var out = SynthexBackend.execOutput(
                            "ls ~/.steam/steam/compatibilitytools.d/ 2>/dev/null; " +
                            "ls /usr/share/steam/compatibilitytools.d/ 2>/dev/null"
                        )
                        var base = ["Proton GE (recommended)", "Proton Experimental", "Default"]
                        return out.split("\n").filter(x=>x).concat(base)
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Lutris:")
                Label {
                    text: SynthexBackend.which("lutris") !== "" ? "✓ Installed" : "Not installed"
                }
                Button {
                    text: "Install Lutris"
                    visible: SynthexBackend.which("lutris") === ""
                    onClicked: SynthexBackend.execAsRoot("flatpak install -y flathub net.lutris.Lutris")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Heroic (Epic/GOG):")
                Label { text: SynthexBackend.which("heroic") !== "" ? "✓ Installed" : "Not installed" }
                Button {
                    text: "Install Heroic"
                    visible: SynthexBackend.which("heroic") === ""
                    onClicked: SynthexBackend.execAsRoot("flatpak install -y flathub com.heroicgameslauncher.hgl")
                }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Latency & Audio") }

            RowLayout {
                Kirigami.FormData.label: i18n("PipeWire quantum (buffer):")
                ComboBox {
                    model: ["32 (ultra-low latency)", "64 (low latency)", "128 (default)", "256", "512", "1024"]
                    currentIndex: 2
                    onActivated: {
                        var vals = [32, 64, 128, 256, 512, 1024]
                        var q = vals[currentIndex]
                        SynthexBackend.execAsRoot(
                            "mkdir -p /etc/pipewire/pipewire.conf.d && " +
                            "echo 'context.properties = { default.clock.quantum = " + q + " }' > " +
                            "/etc/pipewire/pipewire.conf.d/99-gaming-quantum.conf"
                        )
                    }
                }
            }
        }

        // ── Quick-launch buttons ─────────────────────────────────────────────
        Kirigami.Separator {}
        Label {
            text: i18n("Quick Launch")
            font.bold: true
            font.pixelSize: 14
        }

        GridLayout {
            columns: 4
            Layout.fillWidth: true
            columnSpacing: Kirigami.Units.largeSpacing
            rowSpacing:    Kirigami.Units.smallSpacing

            Repeater {
                model: [
                    { label: "Steam",       cmd: "steam",      icon: "folder-games" },
                    { label: "Lutris",      cmd: "lutris",     icon: "applications-games" },
                    { label: "Heroic",      cmd: "heroic",     icon: "applications-games" },
                    { label: "Retroarch",   cmd: "retroarch",  icon: "applications-games" },
                    { label: "Proton GE",   cmd: "xdg-open https://github.com/GloriousEggroll/proton-ge-custom/releases", icon: "internet-web-browser" },
                    { label: "MangoHud Cfg",cmd: "kate /etc/MangoHud/MangoHud.conf",  icon: "configure" },
                    { label: "GameMode Log",cmd: "gamemoded -l",                       icon: "utilities-log-viewer" },
                    { label: "VkBasalt",    cmd: "xdg-open https://github.com/DadSchoorse/vkBasalt", icon: "configure" }
                ]

                Button {
                    text:    modelData.label
                    icon.name: modelData.icon
                    onClicked: SynthexBackend.exec(modelData.cmd)
                    Layout.preferredWidth: 130
                }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }
}
