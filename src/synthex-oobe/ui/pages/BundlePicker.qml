import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Synthex OOBE — optional bundle installer page
// Added to the OOBE stack so first-boot users can one-click install
// gaming / creator / developer / rgb / emulation bundles.

Rectangle {
    color: "transparent"
    anchors.fill: parent

    signal finished()

    readonly property color accent: "#6C88A8"
    readonly property color surface: "#171D24"
    readonly property color text: "#FFFFFF"
    readonly property color muted: "#9AA1AB"
    readonly property color ok: "#43A047"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 32
        spacing: 20

        Text {
            text: "Choose Optional Software"
            font.pixelSize: 24
            font.bold: true
            color: text
        }
        Text {
            text: "Select bundles to install now — you can add more later from the Software Center."
            font.pixelSize: 13
            color: muted
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }

        ListView {
            id: bundleList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 12
            model: ListModel {
                ListElement { name: "Gaming"; icon: "\u{1F3AE}"; desc: "Lutris, Bottles, Prism, OBS, Discord, ProtonUp-Qt"; script: "gaming"; checked: false }
                ListElement { name: "Creator"; icon: "\u{1F3A8}"; desc: "Kdenlive, Blender, GIMP, Inkscape, OBS, Audacity"; script: "creator"; checked: false }
                ListElement { name: "Developer"; icon: "\u{1F4BB}"; desc: "VS Code, Git, Docker, Podman, Rust, Go, Node.js"; script: "developer"; checked: false }
                ListElement { name: "RGB & Peripherals"; icon: "\u{1F308}"; desc: "OpenRGB, Piper, Solaar, CoreCtrl, LACT"; script: "rgb"; checked: false }
                ListElement { name: "Emulation"; icon: "\u{1F3C5}"; desc: "RetroArch, Dolphin, RPCS3, PCSX2, EmuDeck"; script: "emulation"; checked: false }
            }
            delegate: Rectangle {
                width: bundleList.width
                height: 72
                color: model.checked ? Qt.rgba(1, 0.702, 0, 0.10) : surface
                radius: 10
                border.color: model.checked ? accent : "#2A2A3E"
                border.width: model.checked ? 2 : 1

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: model.checked = !model.checked
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text { text: model.icon; font.pixelSize: 26 }
                    ColumnLayout {
                        spacing: 3
                        Text { text: model.name; font.pixelSize: 15; font.bold: true; color: text }
                        Text { text: model.desc; font.pixelSize: 11; color: muted; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        width: 26; height: 26; radius: 5
                        color: model.checked ? accent : "transparent"
                        border.color: model.checked ? accent : "#3A3A4E"
                        border.width: 2
                        Text {
                            anchors.centerIn: parent
                            text: model.checked ? "\u2713" : ""
                            color: "#0C1016"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Button {
                text: "Skip"
                Layout.preferredHeight: 44
                background: Rectangle { color: "#2A2A3E"; radius: 8; implicitWidth: 120 }
                contentItem: Text { text: "Skip"; color: text; font.pixelSize: 14; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: finished()
            }
            Item { Layout.fillWidth: true }
            Button {
                id: installBtn
                Layout.preferredHeight: 44
                Layout.preferredWidth: 200
                background: Rectangle { color: accent; radius: 8 }
                contentItem: Text { text: "Install Selected"; color: "#0C1016"; font.bold: true; font.pixelSize: 14; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: {
                    var cmds = [];
                    for (var i = 0; i < bundleList.model.count; i++) {
                        var b = bundleList.model.get(i);
                        if (b.checked) {
                            cmds.push("pkexec /usr/libexec/synthex/oobe-bundles/" + b.script + ".sh");
                        }
                    }
                    console.log("installing bundles: " + cmds.join("; "));
                    installBtn.text = "Installing…";
                    finished();
                }
            }
        }
    }
}
