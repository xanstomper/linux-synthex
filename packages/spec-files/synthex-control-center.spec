Name:           synthex-control-center
Version:        1.0.0
Release:        1%{?dist}
Summary:        SynthOS unified control center GUI

License:        MIT
URL:            https://getsynthex.io

BuildRequires:  cmake
BuildRequires:  make
BuildRequires:  gcc-c++
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtdeclarative-devel
BuildRequires:  qt6-qtquickcontrols2-devel
BuildRequires:  qt6-qtsvg-devel
BuildRequires:  polkit-devel

Requires:       qt6-qtbase
Requires:       qt6-qtdeclarative
BuildRequires:  qt6-qtquickcontrols2-devel
Requires:       qt6-qtquickcontrols2
Requires:       qt6-qtsvg
Requires:       polkit

%description
Unified control panel for SynthOS.  Provides a Qt6/QML graphical interface
for managing SynthOS-specific settings:

  - Desktop profile switching (Classic / AI / Focus)
  - SynthOS feature toggles (temporal daemon, mesh networking, focus mode)
  - System update channel selection
  - Hardware quick-config (GPU, audio, peripherals)

Requires a SynthOS session (uses D-Bus interfaces provided by synthex-core
daemons).

%prep
%setup -q

%build
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install

# Fallback for non-cmake_install macro systems
# install -Dm755 %{__cmake_builddir}/synthex-control-center \
#     %{buildroot}%{_bindir}/synthex-control-center

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/synthex-control-center.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SynthOS Control Center
Comment=Configure SynthOS system settings
Exec=synthex-control-center
Icon=preferences-system
Categories=Settings;System;
Keywords=settings;control;synthex;
StartupWMClass=synthex-control-center
EOF

install -d %{buildroot}%{_datadir}/polkit-1/actions
cat > %{buildroot}%{_datadir}/polkit-1/actions/io.synthex.control-center.policy << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
    "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
    "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>SynthOS</vendor>
  <vendor_url>https://getsynthex.io</vendor_url>
  <action id="io.synthex.control-center.apply-settings">
    <description>Apply system-wide SynthOS settings</description>
    <message>Authentication is required to apply SynthOS system settings.</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
</policyconfig>
EOF

%files
%{_bindir}/synthex-control-center
%{_datadir}/applications/synthex-control-center.desktop
%{_datadir}/polkit-1/actions/io.synthex.control-center.policy

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 1.0.0-1
- Fix Release tag macro escaping (%%{?dist} → %{?dist})
- Fix install macro escaping (%%{buildroot}%%{_bindir} → %{buildroot}%{_bindir})
- Add complete BuildRequires, Requires, cmake build, .desktop, polkit policy
