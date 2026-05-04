# GPT Pro Review: Step 2

审查对象：`step02_repo_bootstrap_review_packet.md`

## Blocking Issues

None.

## Non-Blocking Issues

1. packet 中 `docs/`、paper、configs、experiments 是以 preserved dependencies 的方式说明，而不是在 Step 2 created/changed tree 中重新列出。考虑到 Step 2 是 bootstrap，不要求重建这些文件；且 Step 1 freeze manifest 已记录 source document hashes，因此不构成 blocking issue。

2. schema 文件当前只是 placeholders。这符合 Step 2，但 Step 3 必须将这些 placeholder schema 替换为真实 JSON Schema validation rules，并确保 CLI validation 不再只做 presence/read checks。

## Alignment Evidence

Step 2 review packet 自包含，覆盖了 repo/bootstrap 所需的根文件、package layout、schema 文件、CLI skeleton、测试入口、fail-closed 边界、secrets/raw results 排除策略，以及 Step 1 spec freeze 前置条件。

根据 packet 内容，Step 2 的实现保持在 bootstrap skeleton 范围内，没有把正式实验逻辑、旧 scaffold、`mock_result` 或 dry-run formal output 重新引入。当前结构足以进入 Step 3 的 schema/provenance/validator 实现阶段。

### 1. 目录结构是否匹配 Step 1 spec

通过。

packet 显示已建立：

* `src/evidence_system/`
* `schemas/`
* `tests/unit/`
* `tests/integration/`
* `tests/e2e/`
* `tests/fixtures/`
* `reviews/packets/`
* `reviews/gpt_pro/`

并且 `src/evidence_system/` 下包含 required package modules：

* `cli`
* `core`
* `contracts`
* `llm`
* `adapters`
* `scorer`
* `orchestrator`
* `audit`
* `stats`
* `paper`
* `release`

`docs/`、paper、configs、experiments 等既有协议/论文依赖在 packet 中被声明为 preserved，而不是被 Step 2 重写或删除。该点满足 Step 2 bootstrap 审查目标。

### 2. package / CLI skeleton 是否清晰

通过。

canonical entry points 使用：

```text
python -m evidence_system.cli.<command>
```

所有正式入口均位于 `src/evidence_system/cli/`，没有依赖 script-only entry point。CLI skeleton 使用统一 bootstrap command pattern，并区分：

* `--bootstrap-check`：返回 bootstrap metadata，退出码 0
* 默认正式动作：fail closed，退出码 2

这符合 Step 2 “只建立 skeleton，不执行正式实验逻辑”的边界。

### 3. `.gitignore` 是否防止 secrets / raw formal results 泄露

通过。

packet 中 `.gitignore` 覆盖了关键排除项：

```text
.env
.env.*
!.env.example
secrets/*
*.pem
*.key
id_rsa*
id_ed25519*
results/raw/
results/raw_runs/
results/raw_artifacts/
results/artifacts/
results/formal/
results/full/
results/logs/
results/private_logs/
results/private_llm_logs/
*.log
*.private.log
```

这满足 Step 2 对 `.env`、`.env.*`、raw runs、raw artifacts、private SSH keys、private prompt/API logs、large formal results 的排除要求。

`.env.example` 只包含空值或非敏感默认路径，没有真实 key、token、host password 或 private key 内容。

### 4. 是否保留论文和实验协议文件

通过。

packet 明确记录 Step 1 precondition：

```text
SPEC_FROZEN: true
manual_confirmation: "SPEC_FROZEN=true"
```

并记录了 source documents hash，source documents 包含：

```text
revised_agent_benchmark_paper.tex
计划.md
实验说明.md
工程文件说明.md
```

同时 packet 声明 existing paper、docs、configs、experiments、preserved result-output dependencies remain in place。未发现 Step 2 删除、重写或替换论文/实验协议文件的证据。

### 5. package CLI 是否完整覆盖 check / deploy / monitor / collect / resume / paper / final-report 职责

通过。

packet 中 required canonical CLI mapping 已覆盖：

```text
check_infra
deploy_all
deploy_webarena
deploy_osworld
deploy_other_vps
deploy_local_androidworld
monitor
collect_results
resume_failed
make_tables
make_figures
make_appendix
final_report
```

同时额外覆盖了后续 lifecycle / experiment / validation entry points：

```text
validate_config
validate_manifest
validate_contracts
draft_contracts
review_contracts
lock_contracts
update_manifest_contract_locks
freeze_predictions
run_preflight
run_full
run_domain
score_records
aggregate_results
make_paper_outputs
validate_results
aggregate
run_audit
run_rerun
make_release
```

关键点是：`deploy_*`、`monitor`、`collect_results`、`resume_failed` 均是独立 package CLI module，没有只隐藏在 `run_domain` 中；paper-output responsibilities 也可单独调用。

### 6. 是否没有实现越界逻辑

通过。

packet 明确显示 Step 2 只做 fail-closed placeholders：

```python
raise BootstrapOnlyError("Formal scoring is not implemented in Step 2.")
```

并明确排除：

```text
No official benchmark adapter logic.
No scorer verdict logic.
No native evaluator mapping logic.
No contract drafting/review/lock/update logic.
No prediction freeze creation.
No preflight/full formal run execution.
No aggregate metrics.
No paper tables/figures/appendix/final report generation.
No release package generation.
No OpenRouter network calls.
No raw artifact writing.
```

`validate_config` 是唯一具有 real bootstrap behavior 的 CLI，但其行为被限定为读取 `configs/infra.yaml` 和 `configs/agents.yaml`，并明确标记：

```text
formal_schema_validation="not_implemented_in_step_2"
```

这没有越界到 Step 3 schema validation 或 formal experiment execution。

### 7. first-class schema 文件是否覆盖最低要求

通过。

packet 中 `schemas/` 覆盖了 0.6.17 minimum schema files：

```text
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
```

并额外包含 raw run、scored record、artifact manifest、evidence contract、human review/time、audit label/item、freeze manifest、release artifact 等后续 provenance/result schema placeholders。

这些 schema 文件被清楚标记为 Step 2 placeholders，不声称已经具备 formal validation rules，因此没有替代 Step 3 的风险。

### 8. tests / bootstrap acceptance 是否满足

通过。

packet 显示测试入口存在：

```text
python -m pytest
```

并记录 self-check：

```text
9 passed in 1.03s
```

测试覆盖：

* required dirs
* pyproject parseability
* schema presence
* config read
* canonical CLI module presence
* `--bootstrap-check`
* default fail-closed behavior
* scripts wrapper policy
* `.env.example` no secret values
* no old scaffold / mock markers

这符合 Step 2 bootstrap acceptance test 范围。

### 9. old scaffold / mock / dry-run formal logic 是否重新引入

通过。

packet 声明：

```text
No scripts/*.py files were created in Step 2.
scripts/ directory status: absent.
```

并通过测试禁止 source 中出现旧 scaffold / `mock_result` markers。当前没有 evidence 表明旧 scaffold、`mock_result`、dry-run output 被当作正式实验逻辑引入。

## Required Fixes

None.

## Decision

ALLOW_NEXT_STEP
