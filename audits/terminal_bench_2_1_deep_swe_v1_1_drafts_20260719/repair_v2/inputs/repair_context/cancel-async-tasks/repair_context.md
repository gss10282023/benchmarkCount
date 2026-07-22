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
- case_unit_id: `cancel-async-tasks`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: cancel-async-tasks
domain: terminal_bench_2_1
task_id: terminal-bench/cancel-async-tasks
native:
  user_goal:
    text: Implement `/app/run.py` exporting async `run_tasks(tasks, max_concurrent)` for system Python so async jobs run subject to the concurrency cap and task cleanup code still runs after keyboard interrupt cancellation.
    support:
    - official/instruction.md::1-3
  benchmark_success:
    text: 'Native success is the official verifier criterion: the pytest run launched by `official/tests/test.sh` passes all six checks in `official/tests/test_outputs.py` (`test_run_py_file_exists`, `test_tasks_run_concurrently`, `test_tasks_obey_max_concurrent`, `test_tasks_cancel_below_max_concurrent`, `test_tasks_cancel_at_max_concurrent`, and `test_tasks_cancel_above_max_concurrent`).'
    support:
    - official/tests/test.sh::19-23
    - official/tests/test_outputs.py::test_run_py_file_exists
    - official/tests/test_outputs.py::test_tasks_run_concurrently
    - official/tests/test_outputs.py::test_tasks_obey_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_below_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_at_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_above_max_concurrent
  checked_by:
    text: The official verifier script `official/tests/test.sh`, which runs pytest against `official/tests/test_outputs.py` and emits retained verifier reports/logs.
    support:
    - official/tests/test.sh::17-23
    - case_packet.md::60-71
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the official pytest run record pass/fail/error status for each of the six verifier checks in `official/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::19-23
    - case_packet.md::60-71
    - official/tests/test_outputs.py::test_run_py_file_exists
    - official/tests/test_outputs.py::test_tasks_run_concurrently
    - official/tests/test_outputs.py::test_tasks_obey_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_below_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_at_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_above_max_concurrent
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is missing or ambiguous, does verifier stdout show pytest completion and any assertion failure details for the official checks?
    support:
    - case_packet.md::60-71
    - official/tests/test.sh::19-23
  - artifact: verifier/test-stderr.txt
    question: If needed, does verifier stderr show import, timeout, or other pytest/verifier errors from the official run?
    support:
    - case_packet.md::60-71
    - official/tests/test.sh::19-23
  success_if:
  - text: Retained verifier evidence establishes that all six named official pytest checks passed in the verifier run.
    support:
    - case_packet.md::48-52
    - official/tests/test.sh::19-23
    - official/tests/test_outputs.py::test_run_py_file_exists
    - official/tests/test_outputs.py::test_tasks_run_concurrently
    - official/tests/test_outputs.py::test_tasks_obey_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_below_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_at_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_above_max_concurrent
  fail_if:
  - text: Retained verifier evidence establishes that any of the six named official pytest checks failed or errored in the verifier run.
    support:
    - case_packet.md::50-52
    - official/tests/test.sh::19-23
    - official/tests/test_outputs.py::test_run_py_file_exists
    - official/tests/test_outputs.py::test_tasks_run_concurrently
    - official/tests/test_outputs.py::test_tasks_obey_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_below_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_at_max_concurrent
    - official/tests/test_outputs.py::test_tasks_cancel_above_max_concurrent
  - text: Retained verifier logs establish that the pytest invocation in `official/tests/test.sh` exited nonzero before all six checks passed because of an import, timeout, or other verifier-side error.
    support:
    - case_packet.md::50-52
    - official/tests/test.sh::19-23
    - case_packet.md::60-71
  undecided_if:
  - text: Retained non-label verifier artifacts are missing or incomplete, so they do not establish either that all six official checks passed or that any official check failed/errored.
    support:
    - case_packet.md::48-52
    - case_packet.md::60-71
    - official/tests/test.sh::19-23
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### stronger_conditions: missing-api-annotation-condition
The official instruction declares parameter and return annotations for `run_tasks`, but the released tests only import and exercise the function and never inspect its annotations. This supported, measurable noncoverage belongs in the stronger layer.

Required correction: Add a stronger condition requiring the final exported declaration to preserve the instructed `tasks: list[Callable[[], Awaitable[None]]]`, `max_concurrent: int`, and `-> None` annotations, with the evaluator’s lack of annotation inspection stated in the rationale and inventory-listed code-bearing artifacts named for assessment.

Cited diagnostic locations: official/instruction.md::1, official/tests/test_outputs.py::test_run_py_file_exists, official/tests/test_outputs.py::test_tasks_run_concurrently, checklist.yaml::stronger.additional_conditions

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.success_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.fail_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.fail_if[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/instruction.md::1': heading '1' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'official/instruction.md::1': heading '1' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::1': heading '1' not found`
