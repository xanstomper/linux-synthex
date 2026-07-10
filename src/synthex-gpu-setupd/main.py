#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS GPU Setup Daemon — configures GPU at boot (Vulkan, VA-API, DRI)

import sys, os, subprocess, logging, time
logging.basicConfig(level=logging.INFO, format="[gpu-setupd] %(levelname)s %(message)s")
log = logging.getLogger("gpu-setupd")

def detect_gpu_vendor():
    try:
        out = subprocess.check_output(["lspci","-mm"], text=True, timeout=10)
        for line in out.splitlines():
            l = line.upper()
            if "VGA" in l or "3D CONTROLLER" in l or "DISPLAY CONTROLLER" in l:
                if "NVIDIA" in l:
                    return "nvidia"
                elif "AMD" in l or "RADEON" in l or "ATI" in l:
                    return "amd"
                elif "INTEL" in l:
                    return "intel"
    except Exception:
        pass
    return "unknown"

def setup_nvidia():
    log.info("Configuring NVIDIA GPU environment")
    env_vars = {
        "__GL_THREADED_OPTIMIZATIONS": "1",
        "NVD_BACKEND":                 "direct",
        "__GL_SHADER_DISK_CACHE":      "1",
        "__GL_SHADER_DISK_CACHE_PATH": "/var/cache/synthex/nvidia-shaders",
    }
    # Write to /etc/environment.d/
    env_dir = "/etc/environment.d"
    os.makedirs(env_dir, exist_ok=True)
    with open(f"{env_dir}/50-synthex-nvidia.conf", "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    # Enable nvidia-persistenced
    subprocess.run(["systemctl","enable","--now","nvidia-persistenced.service"],
                   capture_output=True, timeout=15)
    log.info("NVIDIA setup complete")

def setup_amd():
    log.info("Configuring AMD GPU environment")
    env_dir = "/etc/environment.d"
    os.makedirs(env_dir, exist_ok=True)
    with open(f"{env_dir}/50-synthex-amd.conf", "w") as f:
        f.write("RADV_PERFTEST=nggc,sam,ngg\n")
        f.write("AMD_VULKAN_ICD=RADV\n")
        f.write("MESA_SHADER_CACHE_DIR=/var/cache/synthex/mesa-shaders\n")
    log.info("AMD setup complete")

def setup_intel():
    log.info("Configuring Intel GPU environment")
    env_dir = "/etc/environment.d"
    os.makedirs(env_dir, exist_ok=True)
    with open(f"{env_dir}/50-synthex-intel.conf", "w") as f:
        f.write("INTEL_DRIVER=iris\n")
        f.write("MESA_SHADER_CACHE_DIR=/var/cache/synthex/mesa-shaders\n")
    log.info("Intel setup complete")

def create_shader_dirs():
    for d in ["/var/cache/synthex/nvidia-shaders",
              "/var/cache/synthex/mesa-shaders"]:
        os.makedirs(d, exist_ok=True)
        try:
            import stat
            os.chmod(d, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except Exception:
            pass

def main():
    log.info(f"SynthOS GPU Setup Daemon (pid={os.getpid()})")
    create_shader_dirs()
    vendor = detect_gpu_vendor()
    log.info(f"Detected GPU vendor: {vendor}")
    if vendor == "nvidia":
        setup_nvidia()
    elif vendor == "amd":
        setup_amd()
    elif vendor == "intel":
        setup_intel()
    else:
        log.warning("Unknown GPU vendor — skipping vendor-specific setup")
    log.info("GPU setup daemon complete")

if __name__ == "__main__":
    main()
