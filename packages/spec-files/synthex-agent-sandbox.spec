%global crate_name  synthex-agent-sandbox
%global service     synthex-agent-sandbox.service
%global dbus_conf   org.synthex.AgentSandbox.conf
%global policy_dir  %{_sysconfdir}/synthex/agent-policies

Name:           synthex-agent-sandbox
Version:        2026.10.0
Release:        1%{?dist}
Summary:        SynthOS Brain OS – AI agent isolation sandbox with capability broker

License:        MIT OR Apache-2.0
URL:            https://github.com/synthex-os/linux-synthex
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  libseccomp-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  systemd-rpm-macros

Requires:       synthex-brain = %{version}
Requires:       synthex-neural-ipc = %{version}
Requires:       libseccomp
Requires:       systemd
Requires:       dbus
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
synthex-agent-sandbox is the capability broker and process isolation layer
for SynthOS Brain OS agents.

Security model:
  - Every AI agent process is launched inside a dedicated sandbox with a
    kernel seccomp-BPF filter that blocks ptrace, process_vm_read/write,
    kexec, pivot_root, chroot, mount, BPF program loading, and all
    credential/keyring manipulation syscalls.
  - Capabilities are brokered through a TOML policy file.  Each capability
    kind (ReadFile, WriteFile, ExecuteCommand, NetworkAccess, …) requires
    either auto-grant (policy-declared) or explicit one-time user approval
    via a desktop notification.
  - always_deny entries in the policy are enforced before any approval
    prompt — the agent cannot request them at all.
  - Network access is namespaced: agents default to NetworkAccess(None)
    and must request LocalOnly or Internet through the broker.

Bundled policy profiles:
  default.toml  — balanced policy for general-purpose agents
  cline.toml    — pre-configured for Cline / Claude Code (broad file access,
                  common build tools, no unrestricted shell)

%prep
%setup -q -n synthex-repo-%{version}
%autosetup -n %{name}-%{version}

%build
cargo build --release --package %{crate_name} \
    --manifest-path src/%{crate_name}/Cargo.toml

%install
install -Dm755 target/release/%{crate_name} \
    %{buildroot}/usr/lib/synthex/%{crate_name}
install -Dm644 systemd/synthex-agent.sysusers %{buildroot}%{_sysusersdir}/synthex-agent.conf
install -Dm644 systemd/%{service} \
    %{buildroot}/usr/lib/systemd/system/%{service}
install -Dm644 dbus/%{dbus_conf} \
    %{buildroot}/usr/share/dbus-1/system.d/%{dbus_conf}

# Policy profiles
install -Dm644 configs/agent-policies/default.toml \
    %{buildroot}%{policy_dir}/default.toml
install -Dm644 configs/agent-policies/cline.toml \
    %{buildroot}%{policy_dir}/cline.toml

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
%dir %{policy_dir}
%config(noreplace) %{policy_dir}/default.toml
%config(noreplace) %{policy_dir}/cline.toml

%changelog
* Fri Jul 11 2026 Synthex Project <dev@getsynthex.org> - 2026.10.0-1
- Initial Brain OS release
