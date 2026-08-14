import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 430
    height: 200
    radius: 18
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property int cpuPct: 32
    property int ramPct: 46
    property int diskPct: 61
    property string downSpeed: "128 KB/s"
    property string upSpeed: "42 KB/s"
    property string uptimeStr: "2h 15m"
    property string kernelStr: "6.3.9-synth"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        // ── 1. Top Sparkline Row (CPU / RAM / DISK) ───────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            // CPU Card
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Text {
                        text: "CPU"
                        font.family: "Inter"
                        font.pixelSize: 12
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: root.cpuPct + "%"
                        font.family: "Inter"
                        font.pixelSize: 12
                        color: "#9AA1AB"
                    }
                }

                // Blue Sparkline Canvas
                Canvas {
                    id: cpuCanvas
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var points = [0.2, 0.35, 0.28, 0.5, 0.32, 0.45, 0.6, 0.4, 0.32, 0.55, 0.32]
                        var step = width / (points.length - 1)

                        // Fill area
                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var i = 0; i < points.length; i++) {
                            ctx.lineTo(i * step, height * (1.0 - points[i] * 0.9))
                        }
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fillStyle = "rgba(122, 162, 247, 0.25)"
                        ctx.fill()

                        // Line stroke
                        ctx.beginPath()
                        for (var j = 0; j < points.length; j++) {
                            if (j === 0) ctx.moveTo(0, height * (1.0 - points[j] * 0.9))
                            else ctx.lineTo(j * step, height * (1.0 - points[j] * 0.9))
                        }
                        ctx.strokeStyle = "#7AA2F7"
                        ctx.lineWidth = 1.8
                        ctx.stroke()
                    }
                }
            }

            // RAM Card
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Text {
                        text: "RAM"
                        font.family: "Inter"
                        font.pixelSize: 12
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: root.ramPct + "%"
                        font.family: "Inter"
                        font.pixelSize: 12
                        color: "#9AA1AB"
                    }
                }

                // Purple Sparkline Canvas
                Canvas {
                    id: ramCanvas
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var points = [0.4, 0.42, 0.5, 0.46, 0.52, 0.48, 0.62, 0.45, 0.46, 0.5, 0.46]
                        var step = width / (points.length - 1)

                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var i = 0; i < points.length; i++) {
                            ctx.lineTo(i * step, height * (1.0 - points[i] * 0.9))
                        }
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fillStyle = "rgba(187, 154, 247, 0.25)"
                        ctx.fill()

                        ctx.beginPath()
                        for (var j = 0; j < points.length; j++) {
                            if (j === 0) ctx.moveTo(0, height * (1.0 - points[j] * 0.9))
                            else ctx.lineTo(j * step, height * (1.0 - points[j] * 0.9))
                        }
                        ctx.strokeStyle = "#BB9AF7"
                        ctx.lineWidth = 1.8
                        ctx.stroke()
                    }
                }
            }

            // DISK Card
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Text {
                        text: "DISK"
                        font.family: "Inter"
                        font.pixelSize: 12
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: root.diskPct + "%"
                        font.family: "Inter"
                        font.pixelSize: 12
                        color: "#9AA1AB"
                    }
                }

                // Gold Sparkline Canvas
                Canvas {
                    id: diskCanvas
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var points = [0.55, 0.6, 0.58, 0.61, 0.63, 0.6, 0.65, 0.62, 0.61, 0.61, 0.61]
                        var step = width / (points.length - 1)

                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var i = 0; i < points.length; i++) {
                            ctx.lineTo(i * step, height * (1.0 - points[i] * 0.9))
                        }
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fillStyle = "rgba(229, 168, 75, 0.25)"
                        ctx.fill()

                        ctx.beginPath()
                        for (var j = 0; j < points.length; j++) {
                            if (j === 0) ctx.moveTo(0, height * (1.0 - points[j] * 0.9))
                            else ctx.lineTo(j * step, height * (1.0 - points[j] * 0.9))
                        }
                        ctx.strokeStyle = "#E5A84B"
                        ctx.lineWidth = 1.8
                        ctx.stroke()
                    }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#0affffff"
        }

        // ── 2. Bottom Row (Network / Uptime / Kernel) ─────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            // Network throughput with teal sparkline
            ColumnLayout {
                Layout.preferredWidth: 220
                spacing: 3

                RowLayout {
                    Text {
                        text: "NETWORK"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Item { Layout.preferredWidth: 8 }
                    Text {
                        text: "↓ " + root.downSpeed + "   ↑ " + root.upSpeed
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: "#73DACA"
                    }
                }

                Canvas {
                    id: netCanvas
                    Layout.fillWidth: true
                    Layout.preferredHeight: 22
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var points = [0.1, 0.3, 0.2, 0.7, 0.4, 0.85, 0.3, 0.5, 0.2, 0.4, 0.6, 0.2, 0.3]
                        var step = width / (points.length - 1)

                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var i = 0; i < points.length; i++) {
                            ctx.lineTo(i * step, height * (1.0 - points[i] * 0.85))
                        }
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fillStyle = "rgba(115, 218, 202, 0.20)"
                        ctx.fill()

                        ctx.beginPath()
                        for (var j = 0; j < points.length; j++) {
                            if (j === 0) ctx.moveTo(0, height * (1.0 - points[j] * 0.85))
                            else ctx.lineTo(j * step, height * (1.0 - points[j] * 0.85))
                        }
                        ctx.strokeStyle = "#73DACA"
                        ctx.lineWidth = 1.5
                        ctx.stroke()
                    }
                }
            }

            Item { Layout.fillWidth: true }

            // Uptime & Kernel
            ColumnLayout {
                spacing: 6
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter

                RowLayout {
                    spacing: 12
                    Text {
                        text: "UPTIME"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Text {
                        text: root.uptimeStr
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: "#9AA1AB"
                    }
                }

                RowLayout {
                    spacing: 12
                    Text {
                        text: "KERNEL"
                        font.family: "Inter"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    Text {
                        text: root.kernelStr
                        font.family: "Inter"
                        font.pixelSize: 11
                        color: "#9AA1AB"
                    }
                }
            }
        }
    }
}
