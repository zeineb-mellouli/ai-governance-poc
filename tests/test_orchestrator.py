import json

import jsonschema

from agents.orchestrator import run_audit, write_reports
from agents.schemas import FindingStatus
from tests.fakes import FakeOpenAIClient

NON_COMPLIANT_REPO = "sample_repos/non_compliant/FinalProject"


def test_run_audit_end_to_end_attaches_remediation_above_confidence_threshold():
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [
                {"policy_id": "SEC-3", "status": "NON_COMPLIANT", "confidence": 0.95,
                 "evidence": "hardcoded api_key and connection_string"},
            ],
        },
        remediation_by_policy_id={
            "SEC-3": {"description": "Move secrets to environment variables",
                      "fix": 'api_key = os.environ["API_KEY"]'},
        },
    )

    report = run_audit(NON_COMPLIANT_REPO, client=client)

    assert report.repo_name == "FinalProject"
    sec3 = [f for f in report.findings if f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py"]
    assert len(sec3) == 1
    assert sec3[0].status == FindingStatus.NON_COMPLIANT
    assert sec3[0].remediation is not None
    assert "API_KEY" in sec3[0].remediation.fix


def test_low_confidence_finding_is_gated_to_needs_review_without_remediation():
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [
                {"policy_id": "REPRO-6", "status": "NON_COMPLIANT", "confidence": 0.3,
                 "evidence": "no random_state set"},
            ],
        },
    )

    report = run_audit(NON_COMPLIANT_REPO, client=client)

    repro6 = [f for f in report.findings if f.policy_id == "REPRO-6" and f.file_path == "final_v2_ACTUAL.py"]
    assert len(repro6) == 1
    assert repro6[0].status == FindingStatus.NEEDS_REVIEW
    assert repro6[0].remediation is None


def test_write_reports_produces_schema_valid_json_and_readable_markdown(tmp_path):
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [
                {"policy_id": "SEC-3", "status": "NON_COMPLIANT", "confidence": 0.9, "evidence": "e"},
            ],
        },
        remediation_by_policy_id={"SEC-3": {"description": "d", "fix": "f"}},
    )
    report = run_audit(NON_COMPLIANT_REPO, client=client)

    machine_path, draft_path = write_reports(report, str(tmp_path))

    schema = json.loads(open("report_schema.json").read())
    machine_report = json.loads(machine_path.read_text())
    jsonschema.validate(instance=machine_report, schema=schema)

    draft_text = draft_path.read_text()
    assert "Non-compliant findings" in draft_text
    assert "SEC-3" in draft_text
