#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexgpusetup
# Configures GPU drivers (NVIDIA / AMD / Intel) post-install
# Must run after synthexhardwaredetect and packages

import os, subprocess, re, json

try:
    import calamares
    from calamares.utils import debug, warning, error
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {"rootMountPoint": "/mnt", "synthexGPUVendor": "nvidia", "synthexIsVM": False}
            @classmethod
            def value(cls, k, d=None): return cls._d.get(k, d)
            @classmethod
            def insert(cls, k, v): cls._d[k] = v
        @staticmethod
        def prettyStatus(m): print(f"[gpusetup] {m}")
    calamares = _FakeCal()
    def debug(m):   print(f"[gpusetup] {m}")
    def warning(m): print(f"[gpusetup] WARN: {m}")
    def error(m):   print(f"[gpusetup] ERROR: {m}")


def chroot_run(root: str, cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    """Run a command inside the installed chroot."""
    full = ["chroot", root] + cmd
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


def write_file(path: str, content: str, mode: int = 0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, mode)


def setup_nvidia(root: str) -> bool:
    """Configure NVIDIA proprietary driver in the chroot."""
    calamares.prettyStatus("Configuring NVIDIA drivers…")

    # Ensure akmod service can rebuild
    rc, out = chroot_run(root, ["akmods", "--kernels", "$(uname -r)", "--force"], timeout=300)
    if rc != 0:
        warning(f"akmods build warning (may be ok): {out[:200]}")

    # Blacklist nouveau
    bl_path = os.path.join(root, "etc/modprobe.d/nvidia-blacklist.conf")
    write_file(bl_path, "blacklist nouveau\noptions nouveau modeset=0\n")
    debug("nouveau blacklisted")

    # Dracut initramfs rebuild (include nvidia modules)
    dracut_conf = os.path.join(root, "etc/dracut.conf.d/nvidia.conf")
    write_file(dracut_conf, 'add_drivers+=" nvidia nvidia_modeset nvidia_uvm nvidia_drm "\n')

    rc, out = chroot_run(root, ["dracut", "--force", "--regenerate-all"], timeout=240)
    if rc != 0:
        warning(f"dracut rebuild warning: {out[:200]}")
    else:
        debug("Initramfs rebuilt with NVIDIA modules")

    # Kernel parameter: nvidia-drm.modeset=1
    grub_d = os.path.join(root, "etc/default/grub.d")
    os.makedirs(grub_d, exist_ok=True)
    write_file(
        os.path.join(grub_d, "99-nvidia.conf"),
        'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX nvidia-drm.modeset=1"\n'
    )
    chroot_run(root, ["grub2-mkconfig", "-o", "/boot/grub2/grub.cfg"], timeout=30)

    # SDDM config: use Wayland (works well with recent NVIDIA)
    sddm_conf = os.path.join(root, "etc/sddm.conf.d/nvidia-wayland.conf")
    write_file(sddm_conf,
               "[General]\nDisplayServer=wayland\n\n"
               "[Wayland]\nCompositorCommand=kwin_wayland --drm --no-lockscreen\n")

    # Persist state
    calamares.globalstorage.insert("synthexNVIDIAConfigured", True)
    debug("NVIDIA setup complete")
    return True


def setup_amd(root: str) -> bool:
    """Configure AMD GPU (amdgpu open-source driver)."""
    calamares.prettyStatus("Configuring AMD GPU drivers…")

    # amdgpu is loaded automatically; ensure mesa / Vulkan are present
    # Also enable ROCm if enough VRAM
    hw = calamares.globalstorage.value("synthexHW") or {}
    gpu_model = hw.get("gpu", {}).get("model", "")

    # Early KMS (amdgpu)
    mkinit_conf = os.path.join(root, "etc/modprobe.d/amdgpu.conf")
    write_file(mkinit_conf, "options amdgpu si_support=1\noptions amdgpu cik_support=1\n")

    dracut_conf = os.path.join(root, "etc/dracut.conf.d/amdgpu.conf")
    write_file(dracut_conf, 'add_drivers+=" amdgpu "\n')
    chroot_run(root, ["dracut", "--force", "--regenerate-all"], timeout=240)

    # Environment: prefer Wayland
    env_path = os.path.join(root, "etc/environment")
    env_add = "\n# AMD GPU Wayland settings\nAMD_VULKAN_ICD=RADV\nMESA_LOADER_DRIVER_OVERRIDE=radeonsi\n"
    try:
        with open(env_path, "a") as f:
            f.write(env_add)
    except OSError as e:
        warning(f"Could not append to /etc/environment: {e}")

    calamares.globalstorage.insert("synthexAMDConfigured", True)
    debug("AMD GPU setup complete")
    return True


def setup_intel(root: str) -> bool:
    """Configure Intel integrated graphics."""
    calamares.prettyStatus("Configuring Intel GPU…")

    # Ensure i915 early KMS
    dracut_conf = os.path.join(root, "etc/dracut.conf.d/intel-i915.conf")
    write_file(dracut_conf, 'add_drivers+=" i915 "\n')
    chroot_run(root, ["dracut", "--force", "--regenerate-all"], timeout=240)

    # GuC / HuC firmware for modern Intel
    mkinit_conf = os.path.join(root, "etc/modprobe.d/i915.conf")
    write_file(mkinit_conf,
               "options i915 enable_guc=3\n"
               "options i915 enable_fbc=1\n"
               "options i915 enable_psr=1\n")

    calamares.globalstorage.insert("synthexIntelConfigured", True)
    debug("Intel GPU setup complete")
    return True


def setup_vm_graphics(root: str, hypervisor: str) -> bool:
    """Configure virtual machine display drivers."""
    calamares.prettyStatus(f"Configuring VM graphics ({hypervisor})…")

    if hypervisor in ("vmware", "oracle"):
        # VirtualBox / VMware: install guest additions
        rc, _ = chroot_run(root, ["dnf", "install", "-y",
                                   "open-vm-tools", "xorg-x11-drv-vmware"], timeout=120)
    elif hypervisor in ("kvm", "qemu"):
        write_file(
            os.path.join(root, "etc/modprobe.d/virtio.conf"),
            "options virtio_gpu modeset=1\n"
        )
        rc, _ = chroot_run(root, ["dnf", "install", "-y",
                                   "spice-vdagent", "qemu-guest-agent"], timeout=120)
    else:
        debug(f"Unknown hypervisor '{hypervisor}' — using default drivers")
        rc = 0

    calamares.globalstorage.insert("synthexVMGraphicsConfigured", True)
    return rc == 0


def pretty_name() -> str:
    return "GPU Driver Configuration"


def run() -> None | str:
    root       = calamares.globalstorage.value("rootMountPoint") or ""
    gpu_vendor = calamares.globalstorage.value("synthexGPUVendor") or "unknown"
    is_vm      = calamares.globalstorage.value("synthexIsVM") or False
    hypervisor = calamares.globalstorage.value("synthexHypervisor") or ""

    debug(f"GPU setup: vendor={gpu_vendor} vm={is_vm} hypervisor={hypervisor}")

    if not root:
        return "rootMountPoint not set — cannot configure GPU in chroot"

    if is_vm:
        ok = setup_vm_graphics(root, hypervisor)
        return None if ok else "VM graphics setup had warnings (check logs)"

    if gpu_vendor == "nvidia":
        ok = setup_nvidia(root)
    elif gpu_vendor == "amd":
        ok = setup_amd(root)
    elif gpu_vendor == "intel":
        ok = setup_intel(root)
    else:
        warning(f"Unknown GPU vendor '{gpu_vendor}' — skipping GPU-specific config")
        ok = True

    return None if ok else f"GPU setup for '{gpu_vendor}' had issues (non-fatal)"
