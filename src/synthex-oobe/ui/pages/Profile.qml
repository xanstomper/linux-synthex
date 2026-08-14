import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "#0C1016"
    anchors.fill: parent

    readonly property color accentColor: "#6C88A8"
    readonly property color surfaceColor: "#171D24"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property int selectedProfile: -1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 40
        spacing: 20

        Text {
            text: "Choose Your Profile"
            font.pixelSize: 24
            font.bold: true
            color: textColor
        }

        Text {
            text: "Select a preset that matches how you use your computer"
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
                        name: "Gaming"
                        icon: "\u{1F3AE}"
                        description: "Steam + Proton + Gamescope"
                        color: "#E53935"
                    }
                    ListElement {
                        name: "Developer"
                        icon: "\u{1F4D1}"
                        description: "Rust + Go + Python + Containers"
                        color: "#1E88E5"
                    }
                    ListElement {
                        name: "Creator"
                        icon: "\u{1F58C}"
                        description: "Blender + OBS + Krita"
                        color: "#8E24AA"
                    }
                    ListElement {
                        name: "Minimal"
                        icon: "\u{26A1}"
                        description: "Lightweight browser + terminal"
                        color: "#43A047"
                    }
                }

                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 180
                    radius: 16
                    color: surfaceColor
                    border.color: selectedProfile === index ? accentColor : "#2A2A3E"
                    border.width: selectedProfile === index ? 2 : 1

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: parent.color = Qt.lighter(surfaceColor, 1.1)
                        onExited: parent.color = surfaceColor
                        onClicked: selectedProfile = index
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 12

                        // Icon circle
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 56; height: 56; radius: 28
                            color: Qt.rgba(0, 0, 0, 0.2)

                            Text {
                                anchors.centerIn: parent
                                text: modelData.icon
                                font.pixelSize: 28
                            }
                        }

                        Text {
                            text: modelData.name
                            font.pixelSize: 18
                            font.bold: true
                            color: textColor
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Text {
                            text: modelData.description
                            font.pixelSize: 12
                            color: mutedText
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        // Checkmark when selected
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: selectedProfile === index ? 24 : 0
                            height: selectedProfile === index ? 24 : 0
                            radius: 12
                            color: accentColor
                            visible: selectedProfile === index
                            Behavior on width { NumberAnimation { duration: 150 } }
                            Behavior on height { NumberAnimation { duration: 150 } }

                            Text {
                                anchors.centerIn: parent
                                text: "\u2713"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#0C1016"
                            }
                        }
                    }
                }
            }
        }
    }
}
