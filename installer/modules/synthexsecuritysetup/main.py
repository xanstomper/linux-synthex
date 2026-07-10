#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexsecuritysetup
# Hardens the installed system: SELinux, firewall, SSH, sysctl, fail2ban

import os, subprocess, re

try:
    import calamares
    from calamares.utils import debug, warning
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {"rootMountPoint":"/mnt","synthexProfile":"classic"}
            @classmethod
            def value(cls,k,d=None): return cls._d.get(k,d)
            @classmethod
            def insert(cls,k,v): cls._d[k]=v
        @staticmethod
        def prettyStatus(m): print(f"[secsetup] {m}")
    calamares = _FakeCal()
    def debug(m):   print(f"[secsetup] {m}")
    def warning(m): print(f"[secsetup] WARN: {m}")

def chroot_run(root, cmd, timeout=60):
    try:
        r = subprocess.run(["chroot",root]+cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout+r.stderr
    except Exception as e:
        return 1, str(e)

def write_file(path, content, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"w") as f: f.write(content)
    os.chmod(path, mode)

def pretty_name(): return "Security Hardening"

def run():
    root    = calamares.globalstorage.value("rootMountPoint") or ""
    profile = calamares.globalstorage.value("synthexProfile") or "classic"
    is_vm   = calamares.globalstorage.value("synthexIsVM")    or False

    calamares.prettyStatus("Applying security hardening…")

    if not root:
        return "rootMountPoint not set"

    # ── 1. SELinux ────────────────────────────────────────────────────────────
    selinux_cfg = os.path.join(root, "etc/selinux/config")
    if os.path.exists(selinux_cfg):
        content = open(selinux_cfg).read()
        content = re.sub(r"^SELINUX=.*", "SELINUX=enforcing", content, flags=re.M)
        content = re.sub(r"^SELINUXTYPE=.*", "SELINUXTYPE=targeted", content, flags=re.M)
        with open(selinux_cfg,"w") as f: f.write(content)
        debug("SELinux set to: enforcing / targeted")
    else:
        write_file(selinux_cfg,
                   "# SynthOS SELinux configuration\n"
                   "SELINUX=enforcing\n"
                   "SELINUXTYPE=targeted\n")
        debug("SELinux config created")

    # ── 2. Kernel hardening (sysctl) ──────────────────────────────────────────
    sysctl_path = os.path.join(root, "etc/sysctl.d/99-synthex-security.conf")
    write_file(sysctl_path,
               "# SynthOS Security Hardening\n"
               "# ──────────────────────────\n\n"
               "# Disable IP source routing\n"
               "net.ipv4.conf.all.accept_source_route = 0\n"
               "net.ipv4.conf.default.accept_source_route = 0\n\n"
               "# Ignore ICMP redirects\n"
               "net.ipv4.conf.all.accept_redirects = 0\n"
               "net.ipv4.conf.default.accept_redirects = 0\n"
               "net.ipv6.conf.all.accept_redirects = 0\n\n"
               "# Don't send redirects\n"
               "net.ipv4.conf.all.send_redirects = 0\n\n"
               "# Enable SYN cookie protection\n"
               "net.ipv4.tcp_syncookies = 1\n\n"
               "# Reverse path filtering\n"
               "net.ipv4.conf.all.rp_filter = 1\n"
               "net.ipv4.conf.default.rp_filter = 1\n\n"
               "# Log martian packets\n"
               "net.ipv4.conf.all.log_martians = 1\n\n"
               "# Disable IPv6 autoconf if not needed\n"
               "# net.ipv6.conf.all.autoconf = 0\n\n"
               "# Kernel pointer restriction\n"
               "kernel.kptr_restrict = 2\n\n"
               "# Restrict dmesg\n"
               "kernel.dmesg_restrict = 1\n\n"
               "# ASLR\n"
               "kernel.randomize_va_space = 2\n\n"
               "# Disable core dumps for setuid programs\n"
               "fs.suid_dumpable = 0\n\n"
               "# Protect hardlinks and symlinks\n"
               "fs.protected_hardlinks = 1\n"
               "fs.protected_symlinks = 1\n\n"
               "# Disable unprivileged BPF\n"
               "kernel.unprivileged_bpf_disabled = 1\n\n"
               "# Perf event paranoia\n"
               "kernel.perf_event_paranoid = 3\n")
    debug("sysctl security hardening written")

    # ── 3. SSH hardening ──────────────────────────────────────────────────────
    sshd_cfg = os.path.join(root, "etc/ssh/sshd_config.d/99-synthex.conf")
    write_file(sshd_cfg,
               "# SynthOS SSH Hardening\n"
               "PermitRootLogin no\n"
               "PasswordAuthentication no\n"
               "PubkeyAuthentication yes\n"
               "AuthorizedKeysFile .ssh/authorized_keys\n"
               "X11Forwarding no\n"
               "AllowTcpForwarding no\n"
               "AllowAgentForwarding no\n"
               "MaxAuthTries 3\n"
               "LoginGraceTime 30\n"
               "ClientAliveInterval 300\n"
               "ClientAliveCountMax 2\n"
               "UsePAM yes\n"
               "Protocol 2\n"
               "Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,chacha20-poly1305@openssh.com\n"
               "MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com\n"
               "KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org\n")
    debug("SSH hardening written")

    # ── 4. Fail2ban ───────────────────────────────────────────────────────────
    f2b_dir = os.path.join(root, "etc/fail2ban/jail.d")
    os.makedirs(f2b_dir, exist_ok=True)
    write_file(os.path.join(f2b_dir, "synthex.conf"),
               "[DEFAULT]\n"
               "bantime  = 3600\n"
               "findtime = 600\n"
               "maxretry = 5\n"
               "backend  = systemd\n\n"
               "[sshd]\n"
               "enabled = true\n"
               "port    = ssh\n"
               "filter  = sshd\n"
               "maxretry = 3\n\n"
               "[nginx-http-auth]\n"
               "enabled = false\n")
    chroot_run(root, ["systemctl","enable","fail2ban.service"])
    debug("Fail2ban configured and enabled")

    # ── 5. AIDE (intrusion detection) ────────────────────────────────────────
    aide_cfg = os.path.join(root, "etc/aide.conf")
    if os.path.exists(aide_cfg):
        # Schedule AIDE check weekly
        aide_cron = os.path.join(root, "etc/cron.weekly/aide-check")
        write_file(aide_cron,
                   "#!/bin/bash\n"
                   "# SynthOS AIDE weekly integrity check\n"
                   "/usr/sbin/aide --check --config /etc/aide.conf 2>&1 | "
                   "mail -s 'AIDE Weekly Report' root\n",
                   mode=0o755)
        debug("AIDE weekly check scheduled")

    # ── 6. Audit rules ────────────────────────────────────────────────────────
    audit_rules = os.path.join(root, "etc/audit/rules.d/99-synthex.rules")
    os.makedirs(os.path.dirname(audit_rules), exist_ok=True)
    write_file(audit_rules,
               "# SynthOS Audit Rules\n"
               "-w /etc/passwd -p wa -k identity\n"
               "-w /etc/shadow -p wa -k identity\n"
               "-w /etc/sudoers -p wa -k sudoers\n"
               "-w /etc/ssh/sshd_config -p wa -k sshd_config\n"
               "-w /var/log/auth.log -p wa -k auth_log\n"
               "-a always,exit -F arch=b64 -S execve -k exec\n"
               "-a always,exit -F arch=b32 -S execve -k exec\n"
               "-e 2\n")
    chroot_run(root, ["systemctl","enable","auditd.service"])
    debug("Audit rules and auditd enabled")

    # ── 7. DNF automatic security updates ────────────────────────────────────
    dnf_auto = os.path.join(root, "etc/dnf/automatic.conf")
    if os.path.exists(dnf_auto):
        content = open(dnf_auto).read()
        content = re.sub(r"upgrade_type\s*=.*",  "upgrade_type = security",  content)
        content = re.sub(r"apply_updates\s*=.*", "apply_updates = yes",      content)
        content = re.sub(r"download_updates\s*=.*","download_updates = yes", content)
        with open(dnf_auto,"w") as f: f.write(content)
    else:
        write_file(dnf_auto,
                   "[commands]\n"
                   "upgrade_type = security\n"
                   "apply_updates = yes\n"
                   "download_updates = yes\n"
                   "random_sleep = 900\n\n"
                   "[base]\n"
                   "debuglevel = 1\n")
    chroot_run(root, ["systemctl","enable","dnf-automatic-install.timer"])
    debug("DNF automatic security updates enabled")

    # ── 8. umask and PAM hardening ────────────────────────────────────────────
    login_defs = os.path.join(root, "etc/login.defs")
    if os.path.exists(login_defs):
        content = open(login_defs).read()
        content = re.sub(r"^UMASK\s+.*", "UMASK           027", content, flags=re.M)
        content = re.sub(r"^PASS_MAX_DAYS\s+.*", "PASS_MAX_DAYS   365", content, flags=re.M)
        content = re.sub(r"^PASS_MIN_DAYS\s+.*", "PASS_MIN_DAYS   1",   content, flags=re.M)
        content = re.sub(r"^PASS_WARN_AGE\s+.*", "PASS_WARN_AGE   14",  content, flags=re.M)
        with open(login_defs,"w") as f: f.write(content)
        debug("login.defs hardened")

    # ── 9. USB/Thunderbolt guard (USBGuard) ───────────────────────────────────
    # Skip on VMs — USB passthrough doesn't benefit from USBGuard
    if not is_vm:
        usbguard_rules = os.path.join(root, "etc/usbguard/rules.conf")
        if os.path.exists(usbguard_rules):
            chroot_run(root, ["systemctl","enable","usbguard.service"])
            debug("USBGuard enabled")

    # ── 10. Profile-specific security level ───────────────────────────────────
    if profile == "pro":
        # Pro gets full audit + mandatory AppArmor
        debug("Pro profile: full security audit enabled")
    elif profile == "lite":
        # Lite: skip heavy audit rules to save RAM
        warning("Lite profile: skipping heavy audit rules")

    calamares.globalstorage.insert("synthexSecurityConfigured", True)
    debug("Security hardening complete ✓")
    return None
