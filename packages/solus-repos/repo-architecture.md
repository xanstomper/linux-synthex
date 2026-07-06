# Linux Solus Repository Architecture

## Repository Layout

```
/repo/solus/
├── rawhide/                         # Rolling development — always current
│   ├── x86_64-v3/
│   │   ├── Packages/
│   │   │   ├── a/
│   │   │   ├── b/
│   │   │   └── ...
│   │   ├── repodata/
│   │   │   ├── repomd.xml
│   │   │   ├── repomd.xml.asc       # GPG-signed repomd
│   │   │   ├── primary.xml.zst
│   │   │   ├── filelists.xml.zst
│   │   │   └── other.xml.zst
│   │   └── solus.repo
│   ├── x86_64-v4/
│   │   └── ...
│   └── aarch64/
│       └── ...
│
├── stable/                          # Tagged point releases
│   ├── 2026.1/
│   │   ├── x86_64-v3/
│   │   ├── x86_64-v4/
│   │   └── aarch64/
│   ├── 2026.2/
│   └── ...
│
├── updates/                         # Security + bugfix updates for stable
│   ├── 2026.1/
│   │   ├── x86_64-v3/
│   │   ├── x86_64-v4/
│   │   └── aarch64/
│   ├── 2026.2/
│   └── ...
│
├── testing/                         # Pre-release validation queue
│   ├── 2026.1/
│   │   ├── x86_64-v3/
│   │   ├── x86_64-v4/
│   │   └── aarch64/
│   ├── 2026.2/
│   └── ...
│
└── backports/                       # Older-stable backports
    ├── 2025.4/
    ├── 2026.1/
    └── ...
```

## Repository Configuration

### Repository Definitions

| Repository ID | Type | Base URL | Priority | Enabled |
|--------------|------|----------|----------|---------|
| `solus-rawhide` | Rolling | `https://repo.solus.org/rawhide/$basearch` | 1 | Yes |
| `solus-stable` | Release | `https://repo.solus.org/stable/$releasever/$basearch` | 5 | Conditional |
| `solus-updates` | Updates | `https://repo.solus.org/updates/$releasever/$basearch` | 5 | Yes |
| `solus-testing` | Testing | `https://repo.solus.org/testing/$releasever/$basearch` | 10 | No (opt-in) |
| `solus-backports` | Backports | `https://repo.solus.org/backports/$releasever/$basearch` | 15 | No (opt-in) |
| `solus-source` | Source | `https://repo.solus.org/rawhide/SRPMS` | 99 | Yes |

### Priority Resolution

- Lower priority value = higher priority
- `solus-rawhide` (1) provides all base packages
- `solus-stable` (5) provides release-locked versions
- `solus-updates` (5) overrides stable with security/bugfix releases
- `solus-testing` (10) never overrides stable or updates
- `solus-backports` (15) lowest priority, opt-in only

## Signing Infrastructure

### Key Hierarchy

```
Solus Master Key (offline, encrypted, multi-sig)
    │
    ├── Solus Release Key (release@solus.org)
    │     ├── Signs: RPM packages, repomd.xml
    │     └── Stored: HSM (YubiHSM2 / Nitrokey HSM 2)
    │
    ├── Solus ISO Key (iso@solus.org)
    │     ├── Signs: ISO images, checksum files
    │     └── Stored: HSM (separate slot)
    │
    └── Solus Code Key (code@solus.org)
          ├── Signs: Git tags, container images
          └── Stored: HSM (third slot)
```

### Key Management

| Key | Type | Strength | Rotation | Recovery |
|-----|------|---------|----------|---------|
| Master | RSA + Ed25519 | 8192-bit RSA | Every 5 years | 3-of-5 Shamir Secret Split |
| Release | Ed25519 | 256-bit | Every 2 years | Subkey revocation |
| ISO | Ed25519 | 256-bit | Every 2 years | Subkey revocation |
| Code | Ed25519 | 256-bit | Every 2 years | Subkey revocation |

### Signing Automation

```bash
# RPM signing (automated in CI)
rpm --addsign --define "_gpg_name Solus Release Key" \
    --define "_gpg_sign_cert /path/to/hsm/cert" \
    path/to/package.rpm

# repomd.xml signing
gpg --detach-sign --armor \
    --default-key "Solus Repo <repo@solus.org>" \
    repomd.xml

# ISO signing
gpg --detach-sign --armor \
    --default-key "Solus ISO <iso@solus.org>" \
    solus-linux-2026.1.iso
```

### Verification

```bash
# Verify RPM signature
rpm -K package.rpm

# Verify repomd.xml
gpg --verify repomd.xml.asc repomd.xml

# Verify ISO
gpg --verify solus-linux-2026.1.iso.asc solus-linux-2026.1.iso

# Import Solus Release Key
rpm --import https://repo.solus.org/solus-release-key.asc
```

## Mirror Infrastructure

### Mirror Topology

```
┌──────────────┐
│   Origin     │  repo.solus.org (primary DC)
│   (Primary)  │
└──────┬───────┘
       │
       ├──────────────────────────────┐
       │                              │
       ▼                              ▼
┌──────────────┐            ┌──────────────┐
│   CDN Edge   │            │   Regional   │
│   (Global)   │            │   Mirrors    │
│  BunnyCDN    │            │  (8 regions) │
└──────────────┘            └──────────────┘
       │                              │
       ▼                              ▼
┌──────────────┐            ┌──────────────┐
│  End Users   │            │  End Users   │
│  (primary)   │            │  (fallback)  │
└──────────────┘            └──────────────┘
```

### Mirror Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Storage | 10 TB | 20 TB+ |
| Network | 1 Gbps | 10 Gbps |
| Sync interval | Daily | Every 4 hours |
| Public HTTP | Yes (port 80) | HTTPS + HTTP/2 |
| Rsync support | Yes | Yes (read-only) |

### Mirror Sync Configuration

```bash
# Mirror sync script (run via cron on mirror)
#!/bin/bash
rsync -avz --delete --delay-updates \
    rsync://repo.solus.org/solus/ \
    /srv/mirrors/solus/

# Generate mirror status
echo "Last sync: $(date -u)" > /srv/mirrors/solus/STATUS
```

### Official Mirrors (Planned)

| Location | Hostname | Sponsor |
|----------|----------|---------|
| US East | us-east.mirror.solus.org | TBD |
| US West | us-west.mirror.solus.org | TBD |
| EU West | eu-west.mirror.solus.org | TBD |
| EU East | eu-east.mirror.solus.org | TBD |
| Asia SE | asia-se.mirror.solus.org | TBD |
| Oceania | oceania.mirror.solus.org | TBD |
| South America | sa-east.mirror.solus.org | TBD |
| Africa | af-south.mirror.solus.org | TBD |

## Package Versioning

### Version Scheme

```
<epoch>:<upstream_version>-<package_release>.<dist_tag>
```

### Examples

| Package | Version String | Epoch | Upstream | Release | Dist |
|---------|---------------|-------|----------|---------|------|
| kernel | `1:6.6.30-1.solus` | 1 | 6.6.30 | 1 | solus |
| glibc | `1:2.39-3.solus` | 1 | 2.39 | 3 | solus |
| solus-release | `1:2026.1-1.solus` | 1 | 2026.1 | 1 | solus |
| firefox | `1:126.0-2.solus` | 1 | 126.0 | 2 | solus |

### Version Guidelines

1. **Epoch**: Only incremented when a version comparison would otherwise go backward (extremely rare). Initial epoch is 1.
2. **Upstream version**: Mirror the upstream version string exactly. If upstream uses pre-release identifiers (alpha, beta, rc), use tilde (`~`) for ordering: `2.0~rc1` sorts before `2.0`.
3. **Package release**: Start at 1 for each new upstream version. Increment for Solus-specific patches, build fixes, or configuration changes. Include `%{?dist}` tag for repository differentiation.
4. **Dist tag**: `.solus` for all Solus-built packages. Allows co-installation with Fedora/EPEL packages.

### Update Versioning

```
Old: firefox-1:125.0-1.solus.x86_64.rpm
New: firefox-1:126.0-1.solus.x86_64.rpm   (version bump, release reset)
Fix: firefox-1:126.0-2.solus.x86_64.rpm    (same version, release bump)
```

## Branching Strategy

### Branch-Package Relationship

| Git Branch | Repository Target | Use Case |
|-----------|-------------------|----------|
| `develop` | `rawhide` | Daily development, new packages |
| `release/vX.Y.Z` | `stable/vX.Y.Z` | Release snapshot |
| `hotfix/*` | `updates/vX.Y.Z` | Security patches, critical bugs |
| `testing/*` | `testing/vX.Y.Z` | Pre-release validation |

### Promotion Flow

```
develop (rawhide)
    │
    ▼  [release branch created]
release/vX.Y.Z
    │
    ├──→ stable/vX.Y.Z    (initial release)
    │
    ▼  [hotfixes merged]
hotfix/CVE-XXXX
    │
    ├──→ updates/vX.Y.Z   (security/bugfix updates)
    │
    └──→ testing/vX.Y.Z   (pre-release, then → updates after 7 days)
```

### Merge Policies

| From | To | Strategy | Requires |
|------|----|----------|----------|
| `feature/*` | `develop` | Squash | 1 review + CI pass |
| `develop` | `release/*` | Merge | Freeze + full test suite |
| `release/*` | `main` | Merge | Release vote (3+ PMC) |
| `hotfix/*` | `develop` | Merge | 2 reviews + security scan |
| `hotfix/*` | `release/*` | Cherry-pick | Same as above |
| `testing/*` | `updates/*` | Rebase | 7-day soak + regression pass |

## Multi-Architecture Support

### Architecture Targets

| Arch | Baseline | March Flags | Priority |
|------|----------|-------------|----------|
| `x86_64-v3` | Haswell (2013) | `-march=x86-64-v3 -mtune=generic -O2` | Primary |
| `x86_64-v4` | Skylake-AVX512 (2015) | `-march=x86-64-v4 -mtune=generic -O2 -ftree-vectorize` | Secondary |
| `aarch64` | ARMv8.2-A | `-march=armv8.2-a+crypto+crc -mtune=generic -O2` | Tier 2 |

### Multi-lib Setup

- `/lib64` → native architecture libraries
- `/usr/lib64` → native architecture libraries
- `/usr/lib` → architecture-independent data
- Pure x86_64-v3 builds with no x86_64-v4 fallback for -v4 repos
- aarch64 is standalone (no multi-lib)

### Architecture Support Matrix

| Package Type | x86_64-v3 | x86_64-v4 | aarch64 |
|-------------|-----------|-----------|---------|
| Core (glibc, gcc, kernel) | ✅ | ✅ | ✅ |
| Desktop (GNOME, Budgie) | ✅ | ✅ | ✅ |
| Development (LLVM, Rust) | ✅ | ✅ | ✅ |
| Server (nginx, postgres) | ✅ | ✅ | ✅ |
| Container tooling | ✅ | ✅ | ✅ |
| Proprietary (nvidia-driver) | ✅ | ❌ | ❌ |
| 32-bit compat (wine) | ✅ | ✅ | ❌ |

### Repo Structure Per Architecture

```
rawhide/
├── x86_64-v3/
│   ├── Packages/
│   │   ├── ... (x86_64-v3 optimized)
│   │   └── ... (noarch packages symlinked)
│   ├── repodata/
│   └── solus.repo
├── x86_64-v4/
│   ├── Packages/
│   │   └── ...
│   └── repodata/
└── aarch64/
    ├── Packages/
    │   └── ...
    └── repodata/
```

- `noarch` packages stored in each architecture tree (symlinked or hardlinked)
- `SRPMS` stored once under `rawhide/SRPMS/` (shared across architectures)
- Architecture-specific metadata tracks which packages differ from baseline

### Migration Path

1. **Phase 1** (Current): x86_64-v3 only
2. **Phase 2** (Q3 2026): Add x86_64-v4 as opt-in repo
3. **Phase 3** (Q1 2027): x86_64-v4 becomes default for new installs, v3 maintained for compatibility
4. **Phase 4** (Q1 2028): Add aarch64 as tier-2 architecture
