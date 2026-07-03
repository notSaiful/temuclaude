#!/bin/bash
# Run all automated scouts + distiller in sequence
# This script is called by the cron job (no_agent=True, script-only)

cd /Users/saiful/timuclaude/research

echo "=== Running Scout-arXiv ==="
python3 scripts/scout_arxiv.py 2>&1

echo "=== Running Scout-GitHub ==="
python3 scripts/scout_github.py 2>&1

echo "=== Running Scout-HuggingFace ==="
python3 scripts/scout_huggingface.py 2>&1

echo "=== Running Distiller ==="
python3 scripts/distiller.py 2>&1

echo "=== ALL SCOUTS + DISTILLER COMPLETE ==="