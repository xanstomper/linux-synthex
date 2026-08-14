%define _name synthex-vpn
%define _version 1.0.0
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Synthex VPN configuration — WireGuard client template

License:        MIT
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildArch:      noarch

Requires:       wireguard-tools

%description
WireGuard VPN client configuration template for Synthex.
Includes a ready-to-customise client config and helper scripts.

%prep
%setup -q -n synthex-repo-%{version}

%build
# Nothing to compile — noarch data/script package

%install
mkdir -p %{buildroot}/etc/wireguard
install -m 0600 configs/vpn/wireguard-client.conf \
    %{buildroot}/etc/wireguard/synthex-client.conf
install -Dm0755 configs/vpn/synthex-vpn-helper %{buildroot}%{_bindir}/synthex-vpn

%files
%config(noreplace) %attr(600,root,root) /etc/wireguard/synthex-client.conf
%{_bindir}/synthex-vpn

%changelog
* Sun Jul 06 2026 Synthex Project <info@getsynthex.org> - 1.0.0-1
- WireGuard client configuration template
