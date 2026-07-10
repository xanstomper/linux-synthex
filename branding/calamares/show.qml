// SPDX-License-Identifier: GPL-3.0+
// SynthOS Calamares Installer Slideshow — show.qml
// Displayed during installation. Uses calamares.slideshow API v2.
// Colors: Navy #0B0F1A, Amber #FFB300, Lime #9BBD5C

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    // Auto-advance every 7 seconds
    Timer {
        interval: 7000; running: true; repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 1 — Welcome
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#0B0F1A" }
                GradientStop { position: 1.0; color: "#111827" }
            }

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20
                width: parent.width * 0.7

                // Amber sun logo
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 96; height: 96; radius: 24
                    gradient: Gradient {
                        orientation: Gradient.Vertical
                        GradientStop { position: 0.0; color: "#FFD700" }
                        GradientStop { position: 1.0; color: "#FF8C00" }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "☀"; font.pixelSize: 52; color: "#0B0F1A"
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Welcome to SynthOS"
                    font { pixelSize: 36; weight: Font.Bold; family: "Noto Sans" }
                    color: "#FFFFFF"
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Illuminate Your Desktop"
                    font { pixelSize: 18; family: "Noto Sans" }
                    color: "#FFB300"
                }

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 200; height: 2; radius: 1; color: "#FFB300"; opacity: 0.4
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "SynthOS is installing. This will take a few minutes.\nSit back and explore what's waiting for you."
                    font { pixelSize: 15; family: "Noto Sans" }
                    color: "#8899AA"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 2 — Desktop Profiles
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent; color: "#0B0F1A"

            ColumnLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 24

                Text {
                    text: "Choose Your Desktop Profile"
                    font { pixelSize: 28; weight: Font.Bold; family: "Noto Sans" }
                    color: "#FFB300"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "After install, the Setup Wizard lets you pick the perfect profile."
                    font.pixelSize: 14; color: "#8899AA"
                    Layout.alignment: Qt.AlignHCenter
                }

                Grid {
                    Layout.alignment: Qt.AlignHCenter
                    columns: 3; spacing: 16

                    Repeater {
                        model: [
                            { icon: "🎮", name: "Gaming",      desc: "Steam · Proton · Gamescope" },
                            { icon: "⚡", name: "Focus",       desc: "Minimal · Keyboard-driven"  },
                            { icon: "💻", name: "Pro",         desc: "Dev tools · Containers"      },
                            { icon: "🖥",  name: "Classic",     desc: "Familiar · Windows-like"    },
                            { icon: "🎨", name: "Studio",      desc: "Creative · Media tools"      },
                            { icon: "🤖", name: "AI Hub",      desc: "Local LLM · AI workspace"   },
                        ]
                        delegate: Rectangle {
                            width: 160; height: 82; radius: 12
                            color: "#1A1A2E"; border.color: "#2A2A4E"; border.width: 1

                            ColumnLayout {
                                anchors { fill: parent; margins: 14 }
                                spacing: 4
                                Text { text: modelData.icon; font.pixelSize: 24; Layout.alignment: Qt.AlignHCenter }
                                Text { text: modelData.name;
                                    font { pixelSize: 14; weight: Font.Bold }
                                    color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                                Text { text: modelData.desc; font.pixelSize: 10; color: "#8899AA"
                                    Layout.alignment: Qt.AlignHCenter; horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            }
                        }
                    }
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 3 — Gaming Features
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent; color: "#0B0F1A"

            RowLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 48

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 16

                    Text { text: "🎮"; font.pixelSize: 48 }
                    Text {
                        text: "Built for Gamers"
                        font { pixelSize: 32; weight: Font.Bold; family: "Noto Sans" }
                        color: "#FFB300"
                        wrapMode: Text.WordWrap; Layout.fillWidth: true
                    }
                    Text {
                        text: "SynthOS is optimized for gaming from the ground up. Every component is tuned for maximum performance and minimum latency."
                        font.pixelSize: 14; color: "#8899AA"; wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 10

                    Repeater {
                        model: [
                            ["🟠", "Steam + Proton",          "Play Windows games natively"],
                            ["🟢", "Gamescope Compositor",    "Per-game display scaling & VRR"],
                            ["🔵", "MangoHUD Overlay",        "Real-time FPS, temps & frametime"],
                            ["🟡", "BORE Scheduler",          "Low-latency, responsive kernel"],
                            ["🟣", "GPU Auto-Configure",      "Detects NVIDIA/AMD/Intel auto"],
                            ["⚪", "DXVK + VKD3D + Zink",    "DirectX translation layer stack"],
                            ["🟤", "GameMode daemon",         "CPU/GPU boost during gameplay"],
                            ["🔴", "Flathub + AUR support",   "Thousands of gaming apps"],
                        ]
                        delegate: RowLayout {
                            spacing: 12; Layout.fillWidth: true
                            Text { text: modelData[0]; font.pixelSize: 14 }
                            ColumnLayout {
                                spacing: 1; Layout.fillWidth: true
                                Text { text: modelData[1]; font { pixelSize: 13; weight: Font.Bold }; color: "#FFFFFF" }
                                Text { text: modelData[2]; font.pixelSize: 11; color: "#8899AA" }
                            }
                        }
                    }
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 4 — Developer Tools
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent; color: "#0B0F1A"

            RowLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 48

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 10

                    Repeater {
                        model: [
                            ["🦀", "Rust Toolchain",         "cargo, rustup pre-installed"],
                            ["🐍", "Python 3.12",            "With pip, venv, pyenv ready"],
                            ["📦", "Docker + Podman",        "Containers out of the box"],
                            ["🟩", "Node.js + Bun",          "Modern JS runtime"],
                            ["☕", "Java 21 LTS",            "OpenJDK + Maven + Gradle"],
                            ["🔷", "VS Code + Neovim",       "Editors with Synthex config"],
                            ["🐙", "Git + GitHub CLI",       "Version control & PR flows"],
                            ["🧰", "Make + CMake + Meson",   "Build system tooling"],
                        ]
                        delegate: RowLayout {
                            spacing: 12; Layout.fillWidth: true
                            Text { text: modelData[0]; font.pixelSize: 18 }
                            ColumnLayout {
                                spacing: 1; Layout.fillWidth: true
                                Text { text: modelData[1]; font { pixelSize: 13; weight: Font.Bold }; color: "#FFFFFF" }
                                Text { text: modelData[2]; font.pixelSize: 11; color: "#8899AA" }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 16

                    Text { text: "💻"; font.pixelSize: 48 }
                    Text {
                        text: "A Hacker's Playground"
                        font { pixelSize: 32; weight: Font.Bold; family: "Noto Sans" }
                        color: "#9BBD5C"
                        wrapMode: Text.WordWrap; Layout.fillWidth: true
                    }
                    Text {
                        text: "Everything you need to build, ship, and deploy — pre-configured and ready to code from minute one."
                        font.pixelSize: 14; color: "#8899AA"; wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 5 — AI Features
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent; color: "#0B0F1A"

            ColumnLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 20

                RowLayout {
                    spacing: 16; Layout.alignment: Qt.AlignHCenter
                    Text { text: "🤖"; font.pixelSize: 42 }
                    Text {
                        text: "AI-Native Desktop"
                        font { pixelSize: 32; weight: Font.Bold; family: "Noto Sans" }
                        color: "#FFB300"
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "SynthOS ships with deep AI integration — locally and in the cloud."
                    font.pixelSize: 15; color: "#8899AA"
                }

                Grid {
                    Layout.alignment: Qt.AlignHCenter
                    columns: 2; spacing: 16

                    Repeater {
                        model: [
                            { icon: "🧠", title: "Local LLM Engine",       body: "Ollama + LM Studio built-in\nLlama 3, Mistral, Phi-3 & more" },
                            { icon: "🎙", title: "Voice Commands",          body: "Whisper-powered voice control\nDesktop + terminal + apps"     },
                            { icon: "✨", title: "AI Shell (synth ai)",     body: "Ask in plain English\nRun commands, fix errors"              },
                            { icon: "🔒", title: "Privacy First",           body: "Everything runs offline\nZero telemetry by default"          },
                        ]
                        delegate: Rectangle {
                            width: 280; height: 96; radius: 12
                            color: "#1A1A2E"; border.color: "#2A2A4E"; border.width: 1

                            RowLayout {
                                anchors { fill: parent; margins: 16 }
                                spacing: 14
                                Text { text: modelData.icon; font.pixelSize: 28; Layout.alignment: Qt.AlignTop }
                                ColumnLayout {
                                    spacing: 4; Layout.fillWidth: true
                                    Text { text: modelData.title; font { pixelSize: 14; weight: Font.Bold }; color: "#FFFFFF" }
                                    Text { text: modelData.body; font.pixelSize: 11; color: "#8899AA"
                                        wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 6 — Security & Privacy
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent; color: "#0B0F1A"

            RowLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 40

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 16
                    Text { text: "🛡"; font.pixelSize: 48 }
                    Text {
                        text: "Secure by Default"
                        font { pixelSize: 32; weight: Font.Bold; family: "Noto Sans" }
                        color: "#9BBD5C"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                    }
                    Text {
                        text: "SynthOS ships hardened out of the box.\nNo compromises on your security."
                        font.pixelSize: 15; color: "#8899AA"; wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 12

                    Repeater {
                        model: [
                            ["🔐", "LUKS2 Full-Disk Encryption",   "Optional, configured at install"    ],
                            ["🔥", "Firewalld + nftables",         "Zone-based firewall pre-enabled"    ],
                            ["🔒", "SELinux Enforcing",            "Mandatory Access Control (Fedora)"  ],
                            ["🕵", "AppArmor Profiles",            "Fine-grained app sandboxing"        ],
                            ["🔑", "Secure Boot Ready",            "Signed bootloader & kernel"         ],
                            ["🛡", "SynthGuard IDS",              "Intrusion detection daemon"         ],
                            ["🌐", "DNS-over-HTTPS",               "Encrypted DNS by default"           ],
                            ["🔄", "Automatic Security Updates",   "Critical CVEs patched silently"     ],
                        ]
                        delegate: RowLayout {
                            spacing: 10; Layout.fillWidth: true
                            Text { text: modelData[0]; font.pixelSize: 16 }
                            ColumnLayout {
                                spacing: 1; Layout.fillWidth: true
                                Text { text: modelData[1]; font { pixelSize: 13; weight: Font.Bold }; color: "#FFFFFF" }
                                Text { text: modelData[2]; font.pixelSize: 11; color: "#8899AA" }
                            }
                        }
                    }
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Slide 7 — Get Involved / Community
    // ──────────────────────────────────────────────────────────────────────────
    Slide {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#0B0F1A" }
                GradientStop { position: 1.0; color: "#0D1A0D" }
            }

            ColumnLayout {
                anchors { fill: parent; margins: 48 }
                spacing: 24

                RowLayout {
                    spacing: 16; Layout.alignment: Qt.AlignHCenter
                    Text { text: "🌟"; font.pixelSize: 42 }
                    Text {
                        text: "Almost There!"
                        font { pixelSize: 36; weight: Font.Bold; family: "Noto Sans" }
                        color: "#9BBD5C"
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Your system is being configured. Setup Wizard will launch on first login."
                    font.pixelSize: 16; color: "#8899AA"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap; Layout.fillWidth: true
                }

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 500; height: 1; color: "#2A2A4E"
                }

                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 12
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Find us online"
                        font { pixelSize: 14; weight: Font.Bold }; color: "#FFFFFF"
                    }
                    Repeater {
                        model: [
                            ["🌐", "getsynthex.org",              "https://getsynthex.org"           ],
                            ["💬", "discuss.getsynthex.org",      "Community Forum"                  ],
                            ["🐛", "dev.getsynthex.org",          "Bug Tracker"                      ],
                            ["🐙", "github.com/synthex-linux",    "Open Source on GitHub"            ],
                            ["🎮", "discord.gg/synthex",          "Discord Community"                ],
                        ]
                        delegate: RowLayout {
                            spacing: 12; Layout.alignment: Qt.AlignHCenter
                            Text { text: modelData[0]; font.pixelSize: 16 }
                            Text { text: modelData[1]; font.pixelSize: 13; color: "#FFB300" }
                            Text { text: "·"; color: "#2A2A4E" }
                            Text { text: modelData[2]; font.pixelSize: 12; color: "#8899AA" }
                        }
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "SynthOS 2026.10 · Built with ❤ by the community"
                    font { pixelSize: 13; weight: Font.Bold }; color: "#9BBD5C"
                    topPadding: 10
                }
            }
        }
    }
}
