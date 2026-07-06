import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: oobeThemes
    color: "#0B0F1A"
    anchors.fill: parent

    readonly property color accentColor: "#FFB300"
    readonly property color surfaceColor: "#1A1A2E"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"

    property int selectedTheme: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 40
        spacing: 20

        Text {
            text: "Choose Your Theme"
            font.pixelSize: 24
            font.bold: true
            color: textColor
        }

        Text {
            text: "Pick a look and feel for your desktop"
            font.pixelSize: 13
            color: mutedText
            Layout.bottomMargin: 8
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            rowSpacing: 16
            columnSpacing: 16

            Repeater {
                model: ListModel {
                    ListElement {
                        name: "Solus Dark"
                        preview1: "#0B0F1A"
                        preview2: "#1A1A2E"
                        preview3: "#FFB300"
                        description: "Dark theme with Amber accents \u2022 Default"
                    }
                    ListElement {
                        name: "Solus Light"
                        preview1: "#F5F5F5"
                        preview2: "#FFFFFF"
                        preview3: "#FFB300"
                        description: "Clean light theme for bright environments"
                    }
                    ListElement {
                        name: "Solus Neon"
                        preview1: "#0A0A1A"
                        preview2: "#1A1A3E"
                        preview3: "#00FFAA"
                        description: "Cyberpunk-inspired with green accents"
                    }
                    ListElement {
                        name: "Minimal"
                        preview1: "#1E1E1E"
                        preview2: "#2D2D2D"
                        preview3: "#607D8B"
                        description: "Subtle gray tones for distraction-free work"
                    }
                }

                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 200
                    radius: 16
                    color: surfaceColor
                    border.color: selectedTheme === index ? accentColor : "#2A2A3E"
                    border.width: selectedTheme === index ? 2 : 1

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: selectedTheme = index
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 0
                        spacing: 0

                        // Preview
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 100
                            radius: 16
                            color: modelData.preview1

                            Rectangle {
                                anchors.bottom: parent.bottom
                                anchors.left: parent.left
                                anchors.right: parent.right
                                height: 40
                                color: modelData.preview2

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 12
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 16; height: 16; radius: 8
                                    color: modelData.preview3
                                }

                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.rightMargin: 12
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 60; height: 6; radius: 3
                                    color: modelData.preview3
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        ColumnLayout {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.margins: 16
                            spacing: 4

                            Text {
                                text: modelData.name
                                font.pixelSize: 16
                                font.bold: true
                                color: textColor
                            }

                            Text {
                                text: modelData.description
                                font.pixelSize: 11
                                color: mutedText
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }

        // Apply and Preview button
        Button {
            Layout.alignment: Qt.AlignRight
            Layout.preferredHeight: 40
            Layout.preferredWidth: 180

            background: Rectangle {
                color: accentColor
                radius: 8
                opacity: 0.85
            }
            contentItem: Text {
                text: "\u{1F3A8}  Apply and Preview"
                font.pixelSize: 13
                font.bold: true
                color: "#0B0F1A"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            onClicked: {
                console.log("Theme applied:", model.get(selectedTheme).name);
            }
        }
    }
}
