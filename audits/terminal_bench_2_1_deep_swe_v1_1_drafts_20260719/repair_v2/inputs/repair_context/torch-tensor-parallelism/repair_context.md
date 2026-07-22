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
- case_unit_id: `torch-tensor-parallelism`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: torch-tensor-parallelism
domain: terminal_bench_2_1
task_id: terminal-bench/torch-tensor-parallelism
native:
  user_goal:
    text: Create `/app/parallel_linear.py` implementing `ColumnParallelLinear` and `RowParallelLinear` so they shard `master_weight` per rank, zero-initialize bias when used, reproduce full linear outputs with the specified gather/reduce semantics, and yield correct weight and bias gradients for world sizes 1, 2, and 4.
    support:
    - official/instruction.md::1-19
  benchmark_success:
    text: The official verifier succeeds only if `pytest` exits 0 on `/tests/test_outputs.py`, which means `test_parallel_linear_exists` passes and every parametrized `test_column_parallel_linear` and `test_row_parallel_linear` case passes.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_parallel_linear_exists
    - official/tests/test_outputs.py::test_column_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  checked_by:
    text: '`official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`; the test file checks file existence plus the released column-parallel and row-parallel initialization, output, and gradient assertions.'
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_parallel_linear_exists
    - official/tests/test_outputs.py::_test_column_parallel_linear
    - official/tests/test_outputs.py::_test_row_parallel_linear
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the structured pytest report show whether `test_parallel_linear_exists` passed and whether every parametrized `test_column_parallel_linear` and `test_row_parallel_linear` case passed, failed, or errored?
    support:
    - case_packet.md::74-86
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_parallel_linear_exists
    - official/tests/test_outputs.py::test_column_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  - artifact: verifier/test-stdout.txt
    question: Does pytest stdout corroborate full collection/execution of `/tests/test_outputs.py` and identify any pass/fail/error outcomes for the existence, column-parallel, or row-parallel checks?
    support:
    - case_packet.md::74-86
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_parallel_linear_exists
    - official/tests/test_outputs.py::test_column_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  - artifact: verifier/test-stderr.txt
    question: Does pytest stderr show collection, import, multiprocessing, distributed, or runtime errors that make the verifier run fail even if individual assertion results are incomplete elsewhere?
    support:
    - case_packet.md::74-86
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::_test_column_parallel_linear
    - official/tests/test_outputs.py::_test_row_parallel_linear
  success_if:
  - text: Retained verifier evidence shows `test_parallel_linear_exists` passed, establishing that `/app/parallel_linear.py` existed at verification time.
    support:
    - official/tests/test_outputs.py::test_parallel_linear_exists
  - text: Retained verifier evidence shows every parametrized `test_column_parallel_linear` case passed, which under the released checks means the column-parallel layer had the expected per-rank weight slice, the expected bias slice when enabled, reference-matching forward output, and reference-matching local weight and bias gradients.
    support:
    - official/tests/test_outputs.py::_test_column_parallel_linear
    - official/tests/test_outputs.py::test_column_parallel_linear
  - text: Retained verifier evidence shows every parametrized `test_row_parallel_linear` case passed, which under the released checks means the row-parallel layer had the expected per-rank weight slice, the full bias copy when enabled, reference-matching forward output from pre-scattered inputs, and reference-matching local weight and bias gradients.
    support:
    - official/tests/test_outputs.py::_test_row_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  fail_if:
  - text: Retained verifier evidence shows `test_parallel_linear_exists` failed.
    support:
    - official/tests/test_outputs.py::test_parallel_linear_exists
  - text: Retained verifier evidence shows any parametrized `test_column_parallel_linear` case failed or errored.
    support:
    - official/tests/test_outputs.py::_test_column_parallel_linear
    - official/tests/test_outputs.py::test_column_parallel_linear
  - text: Retained verifier evidence shows any parametrized `test_row_parallel_linear` case failed or errored.
    support:
    - official/tests/test_outputs.py::_test_row_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  - text: Retained verifier evidence shows `/tests/test_outputs.py` ended with a nonzero pytest outcome because of collection, import, multiprocessing, distributed, or other runtime error before all official checks passed.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_parallel_linear_exists
    - official/tests/test_outputs.py::test_column_parallel_linear
    - official/tests/test_outputs.py::test_row_parallel_linear
  undecided_if:
  - text: The retained verifier artifacts do not establish either a full passing pytest run for `/tests/test_outputs.py` or a specific failed/error test or other nonzero pytest outcome; for example, `verifier/ctrf.json` and pytest stdout/stderr are missing, truncated, or mutually inconclusive.
    support:
    - case_packet.md::57-86
    - official/tests/test.sh::18-30
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_user_goal: missing_official_api_in_user_goal
native.user_goal omits the officially specified constructor signatures and torch.nn.Module inheritance.

Required correction: Expand native.user_goal to state the complete official intent, including both exact constructor signatures and module inheritance, while leaving their untested exactness outside native success.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::class declarations and constructor signatures

### stronger_conditions: missing_api_stronger_condition
stronger.additional_conditions is empty even though the instruction explicitly requires exact class inheritance and constructor signatures that the released verifier does not inspect.

Required correction: Add a case-specific stronger condition for torch.nn.Module inheritance and the exact specified constructor parameter lists, explain that the tests only exercise call compatibility, and name retained source/state artifacts capable of assessing the final definitions.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::class declarations and constructor signatures, official/tests/test_outputs.py::_test_column_parallel_linear, official/tests/test_outputs.py::_test_row_parallel_linear

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::class declarations and constructor signatures': heading 'class declarations and constructor signatures' not found
- $.native.user_goal.support[1] pointer 'official/instruction.md::tensor-parallel behavior and test scope': heading 'tensor-parallel behavior and test scope' not found
- $.native.benchmark_success.support[0] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::pytest invocation': symbol 'pytest invocation' not found
- $.native.checked_by.support[4] pointer 'official/tests/test_outputs.py::parametrization': symbol 'parametrization' not found
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[1] pointer 'official/tests/test.sh::pytest invocation': symbol 'pytest invocation' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/test_outputs.py::released tests': symbol 'released tests' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[1] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.native.success_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[2] pointer 'official/tests/test.sh::pytest invocation and status mapping': symbol 'pytest invocation and status mapping' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/instruction.md::class declarations and constructor signatures': heading 'class declarations and constructor signatures' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'official/instruction.md::class declarations and constructor signatures': heading 'class declarations and constructor signatures' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::class declarations and constructor signatures': heading 'class declarations and constructor signatures' not found`
