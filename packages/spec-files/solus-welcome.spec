%define _name solus-welcome
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux Welcome App — first-run guide (Mint/Nobara/Bazzite/CachyOS parity)

License:        MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils
Source0:        solus-welcome
Source1:        solus-welcome.desktop

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       solus-control-center
Requires:       solus-oobe
Requires:       firefox

%description
Solus Linux Welcome App. Launches on first login after installation (and
after OOBE completes) to guide users through:
  - Driver installation
  - Gaming setup
  - Snapshot configuration
  - System updates
  - Software center tour
  - Documentation links
  - Community resources

Inspired by Linux Mint's mintwelcome, Nobara's welcome, Bazzite's setup
guide, and CachyOS's hello app.

%prep
%setup -c -T
cp %{SOURCE0} .
cp %{SOURCE1} .

%build
# Nothing to build — Python script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -d -m 0755 %{buildroot}%{_datadir}/applications
install -m 0755 solus-welcome %{buildroot}%{_bindir}/solus-welcome
install -m 0644 solus-welcome.desktop %{buildroot}%{_datadir}/applications/solus-welcome.desktop

%files
%{_bindir}/solus-welcome
%{_datadir}/applications/solus-welcome.desktop

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-welcome package
- GTK4/libadwaita welcome app with driver, codec, gaming, bundle actions
