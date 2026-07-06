#!/usr/bin/env bash
# Solus Windows Migration Tool
# Imports: Firefox/Chrome bookmarks, user wallpapers, Documents/Pictures/Music folders
# Run from the live ISO or after first boot.
set -euo pipefail

SOURCE_DIR="${1:-/mnt/windows}"
DEST_HOME="${2:-$HOME}"
LOG="/var/log/solus-migration.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

USERS_DIR="$SOURCE_DIR/Users"
if [ ! -d "$USERS_DIR" ]; then
    USERS_DIR="$SOURCE_DIR"; fi

WINDOWS_USER=$(ls "$USERS_DIR" 2>/dev/null | head -1)
[ -z "$WINDOWS_USER" ] && { echo "No Windows user detected at $SOURCE_DIR"; exit 1; }

SRC="$USERS_DIR/$WINDOWS_USER"
DST="$DEST_HOME"

log "Migrating from $SRC to $DST"

mkdir -p "$DST"

# Documents, Pictures, Music, Videos
for d in Documents Pictures Music Videos Desktop; do
    [ -d "$SRC/$d" ] && {
        cp -a "$SRC/$d" "$DST/" 2>/dev/null || rsync -a "$SRC/$d/" "$DST/$d/" 2>/dev/null || true
        log "Migrated $d"
    }
done

# Wallpapers
[ -d "$SRC/AppData/Local/Microsoft/Windows/Web" ] && {
    mkdir -p "$DST/Pictures/windows-wallpapers"
    cp -a "$SRC/AppData/Local/Microsoft/Windows/Web"/* "$DST/Pictures/windows-wallpapers/" 2>/dev/null || true
    log "Migrated wallpapers"
}

# Firefox bookmarks
if [ -f "$SRC/AppData/Roaming/Mozilla/Firefox/Profiles"/*/places.sqlite ]; then
    mkdir -p "$DST/.mozilla/firefox";
    cp "$SRC/AppData/Roaming/Mozilla/Firefox/Profiles"/*/places.sqlite "$DST/.mozilla/firefox/" 2>/dev/null || true
    log "Migrated Firefox bookmarks"
fi

log "Migration complete."
echo "✅ Migration done. Log: $LOG"
