// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

Kirigami.ScrollablePage {
    title: i18n("Gaming Center Settings")

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Library") }

            RowLayout {
                Kirigami.FormData.label: i18n("Scan Steam library:")
                Switch { checked: true }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Scan Lutris library:")
                Switch { checked: true }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Scan Heroic library:")
                Switch { checked: true }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Include Flatpak games:")
                Switch { checked: true }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Custom game folder:")
                TextField { placeholderText: "~/Games"; Layout.preferredWidth: 220 }
                Button { text: "Browse…"; icon.name: "folder" }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Performance Defaults") }

            RowLayout {
                Kirigami.FormData.label: i18n("Auto-enable GameMode on launch:")
                Switch { checked: true }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Show MangoHud by default:")
                Switch { checked: false }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Notify on game exit (stats):")
                Switch { checked: true }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Proton / Wine") }

            RowLayout {
                Kirigami.FormData.label: i18n("Default Proton for new games:")
                ComboBox { model: ["Proton GE (latest)", "Proton Experimental", "System Wine", "Ask each time"] }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("DXVK async:")
                Switch { checked: true }
            }

            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Interface") }

            RowLayout {
                Kirigami.FormData.label: i18n("Start minimised to tray:")
                Switch { checked: false }
            }
            RowLayout {
                Kirigami.FormData.label: i18n("Show playtime in library:")
                Switch { checked: true }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            Button { text: i18n("Reset to defaults"); icon.name: "edit-clear" }
            Button { text: i18n("Save"); icon.name: "document-save"; highlighted: true }
        }
    }
}
