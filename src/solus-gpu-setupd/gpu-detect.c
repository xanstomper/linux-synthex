/**
 * solus-gpu-setupd — Solus GPU Detection and Driver Setup Daemon
 *
 * Detects GPU vendor, checks compatibility, and selects the appropriate
 * driver package. Runs as a oneshot systemd service before display-manager.
 *
 * Licensed under GPL-2.0-or-later
 * Copyright (c) Solus Project
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <signal.h>
#include <sys/utsname.h>
#include <sys/stat.h>
#include <errno.h>

/* Constants                                                          */

#define VENDOR_NVIDIA  0x10de
#define VENDOR_AMD     0x1002
#define VENDOR_INTEL   0x8086
#define VENDOR_VIRTIO  0x1af4

#define MAX_GPUS 8
#define MAX_LINE 256

/* Structs                                                           */

typedef enum {
    DRIVER_NVIDIA_PROPRIETARY,
    DRIVER_NVIDIA_OPEN,
    DRIVER_NVIDIA_NOUVEAU,
    DRIVER_AMDGPU,
    DRIVER_AMDGPU_PRO,
    DRIVER_INTEL,
    DRIVER_INTEL_XE,
    DRIVER_VIRTIO,
    DRIVER_LLVMPIPE,
    DRIVER_UNKNOWN
} DriverType;

static const char *driver_name(DriverType dt)
{
    switch (dt) {
    case DRIVER_NVIDIA_PROPRIETARY: return "nvidia (proprietary)";
    case DRIVER_NVIDIA_OPEN:        return "nvidia-open";
    case DRIVER_NVIDIA_NOUVEAU:     return "nouveau";
    case DRIVER_AMDGPU:             return "amdgpu";
    case DRIVER_AMDGPU_PRO:         return "amdgpu-pro";
    case DRIVER_INTEL:              return "intel-i915";
    case DRIVER_INTEL_XE:           return "intel-xe";
    case DRIVER_VIRTIO:             return "virtio-gpu";
    case DRIVER_LLVMPIPE:           return "llvmpipe";
    default:                        return "unknown";
    }
}

static const char *driver_package(DriverType dt)
{
    switch (dt) {
    case DRIVER_NVIDIA_PROPRIETARY: return "akmod-nvidia xorg-x11-drv-nvidia-cuda";
    case DRIVER_NVIDIA_OPEN:        return "xorg-x11-drv-nvidia";
    case DRIVER_NVIDIA_NOUVEAU:     return "xorg-x11-drv-nouveau";
    case DRIVER_AMDGPU:             return "mesa-dri-drivers mesa-vulkan-drivers";
    case DRIVER_AMDGPU_PRO:         return "mesa-dri-drivers mesa-vulkan-drivers";
    case DRIVER_INTEL:              return "mesa-dri-drivers mesa-vulkan-drivers intel-media-driver";
    case DRIVER_INTEL_XE:           return "mesa-dri-drivers mesa-vulkan-drivers intel-media-driver intel-compute-runtime";
    case DRIVER_VIRTIO:             return "mesa-dri-drivers";
    case DRIVER_LLVMPIPE:           return "";
    default:                        return "";
    }
}

/* Signal handling                                                    */

static volatile sig_atomic_t g_running = 1;

static void handle_signal(int sig)
{
    (void)sig;
    g_running = 0;
}

static void setup_signals(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_signal;
    sigfillset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT,  &sa, NULL);
    signal(SIGPIPE, SIG_IGN);
}

/* Helper: read sysfs file                                            */

static int read_sysfs(const char *path, char *buf, size_t bufsz)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;
    ssize_t n = read(fd, buf, bufsz - 1);
    close(fd);
    if (n <= 0) return -1;
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == ' '))
        n--;
    buf[n] = '\0';
    return 0;
}

/* GPU detection                                                      */

typedef struct {
    int       count;
    uint16_t  vendor_ids[MAX_GPUS];
    uint16_t  device_ids[MAX_GPUS];
    char      models[MAX_GPUS][128];
} GpuList;

static int detect_gpu_vendor(GpuList *list)
{
    memset(list, 0, sizeof(*list));

    DIR *drm = opendir("/sys/class/drm");
    if (!drm) {
        fprintf(stderr, "gpu-setupd: cannot open /sys/class/drm\n");
        return -1;
    }

    struct dirent *entry;
    while ((entry = readdir(drm)) != NULL && list->count < MAX_GPUS) {
        if (strncmp(entry->d_name, "card", 4) != 0)
            continue;
        if (strchr(entry->d_name, '-') != NULL)
            continue;

        char vendor_path[512], device_path[512];
        char vendor_buf[16] = {0}, device_buf[16] = {0};

        snprintf(vendor_path, sizeof(vendor_path),
                 "/sys/class/drm/%s/device/vendor", entry->d_name);
        snprintf(device_path, sizeof(device_path),
                 "/sys/class/drm/%s/device/device", entry->d_name);

        if (read_sysfs(vendor_path, vendor_buf, sizeof(vendor_buf)) != 0)
            continue;
        if (read_sysfs(device_path, device_buf, sizeof(device_buf)) != 0)
            continue;

        int idx = list->count;
        list->vendor_ids[idx] = (uint16_t)strtoul(vendor_buf, NULL, 16);
        list->device_ids[idx] = (uint16_t)strtoul(device_buf, NULL, 16);

        /* Try to read GPU model name from device path */
        char model_path[512];
        snprintf(model_path, sizeof(model_path),
                 "/sys/class/drm/%s/device/subsystem_vendor", entry->d_name);
        /* Use the device ID as a placeholder if no model name */
        snprintf(list->models[idx], sizeof(list->models[idx]),
                 "GPU 0x%04x:0x%04x",
                 list->vendor_ids[idx], list->device_ids[idx]);

        list->count++;
    }
    closedir(drm);
    return list->count;
}

/* Known supported NVIDIA GPUs list                                   */

static bool is_nvidia_gpu_supported(uint16_t device_id)
{
    /* Known supported NVIDIA GPU device IDs (consumer + pro)
     * These are from the RTX 20/30/40 series and Quadro equivalents */
    const uint16_t supported_nvidia[] = {
        /* Turing (RTX 20) */
        0x1e81, 0x1e82, 0x1e84, 0x1e87, 0x1e89, 0x1e90, 0x1eb0, 0x1eb1,
        /* Ampere (RTX 30) */
        0x2204, 0x2206, 0x2208, 0x2216, 0x2221, 0x2230, 0x2231, 0x2232,
        0x2233, 0x2235, 0x2236, 0x2237, 0x2238, 0x2240, 0x2246, 0x224b,
        0x224c, 0x2250, 0x2251, 0x2258, 0x2259, 0x225a, 0x2260, 0x2261,
        0x2262, 0x2264, 0x2267, 0x2268, 0x2269, 0x226a, 0x226b, 0x226c,
        0x228b, 0x228e, 0x2297, 0x229c, 0x22a0, 0x22a4, 0x22b0, 0x22b2,
        0x22b8, 0x22ba, 0x22bc, 0x22be, 0x22c0, 0x22c2, 0x22c4, 0x22c8,
        /* Ada Lovelace (RTX 40) */
        0x2684, 0x2685, 0x2686, 0x2687, 0x2688, 0x2689, 0x268a, 0x268b,
        0x26b1, 0x26b2, 0x26b3, 0x26b4, 0x26b5, 0x26b6, 0x26b7, 0x26b8,
        /* GTX 16 series */
        0x1d01, 0x1d0a, 0x1d0c, 0x1d10, 0x1d11, 0x1d12, 0x1d13, 0x1d14,
        /* Quadro / pro */
        0x1e30, 0x1e32, 0x1e34, 0x1e36, 0x1e38, 0x1e3a, 0x1e3c, 0x1e3e,
        0x223a, 0x223b, 0x223c, 0x223d, 0x223e, 0x223f,
        /* Geforce 9xx (Maxwell) - legacy support */
        0x13c0, 0x13c2, 0x13d7, 0x13d8, 0x13d9, 0x13da, 0x13db,
        0x1401, 0x1402, 0x1406, 0x1407, 0x1430, 0x1431, 0x1436,
    };

    size_t count = sizeof(supported_nvidia) / sizeof(supported_nvidia[0]);
    for (size_t i = 0; i < count; i++) {
        if (supported_nvidia[i] == device_id)
            return true;
    }
    return false;
}

/* Kernel version check                                               */

typedef struct {
    int major;
    int minor;
    int patch;
} KernelVersion;

static int get_kernel_version(KernelVersion *kv)
{
    struct utsname uts;
    if (uname(&uts) != 0)
        return -1;

    if (sscanf(uts.release, "%d.%d.%d", &kv->major, &kv->minor, &kv->patch) < 2)
        return -1;

    return 0;
}

static bool kernel_supports_dgpu()
{
    KernelVersion kv;
    if (get_kernel_version(&kv) != 0)
        return true; /* assume yes */

    /* AMD dGPUs need >= 5.17, Intel Arc needs >= 6.2 */
    if (kv.major >= 6) return true;
    if (kv.major == 5 && kv.minor >= 17) return true;
    return false;
}

/* Security / Wayland checks                                          */

static bool has_secure_boot(void)
{
    char buf[8] = {0};
    /* Try efivars path for SecureBoot */
    DIR *dir = opendir("/sys/firmware/efi/efivars");
    if (!dir) return false;
    closedir(dir);

    /* Try reading SecureBoot variable */
    if (read_sysfs("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c",
                   buf, sizeof(buf)) == 0) {
        /* Byte 4 contains the status (1 = enabled) */
        return (buf[4] == 1);
    }
    return false;
}

static bool is_wayland_session(void)
{
    const char *xdg = getenv("XDG_SESSION_TYPE");
    return (xdg && strcasecmp(xdg, "wayland") == 0);
}

/* Driver selection                                                   */

static DriverType select_driver(uint16_t vendor_id, uint16_t device_id)
{
    switch (vendor_id) {
    case VENDOR_NVIDIA: {
        if (!is_nvidia_gpu_supported(device_id)) {
            fprintf(stderr, "gpu-setupd: NVIDIA GPU 0x%04x not in known list — trying nouveau\n",
                    device_id);
            return DRIVER_NVIDIA_NOUVEAU;
        }

        /* Check kernel version for open driver support */
        KernelVersion kv;
        bool modern_kernel = (get_kernel_version(&kv) == 0 &&
                              (kv.major > 6 || (kv.major == 6 && kv.minor >= 7)));

        if (modern_kernel && !has_secure_boot()) {
            /* RTX 20+ with modern kernel can use the open driver */
            return DRIVER_NVIDIA_OPEN;
        }

        /* Check if Wayland session — nouveau has better Wayland support */
        if (is_wayland_session()) {
            fprintf(stderr, "gpu-setupd: Wayland session detected — using nouveau for compatibility\n");
            return DRIVER_NVIDIA_NOUVEAU;
        }

        return DRIVER_NVIDIA_PROPRIETARY;
    }

    case VENDOR_AMD: {
        if (kernel_supports_dgpu()) {
            return DRIVER_AMDGPU;
        }
        /* Fallback: still try amdgpu, it's the standard */
        return DRIVER_AMDGPU;
    }

    case VENDOR_INTEL: {
        KernelVersion kv;
        bool has_xe = (get_kernel_version(&kv) == 0 &&
                       (kv.major > 6 || (kv.major == 6 && kv.minor >= 8)));

        if (has_xe) {
            /* Try the Xe driver for newer Intel Arc GPUs */
            return DRIVER_INTEL_XE;
        }
        return DRIVER_INTEL;
    }

    case VENDOR_VIRTIO:
        return DRIVER_VIRTIO;

    default:
        /* Unknown GPU — fall back to software rendering */
        fprintf(stderr, "gpu-setupd: unknown GPU vendor 0x%04x — falling back to llvmpipe\n",
                vendor_id);
        return DRIVER_LLVMPIPE;
    }
}

/* Installation (placeholder — calls package manager)                 */

static int install_driver(const char *package_name)
{
    printf("gpu-setupd: installing driver package: %s\n", package_name);

    /* Attempt installation with DNF (Fedora/RPM-based) */
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "/usr/bin/dnf install -y %s 2>/dev/null", package_name);

    int ret = system(cmd);
    if (ret != 0) {
        /* Try zypper for openSUSE-based */
        snprintf(cmd, sizeof(cmd), "/usr/bin/zypper install -y %s 2>/dev/null", package_name);
        ret = system(cmd);
    }

    if (ret == 0) {
        printf("gpu-setupd: driver '%s' installed successfully\n", package_name);
    } else {
        fprintf(stderr, "gpu-setupd: driver installation failed for '%s' (exit=%d)\n",
                package_name, ret);
    }

    return ret;
}

/* Main                                                               */

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    setup_signals();
    fprintf(stderr, "solus-gpu-setupd starting\n");

    /* 1. Detect available GPUs */
    GpuList gpus;
    int gpu_count = detect_gpu_vendor(&gpus);
    if (gpu_count <= 0) {
        fprintf(stderr, "gpu-setupd: no GPU detected\n");
        return 1;
    }

    printf("solus-gpu-setupd: detected %d GPU(s)\n", gpu_count);

    /* 2. For each GPU, select and install driver */
    bool all_ok = true;
    for (int i = 0; i < gpu_count && g_running; i++) {
        DriverType dt = select_driver(gpus.vendor_ids[i], gpus.device_ids[i]);
        const char *pkg = driver_package(dt);

        printf("GPU %d: vendor=0x%04x device=0x%04x model=\"%s\" → driver=%s package=%s\n",
               i, gpus.vendor_ids[i], gpus.device_ids[i], gpus.models[i],
               driver_name(dt), pkg);

        /* Install if this isn't a dry run */
        if (argc > 1 && strcmp(argv[1], "--dry-run") == 0) {
            printf("  (dry run — would install %s)\n", pkg);
            continue;
        }

        if (strlen(pkg) > 0 && dt != DRIVER_LLVMPIPE) {
            if (install_driver(pkg) != 0) {
                fprintf(stderr, "gpu-setupd: failed to install driver for GPU %d\n", i);
                all_ok = false;
            }
        } else {
            printf("GPU %d: using built-in kernel driver, no additional package needed\n", i);
        }
    }

    /* 3. Write detection results to runtime file */
    FILE *out = fopen("/var/run/solus-gpu-profile.json", "w");
    if (out) {
        fprintf(out, "{\"gpuCount\":%d,\"gpus\":[", gpu_count);
        for (int i = 0; i < gpu_count; i++) {
            if (i > 0) fprintf(out, ",");
            DriverType dt = select_driver(gpus.vendor_ids[i], gpus.device_ids[i]);
            fprintf(out,
                    "{\"vendorId\":\"0x%04x\",\"deviceId\":\"0x%04x\","
                    "\"model\":\"%s\",\"driver\":\"%s\",\"package\":\"%s\"}",
                    gpus.vendor_ids[i], gpus.device_ids[i], gpus.models[i],
                    driver_name(dt), driver_package(dt));
        }
        fprintf(out, "]}\n");
        fclose(out);
    }

    fprintf(stderr, "solus-gpu-setupd %s\n",
            all_ok ? "completed successfully" : "completed with errors");
    return all_ok ? 0 : 1;
}