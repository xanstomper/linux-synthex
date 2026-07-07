# CI/CD Architecture — Linux Synthex

## Overview

Linux Synthex uses a fully automated CI/CD pipeline built on:

- **GitHub Actions** — Trigger, build, test, release
- **Fedora Copr** — Community package building and hosting
- **Container-based ISO builder** — Reproducible ISO generation
- **Automated testing** — Unit, integration, regression, security, performance
- **Staged rollouts** — Graduated update delivery

---

## Pipeline Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub     │     │  Build Farm  │     │   Quality   │
│  Repository  │────►│  (Copr/      │────►│   Gates     │
│              │     │   Mock)      │     │             │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Mirrors    │◄────│   Release    │◄────│  ISO Builder│
│   CDN        │     │   Signing    │     │  (Container)│
│              │     │              │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## Workflows

### 1. Build Packages (build-packages.yml)

**Trigger:** Push to rawhide, tag creation

```
Source Push ──► Build RPMs ──► Sign ──► Push to Copr ──► Test Install
```

### 2. Build ISO (build-iso.yml)

**Trigger:** Manual, release tag, nightly

```
Trigger ──► Start Container ──► Install Deps ──► 
             ├── lorax (rootfs)
             ├── livecd-creator (ISO)
             ├── compress
             ├── sign
             └── checksum
          ──► Upload Artifact
```

### 3. Security Scan (security-scan.yml)

**Trigger:** Every push, weekly full scan

```
Code Push ──► 
  ├── OpenSCAP scan
  ├── CVE database check
  ├── Dependency audit
  ├── SAST (static analysis)
  ├── DAST (dynamic, for web UI)
  └── License compliance
```

### 4. Test ISO (test-iso.yml)

**Trigger:** After ISO build

```
ISO Ready ──► 
  ├── Boot in QEMU/KVM
  ├── Check bootloader
  ├── Verify desktop starts
  ├── Run smoke tests
  ├── Install to VM
  ├── Reboot installed
  └── Run post-install tests
```

### 5. Release (release-iso.yml)

**Trigger:** Release tag

```
Tag ──► 
  ├── Build final ISO
  ├── GPG sign
  ├── Generate checksums
  ├── Create torrent
  ├── Sync to mirrors
  ├── Publish release notes
  └── Announce
```

---

## Infrastructure

### Build Servers (Copr)

Fedora Copr provides:
- x86_64 build chroots
- Automatic dependency resolution
- Package signing
- Repository hosting

### ISO Build Environment

Docker/Podman container with:
- Fedora 41+ base
- livecd-tools, lorax, createrepo_c
- All Synthex packages resolvable
- Reproducible build configuration

### Artifact Storage

- ISOs: S3-compatible + CDN
- Packages: Copr + self-hosted fallback
- Checksums + signatures: alongside artifacts

---

## Quality Gates

1. **Build Gate** — All packages build successfully
2. **Dependency Gate** — No broken dependencies
3. **Install Gate** — ISO installs to VM
4. **Boot Gate** — System boots under 12 seconds
5. **Smoke Gate** — Core apps launch
6. **Security Gate** — No CVEs, SELinux enforcing
7. **Performance Gate** — No regression > 5%

---

## Release Channels

| Channel | Build Frequency | Stability | Audience |
|---------|----------------|-----------|----------|
| rawhide | Every push | Experimental | Developers |
| testing | Daily | Unstable | QA team |
| stable | Every release | Stable | General |
| lts | Every 2 years | Enterprise | Enterprise |
