#!/usr/bin/env bash
# Linux Synthex Project File Tree Generator
# Generates a complete ASCII tree of the project

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_FILE="${PROJECT_ROOT}/project-tree.txt"

cd "$PROJECT_ROOT" || exit 1

# Generate tree with file sizes
find . -not -path './.git/*' -not -name '.git' \
  | sort \
  | while IFS= read -r line; do
      depth=$(($(echo "$line" | tr -cd '/' | wc -c)))
      indent=""
      for ((i=0; i<depth; i++)); do
        indent="${indent}│   "
      done
      name=$(basename "$line")
      if [ -f "$line" ]; then
        size=$(stat --format=%s "$line" 2>/dev/null || echo "0")
        echo "${indent}├── ${name}  ($(numfmt --to=iec $size))"
      else
        echo "${indent}├── ${name}/"
      fi
    done > "$OUTPUT_FILE"

echo "Tree written to $OUTPUT_FILE"
wc -l "$OUTPUT_FILE"
