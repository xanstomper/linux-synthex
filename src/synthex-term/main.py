#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Terminal — wrapper that launches the best available terminal

import sys, os, subprocess, shutil

PREFERRED = ["konsole","kitty","alacritty","foot","xterm"]

def main():
    args = sys.argv[1:]
    for term in PREFERRED:
        if shutil.which(term):
            cmd = [term] + (["--"] + args if args else [])
            os.execvp(term, cmd)
    # last resort
    subprocess.run(["xterm"] + args)

if __name__ == "__main__":
    main()
