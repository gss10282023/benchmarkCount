# candidate116 checklist repair pipeline

This directory is a fail-closed repair layer over immutable `wave_003`.  It
never edits `wave_003`, legacy `results/`, `paper_result_packages/`,
`official100`, packet inputs, or the frozen v3 drafting snapshot.  A repaired
case becomes eligible only through a concrete 116-case **effective wave**;
downstream QC and reviews must inspect that wave, not a mixture selected at
promotion time.

## Gates and artifact flow

1. `build_scope_aware_wave3_guard.py` preserves and binds the original
   hard-coded wave3 guard (including `status=fail`), records explicitly named
   live nonbinding-file drift, and separately proves equality of protected data
   roots/official100/packet inputs and all v3 snapshot/live-origin bindings.
2. `build_repair_selection.py` merges the exact 116 per-case automatic QC
   reports with non-overlapping manual audit partitions.  It has explicit
   adapters only for:
   - `androidworld_wave003_manual_semantic_audit/v1` (`case_unit_id`), and
   - `androidworld_wave_003_manual_semantic_audit_batch/v1` (`case_id`).
   Unknown schemas, overlap, gaps, hash mismatch, or status/issue disagreement
   stop the build.
3. `prepare_checklist_repair.py` writes content-addressed repair packets and a
   prelock.  Old checklist/audit prose is tagged as untrusted repair guidance;
   the verbatim full case packet is the sole semantic authority.  The prelock
   freezes Codex login, `gpt-5.6-sol`, `xhigh`, read-only sandbox, six workers,
   the immutable v3 batch runner, the repair prompt, every input, and the
   scope-aware drift evidence before any repair call.
4. `run_checklist_repair_batch.py` invokes the immutable v3 runner only for
   selected repairs.  A nonempty output is rejected; an explicit restart moves
   the *entire* old tree into an incident archive first.  Each successful case
   gets a deterministic diff and hash-bound repair provenance.  This is the
   only model-calling step.
5. `build_effective_checklist_wave.py` physically composes exactly 116 cases:
   `origin=wave_003` for retained cases and `origin=repair` for repaired cases.
   It writes normalized batch records pointing back to the original full
   packets and per-case `effective_origin.json` records.  Neither source wave is
   overwritten.
6. `strict_effective_checklist_qc.py` imports the prelocked original
   `strict_draft_automatic_qc.py` as `strict_qc_base.py` and calls its exact
   `per_case_qc` function for all 116 effective cases.  Only location-derived
   globals are rebound to the original candidate/source context.  A clean
   116/116 automatic pass still does not authorize promotion.
7. New independent human reviews must bind the exact effective checklist and
   effective QC report.  `prepare_repair_aware_promotion.py` accepts only
   116/116 clean reviews and emits a content-addressed handoff containing every
   case origin and repair provenance.
8. `verify_repair_aware_final_manifest.py` rejects a final contracts freeze or
   348-slot manifest unless both bind that handoff, the effective manifest, the
   scope-aware guard, and the per-case provenance.  The legacy hard-coded
   promotion script is therefore not a valid direct path for a repaired cohort;
   a repair-aware promoter must add the extension fields required by this
   verifier.

## Commands (preparation only; no repair call)

Paths below are repository-relative.  Use the repository `.venv` Python.

```bash
.venv/bin/python rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/scripts/build_scope_aware_wave3_guard.py \
  --pre-snapshot rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/validation/pre_generation_wave_003_readonly_snapshot.json \
  --post-snapshot rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/validation/post_generation_wave_003_readonly_snapshot.json \
  --original-guard rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/validation/wave_003_readonly_pre_post_guard_report.json \
  --source-prelock rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/freeze/androidworld_candidate116_codex_cli_draft_prelock_v3.json \
  --live-drift-path neurips_ed_track_minimal/scripts/run_agentdojo_full_draft_review.py \
  --live-drift-path neurips_ed_track_minimal/scripts/case_checklist_review.py \
  --live-drift-path neurips_ed_track_minimal/scripts/review_case_checklist_with_codex.py \
  --live-drift-path neurips_ed_track_minimal/prompts/review_agentdojo_full_checklist.prompt.md \
  --output-dir rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/incidents/wave_003_scope_aware

.venv/bin/python rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/scripts/build_repair_selection.py \
  --source-prelock rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/freeze/androidworld_candidate116_codex_cli_draft_prelock_v3.json \
  --automatic-qc-root rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/automatic_qc_v3 \
  --manual-audit rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/manual_audits/wave_003_batch_a.json \
  --manual-audit rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/manual_audits/wave_003_batch_b.json \
  --manual-audit rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/manual_audits/wave_003_batch_c1.json \
  --manual-audit rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/manual_audits/wave_003_batch_c2.json \
  --output rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/repair_generation/selection/wave_003_repair_selection.json

.venv/bin/python rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/scripts/prepare_checklist_repair.py \
  --source-prelock rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/freeze/androidworld_candidate116_codex_cli_draft_prelock_v3.json \
  --automatic-qc-root rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/automatic_qc_v3 \
  --audit-selection rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/repair_generation/selection/wave_003_repair_selection.json \
  --original-generation-guard rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/validation/wave_003_readonly_pre_post_guard_report.json \
  --changed-path-incident rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/incidents/wave_003_scope_aware/wave_003_live_tool_drift_incident.json \
  --scope-aware-guard rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/draft_generation/incidents/wave_003_scope_aware/wave_003_scope_aware_guard.json
```

Review the generated prelock before running the printed command.  Do **not**
start `run_checklist_repair_batch.py` until that review is complete.

## Post-repair commands

```bash
.venv/bin/python <snapshotted-run_checklist_repair_batch.py> --prelock <repair-prelock.json>
.venv/bin/python <snapshotted-build_effective_checklist_wave.py> --prelock <repair-prelock.json>
.venv/bin/python <snapshotted-strict_effective_checklist_qc.py> \
  --effective-manifest <effective-wave/_effective_manifest.json> \
  --report-root <new-effective-qc-root>
.venv/bin/python <snapshotted-prepare_repair_aware_promotion.py> \
  --effective-manifest <effective-wave/_effective_manifest.json> \
  --effective-qc-root <new-effective-qc-root> \
  --human-review-root <new-effective-human-review-root>
```

All roots are create-once.  No command silently resumes, overwrites, or treats
a model proposal/QC pass as an independent human acceptance.
