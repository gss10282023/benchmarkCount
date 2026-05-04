# Artifact Schema Specification

## Artifact Manifest

Every raw run has an `artifact_manifest/v1` object. The manifest is the only allowed index from scored records to raw evidence. It must be immutable after final collection except through a versioned superseding manifest.

Because the full artifact manifest includes provenance fields such as `agent_id`, the scorer verdict engine must not receive the full manifest directly. Scoring uses a sanitized artifact-manifest projection that preserves artifact ids, paths, sha256 values, official runner/evaluator provenance, visibility, source hashes, and contract requirement ids, while excluding `agent_id`, agent family, model/provider identity, leaderboard/display labels, and other provenance-only identity fields. The full manifest is reattached only after verdict computation by the provenance binder.

Minimum top-level fields:

```json
{
  "schema_version": "artifact_manifest/v1",
  "run_id": "...",
  "record_slot_id": "...",
  "attempt_id": "...",
  "final_attempt": true,
  "domain": "...",
  "phase": "...",
  "experiment_type": "...",
  "priority": "...",
  "case_unit_id": "...",
  "task_id": "...",
  "agent_id": "...",
  "evidence_contract_id": "...",
  "evidence_contract_version": "...",
  "evidence_contract_hash": "...",
  "source_bundle_hash": "...",
  "official_splits_hash": "...",
  "environment_hash": "...",
  "artifacts": []
}
```

Each artifact entry contains:

```json
{
  "artifact_id": "...",
  "artifact_type": "trace|post_state|database_snapshot|api_log|browser_artifact|network_trace|file|message|tool_log|native_evaluator_input|native_evaluator_output|screenshot|structured_output|stdout|stderr|llm_call_log|other",
  "path": "...",
  "sha256": "...",
  "size_bytes": 0,
  "created_at": "...",
  "producer_role": "adapter|official_runner|official_evaluator|benchmark|scorer",
  "producer_name": "...",
  "producer_version": "...",
  "producer_command_hash": "...",
  "official_runner": false,
  "official_evaluator": false,
  "evaluator_name": null,
  "evaluator_version": null,
  "source_bundle_hash": "...",
  "official_splits_hash": "...",
  "environment_hash": "...",
  "verified_evaluator_output_object_hash": null,
  "artifact_created_after_run_start": true,
  "artifact_contract_requirement_ids": [],
  "visibility": "public|access_controlled|not_released",
  "redaction_status": "not_needed|pending|redacted|blocked"
}
```

## Official Provenance For Decisive Native Evidence

Artifact manifest entries that can support native evaluator decisive evidence must include:

```text
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
```

If native evaluator artifact provenance is missing, validation fails or scorer emits `UNRESOLVE R6` only when the locked contract and discovery point allow that. If native label scalar exists without artifact mapping, decisive use is refused. If sha256 mismatches, scoring is refused.

## Required Artifact Classes By Domain

`agentdojo`:

- benign arm trace and injected arm trace.
- workspace state across both arms.
- tool calls, files, messages.
- security and utility native output artifacts, kept separate.
- paired-arm linkage metadata.

`appworld`:

- database snapshots or state queries.
- API logs.
- unit-test artifacts.
- native field checks and evaluator inputs/outputs.

`webarena_verified`:

- browser artifacts.
- network trace.
- structured final output.
- verifier inputs.
- official verifier outputs with official evaluator provenance.

`tau3_retail`:

- tool records.
- backend/database state.
- policy-relevant evidence.
- identity-resolution artifacts.

Appendix domains add their own manifest requirements in `docs/auxiliary_adapters.md`.

## Visibility And Release

Artifacts are classified:

- `public`: safe to publish directly.
- `access_controlled`: requires credential/synthetic personal data scrubbing, access control, or gated release.
- `not_released`: live credentials, real third-party keys, SSH private keys, or artifacts enabling non-sandbox side effects.

UNRESOLVE visibility must remain even when full traces are gated: case identifier, locked claim, evidence contract, taxonomy code, and envelope contribution remain visible.

## Redaction And Secret Rule

No artifact manifest may contain real API keys, SSH private key contents, live credentials, or secret values. Paths to local key files may appear only in infra configuration and must not be copied into review packets or release artifacts. Any secret-like value in raw logs blocks release until redacted or classified not_released.
