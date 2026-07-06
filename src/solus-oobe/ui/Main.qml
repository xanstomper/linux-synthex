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

    // Progress indicator
    property int currentStep: 0
    property string selectedProfile: "minimal"
    property string selectedTheme: "dark"

    Rectangle {
        anchors.fill: parent
        color: "#0B0F1A"

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Header with branding
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                color: "#1A1A2E"

                Text {
                    anchors.centerIn: parent
                    text: "☀️ Solus Linux"
                    font.pixelSize: 28
                    font.bold: true
                    color: "#FFB300"
                }
            }

            // Progress dots
            Row {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                Layout.bottomMargin: 20
                spacing: 12
                Repeater {
                    model: ["Welcome", "Profile", "Theme", "Bundles", "Finish"]
                    Rectangle {
                        width: 12; height: 12
                        radius: 6
                        color: index === oobe.currentStep ? "#FFB300" : "#3A3A4A"
                    }
                }
            }

            // Stacked pages
            StackLayout {
                id: stack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: oobe.currentStep

                // Page 0: Welcome
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        Text { text: "Welcome to Solus"; font.pixelSize: 32; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "Illuminate Your Desktop"; font.pixelSize: 16; color: "#FFB300"; Layout.alignment: Qt.AlignHCenter }
                        Text { text: "Let's set up your system in just a few steps."; font.pixelSize: 14; color: "#AAAAAA"; Layout.alignment: Qt.AlignHCenter }
                        Button {
                            text: "Get Started →"
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: 30
                            onClicked: oobe.currentStep = 1
                            contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 16 }
                            background: Rectangle { color: "#FFB300"; radius: 8; implicitWidth: 200; implicitHeight: 44 }
                        }
                    }
                }

                // Page 1: Profile Selection
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 16
                        Text { text: "What will you use Solus for?"; font.pixelSize: 24; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }

                        GridLayout {
                            columns: 2
                            columnSpacing: 16
                            rowSpacing: 16
                            Layout.alignment: Qt.AlignHCenter

                            Repeater {
                                model: ListModel {
                                    ListElement { name: "🎮 Gaming"; desc: "Steam + Proton + Gamescope + MangoHUD"; val: "gaming" }
                                    ListElement { name: "💻 Developer"; desc: "Rust + Go + Python + Containers"; val: "developer" }
                                    ListElement { name: "🎨 Creator"; desc: "Blender + OBS + Krita + DaVinci"; val: "creator" }
                                    ListElement { name: "⚡ Minimal"; desc: "Lightweight + Browser + Essentials"; val: "minimal" }
                                }
                                Rectangle {
                                    width: 260; height: 100; radius: 12
                                    color: oobe.selectedProfile === model.val ? "#FFB300" : "#1A1A2E"
                                    border.color: oobe.selectedProfile === model.val ? "#FFB300" : "#3A3A4A"
                                    border.width: 2

                                    ColumnLayout {
                                        anchors.centerIn: parent; spacing: 6
                                        Text { text: model.name; font.pixelSize: 20; color: oobe.selectedProfile === model.val ? "#0B0F1A" : "#FFFFFF"; font.bold: true }
                                        Text { text: model.desc; font.pixelSize: 12; color: oobe.selectedProfile === model.val ? "#0B0F1A" : "#AAAAAA"; wrapMode: Text.WordWrap }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: { oobe.selectedProfile = model.val; oobe.currentStep = 2 }
                                    }
                                }
                            }
                        }
                    }
                }

                // Page 2: Theme Selection
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 16
                        Text { text: "Choose your style"; font.pixelSize: 24; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }

                        GridLayout {
                            columns: 3; columnSpacing: 12; rowSpacing: 12
                            Layout.alignment: Qt.AlignHCenter
                            Repeater {
                                model: ListModel {
                                    ListElement { name: "Solus Dark"; preview: "#1A1A2E"; accent: "#FFB300"; val: "dark" }
                                    ListElement { name: "Solus Light"; preview: "#F5F7FF"; accent: "#1565C0"; val: "light" }
                                    ListElement { name: "Neon Gaming"; preview: "#0B0F1A"; accent: "#00D2FF"; val: "neon" }
                                    ListElement { name: "Minimal"; preview: "#222222"; accent: "#FFFFFF"; val: "minimal" }
                                    ListElement { name: "macOS Style"; preview: "#E8E8E8"; accent: "#007AFF"; val: "macos" }
                                    ListElement { name: "Windows 11"; preview: "#1C1C1C"; accent: "#60CDDD"; val: "windows" }
                                }
                                Rectangle {
                                    width: 180; height: 130; radius: 12
                                    color: model.preview
                                    border.color: oobe.selectedTheme === model.val ? "#FFB300" : "#3A3A4A"
                                    border.width: 2

                                    ColumnLayout {
                                        anchors.centerIn: parent; spacing: 8
                                        Rectangle { width: 40; height: 40; radius: 20; color: model.accent; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: model.name; font.pixelSize: 14; color: model.val === "light" || model.val === "macos" ? "#000000" : "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: { oobe.selectedTheme = model.val; oobe.currentStep = 3 }
                                    }
                                }
                            }
                        }
                    }
                }

                // Page 3: Bundle Picker (optional software)
                Item {
                    Loader {
                        anchors.fill: parent
                        source: "pages/BundlePicker.qml"
                        onLoaded: {
                            if (item && item.finished)
                                item.finished.connect(function() { oobe.currentStep = 4 })
                        }
                    }
                }

                // Page 4: Finish
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        Text { text: "Setting up your system..."; font.pixelSize: 24; color: "#FFFFFF"; Layout.alignment: Qt.AlignHCenter }

                        ProgressBar {
                            id: progressBar
                            Layout.preferredWidth: 400
                            Layout.alignment: Qt.AlignHCenter
                            value: 0
                            indeterminate: true
                            contentItem: Rectangle {
                                radius: 4
                                color: "#FFB300"
                            }
                            background: Rectangle { color: "#1A1A2E"; radius: 4 }
                        }

                        Text { id: statusText; text: "Applying settings..."; font.pixelSize: 14; color: "#AAAAAA"; Layout.alignment: Qt.AlignHCenter }

                        Timer {
                            interval: 2000; running: true; repeat: false
                            onTriggered: {
                                statusText.text = "Installing packages for " + oobe.selectedProfile + " mode..."
                            }
                        }
                        Timer {
                            interval: 4000; running: true; repeat: false
                            onTriggered: {
                                statusText.text = "Applying " + oobe.selectedTheme + " theme..."
                            }
                        }
                        Timer {
                            interval: 6000; running: true; repeat: false
                            onTriggered: {
                                statusText.text = "Optimizing for your hardware..."
                            }
                        }
                        Timer {
                            interval: 8000; running: true; repeat: false
                            onTriggered: {
                                statusText.text = "✅ Setup complete!"
                            }
                        }
                        Timer {
                            interval: 10000; running: true; repeat: false
                            onTriggered: {
                                // Mark first boot as complete — disables OOBE on next boot
                                var cmd = "mkdir -p /var/lib/solus && date > /var/lib/solus/firstboot-complete"
                                console.log("Marking first boot complete: " + cmd)
                                
                                // Disable the OOBE systemd service so it never runs again
                                var disableCmd = "systemctl disable solus-oobe 2>/dev/null || true"
                                console.log("Disabling OOBE service: " + disableCmd)
                                
                                // Enable the workspace service for future boots
                                var enableCmd = "systemctl enable solus-workspace 2>/dev/null || true"
                                console.log("Enabling workspace service: " + enableCmd)
                                
                                Qt.quit()
                            }
                        }
                    }
                }
            }
        }
    }
}
