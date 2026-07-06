import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: "transparent"; anchors.fill: parent
    readonly property color accentColor: "#9BBD5C"; readonly property color textColor: "#FFFFFF"; readonly property color okColor: "#43A047"; readonly property color warnColor: "#FB8C00"; readonly property color dangerColor: "#E53935"

    ColumnLayout { anchors.fill: parent; spacing: 20
        Text { text: "Security"; font.pixelSize: 24; font.bold: true; color: textColor }
        GridLayout {
            Layout.fillWidth: true; columns: 3; rowSpacing: 12; columnSpacing: 14
            StatCard { label: "Firewall"; value: "Active"; icon: "🔥"; iconColor: okColor }
            StatCard { label: "SELinux"; value: "Enforcing"; icon: "🔒"; iconColor: okColor }
            StatCard { label: "Secure Boot"; value: "Enabled"; icon: "🔐"; iconColor: warnColor }
        }
        Card {
            Layout.fillWidth: true; title: "Security Features"
            ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 8 }
            Text { text: "Flatpak sandboxing: Flathub apps are sandboxed"; color: textColor; font.pixelSize: 14 }
            Text { text: "AppArmor: enabled for key applications"; color: textColor; font.pixelSize: 14 }
            Text { text: "Snapshot rollback: Timeshift + Snapper active"; color: textColor; font.pixelSize: 14 }
        }
    }
}
