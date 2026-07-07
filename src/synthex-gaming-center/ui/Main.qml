import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: gamingWindow
    visible: true
    width: 1100
    height: 750
    minimumWidth: 900
    minimumHeight: 600
    title: "Synthex Gaming Center"
    color: "#0B0F1A"

    readonly property color accentColor: "#E53935"
    readonly property color bgColor: "#0B0F1A"
    readonly property color surfaceColor: "#1A1A2E"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#121624"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Text { text: "\u{1F3AE}"; font.pixelSize: 24 }
                Text { text: "Gaming Center"; font.pixelSize: 20; font.bold: true; color: textColor }
                Item { Layout.fillWidth: true }

                // Performance mode switch
                Text { text: "Performance Mode"; font.pixelSize: 12; color: mutedText }
                Switch {
                    checked: true
                    indicator: Rectangle {
                        implicitWidth: 44; implicitHeight: 24; radius: 12
                        color: parent.checked ? accentColor : "#3A3A4E"
                        Rectangle { x: parent.checked ? 22 : 2; y: 2; width: 20; height: 20; radius: 10; color: "#FFFFFF"; Behavior on x { NumberAnimation { duration: 120 } } }
                    }
                }
            }
        }

        // Content
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            leftPadding: 24
            rightPadding: 24
            topPadding: 24

            ColumnLayout {
                width: parent.width - 48
                spacing: 20

                // Dashboard metrics
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Repeater {
                        model: [
                            { label: "GPU", value: "Loading...", key: "gpu_name" },
                            { label: "CPU", value: "Loading...", key: "cpu_name" },
                            { label: "RAM", value: "Loading...", key: "memory" },
                            { label: "FPS", value: "Waiting...", key: "fps" }
                        ]

                        delegate: Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 100
                            color: surfaceColor
                            radius: 12
                            border.color: "#2A2A3E"
                            border.width: 1

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 6
                                Text { text: modelData.label; font.pixelSize: 11; color: mutedText; font.uppercase: true }
                                Text { text: modelData.value; font.pixelSize: 22; font.bold: true; color: textColor }
                                Text { text: modelData.sub; font.pixelSize: 10; color: mutedText }
                            }
                        }
                    }
                }

                // Quick Toggles
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Repeater {
                        model: [
                            { label: "MangoHUD", icon: "\u{1F4CA}", on: true },
                            { label: "Gamescope", icon: "\u{1F5A5}", on: true },
                            { label: "vkBasalt", icon: "\u{1F3AD}", on: false },
                            { label: "FPS Limit", icon: "\u{1F4C8}", on: false },
                            { label: "Compositor", icon: "\u{1F4FA}", on: false }
                        ]

                        delegate: Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 56
                            color: surfaceColor
                            radius: 10
                            border.color: modelData.on ? accentColor : "#2A2A3E"
                            border.width: modelData.on ? 2 : 1

                            RowLayout {
                                anchors.fill: parent; anchors.margins: 12; spacing: 8
                                Text { text: modelData.icon; font.pixelSize: 18 }
                                Item { Layout.fillWidth: true }
                                ColumnLayout { spacing: 2
                                    Text { text: modelData.label; font.pixelSize: 11; color: textColor }
                                    Rectangle {
                                        width: 8; height: 8; radius: 4; color: modelData.on ? "#4CAF50" : "#E53935"
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: { console.log("Toggle:", modelData.label); }
                            }
                        }
                    }
                }

                // Per-Game Profiles
                Rectangle {
                    Layout.fillWidth: true
                    color: surfaceColor
                    radius: 12
                    border.color: "#2A2A3E"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Per-Game Profiles"; font.pixelSize: 16; font.bold: true; color: textColor }
                            Item { Layout.fillWidth: true }
                            Button {
                                text: "+ Add Game"
                                flat: true
                                font.pixelSize: 12
                                background: Rectangle { color: accentColor; radius: 6 }
                                contentItem: Text { text: "+ Add Game"; color: "#FFFFFF"; font.pixelSize: 12; font.bold: true }
                            }
                        }

                        ListView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 200
                            clip: true

                            model: ListModel {
                                ListElement { name: "Cyberpunk 2077"; proton: "Proton GE 9.11"; gpu: "Performance"; hud: "On"; shader: "Cached" }
                                ListElement { name: "Elden Ring"; proton: "Proton 9.0"; gpu: "Balanced"; hud: "Off"; shader: "Cached" }
                                ListElement { name: "Valheim"; proton: "Proton 8.0"; gpu: "Eco"; hud: "Off"; shader: "Compiling" }
                                ListElement { name: "Red Dead 2"; proton: "Proton Experimental"; gpu: "Performance"; hud: "On"; shader: "Cached" }
                                ListElement { name: "Hades II"; proton: "Steam Linux Runtime"; gpu: "Balanced"; hud: "Off"; shader: "Cached" }
                            }

                            header: Rectangle {
                                width: parent.width; height: 32; color: "#121624"; radius: 4
                                RowLayout {
                                    anchors.fill: parent; anchors.margins: 8; spacing: 12
                                    Text { text: "Game"; font.pixelSize: 11; color: mutedText; font.bold: true; Layout.preferredWidth: 140 }
                                    Text { text: "Proton"; font.pixelSize: 11; color: mutedText; font.bold: true; Layout.preferredWidth: 140 }
                                    Text { text: "GPU Mode"; font.pixelSize: 11; color: mutedText; font.bold: true; Layout.preferredWidth: 80 }
                                    Text { text: "HUD"; font.pixelSize: 11; color: mutedText; font.bold: true; Layout.preferredWidth: 50 }
                                    Text { text: "Shader"; font.pixelSize: 11; color: mutedText; font.bold: true; Layout.preferredWidth: 80 }
                                    Item { Layout.fillWidth: true }
                                }
                            }

                            delegate: Rectangle {
                                width: parent.width; height: 36; color: index % 2 === 0 ? "#1E1E32" : "transparent"
                                RowLayout {
                                    anchors.fill: parent; anchors.margins: 8; spacing: 12
                                    Text { text: name; font.pixelSize: 13; color: textColor; Layout.preferredWidth: 140 }
                                    Text { text: proton; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 140 }
                                    Text { text: gpu; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 80 }
                                    Text { text: hud === "On" ? "\u2713" : "\u2717"; font.pixelSize: 13; color: hud === "On" ? "#4CAF50" : "#E53935"; Layout.preferredWidth: 50 }
                                    Text { text: shader; font.pixelSize: 11; color: shader === "Cached" ? "#4CAF50" : accentColor; Layout.preferredWidth: 80 }
                                    Item { Layout.fillWidth: true }
                                    Text { text: "\u2699 \u{1F5D1}"; font.pixelSize: 13; color: mutedText }
                                }
                            }
                        }
                    }
                }

                // Proton Manager + Shader Cache
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    // Proton Manager
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 120
                        color: surfaceColor
                        radius: 12
                        border.color: "#2A2A3E"
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 16; spacing: 10
                            Text { text: "Proton Version Manager"; font.pixelSize: 14; font.bold: true; color: textColor }

                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                ComboBox {
                                    Layout.fillWidth: true
                                    model: ["Proton 9.0 (stable)", "Proton Experimental", "Proton GE 9.11", "Proton 8.0", "Steam Linux Runtime"]
                                    currentIndex: 0
                                    font.pixelSize: 12
                                    background: Rectangle { color: "#2A2A3E"; radius: 6; border.color: "#3A3A4E" }
                                    contentItem: Text { text: parent.currentText; color: textColor; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 8 }
                                }

                                Button {
                                    text: "Set Default"
                                    flat: true
                                    Layout.preferredHeight: 32
                                    font.pixelSize: 11
                                    background: Rectangle { color: accentColor; radius: 6 }
                                    contentItem: Text { text: "Set Default"; color: "#FFFFFF"; font.pixelSize: 11; font.bold: true }
                                }
                            }
                        }
                    }

                    // Shader Cache
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 120
                        color: surfaceColor
                        radius: 12
                        border.color: "#2A2A3E"
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 16; spacing: 10
                            Text { text: "Shader Cache Management"; font.pixelSize: 14; font.bold: true; color: textColor }
                            Text { text: "1.2 GB cached \u2022 43 games"; font.pixelSize: 12; color: "#4CAF50" }
                            RowLayout { spacing: 8
                                Button { text: "Clear Cache"; flat: true; font.pixelSize: 11; Layout.preferredHeight: 32; background: Rectangle { color: "#E53935"; radius: 6; opacity: 0.8 }; contentItem: Text { text: "Clear Cache"; color: "#FFFFFF"; font.pixelSize: 11 } }
                                Button { text: "Pre-compile All"; flat: true; font.pixelSize: 11; Layout.preferredHeight: 32; background: Rectangle { color: accentColor; radius: 6 }; contentItem: Text { text: "Pre-compile All"; color: "#FFFFFF"; font.pixelSize: 11; font.bold: true } }
                                Item { Layout.fillWidth: true }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
