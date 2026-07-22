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
- case_unit_id: `fix-ocaml-gc`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: fix-ocaml-gc
domain: terminal_bench_2_1
task_id: terminal-bench/fix-ocaml-gc
native:
  user_goal:
    text: Fix the OCaml garbage-collector change so the compiler no longer crashes during bootstrap, then run the basic testsuite with `make -C testsuite one DIR=tests/basic` and have it run cleanly.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: Native success is established when retained verifier evidence shows the official verifier rebuilt the OCaml tree, ran `make -C testsuite one DIR=tests/basic`, and the verifier's `test_tests_output` check passed; that check requires `/app/ocaml/tests.txt` to exist and contain `40 tests passed`.
    support:
    - official/tests/test.sh::1-32
    - official/tests/test_outputs.py::6-17
  checked_by:
    text: The task-specific verifier script plus its pytest assertion over `/app/ocaml/tests.txt`.
    support:
    - official/tests/test.sh::1-32
    - official/tests/test_outputs.py::6-17
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show `test_tests_output` passed rather than failed or missing?
    support:
    - official/tests/test.sh::24-32
    - official/tests/test_outputs.py::6-17
  - artifact: verifier/test-stdout.txt
    question: Does the retained verifier stdout show the verifier ran the OCaml rebuild/tests flow and produced the `tests.txt`-based check outcome consistent with the CTRF report?
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::6-17
  success_if:
  - text: '`verifier/ctrf.json` shows the verifier''s `test_tests_output` check passed, and retained verifier stdout is consistent with the official flow that rebuilds OCaml, runs `make -C testsuite one DIR=tests/basic`, and checks `/app/ocaml/tests.txt` for `40 tests passed`.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::6-17
  fail_if:
  - text: '`verifier/ctrf.json` shows `test_tests_output` failed, including because `/app/ocaml/tests.txt` was missing or because its contents did not include `40 tests passed`.'
    support:
    - official/tests/test_outputs.py::12-17
  - text: Retained verifier stdout/stderr shows the official verifier did not complete the rebuild/tests flow successfully, and the retained pytest report correspondingly records the check as failed.
    support:
    - official/tests/test.sh::18-32
    - official/tests/test_outputs.py::12-17
  undecided_if:
  - text: The retained non-label verifier artifacts needed to establish the pytest outcome or its underlying `tests.txt` condition are missing, truncated, or inconsistent, so success and failure cannot be determined independently of released reward metadata.
    support:
    - case_packet.md::65-74
    - official/tests/test.sh::24-32
    - official/tests/test_outputs.py::6-17
stronger:
  additional_conditions:
  - id: instruction-level-bootstrap-success
    text: Beyond the native check, retained evidence should show the OCaml compiler bootstrap/build itself completed successfully after the fix, not merely that `/app/ocaml/tests.txt` contained `40 tests passed`.
    rationale: The official instruction says the bug causes the compiler to crash while bootstrapping itself, but the released pytest oracle operationalizes only the retained `tests.txt` existence/content check. The shell script does run `make -j4`, yet the decisive native oracle is the single pytest assertion over `tests.txt`, so a stricter review can separately require retained build evidence for successful bootstrap.
    decisive_artifacts:
    - artifact: verifier/test-stdout.txt
      question: Does retained verifier stdout show the `make clean && ./configure && make -j4` bootstrap/build step completed successfully before the testsuite run?
      support:
      - official/instruction.md::1-1
      - official/tests/test.sh::18-23
    - artifact: verifier/test-stderr.txt
      question: Is retained verifier stderr free of build/bootstrap failure evidence that would contradict a successful OCaml bootstrap?
      support:
      - official/instruction.md::1-1
      - official/tests/test.sh::18-23
    support:
    - official/instruction.md::1-1
    - official/README.md::20-24
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::6-17
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-oracle-strengthened
Native success improperly requires corroborating evidence that the rebuild/tests flow completed, although the released oracle operationalizes only the `test_tests_output` pytest assertion over `tests.txt`.

Required correction: Define native success exactly as a passing `test_tests_output` node and move independently supported build or clean-execution requirements to the stronger layer.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if[0], official/tests/test.sh::18-32, official/tests/test_outputs.py::6-17

### decisive_post_run_evidence: stdout-not-independent
The stdout decisive question depends on comparison with the CTRF report and therefore cannot be answered from that artifact independently.

Required correction: Ask only whether stdout itself directly reports the pytest node’s status; treat CTRF and stdout as alternative independent evidence sources.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], case_packet.md::Available Artifact Inventory

### decision_rules_sfu: false-undecided-from-conjunction
The conjunction of CTRF and stdout moves records to U when one retained artifact already establishes native success or failure.

Required correction: Use alternative independently decisive non-label evidence for S and F, and reserve U strictly for cases where neither native claim can be established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
