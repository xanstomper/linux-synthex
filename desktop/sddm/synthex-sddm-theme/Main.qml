import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: 1920; height: 1080
    color: "#0B0F1A"

    // ── Color tokens ──────────────────────────────────────────────────────────
    readonly property color bgDeep:    "#0B0F1A"
    readonly property color bgMid:     "#1A1A2E"
    readonly property color bgCard:    "#16213E"
    readonly property color border:    "#2A2A4E"
    readonly property color accentAmb: "#FFB300"
    readonly property color accentLim: "#9BBD5C"
    readonly property color textPri:   "#FFFFFF"
    readonly property color textSec:   "#8899AA"
    readonly property color errorClr:  "#FF4444"

    // ── Data models ───────────────────────────────────────────────────────────
    property var userModel:    userModel
    property var sessionModel: sessionModel
    property string selectedUser:    userList.currentIndex >= 0 && userModel.count > 0
                                     ? userModel.data(userModel.index(userList.currentIndex, 0), Qt.DisplayRole) : ""

    // ── Background gradient ───────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#0B0F1A" }
            GradientStop { position: 1.0; color: "#0D1327" }
        }
    }

    // Subtle radial glow behind login card
    Rectangle {
        anchors.centerIn: parent
        width: 640; height: 560
        radius: width / 2
        color: "transparent"
        layer.enabled: true
        layer.effect: null
        Rectangle {
            anchors.centerIn: parent
            width: 640; height: 480
            radius: 320
            color: "#FFB300"
            opacity: 0.04
        }
    }

    // ── Clock & date (top-left) ───────────────────────────────────────────────
    Column {
        anchors { top: parent.top; left: parent.left; margins: 40 }
        spacing: 4
        Text {
            id: clockLabel
            font { pixelSize: 56; weight: Font.Light; family: "Noto Sans" }
            color: root.textPri
            opacity: 0.9
            Timer {
                interval: 1000; running: true; repeat: true; triggeredOnStart: true
                onTriggered: clockLabel.text = Qt.formatTime(new Date(), "hh:mm")
            }
        }
        Text {
            font { pixelSize: 15; family: "Noto Sans" }
            color: root.textSec
            Timer {
                interval: 60000; running: true; repeat: true; triggeredOnStart: true
                onTriggered: parent.text = Qt.formatDate(new Date(), "dddd, MMMM d")
            }
        }
    }

    // ── Session selector (top-right) ──────────────────────────────────────────
    Row {
        anchors { top: parent.top; right: parent.right; margins: 40 }
        spacing: 8
        Text { anchors.verticalCenter: parent.verticalCenter; text: "Session:"; color: root.textSec; font.pixelSize: 13 }
        ComboBox {
            id: sessionCombo
            width: 180; height: 36
            model: sessionModel
            textRole: "name"
            currentIndex: sessionModel.lastIndex
            background: Rectangle {
                color: root.bgCard; radius: 6; border.color: root.border; border.width: 1
            }
            contentItem: Text {
                leftPadding: 10; text: sessionCombo.displayText
                color: root.textPri; font.pixelSize: 13; verticalAlignment: Text.AlignVCenter
            }
            delegate: ItemDelegate {
                width: sessionCombo.width
                contentItem: Text { text: modelData; color: root.textPri; font.pixelSize: 13 }
                background: Rectangle { color: sessionCombo.highlightedIndex === index ? root.bgMid : root.bgCard }
            }
            popup: Popup {
                y: sessionCombo.height; width: sessionCombo.width
                padding: 0
                background: Rectangle { color: root.bgCard; radius: 6; border.color: root.border; border.width: 1 }
                contentItem: ListView {
                    implicitHeight: contentHeight
                    model: sessionCombo.delegateModel
                    clip: true
                }
            }
        }
    }

    // ── Central login card ────────────────────────────────────────────────────
    Rectangle {
        id: loginCard
        anchors.centerIn: parent
        width: 420; height: loginCardCol.implicitHeight + 60
        radius: 18
        color: root.bgMid
        border.color: root.border; border.width: 1

        // Subtle top-edge glow
        Rectangle {
            anchors { top: parent.top; horizontalCenter: parent.horizontalCenter }
            width: 260; height: 2; radius: 1
            color: root.accentAmb; opacity: 0.6
        }

        ColumnLayout {
            id: loginCardCol
            anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: 36; leftMargin: 36; rightMargin: 36 }
            spacing: 0

            // ── Logo + branding ───────────────────────────────────────────────
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 6
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 64; height: 64; radius: 16
                    gradient: Gradient {
                        orientation: Gradient.Vertical
                        GradientStop { position: 0.0; color: "#FFB300" }
                        GradientStop { position: 1.0; color: "#FF8C00" }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "☀"; font.pixelSize: 36
                        color: "#0B0F1A"
                    }
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "SynthOS"; font { pixelSize: 28; weight: Font.Bold; family: "Noto Sans" }
                    color: root.textPri
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Illuminate Your Desktop"
                    font.pixelSize: 12; color: root.accentAmb; opacity: 0.85
                }
            }

            Item { Layout.preferredHeight: 32 }

            // ── User selector ─────────────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                spacing: 4
                Text { text: "User"; font.pixelSize: 12; color: root.textSec }
                ComboBox {
                    id: userList
                    width: parent.width; height: 46
                    model: userModel
                    textRole: "name"
                    background: Rectangle { color: root.bgCard; radius: 8; border.color: root.border; border.width: 1 }
                    contentItem: Text {
                        leftPadding: 14; text: userList.displayText
                        color: root.textPri; font.pixelSize: 15; verticalAlignment: Text.AlignVCenter
                    }
                    delegate: ItemDelegate {
                        width: userList.width
                        contentItem: Text { leftPadding: 14; text: modelData; color: root.textPri; font.pixelSize: 14 }
                        background: Rectangle { color: userList.highlightedIndex === index ? root.bgMid : root.bgCard }
                    }
                    popup: Popup {
                        y: userList.height + 2; width: userList.width; padding: 0
                        background: Rectangle { color: root.bgCard; radius: 8; border.color: root.border; border.width: 1 }
                        contentItem: ListView {
                            implicitHeight: contentHeight; model: userList.delegateModel; clip: true
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 16 }

            // ── Password field ────────────────────────────────────────────────
            Column {
                Layout.fillWidth: true
                spacing: 4
                Text { text: "Password"; font.pixelSize: 12; color: root.textSec }
                Rectangle {
                    width: parent.width; height: 46
                    color: root.bgCard; radius: 8
                    border.color: passField.activeFocus ? root.accentAmb : root.border; border.width: 1
                    Behavior on border.color { ColorAnimation { duration: 150 } }
                    TextInput {
                        id: passField
                        anchors { fill: parent; leftMargin: 14; rightMargin: 44; verticalCenter: parent.verticalCenter }
                        height: parent.height
                        echoMode: TextInput.Password
                        passwordCharacter: "●"
                        font { pixelSize: 18; family: "Noto Sans" }
                        color: root.textPri
                        verticalAlignment: TextInput.AlignVCenter
                        KeyNavigation.tab: loginBtn
                        Keys.onReturnPressed: doLogin()
                        Keys.onEnterPressed: doLogin()
                    }
                    // Show/hide password toggle
                    Text {
                        anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                        text: passField.echoMode === TextInput.Password ? "👁" : "🙈"
                        font.pixelSize: 18; color: root.textSec
                        MouseArea {
                            anchors.fill: parent
                            onClicked: passField.echoMode = passField.echoMode === TextInput.Password
                                       ? TextInput.Normal : TextInput.Password
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 6 }

            // ── Error message ─────────────────────────────────────────────────
            Text {
                id: errorLabel
                Layout.fillWidth: true
                visible: text !== ""; wrapMode: Text.WordWrap
                font.pixelSize: 12; color: root.errorClr
                horizontalAlignment: Text.AlignHCenter
            }

            Item { Layout.preferredHeight: 18 }

            // ── Login button ──────────────────────────────────────────────────
            Rectangle {
                id: loginBtn
                Layout.fillWidth: true; height: 48; radius: 10
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#FFB300" }
                    GradientStop { position: 1.0; color: "#FF8C00" }
                }
                Text {
                    anchors.centerIn: parent
                    text: "Sign In"; font { pixelSize: 16; weight: Font.Bold }; color: "#0B0F1A"
                }
                scale: loginMa.pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: 100 } }
                opacity: loginMa.containsMouse ? 0.9 : 1.0
                MouseArea {
                    id: loginMa; anchors.fill: parent; hoverEnabled: true
                    onClicked: doLogin()
                }
            }

            Item { Layout.preferredHeight: 24 }

            // ── Power buttons ─────────────────────────────────────────────────
            Row {
                Layout.alignment: Qt.AlignHCenter
                spacing: 28
                Repeater {
                    model: [
                        { icon: "⏻", label: "Shut Down", action: "shutdown" },
                        { icon: "↺", label: "Restart",   action: "reboot"   },
                        { icon: "⏾", label: "Suspend",   action: "suspend"  }
                    ]
                    delegate: Column {
                        spacing: 4
                        Rectangle {
                            width: 40; height: 40; radius: 8; color: root.bgCard
                            border.color: powMa.containsMouse ? root.accentAmb : root.border; border.width: 1
                            Behavior on border.color { ColorAnimation { duration: 150 } }
                            Text {
                                anchors.centerIn: parent
                                text: modelData.icon; font.pixelSize: 18; color: root.textPri
                            }
                            MouseArea {
                                id: powMa; anchors.fill: parent; hoverEnabled: true
                                onClicked: {
                                    if (modelData.action === "shutdown") sddm.powerOff()
                                    else if (modelData.action === "reboot") sddm.reboot()
                                    else sddm.suspend()
                                }
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData.label; font.pixelSize: 10; color: root.textSec
                        }
                    }
                }
            }
            Item { Layout.preferredHeight: 6 }
        }
    }

    // ── Keyboard layout (bottom-center) ───────────────────────────────────────
    Row {
        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 24 }
        spacing: 8
        Text { anchors.verticalCenter: parent.verticalCenter; text: "⌨"; font.pixelSize: 16; color: root.textSec }
        ComboBox {
            id: kbdCombo; width: 120; height: 32
            model: keyboard.layouts; textRole: "shortName"
            currentIndex: keyboard.currentLayout
            onCurrentIndexChanged: keyboard.currentLayout = currentIndex
            background: Rectangle { color: root.bgCard; radius: 6; border.color: root.border; border.width: 1 }
            contentItem: Text {
                leftPadding: 8; text: kbdCombo.displayText
                color: root.textPri; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // ── Version watermark (bottom-right) ──────────────────────────────────────
    Text {
        anchors { bottom: parent.bottom; right: parent.right; margins: 20 }
        text: "SynthOS 2026.10 · " + sddm.hostName
        font.pixelSize: 11; color: root.textSec; opacity: 0.5
    }

    // ── Auth logic ────────────────────────────────────────────────────────────
    function doLogin() {
        errorLabel.text = ""
        if (passField.text === "") { errorLabel.text = "Please enter your password."; return }
        sddm.login(root.selectedUser, passField.text, sessionCombo.currentIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            errorLabel.text = "Incorrect password. Please try again."
            passField.text = ""
            passField.forceActiveFocus()
        }
    }

    Component.onCompleted: passField.forceActiveFocus()
}
