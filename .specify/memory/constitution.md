<!--
Sync Impact Report
- Version change: none -> 1.0.0
- Modified principles:
  - Initialized from template placeholders
- Added sections:
  - Repository Constraints
  - Delivery Workflow
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ verified compatible: .specify/templates/plan-template.md
  - ✅ verified compatible: .specify/templates/spec-template.md
  - ✅ verified compatible: .specify/templates/tasks-template.md
- Follow-up TODOs:
  - None
-->

# Data Science Demo Constitution

## Core Principles

### I. Python 3.12 and uv Are Canonical
All repository changes MUST remain compatible with Python 3.12 and use `uv` as the
canonical dependency and environment workflow. Dependency changes MUST be recorded in
`pyproject.toml`, and generated lock or export artifacts MUST stay in sync when they are
affected.

### II. Data Contract Stability First
Changes to ingestion, normalization, or dashboard code MUST preserve a clear earthquake
data contract: explicit field names, explicit type coercion, and safe handling of missing
or malformed upstream values. Schema or partitioning changes MUST be deliberate and MUST
be documented in the same change.

### III. Local Reproducibility Over Hidden Infrastructure
The project MUST remain runnable by a developer from this repository with local tools and
documented commands. New features MUST avoid introducing required external services,
background infrastructure, or deployment-only assumptions unless the repository is also
updated to document and support them.

### IV. Small, Verifiable Changes
Every non-trivial change MUST include the smallest practical validation for the code path
it touches, such as a targeted run, lint check, notebook execution step, or manual
verification note. If no automated test exists for the changed area, the change MUST state
what was run instead.

### V. Keep the Demo Simple
This repository is a focused demo, not a general-purpose data platform. New abstractions,
frameworks, and configuration layers MUST be justified by a concrete repo need and MUST
be rejected when a straightforward Python implementation is sufficient.

## Repository Constraints

- The supported stack is Python 3.12 with `deltalake`, `pandas`, `pyarrow`, `requests`,
  `streamlit`, and related notebook tooling already present in the repository.
- The canonical persisted dataset is the Delta table under
  `notebooks/data/earthquakes_delta_streamed/`.
- Source-of-truth documentation lives in `README.md`; user-visible behavior changes MUST
  update that file when setup, commands, or outputs change materially.
- Pre-commit automation is allowed to enforce formatting and generated dependency exports;
  repo automation MUST not silently change runtime behavior.

## Delivery Workflow

- Feature specs, plans, and tasks generated in this repository MUST satisfy this
  constitution before implementation begins.
- Implementation plans MUST state the concrete validation expected for the work.
- Tasks MUST stay scoped so ingestion behavior, dashboard behavior, and notebook-facing
  changes can be reviewed independently when possible.
- Reviews MUST reject changes that add avoidable complexity, leave dependency artifacts out
  of sync, or change the data contract without documentation.

## Governance

This constitution supersedes ad hoc project conventions for planning and implementation in
this repository. Amendments require updating this file, updating the sync impact report at
the top of the file, and re-checking `.specify/templates/plan-template.md`,
`.specify/templates/spec-template.md`, and `.specify/templates/tasks-template.md` for
continued alignment. Versioning follows semantic versioning for governance changes: MAJOR
for incompatible principle changes or removals, MINOR for new principles or materially new
requirements, and PATCH for clarifications that do not change project obligations.

**Version**: 1.0.0 | **Ratified**: 2026-03-20 | **Last Amended**: 2026-03-20