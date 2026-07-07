#!/bin/bash
# Synthex Dracut Module — Recovery + Boot Validation
# Installs into initramfs to provide:
#   1. Boot failure detection with auto-fallback
#   2. Snapshot rollback from initramfs
#   3. Recovery environment access
#
# Install: dracut --force --add synthex-recovery
# Remove:  dracut --force --omit synthex-recovery

MODULE_NAME="99synthex-recovery"
DRACUT_MODULES_DIR="/usr/lib/dracut/modules.d/${MODULE_NAME}"

install_module() {
    echo "📦 Installing Synthex Recovery dracut module..."
    mkdir -p "$DRACUT_MODULES_DIR"
    
    # Module setup script
    cat > "${DRACUT_MODULES_DIR}/module-setup.sh" << 'MODSETUP'
#!/bin/bash

check() {
    require_binaries bash mount grep sed btrfs || return 1
    return 0
}

depends() {
    echo "bash systemd"
    return 0
}

install() {
    # Install recovery scripts
    inst_script "$moddir/synthex-recovery-init.sh" /usr/bin/synthex-recovery-init
    inst_hook cmdline 90 "$moddir/parse-synthex-options.sh"
    
    # Install tools
    inst_binary btrfs
    inst_binary snapper
    inst_binary grub2-editenv
    
    # Install systemd services
    inst_simple "$moddir/synthex-boot-check.service" \
        "$systemdsystemunitdir/synthex-boot-check.service"
    inst_simple "$moddir/synthex-recovery-shell.service" \
        "$systemdsystemunitdir/synthex-recovery-shell.service"
    
    # Enable services
    systemctl -q --root "$initdir" enable synthex-boot-check
}

installkernel() {
    hostonly='' instmods btrfs ext4 xfs vfat nls_cp437 \
        nls_iso8859-1 ahci nvme usb-storage
}
MODSETUP
    chmod +x "${DRACUT_MODULES_DIR}/module-setup.sh"
    
    # Kernel command line parser
    cat > "${DRACUT_MODULES_DIR}/parse-synthex-options.sh" << 'PARSE'
#!/bin/bash

# Parse Synthex-specific kernel parameters
for param in $(cat /proc/cmdline); do
    case "$param" in
        synthex.recovery=1)
            echo "🔧 Synthex Recovery Mode requested"
            > /tmp/synthex-recovery-mode
            ;;
        synthex.recovery=rollback)
            echo "🔄 Synthex Rollback requested"
            > /tmp/synthex-rollback-mode
            ;;
        synthex.recovery=list)
            echo "📸 Synthex Snapshot List requested"
            > /tmp/synthex-snapshot-list
            ;;
        synthex.snapshot=*)
            SNAPSHOT_ID="${param#synthex.snapshot=}"
            echo "$SNAPSHOT_ID" > /tmp/synthex-target-snapshot
            echo "📸 Booting snapshot #$SNAPSHOT_ID"
            ;;
    esac
done
PARSE
    chmod +x "${DRACUT_MODULES_DIR}/parse-synthex-options.sh"
    
    # Main recovery init script
    cat > "${DRACUT_MODULES_DIR}/synthex-recovery-init.sh" << 'RECOVERY'
#!/bin/bash
# Synthex Recovery Init — runs from initramfs

RECOVERY_FLAG="/tmp/synthex-recovery-mode"
ROLLBACK_FLAG="/tmp/synthex-rollback-mode"
SNAPSHOT_FLAG="/tmp/synthex-snapshot-list"
TARGET_SNAPSHOT="/tmp/synthex-target-snapshot"
FAIL_COUNTER="/var/lib/synthex/boot-failures"
MAX_FAILURES=3

log() {
    echo "[synthex-recovery] $*" >&2
}

check_boot_failures() {
    mkdir -p "$(dirname "$FAIL_COUNTER")" 2>/dev/null
    
    local count=0
    if [ -f "$FAIL_COUNTER" ]; then
        count=$(cat "$FAIL_COUNTER" 2>/dev/null || echo 0)
    fi
    
    log "Boot attempt #$((count + 1))"
    
    if [ "$count" -ge "$((MAX_FAILURES - 1))" ]; then
        log "⚠ $MAX_FAILURES consecutive boot failures detected!"
        log "🔄 Auto-rolling back to last working snapshot..."
        
        # Find latest snapshot before failures started
        if command -v snapper &>/dev/null; then
            LATEST_SNAPSHOT=$(snapper -c root list 2>/dev/null | tail -1 | awk '{print $1}')
            if [ -n "$LATEST_SNAPSHOT" ] && [ "$LATEST_SNAPSHOT" != "0" ]; then
                log "📸 Rolling back to snapshot #$LATEST_SNAPSHOT..."
                snapper -c root undochange "${LATEST_SNAPSHOT}..0" 2>/dev/null || true
            fi
        fi
        
        # Reset counter
        echo 0 > "$FAIL_COUNTER"
    else
        echo $((count + 1)) > "$FAIL_COUNTER"
    fi
}

handle_recovery_mode() {
    log "═══════════════════════════════════"
    log "  Synthex Recovery Environment"
    log "═══════════════════════════════════"
    log ""
    log "Available options:"
    log "  1. mount_root — Mount filesystem"
    log "  2. fix_bootloader — Reinstall GRUB/systemd-boot"
    log "  3. restore_snapshot — Snapper rollback"
    log "  4. repair_fs — BTRFS check+repair"
    log "  5. rescue_shell — Emergency shell"
    log ""
    
    # Auto-mount root
    local root_dev=""
    for dev in /dev/nvme0n1* /dev/sda* /dev/vda*; do
        [ -b "$dev" ] || continue
        if blkid "$dev" 2>/dev/null | grep -q 'btrfs\|ext4'; then
            root_dev="$dev"
            break
        fi
    done
    
    if [ -n "$root_dev" ]; then
        log "📁 Found root device: $root_dev"
        mkdir -p /mnt/root
        mount -o subvol=@ "$root_dev" /mnt/root 2>/dev/null || \
        mount "$root_dev" /mnt/root 2>/dev/null || \
        log "⚠ Could not mount root filesystem"
    fi
    
    # Drop to emergency shell for interactive recovery
    exec /bin/bash
}

handle_rollback() {
    log "🔄 Performing automatic rollback..."
    if command -v snapper &>/dev/null; then
        # Mount root filesystem for snapper access
        mount_root
        
        LATEST=$(snapper -c root list 2>/dev/null | tail -1 | awk '{print $1}')
        if [ -n "$LATEST" ] && [ "$LATEST" != "0" ]; then
            snapper -c root undochange "${LATEST}..0"
            log "✅ Rolled back to snapshot #$LATEST"
        fi
    fi
}

mount_root() {
    for dev in /dev/nvme0n1* /dev/sda* /dev/vda*; do
        [ -b "$dev" ] || continue
        if blkid "$dev" 2>/dev/null | grep -q 'btrfs'; then
            mount -o subvol=@ "$dev" /mnt/root 2>/dev/null || true
            mount -o subvol=@home "$dev" /mnt/root/home 2>/dev/null || true
            return 0
        fi
    done
    return 1
}

# ─── Main ──────────────────────────────────────────────────────────

# Handle kernel parameters
if [ -f "$RECOVERY_FLAG" ]; then
    handle_recovery_mode
fi

if [ -f "$ROLLBACK_FLAG" ]; then
    handle_rollback
    exit 0
fi

if [ -f "$SNAPSHOT_FLAG" ]; then
    log "Available snapshots:"
    mount_root 2>/dev/null
    snapper -c root list 2>/dev/null || log "No snapshots available"
    exec /bin/bash
fi

if [ -f "$TARGET_SNAPSHOT" ]; then
    TARGET=$(cat "$TARGET_SNAPSHOT")
    log "📸 Booting snapshot #$TARGET..."
    mount_root 2>/dev/null
    snapper -c root undochange "${TARGET}..0" 2>/dev/null || true
fi

# Normal boot — check for failures
check_boot_failures
exit 0
RECOVERY
    chmod +x "${DRACUT_MODULES_DIR}/synthex-recovery-init.sh"
    
    # Boot check systemd service
    cat > "${DRACUT_MODULES_DIR}/synthex-boot-check.service" << 'SERVICE'
[Unit]
Description=Synthex Boot Failure Check
Documentation=https://synthex-linux.org/docs/recovery
DefaultDependencies=no
Wants=initrd-root-device.target
After=initrd-root-device.target
Before=initrd.target

[Service]
Type=oneshot
ExecStart=/usr/bin/synthex-recovery-init
RemainAfterExit=yes
StandardOutput=journal+console

[Install]
WantedBy=initrd.target
SERVICE

    # Recovery shell service
    cat > "${DRACUT_MODULES_DIR}/synthex-recovery-shell.service" << 'SHELL'
[Unit]
Description=Synthex Recovery Shell
Documentation=https://synthex-linux.org/docs/recovery
DefaultDependencies=no
After=systemd-vconsole-setup.service
Wants=systemd-vconsole-setup.service

[Service]
Type=idle
ExecStart=/bin/sh -c 'echo "Synthex Recovery — type exit to continue boot"; exec /bin/bash'
StandardInput=tty-force
StandardOutput=journal+console
StandardError=journal+console
SHELL
    
    echo "✅ Synthex Recovery dracut module installed"
}

enable_module() {
    echo "🔧 Enabling Synthex Recovery in initramfs..."
    dracut --force --add synthex-recovery
    echo "✅ Initramfs rebuilt with Synthex Recovery module"
}

disable_module() {
    echo "🔧 Disabling Synthex Recovery from initramfs..."
    dracut --force --omit synthex-recovery
    echo "✅ Initramfs rebuilt without Synthex Recovery module"
}

main() {
    case "${1:-install}" in
        install)
            install_module
            enable_module
            ;;
        enable)
            enable_module
            ;;
        disable)
            disable_module
            ;;
        *)
            echo "Usage: $0 <install|enable|disable>"
            echo ""
            echo "  install  — Install module and rebuild initramfs"
            echo "  enable   — Rebuild initramfs with module"
            echo "  disable  — Rebuild initramfs without module"
            ;;
    esac
}

main "$@"
