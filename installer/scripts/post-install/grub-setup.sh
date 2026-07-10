#!/usr/bin/env bash
# grub-setup.sh — Install SynthOS GRUB2 theme and configure bootloader
# Called by Calamares synthexpostinstall module during installation
# Also callable standalone: sudo ./grub-setup.sh [--target /mnt]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET="${1:-}"                 # e.g. /mnt for chroot install
GRUB_DEFAULT_FILE="/etc/default/grub"
GRUB_CFG_OUT="/boot/grub2/grub.cfg"
GRUB_THEMES_DIR="/boot/grub2/themes/synthex"
EFI_THEMES_DIR="/boot/efi/EFI/fedora/themes/synthex"
THEME_SRC="$REPO_ROOT/desktop/grub-theme"
SCRIPT_40="$REPO_ROOT/configs/grub/40_synthex"
LOG="/var/log/synthex-grub-setup.log"

# Prefix all paths with target if given
t() { echo "${TARGET}${1}"; }

info()  { echo "  [grub-setup] $*" | tee -a "$(t "$LOG")" 2>/dev/null || echo "  [grub-setup] $*"; }
warn()  { echo "  [grub-setup] ⚠ $*" >&2; }
die()   { echo "  [grub-setup] ✗ $*" >&2; exit 1; }

[[ $EUID -ne 0 ]] && die "Must run as root"

info "Starting SynthOS GRUB theme installation"
info "Target: ${TARGET:-/  (live system)}"

# ── 1. Copy theme files ───────────────────────────────────────────────────────
for dest in "$(t "$GRUB_THEMES_DIR")" "$(t "$EFI_THEMES_DIR")"; do
    if mkdir -p "$dest" 2>/dev/null; then
        cp -r "$THEME_SRC"/. "$dest/" 2>/dev/null || true
        info "Theme copied to $dest"
    fi
done

# Embed logo PNG at /boot/grub/synthex-logo.png for theme.txt reference
LOGO_SVG="$(t /usr/share/synthex-branding/synthex-logo.svg)"
LOGO_PNG="$(t /boot/grub/synthex-logo.png)"
[[ -f "$LOGO_SVG" ]] && {
    rsvg-convert -w 200 -h 200 "$LOGO_SVG" -o "$LOGO_PNG" 2>/dev/null && info "Logo PNG generated" || \
    convert "$LOGO_SVG" "$LOGO_PNG" 2>/dev/null && info "Logo PNG generated (ImageMagick)" || \
    warn "Could not convert SVG logo — GRUB will use text only"
}

# ── 2. Install 40_synthex custom entries script ───────────────────────────────
GRUB_D="$(t /etc/grub.d)"
if [[ -d "$GRUB_D" ]] && [[ -f "$SCRIPT_40" ]]; then
    install -m 0755 "$SCRIPT_40" "$GRUB_D/40_synthex"
    info "40_synthex installed to $GRUB_D"
fi

# ── 3. Patch /etc/default/grub ───────────────────────────────────────────────
GRUB_DEF="$(t "$GRUB_DEFAULT_FILE")"
if [[ -f "$GRUB_DEF" ]]; then
    # Determine theme path: EFI or legacy
    if [[ -d "$(t /sys/firmware/efi)" ]] || [[ -d "$(t /boot/efi)" ]]; then
        THEME_PATH="/boot/efi/EFI/fedora/themes/synthex/theme.txt"
    else
        THEME_PATH="/boot/grub2/themes/synthex/theme.txt"
    fi

    patch_grub_key() {
        local KEY="$1" VAL="$2"
        if grep -q "^${KEY}=" "$GRUB_DEF"; then
            sed -i "s|^${KEY}=.*|${KEY}=${VAL}|" "$GRUB_DEF"
        else
            echo "${KEY}=${VAL}" >> "$GRUB_DEF"
        fi
    }

    patch_grub_key GRUB_TIMEOUT               "5"
    patch_grub_key GRUB_TIMEOUT_STYLE         '"menu"'
    patch_grub_key GRUB_DISTRIBUTOR           '"SynthOS"'
    patch_grub_key GRUB_RECORDFAIL_TIMEOUT    "5"
    patch_grub_key GRUB_DISABLE_OS_PROBER     "false"
    patch_grub_key GRUB_DISABLE_SUBMENU       "false"
    patch_grub_key GRUB_DISABLE_RECOVERY      "false"
    patch_grub_key GRUB_TERMINAL_OUTPUT       '"gfxterm"'
    patch_grub_key GRUB_GFXPAYLOAD_LINUX      "keep"
    patch_grub_key GRUB_BACKGROUND            '""'
    patch_grub_key GRUB_THEME                 "\"$THEME_PATH\""

    # Ensure splash + quiet in cmdline
    if grep -q "^GRUB_CMDLINE_LINUX_DEFAULT=" "$GRUB_DEF"; then
        CURRENT=$(grep "^GRUB_CMDLINE_LINUX_DEFAULT=" "$GRUB_DEF" | cut -d= -f2- | tr -d '"')
        echo "$CURRENT" | grep -q "splash"  || CURRENT="$CURRENT splash"
        echo "$CURRENT" | grep -q "quiet"   || CURRENT="$CURRENT quiet"
        echo "$CURRENT" | grep -q "rhgb"    && CURRENT="${CURRENT/rhgb/}"
        patch_grub_key GRUB_CMDLINE_LINUX_DEFAULT "\"$(echo "$CURRENT" | xargs)\""
    else
        echo 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"' >> "$GRUB_DEF"
    fi

    # Custom header comment
    if ! grep -q "SynthOS GRUB Config" "$GRUB_DEF"; then
        sed -i '1s/^/# SynthOS GRUB Configuration — managed by synthex-grub-setup\n/' "$GRUB_DEF"
    fi

    info "/etc/default/grub patched"
fi

# ── 4. Generate GRUB config ───────────────────────────────────────────────────
GRUB_MKCONFIG="$(t /usr/sbin/grub2-mkconfig)"
[[ ! -f "$GRUB_MKCONFIG" ]] && GRUB_MKCONFIG="$(t /usr/sbin/grub-mkconfig)"
[[ ! -f "$GRUB_MKCONFIG" ]] && GRUB_MKCONFIG="$(command -v grub2-mkconfig 2>/dev/null || command -v grub-mkconfig 2>/dev/null || true)"

if [[ -n "$GRUB_MKCONFIG" ]] && [[ -x "$GRUB_MKCONFIG" ]]; then
    RDEV=""
    [[ -n "$TARGET" ]] && RDEV="--root-directory=$TARGET"
    "$GRUB_MKCONFIG" $RDEV -o "$(t "$GRUB_CFG_OUT")" 2>&1 | tail -8 | \
        sed 's/^/  /' | tee -a "$(t "$LOG")" 2>/dev/null || true
    info "grub.cfg generated at $(t "$GRUB_CFG_OUT")"
else
    warn "grub2-mkconfig not found — run manually: grub2-mkconfig -o $GRUB_CFG_OUT"
fi

info "✅ SynthOS GRUB theme installation complete"
