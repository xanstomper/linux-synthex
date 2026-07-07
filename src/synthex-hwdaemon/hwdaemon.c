/**
 * synthex-hwdaemon — Synthex Hardware Detection Daemon
 *
 * Detects CPU, GPU, RAM, storage, chassis type, and connectivity.
 * Outputs JSON to stdout or /var/run/synthex-hw-profile.json.
 *
 * Licensed under GPL-2.0-or-later
 * Copyright (c) Synthex Project
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <sys/ioctl.h>
#include <errno.h>

#if __has_include(<drm/drm.h>)
#include <drm/drm.h>
#define SOLUS_HAVE_DRM 1
#endif

#include "hw-profile.h"

/* Constants                                                          */

#define PROFILE_PATH "/var/run/synthex-hw-profile.json"
#define MAX_LINE 1024

/* Global state for signal handling                                  */

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
    sigaction(SIGHUP,  &sa, NULL);
    signal(SIGPIPE, SIG_IGN);
}

/* Helper: read a sysfs file into buffer                             */

static int read_sysfs(const char *path, char *buf, size_t bufsz)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0)
        return -1;

    ssize_t n = read(fd, buf, bufsz - 1);
    close(fd);

    if (n <= 0)
        return -1;

    /* Strip trailing newline/whitespace */
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == ' ' || buf[n - 1] == '\t'))
        n--;
    buf[n] = '\0';
    return 0;
}

/* CPU detection                                                      */

void detect_cpu(HardwareProfile *profile)
{
    FILE *fp = fopen("/proc/cpuinfo", "r");
    if (!fp) {
        fprintf(stderr, "hwdaemon: cannot open /proc/cpuinfo\n");
        return;
    }

    char line[MAX_LINE];
    int cpu_count = 0;
    int core_count = 0;
    int phys_id = -1;
    int last_phys_id = -1;
    double max_mhz = 0.0;
    double min_mhz = 1e9;

    while (fgets(line, sizeof(line), fp)) {
        /* Remove trailing newline */
        size_t len = strlen(line);
        if (len > 0 && line[len - 1] == '\n')
            line[len - 1] = '\0';

        const char *val;

        if ((val = strstr(line, "vendor_id"))) {
            const char *v = strchr(val, ':');
            if (v) {
                v += 2; /* skip ": " */
                if (strstr(v, "GenuineIntel"))
                    profile->cpu_vendor = CPU_INTEL;
                else if (strstr(v, "AuthenticAMD"))
                    profile->cpu_vendor = CPU_AMD;
                else
                    profile->cpu_vendor = CPU_UNKNOWN;
            }
        }

        if ((val = strstr(line, "model name"))) {
            const char *m = strchr(val, ':');
            if (m) {
                m += 2;
                strncpy(profile->cpu_model, m, sizeof(profile->cpu_model) - 1);
                profile->cpu_model[sizeof(profile->cpu_model) - 1] = '\0';
            }
        }

        if ((val = strstr(line, "cpu MHz"))) {
            const char *m = strchr(val, ':');
            if (m) {
                double mhz = atof(m + 2);
                if (mhz > max_mhz) max_mhz = mhz;
                if (mhz < min_mhz) min_mhz = mhz;
            }
        }

        /* Count unique physical cores via cpu cores / physical id */
        if ((val = strstr(line, "physical id"))) {
            const char *p = strchr(val, ':');
            if (p) {
                phys_id = atoi(p + 2);
                if (phys_id != last_phys_id) {
                    last_phys_id = phys_id;
                }
            }
        }

        if (strstr(line, "processor")) {
            cpu_count++;
        }

        if ((val = strstr(line, "cpu cores"))) {
            const char *c = strchr(val, ':');
            if (c) {
                int nc = atoi(c + 2);
                if (nc > core_count) core_count = nc;
            }
        }
    }
    fclose(fp);

    profile->cpu_cores   = (core_count > 0) ? core_count : (cpu_count / 2);
    profile->cpu_threads = cpu_count;
    profile->cpu_max_ghz = max_mhz / 1000.0;
    profile->cpu_min_ghz = (min_mhz < 1e8) ? (min_mhz / 1000.0) : 0.0;
}

/*
 * GPU detection via /sys/class/drm/cardN/device
 */

void detect_gpu(HardwareProfile *profile)
{
    DIR *drm = opendir("/sys/class/drm");
    if (!drm) {
        fprintf(stderr, "hwdaemon: cannot open /sys/class/drm\n");
        return;
    }

    struct dirent *entry;
    while ((entry = readdir(drm)) != NULL) {
        /* Look for card0-* entries */
        if (strncmp(entry->d_name, "card", 4) != 0)
            continue;
        /* Skip render nodes and other sub-devices */
        if (strchr(entry->d_name, '-') != NULL)
            continue;

        char vendor_path[512];
        char device_path[512];
        char vendor_buf[64] = {0};
        char device_buf[64] = {0};

        snprintf(vendor_path, sizeof(vendor_path),
                 "/sys/class/drm/%s/device/vendor", entry->d_name);
        snprintf(device_path, sizeof(device_path),
                 "/sys/class/drm/%s/device/device", entry->d_name);

        if (read_sysfs(vendor_path, vendor_buf, sizeof(vendor_buf)) != 0)
            continue;
        if (read_sysfs(device_path, device_buf, sizeof(device_buf)) != 0)
            continue;

        /* Parse hex vendor/device IDs */
        profile->gpu_vendor_id = (uint16_t)strtoul(vendor_buf, NULL, 16);
        profile->gpu_device_id = (uint16_t)strtoul(device_buf, NULL, 16);

        switch (profile->gpu_vendor_id) {
        case 0x10de:
            profile->gpu_vendor = GPU_NVIDIA;
            snprintf(profile->gpu_model, sizeof(profile->gpu_model),
                     "NVIDIA GPU (0x%04x)", profile->gpu_device_id);
            break;
        case 0x1002:
            profile->gpu_vendor = GPU_AMD;
            snprintf(profile->gpu_model, sizeof(profile->gpu_model),
                     "AMD GPU (0x%04x)", profile->gpu_device_id);
            break;
        case 0x8086:
            profile->gpu_vendor = GPU_INTEL;
            snprintf(profile->gpu_model, sizeof(profile->gpu_model),
                     "Intel GPU (0x%04x)", profile->gpu_device_id);
            break;
        case 0x1af4:
            profile->gpu_vendor = GPU_VIRTIO;
            snprintf(profile->gpu_model, sizeof(profile->gpu_model),
                     "VirtIO GPU");
            break;
        default:
            profile->gpu_vendor = GPU_UNKNOWN;
            snprintf(profile->gpu_model, sizeof(profile->gpu_model),
                     "Unknown GPU (vendor=0x%04x, device=0x%04x)",
                     profile->gpu_vendor_id, profile->gpu_device_id);
            break;
        }

        /* Use only the first primary GPU */
        break;
    }
    closedir(drm);
}

/* RAM detection from /proc/meminfo                                  */

void detect_ram(HardwareProfile *profile)
{
    FILE *fp = fopen("/proc/meminfo", "r");
    if (!fp) {
        fprintf(stderr, "hwdaemon: cannot open /proc/meminfo\n");
        return;
    }

    char line[MAX_LINE];
    while (fgets(line, sizeof(line), fp)) {
        unsigned long val;
        if (sscanf(line, "MemTotal: %lu kB", &val) == 1)
            profile->ram_total_kb = val;
        else if (sscanf(line, "MemAvailable: %lu kB", &val) == 1)
            profile->ram_available_kb = val;
        else if (sscanf(line, "SwapTotal: %lu kB", &val) == 1)
            profile->swap_total_kb = val;
    }
    fclose(fp);
}

/* Storage detection                                                 */

static StorageType classify_storage(const char *dev_name)
{
    /* NVMe devices start with nvme */
    if (strncmp(dev_name, "nvme", 4) == 0)
        return STORAGE_NVME;

    /* SATA/SD devices: sdX - check rotational */
    if (strncmp(dev_name, "sd", 2) == 0) {
        char rot_path[512];
        snprintf(rot_path, sizeof(rot_path),
                 "/sys/block/%s/queue/rotational", dev_name);
        char rot_buf[8] = {0};
        if (read_sysfs(rot_path, rot_buf, sizeof(rot_buf)) == 0) {
            return (atoi(rot_buf) == 1) ? STORAGE_HDD : STORAGE_SATA;
        }
        return STORAGE_SATA;
    }

    return STORAGE_UNKNOWN;
}

void detect_storage(HardwareProfile *profile)
{
    DIR *block = opendir("/sys/block");
    if (!block) {
        fprintf(stderr, "hwdaemon: cannot open /sys/block\n");
        return;
    }

    struct dirent *entry;
    while ((entry = readdir(block)) != NULL) {
        /* Skip . and .. and ram, loop, dm- devices */
        if (entry->d_name[0] == '.')
            continue;
        if (strncmp(entry->d_name, "ram", 3) == 0)
            continue;
        if (strncmp(entry->d_name, "loop", 4) == 0)
            continue;
        if (strncmp(entry->d_name, "dm-", 3) == 0)
            continue;
        if (strncmp(entry->d_name, "zram", 4) == 0)
            continue;

        /* Found a physical block device */
        profile->storage_type = classify_storage(entry->d_name);
        strncpy(profile->storage_model, entry->d_name,
                sizeof(profile->storage_model) - 1);
        profile->storage_model[sizeof(profile->storage_model) - 1] = '\0';

        /* Try to read device size */
        char size_path[512];
        char size_buf[32] = {0};
        snprintf(size_path, sizeof(size_path),
                 "/sys/block/%s/size", entry->d_name);
        if (read_sysfs(size_path, size_buf, sizeof(size_buf)) == 0) {
            profile->storage_size_sectors = strtoull(size_buf, NULL, 10);
        }

        /* Try model name */
        char model_path[512];
        char model_buf[128] = {0};
        snprintf(model_path, sizeof(model_path),
                 "/sys/block/%s/device/model", entry->d_name);
        if (read_sysfs(model_path, model_buf, sizeof(model_buf)) == 0) {
            strncpy(profile->storage_model, model_buf,
                    sizeof(profile->storage_model) - 1);
        }

        /* Only the first physical disk */
        break;
    }
    closedir(block);
}

/* Chassis detection via DMI                                          */

void detect_chassis(HardwareProfile *profile)
{
    char buf[256] = {0};

    /* Chassis type */
    if (read_sysfs("/sys/class/dmi/id/chassis_type", buf, sizeof(buf)) == 0) {
        int type = atoi(buf);
        switch (type) {
        case 3:  /* Desktop */
        case 4:  /* Low Profile Desktop */
        case 6:  /* Mini Tower */
        case 7:  /* Tower */
            profile->chassis_type = CHASSIS_DESKTOP;
            break;
        case 8:  /* Portable */
        case 9:  /* Laptop */
        case 10: /* Notebook */
        case 11: /* Hand Held */
        case 14: /* Sub Notebook */
            profile->chassis_type = CHASSIS_LAPTOP;
            break;
        case 30: /* Tablet */
            profile->chassis_type = CHASSIS_TABLET;
            break;
        case 23: /* Server */
        case 25: /* Server Blade */
            profile->chassis_type = CHASSIS_SERVER;
            break;
        default:
            profile->chassis_type = CHASSIS_UNKNOWN;
            break;
        }
    }

    /* Product name */
    if (read_sysfs("/sys/class/dmi/id/product_name",
                   buf, sizeof(buf)) == 0) {
        strncpy(profile->product_name, buf, sizeof(profile->product_name) - 1);
    }

    /* Manufacturer */
    if (read_sysfs("/sys/class/dmi/id/sys_vendor",
                   buf, sizeof(buf)) == 0) {
        strncpy(profile->manufacturer, buf, sizeof(profile->manufacturer) - 1);
    }

    /* Chassis model */
    if (read_sysfs("/sys/class/dmi/id/product_version",
                   buf, sizeof(buf)) == 0) {
        strncpy(profile->chassis_model, buf, sizeof(profile->chassis_model) - 1);
    }
}

/* Connectivity detection                                             */

void detect_connectivity(HardwareProfile *profile)
{
    /* Check for wireless interfaces in sysfs */
    DIR *net = opendir("/sys/class/net");
    if (net) {
        struct dirent *entry;
        while ((entry = readdir(net)) != NULL) {
            if (entry->d_name[0] == '.')
                continue;
            /* Check if this interface has a wireless subdirectory */
            char wiphy_path[512];
            snprintf(wiphy_path, sizeof(wiphy_path),
                     "/sys/class/net/%s/wireless", entry->d_name);
            struct stat st;
            if (stat(wiphy_path, &st) == 0 && S_ISDIR(st.st_mode)) {
                profile->wifi_status = WIFI_PRESENT;
                break;
            }
        }
        closedir(net);
    }

    /* Check for Bluetooth via /sys/class/bluetooth */
    DIR *bt = opendir("/sys/class/bluetooth");
    if (bt) {
        struct dirent *entry;
        while ((entry = readdir(bt)) != NULL) {
            if (entry->d_name[0] == '.')
                continue;
            profile->bluetooth_status = BT_PRESENT;
            break;
        }
        closedir(bt);
    }
}

/* Additional system info                                             */

static void detect_system_flags(HardwareProfile *profile)
{
    struct utsname uts;
    if (uname(&uts) == 0) {
        strncpy(profile->kernel_version, uts.release,
                sizeof(profile->kernel_version) - 1);
    }

    /* Check for UEFI */
    char buf[16] = {0};
    struct stat efi_st;
    if (stat("/sys/firmware/efi", &efi_st) == 0 && S_ISDIR(efi_st.st_mode)) {
        profile->has_uefi = true;
    }

    /* Secure boot via efivarfs */
    if (stat("/sys/firmware/efi/efivars", &efi_st) == 0 && S_ISDIR(efi_st.st_mode))
        profile->has_secure_boot = true;

    /* Check for TPM */
    struct stat st;
    if (stat("/sys/class/tpm", &st) == 0 && S_ISDIR(st.st_mode))
        profile->has_tpm = true;

    /* Detect VM */
    if (read_sysfs("/sys/class/dmi/id/product_name",
                   buf, sizeof(buf)) == 0) {
        if (strcasestr(buf, "VirtualBox") ||
            strcasestr(buf, "VMware") ||
            strcasestr(buf, "KVM") ||
            strcasestr(buf, "QEMU") ||
            strcasestr(buf, "Xen")) {
            profile->is_vm = true;
            profile->chassis_type = CHASSIS_VM;
        }
    }
}

/* Handheld gaming device detection                                  */

void detect_handheld(HardwareProfile *profile)
{
    char buf[256] = {0};
    if (read_sysfs("/sys/class/dmi/id/product_name", buf, sizeof(buf)) != 0)
        return;

    if (strstr(buf, "Steam Deck") || strstr(buf, "Jupiter") ||
        strstr(buf, "Galileo")) {
        profile->is_handheld = true;
        strncpy(profile->handheld_model, "Steam Deck",
                sizeof(profile->handheld_model) - 1);
        profile->chassis_type = CHASSIS_HANDHELD;
    } else if (strstr(buf, "ROG Ally") || strstr(buf, "RC71L") ||
               strstr(buf, "RC72L")) {
        profile->is_handheld = true;
        strncpy(profile->handheld_model, "ASUS ROG Ally",
                sizeof(profile->handheld_model) - 1);
        profile->chassis_type = CHASSIS_HANDHELD;
    } else if (strstr(buf, "Legion Go") || strstr(buf, "83E1")) {
        profile->is_handheld = true;
        strncpy(profile->handheld_model, "Lenovo Legion Go",
                sizeof(profile->handheld_model) - 1);
        profile->chassis_type = CHASSIS_HANDHELD;
    } else if (strstr(buf, "AYANEO") || strstr(buf, "AIR") ||
               strstr(buf, "KUN") || strstr(buf, "NEXT")) {
        profile->is_handheld = true;
        strncpy(profile->handheld_model, buf,
                sizeof(profile->handheld_model) - 1);
        profile->chassis_type = CHASSIS_HANDHELD;
    } else if (strstr(buf, "GPD") || strstr(buf, "ONEXPLAYER")) {
        profile->is_handheld = true;
        strncpy(profile->handheld_model, buf,
                sizeof(profile->handheld_model) - 1);
        profile->chassis_type = CHASSIS_HANDHELD;
    }
}

/* VR headset detection via USB vendor ID                            */

void detect_vr_headset(HardwareProfile *profile)
{
    DIR *usb = opendir("/sys/bus/usb/devices");
    if (!usb) return;

    struct dirent *entry;
    int count = 0;

    while ((entry = readdir(usb)) != NULL) {
        if (entry->d_name[0] == '.') continue;

        char vendor_path[512], vendor_buf[16] = {0};
        snprintf(vendor_path, sizeof(vendor_path),
                 "/sys/bus/usb/devices/%s/idVendor", entry->d_name);
        if (read_sysfs(vendor_path, vendor_buf, sizeof(vendor_buf)) != 0)
            continue;

        uint16_t vid = (uint16_t)strtoul(vendor_buf, NULL, 16);

        switch (vid) {
        case 0x0bb4: /* HTC / Vive */
        case 0x28de: /* Valve Index */
        case 0x2833: /* Oculus / Meta */
        case 0x30a2: /* Bigscreen Beyond */
        case 0x2c97: /* Pimax */
            count++;
            break;
        }
    }
    closedir(usb);

    if (count > 0) {
        profile->has_vr_headset = true;
        profile->vr_headset_count = count;
    }
}

/* RGB peripheral detection via known USB vendor IDs                 */

void detect_rgb_devices(HardwareProfile *profile)
{
    DIR *usb = opendir("/sys/bus/usb/devices");
    if (!usb) return;

    struct dirent *entry;
    int count = 0;

    while ((entry = readdir(usb)) != NULL) {
        if (entry->d_name[0] == '.') continue;

        char vendor_path[512], vendor_buf[16] = {0};
        snprintf(vendor_path, sizeof(vendor_path),
                 "/sys/bus/usb/devices/%s/idVendor", entry->d_name);
        if (read_sysfs(vendor_path, vendor_buf, sizeof(vendor_buf)) != 0)
            continue;

        uint16_t vid = (uint16_t)strtoul(vendor_buf, NULL, 16);

        switch (vid) {
        case 0x046d: /* Logitech (G series) */
        case 0x1532: /* Razer */
        case 0x1b1c: /* Corsair */
        case 0x1038: /* SteelSeries */
        case 0x0db0: /* EVGA / Zotac */
        case 0x28de: /* Valve */
        case 0x264a: /* Cooler Master */
        case 0x2516: /* Wooting */
            count++;
            break;
        }
    }
    closedir(usb);

    if (count > 0) {
        profile->has_rgb_devices = true;
        profile->rgb_device_count = count;
    }
}

/* Monitor detection via DRM connectors                              */

void detect_monitors(HardwareProfile *profile)
{
    DIR *drm = opendir("/sys/class/drm");
    if (!drm) return;

    struct dirent *entry;
    int monitor_count = 0;
    int max_refresh = 0;
    bool hdr_capable = false;
    bool vrr_capable = false;
    bool vrr_found = false;

    while ((entry = readdir(drm)) != NULL) {
        if (entry->d_name[0] == '.') continue;

        if (strstr(entry->d_name, "card") != entry->d_name)
            continue;

        char conn_path[512];
        snprintf(conn_path, sizeof(conn_path),
                 "/sys/class/drm/%s", entry->d_name);

        DIR *card = opendir(conn_path);
        if (!card) continue;

        struct dirent *conn;
        while ((conn = readdir(card)) != NULL) {
            if (conn->d_name[0] == '.') continue;
            if (strstr(conn->d_name, "card") == conn->d_name) continue;
            if (strncmp(conn->d_name, "HDMI", 4) != 0 &&
                strncmp(conn->d_name, "DP", 2) != 0 &&
                strncmp(conn->d_name, "eDP", 3) != 0 &&
                strncmp(conn->d_name, "LVDS", 4) != 0 &&
                strncmp(conn->d_name, "DSI", 3) != 0 &&
                strncmp(conn->d_name, "VGA", 3) != 0 &&
                strncmp(conn->d_name, "DVI", 3) != 0 &&
                strncmp(conn->d_name, "Virtual", 7) != 0 &&
                strncmp(conn->d_name, "Writeback", 9) != 0)
                continue;

            /* Check if connector is connected */
            char status_path[512], status_buf[16] = {0};
            snprintf(status_path, sizeof(status_path),
                     "/sys/class/drm/%s/%s/status",
                     entry->d_name, conn->d_name);
            if (read_sysfs(status_path, status_buf, sizeof(status_buf)) == 0) {
                if (strcmp(status_buf, "connected") != 0)
                    continue;
            }

            monitor_count++;

            /* Read max refresh rate from mode list */
            char modes_path[512];
            snprintf(modes_path, sizeof(modes_path),
                     "/sys/class/drm/%s/%s/modes",
                     entry->d_name, conn->d_name);
            FILE *mf = fopen(modes_path, "r");
            if (mf) {
                char mode_line[128];
                while (fgets(mode_line, sizeof(mode_line), mf)) {
                    int w, h, refresh;
                    char interlaced;
                    /* Parse WxH_r or WxHi */
                    if (sscanf(mode_line, "%dx%d%c%d", &w, &h, &interlaced, &refresh) == 4
                        && interlaced == '_') {
                        if (refresh > max_refresh)
                            max_refresh = refresh;
                    }
                }
                fclose(mf);
            }

            /* HDR: check for Colorspace/HDR_OUTPUT_METADATA in connector props */
            if (!hdr_capable) {
                char hdr_path[512];
                snprintf(hdr_path, sizeof(hdr_path),
                         "/sys/class/drm/%s/%s/Colorspace",
                         entry->d_name, conn->d_name);
                struct stat st;
                if (stat(hdr_path, &st) == 0)
                    hdr_capable = true;
            }
        }
        closedir(card);
    }
    closedir(drm);

    /* VRR: check drm driver supports it */
    DIR *drm_root = opendir("/sys/class/drm");
    if (drm_root) {
        struct dirent *e;
        while ((e = readdir(drm_root)) != NULL) {
            if (e->d_name[0] == '.') continue;
            if (strncmp(e->d_name, "card", 4) != 0) continue;
            if (strchr(e->d_name, '-') != NULL) continue;

            char vrr_path[512];
            snprintf(vrr_path, sizeof(vrr_path),
                     "/sys/class/drm/%s/vrr_capable", e->d_name);
            struct stat st;
            if (stat(vrr_path, &st) == 0)
                vrr_found = true;
            break;
        }
        closedir(drm_root);
    }

    profile->monitor_count = monitor_count;
    profile->monitor_max_refresh_hz = max_refresh;
    profile->monitor_hdr_capable = hdr_capable;
    profile->monitor_vrr_capable = vrr_found;
}

/* Profile lifecycle                                                  */

void profile_init(HardwareProfile *profile)
{
    memset(profile, 0, sizeof(HardwareProfile));
    profile->cpu_vendor       = CPU_UNKNOWN;
    profile->gpu_vendor       = GPU_UNKNOWN;
    profile->storage_type     = STORAGE_UNKNOWN;
    profile->chassis_type     = CHASSIS_UNKNOWN;
    profile->wifi_status      = WIFI_NONE;
    profile->bluetooth_status = BT_NONE;
}

void generate_profile(HardwareProfile *profile)
{
    profile_init(profile);

    detect_cpu(profile);
    detect_gpu(profile);
    detect_ram(profile);
    detect_storage(profile);
    detect_chassis(profile);
    detect_handheld(profile);
    detect_connectivity(profile);
    detect_system_flags(profile);
    detect_vr_headset(profile);
    detect_rgb_devices(profile);
    detect_monitors(profile);
}

/* JSON output                                                        */

static const char *cpu_vendor_str(CPUVendor v)
{
    switch (v) {
    case CPU_INTEL:   return "intel";
    case CPU_AMD:     return "amd";
    default:          return "unknown";
    }
}

static const char *gpu_vendor_str(GPUVendor v)
{
    switch (v) {
    case GPU_NVIDIA:  return "nvidia";
    case GPU_AMD:     return "amd";
    case GPU_INTEL:   return "intel";
    case GPU_VIRTIO:  return "virtio";
    default:          return "unknown";
    }
}

static const char *storage_type_str(StorageType t)
{
    switch (t) {
    case STORAGE_NVME:   return "nvme";
    case STORAGE_SATA:   return "sata";
    case STORAGE_HDD:    return "hdd";
    default:             return "unknown";
    }
}

static const char *chassis_type_str(ChassisType t)
{
    switch (t) {
    case CHASSIS_DESKTOP: return "desktop";
    case CHASSIS_LAPTOP:  return "laptop";
    case CHASSIS_TABLET:  return "tablet";
    case CHASSIS_SERVER:  return "server";
    case CHASSIS_VM:      return "vm";
    case CHASSIS_HANDHELD: return "handheld";
    default:              return "unknown";
    }
}

void profile_write_json(const HardwareProfile *profile, int fd)
{
    char buf[8192];
    int n = snprintf(buf, sizeof(buf),
        "{\n"
        "  \"cpu\": {\n"
        "    \"vendor\": \"%s\",\n"
        "    \"model\": \"%s\",\n"
        "    \"cores\": %d,\n"
        "    \"threads\": %d,\n"
        "    \"maxGhz\": %.2f,\n"
        "    \"minGhz\": %.2f\n"
        "  },\n"
        "  \"gpu\": {\n"
        "    \"vendor\": \"%s\",\n"
        "    \"model\": \"%s\",\n"
        "    \"vendorId\": \"0x%04x\",\n"
        "    \"deviceId\": \"0x%04x\"\n"
        "  },\n"
        "  \"memory\": {\n"
        "    \"totalKb\": %lu,\n"
        "    \"availableKb\": %lu,\n"
        "    \"swapTotalKb\": %lu\n"
        "  },\n"
        "  \"storage\": {\n"
        "    \"type\": \"%s\",\n"
        "    \"model\": \"%s\",\n"
        "    \"sectors\": %lu\n"
        "  },\n"
        "  \"system\": {\n"
        "    \"chassis\": \"%s\",\n"
        "    \"product\": \"%s\",\n"
        "    \"manufacturer\": \"%s\",\n"
        "    \"kernel\": \"%s\",\n"
        "    \"uefi\": %s,\n"
        "    \"tpm\": %s,\n"
        "    \"isVm\": %s\n"
        "  },\n"
        "  \"connectivity\": {\n"
        "    \"wifi\": %s,\n"
        "    \"bluetooth\": %s\n"
        "  },\n"
        "  \"peripherals\": {\n"
        "    \"isHandheld\": %s,\n"
        "    \"handheldModel\": \"%s\",\n"
        "    \"vrHeadset\": %s,\n"
        "    \"vrHeadsetCount\": %d,\n"
        "    \"rgbDevices\": %s,\n"
        "    \"rgbDeviceCount\": %d,\n"
        "    \"monitors\": {\n"
        "      \"count\": %d,\n"
        "      \"maxRefreshHz\": %d,\n"
        "      \"hdrCapable\": %s,\n"
        "      \"vrrCapable\": %s\n"
        "    }\n"
        "  }\n"
        "}\n",
        cpu_vendor_str(profile->cpu_vendor),
        profile->cpu_model,
        profile->cpu_cores,
        profile->cpu_threads,
        profile->cpu_max_ghz,
        profile->cpu_min_ghz,
        gpu_vendor_str(profile->gpu_vendor),
        profile->gpu_model,
        profile->gpu_vendor_id,
        profile->gpu_device_id,
        (unsigned long)profile->ram_total_kb,
        (unsigned long)profile->ram_available_kb,
        (unsigned long)profile->swap_total_kb,
        storage_type_str(profile->storage_type),
        profile->storage_model,
        (unsigned long)profile->storage_size_sectors,
        chassis_type_str(profile->chassis_type),
        profile->product_name,
        profile->manufacturer,
        profile->kernel_version,
        profile->has_uefi ? "true" : "false",
        profile->has_tpm ? "true" : "false",
        profile->is_vm ? "true" : "false",
        profile->wifi_status ? "true" : "false",
        profile->bluetooth_status ? "true" : "false",
        profile->is_handheld ? "true" : "false",
        profile->handheld_model,
        profile->has_vr_headset ? "true" : "false",
        profile->vr_headset_count,
        profile->has_rgb_devices ? "true" : "false",
        profile->rgb_device_count,
        profile->monitor_count,
        profile->monitor_max_refresh_hz,
        profile->monitor_hdr_capable ? "true" : "false",
        profile->monitor_vrr_capable ? "true" : "false"
    );

    if (n > 0)
        (void)write(fd, buf, (size_t)n);
}

void profile_print_json(const HardwareProfile *profile)
{
    profile_write_json(profile, STDOUT_FILENO);
    (void)write(STDOUT_FILENO, "\n", 1);
}

int profile_write_json_file(const HardwareProfile *profile, const char *path)
{
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        fprintf(stderr, "hwdaemon: cannot write %s: %s\n",
                path, strerror(errno));
        return -1;
    }
    profile_write_json(profile, fd);
    close(fd);
    return 0;
}

/* Main entry point                                                   */

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    setup_signals();

    fprintf(stderr, "synthex-hwdaemon starting — hardware detection\n");

    HardwareProfile profile;
    generate_profile(&profile);

    /* Write to runtime file */
    if (profile_write_json_file(&profile, PROFILE_PATH) == 0) {
        fprintf(stderr, "hwdaemon: profile written to %s\n", PROFILE_PATH);
    } else {
        /* Fall back to stdout */
        profile_print_json(&profile);
    }

    /* Also output to stdout for pipe consumers */
    profile_print_json(&profile);

    fprintf(stderr, "synthex-hwdaemon complete\n");
    return 0;
}