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
- case_unit_id: `video-processing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: video-processing
domain: terminal_bench_2_1
task_id: terminal-bench/video-processing
native:
  user_goal:
    text: Create `/app/jump_analyzer.py` that takes an MP4 hurdle-jump video, detects the single jump's takeoff and landing frames, and writes `/app/output.toml` with exactly the required field names using only `toml`, `cv2`, and `numpy`.
    support:
    - official/instruction.md::1-25
    - official/task.toml::task.description
  benchmark_success:
    text: 'Native success means the official verifier''s pytest run passes every check in `official/tests/test_outputs.py`: both required video files exist, `/app/jump_analyzer.py` runs successfully on both videos, `/app/output.toml` is created and parseable with the required keys, the takeoff and landing values fall within the inclusive ranges `[50,54]` and `[62,64]` for `/app/example_video.mp4` and `[219,223]` and `[231,234]` for `/tests/test_video.mp4`, and no forbidden third-party imports are present.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_example_video_exists
    - official/tests/test_outputs.py::test_test_video_exists
    - official/tests/test_outputs.py::_test_jump_analyzer_video
    - official/tests/test_outputs.py::test_jump_analyzer_example_video
    - official/tests/test_outputs.py::test_jump_analyzer_test_video
    - official/tests/test_outputs.py::test_jump_analyzer_imports
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::18-24
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for all five official pytest checks in `official/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_example_video_exists
    - official/tests/test_outputs.py::test_test_video_exists
    - official/tests/test_outputs.py::test_jump_analyzer_example_video
    - official/tests/test_outputs.py::test_jump_analyzer_test_video
    - official/tests/test_outputs.py::test_jump_analyzer_imports
  - artifact: verifier/test-stdout.txt
    question: Does retained pytest stdout corroborate which official checks ran and whether any assertion failed or the suite completed cleanly?
    support:
    - official/tests/test.sh::18-24
  success_if:
  - text: Retained verifier evidence establishes that `test_example_video_exists`, `test_test_video_exists`, `test_jump_analyzer_example_video`, `test_jump_analyzer_test_video`, and `test_jump_analyzer_imports` all passed.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_example_video_exists
    - official/tests/test_outputs.py::test_test_video_exists
    - official/tests/test_outputs.py::test_jump_analyzer_example_video
    - official/tests/test_outputs.py::test_jump_analyzer_test_video
    - official/tests/test_outputs.py::test_jump_analyzer_imports
  fail_if:
  - text: Retained verifier evidence establishes that any official pytest check failed, including missing required videos, nonzero execution of `/app/jump_analyzer.py` on either video, missing or unparsable `/app/output.toml`, missing required keys, takeoff or landing values outside either inclusive range, or forbidden third-party imports.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::_test_jump_analyzer_video
    - official/tests/test_outputs.py::test_example_video_exists
    - official/tests/test_outputs.py::test_test_video_exists
    - official/tests/test_outputs.py::test_jump_analyzer_imports
  undecided_if:
  - text: Retained non-label evidence does not establish a full all-pass verifier run and also does not establish any concrete failed official check.
    rationale: The native claim is defined by the official pytest checks, so if retained CTRF/stdout evidence is missing or incomplete, the review is undecided unless some stored artifact independently proves one of those checks passed or failed.
stronger:
  additional_conditions:
  - id: exact_output_schema
    text: Beyond native scoring, retained `/app/output.toml` should show exactly the two required top-level keys `jump_takeoff_frame_number` and `jump_land_frame_number`, with no extra output fields; this closes a measurement gap because the instruction requires the exact structure and field names, while the native verifier only checks that those two keys exist in a parseable TOML file.
    rationale: The official instruction says the TOML output must have the exact structure and field names shown, but `_test_jump_analyzer_video` only asserts presence of the two required fields after parsing and does not reject extras.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does retained `/app/output.toml` contain exactly the two required top-level keys and no extra fields?
      support:
      - official/instruction.md::11-17
      - official/tests/test_outputs.py::_test_jump_analyzer_video
    support:
    - official/instruction.md::11-17
    - official/tests/test_outputs.py::_test_jump_analyzer_video
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_omits_non_test_errors
The native F/U rules do not cover every nonzero status of the oracle-driving `uvx`/pytest command, although `test.sh` maps any such status to native failure.

Required correction: Define native success as retained non-label evidence establishing a zero exit from the exact `uvx`/pytest invocation, and native failure as evidence establishing a nonzero exit, including failed tests and collection, usage, internal, interruption, launcher, or setup errors.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-31

### decision_rules_sfu: incorrect_f_u_boundary
The current U rule can absorb an evidenced benchmark-counted failure whenever no concrete named test failure is available.

Required correction: Reserve U for records where retained non-label evidence establishes neither a zero nor nonzero oracle-command outcome and establishes neither all-pass completion nor a concrete failure/error.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-31, case_packet.md::Native Evaluator Semantics

### source_support_pointers: undecided_rule_has_no_source_pointer
`native.undecided_if[0]` and its rationale lack packet-local support.

Required correction: Add support pointers to `case_packet.md::Native Evaluator Semantics` and `case_packet.md::Available Artifact Inventory`.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
