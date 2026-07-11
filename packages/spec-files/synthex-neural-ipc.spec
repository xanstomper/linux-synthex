%global crate_name  synthex-neural-ipc
%global service     synthex-neural-ipc.service

Name:           synthex-neural-ipc
Version:        2026.10.0
Release:        1%{?dist}
Summary:        SynthOS Brain OS – ultra-fast dual-layer AI agent message bus

License:        MIT OR Apache-2.0
URL:            https://github.com/synthex-os/linux-synthex
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  rust-toolchain
BuildRequires:  cargo
BuildRequires:  pkgconfig(openssl)
BuildRequires:  systemd-rpm-macros

# Must start before all other Brain OS components
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
synthex-neural-ipc is the dual-layer inter-process message bus for SynthOS
Brain OS agents.

Layer 1 — /dev/shm/synthex-neural-bus (mmap ring-buffer):
  Sub-microsecond latency for trusted agents sharing the same uid/pid
  namespace.  Uses a lock-free SPSC ring with cache-line padding.

Layer 2 — Unix-domain sockets under /run/synthex/neural/:
  HMAC-SHA256-verified framed messages for sandboxed agents.  Each agent
  gets its own socket; the broker relays between layers and enforces TTL
  and replay-attack prevention.

The daemon generates a fresh HMAC key at first boot and stores it at
/etc/synthex/neural-ipc.key (mode 0600, owned root:synthex-brain).

%prep
%autosetup -n %{name}-%{version}

%build
cargo build --release --package %{crate_name} \
    --manifest-path src/%{crate_name}/Cargo.toml

%install
install -Dm755 target/release/%{crate_name} \
    %{buildroot}/usr/lib/synthex/%{crate_name}
install -Dm644 systemd/%{service} \
    %{buildroot}/usr/lib/systemd/system/%{service}
# Key generation script (runs once at first boot via tmpfiles)
install -Dm755 src/%{crate_name}/scripts/gen-ipc-key.sh \
    %{buildroot}/usr/lib/synthex/gen-neural-ipc-key.sh
install -Dm644 src/%{crate_name}/scripts/synthex-neural-ipc.conf \
    %{buildroot}/usr/lib/tmpfiles.d/synthex-neural-ipc.conf

%post
%systemd_post %{service}
# Generate HMAC key on first install if it doesn't exist
if [ ! -f /etc/synthex/neural-ipc.key ]; then
    mkdir -p /etc/synthex
    /usr/lib/synthex/gen-neural-ipc-key.sh
fi

%preun
%systemd_preun %{service}

%postun
%systemd_postun_with_restart %{service}

%files
%license LICENSE
%doc README.md
/usr/lib/synthex/%{crate_name}
/usr/lib/synthex/gen-neural-ipc-key.sh
/usr/lib/systemd/system/%{service}
/usr/lib/tmpfiles.d/synthex-neural-ipc.conf

%changelog
* Fri Jul 11 2026 Synthex Project <dev@getsynthex.org> - 2026.10.0-1
- Initial Brain OS release
