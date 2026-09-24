#!/usr/bin/env bash
# Scripted exhaustion experiment: one investigation, synthetic accounting, no model, no network.
# Conditions: exhaustion (budget 100), control (budget 1000, same script), zero-budget (0).
# The alert is the staff selection named "experiment" in data/selected_alerts.json,
# normalized by your own intake stage.
# Usage: scripts/run_exhaustion.sh [selection-key]
set -euo pipefail
cd "$(dirname "$0")/.."
key="${1:-$(uv run python -c 'import json; print(json.load(open("data/selected_alerts.json"))["experiment"])')}"
for condition in exhaustion:100 control:1000 zero-budget:0; do
  label="${condition%%:*}" budget="${condition##*:}"
  out=$(uv run triage investigate --select "$key" --config configs/scripted.toml --budget-tokens "$budget" --label "$label")
  run_dir=$(tail -n1 <<<"$out"); run_dir=${run_dir%%:*}   # the CLI prints "<run dir>: ..." last
  echo "== $label (budget $budget): $out"
  uv run triage summarize "$run_dir" || true   # a MISMATCH line is evidence; keep going
done
