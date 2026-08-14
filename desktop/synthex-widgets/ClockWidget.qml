import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 240
    height: 110
    radius: 18
    color: "#141923"
    border.color: "#14ffffff"
    border.width: 1

    property string currentTime: "04:44"
    property string currentAmPm: "PM"
    property string currentDate: "Tue, 09 August 2022"

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var now = new Date()
            var hours = now.getHours()
            var ampm = hours >= 12 ? "PM" : "AM"
            hours = hours % 12
            hours = hours ? hours : 12
            var strHours = hours < 10 ? "0" + hours : "" + hours
            var min = now.getMinutes()
            var strMin = min < 10 ? "0" + min : "" + min
            root.currentTime = strHours + ":" + strMin
            root.currentAmPm = ampm

            var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            var months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            var dayName = days[now.getDay()]
            var dayNum = now.getDate() < 10 ? "0" + now.getDate() : "" + now.getDate()
            var monthName = months[now.getMonth()]
            root.currentDate = dayName + ", " + dayNum + " " + monthName + " " + now.getFullYear()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 4

        RowLayout {
            spacing: 2
            Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter

            Text {
                text: root.currentTime
                font.family: "Inter"
                font.pixelSize: 38
                font.bold: true
                color: "#7AA2F7"
                font.letterSpacing: -0.5
            }

            Text {
                text: root.currentAmPm
                font.family: "Inter"
                font.pixelSize: 18
                font.bold: true
                color: "#56759B"
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 5
                Layout.leftMargin: 3
            }
        }

        Text {
            text: root.currentDate
            font.family: "Inter"
            font.pixelSize: 13
            font.weight: Font.Medium
            color: "#9AA1AB"
            Layout.alignment: Qt.AlignLeft
        }
    }
}
