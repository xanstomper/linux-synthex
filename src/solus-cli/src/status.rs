// System status module for solus-cli

use sysinfo::System;
use std::fmt;

pub struct SystemInfo {
    pub hostname: String,
    pub kernel: String,
    pub os: String,
    pub uptime: String,
    pub cpu_usage: f32,
    pub memory_used_gb: f64,
    pub memory_total_gb: f64,
    pub processes: usize,
    pub load_avg: String,
}

impl fmt::Display for SystemInfo {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "╭── Solus System Status ──")?;
        writeln!(f, "├ Host:       {}", self.hostname)?;
        writeln!(f, "├ OS:         {}", self.os)?;
        writeln!(f, "├ Kernel:     {}", self.kernel)?;
        writeln!(f, "├ Uptime:     {}", self.uptime)?;
        writeln!(f, "├ CPU:        {:.1}%", self.cpu_usage)?;
        writeln!(f, "├ Memory:     {:.1}/{:.1} GB", self.memory_used_gb, self.memory_total_gb)?;
        writeln!(f, "├ Processes:  {}", self.processes)?;
        writeln!(f, "├ Load:       {}", self.load_avg)?;
        writeln!(f, "╰────────────────────────")?;
        Ok(())
    }
}

pub fn system_info() -> SystemInfo {
    let mut sys = System::new_all();
    sys.refresh_all();

    let uptime_secs = System::uptime();
    let days = uptime_secs / 86400;
    let hours = (uptime_secs % 86400) / 3600;
    let mins = (uptime_secs % 3600) / 60;
    let uptime_str = if days > 0 {
        format!("{days}d {hours}h {mins}m")
    } else {
        format!("{hours}h {mins}m")
    };

    let load_str = std::fs::read_to_string("/proc/loadavg")
        .unwrap_or_default()
        .split_whitespace()
        .take(3)
        .collect::<Vec<_>>()
        .join(" ");

    SystemInfo {
        hostname: System::host_name().unwrap_or_default(),
        kernel: System::kernel_version().unwrap_or_default(),
        os: System::os_version().unwrap_or_default(),
        uptime: uptime_str,
        cpu_usage: sys.global_cpu_usage(),
        memory_used_gb: sys.used_memory() as f64 / 1024.0 / 1024.0,
        memory_total_gb: sys.total_memory() as f64 / 1024.0 / 1024.0,
        processes: sys.processes().len(),
        load_avg: load_str,
    }
}
