import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    readonly property color accentColor: "#FFB300"
    readonly property color surfaceColor: "#1A1A2E"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Text { text: "Rice Presets"; font.pixelSize: 22; font.bold: true; color: textColor }
        Text { text: "One-click complete theme transformations"; font.pixelSize: 13; color: mutedText }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 3
            rowSpacing: 16
            columnSpacing: 16

            Repeater {
                model: ListModel {
                    ListElement {
                        name: "Cyberpunk"
                        icon: "\u{1F525}"
                        color1: "#FF00FF"
                        color2: "#00FFFF"
                        color3: "#0A0A1A"
                        description: "Neon glow with RGB accents \u2022 Futuristic and bold"
                    }
                    ListElement {
                        name: "Minimal"
                        icon: "\u{2B1C}"
                        color1: "#37474F"
                        color2: "#78909C"
                        color3: "#ECEFF1"
                        description: "Clean monochrome \u2022 Distraction-free elegance"
                    }
                    ListElement {
                        name: "Glass"
                        icon: "\u{1F4A7}"
                        color1: "#1A237E"
                        color2: "#E0E0E0"
                        color3: "#FFFFFF"
                        description: "Acrylic transparency \u2022 Modern frosted effects"
                    }
                    ListElement {
                        name: "Nature"
                        icon: "\u{1F33F}"
                        color1: "#2E7D32"
                        color2: "#8D6E63"
                        color3: "#FFF8E1"
                        description: "Earthy warm tones \u2022 Organic and calming"
                    }
                    ListElement {
                        name: "Dark Pro"
                        icon: "\u{2B1B}"
                        color1: "#1A1A2E"
                        color2: "#0D1117"
                        color3: "#FFB300"
                        description: "Sleek dark gradients \u2022 Professional finish"
                    }
                    ListElement {
                        name: "Custom..."
                        icon: "\u{2795}"
                        color1: "#333333"
                        color2: "#555555"
                        color3: "#777777"
                        description: "Build your own theme from scratch"
                    }
                }

                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 220
                    Layout.minimumHeight: 200
                    radius: 16
                    color: surfaceColor
                    border.color: "#2A2A3E"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        // Preview gradient area
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 80
                            radius: 16

                            gradient: Gradient {
                                GradientStop { position: 0.0; color: modelData.color1 }
                                GradientStop { position: 0.5; color: modelData.color2 }
                                GradientStop { position: 1.0; color: modelData.color3 }
                            }

                            Rectangle {
                                anchors.centerIn: parent
                                width: 40; height: 40; radius: 20
                                color: Qt.rgba(0, 0, 0, 0.3)

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    font.pixelSize: 20
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        ColumnLayout {
                            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                            anchors.margins: 16
                            spacing: 6

                            Text {
                                text: modelData.name
                                font.pixelSize: 18
                                font.bold: true
                                color: textColor
                            }

                            Text {
                                text: modelData.description
                                font.pixelSize: 11
                                color: mutedText
                                wrapMode: Text.WordWrap
                                Layout.maximumWidth: parent.width
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Layout.topMargin: 8

                                background: Rectangle {
                                    color: accentColor
                                    radius: 8
                                    opacity: 0.85
                                }
                                contentItem: Text {
                                    text: "\u{1F3A8} Apply Preset"
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: "#0B0F1A"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                onClicked: {
                                    // Show confirmation dialog
                                    presetDialog.open();
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Confirmation Dialog
    Dialog {
        id: presetDialog
        modal: true
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: 400
        height: 200
        background: Rectangle { color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1 }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            Text {
                text: "\u26A0\uFE0F Apply Preset"
                font.pixelSize: 18
                font.bold: true
                color: textColor
            }

            Text {
                text: "This will change your theme, icons, fonts, and layout. A snapshot will be created before applying so you can roll back if needed."
                font.pixelSize: 12
                color: mutedText
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                Item { Layout.fillWidth: true }

                Button {
                    text: "Cancel"
                    flat: true
                    Layout.preferredHeight: 36
                    Layout.preferredWidth: 100
                    background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }
                    contentItem: Text { text: "Cancel"; color: textColor; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: presetDialog.close()
                }

                Button {
                    text: "Apply"
                    flat: true
                    Layout.preferredHeight: 36
                    Layout.preferredWidth: 100
                    background: Rectangle { color: accentColor; radius: 6 }
                    contentItem: Text { text: "Apply"; color: "#0B0F1A"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: {
                        console.log("Preset applied with snapshot");
                        presetDialog.close();
                    }
                }
            }
        }
    }
}
