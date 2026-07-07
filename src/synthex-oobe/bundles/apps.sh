#!/usr/bin/env bash
# Synthex OOBE — Comprehensive Application Bundle Installer
# Called by the OOBE Finish page to install user-selected apps
# Reads app list from /var/lib/synthex/oobe-apps.json (JSON array of app IDs)
# Logs everything to /var/log/synthex-oobe-apps.log
# ================================================================

set -euo pipefail
LOG="/var/log/synthex-oobe-apps.log"
exec > >(tee -a "$LOG") 2>&1

STATE="/var/lib/synthex/oobe-state.json"
APPS_FILE="/var/lib/synthex/oobe-apps.json"

# Ensure Flathub is available
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true

if [ ! -f "$APPS_FILE" ]; then
    echo "[apps] No app list found at $APPS_FILE — skipping"
    exit 0
fi

echo ""
echo "========================================================================"
echo "  Synthex OOBE — Application Installer"
echo "  Started: $(date)"
echo "========================================================================"
echo ""

# Read app list from JSON
APPS=$(python3 -c "
import json, sys
try:
    apps = json.load(open('$APPS_FILE'))
    if isinstance(apps, list):
        print(' '.join(apps))
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)
" 2>/dev/null || echo "")

if [ -z "$APPS" ]; then
    echo "[apps] No apps selected or invalid JSON — skipping"
    exit 0
fi

echo "[apps] Selected applications: $APPS"
echo ""

# ── Helper function ────────────────────────────────────────────
install_app() {
    local app="$1"
    shift
    echo "[apps] Installing ${app}..."
    if "$@" 2>/dev/null; then
        echo "[OK] ${app}"
    else
        echo "[FAIL] ${app}"
    fi
}

# ── Helper: add repo if not already present ────────────────────
ensure_repo() {
    local repo_file="$1"
    local repo_url="$2"
    if [ ! -f "$repo_file" ]; then
        dnf config-manager --add-repo "$repo_url" 2>/dev/null || true
    fi
}

# ── Install each app ───────────────────────────────────────────
for app in $APPS; do
    echo ""
    case $app in

        # ═══════════════════════════════════════════════════════════
        # SYSTEM / AI
        # ═══════════════════════════════════════════════════════════
        ollama)
            install_app "$app" dnf install -y ollama
            systemctl enable --now ollama 2>/dev/null || true
            ;;
        hermes)
            echo "[apps] Installing ${app}..."
            if pip3 show hermes-agent 2>/dev/null; then
                echo "[OK] hermes (already installed)"
            elif pip3 install hermes-agent 2>/dev/null; then
                echo "[OK] hermes"
            elif dnf install -y hermes-agent 2>/dev/null; then
                echo "[OK] hermes"
            else
                echo "[FAIL] hermes — could not install"
            fi
            ;;
        opencode)
            echo "[apps] Installing ${app}..."
            if command -v opencode &>/dev/null; then
                echo "[OK] opencode (already installed)"
            else
                curl -fsSL https://opencode.ai/install.sh 2>/dev/null | bash 2>/dev/null && echo "[OK] opencode" || echo "[FAIL] opencode"
            fi
            ;;
        codex)
            echo "[apps] Installing ${app}..."
            if command -v codex &>/dev/null; then
                echo "[OK] codex (already installed)"
            else
                npm install -g @openai/codex 2>/dev/null && echo "[OK] codex" || echo "[FAIL] codex"
            fi
            ;;
        synthex-agent)
            install_app "$app" dnf install -y synthex-agent
            ;;
        open-webui)
            echo "[apps] Installing ${app}..."
            if podman ps --format '{{.Names}}' 2>/dev/null | grep -q open-webui; then
                echo "[OK] open-webui (already running)"
            else
                podman run -d --name open-webui -p 3000:8080 ghcr.io/open-webui/open-webui:main 2>/dev/null && \
                    echo "[OK] open-webui" || echo "[FAIL] open-webui"
                echo "      Open WebUI available at http://localhost:3000"
            fi
            ;;

        # ═══════════════════════════════════════════════════════════
        # BROWSERS
        # ═══════════════════════════════════════════════════════════
        firefox)
            install_app "$app" dnf install -y firefox
            ;;
        brave)
            ensure_repo "/etc/yum.repos.d/brave-browser.repo" \
                "https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo"
            install_app "$app" dnf install -y brave-browser
            ;;
        chrome)
            ensure_repo "/etc/yum.repos.d/google-chrome.repo" \
                "https://dl.google.com/linux/chrome/rpm/stable/x86_64"
            install_app "$app" dnf install -y google-chrome-stable
            ;;
        tor)
            install_app "$app" dnf install -y tor torbrowser-launcher
            ;;
        edge)
            ensure_repo "/etc/yum.repos.d/microsoft-edge.repo" \
                "https://packages.microsoft.com/yumrepos/edge"
            install_app "$app" dnf install -y microsoft-edge-stable
            ;;
        vivaldi)
            install_app "$app" dnf install -y vivaldi-stable
            ;;
        opera)
            install_app "$app" dnf install -y opera-stable
            ;;

        # ═══════════════════════════════════════════════════════════
        # MESSAGING
        # ═══════════════════════════════════════════════════════════
        discord)
            echo "[apps] Installing ${app}..."
            (flatpak install -y flathub com.discordapp.Discord 2>/dev/null || \
             dnf install -y discord 2>/dev/null) && echo "[OK] discord" || echo "[FAIL] discord"
            ;;
        telegram)
            install_app "$app" dnf install -y telegram-desktop
            ;;
        signal)
            echo "[apps] Installing ${app}..."
            (flatpak install -y flathub org.signal.Signal 2>/dev/null || \
             dnf install -y signal-desktop 2>/dev/null) && echo "[OK] signal" || echo "[FAIL] signal"
            ;;
        whatsapp)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub io.github.mimbrero.WhatsAppDesktop 2>/dev/null && \
                echo "[OK] whatsapp" || echo "[FAIL] whatsapp"
            ;;
        slack)
            echo "[apps] Installing ${app}..."
            (flatpak install -y flathub com.slack.Slack 2>/dev/null || \
             dnf install -y slack 2>/dev/null) && echo "[OK] slack" || echo "[FAIL] slack"
            ;;
        element)
            echo "[apps] Installing ${app}..."
            (flatpak install -y flathub im.riot.Riot 2>/dev/null || \
             dnf install -y element 2>/dev/null) && echo "[OK] element" || echo "[FAIL] element"
            ;;
        zoom)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub us.zoom.Zoom 2>/dev/null && \
                echo "[OK] zoom" || echo "[FAIL] zoom"
            ;;
        thunderbird)
            install_app "$app" dnf install -y thunderbird
            ;;
        mailspring)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub com.getmailspring.Mailspring 2>/dev/null && \
                echo "[OK] mailspring" || echo "[FAIL] mailspring"
            ;;
        sessions)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub io.bassi.Amberol 2>/dev/null && \
                echo "[OK] sessions" || echo "[FAIL] sessions"
            ;;

        # ═══════════════════════════════════════════════════════════
        # GAMING
        # ═══════════════════════════════════════════════════════════
        steam)
            install_app "$app" dnf install -y steam
            ;;
        lutris)
            install_app "$app" dnf install -y lutris
            ;;
        heroic)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub com.heroicgameslauncher.hgl 2>/dev/null && \
                echo "[OK] heroic" || echo "[FAIL] heroic"
            ;;
        gamescope)
            install_app "$app" dnf install -y gamescope
            ;;
        mangohud)
            install_app "$app" dnf install -y mangohud
            ;;
        gamemode)
            install_app "$app" dnf install -y gamemode
            ;;
        protonup)
            install_app "$app" dnf install -y protonup-qt
            ;;
        retroarch)
            install_app "$app" dnf install -y retroarch
            ;;

        # ═══════════════════════════════════════════════════════════
        # MULTIMEDIA
        # ═══════════════════════════════════════════════════════════
        vlc)
            install_app "$app" dnf install -y vlc
            ;;
        mpv)
            install_app "$app" dnf install -y mpv
            ;;
        obs)
            install_app "$app" dnf install -y obs-studio
            ;;
        kdenlive)
            install_app "$app" dnf install -y kdenlive
            ;;
        spotify)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub com.spotify.Client 2>/dev/null && \
                echo "[OK] spotify" || echo "[FAIL] spotify"
            ;;
        audacity)
            install_app "$app" dnf install -y audacity
            ;;

        # ═══════════════════════════════════════════════════════════
        # CREATIVE
        # ═══════════════════════════════════════════════════════════
        blender)
            install_app "$app" dnf install -y blender
            ;;
        gimp)
            install_app "$app" dnf install -y gimp
            ;;
        krita)
            install_app "$app" dnf install -y krita
            ;;
        inkscape)
            install_app "$app" dnf install -y inkscape
            ;;
        libreoffice)
            install_app "$app" dnf install -y libreoffice
            ;;
        onlyoffice)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub org.onlyoffice.desktopeditors 2>/dev/null && \
                echo "[OK] onlyoffice" || echo "[FAIL] onlyoffice"
            ;;
        obsidian)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub md.obsidian.Obsidian 2>/dev/null && \
                echo "[OK] obsidian" || echo "[FAIL] obsidian"
            ;;

        # ═══════════════════════════════════════════════════════════
        # DEVELOPMENT
        # ═══════════════════════════════════════════════════════════
        vscode)
            install_app "$app" dnf install -y code
            ;;
        docker)
            echo "[apps] Installing ${app}..."
            if dnf install -y docker docker-compose 2>/dev/null; then
                systemctl enable --now docker 2>/dev/null || true
                echo "[OK] docker"
            else
                echo "[FAIL] docker"
            fi
            ;;
        podman)
            install_app "$app" dnf install -y podman podman-compose
            ;;
        distrobox)
            install_app "$app" dnf install -y distrobox
            ;;
        gitkraken)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub com.axosoft.GitKraken 2>/dev/null && \
                echo "[OK] gitkraken" || echo "[FAIL] gitkraken"
            ;;
        neovim)
            install_app "$app" dnf install -y neovim
            ;;
        jetbrains)
            echo "[apps] Installing ${app}..."
            flatpak install -y flathub com.jetbrains.IntelliJ-IDEA-Community 2>/dev/null && \
                echo "[OK] jetbrains" || echo "[FAIL] jetbrains"
            ;;

        # ═══════════════════════════════════════════════════════════
        # UNKNOWN
        # ═══════════════════════════════════════════════════════════
        *)
            echo "[apps] Skipping unknown app: $app"
            echo "[WARN] ${app} (no handler defined)"
            ;;
    esac
done

echo ""
echo "========================================================================"
echo "  Application installation complete"
echo "  Finished: $(date)"
echo "  Log: $LOG"
echo "  Some apps may require a logout/login or reboot to appear."
echo "========================================================================"
exit 0
