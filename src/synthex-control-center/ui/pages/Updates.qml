import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"
    readonly property color okColor: "#43A047"
    readonly property color warnColor: "#FB8C00"
    readonly property color surfaceColor: "#1A1A2E"

    property int updateCount: 0
    property bool checking: false
    property string lastCheck: "Never"
    property var updateList: []

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        Text { text: "Updates"; font.pixelSize: 24; font.bold: true; color: textColor }

        // Status cards
        RowLayout {
            Layout.fillWidth: true; spacing: 16
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 100
                color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16
                    Text { text: "System Updates"; font.pixelSize: 14; font.bold: true; color: textColor }
                    Text { text: checking ? "Checking..." : updateCount + " updates available"; font.pixelSize: 20; font.bold: true; color: updateCount > 0 ? warnColor : okColor }
                    Text { text: "Last check: " + lastCheck; font.pixelSize: 11; color: mutedText }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 100
                color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16
                    Text { text: "Security Updates"; font.pixelSize: 14; font.bold: true; color: textColor }
                    Text { text: "Auto-install enabled"; font.pixelSize: 20; font.bold: true; color: okColor }
                    Text { text: "Critical CVE patches within 48h"; font.pixelSize: 11; color: mutedText }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 100
                color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16
                    Text { text: "Flatpak Updates"; font.pixelSize: 14; font.bold: true; color: textColor }
                    Text { text: "Flathub connected"; font.pixelSize: 20; font.bold: true; color: okColor }
                    Text { text: "Auto-updates from Flathub"; font.pixelSize: 11; color: mutedText }
                }
            }
        }

        // Update pipeline
        Rectangle {
            Layout.fillWidth: true; color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12
                Text { text: "Update Pipeline"; font.pixelSize: 16; font.bold: true; color: textColor }
                RowLayout { spacing: 24
                    Rectangle { width: 80; height: 80; radius: 8; color: "#1E3A1E"
                        ColumnLayout { anchors.centerIn: parent; spacing: 4
                            Text { text: "💾"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Snapshot"; font.pixelSize: 10; color: okColor; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Before"; font.pixelSize: 9; color: mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                    Text { text: "→"; font.pixelSize: 24; color: mutedText }
                    Rectangle { width: 80; height: 80; radius: 8; color: "#1E2A3E"
                        ColumnLayout { anchors.centerIn: parent; spacing: 4
                            Text { text: "📦"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Download"; font.pixelSize: 10; color:="#1E88E5"; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "DNF5"; font.pixelSize: 9; color: mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                    Text { text: "→"; font.pixelSize: 24; color: mutedText }
                    Rectangle { width: 80; height: 80; radius: 8; color: "#2A1E3E"
                        ColumnLayout { anchors.centerIn: parent; spacing: 4
                            Text { text: "✅"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Verify"; font.pixelSize: 10; color:="#9B59B6"; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Integrity"; font.pixelSize: 9; color: mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                    Text { text: "→"; font.pixelSize: 24; color: mutedText }
                    Rectangle { width: 80; height: 80; radius: 8; color: "#3A1E1E"
                        ColumnLayout { anchors.centerIn: parent; spacing: 4
                            Text { text: "🔄"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Apply"; font.pixelSize: 10; color:="#E74C3C"; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Atomic"; font.pixelSize: 9; color: mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                    Text { text: "→"; font.pixelSize: 24; color: mutedText }
                    Rectangle { width: 80; height: 80; radius: 8; color: "#1E3A2E"
                        ColumnLayout { anchors.centerIn: parent; spacing: 4
                            Text { text: "🥾"; font.pixelSize: 20; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Boot Check"; font.pixelSize: 10; color: okColor; Layout.alignment: Qt.AlignHCenter }
                            Text { text: "Verify"; font.pixelSize: 9; color: mutedText; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                }
            }
        }

        // Actions
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Button {
                text: checking ? "Checking..." : "Check for Updates"
                Layout.fillWidth: true; Layout.preferredHeight: 48
                enabled: !checking
                background: Rectangle { color: accentColor; radius: 8 }
                contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                onClicked: { checking = true; updateCount = 0; lastCheck = "Just now"; timer.start() }
            }
            Button {
                text: "Update All"
                Layout.fillWidth: true; Layout.preferredHeight: 48
                background: Rectangle { color: "#1E88E5"; radius: 8 }
                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter }
            }
            Button {
                text: "Snapshot First"
                Layout.fillWidth: true; Layout.preferredHeight: 48
                background: Rectangle { color: "#9B59B6"; radius: 8 }
                contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter }
            }
        }

        Timer {
            id: timer; interval: 3000; running: false; repeat: false
            onTriggered: { checking = false; updateCount = Math.floor(Math.random() * 15) + 1 }
        }

        Item { Layout.fillHeight: true }
    }
}
