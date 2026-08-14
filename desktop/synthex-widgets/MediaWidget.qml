import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 360
    height: 190
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.surfaceColor : "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property int activeTab: 0 // 0: Now Playing, 1: Queue, 2: Equalizer
    property string trackTitle: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaTitle : "After Dark"
    property string artistName: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaArtist : "Sweater Weather"
    property string currentTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPos : "1:24"
    property string totalTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaDur : "4:01"
    property real progressPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaProgress : 0.35
    property bool isPlaying: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPlaying : true
    property string coverUrl: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaCover : ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        // ── Tab Bar (Now Playing / Queue / EQ) ──────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                height: 24
                radius: 6
                color: root.activeTab === 0 ? "#257aa2f7" : "transparent"
                Text { text: "󰝚 Now Playing"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: root.activeTab === 0 ? "#7AA2F7" : "#9AA1AB"; anchors.centerIn: parent }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.activeTab = 0 }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 24
                radius: 6
                color: root.activeTab === 1 ? "#257aa2f7" : "transparent"
                Text { text: "󰒮 Queue"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: root.activeTab === 1 ? "#7AA2F7" : "#9AA1AB"; anchors.centerIn: parent }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.activeTab = 1 }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 24
                radius: 6
                color: root.activeTab === 2 ? "#257aa2f7" : "transparent"
                Text { text: "󰓃 EQ"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: root.activeTab === 2 ? "#7AA2F7" : "#9AA1AB"; anchors.centerIn: parent }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.activeTab = 2 }
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
                Layout.preferredWidth: 100
                Layout.preferredHeight: 100
                radius: 12
                color: "#0B0E14"
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
                        GradientStop { position: 0.0; color: "#0D1117" }
                        GradientStop { position: 0.5; color: "#161B22" }
                        GradientStop { position: 1.0; color: "#0B1528" }
                    }

                    Rectangle {
                        width: 28
                        height: 28
                        radius: 14
                        color: "#E2E8F0"
                        anchors.centerIn: parent
                        border.color: "#93C5FD"
                        border.width: 1.5

                        Rectangle {
                            width: 22
                            height: 22
                            radius: 11
                            color: "#0D1117"
                            x: 5
                            y: 2
                        }
                    }

                    // Mini Spectrum Visualizer bars
                    RowLayout {
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 6
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 2

                        Repeater {
                            model: [8, 14, 18, 12, 16, 22, 10, 15]
                            Rectangle {
                                width: 3
                                height: root.isPlaying ? (modelData * (0.6 + Math.random() * 0.4)) : 4
                                radius: 1.5
                                color: "#7AA2F7"
                                Behavior on height { NumberAnimation { duration: 150 } }
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
                    color: "#9AA1AB"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Item { Layout.fillHeight: true }

                // Scrubber
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: root.currentTime; font.family: "Inter"; font.pixelSize: 10; color: "#9AA1AB" }
                        Item { Layout.fillWidth: true }
                        Text { text: root.totalTime; font.family: "Inter"; font.pixelSize: 10; color: "#9AA1AB" }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 4
                        radius: 2
                        color: "#1E2633"

                        Rectangle {
                            width: parent.width * Math.max(0.0, Math.min(1.0, root.progressPct))
                            height: parent.height
                            radius: 2
                            color: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
                        }
                    }
                }

                // Control Buttons
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 16

                    Text {
                        text: "󰒮"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 16
                        color: "#DDE3EB"
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPrevious() }
                        }
                    }

                    Text {
                        text: root.isPlaying ? "󰏤" : "󰐊"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 20
                        color: "#FFFFFF"
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: { if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPlayPause() }
                        }
                    }

                    Text {
                        text: "󰒭"
                        font.family: "Symbols Nerd Font"
                        font.pixelSize: 16
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
                color: modelData.active ? "#257aa2f7" : "#05ffffff"

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
                        radius: 6
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
                text: "Audio Output: " + ((typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.currentAudioOutput : "Speakers")
                font.family: "Inter"
                font.pixelSize: 10
                color: "#9AA1AB"
            }
        }
    }
}
