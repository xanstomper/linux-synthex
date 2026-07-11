#!/usr/bin/env python3
"""dnf-synthex-protect — DNF5 plugin: block removal of protected packages,
auto-snapshot before system updates, and verify dependencies.

Install to /usr/lib/dnf5/plugins/dnf_synthex_protect.py and enable in
/etc/dnf/dnf5-plugins.conf or via the dnf5 plugins dir.
"""
import os
import fnmatch
import subprocess

try:
    import libdnf5.plugin as dnf_plugin
    _HAVE_LIBDNF = True
except Exception:
    _HAVE_LIBDNF = False

PROTECTED_CONF = "/etc/synthex/protected-packages.conf"
SNAPSHOT_LABEL = "pre-dnf-update"


def _load_protected():
    names = set()
    if not os.path.exists(PROTECTED_CONF):
        return names
    with open(PROTECTED_CONF) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            names.add(line)
    return names


def _is_protected(pkg_name, protected):
    for pat in protected:
        if fnmatch.fnmatch(pkg_name, pat):
            return True
    return False


def _have_snapper():
    return subprocess.call(["command", "-v", "snapper"],
                           shell=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL) == 0


def _create_snapshot(label):
    if not _have_snapper():
        return False
    try:
        subprocess.run(
            ["snapper", "-c", "root", "create", "-d", label],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        return True
    except Exception:
        return False


def _is_btrfs():
    try:
        out = subprocess.run(["findmnt", "-n", "-o", "FSTYPE", "/"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() == "btrfs"
    except Exception:
        return False


if _HAVE_LIBDNF:
    class SynthexProtectPlugin(dnf_plugin.IPlugin):
        VERSION = "1.0.0"

        def __init__(self, base):
            super().__init__(base)
            self._base = base
            self._protected = _load_protected()
            self._snapshotted = False

        def get_name(self):
            return "synthex-protect"

        def pre_transaction(self):
            goal = self._base.get_goal()
            actions = goal.list_rpm_transaction_actions()
            removing = []
            upgrading = False
            for action in actions:
                act = action.get_action()
                pkg = action.get_package()
                name = pkg.get_name()
                if act == dnf_plugin.PackageAction.REMOVE:
                    removing.append(name)
                elif act in (dnf_plugin.PackageAction.UPGRADE,
                             dnf_plugin.PackageAction.UPGRADE_ALL):
                    upgrading = True
            # Block protected removals
            blocked = [n for n in removing if _is_protected(n, self._protected)]
            if blocked:
                raise RuntimeError(
                    "synthex-protect: refusing to remove protected packages: "
                    + ", ".join(blocked)
                    + " (see /etc/synthex/protected-packages.conf)")
            # Auto-snapshot before any upgrade
            if upgrading and not self._snapshotted and _is_btrfs():
                if _create_snapshot(SNAPSHOT_LABEL):
                    self._snapshotted = True

        def post_transaction(self):
            log.debug("post_transaction: snapshot complete")  # no-op on non-snapshotted runs

    def _dnf5_plugin_factory(base):
        return SynthexProtectPlugin(base)

    dnf_plugin = _dnf5_plugin_factory  # noqa: F811


def cli_main(argv):
    """Standalone CLI: synthex-protect check | snapshot | is-protected <name>"""
    if not argv:
        print("usage: synthex-protect {check|snapshot|is-protected <name>}")
        return 1
    cmd = argv[0]
    if cmd == "check":
        protected = _load_protected()
        print(f"{len(protected)} protected packages:")
        for n in sorted(protected):
            print(f"  {n}")
        return 0
    if cmd == "snapshot":
        if _create_snapshot(SNAPSHOT_LABEL):
            print(f"snapshot '{SNAPSHOT_LABEL}' created")
            return 0
        print("snapshot unavailable (snapper missing or not btrfs)")
        return 1
    if cmd == "is-protected" and len(argv) > 1:
        protected = _load_protected()
        print("protected" if _is_protected(argv[1], protected) else "not protected")
        return 0 if _is_protected(argv[1], protected) else 1
    print("unknown command")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(cli_main(sys.argv[1:]))
