import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"
    anchors.fill: parent

    readonly property color accentColor: "#9BBD5C"
    readonly property color surfaceColor: "#1A1A2E"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#8899AA"
    readonly property color okColor: "#43A047"
    readonly property color warnColor: "#FB8C00"
    readonly property color dangerColor: "#E53935"

    property var hwProfile: null
    property bool profileLoaded: false
    property int activeMode: 0

    readonly property var cpu: hwProfile ? hwProfile.cpu : null
    readonly property var gpu: hwProfile ? hwProfile.gpu : null
    readonly property var mem: hwProfile ? hwProfile.memory : null
    readonly property var sys: hwProfile ? hwProfile.system : null

    readonly property real ramTotalGB: mem ? Math.round(mem.totalKb / 1048576 * 10) / 10 : 0
    readonly property real ramUsedGB: mem ? Math.round((mem.totalKb - mem.availableKb) / 1048576 * 10) / 10 : 0
    readonly property real ramPct: (mem && mem.totalKb > 0) ? (mem.totalKb - mem.availableKb) / mem.totalKb : 0
    readonly property real swapTotalGB: mem ? Math.round(mem.swapTotalKb / 1048576 * 10) / 10 : 0

    readonly property var systemFlags: {
        if (!sys) return []
        var f = []
        if (sys.uefi) f.push("UEFI")
        if (sys.tpm) f.push("TPM")
        if (sys.isVm) f.push("VM")
        if (sys.kernel) f.push(sys.kernel)
        return f
    }

    function cap(s) { return s ? (s.charAt(0).toUpperCase() + s.slice(1)) : "—" }

    function loadProfile() {
        var raw = null
        try {
            if (typeof HardwareDBus !== "undefined" && HardwareDBus) {
                var reply = HardwareDBus.call("GetProfile")
                if (reply && reply.arguments && reply.arguments.length > 0) {
                    var s = String(reply.arguments[0])
                    if (s.charAt(0) === "{") raw = s
                }
            }
        } catch (e) { raw = null }

        if (raw) {
            try { hwProfile = JSON.parse(raw); profileLoaded = true } catch (e2) {}
            return
        }

        var xhr = new XMLHttpRequest()
        xhr.open("GET", "file:///var/run/synthex-hw-profile.json", true)
        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                var t = xhr.responseText
                if (t && String(t).charAt(0) === "{") {
                    try { hwProfile = JSON.parse(t); profileLoaded = true } catch (e3) {}
                }
            }
        }
        try { xhr.send() } catch (e4) {}
    }

    Component.onCompleted: loadProfile()

    ColumnLayout {
        anchors.fill: parent
        spacing: 24

        Text {
            text: "System Overview"
            font.pixelSize: 24
            font.bold: true
            color: textColor
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Rectangle {
                Layout.preferredWidth: 260
                Layout.preferredHeight: 140
                color: surfaceColor
                radius: 12
                border.color: "#2A2A3E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "\u{1F5A5}"; font.pixelSize: 20 }
                        Item { Layout.fillWidth: true }
                        Text { text: "CPU"; font.pixelSize: 12; color: mutedText; font.capitalization: Font.AllUppercase }
                    }

                    Text {
                        text: cpu ? (cpu.cores + " cores") : "Detecting…"
                        font.pixelSize: 28
                        font.bold: true
                        color: textColor
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 6
                        radius: 3
                        color: "#2A2A3E"
                        Rectangle {
                            width: parent.width * (cpu ? Math.min(cpu.threads / 32, 1.0) : 0)
                            height: 6
                            radius: 3
                            color: accentColor
                            Behavior on width { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
                        }
                    }

                    Text {
                        text: cpu ? (cpu.model + " · " + cpu.threads + " threads · " + cpu.maxGhz.toFixed(2) + " GHz") : "Awaiting hardware profile"
                        font.pixelSize: 11
                        color: mutedText
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 260
                Layout.preferredHeight: 140
                color: surfaceColor
                radius: 12
                border.color: "#2A2A3E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "\u{1F5B9}"; font.pixelSize: 20 }
                        Item { Layout.fillWidth: true }
                        Text { text: "GPU"; font.pixelSize: 12; color: mutedText; font.capitalization: Font.AllUppercase }
                    }

                    Text {
                        text: gpu ? gpu.model : "Detecting…"
                        font.pixelSize: 18
                        font.bold: true
                        color: textColor
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Text {
                        text: gpu ? (cap(gpu.vendor) + " · PCI " + gpu.vendorId + ":" + gpu.deviceId) : "Awaiting hardware profile"
                        font.pixelSize: 11
                        color: mutedText
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle { width: 8; height: 8; radius: 4; color: profileLoaded ? okColor : mutedText }
                        Text {
                            text: profileLoaded ? "Driver ready" : "Detecting"
                            font.pixelSize: 11
                            color: profileLoaded ? okColor : mutedText
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 260
                Layout.preferredHeight: 140
                color: surfaceColor
                radius: 12
                border.color: "#2A2A3E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "\u{1F4BE}"; font.pixelSize: 20 }
                        Item { Layout.fillWidth: true }
                        Text { text: "RAM"; font.pixelSize: 12; color: mutedText; font.capitalization: Font.AllUppercase }
                    }

                    Text {
                        text: mem ? (ramUsedGB + " / " + Math.round(ramTotalGB) + " GB") : "Detecting…"
                        font.pixelSize: 26
                        font.bold: true
                        color: textColor
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 6
                        radius: 3
                        color: "#2A2A3E"
                        Rectangle {
                            width: parent.width * ramPct
                            height: 6
                            radius: 3
                            color: ramPct > 0.85 ? dangerColor : (ramPct > 0.6 ? warnColor : okColor)
                            Behavior on width { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
                        }
                    }

                    Text {
                        text: mem ? (swapTotalGB + " GB swap · " + Math.round(ramPct * 100) + "% used") : "Awaiting hardware profile"
                        font.pixelSize: 11
                        color: mutedText
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 260
                Layout.preferredHeight: 140
                color: surfaceColor
                radius: 12
                border.color: "#2A2A3E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "\u{1F5A4}"; font.pixelSize: 20 }
                        Item { Layout.fillWidth: true }
                        Text { text: "SYSTEM"; font.pixelSize: 12; color: mutedText; font.capitalization: Font.AllUppercase }
                    }

                    Text {
                        text: sys ? cap(sys.chassis) : "Detecting…"
                        font.pixelSize: 22
                        font.bold: true
                        color: textColor
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Text {
                        text: sys ? (sys.product + " · " + sys.manufacturer) : "Awaiting hardware profile"
                        font.pixelSize: 11
                        color: mutedText
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: systemFlags
                            delegate: Rectangle {
                                height: 18
                                radius: 9
                                color: Qt.rgba(0.608, 0.741, 0.361, 0.16)
                                border.color: Qt.rgba(0.608, 0.741, 0.361, 0.5)
                                border.width: 1
                                implicitWidth: flagText.implicitWidth + 16
                                Text {
                                    id: flagText
                                    anchors.centerIn: parent
                                    text: modelData
                                    font.pixelSize: 10
                                    color: accentColor
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Repeater {
                model: [
                    { label: "Gaming Mode", icon: "\u{1F3AE}", desc: "Max GPU perf" },
                    { label: "Developer Mode", icon: "\u{1F4D1}", desc: "Dev tooling ready" },
                    { label: "Battery Saver", icon: "\u{1F50B}", desc: "Power efficient" },
                    { label: "Balanced", icon: "\u{2696}", desc: "Default profile" }
                ]

                delegate: Rectangle {
                    id: modeTile
                    property bool active: index === activeMode
                    property bool hovered: false
                    Layout.preferredWidth: 210
                    Layout.preferredHeight: 80
                    color: active ? Qt.rgba(0.608, 0.741, 0.361, 0.08) : (hovered ? "#24243A" : surfaceColor)
                    radius: 10
                    border.color: active ? accentColor : "#2A2A3E"
                    border.width: active ? 2 : 1
                    Behavior on color { ColorAnimation { duration: 160 } }
                    Behavior on border.color { ColorAnimation { duration: 160 } }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: modeTile.hovered = true
                        onExited: modeTile.hovered = false
                        onClicked: activeMode = index
                    }

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 12
                        Text { text: modelData.icon; font.pixelSize: 24 }
                        ColumnLayout {
                            spacing: 2
                            Text { text: modelData.label; font.pixelSize: 14; font.bold: true; color: textColor }
                            Text { text: modelData.desc; font.pixelSize: 11; color: mutedText }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: "Quick Actions"
                font.pixelSize: 16
                font.bold: true
                color: textColor
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Repeater {
                    model: [
                        { text: "Rollback System", icon: "\u{1F519}", color: dangerColor },
                        { text: "Create Snapshot", icon: "\u{1F4BE}", color: "#1E88E5" },
                        { text: "Update All", icon: "\u{1F504}", color: okColor },
                        { text: "Clean System", icon: "\u{1F9F9}", color: warnColor }
                    ]

                    delegate: Button {
                        id: actionBtn
                        Layout.preferredWidth: 210
                        Layout.preferredHeight: 48
                        flat: true
                        hoverEnabled: true

                        background: Rectangle {
                            color: modelData.color
                            radius: 8
                            opacity: actionBtn.hovered ? 1.0 : 0.88
                            Behavior on opacity { NumberAnimation { duration: 120 } }
                        }

                        contentItem: RowLayout {
                            spacing: 8
                            Text { text: modelData.icon; font.pixelSize: 16 }
                            Text { text: modelData.text; font.pixelSize: 13; font.bold: true; color: "#FFFFFF" }
                        }

                        onClicked: console.log("Action:", modelData.text)
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
