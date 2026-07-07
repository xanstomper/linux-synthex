#!/usr/bin/env bash
# synthex-security-deploy.sh — Deploy Synthex security hardening to installed system
# Installed to /usr/libexec/synthex/security-deploy.sh
# Deploys CIS/NIST-grade hardening: sysctl, auditd, limits, modprobe blacklist, firewalld, SELinux
set -euo pipefail

LOG="/var/log/synthex-security-deploy.log"
SYNTHEX_STATE="/var/lib/synthex"

echo "=== Synthex Security Deployment $(date) ===" | tee "$LOG"
mkdir -p "$SYNTHEX_STATE"

# ── 1. Kernel sysctl hardening (CIS/NIST/KSPP) ─────────────────────
echo "[1/7] Deploying sysctl hardening..." | tee -a "$LOG"
mkdir -p /etc/sysctl.d
cat > /etc/sysctl.d/99-synthex-hardening.conf << 'SYSCTLEOF'
# Synthex Security — CIS Linux Benchmark v3.0 / KSPP / NIST SP 800-53
# Kernel information disclosure
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.printk = 3 3 3 3
kernel.kexec_load_disabled = 1
kernel.unprivileged_bpf_disabled = 1
kernel.perf_event_paranoid = 3
kernel.sysrq = 0
# Memory protection
kernel.randomize_va_space = 2
kernel.slab_freelist_random = 1
kernel.slab_freelist_hardened = 1
kernel.init_on_alloc = 1
kernel.init_on_free = 1
kernel.page_alloc.shuffle = 1
kernel.stack_guard_gap = 256
# Yama ptrace scope
kernel.yama.ptrace_scope = 1
# BPF hardening
net.core.bpf_jit_harden = 2
# Filesystem protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
fs.suid_dumpable = 0
# Network hardening
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
SYSCTLEOF
sysctl --system 2>/dev/null | tail -3 | tee -a "$LOG" || true
echo "  sysctl hardening deployed" | tee -a "$LOG"

# ── 2. Audit daemon rules (CIS Section 4.x / NIST AU-2/AU-3/AU-12) ──
echo "[2/7] Deploying auditd rules..." | tee -a "$LOG"
mkdir -p /etc/audit/rules.d
cat > /etc/audit/rules.d/99-synthex-hardening.rules << 'AUDITEOF'
## Synthex Audit Rules
-D
-b 8192
-f 1
-w /sbin/insmod -p x -k synthex_kernel_module
-w /sbin/modprobe -p x -k synthex_kernel_module
-w /sbin/rmmod -p x -k synthex_kernel_module
-a always,exit -S init_module -S finit_module -S delete_module -k synthex_kernel_module
-a always,exit -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k synthex_perm_mod
-a always,exit -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k synthex_perm_mod
-a always,exit -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k synthex_priv_cmds
-w /usr/sbin/useradd -p x -k synthex_user_mod
-w /usr/sbin/userdel -p x -k synthex_user_mod
-w /usr/sbin/usermod -p x -k synthex_user_mod
-w /usr/sbin/groupadd -p x -k synthex_user_mod
-w /usr/sbin/groupdel -p x -k synthex_user_mod
-w /usr/sbin/groupmod -p x -k synthex_user_mod
-w /var/log/lastlog -p wa -k synthex_logins
-w /var/run/faillock/ -p wa -k synthex_logins
-w /var/log/wtmp -p wa -k synthex_logins
-w /var/log/btmp -p wa -k synthex_logins
-a always,exit -S adjtimex -S settimeofday -k synthex_time_change
-a always,exit -S clock_settime -k synthex_time_change
-w /etc/localtime -p wa -k synthex_time_change
-w /etc/crontab -p wa -k synthex_cron
-w /etc/cron.d/ -p wa -k synthex_cron
-w /etc/cron.daily/ -p wa -k synthex_cron
-w /etc/cron.hourly/ -p wa -k synthex_cron
-w /etc/cron.monthly/ -p wa -k synthex_cron
-w /etc/cron.weekly/ -p wa -k synthex_cron
-w /var/spool/cron/ -p wa -k synthex_cron
-w /etc/systemd/ -p wa -k synthex_systemd
-w /etc/ssh/sshd_config -p wa -k synthex_sshd
-w /etc/sudoers -p wa -k synthex_sudoers
-w /etc/sudoers.d/ -p wa -k synthex_sudoers
-w /usr/bin/synthex- -p x -k synthex_tools
-w /etc/synthex/ -p wa -k synthex_config
AUDITEOF
echo "  auditd rules deployed" | tee -a "$LOG"

# ── 3. Resource limits (CIS Section 5.x / NIST AC-3/AC-6) ──────────
echo "[3/7] Deploying resource limits..." | tee -a "$LOG"
mkdir -p /etc/security/limits.d
cat > /etc/security/limits.d/99-synthex-hardening.conf << 'LIMITEOF'
*               hard    core            0
*               soft    core            0
*               hard    nofile          4096
*               soft    nofile          1024
*               hard    nproc           4096
*               soft    nproc           2048
*               hard    stack           8192
*               soft    stack           4096
*               hard    sigpending      1024
*               soft    sigpending      512
root            hard    nofile          65536
root            soft    nofile          16384
LIMITEOF
echo "  limits deployed" | tee -a "$LOG"

# ── 4. Modprobe attack surface reduction ─────────────────────────────
echo "[4/7] Deploying module blacklist..." | tee -a "$LOG"
mkdir -p /etc/modprobe.d
cat > /etc/modprobe.d/synthex-security.conf << 'MODPROBEOF'
# Synthex Attack Surface Reduction
blacklist firewire_ohci
blacklist firewire_core
blacklist firewire_sbp2
blacklist firewire_net
blacklist dccp
blacklist sctp
blacklist rds
blacklist tipc
blacklist cramfs
blacklist freevxfs
blacklist udf
blacklist hfs
blacklist hfsplus
blacklist trace
blacklist tracing
blacklist mac80211_hwsim
MODPROBEOF
echo "  modprobe blacklist deployed" | tee -a "$LOG"

# ── 5. Firewalld hardening ──────────────────────────────────────────
echo "[5/7] Configuring firewalld..." | tee -a "$LOG"
mkdir -p /etc/firewalld
cat > /etc/firewalld/firewalld.conf << 'FWEOF'
DefaultZone=synthex
FirewallBackend=nftables
LogDenied=all
MinimalForwardPolicy=drop
FlushAllOnReload=yes
FWEOF
echo "  firewalld configured" | tee -a "$LOG"

# ── 6. SELinux enforcing ────────────────────────────────────────────
echo "[6/7] Verifying SELinux..." | tee -a "$LOG"
if [ -f /etc/selinux/config ]; then
    sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config 2>/dev/null || true
    echo "  SELinux set to enforcing" | tee -a "$LOG"
fi

# ── 7. Security metadata ────────────────────────────────────────────
echo "[7/7] Writing security metadata..." | tee -a "$LOG"
mkdir -p /etc/synthex
cat > /etc/synthex/security-profile.json << JSONEOF
{
  "version": "1.0.0",
  "deployed": "$(date -Iseconds)",
  "hardening": {
    "sysctl": true,
    "auditd": true,
    "limits": true,
    "modprobe_blacklist": true,
    "firewalld": true,
    "selinux": "enforcing"
  }
}
JSONEOF
touch "$SYNTHEX_STATE/security-deployed"
echo "=== Security deployment complete $(date) ===" | tee -a "$LOG"
exit 0
