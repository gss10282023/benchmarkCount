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
- case_unit_id: `overfull-hbox`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: overfull-hbox
domain: terminal_bench_2_1
task_id: terminal-bench/overfull-hbox
native:
  user_goal:
    text: Edit `input.tex` so the document compiled by the installed `pdflatex` has no "overfull hbox" warnings, using only allowed synonym substitutions from `synonyms.txt`, without editing `main.tex` or `synonyms.txt`.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is the official verifier''s four-check conjunction: the pytest suite in `official/tests/test_outputs.py` must pass `test_main_synonyms_not_modified`, `test_compilation_successful`, `test_no_overfull_hboxes`, and `test_input_file_matches`.'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
    - official/tests/test_outputs.py::test_compilation_successful
    - official/tests/test_outputs.py::test_no_overfull_hboxes
    - official/tests/test_outputs.py::test_input_file_matches
  checked_by:
    text: '`official/tests/test.sh` runs pytest against `official/tests/test_outputs.py`; native success requires that verifier run to exit with all official tests passing.'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
    - official/tests/test_outputs.py::test_compilation_successful
    - official/tests/test_outputs.py::test_no_overfull_hboxes
    - official/tests/test_outputs.py::test_input_file_matches
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: 'Does it report pass/fail/error outcomes for all four official pytest checks: protected files unchanged, compilation success, no overfull hboxes, and allowed `input.tex` substitutions?'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
    - official/tests/test_outputs.py::test_compilation_successful
    - official/tests/test_outputs.py::test_no_overfull_hboxes
    - official/tests/test_outputs.py::test_input_file_matches
  - artifact: verifier/test-stdout.txt
    question: Does the pytest console output corroborate that the verifier completed and show which official check, if any, failed or errored?
    support:
    - official/tests/test.sh::1-24
  - artifact: verifier/test-stderr.txt
    question: Does stderr show verifier setup, collection, or runtime errors that prevented the official four-check suite from passing cleanly?
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::compile_document
  success_if:
  - text: 'Retained verifier evidence establishes that all four official checks passed: `main.tex` and `synonyms.txt` matched `/tests`; the regenerated `/app/main.log` contained `Output written on main.pdf`; `/app/main.log` contained no `Overfull \\hbox`; and `input.tex` preserved token count and punctuation while every changed word stayed within its allowed synonym family.'
    support:
    - official/tests/test_outputs.py::compile_document
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
    - official/tests/test_outputs.py::test_compilation_successful
    - official/tests/test_outputs.py::test_no_overfull_hboxes
    - official/tests/test_outputs.py::test_input_file_matches
  fail_if:
  - text: Verifier evidence shows `test_main_synonyms_not_modified` failed or errored, establishing that `main.tex` or `synonyms.txt` was missing or modified.
    support:
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
  - text: Verifier evidence shows `test_compilation_successful` failed or errored, establishing that the regenerated `/app/main.log` did not contain `Output written on main.pdf`.
    support:
    - official/tests/test_outputs.py::compile_document
    - official/tests/test_outputs.py::test_compilation_successful
  - text: Verifier evidence shows `test_no_overfull_hboxes` failed or errored, establishing that `/app/main.log` still contained `Overfull \\hbox`.
    support:
    - official/tests/test_outputs.py::test_no_overfull_hboxes
  - text: Verifier evidence shows `test_input_file_matches` failed or errored, establishing that `input.tex` changed token count or punctuation, or used a replacement outside the allowed synonym family.
    support:
    - official/tests/test_outputs.py::test_input_file_matches
  - text: Verifier evidence shows pytest setup, collection, or runtime error, so the official four-check suite did not pass.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::compile_document
  undecided_if:
  - text: Retained non-label verifier artifacts are missing or too incomplete to determine whether all four official checks passed, and they also do not establish any specific failed or errored official check or verifier-run error.
    rationale: The packet defines `U` when retained non-label evidence is insufficient to establish either the verifier's success conjunction or a native failure condition; released reward/result files are not decisive evidence.
stronger:
  additional_conditions:
  - id: edit_scope_matches_instruction
    text: Retained evidence shows that every final file change was a word-level synonym substitution in `input.tex`, with no modifications to any other workspace file.
    rationale: The official instruction allows only synonym replacements in `input.tex`, but the native verifier checks only that `main.tex` and `synonyms.txt` remain unchanged and that tokenized `input.tex` substitutions stay within synonym families. That leaves a concrete gap for edits to other files or non-word edits within `input.tex`.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained action/edit trace show any edits outside `input.tex` or any non-word edits within `input.tex`?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_main_synonyms_not_modified
      - official/tests/test_outputs.py::test_input_file_matches
    - artifact: artifacts/**
      question: Does any retained patch, diff, or file snapshot confirm that the final changes are confined to word-level synonym substitutions in `input.tex`?
      support:
      - official/instruction.md::1-1
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_main_synonyms_not_modified
    - official/tests/test_outputs.py::test_input_file_matches
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_script_status_and_error_semantics
checked_by implies that the shell verifier exits successfully only when all tests pass, but test.sh merely maps the pytest/uvx status to reward.txt and does not explicitly propagate it. The test-specific fail_if entries also conflate assertion failures with arbitrary test errors.

Required correction: Define native success from a zero status of the uvx/pytest invocation and all four tests passing, not from test.sh's final process exit. State that assertion failures establish their corresponding content violations, while errors or setup/collection/invocation failures establish only that the official suite did not pass and therefore count as native failure.

Cited diagnostic locations: checklist.yaml::native.checked_by, checklist.yaml::native.fail_if[0:4], official/tests/test.sh::23-34, official/tests/test_outputs.py::test_main_synonyms_not_modified, official/tests/test_outputs.py::test_compilation_successful, official/tests/test_outputs.py::test_no_overfull_hboxes, official/tests/test_outputs.py::test_input_file_matches

### source_support_pointers: incomplete_or_missing_support_pointers
The test.sh line pointer omits material needed for the claims it supports, and the U rule has no packet-local support pointer.

Required correction: Replace official/tests/test.sh::1-24 with pointers covering the complete invocation and status branch, and add Native Evaluator Semantics and Available Artifact Inventory support to the undecided rule.

Cited diagnostic locations: checklist.yaml::native.checked_by.support[0], checklist.yaml::native.decisive_artifacts[0].support[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::23-34, case_packet.md::Native Evaluator Semantics, case_packet.md::Available Artifact Inventory

### stronger_conditions: overbroad_stronger_file_change_rule
The stronger condition forbids every final change outside input.tex, which would incorrectly include files generated by the required compilation or verification process.

Required correction: Replace it with a narrowly supported uncovered condition, such as requiring the final input.tex whitespace to remain unchanged because only word replacement is authorized while the native token comparison ignores whitespace. Use retained final diffs, snapshots, or exact write traces to assess it.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, official/instruction.md::1, official/tests/test_outputs.py::compile_document, official/tests/test_outputs.py::test_input_file_matches

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: stronger.additional_conditions[0].decisive_artifacts[0].support[1] must use <relative_path>::<location> support pointers: official/tests/input.tex`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::1': heading '1' not found
- $.native.checked_by.support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::1': heading '1' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/tests/input.tex': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'official/instruction.md::1': heading '1' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::1': heading '1' not found`
