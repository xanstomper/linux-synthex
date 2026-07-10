// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

Kirigami.ScrollablePage {
    title: i18n("Controllers")

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        icon.name: "input-gamepad"
        text: i18n("Controllers & Input")
        explanation: i18n("Full controller management is available in the\nSynthOS Control Center → Controllers tab.")
        helpfulAction: Kirigami.Action {
            text: i18n("Open Control Center")
            icon.name: "preferences-system"
            onTriggered: Qt.openUrlExternally("synthex://control-center?page=controllers")
        }
    }
}
