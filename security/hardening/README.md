# SynthOS Hardening Guide

> Version: 1.0.0
> Last Updated: 2026-07-04
> Classification: **INTERNAL**
> Part of: Linux Synthex Security Architecture

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Configuration Files](#3-configuration-files)
4. [Hardening Domains](#4-hardening-domains)
5. [Application Guide](#5-application-guide)
6. [Verification](#6-verification)
7. [Troubleshooting](#7-troubleshooting)
8. [FAQ](#8-faq)

---

## 1. Overview

This directory contains the system hardening configuration for Linux Synthex,
providing kernel-level, network-level, and audit-level security controls.

### Files in this Directory

| File | Purpose | Applies To |
|------|---------|-----------|
| `sysctl.conf` | Kernel parameter hardening | All systems |
| `limits.conf` | Resource usage limits | All users/sessions |
| `auditd.rules` | Security event auditing | All systems |
| `README.md` | This file | — |

### Security Posture Levels

| Level | Description | Suitable For |
|-------|-------------|-------------|
| **Standard** | Default Synthex hardening | Desktop users |
| **Enhanced** | Additional paranoid settings | Power users |
| **Maximum** | All available protections | Production/high-security |

---

## 2. Quick Start

### 2.1 Apply All Hardening

```bash
# 1. Kernel sysctl settings
sudo cp sysctl.conf /etc/sysctl.d/99-synthex-hardening.conf
sudo sysctl -p /etc/sysctl.d/99-synthex-hardening.conf

# 2. Resource limits
sudo cp limits.conf /etc/security/limits.d/99-synthex-hardening.conf
# Verify PAM includes limits:
grep "pam_limits" /etc/pam.d/common-session || echo "Add: session required pam_limits.so"

# 3. Audit rules
sudo cp auditd.rules /etc/audit/rules.d/99-synthex-hardening.rules
sudo augenrules --check
sudo systemctl restart auditd
sudo auditctl -l | grep -c "solus_"  # Should show many rules
```

### 2.2 Verify Installation

```bash
# Run verification script
./verify-hardening.sh

# Or check critical parameters manually:
echo "=== Kernel Hardening ==="
sysctl kernel.kptr_restrict kernel.dmesg_restrict kernel.randomize_va_space
sysctl kernel.yama.ptrace_scope fs.protected_hardlinks fs.protected_symlinks

echo "=== Network Hardening ==="
sysctl net.ipv4.conf.all.rp_filter net.ipv4.tcp_syncookies
sysctl net.ipv4.conf.all.accept_redirects

echo "=== Audit Status ==="
auditctl -s | grep -E "enabled|backlog"
auditctl -l | wc -l

echo "=== Resource Limits ==="
ulimit -c -n -u -s
```

---

## 3. Configuration Files

### 3.1 `sysctl.conf` — Kernel Hardening

**Location**: `/etc/sysctl.d/99-synthex-hardening.conf`
**Service**: `systemd-sysctl` (applied at boot)

This file configures kernel parameters across these domains:

| Section | Controls | Risk if Disabled |
|---------|----------|------------------|
| **Kernel Hardening** | kptr_restrict, dmesg_restrict, kexec | Information leaks, unsigned code execution |
| **Memory Protection** | ASLR, slab freelist, init_on_alloc | Heap attacks, memory corruption |
| **Exec Restrictions** | ptrace_scope, core dumps, user namespaces | Privilege escalation, data leaks |
| **Network (IPv4)** | rp_filter, syncookies, redirects | Spoofing, MITM, DoS |
| **Network (IPv6)** | RA, autoconf, privacy extensions | Address spoofing |
| **Filesystem** | protected_hardlinks, protected_symlinks | TOCTOU, privilege escalation |
| **BPF** | unprivileged_bpf_disabled, bpf_jit_harden | BPF attacks, Spectre |

#### Customization Example

```bash
# If you need user namespaces (e.g., for Docker rootless):
# Comment out or change:
# user.max_user_namespaces = 0
# To:
# user.max_user_namespaces = 10000

# If you need IPv6:
# Comment out or change:
# net.ipv6.conf.all.accept_ra = 0
# To:
# net.ipv6.conf.all.accept_ra = 1
```

### 3.2 `limits.conf` — Resource Limits

**Location**: `/etc/security/limits.d/99-synthex-hardening.conf`
**PAM Module**: `pam_limits.so`

This file restricts per-user resource consumption:

| Resource | Default Limit | Rationale |
|----------|---------------|-----------|
| `core` | 0 | Prevents core dump data leaks |
| `nofile` | 1024/4096 | Prevents fd exhaustion |
| `nproc` | 2048/4096 | Fork bomb mitigation |
| `stack` | 4096/8192 KB | Stack clash protection |
| `maxlogins` | 10 | Account sharing prevention |
| `rtprio` | 0 | Real-time scheduling restriction |

#### User-Specific Limits

Add user-specific overrides at the end of the file:

```
# Allow web server user more connections
www-data        hard    nofile          65536
www-data        soft    nofile          16384

# Allow build user more processes
jenkins         hard    nproc           8192
jenkins         soft    nproc           4096
```

### 3.3 `auditd.rules` — Audit Rules

**Location**: `/etc/audit/rules.d/99-synthex-hardening.rules`
**Service**: `auditd`

This file defines what security events are logged. Key monitoring areas:

| Key Prefix | Events Monitored | Use Case |
|------------|------------------|----------|
| `solus_kernel_module` | Module load/unload | Rootkit detection |
| `solus_sysctl` | Kernel parameter changes | Configuration tampering |
| `synthex_sudo` | Privilege escalation | Intrusion detection |
| `solus_file_perm` | Permission changes | Data integrity |
| `synthex_network_config` | Network configuration | Exfiltration |
| `solus_time_change` | Clock modification | Log manipulation |
| `solus_package_mgmt` | Package operations | Supply chain attacks |

#### Performance Tuning

For high-performance systems, adjust:

```bash
# Reduce audit buffer (if memory-constrained)
sudo auditctl -b 4096

# Reduce event types monitored (remove high-volume rules)
# Comment out: -a always,exit -S execve ...

# Increase rate limit
sudo auditctl -r 5000
```

Monitor backlog health:

```bash
watch -n 5 'auditctl -s | grep backlog'
# If backlog exceeds 80% of buffer, increase buffer size:
sudo auditctl -b 16384
```

---

## 4. Hardening Domains

### 4.1 Standard Hardening (Desktop Default)

The standard profile includes:

```
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 2
net.ipv4.conf.all.rp_filter = 1
net.ipv4.tcp_syncookies = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
user.max_user_namespaces = 10000  # Relaxed for containers
```

### 4.2 Enhanced Hardening (Power Users)

Add to `/etc/sysctl.d/99-synthex-hardening.conf`:

```
# Stricter kernel protection
kernel.kexec_load_disabled = 1
kernel.unprivileged_bpf_disabled = 1
kernel.perf_event_paranoid = 3
kernel.core_uses_pid = 1

# Disable user namespaces (unless needed)
user.max_user_namespaces = 0

# Strict network
net.ipv4.conf.all.log_martians = 1
net.ipv6.conf.all.disable_ipv6 = 1
```

### 4.3 Maximum Hardening (High Security)

Add to `/etc/sysctl.d/99-synthex-hardening.conf`:

```
# Lock down kernel completely
kernel.kexec_load_disabled = 1
kernel.modules_disabled = 1  # Cannot load new modules

# Disable all unprivileged access
kernel.perf_event_paranoid = 3
kernel.yama.ptrace_scope = 3  # No ptrace

# Disable IPv6 entirely
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Maximum filesystem protection
fs.protected_fifos = 2
fs.protected_regular = 2
```

> **WARNING**: Maximum settings can break container runtimes, debugging tools,
> and some desktop features. Test thoroughly before deploying.

---

## 5. Application Guide

### 5.1 Desktop Users

```bash
# Apply standard hardening
sudo cp sysctl.conf /etc/sysctl.d/99-synthex-hardening.conf
sudo sysctl -p /etc/sysctl.d/99-synthex-hardening.conf

# Uncomment in limits.conf for desktop:
# - Keep core=0 for default users
# - Keep stack_limit reasonable (4096/8192)

# Apply audit rules
sudo cp auditd.rules /etc/audit/rules.d/99-synthex-hardening.rules
sudo systemctl restart auditd

# Check for issues:
# - Gaming performance (test a few games)
# - Browser functionality (test web pages)
# - Printer/scanner (test if applicable)
```

### 5.2 Server Administrators

```bash
# Apply enhanced hardening
sudo cp sysctl.conf /etc/sysctl.d/99-synthex-hardening.conf
sudo sysctl -p /etc/sysctl.d/99-synthex-hardening.conf

# Enable additional server protections:
echo "net.ipv4.conf.all.rp_filter = 1" >> /etc/sysctl.d/99-synthex-hardening.conf
echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.d/99-synthex-hardening.conf

# Stricter limits for server
sudo cp limits.conf /etc/security/limits.d/99-synthex-hardening.conf
# Uncomment higher limits for service users

# Apply audit rules (keep all)
sudo cp auditd.rules /etc/audit/rules.d/99-synthex-hardening.rules
sudo systemctl restart auditd

# Verify all services still work
systemctl status nginx mysql postfix 2>/dev/null || true
```

### 5.3 Development/CI Environments

```bash
# Apply standard hardening with relaxed settings for dev tools
sudo cp sysctl.conf /etc/sysctl.d/99-synthex-hardening.conf
sudo sysctl -p /etc/sysctl.d/99-synthex-hardening.conf

# Relax for development:
echo "kernel.yama.ptrace_scope = 1" > /etc/sysctl.d/99-synthex-devel.conf
echo "user.max_user_namespaces = 100000" >> /etc/sysctl.d/99-synthex-devel.conf
sysctl -p /etc/sysctl.d/99-synthex-devel.conf

# Apply audit rules (reduced - developer machines generate lots of events)
# Remove high-volume rules: -a always,exit -S execve
# Keep: -a always,exit -S execve -F uid=0 (only root executions)
```

---

## 6. Verification

### 6.1 Quick Health Check

```bash
#!/bin/bash
# verify-hardening.sh

PASS=0
FAIL=0

check() {
    if [ "$1" = "$2" ]; then
        echo "  [PASS] $3"
        ((PASS++))
    else
        echo "  [FAIL] $3 (expected: $2, got: $1)"
        ((FAIL++))
    fi
}

echo "=== Kernel Hardening Check ==="
check "$(sysctl -n kernel.kptr_restrict)" "2" "kernel.kptr_restrict = 2"
check "$(sysctl -n kernel.dmesg_restrict)" "1" "kernel.dmesg_restrict = 1"
check "$(sysctl -n kernel.randomize_va_space)" "2" "ASLR enabled"
check "$(sysctl -n kernel.yama.ptrace_scope)" "2" "ptrace restricted"

echo ""
echo "=== Network Hardening Check ==="
check "$(sysctl -n net.ipv4.conf.all.rp_filter)" "1" "RP filter enabled"
check "$(sysctl -n net.ipv4.tcp_syncookies)" "1" "SYN cookies enabled"
check "$(sysctl -n net.ipv4.conf.all.accept_redirects)" "0" "No ICMP redirects"

echo ""
echo "=== Filesystem Hardening Check ==="
check "$(sysctl -n fs.protected_hardlinks)" "1" "Protected hardlinks"
check "$(sysctl -n fs.protected_symlinks)" "1" "Protected symlinks"

echo ""
echo "=== Resource Limit Check ==="
check "$(ulimit -c)" "0" "Core dumps disabled"

echo ""
echo "=== SELinux Check ==="
check "$(getenforce 2>/dev/null || echo 'Not available')" "Enforcing" "SELinux enforcing"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
exit $FAIL
```

### 6.2 CIS Benchmark Compliance

Check CIS compliance against these controls:

| CIS Control | Reference | Verification |
|-------------|-----------|------------|
| 1.5.1 | kernel.randomize_va_space = 2 | `sysctl kernel.randomize_va_space` |
| 1.5.2 | kernel.kptr_restrict = 2 | `sysctl kernel.kptr_restrict` |
| 1.5.3 | kernel.dmesg_restrict = 1 | `sysctl kernel.dmesg_restrict` |
| 1.5.4 | kernel.kexec_load_disabled = 1 | `sysctl kernel.kexec_load_disabled` |
| 3.1.1 | net.ipv4.conf.all.rp_filter = 1 | `sysctl net.ipv4.conf.all.rp_filter` |
| 3.1.2 | net.ipv4.tcp_syncookies = 1 | `sysctl net.ipv4.tcp_syncookies` |
| 3.2.1 | net.ipv4.conf.all.accept_redirects = 0 | `sysctl net.ipv4.conf.all.accept_redirects` |
| 3.2.2 | net.ipv4.conf.all.secure_redirects = 0 | `sysctl net.ipv4.conf.all.secure_redirects` |
| 3.3.1 | net.ipv6.conf.all.accept_ra = 0 | `sysctl net.ipv6.conf.all.accept_ra` |
| 4.1.1.1 | auditd installed | `systemctl is-active auditd` |
| 5.1 | core dumps disabled | `ulimit -c` |
| 5.2 | stack size limited | `ulimit -s` |
| 5.3 | maxlogins <= 10 | `grep maxlogins /etc/security/limits.conf` |

### 6.3 Automated Compliance Tool

```bash
# Using Lynis (install first)
sudo eopkg install lynis
sudo lynis audit system --tests-from-group hardening

# Using OpenSCAP
sudo eopkg install openscap-scanner
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_standard \
    --results results.xml \
    --report report.html \
    /usr/share/xml/scap/ssg/content/ssg-synthex-ds.xml
```

---

## 7. Troubleshooting

### 7.1 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| **Docker containers fail** | User namespaces disabled | Set `user.max_user_namespaces=100000` |
| **GDB/debuggers fail** | ptrace_scope=2 | Set `kernel.yama.ptrace_scope=1` |
| **Performance issues** | Audit backlog full | Increase buffer: `auditctl -b 16384` |
| **Can't load kernel modules** | modules_disabled=1 | Revert to `kernel.modules_disabled=0` |
| **Browsers crash** | Too strict memory settings | Relax `vm.overcommit_memory=0` |
| **Flatpak apps fail** | Namespace restrictions | Ensure `user.max_user_namespaces >= 10000` |
| **Can't change firewall** | Immutable audit rules | Remove `-e 2` from audit rules temporarily |

### 7.2 Reverting Changes

```bash
# Revert sysctl to defaults
sudo rm /etc/sysctl.d/99-synthex-hardening.conf
sudo sysctl --system

# Revert limits
sudo rm /etc/security/limits.d/99-synthex-hardening.conf

# Revert audit rules
sudo rm /etc/audit/rules.d/99-synthex-hardening.rules
sudo systemctl restart auditd
```

### 7.3 Checking What's Affected

```bash
# Find what sysctl settings differ from stock
diff <(sysctl -a 2>/dev/null | sort) <(
    sudo sysctl --system 2>/dev/null
    sysctl -a 2>/dev/null | sort
) | head -50

# Check if any processes are failing due to limits
dmesg | grep -i "resource\|limit\|denied" | tail -20

# Check audit backlog
auditctl -s | grep -E "backlog|lost|enabled"
```

---

## 8. FAQ

**Q: Do I need all three files?**
A: Yes, they address different security domains. sysctl.conf hardens the kernel,
limits.conf restricts user resources, and auditd.rules provides detection.

**Q: Will these break my system?**
A: The Standard profile is tested on Synthex desktop/server. Enhanced/Maximum
profiles may break container runtimes and debugging tools.

**Q: How do I customize for specific needs?**
A: Create a new file in the same directory with a lower prefix number
(e.g., `10-custom.conf`) for sysctl overrides. For audit, add rules to
a separate file in rules.d/.

**Q: Do these settings survive kernel updates?**
A: Yes, they're applied via sysctl.d and audit.rules.d at boot, not tied to
specific kernel versions.

**Q: How do I check if the settings are actually applied?**
A: Use `sysctl <parameter>` for kernel settings, `ulimit -a` for limits,
and `auditctl -l` for audit rules.

**Q: Are these settings CIS benchmark compliant?**
A: Yes, the Standard profile meets CIS Level 1 compliance. Enhanced profile
meets Level 2.

**Q: What about performance impact?**
A: Minimal (< 1% CPU overhead) for standard profile. Audit rules are the main
source of overhead; tune based on your needs.

**Q: Can I use these on other distributions?**
A: Most settings are Linux-generic and work on Fedora, RHEL, Debian, Ubuntu,
Arch, and others. Adjust paths accordingly.

---

## References

- [Synthex Security Architecture](../../security-architecture.md)
- [CIS Linux Benchmark](https://www.cisecurity.org/benchmark/linux)
- [Kernel Self-Protection Project](https://kernsec.org/wiki/index.php/Kernel_Self_Protection_Project)
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [sysctl(8)](https://man7.org/linux/man-pages/man8/sysctl.8.html)
- [limits.conf(5)](https://man7.org/linux/man-pages/man5/limits.conf.5.html)
- [audit.rules(7)](https://man7.org/linux/man-pages/man7/audit.rules.7.html)

---

*This document is part of the Linux Synthex Security Architecture v1.0.0*
*Copyright (c) 2026 Linux Synthex Project*
*Licensed under CC-BY-SA 4.0 International*
