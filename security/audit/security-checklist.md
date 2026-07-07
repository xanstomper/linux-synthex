# Linux Synthex Security Audit Checklist

> Version: 1.0.0
> Last Updated: 2026-07-04
> Classification: **INTERNAL - SECURITY AUDIT**
> Reference: CIS Linux Benchmark v3.0, NIST SP 800-53 Rev. 5, PCI DSS v4.0

---

## How to Use This Checklist

Each section contains control items with the following format:

```
[ ] CONTROL-ID: Description
    Expected: <expected value/state>
    Command: <verification command>
    Result: ________________
    Pass/Fail: ___/___
```

- Mark `[x]` when the control passes
- Run the verification command and record the result
- Document any deviations in the Findings section
- Remediation steps are provided for failed controls

---

## Table of Contents

1. [Secure Boot & Firmware](#1-secure-boot--firmware)
2. [Disk Encryption & Storage](#2-disk-encryption--storage)
3. [Kernel Hardening](#3-kernel-hardening)
4. [Mandatory Access Control (SELinux)](#4-mandatory-access-control-selinux)
5. [Firewall & Network](#5-firewall--network)
6. [Authentication & Access Control](#6-authentication--access-control)
7. [Logging & Auditing](#7-logging--auditing)
8. [Application Security](#8-application-security)
9. [Update Management](#9-update-management)
10. [Resource Limits](#10-resource-limits)
11. [Cryptography](#11-cryptography)
12. [TPM & Measured Boot](#12-tpm--measured-boot)
13. [Container & Sandbox Security](#13-container--sandbox-security)
14. [Browser & Desktop Hardening](#14-browser--desktop-hardening)
15. [Physical Security](#15-physical-security)
16. [Security Dashboard](#16-security-dashboard)
17. [Overall Scoring](#17-overall-scoring)

---

## 1. Secure Boot & Firmware

### 1.1 UEFI Secure Boot

```
[ ] SB-01: Secure Boot is enabled in UEFI firmware
    Expected: SecureBoot enabled
    Command: mokutil --sb-state
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-02: Machine Owner Keys (MOK) are properly enrolled
    Expected: Valid MOK listed
    Command: mokutil --list-enrolled
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-03: Shim bootloader is installed and valid
    Expected: shimx64.efi present
    Command: ls -la /boot/efi/EFI/synthex/shimx64.efi
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-04: GRUB is signed and measured
    Expected: grubx64.efi signed
    Command: pesign -S -i /boot/efi/EFI/synthex/grubx64.efi
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-05: Kernel is signed
    Expected: Valid signature
    Command: sbsign --verify /boot/vmlinuz-*-synthex 2>&1 | grep -i "signed"
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-06: UEFI db/dbx variables up to date
    Expected: dbx contains latest revoked signatures
    Command: efi-updatevar -v -k /path 2>/dev/null || echo "db version: $(cat /sys/firmware/efi/efivars/SetupMode-*)"
    Result: ________________
    Pass/Fail: ___/___

[ ] SB-07: Secure Boot revocation list (dbx) is current
    Expected: Certificates revoked for known bootkits
    Command: mokutil --list-revocations 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

### 1.2 Firmware Configuration

```
[ ] FB-01: UEFI BIOS password is set
    Expected: Password enabled
    Command: /usr/libexec/synthex-check-bios-password
    Result: ________________
    Pass/Fail: ___/___

[ ] FB-02: Boot order is locked
    Expected: Only internal drive in boot list
    Command: efibootmgr -v
    Result: ________________
    Pass/Fail: ___/___

[ ] FB-03: USB boot is disabled (production)
    Expected: Disabled in firmware
    Command: dmesg | grep -i "secure boot" || echo "check firmware menu"
    Result: ________________
    Pass/Fail: ___/___

[ ] FB-04: TPM 2.0 is enabled in firmware
    Expected: TPM 2.0 device found
    Command: tpm2_getcap properties-variable | grep -i "TPM"
    Result: ________________
    Pass/Fail: ___/___

[ ] FB-05: TPM is active and managed
    Expected: TPM is active
    Command: systemctl status tpm2-abrmd 2>/dev/null || tpm2_getrandom 8 --hex
    Result: ________________
    Pass/Fail: ___/___

[ ] FB-06: UEFI Secure Boot has no setup mode
    Expected: SetupMode=0
    Command: cat /sys/firmware/efi/efivars/SetupMode-8be4df61-93ca-11d2-aa0d-00e098032b8c
    Result: ________________
    Pass/Fail: ___/___
```

---

## 2. Disk Encryption & Storage

### 2.1 Full Disk Encryption

```
[ ] DE-01: Root filesystem is LUKS2 encrypted
    Expected: crypto_LUKS type on root device
    Command: blkid -t TYPE=crypto_LUKS | grep -E "(cryptroot|/dev/sda[3-4])"
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-02: LUKS2 uses Argon2id PBKDF
    Expected: Argon2id
    Command: cryptsetup luksDump /dev/sdX | grep -i "pbkdf"
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-03: LUKS2 key size is 512 bits (AES-XTS)
    Expected: 512 bits (256-bit AES key × 2)
    Command: cryptsetup luksDump /dev/sdX | grep "Cipher"
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-04: LUKS header backup exists offline
    Expected: Backup file exists
    Command: ls -la /root/luks-header-*.bin 2>/dev/null || echo "MISSING"
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-05: Swap is encrypted
    Expected: cryptswap present
    Command: dmsetup ls | grep swap
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-06: No unencrypted /tmp partition
    Expected: /tmp is tmpfs or encrypted
    Command: mount | grep " /tmp "
    Result: ________________
    Pass/Fail: ___/___

[ ] DE-07: /boot is separate partition
    Expected: Separate /boot partition
    Command: mount | grep " /boot "
    Result: ________________
    Pass/Fail: ___/___
```

### 2.2 LUKS Key Management

```
[ ] LK-01: TPM2 key slot exist for automated unlock
    Expected: Key slot bound to TPM
    Command: systemd-cryptenroll /dev/sdX --tpm2-device=list 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] LK-02: Backup passphrase exists and is stored securely
    Expected: Backup passphrase
    Command: cryptsetup luksDump /dev/sdX | grep -c "LUKS Slot"
    Result: ________________
    Pass/Fail: ___/___

[ ] LK-03: LUKS header is not recoverable without key
    Expected: AFstrip is enabled (default)
    Command: cryptsetup luksDump /dev/sdX | grep "Stripe"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 3. Kernel Hardening

### 3.1 Kernel Boot Parameters

```
[ ] KH-01: Kernel lockdown is enabled
    Expected: integrity or enforcement
    Command: cat /sys/kernel/security/lockdown
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-02: Kernel command line is hardened
    Expected: slab_nomerge, init_on_alloc=1, init_on_free=1, pti=on
    Command: cat /proc/cmdline
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-03: Module signing is enforced
    Expected: module.sig_enforce=1 in cmdline
    Command: cat /proc/cmdline | grep "module.sig_enforce"
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-04: Kernel ASLR is enabled
    Expected: 2 (full randomization)
    Command: sysctl kernel.randomize_va_space | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-05: Kernel pointer restriction is maximum
    Expected: 2 (restrict for all users)
    Command: sysctl kernel.kptr_restrict | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-06: dmesg restriction is enabled
    Expected: 1 (CAP_SYSLOG required)
    Command: sysctl kernel.dmesg_restrict | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-07: Kexec is disabled
    Expected: 1 (kexec disabled)
    Command: sysctl kernel.kexec_load_disabled | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-08: Unprivileged BPF is disabled
    Expected: 1
    Command: sysctl kernel.unprivileged_bpf_disabled | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-09: Perf events are restricted
    Expected: 3 (most restricted)
    Command: sysctl kernel.perf_event_paranoid | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-10: Kernel sysrq is disabled
    Expected: 0
    Command: sysctl kernel.sysrq | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-11: YAMA ptrace scope is restricted
    Expected: 2 (CAP_SYS_PTRACE only) or 3 (none)
    Command: sysctl kernel.yama.ptrace_scope | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] KH-12: CPU vulnerability mitigations are active
    Expected: All mitigations present
    Command: grep . /sys/devices/system/cpu/vulnerabilities/*
    Result: ________________
    Pass/Fail: ___/___
```

### 3.2 Compiler Hardening

```
[ ] CC-01: Stack protector is enabled (glibc)
    Expected: -fstack-protector-strong
    Command: gcc -v -Q -O2 --help=target 2>&1 | grep stack-protector
    Result: ________________
    Pass/Fail: ___/___

[ ] CC-02: FORTIFY_SOURCE=3 is default
    Expected: _FORTIFY_SOURCE=3
    Command: cpp -dM /dev/null 2>/dev/null | grep _FORTIFY_SOURCE || echo "check /etc/rpm/macros"
    Result: ________________
    Pass/Fail: ___/___

[ ] CC-03: CET (Shadow Stack + IBT) is enabled
    Expected: -fcf-protection=full in build flags
    Command: gcc -v -Q --help=target 2>&1 | grep fcf-protection
    Result: ________________
    Pass/Fail: ___/___

[ ] CC-04: CFI is enabled for Clang builds
    Expected: -fsanitize=cfi for Clang compilations
    Command: clang -fsanitize=cfi -c test.c 2>/dev/null && echo "CFI available"
    Result: ________________
    Pass/Fail: ___/___

[ ] CC-05: RELRO is full (BIND_NOW)
    Expected: Full RELRO in binaries
    Command: checksec --file=/usr/bin/flatpak 2>/dev/null | grep "RELRO"
    Result: ________________
    Pass/Fail: ___/___
```

### 3.3 Sysctl Configuration

```
[ ] SC-01: /etc/sysctl.d/99-synthex-hardening.conf exists
    Expected: File present
    Command: ls -la /etc/sysctl.d/99-synthex-hardening.conf
    Result: ________________
    Pass/Fail: ___/___

[ ] SC-02: Sysctl settings are applied
    Expected: Runtime values match config
    Command: sysctl kernel.kptr_restrict kernel.dmesg_restrict kernel.randomize_va_space
    Result: ________________
    Pass/Fail: ___/___

[ ] SC-03: Protected hardlinks is enabled
    Expected: 1
    Command: sysctl fs.protected_hardlinks | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] SC-04: Protected symlinks is enabled
    Expected: 1
    Command: sysctl fs.protected_symlinks | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___
```

---

## 4. Mandatory Access Control (SELinux)

### 4.1 SELinux General Status

```
[ ] SE-01: SELinux is in enforcing mode
    Expected: Enforcing
    Command: getenforce
    Result: ________________
    Pass/Fail: ___/___

[ ] SE-02: SELinux policy type is targeted (or MLS)
    Expected: targeted or mls
    Command: sestatus | grep "Loaded policy name"
    Result: ________________
    Pass/Fail: ___/___

[ ] SE-03: No SELinux denials in audit log (for current boot)
    Expected: No AVC denials
    Command: ausearch -m avc -ts boot 2>&1 | head -5 || echo "No denials"
    Result: ________________
    Pass/Fail: ___/___

[ ] SE-04: Synthex policy module is loaded
    Expected: synthex-policy listed
    Command: semodule -l | grep synthex
    Result: ________________
    Pass/Fail: ___/___

[ ] SE-05: File contexts for Synthex binaries are correct
    Expected: synthex_software_center_exec_t, etc.
    Command: ls -Z /usr/bin/synthex-*
    Result: ________________
    Pass/Fail: ___/___

[ ] SE-06: Synthex policy module has no errors
    Expected: No semantic errors
    Command: secload -P -M -o /dev/null 2>&1 | grep -i "error" || echo "No errors"
    Result: ________________
    Pass/Fail: ___/___
```

### 4.2 SELinux Policy Compliance

```
[ ] SP-01: Policy neverallow rules are enforced
    Expected: No violations
    Command: apt-get install selinux-policy 2>/dev/null; seinfo --neverallow 2>&1 | head
    Result: ________________
    Pass/Fail: ___/___

[ ] SP-02: Unconfined domains are minimized
    Expected: Only init, systemd, kernel unconfined
    Command: seinfo -runconfined_domain -x 2>/dev/null | wc -l
    Result: ________________
    Pass/Fail: ___/___

[ ] SP-03: No domains are running permissive
    Expected: All domains enforcing
    Command: ausearch -m avc -ts boot --check-permissive 2>/dev/null || echo "No permissive domains"
    Result: ________________
    Pass/Fail: ___/___
```

### 4.3 AppArmor Compatibility

```
[ ] AC-01: AppArmor is available in LSM stacking
    Expected: apparmor in LSM list
    Command: cat /sys/kernel/security/lsm
    Result: ________________
    Pass/Fail: ___/___

[ ] AC-02: aa2selinux converter works if needed
    Expected: Tool present
    Command: which aa2selinux 2>/dev/null || echo "Not required if no AppArmor only apps"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 5. Firewall & Network

### 5.1 Firewalld

```
[ ] FW-01: Firewalld service is running
    Expected: Active (running)
    Command: systemctl is-active firewalld
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-02: Default zone is drop (or block)
    Expected: drop or block
    Command: firewall-cmd --get-default-zone
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-03: Only essential services are open
    Expected: Minimal services exposed
    Command: firewall-cmd --list-services
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-04: SSH rate limiting is configured
    Expected: Rich rule present
    Command: firewall-cmd --list-rich-rules | grep rate
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-05: ICMP redirect is blocked
    Expected: -j DROP
    Command: firewall-cmd --direct --get-all-rules | grep redirect
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-06: Invalid packets are dropped
    Expected: CT state INVALID dropped
    Command: firewall-cmd --direct --get-all-rules | grep INVALID
    Result: ________________
    Pass/Fail: ___/___

[ ] FW-07: Logging is configured for denied packets
    Expected: Log prefix configured
    Command: firewall-cmd --list-rich-rules | grep log
    Result: ________________
    Pass/Fail: ___/___
```

### 5.2 Network Kernel Parameters

```
[ ] NW-01: IP forwarding is disabled
    Expected: 0
    Command: sysctl net.ipv4.conf.all.forwarding | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-02: Reverse path filtering is strict
    Expected: 1
    Command: sysctl net.ipv4.conf.all.rp_filter | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-03: TCP SYN cookies are enabled
    Expected: 1
    Command: sysctl net.ipv4.tcp_syncookies | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-04: ICMP redirects are ignored
    Expected: 0
    Command: sysctl net.ipv4.conf.all.accept_redirects | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-05: Source routing is disabled
    Expected: 0
    Command: sysctl net.ipv4.conf.all.accept_source_route | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-06: Martians are logged
    Expected: 1
    Command: sysctl net.ipv4.conf.all.log_martians | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___

[ ] NW-07: IPv6 router advertisements are disabled (if not needed)
    Expected: 0
    Command: sysctl net.ipv6.conf.all.accept_ra | awk '{print $3}'
    Result: ________________
    Pass/Fail: ___/___
```

### 5.3 Network Service Exposure

```
[ ] NS-01: No unexpected listening ports
    Expected: Only expected services
    Command: ss -tlnp
    Result: ________________
    Pass/Fail: ___/___

[ ] NS-02: No UDP services exposed (except DHCP/DNS)
    Expected: Minimal UDP sockets
    Command: ss -ulnp
    Result: ________________
    Pass/Fail: ___/___

[ ] NS-03: No insecure services (telnet, rsh, ftp)
    Expected: Not installed or disabled
    Command: systemctl list-units | grep -E "(telnet|rsh|ftp).*service" | grep enabled || echo "Secure"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 6. Authentication & Access Control

### 6.1 Password Policy

```
[ ] AP-01: PAM password quality is enforced
    Expected: cracklib/pwquality configured
    Command: grep -E "pam_pwquality|pam_cracklib" /etc/pam.d/system-auth
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-02: Minimum password length is 14 characters
    Expected: minlen=14
    Command: grep "minlen" /etc/security/pwquality.conf 2>/dev/null || grep "minlen" /etc/pam.d/*
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-03: Password history is enforced
    Expected: remember=5
    Command: grep "remember" /etc/pam.d/system-auth
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-04: Password maximum age is 90 days
    Expected: PASS_MAX_DAYS <= 90
    Command: grep "PASS_MAX_DAYS" /etc/login.defs
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-05: Account lockout after failed attempts
    Expected: faillock configured
    Command: grep -E "pam_faillock|pam_tally" /etc/pam.d/system-auth
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-06: Root login over SSH is disabled
    Expected: PermitRootLogin no
    Command: grep "^PermitRootLogin" /etc/ssh/sshd_config
    Result: ________________
    Pass/Fail: ___/___

[ ] AP-07: SSH password authentication is disabled (key-only)
    Expected: PasswordAuthentication no
    Command: grep "^PasswordAuthentication" /etc/ssh/sshd_config
    Result: ________________
    Pass/Fail: ___/___
```

### 6.2 User Management

```
[ ] UM-01: No accounts with empty passwords
    Expected: No output
    Command: awk -F: '($2 == "") {print $1}' /etc/shadow
    Result: ________________
    Pass/Fail: ___/___

[ ] UM-02: Root is the only UID 0 account
    Expected: Only root
    Command: awk -F: '($3 == 0) {print $1}' /etc/passwd
    Result: ________________
    Pass/Fail: ___/___

[ ] UM-03: No locked accounts have been unlocked recently
    Expected: No unexpected unlocks
    Command: ausearch -m USER_UNLOCK -ts week-ago 2>/dev/null || echo "No unlocks"
    Result: ________________
    Pass/Fail: ___/___

[ ] UM-04: Inactive accounts are locked
    Expected: INACTIVE=30 or less
    Command: grep "INACTIVE" /etc/default/useradd
    Result: ________________
    Pass/Fail: ___/___

[ ] UM-05: Home directory permissions are 750 or stricter
    Expected: drwxr-x--- (750) or drwx------ (700)
    Command: ls -la /home/ | grep -v "^d.* 755"
    Result: ________________
    Pass/Fail: ___/___
```

### 6.3 Sudo Configuration

```
[ ] SU-01: Sudo requires authentication
    Expected: Defaults targetpw or rootpw
    Command: grep -E "Defaults.*(targetpw|rootpw)" /etc/sudoers
    Result: ________________
    Pass/Fail: ___/___

[ ] SU-02: Timestamp timeout is limited
    Expected: timestamp_timeout=5
    Command: grep "timestamp_timeout" /etc/sudoers
    Result: ________________
    Pass/Fail: ___/___

[ ] SU-03: No NOPASSWD entries exist (except for dedicated service accounts)
    Expected: Minimal or no NOPASSWD
    Command: grep "NOPASSWD" /etc/sudoers /etc/sudoers.d/* 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

---

## 7. Logging & Auditing

### 7.1 Auditd Configuration

```
[ ] LG-01: auditd is installed and running
    Expected: Active (running)
    Command: systemctl is-active auditd
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-02: Audit rules are loaded
    Expected: Rules present
    Command: auditctl -l | wc -l
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-03: Audit log is not world-readable
    Expected: 600 or 640
    Command: ls -la /var/log/audit/audit.log | awk '{print $1}'
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-04: Audit log rotation is configured
    Expected: max_log_file=128, num_logs=5
    Command: grep -E "max_log_file|num_logs" /etc/audit/auditd.conf
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-05: Audit failure mode is set to log
    Expected: -f 1
    Command: auditctl -s | grep "fail"
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-06: Audit backlog has not exceeded limit
    Expected: No backlog errors in logs
    Command: ausearch -m DAEMON_ERR -ts boot 2>&1 | grep -c "backlog" || echo "OK"
    Result: ________________
    Pass/Fail: ___/___

[ ] LG-07: Audit rules file is immutable
    Expected: -e 2 present
    Command: tail -1 /etc/audit/rules.d/99-synthex-hardening.rules | grep "\-e 2"
    Result: ________________
    Pass/Fail: ___/___
```

### 7.2 Audit Coverage

```
[ ] AC-01: Kernel module loading is audited
    Expected: init_module, finit_module, delete_module
    Command: auditctl -l | grep -c "init_module\|finit_module\|delete_module"
    Result: ________________
    Pass/Fail: ___/___

[ ] AC-02: Authentication events are audited
    Expected: PAM, su, sudo logged
    Command: auditctl -l | grep -c "su\|sudo\|pam"
    Result: ________________
    Pass/Fail: ___/___

[ ] AC-03: File permission changes are audited
    Expected: chmod, chown, setxattr
    Command: auditctl -l | grep -c "chmod\|chown\|setxattr"
    Result: ________________
    Pass/Fail: ___/___

[ ] AC-04: Time changes are audited
    Expected: settimeofday, clock_settime
    Command: auditctl -l | grep -c "settimeofday\|clock_settime"
    Result: ________________
    Pass/Fail: ___/___

[ ] AC-05: Synthex-specific events are audited
    Expected: eopkg, flatpak, synthex-* monitored
    Command: auditctl -l | grep -c "eopkg\|flatpak\|synthex"
    Result: ________________
    Pass/Fail: ___/___
```

### 7.3 Remote Logging

```
[ ] RL-01: Remote syslog server is configured
    Expected: *.* @logserver:514
    Command: grep -r "@.*:" /etc/rsyslog.d/ /etc/rsyslog.conf 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-02: TLS is used for remote logging
    Expected: $DefaultNetstreamDriver gtls
    Command: grep "gtls" /etc/rsyslog.d/*.conf 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-03: Audit logs are shipped off-system
    Expected: audisp-remote configured
    Command: grep -r "remote_server\|active = yes" /etc/audit/audisp-remote.conf 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

---

## 8. Application Security

### 8.1 Hardened Malloc

```
[ ] HM-01: glibc heap hardening is enabled
    Expected: MALLOC_CHECK_=3 or glibc.malloc.tcache_count=0
    Command: grep "MALLOC_CHECK_" /etc/environment /etc/profile.d/*.sh
    Result: ________________
    Pass/Fail: ___/___

[ ] HM-02: LD_PRELOAD hardened malloc is configured (if using jemalloc)
    Expected: libjemalloc or libhardened_malloc in ld.so.preload
    Command: cat /etc/ld.so.preload 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] HM-03: Dynamic linker BIND_NOW is configured
    Expected: LD_BIND_NOW=1
    Command: grep "LD_BIND_NOW" /etc/environment /etc/profile.d/*.sh
    Result: ________________
    Pass/Fail: ___/___
```

### 8.2 Flatpak Sandbox

```
[ ] FP-01: Flatpak is installed and up-to-date
    Expected: Latest version
    Command: flatpak --version
    Result: ________________
    Pass/Fail: ___/___

[ ] FP-02: Flatpak applications have restricted permissions
    Expected: Minimal permissions per app
    Command: flatpak info --show-permissions <app-id>
    Result: ________________
    Pass/Fail: ___/___

[ ] FP-03: System-wide Flatpak policy is configured
    Expected: /etc/flatpak/system-policy.conf exists
    Command: ls -la /etc/flatpak/system-policy.conf 2>/dev/null || echo "NOT CONFIGURED"
    Result: ________________
    Pass/Fail: ___/___

[ ] FP-04: Flatpak uses Wayland (no X11 fallback)
    Expected: --socket=wayland --nosocket=x11
    Command: flatpak override --show | grep socket
    Result: ________________
    Pass/Fail: ___/___
```

### 8.3 Synthex Software Center

```
[ ] SW-01: Software Center runs with SELinux restrictions
    Expected: synthex_software_center_t context
    Command: ps -Z -C synthex-software-center 2>/dev/null | awk '{print $1}'
    Result: ________________
    Pass/Fail: ___/___

[ ] SW-02: Software Center uses polkit for privileged operations
    Expected: org.synthex.software-center.policy exists
    Command: ls -la /usr/share/polkit-1/actions/org.synthex.software-center.* 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

---

## 9. Update Management

### 9.1 Automatic Updates

```
[ ] AU-01: Synthex auto-update timer is enabled
    Expected: Enabled and running
    Command: systemctl is-enabled synthex-update.timer
    Result: ________________
    Pass/Fail: ___/___

[ ] AU-02: Automatic updates check is configured
    Expected: Enabled=true in config
    Command: grep "Enabled" /etc/synthex/auto-update.conf 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] AU-03: Automatic firmware updates are enabled
    Expected: UpdateFirmware=true
    Command: grep "UpdateFirmware" /etc/synthex/auto-update.conf 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] AU-04: System is up-to-date with security patches
    Expected: 0 pending security updates
    Command: eopkg list-updates | grep -c "security\|CVE" || echo "OK"
    Result: ________________
    Pass/Fail: ___/___

[ ] AU-05: Flatpak applications are up-to-date
    Expected: No pending Flatpak updates
    Command: flatpak update --dry-run 2>&1 | grep -c "updating" || echo "Up to date"
    Result: ________________
    Pass/Fail: ___/___

[ ] AU-06: Kernel is the latest available version
    Expected: Current kernel matches installed packages
    Command: uname -r; eopkg list-installed | grep "^linux-current"
    Result: ________________
    Pass/Fail: ___/___
```

### 9.2 Update Security

```
[ ] US-01: Repository GPG keys are verified
    Expected: Valid GPG keys
    Command: eopkg list-repo | grep -c "GPG"
    Result: ________________
    Pass/Fail: ___/___

[ ] US-02: Pre/Post-update snapshots are enabled (btrfs)
    Expected: snapper configured for root
    Command: snapper -c root list-configs 2>/dev/null | grep "root" || echo "Not btrfs"
    Result: ________________
    Pass/Fail: ___/___

[ ] US-03: Needs-restarting check is enabled
    Expected: needrestart installed
    Command: which needrestart 2>/dev/null && needrestart -k -v 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

---

## 10. Resource Limits

```
[ ] RL-01: Core dumps are disabled
    Expected: 0
    Command: ulimit -c; grep "core" /etc/security/limits.conf
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-02: Maximum number of processes is limited
    Expected: nproc <= 4096
    Command: ulimit -u
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-03: Stack size is limited
    Expected: stack <= 8192
    Command: ulimit -s
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-04: Max logins per user is limited
    Expected: maxlogins <= 10
    Command: grep "maxlogins" /etc/security/limits.conf
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-05: Real-time priority is restricted for non-root
    Expected: rtprio = 0
    Command: grep "rtprio" /etc/security/limits.conf
    Result: ________________
    Pass/Fail: ___/___

[ ] RL-06: /etc/security/limits.conf is applied by PAM
    Expected: pam_limits.so in PAM stack
    Command: grep "pam_limits" /etc/pam.d/common-session
    Result: ________________
    Pass/Fail: ___/___
```

---

## 11. Cryptography

### 11.1 System Cryptographic Settings

```
[ ] CR-01: /etc/crypto-policies is set to DEFAULT or FUTURE
    Expected: DEFAULT or FUTURE
    Command: update-crypto-policies --show 2>/dev/null || cat /etc/crypto-policies/config
    Result: ________________
    Pass/Fail: ___/___

[ ] CR-02: TLS 1.0 and 1.1 are disabled system-wide
    Expected: PROFILE=SYSTEM or FUTURE
    Command: grep -E "(MIN_TLS_VERSION|TLS.version)" /etc/crypto-policies/back-ends/opensslcnf.config 2>/dev/null || update-crypto-policies --show
    Result: ________________
    Pass/Fail: ___/___

[ ] CR-03: Weak ciphers (RC4, 3DES, MD5) are disabled
    Expected: Not present in system policy
    Command: openssl ciphers -v 'ALL:eNULL' | grep -c "RC4\|3DES\|MD5" || echo "OK"
    Result: ________________
    Pass/Fail: ___/___

[ ] CR-04: SSH uses strong ciphers and MACs
    Expected: No weak algorithms
    Command: sshd -T 2>/dev/null | grep -E "ciphers|macs|kexalgorithms"
    Result: ________________
    Pass/Fail: ___/___
```

### 11.2 Encryption Key Storage

```
[ ] KS-01: SSH host keys use strong algorithms
    Expected: ed25519 or rsa (4096)
    Command: ls -la /etc/ssh/ssh_host_*
    Result: ________________
    Pass/Fail: ___/___

[ ] KS-02: GPG keyring is properly protected
    Expected: 700 on .gnupg
    Command: ls -lad ~/.gnupg/ 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] KS-03: LUKS recovery keys are stored offline
    Expected: Not on device
    Command: test -f /root/luks-recovery-key.txt && echo "ON DEVICE - MOVE OFFLINE" || echo "OK"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 12. TPM & Measured Boot

### 12.1 TPM Health

```
[ ] TM-01: TPM 2.0 device is accessible
    Expected: /dev/tpm0 or /dev/tpmrm0 present
    Command: ls -la /dev/tpm* 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] TM-02: TPM is not in conflict with firmware
    Expected: No TPM errors in dmesg
    Command: dmesg | grep -i tpm | grep -i "error\|fail\|abort"
    Result: ________________
    Pass/Fail: ___/___

[ ] TM-03: TPM PCR values are valid
    Expected: Non-zero, consistent
    Command: tpm2_pcrread sha256:0,2,4,7,9
    Result: ________________
    Pass/Fail: ___/___

[ ] TM-04: TPM owner auth is set
    Expected: Owner auth configured
    Command: tpm2_getcap properties-variable | grep -i "owner\|auth"
    Result: ________________
    Pass/Fail: ___/___
```

### 12.2 Measured Boot

```
[ ] MB-01: IMA is enabled in kernel
    Expected: ima in cmdline
    Command: cat /proc/cmdline | grep "ima"
    Result: ________________
    Pass/Fail: ___/___

[ ] MB-02: IMA policy is loaded
    Expected: Policy in /etc/ima/ima-policy
    Command: cat /sys/kernel/security/ima/policy | head -5
    Result: ________________
    Pass/Fail: ___/___

[ ] MB-03: IMA measurement log is populated
    Expected: Entries in ascii_runtime_measurements
    Command: cat /sys/kernel/security/ima/ascii_runtime_measurements | wc -l
    Result: ________________
    Pass/Fail: ___/___

[ ] MB-04: LUKS key is sealed to TPM PCRs
    Expected: TPM key slot exists
    Command: systemd-cryptenroll /dev/sdX --tpm2-device=list 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] MB-05: Remote attestation is configured (optional)
    Expected: akcert created
    Command: tpm2_createak -c ak.ctx 2>/dev/null || echo "Not configured"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 13. Container & Sandbox Security

### 13.1 Docker/Podman

```
[ ] CT-01: Container runtime uses SELinux
    Expected: selinux-enabled = true
    Command: docker info 2>/dev/null | grep "Security Options" | grep -c selinux || podman info 2>/dev/null | grep -c selinux || echo "Not installed"
    Result: ________________
    Pass/Fail: ___/___

[ ] CT-02: User namespace remapping is enabled
    Expected: userns-remap=default
    Command: cat /etc/docker/daemon.json 2>/dev/null | grep "userns-remap" || podman info 2>/dev/null | grep -c "userns" || echo "Not installed"
    Result: ________________
    Pass/Fail: ___/___

[ ] CT-03: No containers run as privileged
    Expected: No --privileged containers
    Command: docker ps --filter "status=running" --format "{{.Names}} ({{.Command}})" 2>/dev/null | xargs -I{} docker inspect {} 2>/dev/null | grep -c "Privileged.*true" || echo "No running containers"
    Result: ________________
    Pass/Fail: ___/___

[ ] CT-04: Container images are scanned for vulnerabilities
    Expected: Scanner configured
    Command: which trivy 2>/dev/null || which clair 2>/dev/null || echo "No scanner configured"
    Result: ________________
    Pass/Fail: ___/___
```

### 13.2 Flatpak

```
[ ] FC-01: Flatpak bubblewrap sandbox is enforced
    Expected: bubblewrap installed
    Command: which bwrap
    Result: ________________
    Pass/Fail: ___/___

[ ] FC-02: Flatpak portals are configured
    Expected: xdg-desktop-portal running
    Command: systemctl status --user xdg-desktop-portal 2>/dev/null || systemctl is-active xdg-desktop-portal
    Result: ________________
    Pass/Fail: ___/___

[ ] FC-03: No Flatpak apps have unrestricted filesystem access
    Expected: No --filesystem=host or --filesystem=home
    Command: flatpak override --show | grep filesystem
    Result: ________________
    Pass/Fail: ___/___
```

---

## 14. Browser & Desktop Hardening

### 14.1 Browser Security Policies

```
[ ] BR-01: Chromium managed policies are applied
    Expected: synthex-security.json exists
    Command: ls -la /etc/chromium/policies/managed/synthex-security.json 2>/dev/null || ls -la /etc/opt/chrome/policies/managed/synthex-security.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-02: Chromium policy enforces site isolation
    Expected: EnableSiteIsolation=true
    Command: grep "EnableSiteIsolation" /etc/chromium/policies/managed/synthex-security.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-03: Chromium Safe Browsing is enabled
    Expected: SafeBrowsingEnabled=true
    Command: grep "SafeBrowsing" /etc/chromium/policies/managed/synthex-security.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-04: Firefox system policies are applied
    Expected: syspolicy.json exists
    Command: ls -la /etc/firefox/syspolicy.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-05: Firefox tracking protection is enforced
    Expected: EnableTrackingProtection=true
    Command: grep "EnableTrackingProtection" /etc/firefox/syspolicy.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-06: Firefox password manager is disabled
    Expected: OfferToSaveLogins=false
    Command: grep "OfferToSaveLogins" /etc/firefox/syspolicy.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] BR-07: DNS over HTTPS is enforced
    Expected: DoH enabled and locked
    Command: grep "DNSOverHTTPS" /etc/firefox/syspolicy.json 2>/dev/null || grep "DNSOverHttpsMode" /etc/chromium/policies/managed/synthex-security.json 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___
```

### 14.2 Desktop Hardening

```
[ ] DS-01: Screen lock is configured
    Expected: Lock on sleep and screensaver
    Command: gsettings get org.gnome.desktop.screensaver lock-enabled 2>/dev/null || gsettings get org.cinnamon.desktop.screensaver lock-enabled 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] DS-02: Automatic screen lock after 5 minutes
    Expected: lock-delay <= 300 seconds
    Command: gsettings get org.gnome.desktop.screensaver lock-delay 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] DS-03: Wayland is used instead of X11
    Expected: WAYLAND_DISPLAY=wayland-0
    Command: echo $XDG_SESSION_TYPE
    Result: ________________
    Pass/Fail: ___/___

[ ] DS-04: Remote desktop is disabled (unless needed)
    Expected: No VNC/RDP services
    Command: systemctl is-active vncserver 2>/dev/null; systemctl is-active xrdp 2>/dev/null; echo "check"
    Result: ________________
    Pass/Fail: ___/___
```

---

## 15. Physical Security

```
[ ] PS-01: GRUB password is set
    Expected: superusers and password in grub config
    Command: grep "superusers" /etc/grub.d/*.cfg 2>/dev/null || grep "superusers" /boot/grub/grub.cfg 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] PS-02: Single-user mode requires password
    Expected: sulogin or single-user protected
    Command: grep "SINGLE" /etc/sysconfig/init 2>/dev/null || grep "sulogin" /etc/inittab 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] PS-03: USB storage is disabled (production)
    Expected: usb-storage blacklisted
    Command: ls -la /etc/modprobe.d/ | grep "usb-storage" || lsmod | grep usb_storage
    Result: ________________
    Pass/Fail: ___/___

[ ] PS-04: Firewire/Thunderbolt DMA is restricted
    Expected: thunderbolt=off or IOMMU enabled
    Command: cat /proc/cmdline | grep -E "thunderbolt=off|iommu="
    Result: ________________
    Pass/Fail: ___/___

[ ] PS-05: Kernel lockdown prevents physical DMA attacks
    Expected: integrity or enforcement
    Command: cat /sys/kernel/security/lockdown
    Result: ________________
    Pass/Fail: ___/___
```

---

## 16. Security Dashboard

```
[ ] SD-01: Security Dashboard is installed
    Expected: synthex-security-dashboard binary present
    Command: which synthex-security-dashboard
    Result: ________________
    Pass/Fail: ___/___

[ ] SD-02: Security Gatherer service is running
    Expected: Active (running)
    Command: systemctl status synthex-security-gatherer 2>/dev/null | grep "Active"
    Result: ________________
    Pass/Fail: ___/___

[ ] SD-03: Security score is above 80/100
    Expected: >= 80
    Command: dbus-send --system --print-reply --dest=org.synthex.SecurityGatherer1 /org/synthex/SecurityGatherer1 org.synthex.SecurityGatherer1.get_security_score 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] SD-04: Dashboard receives security events
    Expected: Recent events visible
    Command: dbus-send --system --print-reply --dest=org.synthex.SecurityGatherer1 /org/synthex/SecurityGatherer1 org.synthex.SecurityGatherer1.get_recent_events 2>/dev/null
    Result: ________________
    Pass/Fail: ___/___

[ ] SD-05: Dashboard is accessible via app menu
    Expected: .desktop file present
    Command: ls -la /usr/share/applications/org.synthex.SecurityDashboard.desktop
    Result: ________________
    Pass/Fail: ___/___
```

---

## 17. Overall Scoring

### 17.1 Scoring Rubric

| Level | Score | Meaning |
|-------|-------|---------|
| **Critical** | < 50 | Active compromise or misconfiguration that bypasses all layers |
| **High** | 50-69 | Significant hardening gaps that reduce security posture |
| **Medium** | 70-84 | Acceptable security posture with minor hardening opportunities |
| **Low** | 85-94 | Good security posture, near baseline compliance |
| **Minimal** | 95-100 | Excellent security posture, exemplary hardening |

### 17.2 Scoring Table

| Section | Items | Passed | Score | Weight | Weighted |
|---------|-------|--------|-------|--------|----------|
| 1. Secure Boot & Firmware | ___ | ___ | ___% | 10% | ___ |
| 2. Disk Encryption & Storage | ___ | ___ | ___% | 10% | ___ |
| 3. Kernel Hardening | ___ | ___ | ___% | 15% | ___ |
| 4. SELinux | ___ | ___ | ___% | 10% | ___ |
| 5. Firewall & Network | ___ | ___ | ___% | 10% | ___ |
| 6. Authentication & Access | ___ | ___ | ___% | 10% | ___ |
| 7. Logging & Auditing | ___ | ___ | ___% | 10% | ___ |
| 8. Application Security | ___ | ___ | ___% | 5% | ___ |
| 9. Update Management | ___ | ___ | ___% | 5% | ___ |
| 10. Resource Limits | ___ | ___ | ___% | 3% | ___ |
| 11. Cryptography | ___ | ___ | ___% | 3% | ___ |
| 12. TPM & Measured Boot | ___ | ___ | ___% | 3% | ___ |
| 13. Container/Sandbox | ___ | ___ | ___% | 2% | ___ |
| 14. Browser/Desktop | ___ | ___ | ___% | 2% | ___ |
| 15. Physical Security | ___ | ___ | ___% | 1% | ___ |
| 16. Security Dashboard | ___ | ___ | ___% | 1% | ___ |
| **Total** | ___ | ___ | ___ | **100%** | **___%** |

**Final Score**: ___/100

**Risk Level**: _______________

---

## 18. Findings & Recommendations

### 18.1 Critical Findings

| # | Finding | Control Ref | Impact | Recommendation |
|---|---------|-------------|--------|---------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### 18.2 High Findings

| # | Finding | Control Ref | Impact | Recommendation |
|---|---------|-------------|--------|---------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### 18.3 Medium Findings

| # | Finding | Control Ref | Impact | Recommendation |
|---|---------|-------------|--------|---------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## 19. Audit Summary

### Audit Metadata

| Field | Value |
|-------|-------|
| **System Name** | ________________ |
| **Hostname** | ________________ |
| **OS Version** | ________________ |
| **Kernel Version** | ________________ |
| **SELinux Policy** | ________________ |
| **Synthex Version** | ________________ |
| **Audit Date** | ________________ |
| **Auditor** | ________________ |
| **Audit Type** | [ ] Internal  [ ] External  [ ] Compliance  [ ] Full |
| **Classification** | [ ] Confidential  [ ] Internal  [ ] Public |

### Attestation

I have performed the above security audit of this Linux Synthex system and attest
that the results accurately represent the system's current security posture.

**Auditor Signature**: ________________         **Date**: ________________

**Reviewer Signature**: ________________         **Date**: ________________

---

## Appendix: Remediation Timeline

| Priority | Remediation Time |
|----------|------------------|
| Critical | Immediate (< 24 hours) |
| High | Within 1 week |
| Medium | Within 1 month |
| Low | Next maintenance cycle |

---

*This checklist is part of the Linux Synthex Security Architecture v1.0.0*
*Reference: https://github.com/synthex-project/security*
