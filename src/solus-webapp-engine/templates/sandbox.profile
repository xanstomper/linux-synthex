# Solus Web App Sandbox Profile
# Bubblewrap (bwrap) sandbox configuration

# Network access (required for web apps)
share-net

# Filesystem access
ro-bind /usr/lib /usr/lib
ro-bind /usr/lib64 /usr/lib64
ro-bind /etc/fonts /etc/fonts
ro-bind /usr/share/fonts /usr/share/fonts
ro-bind /usr/share/icons /usr/share/icons
ro-bind /etc/alternatives /etc/alternatives
ro-bind /etc/resolv.conf /etc/resolv.conf
ro-bind /etc/hosts /etc/hosts
ro-bind /etc/nsswitch.conf /etc/nsswitch.conf

# GPU acceleration
ro-bind /dev/dri /dev/dri
ro-bind /dev/shm /dev/shm

# Temporary writable dirs
tmpfs /home/user/.cache
tmpfs /home/user/.local/share/webapps/{{APP_ID}}

# Wayland display
ro-bind /run/user/$(id -u)/wayland-0 /run/user/$(id -u)/wayland-0

# PulseAudio
ro-bind /run/user/$(id -u)/pulse /run/user/$(id -u)/pulse

# No root access
unshare-all
hostname solus-webapp

# Seccomp filter
seccomp 10

# Process limits
proc /proc
die-with-parent
