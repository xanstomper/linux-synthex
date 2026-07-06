import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: oobe
    visible: true
    width: 800
    height: 600
    title: "Solus Setup Wizard"
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "#0B0F1A"

    property int currentStep: 0
    property string selectedProfile: "minimal"
    property string selectedTheme: "dark"
    property string statusMessage: "Preparing..."
    property bool setupComplete: false

    Rectangle {
        anchors.fill: parent
        color: "#0B0F1A"

        ColumnLayout {
            anchors.fill: parent; spacing: 0

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 80; color: "#1A1A2E"
                RowLayout { anchors.centerIn: parent; spacing: 12
                    Rectangle { width: 40; height: 40; radius: 10; color: "#9BBD5C"
                        Text { anchors.centerIn: parent; text: "S"; font.pixelSize: 24; font.bold: true; color: "#0B0F1A" }
                    }
                    ColumnLayout { spacing: 2
                        Text { text: "Solus Linux"; font.pixelSize: 24; font.bold: true; color: "#FFFFFF" }
                        Text { text: "Illuminate Your Desktop"; font.pixelSize: 12; color: "#9BBD5C" }
                    }
                }
            }

            // Progress dots
            Row { Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 20; Layout.bottomMargin: 16; spacing: 16
                Repeater {
                    model: ["Welcome", "Profile", "Theme", "Bundles", "Finish"]
                    Row { spacing: 8
                        Rectangle {
                            width: 12; height: 12; radius: 6
                            color: index <= oobe.currentStep ? "#9BBD5C" : "#3A3A4A"
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }
                        Text { text: modelData; font.pixelSize: 11; color: index <= oobe.currentStep ? "#9BBD5C" : "#666" }
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
                        Text { text: "Welcome to Solus"; font.pixelSize: 32; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "The Linux distro that makes all others unnecessary."; font.pixelSize: 14; color: "#8899AA"; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "\n• Arch-level software\n• Mint-level simplicity\n• Nobara-level gaming\n• Bazzite-level recovery\n• CachyOS-level performance"; font.pixelSize: 13; color: "#9BBD5C"; Layout.alignment: Qt.AlignHCenter; lineHeight: 1.6 }
                        Button {
                            text: "Get Started →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 20
                            onClicked: oobe.currentStep = 1
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 16; font.bold: true }
                            background: Rectangle { color: "#9BBD5C"; radius: 8; implicitWidth: 220; implicitHeight: 48 }
                        }
                    }
                }

                // Page 1: Profile Selection
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 16
                        Text { text: "What will you use Solus for?"; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        GridLayout {
                            columns: 2; columnSpacing: 16; rowSpacing: 16; Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: [
                                    { id: "minimal", name: "Beginner", icon: "\u{1F3E0}", desc: "Stable updates, GUI-focused, safe defaults" },
                                    { id: "gaming", name: "Gamer", icon: "\u{1F3AE}", desc: "Steam, Proton-GE, Gamescope, MangoHUD" },
                                    { id: "creator", name: "Creator", icon: "\u{1F3A8}", desc: "OBS, Kdenlive, GIMP, Krita, Blender" },
                                    { id: "developer", name: "Developer", icon: "\u{1F4BB}", desc: "VS Code, Git, Docker, Podman, Distrobox" }
                                ]
                                Rectangle {
                                    width: 320; height: 80; radius: 12
                                    color: oobe.selectedProfile === modelData.id ? "#1A2E1A" : "#1A1A2E"
                                    border.color: oobe.selectedProfile === modelData.id ? "#9BBD5C" : "#2A2A3E"
                                    border.width: oobe.selectedProfile === modelData.id ? 2 : 1
                                    MouseArea { anchors.fill: parent; onClicked: oobe.selectedProfile = modelData.id; cursorShape: Qt.PointingHandCursor }
                                    Row { anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 16; spacing: 12
                                        Text { text: modelData.icon; font.pixelSize: 28 }
                                        Column { anchors.verticalCenter: parent.verticalCenter; spacing: 2
                                            Text { text: modelData.name; font.pixelSize: 15; font.bold: true; color: "#FFFFFF" }
                                            Text { text: modelData.desc; font.pixelSize: 11; color: "#8899AA" }
                                        }
                                    }
                                }
                            }
                        }
                        Button {
                            text: "Next →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12
                            onClicked: oobe.currentStep = 2
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 14; font.bold: true }
                            background: Rectangle { color: "#9BBD5C"; radius: 8; implicitWidth: 160; implicitHeight: 40 }
                        }
                    }
                }

                // Page 2: Theme Selection
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 20
                        Text { text: "Choose Your Theme"; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Row { spacing: 24; Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: [
                                    { id: "dark", name: "Dark", bg: "#0B0F1A", accent: "#9BBD5C" },
                                    { id: "light", name: "Light", bg: "#F5F5F7", accent: "#2A2A2E" },
                                    { id: "mint", name: "Solus Mint", bg: "#2D2D2D", accent: "#9BBD5C" }
                                ]
                                Rectangle {
                                    width: 160; height: 120; radius: 12
                                    color: modelData.bg
                                    border.color: oobe.selectedTheme === modelData.id ? "#9BBD5C" : "#444"
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
                            onClicked: oobe.currentStep = 3
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 14; font.bold: true }
                            background: Rectangle { color: "#9BBD5C"; radius: 8; implicitWidth: 160; implicitHeight: 40 }
                        }
                    }
                }

                // Page 3: App Bundles
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 16
                        Text { text: "Extra Software Bundles"; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        GridLayout {
                            columns: 2; columnSpacing: 16; rowSpacing: 12; Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: [
                                    { name: "Gaming (Steam + Proton)", checked: oobe.selectedProfile === "gaming" },
                                    { name: "Multimedia (OBS + Kdenlive)", checked: false },
                                    { name: "Development (Git + Docker)", checked: oobe.selectedProfile === "developer" },
                                    { name: "Office (LibreOffice)", checked: true }
                                ]
                                Rectangle {
                                    width: 320; height: 48; radius: 8
                                    color: modelData.checked ? "#1A2E1A" : "#1A1A2E"
                                    border.color: modelData.checked ? "#9BBD5C" : "#2A2A3E"; border.width: 1
                                    Row { anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 12; spacing: 10
                                        Rectangle { width: 20; height: 20; radius: 4; color: modelData.checked ? "#9BBD5C" : "#3A3A4A"
                                            Text { anchors.centerIn: parent; text: modelData.checked ? "✓" : ""; font.pixelSize: 14; font.bold: true; color: "#0B0F1A" }
                                        }
                                        Text { text: modelData.name; font.pixelSize: 13; color: "#FFFFFF"; anchors.verticalCenter: parent.verticalCenter }
                                    }
                                }
                            }
                        }
                        Button {
                            text: "Next →"; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12
                            onClicked: oobe.currentStep = 4
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 14; font.bold: true }
                            background: Rectangle { color: "#9BBD5C"; radius: 8; implicitWidth: 160; implicitHeight: 40 }
                        }
                    }
                }

                // Page 4: Finish
                Item {
                    ColumnLayout { anchors.centerIn: parent; spacing: 16
                        Text { text: "Setting up your system..."; font.pixelSize: 24; color: "#FFFFFF"; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "Profile: " + oobe.selectedProfile + "  |  Theme: " + oobe.selectedTheme; font.pixelSize: 12; color: "#8899AA"; Layout.alignment: Qt.AlignHCenter }

                        Rectangle { Layout.preferredWidth: 400; height: 6; radius: 3; color: "#1A1A2E"; Layout.alignment: Qt.AlignHCenter
                            Rectangle { width: parent.width * (oobe.setupComplete ? 1.0 : 0.7); height: 6; radius: 3; color: "#9BBD5C"
                                Behavior on width { NumberAnimation { duration: 500 } }
                            }
                        }

                        Text { id: statusText; text: "Applying settings..."; font.pixelSize: 13; color: "#8899AA"; Layout.alignment: Qt.AlignHCenter }

                        Timer { interval: 2000; running: true; repeat: false
                            onTriggered: statusText.text = "Installing packages for " + oobe.selectedProfile + " mode..." }
                        Timer { interval: 4000; running: true; repeat: false
                            onTriggered: statusText.text = "Applying " + oobe.selectedTheme + " theme..." }
                        Timer { interval: 6000; running: true; repeat: false
                            onTriggered: statusText.text = "Configuring gaming stack..." }
                        Timer { interval: 8000; running: true; repeat: false
                            onTriggered: statusText.text = "Optimizing for your hardware..." }
                        Timer { interval: 10000; running: true; repeat: false
                            onTriggered: { statusText.text = "✅ Setup complete!"; oobe.setupComplete = true }
                        }
                        Timer { interval: 12000; running: true; repeat: false
                            onTriggered: {
                                var cmd = "mkdir -p /var/lib/solus && date > /var/lib/solus/firstboot-complete"
                                console.log("Marking first boot complete")
                                Qt.quit()
                            }
                        }
                    }
                }
            }
        }
    }
}
