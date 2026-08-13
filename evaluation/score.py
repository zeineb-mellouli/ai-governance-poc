"""Score generated compliance reports against the hand-authored ground truth.

Reads reports/<repo>/machine_report.json against evaluation/expected/<repo>.yaml
and reports precision/recall per policy. 

Buckets in the expectation files:
  expect_violations -- must fire. Not firing is a false negative.
  expect_clean      -- must not fire. Firing is a false positive.
  tolerate          -- either verdict defensible; excluded from scoring.

A finding that fires but appears in no bucket is reported as UNLABELLED, never
as a false positive.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agents.schemas import FindingStatus

EXPECTED_DIR = Path(__file__).parent / "expected"

# NEEDS_REVIEW counts as "fired" for recall, the audit did surface it but is
# tracked separately
FIRED_STATUSES = {FindingStatus.NON_COMPLIANT.value, FindingStatus.NEEDS_REVIEW.value}


@dataclass
class PolicyScore:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    needs_review: int = 0
    unlabelled: int = 0
    tolerated: int = 0

    @property
    def precision(self) -> float | None:
        denom = self.tp + self.fp
        return self.tp / denom if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.tp + self.fn
        return self.tp / denom if denom else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p and r else None


@dataclass
class RepoResult:
    repo: str
    by_policy: dict[str, PolicyScore] = field(default_factory=dict)
    false_negatives: list[tuple[str, str, str]] = field(default_factory=list)
    false_positives: list[tuple[str, str, str]] = field(default_factory=list)
    unlabelled: list[tuple[str, str, str]] = field(default_factory=list)

    def score(self, policy: str) -> PolicyScore:
        return self.by_policy.setdefault(policy, PolicyScore())


def _key(policy: str, file_path: str | None) -> tuple[str, str]:
    """Match on (policy_id, file_path); repo-level checks use '' for the path."""
    return policy, (file_path or "")


def _load_labels(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _label_keys(labels: dict, bucket: str) -> dict[tuple[str, str], str]:
    """Collapse a bucket to {(policy, file): note}.

    Two entries can share a key when one file carries two concerns under one
    policy. A finding matches only once, so the keys merge -- but the notes are
    joined rather than overwritten, so the second concern is not lost.
    """
    out: dict[tuple[str, str], str] = {}
    for entry in labels.get(bucket) or []:
        key = _key(entry["policy"], entry.get("file"))
        note = entry.get("note", "")
        out[key] = f"{out[key]}; {note}" if key in out else note
    return out


def score_repo(report_path: Path, expected_path: Path) -> RepoResult:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    labels = _load_labels(expected_path)
    result = RepoResult(repo=report["repo_name"])

    expect_violations = _label_keys(labels, "expect_violations")
    expect_clean = _label_keys(labels, "expect_clean")
    tolerate = _label_keys(labels, "tolerate")

    fired: dict[tuple[str, str], str] = {}
    for finding in report["findings"]:
        if finding["status"] in FIRED_STATUSES:
            fired[_key(finding["policy_id"], finding.get("file_path"))] = finding["status"]

    for key, note in expect_violations.items():
        policy, file_path = key
        if key in fired:
            result.score(policy).tp += 1
            if fired[key] == FindingStatus.NEEDS_REVIEW.value:
                result.score(policy).needs_review += 1
        else:
            result.score(policy).fn += 1
            result.false_negatives.append((policy, file_path, note))

    for key, note in expect_clean.items():
        policy, file_path = key
        if key in fired:
            result.score(policy).fp += 1
            result.false_positives.append((policy, file_path, note))

    for policy, _ in tolerate:
        result.score(policy).tolerated += 1

    labelled = set(expect_violations) | set(expect_clean) | set(tolerate)
    for key in fired:
        if key not in labelled:
            policy, file_path = key
            result.score(policy).unlabelled += 1
            result.unlabelled.append((policy, file_path, ""))

    return result


def score_all(reports_dir: Path) -> list[RepoResult]:
    results = []
    for expected_path in sorted(EXPECTED_DIR.glob("*.yaml")):
        report_path = reports_dir / expected_path.stem / "machine_report.json"
        if not report_path.exists():
            continue
        results.append(score_repo(report_path, expected_path))
    return results


def aggregate(results: list[RepoResult]) -> dict[str, PolicyScore]:
    totals: dict[str, PolicyScore] = {}
    for result in results:
        for policy, score in result.by_policy.items():
            agg = totals.setdefault(policy, PolicyScore())
            agg.tp += score.tp
            agg.fp += score.fp
            agg.fn += score.fn
            agg.needs_review += score.needs_review
            agg.unlabelled += score.unlabelled
            agg.tolerated += score.tolerated
    return totals


def missing_reports(reports_dir: Path) -> list[str]:
    """Labelled repos with no report, these are silently excluded from scoring."""
    return [
        p.stem
        for p in sorted(EXPECTED_DIR.glob("*.yaml"))
        if not (reports_dir / p.stem / "machine_report.json").exists()
    ]
