#!/usr/bin/env bash
#===============================================================================
# Synthex Recovery — Initramfs Hook (dracut module)
#===============================================================================
# Installs the synthex-recovery system into the initramfs.
#
# This dracut module:
#   1. Copies recovery.sh and its dependencies into the initramfs
#   2. Adds recovery entries to GRUB (via dracut's grub2 integration)
#   3. Reads configuration from /etc/synthex/recovery.conf
#   4. Triggers auto-fallback on boot failure detection
#
# Installation:
#   sudo cp synthex-recovery-hook.sh /usr/lib/dracut/modules.d/99synthex-recovery/
#   sudo chmod +x /usr/lib/dracut/modules.d/99synthex-recovery/module-setup.sh
#   sudo dracut --force
#
# Configuration: /etc/synthex/recovery.conf
#   RECOVERY_ENABLED=true
#   AUTO_FALLBACK=true
#   MAX_BOOT_FAILURES=2
#   RECOVERY_MENU_KEY=f8
#===============================================================================

if ! [[ ${dracutbasedir} ]]; then
    # shellcheck disable=SC1090
    [[ -d /usr/lib/dracut ]] && . /usr/lib/dracut/dracut-functions.sh 2>/dev/null || true
fi

# --- Module Metadata ---------------------------------------------------------
check() {
    # Include this module by default
    return 255
}

depends() {
    echo bash
    return 0
}

installkernel() {
    # No special kernel modules needed
    return 0
}

install() {
    local recovery_script="/usr/bin/synthex-recovery"
    local recovery_conf="/etc/synthex/recovery.conf"
    local recovery_data="/usr/share/synthex/recovery"

    # Install the recovery script
    if [[ -f "${recovery_script}" ]]; then
        inst_simple "${recovery_script}" /usr/bin/synthex-recovery
        dracut_instmods btrfs
    else
        dwarn "synthex-recovery not found at ${recovery_script}. Skipping."
    fi

    # Install configuration
    if [[ -f "${recovery_conf}" ]]; then
        inst_simple "${recovery_conf}" /etc/synthex/recovery.conf
    else
        # Create default config
        inst_simple /dev/null /etc/synthex/recovery.conf
        echo "RECOVERY_ENABLED=true" >> "${initdir}/etc/synthex/recovery.conf"
        echo "AUTO_FALLBACK=true" >> "${initdir}/etc/synthex/recovery.conf"
        echo "MAX_BOOT_FAILURES=2" >> "${initdir}/etc/synthex/recovery.conf"
    fi

    # Install dependencies needed by recovery.sh
    # snapper for snapshot management
    if command -v snapper &>/dev/null; then
        inst_binary snapper
        # Inst libraries needed by snapper
        inst_libdir_file "libsnapper*" "libboost*" "libjson*" "libreiser*" 2>/dev/null || true
    fi

    # btrfs tools
    if command -v btrfs &>/dev/null; then
        inst_binary btrfs
    fi

    # dialog or whiptail for menu UI
    if command -v dialog &>/dev/null; then
        inst_binary dialog
        inst_libdir_file "libdialog*" "libcdk*" 2>/dev/null || true
    elif command -v whiptail &>/dev/null; then
        inst_binary whiptail
        inst_libdir_file "libnewt*" "libslang*" "libpopt*" 2>/dev/null || true
    fi

    # core utilities used by recovery
    for cmd in cp mv rm mount umount mkdir grep sed awk cut sort head tail cat echo lsblk blkid findmnt dracut dnf chroot; do
        command -v "${cmd}" &>/dev/null && inst_binary "${cmd}" || true
    done

    # Essential libraries
    inst_libdir_file "libc.so.*" "libm.so.*" "libdl.so.*" "libpthread.so.*" "librt.so.*" "libcap.so.*" 2>/dev/null || true

    # Install GRUB helpers
    for cmd in grub2-install grub2-mkconfig grub2-set-default; do
        command -v "${cmd}" &>/dev/null && inst_binary "${cmd}" || true
    done

    # Install recovery data files (if any)
    if [[ -d "${recovery_data}" ]]; then
        for f in "${recovery_data}"/*; do
            [[ -f "${f}" ]] && inst_simple "${f}" "/usr/share/synthex/recovery/$(basename "${f}")"
        done
    fi

    # Hook into initramfs boot sequence
    # Run recovery check after basic system is up but before root is mounted
    inst_hook pre-mount 99 "${moddir}/recovery-check.sh"

    # Add recovery shell as a rescue option
    inst_hook emergency 99 "${moddir}/recovery-emergency.sh"

    # Install our hook scripts
    # (These will be created by the same module-setup.sh or exist alongside it)
    local hook_check="${moddir}/recovery-check.sh"
    if [[ ! -f "${hook_check}" ]]; then
        # Create inline hook
        echo '#!/bin/sh
# Synthex Recovery — boot check hook
# Only run from initramfs when recovery is enabled
if [ -f /etc/synthex/recovery.conf ]; then
    . /etc/synthex/recovery.conf
    if [ "${RECOVERY_ENABLED}" = "true" ] && [ "${AUTO_FALLBACK}" = "true" ]; then
        /usr/bin/synthex-recovery --check-boot 2>/dev/null || true
    fi
fi
' > "${hook_check}" 2>/dev/null || true
    fi
    inst_hook pre-mount 99 "${hook_check}"

    local hook_emergency="${moddir}/recovery-emergency.sh"
    if [[ ! -f "${hook_emergency}" ]]; then
        echo '#!/bin/sh
echo ""
echo "=== Synthex Recovery ==="
echo "Type: synthex-recovery to launch the recovery menu"
echo "Or type: synthex-recovery --help for options"
echo ""
' > "${hook_emergency}" 2>/dev/null || true
    fi

    # Add recovery entry to GRUB (via /boot/grub2/custom.cfg or dracut config)
    local grub_custom="${initdir}/boot/grub2/custom.cfg"
    if [[ -d "${initdir}/boot/grub2" ]]; then
        cat >> "${grub_custom}" <<'GRUBEOF'
### BEGIN Synthex Recovery ###
menuentry "Synthex Recovery Environment" --id synthex-recovery {
    linux /boot/vmlinuz-* root=LABEL=synthex-root rd.shell rd.break=pre-mount
    initrd /boot/initramfs-*.img
}
### END Synthex Recovery ###
GRUBEOF
    fi

    # Mark that this module was installed
    echo "synthex-recovery: dracut module installed at $(date)" > "${initdir}/etc/synthex/recovery-installed"
}

# --- Hook Scripts (created by install()) ------------------------------------

# The recovery-check.sh script runs pre-mount to check if the system failed to boot.
# If RECOVERY_ENABLED and AUTO_FALLBACK are set, it triggers auto-recovery.

# The recovery-emergency.sh script runs in the emergency shell to remind users
# of the recovery commands available.

# These hooks are written inline by the install() function above.