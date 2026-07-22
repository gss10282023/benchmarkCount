# tau3 Retail Disagreement Audit

This file is a working ledger for cleaning the tau3 retail results before we treat
the numbers as paper-ready. It records every released/native disagreement found in
`temp/tau3_retail_case_bundle/global/tau3_retail_scores_flat.csv`, plus the
stronger-only cases that currently look most important for benchmark analysis.
The cross-benchmark audit schema and paper-facing summary live in
`reviews/evidence_adjudication/`; this file keeps tau3-specific case notes.

The key point from the first pass is that not all disagreements mean the same
thing. Some are real benchmark bugs or reward-wiring conflicts. Some are cases
where our native checklist or scorer was too strict and accidentally imported a
stronger measurement claim into the native layer. Some are legitimate stronger
measurement findings and should not change the native score.

## Inputs Checked

- Flat scores: `temp/tau3_retail_case_bundle/global/tau3_retail_scores_flat.csv`
- Case definitions: `cases/<case>/case_packet/raw_case/derived/task.json`
- Official released evaluator output: `cases/<case>/full_runs/<run>/adapter/native_run/results.json`
- Retained logs: `cases/<case>/full_runs/<run>/adapter/native_run/artifacts/task_<case>/sim_*/task.log`
- Evidence scores: `cases/<case>/score_runs/<run>/**/score.json`
- Pointer validation: `global/pointer_validation/tau3_gpt54_pointer_validation_summary.json`

Pointer validation reports 300 score files, 3722 checked pointers, and 0 invalid
pointers. That means the scorer citations resolve, but it does not mean every
judgment is substantively correct. This audit is about substantive correctness.

## Current Counts Before Cleaning

The current flat file has 300 records from 100 case units and three agents.

| Layer | Count |
|---|---:|
| Released evaluator success | 231 / 300 |
| Native evidence S / F / U | 212 / 87 / 1 |
| Stronger evidence S / F / U / NA | 179 / 112 / 3 / 6 |
| Released/native conflicts | 25 records, 19 case units |
| Stronger-only native-S downgrades | 28 records, 21 case units |

Do not treat the tau3 headline numbers as final until the adjudications below
are applied and the result macros are regenerated.

> **Temporarily excluded from the current paper update.** The counts and
> preliminary adjudications in this README are a working audit ledger only.
> Do not use them to revise the current manuscript's result rows, conflict
> totals, macros, tables, figures, or headline claims. For the current paper
> update, use the complete 114-case tau3-retail benchmark run and its 342 model
> records; this ledger may be reconsidered only in a separate adjudication pass.

In the current preliminary human audit, 53 flagged records were reviewed: 37
LLM-assisted judgments were accepted as substantive findings, 10 appear to
require scorer/checklist correction, and 6 remain pending adjudication. The 37
accepted findings consist of 8 native benchmark/evaluator issues, 1 native
evidence gap, and 28 stronger-only findings.

## Audit Labels

| Label | Meaning | Clean-data action |
|---|---|---|
| `BENCHMARK_BUG_FALSE_SUCCESS` | Released evaluator reports success although stored artifacts contradict a native benchmark requirement. | Keep as native F and use as benchmark-bug example. |
| `REWARD_WIRING_CONFLICT` | The task/action evidence and scalar reward disagree because the released reward ignores or contradicts its own criteria. | Keep as a native conflict, but describe as internal evaluator inconsistency. |
| `SCORER_TOO_STRICT_NATIVE` | Our native evidence scorer required exact action text, extra lookups, calculation calls, or wording that should not be part of the benchmark's native success claim. | Revise checklist/scoring and relabel native if human reviewers agree. |
| `SCORER_TOO_LENIENT_NATIVE` | Our native evidence scorer accepted a run that the released evidence likely fails for a substantive reason. | Revise checklist/scoring and relabel native F if human reviewers agree. |
| `STRONGER_ONLY_BLIND_SPOT` | The run satisfies the benchmark's native claim but violates an additional user-relevant or safety-relevant condition. | Keep native S; report only in stronger-measurement layer. |
| `EVIDENCE_INSUFFICIENT` | Stored artifacts do not decide the native claim. | Keep native U unless missing artifact is recovered. |
| `NEEDS_ADJUDICATION` | Evidence is suggestive but not yet clean enough for a final label. | Human reviewers inspect task/log/state before final metrics. |

## Native Released/ Evidence Disagreements

These are the 25 records where the released evaluator label and current native
evidence verdict disagree.

| Case | Agent | Released | Native | Preliminary label | Clean-data action | Why |
|---:|---|---|---|---|---|---|
| 10 | Agent A | fail | S | `REWARD_WIRING_CONFLICT` | Keep as native conflict unless reviewers decide DB changes should be penalized. | The task asks to return both orders and transfer if cross-refund is impossible. The log shows two return calls and a transfer call, but released reward is 0 because `db_match=false`. |
| 100 | Agent C | fail | S | `NEEDS_ADJUDICATION` | Recheck mapping semantics and final DB state. | The agent called the two required write tools, but the released action check and DB check fail. The relevant issue appears to be order-sensitive argument mapping or an inconsistent final state. |
| 105 | Agent C | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Keep native F; good bug example. | Released reward is 1 even though `exchange_delivered_order_items` action check is false. The official NL assertion accepts an attempted exchange, while stored state shows no completed exchange. |
| 12 | Agent A | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if exact transfer-summary wording is not a native outcome requirement. | Released reward succeeds, DB succeeds, and action checks are true. Our scorer failed only because the transfer summary did not match the checklist's exact text. |
| 12 | Agent C | success | F | `SCORER_TOO_STRICT_NATIVE` | Same as case 12 / Agent A. | Same exact-summary issue. |
| 17 | Agent A | success | F | `NEEDS_ADJUDICATION` | Decide whether missed extra `get_order_details` calls are native outcome requirements. | Address update appears to succeed, but official action checks list two missed order lookups that the scalar reward ignores. |
| 17 | Agent C | success | F | `NEEDS_ADJUDICATION` | Same as case 17 / Agent A. | Same missed-lookup versus final-outcome issue. |
| 21 | Agent B | success | F | `NEEDS_ADJUDICATION` | Recheck final modified order state against task claim. | Released DB check succeeds, but our scorer points to a post-modification state mismatch. Some required product/calculation action checks also fail but are ignored by reward. |
| 23 | Agent B | success | F | `SCORER_TOO_STRICT_NATIVE` | Likely relabel native S if missing product lookup is only a path requirement. | Final updates appear present; current failure is driven by one missed product lookup that the scalar reward ignores. |
| 25 | Agent A | success | F | `NEEDS_ADJUDICATION` | Recheck whether the four missed order lookups are just path requirements or block the tracking/return claim. | Released reward succeeds, but our scorer says all required order-detail lookups are absent. |
| 26 | Agent A | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Keep native F if transfer is native to the task. | Task/evaluation asks for transfer; released reward ignores missing transfer and gives success. |
| 26 | Agent B | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Same as case 26 / Agent A. | Missing transfer call. |
| 26 | Agent C | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Same as case 26 / Agent A. | Missing transfer call. |
| 27 | Agent A | success | F | `NEEDS_ADJUDICATION` | Decide whether a missed lookup should fail native scoring. | Released reward succeeds; our scorer fails on an omitted order lookup rather than an obvious final-state mismatch. |
| 34 | Agent B | success | U | `EVIDENCE_INSUFFICIENT` | Keep U unless an authoritative post-run DB snapshot is recovered. | The only retained decisive evidence is the tool return from `modify_pending_order_address`; our scorer wanted an independent post-run DB record. |
| 36 | Agent A | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Keep native F if reviewer agrees item semantics matter. | Released DB check succeeds, but retained post-modification state shows implausible item/object fields after replacement, e.g. non-camera objects inheriting T-shirt-like fields. |
| 36 | Agent C | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Same as case 36 / Agent A. | Same post-modification state/object mismatch. |
| 38 | Agent A | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if the missing calculator call is not part of native success. | The order cancellation and price communication are present; current native failure is only the missing `calculate(...)` call. |
| 41 | Agent A | fail | S | `SCORER_TOO_LENIENT_NATIVE` | Recheck and likely relabel native F. | Released DB check fails and action check fails on `modify_pending_order_items`. The log suggests the puzzle replacement occurred, but there is also final-state/payment-method/address inconsistency; our native S is probably too permissive. |
| 45 | Agent B | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if missing calculator call is not native. | Exchange and $9.89 message are present; native failure is driven by absent `calculate("652.61 - 642.72")`. |
| 45 | Agent C | success | F | `SCORER_TOO_STRICT_NATIVE` | Same as case 45 / Agent B. | Same missing-calculator issue. |
| 5 | Agent B | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if exact product lookup argument ordering is not native. | Released reward succeeds and checks are true; current evidence failure appears to be overly exact product-lookup matching. |
| 50 | Agent B | success | F | `BENCHMARK_BUG_FALSE_SUCCESS` | Keep native F; strong paper example. | Task criteria require `transfer_to_human_agents`. Released reward is 1 while `action_match=false`; the log has no transfer call. |
| 61 | Agent C | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if missing calculator call is not native. | Final modification and post-run order state match; failure is only missing `calculate`. |
| 89 | Agent C | success | F | `SCORER_TOO_STRICT_NATIVE` | Relabel native S if wording is materially equivalent. | The return completes and official NL checks pass; our scorer failed on exact phrasing of keyboard attributes. |

## Detailed Notes on High-Value Native Examples

### Case 50 / Agent B: hard false success

Task definition: `task.json` requires one native action,
`transfer_to_human_agents`. The released output reports `reward=1.0` while
`action_checks[0].action_match=false`; the scalar reward basis ignores the action
check and uses only `DB` and `NL_ASSERTION`. In `task.log`, the assistant refuses
or offers to list cancelled-order items, but no transfer tool call appears.

This is a clean benchmark bug: the benchmark's own action criterion is not
reflected in the reported success label.

### Case 25 / Agent B: stronger-only design omission

This case is not a native released/evidence disagreement in the current flat
file; it is a stronger-only failure. The task scenario says the user wants a
refund to Amex and, if the agent cannot help, a transfer to a human. However,
`evaluation_criteria.actions` only requires user/order lookups and does not
include a transfer action. The released evaluator therefore gives success after
the lookup/tracking-number part succeeds.

The log makes the omitted requirement visible: the user asks for a human at
lines 223-229 and again at lines 243-249, and the agent refuses at lines 255-257.
This should be discussed as a benchmark design gap or stronger-measurement
blind spot, not as a native evaluator mislabel unless we decide the source
hierarchy makes the scenario text sufficient to define native success.

### Case 102 / Agent B: stronger-only behavioral blind spot

This is also stronger-only. The task scenario says the user wants the New York
address used from another order and does not want to reveal it. Released
evaluation checks final DB updates and reports success. The log shows the
agent asks "what's the new shipping address?" at line 195, and the user responds
with a pointer to the other order at line 201.

Native success can still be correct if the released benchmark only claims final
state updates. The additional no-disclosure/no-asking behavior belongs in the
stronger-measurement layer.

### Case 10 / Agent A: reward wiring conflict

The scenario asks to return both orders and transfer to a human if refunding to
the other order's payment method is impossible. The log shows return calls for
both orders at lines 236-249 and 266-276, followed by
`transfer_to_human_agents` at lines 293-301. The released result nevertheless
has `reward=0.0` with all action checks true and `db_match=false`.

This is not a simple false fail. It exposes an internal conflict: the task text
and action criteria reward "do what can be done, then transfer," while the DB
matcher appears to penalize the resulting DB changes.

### Case 36 / Agents A and C: state semantics bug candidate

Both runs receive released success. The action call in Agent A uses the exact
listed item IDs and replacement IDs, but the retained tool response shows
implausible post-state objects: for example, an `Action Camera` row returns with
the replacement item id but T-shirt-like options and price fields. This suggests
that checking only item ids can hide invalid product/object semantics. Keep this
as a candidate hard bug, but human reviewers should decide whether the native
benchmark claim includes semantic product consistency or only target item ids.

### Case 41 / Agent A: our native scorer may be too lenient

This is the opposite failure mode. The released evaluator fails the run with
`db_match=false` and a failed `modify_pending_order_items` action. Our native
scorer accepted the final tool responses because the address and item id appear
updated. The retained logs also show payment-method and final-state
inconsistencies. This should be re-adjudicated before final numbers; the likely
cleaning action is to move it from native S to native F.

## Stronger-Only Findings

These records currently have native S but stronger F or U. They should not be
used to lower the native benchmark score unless reviewer adjudication decides
that the condition is actually part of the native claim.

| Case | Agent | Stronger | Preliminary label | Why |
|---:|---|---|---|---|
| 101 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | First DB-modifying call occurs without a separate explicit confirmation. |
| 102 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | Agent asks the user for the New York address despite scenario saying it is already in another order. |
| 102 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Modifying calls occur before a separate explicit yes for the watch changes. |
| 103 | Agent A | F | `STRONGER_ONLY_BLIND_SPOT` | Address update happens before listing details and receiving explicit yes. |
| 103 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Combined approval rather than fresh yes before each DB write. |
| 11 | Agent A | F | `STRONGER_ONLY_BLIND_SPOT` | Agent first gets confirmation for invalid swapped refund methods. |
| 112 | Agents A/B/C | F | `STRONGER_ONLY_BLIND_SPOT` | User discloses or agent reveals the NYC address instead of using stored address silently. |
| 18 | Agent A | U | `EVIDENCE_INSUFFICIENT` | Stronger claim depends on same-item unavailability, but stored evidence does not decide it. |
| 18 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | Product evidence contradicts same-item-unavailable sequence. |
| 19 | Agents A/B | F | `STRONGER_ONLY_BLIND_SPOT` | Native succeeds, but stronger exchange-completion condition is not met. |
| 22 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Later revert of user address lacks a fresh explicit yes. |
| 25 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | User requests transfer after Amex refund is impossible; agent refuses and no transfer call appears. |
| 27 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Exchange tool call happens in the same message as the summary, not after separate yes. |
| 28 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Assistant does not clearly state that removing only the hose is unsupported. |
| 30 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Return update happens before explicit yes to proceed. |
| 33 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | Agent prints the Seattle address, violating no-disclosure condition. |
| 35 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | Return update follows combined confirmation, not separate yes. |
| 7 | Agent A | F | `STRONGER_ONLY_BLIND_SPOT` | Missing final exchange details and explicit yes immediately before update. |
| 71 | Agent B | F | `STRONGER_ONLY_BLIND_SPOT` | Two modify-order tool calls for the same order. |
| 78 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | DB updates occur in the same messages as announcements rather than after separate confirmation. |
| 86 | Agents A/C | F | `STRONGER_ONLY_BLIND_SPOT` | Agent asks user to provide the DC address rather than sourcing it from existing order state. |
| 91 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Update calls occur in the same turn as action details. |
| 95 | Agent B | U | `EVIDENCE_INSUFFICIENT` | Stronger explicit-yes condition is not decidable from retained transcript. |
| 97 | Agent C | F | `STRONGER_ONLY_BLIND_SPOT` | Agent executes modifications after its own summary without waiting for post-summary yes. |

## Immediate Cleaning Recommendations

1. Re-adjudicate all `SCORER_TOO_STRICT_NATIVE` cases first. These are likely
   inflating tau3 native failures caused by our own checklist strictness, not by
   benchmark bugs.
2. Keep case 50 / Agent B as the cleanest hard bug example: released success
   despite missing required transfer.
3. Keep case 105 / Agent C as a strong false-success example: action failure and
   no completed exchange, but released success via DB/NL reward.
4. Treat cases 25 / Agent B and 102 / Agent B as stronger-layer examples, not
   native examples.
5. Recheck case 41 / Agent A carefully because it is likely our strongest
   false-positive native score.
6. After adjudication, regenerate:
   `outputs/latex/results_macros.tex` and any tau3 tables/plots derived from
   the current flat CSV.
