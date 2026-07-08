#!/usr/bin/env bash
#===============================================================================
# Synthex Recovery — System Recovery Environment
#===============================================================================
# Recovery environment that runs from initramfs or boot menu.
# Provides a dialog-based menu for common recovery tasks.
#
# Usage:
#   synthex-recovery                    Interactive menu (dialog/whiptail)
#   synthex-recovery --menu            Force menu mode
#   synthex-recovery --check-boot      Check boot status (auto-fallback)
#   synthex-recovery --auto-fallback   Auto-select last working snapshot
#   synthex-recovery <option>          Run specific recovery action directly
#
# Options: restore-snapshot | fix-bootloader | repair-filesystem |
#          reinstall-kernel | reset-configs | rescue-shell | boot-previous
#
# This script is designed to run both:
#   - From initramfs (minimal environment)
#   - From a running system (for troubleshooting)
#===============================================================================

set -euo pipefail

# --- Constants ---------------------------------------------------------------
readonly SELF="synthex-recovery"
readonly CONFIG_FILE="/etc/synthex/recovery.conf"
readonly SNAPSHOT_DIR="/.snapshots"
readonly DEFAULT_KERNEL="kernel-core"
readonly BOOT_COUNTER_FILE="/var/lib/synthex/boot-counter"
readonly MAX_BOOT_FAILURES=2

# Text formatting (may not be available in initramfs)
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- Configuration Defaults -------------------------------------------------
RECOVERY_MENU="auto"       # auto | dialog | whiptail | text
ROOT_MOUNT="/mnt/root"
BOOT_MOUNT="/mnt/boot"
EFI_MOUNT="/mnt/boot/efi"
DEFAULT_SNAPPER_CONFIG="root"

# Load config if available
if [[ -f "${CONFIG_FILE}" ]]; then
    # shellcheck source=/dev/null
    source "${CONFIG_FILE}"
fi

# --- Helpers -----------------------------------------------------------------

log()    { echo -e "${GREEN}[RECOVERY]${NC} $*"; }
warn()   { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()    { error "$*"; exit 1; }

usage() {
    cat <<EOF
Synthex Recovery — System Recovery Environment

Usage: ${SELF} [option]

Options (menu):
  (no args)               Interactive recovery menu
  --menu                  Force interactive menu
  --auto-fallback         Auto-recover by selecting last snapshot

Options (direct):
  restore-snapshot        List and restore from a BTRFS snapshot
  fix-bootloader          Reinstall GRUB to ESP
  repair-filesystem       Run BTRFS check, scrub, balance
  reinstall-kernel        Reinstall kernel packages
  reset-configs           Restore default system configs
  rescue-shell            Drop to a rescue shell
  boot-previous           Boot the previous kernel/state

System:
  --check-boot            Check boot status (increment/check failure counter)
  --help, -h              Show this help message
EOF
}

find_dialog() {
    # Prefer dialog, fallback to whiptail, then plain text
    if command -v dialog &>/dev/null && [[ "${RECOVERY_MENU}" != "whiptail" ]]; then
        echo "dialog"
    elif command -v whiptail &>/dev/null; then
        echo "whiptail"
    else
        echo "text"
    fi
}

msgbox() {
    local title="$1" msg="$2"
    local d
    d="$(find_dialog)"
    case "${d}" in
        dialog)   dialog --title "${title}" --msgbox "${msg}" 10 60 ;;
        whiptail) whiptail --title "${title}" --msgbox "${msg}" 10 60 ;;
        *)        echo "=== ${title} ==="; echo "${msg}"; echo "" ;;
    esac
}

yesno() {
    local title="$1" msg="$2"
    local d
    d="$(find_dialog)"
    case "${d}" in
        dialog)   dialog --title "${title}" --yesno "${msg}" 10 60 ;;
        whiptail) whiptail --title "${title}" --yesno "${msg}" 10 60 ;;
        *)
            echo "=== ${title} ==="
            echo "${msg}"
            echo -n "Continue? [Y/n]: "
            read -r ans
            case "${ans}" in
                n|N|no) return 1 ;;
                *) return 0 ;;
            esac
            ;;
    esac
}

inputbox() {
    local title="$1" msg="$2" default="$3"
    local d result
    d="$(find_dialog)"
    case "${d}" in
        dialog)
            result="$(dialog --title "${title}" --inputbox "${msg}" 10 60 "${default}" 3>&1 1>&2 2>&3)"
            echo "${result}"
            ;;
        whiptail)
            result="$(whiptail --title "${title}" --inputbox "${msg}" 10 60 "${default}" 3>&1 1>&2 2>&3)"
            echo "${result}"
            ;;
        *)
            echo "=== ${title} ==="
            echo "${msg}"
            echo -n "[${default}]: "
            read -r ans
            echo "${ans:-${default}}"
            ;;
    esac
}

menu_choice() {
    local title="$1" msg="$2" height="$3" width="$4" menu_height="$5"
    shift 5
    local d result
    d="$(find_dialog)"
    case "${d}" in
        dialog)
            result="$(dialog --title "${title}" --menu "${msg}" "${height}" "${width}" "${menu_height}" "$@" 3>&1 1>&2 2>&3)"
            echo "${result}"
            ;;
        whiptail)
            result="$(whiptail --title "${title}" --menu "${msg}" "${height}" "${width}" "${menu_height}" "$@" 3>&1 1>&2 2>&3)"
            echo "${result}"
            ;;
        *)
            echo "=== ${title} ==="
            echo "${msg}"
            local i=1
            local items=()
            while [[ $# -gt 0 ]]; do
                local tag="$1"; shift
                local item="$1"; shift
                items+=("${tag}")
                echo "  ${tag}) ${item}"
            done
            echo -n "Selection: "
            read -r ans
            echo "${ans}"
            ;;
    esac
}

# --- Mounting Helpers --------------------------------------------------------

detect_root_device() {
    # Try to find the root device
    local root_dev=""
    root_dev="$(findmnt -n -o SOURCE / 2>/dev/null || echo "")"
    if [[ -z "${root_dev}" ]]; then
        # Try /dev/disk/by-label
        for label in synthex-root synthex_root Synthex ROOT; do
            if [[ -L "/dev/disk/by-label/${label}" ]]; then
                root_dev="$(readlink -f "/dev/disk/by-label/${label}")"
                break
            fi
        done
    fi
    echo "${root_dev:-/dev/mapper/synthex-root}"
}

mount_root() {
    local root_dev="$1"
    if ! mountpoint -q "${ROOT_MOUNT}" 2>/dev/null; then
        mkdir -p "${ROOT_MOUNT}"
        mount "${root_dev}" "${ROOT_MOUNT}" 2>/dev/null || {
            error "Cannot mount root at ${ROOT_MOUNT}"
            return 1
        }
    fi
    # Mount boot/efi if available
    if [[ -d "${ROOT_MOUNT}/boot" ]]; then
        local boot_dev
        boot_dev="$(findmnt -n -o SOURCE /boot 2>/dev/null || echo "")"
        if [[ -n "${boot_dev}" ]]; then
            mkdir -p "${BOOT_MOUNT}"
            mount "${boot_dev}" "${BOOT_MOUNT}" 2>/dev/null || true
        fi
    fi
    return 0
}

umount_all() {
    umount -R "${ROOT_MOUNT}" 2>/dev/null || true
}

# --- Recovery Actions --------------------------------------------------------

restore_snapshot() {
    log "=== Restore Snapshot ==="
    if ! command -v snapper &>/dev/null; then
        error "snapper is not available."
        return 1
    fi

    # List snapshots
    local snap_list
    snap_list="$(snapper -c "${DEFAULT_SNAPPER_CONFIG}" list 2>/dev/null || true)"
    if [[ -z "${snap_list}" ]]; then
        error "No snapshots found or snapper not configured."
        return 1
    fi

    echo "${snap_list}"

    local snap_num
    snap_num="$(inputbox "Restore Snapshot" "Enter snapshot number to restore to:" "")"
    if [[ -z "${snap_num}" ]]; then
        log "Cancelled."
        return 0
    fi

    if yesno "Confirm" "Restore to snapshot #${snap_num}? This will undo all changes since that snapshot."; then
        log "Restoring to snapshot #${snap_num}..."
        snapper -c "${DEFAULT_SNAPPER_CONFIG}" undochange "${snap_num}..0" 2>&1 || {
            error "Snapshot restoration failed."
            return 1
        }
        msgbox "Success" "System restored to snapshot #${snap_num}.\nA reboot is recommended."
        log "Snapshot #${snap_num} restored."
    fi
    return 0
}

fix_bootloader() {
    log "=== Fix Bootloader ==="
    local root_dev
    root_dev="$(detect_root_device)"
    mount_root "${root_dev}" || return 1

    # Find the EFI partition
    local efi_dev=""
    efi_dev="$(blkid -t PARTTYPE=c12a7328-f81f-11d2-ba4b-00a0c93ec93b -o device 2>/dev/null | head -1 || true)"
    if [[ -z "${efi_dev}" ]]; then
        # Common ESP partitions
        for dev in /dev/sda1 /dev/nvme0n1p1 /dev/vda1; do
            if [[ -b "${dev}" ]]; then
                local fstype
                fstype="$(blkid -s TYPE -o value "${dev}" 2>/dev/null || true)"
                if [[ "${fstype}" == "vfat" ]]; then
                    efi_dev="${dev}"
                    break
                fi
            fi
        done
    fi

    if [[ -z "${efi_dev}" ]]; then
        error "EFI system partition not found."
        umount_all
        return 1
    fi

    log "EFI partition: ${efi_dev}"
    mkdir -p "${EFI_MOUNT}"
    mount "${efi_dev}" "${EFI_MOUNT}" 2>/dev/null || {
        error "Cannot mount EFI partition."
        umount_all
        return 1
    }

    # Reinstall GRUB
    if command -v grub2-install &>/dev/null; then
        log "Installing GRUB to ESP..."
        # Chroot approach
        mount --bind /dev "${ROOT_MOUNT}/dev" 2>/dev/null || true
        mount --bind /proc "${ROOT_MOUNT}/proc" 2>/dev/null || true
        mount --bind /sys "${ROOT_MOUNT}/sys" 2>/dev/null || true

        chroot "${ROOT_MOUNT}" /bin/bash -c "
            grub2-install --target=x86_64-efi --efi-directory=${EFI_MOUNT} --bootloader-id=Synthex
            grub2-mkconfig -o /boot/grub2/grub.cfg
        " 2>&1 || {
            error "GRUB installation failed."
            umount_all
            return 1
        }

        umount "${ROOT_MOUNT}/dev" 2>/dev/null || true
        umount "${ROOT_MOUNT}/proc" 2>/dev/null || true
        umount "${ROOT_MOUNT}/sys" 2>/dev/null || true

        msgbox "Success" "Bootloader reinstalled successfully."
        log "Bootloader fixed."
    else
        error "grub2-install not found."
        umount_all
        return 1
    fi

    umount_all
    return 0
}

repair_filesystem() {
    log "=== Repair Filesystem ==="
    local root_dev
    root_dev="$(detect_root_device)"

    log "Running BTRFS check (read-only)..."
    btrfs check --readonly "${root_dev}" 2>&1 || {
        warn "BTRFS check reported issues."
    }

    log "Running BTRFS scrub..."
    if mountpoint -q /; then
        btrfs scrub start -B / 2>&1 || warn "Scrub reported errors."
    else
        mount_root "${root_dev}" || return 1
        btrfs scrub start -B "${ROOT_MOUNT}" 2>&1 || warn "Scrub reported errors."
        umount_all
    fi

    log "Running BTRFS balance..."
    if mountpoint -q /; then
        btrfs balance start -dusage=5 -musage=5 / 2>&1 || warn "Balance had issues."
    else
        mount_root "${root_dev}" || return 1
        btrfs balance start -dusage=5 -musage=5 "${ROOT_MOUNT}" 2>&1 || warn "Balance had issues."
        umount_all
    fi

    msgbox "Complete" "Filesystem repairs completed."
    return 0
}

reinstall_kernel() {
    log "=== Reinstall Kernel ==="
    local root_dev
    root_dev="$(detect_root_device)"
    mount_root "${root_dev}" || return 1

    # Mount needed filesystems for chroot
    mount --bind /dev "${ROOT_MOUNT}/dev" 2>/dev/null || true
    mount --bind /proc "${ROOT_MOUNT}/proc" 2>/dev/null || true
    mount --bind /sys "${ROOT_MOUNT}/sys" 2>/dev/null || true
    mount --bind /run "${ROOT_MOUNT}/run" 2>/dev/null || true

    log "Reinstalling kernel packages..."
    if chroot "${ROOT_MOUNT}" dnf reinstall -y kernel-core kernel-modules kernel-devel 2>&1; then
        log "Kernel reinstalled."
        chroot "${ROOT_MOUNT}" dracut --force 2>&1 || warn "dracut rebuild had issues."
        msgbox "Success" "Kernel packages reinstalled.\nInitramfs rebuilt."
    else
        error "Kernel reinstallation failed."
        umount_all
        return 1
    fi

    umount "${ROOT_MOUNT}/dev" "${ROOT_MOUNT}/proc" "${ROOT_MOUNT}/sys" "${ROOT_MOUNT}/run" 2>/dev/null || true
    umount_all
    return 0
}

reset_configs() {
    log "=== Reset Configs ==="
    local defaults_dir="/etc/synthex/defaults"

    if [[ ! -d "${defaults_dir}" ]]; then
        error "Default configs not found at ${defaults_dir}."
        return 1
    fi

    log "Restoring default configurations from ${defaults_dir}..."
    if yesno "Reset Configs" "Restore default system configurations?\nThis will overwrite modified configs in /etc."; then
        cp -r "${defaults_dir}"/* /etc/ 2>&1 || {
            error "Failed to restore configs."
            return 1
        }
        msgbox "Success" "Default configurations restored.\nSome services may need to be restarted."
        log "Configs restored."
    fi
    return 0
}

rescue_shell() {
    log "=== Rescue Shell ==="
    echo ""
    echo -e "${YELLOW}Entering rescue shell.${NC}"
    echo "Type 'exit' to return to the recovery menu."
    echo "Available: /usr/bin, /bin, mounted root at ${ROOT_MOUNT}"
    echo ""
    if [[ -n "${SHELL:-}" ]]; then
        "${SHELL}" || true
    else
        /bin/bash || /bin/sh || true
    fi
    log "Exited rescue shell."
    return 0
}

boot_previous() {
    log "=== Boot Previous State ==="
    # This action typically requires GRUB integration
    warn "Boot previous is managed via GRUB."
    echo "To boot a previous state:"
    echo "  1. Reboot the system."
    echo "  2. At the GRUB menu, select 'Advanced options for SynthOS'."
    echo "  3. Choose a previous kernel or snapshot entry."
    echo ""
    echo "If GRUB is not showing, use 'fix-bootloader' to restore it."
    msgbox "Info" "Reboot and use GRUB's advanced options\nto select a previous kernel or snapshot."
    return 0
}

auto_fallback() {
    log "=== Auto Fallback ==="
    log "Boot failure detected. Attempting automatic recovery..."

    # Find the latest snapshot
    if command -v snapper &>/dev/null; then
        local last_snapshot
        last_snapshot="$(snapper -c "${DEFAULT_SNAPPER_CONFIG}" list 2>/dev/null | tail -1 | awk '{print $1}')"
        if [[ -n "${last_snapshot}" && "${last_snapshot}" =~ ^[0-9]+$ ]]; then
            log "Rolling back to snapshot #${last_snapshot}..."
            snapper -c "${DEFAULT_SNAPPER_CONFIG}" undochange "${last_snapshot}..0" 2>&1 || {
                error "Auto-fallback failed."
                return 1
            }
            msgbox "Recovered" "System rolled back to snapshot #${last_snapshot}.\nRebooting..."
            log "Auto-fallback to snapshot #${last_snapshot} complete."
            return 0
        fi
    fi

    # Fallback: reinstall kernel
    warn "No snapshots found; reinstalling kernel..."
    reinstall_kernel

    return 0
}

# --- Boot Check (for initramfs hook) ----------------------------------------

check_boot() {
    local counter_file="${BOOT_COUNTER_FILE}"
    local counter=0

    if [[ -f "${counter_file}" ]]; then
        counter="$(cat "${counter_file}" 2>/dev/null || echo 0)"
    fi

    # Check if this is a clean boot (systemd boot-complete flag)
    if systemctl is-system-running --wait 2>/dev/null | grep -qE 'running|degraded'; then
        # Clean boot — reset counter
        echo 0 > "${counter_file}" 2>/dev/null || true
        return 0
    fi

    # Increment counter
    counter=$((counter + 1))
    echo "${counter}" > "${counter_file}" 2>/dev/null || true

    if [[ "${counter}" -ge "${MAX_BOOT_FAILURES}" ]]; then
        warn "Boot failure detected (${counter}/${MAX_BOOT_FAILURES}). Entering recovery..."
        auto_fallback
        return 1
    fi

    log "Boot count: ${counter}/${MAX_BOOT_FAILURES}"
    return 0
}

# --- Main Menu ---------------------------------------------------------------

show_menu() {
    local root_dev
    root_dev="$(detect_root_device)"

    while true; do
        local choice
        choice="$(menu_choice "Synthex Recovery Environment" \
            "System: ${root_dev}\nSelect a recovery action:" \
            18 65 8 \
            "restore-snapshot"  "Restore system from a BTRFS snapshot" \
            "fix-bootloader"    "Reinstall GRUB bootloader to ESP" \
            "repair-filesystem" "Check and repair BTRFS filesystem" \
            "reinstall-kernel"  "Reinstall kernel and rebuild initramfs" \
            "reset-configs"     "Restore default system configurations" \
            "rescue-shell"      "Drop to an emergency rescue shell" \
            "boot-previous"     "Instructions for booting previous state" \
            "quit"              "Exit recovery environment")"

        case "${choice}" in
            restore-snapshot)  restore_snapshot ;;
            fix-bootloader)    fix_bootloader ;;
            repair-filesystem) repair_filesystem ;;
            reinstall-kernel)  reinstall_kernel ;;
            reset-configs)     reset_configs ;;
            rescue-shell)      rescue_shell ;;
            boot-previous)     boot_previous ;;
            quit|"")           echo "Exiting recovery."; break ;;
            *)                 error "Invalid option." ;;
        esac

        echo ""
        echo -n "Press Enter to continue..."
        read -r dummy || true
        clear 2>/dev/null || true
    done
}

# --- Main Entry Point --------------------------------------------------------

main() {
    local cmd="${1:-menu}"

    case "${cmd}" in
        --menu|menu)
            show_menu
            ;;
        --auto-fallback|auto-fallback|autofallback)
            auto_fallback
            exit $?
            ;;
        --check-boot|check-boot|check_boot)
            check_boot
            exit $?
            ;;
        restore-snapshot|restore_snapshot)
            restore_snapshot
            exit $?
            ;;
        fix-bootloader|fix_bootloader)
            fix_bootloader
            exit $?
            ;;
        repair-filesystem|repair_filesystem)
            repair_filesystem
            exit $?
            ;;
        reinstall-kernel|reinstall_kernel)
            reinstall_kernel
            exit $?
            ;;
        reset-configs|reset_configs)
            reset_configs
            exit $?
            ;;
        rescue-shell|rescue_shell)
            rescue_shell
            exit $?
            ;;
        boot-previous|boot_previous)
            boot_previous
            exit $?
            ;;
        --help|-h|help)
            usage
            exit 0
            ;;
        *)
            # If we have a TTY, show menu, otherwise run check
            if [[ -t 0 ]]; then
                show_menu
            else
                check_boot
            fi
            ;;
    esac
}

main "$@"
