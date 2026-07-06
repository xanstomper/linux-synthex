# Solus Linux - Installer UX Design Document

## 1. Overview

The Solus Linux installer is built on **Calamares** — a distribution-independent system installer framework. This document describes the user experience design, visual layout, installation flow, and interaction patterns for the Solus Linux installer across all three editions (Plasma, Hyprland, GNOME).

### 1.1 Design Philosophy

- **Progressive Disclosure**: Present simple choices first, advanced options on demand
- **Guided Confidence**: Each step explains what's happening and why
- **Immediate Feedback**: Visual indicators for disk operations, progress, and errors
- **Consistent Branding**: Solus teal/cyan palette, clean typography, subtle animations
- **Accessibility First**: High contrast, keyboard navigable, screen-reader compatible

### 1.2 Target Audience

- **Primary**: Linux newcomers migrating from Windows/macOS
- **Secondary**: Experienced Linux users wanting a streamlined install
- **Tertiary**: Developers needing customized partitioning and encryption

---

## 2. Visual Design

### 2.1 Color Palette

```
Primary Background:    #1a1a2e   (Deep navy)
Secondary Background:  #16213e   (Dark blue)
Accent Primary:        #33ccff   (Solus cyan)
Accent Secondary:      #00ff88   (Green for success)
Warning:               #ffcc00   (Amber)
Error:                 #ff4444   (Red)
Text Primary:          #ffffff   (White)
Text Secondary:        #b0b0b0   (Light gray)
```

### 2.2 Typography

- **Headings**: Noto Sans Bold, 16-24px
- **Body**: Noto Sans Regular, 12-14px
- **Monospace**: JetBrains Mono, 12px (for partitions, commands)
- **Line Height**: 1.5 for readability

### 2.3 Layout Structure

```
┌─────────────────────────────────────────────┐
│  ┌──────┐  ┌──────────────────────────────┐ │
│  │Step  │  │                              │ │
│  │Nav   │  │      Main Content Area       │ │
│  │Side  │  │                              │ │
│  │Bar   │  │   [Progress Indicators]      │ │
│  │      │  │                              │ │
│  │○ 1   │  │                              │ │
│  │● 2   │  │                              │ │
│  │○ 3   │  │                              │ │
│  │○ 4   │  │                              │ │
│  │○ 5   │  │                              │ │
│  │○ 6   │  │                              │ │
│  │○ 7   │  │                              │ │
│  └──────┘  │                              │ │
│            │  ┌──────────────────────────┐ │ │
│            │  │ [Back]    [Next] [Cancel] │ │ │
│            │  └──────────────────────────┘ │ │
│            └──────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 2.4 Step Navigation Sidebar

The left sidebar shows the installation flow with a clear hierarchy:

- **Completed steps**: ✓ with the step name (grayed, dimmed)
- **Current step**: ● with the step name (accent color, bold)
- **Pending steps**: ○ with the step name (dimmed)
- **Step grouping**: Sections with dividers (e.g., "Preparation", "Installation", "Configuration")

---

## 3. Installation Flow

### 3.1 Welcome Page

**Purpose**: Language selection, readiness check

**Elements**:
- Solus logo and branding at top
- Language dropdown (50+ languages)
- System requirements checklist:
  - ✓ 2 GB+ RAM detected
  - ✓ 25 GB+ disk space available
  - ✓ Internet connection (optional)
  - ✓ AC power (laptops)
- "Try Solus" button (optional, minimized)
- "Install Solus" primary CTA

**States**:
- Requirements met: green checkmarks, "Install Solus" enabled
- Requirements not met: red X with explanation, "Install Solus" disabled with tooltip
- Loading: skeleton UI while hardware is being probed

### 3.2 Location & Timezone

**Purpose**: Set locale, timezone, and regional preferences

**Elements**:
- Interactive world map for timezone selection (clickable regions)
- Region dropdown: "Americas", "Europe", "Asia", etc.
- Zone dropdown: populated based on region
- Timezone preview showing current time
- System locale: auto-detected from selection
- "System language" toggle to match locale

**Interactions**:
- Map click populates region and zone
- Region change filters zone list
- Timezone detected from IP (fallback if network available)

### 3.3 Keyboard Layout

**Purpose**: Configure keyboard layout and variants

**Elements**:
- Interactive keyboard visualization (SVG keyboard)
- Layout dropdown: 100+ layouts
- Variant dropdown: layout-dependent
- "Detect Keyboard Layout" button (asks user to press specific keys)
- Typing test box to verify layout

**Interactions**:
- Keypress highlights on virtual keyboard
- Real-time preview as user types in test box
- Variant list updates when layout changes

### 3.4 Partitioning

**Purpose**: Disk partitioning with multiple modes

**This is the most complex screen with three modes:**

#### 3.4.1 Automatic (Simple) Mode

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│  ● Erase disk and install Solus              │
│     /dev/sda  500 GB SSD                     │
│                                              │
│  ○ Install alongside existing OS             │
│     [Select partition size slider]           │
│     Windows: 200 GB | Solus: 300 GB          │
│                                              │
│  ○ Manual partitioning (advanced)            │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ [Advanced Options ▸]                    │  │
│  │   ✓ BTRFS (recommended)                │  │
│  │   ○ EXT4                               │  │
│  │   ○ XFS                                │  │
│  │   □ Encrypt with LUKS                  │  │
│  │   □ Use ZRAM for swap                  │  │
│  │   □ Enable snapshots (BTRFS only)      │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  [Back]                          [Next]      │
└──────────────────────────────────────────────┘
```

**BTRFS Features** (when selected):
- Subvolume layout visual tree
- Compression indicator: "zstd:3 (recommended)"
- Snapper snapshot schedule: "50 snapshots, 10 daily"

**Encryption Flow**:
When LUKS is selected:
1. Prompt: "Enter passphrase" + strength indicator
2. Confirm: "Re-enter passphrase"
3. Option: "Save recovery key to USB"
4. Warning: "Losing this passphrase means losing all data"

#### 3.4.2 Manual Mode

**Elements**:
- Disk list on left showing all block devices
- Visual partition map (colored bar representation)
- Partition table with columns: Device, Size, Type, Mount Point, Format, Flags
- Toolbar: + (Add), - (Delete), ✎ (Edit), ↺ (Revert)
- Per-partition options: filesystem, mount point, flags

**Interactions**:
- Click partition to select → details panel below
- Drag partition borders to resize (if free space available)
- Right-click context menu for quick actions
- Double-click to edit partition properties

**Partition Table Visualization**:
```
┌──────────────────────────────────────────────────────────┐
│ /dev/sda  500 GiB                                        │
│ ┌──────┬──────────────┬────────────────────────────────┐ │
│ │EFI   │  Boot        │  BTRFS (Solus)                  │ │
│ │512MB │  1 GiB       │  498 GiB                        │ │
│ │fat32 │  ext4        │  /  @ /home @var @snapshots    │ │
│ └──────┴──────────────┴────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 3.5 User Creation

**Purpose**: Create user account and set passwords

**Elements**:
- Name: full name (real name)
- Username: auto-filled from name, editable
- Computer name (hostname): auto-generated, editable
- Password: with strength indicator
- Confirm password
- "Require password to log in" toggle
- "Encrypt home folder" option (if not already via LUKS)
- "Log in automatically" toggle (with security warning)
- Avatar selection (8 presets + custom file picker)

**Password Strength Indicator**:
- Red bar: < 8 chars, weak
- Yellow bar: 8-12 chars, fair
- Light green: 12-16 chars, good
- Green: 16+ chars, strong

### 3.6 Summary / Review

**Purpose**: Show full installation plan before committing

**Elements**:
- Collapsible sections for each configuration area:
  - **Installation Mode**: Device, filesystem, encryption status
  - **Location**: Timezone, locale, keyboard layout
  - **User**: Username, auto-login setting
  - **Disks**: Full partition table with changes list (what will be created/formatted)
  - **Advanced**: Snapshot config, swap config, services
- "Warning: All data on selected partitions will be erased" (red box)
- Checkbox: "I understand that my disk will be modified"
- [Install] button (disabled until checkbox checked)

**Disk Change Summary Style**:
```
Actions to be performed:
  ✓ /dev/sda1 will be formatted as FAT32 (EFI System)
  ✓ /dev/sda2 will be formatted as EXT4 (/boot)
  ✓ /dev/sda3 will be formatted as BTRFS with LUKS encryption (/)
  ✓ /dev/sda4 will be created as BTRFS subvolume @home (/home)
  ✓ Sda3 will be encrypted with LUKS2 (AES-XTS-512)
```

### 3.7 Installation Progress

**Purpose**: Show real-time installation progress

**Elements**:
- Progress bar with percentage and elapsed time
- Current operation description (e.g., "Formatting partitions...", "Extracting files...")
- Detailed log (collapsible, expandable)
- Per-operation checkmarks as they complete
- Cancel button (with "Are you sure?" confirmation dialog)

**Progress Steps**:
1. ✓ Preparing installation (2%)
2. ✓ Partitioning disks (5%)
3. ✓ Formatting partitions (8%)
4. ✓ Mounting filesystems (10%)
5. Extracting system files (15-75%)
   - Sub-progress: "1427/5842 files extracted"
6. ✓ Configuring system (80%)
7. ✓ Installing bootloader (88%)
8. ✓ Setting up users (92%)
9. ✓ Running post-install scripts (95%)
10. ✓ Installation complete (100%)

**Error Handling**:
- Errors shown inline with the failed step highlighted in red
- "Retry" button for recoverable errors
- "Skip" option for non-critical failures
- "View Log" button for diagnostics
- "Save Log to USB" option for bug reports

### 3.8 Completion / Restart

**Purpose**: Confirm successful installation and offer next steps

**Elements**:
- Success message with Solus logo animation
- "Installation Complete!" heading
- Installation summary (time elapsed, size installed)
- Post-install tips:
  - "Visit getsol.us/welcome to get started"
  - "Check for updates in Solus Software Center"
  - "Explore pre-installed applications"
- "Restart Now" button (primary, default)
- "Keep Testing" button (stays in live environment)
- Countdown timer (30 seconds) before auto-restart
- "Eject installation media" reminder

---

## 4. Responsive Behaviors

### 4.1 Window Resizing

| Element | Min Width | Min Height | Behavior |
|---------|-----------|------------|----------|
| Full window | 800px | 600px | Centered on screen |
| Sidebar | 200px | 100% | Fixed width, scrolls internally |
| Content | 600px | 600px | Fluid width, scrolls internally |
| Partition map | 500px | 120px | Scales proportionally |

### 4.2 HiDPI Support

- Automatic detection via Qt scaling factor
- SVG assets for crisp rendering at all scales
- Font sizes in pt (not px) for proper DPI adaptation

---

## 5. Accessibility

### 5.1 Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to next control |
| Shift+Tab | Move to previous control |
| Enter/Space | Activate control |
| Alt+[1-8] | Jump to step N |
| Ctrl+Z | Undo last partition change |
| Escape | Close dialog / Cancel |

### 5.2 Visual Accessibility

- Minimum 4.5:1 contrast ratio for all text
- Focus indicators visible (2px colored border)
- Icons paired with text labels (never icons alone)
- No blinking/flashing elements
- Partition colors distinguishable by pattern (accessible colorblind palette)

### 5.3 Screen Reader Support

- All interactive elements have ARIA labels
- Progress updates announced via live regions
- Error messages linked to their controls
- Partition table uses proper table markup

---

## 6. Branding Elements

### 6.1 Logo Assets

| Asset | Size | Format | Usage |
|-------|------|--------|-------|
| solus-logo.png | 256x256 | PNG RGBA | Branding header |
| solus-logo.svg | Vector | SVG | Scaling contexts |
| solus-icon.png | 48x48 | PNG | Window icon |
| solus-welcome.png | 800x400 | PNG | Welcome background |
| installer-bg.png | 1920x1080 | PNG | Background/wallpaper |

### 6.2 Animation Guidelines

- Transitions: 200ms ease-in-out
- Progress fills: fluid, no stepped increments
- Success indicators: 1s pulse on completion
- Loading spinners: 20rpm continuous rotation
- No decorative animation that delays interaction

### 6.3 Copy & Tone

- **Technical accuracy** over marketing language
- **Positive framing**: "You can" not "You need to"
- **Clear error messages**: "Not enough disk space" not "Installation failed"
- **No jargon without explanation**: "BTRFS (a modern filesystem with snapshot support)"

---

## 7. Error & Edge Cases

### 7.1 Low Disk Space

- Warning threshold: < 30 GB remaining
- Critical threshold: < 25 GB remaining
- "Free up space" suggestion with disk usage analyzer shortcut

### 7.2 Insufficient RAM

- Warning: < 4 GB RAM
- Critical: < 2 GB RAM (installation blocked)
- "Install with swap" suggestion

### 7.3 No Internet Connection

- Offline mode: full installation available
- Feature reduction: no timezone auto-detection, no language pack downloads
- "Connect to network" prompt with network manager shortcut

### 7.4 UEFI vs Legacy BIOS

- Auto-detect firmware type
- UEFI: force GPT, create EFI System Partition
- Legacy: allow MBR or GPT, install BIOS boot
- Dual-boot detection: show existing EFI entries

### 7.5 Dual Boot Detection

- Scan for existing OS installations
- Display detected OS list: "Windows 11 detected", "Ubuntu 24.04 detected"
- "Install alongside" option with size slider
- Boot order configuration after install

### 7.6 Power Failures

- Atomic operations where possible
- Journaling filesystem (BTRFS)
- Recovery prompt on next boot if interrupted

---

## 8. Internationalization

### 8.1 Supported Languages

- Full UI translation: 15 languages (en, de, fr, es, it, pt-BR, ru, ja, zh-CN, zh-TW, ko, pl, nl, sv, tr)
- Partial UI translation: 35+ additional languages
- RTL language support: Arabic, Hebrew, Persian

### 8.2 Translation Guidelines

- Each string wrapped in tr() function for gettext
- Context comments for ambiguous terms
- Screenshot references for translators
- No concatenation of translated strings

---

## 9. Testing Checklist

### 9.1 Functional Tests

- [ ] Welcome page requirements detection
- [ ] Language switch updates entire UI
- [ ] Timezone map interaction
- [ ] Keyboard layout test box
- [ ] Automatic partitioning (erase)
- [ ] Automatic partitioning (alongside)
- [ ] Manual partitioning (create/edit/delete)
- [ ] BTRFS subvolume creation
- [ ] LUKS encryption creation and unlock
- [ ] User creation with all options
- [ ] Summary accuracy
- [ ] Progress reporting
- [ ] Error recovery
- [ ] Cancel during installation
- [ ] Post-install scripts execution
- [ ] Bootloader installation (UEFI)
- [ ] Bootloader installation (BIOS)
- [ ] Restart behavior

### 9.2 Visual Tests

- [ ] Window sizing and scaling
- [ ] HiDPI rendering
- [ ] Color contrast compliance
- [ ] Keyboard navigation
- [ ] Screen reader traversal
- [ ] RTL layout support
- [ ] All translations loaded
- [ ] Logo and branding assets
- [ ] Error state styling
- [ ] Loading state styling

### 9.3 Edge Cases

- [ ] Multiple disks
- [ ] NVMe drives
- [ ] RAID controllers
- [ ] Virtual machine environments
- [ ] Very large disks (4TB+)
- [ ] Very small disks (< 32GB)
- [ ] Existing LVM volumes
- [ ] Existing BTRFS with snapshots
- [ ] Encrypted existing partitions
- [ ] Secure Boot enabled

---

## 10. Appendix

### 10.1 File Layout

```
installer/
├── config/
│   └── calamares-settings.conf    # Main installer configuration
├── design/
│   └── installer-design.md        # This document
├── modules/
│   ├── welcome/                   # Welcome page module
│   ├── partition/                 # Partitioning module
│   ├── users/                     # User management module
│   └── summary/                   # Summary module
├── branding/
│   ├── solus/                     # Solus branding assets
│   │   ├── images/
│   │   │   ├── solus-logo.png
│   │   │   ├── solus-welcome.png
│   │   │   └── installer-bg.png
│   │   ├── slideshow.qml
│   │   └── translations/
│   └── CMakeLists.txt
└── themes/
    ├── solus-dark/                # Dark theme QSS
    └── solus-light/               # Light theme QSS
```

### 10.2 Related Documentation

- [Calamares Wiki](https://github.com/calamares/calamares/wiki)
- [Calamares Source](https://github.com/calamares/calamares)
- [Solus Brand Guidelines](https://getsol.us/branding)
- [BTRFS Sysadmin Guide](https://btrfs.readthedocs.io)
