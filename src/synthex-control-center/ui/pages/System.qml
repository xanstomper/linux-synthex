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

    property var hwProfile: null
    property bool profileLoaded: false

    readonly property var sys: hwProfile ? hwProfile.system : null
    readonly property var cpu: hwProfile ? hwProfile.cpu : null
    readonly property var mem: hwProfile ? hwProfile.memory : null
    readonly property var gpu: hwProfile ? hwProfile.gpu : null

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
        }
    }

    Component.onCompleted: loadProfile()

    ColumnLayout {
        anchors.fill: parent
        spacing: 20

        Text { text: "System Information"; font.pixelSize: 24; font.bold: true; color: textColor }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            rowSpacing: 12; columnSpacing: 14
            StatCard { label: "Hostname"; value: sys ? sys.hostname : "synthex"; icon: "🖥" }
            StatCard { label: "Kernel"; value: sys ? sys.kernel : ""; icon: "🐧" }
            StatCard { label: "Arch"; value: sys ? sys.arch : "x86_64"; icon: "⚙" }
            StatCard { label: "Boot"; value: sys && sys.uefi ? "UEFI" : "Legacy"; icon: "💾" }
            StatCard { label: "TPM"; value: sys && sys.tpm ? "Enabled" : "Disabled"; icon: "🔐" }
            StatCard { label: "VM"; value: sys && sys.isVm ? "Yes" : "No"; icon: "📦" }
        }

        Text { text: "Processor"; font.pixelSize: 18; font.bold: true; color: textColor; Layout.topMargin: 8 }
        Card {
            Layout.fillWidth: true
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: cpu ? cpu.model : "Detecting..."; color: textColor; font.pixelSize: 14 }
            Text { text: cpu ? (cpu.vendor + " — " + cpu.cores + " cores") : ""; color: mutedText; font.pixelSize: 12 }
        }

        Text { text: "Memory"; font.pixelSize: 18; font.bold: true; color: textColor; Layout.topMargin: 8 }
        Card {
            Layout.fillWidth: true
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: mem ? (Math.round(mem.totalKb/1048576*10)/10 + " GB total") : ""; color: textColor; font.pixelSize: 14 }
            Text { text: mem ? (Math.round((mem.totalKb - mem.availableKb)/1048576*10)/10 + " GB used") : ""; color: mutedText; font.pixelSize: 12 }
        }

        Text { text: "Graphics"; font.pixelSize: 18; font.bold: true; color: textColor; Layout.topMargin: 8 }
        Card {
            Layout.fillWidth: true
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: gpu ? (gpu.vendor + " — " + gpu.model) : "Detecting..."; color: textColor; font.pixelSize: 14 }
            Text { text: gpu ? "Driver: " + gpu.driver : ""; color: mutedText; font.pixelSize: 12 }
        }
    }
}
