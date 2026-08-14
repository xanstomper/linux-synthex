import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 430
    height: 200
    radius: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cornerRadius : 18
    color: "#a612161f" // Translucent liquid glass
    border.color: "#28ffffff"
    border.width: 1

    property int cpuPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cpuPct : 32
    property int ramPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.ramPct : 46
    property int diskPct: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.diskPct : 61
    property string downSpeed: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.netDownSpeed : "128 KB/s"
    property string upSpeed: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.netUpSpeed : "42 KB/s"
    property string uptimeStr: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.uptimeStr : "2h 15m"
    property string kernelStr: (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.kernelStr : "6.3.9-synth"

    // Liquid Glass Specular Top Highlight
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22ffffff" }
            GradientStop { position: 0.08; color: "#06ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }

    Connections {
        target: (typeof systemBridge !== "undefined") ? systemBridge : null
        function onCpuChanged() { cpuCanvas.requestPaint() }
        function onRamChanged() { ramCanvas.requestPaint() }
        function onDiskChanged() { diskCanvas.requestPaint() }
        function onNetChanged() { netCanvas.requestPaint() }
    }

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
                        color: "#A0AAB8"
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
                        var points = (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.cpuHistory : [0.2, 0.35, 0.28, 0.5, 0.32, 0.45, 0.6, 0.4, 0.32, 0.55, 0.32]
                        if (!points || points.length < 2) return
                        var step = width / (points.length - 1)

                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var i = 0; i < points.length; i++) {
                            ctx.lineTo(i * step, height * (1.0 - points[i] * 0.9))
                        }
                        ctx.lineTo(width, height)
                        ctx.closePath()
                        ctx.fillStyle = "rgba(122, 162, 247, 0.25)"
                        ctx.fill()

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
                        color: "#A0AAB8"
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
                        var points = (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.ramHistory : [0.4, 0.42, 0.5, 0.46, 0.52, 0.48, 0.62, 0.45, 0.46, 0.5, 0.46]
                        if (!points || points.length < 2) return
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
                        color: "#A0AAB8"
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
                        var points = (typeof systemBridge !== "undefined" && systemBridge) ? systemBridge.diskHistory : [0.55, 0.6, 0.58, 0.61, 0.63, 0.6, 0.65, 0.62, 0.61, 0.61, 0.61]
                        if (!points || points.length < 2) return
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
                        color: "#A0AAB8"
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
                        color: "#A0AAB8"
                    }
                }
            }
        }
    }
}
