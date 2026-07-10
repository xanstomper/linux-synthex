#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS ujust — task runner wrapping 'just' for SynthOS-specific tasks

import sys, os, subprocess, shutil

JUSTFILE = "/usr/share/synthex/Justfile"

def main():
    if not shutil.which("just"):
        print("Error: 'just' is not installed. Install it with: dnf install just", file=sys.stderr)
        sys.exit(1)

    cmd = ["just", "--justfile", JUSTFILE] + sys.argv[1:]
    os.execvp("just", cmd)

if __name__ == "__main__":
    main()
