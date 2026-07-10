#!/usr/bin/env bash
# =============================================================================
# SynthOS — Apply Desktop Profile
# Called by OOBE (apply_profile) and Calamares post-install
# Usage: apply-profile.sh <profile>
# Profiles: classic gaming focus pro studio ai lite
# =============================================================================
set -euo pipefail

PROFILE="${1:-classic}"
LOG_FILE="${SYNTHEX_LOG:-/var/log/synthex-apply-profile.log}"
STATE_DIR="${SYNTHEX_STATE_DIR:-/var/lib/synthex}"
PLASMA_SCRIPT="/usr/bin/plasma-apply-lookandfeel"
LOOKANDFEELS_DIR="/usr/share/plasma/look-and-feel"
KWRITECONFIG="${KWRITECONFIG:-kwriteconfig6}"

log()  { echo "[profile] $*" | tee -a "$LOG_FILE" 2>/dev/null || echo "[profile] $*"; }
warn() { echo "[profile] WARN: $*" >&2; }

# ── Profile definitions ───────────────────────────────────────────────────────
declare -A PROFILE_LAF=(
    [classic]="org.synthos.desktop.classic"
    [gaming]="org.synthos.desktop.gaming"
    [focus]="org.synthos.desktop.focus"
    [pro]="org.synthos.desktop.pro"
    [studio]="org.synthos.desktop.studio"
    [ai]="org.synthos.desktop.ai"
    [lite]="org.synthos.desktop.lite"
)

declare -A PROFILE_COLORSCHEME=(
    [classic]="SynthexDarkAmber"
    [gaming]="SynthexGamingDark"
    [focus]="SynthexFocusDark"
    [pro]="SynthexProDark"
    [studio]="SynthexStudio"
    [ai]="SynthexAI"
    [lite]="SynthexLite"
)

declare -A PROFILE_WALLPAPER=(
    [classic]="/usr/share/wallpapers/SynthOS/synthex-classic.jpg"
    [gaming]="/usr/share/wallpapers/SynthOS/synthex-gaming.jpg"
    [focus]="/usr/share/wallpapers/SynthOS/synthex-focus.jpg"
    [pro]="/usr/share/wallpapers/SynthOS/synthex-pro.jpg"
    [studio]="/usr/share/wallpapers/SynthOS/synthex-studio.jpg"
    [ai]="/usr/share/wallpapers/SynthOS/synthex-ai.jpg"
    [lite]="/usr/share/wallpapers/SynthOS/synthex-lite.jpg"
)

declare -A PROFILE_TASKMANAGER=(
    [gaming]="org.kde.plasma.icontasks"
    [focus]="org.kde.plasma.taskmanager"
    [lite]="org.kde.plasma.taskmanager"
)

# ── Validate profile ──────────────────────────────────────────────────────────
if [[ -z "${PROFILE_LAF[$PROFILE]:-}" ]]; then
    warn "Unknown profile '$PROFILE'. Valid: classic gaming focus pro studio ai lite"
    warn "Falling back to 'classic'"
    PROFILE="classic"
fi

log "Applying profile: $PROFILE"
LAF="${PROFILE_LAF[$PROFILE]}"
COLORSCHEME="${PROFILE_COLORSCHEME[$PROFILE]}"
WALLPAPER="${PROFILE_WALLPAPER[$PROFILE]:-}"

# ── 1. Apply Plasma Look-and-Feel ────────────────────────────────────────────
if command -v "$PLASMA_SCRIPT" &>/dev/null; then
    if [ -d "$LOOKANDFEELS_DIR/$LAF" ]; then
        log "Applying look-and-feel: $LAF"
        "$PLASMA_SCRIPT" --apply "$LAF" &>/dev/null && log "  ✓ Look-and-feel applied" || warn "plasma-apply-lookandfeel failed"
    else
        warn "Look-and-feel package not found: $LOOKANDFEELS_DIR/$LAF"
    fi
else
    warn "plasma-apply-lookandfeel not available; using kwriteconfig6 fallback"
fi

# ── 2. Apply color scheme ─────────────────────────────────────────────────────
if command -v "$KWRITECONFIG" &>/dev/null; then
    "$KWRITECONFIG" --file kdeglobals \
        --group General --key ColorScheme "$COLORSCHEME" &>/dev/null || true
    log "  ✓ Color scheme: $COLORSCHEME"

    # Profile-specific tweaks
    case "$PROFILE" in
        gaming)
            # Disable compositor animations for max fps
            "$KWRITECONFIG" --file kwinrc \
                --group Compositing --key AnimationSpeed "0" &>/dev/null || true
            "$KWRITECONFIG" --file kwinrc \
                --group Compositing --key LatencyPolicy "Low" &>/dev/null || true
            log "  ✓ Gaming: compositor tweaks applied"
            ;;
        focus)
            # Enable auto-hide panel, no show desktop button
            "$KWRITECONFIG" --file plasmashellrc \
                --group "PlasmaViews" --key "panelVisibility" "1" &>/dev/null || true
            log "  ✓ Focus: panel auto-hide enabled"
            ;;
        lite)
            # Disable effects, reduce memory
            "$KWRITECONFIG" --file kwinrc \
                --group Compositing --key Enabled "false" &>/dev/null || true
            log "  ✓ Lite: compositor disabled"
            ;;
        pro)
            # Enable virtual desktops
            "$KWRITECONFIG" --file kwinrc \
                --group Desktops --key Number "4" &>/dev/null || true
            log "  ✓ Pro: 4 virtual desktops enabled"
            ;;
    esac
fi

# ── 3. Apply wallpaper ────────────────────────────────────────────────────────
if command -v plasma-apply-wallpaperimage &>/dev/null && [ -f "$WALLPAPER" ]; then
    plasma-apply-wallpaperimage "$WALLPAPER" &>/dev/null && \
        log "  ✓ Wallpaper: $WALLPAPER" || warn "wallpaper apply failed"
elif command -v "$KWRITECONFIG" &>/dev/null && [ -f "$WALLPAPER" ]; then
    # Fallback: write directly
    "$KWRITECONFIG" --file plasma-org.kde.plasma.desktop-appletsrc \
        --group "Containments" --key "wallpaper" "$WALLPAPER" &>/dev/null || true
    log "  ✓ Wallpaper set via kwriteconfig (fallback)"
fi

# ── 4. Profile-specific service management ────────────────────────────────────
case "$PROFILE" in
    gaming)
        systemctl --user enable --now synthex-gaming-mode.service &>/dev/null || true
        systemctl enable gamemode.service &>/dev/null || true
        ;;
    ai)
        systemctl enable ollama.service &>/dev/null || true
        systemctl --user enable --now synthex-ai-hub.service &>/dev/null || true
        ;;
    lite)
        # Disable heavy services
        systemctl --user disable --now kdeconnect.service &>/dev/null || true
        ;;
esac

# ── 5. Write state ────────────────────────────────────────────────────────────
mkdir -p "$STATE_DIR"
if [ -f "$STATE_DIR/install-profile.json" ]; then
    # Update existing
    python3 -c "
import json, sys
p = json.load(open('$STATE_DIR/install-profile.json'))
p['profile'] = '$PROFILE'
p['look_and_feel'] = '$LAF'
json.dump(p, open('$STATE_DIR/install-profile.json','w'), indent=2)
" 2>/dev/null || true
else
    echo "{\"profile\":\"$PROFILE\",\"look_and_feel\":\"$LAF\",\"version\":\"2026.10\"}" \
        > "$STATE_DIR/install-profile.json"
fi

# ── 6. Reload Plasma if running ───────────────────────────────────────────────
if pgrep -x plasmashell &>/dev/null; then
    kquitapp6 plasmashell &>/dev/null || killall plasmashell &>/dev/null || true
    sleep 1
    nohup plasmashell --replace &>/dev/null &
    log "  ✓ Plasma shell reloaded"
fi

log "Profile '$PROFILE' applied successfully ✓"
