#!/usr/bin/env bash
# Normal experiment: a live model over a small alert set, one budget per investigation.
# Uses your fresh pinned scans, your intake, and your planner.
# This makes paid (or rate-limited) model calls with your own provider key.
# Usage: scripts/run_normal.sh [config.toml]
set -euo pipefail
cd "$(dirname "$0")/.."
config="${1:-configs/live.toml}"
scans=runs/scans/radicale
[ -f "$scans/bandit.json" ] || { echo "run scripts/scan_target.sh first" >&2; exit 1; }
uv run triage intake --scans "$scans" --out runs/alerts/radicale
uv run triage run-set --scans "$scans" --config "$config" --label normal
