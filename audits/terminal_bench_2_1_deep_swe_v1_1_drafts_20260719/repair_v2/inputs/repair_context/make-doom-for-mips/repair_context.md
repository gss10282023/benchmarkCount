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
- case_unit_id: `make-doom-for-mips`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: make-doom-for-mips
domain: terminal_bench_2_1
task_id: terminal-bench/make-doom-for-mips
native:
  user_goal:
    text: Build `doomgeneric_mips` from `/app/doomgeneric/`, using the provided `doomgeneric_img.c`, so `node vm.js` runs it, prints DOOM stdout, and writes frames to the filesystem.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success means retained verifier evidence establishes that the official pytest verifier passed all three checks: `test_vm_execution`, `test_frame_bmp_exists`, and `test_frame_bmp_similar_to_reference`.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::12-110
  checked_by:
    text: Pytest in `official/tests/test_outputs.py`, invoked by `official/tests/test.sh` with CTRF output.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::12-110
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record pass/fail for `test_vm_execution`, `test_frame_bmp_exists`, and `test_frame_bmp_similar_to_reference`?
    support:
    - case_packet.md::57-69
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::12-110
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is missing or ambiguous, does raw pytest output show which official test(s) passed or failed and the corresponding assertion or timeout message?
    support:
    - case_packet.md::57-69
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::12-110
  success_if:
  - text: Retained non-label verifier evidence shows `test_vm_execution` passed, `test_frame_bmp_exists` passed, and `test_frame_bmp_similar_to_reference` passed.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::12-110
  fail_if:
  - text: 'Retained verifier evidence shows `test_vm_execution` failed, including timeout waiting for `/tmp/frame.bmp` or absence of the required stdout substring `I_InitGraphics: DOOM screen size: w x h: 320 x 200`.'
    support:
    - official/tests/test_outputs.py::12-58
  - text: Retained verifier evidence shows `test_frame_bmp_exists` failed because `/tmp/frame.bmp` was missing or empty.
    support:
    - official/tests/test_outputs.py::61-65
  - text: Retained verifier evidence shows `test_frame_bmp_similar_to_reference` failed because the rendered image size mismatched the reference or the computed similarity was below `0.95`.
    support:
    - official/tests/test_outputs.py::68-110
  undecided_if:
  - text: Retained non-label verifier artifacts do not establish the pass/fail status of all three official tests, for example because `verifier/ctrf.json` is absent and raw verifier output is incomplete or ambiguous.
    support:
    - case_packet.md::41-69
    - official/tests/test.sh::18-24
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-failure-semantics-incomplete
Native failure is narrowed to selected assertion and timeout cases, omitting other test errors and other nonzero outcomes of the official pytest invocation.

Required correction: Define native failure from retained non-label evidence that the official pytest command returned nonzero, including any test failure/error and collection or execution error; retain the case-specific examples without making them exhaustive.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-28, official/tests/test_outputs.py::test_frame_bmp_similar_to_reference

### decision_rules_sfu: undecided-overlaps-established-failure
The current U rule can apply when one test is known to have failed but the remaining statuses are unknown.

Required correction: Restrict U to cases where retained non-label evidence establishes neither successful completion of the official verifier nor a nonzero/failing verifier outcome.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if, case_packet.md::Native Evaluator Semantics

### stronger_conditions: official-noncovered-requirements-omitted
The empty stronger layer drops the official MIPS-architecture and required-build-input requirements that the runtime tests do not inspect.

Required correction: Add separate stronger conditions for the MIPS ELF machine identity and for build provenance from /app/doomgeneric using the provided doomgeneric_img.c, with their exact native measurement gaps and inventory-listed assessable artifacts.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::1-1, official/README.md::Overview, official/environment/task-deps/vm.js::parseElfHeader, official/tests/test_outputs.py::12-110

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
