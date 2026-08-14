import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "pages" as Pages

ApplicationWindow {
    id: oobe
    visible: true
    width: 800
    height: 600
    title: "Synthex Setup Wizard"
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "#0C1016"

    property int currentStep: 0
    property string selectedTheme: "dark"
    property var selectedBundles: []
    property var selectedApps: []
    property string statusMessage: "Preparing..."
    property bool setupComplete: false

    Rectangle {
        anchors.fill: parent
        color: "#0C1016"

        ColumnLayout {
            anchors.fill: parent; spacing: 0

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80; color: "#171D24"
                RowLayout { anchors.centerIn: parent; spacing: 12
                    Rectangle { width: 40; height: 40; radius: 10; color: "#6C88A8"
                        Text { anchors.centerIn: parent; text: "S"; font.pixelSize: 24; font.bold: true; color: "#0C1016" }
                    }
                    ColumnLayout { spacing: 2
                        Text { text: "Synthex"; font.pixelSize: 24; font.bold: true; color: "#FFFFFF" }
                        Text { text: "Illuminate Your Desktop"; font.pixelSize: 12; color: "#6C88A8" }
                    }
                }
            }

            // Progress dots
            Row { Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 20; Layout.bottomMargin: 16; spacing: 16
                Repeater {
                    model: ["Welcome", "Theme", "Apps", "Finish"]
                    Row { spacing: 8
                        Rectangle {
                            width: 12; height: 12; radius: 6
                            color: index <= oobe.currentStep ? "#6C88A8" : "#3A3A4A"
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }
                        Text { text: modelData; font.pixelSize: 11; color: index <= oobe.currentStep ? "#6C88A8" : "#666" }
                    }
                }
            }

            StackLayout {
                id: stack
                Layout.fillWidth: true; Layout.fillHeight: true
                currentIndex: oobe.currentStep

                // Page 0: Welcome
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 20
                        Text { text: "Welcome to SynthOS"; font.pixelSize: 32; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "Refined. Minimal. Yours."; font.pixelSize: 14; color: "#9AA1AB"; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "Choose how you would like to set up your desktop:"; font.pixelSize: 13; color: "#7AA2F7"; Layout.alignment: Qt.AlignHCenter }

                        RowLayout {
                            spacing: 16
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: 16

                            // Option 1: Customize Desktop
                            Button {
                                text: "🎨 Customize Desktop →"
                                onClicked: oobe.currentStep = 1
                                contentItem: Text { text: parent.text; color: "#0C1016"; font.pixelSize: 15; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                                background: Rectangle { color: "#7AA2F7"; radius: 10; implicitWidth: 200; implicitHeight: 48 }
                            }

                            // Option 2: Skip & Use Default
                            Button {
                                text: "⚡ Skip & Use Defaults"
                                onClicked: {
                                    oobe.selectedTheme = "nova"
                                    oobe.currentStep = 3
                                }
                                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                                background: Rectangle { color: "#1E2633"; border.color: "#28ffffff"; radius: 10; implicitWidth: 190; implicitHeight: 48 }
                            }
                        }
                    }
                }

                // Page 1: Theme & Finish Selection
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 18
                        Text { text: "Desktop Style & Theme"; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }

                        // Finish: Glass vs Matte
                        RowLayout {
                            spacing: 16
                            Layout.alignment: Qt.AlignHCenter

                            Rectangle {
                                width: 180; height: 54; radius: 10
                                color: oobe.selectedTheme.includes("glass") || oobe.selectedTheme === "nova" ? "#257aa2f7" : "#14ffffff"
                                border.color: oobe.selectedTheme.includes("glass") || oobe.selectedTheme === "nova" ? "#7AA2F7" : "#20ffffff"
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: oobe.selectedTheme = "nova" }
                                RowLayout { anchors.centerIn: parent; spacing: 8
                                    Text { text: "✨"; font.pixelSize: 18 }
                                    Text { text: "Liquid Glass"; font.bold: true; color: "#FFFFFF" }
                                }
                            }

                            Rectangle {
                                width: 180; height: 54; radius: 10
                                color: oobe.selectedTheme === "matte" ? "#257aa2f7" : "#14ffffff"
                                border.color: oobe.selectedTheme === "matte" ? "#7AA2F7" : "#20ffffff"
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: oobe.selectedTheme = "matte" }
                                RowLayout { anchors.centerIn: parent; spacing: 8
                                    Text { text: "⬛"; font.pixelSize: 18 }
                                    Text { text: "Solid Matte"; font.bold: true; color: "#FFFFFF" }
                                }
                            }
                        }

                        // Presets
                        Row { spacing: 14; Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: [
                                    { id: "nova", name: "Nova Dark", bg: "#141923", accent: "#7AA2F7" },
                                    { id: "tokyonight", name: "Tokyo Night", bg: "#1A1B26", accent: "#7AA2F7" },
                                    { id: "catppuccin", name: "Catppuccin", bg: "#1E1E2E", accent: "#89B4FA" },
                                    { id: "nord", name: "Nord Frost", bg: "#2E3440", accent: "#88C0D0" },
                                    { id: "cyberpunk", name: "Cyberpunk", bg: "#0D0D18", accent: "#00F0FF" }
                                ]
                                Rectangle {
                                    width: 108; height: 86; radius: 10
                                    color: modelData.bg
                                    border.color: oobe.selectedTheme === modelData.id ? "#7AA2F7" : "#33ffffff"
                                    border.width: oobe.selectedTheme === modelData.id ? 2 : 1
                                    MouseArea { anchors.fill: parent; onClicked: oobe.selectedTheme = modelData.id; cursorShape: Qt.PointingHandCursor }
                                    ColumnLayout { anchors.centerIn: parent; spacing: 6
                                        Rectangle { width: 34; height: 20; radius: 4; color: modelData.accent; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: modelData.name; font.pixelSize: 11; font.bold: true; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                                    }
                                }
                            }
                        }

                        Button {
                            text: "Next →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 8
                            onClicked: oobe.currentStep = 2
                            contentItem: Text { text: parent.text; color: "#0C1016"; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                            background: Rectangle { color: "#7AA2F7"; radius: 8; implicitWidth: 160; implicitHeight: 40 }
                        }
                    }
                }

                // Page 2: App Picker (37 popular apps)
                Pages.AppPicker {
                    id: appPicker
                    anchors.fill: parent
                    anchors.margins: 0
                    onFinished: {
                        var selectedApps = []
                        for (var i = 0; i < appPicker.appList.model.count; i++) {
                            var item = appPicker.appList.model.get(i)
                            if (item.checked) selectedApps.push(item.id)
                        }
                        oobe.selectedApps = selectedApps
                        oobe.currentStep = 3
                    }
                }
                // Page 3: Finish (uses dedicated Finish page)
                Pages.Finish {
                    id: finishPageItem
                    anchors.fill: parent
                    anchors.margins: 0
                    selectedTheme: oobe.selectedTheme
                    selectedBundles: oobe.selectedBundles
                    selectedApps: oobe.selectedApps
                }
            }
        }
    }
}
