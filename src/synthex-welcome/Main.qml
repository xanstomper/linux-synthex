// SPDX-License-Identifier: GPL-3.0-or-Later
// SynthOS Welcome Application
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: root
    width: 920
    height: 620
    minimumWidth: 760
    minimumHeight: 520
    visible: true
    title: qsTr("Welcome to SynthOS")
    Material.theme: Material.Dark
    Material.accent: "#FFB300"

    // Page model
    readonly property var pages: [
        { id: "welcome",   icon: "🚀", label: qsTr("Welcome") },
        { id: "profile",   icon: "🎨", label: qsTr("Your Profile") },
        { id: "apps",      icon: "📦", label: qsTr("App Bundles") },
        { id: "network",   icon: "🌐", label: qsTr("Network") },
        { id: "tips",      icon: "💡", label: qsTr("Tips & Tricks") },
        { id: "finish",    icon: "✅", label: qsTr("Get Started") },
    ]
    property int currentPage: 0

    // ─── Background ──────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: "#0A0C14"
    }

    // Subtle grid overlay
    Canvas {
        anchors.fill: parent
        opacity: 0.03
        onPaint: {
            var ctx = getContext("2d")
            ctx.strokeStyle = "#FFFFFF"
            ctx.lineWidth = 0.5
            for (var x = 0; x < width; x += 32)  { ctx.moveTo(x,0); ctx.lineTo(x,height); }
            for (var y = 0; y < height; y += 32) { ctx.moveTo(0,y); ctx.lineTo(width,y); }
            ctx.stroke()
        }
    }

    // ─── Left sidebar ─────────────────────────────────────────
    Rectangle {
        id: sidebar
        width: 200
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        color: "#0D1117"

        // Logo
        Column {
            anchors { top: parent.top; left: parent.left; right: parent.right }
            anchors.topMargin: 28
            spacing: 0

            Image {
                source: "/usr/share/pixmaps/synthex-logo.png"
                width: 48; height: 48
                anchors.horizontalCenter: parent.horizontalCenter
                smooth: true
            }
            Text {
                text: "SynthOS"
                font { pixelSize: 20; bold: true; family: "Noto Sans" }
                color: "#FFB300"
                anchors.horizontalCenter: parent.horizontalCenter
                topPadding: 8
            }
            Text {
                text: "2026.10  Ignition"
                font.pixelSize: 11
                color: "#556077"
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        // Nav items
        Column {
            anchors {
                left: parent.left; right: parent.right
                top: parent.top; topMargin: 148
            }
            spacing: 2

            Repeater {
                model: root.pages
                delegate: Rectangle {
                    width: parent.width
                    height: 44
                    color: index === root.currentPage ? "#1A2035" : "transparent"
                    radius: 0

                    Rectangle {
                        width: 3; height: parent.height
                        color: index === root.currentPage ? "#FFB300" : "transparent"
                        anchors.left: parent.left
                    }

                    Row {
                        anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
                        spacing: 10
                        Text { text: modelData.icon; font.pixelSize: 16 }
                        Text {
                            text: modelData.label
                            font.pixelSize: 13
                            color: index === root.currentPage ? "#FFFFFF" : "#8899AA"
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentPage = index
                    }
                }
            }
        }

        // Progress dots
        Row {
            anchors { bottom: parent.bottom; bottomMargin: 20; horizontalCenter: parent.horizontalCenter }
            spacing: 6
            Repeater {
                model: root.pages.length
                delegate: Rectangle {
                    width: index === root.currentPage ? 16 : 6
                    height: 6; radius: 3
                    color: index === root.currentPage ? "#FFB300" : "#2A3550"
                    Behavior on width { NumberAnimation { duration: 200 } }
                }
            }
        }
    }

    // ─── Main content area ────────────────────────────────────
    StackLayout {
        anchors {
            left: sidebar.right; right: parent.right
            top: parent.top; bottom: navBar.top
        }
        currentIndex: root.currentPage

        // Page 0 — Welcome
        WelcomePage {}

        // Page 1 — Profile
        ProfilePage {}

        // Page 2 — Apps
        AppBundlePage {}

        // Page 3 — Network
        NetworkPage {}

        // Page 4 — Tips
        TipsPage {}

        // Page 5 — Finish
        FinishPage {}
    }

    // ─── Bottom nav bar ───────────────────────────────────────
    Rectangle {
        id: navBar
        height: 56
        anchors { left: sidebar.right; right: parent.right; bottom: parent.bottom }
        color: "#0D1117"

        Row {
            anchors { right: parent.right; rightMargin: 24; verticalCenter: parent.verticalCenter }
            spacing: 12

            Button {
                text: qsTr("← Back")
                visible: root.currentPage > 0
                Material.background: "#1A2035"
                onClicked: root.currentPage = Math.max(0, root.currentPage - 1)
            }

            Button {
                text: root.currentPage === root.pages.length - 1 ? qsTr("Get Started!") : qsTr("Next →")
                Material.background: "#FFB300"
                Material.foreground: "#0A0C14"
                onClicked: {
                    if (root.currentPage < root.pages.length - 1)
                        root.currentPage++
                    else
                        Qt.quit()
                }
            }
        }
    }
}
