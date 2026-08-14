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
                        Text { text: "Welcome to Synthex"; font.pixelSize: 32; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "The Linux distro that makes all others unnecessary."; font.pixelSize: 14; color: "#9AA1AB"; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "\n• Arch-level software\n• Mint-level simplicity\n• Nobara-level gaming\n• Bazzite-level recovery\n• CachyOS-level performance"; font.pixelSize: 13; color: "#6C88A8"; Layout.alignment: Qt.AlignHCenter; lineHeight: 1.6 }
                        Button {
                            text: "Get Started →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 20
                            onClicked: oobe.currentStep = 1
                            contentItem: Text { text: parent.text; color: "#0C1016"; font.pixelSize: 16; font.bold: true }
                            background: Rectangle { color: "#6C88A8"; radius: 8; implicitWidth: 220; implicitHeight: 48 }
                        }
                    }
                }

                // Page 1: Theme Selection
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 20
                        Text { text: "Choose Your Theme"; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Row { spacing: 24; Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: [
                                    { id: "dark", name: "Dark", bg: "#0C1016", accent: "#6C88A8" },
                                    { id: "light", name: "Light", bg: "#F5F5F7", accent: "#2A2A2E" },
                                    { id: "mint", name: "Synthex Mint", bg: "#2D2D2D", accent: "#6C88A8" }
                                ]
                                Rectangle {
                                    width: 160; height: 120; radius: 12
                                    color: modelData.bg
                                    border.color: oobe.selectedTheme === modelData.id ? "#6C88A8" : "#444"
                                    border.width: oobe.selectedTheme === modelData.id ? 3 : 1
                                    MouseArea { anchors.fill: parent; onClicked: oobe.selectedTheme = modelData.id; cursorShape: Qt.PointingHandCursor }
                                    ColumnLayout { anchors.centerIn: parent; spacing: 8
                                        Rectangle { width: 60; height: 40; radius: 6; color: modelData.accent; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: modelData.name; font.pixelSize: 13; font.bold: true; color: modelData.bg === "#F5F5F7" ? "#2A2A2E" : "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                                    }
                                }
                            }
                        }
                        Button {
                            text: "Next →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12
                            onClicked: oobe.currentStep = 2
                            contentItem: Text { text: parent.text; color: "#0C1016"; font.pixelSize: 14; font.bold: true }
                            background: Rectangle { color: "#6C88A8"; radius: 8; implicitWidth: 160; implicitHeight: 40 }
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
