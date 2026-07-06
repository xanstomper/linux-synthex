#!/bin/bash
# Solus systemd-boot Configuration Generator
# Alternative bootloader for UEFI systems — lighter, faster than GRUB
# Usage: solus-bootctl install

SOLUS_ENTRIES_DIR="/boot/loader/entries"
SOLUS_LOADER_CONF="/boot/loader/loader.conf"

install_systemd_boot() {
    echo "🔧 Installing systemd-boot..."
    bootctl install 2>/dev/null || {
        echo "⚠ systemd-boot already installed or UEFI not detected"
    }
    mkdir -p "$SOLUS_ENTRIES_DIR"
}

generate_loader_conf() {
    cat > "$SOLUS_LOADER_CONF" << 'LOADER'
# Solus systemd-boot configuration
default  solus
timeout  10
console-mode max
editor   yes
auto-entries 0
auto-firmware 1

# Solus Amber (#FFB300) themed
LOADER
    echo "✅ loader.conf written"
}

generate_solus_entry() {
    local kernel_version="$1"
    local entry_name="solus-${kernel_version}.conf"
    
    cat > "${SOLUS_ENTRIES_DIR}/${entry_name}" << ENTRY
# Solus Linux — Kernel ${kernel_version}
title   ☀️ Solus Linux (${kernel_version})
linux   /vmlinuz-${kernel_version}
initrd  /initramfs-${kernel_version}.img
options root=UUID=ROOT_UUID rw quiet splash rd.luks=1 rd.lvm=1 systemd.clock-usec=$(date +%s%N)
ENTRY
    
    # Create soft link as default
    ln -sf "${SOLUS_ENTRIES_DIR}/${entry_name}" "${SOLUS_ENTRIES_DIR}/solus.conf"
}

generate_recovery_entry() {
    local kernel_version="$1"
    
    cat > "${SOLUS_ENTRIES_DIR}/solus-recovery-${kernel_version}.conf" << ENTRY
# Solus Recovery — Kernel ${kernel_version}
title   🔧 Solus Recovery (${kernel_version})
linux   /vmlinuz-${kernel_version}
initrd  /initramfs-${kernel_version}.img
options root=UUID=ROOT_UUID rw single quiet splash systemd.unit=rescue.target
ENTRY
}

generate_snapshot_entry() {
    local snapshot_id="$1"
    local snapshot_desc="$2"
    
    cat > "${SOLUS_ENTRIES_DIR}/snapshot-${snapshot_id}.conf" << ENTRY
# Solus Snapshot Boot — #${snapshot_id} (${snapshot_desc})
title   📸 Snapshot #${snapshot_id} — ${snapshot_desc}
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash solus.snapshot=${snapshot_id}
ENTRY
}

generate_recovery_mode_entry() {
    cat > "${SOLUS_ENTRIES_DIR}/solus-recovery-main.conf" << ENTRY
# Solus Recovery Environment
title   🔧 Solus Recovery Environment
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash solus.recovery=1
ENTRY
}

generate_last_known_good() {
    cat > "${SOLUS_ENTRIES_DIR}/solus-last-good.conf" << ENTRY
# Solus Last Known Good
title   🔄 Solus — Last Known Good
linux   /vmlinuz-*
initrd  /initramfs-*.img
options root=UUID=ROOT_UUID rw quiet splash solus.recovery=rollback
ENTRY
}

install_theme() {
    # systemd-boot doesn't support custom themes directly,
    # but we can use the bootctl brand and splash
    mkdir -p /boot/loader/themes/solus
    
    # Create a simple splash configuration
    cat > /boot/loader/themes/solus/splash.txt << 'SPLASH'
☀️
Solus Linux
Illuminate Your Desktop
SPLASH
}

main() {
    echo "═══════════════════════════════════"
    echo "  Solus systemd-boot Setup"
    echo "═══════════════════════════════════"
    
    install_systemd_boot
    generate_loader_conf
    generate_recovery_mode_entry
    generate_last_known_good
    
    # Find latest kernel
    latest_kernel=$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -1)
    if [ -n "$latest_kernel" ]; then
        version="${latest_kernel#/boot/vmlinuz-}"
        generate_solus_entry "$version"
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
    echo "  1. ☀️ Solus Linux (default)"
    echo "  2. 🔧 Solus Recovery"
    echo "  3. 🔄 Solus — Last Known Good"
    echo "  4. 📸 Snapshot entries (one per snapshot)"
    echo "  5. ⚙ UEFI Firmware Settings"
    echo ""
    echo "To rebuild: solus-bootctl update"
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
            generate_solus_entry "$version"
            generate_recovery_entry "$version"
            echo "✅ Updated entries for kernel: $version"
        fi
        ;;
    *)
        echo "Usage: solus-bootctl <install|update>"
        ;;
esac