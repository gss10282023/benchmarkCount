# Result Schema Specification

## Formal Result Directories

Formal result objects live under validated directories:

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

Smoke and dry-run outputs must use non-formal locations or explicit `phase=smoke|dry_run` records and cannot be promoted into formal scored records.

## Scored Record Classes

Formal result schema distinguishes:

- `completed_scored_record`: completed benchmark execution eligible for SUCCESS/FAIL/UNRESOLVE.
- `infra_exclusion_record`: benchmark/pre-run failure excluded from evidence-envelope denominator and included in denominator audit.

They may share one physical schema with conditional constraints, but the semantics must remain separate.

## Completed Scored Record

Minimum shape:

```json
{
  "schema_version": "scored_record/v1",
  "domain": "agentdojo|appworld|webarena_verified|tau3_retail|androidworld|workarena|osworld_verified|judge_only|maintenance_update|matched_budget_controls",
  "domain_display_name": "...",
  "benchmark_name": "...",
  "case_unit_id": "...",
  "task_id": "...",
  "record_slot_id": "...",
  "record_id": "...",
  "episode_ids": [],
  "run_id": "...",
  "attempt_id": "...",
  "final_attempt": true,
  "seed": 0,
  "agent_id": "...",
  "phase": "preflight|full|rerun",
  "experiment_type": "main|appendix|diagnostic|audit|maintenance_update|matched_budget_control",
  "priority": "P0|P1|P2|P3",
  "status": "COMPLETED",
  "native_label": "success|fail|unknown|null",
  "native_score": null,
  "diagnostic_status": "not_applicable|completed|infra_excluded|evaluator_failure|evaluator_unstable",
  "appendix_failure_class": "none|infra_pre_run|evaluator_failure|evaluator_unstable|evidence_unresolve",
  "evidence_label": "SUCCESS|FAIL|UNRESOLVE",
  "unresolve_reason": "R1|R2|R3|R4|R5|R6|R7|null",
  "unresolve_level": "trace_level|instrument_level|null",
  "claim_scope": "native_aligned|stronger_measurement",
  "stronger_measurement_mapping": null,
  "evidence_contract_id": "...",
  "evidence_contract_version": "...",
  "evidence_contract_hash": "...",
  "artifact_manifest_path": "...",
  "artifact_manifest_sha256": "...",
  "scorer_version": "...",
  "scorer_code_hash": "...",
  "freeze_manifest_hash": "...",
  "result_schema_hash": "...",
  "taxonomy_version": "...",
  "config_hash": "...",
  "git_commit_hash": "...",
  "started_at": "...",
  "ended_at": "..."
}
```

Conditional constraints:

- `status=COMPLETED` requires `evidence_label` to be SUCCESS, FAIL, or UNRESOLVE.
- UNRESOLVE requires exactly one `unresolve_reason` and one `unresolve_level`.
- SUCCESS and FAIL require null `unresolve_reason` and null `unresolve_level`.
- `claim_scope=stronger_measurement` requires sidecar, appendix, or manifest mapping and is excluded from native-aligned main envelope.
- `phase=smoke|dry_run` cannot be a formal completed scored record.
- `phase=preflight` may be a formal completed scored record only for case units predeclared as P0 preflight slots in the frozen manifest and only after preflight validation passes; otherwise it remains non-formal integration output.
- `native_label` and `native_score` are diagnostic metadata unless decisive use is backed by locked artifact mapping and official provenance.

## Infra Exclusion Record

Minimum shape:

```json
{
  "schema_version": "infra_exclusion_record/v1",
  "domain": "...",
  "domain_display_name": "...",
  "case_unit_id": "...",
  "task_id": "...",
  "record_slot_id": "...",
  "run_id": "...",
  "attempt_id": "...",
  "final_attempt": true,
  "agent_id": "...",
  "phase": "preflight|full|rerun",
  "experiment_type": "...",
  "priority": "P0|P1|P2|P3",
  "status": "INFRA_EXCLUDED",
  "evidence_label": null,
  "unresolve_reason": null,
  "unresolve_level": null,
  "failure_category": "infra_pre_run",
  "recoverable": false,
  "retry_count": 0,
  "raw_log_path": "...",
  "failure_record_path": "...",
  "entered_evidence_denominator": false,
  "entered_denominator_audit": true
}
```

`INFRA_EXCLUDED` must not carry SUCCESS, FAIL, or UNRESOLVE evidence labels. It is excluded from evidence envelope denominator and included in denominator audit.

## Aggregate Metrics

Aggregate metrics are first-class schema objects. For each reporting group:

```json
{
  "schema_version": "aggregate_metrics/v1",
  "domain": "...",
  "group_key": "...",
  "N_completed_scored_records": 0,
  "SUCCESS": 0,
  "FAIL": 0,
  "UNRESOLVE": 0,
  "coverage": 0.0,
  "counted_only_score": null,
  "counted_only_score_undefined_reason": "no_counted_records|null",
  "lower": 0.0,
  "upper": 0.0,
  "width": 0.0,
  "source_scored_record_ids": [],
  "denominator_audit_ref": "...",
  "freeze_manifest_hash": "..."
}
```

Validation requires `N_completed_scored_records = SUCCESS + FAIL + UNRESOLVE`. `COUNTED_ONLY_SCORE` is defined only when SUCCESS+FAIL > 0. If no counted records exist, it is explicit null with reason `no_counted_records`.

## Denominator Audit

Denominator audit records:

```text
attempted_record_slots
completed_records
infra_excluded
agent_caused_failures
formally_documented_missing_or_blocked
retry_attempt_count
notes
```

P0 denominator audit must be able to report attempted=1600 even when completed scored denominator `N` is smaller due to allowed infra exclusions.

## Paper Output Source Mapping

Every table, figure, appendix, macro, and final report value must trace to scored records, denominator audit, human-time logs, LLM logs, release metadata, or manifest records as appropriate. No paper cell may be filled from TeX fallback values, old scaffold output, mock output, or dry-run output.

## OSWorld Fields

OSWorld-Verified and similar diagnostics use:

```text
diagnostic_status: not_applicable | completed | infra_excluded | evaluator_failure | evaluator_unstable
appendix_failure_class: none | infra_pre_run | evaluator_failure | evaluator_unstable | evidence_unresolve
```

Evaluator failure/unstable is not evidence UNRESOLVE.
