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
- case_unit_id: `compile-compcert`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: compile-compcert
domain: terminal_bench_2_1
task_id: terminal-bench/compile-compcert
native:
  user_goal:
    text: Build CompCert 3.13.1 from source under `/tmp/CompCert/`, configured for the development environment's OS and ISA, so `/tmp/CompCert/ccomp` is invocable there and fully functional.
    support:
    - official/instruction.md::1-4
  benchmark_success:
    text: 'Native success is the conjunction of the three official pytest checks invoked by `official/tests/test.sh`: the `ccomp` existence/version check passes, the positive-probe authenticity/functionality check passes, and the negative-probe VLA-rejection check passes.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  checked_by:
    text: Task-specific verifier `official/tests/test.sh`, which runs `pytest` on `/tests/test_outputs.py` and emits a CTRF report.
    support:
    - official/tests/test.sh::18-22
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: 'Does the structured pytest report show pass/fail status for the three official checks: `test_compcert_exists_and_executable`, `test_compcert_valid_and_functional`, and `test_compcert_rejects_unsupported_feature`?'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  - artifact: verifier/test-stdout.txt
    question: Do the retained verifier logs show the assertion outcomes and any command outputs needed to confirm which official predicate passed or failed, especially version output and probe-program behavior?
    support:
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  - artifact: verifier/test-stderr.txt
    question: If a verifier command or assertion failed, does stderr contain the corresponding failure details needed to establish the official failure condition?
    support:
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  success_if:
  - text: 'Retained verifier evidence shows `test_compcert_exists_and_executable` passed: `/tmp/CompCert/ccomp` existed as a regular executable file, `ccomp -version` exited 0, and the combined version output contained `3.13`.'
    support:
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
  - text: 'Retained verifier evidence shows `test_compcert_valid_and_functional` passed: `/tmp/CompCert/ccomp` compiled `positive_probe.c`; the resulting `/tests/positive_probe` was a regular executable ELF binary; its `.comment` output lacked `clang`, `llvm`, `gnu c`, and `gnu c++`; and its runtime behavior matched the official reversed-string, no-arg exit-code, and empty-string checks.'
    support:
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
  - text: 'Retained verifier evidence shows `test_compcert_rejects_unsupported_feature` passed: compiling `negative_probe.c` with `/tmp/CompCert/ccomp` returned nonzero, so the VLA probe was rejected.'
    support:
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  fail_if:
  - text: Retained verifier evidence shows the existence/version check failed, including if `/tmp/CompCert/ccomp` was missing, not a regular file, not executable, `ccomp -version` returned nonzero, or the version output did not contain `3.13`.
    support:
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
  - text: Retained verifier evidence shows the positive-probe authenticity/functionality check failed, including if `positive_probe.c` did not compile with `/tmp/CompCert/ccomp`, the produced binary was missing or non-executable, not ELF, contained a forbidden compiler signature in `.comment`, or failed any official runtime-output or exit-code check.
    support:
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
  - text: Retained verifier evidence shows the unsupported-feature rejection check failed, including if compiling `negative_probe.c` with `/tmp/CompCert/ccomp` succeeded.
    support:
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
  undecided_if:
  - text: Retained artifacts do not establish whether one or more of the three official pytest checks passed or failed, for example because the CTRF report is missing/incomplete and the verifier logs do not contain enough detail to reconstruct the relevant assertion outcome.
    support:
    - official/tests/test.sh::18-22
    rationale: Native success is exactly the outcome of those official pytest checks; without retained non-label evidence for a check result, neither native success nor native failure is established.
stronger:
  additional_conditions:
  - id: fresh_source_build_evidence
    text: Beyond native success, retained run evidence should show that CompCert was freshly built from source under `/tmp/CompCert/` during the run, not merely that an authentic working `ccomp` binary existed there afterward.
    rationale: The official instruction explicitly requires a fresh source build. The released verifier operationalizes only the final binary's presence, version string, probe-compilation behavior, authenticity signals, and VLA rejection, so it does not itself prove build provenance.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the recorded agent actions show obtaining/configuring/building CompCert source under `/tmp/CompCert/` and producing `/tmp/CompCert/ccomp` during the run?
      support:
      - official/instruction.md::1-4
      - official/tests/test_outputs.py::test_compcert_exists_and_executable
      - official/tests/test_outputs.py::test_compcert_valid_and_functional
      - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
    - artifact: agent/*-stdout.txt
      question: Do captured agent stdout logs show source-build/configuration steps and successful CompCert build output consistent with a fresh build under `/tmp/CompCert/`?
      support:
      - official/instruction.md::1-4
      - official/tests/test_outputs.py::test_compcert_exists_and_executable
      - official/tests/test_outputs.py::test_compcert_valid_and_functional
      - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
    support:
    - official/instruction.md::1-4
    - official/tests/test_outputs.py::test_compcert_exists_and_executable
    - official/tests/test_outputs.py::test_compcert_valid_and_functional
    - official/tests/test_outputs.py::test_compcert_rejects_unsupported_feature
```

## Prior independent review findings to repair

### decisive_post_run_evidence: stderr_not_decisive
verifier/test-stderr.txt is designated decisive even though the verifier sources do not establish that pytest node statuses or assertion failures are reported there.

Required correction: Remove verifier/test-stderr.txt from decisive_artifacts; rely on the structured CTRF report or a complete retained pytest stdout report for official node outcomes.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], official/tests/test.sh::18-22, official/tests/test_outputs.py::_run

### decision_rules_sfu: undecided_overlaps_failure
The U rule applies when any official check is unresolved, including cases where a different check is conclusively failed and therefore establishes native F.

Required correction: Define U only when no official check is established as failed and retained evidence does not establish that all three checks passed.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], checklist.yaml::native.fail_if, case_packet.md::Native Evaluator Semantics
