/* == synthex-app-picker.qml - Calamares viewmodule == */
import QtQuick 2.15; import QtQuick.Controls 2.15; import QtQuick.Layouts 1.15
import io.calamares.core 1.0; import io.calamares.ui 1.0

Page {
    id: root; anchors.fill: parent
    readonly property color bg:"#1a1a2e", card:"#1e293b", accent:"#33ccff", txt:"#e2e8f0", mute:"#94a3b8", brd:"#334155"

    property var themeModel: [
        {n:"Graphite",d:"Dark charcoal",c:"#2d3748",a:"#4a5568"},
        {n:"Mint",d:"Fresh green",c:"#1a3b32",a:"#38b2ac"},
        {n:"Midnight",d:"Deep blue",c:"#1a202c",a:"#3b82f6"},
        {n:"Latte",d:"Warm coffee",c:"#3d2e1e",a:"#d69e6b"},
        {n:"Plasma",d:"Vibrant glow",c:"#2d1b3d",a:"#9333ea"}]

    property var cats: [
        {c:"🌐 Browsers",a:[["firefox","Firefox","Privacy-first browser"],["brave","Brave","Chromium with ad-block"],["chrome","Chrome","Google browser"],["tor","Tor Browser","Anonymity browser"],["edge","Edge","Microsoft browser"],["vivaldi","Vivaldi","Customisable browser"],["opera","Opera","Feature-rich browser"]]},
        {c:"💬 Messaging",a:[["discord","Discord","Chat for communities"],["telegram","Telegram","Secure messaging"],["signal","Signal","E2EE messenger"],["whatsapp","WhatsApp","Meta messaging"],["slack","Slack","Team communication"],["element","Element","Matrix client"],["zoom","Zoom","Video conferencing"],["thunderbird","Thunderbird","Email & calendar"],["mailspring","Mailspring","Modern email client"]]},
        {c:"🎮 Gaming",a:[["steam","Steam","Gaming store & launcher"],["lutris","Lutris","Game manager"],["heroic","Heroic","Epic/GOG launcher"],["gamescope","Gamescope","Micro-compositor"],["mangohud","MangoHud","Performance overlay"],["gamemode","GameMode","Optimise game perf"],["protonup","ProtonUp","Proton/Wine manager"],["retroarch","RetroArch","Emulator frontend"]]},
        {c:"🎬 Multimedia",a:[["vlc","VLC","Universal media player"],["mpv","MPV","Minimal media player"],["obs","OBS Studio","Stream & record"],["kdenlive","Kdenlive","Video editor"],["spotify","Spotify","Music streaming"],["audacity","Audacity","Audio editor"]]},
        {c:"🖌 Creative",a:[["blender","Blender","3D creation suite"],["gimp","GIMP","Image editor"],["krita","Krita","Digital painting"],["inkscape","Inkscape","Vector graphics"],["libreoffice","LibreOffice","Office suite"],["onlyoffice","OnlyOffice","Office suite"],["obsidian","Obsidian","Knowledge base"]]},
        {c:"💻 Development",a:[["vscode","VS Code","Code editor"],["docker","Docker","Containers"],["podman","Podman","Daemonless containers"],["distrobox","Distrobox","Distro containers"],["gitkraken","GitKraken","Git GUI client"],["neovim","Neovim","Modern vim editor"],["jetbrains","JetBrains","IDE suite"]]},
        {c:"🤖 AI & Agents",a:[["ollama","Ollama","Local LLM runner"],["hermes","Hermes","AI assistant"],["opencode","OpenCode","AI coding"],["codex","Codex","AI code assistant"],["synthex-agent","Synthex Agent","System AI agent"],["open-webui","Open WebUI","LLM chat interface"]]},
        {c:"🛠 Utilities",a:[["syncthing","Syncthing","File sync"],["qbittorrent","qBittorrent","Torrent client"],["gparted","GParted","Partition editor"],["btop","Btop++","Resource monitor"],["fastfetch","Fastfetch","System info"],["tmux","tmux","Terminal multiplexer"],["neofetch","Neofetch","System info"],["wireshark","Wireshark","Network analyser"],["veracrypt","VeraCrypt","Disk encryption"],["cryptsetup","Cryptsetup","LUKS encryption"],["mullvad","Mullvad","VPN client"]]}]

    property string selT
    property var selA:({})
    property int cnt: 0
    property var catOpen:({})

    function loadSelections() {
        var t = Config.globalStorage.synthexTheme
        var a = Config.globalStorage.synthexApps
        if(t) selT = t
        if(a) { var o = JSON.parse(a); for(var k in o) selA[k] = o[k] }
        var defs = ["firefox","brave","discord","steam","vlc","vscode"]
        for(var i=0;i<defs.length;i++) if(selA[defs[i]]===undefined) selA[defs[i]]=true
        recount()
    }
    function saveSelections() {
        Config.globalStorage.synthexTheme = selT
        Config.globalStorage.synthexApps = JSON.stringify(selA)
    }
    function tog(k) {
        if(selA[k]) delete selA[k]; else selA[k] = true
        recount(); saveSelections()
    }
    function recount() { var n=0; for(var k in selA) n++; cnt=n }
    function toggleCat(i) { if(catOpen[i]) delete catOpen[i]; else catOpen[i] = true }

    background: Rectangle { color: bg }

    ColumnLayout {
        anchors.fill: parent; spacing: 0

        TabBar {
            id: tabBar; Layout.fillWidth: true; Layout.preferredHeight: 38
            background: Rectangle { color: "#0f172a" }
            TabButton {
                text: "🎨 Theme"; font.pointSize: 11; font.bold: tabBar.currentIndex===0
                contentItem: Text { text:parent.text; color:tabBar.currentIndex===0?accent:txt; font:parent.font; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                background: Rectangle { color:tabBar.currentIndex===0?"#1e293b":"transparent"; border.color:tabBar.currentIndex===0?accent:"transparent"; border.width:1 }
            }
            TabButton {
                text: "📦 Apps"; font.pointSize: 11; font.bold: tabBar.currentIndex===1
                contentItem: Text { text:parent.text; color:tabBar.currentIndex===1?accent:txt; font:parent.font; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                background: Rectangle { color:tabBar.currentIndex===1?"#1e293b":"transparent"; border.color:tabBar.currentIndex===1?accent:"transparent"; border.width:1 }
            }
        }

        StackLayout {
            id: stack; Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: tabBar.currentIndex

            /* === TAB 1: THEME === */
            Item {
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 10
                    Text { text:"Select a theme"; color:txt; font.pointSize:14; font.bold:true; Layout.alignment:Qt.AlignHCenter }
                    GridLayout {
                        columns: 3; columnSpacing: 10; rowSpacing: 10
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Repeater {
                            model: themeModel
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 100
                                Layout.minimumWidth: 100; Layout.maximumWidth: 180
                                color: card; radius: 8
                                border.color: selT===modelData.n ? accent : brd
                                border.width: selT===modelData.n ? 2 : 1
                                ColumnLayout {
                                    anchors.centerIn: parent; spacing: 6
                                    Rectangle {
                                        implicitWidth:40; implicitHeight:40; radius:20
                                        color: modelData.c
                                        border.color: modelData.a; border.width: 2
                                        Rectangle { anchors.centerIn:parent; width:12; height:12; radius:6; color:modelData.a }
                                        Layout.alignment: Qt.AlignHCenter
                                    }
                                    Text { text:modelData.n; color:txt; font.pointSize:11; font.bold:true; Layout.alignment:Qt.AlignHCenter }
                                    Text { text:modelData.d; color:mute; font.pointSize:9; Layout.alignment:Qt.AlignHCenter }
                                }
                                MouseArea {
                                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { selT=modelData.n; saveSelections() }
                                }
                            }
                        }
                        Item { Layout.fillWidth:true; Layout.fillHeight:true }
                    }
                }
            }

            /* === TAB 2: APPS === */
            ColumnLayout {
                spacing: 0
                ScrollView {
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                    ColumnLayout {
                        width: parent.width; spacing: 2; topPadding: 6; leftPadding: 8; rightPadding: 8
                        Repeater {
                            model: cats
                            ColumnLayout {
                                spacing: 0; Layout.fillWidth: true
                                Rectangle {
                                    Layout.fillWidth: true; Layout.preferredHeight: 30
                                    color: catOpen[index] ? "#334155" : "#0f172a"; radius: 4
                                    RowLayout {
                                        anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                                        Text { text:catOpen[index]?"▼":"▶"; color:accent; font.pointSize:10 }
                                        Text { text:modelData.c; color:txt; font.pointSize:11; font.bold:true; Layout.fillWidth:true }
                                        Text { text:{var n=0;for(var i=0;i<modelData.a.length;i++)if(selA[modelData.a[i][0]])n++;return n+"/"+modelData.a.length}; color:accent; font.pointSize:9 }
                                    }
                                    MouseArea { anchors.fill:parent; cursorShape:Qt.PointingHandCursor; onClicked:toggleCat(index) }
                                }
                                Item {
                                    Layout.fillWidth: true; Layout.preferredHeight: catOpen[index] ? childrenRect.height : 0; clip: true
                                    visible: catOpen[index]
                                    ColumnLayout {
                                        width: parent.width; spacing: 1; leftPadding: 8; rightPadding: 8
                                        Repeater {
                                            model: modelData.a
                                            Rectangle {
                                                Layout.fillWidth: true; Layout.preferredHeight: 32; color: "transparent"; radius: 3
                                                RowLayout {
                                                    anchors.fill: parent; anchors.leftMargin: 4; spacing: 6
                                                    CheckBox {
                                                        id: chk
                                                        checked: root.selA[modelData[0]] === true
                                                        indicator: Rectangle {
                                                            implicitWidth:16; implicitHeight:16; radius:3
                                                            color: chk.checked ? accent : "#475569"
                                                            border.color: accent; border.width: chk.checked ? 0 : 1
                                                            Text { anchors.centerIn:parent; text:"✓"; color:"#0f172a"; visible:chk.checked; font.bold:true; font.pointSize:9 }
                                                        }
                                                        onCheckedChanged: root.tog(modelData[0])
                                                    }
                                                    Text { text:modelData[1]; color:txt; font.pointSize:10; Layout.minimumWidth:80 }
                                                    Text { text:modelData[2]; color:mute; font.pointSize:9; elide:Text.ElideRight; Layout.fillWidth:true }
                                                }
                                                MouseArea { hoverEnabled:true; anchors.fill:parent; onClicked:chk.checked=!chk.checked }
                                            }
                                        }
                                        Item { Layout.preferredHeight: 4 }
                                    }
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 30; color: "#0f172a"
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                        Text { text:cnt+" app"+(cnt!==1?"s":"")+" selected"; color:accent; font.pointSize:11; font.bold:true }
                        Item { Layout.fillWidth: true }
                        Text { text:selT?"Theme: "+selT:"No theme"; color:selT?txt:mute; font.pointSize:9 }
                    }
                }
            }
        }
    }
    Component.onCompleted: loadSelections()
}
