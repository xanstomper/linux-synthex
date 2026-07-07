###############################################################################
# synthex-security-dashboard.spec
# RPM spec file for Synthex Security Dashboard
#
# Synthex eopkg uses .spec files in packages/spec-files/
# Build with: eopkg build --ignore-safety synthex-security-dashboard.spec
#
# Package: synthex-security-dashboard
# Version: 1.0.0
# Release: 1%{?dist}
# License: GPL-3.0-or-later
# Summary: Security status dashboard for Linux Synthex
#
# Provides a GTK4/libadwaita GUI application for monitoring and managing
# the security state of a SynthOS system, including SELinux status,
# firewall state, disk encryption, TPM integrity, and update status.
#
# BuildRequires:
#   - meson >= 0.60
#   - ninja-build
#   - gobject-introspection-devel
#   - gtk4-devel >= 4.10
#   - libadwaita-devel >= 1.3
#   - python3-devel
#   - pygobject3-devel
#   - dbus-devel >= 1.12
#   - libqmi-devel (optional)
#   - desktop-file-utils
#   - appstream-glib-devel
#   - itstool
#   - glib2-devel >= 2.76
#   - libselinux-devel
#   - systemd-devel
#
# Requires (runtime):
#   - gtk4 >= 4.10
#   - libadwaita >= 1.3
#   - python3 >= 3.11
#   - pygobject3
#   - dbus >= 1.12
#   - selinux-policy-targeted
#   - policycoreutils
#   - firewalld
#   - cryptsetup
#   - tpm2-tools >= 5.0
#   - audit
#   - flatpak
#   - polkit
#   - systemd
#
###############################################################################

%global dash_version 1.0.0

Name:           synthex-security-dashboard
Version:        %{dash_version}
Release:        1%{?dist}
Summary:        Security status dashboard for Linux Synthex

Group:          System/Utilities
License:        GPL-3.0-or-later
URL:            https://github.com/synthex-project/security-dashboard
Source0:        %{name}-%{version}.tar.xz
Source1:        synthex-security-dashboard.service
Source2:        synthex-security-dashboard.timer
Source3:        org.synthex.security-dashboard.policy

BuildArch:      x86_64
BuildRequires:  meson >= 0.60.0
BuildRequires:  ninja-build
BuildRequires:  gtk4-devel >= 4.10.0
BuildRequires:  libadwaita-devel >= 1.3.0
BuildRequires:  python3-devel
BuildRequires:  pygobject3-devel
BuildRequires:  dbus-devel >= 1.12.0
BuildRequires:  desktop-file-utils
BuildRequires:  appstream-glib-devel
BuildRequires:  glib2-devel >= 2.76.0
BuildRequires:  libselinux-devel
BuildRequires:  systemd-devel
BuildRequires:  gettext
BuildRequires:  itstool

Requires:       gtk4 >= 4.10.0
Requires:       libadwaita >= 1.3.0
Requires:       python3 >= 3.11
Requires:       pygobject3
Requires:       dbus >= 1.12.0
Requires:       selinux-policy-targeted
Requires:       policycoreutils
Requires:       firewalld
Requires:       cryptsetup
Requires:       tpm2-tools >= 5.0
Requires:       audit
Requires:       flatpak
Requires:       polkit
Requires:       systemd
Requires:       fwupd

Recommends:     snapper
Recommends:     needrestart

Provides:       synthex-security-gatherer = %{version}
Obsoletes:      synthex-security-gatherer < %{version}

###############################################################################
# DESCRIPTION
###############################################################################

%description
Synthex Security Dashboard provides a unified graphical interface for
monitoring and managing the security state of your Linux Synthex system.

Features:
  - Overall security score (0-100) with per-category breakdown
  - SELinux policy status and enforcement mode
  - Firewall configuration and live event monitoring
  - Disk encryption status with LUKS key slot management
  - TPM 2.0 health and PCR measurement validation
  - Pending security updates with severity indicators
  - Application sandbox enforcement (Flatpak)
  - Browser hardening compliance checklist
  - System audit log viewer with filtering
  - CIS benchmark compliance tracking
  - Kernel hardening status (lockdown, sysctl, mitigations)
  - Vulnerability advisory feed from Synthex Security

The dashboard includes a background gatherer service that collects
security telemetry and exposes it via D-Bus for the GUI frontend
and for integration with other monitoring tools.

###############################################################################
# PREP SECTION
###############################################################################

%prep
%setup -q -n %{name}-%{version}

###############################################################################
# BUILD SECTION
###############################################################################

%build
%meson \
    -Dbuildtype=release \
    -Db_lto=true \
    -Db_pie=true \
    -Dc_args="-fstack-protector-strong -D_FORTIFY_SOURCE=3 -fcf-protection=full" \
    -Dcpp_args="-fstack-protector-strong -D_FORTIFY_SOURCE=3 -fcf-protection=full" \
    -Dpython_install_dir=%{python3_sitelib} \
    -Dsystemdunitdir=%{_unitdir} \
    -Ddbusservicedir=%{_datadir}/dbus-1/system-services \
    -Dpolkitactiondir=%{_datadir}/polkit-1/actions

%meson_build

###############################################################################
# INSTALL SECTION
###############################################################################

%install
%meson_install

# Install systemd service and timer
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/synthex-security-gatherer.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/synthex-security-gatherer.timer

# Install PolicyKit action
install -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/polkit-1/actions/org.synthex.security-dashboard.policy

# Install SELinux policy module
install -D -m 0644 selinux/synthex-security-dashboard.te \
    %{buildroot}%{_datadir}/selinux/packages/synthex-security-dashboard.te

# Create data directories
install -d %{buildroot}%{_localstatedir}/lib/synthex/security-dashboard
install -d %{buildroot}%{_localstatedir}/log/synthex
install -d %{buildroot}%{_sysconfdir}/synthex/security-dashboard

# Install default configuration
install -D -m 0644 conf/security-dashboard.conf \
    %{buildroot}%{_sysconfdir}/synthex/security-dashboard/security-dashboard.conf

# Install gathering service script
install -D -m 0755 libexec/security-gatherer.py \
    %{buildroot}%{_libexecdir}/synthex/security-gatherer.py

# Install D-Bus service file
install -D -m 0644 dbus/org.synthex.SecurityGatherer1.service \
    %{buildroot}%{_datadir}/dbus-1/system-services/org.synthex.SecurityGatherer1.service

# Install D-Bus configuration
install -D -m 0644 dbus/org.synthex.SecurityGatherer1.conf \
    %{buildroot}%{_sysconfdir}/dbus-1/system.d/org.synthex.SecurityGatherer1.conf

# Desktop file
install -D -m 0644 data/org.synthex.SecurityDashboard.desktop \
    %{buildroot}%{_datadir}/applications/org.synthex.SecurityDashboard.desktop

# AppData
install -D -m 0644 data/org.synthex.SecurityDashboard.appdata.xml \
    %{buildroot}%{_datadir}/appdata/org.synthex.SecurityDashboard.appdata.xml

# Icons
install -D -m 0644 data/icons/scalable/apps/org.synthex.SecurityDashboard.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/org.synthex.SecurityDashboard.svg

install -D -m 0644 data/icons/symbolic/apps/org.synthex.SecurityDashboard-symbolic.svg \
    %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps/org.synthex.SecurityDashboard-symbolic.svg

# Compile schemas
glib-compile-schemas %{buildroot}%{_datadir}/glib-2.0/schemas/ || :

# Compile GSettings schemas if any
if [ -f %{buildroot}%{_datadir}/glib-2.0/schemas/org.synthex.security-dashboard.gschema.xml ]; then
    glib-compile-schemas %{buildroot}%{_datadir}/glib-2.0/schemas/
fi

# SELinux policy generation
semodule_package \
    -o %{buildroot}%{_datadir}/selinux/packages/synthex-security-dashboard.pp \
    -m selinux/synthex-security-dashboard.te 2>/dev/null || :

###############################################################################
# POST-INSTALL SCRIPTS
###############################################################################

%post
# Enable and start the gatherer timer
%systemd_post synthex-security-gatherer.timer
%systemd_post synthex-security-gatherer.service

# Reload SELinux policy if SELinux is enforcing
if [ -x /usr/sbin/semodule ] && getenforce 2>/dev/null | grep -qi "enforcing"; then
    semodule -i %{_datadir}/selinux/packages/synthex-security-dashboard.pp 2>/dev/null || :
    restorecon -R /usr/bin/synthex-security-dashboard \
                   /usr/libexec/synthex/ \
                   /var/lib/synthex/ \
                   /var/log/synthex/ 2>/dev/null || :
fi

# Compile GSettings schemas
glib-compile-schemas %{_datadir}/glib-2.0/schemas/ &>/dev/null || :

# Update icon cache
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
    gtk-update-icon-cache -qf %{_datadir}/icons/hicolor &>/dev/null || :
fi

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q &>/dev/null || :
fi

###############################################################################
# POST-UNINSTALL SCRIPTS
###############################################################################

%preun
%systemd_preun synthex-security-gatherer.timer
%systemd_preun synthex-security-gatherer.service

# Remove SELinux policy on uninstall
if [ $1 -eq 0 ] && [ -x /usr/sbin/semodule ]; then
    semodule -r synthex-security-dashboard 2>/dev/null || :
fi

###############################################################################
# POST-TRANSACTION SCRIPTS
###############################################################################

%postun
%systemd_postun_with_restart synthex-security-gatherer.service

# Update icon cache
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
    gtk-update-icon-cache -qf %{_datadir}/icons/hicolor &>/dev/null || :
fi

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q &>/dev/null || :
fi

###############################################################################
# FILES SECTION
###############################################################################

%files
%defattr(-,root,root,-)

# Documentation
%doc README.md
%doc CONTRIBUTING.md
%doc AUTHORS
%license COPYING

# Binaries
%{_bindir}/synthex-security-dashboard
%{_libexecdir}/synthex/security-gatherer.py

# Configuration
%config(noreplace) %{_sysconfdir}/synthex/security-dashboard/security-dashboard.conf
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/org.synthex.SecurityGatherer1.conf

# SELinux policy
%{_datadir}/selinux/packages/synthex-security-dashboard.te
%{_datadir}/selinux/packages/synthex-security-dashboard.pp

# Systemd
%{_unitdir}/synthex-security-gatherer.service
%{_unitdir}/synthex-security-gatherer.timer

# D-Bus
%{_datadir}/dbus-1/system-services/org.synthex.SecurityGatherer1.service

# PolicyKit
%{_datadir}/polkit-1/actions/org.synthex.security-dashboard.policy

# Desktop entry
%{_datadir}/applications/org.synthex.SecurityDashboard.desktop

# AppData
%{_datadir}/appdata/org.synthex.SecurityDashboard.appdata.xml

# Icons
%{_datadir}/icons/hicolor/scalable/apps/org.synthex.SecurityDashboard.svg
%{_datadir}/icons/hicolor/symbolic/apps/org.synthex.SecurityDashboard-symbolic.svg

# GSettings schema (if any)
%{_datadir}/glib-2.0/schemas/org.synthex.security-dashboard.gschema.xml

# UI files (if installed by meson)
%{_datadir}/synthex/security-dashboard/ui/*.ui
%{_datadir}/synthex/security-dashboard/resources/*.css

# Data directories
%dir %{_localstatedir}/lib/synthex/security-dashboard
%dir %{_localstatedir}/log/synthex
%dir %{_sysconfdir}/synthex/security-dashboard

# Locales
%{_datadir}/locale/*/LC_MESSAGES/synthex-security-dashboard.mo

###############################################################################
# CHANGELOG
###############################################################################

%changelog
* Sat Jul 04 2026 Synthex Security Team <security@synthex-project.com> - 1.0.0-1
- Initial release of the Synthex Security Dashboard
- Includes GTK4/libadwaita GUI frontend
- D-Bus security gatherer service
- SELinux policy for dashboard domain
- Systemd timer for periodic data collection
- PolicyKit integration for privileged operations
- Support for: SELinux, Firewalld, LUKS, TPM2, audit, Flatpak, updates

* Tue Jun 01 2026 Synthex Security Team <security@synthex-project.com> - 0.9.0-1
- Beta release for testing

###############################################################################
# NOTES
###############################################################################
#
# To build this package:
#   sudo eopkg install -c system.devel
#   eopkg build synthex-security-dashboard.spec
#
# Or with meson directly:
#   meson setup builddir --buildtype=release -Db_lto=true
#   meson compile -C builddir
#   meson install -C builddir --destdir /tmp/install
#
# Verification after installation:
#   systemctl status synthex-security-gatherer
#   synthex-security-dashboard --version
#   semodule -l | grep synthex
#
# SELinux file contexts:
#   /usr/bin/synthex-security-dashboard:
#       system_u:object_r:synthex_security_dashboard_exec_t:s0
#   /usr/libexec/synthex/security-gatherer.py:
#       system_u:object_r:synthex_security_dashboard_exec_t:s0
#
###############################################################################
# End of spec file
