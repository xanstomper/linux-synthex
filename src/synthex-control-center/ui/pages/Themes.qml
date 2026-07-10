// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Control Center — Themes Page
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import SynthOS.Control 1.0

Kirigami.ScrollablePage {
    id: themesPage
    title: i18n("Themes & Appearance")

    property string currentProfile: SynthexBackend.profileJson("profile") || "classic"
    property string currentColorScheme: SynthexBackend.execOutput(
        "kreadconfig6 --file kdeglobals --group General --key ColorScheme").trim()
    property string currentFont: SynthexBackend.execOutput(
        "kreadconfig6 --file kdeglobals --group General --key font").trim()

    // Profile data
    readonly property var profiles: [
        { id: "classic",  name: "Classic",  desc: "Dark amber — balanced for all users",    icon: "user-desktop",          laf: "org.synthos.desktop.classic"  },
        { id: "gaming",   name: "Gaming",   desc: "High-contrast neon — reduced latency",    icon: "applications-games",    laf: "org.synthos.desktop.gaming"   },
        { id: "focus",    name: "Focus",    desc: "Minimal chrome — distraction-free",       icon: "view-fullscreen",       laf: "org.synthos.desktop.focus"    },
        { id: "pro",      name: "Pro",      desc: "Productivity suite — 4 virtual desks",    icon: "applications-office",   laf: "org.synthos.desktop.pro"      },
        { id: "studio",   name: "Studio",   desc: "Creative workstation — media-focused",    icon: "applications-multimedia",laf: "org.synthos.desktop.studio"  },
        { id: "ai",       name: "AI",       desc: "AI-integrated desktop — local LLM ready", icon: "dialog-information",    laf: "org.synthos.desktop.ai"       },
        { id: "lite",     name: "Lite",     desc: "Lightweight — older/low-RAM hardware",    icon: "computer",              laf: "org.synthos.desktop.lite"     }
    ]

    readonly property var colorSchemes: [
        { id: "SynthexDarkAmber",    name: "Dark Amber",       preview: "#0A0A0F:#FFBA00:#FFD060" },
        { id: "SynthexGamingDark",   name: "Gaming Neon",      preview: "#070712:#00FF87:#00CFFF" },
        { id: "SynthexFocusDark",    name: "Focus Mono",       preview: "#0D0D0D:#E0E0E0:#888888" },
        { id: "SynthexProDark",      name: "Pro Dark",         preview: "#0E0E1A:#AAAAFF:#7070CC" },
        { id: "SynthexStudio",       name: "Studio",           preview: "#121218:#CC88FF:#9955DD" },
        { id: "SynthexAI",           name: "AI Teal",          preview: "#0A0F12:#00DDCC:#0099AA" },
        { id: "SynthexLite",         name: "Lite (light)",     preview: "#F5F5F0:#333333:#888888" },
        { id: "SynthexMidnight",     name: "Midnight",         preview: "#060610:#8888FF:#5555BB" },
        { id: "SynthexOceanBlue",    name: "Ocean Blue",       preview: "#050D1A:#2299FF:#0055BB" },
        { id: "SynthexSolarized",    name: "Solarized",        preview: "#002B36:#268BD2:#2AA198" }
    ]

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        // ── Desktop Profile ──────────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Desktop Profile") }
        }

        // Profile cards grid
        GridLayout {
            columns: 4
            Layout.fillWidth: true
            columnSpacing: Kirigami.Units.smallSpacing
            rowSpacing:    Kirigami.Units.smallSpacing

            Repeater {
                model: profiles
                delegate: Rectangle {
                    Layout.preferredWidth:  170
                    Layout.preferredHeight: 80
                    radius: 8
                    color: modelData.id === currentProfile
                           ? Qt.rgba(Kirigami.Theme.highlightColor.r,
                                     Kirigami.Theme.highlightColor.g,
                                     Kirigami.Theme.highlightColor.b, 0.25)
                           : Qt.rgba(1,1,1,0.04)
                    border.color: modelData.id === currentProfile
                                  ? Kirigami.Theme.highlightColor : "transparent"
                    border.width: 2

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4
                        Kirigami.Icon {
                            source:   modelData.icon
                            width:    24; height: 24
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: modelData.name
                            font.bold: modelData.id === currentProfile
                            font.pixelSize: 13
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: modelData.desc
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: 155
                            opacity: 0.7
                            Layout.alignment: Qt.AlignHCenter
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            currentProfile = modelData.id
                            applyProfileBtn.enabled = true
                        }
                    }
                }
            }
        }

        Button {
            id: applyProfileBtn
            text: i18n("Apply Profile: %1", currentProfile.charAt(0).toUpperCase() + currentProfile.slice(1))
            enabled: false
            icon.name: "dialog-ok-apply"
            Layout.alignment: Qt.AlignRight
            onClicked: {
                SynthexBackend.exec("/usr/lib/synthex/apply-profile.sh " + currentProfile)
                enabled = false
                toast.text = "Profile applied. Plasma will reload."
                toast.visible = true
            }
        }

        Kirigami.InlineMessage {
            id: toast
            Layout.fillWidth: true
            type: Kirigami.MessageType.Positive
            showCloseButton: true
            visible: false
        }

        // ── Color Scheme ─────────────────────────────────────────────────────
        Kirigami.Separator {}
        Label { text: i18n("Color Scheme"); font.bold: true; font.pixelSize: 14 }

        GridLayout {
            columns: 5
            Layout.fillWidth: true
            columnSpacing: Kirigami.Units.smallSpacing
            rowSpacing:    Kirigami.Units.smallSpacing

            Repeater {
                model: colorSchemes
                delegate: ColumnLayout {
                    spacing: 4
                    Rectangle {
                        width: 100; height: 50
                        radius: 6
                        border.color: modelData.id === currentColorScheme
                                      ? Kirigami.Theme.highlightColor : "#33333366"
                        border.width: modelData.id === currentColorScheme ? 2 : 1

                        // Three-bar preview of bg / accent1 / accent2
                        Row {
                            anchors.fill: parent
                            spacing: 0
                            Repeater {
                                model: modelData.preview.split(":")
                                Rectangle {
                                    width: 33; height: parent.height
                                    color: modelData
                                    radius: index === 0 ? 6 : (index === 2 ? 6 : 0)
                                }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                currentColorScheme = modelData.id
                                SynthexBackend.exec("plasma-apply-colorscheme " + modelData.id)
                            }
                        }
                    }
                    Label {
                        text: modelData.name
                        font.pixelSize: 10
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }

        // ── Fonts ─────────────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Fonts") }

            RowLayout {
                Kirigami.FormData.label: i18n("UI Font:")
                ComboBox {
                    model: ["Noto Sans", "Source Sans Pro", "Ubuntu", "Cantarell", "Inter", "Roboto", "IBM Plex Sans"]
                    currentIndex: {
                        var f = currentFont.split(",")[0]
                        var idx = model.indexOf(f)
                        return idx >= 0 ? idx : 0
                    }
                    onActivated: SynthexBackend.exec(
                        "kwriteconfig6 --file kdeglobals --group General --key font '" + currentText + ",11,-1,5,50,0,0,0,0,0'"
                    )
                }
                SpinBox { from: 8; to: 18; value: 11
                    onValueChanged: SynthexBackend.exec(
                        "kwriteconfig6 --file kdeglobals --group General --key font 'Noto Sans," + value + ",-1,5,50,0,0,0,0,0'"
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Fixed-width font:")
                ComboBox {
                    model: ["Noto Sans Mono", "JetBrains Mono", "Fira Code", "Cascadia Code", "Iosevka", "Hack"]
                }
                SpinBox { from: 8; to: 18; value: 11 }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("DPI scaling:")
                Slider {
                    id: dpiSlider; from: 0.75; to: 3.0; stepSize: 0.25; value: 1.0
                    Layout.preferredWidth: 200
                }
                Label { text: (dpiSlider.value * 100).toFixed(0) + "%" }
                Button {
                    text: i18n("Apply")
                    onClicked: SynthexBackend.exec(
                        "kwriteconfig6 --file kdeglobals --group KScreen --key ScaleFactor " + dpiSlider.value
                    )
                }
            }
        }

        // ── Cursor & Icons ────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Icons & Cursor") }

            RowLayout {
                Kirigami.FormData.label: i18n("Icon theme:")
                ComboBox {
                    model: SynthexBackend.execOutput(
                        "ls /usr/share/icons/ | grep -v default | grep -v hicolor | head -20"
                    ).split("\n").filter(x=>x).concat(["Bibata-Modern-Amber","Papirus","Papirus-Dark","breeze","breeze-dark"])
                    onActivated: SynthexBackend.exec(
                        "kwriteconfig6 --file kdeglobals --group Icons --key Theme " + currentText
                    )
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Cursor theme:")
                ComboBox {
                    model: ["Bibata-Modern-Classic", "Bibata-Modern-Amber", "breeze_cursors", "breeze-dark", "default"]
                    onActivated: SynthexBackend.exec(
                        "kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme " + currentText
                    )
                }
                ComboBox {
                    model: ["Small (24)", "Medium (32)", "Large (48)", "XL (64)"]
                    onActivated: {
                        var sizes = [24, 32, 48, 64]
                        SynthexBackend.exec(
                            "kwriteconfig6 --file kcminputrc --group Mouse --key cursorSize " + sizes[currentIndex]
                        )
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Wallpaper:")
                Button {
                    text: i18n("Browse…")
                    icon.name: "folder-pictures"
                    onClicked: wallpaperDialog.open()
                }
                Label {
                    id: wallpaperLabel
                    text: i18n("Current wallpaper")
                    font.pixelSize: 10
                    opacity: 0.7
                }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }

    // Wallpaper file dialog (stub — real one uses QML Platform.FileDialog)
    Dialog {
        id: wallpaperDialog
        title: i18n("Select Wallpaper")
        width: 500; height: 100
        standardButtons: Dialog.Ok | Dialog.Cancel
        Label { text: i18n("Wallpaper picker — open Plasma system settings for full selection.") }
        onAccepted: SynthexBackend.exec("systemsettings --section wallpaper")
    }
}
