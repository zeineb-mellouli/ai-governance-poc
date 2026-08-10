from agents.repository_agent import scan
from agents.schemas import FileType

NON_COMPLIANT_REPO = "sample_repos/non_compliant/FinalProject"
COMPLIANT_REPO = "sample_repos/compliant/ops-code-market_rate"


def test_repo_root_name_and_missing_readme():
    snapshot = scan(NON_COMPLIANT_REPO)
    assert snapshot.repo_root_name == "FinalProject"
    assert snapshot.has_readme is False


def test_readme_detected_when_present():
    snapshot = scan(COMPLIANT_REPO)
    assert snapshot.repo_root_name == "ops-code-market_rate"
    assert snapshot.has_readme is True


def test_file_type_classification():
    snapshot = scan(NON_COMPLIANT_REPO)
    by_path = {f.path: f for f in snapshot.files}

    assert by_path["final_v2_ACTUAL.py"].file_type == FileType.PYTHON
    assert "api_key" in by_path["final_v2_ACTUAL.py"].content
    assert by_path["sql/create_tables.sql"].file_type == FileType.SQL
    assert by_path["pipeline.yml"].file_type == FileType.YAML


def test_notebook_cells_and_outputs_extracted():
    snapshot = scan(NON_COMPLIANT_REPO)
    by_path = {f.path: f for f in snapshot.files}
    notebook = by_path["Untitled.ipynb"]
    assert notebook.file_type == FileType.NOTEBOOK
    assert "customers" in notebook.content


def test_csv_header_only_no_full_data():
    snapshot = scan(NON_COMPLIANT_REPO)
    by_path = {f.path: f for f in snapshot.files}
    customers = by_path["data/customers.csv"]
    assert customers.file_type == FileType.CSV
    assert customers.csv_columns == ["name", "email", "phone", "salary"]
    assert "John Smith" not in customers.content


# --- spec-driven-development scaffolding is not the governed artifact --------


def test_spec_kit_scaffolding_is_excluded_from_the_scan():
    """Governance applies to the pipeline that runs, not the documents describing it.

    On code-polymer this is 29 of 48 files -- 60% of the repository was spec
    documents and spec-kit agent definitions, each costing a model call.
    """
    paths = {f.path for f in scan("sample_repos/sdd_generated/code-polymer").files}

    assert not [p for p in paths if p.startswith("specs/")]
    assert not [p for p in paths if p.startswith(".github/agents/")]
    assert not [p for p in paths if p.startswith(".github/prompts/")]


def test_real_code_and_controls_survive_the_exclusion():
    """The exclusion must not take the pipeline, the CI config, or the DDL with it.

    .github/ has to stay walkable because .github/workflows/ is a genuine CI
    control, and the DDL and README carry the grain statements DM-7 looks for.
    """
    paths = {f.path for f in scan("sample_repos/sdd_generated/code-polymer").files}

    assert "azure-pipelines.yml" in paths
    assert "sql/CreatePolymerPricingFact.sql" in paths
    assert "README.md" in paths
    assert any(p.startswith("pipeline/") for p in paths)

    churn = {f.path for f in scan("sample_repos/sdd_generated/ops-code-customer_churn").files}
    assert not [p for p in churn if p.startswith("specs/")]
    assert any(p.startswith("src/") for p in churn)
    assert "README.md" in churn          # holds this repo's grain statement


def test_a_source_folder_named_agents_is_not_excluded(tmp_path):
    """Position, not name: 'agents' and 'prompts' are ordinary source folders.

    Putting them in SKIP_DIRS would silently drop real code -- this project's own
    pipeline lives in agents/.
    """
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "Auditor.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ".github" / "agents" / "speckit.plan.agent.md").write_text("doc\n", encoding="utf-8")

    paths = {f.path for f in scan(str(tmp_path)).files}
    assert "agents/Auditor.py" in paths
    assert ".github/agents/speckit.plan.agent.md" not in paths
