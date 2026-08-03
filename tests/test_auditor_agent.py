from agents import auditor_agent
from agents.repository_agent import scan
from agents.schemas import FindingStatus
from tests.fakes import FakeOpenAIClient

NON_COMPLIANT_REPO = "sample_repos/non_compliant/FinalProject"
HOLISTIC_ONLY_REPO = "sample_repos/holistic/fin-code-fx_exposure_report"


def test_repo_level_checks_flag_bad_repo_name_and_missing_readme():
    snapshot = scan(NON_COMPLIANT_REPO)
    findings = auditor_agent._evaluate_repo_level(snapshot)
    by_policy = {f.policy_id: f for f in findings}

    assert by_policy["REPO-9"].status == FindingStatus.NON_COMPLIANT
    assert by_policy["NAM-5"].status == FindingStatus.NON_COMPLIANT


def test_audit_records_llm_verdict_for_matching_file():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(verdicts_by_path_substring={
        "final_v2_ACTUAL.py": [
            {"policy_id": "SEC-3", "status": "NON_COMPLIANT", "confidence": 0.95,
             "evidence": "hardcoded api_key and connection_string"},
        ],
    })

    findings, errors = auditor_agent.audit(snapshot, client=client)

    sec3 = [f for f in findings if f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py"]
    assert len(sec3) == 1
    assert sec3[0].status == FindingStatus.NON_COMPLIANT
    assert sec3[0].confidence_score == 0.95
    assert sec3[0].retrieval_chunk_id == "SEC-3"
    assert not errors


def test_holistic_finding_kept_when_no_per_file_check_caught_it():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        holistic_verdicts=[
            {"policy_id": "ARCH-12", "status": "NON_COMPLIANT", "confidence": 0.8,
             "evidence": "no silver-layer file exists anywhere in this repository"},
        ],
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12"]
    assert len(arch12) == 1
    assert arch12[0].file_path is None
    assert arch12[0].status == FindingStatus.NON_COMPLIANT
    assert not errors


def test_holistic_finding_dropped_when_already_flagged_per_file():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "File path: final_v2_ACTUAL.py": [
                {"policy_id": "ARCH-12", "status": "NON_COMPLIANT", "confidence": 0.9,
                 "evidence": "writes back into bronze"},
            ],
        },
        holistic_verdicts=[
            {"policy_id": "ARCH-12", "status": "NON_COMPLIANT", "confidence": 0.8,
             "evidence": "repo-wide echo of the same issue"},
        ],
    )

    findings, _ = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12"]
    assert len(arch12) == 1
    assert arch12[0].file_path == "final_v2_ACTUAL.py"


def test_fake_silver_layer_caught_only_by_holistic_pass():
    """Neither pipeline file is individually suspicious -- 01 does a plausible-looking
    'normalise currency codes' step, 02 reads what looks like validated input -- so
    per-file checks correctly find nothing. Only the holistic pass, seeing that the
    only 'processing' anywhere in the repo is a string uppercase (no null/duplicate/
    range check), can tell the implied quality gate never actually happens.
    """
    snapshot = scan(HOLISTIC_ONLY_REPO)
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "File path: Treasury_Pipeline/01_IngestFXPositions.py": [],
            "File path: Treasury_Pipeline/02_GenerateExposureReport.py": [],
        },
        holistic_verdicts=[
            {"policy_id": "ARCH-12", "status": "NON_COMPLIANT", "confidence": 0.75,
             "evidence": (
                 "Treasury_Pipeline/01_IngestFXPositions.py only uppercases currency_code before "
                 "writing to staging/; Treasury_Pipeline/02_GenerateExposureReport.py then reads that "
                 "staging file straight into the gold report. No file anywhere performs a null, "
                 "duplicate, or range check, so the silver quality gate implied by the folder "
                 "structure never actually happens."
             )},
        ],
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12"]
    assert len(arch12) == 1
    assert arch12[0].file_path is None
    assert arch12[0].status == FindingStatus.NON_COMPLIANT
    assert "01_IngestFXPositions.py" in arch12[0].evidence
    assert "02_GenerateExposureReport.py" in arch12[0].evidence
    assert not errors


def test_audit_continues_after_one_file_fails():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [
                {"policy_id": "SEC-3", "status": "NON_COMPLIANT", "confidence": 0.9, "evidence": "e"},
            ],
        },
        raise_for_substring="pipeline.yml",
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    assert any("pipeline.yml" in e for e in errors)
    assert any(f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py" for f in findings)
