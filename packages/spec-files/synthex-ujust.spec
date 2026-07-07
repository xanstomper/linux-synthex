%define _name synthex-ujust
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS task runner — Bazzite's ujust ported to Synthex

License:        Apache-2.0
URL:            https://getsynthex.org
Source0:        ujust
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       dnf5
Requires:       flatpak
Requires:       gamemode
Requires:       snapper

%description
synthex-ujust is a command-line task runner that provides one-command shortcuts
for common system tasks, ported from Bazzite's "ujust" tool. Includes 27
commands for gaming setup, NVIDIA installation, codec installation, performance
tuning, bundle installation, system fixes, and more.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 ujust %{buildroot}%{_bindir}/ujust

# Bash completions
install -d -m 0755 %{buildroot}%{_datadir}/bash-completion/completions
cat > %{buildroot}%{_datadir}/bash-completion/completions/ujust << 'EOF'
_ujust() {
    local commands="gaming-setup install-nvidia install-codecs update install-flatpak
        setup-snapshots rollback setup-zram enable-game-mode enable-balanced
        enable-powersave install-bundle-gaming install-bundle-creator
        install-bundle-developer install-bundle-rgb install-bundle-emulation
        fix-audio fix-controllers fix-bluetooth fix-display clean-system
        show-hardware create-rescue-usb tune-performance setup-fish
        install-steam-gaming-mode help"
    COMPREPLY=( $(compgen -W "$commands" -- "${COMP_WORDS[1]}") )
}
complete -F _ujust ujust
EOF

%files
%{_bindir}/ujust
%{_datadir}/bash-completion/completions/ujust

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-ujust package
- 27 task commands for gaming, system, performance, bundles, fixes
