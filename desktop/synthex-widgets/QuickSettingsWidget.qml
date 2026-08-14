import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 250
    height: 180
    radius: 18
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property int brightnessPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.brightness : 52
    property int volumePct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.volume : 100

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // ── 1. Backlight Row ───────────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: "󰃠"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 22
                    color: "#E5A84B"
                    Layout.alignment: Qt.AlignVCenter
                }

                ColumnLayout {
                    spacing: 1
                    Layout.fillWidth: true

                    Text {
                        text: "Backlight"
                        font.family: "Inter"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#FFFFFF"
                    }

                    Text {
                        text: "Brightness at " + root.brightnessPct + "%"
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: "#9AA1AB"
                    }
                }
            }

            // Amber Brightness Bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: "#1E2633"

                Rectangle {
                    width: parent.width * (root.brightnessPct / 100.0)
                    height: parent.height
                    radius: 4
                    color: "#E5A84B"
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPositionChanged: {
                        if (pressed) {
                            var pct = Math.max(5, Math.min(100, Math.round((mouse.x / width) * 100)))
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setBrightness(pct)
                            else root.brightnessPct = pct
                        }
                    }
                    onClicked: {
                        var pct = Math.max(5, Math.min(100, Math.round((mouse.x / width) * 100)))
                        if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setBrightness(pct)
                        else root.brightnessPct = pct
                    }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#0affffff"
        }

        // ── 2. Volume Row ──────────────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: "󰕾"
                    font.family: "Symbols Nerd Font"
                    font.pixelSize: 22
                    color: "#2AC3DE"
                    Layout.alignment: Qt.AlignVCenter
                }

                ColumnLayout {
                    spacing: 1
                    Layout.fillWidth: true

                    Text {
                        text: "Volume"
                        font.family: "Inter"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#FFFFFF"
                    }

                    Text {
                        text: "Volume at " + root.volumePct + "%"
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: "#9AA1AB"
                    }
                }
            }

            // Blue Volume Bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: "#1E2633"

                Rectangle {
                    width: parent.width * (root.volumePct / 100.0)
                    height: parent.height
                    radius: 4
                    color: "#2AC3DE"
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPositionChanged: {
                        if (pressed) {
                            var pct = Math.max(0, Math.min(100, Math.round((mouse.x / width) * 100)))
                            if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setVolume(pct)
                            else root.volumePct = pct
                        }
                    }
                    onClicked: {
                        var pct = Math.max(0, Math.min(100, Math.round((mouse.x / width) * 100)))
                        if (typeof systemBridge !== "undefined" && systemBridge) systemBridge.setVolume(pct)
                        else root.volumePct = pct
                    }
                }
            }
        }
    }
}
