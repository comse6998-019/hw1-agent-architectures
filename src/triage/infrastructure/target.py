from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, Field

from triage.domain.model import SHA1_PATTERN, AlertView, RepoSnapshot, ScannerProvenance


class TargetError(RuntimeError):
    """The checkout, a location, or a selection does not match the pinned snapshot."""


class TargetSpec(BaseModel):
    name: str
    role: str
    url: str
    commit: str = Field(pattern=SHA1_PATTERN)
    ref: str
    license: str
    scan_paths: list[str]
    exclude: list[str] = Field(default_factory=list)

    @property
    def snapshot(self) -> RepoSnapshot:
        return RepoSnapshot(name=self.name, url=self.url, commit=self.commit)


def load_targets(manifest: Path) -> dict[str, TargetSpec]:
    return {t["name"]: TargetSpec(**t) for t in json.loads(manifest.read_text())["targets"]}


def load_scanners(manifest: Path) -> dict[str, ScannerProvenance]:
    return {name: ScannerProvenance(**s) for name, s in json.loads(manifest.read_text())["scanners"].items()}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def fetch_target(spec: TargetSpec, dest: Path) -> RepoSnapshot:
    """Fetch exactly the pinned commit into dest (no history, no hooks, no build)."""
    if not dest.exists():
        dest.mkdir(parents=True)
        _git(dest, "init", "--quiet")
        _git(dest, "remote", "add", "origin", spec.url)
        _git(dest, "fetch", "--quiet", "--depth", "1", "origin", spec.commit)
        _git(dest, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    return verify_checkout(spec, dest)


def verify_checkout(spec: TargetSpec, root: Path) -> RepoSnapshot:
    head = _git(root, "rev-parse", "HEAD").strip()
    if head != spec.commit:
        raise TargetError(f"{root} is at {head}, manifest pins {spec.commit}")
    if dirty := _git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise TargetError(f"{root} has local modifications:\n{dirty}")
    return spec.snapshot


def check_location(root: Path, commit: str, path: str, start_line: int, end_line: int) -> str:
    """Check that lines exist in a file at a commit; return the sha256 of those lines.

    Staff check behind `triage validate-fixtures`. Not for student code: evidence
    resolution must be your own, and this check does not detect committed symlinks.
    """
    rel = PurePosixPath(path)
    if rel.is_absolute() or ".." in rel.parts:
        raise TargetError(f"path must be relative and inside the repo: {path}")
    try:
        lines = _git(root, "show", f"{commit}:{rel}").splitlines()
    except subprocess.CalledProcessError as e:
        raise TargetError(f"{path} does not exist at {commit[:12]}") from e
    if not 1 <= start_line <= end_line <= len(lines):
        raise TargetError(f"{path} has {len(lines)} lines; location cites {start_line}-{end_line}")
    return hashlib.sha256("\n".join(lines[start_line - 1 : end_line]).encode()).hexdigest()


# --- staff alert selections -----------------------------------------------------


class Selector(BaseModel):
    """One scanner result, named in the scanner's own terms. Selection is not a verdict."""

    key: str
    scanner: Literal["bandit", "semgrep"]
    rule_id: str
    path: str
    line: int = Field(ge=1)


class Selection(BaseModel):
    target: str
    note: str
    experiment: str  # key of the alert used by the scripted exhaustion experiment
    alerts: list[Selector]

    def get(self, key: str) -> Selector:
        found = next((s for s in self.alerts if s.key == key), None)
        if found is None:
            raise TargetError(f"no selection {key!r}; known: {', '.join(s.key for s in self.alerts)}")
        return found


def load_selection(path: Path) -> Selection:
    return Selection.model_validate_json(path.read_text())


def raw_matches(raw: dict[str, Any], sel: Selector) -> list[dict[str, Any]]:
    """Results in raw Bandit or Semgrep JSON that the selector names."""
    if sel.scanner == "bandit":
        return [r for r in raw["results"]
                if (r["test_id"], r["filename"], r["line_number"]) == (sel.rule_id, sel.path, sel.line)]
    return [r for r in raw["results"]
            if r["check_id"].endswith(sel.rule_id) and (r["path"], r["start"]["line"]) == (sel.path, sel.line)]


def select_alert(alerts: Sequence[AlertView], sel: Selector) -> AlertView:
    """Find the one alert in a student contract that corresponds to a selector."""
    rule = sel.rule_id.rsplit(".", 1)[-1]
    matches = [a for a in alerts
               if a.scanner == sel.scanner and rule in a.rule_id and a.path == sel.path
               and a.start_line <= sel.line <= a.end_line]
    if len(matches) != 1:
        raise TargetError(f"selector {sel.key!r} matched {len(matches)} alerts; expected exactly 1")
    return matches[0]
