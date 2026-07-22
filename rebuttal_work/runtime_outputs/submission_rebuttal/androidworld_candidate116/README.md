# AndroidWorld candidate116 packet workspace

This directory is the isolated Step 4B source-packet workspace. It does not modify the submitted baseline, legacy `results/`, or the checked-in `official100` selector.

## Acceptance state

- Static packet validation: **pass** (116/116 candidate packets; 16/16 extra packets).
- Independent strict acceptance: **pass** (116 semantic records, 116 unique real drafter prompts, and 348 predeclared slots).
- Goal mechanisms: 57 format templates, 33 computed goals, 1 branch template, and 25 IR proto prompts.
- Metadata/code audit: 23 differences are explicitly recorded; runtime goal/evaluator sources take precedence. All 25 incidental `abc.py` provenance labels are excluded from canonical provenance.
- Runtime/device preflight: **blocked**. This is a separate gate and does not weaken static packet checks.
- Legacy-root guard: complete content-tree hashes and entry counts are byte-identical before/after for `neurips_ed_track_minimal`, `results/`, and `paper_result_packages`; the checked-in official100 selector hash is also unchanged. Pre-existing non-immutable flags are recorded rather than misreported as immutable.
- Experiment manifests remain honest `draft` / prelock manifests with empty contract locks. The draft-input sidecar is frozen, but no contract draft or run output exists yet.

## Canonical outputs

- `manifests/androidworld_candidate116_manifest.json`
- `manifests/androidworld_extra16_manifest.json`
- `official_splits/androidworld_candidate116_selected_task_sources.json`
- `official_splits/androidworld_extra16_selected_task_sources.json`
- `case_packets/androidworld/<case_id>/`
- `semantic_records/androidworld_candidate116_semantic_index.json`
- `semantic_records/androidworld_candidate116_metadata_code_conflicts.json`
- `source_bundles/androidworld_candidate116_source_bundle.json`
- `source_bundles/androidworld_extra16_source_bundle.json`
- `ledgers/androidworld_candidate116_348_slot_ledger.json`
- `draft_config/androidworld_candidate116_drafter_config.json`
- `prompts/androidworld_candidate116_rendered_prompt_index.json`
- `freeze/androidworld_candidate116_draft_input_freeze.json`
- `shared_source/androidworld_source_snapshot_manifest.json`
- `validation/pre_operation_readonly_snapshot.json`
- `validation/post_operation_readonly_snapshot.json`
- `validation/strict_acceptance_report.json`
- `validation/static_validation_report.json`
- `validation/runtime_preflight_report.json`
- `validation/SHA256SUMS`

Run `python3 scripts/build_and_validate.py --verify-only` to recheck all retained artifacts without rebuilding them.
