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
- case_unit_id: `sam-cell-seg`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sam-cell-seg
domain: terminal_bench_2_1
task_id: terminal-bench/sam-cell-seg
native:
  user_goal:
    text: Write `/app/convert_masks.py` as an argparse CLI that uses MobileSAM on CPU to convert every mask in a provided metadata CSV into a polyline-only output, preserving the CSV format with updated `xmin`, `xmax`, `ymin`, `ymax`, `coords_x`, and `coords_y`, with no overlaps, one contiguous mask per cell, and no hardcoded paths.
    support:
    - official/instruction.md::1-35
    - official/task.toml::task.description
  benchmark_success:
    text: 'Native success is the official verifier outcome from `official/tests/test.sh`: all pytest checks in `official/tests/test_outputs.py` must pass for `/app/convert_masks.py` existence, successful execution on the official command, `/app/test_output.csv` existence, matching shape and columns, non-rectangular output masks, per-row IoU >= 0.5 against `correct_output.csv`, no significant polygon overlaps, single-contiguous masks, and flat numeric coordinate lists.'
    support:
    - official/tests/test.sh::1-33
    - official/tests/test_outputs.py::test_python_file_exists
    - official/tests/test_outputs.py::test_run_script
    - official/tests/test_outputs.py::test_csv_output_exists
    - official/tests/test_outputs.py::test_csv_shape_cols
    - official/tests/test_outputs.py::test_masks_are_no_longer_rect
    - official/tests/test_outputs.py::test_mask_alignment
    - official/tests/test_outputs.py::test_no_polyline_overlaps
    - official/tests/test_outputs.py::test_single_contiguous_mask_per_cell
    - official/tests/test_outputs.py::test_coords_are_flat_lists
  checked_by:
    text: '`official/tests/test.sh`, which installs verifier dependencies, downloads MobileSAM weights and fixtures, and runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.'
    support:
    - official/tests/test.sh::1-33
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do all official pytest cases from `official/tests/test_outputs.py` report passed, or which named case failed/errored/skipped?
    support:
    - official/tests/test.sh::1-33
    - official/tests/test_outputs.py::test_python_file_exists
    - official/tests/test_outputs.py::test_run_script
    - official/tests/test_outputs.py::test_csv_output_exists
    - official/tests/test_outputs.py::test_csv_shape_cols
    - official/tests/test_outputs.py::test_masks_are_no_longer_rect
    - official/tests/test_outputs.py::test_mask_alignment
    - official/tests/test_outputs.py::test_no_polyline_overlaps
    - official/tests/test_outputs.py::test_single_contiguous_mask_per_cell
    - official/tests/test_outputs.py::test_coords_are_flat_lists
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show the official pytest invocation against `/tests/test_outputs.py` completed, and if not, what command or assertion failure is reported?
    support:
    - official/tests/test.sh::1-33
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr contain subprocess, import, or runtime errors relevant to the official script run or pytest checks when CTRF/stdout is incomplete?
    support:
    - official/tests/test.sh::1-33
    - official/tests/test_outputs.py::test_run_script
  success_if:
  - text: '`verifier/ctrf.json` shows every official pytest check passed, and verifier stdout/stderr are consistent with the `official/tests/test.sh` run completing on the official suite.'
    support:
    - official/tests/test.sh::1-33
    - official/tests/test_outputs.py::test_python_file_exists
    - official/tests/test_outputs.py::test_run_script
    - official/tests/test_outputs.py::test_csv_output_exists
    - official/tests/test_outputs.py::test_csv_shape_cols
    - official/tests/test_outputs.py::test_masks_are_no_longer_rect
    - official/tests/test_outputs.py::test_mask_alignment
    - official/tests/test_outputs.py::test_no_polyline_overlaps
    - official/tests/test_outputs.py::test_single_contiguous_mask_per_cell
    - official/tests/test_outputs.py::test_coords_are_flat_lists
  fail_if:
  - text: '`verifier/ctrf.json` shows any official pytest case failed, errored, or was skipped.'
    support:
    - official/tests/test_outputs.py::test_python_file_exists
    - official/tests/test_outputs.py::test_run_script
    - official/tests/test_outputs.py::test_csv_output_exists
    - official/tests/test_outputs.py::test_csv_shape_cols
    - official/tests/test_outputs.py::test_masks_are_no_longer_rect
    - official/tests/test_outputs.py::test_mask_alignment
    - official/tests/test_outputs.py::test_no_polyline_overlaps
    - official/tests/test_outputs.py::test_single_contiguous_mask_per_cell
    - official/tests/test_outputs.py::test_coords_are_flat_lists
  - text: Verifier stdout/stderr shows the required `python /app/convert_masks.py --csv_path /app/test_metadata.csv --rgb_path /app/test_img.png --output_path /app/test_output.csv --weights_path /app/mobile_sam.pt` subprocess or the subsequent official pytest run failed before all checks could pass.
    support:
    - official/tests/test.sh::1-33
    - official/tests/test_outputs.py::test_run_script
  undecided_if:
  - text: The retained verifier artifacts do not establish a complete official pytest outcome, for example `verifier/ctrf.json` is missing or incomplete and stdout/stderr do not reliably show whether every required check passed or a native failure condition was reached.
    support:
    - official/tests/test.sh::1-33
stronger:
  additional_conditions:
  - id: uses_mobilesam
    text: Beyond native scoring, retained code evidence should show `/app/convert_masks.py` actually uses `mobile_sam` / MobileSAM for mask refinement; the native verifier only scores output behavior and does not check the implementation path.
    rationale: The instruction requires MobileSAM specifically, but the released tests inspect existence, execution, CSV structure, geometry, IoU, overlap, contiguity, and coordinate formatting rather than whether MobileSAM was used.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If the retained workspace snapshot includes `/app/convert_masks.py`, does that script import and call `mobile_sam` / MobileSAM for refinement?
      support:
      - official/instruction.md::1-35
    - artifact: agent/trajectory.json
      question: If final script bytes are not retained elsewhere, does the trajectory show the implemented solution installing, importing, or calling MobileSAM rather than a non-MobileSAM substitute?
      support:
      - official/instruction.md::1-35
    support:
    - official/instruction.md::1-35
    - official/tests/test_outputs.py::test_python_file_exists
    - official/tests/test_outputs.py::test_run_script
    - official/tests/test_outputs.py::test_mask_alignment
  - id: honors_cli_paths
    text: Beyond native scoring, retained code evidence should show the script reads and uses the provided `--weights_path`, `--output_path`, `--rgb_path`, and `--csv_path` arguments instead of hardcoded dataset paths; the native verifier invokes one fixed path set only.
    rationale: The instruction forbids hardcoded paths and requires these argparse parameters, but the released verifier exercises exactly one command with fixed `/app/...` paths.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If `/app/convert_masks.py` is retained, does it wire the four argparse options into actual file reads, writes, and model-loading calls rather than substituting fixed paths?
      support:
      - official/instruction.md::1-35
      - official/tests/test_outputs.py::test_run_script
    - artifact: agent/trajectory.json
      question: If final script bytes are missing, does the trajectory show the implementation using the CLI-provided paths rather than hardcoded test filenames?
      support:
      - official/instruction.md::1-35
      - official/tests/test_outputs.py::test_run_script
    support:
    - official/instruction.md::1-35
    - official/tests/test_outputs.py::test_run_script
```

## Prior independent review findings to repair

### native_user_goal: B1_INCOMPLETE_USER_GOAL
`native.user_goal` omits several explicit implementation constraints from the official instruction.

Required correction: Include the prohibition on original SAM, the prohibition on modifying MobileSAM source, and the listed-package assumption while preserving the full output and CLI goal.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::lines 1-35

### native_evaluator_semantics: B2_SKIP_SEMANTICS
A skipped pytest case is classified as native failure even though `test.sh` uses pytest's exit status and a skip alone ordinarily leaves that status successful.

Required correction: Define native S and F by the immediate pytest exit status captured by `test.sh`; treat skips according to their effect on that status, not as automatic failures.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], official/tests/test.sh::pytest invocation and exit-status branch

### native_evaluator_semantics: B3_INACCURATE_CHECKED_BY
`checked_by` says the verifier downloads fixtures, but `test.sh` copies them from `/tests`; only the MobileSAM weights are downloaded.

Required correction: Describe the verifier setup and invocation exactly as implemented by `official/tests/test.sh`.

Cited diagnostic locations: checklist.yaml::native.checked_by.text, official/tests/test.sh::fixture copy commands

### decisive_post_run_evidence: B4_NONDECISIVE_TRAJECTORY_QUESTION
Installing or importing MobileSAM does not prove that the final script uses it for refinement.

Required correction: Require the retained artifact to expose final script content or execution evidence showing MobileSAM is actually constructed and called in the mask-refinement path.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], official/instruction.md::lines 1-35

### decision_rules_sfu: B5_INVALID_F_RULE
The F rule moves a non-failing skip status into native failure.

Required correction: Make F require non-label evidence of a nonzero pytest outcome or the explicit pre-pytest verifier failure; otherwise use U when neither exit outcome can be established.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], official/tests/test.sh::pytest exit-status branch

### stronger_conditions: B6_STRONGER_PROOF_MISMATCH
The `uses_mobilesam` condition requires actual use, but one decisive question accepts weaker installation or import evidence.

Required correction: Align every decisive question with actual MobileSAM use and keep other source-supported, untested implementation and CSV-preservation requirements as separate stronger conditions.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], official/tests/test_outputs.py::test_run_script

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::entire file': symbol 'entire file' not found
- $.native.decisive_artifacts[0].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::entire file': symbol 'entire file' not found
- $.native.decisive_artifacts[2].support[0] pointer 'official/tests/test.sh::entire file': symbol 'entire file' not found
- $.native.success_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::working-directory guard': symbol 'working-directory guard' not found
- $.native.fail_if[0].support[1] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.undecided_if[0].support[1] pointer 'official/tests/test.sh::entire file': symbol 'entire file' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[1] pointer 'official/tests/test.sh::MobileSAM installation': symbol 'MobileSAM installation' not found
- $.stronger.additional_conditions[1].support[1] pointer 'official/tests/test.sh::MobileSAM installation': symbol 'MobileSAM installation' not found`
