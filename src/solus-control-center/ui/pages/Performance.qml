import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Performance"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "Power Profile"
            RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 12 }
            Repeater {
                model: [
                    { label: "Balanced", icon: "⚖", mode: "balanced" },
                    { label: "Performance", icon: "🚀", mode: "performance" },
                    { label: "Power Saver", icon: "🔋", mode: "powersave" }
                ]
                delegate: ModeToggle {
                    label: modelData.label; icon: modelData.icon; active: false
                    onClicked: console.log("Set mode:", modelData.mode)
                }
            }
        }
        Card {
            Layout.fillWidth: true; title: "Governor"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Current: schedutil (BORE/EEVDF)"; color: textColor; font.pixelSize: 14 }
            Text { text: "CPU frequency driver: acpi-cpufreq / intel_pstate / amd-pstate"; color: mutedText; font.pixelSize: 12 }
        }
        Card {
            Layout.fillWidth: true; title: "Memory Tuning"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "ZRAM: enabled (zstd compression)"; color: textColor; font.pixelSize: 14 }
            Text { text: "Swappiness: 10 (desktop optimized)"; color: textColor; font.pixelSize: 14 }
            Text { text: "THP: madvise (reduces latency spikes)"; color: mutedText; font.pixelSize: 12 }
        }
    }
}
