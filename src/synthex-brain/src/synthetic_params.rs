//! # Synthetic Parameter Generator
//!
//! Generates dense synthetic "parameters" — knowledge injections that expand
//! the effective reasoning capacity of the SynthOS brain.
//!
//! Each generator draws from:
//! 1. **Distilled Datasets** — pre-compressed static knowledge corpora
//! 2. **Live Context** — current system state, recent commands, hardware
//! 3. **Pattern Libraries** — learned solution templates, config recipes
//! 4. **Hypothetical Expansion** — edge case and alternative scenario gen

use serde::{Deserialize, Serialize};
use tracing::debug;

use crate::lazy_chameleon::ScoutKind;

// ── Distilled dataset entry ───────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DistilledEntry {
    pub key:        String,
    pub tags:       Vec<String>,
    pub payload:    String,
    pub relevance:  f32,
    pub confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DistilledDataset {
    pub name:    String,
    pub version: String,
    pub entries: Vec<DistilledEntry>,
}

impl DistilledDataset {
    pub fn search(&self, query: &str, limit: usize) -> Vec<&DistilledEntry> {
        let terms: Vec<String> = query.split_whitespace()
            .map(|s| s.to_lowercase())
            .collect();
        let mut scored: Vec<(f32, &DistilledEntry)> = self.entries.iter()
            .filter_map(|e| {
                let key_lower = e.key.to_lowercase();
                let pay_lower = e.payload.to_lowercase();
                let tags_lower: Vec<String> = e.tags.iter()
                    .map(|t| t.to_lowercase()).collect();
                let score: f32 = terms.iter().map(|t| {
                    let in_key = if key_lower.contains(t.as_str()) { 1.0_f32 } else { 0.0 };
                    let in_tag = if tags_lower.iter().any(|g| g.contains(t.as_str())) { 0.9 } else { 0.0 };
                    let in_pay = if pay_lower.contains(t.as_str()) { 0.5 } else { 0.0 };
                    in_key.max(in_tag).max(in_pay)
                }).sum::<f32>() / terms.len().max(1) as f32;
                if score > 0.0 { Some((score * e.relevance * e.confidence, e)) } else { None }
            })
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        scored.into_iter().take(limit).map(|(_, e)| e).collect()
    }
}

// ── Built-in datasets ─────────────────────────────────────────────────────────

pub fn builtin_datasets() -> Vec<DistilledDataset> {
    vec![
        linux_system_dataset(),
        gpu_hardware_dataset(),
        security_dataset(),
        performance_dataset(),
        package_mgmt_dataset(),
        synthex_patterns_dataset(),
    ]
}

macro_rules! entry {
    ($key:expr, [$($tag:expr),+], $payload:expr, $rel:expr, $conf:expr) => {
        DistilledEntry {
            key:        $key.to_string(),
            tags:       vec![$($tag.to_string()),+],
            payload:    $payload.to_string(),
            relevance:  $rel,
            confidence: $conf,
        }
    };
}

fn linux_system_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "linux-system".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("kernel-param-tuning",
                ["kernel","sysctl","performance","memory","network"],
                "Key sysctl params: vm.swappiness=10(low-swap desktop); vm.dirty_ratio=20,vm.dirty_background_ratio=5(I/O); net.core.rmem_max=16777216,wmem_max=16777216(network buffers); kernel.nmi_watchdog=0(power save); kernel.sched_autogroup_enabled=1(desktop responsiveness). Apply: /etc/sysctl.d/99-synthex.conf. Persist: sysctl --system.",
                0.95, 0.98),
            entry!("systemd-service-debug",
                ["systemd","service","debug","logs","unit"],
                "Debug systemd unit: journalctl -u <svc> -f --since='5m ago'; systemctl status <svc> -l; systemd-analyze blame|head -20. Common fails: ExecStart path wrong→use 'which'; missing deps→add After/Requires; env vars→EnvironmentFile=; permissions→User=/Group=. Fix: systemctl daemon-reload && systemctl restart <svc>.",
                0.92, 0.97),
            entry!("grub-boot-repair",
                ["grub","boot","recovery","initramfs","rescue"],
                "Boot repair: boot live USB; mount /dev/sdXN /mnt; mount --bind /dev /mnt/dev; chroot /mnt; grub-install /dev/sdX; update-grub. Check boot errors: journalctl -b -p err. GRUB reinstall from live: mount /dev/sdX1 /mnt; arch-chroot /mnt; grub-install --target=x86_64-efi --efi-directory=/boot/efi. Initramfs rebuild: dracut -f.",
                0.88, 0.95),
            entry!("filesystem-repair",
                ["filesystem","fsck","ext4","btrfs","xfs","repair"],
                "FS repair: unmount first. ext4: fsck.ext4 -y /dev/sdXN or e2fsck -f -y /dev/sdXN. btrfs: btrfs check --repair /dev/sdXN or btrfs scrub start /mnt; btrfs balance start /mnt. xfs: xfs_repair /dev/sdXN. Data recovery: testdisk, photorec. Bad blocks: badblocks -sv /dev/sdX.",
                0.90, 0.96),
            entry!("dkms-module-build",
                ["dkms","kernel","module","driver","build"],
                "DKMS workflow: dkms add -m <module> -v <ver>; dkms build -m <module> -v <ver>; dkms install -m <module> -v <ver>. Verify: dkms status. Rebuild all after kernel update: dkms autoinstall. Common fail: missing kernel-devel → install linux-headers-$(uname -r). Force rebuild: dkms remove -m <module> -v <ver> --all then re-add.",
                0.87, 0.96),
            entry!("network-debug",
                ["network","networkmanager","wifi","ethernet","nm","debug"],
                "NM debug: nmcli device status; nmcli con show; journalctl -u NetworkManager -f. WiFi scan: nmcli device wifi list. Connect: nmcli device wifi connect <SSID> password <pw>. DNS issues: resolvectl status; symlink /etc/resolv.conf → /run/systemd/resolve/stub-resolv.conf. Reset NM: systemctl restart NetworkManager. Persistent DNS: /etc/systemd/resolved.conf → DNS= line.",
                0.92, 0.94),
            entry!("swap-zram-setup",
                ["swap","zram","memory","compression","performance"],
                "ZRAM optimal config: SIZE=RAM*0.5 (max 8G); algorithm=zstd(best compression/speed balance). Setup: modprobe zram; echo zstd > /sys/block/zram0/comp_algorithm; echo 4G > /sys/block/zram0/disksize; mkswap /sys/block/zram0; swapon /sys/block/zram0 -p 100. Systemd: zram-generator package. Verify: swapon --show.",
                0.85, 0.93),
        ],
    }
}

fn gpu_hardware_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "gpu-hardware".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("nvidia-driver-install",
                ["nvidia","gpu","driver","cuda","install","proprietary"],
                "NVIDIA install (Fedora/RHEL): dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda; wait for kmod build (akmods --force); reboot. Verify: nvidia-smi. Secure Boot: enroll MOK key. Wayland NVIDIA: check /etc/modprobe.d/nvidia-power-management.conf. NVidia preserved memory: options nvidia NVreg_PreserveVideoMemoryAllocations=1. Prime offload: DRI_PRIME=1 app.",
                0.93, 0.95),
            entry!("amd-gpu-performance",
                ["amd","radeon","gpu","performance","driver","radv"],
                "AMD GPU tuning: RADV_PERFTEST=gpl,nggc (Vulkan perf); Mesa env: MESA_VK_DEVICE_SELECT=<pci>; enable high perf: echo performance > /sys/class/drm/card0/device/power_dpm_force_performance_level; AMD MSR: echo 1 > /sys/devices/system/cpu/cpufreq/boost. MangoHUD overlay: MANGOHUD=1 app. VRAM OOM: amdgpu.vm_size=<GB> in /etc/modprobe.d/.",
                0.88, 0.92),
            entry!("vulkan-multi-gpu",
                ["vulkan","gpu","multi","prime","dri","offload"],
                "Multi-GPU Vulkan: VK_ICD_FILENAMES to point to specific GPU ICD. PRIME offload: DRI_PRIME=1 for discrete GPU. List Vulkan devices: vulkaninfo --summary. Test: vkmark with DRI_PRIME=1. Explicit selection: VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json. Check loaded: vulkaninfo 2>&1 | grep deviceName.",
                0.85, 0.90),
            entry!("gaming-performance-env",
                ["gaming","gamemode","performance","latency","fsr","proton"],
                "Gaming stack: gamemoded (GameMode); MangoHUD (overlay); gamescope (Xwayland compositor for latency); Proton: PROTON_USE_WINED3D=0, PROTON_FORCE_LARGE_ADDRESS_AWARE=1, DXVK_ASYNC=1. CPU governer: performance for gaming, schedutil otherwise. IO scheduler: none for NVMe. AMD FSR: WINE_FULLSCREEN_FSR=1 WINE_FULLSCREEN_FSR_STRENGTH=2.",
                0.90, 0.92),
        ],
    }
}

fn security_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "security".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("apparmor-profile-debug",
                ["apparmor","security","profile","deny","audit","selinux"],
                "AppArmor debug: aa-status (profiles); aa-enforce /etc/apparmor.d/<profile>; aa-complain <profile> (permissive mode). View denials: journalctl -xe | grep apparmor. Generate profile: aa-genprof <binary>; let it run; answer prompts. Fix deny: audit log → /etc/apparmor.d/ edit. Add rule: owner /path/** rw,. Reload: apparmor_parser -r /etc/apparmor.d/<profile>.",
                0.87, 0.93),
            entry!("ssh-hardening",
                ["ssh","security","hardening","authorized-keys","sshd"],
                "SSH hardening in /etc/ssh/sshd_config: PermitRootLogin no; PasswordAuthentication no; PubkeyAuthentication yes; MaxAuthTries 3; ClientAliveInterval 300; ClientAliveCountMax 2; AllowUsers <user>. Key-only: ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host. Fail2ban: dnf install fail2ban; systemctl enable --now fail2ban.",
                0.92, 0.97),
            entry!("luks-encryption",
                ["luks","encryption","cryptsetup","tpm2","disk"],
                "LUKS2 setup: cryptsetup luksFormat --type luks2 /dev/sdX; luksOpen /dev/sdX mapper-name; mkfs.ext4 /dev/mapper/mapper-name. Add key: cryptsetup luksAddKey /dev/sdX. TPM2 auto-unlock: clevis bind luks -d /dev/sdX tpm2 '{}'; dracut -f. Backup header: cryptsetup luksHeaderBackup /dev/sdX --header-backup-file luks-header.img.",
                0.85, 0.92),
            entry!("synthex-security-policy",
                ["synthex","security","socket","ipc","capabilities"],
                "SynthOS security: IPC socket at /run/synthex/brain.sock (600 perms, synthex user); DBus: org.synthex.Brain (system bus, polkit rules in /etc/polkit-1/rules.d/); AppArmor profile: /home/jewboy420/linux-synthex/src/synthex-brain/apparmor/synthex-brain. Capabilities: CAP_NET_ADMIN for network monitoring. Audit trail: all IPC calls logged via tracing.",
                0.95, 0.98),
        ],
    }
}

fn performance_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "performance".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("io-scheduler-tuning",
                ["io","scheduler","nvme","ssd","hdd","performance","blkio"],
                "IO scheduler: NVMe/SSD → none; HDD → bq or mq-deadline. Set: echo none > /sys/block/nvme0n1/queue/scheduler. Persistent: udev rule ACTION==\"add\" KERNEL==\"nvme*\" ATTR{queue/scheduler}=\"none\". Queue depth: NVMe default 1024, echo 512 > /sys/block/nvme0n1/queue/nr_requests. Read-ahead: blockdev --setra 256 /dev/nvme0n1. HDD: echo mq-deadline > /sys/block/sda/queue/scheduler.",
                0.88, 0.94),
            entry!("cpu-affinity-isolation",
                ["cpu","affinity","isolation","cpuset","latency","realtime"],
                "CPU isolation: isolcpus=2-3 in GRUB (isolates cores from scheduler); nohz_full=2-3 (no HZ ticks). Pin process: taskset -cp 2-3 <pid>. NUMA: numactl --cpunodebind=0 --membind=0 app. RT priority: chrt -f 99 <cmd>. Check affinity: cat /proc/<pid>/status | grep Cpus. CGroup: systemd-run --property=CPUAffinity=2-3 <cmd>.",
                0.85, 0.92),
            entry!("memory-hugepages",
                ["memory","hugepages","transparent","mmap","latency"],
                "HugePages for DB/VMs: echo 512 > /proc/sys/vm/nr_hugepages (2MB pages=1GB). Transparent HugePages for desktop: echo madvise > /sys/kernel/mm/transparent_hugepage/enabled; for gaming: echo never (reduces jitter). Check: grep HugePages /proc/meminfo. Per-process: madvise(addr, len, MADV_HUGEPAGE). NUMA-aware: numactl --membind=0 for latency.",
                0.82, 0.90),
            entry!("perf-profiling",
                ["perf","profiling","flamegraph","trace","performance"],
                "Perf profiling: perf record -g -F 99 <pid> -- sleep 10; perf report. Flamegraph: perf script | stackcollapse-perf.pl | flamegraph.pl > out.svg. ftrace: trace-cmd record -e sched -e irq -p function_graph; trace-cmd report. eBPF: bpftrace -e 'kprobe:do_sys_openat2 { printf(\"open: %s\\n\", str(arg1)); }'. Latency heatmap: perf stat -e cache-misses,cache-references.",
                0.83, 0.91),
        ],
    }
}

fn package_mgmt_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "package-mgmt".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("dnf-rpm-operations",
                ["dnf","rpm","package","fedora","rhel","install","synthex"],
                "DNF operations: dnf install/remove/update/autoremove; dnf history undo <id>; dnf provides /path/file; dnf repoquery --requires <pkg>; dnf list installed|grep <name>. RPM: rpm -qf /path (find pkg); rpm -ql <pkg> (list files); rpm -qi <pkg> (info); rpm -Va (verify all). Copr: dnf copr enable <user/repo>. Cache: dnf clean all.",
                0.90, 0.95),
            entry!("flatpak-management",
                ["flatpak","sandbox","app","flathub","override","permissions"],
                "Flatpak ops: flatpak install/uninstall/update; flatpak info <app>; flatpak override <app> --filesystem=host; flatpak run --env=KEY=VAL <app>; flatpak override --show <app>. Permissions: flatpak override <app> --nofilesystem=host --filesystem=<path>; --nosocket=wayland/x11; --nodevice=dri. Debug: flatpak run --command=bash <app>. List user: flatpak list --user.",
                0.87, 0.93),
            entry!("makepkg-aur",
                ["aur","makepkg","pkgbuild","arch","cache","build"],
                "AUR build: git clone <aur-url>; cd pkg; makepkg -si. Cache: ~/.cache/makepkg; BUILDDIR=/tmp/makepkg in /etc/makepkg.conf for faster builds (RAM). CFLAGS: -march=native -O2. Custom PKGBUILD: modify source[], sha256sums. yay: yay -S <pkg> (AUR helper). paru: paru -S <pkg>. Build deps only: makepkg --syncdeps. Split packages: makepkg --pkg <subpkg>.",
                0.82, 0.90),
        ],
    }
}

fn synthex_patterns_dataset() -> DistilledDataset {
    DistilledDataset {
        name:    "synthex-patterns".to_string(),
        version: "2026.1".to_string(),
        entries: vec![
            entry!("synthex-brain-ipc",
                ["synthex","brain","ipc","dbus","socket","agent","api"],
                "SynthOS Brain IPC: Unix socket /run/synthex/brain.sock; JSON-RPC-like {method, params}; methods: remember/recall/forget/get_context/list_agents/register_agent/coordinate_task/get_clipboard/set_clipboard/get_enriched_context/build_enriched_prompt/chameleon_stats/token_saver_stats/compress_text/distilled_snapshot/assemble_context_window. DBus: org.synthex.Brain at /org/synthex/Brain. Auth: CapabilityToken handshake.",
                0.98, 0.99),
            entry!("lazy-chameleon-usage",
                ["synthex","chameleon","lazy","scout","injection","distilled"],
                "Lazy Chameleon: LazyChameleon::stall_and_enrich(request, domain_hint) → EnrichedContext. Scout loop runs every interval_secs proactively enriching context. Token saver: compress(text, max_chars) uses 6 strategies (semantic dedup, lexical abbrev, schema compression, hierarchical summarization, priority pruning, delta encoding). Scale adapts 1.0-2.0x based on stall_ms. Stats: chameleon_stats(), token_saver_stats() via DBus.",
                0.97, 0.99),
            entry!("synthex-agent-lifecycle",
                ["synthex","agent","lifecycle","spawn","register","trust"],
                "SynthOS Agent lifecycle: spawn via DBus register_agent(name, capabilities, pid) → returns agent_id. Trust levels: Untrusted/Low/Medium/High/System. Capabilities: memory:read, memory:write, context:read, workspace:*, network:*, system:*. Agents publish events to aether event bus; Broker validates capability tokens; Dead agents auto-expire (PID check). Background agents spawned with agent_task_id for tracking. Teammate naming in TaskStop/TaskOutput.",
                0.96, 0.98),
            entry!("synthex-memory-kinds",
                ["synthex","memory","kinds","semantic","episodic","working"],
                "SynthOS Memory: Semantic(facts/knowledge); Episodic(time-stamped events); Procedural(how-to); Working(active task context); Reflection(meta-cognitive); Reference(external doc/observation/sensor/system data). Edges: RelationKind: BelongsTo, DependsOn, RelatedTo, BlockedBy, CreatedBy, DiscoveredBy, PartOf. Memory salience decay: 0.05 per hour base, importance*confidence*recency consolidation: top-20 episodic-1 reflection summary every 20min.",
                0.95, 0.97),
            entry!("synthex-context-fields",
                ["synthex","context","workspace","window","task","focus"],
                "SynthOS Context fields: current_workspace(0-8), active_window_title, active_window_app, cpu_usage_pct, ram_used_mb, ram_total_mb, net_connections, open_files, current_directory, recent_cmds(last 20), open_files_pct, representative_sample_paths. Context auto-snapshots every 30s; available via get_context IPC. Focus tracking: coordinate_task sets preferred_agent for task routing.",
                0.94, 0.97),
        ],
    }
}

// ── Synthetic Param Generator ─────────────────────────────────────────────────

/// Generates synthetic knowledge injections on demand.
#[derive(Debug)]
pub struct SyntheticParamGenerator {
    datasets: Vec<DistilledDataset>,
}

impl SyntheticParamGenerator {
    pub fn new(datasets: Vec<DistilledDataset>) -> Self {
        Self { datasets }
    }

    pub fn with_builtin() -> Self {
        Self::new(builtin_datasets())
    }

    /// Generate all synthetic params for a request + domain hint.
    /// Returns a list of (kind, content, confidence, novelty, tag) tuples
    /// ready to push into a ScoutInjection.
    pub fn generate_all(
        &self,
        request:     &str,
        domain_hint: Option<&str>,
    ) -> Vec<SyntheticParam> {
        let mut out = Vec::new();

        // 1. Dataset search
        let query = format!("{} {}", request, domain_hint.unwrap_or(""));
        for dataset in &self.datasets {
            let hits = dataset.search(&query, 4);
            for entry in hits {
                debug!("SyntheticParam hit: {} (rel={:.2})", entry.key, entry.relevance);
                out.push(SyntheticParam {
                    kind:       ScoutKind::DistilledDataset,
                    content:    entry.payload.clone(),
                    confidence: entry.confidence,
                    novelty:    entry.relevance,
                    tag:        entry.key.clone(),
                });
            }
        }

        // 2. Reasoning path stubs
        out.extend(self.expand_reasoning_paths(request));

        // 3. Edge cases
        out.extend(self.enumerate_edge_cases(request));

        // 4. Hardware compat hints
        out.extend(self.hardware_compat_injection(request, domain_hint));

        // 5. Performance optimization suggestions
        out.extend(self.perf_optimization_injection(request, domain_hint));

        out
    }

    fn expand_reasoning_paths(&self, request: &str) -> Vec<SyntheticParam> {
        let req_lower = request.to_lowercase();
        let mut paths = Vec::new();

        if req_lower.contains("fix") || req_lower.contains("error") || req_lower.contains("fail") {
            paths.push(SyntheticParam {
                kind:       ScoutKind::ReasoningPaths,
                content:    "Debugging approach: 1) Reproduce minimal case 2) Check recent changes (git log/diff) 3) Examine logs (journalctl -xe, dmesg) 4) Isolate variables 5) Verify assumptions 6) Test fix in isolation 7) Confirm no regression.".to_string(),
                confidence: 0.88,
                novelty:    0.70,
                tag:        "debug-methodology".to_string(),
            });
        }
        if req_lower.contains("install") || req_lower.contains("setup") || req_lower.contains("configure") {
            paths.push(SyntheticParam {
                kind:       ScoutKind::ReasoningPaths,
                content:    "Installation checklist: 1) Check prerequisites (disk space, RAM, deps) 2) Backup current config 3) Review release notes/breaking changes 4) Install in test first 5) Verify service starts 6) Check logs 7) Test functionality 8) Document changes.".to_string(),
                confidence: 0.85,
                novelty:    0.68,
                tag:        "install-methodology".to_string(),
            });
        }
        if req_lower.contains("performance") || req_lower.contains("slow") || req_lower.contains("latency") {
            paths.push(SyntheticParam {
                kind:       ScoutKind::ReasoningPaths,
                content:    "Perf diagnosis: 1) Measure baseline (htop, iostat, perf stat) 2) Profile bottleneck (perf record, strace -c) 3) Check I/O (iotop, blktrace) 4) Memory pressure (vmstat, /proc/meminfo) 5) Network (ss -s, netstat) 6) Apply targeted fix 7) Re-measure.".to_string(),
                confidence: 0.87,
                novelty:    0.72,
                tag:        "perf-methodology".to_string(),
            });
        }

        paths
    }

    fn enumerate_edge_cases(&self, request: &str) -> Vec<SyntheticParam> {
        let req_lower = request.to_lowercase();
        let mut cases = Vec::new();

        if req_lower.contains("service") || req_lower.contains("daemon") {
            cases.push(SyntheticParam {
                kind:       ScoutKind::HypotheticalScenarios,
                content:    "Service edge cases: socket activation race (add Requires=socket.socket); ExecStartPre failure silently skipped (add FailureAction=); OOMKilled (set OOMScoreAdjust=-500); capability drop too aggressive (check AmbientCapabilities); SELinux/AppArmor denial not obvious in main log (check audit.log).".to_string(),
                confidence: 0.80,
                novelty:    0.75,
                tag:        "service-edge-cases".to_string(),
            });
        }
        if req_lower.contains("gpu") || req_lower.contains("graphics") || req_lower.contains("nvidia") || req_lower.contains("amd") {
            cases.push(SyntheticParam {
                kind:       ScoutKind::HypotheticalScenarios,
                content:    "GPU edge cases: Secure Boot blocks unsigned modules (enroll MOK or disable SB); IOMMU groups prevent passthrough (add iommu=pt); power management causes blank screen (NVreg_PreserveVideoMemoryAllocations=1); Wayland vs X11 GPU selection differs (check LIBVA_DRIVER_NAME, __GLX_VENDOR_LIBRARY_NAME).".to_string(),
                confidence: 0.82,
                novelty:    0.78,
                tag:        "gpu-edge-cases".to_string(),
            });
        }

        cases
    }

    fn hardware_compat_injection(
        &self,
        _request:     &str,
        domain_hint:  Option<&str>,
    ) -> Vec<SyntheticParam> {
        let hint = domain_hint.unwrap_or("").to_lowercase();
        let mut out = Vec::new();

        if hint.contains("hardware") || hint.contains("driver") || hint.contains("kernel") {
            out.push(SyntheticParam {
                kind:       ScoutKind::HardwareCompat,
                content:    "Hardware compat checks: lspci -k (loaded drivers); lsmod | grep <module>; dmesg | grep -i firmware (missing firmware); udevadm info /dev/<device>; hwinfo --<type>. Firmware updates: fwupdmgr refresh && fwupdmgr update. Kernel cmdline: cat /proc/cmdline. ACPI tables: acpidump | acpixtract.".to_string(),
                confidence: 0.83,
                novelty:    0.70,
                tag:        "hardware-compat".to_string(),
            });
        }

        out
    }

    fn perf_optimization_injection(
        &self,
        _request:     &str,
        domain_hint:  Option<&str>,
    ) -> Vec<SyntheticParam> {
        let hint = domain_hint.unwrap_or("").to_lowercase();
        let mut out = Vec::new();

        if hint.contains("performance") || hint.contains("gaming") || hint.contains("latency") {
            out.push(SyntheticParam {
                kind:       ScoutKind::PerfOptimization,
                content:    "SynthOS performance profile: CPU governor=performance (gaming/compute), schedutil (general); I/O scheduler=none(NVMe), mq-deadline(HDD); IRQ affinity: isolate GPU IRQs to dedicated core; NUMA: bind process to local node; Huge Pages: 512x2MB for databases; zram: zstd compression for memory expansion.".to_string(),
                confidence: 0.86,
                novelty:    0.74,
                tag:        "synthex-perf-profile".to_string(),
            });
        }

        out
    }
}

/// A single synthetic parameter ready for injection.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyntheticParam {
    pub kind:       ScoutKind,
    pub content:    String,
    pub confidence: f32,
    pub novelty:    f32,
    pub tag:        String,
}
