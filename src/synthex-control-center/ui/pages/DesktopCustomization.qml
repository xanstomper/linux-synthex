import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: desktopPage
    anchors.fill: parent

    // Theme & State properties
    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color surfaceColor: "#161C24"
    readonly property color cardBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property int activeSubTab: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        // ── 1. Page Header ─────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Rectangle {
                width: 48
                height: 48
                radius: 12
                color: desktopPage.accentColor

                Text {
                    text: "󰒓"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 26
                    color: "#0C1116"
                    anchors.centerIn: parent
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Desktop Rice & Appearance Studio"
                    font.family: "Inter"
                    font.pixelSize: 22
                    font.bold: true
                    color: desktopPage.textColor
                }
                Text {
                    text: "Customize desktop materials, theme palettes, floating widgets, dock geometry, wallpapers, and acoustics"
                    font.family: "Inter"
                    font.pixelSize: 13
                    color: desktopPage.mutedText
                }
            }

            Item { Layout.fillWidth: true }

            // Preset Quick Actions
            Button {
                text: "Export Rice"
                contentItem: Text { text: parent.text; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#FFFFFF" }
                background: Rectangle { color: "#257aa2f7"; border.color: desktopPage.accentColor; radius: 8; implicitWidth: 100; implicitHeight: 34 }
                onClicked: {
                    if (typeof systemBridge !== "undefined" && systemBridge) {
                        systemBridge.exportConfig("~/.config/synthex/my-rice.json")
                    }
                }
            }

            Button {
                text: "Reset Defaults"
                contentItem: Text { text: parent.text; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: "#F7768E" }
                background: Rectangle { color: "#1af7768e"; border.color: "#F7768E"; radius: 8; implicitWidth: 110; implicitHeight: 34 }
                onClicked: {
                    if (typeof systemBridge !== "undefined" && systemBridge) {
                        systemBridge.setTheme("nova")
                        systemBridge.setStyleMode("glass")
                    }
                }
            }
        }

        // ── 2. Studio Sub-Tabs ─────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { idx: 0, name: "🎨 Appearance & Themes" },
                    { idx: 1, name: "🧩 Widgets & Layout" },
                    { idx: 2, name: "🖼 Wallpapers" },
                    { idx: 3, name: "🎵 Audio & Acoustics" },
                    { idx: 4, name: "⚡ Performance & Game Mode" }
                ]

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    radius: 8
                    color: desktopPage.activeSubTab === modelData.idx ? "#257aa2f7" : "#0effffff"
                    border.color: desktopPage.activeSubTab === modelData.idx ? desktopPage.accentColor : "transparent"

                    Text {
                        text: modelData.name
                        font.family: "Inter"
                        font.pixelSize: 12
                        font.bold: desktopPage.activeSubTab === modelData.idx
                        color: desktopPage.activeSubTab === modelData.idx ? "#FFFFFF" : "#A0AAB8"
                        anchors.centerIn: parent
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: desktopPage.activeSubTab = modelData.idx
                    }

                    Behavior on color { ColorAnimation { duration: 140 } }
                }
            }
        }

        // ── 3. Tab Contents ────────────────────────────────────────────────
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            // ══════ SUB-TAB 0: APPEARANCE & THEMES ══════
            ColumnLayout {
                width: desktopPage.width - 56
                spacing: 24
                visible: desktopPage.activeSubTab === 0

                // Visual Finish Selector
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text { text: "MATERIAL FINISH"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        // Glass Card
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 70
                            radius: 12
                            color: (typeof systemBridge === "undefined" || !systemBridge || systemBridge.styleMode === "glass") ? "#257aa2f7" : desktopPage.cardBg
                            border.color: (typeof systemBridge === "undefined" || !systemBridge || systemBridge.styleMode === "glass") ? desktopPage.accentColor : "#1fffffff"
                            border.width: 1.5

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14
                                Text { text: "✨"; font.pixelSize: 24 }
                                ColumnLayout {
                                    spacing: 2
                                    Text { text: "Liquid Frosted Glass"; font.family: "Inter"; font.pixelSize: 14; font.bold: true; color: "#FFFFFF" }
                                    Text { text: "Translucent backdrop blur, glowing sheen borders, dynamic reflections"; font.family: "Inter"; font.pixelSize: 11; color: desktopPage.mutedText }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setStyleMode("glass") }
                            }
                        }

                        // Matte Card
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 70
                            radius: 12
                            color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.styleMode === "matte") ? "#257aa2f7" : desktopPage.cardBg
                            border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.styleMode === "matte") ? desktopPage.accentColor : "#1fffffff"
                            border.width: 1.5

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14
                                Text { text: "⬛"; font.pixelSize: 24 }
                                ColumnLayout {
                                    spacing: 2
                                    Text { text: "Solid Deep Matte"; font.family: "Inter"; font.pixelSize: 14; font.bold: true; color: "#FFFFFF" }
                                    Text { text: "Deep slate background, crisp high-contrast solid borders, zero glare"; font.family: "Inter"; font.pixelSize: 11; color: desktopPage.mutedText }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setStyleMode("matte") }
                            }
                        }
                    }
                }

                // 9 Theme Presets
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text { text: "CURATED THEME PRESETS"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                    GridLayout {
                        columns: 3
                        rowSpacing: 12
                        columnSpacing: 12
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "nova", name: "Nova Ice", desc: "Glacier blue & dark slate", color: "#141923", accent: "#7AA2F7" },
                                { key: "tokyonight", name: "Tokyo Night", desc: "Cyberpunk blue & neon violet", color: "#1A1B26", accent: "#7AA2F7" },
                                { key: "catppuccin", name: "Catppuccin Mocha", desc: "Soothing pastel lavender & sapphire", color: "#1E1E2E", accent: "#89B4FA" },
                                { key: "nord", name: "Nord Frost", desc: "Arctic deep sea & polar glacier", color: "#2E3440", accent: "#88C0D0" },
                                { key: "cyberpunk", name: "Cyberpunk Neon", desc: "High-contrast cyan & hot magenta", color: "#0D0D18", accent: "#00F0FF" },
                                { key: "oled", name: "OLED Midnight", desc: "Pure black #000000 power saving", color: "#0A0A0A", accent: "#60A5FA" },
                                { key: "gruvbox", name: "Gruvbox Dark", desc: "Retro warm amber gold & rust orange", color: "#282828", accent: "#D79921" },
                                { key: "rosepine", name: "Rosé Pine", desc: "Earthy rose, pine & iris harmony", color: "#191724", accent: "#EB6F92" },
                                { key: "synthwave", name: "Synthwave '84", desc: "Neon magenta & electric turquoise", color: "#1E122B", accent: "#FF71CE" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 64
                                radius: 10
                                color: modelData.color
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? modelData.accent : "#25ffffff"
                                border.width: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.currentTheme === modelData.key) ? 2 : 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 10

                                    Rectangle { width: 18; height: 18; radius: 9; color: modelData.accent }

                                    ColumnLayout {
                                        spacing: 1
                                        Layout.fillWidth: true
                                        Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                                        Text { text: modelData.desc; font.family: "Inter"; font.pixelSize: 10; color: "#A0AAB8"; elide: Text.ElideRight; Layout.fillWidth: true }
                                    }
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
                    spacing: 10

                    Text { text: "ACCENT PALETTE & COLOR HARMONY"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                    RowLayout {
                        spacing: 12

                        Repeater {
                            model: ["#7AA2F7", "#BB9AF7", "#73DACA", "#E5A84B", "#F7768E", "#9ECE6A", "#00F0FF", "#FF007F", "#FE8019", "#EB6F92"]

                            Rectangle {
                                width: 38; height: 38; radius: 19
                                color: modelData
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.accentColor === modelData) ? "#FFFFFF" : "transparent"
                                border.width: 3

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

            // ══════ SUB-TAB 1: WIDGETS & GEOMETRY ══════
            ColumnLayout {
                width: desktopPage.width - 56
                spacing: 24
                visible: desktopPage.activeSubTab === 1

                // Geometry Sliders
                GridLayout {
                    columns: 2
                    rowSpacing: 16
                    columnSpacing: 20
                    Layout.fillWidth: true

                    // Corner Radius
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "CORNER ROUNDING"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }
                            Item { Layout.fillWidth: true }
                            Text { text: ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18) + " px"; font.family: "Inter"; font.pixelSize: 12; color: desktopPage.mutedText }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0; to: 32; stepSize: 1
                            value: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
                            onMoved: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setCornerRadius(value) }
                        }
                    }

                    // Card Opacity
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "SURFACE OPACITY"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }
                            Item { Layout.fillWidth: true }
                            Text { text: Math.round(((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cardOpacity : 0.94) * 100) + " %"; font.family: "Inter"; font.pixelSize: 12; color: desktopPage.mutedText }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0.5; to: 1.0; stepSize: 0.02
                            value: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cardOpacity : 0.94
                            onMoved: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setCardOpacity(value) }
                        }
                    }
                }

                // Dock Configuration
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text { text: "FLOATING DOCK SCALE"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                    RowLayout {
                        spacing: 12

                        Repeater {
                            model: [
                                { size: 32, label: "Compact (32px)" },
                                { size: 40, label: "Standard (40px)" },
                                { size: 48, label: "Large (48px)" },
                                { size: 56, label: "Expanded (56px)" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                height: 42
                                radius: 8
                                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dockSize === modelData.size) ? "#307aa2f7" : desktopPage.cardBg
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.dockSize === modelData.size) ? desktopPage.accentColor : "#1fffffff"

                                Text {
                                    text: modelData.label
                                    font.family: "Inter"
                                    font.pixelSize: 12
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
                    spacing: 10

                    Text { text: "ACTIVE DESKTOP WIDGETS"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                    GridLayout {
                        columns: 2
                        rowSpacing: 10
                        columnSpacing: 14
                        Layout.fillWidth: true

                        Repeater {
                            model: [
                                { key: "clock", name: "Clock & Calendar Card", icon: "󰥔" },
                                { key: "weather", name: "Live Weather & Forecast", icon: "󰖐" },
                                { key: "quickSettings", name: "Control Center & Sliders", icon: "󰒓" },
                                { key: "mediaPlayer", name: "Media Center & Spectrum Visualizer", icon: "󰝚" },
                                { key: "systemMonitor", name: "System Monitor & Sparklines", icon: "󰍹" },
                                { key: "terminalRice", name: "Terminal System Fetch Card", icon: "󰆍" },
                                { key: "dock", name: "Floating Island Dock", icon: "󰀻" },
                                { key: "topPill", name: "Top Status Pill", icon: "󰹟" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                radius: 10
                                color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "#187aa2f7" : desktopPage.cardBg
                                border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? desktopPage.accentColor : "#1fffffff"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 14
                                    anchors.rightMargin: 14
                                    spacing: 12

                                    Text { text: modelData.icon; font.family: "Symbols Nerd Font"; font.pixelSize: 18; color: desktopPage.accentColor }
                                    Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 13; color: "#FFFFFF"; Layout.fillWidth: true }
                                    Text {
                                        text: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? "󰄬 ACTIVE" : "OFF"
                                        font.family: "Inter"
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.widgetsConfig && systemBridge.widgetsConfig[modelData.key] !== false) ? desktopPage.accentColor : "#67707D"
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

            // ══════ SUB-TAB 2: WALLPAPERS ══════
            ColumnLayout {
                width: desktopPage.width - 56
                spacing: 16
                visible: desktopPage.activeSubTab === 2

                Text { text: "BUILT-IN 4K SVG WALLPAPERS"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                GridLayout {
                    columns: 3
                    rowSpacing: 14
                    columnSpacing: 14
                    Layout.fillWidth: true

                    Repeater {
                        model: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.wallpapersList : []

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 140
                            radius: 12
                            color: "#080B10"
                            border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.wallpaperPath === modelData.path) ? desktopPage.accentColor : "#25ffffff"
                            border.width: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.wallpaperPath === modelData.path) ? 2.5 : 1
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
                                height: 32
                                color: "#cc0c1016"

                                Text {
                                    text: modelData.name
                                    font.family: "Inter"
                                    font.pixelSize: 12
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

            // ══════ SUB-TAB 3: ACOUSTICS & EQ ══════
            ColumnLayout {
                width: desktopPage.width - 56
                spacing: 20
                visible: desktopPage.activeSubTab === 3

                Text { text: "5-BAND GRAPHIC EQUALIZER"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 24

                    Repeater {
                        model: [
                            { label: "60 Hz (Sub-Bass)", idx: 0 },
                            { label: "250 Hz (Warmth)", idx: 1 },
                            { label: "1 kHz (Presence)", idx: 2 },
                            { label: "4 kHz (Clarity)", idx: 3 },
                            { label: "16 kHz (Air/Treble)", idx: 4 }
                        ]

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Layout.alignment: Qt.AlignHCenter

                            Text {
                                text: {
                                    var val = (typeof systemBridge !== "undefined" && systemBridge && systemBridge.eqBands) ? systemBridge.eqBands[modelData.idx] : 0
                                    return (val > 0 ? "+" : "") + val + " dB"
                                }
                                font.family: "Inter"
                                font.pixelSize: 12
                                font.bold: true
                                color: desktopPage.accentColor
                                Layout.alignment: Qt.AlignHCenter
                            }

                            Slider {
                                from: -12; to: 12; stepSize: 1
                                orientation: Qt.Vertical
                                Layout.preferredHeight: 160
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

            // ══════ SUB-TAB 4: PERFORMANCE & GAME MODE ══════
            ColumnLayout {
                width: desktopPage.width - 56
                spacing: 18
                visible: desktopPage.activeSubTab === 4

                Text { text: "HARDWARE PROFILES & GAMING ACCELERATION"; font.family: "Inter"; font.pixelSize: 12; font.bold: true; color: desktopPage.accentColor }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    Repeater {
                        model: [
                            { key: "balanced", name: "Balanced", desc: "Quiet acoustic & standard scheduler" },
                            { key: "gaming", name: "Gaming Turbo", desc: "CachyOS BORE scheduler, high GPU clock" },
                            { key: "powersave", name: "Power Saver", desc: "Max battery life & low CPU voltage" }
                        ]

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 70
                            radius: 10
                            color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === modelData.key) ? "#307aa2f7" : desktopPage.cardBg
                            border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.performanceMode === modelData.key) ? desktopPage.accentColor : "#1fffffff"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 2

                                Text { text: modelData.name; font.family: "Inter"; font.pixelSize: 14; font.bold: true; color: "#FFFFFF" }
                                Text { text: modelData.desc; font.family: "Inter"; font.pixelSize: 11; color: desktopPage.mutedText }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setPerformanceMode(modelData.key)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
