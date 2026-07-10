// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS Control Center — Developer Tools Page
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami
import SynthOS.Control 1.0

Kirigami.ScrollablePage {
    id: devPage
    title: i18n("Developer Tools")

    // ── Tool detection ──────────────────────────────────────────────────────
    function toolVer(cmd) {
        return SynthexBackend.execOutput(cmd + " --version 2>/dev/null | head -1").trim()
    }

    readonly property var devTools: [
        { name: "Git",       icon: "git",         cmd: "git",          ver: toolVer("git"),      pkg: "git"            },
        { name: "Python 3",  icon: "python",       cmd: "python3",      ver: toolVer("python3"),  pkg: "python3"        },
        { name: "Rust",      icon: "rust",         cmd: "rustc",        ver: toolVer("rustc"),    pkg: "rustup"         },
        { name: "Go",        icon: "go",           cmd: "go",           ver: toolVer("go"),       pkg: "golang"         },
        { name: "Node.js",   icon: "nodejs",       cmd: "node",         ver: toolVer("node"),     pkg: "nodejs"         },
        { name: "Java",      icon: "java",         cmd: "java",         ver: toolVer("java"),     pkg: "java-21-openjdk"},
        { name: "GCC",       icon: "gcc",          cmd: "gcc",          ver: toolVer("gcc"),      pkg: "gcc"            },
        { name: "Clang",     icon: "llvm",         cmd: "clang",        ver: toolVer("clang"),    pkg: "clang"          },
        { name: "CMake",     icon: "cmake",        cmd: "cmake",        ver: toolVer("cmake"),    pkg: "cmake"          },
        { name: "Make",      icon: "make",         cmd: "make",         ver: toolVer("make"),     pkg: "make"           },
        { name: "Docker",    icon: "docker",       cmd: "docker",       ver: toolVer("docker"),   pkg: "docker-ce"      },
        { name: "Podman",    icon: "podman",       cmd: "podman",       ver: toolVer("podman"),   pkg: "podman"         }
    ]

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        // ── Tool matrix ───────────────────────────────────────────────────────
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Installed Toolchains") }
        }

        GridLayout {
            columns: 3
            Layout.fillWidth: true
            columnSpacing: Kirigami.Units.smallSpacing
            rowSpacing:    Kirigami.Units.smallSpacing

            Repeater {
                model: devTools
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    radius: 8
                    color: modelData.ver !== "" ? Qt.rgba(0,1,0.4,0.06) : Qt.rgba(1,1,1,0.03)
                    border.color: modelData.ver !== "" ? "#1a5c2a" : Kirigami.Theme.separatorColor
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent; anchors.margins: 10; spacing: 10

                        Kirigami.Icon {
                            source: modelData.ver !== "" ? "emblem-ok-symbolic" : "emblem-error-symbolic"
                            width: 18; height: 18
                            color: modelData.ver !== "" ? "#66EE88" : Kirigami.Theme.disabledTextColor
                        }

                        ColumnLayout {
                            spacing: 2
                            Label {
                                text: modelData.name
                                font.bold: true
                                font.pixelSize: 13
                            }
                            Label {
                                text: modelData.ver !== "" ? modelData.ver : i18n("Not installed")
                                font.pixelSize: 10
                                color: Kirigami.Theme.disabledTextColor
                                elide: Text.ElideRight
                                Layout.maximumWidth: 160
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            visible: modelData.ver === ""
                            text: i18n("Install")
                            icon.name: "list-add"
                            font.pixelSize: 11
                            Layout.preferredHeight: 28
                            onClicked: SynthexBackend.execAsRoot("dnf install -y " + modelData.pkg)
                        }
                    }
                }
            }
        }

        // ── Containers / Distrobox ────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Containers & Environments") }

            RowLayout {
                Kirigami.FormData.label: i18n("Distrobox:")
                Label { text: SynthexBackend.which("distrobox") !== "" ? "✓ " + toolVer("distrobox") : "Not installed" }
                Button {
                    text: "Install Distrobox"
                    visible: SynthexBackend.which("distrobox") === ""
                    onClicked: SynthexBackend.execAsRoot("dnf install -y distrobox")
                }
                Button {
                    text: "New Container…"
                    icon.name: "list-add"
                    visible: SynthexBackend.which("distrobox") !== ""
                    onClicked: newContainerDialog.open()
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Running containers:")
                Label {
                    text: SynthexBackend.execOutput("podman ps --format '{{.Names}}' 2>/dev/null | wc -l").trim() + " running"
                }
                Button {
                    text: i18n("Open Podman Desktop")
                    icon.name: "utilities-terminal"
                    onClicked: SynthexBackend.exec("flatpak run io.podman_desktop.PodmanDesktop 2>/dev/null || podman-desktop")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Buildah (OCI builds):")
                Label { text: SynthexBackend.which("buildah") !== "" ? "✓ " + toolVer("buildah") : "Not installed" }
            }
        }

        // ── Editors & IDEs ────────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Editors & IDEs") }
        }

        GridLayout {
            columns: 4
            Layout.fillWidth: true
            columnSpacing: Kirigami.Units.smallSpacing
            rowSpacing:    Kirigami.Units.smallSpacing

            Repeater {
                model: [
                    { name: "VS Code",     cmd: "code",        flatpak: "com.visualstudio.code",     icon: "text-editor" },
                    { name: "Neovim",      cmd: "nvim",        pkg:     "neovim",                    icon: "utilities-terminal" },
                    { name: "Helix",       cmd: "hx",          pkg:     "helix",                     icon: "utilities-terminal" },
                    { name: "Zed",         cmd: "zed",         flatpak: "dev.zed.Zed",               icon: "text-editor" },
                    { name: "JetBrains",   cmd: "idea",        flatpak: "com.jetbrains.IntelliJ-IDEA-Community", icon: "applications-development" },
                    { name: "Emacs",       cmd: "emacs",       pkg:     "emacs",                     icon: "utilities-terminal" },
                    { name: "Kate",        cmd: "kate",        pkg:     "kate",                      icon: "accessories-text-editor" },
                    { name: "Blender",     cmd: "blender",     flatpak: "org.blender.Blender",       icon: "blender" }
                ]
                delegate: RowLayout {
                    spacing: 6
                    Kirigami.Icon {
                        source: SynthexBackend.which(modelData.cmd) !== "" ? "emblem-ok-symbolic" : "emblem-symbolic"
                        width: 14; height: 14
                        color: SynthexBackend.which(modelData.cmd) !== "" ? "#66EE88" : Kirigami.Theme.disabledTextColor
                    }
                    Label {
                        text: modelData.name
                        font.pixelSize: 12
                        color: SynthexBackend.which(modelData.cmd) !== ""
                               ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                    }
                    Button {
                        visible: SynthexBackend.which(modelData.cmd) !== ""
                        text: i18n("Open")
                        font.pixelSize: 10
                        Layout.preferredHeight: 24
                        onClicked: SynthexBackend.exec(modelData.cmd)
                    }
                    Button {
                        visible: SynthexBackend.which(modelData.cmd) === ""
                        text: i18n("Get")
                        font.pixelSize: 10
                        Layout.preferredHeight: 24
                        onClicked: {
                            if (modelData.flatpak)
                                SynthexBackend.execAsRoot("flatpak install -y flathub " + modelData.flatpak)
                            else
                                SynthexBackend.execAsRoot("dnf install -y " + (modelData.pkg || modelData.cmd))
                        }
                    }
                }
            }
        }

        // ── Version Managers ──────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("Version Managers") }

            RowLayout {
                Kirigami.FormData.label: i18n("rustup (Rust):")
                Label { text: SynthexBackend.execOutput("rustup show active-toolchain 2>/dev/null | head -1").trim() || "Not installed" }
                Button {
                    text: "Update Rust"
                    visible: SynthexBackend.which("rustup") !== ""
                    onClicked: SynthexBackend.exec("konsole --noclose -e bash -c 'rustup update; read'")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("nvm (Node):")
                Label {
                    text: SynthexBackend.execOutput("[ -d ~/.nvm ] && echo 'nvm installed: ' $(ls ~/.nvm/versions/node/ 2>/dev/null | tail -3 | tr '\n' ' ') || echo 'Not installed'").trim()
                }
                Button {
                    text: "Install nvm"
                    visible: !SynthexBackend.fileExists(SynthexBackend.execOutput("echo $HOME").trim() + "/.nvm")
                    onClicked: SynthexBackend.exec("konsole --noclose -e bash -c 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash; read'")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("pyenv (Python):")
                Label {
                    text: SynthexBackend.execOutput("pyenv versions 2>/dev/null | head -3").trim() || "Not installed"
                }
                Button {
                    text: "Install pyenv"
                    visible: SynthexBackend.which("pyenv") === ""
                    onClicked: SynthexBackend.exec("konsole --noclose -e bash -c 'curl https://pyenv.run | bash; read'")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("sdkman (JVM):")
                Label {
                    text: SynthexBackend.execOutput("~/.sdkman/bin/sdkman-init.sh 2>/dev/null; sdk version 2>/dev/null | head -1").trim() || "Not installed"
                }
            }
        }

        // ── Synthex Dev Tools ─────────────────────────────────────────────────
        Kirigami.Separator {}
        Kirigami.FormLayout {
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: i18n("SynthOS Dev Tools") }

            RowLayout {
                Kirigami.FormData.label: i18n("synthex CLI:")
                Label { text: SynthexBackend.execOutput("synthex --version 2>/dev/null").trim() || "Not in PATH" }
                Button {
                    text: "Open Terminal"
                    icon.name: "utilities-terminal"
                    onClicked: SynthexBackend.exec("konsole")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Flatseal (Flatpak perms):")
                Label { text: SynthexBackend.which("flatseal") !== "" ? "✓ Installed" : "Not installed" }
                Button {
                    text: "Install"
                    visible: SynthexBackend.which("flatseal") === ""
                    onClicked: SynthexBackend.execAsRoot("flatpak install -y flathub com.github.tchx84.Flatseal")
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Dev repos enabled:")
                Switch {
                    id: devRepoSwitch
                    checked: SynthexBackend.execOutput("dnf repolist | grep -c synthex-dev || echo 0").trim() !== "0"
                    onToggled: {
                        if (checked)
                            SynthexBackend.execAsRoot("dnf config-manager --enable synthex-dev 2>/dev/null || true")
                        else
                            SynthexBackend.execAsRoot("dnf config-manager --disable synthex-dev 2>/dev/null || true")
                    }
                }
            }
        }

        // ── Quick terminal launchers ──────────────────────────────────────────
        Kirigami.Separator {}
        Label { text: i18n("Quick Launchers"); font.bold: true; font.pixelSize: 14 }

        Flow {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Repeater {
                model: [
                    { t: "System Monitor",   c: "btop" },
                    { t: "htop",             c: "htop" },
                    { t: "Disk Usage (ncdu)",c: "ncdu /" },
                    { t: "Network (ss)",     c: "ss -tulpn" },
                    { t: "Journal Log",      c: "journalctl -xe" },
                    { t: "distrobox list",   c: "distrobox list" },
                    { t: "podman ps",        c: "podman ps -a" },
                    { t: "Nix Shell",        c: "nix-shell" }
                ]
                Button {
                    text: modelData.t
                    icon.name: "utilities-terminal"
                    onClicked: SynthexBackend.exec("konsole --noclose -e bash -c '" + modelData.c + "; read -p Done'")
                }
            }
        }

        Item { height: Kirigami.Units.largeSpacing }
    }

    // ── New container dialog ──────────────────────────────────────────────────
    Dialog {
        id: newContainerDialog
        title: i18n("New Distrobox Container")
        width: 420; standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            spacing: Kirigami.Units.smallSpacing

            Label { text: i18n("Container name:") }
            TextField { id: containerName; placeholderText: "my-dev-env"; Layout.fillWidth: true }

            Label { text: i18n("Image:") }
            ComboBox {
                id: containerImage
                Layout.fillWidth: true
                model: [
                    "ubuntu:24.04",
                    "fedora:latest",
                    "debian:bookworm",
                    "archlinux:latest",
                    "opensuse/tumbleweed",
                    "rockylinux:9",
                    "alpine:latest"
                ]
            }
        }

        onAccepted: {
            var name = containerName.text || "dev-env"
            var img  = containerImage.currentText
            SynthexBackend.exec(
                "konsole --noclose -e bash -c 'distrobox create --name " + name +
                " --image " + img + " && distrobox enter " + name + "; read'"
            )
        }
    }
}
