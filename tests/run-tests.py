#!/usr/bin/env python3
"""Synthex integration tests."""
import os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = 0
failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))

# 1. Systemd services
print("📋 Systemd services:")
svc_dir = os.path.join(ROOT, "systemd")
expected_svcs = ["synthex-desktopd", "synthex-hwdaemon", "synthex-gpu-setupd", "synthex-stored",
                 "synthex-workspace", "synthex-webappd", "synthex-ai-hub", "synthex-blueprint",
                 "synthex-recovery", "synthex-firstboot", "synthex-oobe", "synthex-control-center",
                 "synthex-studiocd", "synthex-marketplace"]
for svc in expected_svcs:
    path = os.path.join(svc_dir, f"{svc}.service")
    check(svc, os.path.exists(path))

# 2. Desktop files
print("\n📋 Desktop launchers:")
desktop_dir = os.path.join(ROOT, "desktop", "applications")
expected_desktop = ["synthex-control-center", "synthex-software-center", "synthex-gaming-center",
                    "synthex-ai-hub", "synthex-studio", "synthex-security-dashboard", "synthex-workspace"]
for d in expected_desktop:
    path = os.path.join(desktop_dir, f"{d}.desktop")
    exists = os.path.exists(path)
    valid = False
    if exists:
        content = open(path).read()
        valid = "Type=Application" in content and "Exec=" in content
    check(d, exists and valid)

# 3. App icons
print("\n📋 App icons:")
icon_dir = os.path.join(ROOT, "branding", "icons")
for icon in ["synthex-control-center", "synthex-ai-hub", "synthex-gaming-center",
             "synthex-software-center", "synthex-studio", "synthex-security-dashboard", "synthex-workspace"]:
    path = os.path.join(icon_dir, f"{icon}.svg")
    check(icon, os.path.exists(path) and os.path.getsize(path) > 100)

# 4. Layout configs
print("\n📋 Layout configs:")
for layout in ["gaming", "balanced", "minimal", "macos", "windows"]:
    path = os.path.join(ROOT, "layouts", f"{layout}.json")
    check(f"{layout}.json", os.path.exists(path))

# 5. Mode scripts
print("\n📋 Mode scripts:")
for mode in ["gaming", "dev", "battery", "balanced", "creator", "streaming"]:
    path = os.path.join(ROOT, "modes", f"{mode}.sh")
    check(f"{mode}.sh", os.path.exists(path) and os.access(path, os.X_OK))

# 6. Source code directories
print("\n📋 Source code:")
src_dir = os.path.join(ROOT, "src")
expected_src = ["synthex-desktopd", "synthex-hwdaemon", "synthex-gpu-setupd", "synthex-stored",
                "synthex-control-center", "synthex-oobe", "synthex-studio", "synthex-gaming-center",
                "synthex-software-center", "synthex-ai-hub", "synthex-blueprint", "synthex-webapp-engine",
                "synthex-workspace", "synthex-recovery", "synthex-security-dashboard", "synthex-boot",
                "synthex-installer"]
for s in expected_src:
    path = os.path.join(src_dir, s)
    check(s, os.path.exists(path))

# 6b. GUI entry point wrappers
print("\n📋 GUI entry point wrappers:")
gui_wrappers = [
    ("synthex-ai-hub/synthex-ai-hub", "AI Hub"),
    ("synthex-gaming-center/synthex-gaming-center", "Gaming Center"),
    ("synthex-software-center/synthex-software-center", "Software Center"),
    ("synthex-control-center/synthex-control-center", "Control Center"),
    ("synthex-studio/synthex-studio", "Studio"),
    ("synthex-security-dashboard/synthex-security-dashboard", "Security Dashboard"),
]
for path, name in gui_wrappers:
    full = os.path.join(src_dir, path)
    check(f"{name} entry point", os.path.exists(full) and os.access(full, os.X_OK))

# 6c. System service entry point wrappers
print("\n📋 System service entry point wrappers:")
svc_wrappers = [
    ("synthex-oobe/synthex-oobe", "OOBE"),
    ("synthex-recovery/synthex-recovery", "Recovery"),
    ("synthex-blueprint/synthex-blueprint", "Blueprint"),
    ("synthex-desktopd/synthex-desktopd", "Desktop Daemon"),
    ("synthex-gpu-setupd/synthex-gpu-setupd", "GPU Setup Daemon"),
    ("synthex-hwdaemon/synthex-hwdaemon", "HW Daemon"),
    ("synthex-studio/synthex-studiocd", "Studio Daemon"),
    ("synthex-webapp-engine/synthex-webappd", "Web App Daemon"),
]
for path, name in svc_wrappers:
    full = os.path.join(src_dir, path)
    check(f"{name} entry point", os.path.exists(full) and os.access(full, os.X_OK))

# 6d. synthex.py CLI — all commands compile + reference real tools
print("\n📋 synthex.py CLI command coverage:")
synthex_py = open(os.path.join(ROOT, "src", "synthex.py")).read()
expected_cmds = ["update","rollback","snapshot","mode","status","layout","theme",
    "install","remove","search","drivers","hw-info","ai","firewall","proton","gpu",
    "blueprint","backup","tray","welcome","recovery","gaming","codecs","nvidia",
    "kernel","service","logs","locale","ananicy","aur","usb","input",
    "power-profiles","upgrade","disk","report","timeshift","handheld","tour","appimage","hermes","agent","codex","kb"]
for cmd in expected_cmds:
    check(f"synthex {cmd}", f'"{cmd}"' in synthex_py or f"'{cmd}'" in synthex_py)

# 7. Security
print("\n📋 Security:")
check("SELinux policy", os.path.exists(os.path.join(ROOT, "security", "selinux-policy", "synthex-policy.te")))
check("SELinux Makefile", os.path.exists(os.path.join(ROOT, "security", "selinux-policy", "Makefile")))
check("sysctl hardening", os.path.exists(os.path.join(ROOT, "security", "hardening", "sysctl.conf")))
check("auditd rules", os.path.exists(os.path.join(ROOT, "security", "hardening", "auditd.rules")))

# 8. Packaging
print("\n📋 Packaging:")
check("DNF groups XML", os.path.exists(os.path.join(ROOT, "packages", "groups", "synthex-comps.xml")))
check("GPG signing key", os.path.exists(os.path.join(ROOT, "packages", "synthex-repos", "RPM-GPG-KEY-synthex")))
spec_count = len(os.listdir(os.path.join(ROOT, "packages", "spec-files")))
check(f"RPM spec files ({spec_count})", spec_count >= 15)

# 9. CI/CD
print("\n📋 CI/CD:")
ci_dir = os.path.join(ROOT, "ci", "github-actions")
workflow_count = len([f for f in os.listdir(ci_dir) if f.endswith(".yml")]) if os.path.exists(ci_dir) else 0
check(f"GitHub Actions workflows ({workflow_count})", workflow_count >= 6)

# 10. Safety system
print("\n📋 Safety system:")
safety_dir = os.path.join(ROOT, "safety")
for f in ["protected-packages.conf", "synthex-safety-check.sh", "synthex-safety.service",
          "rescue-usb-creator.sh", "dnf-synthex-protect.py"]:
    check(f"safety/{f}", os.path.exists(os.path.join(safety_dir, f)))

# 11. udev rules
print("\n📋 udev rules:")
udev_dir = os.path.join(ROOT, "udev")
for f in ["69-synthex-firmware.rules", "70-synthex-controllers.rules",
          "71-synthex-rgb.rules", "72-synthex-handheld.rules"]:
    check(f"udev/{f}", os.path.exists(os.path.join(udev_dir, f)))

# 12. Control Center pages
print("\n📋 Control Center pages:")
cc_pages = os.path.join(ROOT, "src", "synthex-control-center", "ui", "pages")
for p in ["Drivers", "RGB", "Snapshots", "Kernel", "Controllers"]:
    check(f"{p}.qml", os.path.exists(os.path.join(cc_pages, f"{p}.qml")))

# 13. OOBE bundles
print("\n📋 OOBE bundles:")
bundles_dir = os.path.join(ROOT, "src", "synthex-oobe", "bundles")
for b in ["gaming", "creator", "developer", "rgb", "emulation"]:
    path = os.path.join(bundles_dir, f"{b}.sh")
    check(f"{b}.sh", os.path.exists(path) and os.access(path, os.X_OK))
check("BundlePicker.qml", os.path.exists(os.path.join(ROOT, "src", "synthex-oobe", "ui", "pages", "BundlePicker.qml")))

# 14. AI assistant
print("\n📋 AI assistant:")
ai_dir = os.path.join(ROOT, "src", "synthex-ai-hub")
for m in ["driver_assistant.py", "troubleshooter.py", "performance_advisor.py", "synthex-ai-assistant"]:
    check(m, os.path.exists(os.path.join(ai_dir, m)))

# 15. Windows migration tool
print("\n📋 Windows migration:")
check("synthex-migrate-windows.py", os.path.exists(os.path.join(ROOT, "src", "synthex-installer", "synthex-migrate-windows.py")))

# 16. Performance configs
print("\n📋 Performance configs:")
check("99-synthex-performance.conf", os.path.exists(os.path.join(ROOT, "security", "hardening", "99-synthex-performance.conf")))
check("zram-synthex.conf", os.path.exists(os.path.join(ROOT, "security", "hardening", "zram-synthex.conf")))

# 17. Safety packaging spec
print("\n📋 Safety spec:")
check("synthex-safety.spec", os.path.exists(os.path.join(ROOT, "packages", "spec-files", "synthex-safety.spec")))

# 18. Feature parity — Bazzite/CachyOS/Nobara packages present
print("\n📋 Feature parity (Bazzite/CachyOS/Nobara):")
gaming_spec = os.path.join(ROOT, "packages", "spec-files", "synthex-gaming-platform.spec")
ksinc = os.path.join(ROOT, "build", "kickstart", "synthex-gaming-packages.ksinc")
for feature, needle in [
    ("Prism Launcher", "prism-launcher"),
    ("EmuDeck", "emudeck"),
    ("RetroArch", "retroarch"),
    ("Sunshine (streaming)", "sunshine"),
    ("Moonlight", "moonlight"),
    ("Monado (VR)", "monado"),
    ("ALVR (VR)", "alvr"),
    ("SteamVR", "steamvr"),
    ("GreenWithEnvy (NVIDIA)", "greenwithenvy"),
    ("Decky Loader", "decky-loader"),
    ("Handheld Daemon", "handheld-daemon"),
    ("Distrobox", "distrobox"),
    ("Input Remapper", "input-remapper"),
    ("xpadneo", "xpadneo"),
    ("rtkit (audio)", "rtkit"),
]:
    found = (open(gaming_spec).read().find(needle) >= 0) or (open(ksinc).read().find(needle) >= 0)
    check(feature, found)

# 19. Essentials (Flatpak/VPN/scanner/disk-health) + Creator (color/tablet)
print("\n📋 Essentials + Creator specs:")
for spec in ["synthex-essentials.spec", "synthex-creator-platform.spec"]:
    check(spec, os.path.exists(os.path.join(ROOT, "packages", "spec-files", spec)))
ess_spec = os.path.join(ROOT, "packages", "spec-files", "synthex-essentials.spec")
for feature, needle in [
    ("Flatseal", "flatseal"),
    ("Warehouse", "warehouse"),
    ("WireGuard", "wireguard-tools"),
    ("OpenVPN", "openvpn"),
    ("SANE scanning", "sane-backends"),
    ("Simple Scan", "simple-scan"),
    ("SMART monitoring", "smartmontools"),
    ("NVMe CLI", "nvme-cli"),
    ("fwupd", "fwupd"),
]:
    check(feature, open(ess_spec).read().find(needle) >= 0)
creator_spec = os.path.join(ROOT, "packages", "spec-files", "synthex-creator-platform.spec")
for feature, needle in [
    ("OBS browser source", "browser-source"),
    ("Color management (colord)", "colord"),
    ("DisplayCAL", "displaycal"),
    ("Wacom tablet", "libwacom"),
    ("EasyEffects", "easyeffects"),
]:
    check(feature, open(creator_spec).read().find(needle) >= 0)

# 20. Flathub preconfigured + low-latency audio
print("\n📋 Flatpak + audio configs:")
check("Flathub repo file", os.path.exists(os.path.join(ROOT, "packages", "spec-files", "synthex-essentials.spec")) and "flathub" in open(ess_spec).read().lower())
check("setup-flatpak.sh", os.path.exists(os.path.join(ROOT, "scripts", "setup-flatpak.sh")))
check("pipewire-low-latency.conf", os.path.exists(os.path.join(ROOT, "desktop", "defaults", "pipewire-low-latency.conf")))

# 21. Boot speed (perf-boot)
print("\n📋 Boot speed:")
boot_dir = os.path.join(ROOT, "boot")
for f in ["boot-analyze.sh", "boot-optimize.sh", "boot-profile.service"]:
    check(f"boot/{f}", os.path.exists(os.path.join(boot_dir, f)))

# 22. Resource slimming (least hoggy)
print("\n📋 Resource slimming:")
svc_slim_dir = os.path.join(ROOT, "services")
for f in ["service-audit.sh", "synthex-slim-services.sh", "synthex-idle-tune.sh", "synthex-slim.service"]:
    check(f"services/{f}", os.path.exists(os.path.join(svc_slim_dir, f)))

# 23. Daemon memory limits
print("\n📋 Daemon memory limits:")
for svc in ["synthex-desktopd", "synthex-stored", "synthex-ai-hub", "synthex-hwdaemon"]:
    path = os.path.join(ROOT, "systemd", f"{svc}.service")
    content = open(path).read() if os.path.exists(path) else ""
    check(f"{svc} MemoryMax", "MemoryMax" in content)

# 24. ISO build wiring — meta-packages in kickstart + comps + rootfs
print("\n📋 ISO build wiring:")
for ks in ["synthex-plasma.ks", "synthex-gnome.ks", "synthex-hyprland.ks"]:
    path = os.path.join(ROOT, "build", "kickstart", ks)
    content = open(path).read() if os.path.exists(path) else ""
    for meta in ["synthex-safety", "synthex-essentials", "synthex-creator-platform", "synthex-gaming-platform"]:
        check(f"{ks} includes {meta}", meta in content)

comps = os.path.join(ROOT, "packages", "groups", "synthex-comps.xml")
comps_content = open(comps).read() if os.path.exists(comps) else ""
for grp in ["synthex-safety", "synthex-essentials", "synthex-creator"]:
    check(f"comps.xml has {grp} group", f"<id>{grp}</id>" in comps_content)

rootfs = os.path.join(ROOT, "scripts", "build-rootfs-in-docker.sh")
rootfs_content = open(rootfs).read() if os.path.exists(rootfs) else ""
check("rootfs installs meta-packages", "synthex-safety synthex-essentials" in rootfs_content)
check("rootfs enables synthex services", "synthex-safety" in rootfs_content and "systemctl enable" in rootfs_content)

# 25. Kickstart enables Synthex platform services
print("\n📋 Kickstart service enables:")
plasma_ks = os.path.join(ROOT, "build", "kickstart", "synthex-plasma.ks")
plasma_content = open(plasma_ks).read() if os.path.exists(plasma_ks) else ""
for svc in ["synthex-safety.service", "synthex-slim.service", "synthex-boot-profile.service",
            "synthex-oobe.service", "synthex-control-center.service"]:
    check(f"plasma.ks enables {svc}", svc in plasma_content)

# 26. ISO size right-sizing — bloat removed, focused gaming-desktop scope
print("\n📋 ISO size (de-bloated):")
bloat = ["python3-tensorflow", "python3-torch", "cuda-toolkit", "cudnn", "tensorrt",
         "kubelet", "kubeadm", "terraform", "ansible-core", "pulumi", "vagrant",
         "ghc", "scala", "kotlin", "erlang", "ocaml", "swi-prolog", "flutter",
         "octave", "julia", "nerd-fonts-complete", "gfortran", "valgrind",
         "systemtap", "mercurial", "subversion", "helm-secrets"]
for b in bloat:
    # bloat package should NOT appear as an install line (allow it in comments)
    lines = [l.strip() for l in plasma_content.splitlines()
             if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("-")]
    present = any(l == b or l.startswith(b + " ") for l in lines)
    check(f"plasma.ks excludes {b}", not present)

# ISO compression should be zstd (faster than xz, matches CachyOS)
iso_script = os.path.join(ROOT, "build", "livecd", "build-iso.sh")
iso_content = open(iso_script).read() if os.path.exists(iso_script) else ""
check("ISO uses zstd compression", "zstd" in iso_content and "compression-level=19" in iso_content)

# 27. Live ISO experience — auto-login + installer shortcut + polkit
print("\n📋 Live ISO experience:")
check("sddm-live.conf exists", os.path.exists(os.path.join(ROOT, "desktop", "sddm", "sddm-live.conf")))
check("sddm-live.conf has autologin", "Autologin" in open(os.path.join(ROOT, "desktop", "sddm", "sddm-live.conf")).read() and "liveuser" in open(os.path.join(ROOT, "desktop", "sddm", "sddm-live.conf")).read())
check("installer desktop file exists", os.path.exists(os.path.join(ROOT, "desktop", "applications", "synthex-installer.desktop")))
check("installer uses pkexec", "pkexec calamares" in open(os.path.join(ROOT, "desktop", "applications", "synthex-installer.desktop")).read())
check("kickstart has SDDM autologin.conf", "autologin.conf" in plasma_content and "liveuser" in plasma_content)
check("kickstart has polkit installer rule", "49-synthex-live-installer.rules" in plasma_content)
check("kickstart places installer on desktop", "synthex-installer.desktop" in plasma_content and "Desktop" in plasma_content)

# 28. Live ISO security — passwordless sudo + firewall enabled
print("\n📋 Live ISO security:")
check("kickstart has liveuser NOPASSWD sudo", "liveuser ALL=(ALL) NOPASSWD: ALL" in plasma_content)
check("firewalld NOT disabled in kickstart", "systemctl disable firewalld" not in plasma_content)

# 29. Distro parity packages — Bazzite, CachyOS, Nobara, Mint feature specs
print("\n📋 Distro parity feature specs:")
parity_specs = ["synthex-codec-pack", "synthex-welcome", "synthex-mint-extras",
                "synthex-bazzite-extras", "synthex-cachy-tuning", "synthex-nobara-fixes"]
for spec in parity_specs:
    path = os.path.join(ROOT, "packages", "spec-files", f"{spec}.spec")
    check(f"{spec}.spec exists", os.path.exists(path))

# Check meta-standard pulls all parity specs
meta_std = os.path.join(ROOT, "packages", "spec-files", "synthex-meta-standard.spec")
meta_std_content = open(meta_std).read() if os.path.exists(meta_std) else ""
for spec in parity_specs:
    check(f"meta-standard requires {spec}", spec in meta_std_content)

# 30. Distro parity source files — ujust, nvidia installer, codec installer, tuning
print("\n📋 Distro parity source files:")
check("ujust tool exists", os.path.exists(os.path.join(ROOT, "src", "synthex-ujust", "ujust")))
ujust = open(os.path.join(ROOT, "src", "synthex-ujust", "ujust")).read()
for cmd in ["gaming-setup", "install-nvidia", "install-codecs", "tune-performance",
            "install-bundle-gaming", "fix-audio", "rollback", "setup-zram"]:
    check(f"ujust has '{cmd}' command", cmd in ujust)

check("nvidia-installer exists", os.path.exists(os.path.join(ROOT, "src", "synthex-nvidia-installer", "synthex-nvidia-installer")))
nvidia_inst = open(os.path.join(ROOT, "src", "synthex-nvidia-installer", "synthex-nvidia-installer")).read()
check("nvidia-installer detects GPU", "lspci" in nvidia_inst and "NVIDIA" in nvidia_inst)
check("nvidia-installer builds akmod", "akmods" in nvidia_inst)
check("nvidia-installer handles Secure Boot", "mokutil" in nvidia_inst)

check("codec-installer exists", os.path.exists(os.path.join(ROOT, "src", "synthex-codec-installer", "synthex-codec-installer")))
codec_inst = open(os.path.join(ROOT, "src", "synthex-codec-installer", "synthex-codec-installer")).read()
check("codec-installer installs x264", "x264" in codec_inst)
check("codec-installer installs x265", "x265" in codec_inst)
check("codec-installer installs dav1d", "dav1d" in codec_inst)

check("cachy-tuning exists", os.path.exists(os.path.join(ROOT, "src", "synthex-cachy-tuning", "apply-cachy-tuning.sh")))
cachy_tune = open(os.path.join(ROOT, "src", "synthex-cachy-tuning", "apply-cachy-tuning.sh")).read()
check("cachy-tuning has vm.swappiness", "vm.swappiness" in cachy_tune)
check("cachy-tuning has TCP BBR", "tcp_congestion_control" in cachy_tune and "bbr" in cachy_tune)
check("cachy-tuning has ZRAM config", "zram-generator" in cachy_tune)
check("cachy-tuning has I/O scheduler", "scheduler" in cachy_tune)

# 31. Codec pack completeness — all major codecs present
print("\n📋 Codec pack completeness:")
codec_spec = open(os.path.join(ROOT, "packages", "spec-files", "synthex-codec-pack.spec")).read()
for codec in ["x264", "x265", "dav1d", "openh264", "gstreamer1-plugins-ugly-free",
              "gstreamer1-plugins-bad-free-extras", "libdvdcss", "flac", "opus",
              "lame", "ffmpeg", "libva", "intel-vaapi-driver"]:
    check(f"codec-pack includes {codec}", codec in codec_spec)

# 32. Desktop utility tools — daily-use features
print("\n📋 Desktop utility tools (daily-use features):")
check("synthex-desktop-tools.spec exists", os.path.exists(os.path.join(ROOT, "packages", "spec-files", "synthex-desktop-tools.spec")))
dt_spec = open(os.path.join(ROOT, "packages", "spec-files", "synthex-desktop-tools.spec")).read()
for pkg in ["flameshot", "fcitx5", "samba", "xrdp", "blueman", "gammastep",
            "syncthing", "copyq", "keepassxc", "deja-dup", "borgbackup",
            "transmission", "gnome-calculator", "evince", "orca", "cheese",
            "gparted", "grub-customizer", "firewall-config", "gsmartcontrol"]:
    check(f"desktop-tools includes {pkg}", pkg in dt_spec)
check("meta-standard requires synthex-desktop-tools", "synthex-desktop-tools" in meta_std_content)

# 33. Synthex system management tools (kernel/service/log/locale)
print("\n📋 System management tools:")
for tool in ["synthex-kernel-manager", "synthex-service-manager", "synthex-log-viewer", "synthex-locale-setup"]:
    path = os.path.join(ROOT, "src", tool, tool)
    check(f"{tool} exists", os.path.exists(path))

km = open(os.path.join(ROOT, "src", "synthex-kernel-manager", "synthex-kernel-manager")).read()
for cmd in ["list", "install", "switch", "remove", "info", "cleanup"]:
    check(f"kernel-manager has '{cmd}'", cmd in km)

sm = open(os.path.join(ROOT, "src", "synthex-service-manager", "synthex-service-manager")).read()
for cmd in ["list", "start", "stop", "restart", "enable", "disable", "status", "failed"]:
    check(f"service-manager has '{cmd}'", cmd in sm)

lv = open(os.path.join(ROOT, "src", "synthex-log-viewer", "synthex-log-viewer")).read()
for cmd in ["boot", "kernel", "errors", "warnings", "service", "follow", "search"]:
    check(f"log-viewer has '{cmd}'", cmd in lv)

ls = open(os.path.join(ROOT, "src", "synthex-locale-setup", "synthex-locale-setup")).read()
for cmd in ["locale", "timezone", "keyboard", "list-locales", "list-timezones"]:
    check(f"locale-setup has '{cmd}'", cmd in ls)

# 34. Calamares installer config completeness
print("\n📋 Calamares installer config:")
calamares = os.path.join(ROOT, "installer", "config", "calamares-settings.conf")
cal_content = open(calamares).read() if os.path.exists(calamares) else ""
for module in ["welcome", "partition", "mount", "locale", "keyboard", "users",
               "bootloader", "services", "networkcfg", "fstab", "finished",
               "dracut", "initramfs", "displaymanager", "grubcfg"]:
    check(f"calamares has {module} module", module in cal_content)

# 35. System utilities — network, fonts, recovery, monitoring, privacy
print("\n📋 System utilities (network/fonts/recovery/monitoring):")
su_spec_path = os.path.join(ROOT, "packages", "spec-files", "synthex-system-utilities.spec")
check("synthex-system-utilities.spec exists", os.path.exists(su_spec_path))
su_spec = open(su_spec_path).read()
for pkg in ["mtr", "traceroute", "tcpdump", "bind-utils", "iperf3", "nmap",
            "lm_sensors", "thermald", "psensor", "testdisk", "photorec",
            "gddrescue", "google-noto-arabic-fonts", "google-noto-cjk-fonts",
            "wqy-zenhei-fonts", "hunspell-en", "hunspell-es", "hunspell-fr",
            "tor", "proxychains-ng", "openconnect", "ModemManager",
            "fio", "hdparm", "btrfs-progs", "e2fsprogs", "xfsprogs",
            "exfatprogs", "ntfs-3g", "usbutils", "pciutils", "lshw"]:
    check(f"system-utilities includes {pkg}", pkg in su_spec)
check("meta-standard requires synthex-system-utilities", "synthex-system-utilities" in meta_std_content)

# 36. Calamares module configurations (individual .conf files)
print("\n📋 Calamares module configurations:")
calamares_modules = [
    "welcome", "partition", "users", "bootloader", "displaymanager",
    "packages", "services-systemd", "fstab", "locale", "keyboard",
    "grubcfg", "unpackfs", "finished", "shellprocess", "removeuser",
    "machineid", "networkcfg", "dracut"
]
for mod in calamares_modules:
    path = os.path.join(ROOT, "installer", "modules", mod, f"{mod}.conf")
    check(f"calamares {mod}.conf exists", os.path.exists(path))

# 37. Calamares branding descriptor
print("\n📋 Calamares branding:")
branding_desc = os.path.join(ROOT, "branding", "calamares", "branding.desc")
check("branding.desc exists", os.path.exists(branding_desc))
bd = open(branding_desc).read() if os.path.exists(branding_desc) else ""
check("branding has productName", "productName" in bd)
check("branding has sidebar style", "SidebarBackground" in bd)
check("branding has slideshow", "slideshow" in bd)

# 38. Post-install scripts (referenced by Calamares shellprocess)
print("\n📋 Post-install scripts:")
for script in ["post-install.sh", "hardware-detect.sh", "apply-theme.sh"]:
    path = os.path.join(ROOT, "src", "synthex-installer", script)
    check(f"{script} exists", os.path.exists(path))

post_install = open(os.path.join(ROOT, "src", "synthex-installer", "post-install.sh")).read()
check("post-install removes liveuser", "liveuser" in post_install and "userdel" in post_install)
check("post-install enables services", "systemctl enable" in post_install)
check("post-install rebuilds initramfs", "dracut" in post_install)
check("post-install updates GRUB", "grub2-mkconfig" in post_install)
check("post-install cleans sudoers", "10-liveuser" in post_install)

hw_detect = open(os.path.join(ROOT, "src", "synthex-installer", "hardware-detect.sh")).read()
check("hardware-detect detects NVIDIA", "NVIDIA" in hw_detect and "lspci" in hw_detect)
check("hardware-detect detects AMD", "AMD" in hw_detect)
check("hardware-detect detects Intel", "Intel" in hw_detect)
check("hardware-detect writes JSON profile", "synthex-hw-profile.json" in hw_detect)
check("hardware-detect auto-installs NVIDIA", "akmod-nvidia" in hw_detect)
check("hardware-detect configures ZRAM", "zram-generator" in hw_detect)
check("hardware-detect configures I/O scheduler", "scheduler" in hw_detect)
check("hardware-detect detects handhelds", "steamdeck" in hw_detect and "handheld" in hw_detect)

apply_theme = open(os.path.join(ROOT, "src", "synthex-installer", "apply-theme.sh")).read()
check("apply-theme sets GRUB theme", "GRUB_THEME" in apply_theme)
check("apply-theme sets Plymouth", "plymouth-set-default-theme" in apply_theme)
check("apply-theme sets SDDM theme", "synthex-sddm-theme" in apply_theme)
check("apply-theme sets GTK theme", "gtk-theme-name" in apply_theme)
check("apply-theme sets cursor theme", "Bibata" in apply_theme)
check("apply-theme sets font config", "fontconfig" in apply_theme)
check("apply-theme sets wallpaper", "wallpaper" in apply_theme.lower())

# 39. Desktop entries for system tools
print("\n📋 System tool desktop entries:")
for tool in ["synthex-kernel-manager", "synthex-service-manager", "synthex-log-viewer", "synthex-locale-setup"]:
    path = os.path.join(ROOT, "desktop", "applications", f"{tool}.desktop")
    check(f"{tool}.desktop exists", os.path.exists(path))

# 40. Partition config — Btrfs default with subvolumes (critical for snapshots)
print("\n📋 Partition config (Btrfs + snapshots):")
part_conf = open(os.path.join(ROOT, "installer", "modules", "partition", "partition.conf")).read()
check("partition uses btrfs default", "btrfs" in part_conf)
check("partition has @ subvolume", "@" in part_conf and 'mountpoint: "/"' in part_conf)
check("partition has @home subvolume", "@home" in part_conf)
check("partition has @snapshots subvolume", "@snapshots" in part_conf)
check("partition allows manual", "allowManualPartitioning" in part_conf)
check("partition has LUKS support", "luks" in part_conf)

# 41. Users config — proper groups for gaming/admin
print("\n📋 Users config (groups + autologin):")
users_conf = open(os.path.join(ROOT, "installer", "modules", "users", "users.conf")).read()
for group in ["wheel", "audio", "video", "docker", "libvirt", "kvm", "input"]:
    check(f"users config includes {group} group", group in users_conf)

# 42. Services config — all Synthex services enabled
print("\n📋 Services config (Synthex services enabled):")
svc_conf = open(os.path.join(ROOT, "installer", "modules", "services-systemd", "services-systemd.conf")).read()
for svc in ["NetworkManager", "bluetooth", "sddm", "cups", "fwupd", "firewalld",
            "synthex-safety", "synthex-oobe", "synthex-control-center", "synthex-hwdaemon"]:
    check(f"services config enables {svc}", svc in svc_conf)

# 43. New standalone tool specs — have %build, %install, %files, %changelog
print("\n📋 Standalone tool specs (buildable RPMs):")
tool_specs = ["synthex-ujust", "synthex-nvidia-installer", "synthex-codec-installer",
              "synthex-kernel-manager", "synthex-service-manager", "synthex-log-viewer",
              "synthex-locale-setup"]
for spec in tool_specs:
    path = os.path.join(ROOT, "packages", "spec-files", f"{spec}.spec")
    check(f"{spec}.spec exists", os.path.exists(path))
    content = open(path).read()
    check(f"{spec} has Source0", "Source0" in content)
    check(f"{spec} has %prep", "%prep" in content)
    check(f"{spec} has %build", "%build" in content)
    check(f"{spec} has %install", "%install" in content)
    check(f"{spec} has %files", "%files" in content)
    check(f"{spec} has %changelog", "%changelog" in content)
    check(f"{spec} installs to bindir", "%{_bindir}" in content)

# 44. Fixed specs — all 8 previously broken specs now have build sections
print("\n📋 Fixed specs (now have %build/%install):")
for spec in ["synthex-bazzite-extras", "synthex-cachy-tuning", "synthex-codec-pack",
             "synthex-desktop-tools", "synthex-mint-extras", "synthex-nobara-fixes",
             "synthex-system-utilities", "synthex-welcome"]:
    content = open(os.path.join(ROOT, "packages", "spec-files", f"{spec}.spec")).read()
    check(f"{spec} has %build", "%build" in content)
    check(f"{spec} has %install", "%install" in content)
    check(f"{spec} has %changelog", "%changelog" in content)

# 45. Nobara fixes — invalid Requires fixed
print("\n📋 Nobara fixes spec fixes:")
nb = open(os.path.join(ROOT, "packages", "spec-files", "synthex-nobara-fixes.spec")).read()
check("nobara-fixes has Source0", "Source0" in nb)
check("nobara-fixes fixed selinux req", "selinux-policy-targeted" in nb)
check("nobara-fixes fixed prime req", "nvidia-prime" in nb)
check("nobara-fixes no invalid synthex-selinux", "synthex-selinux-adjustments" not in nb)
check("nobara-fixes no invalid synthex-prime", "synthex-prime" not in nb)

# 46. Cachy tuning — Source files + tuned profiles + ananicy rules
print("\n📋 Cachy tuning spec completeness:")
ct = open(os.path.join(ROOT, "packages", "spec-files", "synthex-cachy-tuning.spec")).read()
check("cachy-tuning has Source0 (script)", "Source0:" in ct and "apply-cachy-tuning" in ct)
check("cachy-tuning has tuned gaming profile", "synthex-gaming" in ct)
check("cachy-tuning has ananicy rules source", "ananicy-rules" in ct)
check("cachy-tuning installs sysctl conf", "99-synthex-cachy.conf" in ct)
check("cachy-tuning has vm.swappiness", "vm.swappiness" in ct)

# 47. Source files exist for all specs with Source0
print("\n📋 Source files exist:")
for path, desc in [("src/synthex-ujust/ujust", "ujust"), ("src/synthex-nvidia-installer/synthex-nvidia-installer", "nvidia-inst"), ("src/synthex-codec-installer/synthex-codec-installer", "codec-inst"), ("src/synthex-kernel-manager/synthex-kernel-manager", "kernel-mgr"), ("src/synthex-service-manager/synthex-service-manager", "service-mgr"), ("src/synthex-log-viewer/synthex-log-viewer", "log-viewer"), ("src/synthex-locale-setup/synthex-locale-setup", "locale-setup"), ("src/synthex-nobara-fixes/apply-nobara-fixes.sh", "nobara-fixes"), ("src/synthex-welcome/synthex-welcome", "welcome"), ("src/synthex-cachy-tuning/apply-cachy-tuning.sh", "cachy-tuning"), ("src/synthex-cachy-tuning/tuned-profiles/synthex-gaming/tuned.conf", "gaming tuned"), ("src/synthex-cachy-tuning/ananicy-rules/synthex-rules.conf", "ananicy rules")]:
    check(desc, os.path.exists(os.path.join(ROOT, path)))

# 48. Repo infrastructure scripts
print("\n📋 Repository infrastructure:")
for script in ["generate-gpg-keys.sh", "build-all-rpms.sh", "setup-build-env.sh"]:
    check(f"{script} exists", os.path.exists(os.path.join(ROOT, "scripts", script)))
bld = open(os.path.join(ROOT, "scripts", "build-all-rpms.sh")).read()
check("build-all runs rpmbuild", "rpmbuild" in bld)
check("build-all creates repo", "createrepo" in bld)
check("build-all supports --sign", "--sign" in bld)
gpg = open(os.path.join(ROOT, "scripts", "generate-gpg-keys.sh")).read()
check("gpg-keys generates RSA 4096", "RSA" in gpg and "4096" in gpg)
check("gpg-keys exports public key", "RPM-GPG-KEY-synthex" in gpg)
check("synthex.repo exists", os.path.exists(os.path.join(ROOT, "scripts", "synthex.repo")))

# 49. Nobara fixes script + Welcome app content
print("\n📋 Nobara fixes + welcome app:")
nf = open(os.path.join(ROOT, "src", "synthex-nobara-fixes", "apply-nobara-fixes.sh")).read()
check("nobara-fixes adjusts SELinux", "setsebool" in nf)
check("nobara-fixes configures PipeWire", "pipewire" in nf)
check("nobara-fixes sets vm.max_map_count", "max_map_count" in nf)
check("nobara-fixes installs udev rules", "70-synthex-gaming.rules" in nf)
wf = open(os.path.join(ROOT, "src", "synthex-welcome", "synthex-welcome")).read()
check("welcome uses GTK4", "Gtk" in wf and "4.0" in wf)
check("welcome uses libadwaita", "Adw" in wf)
check("welcome has driver action", "synthex-control-center" in wf)
check("welcome has codec action", "synthex-codec-installer" in wf)
check("welcome has gaming action", "ujust" in wf)

# 50. System configuration files — 29 critical configs
print("\n📋 System configuration files:")
config_files = [
    ("configs/dracut/dracut-synthex.conf", "dracut initramfs config"),
    ("configs/grub/grub-default", "GRUB defaults"),
    ("configs/sddm/sddm-synthex.conf", "SDDM display manager config"),
    ("configs/plymouth/plymouthd-synthex.conf", "Plymouth boot splash config"),
    ("configs/networkmanager/nm-synthex.conf", "NetworkManager config"),
    ("configs/firewalld/synthex.xml", "firewalld zone"),
    ("configs/flatpak/flathub.flatpakrepo", "Flathub flatpak repo"),
    ("configs/flatpak/synthex.flatpakrepo", "Synthex flatpak repo"),
    ("configs/snapper/snapper-root.conf", "Snapper snapshot config"),
    ("configs/sudoers/synthex-sudoers", "sudoers config"),
    ("configs/polkit/49-synthex-nopasswd.rules", "polkit rules"),
    ("configs/dnf/dnf-automatic.conf", "DNF automatic updates"),
    ("configs/journald/journald-synthex.conf", "journald config"),
    ("configs/timesyncd/timesyncd-synthex.conf", "timesyncd NTP config"),
    ("configs/modprobe/synthex-blacklist.conf", "modprobe blacklist"),
    ("configs/modprobe/synthex-nvidia.conf", "NVIDIA modprobe options"),
    ("configs/modprobe/synthex-audio.conf", "audio modprobe options"),
    ("configs/modprobe/synthex-thinkpad.conf", "ThinkPad modprobe options"),
    ("configs/crypttab/crypttab", "LUKS crypttab"),
    ("configs/locale/locale.conf", "locale config"),
    ("configs/locale/vconsole.conf", "vconsole config"),
    ("configs/locale/synthex-locale-gen", "locale generation script"),
    ("configs/secureboot/synthex-shim.conf", "Secure Boot shim config"),
    ("configs/btrfs/btrfs-scrub-timer.conf", "Btrfs scrub timer"),
    ("configs/btrfs/synthex-btrfs-balance", "Btrfs balance cron"),
    ("configs/live/synthex-live-setup.service", "live image service"),
    ("configs/live/live-setup.sh", "live setup script"),
    ("configs/live/install-synthex.desktop", "installer desktop entry"),
    ("configs/calamares-branding/show.qml", "Calamares slideshow"),
]
for path, desc in config_files:
    check(desc, os.path.exists(os.path.join(ROOT, path)))

# 51. System config spec — synthex-system-config
print("\n📋 synthex-system-config spec:")
sc_path = os.path.join(ROOT, "packages", "spec-files", "synthex-system-config.spec")
check("synthex-system-config.spec exists", os.path.exists(sc_path))
sc = open(sc_path).read()
check("system-config has 28 Source declarations", sc.count("Source") >= 28)
check("system-config has %build", "%build" in sc)
check("system-config has %install", "%install" in sc)
check("system-config installs dracut conf", "dracut.conf.d" in sc)
check("system-config installs grub default", "default/grub" in sc)
check("system-config installs sddm conf", "sddm.conf.d" in sc)
check("system-config installs firewalld zone", "firewalld/zones" in sc)
check("system-config installs flatpak remotes", "flatpak/remotes.d" in sc)
check("system-config installs sudoers", "sudoers.d" in sc)
check("system-config installs modprobe", "modprobe.d" in sc)
check("system-config installs live setup", "live-setup" in sc)
check("system-config has %changelog", "%changelog" in sc)
check("meta-standard requires synthex-system-config", "synthex-system-config" in meta_std_content)

# 52. Calamares branding spec
print("\n📋 Calamares branding spec:")
cb_path = os.path.join(ROOT, "packages", "spec-files", "synthex-calamares-branding.spec")
check("synthex-calamares-branding.spec exists", os.path.exists(cb_path))
cb = open(cb_path).read()
check("calamares-branding has Source0 (branding.desc)", "branding.desc" in cb)
check("calamares-branding has Source1 (show.qml)", "show.qml" in cb)
check("calamares-branding has %build", "%build" in cb)
check("calamares-branding has %install", "%install" in cb)
check("calamares-branding installs to branding dir", "calamares/branding/synthex" in cb)
check("calamares-branding has %changelog", "%changelog" in cb)

# 53. Config content validation — critical settings
print("\n📋 Config content validation:")
dracut = open(os.path.join(ROOT, "configs/dracut/dracut-synthex.conf")).read()
check("dracut uses zstd compression", "zstd" in dracut)
check("dracut has hostonly mode", "hostonly" in dracut)
check("dracut includes GPU drivers", "nvidia" in dracut and "amdgpu" in dracut)
check("dracut includes btrfs", "btrfs" in dracut)

grub = open(os.path.join(ROOT, "configs/grub/grub-default")).read()
check("grub has quiet splash cmdline", "quiet splash" in grub)
check("grub blacklists nouveau", "nouveau" in grub)
check("grub has theme", "GRUB_THEME" in grub)
check("grub has cryptodisk", "CRYPTODISK" in grub)
check("grub has recovery", "RECOVERY" in grub)

sddm = open(os.path.join(ROOT, "configs/sddm/sddm-synthex.conf")).read()
check("sddm uses Wayland", "wayland" in sddm.lower())
check("sddm has synthex theme", "synthex-sddm-theme" in sddm)
check("sddm has cursor theme", "CursorTheme" in sddm)

fw = open(os.path.join(ROOT, "configs/firewalld/synthex.xml")).read()
check("firewalld has SSH service", "ssh" in fw)
check("firewalld has gaming ports", "27036" in fw)
check("firewalld has RDP", "3389" in fw)
check("firewalld has VNC", "5900" in fw)

sudoers = open(os.path.join(ROOT, "configs/sudoers/synthex-sudoers")).read()
check("sudoers allows wheel group", "wheel" in sudoers)
check("sudoers has passwordless dnf", "NOPASSWD" in sudoers and "dnf" in sudoers)
check("sudoers has sudo timeout", "timestamp_timeout" in sudoers)

nvidia_mod = open(os.path.join(ROOT, "configs/modprobe/synthex-nvidia.conf")).read()
check("nvidia modprobe enables modeset", "modeset=1" in nvidia_mod)
check("nvidia modprobe has power management", "DynamicPowerManagement" in nvidia_mod)

# 54. Kernel patches — BORE scheduler, gaming latency, tickless, VM tuning
print("\n📋 Kernel patches:")
for patch in ["synthex-0001-bore-scheduler.patch", "synthex-0002-gaming-latency.patch",
              "synthex-0003-tickless-gaming.patch", "synthex-0004-vm-gaming-tuning.patch"]:
    check(f"{patch} exists", os.path.exists(os.path.join(ROOT, "kernel", "patches", patch)))

bore = open(os.path.join(ROOT, "kernel", "patches", "synthex-0001-bore-scheduler.patch")).read()
check("BORE patch has SCHED_BORE", "SCHED_BORE" in bore)
check("BORE patch has fair.c", "fair.c" in bore)
check("BORE patch has burst", "burst" in bore.lower())

latency = open(os.path.join(ROOT, "kernel", "patches", "synthex-0002-gaming-latency.patch")).read()
check("latency patch has sched_latency_ns", "sched_latency_ns" in latency)
check("latency patch reduces granularity", "min_granularity" in latency)

tickless = open(os.path.join(ROOT, "kernel", "patches", "synthex-0003-tickless-gaming.patch")).read()
check("tickless patch has NO_HZ_FULL", "NO_HZ_FULL" in tickless)

vm_patch = open(os.path.join(ROOT, "kernel", "patches", "synthex-0004-vm-gaming-tuning.patch")).read()
check("VM patch has swappiness", "swappiness" in vm_patch)
check("VM patch has watermark", "watermark" in vm_patch)

# 55. Kernel config (defconfig)
print("\n📋 Kernel config:")
kconfig = open(os.path.join(ROOT, "kernel", "configs/synthex-x86_64-defconfig")).read()
check("kernel config has BORE", "SCHED_BORE" in kconfig)
check("kernel config has NO_HZ_FULL", "NO_HZ_FULL" in kconfig)
check("kernel config has HZ_1000", "HZ_1000" in kconfig)
check("kernel config has PREEMPT", "PREEMPT" in kconfig)
check("kernel config has SCHEDUTIL", "SCHEDUTIL" in kconfig)
check("kernel config has ZRAM", "ZRAM" in kconfig)
check("kernel config has BTRFS", "BTRFS_FS" in kconfig)
check("kernel config has ZSTD", "ZSTD" in kconfig)
check("kernel config has AMDGPU", "DRM_AMDGPU" in kconfig)
check("kernel config has I915", "DRM_I915" in kconfig)
check("kernel config has TCP BBR", "TCP_CONG_BBR" in kconfig)
check("kernel config has HIBERNATION", "HIBERNATION" in kconfig)
check("kernel config has LTO", "LTO" in kconfig)

# 56. Gaming optimization configs
print("\n📋 Gaming optimization configs:")
for f in ["limits.conf", "sysctl-gaming.conf", "environment-gaming.conf"]:
    check(f"{f} exists", os.path.exists(os.path.join(ROOT, "configs/gaming", f)))

limits = open(os.path.join(ROOT, "configs/gaming/limits.conf")).read()
check("limits has audio rtprio", "rtprio" in limits and "audio" in limits)
check("limits has nofile", "nofile" in limits and "1048576" in limits)

gaming_sysctl = open(os.path.join(ROOT, "configs/gaming/sysctl-gaming.conf")).read()
check("gaming sysctl has TCP BBR", "tcp_congestion_control" in gaming_sysctl and "bbr" in gaming_sysctl)
check("gaming sysctl has max_map_count", "max_map_count" in gaming_sysctl)

gaming_env = open(os.path.join(ROOT, "configs/gaming/environment-gaming.conf")).read()
check("gaming env has Proton HIDRAW", "PROTON_ENABLE_HIDRAW" in gaming_env)
check("gaming env has DXVK", "DXVK" in gaming_env)
check("gaming env has WINEFSYNC", "WINEFSYNC" in gaming_env)

# 57. Theme files — GTK4, GTK3, SDDM
print("\n📋 Theme files:")
for f in [("branding/theme/synthex-gtk4/gtk.css", "GTK4 CSS"),
          ("branding/theme/synthex-gtk3/gtk.css", "GTK3 CSS"),
          ("branding/theme/synthex-sddm-theme/Main.qml", "SDDM QML"),
          ("branding/theme/synthex-sddm-theme/metadata.desktop", "SDDM metadata"),
          ("branding/theme/synthex-sddm-theme/theme.conf", "SDDM config")]:
    check(f[1], os.path.exists(os.path.join(ROOT, f[0])))

gtk4 = open(os.path.join(ROOT, "branding/theme/synthex-gtk4/gtk.css")).read()
check("GTK4 has accent color", "synthex_accent" in gtk4)
check("GTK4 has dark bg", "#1a1a2e" in gtk4)
check("GTK4 has headerbar", "headerbar" in gtk4)

sddm_qml = open(os.path.join(ROOT, "branding/theme/synthex-sddm-theme/Main.qml")).read()
check("SDDM has login card", "loginCard" in sddm_qml)
check("SDDM has clock", "Clock" in sddm_qml)
check("SDDM has username", "username" in sddm_qml)
check("SDDM has power off", "powerOff" in sddm_qml)

# 58. Hyprland enhancements
print("\n📋 Hyprland enhancements:")
for f in ["waybar-style.css", "wlogout-layout", "wlogout-style.css"]:
    check(f, os.path.exists(os.path.join(ROOT, "desktop/hyprland", f)))

waybar_css = open(os.path.join(ROOT, "desktop/hyprland/waybar-style.css")).read()
check("waybar has workspaces", "workspaces" in waybar_css)
check("waybar has gamemode", "gamemode" in waybar_css)
check("waybar has accent", "#6C88A8" in waybar_css)

wlogout = open(os.path.join(ROOT, "desktop/hyprland/wlogout-layout")).read()
check("wlogout has lock", "lock" in wlogout)
check("wlogout has shutdown", "shutdown" in wlogout)

# 59. New specs
print("\n📋 New specs (gaming-optimizations, kernel, themes):")
for spec in ["synthex-gaming-optimizations", "synthex-kernel", "synthex-themes"]:
    content = open(os.path.join(ROOT, "packages/spec-files", f"{spec}.spec")).read()
    check(f"{spec} has %build", "%build" in content)
    check(f"{spec} has %install", "%install" in content)
    check(f"{spec} has %changelog", "%changelog" in content)

go = open(os.path.join(ROOT, "packages/spec-files/synthex-gaming-optimizations.spec")).read()
check("gaming-opt installs limits.d", "security/limits.d" in go)
check("gaming-opt installs sysctl.d", "sysctl.d" in go)

ks = open(os.path.join(ROOT, "packages/spec-files/synthex-kernel.spec")).read()
check("kernel spec has BORE patch", "bore-scheduler" in ks)
check("kernel spec has defconfig", "defconfig" in ks)

ts = open(os.path.join(ROOT, "packages/spec-files/synthex-themes.spec")).read()
check("themes spec has GTK4 CSS", "gtk4.css" in ts)
check("themes spec has SDDM QML", "Main.qml" in ts)
check("meta-standard requires synthex-themes", "synthex-themes" in meta_std_content)
check("meta-standard requires synthex-gaming-optimizations", "synthex-gaming-optimizations" in meta_std_content)
check("meta-standard requires synthex-kernel", "synthex-kernel" in meta_std_content)

# 59b. Systemd service hardening
print("\n📋 Systemd service hardening:")
svc_dir = os.path.join(ROOT, "systemd")
hardening_directives = ["ProtectSystem", "PrivateTmp", "NoNewPrivileges",
                        "SystemCallArchitectures", "ProtectKernelTunables",
                        "ProtectControlGroups"]
for svc in sorted(os.listdir(svc_dir)):
    if not svc.endswith(".service"): continue
    path = os.path.join(svc_dir, svc)
    content = open(path).read()
    count = sum(1 for d in hardening_directives if d in content)
    check(f"{svc} hardened ({count}/{len(hardening_directives)})", count >= 3)

# 60. Kernel build script
print("\n📋 Kernel build script:")
kbs = open(os.path.join(ROOT, "scripts/build-synthex-kernel.sh")).read()
check("kernel-build applies patches", "patch" in kbs)
check("kernel-build has patch list", "PATCHES" in kbs)
check("kernel-build has BORE", "bore-scheduler" in kbs)
check("kernel-build has defconfig", "defconfig" in kbs)
check("kernel-build supports --install", "--install" in kbs)

# 61. synthex.target — groups all services
print("\n📋 synthex.target integration:")
st = open(os.path.join(ROOT, "systemd/synthex.target")).read()
check("synthex.target exists", os.path.exists(os.path.join(ROOT, "systemd/synthex.target")))
check("target requires dbus", "Requires=dbus.service" in st)
for want in ["synthex-desktopd", "synthex-stored", "synthex-hwdaemon", "synthex-workspace",
             "synthex-recovery", "synthex-blueprint", "synthex-ai-hub"]:
    check(f"target Wants {want}", want in st)

# 62. Makefile build targets
print("\n📋 Makefile build targets:")
mf = open(os.path.join(ROOT, "Makefile")).read()
for t in ["build", "build-desktopd", "build-stored", "build-hwdaemon",
          "build-gpu-setupd", "build-control-center", "build-studio"]:
    check(f"make {t}", f"{t}:" in mf)

# 63. Installer config — all modules referenced in sequence exist on disk
print("\n📋 Installer module completeness:")
cal = open(os.path.join(ROOT, "installer/config/calamares-settings.conf")).read()
mod_dir = os.path.join(ROOT, "installer/modules")
on_disk = set(d for d in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, d)))
# Parse YAMLish — extract items under sequence -> - exec:
seq_modules = set()
in_exec = False
for line in cal.splitlines():
    if line.strip().startswith("- exec:"):
        in_exec = True
        continue
    if in_exec:
        if line.strip().startswith("- ") and not line.strip().startswith("#"):
            m = re.search(r'- (\S+)', line)
            if m:
                mod = m.group(1)
                if not any(c in mod for c in ":/@"):
                    seq_modules.add(mod)
        elif line.strip().startswith("show:") or line.strip().startswith("#"):
            continue
        elif line.strip() and not line.startswith(" ") and not line.startswith("-"):
            break  # exited the exec block
standards = {"mount"}  # built-in Calamares C++ modules, no config dir needed
for m in sorted(seq_modules):
    if m in on_disk or m in standards:
        check(f"calamares module '{m}'", True)
    else:
        check(f"calamares module '{m}'", False)

# 64. Distro parity features — new Nobara/CachyOS/Mint/Arch tools
print("\n📋 Distro parity tools (Nobara/CachyOS/Mint/Arch):")
parity_tools = [
    ("ananicy", "src/synthex-cachy-tuning/synthex-ananicy", "CachyOS auto-nice"),
    ("ananicy service", "systemd/synthex-ananicy.service", "systemd"),
    ("AUR helper", "src/synthex-aur", "Arch AUR"),
    ("USB writer", "src/synthex-usb-writer", "Mint USB writer"),
    ("zstd config", "src/synthex-cachy-tuning/zstd-everything.conf", "CachyOS zstd"),
    ("input remapper", "src/synthex-input-remapper", "Nobara input mapper"),
    ("gaming session desktop", "desktop/applications/synthex-gaming-session.desktop", "Bazzite session"),
]
for name, path, origin in parity_tools:
    full = os.path.join(ROOT, path)
    check(f"{origin}: {name}", os.path.exists(full))
    if os.path.isfile(full) and not any(full.endswith(e) for e in [".conf", ".desktop", ".service"]):
        check(f"{name} executable", os.access(full, os.X_OK))

# 64. Synthex Agent platform — full stack check
print("\n📋 Synthex Agent Platform:")
synthex_items = [
    ("frontend", "src/synthex-agent/synthex-agent", True),
    ("daemon", "src/synthex-agent/daemon/synthex-agentd", True),
    ("QML panel", "src/synthex-agent/ui/Main.qml", False),
    ("Codex IDE", "src/synthex-agent/codex/ui/Codex.qml", False),
    ("DBus XML", "src/synthex-agent/dbus/org.synthex.Agent.xml", False),
    ("DBus service", "src/synthex-agent/dbus/org.synthex.Agent.service", False),
    ("app entry", "desktop/applications/synthex-agent.desktop", False),
    ("codex entry", "desktop/applications/synthex-codex.desktop", False),
    ("autostart daemon", "desktop/autostart/synthex-agent-daemon.desktop", False),
    ("systemd service", "systemd/synthex-agent.service", False),
    ("icon", "branding/icons/synthex-agent.svg", False),
]
for name, path, check_exec in synthex_items:
    full = os.path.join(ROOT, path)
    check(f"Synthex Agent {name}", os.path.exists(full))
    if check_exec and os.path.exists(full):
        check(f"Synthex Agent {name} executable", os.access(full, os.X_OK))

# Agent daemon architecture checks
d = open(os.path.join(ROOT, "src/synthex-agent/daemon/synthex-agentd")).read()
check("DBus service object", "dbus.service.Object" in d)
check("org.synthex.Agent bus", "org.synthex.Agent" in d)
check("coordinator agent", "class CoordinatorAgent" in d)
check("code agent", "class CodeAgent" in d)
check("system agent", "class SystemAgent" in d)
check("research agent", "class ResearchAgent" in d)
check("agent orchestrator", "class AgentOrchestrator" in d)
check("knowledge base", "class KnowledgeBase" in d)
check("tool registry", "class ToolRegistry" in d)
check("memory system", "class MemorySystem" in d)
check("no HTTP server", "HTTPServer" not in d and "BaseHTTPRequestHandler" not in d)

# Installer + target integration
st = open(os.path.join(ROOT, "systemd/synthex.target")).read()
check("synthex.target Wants agent service", "synthex-agent" in st)
sc = open(os.path.join(ROOT, "installer/modules/services-systemd/services-systemd.conf")).read()
check("installer enables agent service", "synthex-agent" in sc)

# 65. Packaging integrity — every spec's first-party install path must exist
print("\n📋 Spec integrity (install paths):")
import glob as _glob, re as _re, os as _os
TOPDIRS = ("desktop/","src/","systemd/","configs/","branding/","installer/","etc/","build/","kernel/","services/","safety/","tests/","docs/","udev/","dbus/","layouts/","modes/","profiles/","scripts/")
_spec_broken = 0
def _expand(p, macros):
    return _re.sub(r'%\{(\w+)\}', lambda m: macros.get(m.group(1), m.group(0)), p)
for _spec in sorted(_glob.glob(os.path.join(ROOT, "packages/spec-files/*.spec"))):
    _s = open(_spec, encoding="utf-8", errors="replace").read()
    _macros = dict(_re.findall(r'^%global\s+(\w+)\s+(\S+)', _s, _re.M))
    for _m in _re.finditer(r'(?m)^\s*(?:install\s+(?:-\S+\s+)*|cp\s+(?:-\S+\s+)*)(\S+)', _s):
        _p = _expand(_m.group(1).strip('"'), _macros)
        if _p.startswith('%') or _p.startswith('/'): continue
        if not _p.startswith(TOPDIRS): continue
        _full = _os.path.join(ROOT, _p)
        if '*' in _p:
            _base = _os.path.dirname(_full)
            if _base and not _os.path.isdir(_base): _spec_broken += 1
        elif not _os.path.exists(_full):
            _spec_broken += 1
check("specs: all first-party install paths exist", _spec_broken == 0,
      f"{_spec_broken} broken")

# 66. Every spec has %files + a Name (buildable sanity)
_bad = [f for f in _glob.glob(os.path.join(ROOT, "packages/spec-files/*.spec"))
        if not _re.search(r'^Name:\s*\S+', open(f, encoding="utf-8", errors="replace").read(), _re.M)
        or not _re.search(r'^%files', open(f, encoding="utf-8", errors="replace").read(), _re.M)]
check("specs: all have Name + %files", len(_bad) == 0, f"{len(_bad)} bad")

# 67. Core components have spec coverage (no unpackaged src dirs)
_all_spec_text = ""
for _f in _glob.glob(os.path.join(ROOT, "packages/spec-files/*.spec")):
    _all_spec_text += open(_f, encoding="utf-8", errors="replace").read()
for _crate in ["synthguard", "synthshield", "synthvault", "synthidentity", "synthnet",
               "synthupdate", "synthbox", "synthex-blueprint", "synthex-boot",
               "synthex-studio", "synthex-webapp-engine", "synthex-predictive-launch",
               "synthex-widgets", "synthex-app-manager"]:
    check(f"spec coverage: {_crate}", f"Name:           {_crate}" in _all_spec_text or _crate in _all_spec_text)

# 68. sysusers for every service with a system User=
for _svc, _user in [("synthex-brain.service", "synthex-brain"),
                    ("synthex-agent-sandbox.service", "synthex-agent")]:
    _unit = open(os.path.join(ROOT, "systemd", _svc)).read()
    _sysu = _os.path.exists(os.path.join(ROOT, "systemd", _user + ".sysusers"))
    check(f"sysusers: {_user}", ("User=" + _user) not in _unit or _sysu)

# 69. No hardcoded personal users in shipped units
_leak = []
for _u in _glob.glob(os.path.join(ROOT, "systemd/*.service")):
    _t = open(_u).read()
    if _re.search(r'^User=(?!root$)\w+$', _t, _re.M) and "User=root" not in _t:
        for _mm in _re.finditer(r'^User=(\w+)$', _t, _re.M):
            _n = _mm.group(1)
            if not _n.startswith("synthex") and _n not in ("_", "messagebus", "systemd-", "dnf"):
                _leak.append((_os.path.basename(_u), _n))
check("no personal User= in units", len(_leak) == 0, str(_leak[:3]))

# 70. Build pipeline present
for _f in ["build/scripts/make-srctars.sh", "build/scripts/local-repo.sh"]:
    check(f"pipeline: {_f}", _os.access(_os.path.join(ROOT, _f), _os.X_OK))

# 71. Synthex Aegis Behavioral Attack Prevention Suite
print("\n📋 Synthex Aegis Endpoint Security:")
aegis_dir = os.path.join(ROOT, "src", "synthex-aegis")
check("aegis engine exists", os.path.exists(os.path.join(aegis_dir, "aegis_engine.py")))
check("aegis gui exists", os.path.exists(os.path.join(aegis_dir, "aegis_gui.py")))
check("aegis daemon exists", os.path.exists(os.path.join(aegis_dir, "aegis_daemon.py")))
check("aegis desktop launcher exists", os.path.exists(os.path.join(aegis_dir, "synthex-aegis.desktop")))

# Verify Aegis Behavioral Engine functionality
try:
    sys.path.insert(0, aegis_dir)
    from aegis_engine import AegisEngine
    ae = AegisEngine.get_instance()
    check("aegis engine instance initialized", ae is not None)
    status = ae.get_status()
    check("aegis realtime protection active", status.get("realtime_active") is True)
    check("aegis reverse shell shield active", status.get("reverse_shell_shield") is True)
    check("aegis memory integrity shield active", status.get("memory_integrity") is True)
    check("aegis integrity baselines audit", isinstance(ae.audit_system_baselines(), list))
    check("aegis SUID privilege escalation auditor", isinstance(ae.audit_suid_binaries(), list))
except Exception as _e:
    check("aegis engine functional validation", False, str(_e))

# Aegis production daemon + service integration
import subprocess as _sp
import tempfile as _tf
import json as _json
check("aegis systemd service unit exists", os.path.exists(os.path.join(ROOT, "systemd", "synthex-aegis.service")))
_unit = open(os.path.join(ROOT, "systemd", "synthex-aegis.service")).read() if os.path.exists(os.path.join(ROOT, "systemd", "synthex-aegis.service")) else ""
check("aegis unit hardened + installable", all(k in _unit for k in ["ExecStart=/usr/bin/synthex-aegis-daemon", "ProtectSystem=strict", "WantedBy=multi-user.target"]))
_target = open(os.path.join(ROOT, "systemd", "synthex.target")).read()
check("aegis wired into synthex.target", "synthex-aegis.service" in _target)
_desktop = open(os.path.join(aegis_dir, "synthex-aegis.desktop")).read()
check("aegis desktop file portable (no home paths)", "/home/" not in _desktop and "Exec=synthex-aegis" in _desktop)
check("aegis daemon launcher exists", os.access(os.path.join(aegis_dir, "synthex-aegis-daemon"), os.X_OK))
try:
    _tmp = _tf.mkdtemp(prefix="aegis-rt-")
    with open(os.path.join(_tmp, "config.json"), "w") as _f:
        _json.dump({"realtime_protection": True, "auto_terminate_malicious_pids": False,
                    "desktop_notifications": False, "privilege_escalation_guard": False}, _f)
    _r = _sp.run([sys.executable, os.path.join(aegis_dir, "aegis_daemon.py"),
                  "--once", "--data-dir", _tmp], capture_output=True, text=True, timeout=120)
    check("aegis daemon --once full audit pass", _r.returncode == 0 and "Single audit pass complete" in _r.stdout,
          _r.stderr[-200:] if _r.returncode != 0 else None)
    import shutil as _sh
    _sh.rmtree(_tmp, ignore_errors=True)
except Exception as _e:
    check("aegis daemon --once full audit pass", False, str(_e))

_mk = open(os.path.join(ROOT, "Makefile")).read()
check("aegis make install target present", "install-aegis:" in _mk and "/usr/bin/synthex-aegis-daemon" in _mk)
check("aegis packaging unit registered", os.path.exists(os.path.join(ROOT, "packages", "services-systemd", "synthex-aegis.service")))

# 72. Synthex System Doctor, Auto-Repair & Anti-Bricking Suite
print("\n📋 Synthex System Doctor & Anti-Bricking Auto-Repair:")
doc_dir = os.path.join(ROOT, "src", "synthex-doctor")
check("synthex doctor script exists", os.path.exists(os.path.join(doc_dir, "synthex_doctor.py")))

try:
    sys.path.insert(0, doc_dir)
    from synthex_doctor import SynthexDoctor
    doc = SynthexDoctor(dry_run=True)
    check("synthex doctor initialized", doc is not None)
    diag = doc.run_full_diagnosis(auto_fix=False)
    check("synthex doctor full diagnostic pass", len(diag) >= 6)
    check("synthex doctor bootloader check", any(d.component == "Bootloader & Initramfs" for d in diag))
    check("synthex doctor fstab check", any(d.component == "Filesystem Mounts (/etc/fstab)" for d in diag))
    check("synthex doctor package database check", any(d.component == "Package Manager Database" for d in diag))
    snaps = SynthexDoctor.get_available_snapshots()
    check("synthex doctor snapshots discovery", len(snaps) > 0)
    
    # Kernel-Level Doctor checks
    from kernel_doctor import KernelDoctor
    kdoc = KernelDoctor(dry_run=True)
    check("kernel doctor initialized", kdoc is not None)
    kdiag = kdoc.run_full_kernel_diagnostics(auto_patch=False)
    check("kernel doctor full diagnostics pass", len(kdiag) >= 5)
    check("kernel doctor taint diagnostic", any(k.subsystem == "Kernel Core & Taint Health" for k in kdiag))
    check("kernel doctor cmdline patcher", any(k.subsystem == "Kernel Boot Parameters (cmdline)" for k in kdiag))
    check("kernel doctor sysrq recovery", any(k.subsystem == "Magic SysRq Emergency Recovery" for k in kdiag))
    check("kernel doctor dracut hook check", any(k.subsystem == "Dracut Early-Boot Auto-Healer" for k in kdiag))
except Exception as _e:
    check("synthex doctor functional validation", False, str(_e))

# 73. Synthex Hardware, Kernel & System Cryptographic Security Suite
print("\n📋 Synthex Hardware, Kernel & System Cryptographic Security Suite:")
sec_dir = os.path.join(ROOT, "src", "synthex-security")
check("synthex encryption engine script exists", os.path.exists(os.path.join(sec_dir, "synthex_encryption.py")))
check("synthex encrypt cli wrapper exists", os.access(os.path.join(ROOT, "src", "synthex-encrypt"), os.X_OK))

try:
    sys.path.insert(0, sec_dir)
    from synthex_encryption import SynthexEncryptionEngine
    crypto_engine = SynthexEncryptionEngine(dry_run=True)
    check("encryption engine initialized", crypto_engine is not None)
    health = crypto_engine.get_full_cryptographic_health()
    check("encryption health diagnostics pass", health.get("overall_security_score", 0) > 0)
    check("encryption tpm2 telemetry check", "present" in health.get("tpm2", {}))
    check("encryption cpu acceleration check", "aes_ni" in health.get("cpu_crypto", {}))
    check("encryption memory encryption check", "technology" in health.get("memory_encryption", {}))
    check("encryption kernel security check", "hardened" in health.get("kernel_security", {}))
    check("encryption luks storage check", len(health.get("luks_volumes", [])) > 0)
    check("encryption swap check", "is_encrypted" in health.get("swap_encryption", {}))
    
    # Test hardening methods (dry_run mode)
    ok_h, _ = crypto_engine.apply_kernel_anticoldboot_hardening()
    check("encryption anti-coldboot sysctl hardening", ok_h is True)
    ok_m, _ = crypto_engine.enable_kernel_memory_encryption()
    check("encryption kernel memory encryption activation", ok_m is True)
    ok_t, _ = crypto_engine.enroll_tpm2("/dev/mapper/synthex-root")
    check("encryption tpm2 enrollment dry-run", ok_t is True)

    # Anti-Forensics Engine Validation
    from synthex_anti_forensics import SynthexAntiForensicsEngine
    af_engine = SynthexAntiForensicsEngine(dry_run=True)
    check("anti-forensics engine initialized", af_engine is not None)
    af_audit = af_engine.audit_anti_forensics()
    check("anti-forensics audit pass", len(af_audit.get("vectors", [])) == 7)
    check("anti-forensics coldboot check", af_audit.get("coldboot_defense") is True)
    # Zero-Telemetry & ISP Stealth Engine Validation
    from synthex_telemetry_killer import SynthexTelemetryKiller
    telem_killer = SynthexTelemetryKiller(dry_run=True)
    check("telemetry killer initialized", telem_killer is not None)
    priv_audit = telem_killer.audit_privacy_shield()
    check("privacy shield audit pass", len(priv_audit.get("vectors", [])) == 7)
    check("zero telemetry state check", "ZERO TELEMETRY" in priv_audit.get("telemetry_state", ""))
    check("encrypted dns check", priv_audit.get("encrypted_dns_active") is True)
    check("mac randomization check", priv_audit.get("mac_randomization_active") is True)
    check("webrtc leak shield check", priv_audit.get("webrtc_shield_active") is True)
    ok_priv, _ = telem_killer.apply_maximum_privacy_lockdown()
    check("zero telemetry maximum lockdown application", ok_priv is True)
except Exception as _e:
    check("zero telemetry functional validation", False, str(_e))

# 74. Synthex SpoofGoof Zero-Latency Packet Noise & Traffic Obfuscation Engine
print("\n📋 Synthex SpoofGoof Zero-Latency Packet Noise & Traffic Obfuscation Engine:")
sg_dir = os.path.join(ROOT, "src", "spoofgoof")
sec_dir = os.path.join(ROOT, "src", "synthex-security")
check("spoofgoof engine script exists", os.path.exists(os.path.join(sec_dir, "synthex_spoofgoof.py")))
check("spoofgoof cli launcher exists", os.access(os.path.join(sg_dir, "spoofgoof"), os.X_OK))
check("spoofgoof systemd unit exists", os.path.exists(os.path.join(ROOT, "systemd", "synthex-spoofgoof.service")))

try:
    sys.path.insert(0, sec_dir)
    from synthex_spoofgoof import SpoofGoofEngine
    sg_engine = SpoofGoofEngine(dry_run=True)
    check("spoofgoof engine initialized", sg_engine is not None)
    sg_status = sg_engine.get_status()
    check("spoofgoof status query pass", sg_status.get("active") is True)
    check("spoofgoof zero latency fast path check", "+0.0 ms" in sg_status.get("network_latency_penalty", ""))
    check("spoofgoof correlation resistance check", "99.8%" in sg_status.get("correlation_resistance_score", ""))
    check("spoofgoof profile switch balanced", sg_engine.set_profile("balanced") is True)
    check("spoofgoof profile switch ultra stealth", sg_engine.set_profile("ultra_stealth") is True)
    check("spoofgoof profile switch gaming", sg_engine.set_profile("gaming") is True)
    payload = sg_engine.generate_chaff_payload(64)
    check("spoofgoof chaff payload generation", len(payload) == 64)
except Exception as _e:
    check("spoofgoof functional validation", False, str(_e))

# Summary
print(f"\n{'='*50}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'='*50}")
sys.exit(failed)

# 29. Control center QML pages
print("\n📋 Control center pages:")
for p in ["Dashboard","System","Performance","Gaming","Developer","Themes","Security","Updates","Drivers","RGB","Snapshots","Kernel","Controllers"]:
    path = os.path.join(ROOT, "src", "synthex-control-center", "ui", "pages", p+".qml")
    ok = os.path.exists(path)
    if ok:
        c = open(path).read()
        ok = "Rectangle {" in c or "Item {" in c
    check(f"{p}.qml", ok)

# 30. Control center components
print("\n📋 Control center components:")
for c in ["Card","StatCard","StatusCard","ModeToggle","Sidebar"]:
    path = os.path.join(ROOT, "src", "synthex-control-center", "ui", "components", c+".qml")
    check(f"{c}.qml", os.path.exists(path))

# 31. Flatpak setup + OOBE bundles
print("\n📋 Flatpak + OOBE bundles:")
check("setup-flatpak.sh", os.path.exists(os.path.join(ROOT, "scripts", "setup-flatpak.sh")))
for b in ["gaming","creator","developer","rgb","emulation"]:
    path = os.path.join(ROOT, "src", "synthex-oobe", "bundles", b+".sh")
    check(f"oobe bundle {b}.sh", os.path.exists(path))
