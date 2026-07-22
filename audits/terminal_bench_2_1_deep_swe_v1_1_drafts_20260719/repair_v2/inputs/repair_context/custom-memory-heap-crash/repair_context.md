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
- case_unit_id: `custom-memory-heap-crash`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: custom-memory-heap-crash
domain: terminal_bench_2_1
task_id: terminal-bench/custom-memory-heap-crash
native:
  user_goal:
    text: Fix the `/app/` program so the RELEASE build no longer crashes, while only changing `/app/user.cpp` and leaving no Valgrind-detected memory leaks.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: 'Native success requires retained verifier evidence that the official pytest suite passed all six task checks: protected files unchanged, debug compile succeeds, release compile succeeds, debug run exits 0, release run exits 0, and Valgrind on the release binary exits 0 with no definite leaks.'
    support:
    - official/tests/test.sh::20-24
    - official/tests/test_outputs.py::test_protected_files_not_modified
    - official/tests/test_outputs.py::test_program_compiles_debug
    - official/tests/test_outputs.py::test_program_compiles_release
    - official/tests/test_outputs.py::test_debug_build_runs_without_crash
    - official/tests/test_outputs.py::test_release_build_runs_without_crash
    - official/tests/test_outputs.py::test_no_memory_leaks_with_valgrind
  checked_by:
    text: Official task verifier `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` and treats the suite outcome as the benchmark check.
    support:
    - official/tests/test.sh::20-31
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report record pass/fail status for each of the six official pytest tests?
    support:
    - official/tests/test.sh::20-24
    - official/tests/test_outputs.py::test_protected_files_not_modified
    - official/tests/test_outputs.py::test_program_compiles_debug
    - official/tests/test_outputs.py::test_program_compiles_release
    - official/tests/test_outputs.py::test_debug_build_runs_without_crash
    - official/tests/test_outputs.py::test_release_build_runs_without_crash
    - official/tests/test_outputs.py::test_no_memory_leaks_with_valgrind
  - artifact: verifier/test-stdout.txt
    question: Does the retained pytest stdout corroborate a complete run of the same six tests, including any assertion details for compile, crash, protected-file, or Valgrind failures?
    support:
    - official/tests/test.sh::20-24
    - official/tests/test_outputs.py::test_protected_files_not_modified
    - official/tests/test_outputs.py::test_program_compiles_debug
    - official/tests/test_outputs.py::test_program_compiles_release
    - official/tests/test_outputs.py::test_debug_build_runs_without_crash
    - official/tests/test_outputs.py::test_release_build_runs_without_crash
    - official/tests/test_outputs.py::test_no_memory_leaks_with_valgrind
  success_if:
  - text: 'Retained verifier evidence shows all six official pytest tests passed: `test_protected_files_not_modified`, `test_program_compiles_debug`, `test_program_compiles_release`, `test_debug_build_runs_without_crash`, `test_release_build_runs_without_crash`, and `test_no_memory_leaks_with_valgrind`.'
    support:
    - official/tests/test.sh::20-24
    - official/tests/test_outputs.py::test_protected_files_not_modified
    - official/tests/test_outputs.py::test_program_compiles_debug
    - official/tests/test_outputs.py::test_program_compiles_release
    - official/tests/test_outputs.py::test_debug_build_runs_without_crash
    - official/tests/test_outputs.py::test_release_build_runs_without_crash
    - official/tests/test_outputs.py::test_no_memory_leaks_with_valgrind
  fail_if:
  - text: Retained verifier evidence shows any one of the six official pytest tests failed or errored, including protected-file modification, compilation failure, a nonzero debug or release run, or a nonzero Valgrind run on the release binary.
    support:
    - official/tests/test_outputs.py::test_protected_files_not_modified
    - official/tests/test_outputs.py::test_program_compiles_debug
    - official/tests/test_outputs.py::test_program_compiles_release
    - official/tests/test_outputs.py::test_debug_build_runs_without_crash
    - official/tests/test_outputs.py::test_release_build_runs_without_crash
    - official/tests/test_outputs.py::test_no_memory_leaks_with_valgrind
  undecided_if:
  - text: The retained non-label verifier artifacts are missing, truncated, or inconsistent, so the pass/fail status of one or more of the six official pytest tests cannot be established independently.
    rationale: Native `U` applies when retained non-label evidence does not establish either full-suite success or any concrete official test failure; `result.json` and `verifier/reward.txt` are excluded from decisive evidence by the drafting instructions.
stronger:
  additional_conditions:
  - id: only_user_cpp_modified
    text: Beyond native scoring, retained diff evidence should show that no existing file other than `/app/user.cpp` was modified; the released verifier only checks `/app/main.cpp` and `/app/user.h`.
    rationale: The instruction forbids modifying any other existing file, but the native evaluator operationalizes that restriction only through MD5 checks on two specific files, so native success can miss other unauthorized edits.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Is there a retained patch or workspace diff showing edits only to `/app/user.cpp` and no other existing file?
      support:
      - official/instruction.md::1-3
      - official/tests/test_outputs.py::EXPECTED_CHECKSUMS
      - official/tests/test_outputs.py::test_protected_files_not_modified
    - artifact: agent/trajectory.json
      question: Does the retained command/edit trace avoid modifying any existing file other than `/app/user.cpp`?
      support:
      - official/instruction.md::1-3
      - official/tests/test_outputs.py::EXPECTED_CHECKSUMS
      - official/tests/test_outputs.py::test_protected_files_not_modified
    support:
    - official/instruction.md::1-3
    - official/tests/test_outputs.py::EXPECTED_CHECKSUMS
    - official/tests/test_outputs.py::test_protected_files_not_modified
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_uses_individual_pass_predicate
Native success and failure are expressed as six individual test-status predicates rather than the exact verifier predicate: zero versus nonzero exit from the configured pytest command.

Required correction: Define native S when retained non-label evidence establishes that the exact pytest invocation returned zero, and native F when it establishes a nonzero return for any reason. Keep individual test outcomes as diagnostic evidence rather than an additional native requirement.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], official/tests/test.sh::20-28

### decision_rules_sfu: sfu_misclassifies_verifier_outcomes
The current rules can move a benchmark-counted zero-exit outcome to U unless all six tests are recorded as passed, and they omit nonzero verifier outcomes not represented as an individual test failure or error.

Required correction: Make S/F follow the pytest process exit status exactly and reserve U solely for insufficient or irreconcilable retained non-label evidence about that status.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::20-28

### source_support_pointers: evaluator_claim_not_supported
The source cited for the all-six-passed claim actually implements a shell exit-status branch and therefore does not support that stronger claim.

Required correction: Rewrite the evaluator claims to the zero/nonzero pytest exit predicate while retaining the exact `test.sh` and `test_outputs.py` pointers for the command and its configured tests.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.support[0], checklist.yaml::native.success_if[0].support[0], official/tests/test.sh::20-28
