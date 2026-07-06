%define _name solus-codec-pack
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux complete multimedia codec pack — users never hunt for codecs

License:        GPL-2.0-or-later and BSD and MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils

# ─── Video encoders/decoders ──────────────────────────────────────────
Requires:       ffmpeg
Requires:       ffmpeg-libs
Requires:       x264
Requires:       x265
Requires:       libaom
Requires:       dav1d
Requires:       openh264
Requires:       libvpx
Requires:       libtheora
Requires:       libvorbis
Requires:       xvidcore

# ─── GStreamer — full plugin set (good/bad/ugly/libav) ────────────────
Requires:       gstreamer1
Requires:       gstreamer1-plugins-base
Requires:       gstreamer1-plugins-good
Requires:       gstreamer1-plugins-bad-free
Requires:       gstreamer1-plugins-bad-free-extras
Requires:       gstreamer1-plugins-ugly-free
Requires:       gstreamer1-plugin-libav

# ─── Audio codecs ─────────────────────────────────────────────────────
Requires:       flac
Requires:       opus
Requires:       opus-tools
Requires:       lame
Requires:       lame-libs
Requires:       twolame
Requires:       faac
Requires:       faad2
Requires:       libmad
Requires:       libsndfile
Requires:       soxr

# ─── DVD playback ─────────────────────────────────────────────────────
Requires:       libdvdnav
Requires:       libdvdread
Requires:       libdvdcss

# ─── Hardware acceleration ────────────────────────────────────────────
Requires:       libva
Requires:       libva-utils
Requires:       intel-vaapi-driver
Requires:       mesa-va-drivers
Requires:       mesa-vdpau-drivers
Requires:       libvdpau

# ─── Container/format support ─────────────────────────────────────────
Requires:       libmatroska
Requires:       libmp4v2
Requires:       libass
Requires:       libbluray
Requires:       libbluray-bdjava
Requires:       libmodplug

# ─── Image formats ────────────────────────────────────────────────────
Requires:       libwebp
Requires:       libjxl
Requires:       libheif
Requires:       libavif
Requires:       jasper-libs
Requires:       openjpeg2

# ─── Subtitle support ─────────────────────────────────────────────────
Requires:       libass
Requires:       enchant2

# ─── Media players ────────────────────────────────────────────────────
Requires:       vlc
Requires:       vlc-plugin-gstreamer
Requires:       mpv
Requires:       ffmpegthumbnailer

# ─── Audio production extras ──────────────────────────────────────────
Requires:       libsndfile
Requires:       libsamplerate
Requires:       taglib

%description
Solus Linux complete multimedia codec pack. Provides full out-of-the-box
support for H.264, H.265/HEVC, AV1, VP9, VP8, AAC, MP3, FLAC, Opus, DVD
playback, Blu-ray, and all major container formats. Hardware acceleration
via VAAPI, VDPAU, NVENC, NVDEC, and AMF. Users never need to hunt for
codecs — everything works immediately.

This is Nobara's codec strength + CachyOS's hardware acceleration + Bazzite's
media support, combined into one comprehensive package.

%prep
%setup -c -T

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-codec-pack package
- Complete codec suite: H.264/H.265/AV1/VP9, DVD/Blu-ray, VAAPI/NVENC
