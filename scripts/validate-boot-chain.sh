#!/bin/bash
# Synthex Boot Chain Validation Script
# Verifies the entire boot chain is functional
# Run after installation or kernel update

set -euo pipefail

AMBER='\033[38;5;214m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

PASS=0
FAIL=0
WARN=0

check() {
    if [ "$2" -eq 0 ]; then
        echo -e "  ${GREEN}✅${NC} $1"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}❌${NC} $1"
        FAIL=$((FAIL + 1))
    fi
}

warn() {
    echo -e "  ${YELLOW}⚠️${NC} $1"
    WARN=$((WARN + 1))
}

echo ""
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo -e "${AMBER}  🔍 Synthex Boot Chain Validation${NC}"
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo ""

# ─── 1. UEFI / Firmware ───────────────────────────────────────────

echo -e "${BOLD}1. Firmware / UEFI${NC}"
echo "──────────────────────"

if [ -d /sys/firmware/efi ]; then
    check "UEFI mode detected" 0
    check "EFI variables accessible" $(ls -1 /sys/firmware/efi/efivars/ 2>/dev/null | wc -l)
else
    warn "Legacy BIOS mode (UEFI recommended)"
fi

check "System firmware available" $(efibootmgr 2>/dev/null | wc -l || echo 0)

# ─── 2. Secure Boot ────────────────────────────────────────────────

echo -e "\n${BOLD}2. Secure Boot${NC}"
echo "──────────────────────"

if command -v mokutil &>/dev/null; then
    SB_STATE=$(mokutil --sb-state 2>/dev/null || echo "unknown")
    if echo "$SB_STATE" | grep -q "enabled"; then
        check "Secure Boot enabled" 0
    elif echo "$SB_STATE" | grep -q "disabled"; then
        warn "Secure Boot disabled (not required but recommended)"
    else
        warn "Cannot determine Secure Boot state"
    fi
else
    warn "mokutil not available"
fi

# ─── 3. Bootloader ─────────────────────────────────────────────────

echo -e "\n${BOLD}3. Bootloader${NC}"
echo "──────────────────────"

# Check GRUB
if [ -f /boot/grub2/grub.cfg ]; then
    check "GRUB config exists" 0
    check "GRUB config has Synthex entries" $(grep -c "Synthex" /boot/grub2/grub.cfg 2>/dev/null || echo 0)
    check "GRUB config has recovery entries" $(grep -ic "recovery" /boot/grub2/grub.cfg 2>/dev/null || echo 0)
else
    FAIL=$((FAIL + 1))
    echo -e "  ${RED}❌${NC} GRUB config not found"
fi

# Check systemd-boot as alternative
if [ -f /boot/loader/loader.conf ]; then
    check "systemd-boot config exists" 0
    check "systemd-boot entries found" $(ls -1 /boot/loader/entries/*.conf 2>/dev/null | wc -l || echo 0)
fi

# GRUB installation
if [ -f /boot/efi/EFI/synthex/grubx64.efi ] || [ -f /boot/efi/EFI/BOOT/BOOTX64.EFI ]; then
    check "GRUB EFI binary installed" 0
else
    warn "GRUB EFI binary not found (may be systemd-boot)"
fi

# ─── 4. Kernel ─────────────────────────────────────────────────────

echo -e "\n${BOLD}4. Kernel & Initramfs${NC}"
echo "──────────────────────"

KERNEL_COUNT=$(ls -1 /boot/vmlinuz-* 2>/dev/null | wc -l || echo 0)
INITRAMFS_COUNT=$(ls -1 /boot/initramfs-*.img 2>/dev/null | wc -l || echo 0)

check "Kernels installed ($KERNEL_COUNT found)" 0
check "Initramfs images found ($INITRAMFS_COUNT)" 0

# Check latest kernel
LATEST_KERNEL=$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -1)
if [ -n "$LATEST_KERNEL" ]; then
    KERNEL_VER="${LATEST_KERNEL#/boot/vmlinuz-}"
    INITRAMFS="/boot/initramfs-${KERNEL_VER}.img"
    check "Latest kernel: $KERNEL_VER" 0
    check "Initramfs for latest kernel exists" $(test -f "$INITRAMFS" && echo 0 || echo 1)
fi

# ─── 5. Root Filesystem ────────────────────────────────────────────

echo -e "\n${BOLD}5. Root Filesystem${NC}"
echo "──────────────────────"

ROOT_FS=$(findmnt -n -o FSTYPE / 2>/dev/null || echo "unknown")
ROOT_DEV=$(findmnt -n -o SOURCE / 2>/dev/null || echo "unknown")

if [ "$ROOT_FS" = "btrfs" ]; then
    check "BTRFS filesystem detected" 0
    check "BTRFS compression active" $(mount | grep -c "compress=" 2>/dev/null || echo 0)
    check "BTRFS subvolumes found" $(btrfs subvolume list / 2>/dev/null | wc -l || echo 0)
    check "Snapper configured" $(command -v snapper &>/dev/null && snapper -c root list 2>/dev/null | wc -l || echo 0)
else
    warn "Filesystem: $ROOT_FS (BTRFS recommended for snapshots)"
fi

# Check LUKS
if dmsetup ls --target crypt 2>/dev/null | grep -q .; then
    check "LUKS encryption detected" 0
fi

# ─── 6. Systemd Boot Analysis ─────────────────────────────────────

echo -e "\n${BOLD}6. Boot Performance${NC}"
echo "──────────────────────"

if command -v systemd-analyze &>/dev/null; then
    BOOT_TIME=$(systemd-analyze 2>/dev/null | grep -oP '=\s*\K[0-9.]+(?=s)' || echo "N/A")
    echo "  Boot time: ${BOOT_TIME}s"
    
    BLAME_OUTPUT=$(systemd-analyze blame 2>/dev/null | head -5 || echo "")
    if [ -n "$BLAME_OUTPUT" ]; then
        echo "  Slowest services:"
        echo "$BLAME_OUTPUT" | while read line; do echo "    $line"; done
    fi
else
    warn "systemd-analyze not available"
fi

# ─── 7. Recovery System ───────────────────────────────────────────

echo -e "\n${BOLD}7. Recovery System${NC}"
echo "──────────────────────"

check "synthex-recovery script exists" $(test -f /usr/bin/synthex-recovery && echo 0 || echo 1)
check "Recovery initramfs hook installed" $(ls /usr/lib/dracut/modules.d/*synthex* 2>/dev/null | wc -l || echo 0)
check "Recovery systemd service installed" $(systemctl list-unit-files synthex-recovery* 2>/dev/null | grep -c "synthex-recovery" || echo 0)
check "GRUB recovery entries configured" $(grep -c "Recovery" /boot/grub2/grub.cfg 2>/dev/null || echo 0)

# ─── 8. First Boot System ─────────────────────────────────────────

echo -e "\n${BOLD}8. First Boot System${NC}"
echo "──────────────────────"

check "synthex-firstboot.service installed" $(systemctl list-unit-files synthex-firstboot* 2>/dev/null | grep -c "synthex-firstboot" || echo 0)
check "synthex-oobe.service installed" $(systemctl list-unit-files synthex-oobe* 2>/dev/null | grep -c "synthex-oobe" || echo 0)

if [ -f /var/lib/synthex/firstboot-complete ]; then
    echo -e "  ${GREEN}✅${NC} First boot already completed: $(cat /var/lib/synthex/firstboot-complete)"
fi

# ─── Summary ───────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL + WARN))
echo ""
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo -e "  ${BOLD}Boot Chain Validation Complete${NC}"
echo ""
echo -e "  ${GREEN}✅ Pass: ${PASS}${NC}"
echo -e "  ${RED}❌ Fail: ${FAIL}${NC}"
echo -e "  ${YELLOW}⚠️  Warnings: ${WARN}${NC}"
echo -e "  Total checks: ${TOTAL}"
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✅ Boot chain looks good!${NC}"
else
    echo -e "${RED}❌ $FAIL checks failed. Review issues above.${NC}"
fi
