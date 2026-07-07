#!/usr/bin/env python3
"""JSON validation script for Synthex project."""
import json, glob, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
valid = 0
invalid = 0

for pattern in ["layouts/*.json", "src/**/*.json", "src/**/presets/*.json", "src/**/data/*.json"]:
    for f in glob.glob(os.path.join(ROOT, pattern), recursive=True):
        if "project-inventory" in f or "node_modules" in f:
            continue
        try:
            json.load(open(f))
            valid += 1
        except Exception as e:
            print(f"  ❌ {os.path.relpath(f, ROOT)}: {e}")
            invalid += 1

if invalid == 0:
    print(f"  ✅ All {valid} JSON files valid")
else:
    print(f"  ⚠️  {valid} valid, {invalid} invalid")
    sys.exit(1)
