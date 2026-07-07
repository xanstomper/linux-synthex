#!/bin/bash
# Synthex systemd-boot Configuration Generator
# Alternative bootloader for UEFI systems — lighter, faster than GRUB
# Usage: synthex-bootctl install

SYNTHEX_ENTRIES_DIR="/boot/loader/entries"
SYNTHEX_LOADER_CONF="/boot/loader/loader.conf"

install_systemd_boot() {
    echo "🔧 Installing systemd-boot..."
    bootctl install 2>/dev/null || {
        echo "⚠ systemd-boot already installed or UEFI not detected"
    }
    mkdir -p "$SYNTHEX_ENTRIES_DIR"
}

generate_loader_conf() {
    cat > "$SYNTHEX_LOADER_CONF" << 'LOADER'
# Synthex systemd-boot configuration
default  synthex
timeout  10
console-mode max
editor   yes
auto-entries 0
auto-firmware 1

# Synthex Amber (#FFB300) themed
LOADER
    echo "✅ loader.conf written"
}

generate_synthex_entry() {
    local kernel_version="$1"
    local entry_name="synthex-${kernel_version}.conf"
    
    cat > "${SYNTHEX_ENTRIES_DIR}/${entry_name}" << ENTRY
# SynthOS — Kernel ${kernel_version}
title   ☀️ SynthOS (${kernel_version})
linux   /vmlinuz-${kernel_version}
initrd  /initramfs-${kernel_version}.img
options root=UUID=ROOT_UUID rw quiet splash rd.luks=1 rd.lvm=1 systemd.clock-usec=$(date +%s%N)
ENTRY
    
    # Create soft link as default
    ln -sf "${SYNTHEX_ENTRIES_DIR}/${entry_name}" "${SYNTHEX_ENTRIES_DIR}/synthex.conf"
}

generate_recovery_entry() {
    local kernel_version="$1"
    
    cat > "${SYNTHEX_ENTRIES_DIR}/synthex-recovery-${kernel_version}.conf" << ENTRY
# Synthex Recovery — Kernel ${kernel_version}
title   🔧 Synthex Recovery (${kernel_version})
linux   /vmlinuz-${kernel_version}
initrd  /initramfs-${kernel_version}.img
options root=UUID=ROOT_UUID rw single quiet splash systemd.unit=rescue.target
ENTRY
}

generate_snapshot_entry() {
    local snapshot_id="$1"
    local snapshot_desc="$2"
    
    cat > "${SYNTHEX_ENTRIES_DIR}/snapshot-${snapshot_id}.conf" << ENTRY
# Synthex Snapshot Boot — #${snapshot_id} (${snapshot_desc})
title   📸 Snapshot #${snapshot_id} — ${snapshot_desc}
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash synthex.snapshot=${snapshot_id}
ENTRY
}

generate_recovery_mode_entry() {
    cat > "${SYNTHEX_ENTRIES_DIR}/synthex-recovery-main.conf" << ENTRY
# Synthex Recovery Environment
title   🔧 Synthex Recovery Environment
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash synthex.recovery=1
ENTRY
}

generate_last_known_good() {
    cat > "${SYNTHEX_ENTRIES_DIR}/synthex-last-good.conf" << ENTRY
# Synthex Last Known Good
title   🔄 Synthex — Last Known Good
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash synthex.recovery=rollback
ENTRY
}

install_theme() {
    # systemd-boot doesn't support custom themes directly,
    # but we can use the bootctl brand and splash
    mkdir -p /boot/loader/themes/synthex
    
    # Create a simple splash configuration
    cat > /boot/loader/themes/synthex/splash.txt << 'SPLASH'
☀️
SynthOS
Illuminate Your Desktop
SPLASH
}

main() {
    echo "═══════════════════════════════════"
    echo "  Synthex systemd-boot Setup"
    echo "═══════════════════════════════════"
    
    install_systemd_boot
    generate_loader_conf
    generate_recovery_mode_entry
    generate_last_known_good
    
    # Find latest kernel
    latest_kernel=$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -1)
    if [ -n "$latest_kernel" ]; then
        version="${latest_kernel#/boot/vmlinuz-}"
        generate_synthex_entry "$version"
        generate_recovery_entry "$version"
        echo "✅ Created entries for kernel: $version"
    else
        echo "⚠ No kernel found in /boot/"
    fi
    
    install_theme
    
    echo ""
    echo "✅ systemd-boot configuration complete!"
    echo ""
    echo "Boot entries:"
    echo "  1. ☀️ SynthOS (default)"
    echo "  2. 🔧 Synthex Recovery"
    echo "  3. 🔄 Synthex — Last Known Good"
    echo "  4. 📸 Snapshot entries (one per snapshot)"
    echo "  5. ⚙ UEFI Firmware Settings"
    echo ""
    echo "To rebuild: synthex-bootctl update"
}

case "${1:-}" in
    install)
        main
        ;;
    update)
        # Regenerate kernel entries
        latest_kernel=$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -1)
        if [ -n "$latest_kernel" ]; then
            version="${latest_kernel#/boot/vmlinuz-}"
            generate_synthex_entry "$version"
            generate_recovery_entry "$version"
            echo "✅ Updated entries for kernel: $version"
        fi
        ;;
    *)
        echo "Usage: synthex-bootctl <install|update>"
        ;;
esac