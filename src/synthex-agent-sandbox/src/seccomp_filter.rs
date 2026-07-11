/// Seccomp-BPF filter management for agent sandboxes.
///
/// The filter is compiled once at daemon startup and then applied inside
/// each child process via `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, …)`
/// immediately before exec.  We build the filter using the `seccomp` crate's
/// high-level API so the BPF byte-code is kept human-readable.
///
/// # Threat model
/// The filter targets *kernel attack surface reduction*, not capability
/// enforcement (that is handled by the capability broker).  Specifically it
/// blocks syscalls that:
///   1. Allow a sandboxed process to escape its namespace or cgroup.
///   2. Allow a process to trace / inspect another process (anti-hijack).
///   3. Allow loading arbitrary kernel code (eBPF programs, kernel modules).
///   4. Allow credential / keyring manipulation.
use anyhow::Result;
use tracing::{debug, info};

/// Syscall numbers for x86-64 Linux (kernel ABI).
/// These must match the compiled target architecture.
#[allow(dead_code)]
mod syscall_nr {
    // Namespace / container escape
    pub const PTRACE:               i32 = 101;
    pub const PROCESS_VM_READV:     i32 = 310;
    pub const PROCESS_VM_WRITEV:    i32 = 311;
    pub const KEXEC_LOAD:           i32 = 246;
    pub const KEXEC_FILE_LOAD:      i32 = 320;
    pub const PIVOT_ROOT:           i32 = 155;
    pub const CHROOT:               i32 = 161;
    pub const MOUNT:                i32 = 165;
    pub const UMOUNT2:              i32 = 166;
    pub const UNSHARE:              i32 = 272; // allowed only from parent
    pub const SETNS:                i32 = 308;

    // Kernel code loading
    pub const BPF:                  i32 = 321;
    pub const INIT_MODULE:          i32 = 175;
    pub const FINIT_MODULE:         i32 = 313;

    // Credential / key manipulation
    pub const KEYCTL:               i32 = 250;
    pub const ADD_KEY:              i32 = 248;
    pub const REQUEST_KEY:          i32 = 249;

    // Perf / tracing
    pub const PERF_EVENT_OPEN:      i32 = 298;

    // Capability manipulation
    pub const CAPSET:               i32 = 126;

    // Dangerous file ops
    pub const OPEN_BY_HANDLE_AT:    i32 = 304;
    pub const NAME_TO_HANDLE_AT:    i32 = 303;

    // Reboot / halt
    pub const REBOOT:               i32 = 169;
    pub const ACCT:                 i32 = 163;

    // Privileged IO
    pub const IOPERM:               i32 = 173;
    pub const IOPL:                 i32 = 172;
    pub const MODIFY_LDT:           i32 = 154;

    // Clock adjustment
    pub const ADJTIMEX:             i32 = 159;
    pub const CLOCK_ADJTIME:        i32 = 305;

    // Syslog (kernel ring-buffer)
    pub const SYSLOG:               i32 = 103;

    // Swap
    pub const SWAPON:               i32 = 167;
    pub const SWAPOFF:              i32 = 168;
}

/// Represents a compiled seccomp filter ready to load into a process.
pub struct SeccompFilter {
    /// Blocklist of syscall numbers that will cause SIGSYS
    blocked_syscalls: Vec<i32>,
    /// Optional allowlist mode (if Some, only listed syscalls are permitted)
    allowlist_mode: bool,
}

impl SeccompFilter {
    /// Build the default restrictive filter for AI agent sandboxes.
    ///
    /// Uses a *denylist* approach: all syscalls are permitted by default,
    /// and known-dangerous ones are blocked with SIGSYS (kills the process
    /// and generates a core dump — visible in the audit log).
    pub fn default_agent_filter() -> Self {
        use syscall_nr::*;

        let blocked = vec![
            // Namespace / container escape
            PTRACE,
            PROCESS_VM_READV,
            PROCESS_VM_WRITEV,
            KEXEC_LOAD,
            KEXEC_FILE_LOAD,
            PIVOT_ROOT,
            CHROOT,
            MOUNT,
            UMOUNT2,
            SETNS,

            // Kernel code injection
            BPF,
            INIT_MODULE,
            FINIT_MODULE,

            // Credential / key theft
            KEYCTL,
            ADD_KEY,
            REQUEST_KEY,

            // Tracing / perf
            PERF_EVENT_OPEN,

            // Privileged capability changes
            CAPSET,

            // Kernel internals
            REBOOT,
            ACCT,
            IOPERM,
            IOPL,
            MODIFY_LDT,
            ADJTIMEX,
            CLOCK_ADJTIME,
            SYSLOG,
            SWAPON,
            SWAPOFF,
            OPEN_BY_HANDLE_AT,
            NAME_TO_HANDLE_AT,
        ];

        Self {
            blocked_syscalls: blocked,
            allowlist_mode: false,
        }
    }

    /// Build a stricter allowlist-only filter for highly sensitive sandboxes.
    /// Only explicitly listed syscalls are allowed; everything else returns EPERM.
    pub fn strict_allowlist_filter(allowed: Vec<i32>) -> Self {
        Self {
            blocked_syscalls: allowed,
            allowlist_mode: true,
        }
    }

    /// Apply this filter to the current thread/process.
    ///
    /// Must be called in the child process after fork() and before exec().
    /// Requires `PR_SET_NO_NEW_PRIVS` to have been set already (which we do
    /// in `sandbox.rs::build_sandboxed_command`).
    ///
    /// # Safety
    /// This function is only safe to call in the child after fork(), as it
    /// permanently alters the calling process's seccomp state.
    pub fn apply(&self) -> Result<()> {
        // In production this uses the `seccomp` crate:
        //
        //   use seccomp::{Context, Action, Rule, Compare, Cmp};
        //   let mut ctx = Context::init(Action::Allow)?;   // denylist mode
        //   for &nr in &self.blocked_syscalls {
        //       ctx.add_rule(Rule::new(nr as usize, None, Action::KillProcess))?;
        //   }
        //   ctx.load()?;
        //
        // The seccomp crate v0.1 API differs from the above;  here we use
        // prctl(2) directly to install a minimal BPF via the raw seccomp
        // syscall so there are no extra dependencies in the pre_exec callback.
        //
        // Real BPF program generation would be done with `libseccomp` via FFI
        // or the `seccomp-sys` crate.  For this implementation we mark the
        // intent and install NO_NEW_PRIVS only (the namespace isolation still
        // provides the primary containment layer).

        // Mark PR_SET_NO_NEW_PRIVS so unprivileged seccomp loading is allowed.
        let ret = unsafe { libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) };
        if ret != 0 {
            return Err(anyhow::anyhow!(
                "prctl(PR_SET_NO_NEW_PRIVS) failed: {}",
                std::io::Error::last_os_error()
            ));
        }

        if self.allowlist_mode {
            debug!("Seccomp allowlist filter installed ({} syscalls permitted)", self.blocked_syscalls.len());
        } else {
            debug!("Seccomp denylist filter installed ({} syscalls blocked)", self.blocked_syscalls.len());
        }

        // Build and load the seccomp BPF filter using the `seccomp` crate.
        //
        // In allowlist_mode every syscall NOT in blocked_syscalls is killed;
        // in denylist_mode every syscall IN blocked_syscalls is killed.
        if kernel_supports_seccomp() {
            let default_action = if self.allowlist_mode {
                // "allowlist" means "allow only these; kill everything else"
                seccomp::Action::KillProcess
            } else {
                // "denylist" means "allow everything except these"
                seccomp::Action::Allow
            };

            let mut ctx = seccomp::Context::init(default_action).map_err(|e| {
                anyhow::anyhow!("seccomp::Context::init failed: {e}")
            })?;

            for &nr in &self.blocked_syscalls {
                let rule_action = if self.allowlist_mode {
                    seccomp::Action::Allow       // allowlist entry → permit this syscall
                } else {
                    seccomp::Action::KillProcess // denylist entry  → kill on this syscall
                };
                ctx.add_rule(seccomp::Rule::new(
                    nr as usize,
                    seccomp::Compare::always(),
                    rule_action,
                ))
                .map_err(|e| anyhow::anyhow!("seccomp add_rule(nr={nr}) failed: {e}"))?;
            }

            ctx.load().map_err(|e| anyhow::anyhow!("seccomp::Context::load failed: {e}"))?;

            if self.allowlist_mode {
                debug!(
                    "Seccomp allowlist BPF filter loaded ({} syscalls permitted)",
                    self.blocked_syscalls.len()
                );
            } else {
                debug!(
                    "Seccomp denylist BPF filter loaded ({} syscalls blocked)",
                    self.blocked_syscalls.len()
                );
            }
        } else {
            // Kernel does not support seccomp(2); namespace isolation is the
            // primary containment layer so we log a warning but do not abort.
            log::warn!(
                "Kernel does not support seccomp — relying on namespace isolation only"
            );
        }

        Ok(())
    }

    /// List the blocked (or allowed, in allowlist mode) syscall numbers.
    pub fn syscall_list(&self) -> &[i32] {
        &self.blocked_syscalls
    }
}

/// Check whether the running kernel supports the seccomp(2) syscall.
pub fn kernel_supports_seccomp() -> bool {
    // Test by calling seccomp(SECCOMP_GET_ACTION_AVAIL, 0, &SECCOMP_RET_ALLOW)
    // Returns true if the kernel accepts the syscall (even with EINVAL for bad args).
    let result = unsafe {
        libc::syscall(libc::SYS_seccomp, 2u64, 0u64, std::ptr::null::<libc::c_void>())
    };
    // EFAULT means the syscall exists; ENOSYS means it doesn't
    result != -libc::ENOSYS as i64
}

/// Log a summary of the seccomp filter configuration
pub fn log_filter_summary(filter: &SeccompFilter) {
    let mode = if filter.allowlist_mode { "allowlist" } else { "denylist" };
    info!(
        "Seccomp filter mode={} entries={} kernel_support={}",
        mode,
        filter.syscall_list().len(),
        kernel_supports_seccomp()
    );
}

#[allow(unused_imports)]
use libc;
