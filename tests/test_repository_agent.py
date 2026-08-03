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
