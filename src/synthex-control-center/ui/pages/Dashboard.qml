import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ScrollView {
    id: root
    clip: true
    contentWidth: availableWidth

    readonly property color accentColor: "#7AA2F7"
    readonly property color surfaceColor: "#141923"
    readonly property color cardBorder: "rgba(255, 255, 255, 0.08)"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    ColumnLayout {
        width: parent.width
        spacing: 20

        // ── Top Header Title Banner ─────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                spacing: 2

                RowLayout {
                    spacing: 8
                    Text {
                        text: "synth"
                        font.family: "Inter"
                        font.pixelSize: 26
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Text {
                        text: "OS"
                        font.family: "Inter"
                        font.pixelSize: 26
                        font.bold: true
                        color: "#7AA2F7"
                    }
                }

                Text {
                    text: "refined. minimal. yours."
                    font.family: "Inter"
                    font.pixelSize: 13
                    color: "#9AA1AB"
                }

                // Gradient Accent Underline
                Rectangle {
                    Layout.preferredWidth: 160
                    Layout.preferredHeight: 3
                    radius: 2
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: "#7AA2F7" }
                        GradientStop { position: 0.5; color: "#BB9AF7" }
                        GradientStop { position: 1.0; color: "#F7768E" }
                    }
                }
            }

            Item { Layout.fillWidth: true }
        }

        // ── TOP ROW: System Overview + 4 Metric Sparkline Cards ──────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            // 1. System Overview Card
            Rectangle {
                Layout.preferredWidth: 240
                Layout.preferredHeight: 150
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 4

                    Text {
                        text: "SYSTEM OVERVIEW"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    Item { Layout.preferredHeight: 4 }

                    RowLayout {
                        spacing: 8
                        Text { text: "Distro"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "synth OS"; font.pixelSize: 11; font.bold: true; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "Version"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "1.0 (Zenith)"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "Kernel"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "6.3.9-synth"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "Shell"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "fish 3.7.1"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "WM"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "Hyprland"; font.pixelSize: 11; color: textColor }
                    }
                }
            }

            // 2. CPU Metric Card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "CPU"; font.pixelSize: 11; font.bold: true; color: mutedText }
                        Item { Layout.fillWidth: true }
                        Text { text: "32%"; font.pixelSize: 13; font.bold: true; color: "#7AA2F7" }
                    }
                    Text { text: "Intel Core i7-9750H"; font.pixelSize: 11; color: textColor }

                    Item { Layout.fillHeight: true }

                    Canvas {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            var pts = [0.2, 0.35, 0.28, 0.5, 0.32, 0.45, 0.6, 0.4, 0.32, 0.55, 0.32]
                            var step = width / (pts.length - 1)
                            ctx.beginPath(); ctx.moveTo(0, height)
                            for (var i = 0; i < pts.length; i++) ctx.lineTo(i * step, height * (1.0 - pts[i] * 0.9))
                            ctx.lineTo(width, height); ctx.closePath()
                            ctx.fillStyle = "rgba(122, 162, 247, 0.25)"; ctx.fill()

                            ctx.beginPath()
                            for (var j = 0; j < pts.length; j++) {
                                if (j === 0) ctx.moveTo(0, height * (1.0 - pts[j] * 0.9))
                                else ctx.lineTo(j * step, height * (1.0 - pts[j] * 0.9))
                            }
                            ctx.strokeStyle = "#7AA2F7"; ctx.lineWidth = 1.8; ctx.stroke()
                        }
                    }
                }
            }

            // 3. MEMORY Metric Card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "MEMORY"; font.pixelSize: 11; font.bold: true; color: mutedText }
                        Item { Layout.fillWidth: true }
                        Text { text: "46%"; font.pixelSize: 13; font.bold: true; color: "#BB9AF7" }
                    }
                    Text { text: "7.2 GB / 15.6 GB"; font.pixelSize: 11; color: textColor }

                    Item { Layout.fillHeight: true }

                    Canvas {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            var pts = [0.4, 0.42, 0.5, 0.46, 0.52, 0.48, 0.62, 0.45, 0.46, 0.5, 0.46]
                            var step = width / (pts.length - 1)
                            ctx.beginPath(); ctx.moveTo(0, height)
                            for (var i = 0; i < pts.length; i++) ctx.lineTo(i * step, height * (1.0 - pts[i] * 0.9))
                            ctx.lineTo(width, height); ctx.closePath()
                            ctx.fillStyle = "rgba(187, 154, 247, 0.25)"; ctx.fill()

                            ctx.beginPath()
                            for (var j = 0; j < pts.length; j++) {
                                if (j === 0) ctx.moveTo(0, height * (1.0 - pts[j] * 0.9))
                                else ctx.lineTo(j * step, height * (1.0 - pts[j] * 0.9))
                            }
                            ctx.strokeStyle = "#BB9AF7"; ctx.lineWidth = 1.8; ctx.stroke()
                        }
                    }
                }
            }

            // 4. STORAGE Metric Card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "STORAGE"; font.pixelSize: 11; font.bold: true; color: mutedText }
                        Item { Layout.fillWidth: true }
                        Text { text: "61%"; font.pixelSize: 13; font.bold: true; color: "#F7768E" }
                    }
                    Text { text: "141 GB / 232 GB"; font.pixelSize: 11; color: textColor }

                    Item { Layout.fillHeight: true }

                    Canvas {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            var pts = [0.55, 0.6, 0.58, 0.61, 0.63, 0.6, 0.65, 0.62, 0.61, 0.61, 0.61]
                            var step = width / (pts.length - 1)
                            ctx.beginPath(); ctx.moveTo(0, height)
                            for (var i = 0; i < pts.length; i++) ctx.lineTo(i * step, height * (1.0 - pts[i] * 0.9))
                            ctx.lineTo(width, height); ctx.closePath()
                            ctx.fillStyle = "rgba(247, 118, 142, 0.25)"; ctx.fill()

                            ctx.beginPath()
                            for (var j = 0; j < pts.length; j++) {
                                if (j === 0) ctx.moveTo(0, height * (1.0 - pts[j] * 0.9))
                                else ctx.lineTo(j * step, height * (1.0 - pts[j] * 0.9))
                            }
                            ctx.strokeStyle = "#F7768E"; ctx.lineWidth = 1.8; ctx.stroke()
                        }
                    }
                }
            }

            // 5. NETWORK Metric Card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "NETWORK"; font.pixelSize: 11; font.bold: true; color: mutedText }
                        Item { Layout.fillWidth: true }
                        Text { text: "↓ 128 KB/s  ↑ 42 KB/s"; font.pixelSize: 11; font.bold: true; color: "#73DACA" }
                    }

                    Item { Layout.fillHeight: true }

                    Canvas {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            var pts = [0.1, 0.3, 0.2, 0.7, 0.4, 0.85, 0.3, 0.5, 0.2, 0.4, 0.6, 0.2, 0.3]
                            var step = width / (pts.length - 1)
                            ctx.beginPath(); ctx.moveTo(0, height)
                            for (var i = 0; i < pts.length; i++) ctx.lineTo(i * step, height * (1.0 - pts[i] * 0.85))
                            ctx.lineTo(width, height); ctx.closePath()
                            ctx.fillStyle = "rgba(115, 218, 202, 0.20)"; ctx.fill()

                            ctx.beginPath()
                            for (var j = 0; j < pts.length; j++) {
                                if (j === 0) ctx.moveTo(0, height * (1.0 - pts[j] * 0.85))
                                else ctx.lineTo(j * step, height * (1.0 - pts[j] * 0.85))
                            }
                            ctx.strokeStyle = "#73DACA"; ctx.lineWidth = 1.5; ctx.stroke()
                        }
                    }
                }
            }
        }

        // ── BOTTOM ROW: Processes, Disk Usage, Hardware, Network, Quick Actions
        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            // 1. TOP PROCESSES
            Rectangle {
                Layout.preferredWidth: 240
                Layout.preferredHeight: 200
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 6

                    Text {
                        text: "TOP PROCESSES"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Process"; font.pixelSize: 10; color: mutedText; Layout.preferredWidth: 80 }
                        Text { text: "PID"; font.pixelSize: 10; color: mutedText; Layout.preferredWidth: 40 }
                        Text { text: "CPU%"; font.pixelSize: 10; color: mutedText; Layout.preferredWidth: 40 }
                        Text { text: "MEM%"; font.pixelSize: 10; color: mutedText; Layout.preferredWidth: 40 }
                    }

                    Repeater {
                        model: [
                            { name: "firefox", icon: "🌐", pid: "2456", cpu: "6.7", mem: "2.8", col: "#FF7139" },
                            { name: "spotify", icon: "🎵", pid: "3184", cpu: "3.1", mem: "2.1", col: "#1DB954" },
                            { name: "code", icon: "💻", pid: "4512", cpu: "2.4", mem: "3.3", col: "#007ACC" },
                            { name: "obs", icon: "📹", pid: "2140", cpu: "1.8", mem: "2.6", col: "#9D7CD8" },
                            { name: "discord", icon: "💬", pid: "5620", cpu: "1.3", mem: "1.7", col: "#5865F2" }
                        ]

                        RowLayout {
                            Layout.fillWidth: true
                            RowLayout {
                                Layout.preferredWidth: 80
                                spacing: 4
                                Text { text: modelData.icon; font.pixelSize: 10 }
                                Text { text: modelData.name; font.pixelSize: 11; color: textColor; elide: Text.ElideRight }
                            }
                            Text { text: modelData.pid; font.pixelSize: 10; color: mutedText; Layout.preferredWidth: 40 }
                            Text { text: modelData.cpu; font.pixelSize: 10; color: textColor; Layout.preferredWidth: 40 }
                            Text { text: modelData.mem; font.pixelSize: 10; color: textColor; Layout.preferredWidth: 40 }
                        }
                    }
                }
            }

            // 2. DISK USAGE
            Rectangle {
                Layout.preferredWidth: 240
                Layout.preferredHeight: 200
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    Text {
                        text: "DISK USAGE"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    Repeater {
                        model: [
                            { part: "/ (root)", pct: "82%", val: "45 GB / 72 GB", col: "#73DACA" },
                            { part: "/home", pct: "55%", val: "98 GB / 176 GB", col: "#7AA2F7" },
                            { part: "/boot", pct: "26%", val: "0.3 GB / 1 GB", col: "#E0AF68" },
                            { part: "/var", pct: "34%", val: "6 GB / 20 GB", col: "#2AC3DE" }
                        ]

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.part; font.pixelSize: 11; color: textColor }
                                Rectangle {
                                    width: 32; height: 16; radius: 4; color: "rgba(255,255,255,0.08)"
                                    Text { text: modelData.pct; font.pixelSize: 9; font.bold: true; color: modelData.col; anchors.centerIn: parent }
                                }
                                Item { Layout.fillWidth: true }
                                Text { text: modelData.val; font.pixelSize: 10; color: mutedText }
                            }

                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 4; radius: 2; color: "rgba(255,255,255,0.06)"
                                Rectangle { width: parent.width * (parseInt(modelData.pct)/100.0); height: parent.height; radius: 2; color: modelData.col }
                            }
                        }
                    }
                }
            }

            // 3. HARDWARE
            Rectangle {
                Layout.preferredWidth: 230
                Layout.preferredHeight: 200
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 6

                    Text {
                        text: "HARDWARE"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    RowLayout {
                        spacing: 8
                        Text { text: "CPU"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "Intel i7-9750H"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "GPU"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "NVIDIA GTX 1650"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "RAM"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "16 GB DDR4"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "Disk"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "NVMe 512GB"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "Battery"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 48 }
                        Text { text: "82% (Charging)"; font.pixelSize: 11; font.bold: true; color: "#73DACA" }
                    }
                }
            }

            // 4. NETWORK INTERFACES
            Rectangle {
                Layout.preferredWidth: 210
                Layout.preferredHeight: 200
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 6

                    Text {
                        text: "NETWORK INTERFACES"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    RowLayout {
                        spacing: 8
                        Text { text: "wlan0"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 60 }
                        Text { text: "192.168.1.58"; font.pixelSize: 11; color: textColor }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "eth0"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 60 }
                        Text { text: "Disconnected"; font.pixelSize: 11; color: "#67707D" }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "bluetooth"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 60 }
                        Text { text: "Connected"; font.pixelSize: 11; color: "#7AA2F7" }
                    }
                    RowLayout {
                        spacing: 8
                        Text { text: "vpn0"; font.pixelSize: 11; color: mutedText; Layout.preferredWidth: 60 }
                        Text { text: "Disconnected"; font.pixelSize: 11; color: "#67707D" }
                    }
                }
            }

            // 5. QUICK ACTIONS
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 200
                color: surfaceColor
                radius: 14
                border.color: cardBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    Text {
                        text: "QUICK ACTIONS"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: mutedText
                        font.letterSpacing: 0.5
                    }

                    Repeater {
                        model: [
                            { name: "System Update", icon: "🔄" },
                            { name: "Driver Manager", icon: "🛠" },
                            { name: "Backup System", icon: "💾" },
                            { name: "System Logs", icon: "📋" }
                        ]

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            radius: 8
                            color: "rgba(255, 255, 255, 0.04)"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                spacing: 8
                                Text { text: modelData.icon; font.pixelSize: 12 }
                                Text { text: modelData.name; font.pixelSize: 11; font.weight: Font.Medium; color: textColor }
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onEntered: parent.color = "rgba(255, 255, 255, 0.08)"
                                onExited: parent.color = "rgba(255, 255, 255, 0.04)"
                            }
                        }
                    }
                }
            }
        }
    }
}
