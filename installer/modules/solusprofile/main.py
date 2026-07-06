#!/usr/bin/env python3
"""
Calamares Solus Profile Module — auto-detects hardware + correct drivers.
"""
import os, subprocess, json

NAME = "solusprofile"


def run():
    gpu = detect_gpu()
    profile = select_profile(gpu)
    os.makedirs("/etc/calamares/scripts", exist_ok=True)
    with open("/etc/calamares/scripts/solus-profile", "w") as f:
        f.write(f"SOLUS_PROFILE={profile['id']}")
        f.write(f"SOLUS_PACKAGES={' '.join(profile['packages'])}")
        f.write(f"SOLUS_GPU={gpu.get('vendor', 'unknown')}")


def detect_gpu():
    info = {'vendor': 'unknown', 'model': 'unknown', 'driver': 'mesa'}
    try:
        out = subprocess.check_output(['lspci', '-nn', '-d', '::0300'], text=True, timeout=10)
        for line in out.strip().splitlines()[:1]:
            low = line.lower()
            if 'nvidia' in low or '10de:' in line:
                info = {'vendor': 'nvidia', 'model': line.split(':')[-1].strip(), 'driver': 'nvidia'}
            elif 'amd' in low or 'advanced micro devices' in low or '1002:' in line:
                info = {'vendor': 'amd', 'model': line.split(':')[-1].strip(), 'driver': 'mesa'}
            elif 'intel' in low or '8086:' in line:
                info = {'vendor': 'intel', 'model': line.split(':')[-1].strip(), 'driver': 'mesa'}
    except Exception:
        pass
    return info


def select_profile(gpu):
    pkgs = ['solus-meta-standard']
    if gpu['vendor'] == 'nvidia':
        pkgs.append('solus-gpu-nvidia')
    elif gpu['vendor'] == 'amd':
        pkgs.append('solus-gpu-amdgpu')
    elif gpu['vendor'] == 'intel':
        pkgs.append('solus-gpu-intel')
    return {'id': 'gaming', 'packages': pkgs + ['solus-gaming-platform']}


def pretty_name():
    return 'Solus Auto-Profile'

def required():
    return ['partition', 'fstab', 'users']

def weight():
    return 15
