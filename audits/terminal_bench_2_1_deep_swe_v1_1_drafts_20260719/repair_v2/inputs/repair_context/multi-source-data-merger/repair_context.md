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
- case_unit_id: `multi-source-data-merger`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: multi-source-data-merger
domain: terminal_bench_2_1
task_id: terminal-bench/multi-source-data-merger
native:
  user_goal:
    text: Merge the three official user-data sources into `/app/merged_users.parquet` using the instructed field mappings and source-priority rules, and write `/app/conflicts.json` in the specified conflict-report format.
    support:
    - official/instruction.md::1-62
  benchmark_success:
    text: 'Native success means the official verifier''s three pytest checks all pass: the two output files exist, `merged_users.parquet` satisfies the exact row/id/value assertions, and `conflicts.json` satisfies the exact conflict-report assertions in `official/tests/test_outputs.py`.'
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::11-56
  checked_by:
    text: '`official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`; the native verdict is the resulting pass/fail of that test file.'
    support:
    - official/tests/test.sh::18-30
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail status for `test_output_files_exist`, `test_merged_data_exact_values`, and `test_conflict_report_values`?
    support:
    - case_packet.md::113-124
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::11-56
  - artifact: verifier/test-stdout.txt
    question: If CTRF is missing or incomplete, does the retained pytest stdout establish whether any of the three official tests passed or failed?
    support:
    - case_packet.md::113-124
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::11-56
  - artifact: artifacts/**
    question: Do retained copies of `/app/merged_users.parquet` and `/app/conflicts.json`, if present, establish or refute the exact assertions made by the three official tests?
    support:
    - case_packet.md::113-124
    - official/tests/test_outputs.py::11-56
  success_if:
  - text: 'Retained non-label evidence establishes that all three official tests pass: `/app/merged_users.parquet` and `/app/conflicts.json` exist; the parquet has exactly 4 rows with `user_id` set `{101,102,103,104}`, user 101 values `John Doe` / `john@a.com` / `2024-01-15`, and user 104 values `Alice Brown` / `alice@c.com` / `2024-04-01`; and `conflicts.json` has `total_conflicts >= 1`, `len(conflicts) == total_conflicts`, at least one conflict for user 101, and any user-101 email conflict shows `values.source_a == "john@a.com"` and `selected == "john@a.com"`.'
    support:
    - official/tests/test_outputs.py::11-56
    - case_packet.md::113-124
  fail_if:
  - text: 'Retained non-label evidence establishes failure of any one of the three official checks: either an output file is missing, the parquet violates any asserted row/id/value condition, or the conflict report violates any asserted `total_conflicts`, list-length, user-101-conflict, or user-101-email-conflict condition; equivalently, retained pytest results show any of the three named tests failed.'
    support:
    - official/tests/test_outputs.py::11-56
    - official/tests/test.sh::18-30
    - case_packet.md::113-124
  undecided_if:
  - text: Retained artifacts do not establish pass/fail status for all three official tests, and retained copies of the output files are absent or insufficient to evaluate the tested assertions independently.
    support:
    - case_packet.md::113-124
    - official/tests/test_outputs.py::11-56
stronger:
  additional_conditions:
  - id: instruction_schema_types
    text: 'Beyond native success, retained `merged_users.parquet` should satisfy the instruction-level output schema: required columns `user_id`, `name`, `email`, and `created_date` are present, every `user_id` is stored as an integer, every `created_date` value is in `YYYY-MM-DD`, and `status` appears only as the optional field named in the instruction.'
    rationale: The instruction makes these schema, type, and date-format requirements explicit, but the released tests only check row count, the `user_id` set, and a few exact field values; they do not fully operationalize the full column/type/date-format requirement.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained copies of `/app/merged_users.parquet`, if present, show the required columns and the full-column integer/date-format properties required by the instruction?
      support:
      - case_packet.md::113-124
      - official/instruction.md::22-28
      - official/instruction.md::55-62
    support:
    - official/instruction.md::22-28
    - official/instruction.md::55-62
    - official/tests/test_outputs.py::17-35
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_email_quantifier_and_failure_scope
Native success silently strengthens the conditional email-conflict assertion from the first matching entry to “any” matching entry, and native failure is narrower than the verifier’s nonzero-pytest criterion.

Required correction: State that only email_conflicts[0] is checked when the list is nonempty, and define native failure to include retained evidence of any nonzero pytest outcome, including assertion, collection, parsing, or execution failure.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], official/tests/test_outputs.py::49-56, official/tests/test.sh::18-30

### decision_rules_sfu: undecided_overlaps_failure
The current U condition can apply after retained evidence already establishes that one official test failed.

Required correction: Define U only when retained non-label evidence establishes neither that all three tests passed nor that pytest/native evaluation failed.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics

### stronger_conditions: stronger_mixes_covered_and_uncovered_requirements
The stronger condition treats required-column presence as an evaluator gap even though the tests directly require those columns, and it does not cleanly enumerate the principal instruction-supported gaps.

Required correction: Remove already-operationalized column presence and ambiguous extra-column language; retain full-column type/date validation and add separate conditions for complete field mapping/priority resolution and complete conflict reporting, each with an explicit noncoverage rationale and assessable retained artifacts.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::22-62, official/tests/test_outputs.py::17-56

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[3].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
