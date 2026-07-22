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
- case_unit_id: `build-pov-ray`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: build-pov-ray
domain: terminal_bench_2_1
task_id: terminal-bench/build-pov-ray
native:
  user_goal:
    text: Build POV-Ray 2.2 from source archives, extract the source tree to `/app/povray-2.2`, install the executable at `/usr/local/bin/povray`, and leave `/app/deps/illum1.pov` unmodified so the provided scene renders successfully.
    support:
    - official/instruction.md::1-6
    - official/README.md::3-17
  benchmark_success:
    text: 'The official verifier succeeds iff `official/tests/test.sh` reaches pytest and all three tests in `official/tests/test_outputs.py` pass: render `/app/deps/illum1.pov` with `/usr/local/bin/povray` and `/app/povray-2.2/povdoc/include`, produce a valid 640x480 PNG converted from `/app/illum1.tga` with SSIM > 0.87 against the reference image, report version `2.2`, and match the expected MD5s for the checked source files and `deps/illum1.pov`.'
    support:
    - official/tests/test.sh::1-30
    - official/tests/test_outputs.py::test_illum1_render_and_verify
    - official/tests/test_outputs.py::test_povray_version
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
  checked_by:
    text: Official shell verifier `official/tests/test.sh`, which runs pytest with CTRF output on `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::1-30
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it show pass/fail outcomes for `test_illum1_render_and_verify`, `test_povray_version`, and `test_povray_built_from_correct_source`?
    support:
    - official/tests/test.sh::16-23
    - official/tests/test_outputs.py::test_illum1_render_and_verify
    - official/tests/test_outputs.py::test_povray_version
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout preserve the pytest summary, SSIM printout, or an early verifier-script failure needed to interpret the native result?
    support:
    - official/tests/test.sh::11-23
    - official/tests/test_outputs.py::test_illum1_render_and_verify
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr preserve render/version/hash diagnostics or pytest/setup errors when CTRF or stdout is incomplete?
    support:
    - official/tests/test.sh::11-23
    - official/tests/test_outputs.py::test_illum1_render_and_verify
    - official/tests/test_outputs.py::test_povray_version
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
  success_if:
  - text: 'Retained verifier evidence shows `test_illum1_render_and_verify` passed: `/usr/local/bin/povray` created `/app/illum1.tga`, conversion to PNG succeeded, the PNG was valid at 640x480, and SSIM against the reference image was > 0.87.'
    support:
    - official/tests/test_outputs.py::test_illum1_render_and_verify
  - text: Retained verifier evidence shows `test_povray_version` passed because `/usr/local/bin/povray -h` produced output containing `2.2`.
    support:
    - official/tests/test_outputs.py::test_povray_version
  - text: Retained verifier evidence shows `test_povray_built_from_correct_source` passed because `/app/povray-2.2` existed, every checked source file matched its expected MD5, and `/app/deps/illum1.pov` matched its expected MD5.
    support:
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
  fail_if:
  - text: Verifier stdout/stderr establishes that `official/tests/test.sh` failed before collecting or completing the official pytest checks, including the explicit no-WORKDIR guard or pytest/setup failure.
    support:
    - official/tests/test.sh::11-30
  - text: Retained verifier evidence shows `test_illum1_render_and_verify` failed, including no `/app/illum1.tga`, failed TGA-to-PNG conversion, invalid PNG, wrong image size, or SSIM <= 0.87.
    support:
    - official/tests/test_outputs.py::test_illum1_render_and_verify
  - text: Retained verifier evidence shows `test_povray_version` failed because the executable produced no usable output or the output did not contain `2.2`.
    support:
    - official/tests/test_outputs.py::test_povray_version
  - text: Retained verifier evidence shows `test_povray_built_from_correct_source` failed because `/app/povray-2.2` was missing, a checked POV-Ray source file was missing or had the wrong MD5, or `/app/deps/illum1.pov` was modified.
    support:
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
  undecided_if:
  - text: The retained non-label verifier artifacts do not establish whether the official verifier reached pytest and how each of the three official tests resolved.
    rationale: Native success or failure for this case is established only by retained evidence of the released verifier's script-and-pytest outcome. If CTRF and verifier logs are missing or too incomplete to recover those outcomes, neither side is proven from stored evidence.
stronger:
  additional_conditions:
  - id: archive_download_and_extraction_evidenced
    text: Retained agent evidence shows POV-Ray 2.2 source archives were actually downloaded and extracted into `/app/povray-2.2` before the build; native scoring checks only the resulting files, hashes, and executable behavior.
    rationale: The official instruction explicitly requires finding and downloading source archives, then extracting them to `/app/povray-2.2`. The released evaluator verifies post-build authenticity and behavior but does not operationalize the acquisition step itself.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show commands and results that download POV-Ray 2.2 archives and extract them into `/app/povray-2.2`?
      support:
      - official/instruction.md::1-1
    - artifact: agent/*-stdout.txt
      question: Do the agent terminal logs corroborate successful archive retrieval and extraction into `/app/povray-2.2`?
      support:
      - official/instruction.md::1-1
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_povray_built_from_correct_source
```

## Prior independent review findings to repair

### native_user_goal: native-goal-omissions
native.user_goal does not faithfully retain the instruction to find and download the archives or the stated comparison of the rendered scene against a reference image.

Required correction: State the complete user intent: locate and download the POV-Ray 2.2 archives, extract and compile them, install the executable at the required path, preserve illum1.pov, and render it for comparison with the reference image.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-6

### source_support_pointers: unsupported-undecided-rule
native.undecided_if[0] has no support field for its claims about the retained-evidence boundary and official verifier outcome.

Required correction: Add packet-local support pointing to the Native Evaluator Semantics and Available Artifact Inventory sections.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
