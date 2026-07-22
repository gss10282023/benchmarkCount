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
- case_unit_id: `db-wal-recovery`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: db-wal-recovery
domain: terminal_bench_2_1
task_id: terminal-bench/db-wal-recovery
native:
  user_goal:
    text: Repair the encrypted/corrupted WAL so SQLite can read it, recover all 11 database records including WAL changes, and write them as a JSON array sorted by `id` to `/app/recovered.json`.
    support:
    - official/instruction.md::1-10
  benchmark_success:
    text: 'Retained non-label evidence establishes that `/app/recovered.json` satisfies every official pytest check in `official/tests/test_outputs.py`: the file exists, parses as a non-empty list of records with integer `id`/`value` and string `name`, ids are sorted with no duplicates, the list is exactly ids 1 through 11, names for ids 3 through 11 match the official expected values, `value` is 150 for id 1 and 250 for id 2, and WAL-specific recovery yields more than 5 records with the checked WAL update/insert values present.'
    support:
    - official/tests/test.sh::1-23
    - official/tests/test_outputs.py::1-85
  checked_by:
    text: The task-specific verifier runs `pytest` on `official/tests/test_outputs.py` via `official/tests/test.sh`.
    support:
    - official/tests/test.sh::1-23
    - official/tests/test_outputs.py::1-85
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show whether each official pytest check in `official/tests/test_outputs.py` passed or failed?
    support:
    - official/tests/test.sh::1-23
    - official/tests/test_outputs.py::1-85
  - artifact: artifacts/**
    question: If a retained copy of `/app/recovered.json` is present, does it satisfy the exact file, JSON, structure, sort, uniqueness, cardinality, id/name, and checked value predicates enforced by the official tests?
    support:
    - official/tests/test_outputs.py::1-85
  success_if:
  - text: A retained `verifier/ctrf.json` shows that every pytest check in `official/tests/test_outputs.py` passed.
    support:
    - official/tests/test.sh::1-23
    - official/tests/test_outputs.py::1-85
  - text: Or a retained copy of `/app/recovered.json` under `artifacts/**` independently satisfies all official predicates checked by `official/tests/test_outputs.py`.
    support:
    - official/tests/test_outputs.py::1-85
  fail_if:
  - text: A retained `verifier/ctrf.json` shows that any pytest check in `official/tests/test_outputs.py` failed.
    support:
    - official/tests/test.sh::1-23
    - official/tests/test_outputs.py::1-85
  - text: Or a retained copy of `/app/recovered.json` under `artifacts/**` violates any official predicate checked by `official/tests/test_outputs.py`, including wrong JSON type or field types, unsorted or duplicate ids, not exactly 11 ids `1..11`, wrong checked names, or id 1/id 2 values other than 150/250.
    support:
    - official/tests/test_outputs.py::1-85
  undecided_if:
  - text: Retained evidence does not include a decisive verifier report and also does not retain enough of `/app/recovered.json` to evaluate every official predicate directly.
    rationale: The native claim is exactly the official pytest predicate set; without per-test verifier evidence or a retained recovered output file sufficient to check that full predicate set, neither native success nor native failure is established from stored evidence.
stronger:
  additional_conditions:
  - id: wal-file-actually-repaired
    text: Beyond native scoring, retained evidence should show that the agent actually repaired `/app/main.db-wal` into a SQLite-readable WAL state, not merely produced a correct `recovered.json`; the released evaluator only checks the JSON output.
    rationale: The official instruction and README require fixing the WAL so SQLite can read it, but the released tests never inspect `/app/main.db-wal` or run SQLite against a repaired WAL file and instead only read `/app/recovered.json`. This is a concrete task/evaluator gap.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the retained commands and observed results show SQLite successfully reading the database with the repaired WAL after the WAL file was modified?
      support:
      - official/instruction.md::1-10
      - official/README.md::1-31
    - artifact: agent/*-stdout.txt
      question: Do retained command outputs show a successful SQLite read from the repaired WAL-backed database, rather than only construction of `recovered.json` by another route?
      support:
      - official/instruction.md::1-10
      - official/README.md::1-31
    support:
    - official/instruction.md::1-10
    - official/README.md::1-31
    - official/tests/test_outputs.py::1-85
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-exit-semantics
Native success and failure are stated only through per-test outcomes or direct output predicates, omitting that test.sh maps the pytest process exit status to the released result.

Required correction: State the pytest exit-zero/nonzero rule explicitly and permit retained verifier logs to establish collection, execution, or internal-error failures without using reward.txt as decisive evidence.

Cited diagnostic locations: official/tests/test.sh::uvx pytest invocation, official/tests/test.sh::if [ $? -eq 0 ], checklist.yaml::native.fail_if

### decisive_post_run_evidence: stdout-not-route-decisive
Standalone agent stdout cannot independently establish that SQLite read through a repaired WAL rather than that expected data was produced by another route.

Required correction: Remove standalone stdout as decisive for this condition, or combine the relevant command and observed result in a single retained trace artifact such as agent/trajectory.json.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], review_prompt.md::decisive_post_run_evidence

### decision_rules_sfu: u-overlaps-f
The U rule requires insufficient evidence to evaluate every predicate, even though partial evidence can conclusively demonstrate one predicate violation and therefore native failure.

Required correction: Define U only when there is neither complete evidence of success nor evidence of any output-predicate or verifier-execution failure.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics

### source_support_pointers: incomplete-source-ranges
The cited line ranges exclude portions of the official sources needed for the associated claims.

Required correction: Use complete, resolvable function- or passage-level pointers covering the output requirements, every test, and the verifier exit-status branch.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::native.benchmark_success.support[1], official/instruction.md::The output should have the format, official/tests/test_outputs.py::test_wal_was_decrypted

### stronger_conditions: stronger-artifact-insufficient
Although the stronger requirement and evaluator gap are valid, one named artifact cannot assess the causal WAL-repair fact it is assigned.

Required correction: Retain the condition but use a trace containing both commands and observed results as its decisive artifact; remove standalone stdout.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::Your task is to, official/tests/test_outputs.py::test_wal_was_decrypted

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::Your task is to': heading 'Your task is to' not found
- $.native.user_goal.support[1] pointer 'official/instruction.md::The output should have the format': heading 'The output should have the format' not found
- $.native.benchmark_success.support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.decisive_artifacts[2].support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.success_if[0].support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.native.fail_if[1].support[0] pointer 'official/tests/test.sh::uvx pytest invocation': symbol 'uvx pytest invocation' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::Your task is to': heading 'Your task is to' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::Your task is to': heading 'Your task is to' not found`
