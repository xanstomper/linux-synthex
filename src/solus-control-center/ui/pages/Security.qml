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
    readonly property color dangerColor: "#E53935"
    readonly property color surfaceColor: "#1A1A2E"

    ColumnLayout {
        anchors.fill: parent; spacing: 20

        Text { text: "Security"; font.pixelSize: 24; font.bold: true; color: textColor }

        // Security overview cards
        GridLayout {
            Layout.fillWidth: true; columns: 4; rowSpacing: 12; columnSpacing: 14
            StatCard { label: "Firewall"; value: "Active"; icon: "🔥"; iconColor: okColor }
            StatCard { label: "SELinux"; value: "Enforcing"; icon: "🔒"; iconColor: okColor }
            StatCard { label: "Secure Boot"; value: "Enabled"; icon: "🔐"; iconColor: okColor }
            StatCard { label: "Disk Encryption"; value: "LUKS2"; icon: "💾"; iconColor: okColor }
        }

        // Security details
        RowLayout {
            Layout.fillWidth: true; spacing: 16

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 260
                color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                    Text { text: "🛡️ Active Protection"; font.pixelSize: 16; font.bold: true; color: textColor }
                    Repeater {
                        model: [
                            { name: "Firewalld (nftables)", status: "enabled", icon: "✅" },
                            { name: "SELinux (enforcing)", status: "enabled", icon: "✅" },
                            { name: "Secure Boot (shim+GRUB)", status: "enabled", icon: "✅" },
                            { name: "TPM2 measured boot", status: "enabled", icon: "✅" },
                            { name: "Kernel lockdown", status: "enabled", icon: "✅" },
                            { name: "Flatpak sandboxing", status: "enabled", icon: "✅" },
                            { name: "Application permissions", status: "active", icon: "✅" },
                            { name: "Hardened sysctl", status: "enabled", icon: "✅" }
                        ]
                        RowLayout { Layout.fillWidth: true; spacing: 8
                            Text { text: modelData.icon; font.pixelSize: 14 }
                            Text { text: modelData.name; font.pixelSize: 13; color: textColor; Layout.fillWidth: true }
                            Rectangle { width: 60; height: 20; radius: 10; color: okColor
                                Text { anchors.centerIn: parent; text: "ON"; font.pixelSize: 10; font.bold: true; color: "#FFFFFF" }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 260
                color: surfaceColor; radius: 12; border.color: "#2A2A3E"; border.width: 1
                ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8
                    Text { text: "🔍 Security Audit"; font.pixelSize: 16; font.bold: true; color: textColor }
                    Repeater {
                        model: [
                            { check: "Firewall rules", pass: true },
                            { check: "SELinux policy", pass: true },
                            { check: "Open ports scan", pass: true },
                            { check: "SSH config", pass: true },
                            { check: "User permissions", pass: true },
                            { check: "File permissions", pass: true },
                            { check: "Package signatures", pass: true },
                            { check: "Boot integrity", pass: true }
                        ]
                        RowLayout { Layout.fillWidth: true; spacing: 8
                            Rectangle { width: 8; height: 8; radius: 4; color: modelData.pass ? okColor : dangerColor }
                            Text { text: modelData.check; font.pixelSize: 13; color: textColor; Layout.fillWidth: true }
                            Text { text: modelData.pass ? "Pass" : "Fail"; font.pixelSize: 12; color: modelData.pass ? okColor : dangerColor }
                        }
                    }
                }
            }
        }

        // Quick actions
        Card {
            Layout.fillWidth: true; title: "Quick Actions"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12
                Button { text: "Run Security Audit"; background: Rectangle { color: accentColor; radius: 8 }
                    contentItem: Text { text: parent.text; color: "#0B0F1A"; font.pixelSize: 13; font.bold: true }
                }
                Button { text: "View Firewall Rules"; background: Rectangle { color: "#1E88E5"; radius: 8 }
                    contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 13 }
                }
                Button { text: "Check for CVEs"; background: Rectangle { color: "#FB8C00"; radius: 8 }
                    contentItem: Text { text: parent.text; color: "#FFFFFF"; font.pixelSize: 13 }
                }
            }
        }
    }
}
