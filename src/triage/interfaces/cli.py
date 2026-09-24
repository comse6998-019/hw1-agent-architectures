from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from triage import StudentTODO
from triage.application import agent, intake, pipeline
from triage.application.config import RunConfig
from triage.domain.alert import Alert
from triage.domain.model import InvestigationResult
from triage.infrastructure.eventlog import TraceWriter
from triage.infrastructure.providers import RecordingProvider, make_provider
from triage.infrastructure.rundir import new_run_dir, summarize
from triage.infrastructure.settings import load_config, load_dotenv
from triage.infrastructure.target import (
    TargetError,
    check_location,
    fetch_target,
    load_scanners,
    load_selection,
    load_targets,
    raw_matches,
    select_alert,
)

MANIFEST = Path("data/targets.json")
SELECTION = Path("data/selected_alerts.json")
SCANS = Path("data/scans/radicale")


def _code_commit() -> str | None:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return head + ("-dirty" if dirty.strip() else "")


def run_one(alert: Alert, repo: Path, config: RunConfig, run_dir: Path) -> InvestigationResult:
    """One investigation with its own trace, boundary log, and metadata."""
    run_id = uuid.uuid4().hex[:12]
    run_dir.mkdir(parents=True, exist_ok=False)
    meta = {
        "run_id": run_id,
        "alert_id": alert.alert_id,
        "commit": alert.commit,
        "measurement": "synthetic (scripted provider)" if config.provider == "scripted" else "live model",
        "code_commit": _code_commit(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    (run_dir / "config.json").write_text(config.model_dump_json(indent=2))
    (run_dir / "alert.json").write_text(alert.model_dump_json(indent=2))
    provider = RecordingProvider(make_provider(config), run_dir / "boundary.jsonl")
    trace = TraceWriter(run_dir / "trace.jsonl", run_id)
    result = agent.investigate(alert, repo, config, provider, trace)
    (run_dir / "result.json").write_text(result.model_dump_json(indent=2))
    return result


def _alerts_from_scans(scans: Path, target: str) -> list[Alert]:
    """Run your intake stage over the raw scanner JSON in a directory."""
    snapshot = load_targets(MANIFEST)[target].snapshot
    scanners = load_scanners(MANIFEST)
    alerts: list[Alert] = []
    for name, normalize in (("bandit", intake.normalize_bandit), ("semgrep", intake.normalize_semgrep)):
        raw_path = scans / f"{name}.json"
        if raw_path.exists():
            alerts += normalize(json.loads(raw_path.read_text()), snapshot, scanners[name])
    return alerts


def _config(args: argparse.Namespace) -> RunConfig:
    load_dotenv()
    return load_config(args.config, budget_tokens=args.budget_tokens, output_allowance=args.output_allowance)


def cmd_fetch_target(args: argparse.Namespace) -> None:
    spec = load_targets(args.manifest)[args.name]
    snapshot = fetch_target(spec, args.dest or Path("targets") / spec.name)
    print(f"ok: {snapshot.snapshot_id} ({spec.ref}, {spec.license})")


def cmd_validate_fixtures(args: argparse.Namespace) -> None:
    """Each staff selection names exactly one raw scanner result, at lines that exist at the pinned commit."""
    selection = load_selection(SELECTION)
    commit = load_targets(MANIFEST)[selection.target].commit
    for sel in selection.alerts:
        found = raw_matches(json.loads((args.scans / f"{sel.scanner}.json").read_text()), sel)
        if len(found) != 1:
            sys.exit(f"{sel.key}: {len(found)} raw results match; expected 1")
        digest = check_location(args.repo, commit, sel.path, sel.line, sel.line)
        print(f"ok: {sel.key} -> {sel.path}:{sel.line} sha256={digest[:12]}")


def cmd_intake(args: argparse.Namespace) -> None:
    alerts = _alerts_from_scans(args.scans, args.target)
    args.out.mkdir(parents=True, exist_ok=True)
    for alert in alerts:
        (args.out / f"{alert.alert_id}.json").write_text(alert.model_dump_json(indent=2))
    print(f"wrote {len(alerts)} alerts to {args.out}")


def cmd_investigate(args: argparse.Namespace) -> None:
    config = _config(args)
    alerts = _alerts_from_scans(args.scans, args.target)
    if args.alert_id:
        alert = next((a for a in alerts if a.alert_id == args.alert_id), None)
        if alert is None:
            sys.exit(f"no alert with id {args.alert_id!r}; `triage intake --out <dir>` lists them")
    else:
        alert = select_alert(alerts, load_selection(SELECTION).get(args.select))
    run_dir = new_run_dir(config, args.label)
    result = run_one(alert, args.repo, config, run_dir)
    print(f"{run_dir}: {result.terminal_reason} verdict={result.finding.verdict if result.finding else None}")


def cmd_run_set(args: argparse.Namespace) -> None:
    config = _config(args)
    selected = pipeline.plan(_alerts_from_scans(args.scans, args.target), config)
    set_dir = new_run_dir(config, args.label)
    results = [run_one(a, args.repo, config, set_dir / f"{i:02d}-{a.alert_id}") for i, a in enumerate(selected)]
    pipeline.write_report(results, selected, set_dir / "report.md")
    print(f"{set_dir}: {len(results)} investigations, report at {set_dir / 'report.md'}")


def cmd_summarize(args: argparse.Namespace) -> None:
    """Reconcile a run's trace against the independent boundary log."""
    s = summarize(args.run_dir)
    print(f"measurement:            {s.measurement}")
    print(f"model calls requested:  {s.kinds['ModelCallRequested']}")
    print(f"admitted / rejected:    {s.kinds['ModelCallAdmitted']} / {s.kinds['ModelCallRejected']}")
    print(f"issued (boundary log):  {s.issued} (raised: {s.raised})")
    print(f"tokens reported:        {s.tokens_reported} (calls without usage: {s.calls_without_usage})")
    print(f"tools:                  {dict(s.tools)}")
    print(f"terminal:               {s.terminal_reasons[-1] if s.terminal_reasons else 'MISSING'}")
    if not s.reconciles:
        print("MISMATCH: admitted calls, issued calls, and terminal events do not reconcile")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="triage", description="HW1 bounded security-alert triage.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("fetch-target", help="Fetch the pinned target commit and verify it.")
    s.add_argument("--name", default="radicale")
    s.add_argument("--manifest", type=Path, default=MANIFEST)
    s.add_argument("--dest", type=Path)
    s.set_defaults(func=cmd_fetch_target)

    s = sub.add_parser("validate-fixtures", help="Check the staff alert selections against the scans and the checkout.")
    s.add_argument("--scans", type=Path, default=SCANS)
    s.add_argument("--repo", type=Path, default=Path("targets/radicale"))
    s.set_defaults(func=cmd_validate_fixtures)

    def scan_args(s: argparse.ArgumentParser) -> None:
        s.add_argument("--scans", type=Path, default=SCANS, help="Directory with bandit.json and semgrep.json.")
        s.add_argument("--target", default="radicale")

    s = sub.add_parser("intake", help="Normalize raw scanner JSON with your intake stage and write the alerts.")
    scan_args(s)
    s.add_argument("--out", type=Path, required=True)
    s.set_defaults(func=cmd_intake)

    for name, func, helptext in (
        ("investigate", cmd_investigate, "Investigate one alert (one run, one budget)."),
        ("run-set", cmd_run_set, "Plan, investigate a small alert set sequentially, and write the report."),
    ):
        s = sub.add_parser(name, help=helptext)
        scan_args(s)
        if name == "investigate":
            which = s.add_mutually_exclusive_group(required=True)
            which.add_argument("--select", help="Key from data/selected_alerts.json.")
            which.add_argument("--alert-id", help="An alert_id from your intake contract.")
        s.add_argument("--repo", type=Path, default=Path("targets/radicale"))
        s.add_argument("--config", type=Path, required=True)
        s.add_argument("--budget-tokens", type=int, help="Override [budget].tokens.")
        s.add_argument("--output-allowance", type=int, help="Override [budget].output_allowance.")
        s.add_argument("--label", default="run")
        s.set_defaults(func=func)

    s = sub.add_parser("summarize", help="Reconcile a run's trace with its boundary log.")
    s.add_argument("run_dir", type=Path)
    s.set_defaults(func=cmd_summarize)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except StudentTODO as todo:
        sys.exit(f"not implemented yet (student TODO): {todo}")
    except TargetError as e:
        sys.exit(f"error: {e}")
