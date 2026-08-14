import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import org.synthex.Backend 1.0

Window {
    id: mainWindow
    visible: true
    width: 1200
    height: 800
    minimumWidth: 960
    minimumHeight: 640
    title: "Synthex Control Center"
    color: "#0C1116"

    property int activeNavIndex: 0
    property string currentPage: "Dashboard"

    // Accent color
    readonly property color accentColor: "#6C88A8"
    readonly property color bgColor: "#0C1116"
    readonly property color surfaceColor: "#171D24"
    readonly property color textColor: "#FFFFFF"
    readonly property color mutedText: "#9AA1AB"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar
        Rectangle {
            id: sidebar
            Layout.preferredWidth: 64
            Layout.fillHeight: true
            color: "#161C22"
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Logo area
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    color: "transparent"

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            width: 36
                            height: 36
                            radius: 8
                            color: accentColor
                            Text {
                                anchors.centerIn: parent
                                text: "S"
                                font.pixelSize: 22
                                font.bold: true
                                color: "#0C1116"
                            }
                        }

                        ColumnLayout {
                            visible: false
                            spacing: 2
                            Text {
                                text: "Synthex"
                                font.pixelSize: 18
                                font.bold: true
                                color: textColor
                            }
                            Text {
                                text: "Control Center"
                                font.pixelSize: 11
                                color: mutedText
                            }
                        }
                    }
                }

                // Separator
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: "#12FFFFFF"
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                }

                // Navigation items
                ListView {
                    id: navList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 12
                    clip: true
                    interactive: false
                    model: ListModel {
                        ListElement { name: "Dashboard"; icon: "\u{1F4CA}" }
                        ListElement { name: "System"; icon: "\u{1F4BB}" }
                        ListElement { name: "Performance"; icon: "\u{26A1}" }
                        ListElement { name: "Gaming"; icon: "\u{1F3AE}" }
                        ListElement { name: "Developer"; icon: "\u{1F4D1}" }
                        ListElement { name: "Themes"; icon: "\u{1F3A8}" }
                        ListElement { name: "Security"; icon: "\u{1F6E1}" }
                        ListElement { name: "Updates"; icon: "\u{1F504}" }
                        ListElement { name: "Drivers"; icon: "\u{1F527}" }
                        ListElement { name: "RGB"; icon: "\u{1F308}" }
                        ListElement { name: "Snapshots"; icon: "\u{1F4BE}" }
                        ListElement { name: "Kernel"; icon: "\u{1F9A0}" }
                        ListElement { name: "Controllers"; icon: "\u{1F579}" }
                    }

                    delegate: ItemDelegate {
                        width: parent.width
                        height: 44
                        highlighted: ListView.isCurrentItem
                        leftPadding: 0
                        rightPadding: 0

                        background: Rectangle {
                            color: highlighted ? Qt.rgba(0.42, 0.53, 0.66, 0.16) : (hovered ? "#1E2030" : "transparent")
                            radius: 8
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            Behavior on color { ColorAnimation { duration: 140 } }

                            Rectangle {
                                visible: highlighted
                                width: 3
                                height: 24
                                color: accentColor
                                radius: 2
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: 0
                            }
                        }

                        contentItem: RowLayout {
                            spacing: 0
                            Text {
                                text: model.icon
                                font.pixelSize: 18
                            }
                            Text {
                                visible: false
                                text: model.name
                                font.pixelSize: 14
                                color: highlighted ? textColor : mutedText
                                font.bold: highlighted
                            }
                            Item { Layout.fillWidth: true }
                        }

                        ToolTip.visible: hovered
                        ToolTip.text: model.name
                        ToolTip.delay: 350
                        onClicked: {
                            navList.currentIndex = index;
                            activeNavIndex = index;
                            currentPage = model.name;
                            pageStack.replace(pageComponent, { pageName: model.name });
                        }
                    }
                }

                // Footer
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: "#12FFFFFF"
                    Layout.leftMargin: 16
                    Layout.rightMargin: 16
                }

                Item { Layout.preferredHeight: 16 }
            }
        }

        // Content area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: bgColor

            StackView {
                id: pageStack
                anchors.fill: parent
                anchors.margins: 24
                initialItem: pageComponent

                replaceEnter: Transition {
                    NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200; easing.type: Easing.OutCubic }
                }
                replaceExit: Transition {
                    NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 150 }
                }

                Component {
                    id: pageComponent
                    Loader {
                        property string pageName: "Dashboard"
                        source: {
                            switch(pageName) {
                                case "Dashboard":    return "pages/Dashboard.qml";
                                case "System":       return "pages/System.qml";
                                case "Performance":  return "pages/Performance.qml";
                                case "Gaming":       return "pages/Gaming.qml";
                                case "Developer":    return "pages/Developer.qml";
                                case "Desktop":      return "pages/DesktopCustomization.qml";
                                case "Themes":       return "pages/DesktopCustomization.qml";
                                case "Security":     return "pages/Security.qml";
                                case "Updates":      return "pages/Updates.qml";
                                case "Drivers":      return "pages/Drivers.qml";
                                case "RGB":          return "pages/RGB.qml";
                                case "Snapshots":    return "pages/Snapshots.qml";
                                case "Kernel":       return "pages/Kernel.qml";
                                case "Controllers":  return "pages/Controllers.qml";
                                default:             return "pages/Dashboard.qml";
                            }
                        }
                    }
                }
            }
        }
    }

    // Page title header
    Rectangle {
        id: pageHeader
        anchors.top: parent.top
        anchors.left: sidebar.right
        anchors.right: parent.right
        height: 60
        color: "#161C22"
        z: 10

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            text: currentPage
            font.pixelSize: 22
            font.bold: true
            color: textColor
        }
    }

    // Adjust content area for header
    onCurrentPageChanged: {
        pageStack.anchors.topMargin = 60 + 24;
    }

    Component.onCompleted: {
        pageStack.anchors.topMargin = 60 + 24;
    }
}
