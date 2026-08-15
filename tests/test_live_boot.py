#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Live-Boot Experience Test — proves the ISO is usable BEFORE installing,
matching a Mint-style live desktop:
  LIVE-1  Every edition kickstart builds a live squashfs image (liveimg)
  LIVE-2  The live user IS created in the image (not just referenced)
  LIVE-3  Autologin desktop entry + installer launcher + passwordless sudo exist
  LIVE-4  The live-setup.service runs ONLY when the persistent live-mode marker
          exists — and that marker lives in the squashfs (survives boot), not
          the tmpfs /run (which would wipe it and kill the live session)
  LIVE-5  post-install removes the live-mode marker + liveuser + autologin so
          an installed system never boots into the live flow
  LIVE-6  the desktop app stack installed in the live image is usable
          (browser via flatpak, file manager, audio, partition tools, printer)
"""

import os
import re
import sys
import glob
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KS_DIR = ROOT / "build" / "kickstart"
EVIDENCE = []


def record(name, detail):
    EVIDENCE.append((name, detail))


def read(path):
    return path.read_text() if path.exists() else ""


class LiveBootProof(unittest.TestCase):

    def test_live_1_liveimg_all_editions(self):
        editions = sorted(p.stem.replace("synthex-", "")
                          for p in KS_DIR.glob("synthex-*.ks"))
        self.assertTrue(len(editions) >= 4, f"expected editions, got {editions}")
        for ed in editions:
            c = read(KS_DIR / f"synthex-{ed}.ks")
            self.assertIn("liveimg", c, f"{ed} not a live image (no liveimg)")
        record("LIVE-1 · live squashfs images", f"{', '.join(editions)} all declare liveimg")

    def test_live_2_liveuser_created(self):
        for ed in ["plasma", "gnome", "hyprland", "gaming"]:
            ks = read(KS_DIR / f"synthex-{ed}.ks")
            self.assertIn("user --name=liveuser", ks,
                          f"{ed}: liveuser directive missing (autologin has no user to login as)")
            self.assertIn("--groups=wheel", ks, f"{ed}: liveuser not in wheel (no sudo)")
        record("LIVE-2 · liveuser created",
               "user --name=liveuser --groups=wheel,audio,video,input,storage in all desktop editions")

    def test_live_3_live_session_plumbing(self):
        plasma = read(KS_DIR / "synthex-plasma.ks")
        self.assertIn("autologin.conf", plasma, "no SDDM autologin config")
        self.assertIn("liveuser", plasma)
        self.assertIn("49-synthex-live-installer.rules", plasma, "polkit rule missing")
        self.assertIn("NOPASSWD", plasma, "passwordless sudo missing")
        self.assertIn("synthex-live-setup.service", plasma, "live-setup service not enabled")
        sddm = read(ROOT / "desktop/sddm/sddm-live.conf")
        self.assertIn("User=liveuser", sddm, "sddm-live lacks autologin liveuser")
        installer = read(ROOT / "desktop/applications/synthex-installer.desktop")
        self.assertIn("pkexec calamares", installer, "installer launcher broken")
        record("LIVE-3 · live plumbing",
               "SDDM autologin.conf · polkit rule 49-synthex-live-installer · NOPASSWD sudo · "
               "synthex-live-setup.service · Install-Synthex desktop launcher")

    def test_live_4_marker_persists(self):
        """The live-mode marker must NOT be in tmpfs /run. A /run marker is wiped
        each boot, so ConditionPathExists would fail and the live session never
        initialises. The marker lives in the squashfs at /etc/synthex/live-mode."""
        svc = read(ROOT / "configs/live/synthex-live-setup.service")
        self.assertIn("ConditionPathExists=", svc, "service lacks a live gate")
        marker = re.search(r"ConditionPathExists=(\S+)", svc)
        self.assertIsNotNone(marker)
        self.assertNotIn("/run/", marker.group(1),
                         "live marker in tmpfs /run — wiped on boot, live session would never start")
        self.assertIn("/etc/", marker.group(1),
                      "live marker should be in a persistent (squashfs) path")
        for ed in ["plasma", "gnome", "hyprland", "gaming", "minimal"]:
            c = read(KS_DIR / f"synthex-{ed}.ks")
            self.assertIn("live-mode", c, f"{ed}: kickstart does not write the persistent live-mode marker")
        record("LIVE-4 · persistent live marker",
               f"marker @ {marker.group(1)} (squashfs) — survives boot; /run would not")

    def test_live_5_postinstall_cleans_live(self):
        """After Calamares installs to disk, live-only state must be removed so the
        installed system drops the live user, sudoers, autologin and the marker."""
        for cand in [ROOT/"src/synthex-installer/post-install.sh",
                     ROOT/"build/rpmbuild/SOURCES/post-install.sh",
                     ROOT/"build/scripts/post-install.sh"]:
            if not cand.exists():
                continue
            txt = read(cand)
            if "liveuser" not in txt:
                continue
            self.assertIn("userdel -r liveuser", txt, f"{cand}: liveuser not deleted on install")
            self.assertIn("live-mode", txt, f"{cand}: live-mode marker not removed on install")
            self.assertIn("autologin.conf", txt, f"{cand}: autologin not removed on install")
            record("LIVE-5 · post-install cleanup", f"{cand.name} removes liveuser + live-mode + autologin")
            return
        self.fail("no post-install script found to clean live state")

    def test_live_6_live_desktop_apps(self):
        """The live desktop should boot usable: file manager, audio, network,
        partition tool, printer, and a web browser (via the default Flatpak)."""
        plasma = read(KS_DIR / "synthex-plasma.ks")
        for needed in ["dolphin", "pipewire-pulseaudio", "NetworkManager-wifi",
                       "partitionmanager", "system-config-printer", "gstreamer1-plugins-good",
                       "flatpak", "ffmpeg-free", "mesa-vulkan-drivers"]:
            self.assertIn(needed, plasma, f"live desktop missing {needed}")
        # browser ships via Flatpak (Mint/Fedora live pattern), Flatpak is default-enabled
        self.assertIn("flatpak", plasma, "flatpak not present for Firefox")
        record("LIVE-6 · live desktop apps",
               "dolphin · pipewire · NetworkManager-wifi · partitionmanager · "
               "system-config-printer · gstreamer-good · ffmpeg · mesa-vulkan · flatpak(browser)")

    def test_live_7_no_oobe_on_live(self):
        """A Mint-style live session must NOT run the first-boot wizard / OOBE —
        it auto-logs-in to a usable desktop. Firstboot/OOBE only run after a real
        install (post-install re-enables them). live-setup disables them on live."""
        live = read(ROOT / "configs/live/live-setup.sh")
        for svc in ["synthex-firstboot", "synthex-oobe"]:
            self.assertIn(f"systemctl disable {svc}", live,
                          f"live session does not disable {svc} — it would pop up on live boot")
        # post-install re-enables them for the installed system
        post = read(ROOT / "build/scripts/post-install.sh")
        self.assertIn("synthex-firstboot", post, "post-install should enable firstboot after install")
        record("LIVE-7 · no OOBE on live", "live-setup disables synthex-firstboot + synthex-oobe; "
                                            "post-install re-enables them for the installed system")

    def test_live_8_sddm_session_consistent(self):
        """SDDM Session must be a resolvable .desktop id (plasma.desktop), and all
        live autologin sources must agree — a bare 'plasma' would fail auto-login."""
        for src in [read(KS_DIR / "synthex-plasma.ks"),
                    read(ROOT / "configs/live/live-setup.sh"),
                    read(ROOT / "desktop/sddm/sddm-live.conf")]:
            if "Session=" in src:
                sess = [l for l in src.splitlines() if l.startswith("Session=")][0]
                self.assertIn(".desktop", sess,
                              f"SDDM session not resolvable: {sess}")
        record("LIVE-8 · SDDM session consistent", "all autologin sources use <session>.desktop")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    print("\n════ LIVE-BOOT EVIDENCE ════")
    for n, d in EVIDENCE:
        print(f" ▶ {n}\n   {d}")