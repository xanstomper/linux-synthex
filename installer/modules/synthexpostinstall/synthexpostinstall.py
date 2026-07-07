#!/usr/bin/env python3
"""Synthex Post-Install — Applies profile, installs apps, configures first-boot.
Wires up all Synthex apps and packages into the installed system.

This is the master wiring module. It:
1. Reads user selections from Calamares global storage
2. Installs the selected apps via dnf/flatpak
3. Applies the desktop profile and theme
4. Enables all Synthex systemd services
5. Writes install manifest for first-boot OOBE
"""
import os, json, subprocess, shutil, glob as globmod

try:
    import calamares
    from calamares.utils import debug, warning
except ImportError:
    def debug(msg): print(f"[synthexpostinstall] {msg}")
    def warning(msg): print(f"[synthexpostinstall] WARNING: {msg}")

SYNTHEX_STATE = "/var/lib/synthex"
SYNTHEX_BIN = "/usr/bin"
SYNTHEX_LIBEXEC = "/usr/libexec/synthex"
SYNTHEX_SERVICES = "/usr/lib/systemd/system"

# ─── Profile-to-package-group mapping ──────────────────────────────────
# Maps each desktop profile to the RPM package groups it needs.
# These groups are defined in packages/groups/synthex-comps.xml
PROFILE_GROUPS = {
    "focus":   ["synthex-core", "synthex-codecs"],
    "gaming":  ["synthex-core", "synthex-plasma", "synthex-gaming", "synthex-codecs", "synthex-nvidia"],
    "pro":     ["synthex-core", "synthex-plasma", "synthex-codecs", "synthex-developer"],
    "touch":   ["synthex-core", "synthex-plasma", "synthex-handheld", "synthex-codecs"],
    "classic": ["synthex-core", "synthex-plasma", "synthex-codecs"],
    "lite":    ["synthex-core"],
    "studio":  ["synthex-core", "synthex-plasma", "synthex-codecs", "synthex-creator"],
    "ai":      ["synthex-core", "synthex-plasma", "synthex-codecs", "synthex-ai"],
}

# ─── Synthex Apps Registry (60+ apps) ──────────────────────────────────
# Every app in the QML app picker has a matching entry here.
# Each entry maps app ID → {name, command}.
# The command is tried in order: flatpak first (reliable), then dnf.
SYNTHEX_APPS_REGISTRY = {
    # ── Browsers ──
    "firefox":   {"name": "Firefox",          "cmd": "dnf install -y firefox"},
    "brave":     {"name": "Brave Browser",    "cmd": "flatpak install -y flathub com.brave.Browser 2>/dev/null || dnf config-manager --add-repo https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo 2>/dev/null && dnf install -y brave-browser"},
    "chrome":    {"name": "Google Chrome",    "cmd": "flatpak install -y flathub com.google.Chrome 2>/dev/null || dnf config-manager --add-repo https://dl.google.com/linux/chrome/rpm/stable/x86_64 2>/dev/null && dnf install -y google-chrome-stable"},
    "tor":       {"name": "Tor Browser",      "cmd": "flatpak install -y flathub org.torproject.Torbrowser 2>/dev/null || dnf install -y torbrowser-launcher"},
    "edge":      {"name": "Microsoft Edge",   "cmd": "flatpak install -y flathub com.microsoft.Edge"},
    "vivaldi":   {"name": "Vivaldi",          "cmd": "flatpak install -y flathub com.vivaldi.Vivaldi"},
    "opera":     {"name": "Opera",            "cmd": "flatpak install -y flathub com.opera.Opera"},
    # ── Messaging ──
    "discord":   {"name": "Discord",          "cmd": "flatpak install -y flathub com.discordapp.Discord 2>/dev/null || dnf install -y discord"},
    "telegram":  {"name": "Telegram",         "cmd": "flatpak install -y flathub org.telegram.desktop 2>/dev/null || dnf install -y telegram-desktop"},
    "signal":    {"name": "Signal Desktop",   "cmd": "flatpak install -y flathub org.signal.Signal"},
    "whatsapp":  {"name": "WhatsApp Desktop", "cmd": "flatpak install -y flathub io.github.mimbrero.WhatsAppDesktop"},
    "slack":     {"name": "Slack",            "cmd": "flatpak install -y flathub com.slack.Slack"},
    "element":   {"name": "Element",          "cmd": "flatpak install -y flathub im.riot.Riot"},
    "zoom":      {"name": "Zoom",             "cmd": "flatpak install -y flathub us.zoom.Zoom"},
    "thunderbird": {"name": "Thunderbird",    "cmd": "dnf install -y thunderbird"},
    "mailspring":  {"name": "Mailspring",     "cmd": "flatpak install -y flathub com.getmailspring.Mailspring"},
    # ── Gaming ──
    "steam":     {"name": "Steam",            "cmd": "dnf install -y steam"},
    "lutris":    {"name": "Lutris",           "cmd": "dnf install -y lutris"},
    "heroic":    {"name": "Heroic Games",     "cmd": "flatpak install -y flathub com.heroicgameslauncher.hgl 2>/dev/null || dnf install -y heroic-games-launcher"},
    "gamescope": {"name": "Gamescope",        "cmd": "dnf install -y gamescope"},
    "mangohud":  {"name": "MangoHud",         "cmd": "dnf install -y mangohud"},
    "gamemode":  {"name": "GameMode",         "cmd": "dnf install -y gamemode"},
    "protonup":  {"name": "ProtonUp-Qt",      "cmd": "flatpak install -y flathub net.davidotek.pupgui2"},
    "retroarch": {"name": "RetroArch",        "cmd": "dnf install -y retroarch"},
    # ── Multimedia ──
    "vlc":       {"name": "VLC Media Player", "cmd": "dnf install -y vlc"},
    "mpv":       {"name": "MPV Player",       "cmd": "dnf install -y mpv"},
    "obs":       {"name": "OBS Studio",       "cmd": "dnf install -y obs-studio"},
    "kdenlive":  {"name": "Kdenlive",         "cmd": "dnf install -y kdenlive"},
    "spotify":   {"name": "Spotify",          "cmd": "flatpak install -y flathub com.spotify.Client 2>/dev/null || dnf install -y spotify-client"},
    "audacity":  {"name": "Audacity",         "cmd": "dnf install -y audacity"},
    # ── Creative ──
    "blender":   {"name": "Blender 3D",       "cmd": "dnf install -y blender"},
    "gimp":      {"name": "GIMP",             "cmd": "dnf install -y gimp"},
    "krita":     {"name": "Krita",            "cmd": "dnf install -y krita"},
    "inkscape":  {"name": "Inkscape",         "cmd": "dnf install -y inkscape"},
    "libreoffice": {"name": "LibreOffice",    "cmd": "dnf install -y libreoffice"},
    "onlyoffice":  {"name": "OnlyOffice",     "cmd": "flatpak install -y flathub com.onlyoffice.Desktopeditors"},
    "obsidian":  {"name": "Obsidian",         "cmd": "flatpak install -y flathub md.obsidian.Obsidian 2>/dev/null || dnf install -y obsidian"},
    # ── Development ──
    "vscode":    {"name": "VS Code",          "cmd": "dnf install -y code"},
    "docker":    {"name": "Docker",           "cmd": "dnf install -y docker docker-compose"},
    "podman":    {"name": "Podman",           "cmd": "dnf install -y podman podman-compose"},
    "distrobox": {"name": "Distrobox",        "cmd": "dnf install -y distrobox"},
    "gitkraken": {"name": "GitKraken",        "cmd": "flatpak install -y flathub com.axosoft.GitKraken"},
    "neovim":    {"name": "Neovim",           "cmd": "dnf install -y neovim"},
    "jetbrains": {"name": "JetBrains IDEs",   "cmd": "flatpak install -y flathub com.jetbrains.IntelliJ-IDEA-Community"},
    # ── AI & Agents ──
    "ollama":       {"name": "Ollama",        "cmd": "curl -fsSL https://ollama.com/install.sh | sh"},
    "hermes":       {"name": "Hermes",        "cmd": "pip3 install hermes-agent 2>/dev/null || echo 'Install hermes manually'"},
    "opencode":     {"name": "OpenCode",      "cmd": "curl -fsSL https://opencode.ai/install.sh | sh 2>/dev/null || echo 'Install opencode manually'"},
    "codex":        {"name": "Codex",         "cmd": "npm install -g @openai/codex 2>/dev/null || echo 'Install codex manually'"},
    "synthex-agent": {"name": "Synthex Agent", "cmd": "dnf install -y synthex-agent"},
    "open-webui":   {"name": "Open WebUI",     "cmd": "pip3 install open-webui 2>/dev/null || echo 'Install open-webui manually'"},
    # ── Utilities ──
    "syncthing":   {"name": "Syncthing",      "cmd": "dnf install -y syncthing"},
    "qbittorrent": {"name": "qBittorrent",    "cmd": "dnf install -y qbittorrent"},
    "gparted":     {"name": "GParted",        "cmd": "dnf install -y gparted"},
    "btop":        {"name": "Btop++",          "cmd": "dnf install -y btop"},
    "fastfetch":   {"name": "Fastfetch",       "cmd": "dnf install -y fastfetch"},
    "tmux":        {"name": "tmux",            "cmd": "dnf install -y tmux"},
    "neofetch":    {"name": "Neofetch",       "cmd": "dnf install -y neofetch"},
    "wireshark":   {"name": "Wireshark",      "cmd": "dnf install -y wireshark"},
    "veracrypt":   {"name": "VeraCrypt",      "cmd": "flatpak install -y flathub org.veracrypt.VeraCrypt"},
    "cryptsetup":  {"name": "Cryptsetup",     "cmd": "dnf install -y cryptsetup"},
    "mullvad":     {"name": "Mullvad VPN",    "cmd": "flatpak install -y flathub com.mullvad.MullvadBrowser 2>/dev/null || dnf config-manager --add-repo https://repository.mullvad.net/rpm/stable/mullvad.repo 2>/dev/null && dnf install -y mullvad-vpn"},
}


def install_app(app_id):
    """Install a single app from the registry.
    Returns True if installed successfully, False otherwise."""
    if app_id not in SYNTHEX_APPS_REGISTRY:
        warning(f"Unknown app: {app_id}")
        return False

    app_info = SYNTHEX_APPS_REGISTRY[app_id]
    debug(f"  Installing {app_info['name']} ({app_id})...")

    try:
        result = subprocess.run(
            ["sh", "-c", app_info["cmd"]],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            debug(f"  Installed {app_info['name']}")
            return True
        else:
            warning(f"  Failed to install {app_info['name']}: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        warning(f"  Timeout installing {app_info['name']}")
        return False
    except Exception as e:
        warning(f"  Error installing {app_info['name']}: {e}")
        return False


def install_apps(app_ids):
    """Install multiple apps. Returns count of successes."""
    installed = 0
    failed = 0
    for app_id in app_ids:
        if install_app(app_id):
            installed += 1
        else:
            failed += 1
    debug(f"Apps: {installed} installed, {failed} failed")
    return installed


def setup_desktop_profile(profile, theme, gpu_info):
    """Apply the desktop profile and theme settings."""
    profile_data = {
        "profile": profile,
        "theme": theme,
        "gpu": gpu_info.get("vendor", "unknown") if isinstance(gpu_info, dict) else str(gpu_info),
        "applied_at": "post-install",
    }
    with open(f"{SYNTHEX_STATE}/profile.json", "w") as f:
        json.dump(profile_data, f, indent=2)

    # Apply KDE Plasma layout
    desktop_cmd = shutil.which("synthex-desktop")
    if desktop_cmd:
        subprocess.run([desktop_cmd, "apply", profile], capture_output=True, timeout=30)
        debug(f"Applied profile: {profile}")
    else:
        debug("synthex-desktop not found, skipping profile apply")

    # Apply theme
    for theme_cmd_name in ["synthex-theme", f"{SYNTHEX_BIN}/synthex-theme"]:
        theme_cmd = shutil.which(theme_cmd_name) or theme_cmd_name
        if os.path.exists(theme_cmd):
            subprocess.run([theme_cmd, "apply", theme], capture_output=True, timeout=30)
            debug(f"Applied theme: {theme}")
            break
    else:
        debug("synthex-theme not found, skipping theme apply")


def install_package_groups(groups):
    """Install Synthex RPM package groups via dnf group install."""
    for group in groups:
        debug(f"Installing package group: {group}")
        try:
            subprocess.run(
                ["dnf", "group", "install", "-y", group],
                capture_output=True, timeout=600
            )
        except Exception as e:
            warning(f"Failed to install group {group}: {e}")


def enable_services():
    """Enable Synthex-specific systemd services."""
    services = [
        # Core daemons
        "synthex-system-daemon.service",
        "synthex-desktopd.service",
        "synthex-hwdaemon.service",
        "synthex-gpu-setupd.service",
        "synthex-stored.service",
        "synthex-ai-daemon.service",
        # System management
        "synthex-snapshot-manager.timer",
        "synthex-blueprint.timer",
        # OOBE
        "synthex-oobe.service",
        # Target
        "synthex.target",
    ]
    enabled = 0
    for svc in services:
        try:
            result = subprocess.run(
                ["systemctl", "enable", svc],
                capture_output=True, timeout=15
            )
            if result.returncode == 0:
                enabled += 1
        except Exception:
            pass
    debug(f"Enabled {enabled}/{len(services)} Synthex services")


def install_systemd_services():
    """Copy Synthex systemd unit files to the target system."""
    service_files = globmod.glob("/usr/share/synthex/systemd/*.service") + \
                    globmod.glob("/usr/share/synthex/systemd/*.timer")
    if not service_files:
        debug("No systemd unit files found in /usr/share/synthex/systemd/")
        return

    target_dir = "/etc/systemd/system"
    os.makedirs(target_dir, exist_ok=True)
    for svc_file in service_files:
        dest = os.path.join(target_dir, os.path.basename(svc_file))
        try:
            shutil.copy2(svc_file, dest)
            debug(f"Installed service: {os.path.basename(svc_file)}")
        except Exception as e:
            warning(f"Failed to install {svc_file}: {e}")


def setup_synthex_binaries():
    """Ensure all Synthex binaries are in PATH and executable."""
    bin_dir = "/usr/bin"
    for binary in globmod.glob("/usr/libexec/synthex/synthex-*"):
        dest = os.path.join(bin_dir, os.path.basename(binary))
        try:
            if not os.path.exists(dest):
                shutil.copy2(binary, dest)
                os.chmod(dest, 0o755)
                debug(f"Linked binary: {os.path.basename(binary)}")
        except Exception as e:
            warning(f"Failed to link {binary}: {e}")


def setup_flatpak():
    """Ensure Flatpak and Flathub are configured."""
    try:
        subprocess.run(
            ["flatpak", "remote-add", "--if-not-exists",
             "flathub", "https://flathub.org/repo/flathub.flatpakrepo"],
            capture_output=True, timeout=30
        )
        debug("Flatpak/Flathub configured")
    except Exception:
        debug("Flatpak not available, skipping")


def write_first_boot_marker():
    """Create marker file so OOBE runs on first boot."""
    try:
        os.makedirs(SYNTHEX_STATE, exist_ok=True)
        with open(f"{SYNTHEX_STATE}/.first-boot", "w") as f:
            f.write("pending")
        debug("First-boot marker created")
    except Exception as e:
        warning(f"Failed to create first-boot marker: {e}")


def run():
    """Main entry point — called by Calamares synthexpostinstall job module."""
    # Read selections from Calamares global storage
    profile = "focus"
    apps = []
    theme = "graphite"
    username = "synthex"
    gpu = {"vendor": "unknown"}

    try:
        profile = calamares.globalstorage.value("synthexProfile") or profile
        apps = calamares.globalstorage.value("synthexApps") or apps
        theme = calamares.globalstorage.value("synthexTheme") or theme
        username = calamares.globalstorage.value("username") or username
        gpu = calamares.globalstorage.value("synthexGpu") or gpu
    except Exception as e:
        debug(f"Could not read Calamares global storage: {e}")

    debug(f"Post-install: profile={profile}, apps={len(apps)}, theme={theme}, user={username}")

    # Ensure state directory exists
    os.makedirs(SYNTHEX_STATE, exist_ok=True)

    # 1. Write install manifest
    install_data = {
        "profile": profile,
        "theme": theme,
        "apps": apps,
        "username": username,
        "gpu": gpu if isinstance(gpu, dict) else {"vendor": str(gpu)},
        "package_groups": PROFILE_GROUPS.get(profile, ["synthex-core"]),
    }
    with open(f"{SYNTHEX_STATE}/install-profile.json", "w") as f:
        json.dump(install_data, f, indent=2)
    debug(f"Wrote install manifest to {SYNTHEX_STATE}/install-profile.json")

    # 2. Install profile package groups
    groups = PROFILE_GROUPS.get(profile, ["synthex-core"])
    install_package_groups(groups)

    # 3. Setup Flatpak
    setup_flatpak()

    # 4. Install user-selected apps
    if apps:
        debug(f"Installing {len(apps)} user-selected apps...")
        # Save for OOBE deferred install
        with open(f"{SYNTHEX_STATE}/oobe-apps.json", "w") as f:
            json.dump(apps, f)
        install_apps(apps)
    else:
        debug("No user-selected apps, skipping")

    # 5. Setup Synthex binaries
    setup_synthex_binaries()

    # 6. Install systemd services
    install_systemd_services()

    # 7. Apply desktop profile and theme
    setup_desktop_profile(profile, theme, gpu)

    # 8. Enable services
    enable_services()

    # 9. Write first-boot marker
    write_first_boot_marker()

    debug("Post-install configuration complete")
    return None
