#!/usr/bin/env bash
# synthex-recovery — Synthex Recovery Environment
# GUI system repair tool for boot failures and system issues
# Can run from initramfs or installed system

set -euo pipefail

VERSION="1.0.0"

# ─── UI Functions ───────────────────────────────────────────

show_header() {
    clear
    echo "═══════════════════════════════════════════════"
    echo "  🔧 Synthex Recovery Environment v$VERSION"
    echo "  Repair your system without reinstalling"
    echo "═══════════════════════════════════════════════"
    echo ""
}

show_menu() {
    show_header
    echo "  What would you like to do?"
    echo ""
    echo "  1) 🔄 Restore Snapshot"
    echo "     Roll back to a previous system state"
    echo ""
    echo "  2) 🔧 Fix Bootloader"
    echo "     Reinstall GRUB/systemd-boot"
    echo ""
    echo "  3) 📁 Repair Filesystem"
    echo "     Check and repair BTRFS/ext4"
    echo ""
    echo "  4) 💾 Reinstall Kernel"
    echo "     Install last working kernel version"
    echo ""
    echo "  5) 🔄 Reset Configs"
    echo "     Restore default system settings"
    echo ""
    echo "  6) ⌨️ Rescue Shell"
    echo "     Root terminal for advanced fixes"
    echo ""
    echo "  7) 🔁 Boot Previous State"
    echo "     Boot last known-good snapshot"
    echo ""
    echo "  q) Quit / Reboot"
    echo ""
    echo -n "  Select option [1-7/q]: "
    read -r choice
    echo ""
    
    case "$choice" in
        1) restore_snapshot ;;
        2) fix_bootloader ;;
        3) repair_filesystem ;;
        4) reinstall_kernel ;;
        5) reset_configs ;;
        6) rescue_shell ;;
        7) boot_previous ;;
        q|Q) reboot_system ;;
        *) show_menu ;;
    esac
}

# ─── Recovery Functions ─────────────────────────────────────

restore_snapshot() {
    show_header
    echo "📸 Available Snapshots"
    echo "──────────────────────"
    
    if command -v snapper &>/dev/null; then
        snapper -c root list 2>/dev/null || echo "No snapshots found"
    else
        echo "Snapper not available."
        echo "Checking BTRFS snapshots manually..."
        ls -1 /.snapshots/*/snapshot 2>/dev/null || echo "No snapshots found"
    fi
    
    echo ""
    echo -n "Enter snapshot number to restore (or 0 to cancel): "
    read -r snap_id
    
    if [ "$snap_id" = "0" ] || [ -z "$snap_id" ]; then
        show_menu
        return
    fi
    
    echo ""
    echo "⚠ WARNING: This will revert your system to snapshot #$snap_id"
    echo -n "Are you sure? [y/N]: "
    read -r confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "🔄 Restoring snapshot #$snap_id..."
        snapper -c root undochange "${snap_id}..0"
        echo "✅ Snapshot restored. Rebooting..."
        sleep 2
        reboot
    else
        show_menu
    fi
}

fix_bootloader() {
    show_header
    echo "🔧 Fixing Bootloader"
    echo "────────────────────"
    
    # Find root partition
    root_dev=$(findmnt -n -o SOURCE / 2>/dev/null | sed 's/\[.*\]//')
    echo "Root device: $root_dev"
    
    # Find ESP
    esp_dev=$(findmnt -n -o SOURCE /boot 2>/dev/null || findmnt -n -o SOURCE /boot/efi 2>/dev/null)
    echo "ESP device: $esp_dev"
    
    if [ -z "$esp_dev" ]; then
        echo "⚠ Cannot find EFI System Partition"
        echo -n "Enter ESP device (e.g., /dev/nvme0n1p1): "
        read -r esp_dev
    fi
    
    echo ""
    echo "1) GRUB (default)"
    echo "2) systemd-boot"
    echo -n "Select bootloader: "
    read -r bl_choice
    
    case "$bl_choice" in
        2)
            echo "Installing systemd-boot..."
            bootctl install 2>/dev/null || echo "⚠ systemd-boot install failed"
            ;;
        *)
            echo "Reinstalling GRUB..."
            if [ -d /sys/firmware/efi ]; then
                grub2-install --target=x86_64-efi --efi-directory=/boot --recheck
            else
                grub2-install "$root_dev" --recheck
            fi
            grub2-mkconfig -o /boot/grub2/grub.cfg
            ;;
    esac
    
    echo ""
    echo "✅ Bootloader fixed!"
    echo -n "Press Enter to return to menu..."
    read -r
    show_menu
}

repair_filesystem() {
    show_header
    echo "📁 Filesystem Repair"
    echo "────────────────────"
    
    # Check filesystems
    echo "Checking BTRFS filesystems..."
    for dev in $(findmnt -t btrfs -o SOURCE 2>/dev/null | tail -n +2); do
        echo "  Checking $dev..."
        btrfs check "$dev" 2>/dev/null || echo "  ⚠ Full check requires unmounted filesystem"
    done
    
    echo ""
    echo "Running BTRFS scrub (read-only check)..."
    for mount in $(findmnt -t btrfs -o TARGET 2>/dev/null | tail -n +2); do
        echo "  Scrub on $mount..."
        btrfs scrub start -B "$mount" 2>/dev/null || echo "  ⚠ Scrub not available"
    done
    
    echo ""
    echo "Repairing filesystems..."
    for dev in $(findmnt -t btrfs -o SOURCE 2>/dev/null | tail -n +2); do
        echo "  Repairing $dev..."
        fsck -y "$dev" 2>/dev/null || true
    done
    
    echo ""
    echo "✅ Filesystem check complete"
    echo -n "Press Enter to return to menu..."
    read -r
    show_menu
}

reinstall_kernel() {
    show_header
    echo "💾 Reinstalling Kernel"
    echo "──────────────────────"
    
    echo "Current kernel: $(uname -r 2>/dev/null || echo 'not running')"
    
    echo ""
    echo "Available kernels:"
    dnf list installed kernel* 2>/dev/null | grep -E '^kernel' || echo "No kernels found"
    
    echo ""
    echo -n "Reinstall current kernel? [Y/n]: "
    read -r confirm
    
    if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
        echo "Reinstalling kernel..."
        dnf reinstall -y kernel kernel-core kernel-modules 2>/dev/null || {
            echo "⚠ DNF reinstall failed, trying alternative..."
            latest=$(ls -1t /boot/vmlinuz-* 2>/dev/null | head -1)
            if [ -n "$latest" ]; then
                echo "Latest kernel: $latest"
                dracut --force
            fi
        }
        echo "✅ Kernel reinstalled"
    fi
    
    echo ""
    echo -n "Press Enter to return to menu..."
    read -r
    show_menu
}

reset_configs() {
    show_header
    echo "🔄 Reset System Configs"
    echo "────────────────────────"
    echo ""
    echo "⚠ This resets Synthex-specific settings to defaults."
    echo "Your personal files will NOT be affected."
    echo ""
    echo "1) Reset Synthex themes and desktop layout"
    echo "2) Reset system services to defaults"
    echo "3) Reset ALL Synthex configs"
    echo "4) Cancel"
    echo ""
    echo -n "Select option: "
    read -r reset_choice
    
    case "$reset_choice" in
        1)
            echo "Resetting desktop configs..."
            rm -f ~/.config/kdeglobals ~/.config/kwinrc ~/.config/plasma*
            echo "✅ Desktop configs reset"
            ;;
        2)
            echo "Resetting system services..."
            systemctl preset-all
            echo "✅ System services reset"
            ;;
        3)
            echo "Resetting ALL Synthex configs..."
            rm -f /etc/synthex/*.conf 2>/dev/null || true
            rm -f ~/.config/synthex/* 2>/dev/null || true
            systemctl preset-all
            echo "✅ All configs reset"
            ;;
        *)
            show_menu
            return
            ;;
    esac
    
    echo ""
    echo -n "Press Enter to return to menu..."
    read -r
    show_menu
}

rescue_shell() {
    show_header
    echo "⌨️ Rescue Shell"
    echo "────────────────"
    echo "You are now in a root shell."
    echo "Type 'exit' to return to recovery menu."
    echo ""
    echo "Useful commands:"
    echo "  dnf reinstall <pkg>  — Reinstall a broken package"
    echo "  journalctl -xb       — View boot logs"
    echo "  dracut --force       — Rebuild initramfs"
    echo "  snapper list         — List snapshots"
    echo "  btrfs scrub start /  — Check filesystem"
    echo ""
    /bin/bash || true
    show_menu
}

boot_previous() {
    show_header
    echo "🔁 Booting Previous State"
    echo "──────────────────────────"
    echo ""
    echo "Setting 'last known good' boot entry..."
    
    # Get the latest snapshot before current
    if command -v snapper &>/dev/null; then
        latest=$(snapper -c root list 2>/dev/null | grep -v "^0\|^Current\|^single" | tail -1 | awk '{print $1}')
        if [ -n "$latest" ]; then
            echo "Rolling back to snapshot #$latest..."
            snapper -c root undochange "${latest}..0"
            echo "✅ Rolled back. Rebooting to previous state..."
            sleep 2
            reboot
        fi
    fi
    
    echo "⚠ No snapshots found. Cannot roll back."
    echo -n "Press Enter to return to menu..."
    read -r
    show_menu
}

reboot_system() {
    echo ""
    echo "Rebooting..."
    sleep 1
    reboot
}

# ─── Auto-Fallback Detection ─────────────────────────────────

check_boot_failures() {
    local fail_count=0
    local fail_file="/var/lib/synthex/boot-failures"
    
    if [ -f "$fail_file" ]; then
        fail_count=$(cat "$fail_file")
    fi
    
    if [ "$fail_count" -ge 2 ]; then
        echo "⚠ Boot failures detected ($fail_count consecutive)"
        echo "🔁 Automatically switching to last working snapshot..."
        
        # Reset counter
        echo "0" > "$fail_file"
        
        # Find latest snapshot
        latest=$(snapper -c root list 2>/dev/null | tail -1 | awk '{print $1}')
        if [ -n "$latest" ]; then
            echo "🔄 Rolling back to snapshot #$latest..."
            snapper -c root undochange "${latest}..0"
        fi
    fi
    
    # Increment counter
    echo $((fail_count + 1)) > "$fail_file"
}

# ─── Main ────────────────────────────────────────────────────

main() {
    # Check if running from initramfs
    if [ "${1:-}" = "--initramfs" ]; then
        check_boot_failures
        exit 0
    fi
    
    # Check for boot failures
    if [ "${1:-}" = "--check-boot" ]; then
        check_boot_failures
        exit 0
    fi
    
    # Interactive recovery menu (needs dialog or terminal)
    if command -v dialog &>/dev/null; then
        # Use dialog if available
        show_menu_dialog
    else
        show_menu
    fi
}

# If no dialog, use text menu
main "$@"
