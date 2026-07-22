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
- case_unit_id: `cobol-modernization`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: cobol-modernization
domain: terminal_bench_2_1
task_id: terminal-bench/cobol-modernization
native:
  user_goal:
    text: 'Create `/app/program.py` that reimplements `program.cbl`: read `/app/src/INPUT.DAT`, apply the COBOL logic to `/app/data/ACCOUNTS.DAT`, `/app/data/BOOKS.DAT`, and `/app/data/TRANSACTIONS.DAT`, and produce the same resulting `.DAT` contents as the COBOL program from the same starting state.'
    support:
    - official/instruction.md::1-10
  benchmark_success:
    text: 'Native success is established when the official verifier run passes all three pytest checks in `official/tests/test_outputs.py`: `/app/program.py` exists, the named data files exist, and after `test_program_output` resets the files to its hard-coded fixture and runs `/app/program.py` three times on its hard-coded `INPUT.DAT` values, the final `ACCOUNTS.DAT`, `BOOKS.DAT`, and `TRANSACTIONS.DAT` contents exactly equal the test''s expected strings.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::11-94
  checked_by:
    text: Checked by the official verifier script `official/tests/test.sh`, which runs pytest on `official/tests/test_outputs.py` and treats a clean pytest exit as success.
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::11-94
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record pass/fail outcomes for `test_required_files_exist`, `test_data_files_exist`, and `test_program_output` from the official pytest run?
    support:
    - case_packet.md::68-80
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::11-94
  - artifact: verifier/test-stdout.txt
    question: Does pytest stdout show the three official tests ran and, if a test failed, identify the missing file, non-zero program run, or file-content mismatch?
    support:
    - case_packet.md::68-80
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::11-94
  - artifact: verifier/test-stderr.txt
    question: If CTRF or stdout is incomplete, does stderr contain the decisive execution error or pytest failure details for the official tests?
    support:
    - case_packet.md::68-80
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::11-94
  success_if:
  - text: Retained verifier evidence shows `test_required_files_exist`, `test_data_files_exist`, and `test_program_output` all passed in the official pytest run.
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::11-94
  fail_if:
  - text: Retained verifier evidence shows `test_required_files_exist` failed because `/app/program.py` was missing.
    support:
    - official/tests/test_outputs.py::11-18
  - text: Retained verifier evidence shows `test_data_files_exist` failed because any of `/app/data/ACCOUNTS.DAT`, `/app/data/BOOKS.DAT`, `/app/data/TRANSACTIONS.DAT`, or `/app/src/INPUT.DAT` was missing.
    support:
    - official/tests/test_outputs.py::21-31
  - text: Retained verifier evidence shows `test_program_output` failed because any `python /app/program.py` invocation returned non-zero or because the final `ACCOUNTS.DAT`, `BOOKS.DAT`, or `TRANSACTIONS.DAT` content differed from the test's expected strings after the test's fixed setup and three input writes.
    support:
    - official/tests/test_outputs.py::34-94
  undecided_if:
  - text: Retained non-label verifier evidence is missing or too incomplete to determine whether the three official pytest checks passed or which one failed, such as when `verifier/ctrf.json` is absent/incomplete and pytest stdout/stderr do not establish the outcomes.
    support:
    - case_packet.md::68-80
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::11-94
stronger:
  additional_conditions:
  - id: official-cobol-equivalence-on-task-provided-state
    text: 'Beyond native scoring, retained evidence should establish that `/app/program.py` matches the COBOL program on the task-provided comparison boundary: starting from the official `INPUT.DAT` and the official initial `ACCOUNTS.DAT`, `BOOKS.DAT`, and `TRANSACTIONS.DAT`, both programs produce the same resulting `.DAT` contents.'
    rationale: The official instruction defines success as equivalence to the COBOL program for the same input and initial data state. The released verifier instead overwrites those files with a different three-transaction fixture and checks only that one Python-only scenario, so native success does not by itself establish the official COBOL-comparison claim on the task-provided state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show both the COBOL program and `/app/program.py` being run from the same official starting files and their resulting `.DAT` outputs being compared?
      support:
      - case_packet.md::68-80
      - official/instruction.md::1-10
      - official/environment/src/INPUT.DAT::1-1
      - official/environment/data/ACCOUNTS.DAT::1-1
      - official/environment/data/BOOKS.DAT::1-1
      - official/environment/data/TRANSACTIONS.DAT::1-1
    - artifact: agent/*-stdout.txt
      question: Do retained command outputs show that the compared `ACCOUNTS.DAT`, `BOOKS.DAT`, and `TRANSACTIONS.DAT` results from the COBOL and Python runs were equal on that official starting state?
      support:
      - case_packet.md::68-80
      - official/instruction.md::1-10
      - official/environment/src/INPUT.DAT::1-1
      - official/environment/data/ACCOUNTS.DAT::1-1
      - official/environment/data/BOOKS.DAT::1-1
      - official/environment/data/TRANSACTIONS.DAT::1-1
    support:
    - official/instruction.md::1-10
    - official/environment/src/INPUT.DAT::1-1
    - official/environment/data/ACCOUNTS.DAT::1-1
    - official/environment/data/BOOKS.DAT::1-1
    - official/environment/data/TRANSACTIONS.DAT::1-1
    - official/tests/test_outputs.py::36-84
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-failure-criterion-too-narrow
The released verifier selects failure for any nonzero exit from its pytest command, while the checklist limits native F to three categories of test assertion failure.

Required correction: Replace or supplement `native.fail_if` with a rule covering any retained-evidence-established nonzero outcome of the exact official pytest invocation, including assertion, collection, and execution errors.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-29

### decision_rules_sfu: evidence-established-nonzero-can-fall-outside-f
A decisive stderr/stdout trace showing pytest collection or execution failure would establish the verifier's failure branch, but the present SFU rules would not assign F and could incorrectly leave the record U.

Required correction: Define F by the exact nonzero pytest criterion and reserve U solely for cases where retained non-label evidence establishes neither zero nor nonzero completion of that invocation.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], checklist.yaml::native.decisive_artifacts[2], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
