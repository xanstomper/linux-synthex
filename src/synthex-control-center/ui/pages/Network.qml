import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: networkPage
    anchors.fill: parent

    readonly property color accentColor: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.accentColor : "#7AA2F7"
    readonly property color cardBg: "#161C24"
    readonly property color itemBg: "#1E2632"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    property bool wifiEnabled: true
    property bool airplaneMode: false
    property string connectedSsid: "SynthNet-5G"
    property string ipAddress: "192.168.1.142"
    property string gateway: "192.168.1.1"
    property string dnsServer: "1.1.1.1, 8.8.8.8"
    property string macAddress: "e4:5f:01:8b:22:9c"

    ScrollView {
        anchors.fill: parent
        anchors.margins: 28
        clip: true

        ColumnLayout {
            width: networkPage.width - 56
            spacing: 22

            // ── Header & Master Toggles ────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    width: 44; height: 44; radius: 10
                    color: networkPage.accentColor
                    Text { text: "󰤨"; font.family: "Symbols Nerd Font"; font.pixelSize: 22; color: "#0C1116"; anchors.centerIn: parent }
                }

                ColumnLayout {
                    spacing: 2
                    Text { text: "Network & Internet"; font.family: "Inter"; font.pixelSize: 20; font.bold: true; color: networkPage.textColor }
                    Text { text: "Wi-Fi connections, Ethernet adapters, IP routing, and VPN tunnels"; font.family: "Inter"; font.pixelSize: 12; color: networkPage.mutedText }
                }

                Item { Layout.fillWidth: true }

                // Airplane mode toggle
                Rectangle {
                    Layout.preferredWidth: 150; height: 38; radius: 8
                    color: networkPage.airplaneMode ? "#30f7768e" : networkPage.itemBg
                    border.color: networkPage.airplaneMode ? "#F7768E" : "#1fffffff"

                    RowLayout {
                        anchors.fill: parent; anchors.margins: 10; spacing: 8
                        Text { text: "✈"; font.pixelSize: 14; color: networkPage.airplaneMode ? "#F7768E" : networkPage.mutedText }
                        Text { text: "Airplane Mode"; font.family: "Inter"; font.pixelSize: 12; font.bold: networkPage.airplaneMode; color: "#FFFFFF"; Layout.fillWidth: true }
                        Switch {
                            checked: networkPage.airplaneMode
                            onToggled: {
                                networkPage.airplaneMode = checked
                                if (checked) networkPage.wifiEnabled = false
                            }
                        }
                    }
                }
            }

            // ── 1. Wi-Fi Master Card ───────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: networkPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: wifiCol.implicitHeight + 32

                ColumnLayout {
                    id: wifiCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Text { text: "󰤨"; font.family: "Symbols Nerd Font"; font.pixelSize: 20; color: networkPage.accentColor }
                        ColumnLayout {
                            spacing: 1
                            Text { text: "Wi-Fi"; font.family: "Inter"; font.pixelSize: 14; font.bold: true; color: networkPage.textColor }
                            Text { text: networkPage.wifiEnabled ? ("Connected to " + networkPage.connectedSsid) : "Wi-Fi adapter is turned off"; font.family: "Inter"; font.pixelSize: 11; color: networkPage.mutedText }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            checked: networkPage.wifiEnabled
                            onToggled: networkPage.wifiEnabled = checked
                        }
                    }

                    // Available Wi-Fi Networks List
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: networkPage.wifiEnabled

                        Text { text: "AVAILABLE NETWORKS"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: networkPage.accentColor; Layout.topMargin: 4 }

                        Repeater {
                            model: [
                                { ssid: "SynthNet-5G", signal: 95, secure: true, connected: true, freq: "5 GHz" },
                                { ssid: "QuantumFiber_Guest", signal: 78, secure: true, connected: false, freq: "5 GHz" },
                                { ssid: "HomeNetwork_2.4G", signal: 64, secure: true, connected: false, freq: "2.4 GHz" },
                                { ssid: "Starlink-HighSpeed", signal: 45, secure: true, connected: false, freq: "5 GHz" },
                                { ssid: "OpenCoffeeWiFi", signal: 30, secure: false, connected: false, freq: "2.4 GHz" }
                            ]

                            Rectangle {
                                Layout.fillWidth: true
                                height: 48
                                radius: 8
                                color: modelData.connected ? "#207aa2f7" : networkPage.itemBg
                                border.color: modelData.connected ? networkPage.accentColor : "#15ffffff"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 14
                                    anchors.rightMargin: 14
                                    spacing: 12

                                    Text {
                                        text: modelData.signal > 70 ? "󰤨" : (modelData.signal > 40 ? "󰤥" : "󰤢")
                                        font.family: "Symbols Nerd Font"
                                        font.pixelSize: 16
                                        color: modelData.connected ? networkPage.accentColor : networkPage.mutedText
                                    }

                                    ColumnLayout {
                                        spacing: 1
                                        Text { text: modelData.ssid; font.family: "Inter"; font.pixelSize: 13; font.bold: modelData.connected; color: "#FFFFFF" }
                                        Text { text: modelData.freq + (modelData.secure ? " • Secured (WPA3)" : " • Open Network"); font.family: "Inter"; font.pixelSize: 10; color: networkPage.mutedText }
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        visible: modelData.connected
                                        text: "󰄬 CONNECTED"
                                        font.family: "Inter"
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: networkPage.accentColor
                                    }

                                    Button {
                                        visible: !modelData.connected
                                        text: "Connect"
                                        contentItem: Text { text: parent.text; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: "#FFFFFF" }
                                        background: Rectangle { color: "#257aa2f7"; border.color: networkPage.accentColor; radius: 6; implicitWidth: 80; implicitHeight: 28 }
                                        onClicked: {
                                            networkPage.connectedSsid = modelData.ssid
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── 2. Active Connection Details & IP Configuration ────────────
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: networkPage.cardBg
                border.color: "#1fffffff"
                implicitHeight: detailsCol.implicitHeight + 32

                ColumnLayout {
                    id: detailsCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text { text: "CONNECTION PROPERTIES (IPv4 / IPv6)"; font.family: "Inter"; font.pixelSize: 11; font.bold: true; color: networkPage.accentColor }

                    GridLayout {
                        columns: 2
                        rowSpacing: 12
                        columnSpacing: 20
                        Layout.fillWidth: true

                        // IP Address
                        ColumnLayout {
                            spacing: 2
                            Text { text: "IPv4 Address"; font.family: "Inter"; font.pixelSize: 11; color: networkPage.mutedText }
                            Text { text: networkPage.ipAddress; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                        }

                        // Gateway
                        ColumnLayout {
                            spacing: 2
                            Text { text: "Default Gateway"; font.family: "Inter"; font.pixelSize: 11; color: networkPage.mutedText }
                            Text { text: networkPage.gateway; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                        }

                        // DNS
                        ColumnLayout {
                            spacing: 2
                            Text { text: "DNS Servers"; font.family: "Inter"; font.pixelSize: 11; color: networkPage.mutedText }
                            Text { text: networkPage.dnsServer; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                        }

                        // MAC
                        ColumnLayout {
                            spacing: 2
                            Text { text: "Hardware MAC Address"; font.family: "Inter"; font.pixelSize: 11; color: networkPage.mutedText }
                            Text { text: networkPage.macAddress; font.family: "Inter"; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                        }
                    }
                }
            }
        }
    }
}
