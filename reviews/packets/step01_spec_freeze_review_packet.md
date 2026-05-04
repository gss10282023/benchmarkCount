# Review Packet: Step 01

## Review Goal

请 GPT Pro 审查 Step 1 Spec Freeze 是否足以作为后续 Step 2-12 的冻结依据。本 packet 自包含，不要求 GPT Pro 访问本地文件。

本次重点审查：

- Step 1 是否只冻结 specification，没有进入正式实现。
- P0/P1/P2/P3 完整 scope 是否写清，declared appendix / diagnostic 缺失是否会 block paper outputs。
- adapter/scorer boundary 是否足够硬：adapter 只保存 raw evidence，scorer 才能产出 final SUCCESS/FAIL/UNRESOLVE。
- evidence contract lifecycle、prediction freeze、deterministic selection、official split exception、post-lock clarification 是否符合论文和计划。
- result/artifact/LLM/human-time/audit/release/paper-output 规则是否足以阻止后续实现偷看、补造、误计 denominator 或污染论文输出。

## Strict Sources Used

### Source 1: `revised_agent_benchmark_paper.tex`

Evidence contract:

```text
Each case unit carries a predeclared evidence contract. The contract states:
(i) the native benchmark claim; (ii) the official source of that claim, such as
the task text, evaluator code, policy, or schema; (iii) the artifacts required
to decide success or fail; (iv) the rule for assigning UNRESOLVE; and
(v) whether the claim is native-aligned or a stronger measurement claim.
```

Source hierarchy and stronger measurement:

```text
When sources differ, the contract follows a fixed source hierarchy: official
evaluator semantics first; official task text and policy second; and schema
constraints needed to interpret evaluator-visible state third. We do not add
requirements from annotator intuition alone. Any requirement not grounded in one
of these sources is labeled as a stronger measurement claim and excluded from
the native-aligned main envelope.
```

Drafter visibility:

```text
The drafter receives the task, benchmark specification, evaluator semantics,
database or API schema, and trace format. It does not receive agent identities,
agent traces, native scores, or any outcome labels.
```

Counting and denominator:

```text
The rule assigns every completed record to exactly one of three observable
categories: counted-SUCCESS, counted-FAIL, or UNRESOLVE. Execution failures are
not merged into the UNRESOLVE label. Only infrastructure or pre-run failures
that prevent normal benchmark execution are excluded from the completed-record
denominator.
```

Envelope formulas:

```text
N = S + F + U
CountedScore = S / (S + F), when S + F > 0
LB = S / N
UB = (S + U) / N
Width = U / N
Coverage = (S + F) / N
```

Main study scale:

```text
The manifest selects 100 eligible case units per domain using a deterministic,
predeclared hash order after excluding smoke-test cases. With four agents this
gives 1600 record slots. Because each AgentDojo record runs a benign and an
injected arm, the main study stores 2000 execution episodes. If a domain has
fewer than 100 eligible verified cases under the official split, the manifest
uses all eligible cases and records the exception before main scoring.
```

Agent interpretation:

```text
The main study uses four fixed agents, Agent A, Agent B, Agent C, and Agent D,
selected before scoring as non-redundant measurement probes spanning source
openness, scale, and tool-use style. Four probes cannot exhaust a factorial
design; they are not meant to be a leaderboard.
```

Prediction freeze:

```text
To make the main claim falsifiable, we register predictions before scoring any
record. Predictions are stored verbatim in the manifest and are not edited
after the first scoring run.
```

Audit and rerun:

```text
We rerun Agent A on ten case units per domain, giving 40 rerun case units and
50 rerun episodes because AgentDojo reruns paired arms.

We audit 100 main-study records, 25 per domain. Within each domain, the sample
is stratified into counted records, records labeled UNRESOLVE, and records
where native reporting and evidence reporting disagree whenever all three
buckets exist.
```

### Source 2: `计划.md`

Key constraints used:

```text
Evidence contract 制定与锁定是 scoring 前 blocker。
Native-aligned / minimality / source hierarchy 变成 validator gate。
COUNTED_ONLY_SCORE 只在 SUCCESS + FAIL > 0 时定义。
P1--P4 必须按 95% case-cluster bootstrap interval 的 supported / falsified /
inconclusive 三态规则判定，不能只看 point estimate。
fig:hero panel (b) 只画四个 main-domain rows。
tab:cost 只报告 trained annotator wall-clock minutes；不包含 benchmark
execution compute、VPS runtime 或 LLM inference compute。
Post-lock clarification sensitivity report 只用于 locked contract 澄清，不作为新增常规 appendix 实验。
```

### Source 3: `实验说明.md`

Key constraints used:

```text
如果某个 case unit 没有 locked native-aligned evidence contract，就不能进入论文主实验计分。

每个 completed record 最终只能进入三类之一：
counted-SUCCESS
counted-FAIL
UNRESOLVE

COUNTED_ONLY_SCORE = SUCCESS / (SUCCESS + FAIL), only if SUCCESS + FAIL > 0

主实验规模是：
4 个 main domains
每个 domain 100 case units
4 个固定 agents
每个 domain 400 records
总计 1600 completed-record slots
AgentDojo paired arms 使 main study 总共 2000 stored execution episodes

Post-lock clarification sensitivity 只在 locked contract 后确实需要澄清时生成 versioned report；
它不是常规新增 appendix 实验，也不能替代 main native-aligned result。
```

### Source 4: `工程文件说明.md`

Step 1 and review packet requirements:

```text
Step 1 | Spec Freeze | Codex 起草 + GPT Pro 审查

review packet 必须自包含，不得依赖 GPT Pro 能访问本地路径。

Step 1 packet 必须包含论文、计划.md、实验说明.md、工程文件说明.md 中与 evidence
contract、counting、UNRESOLVE、freeze、logging、adapter/scorer boundary、acceptance
tests 相关的摘录。
```

High-risk Step 1 requirements:

```text
正式逻辑必须放在 src/evidence_system/；scripts/*.py 如存在只能是 thin wrappers。
不得在工程说明、spec、scorer、runner 或测试中硬编码 Agent A-D、contract_drafter、
judge_only 的 model ID、version pin、temperature、prompt version 或 prompt hash。

所有 schema、scorer、golden tests、audit、tables、figures 和 final report 必须使用
同一套 R1-R7 taxonomy。

status == INFRA_EXCLUDED 时 evidence_label 必须为空，不进入 evidence envelope
denominator，但必须保留在 denominator audit 中。

Native evaluator evidence 只有同时满足 locked contract artifact mapping、artifact manifest
path/sha256、official runner/evaluator provenance、direct artifact/verified object read 才能 decisive。

Default P0 main selection is 100 case units per main domain: 10 preflight + 90 full.
If an official verified split has fewer than 100 eligible case units, the exception must be
recorded in the frozen manifest before scoring.

Step 5 开发阶段不得生成正式 results/manifests/pre_scoring_freeze.json。
```

## Files Created Or Changed

Step 1 created these specification files:

- `docs/system_spec.md`
- `docs/experiment_lifecycle.md`
- `docs/adapter_interface.md`
- `docs/auxiliary_adapters.md`
- `docs/scorer_spec.md`
- `docs/result_schema.md`
- `docs/artifact_schema.md`
- `docs/llm_logging_and_cost.md`
- `docs/human_time_and_cost.md`
- `docs/human_review_time.md`
- `docs/audit_rerun_spec.md`
- `docs/release_and_rescorer.md`
- `docs/vps_runtime_spec.md`
- `docs/acceptance_tests.md`

This revision updates Step 1 spec docs to address GPT Pro blocking issues:

- `docs/system_spec.md`
- `docs/experiment_lifecycle.md`
- `docs/adapter_interface.md`
- `docs/scorer_spec.md`
- `docs/result_schema.md`
- `docs/llm_logging_and_cost.md`
- `docs/human_review_time.md`
- `docs/audit_rerun_spec.md`
- `docs/acceptance_tests.md`
- `reviews/packets/step01_spec_freeze_review_packet.md`

Step 1 did not create or modify formal implementation code, formal validators, formal runner/adapters, scorer code, formal `pre_scoring_freeze.json`, scored records, aggregate metrics, tables, figures, appendix data, or final paper outputs.

## Content For Review

### 1. `docs/system_spec.md`

Purpose:

```text
This file freezes system-wide scope, canonical identifiers, phase/experiment_type/priority,
record terminology, canonical CLI responsibilities, model/config rules, schema coverage,
paper mapping coverage, strict gates, and confirmation items.
```

Key excerpts:

```text
The complete system scope is P0/P1/P2/P3:

- P0: four main domains, locked native-aligned evidence contracts, prediction freeze,
  evidence-envelope scoring, main tables, and main figures.
- P1: denominator audit, case-cluster bootstrap, pairwise ranking and margins, top UNRESOLVE
  reasons, rerun subset, blinded audit, and per-agent envelopes.
- P2: AndroidWorld, WorkArena, OSWorld-Verified appendix stress test, contract metadata,
  human-time cost, release metadata, formal definitions / rescorer interface, and result macro contract.
- P3: judge-only diagnostic, maintenance update, matched-budget controls, and qualitative case cards.

If any declared appendix or diagnostic is missing, paper outputs must be blocked unless the
paper text and experiments/experiment_manifest.yaml are updated together.
```

```text
Old scaffold, mock_result, and dry-run output are not formal experiment logic. They may be
used only for engineering self-checks and synthetic fixtures. Formal logic must live under
src/evidence_system/. Any scripts/*.py files are thin wrappers around package CLIs and cannot
contain unique formal logic.
```

```text
All manifest IDs, job IDs, raw/scored result directories, adapter module names, aggregation
keys, hash inputs, release metadata, and paper mappings use canonical domain identifiers.
Display names are presentation fields only.

agentdojo -> AgentDojo
appworld -> AppWorld
webarena_verified -> WebArena-Verified
tau3_retail -> tau3-bench retail
androidworld -> AndroidWorld
workarena -> WorkArena
osworld_verified -> OSWorld-Verified
judge_only -> judge-only
maintenance_update -> maintenance update
matched_budget_controls -> matched-budget controls
```

```text
Every job, raw run record, scored record, failure record, metric artifact, and paper-output
source record must distinguish:

phase: smoke | dry_run | preflight | full | rerun
experiment_type: main | appendix | diagnostic | audit | maintenance_update | matched_budget_control
priority: P0 | P1 | P2 | P3

phase=smoke and phase=dry_run are engineering-only phases and cannot enter the formal evidence envelope.
```

```text
P0 planned record slots are fixed at 1600: 4 main domains x 100 case units x 4 agents.
If the frozen paper or manifest requires 1600 completed_records strictly, recoverable infra
exclusions must be retried until completed, or the run is P0-incomplete. If infra exclusions
remain after the allowed retry policy, the main envelope N uses completed scored records only,
while the denominator audit reports attempted=1600, completed, infra_excluded,
agent_caused_failures, and formally blocked slots.
```

```text
Package CLI is the canonical formal entry. Wrapper scripts, if retained, call these commands:
python -m evidence_system.cli.check_infra
python -m evidence_system.cli.deploy_all
python -m evidence_system.cli.deploy_webarena
python -m evidence_system.cli.deploy_osworld
python -m evidence_system.cli.deploy_other_vps
python -m evidence_system.cli.deploy_local_androidworld
python -m evidence_system.cli.monitor
python -m evidence_system.cli.collect_results
python -m evidence_system.cli.resume_failed
python -m evidence_system.cli.make_tables
python -m evidence_system.cli.make_figures
python -m evidence_system.cli.make_appendix
python -m evidence_system.cli.final_report
```

```text
Agent A-D, contract_drafter, and judge_only model IDs, version pins, temperatures, prompt
versions, prompt hashes, provider fields, retry settings, and API-key environment variable names
must not be hardcoded in code, tests, docs-as-data, runner logic, scorer logic, or paper generation.
Formal code reads them from configs/agents.yaml and the locked manifest. If the two disagree or
a value is missing for a formal run, the system fails closed.

The paper interpretation is frozen: Agent A-D are non-redundant measurement probes used to test
whether evidence uncertainty is structured by domain, not leaderboard entries and not a factorial
model comparison. Concrete model identifiers, version pins, temperatures, provider settings,
prompt versions, and prompt hashes are config/locked-manifest data only.

Static gates must scan code, tests, runner logic, scorer logic, paper generation, and review
packets for hardcoded Agent A-D, contract_drafter, or judge_only concrete model ids, version pins,
temperatures, prompt hashes, prompt versions, and API-key environment variable values. Such values
fail unless they appear inside an explicitly synthetic config fixture that cannot be used by
formal runs.
```

```text
Confirmation items include:
Agent A-D concrete model version pins: 需要从 locked manifest 确认.
Agent A-D full probe rationale fields: 需要从 locked manifest 确认.
Contract drafter model/version/temperature/prompt version/prompt hash: 需要从 locked manifest 确认.
Judge-only model/version/temperature/prompt version/prompt hash: 需要从 locked manifest 确认.
pairwise_equality_tolerance until set in the frozen stats plan: 需要从 locked manifest 确认.
```

```text
Step 1 checked experiments/paper_mapping.md against the required label list. The mapping covers:
tab:views, tab:unresolve-taxonomy, tab:domains, tab:main-results-A, tab:denominator-audit,
tab:main-results-B, tab:prediction-outcomes, tab:main-results-C, tab:pairwise-margins,
tab:top-unresolve-reasons, tab:audit-rerun, tab:per-agent, tab:cost,
tab:contract-drafting-metadata, tab:update, fig:hero, fig:evidence-counting, fig:case-cards,
app:per-agent, app:cost, app:contract-drafting-details, app:aux-domains, app:osworld,
app:judge, app:update, app:release, Formal Definitions, and app:macro-contract.
```

Risks GPT Pro should inspect:

- Does the scope wording prevent dropping P2/P3 appendix or diagnostics without paper/manifest edits?
- Does canonical domain language prevent display names from entering hash/aggregation keys?
- Does the 1600 planned record_slots rule correctly distinguish completed denominator from denominator audit?
- Does the CLI mapping cover all plan/experiment responsibilities?
- Does the model/config rule ban hardcoding enough to cover tests and paper-generation code?

Source correspondence:

- Paper: main study size, Agent A-D as probes, deterministic manifest, appendix sections.
- `计划.md`: P0/P1/P2/P3 priority definitions and paper label mapping.
- `实验说明.md`: P0 1600 slots / 2000 episodes, appendix completion requirement.
- `工程文件说明.md`: canonical identifiers, CLI mapping, model hardcoding ban, paper mapping gate.

### 2. `docs/experiment_lifecycle.md`

Purpose:

```text
This file freezes the formal ordering from repo bootstrap through release, including evidence
contract lifecycle, prediction freeze, deterministic selection, P0 execution semantics, retry,
scoring, aggregation, and paper-output gates.
```

Key excerpts:

```text
The formal lifecycle is:

bootstrap repo
-> validate config, manifest, official splits, source bundle, and paper mapping
-> draft evidence contracts
-> human review with timing
-> lock contracts
-> update manifest with contract hash, lock time, and version
-> validate locked contracts
-> freeze prediction registry and all code/config/hash inputs
-> deploy and check infrastructure
-> adapter smoke
-> preflight 10 case units per main domain
-> validate preflight
-> full run
-> scoring from locked contracts and raw artifacts
-> validate scored results
-> audit and rerun diagnostics
-> aggregation, bootstrap, pairwise margins, and P1-P4 outcomes
-> appendix diagnostics and release metadata
-> paper tables, figures, appendix, result macros, and final report
-> release audit package
```

```text
No formal scorer output, aggregate metric, freeze file, or paper output may be produced before
the required upstream gates pass. Step 8 vertical-slice scoring or aggregation is provisional
integration testing only; it cannot create formal scored records, formal metrics, formal
pre_scoring_freeze.json, or paper outputs.
```

Evidence contract lifecycle:

```text
Evidence contract draft/review/lock is a P0 blocker. For every case unit that can produce
evidence-scored records or update-countability results:

1. A contract-drafting LLM drafts requirements using only task text, official policy, evaluator
   code or description, database/API/browser/file/tool schema, trace schema, available post-run
   artifact types, and the native-aligned vs stronger_measurement template.
2. The drafter must be blind to agent identity, agent trace, native score, native evaluator
   pass/fail scalar, outcome label, alternate view verdicts, evidence label, UNRESOLVE reason,
   and scored/paper-output values.
3. Human adapter authors audit and edit each proposed requirement against the source hierarchy:
   official evaluator semantics, official task text / policy, then schema constraints needed to
   interpret evaluator-visible state.
4. Unsupported native-aligned requirements are removed or marked stronger_measurement.
5. Every stronger_measurement claim gets a sidecar report, appendix mapping, or manifest mapping
   and stays out of native-aligned main results.
6. The locked contract records version, hash, lock time, reviewer, drafter metadata, prompt
   version/hash, visible input hashes, hidden-input assertion, source-support audit, and claim scope.
7. The manifest records the locked contract id/version/hash before scoring.
```

Post-lock clarification:

```text
If a locked contract needs clarification after outcomes are available, the change creates a
superseded/clarification contract version and a sensitivity report mapping only. It is never
folded into the native-aligned main result.
```

Prediction freeze inputs:

```text
Prediction freeze must occur before scoring. The formal pre-scoring freeze must include:
manifest_hash, paper_mapping_hash, official_splits_hash, eligible_case_unit_set_hash,
excluded_smoke_case_units, smoke_exclusion_hash, case_selection_order_hash, hash_function,
hash_salt_hash, source_bundle_hash, agents_config_hash, infra_config_hash, locked_contracts_hash,
evidence_contract_template_version/hash, contract_drafting_prompt_version/hash,
prediction_registry_hash, taxonomy_version, result_schema_hash, artifact_schema_hash,
scorer_version, scorer_code_hash, code_git_commit, bootstrap_plan_hash, bootstrap_seed,
bootstrap_resample_count, audit_sampling_plan_hash, audit_sample_seed, rerun_subset_hash,
rerun_subset_selection_rule, P1-P4 predictions, pairwise_equality_tolerance,
P1-P4 threshold boundary rule.
```

Step 5 freeze-file prohibition:

```text
Step 5 may implement freeze CLI and tests, but it must not create a formal
results/manifests/pre_scoring_freeze.json. Formal freeze creation waits until Step 1-12 are
approved and formal experiment flow begins.
```

Deterministic selection and official split exception:

```text
Main-domain default selection is 100 case units per domain: 10 preflight and 90 full. Selection
must freeze hash_function, hash_salt_hash, eligible_case_unit_set_hash, excluded_smoke_case_units,
smoke_exclusion_hash, case_selection_order_hash, case selection order, seeds, rerun subset rule.

If an official verified split has fewer than 100 eligible case units, the exception must be
recorded in the frozen manifest before scoring. Otherwise the system fails closed. It cannot
backfill with non-official, duplicated, smoke-test, appendix, or synthetic cases.

Preflight status is formal only for frozen manifest slots. The 10 P0 preflight case units per
main domain may enter formal scored records only when they were predeclared in the frozen P0
manifest, passed preflight validation, and are carried forward as final selected attempts under
the same contract/config/taxonomy hashes. phase=smoke and phase=dry_run outputs can never enter
formal scored records, metrics, tables, figures, appendix empirical outputs, or final report values.

Failed formal preflight validation blocks the full run. Recovery is limited to retry/resume under
the same frozen manifest, record_slot, case_unit_id, contract version/hash, config hash, taxonomy
version, and deterministic selection order. Failed or inconvenient preflight slots cannot be
replaced, cherry-picked, moved to appendix, or silently dropped from P0 accounting.
```

Native evaluator decisive evidence:

```text
The scorer must not use raw_run.native_label, native score, or normalized summary scalar as
decisive evidence unless the locked contract maps a native evaluator artifact as allowed/required
evidence and the artifact has path, sha256, official runner/evaluator provenance, and direct
verified object read.
```

Risks GPT Pro should inspect:

- Does the lifecycle force contract lock and prediction freeze before any formal scoring?
- Is Step 5 explicitly blocked from producing a formal freeze file during development?
- Are deterministic selection fields and official split exceptions sufficient?
- Does post-lock clarification only feed sensitivity analysis?
- Does the native evaluator rule fully block raw summary scalar shortcuts?

Source correspondence:

- Paper: contract before scoring, predictions before scoring, deterministic 100 case-unit manifest.
- `计划.md`: contract lock blocker, freeze input list, official split exception, post-lock clarification.
- `实验说明.md`: preflight/full order and main/appendix execution order.
- `工程文件说明.md`: Step 5 formal freeze prohibition and vertical slice non-formal rule.

### 3. `docs/adapter_interface.md`

Purpose:

```text
This file freezes the main-domain adapter boundary, CLI, job input, raw output, domain-specific
raw evidence expectations, artifact manifest requirements, and failure semantics.
```

Adapter/scorer boundary:

```text
An adapter runs an official benchmark or diagnostic runner and saves raw evidence. It never
produces final evidence verdicts. It may save native evaluator outputs, native labels, native
scores, runner summaries, and benchmark logs as raw artifacts, but it must not decide final
SUCCESS, FAIL, or UNRESOLVE.
```

Adapter CLI:

```text
python -m evidence_system.adapters.<canonical_domain> \
  --job-json <path> \
  --result-json <path> \
  --artifacts-dir <path> \
  --llm-calls-log <path> \
  --stdout-log <path> \
  --stderr-log <path>
```

Job input:

```text
job.json is a validated job.schema.json object. Required fields include:
schema_version, run_id, record_slot_id, phase, experiment_type, priority, domain,
domain_display_name, case_unit_id, task_id, agent_id, seed, attempt_id, attempt_index,
evidence_contract_id, evidence_contract_version, evidence_contract_hash, agent_config_ref,
benchmark_config_ref, official_split_ref, machine_role, expected_artifact_contract,
config_hash, manifest_hash, code_git_commit.

agent_config_ref resolves to configs/agents.yaml plus locked manifest metadata. The job may
include a resolved config snapshot for reproducibility, but formal validation fails if it
disagrees with config and locked manifest.
```

Raw output:

```text
The adapter writes a raw_run_record/v1 object, not a scored record.

Required output groups:
- identity: run_id, record_slot_id, attempt_id, phase, experiment_type, priority, canonical
  domain id, case_unit_id, task_id, agent_id, seed.
- execution status: raw_status, start/end timestamps, benchmark started flag, timeout/abort
  fields, recoverable flag.
- episode ids: one episode for most domains; AgentDojo has benign and injected episode ids per record.
- official runner metadata: runner name, runner version, command hash, official split reference,
  source bundle hash, environment hash.
- native output metadata: native label/score as diagnostic metadata only, plus native evaluator
  artifact ids when present.
- artifact manifest path and hash.
- llm call log path and hash.
- stdout/stderr log paths and hashes.
- failure record path if execution failed before normal benchmark start.
- contains_final_evidence_label=false.

The adapter output must explicitly state that it contains no final evidence label. Missing
contains_final_evidence_label, setting it to true, or carrying contradictory final evidence fields
fails schema validation.
```

Native evaluator rule:

```text
If only raw_run.native_label or a runner summary scalar exists, the scorer refuses decisive use.
```

Failure semantics:

```text
Adapters classify failures without converting them to evidence labels:

- infra/pre-run failure: benchmark did not begin normally; write failure record and possible
  infra_exclusion_record.
- agent-caused failure after benchmark start: completed raw run; scorer may produce FAIL if native
  semantics supports fail.
- evaluator failure/unstable: for OSWorld-Verified and any diagnostic requiring evaluator status;
  do not silently map to UNRESOLVE.
- artifact/logging failure: raw execution may be complete, but evidence may be incomplete; scorer
  or validator decides whether validation fails or UNRESOLVE applies.

INFRA_EXCLUDED must not carry SUCCESS/FAIL/UNRESOLVE evidence labels and never enters the
evidence-envelope denominator.
```

Risks GPT Pro should inspect:

- Is the phrase "native labels as raw artifacts" safe enough, given scorer restrictions?
- Is the required `contains_final_evidence_label=false` field enough to make the boundary schema-testable?
- Are failure categories sufficient to keep infra/pre-run exclusions out of UNRESOLVE?
- Are main-domain raw evidence requirements sufficient for later scoring?

Source correspondence:

- Paper: adapters collect traces/artifacts; scorer applies evidence rule.
- `计划.md`: adapter cannot decide final verdict; native evaluator use must be artifact-backed.
- `实验说明.md`: AgentDojo paired arms, WebArena verifier artifacts, AppWorld database artifacts, tau3 policy/backend evidence.
- `工程文件说明.md`: Step 8 adapter acceptance tests and artifact manifest provenance requirements.

### 4. `docs/auxiliary_adapters.md`

Purpose:

```text
This file freezes appendix and diagnostic adapter semantics for AndroidWorld, WorkArena,
OSWorld-Verified, judge-only, maintenance update, and matched-budget controls.
```

General appendix gate:

```text
Auxiliary adapters are part of the complete P0/P1/P2/P3 system scope, but they do not enter
the P0 native-aligned main envelope unless the paper and manifest are updated to make them
main experiments. Declared appendix or diagnostic outputs block paper generation if missing,
unless the paper text and manifest are updated together.
```

AndroidWorld and WorkArena:

```text
AndroidWorld:
Canonical domain id: androidworld.
Experiment type: appendix.
Priority: P2.
Machine role: local AndroidWorld machine.
Counts and selected case units are 需要从 locked manifest 确认. AndroidWorld is an appendix
negative control and cannot enter the four-domain P0 aggregate.

WorkArena:
Canonical domain id: workarena.
Experiment type: appendix.
Priority: P2.
Counts and selected case units are 需要从 locked manifest 确认. WorkArena is an appendix
negative control and cannot enter the P0 aggregate.
```

OSWorld-Verified diagnostic status:

```text
Canonical domain id: osworld_verified.
Experiment type: appendix.
Priority: P2.

Raw/scored schema must support:
diagnostic_status: not_applicable | completed | infra_excluded | evaluator_failure | evaluator_unstable
appendix_failure_class: none | infra_pre_run | evaluator_failure | evaluator_unstable | evidence_unresolve

evaluator_failure and evaluator_unstable must not be silently mapped to evidence UNRESOLVE.
Evidence UNRESOLVE applies only when a completed evidence record lacks enough raw evidence to
decide a locked claim.
```

Judge-only blind input:

```text
Canonical domain id: judge_only.
Experiment type: diagnostic.
Priority: P3.

Judge-only is diagnostic, not a headline baseline. The judge input must be blind to:
agent identity
native_label
native_score
native evaluator pass/fail scalar
outcome label
evidence label
UNRESOLVE reason
alternate view verdicts
scored values
paper-output values

Allowed input includes judge-readable task text, official policy, locked contract, required
artifacts, trace without agent identity, and post-run artifacts. The diagnostic reports
success/fail/inconclusive, disagreement rates, and judge assignments on evidence-UNRESOLVE records.
```

Maintenance update and matched-budget:

```text
maintenance_update exact funnel:
6 raw proposals per main domain
3 selected per main domain
24 proposed total
12 selected total
15 executed total because AgentDojo selected candidates are paired

matched_budget_controls:
Controls must use the same proposal/selection budget as the evidence-aware update process.
Required controls are one-shot generation, evidence-blind generation, and static benchmark refresh.
Outputs report countable updates and envelope-width reduction with provenance.
```

Risks GPT Pro should inspect:

- Does judge-only blindness include native evaluator scalar and paper/scored outputs?
- Does OSWorld status prevent evaluator failure/unstable from becoming evidence UNRESOLVE?
- Does the appendix gate prevent auxiliary results from polluting P0?
- Does maintenance update preserve exact funnel semantics?

Source correspondence:

- Paper: appendix sections `app:aux-domains`, `app:osworld`, `app:judge`, `app:update`.
- `计划.md`: P2/P3 scope and missing appendix block.
- `实验说明.md`: OSWorld stress distinction, judge-only diagnostic, update/matched-budget controls.
- `工程文件说明.md`: auxiliary adapter acceptance tests and declared appendix gate.

### 5. `docs/scorer_spec.md`

Purpose:

```text
This file freezes the locked-contract scorer boundary, allowed and forbidden inputs, native
evaluator decisive-evidence rule, output shape, R1-R7 taxonomy, claim scope, domain rules,
counting formulas, and scorer acceptance tests.
```

Scorer boundary:

```text
The scorer is the only component that emits final evidence labels for completed records:
SUCCESS | FAIL | UNRESOLVE

Adapters, orchestrators, monitors, collectors, native benchmark runners, and paper-output code
do not emit final evidence labels.
```

Verdict input boundary:

```text
The scorer has two layers:
1. verdict_engine computes SUCCESS/FAIL/UNRESOLVE from locked contract, raw artifacts, artifact
   manifest, freeze/schema/taxonomy metadata, and case metadata that excludes agent identity.
2. provenance_binder attaches agent_id, agent config references, run grouping, audit/rerun grouping,
   and paper aggregation metadata after the verdict is computed.

verdict_engine must not receive agent_id, agent family, model identity, provider, model version,
leaderboard rank, or any equivalent agent-identity feature. Domain id, case_unit_id, task_id,
contract id/hash, and artifact ids are allowed because they select the locked claim and domain
rule set, not an agent branch.

The implementation must make this separation testable: an invalid fixture where only agent_id
changes must produce the same verdict_engine output hash, and any verdict branch conditioned on
agent identity fails validation.
```

Allowed verdict_engine inputs:

```text
- locked evidence contract and its hash/version/status.
- manifest case metadata and deterministic selection metadata.
- raw traces, post-state evidence, tool logs, browser artifacts, database snapshots, files,
  messages, API logs, screenshots, evaluator input/output artifacts, and other raw artifacts.
- artifact manifest with paths, sha256 values, official provenance, visibility, and contract
  requirement ids.
- freeze manifest and schema/taxonomy versions.
- native evaluator output only through the locked artifact mapping rule.

The provenance_binder may read job metadata needed for grouping, including agent_id, only after
verdict_engine output is fixed.
```

Forbidden inputs:

```text
The scorer must not use these as decisive evidence:
- raw_run.native_label by default.
- native score scalar.
- native evaluator pass/fail scalar unless backed by locked artifact mapping.
- native scalar shortcut or normalized benchmark summary.
- outcome_label.
- prior benchmark outcome verdict.
- previous run outcome.
- previous scored/evidence label.
- adapter-produced summary verdict.
- runner-produced summary verdict.
- alternate view verdicts.
- paper-output values.
- scored values from another scorer run.
- judge-only diagnostic labels.
- any equivalent derived field that encodes outcome, score, native verdict, paper value, or prior evidence label.
- agent family/model identity as a verdict condition.
- agent_id inside verdict_engine.
- post-lock clarification contract version for native-aligned main results.
```

Native evaluator decisive evidence:

```text
Native evaluator output can be decisive only when all conditions hold:
1. the locked contract lists the evaluator artifact as allowed or required evidence for the claim;
2. the artifact manifest includes path and sha256 for that artifact;
3. the artifact provenance matches official runner/evaluator metadata;
4. the scorer directly reads the artifact or a verified evaluator-output object.

Missing provenance produces validation failure or UNRESOLVE R6 depending on discovery point and
locked contract rules. A sha mismatch refuses scoring.
```

R1-R7 taxonomy:

```text
R1 Missing state query
R2 Unobservable side effect
R3 Ambiguous identity mapping
R4 Required state-preservation evidence absent
R5 Paired-arm asymmetry
R6 Evaluator output ambiguity
R7 Claim-scope mismatch

Every UNRESOLVE completed record has exactly one category. If multiple categories apply, the
scorer uses the upstream-priority rule: choose the most upstream reason that, if fixed first,
would unblock the others.
```

Formal R1-R7 semantics:

```text
Fail-closed validation happens before taxonomy assignment. Unlocked contracts, hash mismatch,
artifact sha mismatch, missing formal freeze, non-final attempts, and INFRA_EXCLUDED inputs refuse
scoring rather than producing UNRESOLVE.

R1 Missing state query:
Applies when the locked native-aligned claim requires a backend, database, environment, browser,
file, tool, or other evaluator-visible state value, but no post-action query/snapshot/artifact for
that value exists. Does not apply when a state artifact exists but target identity is ambiguous
(R3), when missing evidence is official preservation/diff evidence (R4), or when native evaluator
output is ambiguous (R6). Positive fixture: AppWorld CRM row expected after update but no database
read/unit-test/post-state artifact exists. Negative fixture: row exists but two customers match (R3).

R2 Unobservable side effect:
Applies when the action may have occurred but the consequence is not exposed by any benchmark
artifact path, such as delivery, send receipt, payment settlement, or external service effect.
Does not apply when an official state query could have been captured but is absent (R1), or to
evaluator-output ambiguity (R6). Positive fixture: message send returns no receipt/message id.
Negative fixture: backend table would show the side effect but adapter did not save it (R1).

R3 Ambiguous identity mapping:
Applies when multiple records, accounts, customers, orders, files, recipients, browser targets, or
entities match the claim and raw evidence does not identify which was acted on. Takes priority over
R1/R4 when missing state/preservation evidence cannot be tied to a unique target. Positive fixture:
tau3_retail two customers share a name and no unique id is logged. Negative fixture: unique id is
logged but no post-state exists (R1).

R4 Required state-preservation evidence absent:
Applies when official task, policy, evaluator, or reported native claim requires preserving
unrelated state but no diff/snapshot/audit log/preservation artifact exists. Does not apply to a
no-collateral-change requirement invented by annotator intuition; unsupported requirements must be
removed or moved to stronger_measurement. Positive fixture: official calendar task requires
preserving other events but no post-run diff is captured. Negative fixture: native sources do not
require no-collateral-change.

R5 Paired-arm asymmetry:
Applies when a locked paired-arm claim cannot be jointly decided because one arm is missing, not
linked, or undecidable while the other arm is decidable. Applies primarily to AgentDojo-style
benign/injected paired records. Does not apply to unpaired domains or infra/pre-run failure.
Positive fixture: benign arm decisive, injected arm lacks required security evidence. Negative
fixture: both arms have the same ambiguous target identity (R3).

R6 Evaluator output ambiguity:
Applies when native evaluator artifact exists or is required, but inputs, provenance, verified
object, or stored details do not uniquely support the locked native-aligned claim. Applies when
official evaluator output is present but required official provenance is missing and the locked
contract permits UNRESOLVE rather than validation failure. Sha mismatch refuses scoring. Positive
fixture: WebArena verifier emits a label but stored verifier inputs do not show required target.
Negative fixture: verified evaluator object, inputs, path, sha256, and official provenance all match.

R7 Claim-scope mismatch:
Applies when trace/artifacts support a related, weaker, stronger, or different claim than the
predeclared locked claim, leaving the reported claim undecided. Applies when unsupported stronger
requirement remains inside native-aligned scoring instead of being removed/mapped. Positive fixture:
tau3_retail agent gives useful refund explanation but locked claim requires backend policy record.
Negative fixture: correct claim targeted but backend state query missing (R1).
```

Upstream-priority rules:

```text
1. Not completed, INFRA_EXCLUDED, artifact sha mismatch, missing locked contract, or freeze/hash
   violation: do not assign UNRESOLVE; fail validation or classify outside evidence envelope.
2. Evidence for a different claim or unsupported stronger measurement left in native-aligned scoring:
   choose R7 before evidence-missing reasons.
3. Paired-arm completeness locked precondition with one arm blocking paired claim: choose R5 unless
   upstream issue is R7 or infra exclusion.
4. Target identity ambiguous: choose R3 before R1/R4.
5. Official state-preservation evidence required and absent: choose R4 before generic R1.
6. Missing ordinary state query: choose R1.
7. Side effect unobservable by benchmark instrumentation: choose R2.
8. Decisive route depends on ambiguous native evaluator artifact/provenance/inputs: choose R6 unless
   validation must fail closed.

Golden fixtures must include positive and negative fixtures for each R1-R7 reason and overlap
fixtures for R3-over-R1, R4-over-R1, R5-over-arm-specific-missing-evidence, R7-over-R1/R4, and
R6-versus-validation-failure.
```

Claim scope:

```text
claim_scope is native_aligned | stronger_measurement.
Native-aligned main envelope includes only native_aligned. Any stronger_measurement record must
have a sidecar report id, appendix mapping, or manifest mapping. Missing mapping fails closed.
```

COUNTED_ONLY_SCORE:

```text
COUNTED_ONLY_SCORE = SUCCESS / (SUCCESS + FAIL) when SUCCESS + FAIL > 0.
If SUCCESS+FAIL is zero, COUNTED_ONLY_SCORE is null with reason no_counted_records.
It is not 0, 1, empty string, paper fallback text, or a generated substitute.
```

Risks GPT Pro should inspect:

- Are forbidden inputs comprehensive enough to prevent leakage from native labels or paper outputs?
- Is verdict_engine/provenance_binder separation strong enough to make agent identity leakage testable?
- Are outcome_label, prior outcome verdict, adapter/runner summary verdicts, and previous scored
  labels fully excluded from decisive evidence?
- Are R1-R7 formal semantics and golden fixtures specific enough for Step 7 implementation?
- Is R6 behavior clear enough when native evaluator artifact exists but provenance is missing?
- Should domain rules add more artifact-specific examples for tau3/AppWorld/WebArena?
- Does the scorer acceptance list cover every fail-closed condition?

Source correspondence:

- Paper: native-aligned claim, evidence contract, UNRESOLVE taxonomy, counting formulas.
- `计划.md`: scorer only reads locked contract/raw artifacts; native_label not decisive by default.
- `实验说明.md`: SUCCESS/FAIL/UNRESOLVE, COUNTED_ONLY_SCORE undefined.
- `工程文件说明.md`: R1-R7 fixed taxonomy, native evaluator decisive evidence conditions.

### 6. `docs/result_schema.md`

Purpose:

```text
This file freezes result directories, completed_scored_record and infra_exclusion_record
semantics, aggregate metrics, denominator audit fields, paper-output source mapping, and OSWorld fields.
```

Formal result directories:

```text
results/raw_runs/
results/artifacts/
results/scored_records/
results/logs/llm_calls/
results/logs/human_review/
results/logs/human_time/
results/metrics/
results/tables/
results/figures/
results/appendix/
results/manifests/
results/failures/
results/audits/
results/reruns/
results/release/
results/reports/
```

Scored record classes:

```text
Formal result schema distinguishes:
- completed_scored_record: completed benchmark execution eligible for SUCCESS/FAIL/UNRESOLVE.
- infra_exclusion_record: benchmark/pre-run failure excluded from evidence-envelope denominator
  and included in denominator audit.
```

Completed record conditions:

```text
status=COMPLETED requires evidence_label to be SUCCESS, FAIL, or UNRESOLVE.
UNRESOLVE requires exactly one unresolve_reason and one unresolve_level.
SUCCESS and FAIL require null unresolve_reason and null unresolve_level.
claim_scope=stronger_measurement requires sidecar, appendix, or manifest mapping and is excluded
from native-aligned main envelope.
phase=smoke|dry_run cannot be a formal completed scored record.
phase=preflight may be a formal completed scored record only for case units predeclared as P0
preflight slots in the frozen manifest and only after preflight validation passes; otherwise it
remains non-formal integration output.
native_label and native_score are diagnostic metadata unless decisive use is backed by locked
artifact mapping and official provenance.
```

INFRA_EXCLUDED schema:

```text
status: INFRA_EXCLUDED
evidence_label: null
unresolve_reason: null
unresolve_level: null
failure_category: infra_pre_run
entered_evidence_denominator: false
entered_denominator_audit: true

INFRA_EXCLUDED must not carry SUCCESS, FAIL, or UNRESOLVE evidence labels. It is excluded from
evidence envelope denominator and included in denominator audit.
```

Aggregate metrics:

```text
Validation requires N_completed_scored_records = SUCCESS + FAIL + UNRESOLVE.
COUNTED_ONLY_SCORE is defined only when SUCCESS+FAIL > 0. If no counted records exist, it is
explicit null with reason no_counted_records.
```

Denominator audit:

```text
Denominator audit records:
attempted_record_slots
completed_records
infra_excluded
agent_caused_failures
formally_documented_missing_or_blocked
retry_attempt_count
notes

P0 denominator audit must be able to report attempted=1600 even when completed scored denominator N
is smaller due to allowed infra exclusions.
```

OSWorld fields:

```text
diagnostic_status: not_applicable | completed | infra_excluded | evaluator_failure | evaluator_unstable
appendix_failure_class: none | infra_pre_run | evaluator_failure | evaluator_unstable | evidence_unresolve

Evaluator failure/unstable is not evidence UNRESOLVE.
```

Risks GPT Pro should inspect:

- Are conditional constraints sufficient for schema implementation?
- Does `native_label` remain diagnostic-only?
- Does denominator audit capture attempted record_slots and infra exclusions?
- Is `phase=preflight` allowed as formal completed scored record because preflight cases are part of final manifest? If not, flag.

Source correspondence:

- Paper: completed denominator, not merging infra failures with UNRESOLVE.
- `计划.md`: conditional result schema constraints and denominator audit.
- `实验说明.md`: formulas, P0 attempted/completed/excluded reporting.
- `工程文件说明.md`: completed_scored_record vs infra_exclusion_record distinction.

### 7. `docs/artifact_schema.md`

Purpose:

```text
This file freezes artifact_manifest/v1 and the official provenance fields needed for native
evaluator decisive evidence, domain artifact classes, release visibility, and secret handling.
```

Artifact manifest:

```text
Every raw run has an artifact_manifest/v1 object. The manifest is the only allowed index from
scored records to raw evidence. It must be immutable after final collection except through a
versioned superseding manifest.

Because the full artifact manifest includes provenance fields such as agent_id, the scorer
verdict engine must not receive the full manifest directly. Scoring uses a sanitized
artifact-manifest projection that preserves artifact ids, paths, sha256 values, official
runner/evaluator provenance, visibility, source hashes, and contract requirement ids, while
excluding agent_id, agent family, model/provider identity, leaderboard/display labels, and other
provenance-only identity fields. The full manifest is reattached only after verdict computation by
the provenance binder.
```

Top-level fields:

```text
schema_version, run_id, record_slot_id, attempt_id, final_attempt, domain, phase,
experiment_type, priority, case_unit_id, task_id, agent_id, evidence_contract_id,
evidence_contract_version, evidence_contract_hash, source_bundle_hash, official_splits_hash,
environment_hash, artifacts.
```

Official runner/evaluator provenance:

```text
Artifact manifest entries that can support native evaluator decisive evidence must include:
producer_role
producer_name
producer_version
producer_command_hash
official_runner
official_evaluator
evaluator_name
evaluator_version
source_bundle_hash
official_splits_hash
environment_hash
verified_evaluator_output_object_hash
artifact_created_after_run_start
artifact_contract_requirement_ids

If native evaluator artifact provenance is missing, validation fails or scorer emits UNRESOLVE R6
only when the locked contract and discovery point allow that. If native label scalar exists without
artifact mapping, decisive use is refused. If sha256 mismatches, scoring is refused.
```

Domain artifact classes:

```text
agentdojo:
benign arm trace and injected arm trace; workspace state across both arms; tool calls, files,
messages; security and utility native output artifacts kept separate; paired-arm linkage metadata.

appworld:
database snapshots or state queries; API logs; unit-test artifacts; native field checks and
evaluator inputs/outputs.

webarena_verified:
browser artifacts; network trace; structured final output; verifier inputs; official verifier
outputs with official evaluator provenance.

tau3_retail:
tool records; backend/database state; policy-relevant evidence; identity-resolution artifacts.
```

Visibility and secret rule:

```text
Artifacts are classified public, access_controlled, or not_released.
UNRESOLVE visibility must remain even when full traces are gated: case identifier, locked claim,
evidence contract, taxonomy code, and envelope contribution remain visible.

No artifact manifest may contain real API keys, SSH private key contents, live credentials, or
secret values.
```

Risks GPT Pro should inspect:

- Are official provenance fields complete enough for decisive native evaluator use?
- Should artifact immutability include manifest hash chaining?
- Are domain artifact classes sufficient for locked-contract scoring?
- Does release visibility preserve UNRESOLVE transparency without leaking secrets?

Source correspondence:

- Paper: raw artifacts support evidence contracts and release/rescorer.
- `计划.md`: artifact manifest official provenance fields.
- `实验说明.md`: required raw traces, post-run artifacts, native evaluator inputs, browser/db/tool artifacts.
- `工程文件说明.md`: native evaluator decisive evidence requires path/sha/provenance/direct read.

### 8. `docs/llm_logging_and_cost.md`

Purpose:

```text
This file freezes LLM call logging, config source, contract drafter visibility, judge-only
visibility, and separation of LLM costs from tab:cost.
```

Configuration source:

```text
Provider, model, model version, API key environment variable name, temperature, max_tokens,
timeout, retry, rate limit, prompt version, prompt hash, response metadata setting, and cost
tracking setting are read from configs/agents.yaml and locked manifest. Formal run fails closed
on disagreement.

Values for Agent A-D, contract_drafter, and judge_only must not be hardcoded in code, tests,
scorer, runner, paper output, or review packets. API key values are read from environment
variables and are never logged.
```

LLM call log fields:

```text
Each call writes llm_call/v1 with:
call_id, run_id, record_slot_id, attempt_id, contract_draft_id, case_unit_id,
evidence_contract_id, contract_version, visible_input_hash, hidden_input_assertion_hash, domain,
phase, experiment_type, priority, agent_id_or_role, provider, model, model_version, api_key_env,
prompt_version, prompt_hash, prompt_hash_method, temperature, max_tokens, timeout_seconds,
retry_index, rate_limit_bucket, request_timestamp, response_timestamp, response_metadata,
token_usage, cost, config_hash, manifest_hash, redaction_status.

token_usage preserves provider-specific categories where available: prompt/input tokens,
completion/output tokens, cached input tokens, reasoning tokens, and total tokens.

cost records amount, currency, pricing_source, pricing_table_id, pricing_table_version,
pricing_source_hash, and cost_calculation_method. If provider response includes token/cost metadata,
use it. If cost is unavailable and a pricing table is configured, mark pricing_source=config_estimate
and record pricing table provenance. If neither is available, record unavailable; do not invent cost.

For Agent A-D execution calls, run-centric fields (run_id, record_slot_id, attempt_id) are required.
For contract-drafting calls, which happen before benchmark runs and before locked contract hashes
exist, the required linkage fields are:
contract_draft_id, case_unit_id, domain, task_id when available, evidence_contract_id when assigned,
contract_template_version/hash, prompt_version, prompt_hash, visible_input_hash,
hidden_input_assertion_hash, source_bundle_hash, call_id.

The locked contract metadata must back-reference the exact contract-drafting LLM call_id and
contract_draft_id. tab:contract-drafting-metadata, LLM cost provenance, and drafter-visibility
validation must fail closed if a locked contract cannot be linked to the exact LLM call log entry
that produced its draft, or if visible-input / hidden-input assertion hashes are missing.
```

Contract drafter allowed/forbidden inputs:

```text
Allowed:
task_text
official_policy
evaluator_code_or_description
database/API/browser/file/tool schema
trace_schema
available_post_run_artifact_types
native_aligned vs stronger_measurement template

Forbidden:
agent identity
agent trace
native score
native evaluator pass/fail scalar
outcome label
alternate view verdicts
evidence label
UNRESOLVE reason
scored values
paper-output values

Any contract draft that sees forbidden inputs is discarded for main results and must be
redrafted/reviewed/locked.
```

Judge-only visibility:

```text
Judge-only diagnostic must be blind to native_label, native_score, native evaluator pass/fail
scalar, outcome label, scored/paper-output values, agent identity, evidence label, UNRESOLVE
reason, and alternate view verdicts. The log records a forbidden-input assertion.
```

LLM cost boundary:

```text
LLM cost logs support audit, monitoring, and final report cost/latency/failure provenance when
the paper/report asks for LLM usage statistics. They do not feed tab:cost. tab:cost is trained
annotator wall-clock human-time only.
```

Risks GPT Pro should inspect:

- Is the drafter forbidden-input list broader than the paper minimum and acceptable?
- Should raw prompts be stored or only prompt hashes, considering release/security?
- Are config/manifest mismatch fail-closed rules clear?
- Does LLM cost separation prevent `tab:cost` contamination?

Source correspondence:

- Paper: drafter sees task/evaluator/schema but not agent/outcome.
- `计划.md`: OpenRouter/LLM logging and model configuration from `configs/agents.yaml`.
- `实验说明.md`: API key env vars and cost tracking.
- `工程文件说明.md`: no hardcoded model/prompt values; judge-only blind input includes native labels/scalars.

### 9. `docs/human_time_and_cost.md`

Purpose:

```text
This file freezes human-time logging and cost-table source rules.
```

Boundary:

```text
Human-time logs measure trained annotator or adapter-author wall-clock work. They are separate from:
- LLM token/cost logs.
- VPS runtime or cloud bills.
- benchmark execution compute.
- local AndroidWorld machine runtime.

tab:cost is generated only from human-time logs. It must not read LLM/OpenRouter token costs,
VPS runtime, benchmark runtime, or inferred estimates.
```

Human-time schema:

```text
Each activity writes human_time/v1:
activity_id, reviewer_or_worker_id, role, activity_type, domain, case_unit_id, record_id,
started_at, finished_at, duration_minutes, action, source_artifacts, notes, phase,
experiment_type, priority, manifest_hash, contract_hash, no_llm_cost_included,
no_vps_cost_included.

Validation requires started_at < finished_at, non-negative duration, reviewer/worker id, action,
and source artifact references where applicable.
```

Cost table inputs:

```text
tab:cost requires per-domain:
- draft/lock contract minutes per case.
- score evidence minutes per record.
- tag UNRESOLVE minutes per record.
- per-domain one-time setup notes.

Contract-drafting LLM may reduce first-draft time, but human lock time is recorded separately
and cannot be replaced by LLM time.
```

Risks GPT Pro should inspect:

- Does the schema cover setup notes and all human activities in `tab:cost`?
- Does it adequately separate contract first-draft LLM time from human lock time?
- Should audit time appear in `tab:cost` or only final report/supporting logs?

Source correspondence:

- Paper appendix `app:cost` and `tab:cost`.
- `计划.md`: `tab:cost` human-time-only.
- `实验说明.md`: draft/lock, score evidence, tag UNRESOLVE human time from start.
- `工程文件说明.md`: LLM cost cannot fill trained annotator wall-clock table.

### 10. `docs/human_review_time.md`

Purpose:

```text
This file freezes human review timing for contract lock and audit review logs.
```

Contract review:

```text
Human adapter authors review contract drafts before scoring. The review record must show:
review_started_at
review_finished_at
duration_minutes
reviewer_id
source_bundle_hash
visible_input_hash
review_actions
source hierarchy applied
unsupported requirements removed
requirements marked stronger_measurement
final lock decision
locked_at
locked_by
contract_version
contract_hash
manifest_hash

Required ordering:
draft created_at <= review_started_at < review_finished_at <= locked_at < first_scoring_started_at

If lock time is missing or later than scoring, the record cannot enter formal scoring.
```

Review input restrictions:

```text
Human contract review uses official task/evaluator/policy/schema sources and the draft contract.
The review log records source_bundle_hash and visible_input_hash for the exact materials shown to
the reviewer. Contract reviewers must not use agent identity, agent trace, native_label,
native_score, native evaluator pass/fail scalar, outcome label, prior outcome verdict, scored
values, paper-output values, judge-only labels, alternate view verdicts, adapter/runner summary
verdicts, or any other agent outcome to alter native-aligned contracts. After locking, any
clarification creates a superseded/clarification contract version and sensitivity report mapping only.
```

Human audit:

```text
Blinded human audit records must capture auditor id, assignment id, start/finish/duration, domain,
stratum, record id, inputs shown to auditor, forbidden-input assertion, auditor label over
counted-SUCCESS / counted-FAIL / UNRESOLVE, auditor R1-R7 taxonomy label when UNRESOLVE, and
disagreement notes.

Auditor inputs include task, trace, available evidence, and locked contract. They exclude agent
identity, native_label, native_score, native evaluator pass/fail scalar, outcome label, prior
outcome verdict, scored values, paper-output values, counting decision, UNRESOLVE reason, alternate
view verdicts, judge-only labels, and adapter/runner summary verdicts.
```

Risks GPT Pro should inspect:

- Does review timing fully prove contract lock precedes scoring?
- Should review logs also hash the source bundle shown to reviewers?
- Does auditor blindness need to exclude native score scalar explicitly here as in other docs?

Source correspondence:

- Paper: human adapter authors audit/edit/lock before scoring; audit is blinded.
- `计划.md`: human review time and lock provenance.
- `实验说明.md`: lock before preflight/scoring and audit visibility.
- `工程文件说明.md`: human review start/finish/duration/reviewer/action logging.

### 11. `docs/audit_rerun_spec.md`

Purpose:

```text
This file freezes audit/rerun/bootstrap/pairwise/P1-P4 statistical rules.
```

Frozen plans:

```text
Audit sampling plan, audit sample seed, rerun subset, rerun subset selection rule,
bootstrap seed/resample count, pairwise_equality_tolerance, and P1-P4 threshold boundary behavior
must be frozen before formal scoring.

Until a formal value is set in the frozen stats plan, pairwise_equality_tolerance is
需要从 locked manifest 确认; missing tolerance blocks aggregation and paper outputs.

Default boundary rule:
supported: full 95% interval strictly lies on predicted side
falsified: full 95% interval strictly lies on opposite side
inconclusive: interval touches or crosses threshold

An inclusive threshold rule is allowed only if frozen before results are seen.
```

Bootstrap:

```text
Bootstrap resamples case units within domain with replacement and keeps all agent records attached
to a resampled case unit. It does not resample records independently. Intervals are secondary
descriptive views over a deterministic manifest; they condition on stored traces, fixed agent
versions, and fixed environments.
```

P1-P4:

```text
Prediction outcomes are supported, falsified, or inconclusive.

P1: AppWorld and WebArena-Verified width intervals each strictly below 15% support; either lower
bound strictly above 15% falsifies; interval touching 15% is inconclusive unless an inclusive rule was frozen.
P2: AgentDojo width minus max(AppWorld, WebArena-Verified) contrast interval strictly above
20 percentage points supports; upper bound strictly below 20 pp falsifies; touching is inconclusive unless frozen otherwise.
P3: tau3_retail width must be strictly above both negative controls and strictly below AgentDojo by contrast intervals.
P4: fraction of non-identified pairs on AgentDojo or tau3_retail supports only when the lower
interval bound satisfies the frozen 75% rule; upper bound below 75% falsifies.
Exact zero-width equality is reported separately and is not evidence-induced non-identification.
```

Pairwise:

```text
i > j if LB_i,d > UB_j,d
j > i if LB_j,d > UB_i,d
? otherwise
= only if both evidence envelopes are exactly equal under frozen pairwise_equality_tolerance

Ordinary interval overlap is ?, not equality.
```

Rerun and audit:

```text
Rerun subset:
Agent A
10 case units per main domain
40 total rerun case units
50 total rerun episodes because AgentDojo reruns paired arms

Audit sample:
100 main-study records
25 records per main domain
stratified stress sample with required within-domain buckets

Within each main domain, the audit sampler must form the required strata from the formal scored-record source set:
counted records: evidence_label in SUCCESS | FAIL
UNRESOLVE records: evidence_label == UNRESOLVE
native/evidence disagreement records: native reporting and evidence reporting disagree

When all three buckets exist in a domain, all three must be represented in that domain's 25-record
audit sample. If a bucket is empty, the audit sampling manifest must record bucket_empty with the
source count and redistribute the remaining quota according to the frozen audit_sampling_plan. If
a non-empty required bucket is omitted, audit validation fails and paper outputs depending on
tab:audit-rerun are blocked. This is a stratified stress sample, not a simple random sample.

Auditors see task, trace, available evidence, and locked evidence contract. The blinded audit
forbidden-input list is: agent identity, native_label, native_score, native evaluator pass/fail
scalar, outcome label, prior outcome verdict, scored values, paper-output values, counting decision,
UNRESOLVE reason, alternate view verdicts, judge-only labels, and adapter/runner summary verdicts.

Metrics:
- auditor-vs-scorer agreement over counted-SUCCESS, counted-FAIL, UNRESOLVE.
- inter-rater kappa over counted vs UNRESOLVE.
- R1-R7 taxonomy kappa only where both auditors mark UNRESOLVE.
```

Risks GPT Pro should inspect:

- Is the default interval-touching rule correctly inconclusive?
- Does P4 wording handle equality and non-identification correctly?
- Is `需要从 locked manifest 确认` sufficient for pairwise tolerance at Step 1, with missing value blocking aggregation before formal scoring?
- Is the audit forbidden-input list now consistent with judge-only and contract review blindness?

Source correspondence:

- Paper: interval interpretation, pairwise rule, P1-P4 predictions, audit/rerun sizes.
- `计划.md`: bootstrap plan, pairwise margins, P1-P4 threshold boundaries.
- `实验说明.md`: case-cluster bootstrap and audit/rerun implementation.
- `工程文件说明.md`: pairwise_equality_tolerance and boundary behavior freeze.

### 12. `docs/release_and_rescorer.md`

Purpose:

```text
This file freezes release traceability, public/gated/not-released classification, rescorer
interface, post-lock clarification, and paper-output detail gates.
```

Release traceability:

```text
The release package must let a reader trace every reported envelope, table value, figure value,
appendix metric, and final report statistic back to manifest entry, case unit, agent config and
locked manifest metadata, locked evidence contract, scorer/rescorer version, raw artifact paths
and hashes, LLM call logs where applicable, human-time or human-review logs where applicable,
denominator audit and failure records where applicable.

Every reported envelope binds the version tuple:
(rescorer version, manifest version, contract version, taxonomy version)
```

Release visibility:

```text
public: per-case manifests with task ids, locked claim, evidence contract, claim-scope label,
UNRESOLVE taxonomy code, envelope contributions, rescorer source/tests, template/prompt versions,
per-domain summaries, robust-ranking matrices, denominator audits, audit instructions, item-level
audit labels, stratum counts, and audit disagreement set.

access_controlled: traces or fragments containing prompt-injection content, placeholder credentials,
API-like tokens, synthetic personal data, sensitive browser/workspace state, or gated benchmark assets
after scrubbing and sandbox re-pinning.

not_released: live-account credentials, real third-party API keys, SSH private keys, private service
credentials, and artifacts enabling non-sandbox side effects.
```

Post-lock clarification / superseded contract:

```text
Locked contracts cannot be changed based on outcomes. Any clarification creates a
superseded/clarification contract version containing:
clarification_reason
clarification_requested_at
clarification_locked_at
supersedes_contract_id/version/hash
main_result_eligible: false
sensitivity_report_id

Clarified contracts feed sensitivity reports only. They do not enter native-aligned main result,
main tables, main figures, or headline report values.
```

Paper-output gates:

```text
- tab:views reports evidence envelope, counted-only, native benchmark, optimistic, and pessimistic
  views with shared provenance.
- native-score-inside-envelope appears in tab:main-results-B and is backed by validated metrics.
- fig:hero panel (b) includes only the four P0 main domains: agentdojo, appworld,
  webarena_verified, tau3_retail.
- fig:case-cards has case-level provenance and source artifact ids, not hand-authored examples
  without artifacts.
- app:update exact funnel: 6 raw proposals/domain, 3 selected/domain, 24 proposed, 12 selected,
  15 executed because AgentDojo is paired.
- matched-budget controls use the same proposal/selection budget and report countable updates plus
  envelope-width reduction.
- judge-only metrics are diagnostic and include success/fail/inconclusive, disagreement rates, and
  assignments on evidence-UNRESOLVE records.
- final report cost, latency, and failure statistics have provenance and are not estimated or backfilled.
- tab:cost comes only from human-time logs.
- stronger_measurement sidecar data never enters native-aligned main envelope.
```

Macro contract:

```text
Final paper build must set resultdatatrue. It must not retain fillfromdata, row-file fallback text,
figure layout values used as empirical data, or manually entered paper cells. Missing empirical data
blocks paper outputs unless the paper and manifest are updated.
```

Risks GPT Pro should inspect:

- Does release traceability cover final_report cost/latency/failure provenance?
- Are public/gated/not-released classes safe enough around secrets and side effects?
- Does post-lock clarification block main-result contamination?
- Are paper-output detail gates complete relative to the paper labels?

Source correspondence:

- Paper: responsible release plan, formal definitions, macro contract, paper output labels.
- `计划.md`: release/rescorer, macro contract, case cards, update, judge-only, matched-budget controls.
- `实验说明.md`: final report and appendix generation requirements.
- `工程文件说明.md`: paper output detailed acceptance and post-lock clarification.

### 13. `docs/vps_runtime_spec.md`

Purpose:

```text
This file freezes machine roles, domain routing, deployment CLI responsibilities, infra checks,
deployment manifest, monitoring, collection, and resume behavior.
```

Machine roles:

```text
Formal scheduling uses machine roles:
webarena_vps
osworld_vps
other_vps
local_androidworld

Domain routing:
- webarena_verified runs only on webarena_vps.
- osworld_verified runs only on osworld_vps.
- androidworld runs only on local_androidworld.
- agentdojo, appworld, tau3_retail, workarena, judge_only, maintenance_update, and
  matched_budget_controls run on other_vps unless the locked infra manifest says otherwise.
```

Secret handling:

```text
SSH private key contents, API keys, live credentials, and service secrets must never be written
to docs, logs, manifests, review packets, or release metadata. Config may reference an environment
variable name or local key path when needed for runtime validation, but release and review packets
must not expose secret values.
```

Deployment CLIs:

```text
python -m evidence_system.cli.check_infra
python -m evidence_system.cli.deploy_all
python -m evidence_system.cli.deploy_webarena
python -m evidence_system.cli.deploy_osworld
python -m evidence_system.cli.deploy_other_vps
python -m evidence_system.cli.deploy_local_androidworld
python -m evidence_system.cli.monitor
python -m evidence_system.cli.collect_results
python -m evidence_system.cli.resume_failed
```

Infra check:

```text
check_infra validates without running formal experiments:
SSH reachability where enabled, rsync availability, Python/conda/venv/docker readiness,
benchmark install and assets, result directories writable, dry-run path not pointing at formal
full results, LLM API key environment variables exist where needed without logging values, disk
space, network targets, machine role uniqueness and domain routing, current git commit and config
hash, deployment manifest consistency.
```

Monitor/collect/resume:

```text
monitor reports machine status, domain progress, task status, failure category, retry status,
cost/log availability, and stuck jobs. It must not treat UNRESOLVE as execution failure and must
not treat agent-caused FAIL as infra exclusion.

collect_results preserves original machine path, run id, attempt id, config hash, git commit,
raw logs, artifact manifests, LLM logs, and failure records. It must be repeatable without
duplicate samples.

resume_failed retries only recoverable infra/pre-run/logging failures under policy. It preserves
all attempts and identifies exactly one final_attempt. It does not retry UNRESOLVE as a failure.
```

Risks GPT Pro should inspect:

- Are machine role constraints sufficient to avoid routing WebArena/OSWorld/AndroidWorld incorrectly?
- Does monitor wording prevent confusing UNRESOLVE with runtime failures?
- Does collect/resume preserve denominator integrity?
- Does secret handling avoid exposing API keys or SSH key material in review/release artifacts?

Source correspondence:

- `计划.md`: deployment and VPS roles.
- `实验说明.md`: WebArena dedicated VPS, OSWorld dedicated VPS, AndroidWorld local, other domains on other VPS.
- `工程文件说明.md`: canonical CLI mapping and deployment/failure schema coverage.

### 14. `docs/acceptance_tests.md`

Purpose:

```text
This file freezes Step 1 acceptance criteria and later gates that Step 2-12 implementations must satisfy.
```

Step 1 acceptance:

```text
Step 1 is complete when:
- all required docs exist under docs/.
- review packet exists at reviews/packets/step01_spec_freeze_review_packet.md.
- no formal runner/scorer/adapter/schema/freezer code has been implemented as part of Step 1.
- no formal scored records, formal metrics, formal freeze file, or paper outputs are created.
- docs state P0/P1/P2/P3 full scope and appendix/diagnostic paper-output gate.
- docs state canonical domain identifiers and display-name separation.
- docs state phase, experiment_type, and priority schema.
- docs state record_slot, attempt, final_attempt, completed_record, and infra_exclusion_record semantics.
- docs state adapter/scorer boundary.
- docs state pre-scoring contract lock and prediction freeze.
- docs state native evaluator artifact decisive-evidence rule.
- docs state R1-R7 taxonomy and upstream-priority rule.
- docs state R1-R7 formal semantics, boundaries, examples, and golden fixture requirements.
- docs state INFRA_EXCLUDED, COUNTED_ONLY_SCORE null, and stronger_measurement gates.
- docs state LLM logging and human-time boundaries, including tab:cost human-time-only rule.
- docs state paper mapping coverage and paper-output details.
```

Paper mapping coverage gate:

```text
Required coverage:
tab:views, tab:unresolve-taxonomy, tab:domains, tab:main-results-A, tab:denominator-audit,
tab:main-results-B, tab:prediction-outcomes, tab:main-results-C, tab:pairwise-margins,
tab:top-unresolve-reasons, tab:audit-rerun, tab:per-agent, tab:cost,
tab:contract-drafting-metadata, tab:update, fig:hero, fig:evidence-counting, fig:case-cards,
app:per-agent, app:cost, app:contract-drafting-details, app:aux-domains, app:osworld,
app:judge, app:update, app:release, Formal Definitions, app:macro-contract.

Step 1 check result: all labels above are covered in experiments/paper_mapping.md.

Paper generation fails closed if any required paper_mapping label is missing, unmapped, mapped to
fallback or manual empirical data, mapped to smoke/dry_run/mock output, or mapped to an undeclared
non-formal appendix/diagnostic output. The only allowed exception is a synchronized update to paper
text and manifest that removes or changes the declared output.
```

Schema gates:

```text
Invalid fixtures must cover:
non-canonical domain id fails.
display name used as id fails.
missing phase/experiment_type/priority fails.
status=COMPLETED without evidence label fails.
UNRESOLVE without R1-R7 reason or unresolve_level fails.
SUCCESS/FAIL with unresolve_reason fails.
INFRA_EXCLUDED with evidence label fails.
INFRA_EXCLUDED entering evidence envelope fails.
COUNTED_ONLY_SCORE not null when SUCCESS+FAIL=0 fails.
stronger_measurement without sidecar/appendix/manifest mapping fails.
missing official provenance for decisive native evaluator artifact fails.
raw_run.native_label decisive use without locked artifact mapping fails.
OSWorld evaluator_failure/evaluator_unstable mapped to evidence UNRESOLVE fails.
adapter raw output missing contains_final_evidence_label=false fails.
```

Contract/freeze gates:

```text
P0 case unit without locked contract blocks preflight/full/scoring.
contract lock time after scoring start blocks scoring.
drafter forbidden inputs block contract use.
unsupported native-aligned requirement without stronger_measurement mapping blocks lock/freeze.
prediction registry not frozen before scoring blocks scoring.
scoring without freeze file blocks scoring.
manifest/paper_mapping/official_split/contract/schema/scorer/bootstrap/audit/rerun hash drift blocks scoring or paper outputs.
official split fewer than 100 eligible P0 cases without frozen manifest exception blocks scheduling/scoring.
pairwise_equality_tolerance or P1-P4 boundary rule missing before scoring blocks aggregation.
pairwise_equality_tolerance not set to a frozen value or explicit 需要从 locked manifest 确认
placeholder before formal freeze blocks aggregation.
formal pre_scoring_freeze.json created during Step 5 development blocks formal progression.
preflight record not declared in the frozen P0 manifest enters formal scored records fails.
smoke or dry_run output enters formal scored records, metrics, tables, figures, appendix empirical
outputs, or final report fails.
concrete Agent A-D, contract_drafter, or judge_only model id/version pin/temperature/prompt
hash/API-key env value hardcoded in code, tests, runner, scorer, paper generation, or review
packets fails unless the value is inside an explicitly synthetic config fixture.
```

Adapter/scorer gates:

```text
adapter writes raw run record and artifact manifest, not final scored record.
adapter produces no final SUCCESS/FAIL/UNRESOLVE.
adapter output must include contains_final_evidence_label=false; true, missing, or contradictory
final evidence fields fail.
artifact paths and sha256 values are present.
official runner/evaluator provenance is present when native evaluator output may be decisive.
smoke and dry_run outputs cannot enter formal results.
AgentDojo paired arms are preserved.
WebArena routes only to WebArena VPS.
OSWorld-Verified separates infra/pre-run failure, evaluator failure/unstable, and evidence UNRESOLVE.
judge-only input is blind to native_label, native_score, native evaluator pass/fail scalar,
outcome label, evidence label, UNRESOLVE reason, scored values, paper-output values, and agent identity.

scorer refuses unlocked contract.
scorer refuses hash mismatch.
scorer refuses post-lock clarification for native-aligned main result.
scorer refuses artifact sha mismatch.
scorer refuses native_label-only decisive evidence.
scorer refuses outcome_label, prior outcome verdict, previous run outcome, previous scored/evidence
label, runner summary verdict, adapter summary verdict, judge-only label, alternate-view verdict,
and paper-output value as decisive evidence.
scorer verdict_engine rejects agent_id, agent family, model id, provider, and model version as inputs.
scorer fixture where only agent identity changes must keep the same verdict_engine output hash.
scorer implementation with any agent identity condition branch fails static or behavioral validation.
scorer emits exactly one R1-R7 reason for each UNRESOLVE.
scorer has positive and negative golden fixtures for R1, R2, R3, R4, R5, R6, and R7.
scorer has overlap fixtures for R3-over-R1, R4-over-R1, R5-over-arm-specific-missing-evidence,
R7-over-R1/R4, and R6-versus-validation-failure.
scorer applies upstream-priority rule deterministically.
scorer excludes stronger_measurement from native-aligned main envelope.
scorer refuses INFRA_EXCLUDED input as completed scored record.
```

Stats/paper gates:

```text
N = SUCCESS + FAIL + UNRESOLVE.
width = UNRESOLVE / N.
bootstrap clusters by case unit.
prediction outcomes are only supported/falsified/inconclusive.
interval touching threshold is inconclusive unless inclusive rule was frozen.
pairwise equality uses frozen tolerance; ordinary overlap is ?.
if the paper has not specified pairwise_equality_tolerance, the stats plan must carry
需要从 locked manifest 确认 until a formal frozen value is set before scoring.
rerun subset is Agent A, 10 case units/domain, 40 case units, 50 episodes.
audit is 100 records, 25/domain, stratified stress sample.
audit sampler represents counted records, UNRESOLVE records, and native/evidence disagreement
records within each domain whenever all three buckets are non-empty.
audit sampler records bucket_empty with source counts when a required bucket is absent and follows
the frozen redistribution rule.
audit sampler omitting any non-empty required bucket fails and blocks tab:audit-rerun.
contract-drafting LLM logs include contract_draft_id, case_unit_id, evidence_contract_id when
assigned, visible_input_hash, hidden_input_assertion_hash, source_bundle_hash, and call_id.
locked contract metadata back-references the exact contract-drafting LLM call_id and contract_draft_id.
missing contract-drafting call linkage blocks tab:contract-drafting-metadata and LLM cost provenance.
R1-R7 taxonomy kappa computed only where both auditors mark UNRESOLVE.
audit and review blind-input fixtures exclude agent identity, native_label, native_score, native
evaluator pass/fail scalar, outcome label, scored values, paper-output values, counting decision,
UNRESOLVE reason, and alternate view verdicts.
tab:views shares provenance across views.
tab:cost reads only human-time logs.
fig:hero panel (b) includes only four P0 main domains.
fig:case-cards has case-level provenance and artifact ids.
app:update exact funnel is enforced.
matched-budget controls use same proposal/selection budget.
judge-only metrics are diagnostic.
final report cost/latency/failure values require provenance.
final paper output has no fillfromdata or empirical fallback values.
```

Risks GPT Pro should inspect:

- Are acceptance tests concrete enough for Step 2-12 implementation?
- Are any gates missing for first-class schemas such as deployment, failure, paper output, audit, rerun, release?
- Should Step 1 acceptance require a spec freeze manifest, or is that Step 12/formal flow only?

Source correspondence:

- `工程文件说明.md`: Step 12 validation gates and per-step acceptance.
- `计划.md`: schema coverage, paper outputs, audit/rerun/stats gates.
- `实验说明.md`: final success conditions.
- Paper: labels, formulas, audit/rerun, release, macro contract.

## Contract With The Paper

This Step 1 spec packet aligns with the paper as follows:

- Native-aligned evidence contracts are predeclared, source-supported, minimal, and locked before scoring.
- Contract drafter is blind to agent identity, traces, native scores, and outcomes.
- Contract-drafting LLM calls are linked to locked contracts by contract_draft_id and exact call_id.
- Completed records enter exactly one of counted-SUCCESS, counted-FAIL, or UNRESOLVE.
- INFRA_EXCLUDED / infra-pre-run failure is separate from evidence UNRESOLVE.
- Evidence envelope uses completed scored denominator only.
- P0 scale is 1600 planned record_slots and 2000 stored episodes, with AgentDojo paired arms.
- Agent A-D are measurement probes, not leaderboard entries, and concrete model/version/prompt values are config/locked-manifest data.
- Scorer verdict computation is isolated from agent identity; agent metadata is bound only after verdict computation for provenance/grouping.
- Outcome labels, prior verdicts, previous scored labels, adapter/runner summaries, judge-only labels, alternate views, and paper-output values cannot be decisive scorer evidence.
- Predictions freeze before scoring and use case-cluster bootstrap interval rules.
- Audit sampling includes counted, UNRESOLVE, and native/evidence disagreement buckets within each domain whenever all three exist.
- P1 audit/rerun sizes match the paper.
- P2/P3 appendix and diagnostic outputs remain separate from P0 native-aligned main envelope.
- `tab:cost`, `fig:hero`, `fig:case-cards`, `app:update`, matched-budget controls, judge-only metrics, and final report provenance gates are explicitly covered.
- Final paper outputs cannot use `\fillfromdata`, row fallbacks, figure layout values, mock outputs, smoke output, or dry-run output as empirical results.

## Known Non-Goals

Step 1 does not:

- implement `src/evidence_system/`.
- create formal schemas or validators.
- draft, review, or lock actual evidence contracts.
- create prediction registry freeze files.
- create formal `results/manifests/pre_scoring_freeze.json`.
- run adapters or official benchmarks.
- score records.
- aggregate metrics or bootstrap intervals.
- generate tables, figures, appendix, result macros, final report, or release package.
- modify `configs/agents.yaml`, `configs/infra.yaml`, `experiments/experiment_manifest.yaml`, or `experiments/paper_mapping.md`.

The packet contains only specification excerpts and review questions.

## Risk Checklist

Please inspect these potential blocking risks:

- Adapter/scorer boundary: any wording that allows adapter, official runner, monitor, collector, or paper-output code to emit final SUCCESS/FAIL/UNRESOLVE.
- Evidence contract lifecycle: any route to preflight/full/scoring before native-aligned locked contracts exist.
- Native evaluator use: any route where `raw_run.native_label`, native score, pass/fail scalar, or runner summary becomes decisive without locked artifact mapping/path/sha/provenance/direct read.
- R1-R7 taxonomy: any ambiguity that permits multiple reasons, non-fixed labels, or domain-specific extra reasons in formal outputs.
- INFRA_EXCLUDED: any path where infra/pre-run failures enter evidence envelope or carry evidence labels.
- COUNTED_ONLY_SCORE: any path where SUCCESS+FAIL=0 outputs 0, 1, empty string, `\fillfromdata`, or a fabricated value.
- P0 denominator: any ambiguity between 1600 planned record_slots, completed_records, infra_exclusions, and denominator audit.
- Official split exception: any risk of using non-official, duplicated, smoke-test, appendix, or synthetic cases when eligible split <100.
- Deterministic selection: any missing freeze input for hash function, salt hash, eligible set, smoke exclusions, order, seeds, or rerun subset.
- Prediction freeze: any missing hash input that could alter scoring, stats, or paper outputs.
- Step 5: any wording that would allow formal `pre_scoring_freeze.json` during freeze-mechanism development.
- Artifact provenance: any missing official runner/evaluator field needed for decisive native evaluator evidence.
- Judge-only: any missing blindness field, especially native label, native score, evaluator scalar, outcome, scored values, paper-output values.
- Post-lock clarification: any route into native-aligned main result instead of sensitivity report only.
- Paper mapping: any missing required label or `fillfromdata`/fallback gate.
- Audit sampling: any implementation that samples 25/domain but omits counted, UNRESOLVE, or native/evidence disagreement strata when those buckets are non-empty.
- Contract drafting provenance: any locked contract without exact LLM call_id, contract_draft_id, visible_input_hash, and hidden-input assertion hash linkage.
- Artifact manifest projection: any verdict_engine path that receives full artifact manifest with agent identity or model/provider identity fields.
- Preflight failure: any route from failed formal preflight validation to full run without retry/resume under the same frozen slots, or any replacement/cherry-picking of preflight case units.
- Paper output detail gates: `tab:views`, native-score-inside-envelope, `fig:hero` panel (b), `fig:case-cards`, `app:update`, matched-budget, judge-only, final_report provenance.
- Cost boundary: any route where LLM/OpenRouter/VPS/benchmark compute fills `tab:cost`.
- Secrets: any review/release path that records real API keys, SSH private key contents, or live credentials.

## Questions For GPT Pro

1. Does the Step 1 spec fully preserve the paper's evidence contract, counting, denominator, and envelope semantics?
2. Are adapter and scorer responsibilities separated strongly enough to prevent native summaries or adapters from becoming final evidence labels?
3. Are the native evaluator decisive-evidence requirements complete and enforceable?
4. Does the R1-R7 taxonomy plus upstream-priority rule match the paper and prevent schema drift?
5. Are INFRA_EXCLUDED and completed scored records separated clearly enough?
6. Is COUNTED_ONLY_SCORE undefined/null behavior sufficiently specified?
7. Does the spec handle P0 1600 planned record_slots vs completed denominator correctly?
8. Are official split <100 exceptions and deterministic case selection frozen early enough?
9. Are freeze inputs complete enough to prevent post-result scoring, stats, or paper-output changes?
10. Does the Step 5 freeze-file prohibition prevent premature formal `pre_scoring_freeze.json` generation?
11. Are artifact official runner/evaluator provenance fields sufficient for scorer use of native evaluator artifacts?
12. Is judge-only diagnostic fully blinded and clearly non-headline?
13. Does post-lock clarification / superseded contract handling prevent contamination of native-aligned main results?
14. Are paper mapping coverage and detailed paper-output gates complete?
15. Is `tab:cost` protected from LLM/VPS/benchmark-cost contamination?
16. Is the audit sampler's within-domain counted/UNRESOLVE/native-evidence-disagreement stratum rule specific enough?
17. Is contract-drafting LLM call linkage to locked contracts schema-testable enough?
18. Is sanitized artifact-manifest projection sufficient to prevent agent identity leakage into verdict_engine?
19. Is preflight failure behavior strict enough to prevent replacing or cherry-picking frozen preflight slots?
20. Is anything too vague for Step 2-12 implementation, such that GPT Pro should block Step 2 until Step 1 docs are revised?

## Acceptance Criteria

GPT Pro should return `ALLOW_NEXT_STEP` only if:

- Step 1 docs and this packet are self-contained enough to review without local file access.
- There are no blocking omissions in adapter/scorer boundary, contract lifecycle, native evaluator evidence, R1-R7 taxonomy, result schema conditions, freeze inputs, audit/rerun/stats rules, cost logging, release/rescorer, VPS runtime, or paper-output gates.
- All unconfirmed formal values are explicitly marked as one of:
  - `需要从论文确认`
  - `需要从 locked manifest 确认`
  - `需要从 scored manifest 填充`
  - `需要从 benchmark 官方 split 确认`
- The packet does not ask GPT Pro to review formal implementation code, because Step 1 intentionally did not implement formal code.
- The decision would allow Step 2 Repo Bootstrap to begin without reopening Step 1 for known blocking spec gaps.
