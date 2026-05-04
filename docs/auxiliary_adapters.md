# Auxiliary And Diagnostic Adapters

## General Rule

Auxiliary adapters are part of the complete P0/P1/P2/P3 system scope, but they do not enter the P0 native-aligned main envelope unless the paper and manifest are updated to make them main experiments. Declared appendix or diagnostic outputs block paper generation if missing, unless the paper text and manifest are updated together.

Each auxiliary adapter follows `docs/adapter_interface.md`: it saves raw evidence and provenance only. Evidence labels are produced only by the locked-contract scorer or by a locked diagnostic scoring spec where the paper declares diagnostic semantics.

## AndroidWorld

Canonical domain id: `androidworld`.

Experiment type: `appendix`.

Priority: P2.

Machine role: local AndroidWorld machine.

Required raw evidence:

- device or emulator state.
- task-specific success-check artifacts.
- evaluator artifacts.
- screenshots or structured UI state when available.
- run logs, LLM logs, environment hash, benchmark version, and official split / appendix manifest references.

Counts and selected case units are `需要从 locked manifest 确认`. AndroidWorld is an appendix negative control and cannot enter the four-domain P0 aggregate.

## WorkArena

Canonical domain id: `workarena`.

Experiment type: `appendix`.

Priority: P2.

Machine role: other VPS unless the locked infra manifest says otherwise.

Required raw evidence:

- browser state.
- enterprise workflow artifacts.
- benchmark validator inputs/outputs.
- task policy or workflow description.
- runner logs, environment hash, official split / appendix manifest references.

Counts and selected case units are `需要从 locked manifest 确认`. WorkArena is an appendix negative control and cannot enter the P0 aggregate.

## OSWorld-Verified

Canonical domain id: `osworld_verified`.

Experiment type: `appendix`.

Priority: P2.

Machine role: OSWorld-Verified VPS.

The OSWorld-Verified appendix stress test must distinguish execution and evaluator problems from evidence UNRESOLVE. Raw/scored schema must support:

```text
diagnostic_status: not_applicable | completed | infra_excluded | evaluator_failure | evaluator_unstable
appendix_failure_class: none | infra_pre_run | evaluator_failure | evaluator_unstable | evidence_unresolve
```

`evaluator_failure` and `evaluator_unstable` must not be silently mapped to evidence UNRESOLVE. Evidence UNRESOLVE applies only when a completed evidence record lacks enough raw evidence to decide a locked claim. Counts and selected case units are `需要从 locked manifest 确认`.

## Judge-Only Diagnostic

Canonical domain id: `judge_only`.

Experiment type: `diagnostic`.

Priority: P3.

Judge-only is diagnostic, not a headline baseline. The judge model values are read from `configs/agents.yaml` and locked manifest. The judge input must be blind to:

```text
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
```

Allowed input includes judge-readable task text, official policy, locked contract, required artifacts, trace without agent identity, and post-run artifacts. The diagnostic reports success/fail/inconclusive, disagreement rates, and judge assignments on evidence-UNRESOLVE records.

## Maintenance Update

Canonical domain id: `maintenance_update`.

Experiment type: `maintenance_update`.

Priority: P3.

The exact funnel is frozen by the paper:

```text
6 raw proposals per main domain
3 selected per main domain
24 proposed total
12 selected total
15 executed total because AgentDojo selected candidates are paired
```

The adapter must preserve proposal, selection, execution, checked, counted, UNRESOLVE, top reason, and artifact provenance. It cannot report only candidate task counts.

## Matched-Budget Controls

Canonical domain id: `matched_budget_controls`.

Experiment type: `matched_budget_control`.

Priority: P3.

Controls must use the same proposal/selection budget as the evidence-aware update process. Required controls are one-shot generation, evidence-blind generation, and static benchmark refresh. Outputs report countable updates and envelope-width reduction with provenance.

## Missing Auxiliary Outputs

If AndroidWorld, WorkArena, OSWorld-Verified, judge-only, maintenance update, matched-budget controls, release metadata, formal definitions mapping, or macro-contract data are declared in the paper/manifest but missing, paper outputs fail closed. A missing appendix cannot be hidden by omitting rows or using fallback text.
