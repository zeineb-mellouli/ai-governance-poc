from agents import auditor_agent
from agents.repository_agent import scan
from agents.schemas import Finding, FindingStatus, RemediationStatus
from tests.fakes import FakeOpenAIClient, verdict

NON_COMPLIANT_REPO = "sample_repos/non_compliant/FinalProject"
HOLISTIC_ONLY_REPO = "sample_repos/holistic/fin-code-fx_exposure_report"

# Quotes lifted verbatim from the sample repos. The Auditor now checks that a
# reported violation's evidence really occurs in the file it was drawn from, so
# a made-up quote here would (correctly) be routed to review instead of counted.
SECRET_QUOTE = 'api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
BRONZE_READ_QUOTE = 'df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")'
FX_UPPERCASE_QUOTE = 'processed["currency_code"] = processed["currency_code"].str.upper()'


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
            verdict("SEC-3", quote=SECRET_QUOTE, evidence="hardcoded api_key"),
        ],
    })

    findings, errors = auditor_agent.audit(snapshot, client=client)

    sec3 = [f for f in findings if f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py"]
    assert len(sec3) == 1
    assert sec3[0].status == FindingStatus.NON_COMPLIANT
    # Every sample agreed, so confidence is 1.0 -- measured, not self-reported.
    assert sec3[0].confidence_score == 1.0
    assert sec3[0].retrieval_chunk_id == "SEC-3"
    assert not errors


def test_holistic_finding_kept_when_no_per_file_check_caught_it():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        holistic_verdicts=[
            verdict("ARCH-12", quote=BRONZE_READ_QUOTE,
                    evidence="no silver-layer file exists anywhere in this repository"),
        ],
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12" and f.status != FindingStatus.NOT_APPLICABLE]
    assert len(arch12) == 1
    assert arch12[0].file_path is None
    assert arch12[0].status == FindingStatus.NON_COMPLIANT
    assert not errors


def test_holistic_finding_dropped_when_already_flagged_per_file():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "File path: final_v2_ACTUAL.py": [
                verdict("ARCH-12", quote=BRONZE_READ_QUOTE, evidence="writes back into bronze"),
            ],
        },
        holistic_verdicts=[
            verdict("ARCH-12", quote=BRONZE_READ_QUOTE, evidence="repo-wide echo of the same issue"),
        ],
    )

    findings, _ = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12" and f.status == FindingStatus.NON_COMPLIANT]
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
            verdict("ARCH-12", quote=FX_UPPERCASE_QUOTE, evidence=(
                "Treasury_Pipeline/01_IngestFXPositions.py only uppercases currency_code before "
                "writing to staging/; Treasury_Pipeline/02_GenerateExposureReport.py then reads that "
                "staging file straight into the gold report. No file anywhere performs a null, "
                "duplicate, or range check, so the silver quality gate implied by the folder "
                "structure never actually happens."
            )),
        ],
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    arch12 = [f for f in findings if f.policy_id == "ARCH-12" and f.status == FindingStatus.NON_COMPLIANT]
    assert len(arch12) == 1
    assert arch12[0].file_path is None
    assert "01_IngestFXPositions.py" in arch12[0].evidence
    assert "02_GenerateExposureReport.py" in arch12[0].evidence
    assert not errors


def test_audit_continues_after_one_file_fails():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [verdict("SEC-3", quote=SECRET_QUOTE)],
        },
        raise_for_substring="pipeline.yml",
    )

    findings, errors = auditor_agent.audit(snapshot, client=client)

    assert any("pipeline.yml" in e for e in errors)
    assert any(f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py" for f in findings)


# --- structured verdicts: status is derived, never stated --------------------


def test_verdict_that_does_not_apply_becomes_not_applicable():
    status, note = auditor_agent._verdict_to_status(
        {"applies": False, "violation_present": None, "evidence_quote": ""}, "file body"
    )
    assert status == FindingStatus.NOT_APPLICABLE
    assert note is None


def test_violation_without_a_quote_is_routed_to_review():
    """A violation the model cannot point at in the file is not a finding.

    This is the anti-fabrication gate: the observed failure was a per-file
    verdict asserting that requirements.txt had unpinned packages while
    evaluating azure-pipelines.yml, a file it could not see the contents of.
    """
    status, note = auditor_agent._verdict_to_status(
        {"applies": True, "violation_present": True, "evidence_quote": ""}, "file body"
    )
    assert status == FindingStatus.NEEDS_REVIEW
    assert "no quoted evidence" in note


def test_violation_quoting_text_absent_from_the_file_is_routed_to_review():
    status, note = auditor_agent._verdict_to_status(
        {"applies": True, "violation_present": True, "evidence_quote": "pandas  # unpinned"},
        "import pandas as pd\n",
    )
    assert status == FindingStatus.NEEDS_REVIEW
    assert "does not appear in the file" in note


def test_grounding_tolerates_rewrapped_whitespace():
    status, note = auditor_agent._verdict_to_status(
        {"applies": True, "violation_present": True, "evidence_quote": "api_key = 'x'"},
        "foo\napi_key   =    'x'\nbar",
    )
    assert status == FindingStatus.NON_COMPLIANT
    assert note is None


def test_missing_verdicts_are_filled_in_and_reported():
    """The grid stays the same size on every run, and the gap is visible."""
    policies = auditor_agent._load_policies()
    candidates = ["SEC-3", "DQ-1", "OPS-2"]

    findings, missing = auditor_agent._findings_from_payload(
        {"verdicts": [verdict("SEC-3", applies=False, violation=None)]},
        candidates,
        policies,
        source_text="body",
        file_path="a.py",
        retrieval_scores={},
    )

    assert len(findings) == len(candidates)
    assert missing == ["DQ-1", "OPS-2"]
    assert all(f.status == FindingStatus.NOT_APPLICABLE for f in findings)


# --- applicability gating: file type decided in code, not in prose ----------


def test_policy_candidates_are_gated_by_file_type():
    """Each of these used to be a "Return NOT_APPLICABLE if..." sentence in a prompt."""
    policies = auditor_agent._load_policies()

    def candidates(path):
        return set(auditor_agent._file_candidates(path, policies))

    # NAM-5's model half is the column rule, so only data files can carry it.
    assert "NAM-5" in candidates("gold/Report_2024-07-01.csv")
    assert "NAM-5" not in candidates("pipeline/transforms.py")

    # SQL-11 requires PascalCase columns; a CSV header must be snake_case under
    # NAM-5. Gating by extension is what stops the two contradicting each other.
    assert "SQL-11" not in candidates("gold/Report_2024-07-01.csv")
    assert "SQL-11" in candidates("Risk_SQL/CreateVarBreachFact.sql")

    # GIT-8 is a control on CI config and contribution guides, not on prose.
    assert "GIT-8" in candidates("azure-pipelines.yml")
    assert "GIT-8" in candidates(".github/workflows/ci.yml")
    assert "GIT-8" not in candidates("README.md")
    assert "GIT-8" not in candidates("specs/001-thing/quickstart.md")

    # Test files are not pipeline jobs and are not expected to log or validate.
    assert "OPS-2" not in candidates("tests/test_pipeline.py")
    assert "DQ-1" not in candidates("tests/test_pipeline.py")
    assert "OPS-2" in candidates("src/Ingest.py")

    # A markdown file can still leak a credential.
    assert candidates("README.md") == {"SEC-3"}
    # ...but a template documenting required secrets is exempt by design.
    assert candidates(".env.example") == set()


def test_repository_and_deterministic_policies_are_withheld_from_the_per_file_pass():
    policies = auditor_agent._load_policies()
    every_candidate = set()
    for path in ["a.py", "b.sql", "c.csv", "azure-pipelines.yml", "README.md"]:
        every_candidate |= set(auditor_agent._file_candidates(path, policies))

    assert "DM-7" not in every_candidate      # answerable only across the whole repo
    assert "REPO-9" not in every_candidate    # decided by regex in code
    assert "REPRO-13" not in every_candidate  # decided by parsing in code

    assert auditor_agent._deterministic_ids(policies) == {"REPO-9", "REPRO-13"}
    assert auditor_agent._repository_only_ids(policies) == {"DM-7"}


# --- deterministic naming repair --------------------------------------------


def test_suggest_name_repairs_case_and_date_format():
    assert auditor_agent._suggest_name("sql/create_tables.sql") == "sql/CreateTables.sql"
    assert auditor_agent._suggest_name("data/customers.csv") == "data/Customers.csv"
    assert auditor_agent._suggest_name("pipeline/utils/logging_config.py") == "pipeline/utils/LoggingConfig.py"
    assert (
        auditor_agent._suggest_name("bronze/CollateralPositions_20240815.csv")
        == "bronze/CollateralPositions_2024-08-15.csv"
    )
    # Stage prefix is the house convention and survives the rename.
    assert (
        auditor_agent._suggest_name("silver/DailyCashMovements_validated_20240701.csv")
        == "silver/DailyCashMovementsValidated_2024-07-01.csv"
    )


def test_suggest_name_declines_when_the_right_name_is_a_judgement_call():
    """A vague token means the name carries no information to repair."""
    assert auditor_agent._suggest_name("Untitled.ipynb") is None
    assert auditor_agent._suggest_name("final_v2_ACTUAL.py") is None
    # Eight digits that are not a real date: do not guess what was meant.
    assert auditor_agent._suggest_name("data/Report_99999999.csv") is None


def test_suggested_name_never_itself_violates_the_grammar():
    for path in [
        "sql/create_tables.sql",
        "data/customers.csv",
        "bronze/CollateralPositions_20240815.csv",
        "silver/DailyCashMovements_validated_20240701.csv",
    ]:
        suggested = auditor_agent._suggest_name(path)
        assert suggested is not None
        assert auditor_agent._name_violations(suggested) == []


def test_naming_findings_carry_a_deterministic_git_mv_and_stay_non_compliant():
    snapshot = scan(NON_COMPLIANT_REPO)
    findings = {f.file_path: f for f in auditor_agent._evaluate_file_names(snapshot)}

    fixable = findings["sql/create_tables.sql"]
    assert fixable.status == FindingStatus.NON_COMPLIANT
    assert fixable.confidence_score == 1.0
    assert fixable.remediation_status == RemediationStatus.AUTO_FIXED
    assert fixable.remediation.fix == "git mv sql/create_tables.sql sql/CreateTables.sql"

    unfixable = findings["Untitled.ipynb"]
    assert unfixable.status == FindingStatus.NON_COMPLIANT
    assert unfixable.remediation is None
    assert unfixable.remediation_status == RemediationStatus.NO_FIX_AVAILABLE
    assert "author must choose it" in unfixable.remediation_note


# --- self-consistency voting ------------------------------------------------


def _sample(status: FindingStatus, evidence: str = "e") -> Finding:
    return Finding(
        policy_id="DQ-1", title="t", severity="HIGH", file_path="a.py",
        status=status, confidence_score=1.0, evidence=evidence,
        retrieval_chunk_id="DQ-1", retrieval_score=0.1,
    )


def test_vote_takes_the_majority_and_reports_the_agreement_rate():
    voted = auditor_agent._vote([
        [_sample(FindingStatus.NON_COMPLIANT, "found it")],
        [_sample(FindingStatus.NON_COMPLIANT, "found it")],
        [_sample(FindingStatus.COMPLIANT, "looks fine")],
    ])
    assert len(voted) == 1
    assert voted[0].status == FindingStatus.NON_COMPLIANT
    assert voted[0].confidence_score == round(2 / 3, 3)
    assert "2/3 samples agreed" in voted[0].evidence


def test_unanimous_vote_scores_full_confidence_and_adds_no_noise():
    voted = auditor_agent._vote([[_sample(FindingStatus.COMPLIANT)]] * 3)
    assert voted[0].confidence_score == 1.0
    assert "samples agreed" not in voted[0].evidence


def test_a_split_vote_is_undecided_rather_than_guessed():
    """A model with no settled view is exactly what NEEDS_REVIEW is for."""
    voted = auditor_agent._vote([
        [_sample(FindingStatus.NON_COMPLIANT)],
        [_sample(FindingStatus.COMPLIANT)],
        [_sample(FindingStatus.NOT_APPLICABLE)],
    ])
    assert voted[0].status == FindingStatus.NEEDS_REVIEW
    assert "samples split" in voted[0].evidence


def test_sampling_uses_a_fixed_seed_sequence():
    """Samples differ from each other, but the set of samples is reproducible."""
    settings = [auditor_agent._sample_settings(i, 3) for i in range(3)]
    seeds = [s for s, _ in settings]
    assert len(set(seeds)) == 3
    assert seeds == sorted(seeds)
    assert all(temp == auditor_agent.VOTE_TEMPERATURE for _, temp in settings)
    # k=1 measures nothing, so there is no reason to leave greedy decoding.
    assert auditor_agent._sample_settings(0, 1) == (auditor_agent.REQUEST_SEED, 0.0)


def test_samples_argument_overrides_the_module_default():
    assert auditor_agent._resolve_samples(None) == auditor_agent.AUDIT_SAMPLES
    assert auditor_agent._resolve_samples(1) == 1
    assert auditor_agent._resolve_samples(5) == 5
    assert auditor_agent._resolve_samples(0) == 1  # never zero calls


def test_disagreeing_samples_lower_confidence_end_to_end():
    snapshot = scan(NON_COMPLIANT_REPO)
    client = FakeOpenAIClient(verdicts_by_path_substring={
        # A per-sample script: two samples see the secret, one does not.
        "final_v2_ACTUAL.py": [
            [verdict("SEC-3", quote=SECRET_QUOTE)],
            [verdict("SEC-3", quote=SECRET_QUOTE)],
            [verdict("SEC-3", violation=False)],
        ],
    })

    findings, _ = auditor_agent.audit(snapshot, client=client)

    sec3 = next(f for f in findings if f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py")
    assert sec3.status == FindingStatus.NON_COMPLIANT
    assert sec3.confidence_score == round(2 / 3, 3)


# --- REPRO-13 dependency pinning, decided by parsing ------------------------


def test_unpinned_requirements_are_named_exactly():
    assert auditor_agent._unpinned_from_requirements(
        "pandas==2.1.4\nscikit-learn\nstatsmodels\n"
    ) == ["scikit-learn", "statsmodels"]
    # Comments, blank lines and pip flags are not packages.
    assert auditor_agent._unpinned_from_requirements(
        "# deps\n\n-r base.txt\n--index-url https://x\npandas==2.1.4\n"
    ) == []
    # A range or compatible-release specifier is not an exact version.
    assert auditor_agent._unpinned_from_requirements("pandas>=2.0\nnumpy~=1.26\n") == ["pandas", "numpy"]
    # Environment markers and direct references are handled.
    assert auditor_agent._unpinned_from_requirements(
        "pandas==2.1.4; python_version>='3.9'\nlib @ git+https://x\n"
    ) == []


def test_pinning_check_passes_a_fully_pinned_repo():
    """Regression: six of eight repos were flagged despite fully pinned manifests."""
    policy = auditor_agent._load_policies()["REPRO-13"]
    for repo in [
        "sample_repos/compliant/ops-code-market_rate",
        "sample_repos/not_applicable/fin-code-filing_deadline_tracker",
        "sample_repos/adversarial/fin-code-collateral_management",
        "sample_repos/holistic/fin-code-fx_exposure_report",
        "sample_repos/ambiguous/fin-code-credit_scoring_model",
    ]:
        finding = auditor_agent._evaluate_dependency_pinning(scan(repo), policy)
        assert finding.status == FindingStatus.COMPLIANT, f"{repo}: {finding.evidence}"


def test_pinning_check_flags_only_genuinely_unpinned_repos():
    policy = auditor_agent._load_policies()["REPRO-13"]

    var_risk = auditor_agent._evaluate_dependency_pinning(
        scan("sample_repos/realistic/fin-code-var_risk_model"), policy
    )
    assert var_risk.status == FindingStatus.NON_COMPLIANT
    assert "scikit-learn" in var_risk.evidence and "statsmodels" in var_risk.evidence

    final_project = auditor_agent._evaluate_dependency_pinning(scan(NON_COMPLIANT_REPO), policy)
    assert final_project.status == FindingStatus.NON_COMPLIANT
    assert "pandas" in final_project.evidence


def test_missing_readme_gets_a_scaffold_fix():
    snapshot = scan(NON_COMPLIANT_REPO)
    readme = next(
        f for f in auditor_agent._evaluate_repo_level(snapshot)
        if f.policy_id == "NAM-5" and f.file_path is None
    )
    assert readme.status == FindingStatus.NON_COMPLIANT
    assert readme.remediation_status == RemediationStatus.AUTO_FIXED
    assert "README.md" in readme.remediation.fix
