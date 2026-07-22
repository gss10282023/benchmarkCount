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

- benchmark: `terminal_bench_2_1`
- case_unit_id: `llm-inference-batching-scheduler`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: llm-inference-batching-scheduler
domain: terminal_bench_2_1
task_id: terminal-bench/llm-inference-batching-scheduler
native:
  user_goal:
    text: Produce `plan_b1.jsonl` and `plan_b2.jsonl` for the two request buckets so every request is assigned exactly once to a batch with a valid shape, using at most 8 unique shapes across both buckets, meeting the stated per-bucket cost, pad-ratio, p95-latency, and sequential-time thresholds, while leaving the input files unchanged.
    support:
    - official/instruction.md::1-48
  benchmark_success:
    text: 'Native success is the official verifier pytest run passing all six task tests: `test_output_files_exist`, `test_input_data_integrity`, `test_generate_and_schema`, `test_solution_shape_feasibility_and_batch_consistency`, `test_solution_coverage_no_duplicates`, and `test_performance_thresholds`.'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_input_data_integrity
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
    - official/tests/test_outputs.py::test_performance_thresholds
  checked_by:
    text: Official verifier script `official/tests/test.sh` runs pytest on `official/tests/test_outputs.py`; native success is established by that test suite passing.
    support:
    - official/tests/test.sh::1-24
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: 'Does the retained CTRF report show pass/fail outcomes for the six official verifier tests that define native success: output existence, input integrity, schema/coverage, shape feasibility with batch consistency, no-duplicate coverage, and performance thresholds?'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_input_data_integrity
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
    - official/tests/test_outputs.py::test_performance_thresholds
  - artifact: artifacts/**
    question: Do the retained artifacts include the emitted `plan_b1.jsonl` and `plan_b2.jsonl` contents needed to inspect request coverage, assigned shapes, batch consistency, and recompute the cost, padding, latency, and unique-shape metrics used by the verifier?
    support:
    - official/instruction.md::1-48
    - official/tests/test_outputs.py::_plan_metrics
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
    - official/tests/test_outputs.py::test_performance_thresholds
    - official/tests/cost_model_for_tests.py::CostModel.plan_metrics
  success_if:
  - text: '`verifier/ctrf.json` records passes for `test_output_files_exist` and `test_input_data_integrity`.'
    support:
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_input_data_integrity
  - text: '`verifier/ctrf.json` records passes for `test_generate_and_schema`, `test_solution_shape_feasibility_and_batch_consistency`, and `test_solution_coverage_no_duplicates`, establishing exact-once coverage of each bucket, valid aligned shapes, and identical shapes within each batch.'
    support:
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
  - text: '`verifier/ctrf.json` records a pass for `test_performance_thresholds`, establishing bucket 1 meets cost <= `3.0e11`, pad_ratio <= `0.055`, p95_latency_ms <= `2.1e6`, sequential_timecost <= `2.7e8`; bucket 2 meets cost <= `4.8e10`, pad_ratio <= `0.15`, p95_latency_ms <= `2.1e5`, sequential_timecost <= `3.2e7`; and the combined unique-shape count across both plans is <= `8`.'
    support:
    - official/tests/test_outputs.py::test_performance_thresholds
    - official/tests/test_outputs.py::_plan_metrics
    - official/tests/cost_model_for_tests.py::CostModel.plan_metrics
  fail_if:
  - text: '`verifier/ctrf.json` records a failure for `test_output_files_exist` or `test_input_data_integrity`.'
    support:
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_input_data_integrity
  - text: '`verifier/ctrf.json` records a failure for `test_generate_and_schema`, `test_solution_shape_feasibility_and_batch_consistency`, or `test_solution_coverage_no_duplicates`; this covers missing or duplicate request_ids, invalid shape fields, seq-alignment violations, infeasible assigned shapes, inconsistent shapes within a batch, or per-bucket shape-count violations.'
    support:
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
  - text: '`verifier/ctrf.json` records a failure for `test_performance_thresholds`; this covers either bucket exceeding any configured cost, pad_ratio, p95_latency_ms, or sequential_timecost limit, or the combined unique-shape cap exceeding `8`.'
    support:
    - official/tests/test_outputs.py::test_performance_thresholds
    - official/tests/test_outputs.py::_plan_metrics
    - official/tests/cost_model_for_tests.py::CostModel.plan_metrics
  undecided_if:
  - text: Retained non-label evidence does not include a decisive verifier report for the official tests, and the retained plan artifacts are missing or incomplete, so neither full verifier success nor any specific verifier failure can be established.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_input_data_integrity
    - official/tests/test_outputs.py::test_generate_and_schema
    - official/tests/test_outputs.py::test_solution_shape_feasibility_and_batch_consistency
    - official/tests/test_outputs.py::test_solution_coverage_no_duplicates
    - official/tests/test_outputs.py::test_performance_thresholds
    rationale: Native success and failure are defined by the official verifier tests; without retained outcomes for those tests or enough retained plan evidence to replay all of them, the case is undecidable.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_semantics_incomplete
The native failure rules do not reproduce test.sh’s treatment of every nonzero pytest outcome; they cover named test failures but not collection errors, test errors, interruptions, or comparable execution failures.

Required correction: Define native success by the exact pytest command returning zero and native failure by retained non-label evidence that it returned nonzero, including failed tests, errors, collection failures, or interruptions. Add test stdout/stderr as conditional decisive evidence for those outcomes.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::pytest invocation and status branch

### decision_rules_sfu: sfu_error_gap
The current rules can leave a decisive pytest error unclassified because it is not a named test failure and the U condition requires the decisive verifier report to be absent.

Required correction: Make F cover any retained non-label evidence establishing a nonzero official pytest outcome or a specific deterministic test violation, and define U simply as the absence of sufficient evidence for either S or F.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics

### source_support_pointers: user_goal_pointer_truncated
The line pointer `official/instruction.md::1-48` ends before material portions of the claimed user goal, including the target thresholds and deliverables.

Required correction: Replace the truncated range with concrete pointers covering Goal, the target-threshold table, and Deliverables, or cite the complete native agent-visible instruction section in the packet.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], official/instruction.md::Baseline, official/instruction.md::Deliverables

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.success_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.fail_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.fail_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[3].support[0] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::Goal': heading 'Goal' not found
- $.native.user_goal.support[1] pointer 'official/instruction.md::Baseline target-threshold table': heading 'Baseline target-threshold table' not found
- $.native.user_goal.support[2] pointer 'official/instruction.md::Deliverables': heading 'Deliverables' not found
- $.native.benchmark_success.support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.decisive_artifacts[0].support[0] pointer 'official/tests/test.sh::pytest invocation': symbol 'pytest invocation' not found
- $.native.decisive_artifacts[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.decisive_artifacts[2].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.decisive_artifacts[3].support[0] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.success_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.success_if[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.fail_if[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.fail_if[1].support[0] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found`
