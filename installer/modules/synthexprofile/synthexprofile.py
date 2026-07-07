#!/usr/bin/env python3
"""Synthex App Selection — fallback job module."""
import os, json
try:
    import calamares
    from calamares.utils import debug
except ImportError:
    pass

NAME = "synthexprofile"

def run():
    apps = calamares.globalstorage.value("synthexApps") or []
    calamares.globalstorage.insert("synthexPackages", apps)
    debug(f"Selected {len(apps)} apps for install")
    return None
