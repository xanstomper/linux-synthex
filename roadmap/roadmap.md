# Linux Synthex — Project Roadmap

> **Last Updated:** July 2026
> **Status:** Pre-Alpha (Phase 0)

---

## Overview

Linux Synthex development is organized into 6 phases over approximately 18 months from project initiation to stable release.

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
Pre-Alpha   Alpha        Beta         RC           Stable       LTS
             
Q3 2026     Q4 2026      Q1 2027      Q2 2027     Q3 2027     Q4 2027
```

---

## Phase 0: Foundation (Current — Q3 2026)

**Goal:** Establish project infrastructure, architecture, and build pipeline.

### Deliverables

- [x] Project architecture documentation
- [x] Kernel configuration and build system
- [x] Security architecture and hardening
- [x] Brand identity and design language
- [ ] Build infrastructure setup
- [ ] ISO build pipeline
- [ ] Package repository structure
- [ ] CI/CD pipeline v1
- [ ] Development team formation
- [ ] Community channels
- [ ] Contributor guidelines

### Success Criteria
- First bootable ISO can be built
- Build pipeline is reproducible
- Architecture docs cover all components
- Kernel compiles with Synthex config

### Estimated Timeline
- **Weeks 1-2:** Architecture + kernel + security
- **Weeks 3-4:** Build infrastructure + CI/CD
- **Weeks 5-6:** First bootable ISO
- **Weeks 7-8:** Internal testing + refinement

---

## Phase 1: Alpha (Q4 2026)

**Goal:** Bootable, installable system with core functionality.

### Deliverables

#### Core System
- [ ] Synthex Kernel boots on real hardware (AMD, Intel, NVIDIA)
- [ ] BTRFS with compression + snapshots operational
- [ ] SELinux enforcing with Synthex policy
- [ ] Full disk encryption (LUKS2 + TPM2)
- [ ] Secure Boot signed kernel + bootloader
- [ ] Systemd-boot default with GRUB fallback

#### Desktop
- [ ] Synthex Plasma edition boots to desktop
- [ ] Default theme and branding applied
- [ ] Dark/Light mode switching
- [ ] Accent color engine functional
- [ ] Panel layout + default widgets
- [ ] KWin rules for Synthex apps
- [ ] SDDM themed login screen
- [ ] Plymouth boot splash

#### Gaming
- [ ] Steam installs and runs
- [ ] Proton GE functional
- [ ] Gamescope integration
- [ ] MangoHUD overlay
- [ ] AMD GPU driver stack
- [ ] NVIDIA driver (proprietary) support
- [ ] GPU driver manager

#### Installer
- [ ] Calamares boots from ISO
- [ ] Automatic partitioning (BTRFS + LUKS)
- [ ] Custom partitioning
- [ ] User creation
- [ ] Bootloader installation
- [ ] Post-install first-boot setup

#### Packages
- [ ] Synthex repository online (Copr)
- [ ] Kernel RPMs building
- [ ] Meta-packages defined
- [ ] Updates via DNF5 working

### Success Criteria
- ISO installs on 3+ different hardware configurations
- Steam runs 5 popular games at native performance
- Boot time < 15 seconds on NVMe
- Security audit baseline passes
- Encrypted install works end-to-end

---

## Phase 2: Beta (Q1 2027)

**Goal:** Feature-complete, daily-driver ready for early adopters.

### Deliverables

#### Desktop Polish
- [ ] Synthex Fluent Material design fully implemented
- [ ] KDE Plasma 6 all widgets themed
- [ ] Notification center design
- [ ] System Settings reorganized
- [ ] OOBE (first-run wizard) complete
- [ ] Dynamic wallpapers (time-based)
- [ ] Animation system polished
- [ ] System tray and notification UX

#### Gaming Platform
- [ ] Gaming Control Center GUI v1
- [ ] Per-game optimization profiles
- [ ] Shader cache pre-compilation
- [ ] HDR support (Wayland)
- [ ] VRR support
- [ ] Lutris + Heroic Launcher preconfigured
- [ ] Controller auto-detection
- [ ] Performance overlay (MangoHUD)
- [ ] vkBasalt post-processing

#### Developer Experience
- [ ] Development Hub GUI v1
- [ ] Language runtime management
- [ ] Container management (Podman)
- [ ] VS Code preconfigured with extensions
- [ ] Toolbox/distrobox integration
- [ ] Git configuration UI
- [ ] Docker compatibility layer

#### AI Integration
- [ ] Synthex AI Hub v1 (basic)
- [ ] Ollama preinstalled and configured
- [ ] Model manager (download/remove)
- [ ] GPU acceleration confirmed
- [ ] Chat interface
- [ ] 10+ models downloadable from library

#### Security
- [ ] Security Dashboard GUI v1
- [ ] Firewall management UI
- [ ] Update management
- [ ] Encryption status
- [ ] System health monitoring
- [ ] Auto-updates configured
- [ ] Flatpak permissions manager

#### Hyprland Edition
- [ ] Default configuration
- [ ] Waybar themed
- [ ] Wofi/any launcher configured
- [ ] Screenshot tools
- [ ] Workspace management
- [ ] Wallpaper daemon
- [ ] Notification daemon

### Success Criteria
- 100+ beta testers actively using as daily driver
- Steam playtime > 10 hours without crash
- Security dashboard reports clean on audit
- AI Hub runs 7B models locally
- Developer edition builds and tests software
- < 10% regression in performance vs upstream

---

## Phase 3: Release Candidate (Q2 2027)

**Goal:** Production-ready quality with comprehensive testing.

### Deliverables

#### Quality Assurance
- [ ] Automated test suite (unit + integration + regression)
- [ ] Performance benchmark regression testing
- [ ] Security scanning (OpenSCAP, OWASP)
- [ ] Hardware compatibility matrix
- [ ] Upgrade path testing (Fedora → Synthex)
- [ ] Multi-language support (20+ languages)
- [ ] Accessibility (a11y) audit
- [ ] Power consumption benchmarking

#### GNOME Edition
- [ ] Synthex GNOME Shell theme
- [ ] Default GNOME extensions
- [ ] Synthex accent colors
- [ ] Preconfigured workflow

#### Final Polish
- [ ] All 3 editions installable from single ISO
- [ ] Customization center GUI complete
- [ ] Preset system (Windows, macOS, Gaming, Dev)
- [ ] Snapshot manager GUI
- [ ] Rollback utility
- [ ] Package rollback via history
- [ ] Software Center polish
- [ ] Complete onboarding flow

#### Infrastructure
- [ ] Public mirrors (3+ continents)
- [ ] Update infrastructure (staged rollouts)
- [ ] GPG + SIG signing automation
- [ ] ISO torrent infrastructure
- [ ] Bug tracker (GitHub Issues)
- [ ] Community forums
- [ ] Documentation site

### Success Criteria
- RC1 installs on 50+ hardware configurations
- All security controls verified by external auditor
- Performance regression < 5% vs clean Fedora
- 95%+ Steam game compatibility
- < 5 critical bugs open

---

## Phase 4: Stable (Q3 2027)

**Goal:** Public release — Linux Synthex 1.0 "Ignition"

### Deliverables

#### Release
- [ ] Linux Synthex 1.0 ISO (all editions)
- [ ] Release announcement
- [ ] Press kit
- [ ] Release notes
- [ ] Upgrade guide from Fedora
- [ ] Known issues document
- [ ] Community celebration 🎉

#### Post-Release
- [ ] Stable updates repository online
- [ ] Point releases (1.1, 1.2) scheduled
- [ ] Security response team formed
- [ ] Community governance established
- [ ] Contributor program launched

### Success Criteria
- 10,000+ downloads in first month
- Positive reviews from Linux press
- Boot time < 10 seconds on modern hardware
- Idle RAM < 800 MB
- 90%+ user satisfaction survey

---

## Phase 5: Long-Term Support (Q4 2027+)

**Goal:** Enterprise-grade LTS release with commercial support options.

### Deliverables

#### LTS Release
- [ ] Linux Synthex 2.0 LTS
- [ ] 5-year support commitment
- [ ] Commercial support tiers
- [ ] Enterprise compliance certifications
- [ ] GovCloud/air-gapped deployment support
- [ ] Real-time kernel variant (industrial)

#### Ecosystem
- [ ] Synthex Flatpak remote
- [ ] Synthex App Store
- [ ] Synthex Certified Hardware program
- [ ] OEM pre-install partnerships
- [ ] Synthex Cloud images (AWS, Azure, GCP)

---

## Key Milestones Summary

| Milestone | Date | Target |
|-----------|------|--------|
| Architecture complete | Q3 2026 | Documentation + design |
| First bootable ISO | Q3 2026 | Internal development |
| Alpha release | Q4 2026 | Community testing |
| Beta release | Q1 2027 | Early adopters |
| Release Candidate | Q2 2027 | Pre-production |
| **Synthex 1.0 Stable** | **Q3 2027** | **Public launch** |
| Synthex 2.0 LTS | Q4 2027+ | Enterprise |

---

## Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Kernel maintainer shortage | High | Medium | Training program, Red Hat collaboration |
| NVIDIA Wayland issues | High | Medium | Fallback to X11 session option |
| Package dependency conflicts | Medium | Medium | CI/CD testing, staged updates |
| Community adoption slow | Medium | Low | Strong onboarding, Windows migration tools |
| Funding/budget constraints | Medium | Medium | Open-source, community-driven, Copr infrastructure |
| Security vulnerability in stack | High | Low | Rapid patching, defense-in-depth, security team |

---

## Get Involved

- **Contribute:** See [CONTRIBUTING.md](docs/developer/contributing.md)
- **Report Bugs:** GitHub Issues
- **Join Discussion:** Discord / Matrix
- **Test:** Run the beta ISO and submit feedback
- **Package:** Help maintain Synthex repository packages
- **Document:** Improve our documentation
- **Donate:** Support infrastructure costs

---

<div align="center">
  <i>"Illuminate Your Desktop"</i>
</div>
