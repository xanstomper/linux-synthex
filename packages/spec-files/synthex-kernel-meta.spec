Name:           synthex-kernel-meta
Version:        2026.10
Release:        1%%{?dist}
Summary:        Synthex kernel meta-package

License:        GPLv2
URL:            https://getsynthex.io

Requires:       kernel, kernel-core, kernel-modules
Suggests:       kernel-zen, kernel-rt

%%description
Synthex kernel meta-package with BORE scheduler support.

%%files
%%dir /etc/synthex

%%post
cat > /etc/sysctl.d/99-synthex-kernel.conf << 'EOF'
kernel.sched_latency_ns = 6000000
vm.swappiness = 10
vm.vfs_cache_pressure = 50
EOF

%%changelog
* Mon Jul 06 2026 - Initial
