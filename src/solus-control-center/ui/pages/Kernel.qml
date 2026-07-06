import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color mutedText: "#8899AA"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Kernel"; font.pixelSize: 24; font.bold: true; color: textColor }
        Card {
            Layout.fillWidth: true; title: "Current Kernel"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Solus Kernel (BORE + EEVDF)"; color: textColor; font.pixelSize: 16; font.bold: true }
            Text { text: "Scheduler: BORE ( responsiveness ) + EEVDF"; color: mutedText; font.pixelSize: 12 }
            Text { text: "Tickless + PREEMPT full + CONFIG_NO_HZ_FULL"; color: mutedText; font.pixelSize: 12 }
        }
        Card {
            Layout.fillWidth: true; title: "Boot Profile Trend"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Boot times recorded at /var/lib/solus/boot-times.json"; color: mutedText; font.pixelSize: 12 }
            Text { text: "Target: < 10s on NVMe"; color: textColor; font.pixelSize: 14 }
        }
    }
}
