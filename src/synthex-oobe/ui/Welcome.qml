import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

// Synthex Welcome Screen — KDE Kirigami native UI
// Like Mint's Welcome Screen but using native KDE widgets

Kirigami.ApplicationWindow {
    id: welcome
    title: "Welcome to SynthOS"
    width: 720
    height: 480
    minimumWidth: 600
    minimumHeight: 400
    
    pageStack.initialPage: welcomePage
    
    Component {
        id: welcomePage
        
        Kirigami.Page {
            title: "Welcome to SynthOS"
            
            Kirigami.CardsLayout {
                columns: 2
                
                Kirigami.Card {
                    banner {
                        title: "🖥 Desktop Tour"
                        backgroundColor: "#9BBD5C"
                    }
                    contentItem: Label {
                        text: "Explore your new Synthex desktop"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Open"
                            onTriggered: Qt.openUrlExternally("help:/synthex/tour")
                        }
                    ]
                }
                
                Kirigami.Card {
                    banner {
                        title: "📦 Software Manager"
                        backgroundColor: "#4A90D9"
                    }
                    contentItem: Label {
                        text: "Install applications and games"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Open"
                            onTriggered: Qt.openUrlExternally("synthex-software-center")
                        }
                    ]
                }
                
                Kirigami.Card {
                    banner {
                        title: "⚙ System Settings"
                        backgroundColor: "#E67E22"
                    }
                    contentItem: Label {
                        text: "Customize your system"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Open"
                            onTriggered: Qt.openUrlExternally("systemsettings")
                        }
                    ]
                }
                
                Kirigami.Card {
                    banner {
                        title: "🎮 Gaming"
                        backgroundColor: "#27AE60"
                    }
                    contentItem: Label {
                        text: "Install gaming tools and optimize"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Open"
                            onTriggered: Qt.openUrlExternally("synthex-gaming-center")
                        }
                    ]
                }
                
                Kirigami.Card {
                    banner {
                        title: "🔒 Security"
                        backgroundColor: "#8E44AD"
                    }
                    contentItem: Label {
                        text: "Check system security status"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Check"
                            onTriggered: Qt.openUrlExternally("synthex-security-check")
                        }
                    ]
                }
                
                Kirigami.Card {
                    banner {
                        title: "🌐 First Steps"
                        backgroundColor: "#2C3E50"
                    }
                    contentItem: Label {
                        text: "Getting started guide"
                        color: Kirigami.Theme.textColor
                    }
                    actions: [
                        Kirigami.Action {
                            text: "Open"
                            onTriggered: Qt.openUrlExternally("help:/synthex/getting-started")
                        }
                    ]
                }
            }
            
            footer: RowLayout {
                Layout.fillWidth: true
                CheckBox {
                    id: dontShowAgain
                    text: "Don't show on startup"
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: "Close"
                    onClicked: {
                        if (dontShowAgain.checked)
                            console.log("Disable welcome on startup")
                        welcome.close()
                    }
                }
            }
        }
    }
}
