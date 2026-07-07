# Contributing to SynthOS

> **Audience:** Developers, designers, translators, and community members  
> **Last updated:** July 2026  
> **Repository:** https://github.com/synthex-project

---

## Table of Contents

1. [Code of Conduct](#1-code-of-conduct)
2. [Getting Started as a Contributor](#2-getting-started-as-a-contributor)
3. [Development Environment Setup](#3-development-environment-setup)
4. [Repository Overview](#4-repository-overview)
5. [Coding Standards](#5-coding-standards)
6. [Package Contribution Guide](#6-package-contribution-guide)
7. [Theme Contribution Guide](#7-theme-contribution-guide)
8. [Documentation Contribution Guide](#8-documentation-contribution-guide)
9. [Translation Guide](#9-translation-guide)
10. [Testing Requirements](#10-testing-requirements)
11. [PR Workflow](#11-pr-workflow)
12. [Review Process](#12-review-process)
13. [Community Roles](#13-community-roles)

---

## 1. Code of Conduct

### 1.1 Our Pledge

As a member of the Synthex community, we are committed to creating a welcoming, inclusive, and harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### 1.2 Our Standards

**Examples of behavior that contributes to a positive environment:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**

- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### 1.3 Enforcement

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at **conduct@getsynthex.org**. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances.

### 1.4 Scope

This Code of Conduct applies both within project spaces and in public spaces when an individual is representing the project or its community.

### 1.5 Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining the consequences for any action they deem in violation of this Code of Conduct:

| Violation | Consequence |
|-----------|-------------|
| **Minor infraction** (e.g., inappropriate language) | Private warning with clarification |
| **Repeated minor infractions** | Public warning, temporary restriction |
| **Major violation** (e.g., harassment, personal attack) | Temporary or permanent ban |
| **Extreme violation** (e.g., hate speech, doxxing) | Immediate permanent ban |

---

## 2. Getting Started as a Contributor

### 2.1 First Steps

1. **Join the community:**
   - [Synthex Forums](https://discuss.getsynthex.org)
   - [Synthex Matrix Chat](https://matrix.to/#/#synthex:matrix.org)
   - [Synthex Discord](https://discord.gg/synthex)
   - [Synthex IRC](ircs://irc.libera.chat:6697/#synthex)

2. **Find something to work on:**
   - Look for issues tagged `help-wanted` or `good-first-issue` on GitHub
   - Check the [Synthex Issue Tracker](https://github.com/synthex-project/issues)
   - Join the #synthex-dev channel and ask for guidance
   - Review the [Roadmap](https://wiki.getsynthex.org/Roadmap)

3. **Understand the project structure:**
   - Synthex packages (RPM spec files)
   - Synthex tools and infrastructure
   - Desktop integration and theming
   - Documentation and translations
   - Quality assurance and testing

### 2.2 Contribution Paths

| Role | Skills | Typical Tasks |
|------|--------|--------------|
| **Package Maintainer** | RPM packaging, dependency resolution | Maintaining and updating packages |
| **Developer** | C/C++, Python, Qt, system programming | Core tools, infrastructure, bug fixes |
| **Designer** | SVG, color theory, KDE theming | Themes, icons, branding, UI polish |
| **Documentation Writer** | Technical writing, markdown | Guides, wiki, API docs, tutorials |
| **Translator** | Foreign language fluency | Localization, l10n, i18n |
| **QA Tester** | Attention to detail, testing methods | Bug reporting, regression testing |
| **Community Support** | Patience, communication skills | Forum/chat assistance, onboarding |

---

## 3. Development Environment Setup

### 3.1 Prerequisites

```bash
# Install development tools
sudo dnf5 group install "Development Tools"
sudo dnf5 install git git-lfs curl wget

# Install RPM development tools
sudo dnf5 install rpm-build rpmdevtools rpmlint

# Install Mock (for building packages in chroot)
sudo dnf5 install mock
sudo usermod -aG mock $USER
# Log out and back in for group changes

# Install Python development tools
sudo dnf5 install python3 python3-devel python3-pip
python3 -m pip install --user pre-commit

# Install documentation tools
sudo dnf5 install python3-sphinx python3-sphinx-rtd-theme doxygen
```

### 3.2 Clone Repositories

```bash
# Create workspace
mkdir -p ~/synthex-dev
cd ~/synthex-dev

# Clone main repositories
git clone https://github.com/synthex-project/packages.git
git clone https://github.com/synthex-project/synthex-sc.git
git clone https://github.com/synthex-project/synthex-settings.git
git clone https://github.com/synthex-project/artwork.git
git clone https://github.com/synthex-project/synthex-website.git
git clone https://github.com/synthex-project/docs.git

# Clone package-specific repos (if working on a specific package)
git clone https://github.com/synthex-project/linux.git
git clone https://github.com/synthex-project/mesa.git
# ... etc.
```

### 3.3 Set Up Git Configuration

```bash
# Configure git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global pull.rebase true
git config --global fetch.prune true

# Fork the repo on GitHub and add your fork as remote
cd ~/synthex-dev/packages
git remote add fork git@github.com:YOUR_USERNAME/packages.git
```

### 3.4 Set Up Pre-Commit Hooks

```bash
# Install pre-commit hooks (found in .pre-commit-config.yaml)
cd ~/synthex-dev/packages
pre-commit install

# This will automatically run checks before each commit:
# - rpmlint (RPM spec validation)
# - shellcheck (shell script validation)
# - trailing-whitespace fixes
# - end-of-file fixes
```

### 3.5 Development Tools

#### Visual Studio Code
```bash
flatpak install flathub com.visualstudio.code
# Recommended extensions:
# - RPM Spec (lang-rpm)
# - ShellCheck
# - GitLens
# - YAML
# - Markdown Preview Enhanced
```

#### Kate (KDE Advanced Editor)
```bash
sudo dnf5 install kate
# Kate has excellent RPM spec highlighting and LSP support
```

---

## 4. Repository Overview

### 4.1 Main Repositories

| Repository | Description | Language/Tools |
|------------|-------------|----------------|
| [packages](https://github.com/synthex-project/packages) | RPM spec files for all Synthex packages | RPM spec, shell |
| [synthex-sc](https://github.com/synthex-project/synthex-sc) | Synthex Software Center | Python, Qt6 |
| [synthex-settings](https://github.com/synthex-project/synthex-settings) | System configuration defaults | INI, XML, shell |
| [artwork](https://github.com/synthex-project/artwork) | Branding, themes, wallpapers | SVG, QML, CSS |
| [linux](https://github.com/synthex-project/linux) | SynthOS kernel config | Kernel config, patches |
| [docs](https://github.com/synthex-project/docs) | Documentation | Markdown, reStructuredText |
| [synthex-website](https://github.com/synthex-project/website) | getsynthex.org website | Hugo, Markdown |
| [synthex-installer](https://github.com/synthex-project/calamares) | Calamares installer config | YAML, Python |

### 4.2 Repository Structure (packages)

```
packages/
├── packages/                    # Package definitions (by name)
│   ├── f/
│   │   └── firefox/
│   │       ├── firefox.spec     # RPM spec file
│   │       ├── sources          # Source tarball URLs
│   │       ├── patches/         # Distribution patches
│   │       │   ├── firefox-synthex-defaults.patch
│   │       │   └── firefox-wayland-default.patch
│   │       └── tests/           # Package-level tests
│   │           └── smoke-test.sh
│   ├── k/
│   │   └── kate/
│   ├── l/
│   │   └── linux/
│   └── .../
├── groups/                      # Package groups
│   ├── base-synthex.conf
│   ├── desktop-plasma.conf
│   └── development.conf
├── Makefile                     # Build orchestration
├── Makefile.common              # Common build rules
└── scripts/                     # Build/CI helper scripts
```

### 4.3 Repository Branches

| Branch | Purpose | Merge Policy |
|--------|---------|-------------|
| `master` | Development branch | All PRs target this |
| `stable` | Released branch | Merged from master before releases |
| `feature/*` | Feature branches | Short-lived, merged to master |
| `fix/*` | Bug fix branches | Short-lived, merged to master |

---

## 5. Coding Standards

### 5.1 General Guidelines

- **Consistency over perfection**: Follow existing patterns in the codebase
- **Readability**: Code is read more often than written — prioritize clarity
- **Comments**: Explain *why*, not *what* (the code shows *what*)
- **Documentation**: Every public API/function needs a docstring
- **Error handling**: Always check return values and handle errors gracefully

### 5.2 Python (for synthex-sc and tools)

```python
"""
Module docstring describing purpose.

Use reStructuredText format.
"""
import os
import sys
from typing import Optional, List

# Constants in UPPER_CASE
MAX_RETRIES = 3

# Classes in PascalCase
class PackageManager:
    """Handle package operations."""

    # Public methods in snake_case
    def install_package(self, name: str, version: Optional[str] = None) -> bool:
        """
        Install a package by name.

        Args:
            name: Package name to install
            version: Specific version (default: latest)

        Returns:
            True if installation succeeded, False otherwise

        Raises:
            PackageNotFoundError: If package doesn't exist
        """
        if not name:
            raise ValueError("Package name cannot be empty")
        # Implementation
        return True

    # Private methods prefixed with underscore
    def _resolve_dependencies(self, packages: List[str]) -> List[str]:
        """Resolve package dependencies (internal)."""
        pass

# Module-level functions in snake_case
def get_cache_dir() -> str:
    """Return the cache directory path."""
    return os.path.expanduser("~/.cache/synthex-sc")
```

**Python style:**
- Follow [PEP 8](https://peps.python.org/pep-0008/) strictly
- Line length: 100 characters
- Use type hints for all public functions
- Use f-strings for string formatting
- Use pathlib for file paths (not os.path)

### 5.3 Shell Scripts

```bash
#!/bin/bash
#
# Description of the script's purpose.
# Usage: ./script-name.sh [options]

set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_FILE="${HOME}/.config/synthex-tool.conf"

# Functions
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -o, --output    Output directory

Description:
    This script does something useful for Synthex.
EOF
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) usage ;;
        -v|--verbose) VERBOSE=1 ;;
        -o|--output) OUTPUT_DIR="$2"; shift ;;
        *) log "Unknown option: $1"; usage ;;
    esac
    shift
done

# Main
main() {
    log "Starting..."
    # Implementation
    log "Done."
}

main "$@"
```

**Shell style:**
- Always use bash shebang (`#!/bin/bash`)
- Use `set -euo pipefail` for strict error handling
- Use `readonly` for constants
- Prefer `[[ ]]` over `[ ]` for conditionals
- Quote all variable expansions: `"$var"`
- Use functions for logical grouping
- Document usage with `usage()` function

### 5.4 RPM Spec Files

```rpm
# spec file for firefox
%global maj_ver 128
%global min_ver 0

Name:       firefox
Version:    128.0.3
Release:    1%{?dist}
Summary:    Mozilla Firefox Web Browser

License:    MPL-2.0
URL:        https://www.mozilla.org/firefox/
Source0:    https://archive.mozilla.org/pub/firefox/releases/%{version}/source/firefox-%{version}.source.tar.xz
Source1:    firefox.desktop
Source2:    firefox-synthex-branding

Patch0:     firefox-wayland-default.patch
Patch1:     firefox-synthex-search.patch

BuildRequires:  gcc-c++
BuildRequires:  rust >= 1.70
BuildRequires:  nasm
BuildRequires:  pkgconfig(nspr)
BuildRequires:  pkgconfig(nss)
BuildRequires:  python3-devel
# ... other BRs

Requires:       dbus
Requires:       libX11
Requires:       pulseaudio-libs

%description
Mozilla Firefox is a free, open-source web browser.

%prep
%setup -q -n firefox-%{version}
%patch0 -p1
%patch1 -p1

%build
%configure \
    --enable-application=browser \
    --enable-optimize \
    --enable-default-toolkit=cairo-gtk3-wayland \
    --disable-crashreporter \
    --with-system-nspr \
    --with-system-nss
%make_build

%install
%make_install
install -Dm0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop

%check
# Smoke test
./mach test --headless

%files
%license LICENSE
%doc README.txt
%{_bindir}/firefox
%{_libdir}/firefox/
%{_datadir}/applications/firefox.desktop
%{_datadir}/icons/hicolor/*/apps/firefox*
%{_datadir}/pixmaps/firefox*
%{_mandir}/man1/firefox.1*

%changelog
* Mon Jun 23 2026 Developer Name <dev@getsynthex.org> - 128.0.3-1
- Update to 128.0.3
- Security fixes
```

**Spec file conventions:**
- Use `%global` for version macros
- Order sections: Name → Version → (Build)Requires → Description → %prep → %build → %install → %check → %files → %changelog
- All BuildRequires should be pkgconfig-style when possible
- Include a %check section for smoke tests
- Keep %files list comprehensive with file globs

### 5.5 Commit Messages

```
component: Brief summary of changes (50 chars max)

Detailed description of what and why, wrapped at 72 characters.
Explain the motivation for the change, not just the implementation.

Fixes: #1234
Related: #5678

Signed-off-by: Your Name <email@example.com>
```

| Prefix | Component |
|--------|-----------|
| `firefox:` | Firefox package changes |
| `kernel:` | Kernel package/config changes |
| `synthex-sc:` | Software Center |
| `docs:` | Documentation |
| `artwork:` | Themes and branding |
| `ci:` | Build system / CI changes |
| `meta:` | Repository meta-files |
| `lib/` | Library packages |
| `fix:` | Bug fixes |
| `feat:` | New features |
| `refactor:` | Code restructuring |
| `test:` | Test additions or modifications |

---

## 6. Package Contribution Guide

### 6.1 Package Lifecycle

```
Upstream Release → Spec Update → Local Build → Test → PR → Review → Merge → Build → Release
```

### 6.2 Adding a New Package

1. **Check if package already exists:**
   ```bash
   ls ~/synthex-dev/packages/packages/*/<package-name>
   # Or search the repository
   ```

2. **Create package directory:**
   ```bash
   cd ~/synthex-dev/packages
   mkdir -p packages/<first-letter>/<package-name>
   ```

3. **Create spec file:**
   ```bash
   cd packages/<first-letter>/<package-name>
   # Create <package-name>.spec (see Section 5.4 for template)
   ```

4. **Create sources file:**
   ```
   # sources file containing tarball checksums
   SHA256 (package-1.0.0.tar.gz) = abc123...
   ```

5. **Create initial patch set (if needed):**
   ```bash
   mkdir patches
   ```

6. **Build locally (see building-packages.md):**
   ```bash
   make -C ../.. <package-name>
   ```

7. **Submit PR with:**
   - The spec file
   - sources file
   - Any patches
   - A brief description of the package and its purpose

### 6.3 Updating a Package

```bash
# 1. Clone or update packages repo
cd ~/synthex-dev/packages
git checkout master
git pull upstream master

# 2. Find the package
cd packages/<first-letter>/<package-name>

# 3. Update Version in spec
# 4. Update sources tarball URL and checksum
# 5. Update patches if needed
# 6. Test build
# 7. Commit and PR
```

### 6.4 Package Review Checklist

| Check | Criteria |
|-------|----------|
| **Licensing** | License is FOSS-compatible, `%license` used |
| **Dependencies** | All BuildRequires/Requires listed correctly |
| **Security** | No insecure practices (hardcoded paths, etc.) |
| **Files** | All files listed, correct permissions |
| **Scriptlets** | No unnecessary scriptlets |
| **Tests** | %check present if upstream has tests |
| **Patches** | Upstream-ready, documented in spec |

---

## 7. Theme Contribution Guide

### 7.1 Types of Themes

| Theme Type | Format | Location in repo |
|------------|--------|-----------------|
| **Plasma Style** | QML + SVG | `artwork/plasma-styles/` |
| **Color Scheme** | .colors | `artwork/color-schemes/` |
| **Icon Theme** | SVG icons | `artwork/icons/` |
| **Cursor Theme** | XCursor + SVG | `artwork/cursors/` |
| **Window Decorations** | QML | `artwork/decorations/` |
| **Wallpapers** | PNG/JPG/SVG | `artwork/wallpapers/` |
| **Splash Screen** | QML | `artwork/splash/` |
| **SDDM Theme** | QML | `artwork/sddm/` |
| **GRUB Theme** | Config + images | `artwork/grub/` |

### 7.2 Creating a Theme

```bash
# Fork and clone artwork repo
git clone https://github.com/YOUR_USERNAME/artwork.git
cd artwork

# Create new theme directory
mkdir -p plasma-styles/my-theme/
cd plasma-styles/my-theme/

# Create metadata
cat > metadata.desktop <<EOF
[Desktop Entry]
Name=My Theme
Comment=A custom Synthex theme
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Name=my-theme
X-KDE-PluginInfo-Category=Plasma Theme
X-KDE-PluginInfo-License=GPL-2.0+
EOF

# Create theme files (SVG, QML, etc.)
# See existing themes for structure
```

### 7.3 Theme Design Guidelines

- **Follow Synthex brand colors** (accent, complementary)
- **Support dark and light variants**
- **Test on both Wayland and X11**
- **Support HiDPI** (provide SVG elements where possible)
- **Maintain readability** — high contrast for text
- **Match panel transparency** (default: translucent)

### 7.4 Synthex Brand Colors

```
Primary:    #5294E2   (Blue - accent)
Secondary:  #1B1B1B   (Dark gray - backgrounds)
Light:      #FFFFFF   (White - text on dark)
Text:       #31363B   (Dark text on light)
Success:    #27AE60   (Green)
Warning:    #F39C12   (Orange)
Error:      #E74C3C   (Red)
Info:       #3498DB   (Blue)

Background Dark:  #2E3440 (Nord dark)
Background Light: #F5F5F5
Surface Dark:     #3B4252
Surface Light:    #FFFFFF
```

### 7.5 Submitting Theme

1. Push to your fork
2. Create PR against artwork repository
3. Include screenshots of your theme
4. List any dependencies or special requirements
5. Ensure all metadata is correct

---

## 8. Documentation Contribution Guide

### 8.1 Documentation Repositories

| Repository | Content | Format |
|------------|---------|--------|
| [docs](https://github.com/synthex-project/docs) | User guides, admin guides | Markdown |
| [wiki](https://wiki.getsynthex.org) | Wiki content (via Git) | MediaWiki |
| [website](https://github.com/synthex-project/website) | getsynthex.org website | Hugo/Markdown |
| API docs | In-source docstrings | reStructuredText / Doxygen |

### 8.2 Documentation Style Guide

#### Markdown conventions:

```markdown
# Document Title (H1 - Page title only)

## Section (H2 - Major sections)

### Subsection (H3 - Within sections)

#### Sub-subsection (H4 - Avoid if possible)

**Bold** for UI elements, menu items
`Code` for commands, filenames, variables
> Blockquote for notes, warnings, tips

Lists:
- Use dashes for unordered lists
- Keep items parallel in structure

1. Numbered lists for sequential steps
2. Each step is a complete action

[Links](https://example.com) with descriptive text
```

#### Note/Warning/Tip blocks:

```markdown
> **Note:** Additional information that may be useful but not critical.

> **Warning:** Important information about potential issues or data loss.

> **Tip:** A helpful suggestion to improve the reader's experience.
```

#### Code blocks with language tags:

````markdown
```bash
# Shell commands
sudo dnf5 install package
```

```python
# Python code
def hello():
    print("Hello, Synthex!")
```

```yaml
# YAML configuration
key: value
```
````

### 8.3 Documentation Workflow

1. **Find documentation to improve:**
   - Look for `docs:` issues on GitHub
   - Check the wiki for outdated content
   - Note areas users frequently ask about

2. **Write content:**
   ```
   docs/
   ├── architecture/
   ├── user/
   ├── developer/
   ├── security/
   └── build/
   ```

3. **Submit PR:**
   ```bash
   git checkout -b docs/my-improvement
   # Make changes
   git add docs/my-new-guide.md
   git commit -m "docs: Add guide for XYZ"
   git push origin docs/my-improvement
   # Create PR on GitHub
   ```

### 8.4 Documentation Review

| Reviewer | Focus |
|----------|-------|
| **Technical review** | Accuracy of commands, explanations |
| **Editorial review** | Grammar, clarity, structure |
| **User testing** | Can a new user follow the guide? |
| **Link check** | All internal/external links work |

---

## 9. Translation Guide

### 9.1 Translation Platforms

Synthex uses **Weblate** for community translations:

```
https://translate.getsynthex.org
```

### 9.2 Getting Started with Translations

1. **Create an account on Weblate** (or use GitHub login)
2. **Browse to a project** you want to translate
3. **Select your language** from the list
4. **Start translating** strings

### 9.3 Translating Software

For Synthex applications (synthex-sc, etc.):

```bash
# .ts files (Qt Linguist format)
# Located in: synthex-sc/translations/
# Tools needed:
sudo dnf5 install qt6-linguist

# Update translation files
lupdate synthex-sc.pro

# Edit translations
linguist translations/synthex-sc_de.ts

# Release translations
lrelease translations/synthex-sc_de.ts
```

### 9.4 Translation Guidelines

- **Maintain context** — read the surrounding UI/story
- **Keep it natural** — prefer natural phrasing over literal translation
- **Technical terms** — keep untranslated if they're common (e.g., "file", "save")
- **Short strings** — screens have limited space; keep translations concise
- **Placeholders** — preserve `%1`, `%2`, etc. (they're replaced at runtime)
- **Accelerators** — preserve `&` for keyboard shortcuts where appropriate

### 9.5 Language Quality Levels

| Level | Progress | Status |
|-------|----------|--------|
| **Core** | 100% translated | Included in release |
| **Complete** | >80% translated | Included in release |
| **Partial** | >50% translated | Available via update |
| **Incomplete** | <50% translated | Available via web only |

---

## 10. Testing Requirements

### 10.1 Testing Levels

| Level | Scope | Required For |
|-------|-------|-------------|
| **L0 - Build** | Package builds successfully | All PRs |
| **L1 - Smoke** | Basic functionality works | All PRs |
| **L2 - Integration** | Works with other components | Feature PRs |
| **L3 - Regression** | Existing features not broken | Complex PRs |
| **L4 - Performance** | No performance degradation | System-level changes |

### 10.2 Build Testing

```bash
# Every package PR must build successfully:

# 1. Mock build (isolated chroot)
mock -r synthex-x86_64 --rebuild <package>.src.rpm

# 2. Local build
make -C ~/synthex-dev/packages <package-name>

# 3. rpmlint validation
rpmlint <package>.rpm
# Expected: No errors, minimal warnings
```

### 10.3 Smoke Testing

```bash
# After successful build, install and verify:
sudo dnf5 install <package>.rpm

# Run the application
<package-binary> --version

# Check it doesn't crash
<package-binary> --help

# For libraries:
ldconfig -p | grep <package>
```

### 10.4 Automated Testing

```bash
# Run package tests
cd packages/<first-letter>/<package-name>
make test

# Run integration tests (if applicable)
cd ~/synthex-dev/synthex-sc
python3 -m pytest tests/
```

### 10.5 Test Requirements by PR Type

| PR Type | Build | Smoke | Integration | Regression |
|---------|-------|-------|-------------|------------|
| Version bump | ✅ | ✅ | ❌ | ❌ |
| New package | ✅ | ✅ | ❌ | ❌ |
| Bug fix | ✅ | ✅ | ❌ | ✅ |
| Feature | ✅ | ✅ | ✅ | ✅ |
| Security fix | ✅ | ✅ | ✅ | ✅ |
| Architecture change | ✅ | ✅ | ✅ | ✅ |

---

## 11. PR Workflow

### 11.1 PR Lifecycle

```
Fork → Branch → Commit → Push → PR → Review → CI → Merge → Deploy
```

### 11.2 Step-by-Step PR Process

#### 1. Create a Fork
```bash
# On GitHub, fork the repository to your account
# Then clone your fork:
git clone git@github.com:YOUR_USERNAME/packages.git
cd packages
git remote add upstream https://github.com/synthex-project/packages.git
```

#### 2. Create a Feature Branch
```bash
git checkout master
git pull upstream master
git checkout -b update-firefox-128
```

#### 3. Make Changes
```bash
# Edit files
vim packages/f/firefox/firefox.spec
# Stage and commit
git add packages/f/firefox/
git commit -m "firefox: Update to 128.0.3

- Security fixes for CVE-2024-XXXX
- Bug fixes for stability
- Update patches for new version

Fixes: #1234
Signed-off-by: Your Name <email@example.com>"
```

#### 4. Push to Fork
```bash
git push origin update-firefox-128
```

#### 5. Create Pull Request
```bash
# On GitHub, navigate to your fork
# Click "Compare & pull request"
# Fill in PR template:
```

**PR Template:**
```markdown
## Summary
Brief description of the changes.

## Type of Change
- [ ] New package
- [ ] Package update
- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Other (describe)

## Testing
- [ ] Build successful
- [ ] Smoke test passed
- [ ] rpmlint clean (or documented exceptions)

## Dependencies
List any new or updated dependencies.

## Related Issues
Fixes: #<issue-number>

## Additional Notes
Any migration steps, configuration changes, or special considerations.
```

#### 6. CI Checks
Automated checks run on every PR:
```
☐ Build check (make package)
☐ rpmlint validation
☐ Dependency resolution
☐ Shellcheck (for scripts)
☐ Pre-commit hooks
```

#### 7. Address Review Feedback
```bash
# Make requested changes
git add -p
git commit -m "firefox: Address review feedback"
git push origin update-firefox-128
```

#### 8. Merge
- PR is merged by a maintainer
- Squash commits if multiple fixup commits

### 11.3 PR Checklist

```
☐ One logical change per PR
☐ Commit messages follow convention
☐ Branch name follows convention (type/component-description)
☐ All CI checks pass
☐ Build succeeds locally
☐ rpmlint reports no errors
☐ Tests pass
☐ Properly tagged with labels (bug, enhancement, documentation)
☐ Linked to relevant issues
☐ Signed-off-by included
```

### 11.4 What to Avoid

- **Large monolithic PRs** — break into logical pieces
- **Unrelated changes** — don't fix whitespace in the same PR as a feature
- **Missing commits** — always include the changelog entry
- **Force-pushing** to shared branches (your fork branch is OK)
- **Closing and reopening PRs** — push new commits instead

---

## 12. Review Process

### 12.1 Review Timeline

| PR Complexity | Expected Review Time |
|---------------|---------------------|
| Simple (version bump) | 1–2 business days |
| Moderate (bug fix) | 2–5 business days |
| Complex (new package) | 5–10 business days |
| Major (architecture) | 10+ business days |

### 12.2 Reviewer Responsibilities

Reviewers check for:

1. **Correctness** — Does the change work as intended?
2. **Security** — Does it introduce vulnerabilities?
3. **Maintainability** — Will it be easy to update?
4. **Style** — Does it follow project conventions?
5. **Testing** — Is there adequate test coverage?
6. **Documentation** — Are changes documented?

### 12.3 Review Levels

| Level | Who | Type |
|-------|-----|------|
| **L1 - Quick review** | Any maintainer | Format, style, basic correctness |
| **L2 - Technical review** | Subject matter expert | Architecture, performance, security |
| **L3 - Security review** | Security team | Critical security changes |
| **L4 - Release review** | Release manager | Pre-release stabilization |

### 12.4 Code Review Etiquette

**For reviewers:**
- Be specific in feedback ("Line 42: This needs error handling")
- Explain *why* something should change
- Acknowledge good code ("This approach is elegant")
- Distinguish between "must fix" and "nice to have"

**For contributors:**
- Don't take feedback personally
- Ask clarifying questions if needed
- Push fixup commits (don't force-push during review)
- Thank reviewers for their time

### 12.5 Approval Requirements

| PR Type | Approvals Required |
|---------|-------------------|
| Bug fix | 1 maintainer |
| Version bump | 1 maintainer |
| New package | 2 maintainers |
| Security fix | 2 maintainers (including security team) |
| Architecture change | 3 maintainers |
| Documentation | 1 maintainer |

---

## 13. Community Roles

### 13.1 Role Hierarchy

```
┌────────────────────────────────────────────────────────────────┐
│                    Community Structure                          │
│                                                                │
│   Synthex Project Lead                                           │
│       │                                                        │
│   ├── Release Manager                                          │
│   │       │                                                    │
│   ├── Package Maintainers                                      │
│   │   ├── Core maintainers (system packages)                   │
│   │   ├── Desktop maintainers (Plasma, GNOME)                  │
│   │   └── Community maintainers (user-contributed)             │
│   │                                                            │
│   ├── Development Team                                         │
│   │   ├── Infrastructure developers                            │
│   │   ├── Desktop integration developers                       │
│   │   └── Tooling developers                                   │
│   │                                                            │
│   ├── Design Team                                              │
│   │   ├── Theme designers                                      │
│   │   ├── Icon designers                                       │
│   │   └── Branding/UX designers                                │
│   │                                                            │
│   ├── Documentation Team                                       │
│   │   ├── Technical writers                                    │
│   │   ├── Wiki maintainers                                     │
│   │   └── Tutorial authors                                     │
│   │                                                            │
│   ├── Translation Team                                         │
│   │   └── Language coordinators per locale                     │
│   │                                                            │
│   ├── Quality Assurance Team                                   │
│   │   ├── Testers                                              │
│   │   ├── Bug triage                                           │
│   │   └── Automated testing                                    │
│   │                                                            │
│   └── Community Team                                           │
│       ├── Forum moderators                                     │
│       ├── Chat moderators                                      │
│       └── Onboarding helpers                                   │
└────────────────────────────────────────────────────────────────┘
```

### 13.2 Role Responsibilities

| Role | Responsibilities | Requirements |
|------|----------------|--------------|
| **Contributor** | Submit PRs, report bugs, help others | None |
| **Package Maintainer** | Maintain one or more packages | 5+ accepted package PRs |
| **Developer** | Core code contributions | Proven technical skills |
| **Designer** | Theme and visual contributions | Portfolio of work |
| **Writer** | Documentation and guides | Writing samples |
| **Translator** | Localization | Fluent in target language |
| **Tester** | QA and bug reporting | Attention to detail |
| **Moderator** | Community management | Community trust |
| **Maintainer** | Merge PRs, guide direction | Sustained contributions |
| **Release Manager** | Coordinate releases | Deep system knowledge |
| **Project Lead** | Project direction | Community consensus |

### 13.3 Becoming a Maintainer

1. **Start contributing** — submit PRs, help in forums
2. **Build trust** — consistent, quality contributions over time
3. **Get nominated** — an existing maintainer nominates you
4. **Vote** — existing maintainers vote (consensus required)
5. **Onboarding** — access to repos, CI, and communication channels

### 13.4 Communication Channels

| Channel | Purpose | URL |
|---------|---------|-----|
| **Matrix** | Real-time dev chat | `#synthex:matrix.org` |
| **Discord** | Community chat | `https://discord.gg/synthex` |
| **IRC** | Legacy chat | `#synthex` on Libera.Chat |
| **Forum** | Discussion, support | `https://discuss.getsynthex.org` |
| **GitHub** | Code, issues, PRs | `https://github.com/synthex-project` |
| **Wiki** | Documentation | `https://wiki.getsynthex.org` |
| **Weblate** | Translations | `https://translate.getsynthex.org` |
| **Mail** | Security reports | `security@getsynthex.org` |

### 13.5 Recognition

Contributors are recognized through:
- **GitHub** — listed as contributors to repositories
- **Synthex Website** — contributors page
- **Release notes** — named in release announcements
- **Badges** — contributor badges on forum
- **Maintainer status** — elevated access and responsibility

---

## Appendix A: Quick Reference

```bash
# Daily workflow
git checkout master
git pull upstream master
git checkout -b fix/my-fix
# Make changes
git add -A
git commit -m "component: Description"
git push origin fix/my-fix
# Create PR on GitHub
```

## Appendix B: Useful Tools

| Tool | Purpose | Installation |
|------|---------|-------------|
| `rpmlint` | RPM spec validation | `sudo dnf5 install rpmlint` |
| `mock` | Isolated build chroot | `sudo dnf5 install mock` |
| `shellcheck` | Shell script linting | `sudo dnf5 install shellcheck` |
| `pre-commit` | Git hook automation | `pip install pre-commit` |
| `git` | Version control | `sudo dnf5 install git` |
| `diffoscope` | Deep file comparison | `sudo dnf5 install diffoscope` |
| `abicheck` | ABI compatibility | `sudo dnf5 install abicheck` |

## Appendix C: Issue Labels

| Label | Meaning |
|-------|---------|
| `bug` | Confirmed bug |
| `enhancement` | Feature request |
| `help-wanted` | Looking for a contributor |
| `good-first-issue` | Beginner-friendly |
| `security` | Security-related |
| `critical` | Urgent priority |
| `pending-review` | Awaiting maintainer review |
| `needs-rebase` | PR needs to be rebased |
| `documentation` | Docs-related |
| `translation` | Translation needed |
| `question` | Needs discussion/resolution |
