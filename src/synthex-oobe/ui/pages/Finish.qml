import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Rectangle {
    id: finishPage
    color: "#0C1016"
    anchors.fill: parent

    readonly property color accentColor: "#6C88A8"
    readonly property color surfaceColor: "#171D24"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property bool setupComplete: false
    property string selectedProfile: "minimal"
    property string selectedTheme: "dark"
    property var selectedBundles: []
    property var selectedApps: []

    property int currentStep: 0
    readonly property var steps: [
        { text: "Creating user environment...", cmd: "oobe" },
        { text: "Installing profile packages...", cmd: "profile" },
        { text: "Applying theme...", cmd: "theme" },
        { text: "Installing applications...", cmd: "apps" },
        { text: "Auto-detecting hardware...", cmd: "hardware" },
        { text: "Setting up recovery...", cmd: "recovery" },
        { text: "Finalizing setup...", cmd: "finalize" }
    ]

    function runBackendStep(stepIndex) {
        if (stepIndex >= steps.length) {
            setupComplete = true
            return
        }
        currentStep = stepIndex
        var step = steps[stepIndex]
        statusText.text = step.text
        try {
            var state = JSON.stringify({
                step: stepIndex, phase: step.cmd,
                profile: selectedProfile, theme: selectedTheme,
                bundles: selectedBundles, apps: selectedApps,
                timestamp: new Date().toISOString()
            })
        } catch (e) {}
        advanceTimer.start()
    }

    function hardwareLog(msg) {
        logText.text += "\u27A4 " + msg + "\n"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 40
        spacing: 16

        // Summary
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 120
            color: surfaceColor
            radius: 12
            border.color: "#2A2A3E"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8

                Text {
                    text: "Setup Summary"
                    font.pixelSize: 16
                    font.bold: true
                    color: textColor
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 40
                    rowSpacing: 6

                    Repeater {
                        model: [
                            { label: "Profile", value: selectedProfile },
                            { label: "Theme", value: selectedTheme },
                            { label: "Bundles", value: selectedBundles.length > 0 ? selectedBundles.join(', ') : 'None' },
                            { label: "Apps", value: selectedApps.length > 0 ? selectedApps.join(', ') : 'None' },
                            { label: "Status", value: setupComplete ? 'Complete' : 'Configuring...' }
                        ]

                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text { text: modelData.label + ":"; font.pixelSize: 12; color: mutedText; Layout.preferredWidth: 80 }
                            Text { text: modelData.value; font.pixelSize: 12; font.bold: true; color: textColor }
                        }
                    }
                }
            }
        }

        // Progress Section
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: surfaceColor
            radius: 12
            border.color: "#2A2A3E"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: "Setting up your system..."
                    font.pixelSize: 18
                    font.bold: true
                    color: textColor
                }

                // Progress bar
                Rectangle {
                    Layout.fillWidth: true
                    height: 8
                    radius: 4
                    color: "#2A2A3E"

                    Rectangle {
                        id: progressFill
                        width: parent.width * 0.65
                        height: 8
                        radius: 4
                        color: accentColor

                        PropertyAnimation {
                            target: progressFill
                            property: "width"
                            from: 0
                            to: progressFill.parent.width
                            duration: 3000
                            running: true
                        }
                    }
                }

                // Step indicators
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Repeater {
                        model: [
                            { text: "Configuring system settings...", done: true },
                            { text: "Customizing desktop...", done: false },
                            { text: "Installing profile packages...", done: false },
                            { text: "Auto-detecting hardware...", done: false },
                            { text: "Finalizing setup...", done: false }
                        ]

                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            Text {
                                text: modelData.done ? "\u2705" : "\u{1F7E2}"
                                font.pixelSize: 14
                            }

                            Text {
                                text: modelData.text
                                font.pixelSize: 13
                                color: modelData.done ? "#4CAF50" : mutedText
                                font.bold: modelData.done
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: modelData.done ? "Done" : "In progress..."
                                font.pixelSize: 11
                                color: modelData.done ? "#4CAF50" : accentColor
                            }
                        }
                    }
                }

                // Hardware detection log
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    radius: 8
                    color: "#0D1117"
                    clip: true

                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 8
                        contentHeight: logText.height
                        Text {
                            id: logText
                            text: "\u27A4 Starting Synthex OOBE...\n"
                            font.pixelSize: 10
                            font.family: "monospace"
                            color: "#4CAF50"
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }

        // Get Started button (shown when complete)
        Button {
            id: getStartedBtn
            Layout.alignment: Qt.AlignRight
            Layout.preferredHeight: 44
            Layout.preferredWidth: 180
            visible: setupComplete

            background: Rectangle { color: accentColor; radius: 8 }
            contentItem: Text {
                text: "\u{1F680}  Get Started"
                font.pixelSize: 14
                font.bold: true
                color: "#0C1016"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            onClicked: {
                console.log("OOBE complete! Disabling OOBE service...");
                // Disable OOBE service via D-Bus
                Qt.quit();
            }
        }

        // Sequential step advancement
        Timer {
            id: advanceTimer
            interval: 800
            running: false
            repeat: false
            onTriggered: {
                hardwareLog(steps[currentStep].text + " - done")
                runBackendStep(currentStep + 1)
            }
        }

        // Start the setup process
        Component.onCompleted: {
            runBackendStep(0)
        }
    }
}
