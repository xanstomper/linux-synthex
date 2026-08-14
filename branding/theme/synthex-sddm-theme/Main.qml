import QtQuick 2.15
import SddmComponents 2.0 as Sddm

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#1a1a2e"

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#1a1a2e" }
            GradientStop { position: 0.5; color: "#16213e" }
            GradientStop { position: 1.0; color: "#232A34" }
        }
    }

    // Logo
    Image {
        id: logo
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: parent.height * 0.12
        source: "synthex-logo.png"
        width: 140
        height: 140
        fillMode: Image.PreserveAspectFit
    }

    // Welcome text
    Text {
        id: welcomeText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: logo.bottom
        anchors.topMargin: 16
        text: "SynthOS"
        color: "#e94560"
        font.pixelSize: 42
        font.bold: true
    }

    Text {
        id: subtitle
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: welcomeText.bottom
        anchors.topMargin: 6
        text: "The gaming-focused Linux distribution"
        color: "#a0a0b0"
        font.pixelSize: 18
    }

    // Clock
    Clock {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: subtitle.bottom
        anchors.topMargin: 30
        color: "#ffffff"
        font.pixelSize: 56
    }

    Text {
        id: dateText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: clock.bottom
        anchors.topMargin: 4
        color: "#a0a0b0"
        font.pixelSize: 20
        text: Qt.formatDateTime(new Date(), "dddd, MMMM d")
    }

    // ─── Login card ───────────────────────────────────────────────────
    Rectangle {
        id: loginCard
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: parent.height * 0.1
        width: 420
        height: 250
        color: "#16213e"
        radius: 16
        border.color: "#2a2a4e"
        border.width: 1

        // Avatar
        Rectangle {
            id: avatar
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 18
            width: 60
            height: 60
            radius: 30
            color: "#232A34"
            border.color: "#e94560"
            border.width: 2
            Text { anchors.centerIn: parent; text: "👤"; font.pixelSize: 28 }
        }

        // Username field
        LineEdit {
            id: username
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: avatar.bottom
            anchors.topMargin: 14
            width: 350
            height: 42
            color: "#ffffff"
            font.pixelSize: 16
            placeholderText: "Username"
            placeholderColor: "#606070"
            onAccepted: password.forceActiveFocus()
            Rectangle {
                anchors.fill: parent
                color: "#1a1a2e"
                radius: 8
                border.color: "#2a2a4e"
                z: -1
            }
        }

        // Password field
        LineEdit {
            id: password
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: username.bottom
            anchors.topMargin: 10
            width: 350
            height: 42
            color: "#ffffff"
            font.pixelSize: 16
            echoMode: TextInput.Password
            placeholderText: "Password"
            placeholderColor: "#606070"
            onAccepted: sddm.login(username.text, password.text, session.currentIndex)
            Rectangle {
                anchors.fill: parent
                color: "#1a1a2e"
                radius: 8
                border.color: "#2a2a4e"
                z: -1
            }
        }

        // Login button
        Rectangle {
            id: loginButton
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: password.bottom
            anchors.topMargin: 12
            width: 350
            height: 42
            color: "#e94560"
            radius: 8
            Text { anchors.centerIn: parent; text: "Sign In"; color: "#ffffff"; font.pixelSize: 17; font.bold: true }
            MouseArea {
                anchors.fill: parent
                onClicked: sddm.login(username.text, password.text, session.currentIndex)
            }
        }
    }

    // ─── Session selector ─────────────────────────────────────────────
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        anchors.left: parent.left
        anchors.leftMargin: 20
        width: 180
        height: 36
        color: "#16213e"
        radius: 8
        border.color: "#2a2a4e"
        ComboBox {
            id: session
            anchors.fill: parent
            anchors.margins: 4
            model: sessionModel
            color: "#ffffff"
            font.pixelSize: 13
        }
    }

    // ─── Reboot ───────────────────────────────────────────────────────
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 64
        width: 36
        height: 36
        color: "#16213e"
        radius: 18
        border.color: "#2a2a4e"
        Text { anchors.centerIn: parent; text: "↻"; font.pixelSize: 18; color: "#e94560" }
        MouseArea { anchors.fill: parent; onClicked: sddm.reboot() }
    }

    // ─── Power off ────────────────────────────────────────────────────
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        anchors.right: parent.right
        anchors.rightMargin: 16
        width: 36
        height: 36
        color: "#16213e"
        radius: 18
        border.color: "#2a2a4e"
        Text { anchors.centerIn: parent; text: "⏻"; font.pixelSize: 18; color: "#e94560" }
        MouseArea { anchors.fill: parent; onClicked: sddm.powerOff() }
    }
}

