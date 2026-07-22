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
- case_unit_id: `circuit-fibsqrt`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: circuit-fibsqrt
domain: terminal_bench_2_1
task_id: terminal-bench/circuit-fibsqrt
native:
  user_goal:
    text: Create `/app/gates.txt` with fewer than 32,000 lines, using the allowed gate-statement forms, so calling `/app/sim N` outputs `fib(isqrt(N)) % 2^32` after 32,000 simulation steps.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: 'Native success is official verifier success: `official/tests/test.sh` runs `pytest` on `/tests/test_outputs.py`, and all three tests there pass: `test_gates_file_exists`, `test_gates_file_size`, and `test_sqrt_fib`. In `test_sqrt_fib`, `/tests/sim.c` must compile, and `/app/sim` must return the expected integer for every fixed input in `test_cases`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::7-23
    - official/tests/test_outputs.py::56-147
  checked_by:
    text: Official task-specific verifier `official/tests/test.sh`, which records a CTRF pytest report for `/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::18-22
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest CTRF report show pass/fail status for `test_gates_file_exists`, `test_gates_file_size`, and `test_sqrt_fib`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::7-23
    - official/tests/test_outputs.py::56-147
  - artifact: verifier/test-stdout.txt
    question: If `test_sqrt_fib` ran, does verifier stdout show compilation failure, `/app/sim` execution/parsing errors, or any expected-vs-actual mismatch on the fixed `test_cases` list?
    support:
    - official/tests/test_outputs.py::63-70
    - official/tests/test_outputs.py::73-147
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr contain pytest or system errors needed to determine whether the official tests completed and why they failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::63-70
    - official/tests/test_outputs.py::119-147
  success_if:
  - text: Retained verifier evidence establishes that `test_gates_file_exists` passed, so `/app/gates.txt` existed when the official verifier ran.
    support:
    - official/tests/test_outputs.py::7-11
  - text: Retained verifier evidence establishes that `test_gates_file_size` passed, so `/app/gates.txt` had fewer than 32,000 lines.
    support:
    - official/tests/test_outputs.py::14-23
  - text: 'Retained verifier evidence establishes that `test_sqrt_fib` passed: compiling `/tests/sim.c` succeeded, and for every input in the verifier''s fixed `test_cases` list, `/app/sim` exited successfully, stdout parsed as an integer, and that integer equaled `fibonacci(isqrt(n)) % (2**32)`.'
    support:
    - official/tests/test_outputs.py::63-70
    - official/tests/test_outputs.py::73-147
  fail_if:
  - text: Retained verifier evidence establishes that `test_gates_file_exists` failed because `/app/gates.txt` did not exist.
    support:
    - official/tests/test_outputs.py::7-11
  - text: Retained verifier evidence establishes that `test_gates_file_size` failed because `/app/gates.txt` had 32,000 or more lines.
    support:
    - official/tests/test_outputs.py::14-23
  - text: Retained verifier evidence establishes that `test_sqrt_fib` failed because compiling `/tests/sim.c` failed, or some `/app/sim` invocation in the fixed `test_cases` list exited nonzero, or stdout was not parseable as an integer, or an actual output differed from the computed expected value.
    support:
    - official/tests/test_outputs.py::63-70
    - official/tests/test_outputs.py::73-147
  undecided_if:
  - text: The retained verifier artifacts do not reliably establish the pass/fail status of all three official pytest checks, or they omit the details needed to determine why `test_sqrt_fib` stopped before a definitive comparison result.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::7-23
    - official/tests/test_outputs.py::56-147
stronger:
  additional_conditions:
  - id: full_input_correctness
    text: Beyond native sampled testing, retained circuit artifacts establish that the produced `/app/gates.txt` computes `fib(isqrt(N)) % 2^32` for all inputs accepted by `/app/sim`, not only the verifier's fixed `test_cases` list.
    rationale: The official instruction states the circuit should work when calling `/app/sim N` generally, but the released evaluator checks only a finite hard-coded sample list.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained circuit artifacts include the final `/app/gates.txt` (or equivalent retained circuit source) with enough detail to establish correctness beyond the verifier's fixed sample list?
      support:
      - official/instruction.md::11-13
      - official/tests/test_outputs.py::73-147
    support:
    - official/instruction.md::11-13
    - official/tests/test_outputs.py::73-147
  - id: line_syntax_compliance
    text: Retained circuit artifacts establish that every line of the final `/app/gates.txt` uses one of the six gate-statement forms required by the instruction.
    rationale: The instruction explicitly constrains line syntax, but the released tests check existence, line count, and sampled outputs; the simulator ignores lines it cannot parse instead of making syntax compliance a direct native pass/fail condition.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained circuit artifacts include the final `/app/gates.txt`, and does that file show every line conforms to one of the allowed `out...` assignment forms?
      support:
      - official/instruction.md::1-7
      - official/tests/sim.c::100-181
    support:
    - official/instruction.md::1-7
    - official/tests/sim.c::100-181
    - official/tests/test_outputs.py::7-23
    - official/tests/test_outputs.py::56-147
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_not_exhaustive
native.fail_if does not reproduce the complete official verifier failure semantics because it recognizes only enumerated, diagnosed test causes. Retained evidence that the official pytest invocation failed or errored is sufficient for native F even if the precise cause is not retained.

Required correction: Add a general fail_if rule covering any retained non-label evidence that the task-specific pytest invocation did not complete successfully with all three tests passing, including failed or errored tests and other established nonzero pytest outcomes.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-27, case_packet.md::Native Evaluator Semantics

### decision_rules_sfu: undecided_requires_unnecessary_diagnosis
native.undecided_if incorrectly permits U when the reason test_sqrt_fib stopped is unavailable, even if retained evidence establishes that the official check failed.

Required correction: Define U solely as the absence of sufficient non-label evidence to establish either that all three official tests passed or that the official verifier criterion failed. Do not require a failure diagnosis before assigning F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], checklist.yaml::native.fail_if[2], case_packet.md::Native Evaluator Semantics
