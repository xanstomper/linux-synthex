// SPDX-License-Identifier: GPL-2.0-or-later
// Synthex Calamares Installer Slideshow
// Shown during installation to highlight Synthex features

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15
import calamares.slideshow 1.0

Presentation
{
    id: presentation

    Timer {
        interval: 8000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    // ─── Slide 1: Welcome ─────────────────────────────────────────
    Slide {
        anchors.fill: parent

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Image {
                source: "synthex-logo.png"
                width: 128
                height: 128
                Layout.alignment: Qt.AlignHCenter
                fillMode: Image.PreserveAspectFit
            }

            Text {
                text: "Welcome to Synthex"
                font.pixelSize: 32
                font.bold: true
                color: "#33ccff"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "The definitive Linux desktop experience"
                font.pixelSize: 16
                color: "#b0b0b0"
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    // ─── Slide 2: Features ────────────────────────────────────────
    Slide {
        anchors.fill: parent

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 15

            Text {
                text: "What's Included"
                font.pixelSize: 28
                font.bold: true
                color: "#33ccff"
                Layout.alignment: Qt.AlignHCenter
            }

            Repeater {
                model: [
                    "✓ KDE Plasma Desktop — Beautiful, customizable",
                    "✓ Gaming Ready — Steam, Proton, Gamescope, MangoHUD",
                    "✓ Developer Tools — Rust, Python, VS Code, Docker",
                    "✓ Performance Optimized — BORE Scheduler, ZRAM",
                    "✓ Secure by Default — SELinux, Firewalld, LUKS",
                    "✓ AI-Integrated — Local LLM, Voice Commands",
                ]
                delegate: Text {
                    text: modelData
                    font.pixelSize: 14
                    color: "#ffffff"
                    Layout.alignment: Qt.AlignLeft
                    leftPadding: 40
                }
            }
        }
    }

    // ─── Slide 3: Profiles ────────────────────────────────────────
    Slide {
        anchors.fill: parent

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 15

            Text {
                text: "Choose Your Experience"
                font.pixelSize: 28
                font.bold: true
                color: "#33ccff"
                Layout.alignment: Qt.AlignHCenter
            }

            GridLayout {
                columns: 2
                columnSpacing: 30
                rowSpacing: 10
                Layout.alignment: Qt.AlignHCenter

                Repeater {
                    model: [
                        "Focus", "Minimal & keyboard-driven",
                        "Gaming", "Console-like Big Picture",
                        "Pro", "Developer cockpit",
                        "Classic", "Windows-like familiarity",
                        "Studio", "Content creation suite",
                        "AI", "AI-first workspace",
                    ]
                    delegate: Rectangle {
                        width: 200
                        height: 32
                        color: "transparent"
                        Text {
                            text: modelData
                            font.pixelSize: index % 2 === 0 ? 15 : 13
                            font.bold: index % 2 === 0
                            color: index % 2 === 0 ? "#33ccff" : "#b0b0b0"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }
    }

    // ─── Slide 4: Community ────────────────────────────────────────
    Slide {
        anchors.fill: parent

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "Join the Community"
                font.pixelSize: 28
                font.bold: true
                color: "#33ccff"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Synthex is built by the community, for the community."
                font.pixelSize: 16
                color: "#ffffff"
                Layout.alignment: Qt.AlignHCenter
            }

            Repeater {
                model: [
                    "🌐 Website: https://getsynthex.org",
                    "💬 Forum: https://discuss.getsynthex.org",
                    "🐛 Bug Tracker: https://dev.getsynthex.org",
                    "💻 GitHub: https://github.com/synthex-linux",
                    "🎮 Discord: https://discord.gg/synthex",
                ]
                delegate: Text {
                    text: modelData
                    font.pixelSize: 14
                    color: "#b0b0b0"
                    Layout.alignment: Qt.AlignLeft
                    leftPadding: 40
                }
            }

            Text {
                text: "Thank you for choosing Synthex!"
                font.pixelSize: 18
                font.bold: true
                color: "#00ff88"
                Layout.alignment: Qt.AlignHCenter
                topPadding: 20
            }
        }
    }
}
