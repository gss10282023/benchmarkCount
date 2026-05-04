# Review Packet: Step 02

## Review Goal
Please review whether Step 2, "Repo Bootstrap 和基础文件结构", creates a repository skeleton that can support the frozen evidence-envelope experiment protocol without moving ahead into Step 3 or implementing formal experiment logic.

The review should focus on structure, boundaries, canonical entry points, schema object presence, secret handling, and testability. It should not require formal schema validation, contract lifecycle, scorer behavior, adapters, deployment, aggregation, freeze, paper outputs, or release logic; those are later steps.

Decision target:

```text
ALLOW_NEXT_STEP only if Step 2 structure is sufficient and Blocking Issues is empty.
BLOCK_NEXT_STEP if any required Step 2 directory, CLI skeleton, first-class schema file, test entry, secret exclusion, or fail-closed boundary is missing.
```

## Strict Sources Used
This packet is self-contained for GPT Pro. The following source excerpts are the binding sources used for Step 2.

Source: `工程文件说明.md` 0.4, review packet mechanism:

```text
每个 review packet 必须包含:
Review Goal
Strict Sources Used
Files Created Or Changed
Content For Review
Contract With The Paper
Known Non-Goals
Risk Checklist
Questions For GPT Pro
Acceptance Criteria

Step 2 给 GPT Pro 的审查包内容:
repo tree, pyproject.toml, .gitignore, package layout, 测试入口.

Packet 必须自包含, 不得依赖 GPT Pro 能访问本地路径.
高风险规则必须放原文摘录.
```

Source: `工程文件说明.md` 0.6.1, canonical CLI and formal-code boundary:

```text
正式逻辑必须放在 `src/evidence_system/` 下. 正式入口优先使用:
python -m evidence_system.cli.<command>

`scripts/*.py` 如存在, 只能是 thin wrappers, 内部调用 package CLI;
不得让正式逻辑只存在于 `scripts/`.

Canonical mapping:
scripts/check_infra.py -> python -m evidence_system.cli.check_infra
scripts/deploy_all.py -> python -m evidence_system.cli.deploy_all
scripts/deploy_webarena.py -> python -m evidence_system.cli.deploy_webarena
scripts/deploy_osworld.py -> python -m evidence_system.cli.deploy_osworld
scripts/deploy_other_vps.py -> python -m evidence_system.cli.deploy_other_vps
scripts/deploy_local_androidworld.py -> python -m evidence_system.cli.deploy_local_androidworld
scripts/monitor.py -> python -m evidence_system.cli.monitor
scripts/collect_results.py -> python -m evidence_system.cli.collect_results
scripts/resume_failed.py -> python -m evidence_system.cli.resume_failed
scripts/make_tables.py -> python -m evidence_system.cli.make_tables
scripts/make_figures.py -> python -m evidence_system.cli.make_figures
scripts/make_appendix.py -> python -m evidence_system.cli.make_appendix
scripts/final_report.py -> python -m evidence_system.cli.final_report

make_tables, make_figures, make_appendix, final_report 可以共享
evidence_system.paper 和 make_paper_outputs 内部实现, 但 CLI
responsibilities 必须可单独调用、可测试、可审计.

deploy_*, monitor, collect_results, resume_failed 可以复用
orchestrator.remote / orchestrator.resume, 但不得只隐含在 run_domain 中.
```

Source: `工程文件说明.md` 0.6.17, first-class schema coverage:

```text
Schema coverage must treat manifest, job, deployment, stats, and paper outputs
as first-class validated artifacts, not implicit Python dicts. At minimum:

experiment_manifest.schema.json
paper_mapping.schema.json
job.schema.json
agent_config.schema.json
infra_config.schema.json
stats_plan.schema.json
bootstrap_plan.schema.json
audit_sampling_plan.schema.json
rerun_subset.schema.json
aggregate_metrics.schema.json
prediction_outcome.schema.json
pairwise_matrix.schema.json
paper_output.schema.json
denominator_audit.schema.json
failure_record.schema.json
deployment_manifest.schema.json

These schemas must cover experiment id, priority, canonical domain id,
paper labels, case counts, agents, official splits, contract metadata,
raw logs, metrics, tables, figures, machine role, human-time cost,
Agent A-D probe rationale, phase / experiment_type / priority,
deployment provenance, and paper-output source mapping.
```

Source: `工程文件说明.md` Step 2:

```text
Step 2: Repo Bootstrap 和基础文件结构.
主责: Codex. GPT Pro 只做轻量结构审查. 人工确认新 repo 起点.

Required root files:
pyproject.toml
README.md
.gitignore
.env.example

Required directories include:
docs/
schemas/
src/evidence_system/
scripts/ optional thin wrappers only
tests/unit/
tests/integration/
tests/e2e/
tests/fixtures/

Required package modules include:
cli, core, contracts, llm, adapters, scorer, orchestrator, audit, stats,
paper, release.

Bootstrap acceptance test:
- `python -m pytest` 可以运行.
- `python -m evidence_system.cli.validate_config` 能读
  `configs/infra.yaml` 和 `configs/agents.yaml`.
- canonical CLI mapping in 0.6.1 exists for infra check, deploy, monitor,
  collect, resume, tables, figures, appendix, and final report responsibilities.
- 若创建 `scripts/*.py`, 它们必须只是调用 `evidence_system.cli` 的
  thin wrappers; formal logic 不得只存在于 `scripts/`.
- `.env.example` 不包含真实 key.
- `.gitignore` 排除 `.env`, `.env.*`, `results/raw_runs/`,
  `results/artifacts/`, private SSH keys, API logs containing raw prompts
  if marked private.
```

Source: `工程文件说明.md` additional fail-closed gates:

```text
`SPEC_FROZEN=true` missing or `results/manifests/spec_freeze.json` missing
docs/paper_mapping/source document hashes -> block Step 2+ formal progression.

canonical CLI mapping missing for any required plan/experiment script
responsibility -> block Step 2/12 approval.
```

Source: `docs/system_spec.md`, old scaffold and mock/dry-run boundary:

```text
Old scaffold, `mock_result`, and dry-run output are not formal experiment logic.
They may be used only for engineering self-checks and synthetic fixtures.
Formal logic must live under `src/evidence_system/`.
Any `scripts/*.py` files are thin wrappers around package CLIs and cannot
contain unique formal logic.
```

Step 2 precondition evidence recorded before this bootstrap:

```text
reviews/gpt_pro/step01_spec_freeze_review.md exists.
Step 1 review Decision: ALLOW_NEXT_STEP.
Step 1 Blocking Issues: "未发现需要阻断 Step 2 的 Step 1 spec gap."
results/manifests/spec_freeze.json exists.
SPEC_FROZEN: true.
manual_confirmation: "SPEC_FROZEN=true".
spec_freeze.json records:
  docs_hash: 8490e999c28d241a12b405b9793ea997b5d754ffc8afa51f556d8362962e7101
  paper_mapping_hash: 678f35e422b16a6a250d4eb7e364b9ff2a1c34dfe3fe5daa4d177fd8ec3adca9
  source_documents_hash: 71dc1ab6e0660908dbf4240a51bc91d22de99e2921613ba7d5d42207f59cd776
  source_documents include revised_agent_benchmark_paper.tex, 计划.md,
  实验说明.md, 工程文件说明.md with sha256 entries.
```

## Files Created Or Changed
Only the Step 2 review packet is being reviewed here, but this packet describes the Step 2 bootstrap files created earlier. No formal implementation logic is modified by this packet update.

Step 2 root files:

```text
pyproject.toml
README.md
.gitignore
.env.example
```

Step 2 package, schema, tests, and review directories:

```text
schemas/
src/evidence_system/
tests/
reviews/packets/
reviews/gpt_pro/
```

Created package module groups:

```text
src/evidence_system/cli/
src/evidence_system/core/
src/evidence_system/contracts/
src/evidence_system/llm/
src/evidence_system/adapters/
src/evidence_system/scorer/
src/evidence_system/orchestrator/
src/evidence_system/audit/
src/evidence_system/stats/
src/evidence_system/paper/
src/evidence_system/release/
```

Review packet files present:

```text
reviews/packets/step01_spec_freeze_review_packet.md
reviews/packets/step02_repo_bootstrap_review_packet.md
reviews/gpt_pro/step01_spec_freeze_review.md
```

No `scripts/*.py` files were created in Step 2. Current `scripts/` status: absent.

## Content For Review
This section includes the key file content or tree excerpts needed for a self-contained Step 2 review. Each item includes purpose, excerpt, risks for GPT Pro, and mapping to `工程文件说明.md` Step 2 / 0.6.1 / 0.6.17 as applicable.

### 1. Root File: `pyproject.toml`
Purpose: make the package installable from `src/`, configure the test entry, and avoid hidden script-only logic.

Key content excerpt:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "evidence-system"
version = "0.0.0"
description = "Bootstrap skeleton for the evidence-envelope experiment system."
readme = "README.md"
requires-python = ">=3.11"
authors = [
  { name = "Evidence System Maintainers" }
]
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0"
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"
```

Risk points for GPT Pro:
- Confirm package discovery is rooted in `src`, not `scripts`.
- Confirm `python -m pytest` has a defined test entry.
- Confirm no runtime dependency or entry point creates formal experiment behavior.

Mapping:
- Step 2: required `pyproject.toml`, test entry.
- 0.6.1: supports package CLI under `src/evidence_system`.
- 0.6.17: no direct schema implementation here; schema objects are files under `schemas/`.

### 2. Root File: `README.md`
Purpose: document Step 2 boundary for future reviewers and users.

Key content excerpt:

```markdown
# Evidence System Bootstrap

This repository contains the Step 2 package skeleton for the evidence-envelope benchmark experiment system.

The current state is intentionally limited:

- Formal code lives under `src/evidence_system/`.
- Existing paper, docs, configs, experiments, and preserved result-output dependencies remain in place.
- Adapter, scorer, deployment, orchestration, statistics, paper-output, release, and LLM logic are bootstrap placeholders only.
- Commands that would run or mutate formal experiments fail closed unless called in explicit bootstrap-check mode.

Canonical formal entry points use:

python -m evidence_system.cli.<command>

The legacy `scripts/*.py` entry points are not created in this step. If wrappers are added later, they must only delegate to package CLIs and must not contain unique formal logic.

Bootstrap Checks:
python -m pytest
python -m evidence_system.cli.validate_config

Secrets:
Do not put real API keys, SSH private keys, credentials, or private prompt logs in repository files. Use environment variable names and local paths only.
```

Risk points for GPT Pro:
- Confirm README does not imply Step 2 has implemented formal adapters, scorers, freeze, or paper outputs.
- Confirm README points to package CLIs rather than script-only entry points.
- Confirm secret policy is explicit.

Mapping:
- Step 2: required `README.md`.
- 0.6.1: documents formal logic under `src/evidence_system/` and package CLI.
- 0.6.17: no schema rules are claimed; schema validation remains later work.

### 3. Root File: `.gitignore`
Purpose: prevent real secrets, raw artifacts, raw runs, raw/private logs, caches, and large formal results from entering the repository.

Key content excerpt:

```gitignore
.DS_Store
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
venv/
build/
dist/
*.egg-info/

.env
.env.*
!.env.example
secrets/*
!secrets/.env.example

*.pem
*.key
*.p8
id_rsa
id_rsa*
id_ed25519
id_ed25519*
*ssh_private_key*

results/raw/
results/raw_runs/
results/raw_artifacts/
results/artifacts/
results/formal/
results/full/
results/logs/
results/private_logs/
results/private_llm_logs/
results/llm_logs/private/
results/preflight/
results/failures/
results/audits/
results/reruns/
results/bootstrap/
results/tmp/

*.log
*.private.log
```

Risk points for GPT Pro:
- Confirm `.env` and `.env.*` are excluded while `.env.example` remains trackable.
- Confirm private SSH key patterns are excluded.
- Confirm raw artifacts and raw runs are excluded.
- Confirm large formal result directories are excluded.
- Confirm this does not exclude preserved checked-in paper dependency outputs already present under `results/tables`, `results/figures`, and `results/appendix`.

Mapping:
- Step 2: required `.gitignore` with `.env`, `.env.*`, `results/raw_runs/`, `results/artifacts/`, private SSH keys, private API/prompt logs.
- 0.6.1: supports separation of formal package code from raw run outputs.
- 0.6.17: keeps future first-class result artifacts auditable by avoiding accidental raw/private artifact commits.

### 4. Root File: `.env.example`
Purpose: provide environment variable names only, with no real values.

Full content:

```dotenv
# Step 2 bootstrap environment template.
# Values are intentionally empty. Do not commit real secrets.

OPENROUTER_API_KEY=
EVIDENCE_SYSTEM_ROOT=
EVIDENCE_SYSTEM_CONFIG_DIR=configs
EVIDENCE_SYSTEM_RESULTS_DIR=results

# Optional local-only SSH key path reference. Do not paste private key contents.
EVIDENCE_SYSTEM_SSH_KEY_PATH=
```

Risk points for GPT Pro:
- Confirm no real API key, token, host password, or private key content appears.
- Confirm `OPENROUTER_API_KEY` is an env var name only, not a value.
- Confirm local path defaults are not secrets.

Mapping:
- Step 2: required `.env.example` with no real key.
- 0.6.1: no formal runtime config is hardcoded here.
- 0.6.17: no schema impact; secret handling protects future provenance artifacts.

### 5. Package Layout: `src/evidence_system/`
Purpose: establish the formal-code home and module boundaries for future steps. Current files are skeletons; formal logic is intentionally absent.

Tree excerpt:

```text
src/evidence_system/
  __init__.py
  adapters/
    __init__.py
    base.py
    agentdojo.py
    androidworld.py
    appworld.py
    judge_only.py
    maintenance_update.py
    matched_budget_controls.py
    osworld_verified.py
    tau3_retail.py
    webarena_verified.py
    workarena.py
  audit/
    __init__.py
    agreement.py
    blind_packet.py
    kappa.py
    rerun.py
    sampling.py
  cli/
    __init__.py
    __main__.py
    _common.py
    validate_config.py
    validate_manifest.py
    check_infra.py
    deploy_all.py
    deploy_webarena.py
    deploy_osworld.py
    deploy_other_vps.py
    deploy_local_androidworld.py
    monitor.py
    collect_results.py
    resume_failed.py
    validate_contracts.py
    draft_contracts.py
    review_contracts.py
    lock_contracts.py
    update_manifest_contract_locks.py
    freeze_predictions.py
    run_preflight.py
    run_full.py
    run_domain.py
    score_records.py
    aggregate_results.py
    aggregate.py
    run_audit.py
    run_rerun.py
    make_paper_outputs.py
    make_tables.py
    make_figures.py
    make_appendix.py
    final_report.py
    validate_results.py
    make_release.py
  contracts/
    draft.py
    review.py
    lock.py
    review_time.py
    manifest_update.py
    validate.py
  core/
    config.py
    errors.py
    hashing.py
    manifest.py
    paths.py
    provenance.py
    schemas.py
    time.py
  llm/
    openrouter_client.py
    cost.py
    logging.py
    prompts.py
  orchestrator/
    scheduler.py
    retry.py
    resume.py
    remote.py
    jobs.py
  paper/
    tables.py
    figures.py
    appendix.py
    latex_macros.py
  release/
    metadata.py
    visibility.py
    rescorer_package.py
  scorer/
    engine.py
    evidence_loader.py
    artifact_index.py
    unresolve.py
    native_mapping.py
    domain_rules/
      agentdojo.py
      appworld.py
      tau3_retail.py
      webarena_verified.py
  stats/
    envelopes.py
    bootstrap.py
    pairwise.py
    predictions.py
```

Representative fail-closed placeholder excerpt:

```python
from evidence_system.core.errors import BootstrapOnlyError

def score_records() -> None:
    raise BootstrapOnlyError("Formal scoring is not implemented in Step 2.")
```

Adapter boundary excerpt:

```python
@dataclass(frozen=True)
class AdapterSkeleton:
    canonical_domain_id: str
    contains_formal_runner_logic: bool = False
    can_emit_final_evidence_label: bool = False

def run_adapter() -> None:
    raise BootstrapOnlyError("Formal adapter execution is not implemented in Step 2.")
```

Canonical domain skeleton excerpt:

```python
CANONICAL_DOMAIN_IDS = (
    "agentdojo",
    "appworld",
    "webarena_verified",
    "tau3_retail",
    "androidworld",
    "workarena",
    "osworld_verified",
    "judge_only",
    "maintenance_update",
    "matched_budget_controls",
)
```

Risk points for GPT Pro:
- Confirm formal logic home is `src/evidence_system/`, not `scripts/`.
- Confirm Step 2 did not implement official benchmark adapters.
- Confirm Step 2 did not implement a scorer, freeze creator, aggregate metrics, or paper outputs.
- Confirm placeholder modules fail closed rather than silently returning formal-looking records.
- Confirm canonical domain IDs use canonical identifiers, not display names.

Mapping:
- Step 2: required package layout, including contracts, llm, adapters, scorer, orchestrator, audit, stats, paper, release.
- 0.6.1: formal logic boundary and package entry structure.
- 0.6.17: stats/paper/deployment/failure schema objects are present separately under `schemas/`; package modules do not replace schema objects with untyped dicts.

### 6. CLI Skeleton: `src/evidence_system/cli/`
Purpose: provide canonical, independently callable package CLI modules for plan/experiment responsibilities, while failing closed before later implementation steps.

Common CLI skeleton excerpt from `src/evidence_system/cli/_common.py`:

```python
@dataclass(frozen=True)
class BootstrapCommand:
    name: str
    responsibility: str
    owner_module: str

def build_bootstrap_parser(command: BootstrapCommand) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"python -m evidence_system.cli.{command.name}",
        description=command.responsibility,
    )
    parser.add_argument(
        "--bootstrap-check",
        action="store_true",
        help="Return command metadata without executing formal experiment logic.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser

def bootstrap_main(command: BootstrapCommand, argv: Sequence[str] | None = None) -> int:
    parser = build_bootstrap_parser(command)
    args = parser.parse_args(argv)
    payload = {
        **asdict(command),
        "status": "bootstrap_only" if args.bootstrap_check else "blocked",
        "formal_logic": "not_implemented_in_step_2",
        "side_effects": "none",
    }
    if args.bootstrap_check:
        emit(payload, args.json)
        return 0
    payload["reason"] = "Step 2 skeleton fails closed for formal actions."
    emit(payload, args.json)
    return 2
```

Example individual CLI module, `src/evidence_system/cli/deploy_all.py`:

```python
from evidence_system.cli._common import BootstrapCommand, run

COMMAND = BootstrapCommand(
    name="deploy_all",
    responsibility="Deploy all configured benchmark machines idempotently.",
    owner_module="evidence_system.orchestrator.remote",
)

if __name__ == "__main__":
    run(COMMAND)
```

`validate_config` is the one Step 2 command with real bootstrap behavior, but not formal schema validation:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_config",
        description="Read infra and agent configs without formal schema validation.",
    )
    add_config_args(parser)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = validate_config_files([args.infra_config, args.agents_config])
    except ConfigValidationError as exc:
        print(f"validate_config: {exc}", file=sys.stderr)
        return 1
    payload = summary.to_dict()
    ...
    return 0
```

CLI coverage table:

```text
Required command                         File
check_infra                              src/evidence_system/cli/check_infra.py
deploy_all                               src/evidence_system/cli/deploy_all.py
deploy_webarena                          src/evidence_system/cli/deploy_webarena.py
deploy_osworld                           src/evidence_system/cli/deploy_osworld.py
deploy_other_vps                         src/evidence_system/cli/deploy_other_vps.py
deploy_local_androidworld                src/evidence_system/cli/deploy_local_androidworld.py
monitor                                  src/evidence_system/cli/monitor.py
collect_results                          src/evidence_system/cli/collect_results.py
resume_failed                            src/evidence_system/cli/resume_failed.py
validate_config                          src/evidence_system/cli/validate_config.py
validate_manifest                        src/evidence_system/cli/validate_manifest.py
validate_contracts                       src/evidence_system/cli/validate_contracts.py
draft_contracts                          src/evidence_system/cli/draft_contracts.py
review_contracts                         src/evidence_system/cli/review_contracts.py
lock_contracts                           src/evidence_system/cli/lock_contracts.py
update_manifest_contract_locks           src/evidence_system/cli/update_manifest_contract_locks.py
freeze_predictions                       src/evidence_system/cli/freeze_predictions.py
run_preflight                            src/evidence_system/cli/run_preflight.py
run_full                                 src/evidence_system/cli/run_full.py
run_domain                               src/evidence_system/cli/run_domain.py
score_records                            src/evidence_system/cli/score_records.py
aggregate_results                        src/evidence_system/cli/aggregate_results.py
make_paper_outputs                       src/evidence_system/cli/make_paper_outputs.py
make_tables                              src/evidence_system/cli/make_tables.py
make_figures                             src/evidence_system/cli/make_figures.py
make_appendix                            src/evidence_system/cli/make_appendix.py
final_report                             src/evidence_system/cli/final_report.py
validate_results                         src/evidence_system/cli/validate_results.py
```

Additional lifecycle CLI skeletons present beyond the user's required list:

```text
aggregate
run_audit
run_rerun
make_release
```

Risk points for GPT Pro:
- Confirm all listed required CLI responsibilities are present as separate package modules.
- Confirm `deploy_*`, `monitor`, `collect_results`, and `resume_failed` are not hidden only inside `run_domain`.
- Confirm paper-output responsibilities are separately callable.
- Confirm formal actions default to blocked return code 2 unless `--bootstrap-check` is used.
- Confirm `validate_config` only reads checked-in config structure and does not validate formal schema or run infra.

Mapping:
- Step 2: CLI skeleton and `validate_config` acceptance test.
- 0.6.1: package CLI is canonical; scripts wrappers optional only.
- 0.6.17: future schema-backed validation is not bypassed by current CLI stubs.

### 7. Core Config And Schema Registry
Purpose: provide minimal bootstrap utilities for reading checked-in configs and checking required schema file presence. Formal validators are deferred to Step 3.

`src/evidence_system/core/config.py` behavior excerpt:

```python
@dataclass(frozen=True)
class ConfigReadResult:
    path: str
    sha256: str
    schema_version: str
    top_level_keys: list[str]

@dataclass(frozen=True)
class ConfigValidationSummary:
    status: str
    formal_schema_validation: str
    files: list[ConfigReadResult]

def validate_config_files(paths: list[str | Path]) -> ConfigValidationSummary:
    files = [read_config_file(path) for path in paths]
    return ConfigValidationSummary(
        status="ok",
        formal_schema_validation="not_implemented_in_step_2",
        files=files,
    )
```

`src/evidence_system/core/schemas.py` required file list excerpt:

```python
REQUIRED_SCHEMA_FILES = (
    "experiment_manifest.schema.json",
    "paper_mapping.schema.json",
    "job.schema.json",
    "agent_config.schema.json",
    "infra_config.schema.json",
    "raw_run.schema.json",
    "scored_record.schema.json",
    "infra_exclusion_record.schema.json",
    "failure_record.schema.json",
    "artifact_manifest.schema.json",
    "evidence_contract.schema.json",
    "contract_review.schema.json",
    "llm_call.schema.json",
    "human_review.schema.json",
    "human_time.schema.json",
    "audit_item.schema.json",
    "audit_label.schema.json",
    "rerun_record.schema.json",
    "stats_plan.schema.json",
    "bootstrap_plan.schema.json",
    "audit_sampling_plan.schema.json",
    "rerun_subset.schema.json",
    "aggregate_metrics.schema.json",
    "prediction_outcome.schema.json",
    "pairwise_matrix.schema.json",
    "denominator_audit.schema.json",
    "paper_output.schema.json",
    "freeze_manifest.schema.json",
    "deployment_manifest.schema.json",
    "release_artifact.schema.json",
)
```

Risk points for GPT Pro:
- Confirm "validation" wording is clearly limited: Step 2 reads configs but does not claim formal schema validation.
- Confirm the schema registry is a file-presence check, not a substitute for Step 3 validators.

Mapping:
- Step 2: `validate_config` can read `configs/infra.yaml` and `configs/agents.yaml`.
- 0.6.1: package utility lives under `src/evidence_system/core`.
- 0.6.17: required schema objects are enumerated explicitly and kept first-class.

### 8. Schema Directory: `schemas/`
Purpose: create first-class schema files required for later validated artifacts. These are Step 2 placeholders; formal JSON Schema content belongs to Step 3.

Schema file list:

```text
schemas/agent_config.schema.json
schemas/aggregate_metrics.schema.json
schemas/artifact_manifest.schema.json
schemas/audit_item.schema.json
schemas/audit_label.schema.json
schemas/audit_sampling_plan.schema.json
schemas/bootstrap_plan.schema.json
schemas/contract_review.schema.json
schemas/denominator_audit.schema.json
schemas/deployment_manifest.schema.json
schemas/evidence_contract.schema.json
schemas/experiment_manifest.schema.json
schemas/failure_record.schema.json
schemas/freeze_manifest.schema.json
schemas/human_review.schema.json
schemas/human_time.schema.json
schemas/infra_config.schema.json
schemas/infra_exclusion_record.schema.json
schemas/job.schema.json
schemas/llm_call.schema.json
schemas/pairwise_matrix.schema.json
schemas/paper_mapping.schema.json
schemas/paper_output.schema.json
schemas/prediction_outcome.schema.json
schemas/raw_run.schema.json
schemas/release_artifact.schema.json
schemas/rerun_record.schema.json
schemas/rerun_subset.schema.json
schemas/scored_record.schema.json
schemas/stats_plan.schema.json
```

Representative placeholder schema content:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "evidence_system/schemas/job.schema.json",
  "title": "Job Schema - Step 2 Placeholder",
  "description": "First-class schema file created in Step 2. Formal validation rules are implemented in Step 3.",
  "type": "object",
  "x-formal-validation": "not_implemented_in_step_2"
}
```

0.6.17 coverage table:

```text
0.6.17 category or named schema       Present Step 2 schema file(s)
experiment manifest                   experiment_manifest.schema.json
paper mapping                         paper_mapping.schema.json
job                                   job.schema.json
agent config                          agent_config.schema.json
infra config                          infra_config.schema.json
stats plan                            stats_plan.schema.json
bootstrap plan                        bootstrap_plan.schema.json
audit sampling plan                   audit_sampling_plan.schema.json
rerun subset                          rerun_subset.schema.json
aggregate metrics                     aggregate_metrics.schema.json
prediction outcome                    prediction_outcome.schema.json
pairwise matrix                       pairwise_matrix.schema.json
paper output                          paper_output.schema.json
denominator audit                     denominator_audit.schema.json
failure record                        failure_record.schema.json
deployment manifest                   deployment_manifest.schema.json

Additional first-class result/provenance schemas:
raw_run.schema.json
scored_record.schema.json
infra_exclusion_record.schema.json
artifact_manifest.schema.json
evidence_contract.schema.json
contract_review.schema.json
llm_call.schema.json
human_review.schema.json
human_time.schema.json
audit_item.schema.json
audit_label.schema.json
rerun_record.schema.json
freeze_manifest.schema.json
release_artifact.schema.json
```

Risk points for GPT Pro:
- Confirm every 0.6.17 minimum schema is present.
- Confirm manifest/job/config/stats/bootstrap/audit/rerun/aggregate/pairwise/paper/deployment/failure schemas are represented.
- Confirm placeholder schemas cannot be mistaken for formal validators; Step 3 must replace them with real rules.

Mapping:
- Step 2: required `schemas/` directory and named schema files.
- 0.6.1: no CLI bypasses these future schema objects.
- 0.6.17: first-class schema coverage.

### 9. Tests Directory: `tests/`
Purpose: establish test entry and bootstrap gates for Step 2 structure.

Tree excerpt:

```text
tests/unit/test_step02_bootstrap.py
tests/integration/.gitkeep
tests/e2e/.gitkeep
tests/fixtures/.gitkeep
```

Test content excerpt:

```python
REQUIRED_DIRS = [
    "src/evidence_system",
    "src/evidence_system/cli",
    "src/evidence_system/contracts",
    "src/evidence_system/llm",
    "src/evidence_system/adapters",
    "src/evidence_system/orchestrator",
    "src/evidence_system/audit",
    "src/evidence_system/stats",
    "src/evidence_system/paper",
    "src/evidence_system/release",
    "tests",
    "schemas",
    "reviews/packets",
    "reviews/gpt_pro",
]

CANONICAL_CLI_MODULES = [
    "validate_config",
    "validate_manifest",
    "check_infra",
    "deploy_all",
    "deploy_webarena",
    "deploy_osworld",
    "deploy_other_vps",
    "deploy_local_androidworld",
    "monitor",
    "collect_results",
    "resume_failed",
    "validate_contracts",
    "draft_contracts",
    "review_contracts",
    "lock_contracts",
    "update_manifest_contract_locks",
    "freeze_predictions",
    "run_preflight",
    "run_full",
    "run_domain",
    "score_records",
    "aggregate_results",
    "aggregate",
    "run_audit",
    "run_rerun",
    "make_paper_outputs",
    "make_tables",
    "make_figures",
    "make_appendix",
    "final_report",
    "validate_results",
    "make_release",
]
```

Further test excerpts:

```python
def test_canonical_cli_modules_exist_and_bootstrap_check() -> None:
    for module_name in CANONICAL_CLI_MODULES:
        importlib.import_module(f"evidence_system.cli.{module_name}")
        if module_name == "validate_config":
            continue
        result = subprocess.run(
            [sys.executable, "-m", f"evidence_system.cli.{module_name}",
             "--bootstrap-check", "--json"],
            ...
        )
        assert result.returncode == 0
        assert '"formal_logic": "not_implemented_in_step_2"' in result.stdout

def test_formal_actions_fail_closed_by_default() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evidence_system.cli.check_infra", "--json"],
        ...
    )
    assert result.returncode == 2
    assert '"status": "blocked"' in result.stdout

def test_no_script_wrappers_with_unique_logic() -> None:
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return
    for path in scripts_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "evidence_system.cli" in text, path

def test_env_example_contains_no_secret_values() -> None:
    ...
    assert value.strip() in {"", "configs", "results"}, line

def test_new_src_contains_no_legacy_formal_scaffold_markers() -> None:
    forbidden_fragments = ["mock" + "_result", "old runner scaffold"]
    for path in (ROOT / "src").rglob("*.py"):
        ...
        assert fragment not in text, path
```

Self-check result:

```text
.venv/bin/python -m pytest
9 passed in 1.03s
```

Risk points for GPT Pro:
- Confirm tests cover required Step 2 structure, pyproject parseability, schema presence, config read, CLI skeletons, fail-closed behavior, script wrapper policy, secret-free `.env.example`, and old scaffold markers.
- Confirm tests are bootstrap tests only; they do not validate formal schema semantics or run experiments.

Mapping:
- Step 2: `python -m pytest` can run; test directories exist.
- 0.6.1: tests enforce CLI module presence and script-wrapper policy.
- 0.6.17: tests enforce schema file presence.

### 10. Reviews Directory: `reviews/packets/` And `reviews/gpt_pro/`
Purpose: maintain the GPT Pro review packet and review output workflow required by `工程文件说明.md` 0.4.

Tree excerpt:

```text
reviews/
  gpt_pro/
    step01_spec_freeze_review.md
  packets/
    step01_spec_freeze_review_packet.md
    step02_repo_bootstrap_review_packet.md
```

Step 1 review excerpt:

```text
# GPT Pro Review: Step 1

## Blocking Issues
未发现需要阻断 Step 2 的 Step 1 spec gap.

## Decision
ALLOW_NEXT_STEP
```

Step 1 spec freeze manifest excerpt:

```json
{
  "schema_version": "spec_freeze/v1",
  "manifest_type": "step1_spec_freeze_gate",
  "SPEC_FROZEN": true,
  "manual_confirmation": "SPEC_FROZEN=true",
  "gate_status": "ALLOW_NEXT_STEP",
  "gpt_pro_review": {
    "path": "reviews/gpt_pro/step01_spec_freeze_review.md",
    "decision": "ALLOW_NEXT_STEP",
    "blocking_issues_empty": true
  },
  "docs_hash": "8490e999c28d241a12b405b9793ea997b5d754ffc8afa51f556d8362962e7101",
  "paper_mapping_hash": "678f35e422b16a6a250d4eb7e364b9ff2a1c34dfe3fe5daa4d177fd8ec3adca9",
  "source_documents_hash": "71dc1ab6e0660908dbf4240a51bc91d22de99e2921613ba7d5d42207f59cd776"
}
```

Risk points for GPT Pro:
- Confirm Step 2 preconditions are recorded: Step 1 GPT Pro review exists, Decision is ALLOW_NEXT_STEP, Blocking Issues are empty, SPEC_FROZEN=true, and spec_freeze manifest records docs/paper/source hashes.
- Confirm Step 2 packet exists under the standard path.
- Confirm there is not yet a Step 2 GPT Pro review; that is GPT Pro's expected output after reviewing this packet.

Mapping:
- Step 2: review packet generated.
- 0.4: fixed packet structure and GPT Pro review workflow.
- Additional fail-closed gate: Step 2+ progression requires SPEC_FROZEN and hashes.

### 11. `scripts/` Thin-Wrapper Policy
Purpose: show that Step 2 does not create script-only formal logic.

Current status:

```text
scripts/ directory status: absent.
No scripts/*.py files were created in Step 2.
```

Policy enforced by tests if scripts are later added:

```python
def test_no_script_wrappers_with_unique_logic() -> None:
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return
    for path in scripts_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "evidence_system.cli" in text, path
```

Risk points for GPT Pro:
- Confirm absence of `scripts/` is acceptable under Step 2 because scripts are optional.
- Confirm no formal responsibility exists only in `scripts/`.
- Confirm future wrappers would need to delegate to package CLI.

Mapping:
- Step 2: scripts optional thin wrappers only.
- 0.6.1: package CLI is canonical; scripts cannot contain unique formal logic.
- 0.6.17: no schema responsibility is hidden in scripts.

### 12. Explicit Non-Implementation Evidence
Purpose: identify high-risk places where Step 2 must not overreach.

Formal action fail-closed output shape:

```json
{
  "formal_logic": "not_implemented_in_step_2",
  "name": "check_infra",
  "owner_module": "evidence_system.orchestrator.remote",
  "responsibility": "Check infrastructure readiness without running formal experiments.",
  "side_effects": "none",
  "status": "bootstrap_only"
}
```

Default formal action behavior:

```text
python -m evidence_system.cli.check_infra --json
returns code 2 and status "blocked".
```

Formal logic explicitly absent in Step 2:

```text
No official benchmark adapter logic.
No scorer verdict logic.
No native evaluator mapping logic.
No contract drafting/review/lock/update logic.
No prediction freeze creation.
No preflight/full formal run execution.
No formal scored records.
No aggregate metrics.
No paper tables/figures/appendix/final report generation.
No release package generation.
No OpenRouter network calls.
No cost computation.
No raw artifact writing.
No formal results/manifests/pre_scoring_freeze.json.
```

Risk points for GPT Pro:
- Confirm the use of the word "placeholder" is explained and constrained: it means a first-class Step 2 path or fail-closed module, not a formal implementation.
- Confirm no placeholder produces formal data.
- Confirm no `mock_result` or dry-run output is used as formal experiment logic.

Mapping:
- Step 2: bootstrap only.
- 0.6.1: formal logic belongs in package modules once implemented, but current modules are fail-closed.
- 0.6.17: schema placeholders are first-class objects but not validators.

## Contract With The Paper
Step 2 supports the paper/plan/experiment protocol by creating the engineering surface required before formal schemas, contracts, scoring, and experiments can exist.

Alignment points:

- Formal-code boundary: all package code is under `src/evidence_system/`; no formal logic exists only in `scripts/`.
- Canonical package CLI: required commands are present as `python -m evidence_system.cli.<command>` modules and independently callable in bootstrap-check mode.
- CLI scope: deployment, infra check, monitoring, collection, resume, config/manifest/contract validation, contract lifecycle, prediction freeze, preflight/full/domain runs, scoring, aggregation, paper outputs, appendix, final report, and result validation all have package module entry points.
- Fail-closed behavior: commands that would run or mutate formal experiments are blocked by default in Step 2.
- First-class schema objects: manifest, job, config, stats, bootstrap, audit, rerun, aggregate, pairwise, paper, deployment, failure, and related result/provenance schema files exist under `schemas/`.
- Secret handling: `.env.example` contains env var names only; `.gitignore` excludes real env files, private keys, raw artifacts, raw runs, private logs, and large formal result directories.
- Preserved dependencies: existing paper, docs, configs, experiments, and preserved `results/outputs` dependencies are retained; Step 2 does not delete or rewrite them.
- Step 1 gate: Step 1 GPT Pro review and spec freeze manifest are recorded before this Step 2 work.

## Known Non-Goals
Step 2 intentionally does not do the following:

- No formal JSON/YAML schema rules or validators.
- No formal adapter implementation for any domain.
- No official benchmark runner invocation.
- No scorer, evidence verdict, native evaluator mapping, or raw artifact decisive-evidence logic.
- No evidence contract draft/review/lock/update implementation.
- No OpenRouter client, API call, model config resolution, cost computation, or LLM logging implementation.
- No scheduler, retry/resume policy, remote deployment, monitor, or collection implementation.
- No prediction freeze creation or pre-scoring freeze file.
- No preflight/full/rerun/audit formal run.
- No formal scored records, aggregate metrics, bootstrap intervals, pairwise outputs, paper tables, figures, appendix, final report, release package, or rescorer package.
- No `scripts/*.py` wrappers.
- No Step 3 schema work.

## Risk Checklist
High-risk checks GPT Pro should apply:

- Formal logic location: any formal logic outside `src/evidence_system/` should block.
- Script boundary: any `scripts/*.py` file with unique logic should block. Current status is no `scripts/` directory.
- CLI completeness: missing any required CLI skeleton from the requested list should block.
- CLI independence: required commands must be separate package modules, not only hidden behind another command.
- Fail-closed behavior: formal commands must not run by default in Step 2.
- Schema coverage: missing manifest/job/config/stats/bootstrap/audit/rerun/aggregate/pairwise/paper/deployment/failure schema files should block.
- Placeholder clarity: placeholder schema files and modules must be clearly non-formal and Step 3/later-owned.
- Secret handling: `.env.example` must not contain real keys; `.gitignore` must exclude `.env`, secret files, private keys, raw artifacts, raw runs, private logs, and large formal results.
- Old scaffold/mock/dry-run: Step 2 must not introduce old scaffold, `mock_result`, or dry-run formal logic.
- Boundary: Step 2 must not implement formal adapter, scorer, freeze, scoring, aggregation, paper-output, or release logic.
- Preconditions: Step 1 review must exist, allow next step, have empty blocking issues, and `results/manifests/spec_freeze.json` must record `SPEC_FROZEN=true` plus docs/paper/source hashes.

## Questions For GPT Pro
1. Is this Step 2 repo skeleton sufficient for Step 3 schema/provenance/validator work without further structure changes?
2. Does the packet show enough file content and tree excerpts for a self-contained web review?
3. Does all formal-code scaffolding live under `src/evidence_system/`?
4. Are `scripts/*.py` absent or constrained to thin wrappers if later created?
5. Does the CLI skeleton cover all required commands: `check_infra`, `deploy_all`, `deploy_webarena`, `deploy_osworld`, `deploy_other_vps`, `deploy_local_androidworld`, `monitor`, `collect_results`, `resume_failed`, `validate_config`, `validate_manifest`, `validate_contracts`, `draft_contracts`, `review_contracts`, `lock_contracts`, `update_manifest_contract_locks`, `freeze_predictions`, `run_preflight`, `run_full`, `run_domain`, `score_records`, `aggregate_results`, `make_paper_outputs`, `make_tables`, `make_figures`, `make_appendix`, `final_report`, and `validate_results`?
6. Are schema files present for manifest/job/config/stats/bootstrap/audit/rerun/aggregate/pairwise/paper/deployment/failure artifacts?
7. Are `.gitignore` and `.env.example` sufficient to avoid secret/raw artifact/raw run/large formal result leakage?
8. Is the placeholder/fail-closed behavior appropriate, or does any placeholder risk being mistaken for formal logic?
9. Are the Step 1 preconditions sufficiently recorded for Step 2 review?

## Acceptance Criteria
GPT Pro should allow Step 3 only if all criteria below are satisfied:

- Fixed packet structure is present and self-contained.
- `pyproject.toml`, `README.md`, `.gitignore`, and `.env.example` are represented with enough content to review.
- `src/evidence_system/` package layout is represented and includes `cli`, `core`, `contracts`, `llm`, `adapters`, `scorer`, `orchestrator`, `audit`, `stats`, `paper`, and `release`.
- Required CLI skeleton modules are present and independently callable.
- `validate_config` reads `configs/infra.yaml` and `configs/agents.yaml` but does not claim formal schema validation.
- `scripts/` is absent, or any future `scripts/*.py` would be thin wrappers only.
- `schemas/` contains the required first-class schema file names, including all 0.6.17 minimum schemas.
- Test structure exists and Step 2 tests pass.
- `.gitignore` excludes `.env`, `.env.*`, secret files, private keys, raw artifacts, raw runs, private logs, and large formal results.
- `.env.example` contains no real API key, SSH private key, token, or credential value.
- Step 2 did not introduce old scaffold, `mock_result`, dry-run formal logic, formal adapter/scorer/freeze/scoring/aggregation/paper-output logic, or formal results.
- Step 2 preconditions are recorded: Step 1 GPT Pro review exists, Decision is `ALLOW_NEXT_STEP`, Blocking Issues are empty, `SPEC_FROZEN=true`, and `spec_freeze.json` records docs hash, paper_mapping hash, and source document hashes.
- Blocking Issues must be empty and Decision must be `ALLOW_NEXT_STEP` before proceeding to Step 3.
