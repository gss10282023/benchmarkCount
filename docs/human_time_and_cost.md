# Human Time And Cost

## Boundary

Human-time logs measure trained annotator or adapter-author wall-clock work. They are separate from:

- LLM token/cost logs.
- VPS runtime or cloud bills.
- benchmark execution compute.
- local AndroidWorld machine runtime.

`tab:cost` is generated only from human-time logs. It must not read LLM/OpenRouter token costs, VPS runtime, benchmark runtime, or inferred estimates.

## Human Time Schema

Each activity writes `human_time/v1`:

```json
{
  "schema_version": "human_time/v1",
  "activity_id": "...",
  "reviewer_or_worker_id": "...",
  "role": "adapter_author|auditor|scorer_reviewer|release_reviewer|other",
  "activity_type": "contract_draft_review|contract_lock|evidence_scoring_review|unresolve_tagging|audit|rerun_review|setup|release_review",
  "domain": "...",
  "case_unit_id": null,
  "record_id": null,
  "started_at": "...",
  "finished_at": "...",
  "duration_minutes": 0.0,
  "action": "...",
  "source_artifacts": [],
  "notes": "...",
  "phase": "...",
  "experiment_type": "...",
  "priority": "...",
  "manifest_hash": "...",
  "contract_hash": null,
  "no_llm_cost_included": true,
  "no_vps_cost_included": true
}
```

Validation requires `started_at < finished_at`, non-negative duration, reviewer/worker id, action, and source artifact references where applicable.

## Cost Table Inputs

`tab:cost` requires per-domain:

- draft/lock contract minutes per case.
- score evidence minutes per record.
- tag UNRESOLVE minutes per record.
- per-domain one-time setup notes.

Contract-drafting LLM may reduce first-draft time, but human lock time is recorded separately and cannot be replaced by LLM time. Paper values are `需要从 scored manifest 填充` until human-time logs exist.

## Final Report Cost/Latency/Failure Provenance

Final report cost, latency, and failure statistics must have provenance. If the report includes LLM cost, VPS cost, runtime, or failure statistics, those values come from their own logs and are labeled separately from `tab:cost`. Missing provenance blocks those final report values.
