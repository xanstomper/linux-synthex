%define _name synthex-welcome
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS Welcome App — first-run guide (Mint/Nobara/Bazzite/CachyOS parity)

License:        MIT
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils
Source0:        synthex-welcome
Source1:        synthex-welcome.desktop

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       synthex-control-center
Requires:       synthex-oobe
Requires:       firefox

%description
SynthOS Welcome App. Launches on first login after installation (and
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
install -m 0755 synthex-welcome %{buildroot}%{_bindir}/synthex-welcome
install -m 0644 synthex-welcome.desktop %{buildroot}%{_datadir}/applications/synthex-welcome.desktop

%files
%{_bindir}/synthex-welcome
%{_datadir}/applications/synthex-welcome.desktop

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-welcome package
- GTK4/libadwaita welcome app with driver, codec, gaming, bundle actions
