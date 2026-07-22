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
- case_unit_id: `crack-7z-hash`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: crack-7z-hash
domain: terminal_bench_2_1
task_id: terminal-bench/crack-7z-hash
native:
  user_goal:
    text: Create `/app/solution.txt` containing the word found in `secret_file.txt` inside `secrets.7z`.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: Native success is established when retained verifier evidence shows the official pytest verifier for `/tests/test_outputs.py` passed, which requires both `test_solution_file` and `test_solution_content` to pass.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test_outputs.py::test_solution_content
  checked_by:
    text: Checked by the official verifier's pytest run and retained verifier outputs, primarily `verifier/ctrf.json` corroborated by verifier stdout/stderr.
    support:
    - official/tests/test.sh::18-22
    - case_packet.md::52-63
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_solution_file` and `test_solution_content`?
    support:
    - case_packet.md::52-63
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test_outputs.py::test_solution_content
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout corroborate that the pytest run executed `/tests/test_outputs.py` and report which of the two official tests passed or failed?
    support:
    - case_packet.md::52-63
    - official/tests/test.sh::18-22
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr show test errors or verifier failures that affect interpretation of the pytest outcome?
    support:
    - case_packet.md::52-63
    - official/tests/test.sh::18-22
  success_if:
  - text: '`verifier/ctrf.json`, corroborated by verifier stdout/stderr, shows both `test_solution_file` and `test_solution_content` passed in the official pytest run.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test_outputs.py::test_solution_content
    - case_packet.md::52-63
  fail_if:
  - text: Retained verifier evidence shows `test_solution_file` failed, establishing that `/app/solution.txt` was missing for the official check.
    support:
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test.sh::18-22
    - case_packet.md::52-63
  - text: Retained verifier evidence shows `test_solution_content` failed, establishing that `/app/solution.txt` did not contain stripped content exactly equal to `honeybear` for the official check.
    support:
    - official/tests/test_outputs.py::test_solution_content
    - official/tests/test.sh::18-22
    - case_packet.md::52-63
  undecided_if:
  - text: Native verdict is undecided when retained non-label verifier artifacts do not establish whether `test_solution_file` and `test_solution_content` passed or failed, such as missing or non-interpretable CTRF data with insufficient verifier stdout/stderr corroboration.
    support:
    - case_packet.md::52-63
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test_outputs.py::test_solution_content
stronger:
  additional_conditions:
  - id: archive-derived-word-evidence
    text: Beyond native scoring, retained agent trace/log evidence should show that the word written to `/app/solution.txt` was obtained from `secret_file.txt` inside `secrets.7z` by cracking/extracting the archive, rather than being written directly as a constant.
    rationale: The official task materials describe recovering the word from the password-protected archive and explicitly mention cracking/extraction steps with John the Ripper, but the released verifier operationalizes only the final existence of `/app/solution.txt` and exact stripped content `honeybear`. This is a concrete reviewable gap between task intent and native measurement.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show commands/actions that crack or extract `secrets.7z` and read `secret_file.txt` before writing `/app/solution.txt`?
      support:
      - case_packet.md::52-58
      - official/instruction.md::1-1
      - official/README.md::4-4
      - official/README.md::26-30
    - artifact: agent/*-stdout.txt
      question: Do retained agent stdout logs show outputs from cracking or extraction steps against `secrets.7z` or reading `secret_file.txt` that support the archive-derived result?
      support:
      - case_packet.md::52-58
      - official/README.md::4-4
      - official/README.md::26-30
    support:
    - official/instruction.md::1-1
    - official/README.md::4-4
    - official/README.md::21-30
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file
    - official/tests/test_outputs.py::test_solution_content
    - case_packet.md::52-58
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-failure-semantics-incomplete
Native F does not reproduce the verifier’s complete failure semantics: `test.sh` selects failure whenever the pytest command status is nonzero, not only when either named assertion is reported as failed.

Required correction: Define native success as retained non-label evidence establishing a zero status for the official pytest invocation and native failure as evidence establishing any nonzero status, including test, collection, execution, or verifier errors.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-28

### decision_rules_sfu: sfu-misclassifies-verifier-errors
Because F is limited to two explicit test failures, retained evidence of another nonzero official verifier outcome may incorrectly fall under U.

Required correction: Make F cover every evidenced nonzero outcome of the official pytest invocation and reserve U exclusively for evidence that establishes neither zero nor nonzero status.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-28, case_packet.md::Native Evaluator Semantics

### source_support_pointers: artifact-inventory-pointer-range
The repeated `case_packet.md::52-63` pointer does not reach the packet entries for `verifier/ctrf.json`, `verifier/test-stdout.txt`, and `verifier/test-stderr.txt`.

Required correction: Replace the inaccurate range with `case_packet.md::Available Artifact Inventory` or exact ranges that contain each named artifact.

Cited diagnostic locations: checklist.yaml::native.checked_by.support, checklist.yaml::native.decisive_artifacts, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[0].support[3] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.fail_if[0].support[3] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[2] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].support[5] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
