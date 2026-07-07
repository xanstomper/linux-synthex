%global _name synthex-meta-developer
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS developer desktop meta-package

License:        MIT
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils

# Languages
Requires:       rust
Requires:       cargo
Requires:       golang
Requires:       nodejs
Requires:       nodejs-npm
Requires:       java-21-openjdk
Requires:       python3-devel
Requires:       python3-pip

# Containers
Requires:       podman
Requires:       buildah
Requires:       skopeo
Requires:       docker-ce
Requires:       docker-ce-cli
Requires:       containerd.io
Requires:       distrobox
Requires:       toolbox

# Virtualization
Requires:       qemu
Requires:       qemu-kvm
Requires:       libvirt
Requires:       virt-manager

# VCS
Requires:       git
Requires:       git-lfs

# Editors
Requires:       code

# Build tools
Requires:       cmake
Requires:       ninja-build
Requires:       gcc
Requires:       gcc-c++
Requires:       make

# Databases
Requires:       sqlite
Requires:       mariadb
Requires:       postgresql

%description
Synthex Developer meta-package. Complete development environment:
Rust, Go, Node.js, Java, Python, Docker, Podman, QEMU/KVM,
VS Code, Git, build tools, and databases.

%prep
%setup -c -T

%build
echo "Synthex Developer Platform" > build.log

%install
mkdir -p %{buildroot}%{_datadir}/synthex/
echo "%{_name}-%{_version}-%{_release}" > %{buildroot}%{_datadir}/synthex/meta-developer-version

%files
%{_datadir}/synthex/meta-developer-version

%changelog
* Tue Jul 2026 Synthex Project
- Initial developer meta-package
