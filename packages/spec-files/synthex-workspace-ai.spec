%global crate_name  synthex-workspace-ai
%global service     synthex-workspace-ai.service
%global dbus_conf   org.synthex.WorkspaceAI.conf

Name:           synthex-workspace-ai
Version:        2026.10.0
Release:        1%{?dist}
Summary:        SynthOS Brain OS – multi-workspace AI consciousness daemon

License:        MIT OR Apache-2.0
URL:            https://github.com/synthex-os/linux-synthex
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  systemd-rpm-macros

Requires:       synthex-brain = %{version}
Requires:       synthex-neural-ipc = %{version}
Requires:       systemd
Requires:       dbus
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
synthex-workspace-ai is the multi-workspace agent consciousness daemon for
SynthOS Brain OS.  It maps each KDE virtual desktop to an isolated AI context
so separate agents can work concurrently across workspaces without polluting
each other's state.

Key capabilities:
  - Per-workspace AI context (task, role, open files, active agents)
  - KWin D-Bus bridge: programmatic desktop switching, window placement,
    and visual effect triggers from agent code
  - Multi-agent coordinator: delegates sub-tasks to workspace-local agents
    and collects results
  - Session snapshot/restore: workspace AI state survives reboots
  - Syncs context summaries to synthex-brain every 60 s

%prep
%setup -q -n synthex-repo-%{version}

%build
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-workspace-ai target/release/synthex-workspace-ai
cp -f target/release/synthex-workspace-ai target/release/%{crate_name} 2>/dev/null || true
cp -f target/release/synthex-workspace-ai target/release/synthex-compat 2>/dev/null || true
%install
install -Dm755 target/release/%{crate_name} \
    %{buildroot}/usr/lib/synthex/%{crate_name}
install -Dm644 systemd/%{service} \
    %{buildroot}/usr/lib/systemd/system/%{service}
install -Dm644 dbus/%{dbus_conf} \
    %{buildroot}/usr/share/dbus-1/system.d/%{dbus_conf}

%post
%systemd_post %{service}

%preun
%systemd_preun %{service}

%postun
%systemd_postun_with_restart %{service}

%files
%license LICENSE
%doc README.md
/usr/lib/synthex/%{crate_name}
/usr/lib/systemd/system/%{service}
/usr/share/dbus-1/system.d/%{dbus_conf}

%changelog
* Fri Jul 11 2026 Synthex Project <dev@getsynthex.org> - 2026.10.0-1
- Initial Brain OS release
