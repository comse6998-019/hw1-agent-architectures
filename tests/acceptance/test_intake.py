from __future__ import annotations

import json
import re

import pytest
from conftest import ROOT

from triage.application import intake
from triage.infrastructure.target import load_scanners, load_selection, load_targets, select_alert

SCANNERS = load_scanners(ROOT / "data/targets.json")
SNAPSHOT = load_targets(ROOT / "data/targets.json")["radicale"].snapshot
NORMALIZERS = {"bandit": intake.normalize_bandit, "semgrep": intake.normalize_semgrep}


def raw(name: str) -> dict:
    return json.loads((ROOT / f"data/scans/radicale/{name}.json").read_text())


def normalize(name: str) -> list:
    return NORMALIZERS[name](raw(name), SNAPSHOT, SCANNERS[name])


def claim(name: str, result: dict) -> tuple[str, str, int]:
    if name == "bandit":
        return result["test_id"], result["filename"], result["line_number"]
    return result["check_id"].rsplit(".", 1)[-1], result["path"], result["start"]["line"]


@pytest.mark.parametrize("name", ["bandit", "semgrep"])
def test_every_raw_claim_becomes_one_alert(name: str) -> None:
    alerts = normalize(name)
    assert len(alerts) == len(raw(name)["results"])
    unmatched = list(alerts)
    for result in raw(name)["results"]:
        rule, path, line = claim(name, result)
        match = next(a for a in unmatched
                     if a.scanner == name and rule in a.rule_id and a.path == path and a.start_line <= line <= a.end_line)
        unmatched.remove(match)
    assert all(a.commit == SNAPSHOT.commit for a in alerts)


@pytest.mark.parametrize("name", ["bandit", "semgrep"])
def test_alert_ids_are_stable_and_unique(name: str) -> None:
    first, second = normalize(name), normalize(name)
    assert [a.alert_id for a in first] == [a.alert_id for a in second]
    assert len({a.alert_id for a in first}) == len(first)
    assert all(re.fullmatch(r"[A-Za-z0-9._-]+", a.alert_id) for a in first)  # used as a file name


@pytest.mark.parametrize("name", ["bandit", "semgrep"])
def test_alert_ids_do_not_depend_on_result_order(name: str) -> None:
    reordered = {**raw(name), "results": list(reversed(raw(name)["results"]))}
    alerts = NORMALIZERS[name](reordered, SNAPSHOT, SCANNERS[name])
    def claims(found: list) -> set:  # each id must stay with its claim, not with a position
        return {(a.alert_id, a.scanner, a.rule_id, a.path, a.start_line, a.end_line) for a in found}

    assert claims(alerts) == claims(normalize(name))


@pytest.mark.parametrize("name", ["bandit", "semgrep"])
def test_alerts_record_scanner_provenance(name: str) -> None:
    dumped = normalize(name)[0].model_dump_json()
    scanner = SCANNERS[name]
    assert scanner.version in dumped and scanner.command in dumped
    assert all(digest in dumped for digest in scanner.ruleset_sha256.values())


def test_alerts_round_trip_through_json() -> None:
    alert = normalize("bandit")[0]
    assert type(alert).model_validate_json(alert.model_dump_json()) == alert


def test_every_staff_selection_resolves_to_one_alert() -> None:
    alerts = normalize("bandit") + normalize("semgrep")
    for sel in load_selection(ROOT / "data/selected_alerts.json").alerts:
        select_alert(alerts, sel)
