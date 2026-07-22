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
- case_unit_id: `raman-fitting`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: raman-fitting
domain: terminal_bench_2_1
task_id: terminal-bench/raman-fitting
native:
  user_goal:
    text: Fit the Raman spectrum's G and 2D peaks and write `/app/results.json` containing `x0`, `gamma`, `amplitude`, and `offset` for each peak.
    support:
    - official/instruction.md::1-14
  benchmark_success:
    text: 'Native success is the official verifier script exiting successfully after pytest passes all three official checks: `/app/results.json` exists; `G.x0`, `G.gamma`, `G.amplitude`, and `G.offset` satisfy `abs(x0-1580.3)<5`, `abs(gamma-9.06)<1`, `abs(1-amplitude/8382.69)<0.05`, and `abs(1-offset/5561.03)<0.1`; and `2D.x0`, `2D.gamma`, `2D.amplitude`, and `2D.offset` satisfy `abs(1-x0/2670.08)<0.05`, `abs(gamma-17.52)<1`, `abs(1-amplitude/12314.42)<0.05`, and `abs(1-offset/1239.09)<0.1`.'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_result_file_exists
    - official/tests/test_outputs.py::test_G_Peak
    - official/tests/test_outputs.py::test_2D_Peak
  checked_by:
    text: Official pytest-based verifier in `official/tests/test.sh`, which runs `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_result_file_exists
    - official/tests/test_outputs.py::test_G_Peak
    - official/tests/test_outputs.py::test_2D_Peak
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do `test_result_file_exists`, `test_G_Peak`, and `test_2D_Peak` each pass or fail?
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_result_file_exists
    - official/tests/test_outputs.py::test_G_Peak
    - official/tests/test_outputs.py::test_2D_Peak
  - artifact: artifacts/**
    question: Is there a retained copy of `/app/results.json`, and if so does it contain `G` and `2D` entries whose values satisfy the exact existence and tolerance predicates used by the official tests?
    support:
    - official/tests/test_outputs.py::test_result_file_exists
    - official/tests/test_outputs.py::test_G_Peak
    - official/tests/test_outputs.py::test_2D_Peak
  - artifact: verifier/test-stdout.txt
    question: If CTRF is absent or incomplete, do verifier logs show pytest/assertion failures or the working-directory guard error from the official verifier script?
    support:
    - official/tests/test.sh::1-24
  success_if:
  - text: 'Retained non-label evidence establishes that all three official checks passed: `/app/results.json` existed, the G-peak values satisfied `abs(x0-1580.3)<5`, `abs(gamma-9.06)<1`, `abs(1-amplitude/8382.69)<0.05`, and `abs(1-offset/5561.03)<0.1`, and the 2D-peak values satisfied `abs(1-x0/2670.08)<0.05`, `abs(gamma-17.52)<1`, `abs(1-amplitude/12314.42)<0.05`, and `abs(1-offset/1239.09)<0.1`.'
    support:
    - official/tests/test_outputs.py::test_result_file_exists
    - official/tests/test_outputs.py::test_G_Peak
    - official/tests/test_outputs.py::test_2D_Peak
  fail_if:
  - text: Retained verifier logs establish that `official/tests/test.sh` failed before or during pytest, including the explicit working-directory guard.
    support:
    - official/tests/test.sh::1-24
  - text: Retained non-label evidence establishes that `/app/results.json` was missing when the official existence check ran.
    support:
    - official/tests/test_outputs.py::test_result_file_exists
  - text: Retained non-label evidence establishes that the G-peak check failed, including any failure of `abs(x0-1580.3)<5`, `abs(gamma-9.06)<1`, `abs(1-amplitude/8382.69)<0.05`, or `abs(1-offset/5561.03)<0.1`.
    support:
    - official/tests/test_outputs.py::test_G_Peak
  - text: Retained non-label evidence establishes that the 2D-peak check failed, including any failure of `abs(1-x0/2670.08)<0.05`, `abs(gamma-17.52)<1`, `abs(1-amplitude/12314.42)<0.05`, or `abs(1-offset/1239.09)<0.1`.
    support:
    - official/tests/test_outputs.py::test_2D_Peak
  undecided_if:
  - text: Native status is undecided if retained non-label evidence does not establish whether the verifier completed and passed or failed, and there is no retained `results.json` copy available to reapply the official existence and tolerance checks.
    rationale: The native claim is defined by the official verifier/tests; without decisive verifier evidence and without the evaluated output, stored artifacts do not establish either success or failure.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: incorrect_shell_exit_semantics
Native success is incorrectly described as successful exit of the overall verifier script, and the first failure rule is broad enough to count non-fatal setup-command errors. The released criterion is the pytest command’s status as mapped to 1 or 0 by the shell branch, with the separate working-directory guard exiting before pytest.

Required correction: Define native success as pytest exiting zero with all three official tests passing. Define failure as the guard’s explicit exit or retained evidence that the pytest invocation returned nonzero, including test failures or inability to execute pytest. Do not use the script’s eventual process exit status or merely observed non-fatal setup errors.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.fail_if[0], official/tests/test.sh::12-29

### stronger_conditions: omitted_fit_derivation_condition
The empty stronger layer omits the instruction-supported requirement that the reported parameters result from fitting the supplied Raman spectrum, which the released tests do not operationalize.

Required correction: Add a stronger condition requiring retained evidence that the G and 2D parameters were obtained by fitting the provided spectrum, identify the tests’ output-only measurement gap, and name retained trajectory or fitting artifacts that could assess it.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::1-18, official/tests/test_outputs.py::test_G_Peak, official/tests/test_outputs.py::test_2D_Peak
