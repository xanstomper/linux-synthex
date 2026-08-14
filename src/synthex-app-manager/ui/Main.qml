// SPDX-License-Identifier: GPL-3.0-or-Later
// SynthOS App Manager — GTK-style app catalogue with Flatpak + DNF backend
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: root
    width: 1100; height: 720
    minimumWidth: 900; minimumHeight: 560
    visible: true
    title: qsTr("SynthOS App Manager")
    Material.theme: Material.Dark
    Material.accent: "#6C88A8"

    // ─── State ─────────────────────────────────────────────
    property string currentCategory: "featured"
    property string searchQuery: ""
    property bool installing: false

    readonly property var categories: [
        { id: "featured",     icon: "⭐", label: qsTr("Featured") },
        { id: "browsers",     icon: "🌐", label: qsTr("Browsers") },
        { id: "productivity", icon: "📋", label: qsTr("Productivity") },
        { id: "gaming",       icon: "🎮", label: qsTr("Gaming") },
        { id: "media",        icon: "🎵", label: qsTr("Media") },
        { id: "development",  icon: "💻", label: qsTr("Development") },
        { id: "utilities",    icon: "🔧", label: qsTr("Utilities") },
        { id: "security",     icon: "🔒", label: qsTr("Security") },
        { id: "installed",    icon: "✅", label: qsTr("Installed") },
    ]

    readonly property var apps: {
        "featured": [
            { name: "Firefox",        id: "org.mozilla.firefox",     source: "flatpak", icon: "🦊", desc: "Fast, private web browser",       installed: true  },
            { name: "Brave",          id: "com.brave.Browser",       source: "flatpak", icon: "🦁", desc: "Privacy-focused Chromium browser", installed: false },
            { name: "VS Code",        id: "com.visualstudio.code",   source: "flatpak", icon: "🔵", desc: "Powerful code editor",             installed: false },
            { name: "Obsidian",       id: "md.obsidian.Obsidian",    source: "flatpak", icon: "💎", desc: "Knowledge management",             installed: false },
            { name: "Discord",        id: "com.discordapp.Discord",   source: "flatpak", icon: "💬", desc: "Voice & text chat",               installed: false },
            { name: "GIMP",           id: "org.gimp.GIMP",           source: "flatpak", icon: "🎨", desc: "Powerful image editor",            installed: false },
            { name: "Steam",          id: "com.valvesoftware.Steam",  source: "flatpak", icon: "🎮", desc: "The ultimate game store",         installed: false },
            { name: "VLC",            id: "org.videolan.VLC",         source: "flatpak", icon: "🎬", desc: "Universal media player",          installed: true  },
            { name: "LibreOffice",    id: "org.libreoffice.LibreOffice", source:"flatpak",icon:"📄", desc: "Complete office suite",           installed: false },
            { name: "Blender",        id: "org.blender.Blender",      source:"flatpak", icon: "🌀", desc: "3D creation suite",                installed: false },
        ]
    }

    // ─── Background ────────────────────────────────────────
    Rectangle { anchors.fill: parent; color: "#0A0C14" }

    // ─── Layout ────────────────────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Left sidebar — categories
        Rectangle {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            color: "#0D1117"

            Column {
                anchors { top: parent.top; topMargin: 16; left: parent.left; right: parent.right }
                spacing: 1

                Text {
                    text: "  " + qsTr("Categories")
                    font { pixelSize: 11; bold: true; family: "Noto Sans" }
                    color: "#556077"
                    leftPadding: 16
                    topPadding: 8; bottomPadding: 8
                }

                Repeater {
                    model: root.categories
                    delegate: Rectangle {
                        width: parent.width; height: 40
                        color: modelData.id === root.currentCategory ? "#1A2035" : "transparent"
                        radius: 0

                        Rectangle {
                            width: 3; height: parent.height
                            color: modelData.id === root.currentCategory ? "#6C88A8" : "transparent"
                        }

                        Row {
                            anchors { left: parent.left; leftMargin: 18; verticalCenter: parent.verticalCenter }
                            spacing: 10
                            Text { text: modelData.icon; font.pixelSize: 15 }
                            Text {
                                text: modelData.label; font.pixelSize: 13
                                color: modelData.id === root.currentCategory ? "#FFFFFF" : "#9AA1AB"
                            }
                        }
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: root.currentCategory = modelData.id
                        }
                    }
                }
            }
        }

        // Main content
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Toolbar
            Rectangle {
                Layout.fillWidth: true; height: 56; color: "#0D1117"
                RowLayout {
                    anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                    Text { text: qsTr("App Manager"); font { pixelSize: 18; bold: true }; color: "#FFFFFF" }
                    Item { Layout.fillWidth: true }
                    TextField {
                        Layout.preferredWidth: 260; height: 36
                        placeholderText: qsTr("Search apps…")
                        color: "#FFFFFF"
                        Material.accent: "#6C88A8"
                        onTextChanged: root.searchQuery = text
                    }
                    Button {
                        text: qsTr("⟳ Updates")
                        Material.background: "#1A2035"
                        onClicked: appManagerBridge.checkUpdates()
                    }
                }
            }

            // App grid
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; padding: 16

                Flow {
                    width: parent.width; spacing: 12

                    Repeater {
                        model: {
                            var cat = root.currentCategory
                            var all = root.apps[cat] || root.apps["featured"]
                            if (root.searchQuery.length > 1)
                                return all.filter(a => a.name.toLowerCase().includes(root.searchQuery.toLowerCase()))
                            return all
                        }
                        delegate: Rectangle {
                            width: 200; height: 220; radius: 10
                            color: "#111827"
                            border.color: "#1E2D3D"; border.width: 1

                            Column {
                                anchors { fill: parent; margins: 16 }
                                spacing: 8

                                Text { text: modelData.icon; font.pixelSize: 40; anchors.horizontalCenter: parent.horizontalCenter }
                                Text { text: modelData.name; font { pixelSize: 14; bold: true }; color: "#FFFFFF"; anchors.horizontalCenter: parent.horizontalCenter }
                                Text {
                                    text: modelData.desc; font.pixelSize: 11; color: "#9AA1AB"
                                    wrapMode: Text.WordWrap; width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Text {
                                    text: modelData.source.toUpperCase()
                                    font.pixelSize: 10; color: "#556077"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }
                                Item { height: 4 }
                                Button {
                                    width: parent.width; height: 34
                                    text: modelData.installed ? qsTr("Remove") : qsTr("Install")
                                    Material.background: modelData.installed ? "#2A1510" : "#1A3520"
                                    Material.foreground: modelData.installed ? "#FF6B6B" : "#4ADE80"
                                    onClicked: {
                                        if (modelData.installed)
                                            appManagerBridge.remove(modelData.id, modelData.source)
                                        else
                                            appManagerBridge.install(modelData.id, modelData.source)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Status bar
            Rectangle {
                Layout.fillWidth: true; height: 32; color: "#0D1117"
                Text {
                    anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                    text: root.installing ? qsTr("Installing…") : qsTr("Ready")
                    font.pixelSize: 12; color: "#556077"
                }
                ProgressBar {
                    anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                    width: 200; visible: root.installing; indeterminate: true
                    Material.accent: "#6C88A8"
                }
            }
        }
    }
}
