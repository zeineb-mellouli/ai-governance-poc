<!--
SYNC IMPACT REPORT
Version change: [PLACEHOLDER] → 1.0.0
Modified principles: N/A — initial population from blank template
Added sections:
  - Core Principles (I through X)
  - Development Workflow
  - Governance
Removed sections: All bracketed template placeholders replaced
Templates requiring updates:
  - .specify/templates/plan-template.md   ✅ No changes required (Constitution Check uses dynamic reference)
  - .specify/templates/spec-template.md   ✅ No changes required
  - .specify/templates/tasks-template.md  ✅ No changes required (phase labels are already generic)
Deferred TODOs: None — all fields resolved from user input and project context
-->

# Code Polymer Constitution

## Core Principles

### I. Security First (NON-NEGOTIABLE)
API keys, passwords, and connection strings MUST never be hardcoded in source files, notebooks,
or configuration committed to version control. All credentials MUST be read exclusively via
`os.environ`. Any PR introducing a hardcoded secret MUST be rejected immediately and the secret
rotated before the branch is re-opened.

**Rationale**: Hardcoded secrets leak through version history and are a primary vector for
credential theft. Environment-variable injection is the lowest-friction, universally portable
mitigation and is enforceable via static analysis.

### II. Data Quality Gate (NON-NEGOTIABLE)
Every pipeline layer write (bronze → silver, silver → gold) MUST be preceded by a validation step
using **pandera** schemas that assert: absence of nulls in mandatory columns, no duplicate records
on business keys, and all numeric fields within declared acceptable ranges. Code that writes to
any layer without a passing pandera validation MUST NOT be merged.

**Rationale**: Silent data corruption downstream is harder to diagnose than a clear validation
failure at ingestion time. Pandera schemas are version-controllable, auditable, and
self-documenting.

### III. Medallion Architecture (NON-NEGOTIABLE)
All pipelines MUST follow the three-layer pattern:
- **Bronze** — raw, immutable ingestion layer. Transform code MUST NEVER overwrite bronze data.
- **Silver** — validated and cleansed layer, produced exclusively from bronze.
- **Gold** — aggregated and business-ready layer, produced exclusively from silver.

Layer skipping is prohibited. Any pipeline that reads from bronze and writes directly to gold
MUST be rejected at PR review.

**Rationale**: The medallion pattern ensures full data lineage traceability, enables isolated
debugging per layer, and guarantees that raw source data is always recoverable.

### IV. Observability
All pipeline scripts and modules MUST use the Python `logging` module configured with a
`FileHandler` for all operational messages. `print()` MUST NOT be used for operational,
diagnostic, or error output. Every pipeline run MUST emit at minimum: a START log entry with
run parameters, an END log entry with record counts, and structured ERROR entries on failure.

**Rationale**: `print()` output is lost in scheduled or headless execution contexts. File-backed
structured logging enables post-hoc incident analysis without requiring pipeline re-execution.

### V. Privacy by Default
Personally Identifiable Information (PII) — including but not limited to full names, email
addresses, and phone numbers — MUST NEVER appear in output datasets, log files, saved notebook
cell outputs, or any artifact committed to the repository. PII fields MUST be masked, hashed, or
dropped prior to any layer write.

**Rationale**: Compliance with data-protection regulations (GDPR, POPIA, CCPA) requires that PII
handling be explicit and opt-in. Incidental PII exposure in logs or outputs is a reportable
breach.

### VI. File Naming Standards
The following conventions MUST be applied consistently:
- **Files**: CamelCase with a `yyyyMMdd` date suffix (e.g., `CustomerExtract_20260713.csv`).
- **Folders**: `<Project>_<Feature>` format (e.g., `CodePolymer_Pricing`).
- **CSV columns**: snake_case exclusively (e.g., `customer_id`, `unit_price`).

Deviations require explicit team approval documented in the relevant PR description.

**Rationale**: Consistent naming reduces cognitive load during file discovery and prevents
ambiguous lexicographic ordering in date-stamped data deliveries across environments.

### VII. Reproducibility
ALL runtime dependencies MUST be pinned to exact versions in `requirements.txt` (no range
specifiers such as `>=` or `~=`). Any stochastic operation MUST call `np.random.seed()` with a
documented, fixed seed value immediately before execution. Pipelines without pinned dependencies
or unseeded stochastic steps MUST NOT be merged.

**Rationale**: Reproducibility is a prerequisite for debugging and regulatory audit.
Unpinned dependencies cause silent behaviour changes across environments and over time.

### VIII. Git Workflow
The repository MUST maintain exactly three branch types:
- `master` — production-ready code only; no direct commits permitted.
- `develop` — integration branch for completed user-story branches.
- `user-story/{id}` — short-lived feature branches, one per user story.

All commits MUST conform to the Conventional Commits specification
(e.g., `feat:`, `fix:`, `docs:`, `chore:`). Every pull request targeting `develop` or `master`
MUST have a minimum of **1 reviewer** approval before merge.

**Rationale**: A disciplined branching model reduces merge conflicts and makes CI/CD gate logic
predictable. Conventional commits enable automated changelog generation and semantic versioning.

### IX. SQL Naming Standards
All SQL objects — tables, views, stored procedures, indexes, and constraints — MUST use
**PascalCase** naming. Type-prefix conventions (`tbl_`, `sp_`, `vw_`, `fn_`) are prohibited.
Data model tables MUST carry `Fact` or `Dim` suffixes (e.g., `FactSalesOrder`, `DimCustomer`).
The `Key` suffix is reserved exclusively for primary-key and foreign-key columns
(e.g., `CustomerKey`, `OrderKey`).

**Rationale**: Prefix-free PascalCase names are more readable, avoid vendor lock-in on naming
conventions, and the Fact/Dim suffix pattern directly communicates the dimensional modelling role
of each object without relying on external documentation.

### X. Repository Naming
All repositories MUST follow the pattern `{dept}-{resource}-{project_name}` using lowercase
kebab-case components (e.g., `fin-code-polymer_pricing`, `ops-etl-supplier_onboarding`).
The `{dept}` segment MUST be a recognised departmental abbreviation; `{resource}` identifies the
system or dataset; `{project_name}` identifies the specific initiative.

**Rationale**: A structured naming convention enables automated governance tooling, rapid
org-wide repository discovery, and unambiguous departmental ownership attribution.

## Development Workflow

This section captures the end-to-end delivery process enforced by this constitution.

1. **Feature branching**: Create `user-story/{id}` from `develop`.
2. **Specification**: Author `spec.md` using the spec template before writing any code.
3. **Planning**: Run `/speckit.plan` to produce `plan.md`. The Constitution Check gate MUST pass
   before implementation begins.
4. **Implementation**: Follow tasks in `tasks.md`. Every task touching data MUST satisfy
   Principles II (Quality Gate), III (Medallion), IV (Observability), and V (Privacy).
5. **PR gate**: All PRs MUST pass automated linting, pandera validation tests, and have ≥ 1
   reviewer approval. Any constitution principle violation is grounds for a blocking review.
6. **Merge path**: `user-story/{id}` → `develop` → `master`. Direct commits to `master` are
   forbidden.

## Governance

This constitution supersedes all informal team conventions and prior ad-hoc standards documents.
Amendments MUST be proposed via a `user-story/{id}` branch, documented in this file with a
version bump, and approved by at least **2 reviewers** before merging to `develop`.

**Versioning policy**:
- **MAJOR**: Removal or redefinition of a NON-NEGOTIABLE principle (Principles I, II, III).
- **MINOR**: Addition of a new principle or section, or materially expanded guidance on an
  existing principle.
- **PATCH**: Clarifications, wording fixes, and non-semantic refinements.

**Compliance review**: This constitution MUST be reviewed against active pipeline code at the
start of each project milestone. Violations found during review MUST be filed as dedicated
`user-story/{id}` remediation branches and resolved before the milestone closes.

**Version**: 1.0.0 | **Ratified**: 2026-07-13 | **Last Amended**: 2026-07-13
