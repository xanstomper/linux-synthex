import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 660
    height: 720
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 20
    color: "#e612161f" // Liquid Glass translucent base
    border.color: "#30ffffff"
    border.width: 1

    signal closeRequested()

    property int activeTab: 0

    // Liquid Glass Specular Sheen
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#25ffffff" }
            GradientStop { position: 0.06; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 14

        // ── 1. Top Header Bar ──────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Rectangle {
                width: 32
                height: 32
                radius: 8
                color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"

                Text {
                    text: "󰒓"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 18
                    color: "#FFFFFF"
                    anchors.centerIn: parent
                }
            }

            ColumnLayout {
                spacing: 1
                Text {
                    text: "Desktop Studio & Rice Customizer"
                    font.family: "Inter"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#FFFFFF"
                }
                Text {
                    text: "Refine every pixel, geometry, acoustic curve, and color profile"
                    font.family: "Inter"
                    font.pixelSize: 11
                    color: "#A0AAB8"
                }
            }

            Item { Layout.fillWidth: true }

            // Close Button
            Rectangle {
                width: 30
                height: 30
                radius: 15
                color: "#1affffff"
                Text {
                    text: "✕"
                    font.family: "Inter"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#A0AAB8"
                    anchors.centerIn: parent
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.closeRequested()
                }
            }
        }

        // ── 2. Studio Tabs ─────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: [
                    { idx: 0, icon: "🎨", name: "Appearance" },
                    { idx: 1, icon: "🧩", name: "Widgets" },
                    { idx: 2, icon: "🖼", name: "Wallpaper" },
                    { idx: 3, icon: "🎵", name: "Acoustics" },
                    { idx: 4, icon: "💾", name: "Presets" }
                ]

                Rectangle {
                    Layout.fillWidth: true
                    height: 34
                    radius: 8
                    color: root.activeTab === modelData.idx ? "#307aa2f7" : "#08ffffff"
                    border.color: root.activeTab === modelData.idx ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "transparent"

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Text { text: modelData.icon; font.pixelSize: 13 }
                        Text {
                            text: modelData.name
                            font.family: "Inter"
                            font.pixelSize: 12
                            font.bold: root.activeTab === modelData.idx
                            color: root.activeTab === modelData.idx ? "#FFFFFF" : "#A0AAB8"
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.activeTab = modelData.idx
                    }

                    Behavior on color { ColorAnimation { duration: 140 } }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#0fffffff"
        }

        // ── 3. Tab Contents ────────────────────────────────────────────────
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            // ══════ TAB 0: APPEARANCE & THEMES ══════
            ColumnLayout {
                width: root.width - 40
                spacing: 18
                visible: root.activeTab === 0

                // Visual Finish Mode
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text { text: "VISUAL FINISH & MATERIAL"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        // Liquid Glass
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 52; radius: 10
                            color: ((!systemBridge || systemBridge.styleMode === "glass") ? "#257aa2f7" : "#08ffffff")
                            border.color: ((!systemBridge || systemBridge.styleMode === "glass") ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#1fffffff")
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 10; spacing: 10
                                Text { text: "✨"; font.pixelSize: 18 }
                                ColumnLayout {
                                    spacing: 1
                                    Text { text: "Liquid Glass"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF" }
                                    Text { text: "Translucent sheen & blur"; font.family: "Inter"; font.pixelSize: 10; color: "#A0AAB8" }
                                }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setStyleMode("glass") } }
                        }

                        // Solid Matte
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 52; radius: 10
                            color: (systemBridge && systemBridge.styleMode === "matte") ? "#257aa2f7" : "#08ffffff"
                            border.color: (systemBridge && systemBridge.styleMode === "matte") ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#1fffffff"
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 10; spacing: 10
                                Text { text: "⬛"; font.pixelSize: 18 }
                                ColumnLayout {
                                    spacing: 1
                                    Text { text: "Solid Matte"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF" }
                                    Text { text: "Deep slate, crisp focus"; font.family: "Inter"; font.pixelSize: 10; color: "#A0AAB8" }
                                }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setStyleMode("matte") } }
                        }
                    }
                }

                // Theme Presets Grid (9 Complete Themes)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text { text: "CURATED THEME PRESETS"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                    GridLayout {
                        columns: 3
                        rowSpacing: 8
                        columnSpacing: 8
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "nova", name: "Nova Ice", color: "#141923", accent: "#7AA2F7" },
                                { key: "tokyonight", name: "Tokyo Night", color: "#1A1B26", accent: "#7AA2F7" },
                                { key: "catppuccin", name: "Catppuccin", color: "#1E1E2E", accent: "#89B4FA" },
                                { key: "nord", name: "Nord Frost", color: "#2E3440", accent: "#88C0D0" },
                                { key: "cyberpunk", name: "Cyberpunk", color: "#0D0D18", accent: "#00F0FF" },
                                { key: "oled", name: "OLED Midnight", color: "#0A0A0A", accent: "#60A5FA" },
                                { key: "gruvbox", name: "Gruvbox Dark", color: "#282828", accent: "#D79921" },
                                { key: "rosepine", name: "Rosé Pine", color: "#191724", accent: "#EB6F92" },
                                { key: "synthwave", name: "Synthwave '84", color: "#1E122B", accent: "#FF71CE" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                radius: 8
                                color: modelData.color
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? modelData.accent : "#1fffffff"
                                border.width: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? 2 : 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 8

                                    Rectangle { width: 14; height: 14; radius: 7; color: modelData.accent }
                                    Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF"; Layout.fillWidth: true; elide: Text.ElideRight }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setTheme(modelData.key)
                                    }
                                }
                            }
                        }
                    }
                }

                // Custom Accent Palette
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text { text: "CUSTOM ACCENT PALETTE"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                    RowLayout {
                        spacing: 10

                        Repeater {
                            model: ["#7AA2F7", "#BB9AF7", "#73DACA", "#E5A84B", "#F7768E", "#9ECE6A", "#00F0FF", "#FF007F", "#FE8019", "#EB6F92"]

                            Rectangle {
                                width: 32; height: 32; radius: 16
                                color: modelData
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.accentColor === modelData) ? "#FFFFFF" : "transparent"
                                border.width: 2.5

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setAccentColor(modelData)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ══════ TAB 1: WIDGETS & GEOMETRY ══════
            ColumnLayout {
                width: root.width - 40
                spacing: 18
                visible: root.activeTab === 1

                // Corner Radius Slider
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "CORNER ROUNDING GEOMETRY"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }
                        Item { Layout.fillWidth: true }
                        Text { text: ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18) + " px"; font.family: "Inter"; font.pixelSize: 11; color: "#A0AAB8" }
                    }

                    Slider {
                        Layout.fillWidth: true
                        from: 0; to: 32; stepSize: 1
                        value: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
                        onMoved: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setCornerRadius(value) }
                    }
                }

                // Dock Position & Size
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text { text: "FLOATING DOCK SCALE & POSITION"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                    RowLayout {
                        spacing: 10

                        Repeater {
                            model: [
                                { size: 32, label: "Compact (32px)" },
                                { size: 40, label: "Standard (40px)" },
                                { size: 48, label: "Large (48px)" },
                                { size: 56, label: "Expanded (56px)" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 8
                                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dockSize === modelData.size) ? "#307aa2f7" : "#08ffffff"
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dockSize === modelData.size) ? "#7AA2F7" : "transparent"

                                Text {
                                    text: modelData.label
                                    font.family: "Inter"
                                    font.pixelSize: 11
                                    font.bold: true
                                    color: "#FFFFFF"
                                    anchors.centerIn: parent
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setDockSize(modelData.size)
                                    }
                                }
                            }
                        }
                    }
                }

                // Widget Toggles
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text { text: "INDIVIDUAL WIDGET VISIBILITY"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                    GridLayout {
                        columns: 2
                        rowSpacing: 8
                        columnSpacing: 12
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "clock", name: "Clock & Date Widget", icon: "󰥔" },
                                { key: "weather", name: "Live Weather Widget", icon: "󰖐" },
                                { key: "quickSettings", name: "Control Center / Sliders", icon: "󰒓" },
                                { key: "mediaPlayer", name: "Media Center & Visualizer", icon: "󰝚" },
                                { key: "systemMonitor", name: "System Monitor & Sparklines", icon: "󰍹" },
                                { key: "terminalRice", name: "Terminal System Fetch Card", icon: "󰆍" },
                                { key: "dock", name: "Bottom Island Dock", icon: "󰀻" },
                                { key: "topPill", name: "Top Header Status Pill", icon: "󰹟" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                radius: 8
                                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "#187aa2f7" : "#06ffffff"
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "#407aa2f7" : "#10ffffff"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 10

                                    Text { text: modelData.icon; font.family: "Symbols Nerd Font"; font.pixelSize: 15; color: "#7AA2F7" }
                                    Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 12; color: "#FFFFFF"; Layout.fillWidth: true }
                                    Text {
                                        text: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "󰄬 ON" : "OFF"
                                        font.family: "Inter"
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "#7AA2F7" : "#67707D"
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (typeof systemBridge !== "undefined" && systemBridge) {
                                            var cur = (systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false)
                                            systemBridge.toggleWidget(modelData.key, !cur)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ══════ TAB 2: WALLPAPERS ══════
            ColumnLayout {
                width: root.width - 40
                spacing: 16
                visible: root.activeTab === 2

                Text { text: "BUILT-IN 4K WALLPAPERS"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                GridLayout {
                    columns: 2
                    rowSpacing: 12
                    columnSpacing: 12
                    Layout.fillWidth: true

                    Repeater {
                        model: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.wallpapersList : []

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 110
                            radius: 12
                            color: "#080B10"
                            border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.wallpaperPath === modelData.path) ? ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7") : "#1fffffff"
                            border.width: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.wallpaperPath === modelData.path) ? 2 : 1
                            clip: true

                            Image {
                                anchors.fill: parent
                                source: modelData.path
                                fillMode: Image.PreserveAspectCrop
                            }

                            Rectangle {
                                anchors.bottom: parent.bottom
                                anchors.left: parent.left
                                anchors.right: parent.right
                                height: 30
                                color: "#cc0c1016"

                                Text {
                                    text: modelData.name
                                    font.family: "Inter"
                                    font.pixelSize: 11
                                    font.bold: true
                                    color: "#FFFFFF"
                                    anchors.centerIn: parent
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setWallpaper(modelData.path)
                                }
                            }
                        }
                    }
                }
            }

            // ══════ TAB 3: ACOUSTICS & EQUALIZER ══════
            ColumnLayout {
                width: root.width - 40
                spacing: 18
                visible: root.activeTab === 3

                Text { text: "5-BAND GRAPHIC EQUALIZER"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Repeater {
                        model: [
                            { label: "60 Hz", idx: 0 },
                            { label: "250 Hz", idx: 1 },
                            { label: "1 kHz", idx: 2 },
                            { label: "4 kHz", idx: 3 },
                            { label: "16 kHz", idx: 4 }
                        ]

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Layout.alignment: Qt.AlignHCenter

                            Text {
                                text: {
                                    var val = (typeof systemBridge !== "undefined" && systemBridge && systemBridge.eqBands) ? systemBridge.eqBands[modelData.idx] : 0
                                    return (val > 0 ? "+" : "") + val + " dB"
                                }
                                font.family: "Inter"
                                font.pixelSize: 11
                                color: "#A0AAB8"
                                Layout.alignment: Qt.AlignHCenter
                            }

                            Slider {
                                from: -12; to: 12; stepSize: 1
                                orientation: Qt.Vertical
                                Layout.preferredHeight: 140
                                Layout.alignment: Qt.AlignHCenter
                                value: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.eqBands) ? systemBridge.eqBands[modelData.idx] : 0
                                onMoved: {
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setEqBand(modelData.idx, value)
                                }
                            }

                            Text {
                                text: modelData.label
                                font.family: "Inter"
                                font.pixelSize: 11
                                font.bold: true
                                color: "#FFFFFF"
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                }
            }

            // ══════ TAB 4: PRESETS & BACKUP ══════
            ColumnLayout {
                width: root.width - 40
                spacing: 18
                visible: root.activeTab === 4

                Text { text: "RICE BACKUP & IMPORT / EXPORT"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7" }

                RowLayout {
                    spacing: 14

                    // Export Button
                    Rectangle {
                        Layout.preferredWidth: 200
                        height: 44
                        radius: 8
                        color: "#207aa2f7"
                        border.color: "#7AA2F7"

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            Text { text: "󰆓"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#7AA2F7" }
                            Text { text: "Export Rice (.json)"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF" }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (typeof systemBridge !== "undefined" && systemBridge) {
                                    systemBridge.exportConfig("~/.config/synthex/exported-rice.json")
                                }
                            }
                        }
                    }

                    // Reset Button
                    Rectangle {
                        Layout.preferredWidth: 180
                        height: 44
                        radius: 8
                        color: "#18f7768e"
                        border.color: "#F7768E"

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            Text { text: "󰜉"; font.family: "Symbols Nerd Font"; font.pixelSize: 16; color: "#F7768E" }
                            Text { text: "Reset to Default"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF" }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (typeof systemBridge !== "undefined" && systemBridge) {
                                    systemBridge.setTheme("nova")
                                    systemBridge.setStyleMode("glass")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
