%define _name synthex-vpn
%define _version 1.0.0
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Synthex VPN configuration — WireGuard client template

License:        MIT
URL:            https://getsynthex.org

BuildArch:      noarch

Requires:       wireguard-tools

%description
WireGuard VPN client configuration template for Synthex.
Includes a ready-to-customise client config and helper scripts.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
mkdir -p %{buildroot}/etc/wireguard
install -m 0600 %{_sourcedir}/wireguard-client.conf \
    %{buildroot}/etc/wireguard/synthex-client.conf

%files
%config(noreplace) %attr(600,root,root) /etc/wireguard/synthex-client.conf

%changelog
* Sun Jul 06 2026 Synthex Project <info@getsynthex.org> - 1.0.0-1
- WireGuard client configuration template
