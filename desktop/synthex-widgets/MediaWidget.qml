import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 360
    height: 196
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: "#a612161f" // Translucent liquid glass
    border.color: "#28ffffff"
    border.width: 1

    property int activeTab: 0
    property string trackTitle: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaTitle : "After Dark"
    property string artistName: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaArtist : "Sweater Weather"
    property string currentTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPos : "1:24"
    property string totalTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaDur : "4:01"
    property real progressPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaProgress : 0.35
    property bool isPlaying: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPlaying : true
    property string coverUrl: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaCover : ""

    // Liquid Glass Specular Top Highlight
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22ffffff" }
            GradientStop { position: 0.08; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        // ── Tab Bar (Now Playing / Queue / EQ) ──────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { idx: 0, label: "󰝚 Now Playing" },
                    { idx: 1, label: "󰒮 Queue" },
                    { idx: 2, label: "󰓃 EQ" }
                ]

                Rectangle {
                    Layout.fillWidth: true
                    height: 26
                    radius: 7
                    color: root.activeTab === modelData.idx ? "#307aa2f7" : "#08ffffff"
                    border.color: root.activeTab === modelData.idx ? "#7AA2F7" : "transparent"

                    Text {
                        text: modelData.label
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: root.activeTab === modelData.idx ? "#FFFFFF" : "#9AA1AB"
                        anchors.centerIn: parent
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.activeTab = modelData.idx
                    }

                    Behavior on color { ColorAnimation { duration: 160 } }
                }
            }
        }

        // ── Tab 0: Now Playing ─────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14
            visible: root.activeTab === 0

            // Album Artwork & Visualizer
            Rectangle {
                Layout.preferredWidth: 104
                Layout.preferredHeight: 104
                radius: 14
                color: "#080B10"
                border.color: "#20ffffff"
                clip: true

                Image {
                    anchors.fill: parent
                    source: root.coverUrl
                    fillMode: Image.PreserveAspectCrop
                    visible: root.coverUrl !== ""
                }

                // Fallback Atmospheric Moon Graphic
                Rectangle {
                    anchors.fill: parent
                    visible: root.coverUrl === ""
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#0B0E14" }
                        GradientStop { position: 0.5; color: "#131822" }
                        GradientStop { position: 1.0; color: "#0B1528" }
                    }

                    Rectangle {
                        width: 30
                        height: 30
                        radius: 15
                        color: "#E2E8F0"
                        anchors.centerIn: parent
                        border.color: "#93C5FD"
                        border.width: 1.5

                        Rectangle {
                            width: 24
                            height: 24
                            radius: 12
                            color: "#0B0E14"
                            x: 5
                            y: 2
                        }
                    }

                    // Mini Spectrum Visualizer bars
                    RowLayout {
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 3

                        Repeater {
                            model: [10, 16, 22, 14, 18, 26, 12, 17]
                            Rectangle {
                                width: 3
                                height: root.isPlaying ? (modelData * (0.6 + Math.sin(Date.now()/200 + index)*0.35)) : 4
                                radius: 1.5
                                color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                                Behavior on height { NumberAnimation { duration: 100 } }
                            }
                        }
                    }
                }
            }

            // Track Details & Controls
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4

                Text {
                    text: root.trackTitle
                    font.family: "Inter"
                    font.pixelSize: 14
                    font.bold: true
                    color: "#FFFFFF"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Text {
                    text: root.artistName
                    font.family: "Inter"
                    font.pixelSize: 11
                    color: "#A0AAB8"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Item { Layout.fillHeight: true }

                // Scrubber
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: root.currentTime; font.family: "Inter"; font.pixelSize: 10; color: "#A0AAB8" }
                        Item { Layout.fillWidth: true }
                        Text { text: root.totalTime; font.family: "Inter"; font.pixelSize: 10; color: "#A0AAB8" }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 5
                        radius: 2.5
                        color: "#1E2633"

                        Rectangle {
                            width: parent.width * Math.max(0.0, Math.min(1.0, root.progressPct))
                            height: parent.height
                            radius: 2.5
                            color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                        }
                    }
                }

                // Control Buttons
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 18

                    Text {
                        text: "󰒮"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 18
                        color: "#DDE3EB"
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPrevious() }
                        }
                    }

                    Text {
                        text: root.isPlaying ? "󰏤" : "󰐊"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 24
                        color: "#FFFFFF"
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPlayPause() }
                        }
                    }

                    Text {
                        text: "󰒭"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 18
                        color: "#DDE3EB"
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaNext() }
                        }
                    }
                }
            }
        }

        // ── Tab 1: Queue & Playlist ─────────────────────────────────────────
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            visible: root.activeTab === 1
            model: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaQueue : []

            delegate: Rectangle {
                width: parent.width
                height: 28
                radius: 6
                color: modelData.active ? "#307aa2f7" : "#05ffffff"
                border.color: modelData.active ? "#7AA2F7" : "transparent"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8

                    Text {
                        text: (index + 1) + "."
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: modelData.active ? "#7AA2F7" : "#67707D"
                    }

                    Text {
                        text: modelData.title + " – " + modelData.artist
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: modelData.active
                        color: modelData.active ? "#FFFFFF" : "#DDE3EB"
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Text {
                        text: modelData.dur
                        font.family: "Inter"
                        font.pixelSize: 10
                        color: "#9AA1AB"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof systemBridge !== "undefined" && systemBridge) {
                            systemBridge.playQueueTrack(index)
                        }
                    }
                }
            }
        }

        // ── Tab 2: Equalizer Presets ────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6
            visible: root.activeTab === 2

            Text {
                text: "ACOUSTIC PROFILE PRESETS"
                font.family: "Inter"
                font.pixelSize: 10
                font.bold: true
                color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
            }

            GridLayout {
                columns: 2
                rowSpacing: 6
                columnSpacing: 6
                Layout.fillWidth: true

                Repeater {
                    model: ["Balanced", "Bass Boost", "Vocal Clarity", "Electronic Hi-Fi"]

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        radius: 7
                        color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.eqPreset === modelData) ? "#357aa2f7" : "#08ffffff"
                        border.color: (typeof systemBridge !== "undefined" && systemBridge && systemBridge.eqPreset === modelData) ? "#7AA2F7" : "transparent"

                        Text {
                            text: modelData
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
                                if (typeof systemBridge !== "undefined" && systemBridge) {
                                    systemBridge.setEqPreset(modelData)
                                }
                            }
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }

            Text {
                text: "Audio Routing: " + ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.currentAudioOutput : "Speakers")
                font.family: "Inter"
                font.pixelSize: 10
                color: "#A0AAB8"
            }
        }
    }
}
