// ─────────────────────────────────────────────────────────────────────────────
//  SynthOS SDDM Theme — "Nova"
//  Floating glass login card on a calm charcoal gradient with periwinkle
//  accents. Design tokens: branding/theme/tokens/nova.json
// ─────────────────────────────────────────────────────────────────────────────
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

Item {
    id: root
    width: 1920; height: 1080

    // ── Design tokens (Nova) ─────────────────────────────────────────────────
    readonly property color bgDeep:    "#0C1016"   // deep charcoal
    readonly property color bgMid:     "#10151B"   // primary background
    readonly property color bgHigh:    "#1B222B"   // lifted charcoal
    readonly property color surface:   "#171D24"   // secondary surface
    readonly property color elevated:  "#1E242F"   // elevated surface
    readonly property color hairline:  "#FFFFFF"   // used at low alpha
    readonly property color accent:    "#6C88A8"   // periwinkle
    readonly property color accentHi:  "#82A0BE"
    readonly property color lavender:  "#ABA2E4"   // secondary accent
    readonly property color accentInk: "#0C1116"   // text on accent
    readonly property color textPri:   "#DDE3EB"
    readonly property color textSec:   "#9AA1AB"
    readonly property color textMut:   "#67707D"
    readonly property color danger:    "#D97C82"
    readonly property color ok:        "#7FBF8A"

    readonly property int   radiusLg: 18
    readonly property int   radiusMd: 14
    readonly property int   radiusSm: 10
    readonly property real  glassAlpha: 0.72

    // ── Data ────────────────────────────────────────────────────────────────
    property string selectedUser: userList.currentIndex >= 0 && userModel.count > 0
                                  ? userModel.data(userModel.index(userList.currentIndex, 0), Qt.DisplayRole)
                                  : (userModel.count > 0
                                     ? userModel.data(userModel.index(0, 0), Qt.DisplayRole)
                                     : "")

    // ─────────────────────────────────────────────────────────────────────────
    //  Backdrop — calm charcoal gradient with two soft periwinkle blooms
    // ─────────────────────────────────────────────────────────────────────────
    Item {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: root.bgDeep }
                GradientStop { position: 0.55; color: root.bgMid }
                GradientStop { position: 1.0; color: root.bgHigh }
            }
        }

        // Soft periwinkle bloom, upper-left
        Rectangle {
            x: parent.width * 0.24 - width / 2
            y: parent.height * 0.26 - height / 2
            width: 720; height: 720; radius: 360
            color: root.accent; opacity: 0.07
            Rectangle { anchors.centerIn: parent; width: 440; height: 440; radius: 220
                color: root.accent; opacity: 0.08 }
        }

        // Lavender bloom, lower-right
        Rectangle {
            x: parent.width * 0.78 - width / 2
            y: parent.height * 0.74 - height / 2
            width: 640; height: 640; radius: 320
            color: root.lavender; opacity: 0.05
            Rectangle { anchors.centerIn: parent; width: 380; height: 380; radius: 190
                color: root.lavender; opacity: 0.07 }
        }

        // Vignette
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: Qt.rgba(0,0,0,0.30) }
                GradientStop { position: 0.5; color: Qt.rgba(0,0,0,0.0)  }
                GradientStop { position: 1.0; color: Qt.rgba(0,0,0,0.45) }
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  Clock — top-left
    // ─────────────────────────────────────────────────────────────────────────
    Column {
        anchors { top: parent.top; left: parent.left; topMargin: 56; leftMargin: 64 }
        spacing: 2
        opacity: 0
        Text {
            id: clockLabel
            font { pixelSize: 68; weight: Font.ExtraLight; family: "Inter" }
            color: root.textPri
            renderType: Text.NativeRendering
            Timer { interval: 1000; running: true; repeat: true; triggeredOnStart: true;
                onTriggered: clockLabel.text = Qt.formatTime(new Date(), "hh:mm") }
        }
        Text {
            id: dateLabel
            font { pixelSize: 15; weight: Font.Light; family: "Inter" }
            color: root.textSec
            Timer { interval: 30000; running: true; repeat: true; triggeredOnStart: true;
                onTriggered: dateLabel.text = Qt.formatDate(new Date(), "dddd · MMMM d") }
        }
        Behavior on opacity { NumberAnimation { duration: 900; easing.type: Easing.OutCubic } }
        Component.onCompleted: opacity = 1
    }

    // Session selector — top-right
    Row {
        id: sessionRow
        anchors { top: parent.top; right: parent.right; topMargin: 60; rightMargin: 64 }
        spacing: 10
        opacity: 0
        Behavior on opacity { NumberAnimation { duration: 900; easing.type: Easing.OutCubic } }
        Component.onCompleted: opacity = 1

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "Session"; color: root.textMut; font { pixelSize: 12; family: "Inter" }
        }
        ComboBox {
            id: sessionCombo
            width: 200; height: 38
            model: sessionModel; textRole: "name"
            currentIndex: sessionModel.lastIndex
            background: Rectangle { color: Qt.rgba(0.11,0.12,0.15,0.65); radius: root.radiusSm;
                border.color: Qt.rgba(1,1,1,0.08); border.width: 1 }
            contentItem: Text { leftPadding: 12; text: sessionCombo.displayText;
                color: root.textPri; font { pixelSize: 13; family: "Inter" }; verticalAlignment: Text.AlignVCenter }
            delegate: ItemDelegate { width: sessionCombo.width
                contentItem: Text { leftPadding: 12; text: modelData; color: root.textPri; font.pixelSize: 13 }
                background: Rectangle { color: sessionCombo.highlightedIndex === index ? Qt.rgba(0.42,0.53,0.66,0.16) : "transparent" } }
            popup: Popup { y: sessionCombo.height + 6; width: sessionCombo.width; padding: 0
                background: Rectangle { color: root.elevated; radius: root.radiusSm; border.color: Qt.rgba(1,1,1,0.10); border.width: 1 }
                contentItem: ListView { implicitHeight: contentHeight; model: sessionCombo.delegateModel; clip: true } }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  Floating glass login card
    // ─────────────────────────────────────────────────────────────────────────
    Item {
        id: cardHost
        anchors.centerIn: parent
        width: 440
        height: loginCard.height

        // soft drop shadow
        Rectangle { anchors.centerIn: loginCard; anchors.fill: loginCard
            color: "#000"; radius: root.radiusLg; opacity: 0.45; scale: 1.04; z: -1 }

        Rectangle {
            id: loginCard
            anchors.fill: parent
            radius: root.radiusLg
            color: Qt.rgba(0.090, 0.114, 0.141, root.glassAlpha)   // #171D24 @ alpha
            border.color: Qt.rgba(1,1,1,0.10); border.width: 1

            // top sheen
            Rectangle { anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: 1 }
                height: 1; color: Qt.rgba(1,1,1,0.14) }
            // periwinkle accent underline
            Rectangle { anchors { top: parent.top; horizontalCenter: parent.horizontalCenter; topMargin: -1 }
                width: 120; height: 2; radius: 1; color: root.accent; opacity: 0.9 }

            // entrance: slide up + fade
            opacity: 0; y: 28
            Behavior on opacity { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: 800; easing.type: Easing.OutQuint } }

            ColumnLayout {
                anchors { fill: parent; topMargin: 40; leftMargin: 40; rightMargin: 40; bottomMargin: 32 }
                spacing: 0

                // ── Mark ──
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 76; Layout.preferredHeight: 76
                    Rectangle { anchors.centerIn: parent; width: 76; height: 76; radius: 38
                        color: root.accent; opacity: 0.10 }
                    Rectangle { anchors.centerIn: parent; width: 58; height: 58; radius: 29
                        color: root.accent; opacity: 0.14 }
                    Rectangle {
                        id: mark
                        anchors.centerIn: parent; width: 44; height: 44; radius: 22
                        gradient: Gradient { orientation: Gradient.Vertical
                            GradientStop { position: 0.0; color: root.accentHi }
                            GradientStop { position: 0.6; color: root.accent }
                            GradientStop { position: 1.0; color: root.lavender } }
                        // gentle pulse
                        SequentialAnimation on scale { loops: Animation.Infinite
                            NumberAnimation { to: 1.05; duration: 3200; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0;  duration: 3200; easing.type: Easing.InOutSine } }
                        Text { anchors.centerIn: parent; text: "◆"
                            font { pixelSize: 22; weight: Font.Bold }
                            color: root.accentInk }
                    }
                }

                Item { Layout.preferredHeight: 18 }

                Text { Layout.alignment: Qt.AlignHCenter
                    text: "SynthOS"
                    font { pixelSize: 30; weight: Font.DemiBold; family: "Inter"; letterSpacing: 1 }
                    color: root.textPri }
                Text { Layout.alignment: Qt.AlignHCenter
                    text: "A CALM, PRECISE DESKTOP"
                    font { pixelSize: 10; family: "Inter"; letterSpacing: 3 }
                    color: root.accent; opacity: 0.9 }

                Item { Layout.preferredHeight: 30 }

                // ── User ──
                Text { text: "USER"; font { pixelSize: 10; family: "Inter"; weight: Font.Bold; letterSpacing: 2 }
                    color: root.textMut; Layout.fillWidth: true }
                Item { Layout.preferredHeight: 6 }
                ComboBox {
                    id: userList
                    Layout.fillWidth: true; Layout.preferredHeight: 48
                    model: userModel; textRole: "name"
                    background: Rectangle {
                        radius: root.radiusMd
                        color: Qt.rgba(0.06,0.07,0.09,0.65)
                        border.color: userList.activeFocus ? Qt.rgba(0.42,0.53,0.66,0.6) : Qt.rgba(1,1,1,0.08)
                        border.width: 1
                        Behavior on border.color { ColorAnimation { duration: 180 } } }
                    contentItem: Text { leftPadding: 16; text: userList.displayText || "Select user"
                        color: userList.displayText ? root.textPri : root.textMut
                        font { pixelSize: 15; family: "Inter" }; verticalAlignment: Text.AlignVCenter }
                    delegate: ItemDelegate { width: userList.width
                        contentItem: Text { leftPadding: 16; text: modelData; color: root.textPri; font.pixelSize: 14 }
                        background: Rectangle { color: userList.highlightedIndex === index ? Qt.rgba(0.42,0.53,0.66,0.16) : "transparent" } }
                    popup: Popup { y: userList.height + 6; width: userList.width; padding: 0
                        background: Rectangle { color: root.elevated; radius: root.radiusMd; border.color: Qt.rgba(1,1,1,0.10); border.width: 1 }
                        contentItem: ListView { implicitHeight: contentHeight; model: userList.delegateModel; clip: true } }
                }

                Item { Layout.preferredHeight: 18 }

                // ── Password ──
                Text { text: "PASSWORD"; font { pixelSize: 10; family: "Inter"; weight: Font.Bold; letterSpacing: 2 }
                    color: root.textMut; Layout.fillWidth: true }
                Item { Layout.preferredHeight: 6 }
                Rectangle {
                    id: passBox
                    Layout.fillWidth: true; Layout.preferredHeight: 48; radius: root.radiusMd
                    color: Qt.rgba(0.06,0.07,0.09,0.65)
                    border.color: passField.activeFocus ? Qt.rgba(0.42,0.53,0.66,0.7)
                                : (errorLabel.text !== "" ? Qt.rgba(0.85,0.49,0.51,0.7) : Qt.rgba(1,1,1,0.08))
                    border.width: 1
                    Behavior on border.color { ColorAnimation { duration: 180 } }

                    TextInput {
                        id: passField
                        anchors { fill: parent; leftMargin: 16; rightMargin: 52 }
                        echoMode: TextInput.Password; passwordMaskDelay: 600; passwordCharacter: "•"
                        font { pixelSize: 16; family: "Inter" }
                        color: root.textPri; verticalAlignment: TextInput.AlignVCenter
                        clip: true
                        KeyNavigation.tab: loginBtn
                        Keys.onReturnPressed: doLogin()
                        Keys.onEnterPressed: doLogin()
                        selectedTextColor: root.accentInk; selectionColor: root.accent
                    }
                    Text {
                        anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                        text: "Enter password"; color: root.textMut; font { pixelSize: 15; family: "Inter" }
                        visible: passField.text === ""
                        MouseArea { anchors.fill: parent; onClicked: passField.forceActiveFocus() }
                    }
                    // reveal toggle
                    Text {
                        anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                        text: passField.echoMode === TextInput.Password ? "◉" : "○"
                        font.pixelSize: 16
                        color: passField.echoMode === TextInput.Password ? root.textMut : root.accent
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            onClicked: passField.echoMode = (passField.echoMode === TextInput.Password) ? TextInput.Normal : TextInput.Password }
                    }
                }

                // ── Error ──
                Text {
                    id: errorLabel
                    Layout.fillWidth: true; Layout.topMargin: 10
                    visible: text !== ""; wrapMode: Text.WordWrap
                    font { pixelSize: 12; family: "Inter" }; color: root.danger
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                    onTextChanged: opacity = (text !== "") ? 1 : 0
                    SequentialAnimation on x {
                        running: errorLabel.text !== ""
                        NumberAnimation { from: 0; to: -6; duration: 50; easing.type: Easing.OutQuad }
                        NumberAnimation { from: -6; to: 6; duration: 50; easing.type: Easing.InOutQuad }
                        NumberAnimation { from: 6; to: -4; duration: 50; easing.type: Easing.InOutQuad }
                        NumberAnimation { from: -4; to: 0; duration: 60; easing.type: Easing.OutQuad }
                    }
                }

                Item { Layout.preferredHeight: errorLabel.visible ? 14 : 22 }

                // ── Sign in ──
                Rectangle {
                    id: loginBtn
                    Layout.fillWidth: true; Layout.preferredHeight: 50; radius: root.radiusMd
                    gradient: Gradient { orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: loginMa.containsMouse ? root.accentHi : root.accent }
                        GradientStop { position: 1.0; color: loginMa.containsMouse ? root.accent : root.lavender } }
                    scale: loginMa.pressed ? 0.975 : 1.0
                    Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
                    Row {
                        anchors.centerIn: parent; spacing: 10
                        Text { text: "→"; color: root.accentInk; font { pixelSize: 18; weight: Font.Bold }; visible: !loginMa.pressed }
                        Text { text: "Sign In"; color: root.accentInk; font { pixelSize: 16; weight: Font.Bold; family: "Inter" } }
                    }
                    MouseArea { id: loginMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: doLogin() }
                }

                Item { Layout.preferredHeight: 26 }

                // ── Power ──
                Row {
                    Layout.alignment: Qt.AlignHCenter; spacing: 16
                    Repeater {
                        model: [
                            { icon: "⏻", label: "Power",   action: "shutdown" },
                            { icon: "↻", label: "Restart",  action: "reboot"   },
                            { icon: "⏾", label: "Sleep",    action: "suspend"  }
                        ]
                        delegate: Column {
                            spacing: 6
                            Rectangle {
                                width: 42; height: 42; radius: root.radiusSm
                                color: Qt.rgba(0.06,0.07,0.09,0.65)
                                border.color: ma.containsMouse ? Qt.rgba(0.42,0.53,0.66,0.8) : Qt.rgba(1,1,1,0.08)
                                border.width: 1
                                Behavior on border.color { ColorAnimation { duration: 160 } }
                                scale: ma.pressed ? 0.92 : 1.0
                                Behavior on scale { NumberAnimation { duration: 90 } }
                                Text { anchors.centerIn: parent; text: modelData.icon;
                                    font.pixelSize: 17; color: ma.containsMouse ? root.accent : root.textSec }
                                MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (modelData.action === "shutdown") sddm.powerOff()
                                        else if (modelData.action === "reboot") sddm.reboot()
                                        else sddm.suspend()
                                    } }
                            }
                            Text { anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.label; font { pixelSize: 9; family: "Inter"; letterSpacing: 1 }
                                color: ma.containsMouse ? root.textSec : root.textMut }
                        }
                    }
                }
            }
        }

        Component.onCompleted: { loginCard.opacity = 1; loginCard.y = 0 }
    }

    // ─────────────────────────────────────────────────────────────────────────
    //  Bottom bar
    // ─────────────────────────────────────────────────────────────────────────
    Row {
        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 28 }
        spacing: 10; opacity: 0
        Behavior on opacity { NumberAnimation { duration: 900; easing.type: Easing.OutCubic } }
        Component.onCompleted: opacity = 1
        Text { anchors.verticalCenter: parent.verticalCenter; text: "A"; color: root.textMut; font { pixelSize: 12 } }
        ComboBox {
            id: kbdCombo; width: 130; height: 32
            model: keyboard.layouts; textRole: "shortName"
            currentIndex: keyboard.currentLayout
            onCurrentIndexChanged: keyboard.currentLayout = currentIndex
            background: Rectangle { color: Qt.rgba(0.06,0.07,0.09,0.65); radius: root.radiusSm; border.color: Qt.rgba(1,1,1,0.08); border.width: 1 }
            contentItem: Text { leftPadding: 10; text: kbdCombo.displayText; color: root.textPri; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
        }
    }

    Text {
        anchors { bottom: parent.bottom; right: parent.right; margins: 22 }
        text: "SynthOS 2026.10 · " + sddm.hostName
        font { pixelSize: 10; family: "Inter"; letterSpacing: 1 }
        color: root.textMut; opacity: 0
        Behavior on opacity { NumberAnimation { duration: 900 } }
        Component.onCompleted: opacity = 0.7
    }

    // ── Auth logic ────────────────────────────────────────────────────────────
    function doLogin() {
        errorLabel.text = ""
        if (root.selectedUser === "") { errorLabel.text = "No user selected."; return }
        if (passField.text === "")     { errorLabel.text = "Enter your password to continue."; passField.forceActiveFocus(); return }
        sddm.login(root.selectedUser, passField.text, sessionCombo.currentIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            errorLabel.text = "Incorrect password — try again."
            passField.text = ""
            passField.forceActiveFocus()
        }
    }

    Component.onCompleted: passField.forceActiveFocus()
}
