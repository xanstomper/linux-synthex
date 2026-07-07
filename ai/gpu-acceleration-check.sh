#!/usr/bin/env python3
"""Synthex AI GPU Check — verify GPU acceleration for AI workloads."""
import os, sys, subprocess, json

def check_nvidia():
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            # Parse GPU info
            lines = r.stdout.splitlines()
            gpu_lines = [l for l in lines if "NVIDIA" in l and "GeForce" in l or "Tesla" in l or "RTX" in l]
            cuda_version = "?"
            for l in lines:
                if "CUDA Version" in l:
                    cuda_version = l.split(":")[-1].strip()
            return {"available": True, "gpus": gpu_lines, "cuda": cuda_version}
    except: pass
    return {"available": False}

def check_rocm():
    try:
        r = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return {"available": True, "output": r.stdout[:200]}
    except: pass
    # Check for AMDGPU driver
    try:
        r = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=5)
        if "amdgpu" in r.stdout:
            return {"available": True, "driver": "amdgpu"}
    except: pass
    return {"available": False}

def check_vulkan():
    try:
        r = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return {"available": True, "summary": r.stdout[:200]}
    except: pass
    return {"available": False}

def check_ollama():
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            models = [l.split()[0] for l in r.stdout.splitlines()[1:] if l.strip()]
            return {"available": True, "models": models}
    except: pass
    return {"available": False}

def main():
    print("🤖 Synthex AI GPU Acceleration Check")
    print("═" * 45)

    nvidia = check_nvidia()
    rocm = check_rocm()
    vulkan = check_vulkan()
    ollama = check_ollama()

    print(f"\nNVIDIA GPU:{' ✅ ' + ', '.join(nvidia.get('gpus', ['Detected'])) + ' (CUDA ' + nvidia.get('cuda', '?') + ')' if nvidia['available'] else ' ❌ Not detected'}")
    print(f"AMD ROCm:{' ✅ Detected' if rocm['available'] else ' ❌ Not detected (amdgpu driver may still work)'}")
    print(f"Vulkan:{' ✅ Available' if vulkan['available'] else ' ❌ Not available'}")
    print(f"Ollama:{' ✅ Available — Models: ' + ', '.join(ollama.get('models', ['None'])) if ollama['available'] else ' ❌ Not installed'}")
    print(f"\n    {ollama.get('models', [])}")

    print("\nRecommendations:")
    if nvidia["available"]:
        print("  🟢 NVIDIA GPU detected — best for AI workloads")
        print("     Use CUDA for LLM acceleration (ollama, llama.cpp)")
    elif rocm["available"]:
        print("  🟢 AMD GPU with ROCm detected — good for AI workloads")
        print("     Use ROCm for LLM acceleration")
    else:
        print("  🟡 No AI-accelerated GPU detected")
        print("     CPU inference works but is slower")
        print("     Consider: ollama pull deepseek-r1:1.5b (runs on CPU)")

    print(f"\n   Ollama available: {ollama['available']}")
    print("   Vulkan available: Yes" if vulkan["available"] else "   Vulkan for GPU compute: Install mesa-vulkan-drivers")
    print()
    print("   Install: synthex ai setup-webui   (Open WebUI + Ollama)")

if __name__ == "__main__":
    main()
