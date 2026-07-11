/* Synthex Calamares Installer Slideshow
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Calamares 1.0 as Calamares

Calamares.Slideshow {
    id: slideshow
    anchors.fill: parent

    property var slides: [
        {
            title:    qsTr("Welcome to SynthOS"),
            subtitle: qsTr("Installing your intelligent Linux desktop…"),
            icon:     "synthex-logo.png",
            body:     qsTr("SynthOS is a next-generation Fedora-based Linux distribution designed to be the definitive Linux desktop experience. Please wait while we configure your system.")
        },
        {
            title:    qsTr("AI-Powered Desktop"),
            subtitle: qsTr("Hermes — Your Native AI Assistant"),
            icon:     "synthex-logo.png",
            body:     qsTr("SynthOS includes Hermes, a fully local AI assistant that works without an internet connection. Powered by Ollama and local LLMs, your data stays private.")
        },
        {
            title:    qsTr("Gaming Ready"),
            subtitle: qsTr("Steam, Proton, MangoHud & more"),
            icon:     "synthex-logo.png",
            body:     qsTr("SynthOS ships with a gaming-optimized kernel, Proton-GE, MangoHud, GameMode, and the Heroic launcher — ready to play from day one.")
        },
        {
            title:    qsTr("Beautiful & Customizable"),
            subtitle: qsTr("Dark amber theme, 9 desktop profiles"),
            icon:     "synthex-logo.png",
            body:     qsTr("Choose from Classic, Gaming, Minimal, Studio, AI Workstation and more. SynthOS adapts to how you work with per-profile theming and app bundles.")
        },
        {
            title:    qsTr("Security Built-In"),
            subtitle: qsTr("SELinux enforcing, LUKS2, Secure Boot"),
            icon:     "synthex-logo.png",
            body:     qsTr("SynthOS enforces SELinux, supports LUKS2 full-disk encryption, Secure Boot, firewalld, and automatic security updates out of the box.")
        },
        {
            title:    qsTr("Almost Ready!"),
            subtitle: qsTr("Finishing up your SynthOS installation…"),
            icon:     "synthex-logo.png",
            body:     qsTr("We're applying the final configuration. Your SynthOS system will be ready in moments. Thank you for choosing SynthOS!")
        }
    ]

    property int currentSlide: 0

    Timer {
        id: slideTimer
        interval: 7000
        running: slideshow.isCurrentPage
        repeat: true
        onTriggered: {
            currentSlide = (currentSlide + 1) % slides.length
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#0B0F1A"

        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width * 0.75
            spacing: 32

            Image {
                Layout.alignment: Qt.AlignHCenter
                source: slides[currentSlide].icon
                width: 80; height: 80
                fillMode: Image.PreserveAspectFit
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: slides[currentSlide].title
                font.pixelSize: 28
                font.bold: true
                color: "#FFB300"
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: slides[currentSlide].subtitle
                font.pixelSize: 16
                color: "#E8E8E8"
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width
                text: slides[currentSlide].body
                font.pixelSize: 13
                color: "#B0B0B0"
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            Row {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                Repeater {
                    model: slides.length
                    Rectangle {
                        width: index === currentSlide ? 20 : 8
                        height: 8
                        radius: 4
                        color: index === currentSlide ? "#FFB300" : "#444444"
                        Behavior on width { NumberAnimation { duration: 200 } }
                    }
                }
            }
        }
    }
}
