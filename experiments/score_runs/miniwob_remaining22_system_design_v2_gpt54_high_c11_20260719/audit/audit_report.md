# MiniWoB remaining-22 v2 score audit

- Audit status: `complete`
- Records: 66 (cases: 22)
- Structurally valid: 66/66
- Native verdicts: `{"F": 33, "S": 33}`
- Released labels: `{"fail": 33, "success": 33}`
- Native/released agreement: 66; disagreements: 0
- Stronger verdicts: `{"F": 15, "NA": 42, "S": 9}`
- Native S + stronger F (reported only, not a conflict inference): 1
- Confirmed benchmark conflicts after separate record-level review: 0

## System-design checks

- checklist_freeze_precedes_scores: `True`
- released_label_blinded_from_model_workspace: `True`
- model_outputs_contain_only_native_and_stronger: `True`
- native_scored_as_S_F_U: `True`
- stronger_reported_separately: `True`
- stronger_not_used_as_conflict_inference: `True`
- disagreements_receive_separate_record_level_audit: `True`
- benchmark_conflict_requires_retained_and_source_pointers: `True`
- scorer_configuration_gpt54_high_default_nonfast_c11: `True`

## Disagreement records

No native/released-label disagreements.

## Validation errors

No structural, provenance, blinding, schema, or decisive-pointer errors.
