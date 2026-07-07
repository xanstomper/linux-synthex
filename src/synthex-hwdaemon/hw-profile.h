#ifndef SYNTHEX_HW_PROFILE_H
#define SYNTHEX_HW_PROFILE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Enums                                                              */

typedef enum {
    CPU_INTEL   = 0,
    CPU_AMD     = 1,
    CPU_UNKNOWN = 2
} CPUVendor;

typedef enum {
    GPU_NVIDIA   = 0,
    GPU_AMD      = 1,
    GPU_INTEL    = 2,
    GPU_VIRTIO   = 3,
    GPU_UNKNOWN  = 4
} GPUVendor;

typedef enum {
    STORAGE_NVME    = 0,
    STORAGE_SATA    = 1,
    STORAGE_HDD     = 2,
    STORAGE_UNKNOWN = 3
} StorageType;

typedef enum {
    CHASSIS_DESKTOP  = 0,
    CHASSIS_LAPTOP   = 1,
    CHASSIS_TABLET   = 2,
    CHASSIS_SERVER   = 3,
    CHASSIS_VM       = 4,
    CHASSIS_HANDHELD = 5,
    CHASSIS_UNKNOWN  = 6
} ChassisType;

typedef enum {
    WIFI_NONE     = 0,
    WIFI_PRESENT  = 1
} WifiStatus;

typedef enum {
    BT_NONE     = 0,
    BT_PRESENT  = 1
} BluetoothStatus;

/* HardwareProfile struct                                             */

typedef struct {
    /* CPU */
    CPUVendor   cpu_vendor;
    char        cpu_model[256];
    int         cpu_cores;
    int         cpu_threads;
    double      cpu_max_ghz;
    double      cpu_min_ghz;

    /* GPU */
    GPUVendor   gpu_vendor;
    char        gpu_model[256];
    uint16_t    gpu_vendor_id;
    uint16_t    gpu_device_id;

    /* Memory */
    uint64_t    ram_total_kb;
    uint64_t    ram_available_kb;
    uint64_t    swap_total_kb;

    /* Storage */
    StorageType storage_type;
    char        storage_model[128];
    uint64_t    storage_size_sectors;

    /* System */
    ChassisType chassis_type;
    char        chassis_model[128];
    char        product_name[128];
    char        manufacturer[128];
    char        kernel_version[128];

    /* Connectivity */
    WifiStatus      wifi_status;
    BluetoothStatus bluetooth_status;

    /* Flags */
    bool        has_secure_boot;
    bool        has_uefi;
    bool        has_tpm;
    bool        is_vm;

    /* Form-factor / peripheral extras */
    bool        is_handheld;
    char        handheld_model[128];
    bool        has_vr_headset;
    int         vr_headset_count;
    bool        has_rgb_devices;
    int         rgb_device_count;
    int         monitor_count;
    int         monitor_max_refresh_hz;
    bool        monitor_hdr_capable;
    bool        monitor_vrr_capable;
} HardwareProfile;

/* Function declarations                                              */

/**
 * Detect CPU vendor, model, cores, threads from /proc/cpuinfo
 */
void detect_cpu(HardwareProfile *profile);

/**
 * Detect GPU from /sys/class/drm/ device nodes
 */
void detect_gpu(HardwareProfile *profile);

/**
 * Read memory info from /proc/meminfo
 */
void detect_ram(HardwareProfile *profile);

/**
 * Detect storage type and model from /sys/block/
 */
void detect_storage(HardwareProfile *profile);

/**
 * Detect chassis type from DMI/sysfs
 */
void detect_chassis(HardwareProfile *profile);

/**
 * Detect wireless and bluetooth from sysfs / USB
 */
void detect_connectivity(HardwareProfile *profile);

/**
 * Detect handheld gaming devices (Steam Deck / ROG Ally / Legion Go / AYANEO)
 */
void detect_handheld(HardwareProfile *profile);

/**
 * Detect VR headsets by USB vendor id
 */
void detect_vr_headset(HardwareProfile *profile);

/**
 * Detect OpenRGB-compatible RGB peripherals by USB vendor id
 */
void detect_rgb_devices(HardwareProfile *profile);

/**
 * Detect connected monitors, max refresh rate and HDR/VRR capability
 */
void detect_monitors(HardwareProfile *profile);

/**
 * Populate all fields of the HardwareProfile
 */
void generate_profile(HardwareProfile *profile);

/**
 * Write profile as JSON to a file descriptor
 */
void profile_write_json(const HardwareProfile *profile, int fd);

/**
 * Write profile as JSON to a file path
 */
int profile_write_json_file(const HardwareProfile *profile, const char *path);

/**
 * Print profile as JSON to stdout
 */
void profile_print_json(const HardwareProfile *profile);

/**
 * Initialise profile struct with defaults (zero / unknown)
 */
void profile_init(HardwareProfile *profile);

#ifdef __cplusplus
}
#endif

#endif /* SYNTHEX_HW_PROFILE_H */