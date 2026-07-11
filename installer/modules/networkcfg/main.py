#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: networkcfg
# Configures NetworkManager, hostname, DNS-over-TLS, and optional VPN
# in the installed chroot.  Reads networkcfg.conf and GlobalStorage.

import json
import os
import re
import shutil
import subprocess

try:
    import libcalamares
    from libcalamares.utils import debug, warning
    _GS      = libcalamares.globalStorage
    _JOB_CFG = libcalamares.job.configuration
except (ImportError, AttributeError):
    class _FakeGS:
        _d = {
            "rootMountPoint":   "/mnt",
            "hostname":         "synthos",
            "synthexHW":        {"network": {"has_wifi": True}},
            "dnsOverHTTPS":     False,
            "vpnEnabled":       False,
        }
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "saveNetworkConfiguration": True,
            "copyNMConnections":        True,
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[networkcfg] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[networkcfg] {m}")
    def warning(m): print(f"[networkcfg] WARN: {m}")


# Live-system NetworkManager connection directory
_HOST_NM_CONNECTIONS = "/etc/NetworkManager/system-connections"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chroot(root: str, cmd: list, timeout: int = 60):
    try:
        r = subprocess.run(
            ["chroot", root] + cmd,
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            debug(f"[networkcfg] rc={r.returncode} {' '.join(cmd)}: {out[:300]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        warning(f"[networkcfg] timed out: {' '.join(cmd)}")
        return 1, "timeout"
    except Exception as exc:
        warning(f"[networkcfg] error: {exc}")
        return 1, str(exc)


def _write(path: str, content: str, mode: int = 0o644) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, mode)


# ---------------------------------------------------------------------------
# Sub-steps
# ---------------------------------------------------------------------------

def _enable_networkmanager(root: str) -> None:
    """Enable NetworkManager and related services."""
    for svc in [
        "NetworkManager.service",
        "NetworkManager-wait-online.service",
        "NetworkManager-dispatcher.service",
    ]:
        unit = os.path.join(root, "usr/lib/systemd/system", svc)
        if os.path.isfile(unit):
            _chroot(root, ["systemctl", "enable", svc], timeout=20)
    debug("[networkcfg] NetworkManager enabled")


def _write_nm_conf(root: str, has_wifi: bool) -> None:
    """Write the main NetworkManager.conf."""
    nm_conf_path = os.path.join(root, "etc/NetworkManager/NetworkManager.conf")
    content = (
        "[main]\n"
        "plugins=keyfile\n"
        "dhcp=internal\n"
        "no-auto-default=*\n\n"
        "[connectivity]\n"
        "uri=http://nmcheck.gnome.org/check_network_status.txt\n"
        "response=NetworkManager is online\n"
        "interval=300\n\n"
        "[device]\n"
        "wifi.backend=wpa_supplicant\n"
        f"wifi.powersave={'2' if has_wifi else '3'}\n\n"
        "[connection]\n"
        "ipv6.ip6-privacy=2\n"
        "connection.stable-id=${CONNECTION}/${BOOT}\n\n"
        "[logging]\n"
        "level=WARN\n"
    )
    _write(nm_conf_path, content)
    debug("[networkcfg] NetworkManager.conf written")

    if has_wifi:
        wifi_pm = os.path.join(root, "etc/NetworkManager/conf.d/wifi-powersave.conf")
        _write(wifi_pm, "[connection]\nwifi.powersave=2\n")
        _chroot(root, ["systemctl", "enable", "wpa_supplicant.service"], timeout=20)
        debug("[networkcfg] WiFi power-save disabled, wpa_supplicant enabled")


def _set_hostname(root: str, hostname: str) -> None:
    """Write /etc/hostname and /etc/hosts."""
    if not hostname:
        hostname = "synthos"

    # Sanitise: RFC 1123 compatible
    hostname = re.sub(r"[^a-zA-Z0-9\-]", "-", hostname).strip("-") or "synthos"

    _write(os.path.join(root, "etc/hostname"), hostname + "\n")
    _write(
        os.path.join(root, "etc/hosts"),
        f"127.0.0.1   localhost\n"
        f"127.0.1.1   {hostname}.localdomain {hostname}\n"
        f"::1         localhost ip6-localhost ip6-loopback\n"
        f"ff02::1     ip6-allnodes\n"
        f"ff02::2     ip6-allrouters\n",
    )
    # Best-effort via hostnamectl (no D-Bus in chroot)
    _chroot(root, ["hostnamectl", "--transient", "set-hostname", hostname], timeout=10)
    debug(f"[networkcfg] Hostname → {hostname!r}")


def _configure_dns(root: str, dot_enabled: bool) -> None:
    """Write systemd-resolved config with optional DNS-over-TLS."""
    resolved_dir = os.path.join(root, "etc/systemd/resolved.conf.d")
    os.makedirs(resolved_dir, exist_ok=True)

    # Primary DNS: Quad9 (privacy-focused), Cloudflare, Google fallback
    dot_line = "DNSOverTLS=yes" if dot_enabled else "DNSOverTLS=opportunistic"
    _write(
        os.path.join(resolved_dir, "synthex.conf"),
        "[Resolve]\n"
        "DNS=9.9.9.9#dns.quad9.net 1.1.1.1#cloudflare-dns.com\n"
        "FallbackDNS=8.8.8.8#dns.google 1.0.0.1#cloudflare-dns.com\n"
        "DNSSEC=allow-downgrade\n"
        f"{dot_line}\n"
        "MulticastDNS=yes\n"
        "LLMNR=no\n",
    )
    _chroot(root, ["systemctl", "enable", "systemd-resolved.service"], timeout=20)

    # Replace /etc/resolv.conf with symlink to stub resolver
    resolv = os.path.join(root, "etc/resolv.conf")
    if os.path.isfile(resolv) and not os.path.islink(resolv):
        os.rename(resolv, resolv + ".orig")
    if not os.path.exists(resolv):
        os.symlink("../run/systemd/resolve/stub-resolv.conf", resolv)

    if dot_enabled:
        debug("[networkcfg] DNS-over-TLS enabled (Quad9 + Cloudflare)")
    else:
        debug("[networkcfg] systemd-resolved configured (DoT=opportunistic)")


def _configure_firewall(root: str) -> None:
    """Enable firewalld with a sensible default zone."""
    unit = os.path.join(root, "usr/lib/systemd/system/firewalld.service")
    if not os.path.isfile(unit):
        debug("[networkcfg] firewalld not present — skipping firewall config")
        return
    _chroot(root, ["systemctl", "enable", "firewalld.service"], timeout=20)
    debug("[networkcfg] Firewall (firewalld) enabled; default zone=public")


def _copy_nm_connections(root: str) -> None:
    """Copy live NetworkManager connections into the installed system."""
    src_dir = _HOST_NM_CONNECTIONS
    dst_dir = os.path.join(root, "etc/NetworkManager/system-connections")
    if not os.path.isdir(src_dir):
        debug("[networkcfg] No live NM connections to copy")
        return
    os.makedirs(dst_dir, exist_ok=True)
    copied = 0
    for fname in os.listdir(src_dir):
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            os.chmod(dst, 0o600)
            copied += 1
    debug(f"[networkcfg] Copied {copied} NM connection file(s) to target")


def _configure_bluetooth(root: str) -> None:
    """Enable Bluetooth service and patch /etc/bluetooth/main.conf."""
    unit = os.path.join(root, "usr/lib/systemd/system/bluetooth.service")
    if not os.path.isfile(unit):
        return
    _chroot(root, ["systemctl", "enable", "bluetooth.service"], timeout=20)

    bt_conf = os.path.join(root, "etc/bluetooth/main.conf")
    if os.path.isfile(bt_conf):
        with open(bt_conf, encoding="utf-8") as fh:
            text = fh.read()
        text = re.sub(r"#\s*FastConnectable\s*=.*", "FastConnectable = true",  text)
        text = re.sub(r"#\s*AutoEnable\s*=.*",      "AutoEnable = true",       text)
        with open(bt_conf, "w", encoding="utf-8") as fh:
            fh.write(text)
        debug("[networkcfg] Bluetooth: AutoEnable + FastConnectable set")


def _configure_vpn(root: str) -> None:
    """Enable VPN client services if their config exists (best-effort)."""
    # WireGuard
    wg_dir = os.path.join(root, "etc/wireguard")
    if os.path.isdir(wg_dir):
        for conf in os.listdir(wg_dir):
            if conf.endswith(".conf"):
                iface = conf[:-5]
                _chroot(root,
                        ["systemctl", "enable", f"wg-quick@{iface}.service"],
                        timeout=20)
                debug(f"[networkcfg] WireGuard interface enabled: {iface}")

    # OpenVPN
    ovpn_dir = os.path.join(root, "etc/openvpn/client")
    if os.path.isdir(ovpn_dir):
        for conf in os.listdir(ovpn_dir):
            if conf.endswith(".conf"):
                name = conf[:-5]
                _chroot(root,
                        ["systemctl", "enable", f"openvpn-client@{name}.service"],
                        timeout=20)
                debug(f"[networkcfg] OpenVPN client enabled: {name}")


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "Network Configuration"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    cfg  = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}
    hw   = _GS.value("synthexHW") or {}
    net  = hw.get("network", {})
    has_wifi = net.get("has_wifi", False)

    hostname  = _GS.value("hostname") or _GS.value("hostname", "synthos")
    dot       = bool(_GS.value("dnsOverHTTPS") or _GS.value("dnsOverTLS"))
    vpn_req   = bool(_GS.value("vpnEnabled"))
    copy_nm   = bool(cfg.get("copyNMConnections", True))

    libcalamares.prettyStatus("Enabling NetworkManager…")
    _enable_networkmanager(root)

    libcalamares.prettyStatus("Writing NetworkManager configuration…")
    _write_nm_conf(root, has_wifi)

    libcalamares.prettyStatus(f"Setting hostname: {hostname}…")
    _set_hostname(root, hostname)

    libcalamares.prettyStatus("Configuring DNS…")
    _configure_dns(root, dot)

    libcalamares.prettyStatus("Configuring firewall…")
    _configure_firewall(root)

    libcalamares.prettyStatus("Configuring Bluetooth…")
    _configure_bluetooth(root)

    if copy_nm:
        libcalamares.prettyStatus("Copying network connections…")
        _copy_nm_connections(root)

    if vpn_req:
        libcalamares.prettyStatus("Configuring VPN…")
        _configure_vpn(root)

    debug("[networkcfg] Network configuration complete.")
    _GS.insert("networkcfgConfigured", True)
    return None
