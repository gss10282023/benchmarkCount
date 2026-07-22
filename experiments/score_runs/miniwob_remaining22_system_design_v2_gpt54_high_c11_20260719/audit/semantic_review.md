# MiniWoB remaining-22 v2 semantic score review

## Scope and method

All 66 records were reviewed against the locked checklist, the exact retained `native_evaluator_output.json`, the model's decisive pointers, and the separately retained released label. The review does not alter any checklist or score.

The concrete native cross-check is independent of the released label: valid final validation with `done=true`, binary `reward=1.0`, and positive `info.RAW_REWARD_GLOBAL` supports S; a completed record with reward `0.0`, non-positive raw reward, invalid page/URL, or final non-completion supports F under the locked MiniWoB rules.

## Native review

- All 66 native verdicts match the concrete final validator fields: 33 S and 33 F.
- All decisive pointers resolve to retained checklist/evidence locations and avoid summary-only `native_label`/`native_score` fields.
- All 66 released labels independently match the native verdicts after scoring: 33 success/S and 33 fail/F.
- Therefore the batch has zero native/released-label disagreement records.

## Stronger-measurement review

The 24 records from the eight cases with locked stronger conditions were reviewed separately:

- `click-checkboxes` (3): stronger S; the retained final checkbox states match the runtime request exactly.
- `draw-circle` (3): stronger F; native is already F and retained paths/browser state contradict a complete circle centered on the marker.
- `email-inbox-forward` and `email-inbox-forward-nl-turk` (6): stronger F because native is F. Per-condition checks are retained as contradicted where sender identity is established and undecided where the failed run does not establish it.
- `generate-number` (3): stronger S; Generate precedes Submit and the retained generated values satisfy the runtime less-than requirement.
- `odd-or-even` (3): stronger F. Agent A is the sole native S plus stronger F record: binary native reward is `1.0` because raw reward is positive, but `RAW_REWARD_GLOBAL=0.3333333333333333` is partial rather than full classification credit. Agents B and C are native F and stronger F.
- `terminal` (3): stronger F because native is F; the exact literal-extension deletion condition remains undecided in the failed runs.
- `use-colorwheel-2` (3): stronger S; runtime target and submitted RGB value match exactly.

Totals are stronger S=9, F=15, NA=42. The one native S plus stronger F record is reported only as a stronger-measurement result and is not treated as a benchmark conflict.

## Generation and retry review

The sealed batch contains 66 successful final scores. Nine records needed a second model attempt (75 attempts total): eight first attempts exited nonzero and one first attempt was rejected by scoring guardrails. Every saved final attempt exits successfully, passes the output schema and guardrails, matches the final `score.json`, and retains its attempt-level events, telemetry, stderr/stdout, reasoning, and model output.

## Conflict conclusion

There are no native/released-label disagreements, so the separate record-level conflict audit has an empty denominator. Confirmed benchmark conflicts: 0. Stronger failure was not used as a conflict inference.
