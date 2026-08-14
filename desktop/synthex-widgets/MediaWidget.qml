import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 320
    height: 140
    radius: 18
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property string trackTitle: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaTitle : "After Dark"
    property string artistName: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaArtist : "Sweater Weather"
    property string currentTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPos : "1:24"
    property string totalTime: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaDur : "4:01"
    property real progressPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaProgress : 0.35
    property bool isPlaying: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaPlaying : true
    property string coverUrl: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.mediaCover : ""

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        // Album Artwork
        Rectangle {
            Layout.preferredWidth: 108
            Layout.preferredHeight: 108
            radius: 12
            color: "#0B0E14"
            clip: true

            Image {
                anchors.fill: parent
                source: root.coverUrl
                fillMode: Image.PreserveAspectCrop
                visible: root.coverUrl !== ""
            }

            // Fallback moon artwork representation if no MPRIS cover
            Rectangle {
                anchors.fill: parent
                visible: root.coverUrl === ""
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#0D1117" }
                    GradientStop { position: 0.5; color: "#161B22" }
                    GradientStop { position: 1.0; color: "#0B1528" }
                }

                Rectangle {
                    width: 32
                    height: 32
                    radius: 16
                    color: "#E2E8F0"
                    anchors.centerIn: parent
                    border.color: "#93C5FD"
                    border.width: 2

                    Rectangle {
                        width: 26
                        height: 26
                        radius: 13
                        color: "#0D1117"
                        x: 6
                        y: 2
                    }
                }

                Rectangle {
                    width: 48
                    height: 2
                    color: "#6693c5fd"
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 84
                }
            }
        }

        // Track Details & Controls
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6

            Text {
                text: root.trackTitle
                font.family: "Inter"
                font.pixelSize: 15
                font.bold: true
                color: "#FFFFFF"
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                text: root.artistName
                font.family: "Inter"
                font.pixelSize: 12
                color: "#9AA1AB"
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Item { Layout.fillHeight: true }

            // Progress Slider
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: root.currentTime
                        font.family: "Inter"
                        font.pixelSize: 10
                        color: "#9AA1AB"
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: root.totalTime
                        font.family: "Inter"
                        font.pixelSize: 10
                        color: "#9AA1AB"
                    }
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
                        color: "#7AA2F7"
                    }

                    // Thumb
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: "#FFFFFF"
                        x: parent.width * Math.max(0.0, Math.min(1.0, root.progressPct)) - 4
                        y: -2
                    }
                }
            }

            // Playback Buttons
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 20

                Text {
                    text: "󰒮"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 18
                    color: "#DDE3EB"
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPrevious()
                        }
                    }
                }

                Text {
                    text: root.isPlaying ? "󰏤" : "󰐊"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 22
                    color: "#FFFFFF"
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaPlayPause()
                        }
                    }
                }

                Text {
                    text: "󰒭"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 18
                    color: "#DDE3EB"
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.mediaNext()
                        }
                    }
                }
            }
        }
    }
}
