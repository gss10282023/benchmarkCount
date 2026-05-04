# Main Adapter Interface

## Boundary

An adapter runs an official benchmark or diagnostic runner and saves raw evidence. It never produces final evidence verdicts. It may save native evaluator outputs, native labels, native scores, runner summaries, and benchmark logs as raw artifacts, but it must not decide final `SUCCESS`, `FAIL`, or `UNRESOLVE`.

The formal adapter implementation lives under `src/evidence_system/adapters/`. A domain-specific command may expose:

```bash
python -m evidence_system.adapters.<canonical_domain> \
  --job-json <path> \
  --result-json <path> \
  --artifacts-dir <path> \
  --llm-calls-log <path> \
  --stdout-log <path> \
  --stderr-log <path>
```

The package CLI may wrap this via `python -m evidence_system.cli.run_domain`.

## Job Input

`job.json` is a validated `job.schema.json` object. Required fields include:

```json
{
  "schema_version": "job/v1",
  "run_id": "...",
  "record_slot_id": "...",
  "phase": "smoke|dry_run|preflight|full|rerun",
  "experiment_type": "main|appendix|diagnostic|audit|maintenance_update|matched_budget_control",
  "priority": "P0|P1|P2|P3",
  "domain": "agentdojo|appworld|webarena_verified|tau3_retail|androidworld|workarena|osworld_verified|judge_only|maintenance_update|matched_budget_controls",
  "domain_display_name": "...",
  "case_unit_id": "...",
  "task_id": "...",
  "agent_id": "Agent A|Agent B|Agent C|Agent D",
  "seed": 0,
  "attempt_id": "...",
  "attempt_index": 1,
  "evidence_contract_id": "...",
  "evidence_contract_version": "...",
  "evidence_contract_hash": "...",
  "agent_config_ref": "...",
  "benchmark_config_ref": "...",
  "official_split_ref": "...",
  "machine_role": "...",
  "expected_artifact_contract": {},
  "config_hash": "...",
  "manifest_hash": "...",
  "code_git_commit": "..."
}
```

`agent_config_ref` resolves to `configs/agents.yaml` plus locked manifest metadata. The job may include a resolved config snapshot for reproducibility, but formal validation fails if it disagrees with config and locked manifest. The job cannot hardcode Agent A-D, contract_drafter, or judge_only model/version/prompt values outside those sources.

## Raw Run Output

The adapter writes a `raw_run_record/v1` object, not a scored record. Required output groups:

- identity: run_id, record_slot_id, attempt_id, phase, experiment_type, priority, canonical domain id, case_unit_id, task_id, agent_id, seed.
- execution status: `raw_status`, start/end timestamps, benchmark started flag, timeout/abort fields, recoverable flag.
- episode ids: one episode for most domains; AgentDojo has benign and injected episode ids per record.
- official runner metadata: runner name, runner version, command hash, official split reference, source bundle hash, environment hash.
- native output metadata: native label/score as diagnostic metadata only, plus native evaluator artifact ids when present.
- artifact manifest path and hash.
- llm call log path and hash.
- stdout/stderr log paths and hashes.
- failure record path if execution failed before normal benchmark start.
- `contains_final_evidence_label=false`.

The adapter output must explicitly state that it contains no final evidence label. Missing `contains_final_evidence_label`, setting it to true, or carrying contradictory final evidence fields fails schema validation.

## Main Domains

The four main adapters use canonical domain ids:

- `agentdojo`: must preserve benign/injected arms, paired-arm linkage, workspace state, messages, files, tool calls, utility/security native outputs, and enough provenance to identify R5 paired-arm asymmetry.
- `appworld`: must preserve database state, API logs, unit-test artifacts, native field checks, and evaluator artifacts.
- `webarena_verified`: must run only on WebArena VPS role, preserve browser artifacts, network trace, structured final output, verifier inputs, official evaluator outputs, and verifier provenance.
- `tau3_retail`: must preserve tool records, backend/database state, policy-relevant evidence, identity-resolution evidence, and official task/policy references.

## Required Artifact Manifest

Every adapter writes `artifact_manifest/v1`. It lists each raw artifact with path, sha256, size, mime/type, created_at, producer, provenance, visibility class, and contract requirement ids.

Native evaluator output can support decisive evidence only when:

1. the locked contract lists it as allowed or required evidence;
2. the artifact manifest records path and sha256;
3. the provenance matches official runner/evaluator;
4. the scorer directly reads the artifact or a verified evaluator-output object.

If only `raw_run.native_label` or a runner summary scalar exists, the scorer refuses decisive use.

## Adapter Failure Semantics

Adapters classify failures without converting them to evidence labels:

- infra/pre-run failure: benchmark did not begin normally; write failure record and possible `infra_exclusion_record`.
- agent-caused failure after benchmark start: completed raw run; scorer may produce FAIL if native semantics supports fail.
- evaluator failure/unstable: for OSWorld-Verified and any diagnostic requiring evaluator status; do not silently map to UNRESOLVE.
- artifact/logging failure: raw execution may be complete, but evidence may be incomplete; scorer or validator decides whether validation fails or UNRESOLVE applies.

`INFRA_EXCLUDED` must not carry SUCCESS/FAIL/UNRESOLVE evidence labels and never enters the evidence-envelope denominator.

## Acceptance For Adapters

Every adapter smoke test must:

- use canonical domain id and separate display name.
- use phase, experiment_type, and priority fields.
- write raw artifacts and artifact manifest with hashes.
- include official runner/evaluator provenance where relevant.
- avoid real LLM calls unless the phase and test explicitly require them.
- avoid writing formal metrics, formal scored records, formal freeze files, or paper outputs.
- prove no final SUCCESS/FAIL/UNRESOLVE comes from adapter code.
- fail if raw run output is missing `contains_final_evidence_label=false`.
