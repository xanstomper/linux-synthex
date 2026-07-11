// SPDX-License-Identifier: GPL-3.0-or-later
//
// synthex-neural-ipc — POSIX Shared Memory
//
// Zero-copy large-data transfer between agents.
//
// Lifecycle:
//   Writer                                    Reader
//   ──────                                    ──────
//   shmem_create(name, size) → ShmHandle      (receives ShmRef in a Message)
//   shmem_write(&handle, data) → ShmRef       shmem_read(&shmref) → Vec<u8>
//   [send ShmRef inside Message]              shmem_release(&shmref)
//   shmem_unlink(name)        ← after readers confirm

use anyhow::{Context, Result};
use libc::{
    c_int, c_void, ftruncate, mmap, munmap, shm_open, shm_unlink,
    MAP_FAILED, MAP_SHARED, O_CREAT, O_RDONLY, O_RDWR, PROT_READ, PROT_WRITE,
    S_IRUSR, S_IWUSR,
};
use std::ffi::CString;

use crate::protocol::ShmRef;

/// Maximum size of a single shared-memory segment (256 MiB).
pub const SHM_MAX_BYTES: usize = 256 * 1024 * 1024;

/// Prefix for all SynthOS IPC shared-memory segments.
const SHM_PREFIX: &str = "/synthex-ipc-";

// ── Handle (writer side) ─────────────────────────────────────────────────────

pub struct ShmHandle {
    /// POSIX shm name (includes leading '/').
    pub name: String,
    /// Size of the mapping.
    pub size: usize,
    /// Raw pointer to the mapped region.
    ptr: *mut c_void,
    /// File descriptor returned by shm_open.
    fd: c_int,
}

// SAFETY: ShmHandle owns its mapping and the fd; we serialise access at a
// higher level (one writer per segment).
unsafe impl Send for ShmHandle {}
unsafe impl Sync for ShmHandle {}

impl Drop for ShmHandle {
    fn drop(&mut self) {
        unsafe {
            if !self.ptr.is_null() && self.ptr != MAP_FAILED {
                munmap(self.ptr, self.size);
            }
            if self.fd >= 0 {
                libc::close(self.fd);
            }
        }
    }
}

/// Create a new POSIX shared-memory segment of `size` bytes.
///
/// The segment is named `SHM_PREFIX` + a random hex suffix so that
/// multiple concurrent transfers never collide.
pub fn shmem_create(size: usize) -> Result<ShmHandle> {
    if size == 0 || size > SHM_MAX_BYTES {
        anyhow::bail!("shmem_create: size {} out of range (1..={})", size, SHM_MAX_BYTES);
    }

    // Generate a unique name.
    let suffix = uuid::Uuid::new_v4().simple().to_string();
    let name = format!("{}{}", SHM_PREFIX, &suffix[..16]);
    let cname = CString::new(name.clone()).unwrap();

    let fd = unsafe {
        shm_open(
            cname.as_ptr(),
            O_CREAT | O_RDWR,
            (S_IRUSR | S_IWUSR) as libc::mode_t,
        )
    };
    if fd < 0 {
        anyhow::bail!(
            "shm_open({}) failed: {}",
            name,
            std::io::Error::last_os_error()
        );
    }

    if unsafe { ftruncate(fd, size as libc::off_t) } < 0 {
        unsafe { libc::close(fd) };
        anyhow::bail!(
            "ftruncate({}, {}) failed: {}",
            name,
            size,
            std::io::Error::last_os_error()
        );
    }

    let ptr = unsafe {
        mmap(
            std::ptr::null_mut(),
            size,
            PROT_READ | PROT_WRITE,
            MAP_SHARED,
            fd,
            0,
        )
    };
    if ptr == MAP_FAILED {
        unsafe { libc::close(fd) };
        anyhow::bail!("mmap({}) failed: {}", name, std::io::Error::last_os_error());
    }

    Ok(ShmHandle { name, size, ptr, fd })
}

/// Write `data` into `handle` at offset 0 and return a [`ShmRef`] that the
/// reader can use to locate and map the data.
///
/// `data` must fit within `handle.size`.
pub fn shmem_write(handle: &ShmHandle, data: &[u8]) -> Result<ShmRef> {
    if data.len() > handle.size {
        anyhow::bail!(
            "shmem_write: data ({} bytes) exceeds segment size ({} bytes)",
            data.len(),
            handle.size
        );
    }
    // SAFETY: handle.ptr is valid for handle.size bytes (checked at creation).
    unsafe {
        std::ptr::copy_nonoverlapping(data.as_ptr(), handle.ptr as *mut u8, data.len());
    }
    Ok(ShmRef {
        name: handle.name.clone(),
        size: handle.size,
        offset: 0,
        data_len: data.len(),
    })
}

/// Unlink the underlying POSIX shm object so the kernel reclaims it once all
/// mappings are closed.  Call this after all readers have called
/// `shmem_release`.
pub fn shmem_unlink(name: &str) -> Result<()> {
    let cname = CString::new(name).context("shmem_unlink: nul in name")?;
    if unsafe { shm_unlink(cname.as_ptr()) } < 0 {
        // ENOENT is benign — already unlinked.
        let err = std::io::Error::last_os_error();
        if err.kind() != std::io::ErrorKind::NotFound {
            anyhow::bail!("shm_unlink({}) failed: {}", name, err);
        }
    }
    Ok(())
}

// ── Reader side ──────────────────────────────────────────────────────────────

/// Map the shared-memory segment described by `shmref`, copy out the payload,
/// and immediately unmap.  This is a safe, copying read — for hot-path
/// zero-copy reads see `shmem_map_ro`.
pub fn shmem_read(shmref: &ShmRef) -> Result<Vec<u8>> {
    let cname = CString::new(shmref.name.clone()).context("shmem_read: nul in name")?;
    let fd = unsafe { shm_open(cname.as_ptr(), O_RDONLY, 0) };
    if fd < 0 {
        anyhow::bail!(
            "shmem_read shm_open({}) failed: {}",
            shmref.name,
            std::io::Error::last_os_error()
        );
    }

    let ptr = unsafe {
        mmap(std::ptr::null_mut(), shmref.size, PROT_READ, MAP_SHARED, fd, 0)
    };
    unsafe { libc::close(fd) };

    if ptr == MAP_FAILED {
        anyhow::bail!(
            "shmem_read mmap({}) failed: {}",
            shmref.name,
            std::io::Error::last_os_error()
        );
    }

    let end = shmref.offset + shmref.data_len;
    if end > shmref.size {
        unsafe { munmap(ptr, shmref.size) };
        anyhow::bail!(
            "shmem_read: offset+data_len ({}) exceeds segment size ({})",
            end,
            shmref.size
        );
    }

    let slice = unsafe {
        std::slice::from_raw_parts(
            (ptr as *const u8).add(shmref.offset),
            shmref.data_len,
        )
    };
    let out = slice.to_vec();
    unsafe { munmap(ptr, shmref.size) };
    Ok(out)
}

/// Notify the broker that this agent is done with the shared-memory segment.
/// Currently a thin wrapper around unlink; a refcount scheme can replace this.
pub fn shmem_release(shmref: &ShmRef) -> Result<()> {
    shmem_unlink(&shmref.name)
}

// ── Zero-copy read-only mapping (advanced) ───────────────────────────────────

/// A live read-only mapping of a shared-memory segment.
/// Dropped when the handle goes out of scope.
pub struct ShmMapRo {
    ptr: *const u8,
    size: usize,
    pub offset: usize,
    pub data_len: usize,
}

impl ShmMapRo {
    /// Access the payload slice without copying.
    pub fn as_slice(&self) -> &[u8] {
        // SAFETY: ptr + offset is within the mapped region for data_len bytes.
        unsafe { std::slice::from_raw_parts(self.ptr.add(self.offset), self.data_len) }
    }
}

impl Drop for ShmMapRo {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe { munmap(self.ptr as *mut c_void, self.size) };
        }
    }
}

unsafe impl Send for ShmMapRo {}

/// Map a shared-memory segment read-only without copying the data.
/// The caller must not retain the slice past the lifetime of `ShmMapRo`.
pub fn shmem_map_ro(shmref: &ShmRef) -> Result<ShmMapRo> {
    let cname = CString::new(shmref.name.clone()).context("shmem_map_ro: nul in name")?;
    let fd = unsafe { shm_open(cname.as_ptr(), O_RDONLY, 0) };
    if fd < 0 {
        anyhow::bail!(
            "shmem_map_ro shm_open({}) failed: {}",
            shmref.name,
            std::io::Error::last_os_error()
        );
    }

    let ptr = unsafe {
        mmap(std::ptr::null_mut(), shmref.size, PROT_READ, MAP_SHARED, fd, 0)
    };
    unsafe { libc::close(fd) };

    if ptr == MAP_FAILED {
        anyhow::bail!(
            "shmem_map_ro mmap({}) failed: {}",
            shmref.name,
            std::io::Error::last_os_error()
        );
    }

    Ok(ShmMapRo {
        ptr: ptr as *const u8,
        size: shmref.size,
        offset: shmref.offset,
        data_len: shmref.data_len,
    })
}
