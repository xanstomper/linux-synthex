# SynthOS Justfile — ujust task runner
# Usage: ujust <recipe>  OR  just --justfile /usr/share/synthex/Justfile <recipe>
# SPDX-License-Identifier: GPL-3.0-or-later

set shell := ["bash", "-c"]
set export := true

SYNTHEX_VERSION := "2026.10"
SYNTHEX_EDITION := env_var_or_default("SYNTHEX_EDITION", "plasma")

# ---------- DEFAULT ----------
default:
    @just --list --unsorted

# ---------- SYSTEM ----------

## Update SynthOS (dnf upgrade + flatpak update)
update:
    sudo dnf upgrade --refresh -y
    flatpak update -y
    echo "✓ SynthOS updated"

## Refresh package metadata only
refresh:
    sudo dnf check-update

## Full system upgrade with reboot prompt
upgrade:
    sudo dnf distro-sync --refresh -y
    flatpak update -y
    @echo "Upgrade complete. Reboot recommended."

## Install package(s)  e.g.: ujust install htop
install *PKGS:
    flatpak install --noninteractive {{PKGS}} 2>/dev/null \
        || sudo dnf install -y {{PKGS}}

## Remove package(s)
remove *PKGS:
    sudo dnf remove -y {{PKGS}}

## Clean package cache
clean:
    sudo dnf clean all
    flatpak uninstall --unused -y

## Show SynthOS version info
version:
    @cat /etc/synthex/synthex-release 2>/dev/null || echo "SynthOS {{SYNTHEX_VERSION}}"
    @uname -r
    @flatpak --version

## Open SynthOS Control Center
control-center:
    synthex-control-center &

## Open SynthOS App Manager
app-manager:
    synthex-app-manager &

## Open Gaming Center
gaming-center:
    synthex-gaming-center &

# ---------- GPU ----------

## Detect and show GPU info
gpu-info:
    synthex-hardware-detect --gpu --json 2>/dev/null | python3 -m json.tool || lspci | grep -i "vga\|3d\|display"

## Install NVIDIA drivers (proprietary)
nvidia-install:
    synthex-nvidia-installer --auto

## Switch to open-source GPU drivers
gpu-open:
    synthex-gpu-switch --open

## Switch to proprietary GPU drivers
gpu-proprietary:
    synthex-gpu-switch --proprietary

## Configure GPU for gaming (performance mode)
gpu-gaming:
    synthex-gpu-setupd --profile gaming

## Configure GPU for desktop (balanced mode)
gpu-desktop:
    synthex-gpu-setupd --profile balanced

# ---------- GAMING ----------

## Enable GameMode for current session
gaming-mode:
    systemctl --user start synthex-gaming-mode.service
    @echo "✓ Gaming mode enabled"

## Disable GameMode
gaming-mode-off:
    systemctl --user stop synthex-gaming-mode.service
    @echo "✓ Gaming mode disabled"

## Open Heroic Games Launcher
heroic:
    flatpak run com.heroicgameslauncher.hgl &

## Open Steam
steam:
    steam &

## Manage Proton versions
proton:
    synthex-proton-manager &

## Install gaming packages bundle
gaming-setup:
    sudo dnf install -y @synthex-gaming-core mangohud gamemode proton-ge-custom
    flatpak install -y com.heroicgameslauncher.hgl com.valvesoftware.Steam

# ---------- DESKTOP ----------

## Apply a desktop profile  e.g.: ujust apply-profile gaming
apply-profile PROFILE:
    synthex-control-center --apply-profile {{PROFILE}}

## List available profiles
list-profiles:
    @ls /usr/share/synthex/profiles/ 2>/dev/null | sed 's/.json//'

## Reset desktop to default profile
reset-profile:
    synthex-control-center --apply-profile classic
    @echo "✓ Reset to Classic profile"

## Open wallpaper picker
wallpaper:
    plasmawindowed org.kde.plasma.wallpaperapp &

## Toggle dark/light mode
toggle-theme:
    plasma-apply-colorscheme --list-schemes | head -5

# ---------- AI / HERMES ----------

## Start Hermes AI assistant
hermes:
    hermes-daemon --start 2>/dev/null || synthex-agent start

## Open Hermes chat window
hermes-chat:
    hermes &

## Stop Hermes daemon
hermes-stop:
    hermes-daemon --stop 2>/dev/null || synthex-agent stop

## Pull/update default AI model
ai-model-update:
    ollama pull llama3.2 && ollama pull codellama:7b

## Show AI model status
ai-status:
    ollama list

# ---------- SECURITY ----------

## Show security dashboard
security:
    synthex-security-dashboard &

## Run security audit
security-audit:
    sudo synthex-security-setup --audit

## Enable enhanced security (SELinux enforcing + hardened SSH)
security-harden:
    sudo synthex-security-setup --harden

## Check for security advisories
security-check:
    sudo dnf updateinfo list security

## Configure firewall
firewall:
    sudo firewall-config &

## Show firewall status
firewall-status:
    sudo firewall-cmd --list-all

# ---------- SNAPSHOTS ----------

## Create a BTRFS snapshot
snapshot:
    synthex-snapshot-manager --create "manual-$(date +%Y%m%d-%H%M%S)"

## List snapshots
snapshots:
    synthex-snapshot-manager --list

## Restore snapshot (interactive)
snapshot-restore:
    synthex-snapshot-manager --restore

# ---------- DEVELOPMENT ----------

## Open developer tools
dev-tools:
    synthex-control-center --page developer &

## Open VS Code
code:
    flatpak run com.visualstudio.code &

## Open Flatpak
code-oss:
    flatpak run com.visualstudio.code &

## Build SynthOS (developer use only)
build-iso EDITION="plasma":
    cd $(git rev-parse --show-toplevel 2>/dev/null || echo "/usr/share/synthex") && \
    bash build/scripts/build-iso.sh --edition {{EDITION}}

## Validate last built ISO
validate-iso:
    bash build/scripts/validate-iso.sh

# ---------- SYSTEM HEALTH ----------

## Show disk health (SMART)
disk-health:
    synthex-disk-health &

## Show system logs (last 50 errors)
logs:
    synthex-log-viewer &

## Show hardware info
hardware-info:
    synthex-hardware-detect --all --json | python3 -m json.tool

## Run system health check
health:
    @echo "=== SynthOS Health Check ==="
    @systemctl is-active NetworkManager && echo "✓ Network: OK" || echo "✗ Network: FAILED"
    @systemctl is-active pipewire && echo "✓ Audio: OK" || echo "✗ Audio: FAILED"
    @[ -f /etc/selinux/config ] && grep -q "SELINUX=enforcing" /etc/selinux/config && echo "✓ SELinux: enforcing" || echo "⚠ SELinux: not enforcing"
    @df -h / | tail -1 | awk '{print "✓ Disk: " $4 " free (" $5 " used)"}'
    @free -h | awk '/^Mem/{print "✓ RAM: " $4 " free / " $2 " total"}'

# ---------- NETWORK ----------

## Configure VPN
vpn:
    nm-connection-editor &

## Show network status
network-status:
    nmcli general status
    nmcli connection show --active

## Configure Wi-Fi
wifi:
    plasma-nm &

# ---------- CONTAINERS ----------

## Open Distrobox TUI
distrobox:
    distrobox list

## Create Ubuntu container
container-ubuntu:
    distrobox-create --name ubuntu --image ubuntu:24.04

## Create Arch container
container-arch:
    distrobox-create --name arch --image archlinux:latest

## Open Podman dashboard
podman-dashboard:
    flatpak run io.github.marhkb.Pods &

# ---------- MISC ----------

## Show system info (neofetch-style)
info:
    synthex-system-report --full 2>/dev/null || neofetch 2>/dev/null || fastfetch

## Open SynthOS welcome screen
welcome:
    synthex-welcome &

## Open release notes
release-notes:
    xdg-open https://getsynthex.org/releases/2026.10 &

## Open SynthOS documentation
docs:
    xdg-open https://docs.getsynthex.org &

## Report a bug
bug-report:
    xdg-open https://github.com/synthex-linux/issues/new &
