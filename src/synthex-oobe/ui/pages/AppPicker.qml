import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "transparent"
    anchors.fill: parent
    signal finished()
    readonly property string accent: "#33ccff"
    readonly property string surface: "#1a1a2e"
    readonly property string text: "#ffffff"
    readonly property string muted: "#b0b0b0"
    property var appSelections: ({})

    readonly property var appData: [
        { id: "firefox",     name: "Firefox",           cat: "🌐 Browsers",     desc: "Open-source browser from Mozilla",                  checked: true  },
        { id: "brave",       name: "Brave",             cat: "🌐 Browsers",     desc: "Privacy-first browser with built-in ad blocking",  checked: true  },
        { id: "chrome",      name: "Google Chrome",     cat: "🌐 Browsers",     desc: "Fast browser by Google",                           checked: false },
        { id: "tor",         name: "Tor Browser",        cat: "🌐 Browsers",     desc: "Anonymous browsing via Tor network",               checked: false },
        { id: "edge",        name: "Microsoft Edge",    cat: "🌐 Browsers",     desc: "Chromium-based browser by Microsoft",              checked: false },
        { id: "vivaldi",     name: "Vivaldi",           cat: "🌐 Browsers",     desc: "Highly customizable browser",                      checked: false },
        { id: "opera",       name: "Opera",             cat: "🌐 Browsers",     desc: "Feature-rich Chromium browser",                    checked: false },
        { id: "discord",     name: "Discord",           cat: "💬 Messaging",    desc: "Voice, video & text for communities",               checked: true  },
        { id: "telegram",    name: "Telegram",          cat: "💬 Messaging",    desc: "Cloud-based messaging platform",                   checked: false },
        { id: "signal",      name: "Signal",            cat: "💬 Messaging",    desc: "Encrypted messaging & calls",                      checked: false },
        { id: "whatsapp",    name: "WhatsApp",          cat: "💬 Messaging",    desc: "Meta messaging & calling app",                     checked: false },
        { id: "slack",       name: "Slack",             cat: "💬 Messaging",    desc: "Workplace messaging & team collaboration",          checked: false },
        { id: "element",     name: "Element",           cat: "💬 Messaging",    desc: "Matrix-based secure collaboration",                checked: false },
        { id: "zoom",        name: "Zoom",              cat: "💬 Messaging",    desc: "Video conferencing & meetings",                    checked: false },
        { id: "thunderbird", name: "Thunderbird",       cat: "💬 Messaging",    desc: "Open-source email & calendar client",              checked: false },
        { id: "mailspring",  name: "Mailspring",        cat: "💬 Messaging",    desc: "Modern email client with unified inbox",           checked: false },
        { id: "steam",       name: "Steam",             cat: "🎮 Gaming",       desc: "PC gaming store & library manager",                checked: true  },
        { id: "lutris",      name: "Lutris",            cat: "🎮 Gaming",       desc: "Game manager for Linux & Wine",                    checked: false },
        { id: "heroic",      name: "Heroic Games",      cat: "🎮 Gaming",       desc: "Open-source Epic & GOG launcher",                  checked: false },
        { id: "gamescope",   name: "Gamescope",         cat: "🎮 Gaming",       desc: "Micro-compositor for Steam gaming",                checked: false },
        { id: "mangohud",    name: "MangoHud",          cat: "🎮 Gaming",       desc: "Performance overlay for games",                    checked: false },
        { id: "gamemode",    name: "GameMode",          cat: "🎮 Gaming",       desc: "Optimize system for gaming performance",           checked: false },
        { id: "protonup",    name: "ProtonUp-Qt",       cat: "🎮 Gaming",       desc: "Install & manage Proton/Wine versions",            checked: false },
        { id: "retroarch",   name: "RetroArch",         cat: "🎮 Gaming",       desc: "Multi-system emulator frontend",                  checked: false },
        { id: "vlc",         name: "VLC",               cat: "🎬 Multimedia",   desc: "Versatile media player",                           checked: true  },
        { id: "mpv",         name: "MPV",               cat: "🎬 Multimedia",   desc: "Lightweight video player",                         checked: false },
        { id: "obs",         name: "OBS Studio",        cat: "🎬 Multimedia",   desc: "Screen recording & live streaming",               checked: false },
        { id: "kdenlive",    name: "Kdenlive",          cat: "🎬 Multimedia",   desc: "Feature-rich video editor",                       checked: false },
        { id: "spotify",     name: "Spotify",           cat: "🎬 Multimedia",   desc: "Music streaming service",                         checked: false },
        { id: "audacity",    name: "Audacity",          cat: "🎬 Multimedia",   desc: "Open-source audio editor & recorder",              checked: false },
        { id: "blender",     name: "Blender",           cat: "🖌 Creative",     desc: "3D modeling & animation suite",                    checked: false },
        { id: "gimp",        name: "GIMP",              cat: "🖌 Creative",     desc: "Image editing & manipulation",                     checked: false },
        { id: "krita",       name: "Krita",             cat: "🖌 Creative",     desc: "Digital painting & illustration",                 checked: false },
        { id: "inkscape",    name: "Inkscape",          cat: "🖌 Creative",     desc: "Vector graphics editor",                          checked: false },
        { id: "libreoffice", name: "LibreOffice",       cat: "🖌 Creative",     desc: "Full office productivity suite",                  checked: false },
        { id: "onlyoffice",  name: "OnlyOffice",        cat: "🖌 Creative",     desc: "Office suite with deep format compat",            checked: false },
        { id: "obsidian",    name: "Obsidian",          cat: "🖌 Creative",     desc: "Personal knowledge base & note-taking",            checked: false },
        { id: "vscode",      name: "VS Code",           cat: "💻 Development",  desc: "Code editor with rich extension ecosystem",        checked: true  },
        { id: "docker",      name: "Docker",            cat: "💻 Development",  desc: "Container platform for development",               checked: false },
        { id: "podman",      name: "Podman",            cat: "💻 Development",  desc: "Daemonless container engine",                     checked: false },
        { id: "distrobox",   name: "Distrobox",         cat: "💻 Development",  desc: "Manage containers as integrated toolboxes",        checked: false },
        { id: "gitkraken",   name: "GitKraken",         cat: "💻 Development",  desc: "Git client with a visual interface",               checked: false },
        { id: "neovim",      name: "Neovim",            cat: "💻 Development",  desc: "Modern modal code editor",                        checked: false },
        { id: "jetbrains",   name: "JetBrains Toolbox", cat: "💻 Development",  desc: "Professional IDE suite manager",                  checked: false },
        { id: "ollama",          name: "Ollama",          cat: "🤖 AI & Agents",   desc: "Run local LLMs on your machine",                checked: false },
        { id: "hermes",          name: "Hermes",          cat: "🤖 AI & Agents",   desc: "AI agent assistant for your desktop",            checked: false },
        { id: "opencode",        name: "OpenCode",        cat: "🤖 AI & Agents",   desc: "Open-source AI coding agent",                   checked: false },
        { id: "codex",           name: "Codex",           cat: "🤖 AI & Agents",   desc: "AI assistant with code execution",              checked: false },
        { id: "synthex-agent",   name: "Synthex Agent",   cat: "🤖 AI & Agents",   desc: "Synthex system management agent",               checked: false },
        { id: "open-webui",      name: "Open WebUI",      cat: "🤖 AI & Agents",   desc: "Web interface for local LLMs",                  checked: false },
        { id: "syncthing",   name: "Syncthing",         cat: "🛠 Utilities",    desc: "Peer-to-peer file sync",                          checked: false },
        { id: "qbittorrent", name: "qBittorrent",       cat: "🛠 Utilities",    desc: "Torrent client",                                  checked: false },
        { id: "gparted",     name: "GParted",           cat: "🛠 Utilities",    desc: "Partition manager",                               checked: false },
        { id: "btop",        name: "btop++",            cat: "🛠 Utilities",    desc: "System resource monitor",                         checked: false },
        { id: "fastfetch",   name: "Fastfetch",         cat: "🛠 Utilities",    desc: "System info tool",                                checked: false },
        { id: "tmux",        name: "tmux",              cat: "🛠 Utilities",    desc: "Terminal multiplexer",                            checked: false },
        { id: "neofetch",    name: "Neofetch",          cat: "🛠 Utilities",    desc: "System info display",                             checked: false },
        { id: "wireshark",   name: "Wireshark",         cat: "🛠 Utilities",    desc: "Network protocol analyzer",                      checked: false },
        { id: "veracrypt",   name: "VeraCrypt",         cat: "🛠 Utilities",    desc: "Volume encryption tool",                         checked: false },
        { id: "cryptsetup",  name: "Cryptsetup",        cat: "🛠 Utilities",    desc: "LUKS disk encryption manager",                   checked: false },
        { id: "mullvad",     name: "Mullvad VPN",       cat: "🛠 Utilities",    desc: "Privacy-focused VPN client",                     checked: false }
    ]
    readonly property int totalCount: appData.length
    property int checkedCount: {
        var c = 0;
        for (var i = 0; i < appData.length; ++i)
            if (appData[i].checked) c++;
        return c;
    }
    readonly property var categories: ["🌐 Browsers","💬 Messaging","🎮 Gaming","🎬 Multimedia","🖌 Creative","💻 Development","🤖 AI & Agents","🛠 Utilities"]
    readonly property var bundles: {
        var b = {};
        b["🎮 Gaming"]   = ["steam","lutris","heroic","gamescope","mangohud","gamemode","protonup","retroarch"];
        b["💻 Development"] = ["vscode","docker","podman","distrobox","gitkraken","neovim","jetbrains"];
        b["🖌 Creative"]  = ["blender","gimp","krita","inkscape","libreoffice","onlyoffice","obsidian"];
        b["🤖 AI & Agents"] = ["ollama","hermes","opencode","codex","synthex-agent","open-webui"];
        return b;
    }
    function applyBundle(appIds) {
        for (var i = 0; i < appData.length; ++i)
            appData[i].checked = appIds.indexOf(appData[i].id) >= 0;
        listView.model = null; listView.model = appData;
    }
    function selectAll() {
        for (var i = 0; i < appData.length; ++i) appData[i].checked = true;
        listView.model = null; listView.model = appData;
    }
    function selectNone() {
        for (var i = 0; i < appData.length; ++i) appData[i].checked = false;
        listView.model = null; listView.model = appData;
    }
    function setSelectedApps() {
        var sel = {};
        for (var i = 0; i < appData.length; ++i)
            if (appData[i].checked) sel[appData[i].id] = true;
        appSelections = sel;
    }

    ColumnLayout {
        anchors.fill: parent; spacing: 0
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 60
            color: Qt.rgba(0,0,0,0.4)
            Text {
                anchors.left: parent.left; anchors.leftMargin: 28; anchors.verticalCenter: parent.verticalCenter
                text: "📦  App Picker"; color: root.text; font.pixelSize: 20; font.bold: true
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 28; anchors.verticalCenter: parent.verticalCenter
                text: "Choose what to install"; color: root.muted; font.pixelSize: 13
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 56
            color: Qt.rgba(0,0,0,0.2)
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20; spacing: 8
                Text { text: "⚡ Quick Pick:"; color: root.muted; font.pixelSize: 12; font.bold: true }
                Repeater {
                    model: [
                        { label: "🎮 Gaming",   bundle: bundles["🎮 Gaming"] },
                        { label: "💻 Dev",      bundle: bundles["💻 Development"] },
                        { label: "🖌 Creative", bundle: bundles["🖌 Creative"] },
                        { label: "🤖 AI",       bundle: bundles["🤖 AI & Agents"] },
                        { label: "🟢 All",       bundle: null, action: "all" },
                        { label: "⚪ None",      bundle: null, action: "none" }
                    ]
                    delegate: Button {
                        id: quickBtn; Layout.preferredHeight: 34
                        implicitWidth: quickTxt.implicitWidth + 20
                        background: Rectangle {
                            radius: 8
                            color: quickBtn.hovered ? Qt.rgba(1,1,1,0.1) : Qt.rgba(1,1,1,0.04)
                            border.width: 1; border.color: Qt.rgba(1,1,1,0.12)
                        }
                        contentItem: Text {
                            id: quickTxt; text: modelData.label; color: root.text
                            font.pixelSize: 12; font.bold: true
                            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: {
                            if (modelData.action === "all") selectAll();
                            else if (modelData.action === "none") selectNone();
                            else applyBundle(modelData.bundle);
                        }
                    }
                }
                Item { Layout.fillWidth: true }
            }
        }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded; ScrollBar.vertical.interactive: true
            ListView {
                id: listView; model: appData
                section.property: "cat"; section.delegate: categoryHeader
                spacing: 2; currentIndex: -1
                delegate: Rectangle {
                    width: ListView.view.width; height: 44
                    color: mouseArea.containsMouse ? Qt.rgba(1,1,1,0.04) : "transparent"
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 24; anchors.rightMargin: 24; spacing: 12
                        CheckBox {
                            id: chk; checked: modelData.checked
                            onCheckedChanged: modelData.checked = chk.checked
                            indicator: Rectangle {
                                width: 20; height: 20; x: 0; y: (parent.height - height) / 2; radius: 5
                                color: chk.checked ? root.accent : Qt.rgba(1,1,1,0.06)
                                border.width: 1; border.color: chk.checked ? root.accent : Qt.rgba(1,1,1,0.15)
                                Text {
                                    anchors.centerIn: parent; text: "✓"; color: "#ffffff"
                                    font.pixelSize: 12; font.bold: true; visible: chk.checked
                                }
                            }
                        }
                        Text {
                            Layout.preferredWidth: 140; text: modelData.name; color: root.text
                            font.pixelSize: 14; font.bold: true; elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true; text: modelData.desc; color: root.muted
                            font.pixelSize: 12; elide: Text.ElideRight
                        }
                    }
                    MouseArea {
                        id: mouseArea; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor; onClicked: chk.checked = !chk.checked
                    }
                }
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 72
            color: Qt.rgba(0,0,0,0.35)
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 32; anchors.rightMargin: 32; spacing: 16
                Text {
                    text: "%1 app%2 selected".arg(root.checkedCount).arg(root.checkedCount === 1 ? "" : "s")
                    color: root.muted; font.pixelSize: 13
                }
                Item { Layout.fillWidth: true }
                Button {
                    id: skipBtn; Layout.preferredHeight: 44; Layout.preferredWidth: 130
                    background: Rectangle {
                        radius: 10
                        color: skipBtn.hovered ? Qt.rgba(1,1,1,0.08) : "transparent"
                        border.width: 1; border.color: Qt.rgba(1,1,1,0.2)
                    }
                    contentItem: Text {
                        text: "⏭  Skip"; color: root.muted; font.pixelSize: 15; font.bold: true
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: { root.setSelectedApps(); root.finished(); }
                }
                Button {
                    id: installBtn; Layout.preferredHeight: 44; Layout.preferredWidth: 240
                    enabled: root.checkedCount > 0
                    background: Rectangle {
                        radius: 10
                        color: installBtn.enabled
                            ? (installBtn.hovered ? Qt.lighter(root.accent, 1.15) : root.accent)
                            : Qt.rgba(0.2,0.8,1,0.2)
                        opacity: installBtn.enabled ? 1.0 : 0.5
                    }
                    contentItem: Text {
                        text: "📥  Install Selected (%1)".arg(root.checkedCount)
                        color: installBtn.enabled ? "#ffffff" : root.muted
                        font.pixelSize: 15; font.bold: true
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: { root.setSelectedApps(); root.finished(); }
                }
            }
        }
    }

    Component {
        id: categoryHeader
        Rectangle {
            width: listView.width; height: 36
            color: Qt.rgba(0,0,0,0.3)
            Text {
                anchors.left: parent.left; anchors.leftMargin: 24; anchors.verticalCenter: parent.verticalCenter
                text: section; color: root.accent; font.pixelSize: 14; font.bold: true
            }
        }
    }
}
