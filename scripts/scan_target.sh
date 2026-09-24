#!/usr/bin/env bash
# Run the pinned scanners over a fetched target. Static analysis only: the
# target's code is never installed or executed.
# Usage: scripts/scan_target.sh [target-name]   (default: radicale)
# Output: runs/scans/<target>/{bandit,semgrep}.json
set -euo pipefail
cd "$(dirname "$0")/.."
name="${1:-radicale}"
repo="targets/$name"
out="$PWD/runs/scans/$name"
# Relative ruleset paths keep Semgrep rule ids machine-independent (runs.scans.rules.*).
rules="$PWD/runs/scans/rules"
demos_sha=e06d58f25de3dd8485050edc4fa859c664deea3e

[ -d "$repo" ] || { echo "missing $repo; run: uv run triage fetch-target --name $name" >&2; exit 1; }
uv run triage fetch-target --name "$name" >/dev/null   # re-verifies the pinned commit and a clean tree
mkdir -p "$out" "$rules"

IFS=$'\t' read -r scan_paths exclude < <(uv run python - "$name" <<'PY'
import json, sys
t = {t["name"]: t for t in json.load(open("data/targets.json"))["targets"]}[sys.argv[1]]
print(" ".join(t["scan_paths"]) + "\t" + (",".join(t["exclude"]) or "-"))
PY
)

for f in python.yml owasp-top-ten.yml; do
  [ -f "$rules/$f" ] || curl -fsSL -o "$rules/$f" "https://raw.githubusercontent.com/comse6998-019/demos/$demos_sha/intake/rules/$f"
  want=$(uv run python -c "import json; print(json.load(open('data/targets.json'))['scanners']['semgrep']['ruleset_sha256']['$f'])")
  got=$(shasum -a 256 "$rules/$f" | cut -d' ' -f1)
  [ "$want" = "$got" ] || { echo "ruleset $f sha256 mismatch: $got" >&2; exit 1; }
done

bandit_x=(); semgrep_x=()
if [ "$exclude" != "-" ]; then
  bandit_x=(-x "$exclude")
  IFS=, read -ra ex <<< "$exclude"; for e in "${ex[@]}"; do semgrep_x+=(--exclude "$e"); done
fi

# Bandit exits 1 when it reports issues; that is expected. Old output is removed
# first so a scanner that fails without writing cannot leave a stale file behind.
# ${a[@]+"${a[@]}"} keeps an empty array safe under set -u in macOS bash 3.2.
rm -f "$out/bandit.json" "$out/semgrep.json"
(cd "$repo" && uv run --project "$OLDPWD" --group scan bandit -q -r $scan_paths ${bandit_x[@]+"${bandit_x[@]}"} -f json -o "$out/bandit.json") || [ $? -eq 1 ]
(cd "$repo" && uv run --project "$OLDPWD" --group scan semgrep scan -q --metrics=off --disable-version-check \
   --config ../../runs/scans/rules/python.yml --config ../../runs/scans/rules/owasp-top-ten.yml ${semgrep_x[@]+"${semgrep_x[@]}"} --json -o "$out/semgrep.json" $scan_paths)

uv run python - "$out" <<'PY'
import collections, json, sys
out = sys.argv[1]
b = json.load(open(f"{out}/bandit.json")); s = json.load(open(f"{out}/semgrep.json"))
print(f"bandit : {len(b['results'])} results, {len(b['errors'])} errors, by rule {dict(collections.Counter(r['test_id'] for r in b['results']).most_common())}")
print(f"semgrep: {len(s['results'])} results, {len(s['errors'])} errors, version {s.get('version')}")
if b["errors"] or s["errors"]:
    sys.exit("scanner reported parse errors; check the Python version (3.12+ required)")
ref = out.replace("runs/scans", "data/scans")
for name, volatile in (("bandit", "generated_at"), ("semgrep", "time")):
    try:
        mine, theirs = json.load(open(f"{out}/{name}.json")), json.load(open(f"{ref}/{name}.json"))
    except FileNotFoundError:
        continue
    mine.pop(volatile, None); theirs.pop(volatile, None)
    print(f"{name}: {'matches' if mine == theirs else 'DIFFERS FROM'} the reference scan in data/scans")
PY
