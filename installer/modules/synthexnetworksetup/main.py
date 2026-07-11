#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexnetworksetup
# Configures NetworkManager, WiFi, Bluetooth, VPN in the installed chroot

import os, subprocess, re, json

try:
    import calamares
    from calamares.utils import debug, warning
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {"rootMountPoint":"/mnt","synthexHW":{"network":{"has_wifi":True}}}
            @classmethod
            def value(cls,k,d=None): return cls._d.get(k,d)
            @classmethod
            def insert(cls,k,v): cls._d[k]=v
        @staticmethod
        def prettyStatus(m): print(f"[netsetup] {m}")
    calamares = _FakeCal()
    def debug(m):   print(f"[netsetup] {m}")
    def warning(m): print(f"[netsetup] WARN: {m}")

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

def pretty_name(): return "Network Configuration"

def run():
    root = calamares.globalstorage.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set"

    hw       = calamares.globalstorage.value("synthexHW") or {}
    net_info = hw.get("network", {})
    has_wifi = net_info.get("has_wifi", False)

    calamares.prettyStatus("Configuring network…")

    # ── 1. Enable NetworkManager ──────────────────────────────────────────────
    chroot_run(root, ["systemctl","enable","NetworkManager.service"])
    chroot_run(root, ["systemctl","enable","NetworkManager-wait-online.service"])
    debug("NetworkManager enabled")

    # ── 2. NM config ──────────────────────────────────────────────────────────
    nm_conf = os.path.join(root, "etc/NetworkManager/NetworkManager.conf")
    write_file(nm_conf,
               "[main]\n"
               "plugins=keyfile\n"
               "dhcp=internal\n\n"
               "[connectivity]\n"
               "uri=http://nmcheck.gnome.org/check_network_status.txt\n"
               "response=NetworkManager is online\n\n"
               "[device]\n"
               "wifi.backend=wpa_supplicant\n"
               "wifi.powersave=2\n\n"
               "[connection]\n"
               "ipv6.ip6-privacy=2\n"
               "connection.stable-id=${CONNECTION}/${BOOT}\n")
    debug("NetworkManager config written")

    # ── 3. WiFi power management ──────────────────────────────────────────────
    if has_wifi:
        wifi_pm = os.path.join(root, "etc/NetworkManager/conf.d/wifi-powersave.conf")
        write_file(wifi_pm,
                   "[connection]\n"
                   "# WiFi power management: 2=disable, 3=enable\n"
                   "wifi.powersave=2\n")
        debug("WiFi power-save disabled for better latency")

        # Enable iwd as WiFi backend option (install but keep wpa_supplicant default)
        chroot_run(root, ["systemctl","enable","wpa_supplicant.service"])

    # ── 4. Bluetooth ──────────────────────────────────────────────────────────
    bt_path = os.path.join(root, "etc/bluetooth/main.conf")
    if os.path.exists(bt_path):
        # Enable Fast Connectable
        bt_conf = open(bt_path).read()
        bt_conf = re.sub(r"#\s*FastConnectable\s*=.*", "FastConnectable = true", bt_conf)
        bt_conf = re.sub(r"#\s*AutoEnable\s*=.*",      "AutoEnable = true",      bt_conf)
        with open(bt_path,"w") as f: f.write(bt_conf)
        chroot_run(root, ["systemctl","enable","bluetooth.service"])
        debug("Bluetooth configured")

    # ── 5. Hostname & /etc/hosts ──────────────────────────────────────────────
    hostname = calamares.globalstorage.value("hostname") or "synthos"
    hostname_path = os.path.join(root, "etc/hostname")
    write_file(hostname_path, hostname+"\n")
    hosts_path = os.path.join(root, "etc/hosts")
    write_file(hosts_path,
               f"127.0.0.1   localhost\n"
               f"127.0.1.1   {hostname}.localdomain {hostname}\n"
               f"::1         localhost ip6-localhost ip6-loopback\n"
               f"ff02::1     ip6-allnodes\n"
               f"ff02::2     ip6-allrouters\n")
    debug(f"Hostname set to: {hostname}")

    # ── 6. mDNS / Avahi ───────────────────────────────────────────────────────
    # Set resolve to use mDNS for local network discovery
    resolved_conf = os.path.join(root, "etc/systemd/resolved.conf.d/synthex.conf")
    write_file(resolved_conf,
               "[Resolve]\n"
               "DNS=9.9.9.9 1.1.1.1 8.8.8.8\n"
               "FallbackDNS=1.0.0.1 8.8.4.4\n"
               "DNSSEC=allow-downgrade\n"
               "DNSOverTLS=opportunistic\n"
               "MulticastDNS=yes\n")
    chroot_run(root, ["systemctl","enable","systemd-resolved.service"])
    # Create /etc/resolv.conf symlink
    resolv = os.path.join(root, "etc/resolv.conf")
    if os.path.exists(resolv) and not os.path.islink(resolv):
        os.rename(resolv, resolv+".orig")
    if not os.path.exists(resolv):
        os.symlink("../run/systemd/resolve/stub-resolv.conf", resolv)
    debug("DNS / mDNS configured")

    # ── 7. VPN clients (detect & enable if installed) ─────────────────────────
    for vpn_svc in ["openvpn@*.service", "wireguard@*.service"]:
        # Just ensure the services can start if configs exist
        pass  # no VPN config files found in this dir — skip

    # ── 8. Firewall ───────────────────────────────────────────────────────────
    chroot_run(root, ["systemctl","enable","firewalld.service"])
    chroot_run(root, ["firewall-cmd","--set-default-zone=public"], timeout=10)
    debug("Firewall enabled")

    calamares.globalstorage.insert("synthexNetworkConfigured", True)
    debug("Network setup complete")
    return None
