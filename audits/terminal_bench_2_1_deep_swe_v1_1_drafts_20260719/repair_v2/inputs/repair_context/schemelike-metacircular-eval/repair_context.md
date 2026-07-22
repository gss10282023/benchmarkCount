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
- case_unit_id: `schemelike-metacircular-eval`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: schemelike-metacircular-eval
domain: terminal_bench_2_1
task_id: terminal-bench/schemelike-metacircular-eval
native:
  user_goal:
    text: Produce `eval.scm`, a Scheme metacircular evaluator for the `interp.py` language that reads one file-path line from stdin, interprets that `.scm` file, forwards remaining stdin/stdout to the interpreted program, and can run the visible test programs and itself.
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: The official verifier succeeds iff `official/tests/test.sh` runs `pytest` on `official/tests/test_outputs.py` and `test_interp` finds every `.scm` file in `/tests/test` and `/tests/shadow_test` free of direct/eval timeout, free of the verifier's explicit direct-execution failure check, and matched on stdout under `compare_outputs`; for paths containing `05-simple`, `calculator.scm`, or `closures.scm`, the same normalized stdout must also match when `eval.scm` interprets itself once before the target program. `compare_outputs` uses `normalize_output`, which strips a trailing standalone `True` line before comparing stdout.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::find_test_files
    - official/tests/test_outputs.py::run_scheme_through_eval
    - official/tests/test_outputs.py::compare_outputs
    - official/tests/test_outputs.py::normalize_output
  checked_by:
    text: Official task verifier `official/tests/test.sh`, which runs `pytest` over `official/tests/test_outputs.py` and writes CTRF output.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_interp
  decisive_artifacts:
  - artifact: verifier/test-stdout.txt
    question: 'Does the verifier log show every discovered `.scm` file reported `PASSED: OK`, or else show a concrete official failure mode such as timeout, direct execution failure, or normalized-output mismatch, including the extra metacircular comparison for `05-simple`, `calculator.scm`, and `closures.scm`?'
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::find_test_files
    - official/tests/test_outputs.py::compare_outputs
    - official/tests/test_outputs.py::run_scheme_through_eval
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr contain tracebacks or runtime failures needed to interpret whether `test_interp` completed the official comparisons?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_interp
  - artifact: verifier/ctrf.json
    question: Does the retained pytest record for `test_interp` preserve the official test outcome and any captured failure details needed to confirm the stdout/stderr evidence?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_interp
  success_if:
  - text: 'Retained verifier evidence shows that `test_interp` enumerated the official `/tests/test` and `/tests/shadow_test` `.scm` files and every required comparison reported `PASSED: OK`, including the extra metacircular comparison for paths containing `05-simple`, `calculator.scm`, or `closures.scm`.'
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::find_test_files
    - official/tests/test_outputs.py::run_scheme_through_eval
    - official/tests/test_outputs.py::compare_outputs
  - text: The same retained evidence shows no official timeout occurred in direct or eval execution, and no direct execution hit the verifier's explicit nonzero-code failure check.
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::run_scheme_direct
    - official/tests/test_outputs.py::run_scheme_through_eval
  fail_if:
  - text: Verifier evidence shows any enumerated `.scm` case hit a direct or eval timeout under `test_interp`.
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::run_scheme_direct
    - official/tests/test_outputs.py::run_scheme_through_eval
  - text: Verifier evidence shows direct execution of any enumerated `.scm` file failed under the verifier's explicit `direct_code` check.
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::run_scheme_direct
  - text: Verifier evidence shows any official stdout comparison failed after `normalize_output`, including any selected metacircular comparison for `05-simple`, `calculator.scm`, or `closures.scm`.
    support:
    - official/tests/test_outputs.py::test_interp
    - official/tests/test_outputs.py::compare_outputs
    - official/tests/test_outputs.py::normalize_output
  undecided_if:
  - text: Required verifier artifacts are missing, truncated, or do not preserve enough per-file stdout/stderr detail to determine whether all official comparisons ran and passed or whether an official failure condition was triggered.
    rationale: Native success and failure are both defined by the retained verifier traces from `test_interp`; without readable verifier evidence, the released criterion cannot be reconstructed from non-label artifacts.
stronger:
  additional_conditions:
  - id: raw_stdout_no_normalized_extra_output
    text: Beyond native scoring, retained evidence should show raw `python3 interp.py eval.scm` runs emit exactly the interpreted program's stdout, with no extra trailing `True` or other output that the released verifier would ignore via `normalize_output`.
    rationale: 'This is a concrete measurement gap: the instruction requires forwarding the interpreted program''s output to stdout, while the released evaluator weakens that check by stripping a trailing standalone `True` line before comparison.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do retained command transcripts show raw stdout from one or more `python3 interp.py eval.scm` runs without an extra trailing `True` line or other evaluator-normalized extra output?
      support:
      - official/instruction.md::2-10
      - official/tests/test_outputs.py::normalize_output
    - artifact: agent/*-stdout.txt
      question: Do retained agent stdout logs preserve raw `eval.scm` command output showing no extra trailing `True` line or other normalized-away output?
      support:
      - official/instruction.md::2-10
      - official/tests/test_outputs.py::normalize_output
    support:
    - official/instruction.md::2-10
    - official/tests/test_outputs.py::compare_outputs
    - official/tests/test_outputs.py::normalize_output
```

## Prior independent review findings to repair

### native_evaluator_semantics: NES-001
The native success/failure characterization is incomplete: it omits the pytest-passing no-files return branch and native failures caused by assertion-independent unhandled, collection, invocation, or startup errors.

Required correction: Define native success from retained non-label evidence that the configured uvx/pytest invocation exited zero, explicitly preserving the no-files return behavior. Define native failure as evidence that this invocation exited nonzero, including the enumerated per-file failures and other pytest/verifier errors.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if, checklist.yaml::native.fail_if, official/tests/test_outputs.py::test_interp, official/tests/test.sh::18-22

### decision_rules_sfu: SFU-001
Current S/F rules can move established benchmark outcomes to U because they do not cover every zero/nonzero pytest outcome.

Required correction: Make S correspond to established zero exit and F correspond to established nonzero exit using raw verifier evidence; use U only when that status cannot be established without reward/result fields.

Cited diagnostic locations: checklist.yaml::native.success_if, checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-22

### source_support_pointers: SRC-001
The cited test_interp source contradicts the checklist’s claimed iff rule by containing an unhandled no-files return path and allowing other exceptions to fail pytest.

Required correction: Revise the supported semantic claim to account for all relevant control paths shown by test_interp and test.sh.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.support, official/tests/test_outputs.py::test_interp, official/tests/test.sh::18-22
