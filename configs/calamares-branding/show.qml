# /usr/share/calamares/branding/solus/show.qml — Calamares slideshow
# Simple QML slideshow shown during installation

import QtQuick 2.0

Rectangle {
    id: root
    width: 800
    height: 600
    color: "#1a1a2e"

    // Slides
    ListModel {
        id: slides
        ListElement { title: "Welcome to Solus"; subtitle: "The gaming-focused Linux distribution"; color: "#e94560" }
        ListElement { title: "Gaming Ready"; subtitle: "Steam, Proton, Lutris, Heroic — all preconfigured"; color: "#0f3460" }
        ListElement { title: "Performance Tuned"; subtitle: "CachyOS-style kernel tuning out of the box"; color: "#16213e" }
        ListElement { title: "Bazzite Features"; subtitle: "ujust, handheld support, Steam Gaming Mode"; color: "#533483" }
        ListElement { title: "Nobara Fixes"; subtitle: "NVIDIA wizard, OBS plugins, audio improvements"; color: "#e94560" }
        ListElement { title: "Mint Usability"; subtitle: "Timeshift, USB writer, beginner-friendly tools"; color: "#0f3460" }
        ListElement { title: "Recovery System"; subtitle: "Btrfs snapshots, automatic rollback, boot repair"; color: "#16213e" }
        ListElement { title: "Unified Control Center"; subtitle: "One app for drivers, RGB, performance, snapshots"; color: "#533483" }
        ListElement { title: "Almost Done"; subtitle: "Installing packages and configuring your system..."; color: "#e94560" }
    }

    property int currentSlide: 0

    Timer {
        id: slideTimer
        interval: 4000
        running: true
        repeat: true
        onTriggered: {
            if (root.currentSlide < slides.count - 1) {
                root.currentSlide++
            }
        }
    }

    // Logo
    Image {
        id: logo
        anchors.top: parent.top
        anchors.topMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        source: "solus-logo.png"
        width: 120
        height: 120
        fillMode: Image.PreserveAspectFit
    }

    // Title
    Text {
        id: title
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -30
        text: slides.get(root.currentSlide).title
        color: slides.get(root.currentSlide).color
        font.pixelSize: 36
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
    }

    // Subtitle
    Text {
        id: subtitle
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 20
        width: parent.width - 100
        text: slides.get(root.currentSlide).subtitle
        color: "#ffffff"
        font.pixelSize: 20
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
    }

    // Progress dots
    Row {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 30
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 10

        Repeater {
            model: slides.count
            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: index === root.currentSlide ? "#e94560" : "#555555"
            }
        }
    }
}
