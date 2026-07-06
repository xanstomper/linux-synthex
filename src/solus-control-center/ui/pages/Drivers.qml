import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color okColor: "#43A047"; readonly property color warnColor: "#FB8C00"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Drivers"; font.pixelSize: 24; font.bold: true; color: textColor }
        GridLayout {
            Layout.fillWidth: true; columns: 3; rowSpacing: 12; columnSpacing: 14
            StatCard { label: "NVIDIA"; value: "DKMS"; icon: "🎮"; iconColor: warnColor }
            StatCard { label: "AMD"; value: "RADV"; icon: "🔴"; iconColor: okColor }
            StatCard { label: "Intel"; value: "ANV"; icon: "🔵"; iconColor: okColor }
        }
        Card {
            Layout.fillWidth: true; title: "Graphics Stack"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Mesa (AMD/Intel) — auto-configured"; color: textColor; font.pixelSize: 14 }
            Text { text: "NVIDIA — DKMS modules, Secure Boot signed"; color: textColor; font.pixelSize: 14 }
            Text { text: "Vulkan: RADV + ANV + NVIDIA"; color: mutedText; font.pixelSize: 12 }
            Text { text: "VAAPI/NVDEC/NVENC: hardware accel enabled"; color: mutedText; font.pixelSize: 12 }
        }
        Card {
            Layout.fillWidth: true; title: "Firmware"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "linux-firmware: latest"; color: textColor; font.pixelSize: 14 }
            Text { text: "fwupd: firmware updater active"; color: textColor; font.pixelSize: 14 }
        }
    }
}
