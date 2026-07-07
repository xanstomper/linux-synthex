#!/usr/bin/env python3
"""Synthex App Selection — Calamares View Module (QtPy bridge)."""
import os, json
import calamares
from calamares.utils import debug

NAME = "synthexprofile"

def pretty_name(): return "Synthex App Selection"
def required(): return []
def weight(): return 20

def run_checks():
    if not calamares.globalstorage.value("synthexTheme"):
        calamares.globalstorage.insert("synthexTheme", "graphite")
    if not calamares.globalstorage.value("synthexApps"):
        calamares.globalstorage.insert("synthexApps", [])
    debug("Defaults set")

def run():
    """Merge QML selections into package list for installer."""
    apps = calamares.globalstorage.value("synthexApps") or []
    debug(f"Selected apps: {len(apps)}")

    # Store package list for packages module
    calamares.globalstorage.insert("synthexPackages", apps)

    # Write to disk for post-install
    sd = "/var/lib/synthex"
    os.makedirs(sd, exist_ok=True)
    with open(f"{sd}/install-profile.json","w") as f:
        json.dump({"apps": apps}, f, indent=2)

    debug(f"Total packages: {len(apps)}")
    return None

