import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Synthex Welcome Screen — Linux Mint-inspired first-run dashboard
// Single-page design with helpful links and quick actions

ApplicationWindow {
    id: welcome
    visible: true
    width: 800
    height: 520
    title: "Welcome to Synthex"
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "#F5F5F7"

    Rectangle {
        anchors.fill: parent
        color: "#F5F5F7"

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Header — Mint-style green bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                color: "#6C88A8"
                clip: true

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text {
                        text: "☀️"
                        font.pixelSize: 36
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "Welcome to SynthOS"
                        font.pixelSize: 22
                        font.bold: true
                        color: "#FFFFFF"
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "A fast, secure, and elegant operating system"
                        font.pixelSize: 13
                        color: "#E8F5D6"
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }

            // Main content — card grid like Mint's welcome screen
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#F5F5F7"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 16

                    // First row
                    RowLayout {
                        spacing: 12
                        Layout.alignment: Qt.AlignHCenter

                        WelcomeCard {
                            icon: "🖥"
                            title: "Desktop Tour"
                            desc: "Explore your new desktop"
                            onClicked: console.log("tour")
                        }
                        WelcomeCard {
                            icon: "📦"
                            title: "Software Manager"
                            desc: "Install applications"
                            onClicked: console.log("software")
                        }
                        WelcomeCard {
                            icon: "⚙"
                            title: "System Settings"
                            desc: "Customize your system"
                            onClicked: console.log("settings")
                        }
                        WelcomeCard {
                            icon: "🎮"
                            title: "Gaming Setup"
                            desc: "Install gaming tools"
                            onClicked: console.log("gaming")
                        }
                    }

                    // Second row
                    RowLayout {
                        spacing: 12
                        Layout.alignment: Qt.AlignHCenter

                        WelcomeCard {
                            icon: "🌐"
                            title: "First Steps"
                            desc: "Getting started guide"
                            onClicked: console.log("firststeps")
                        }
                        WelcomeCard {
                            icon: "🔒"
                            title: "Security"
                            desc: "Check system security"
                            onClicked: console.log("security")
                        }
                        WelcomeCard {
                            icon: "🎨"
                            title: "Customize"
                            desc: "Themes and appearance"
                            onClicked: console.log("themes")
                        }
                        WelcomeCard {
                            icon: "💬"
                            title: "Community"
                            desc: "Get help and connect"
                            onClicked: console.log("community")
                        }
                    }

                    // Bottom checkbox
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 20
                        CheckBox {
                            id: dontShowAgain
                            text: "Don't show this on startup"
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }
    }
}

// Reusable card component — Mint-style
component WelcomeCard: Rectangle {
    property string icon: ""
    property string title: ""
    property string desc: ""
    signal clicked()

    width: 160
    height: 120
    radius: 8
    color: "#FFFFFF"
    border.color: "#E0E0E0"
    border.width: 1

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 6

        Text {
            text: icon
            font.pixelSize: 28
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            text: title
            font.pixelSize: 13
            font.bold: true
            color: "#2A2A2E"
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            text: desc
            font.pixelSize: 11
            color: "#888888"
            Layout.alignment: Qt.AlignHCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: parent.color = "#F0F7E6"  // Light mint green on hover
        onExited: parent.color = "#FFFFFF"
        onClicked: parent.clicked()
    }
}
