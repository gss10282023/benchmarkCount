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
- case_unit_id: `sqlite-db-truncate`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sqlite-db-truncate
domain: terminal_bench_2_1
task_id: terminal-bench/sqlite-db-truncate
native:
  user_goal:
    text: Recover as many rows as possible from `/app/trunc.db` and write them to `/app/recover.json` as JSON objects with `word` and `value` fields.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is that the single official verifier test passes: `/app/recover.json` is loadable as JSON and its distinct exact `(word, value)` pairs include at least 7 of the 8 official pairs used by the test.'
    support:
    - official/tests/test_outputs.py::8-31
    - official/tests/test.sh::18-22
  checked_by:
    text: '`official/tests/test.sh` runs `pytest` on `official/tests/test_outputs.py`, and the decisive native check is `test_json_data`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::20-31
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show `official/tests/test_outputs.py::test_json_data` passed or failed?
    support:
    - case_packet.md::58-69
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::20-31
  - artifact: verifier/test-stdout.txt
    question: What pytest result and failure details, if any, were reported for `test_json_data`?
    support:
    - case_packet.md::58-69
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::20-31
  - artifact: artifacts/**
    question: If the produced `/app/recover.json` was retained, does it parse as JSON and contain at least 7 distinct exact official `(word, value)` pairs under the test's set-intersection rule?
    support:
    - case_packet.md::58-69
    - official/tests/test_outputs.py::8-31
  success_if:
  - text: Retained verifier evidence establishes that `official/tests/test_outputs.py::test_json_data` passed.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::20-31
    - case_packet.md::58-69
  - text: If retained, `/app/recover.json` independently establishes native success when it parses as JSON and its distinct exact `(word, value)` pairs contain at least 7 of the 8 official pairs used by the test.
    support:
    - official/tests/test_outputs.py::8-31
    - case_packet.md::58-69
  fail_if:
  - text: Retained verifier evidence establishes that `official/tests/test_outputs.py::test_json_data` failed, including assertion failure or file/JSON/key/type errors while loading or reading `/app/recover.json`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::20-31
    - case_packet.md::58-69
  - text: If retained, `/app/recover.json` establishes native failure when it is not valid JSON or when its distinct exact-match count against the 8 official `(word, value)` pairs is 6 or fewer.
    support:
    - official/tests/test_outputs.py::8-31
    - case_packet.md::58-69
  undecided_if:
  - text: The retained artifacts do not show a decisive verifier pass/fail for `test_json_data`, and no retained `/app/recover.json` is available to recompute the official exact-match rule.
    support:
    - case_packet.md::58-69
    - official/tests/test_outputs.py::8-31
    - official/tests/test.sh::18-22
stronger:
  additional_conditions:
  - id: recover_all_official_rows
    text: 'Measurement gap beyond native pass: retained evidence should show `/app/recover.json` recovers all 8 official `(word, value)` pairs, not merely 7 of 8.'
    rationale: The instruction says to recover as many rows as possible, but the released verifier accepts any output with more than 6 matches.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If `/app/recover.json` was retained, does it contain all 8 distinct exact official `(word, value)` pairs?
      support:
      - case_packet.md::58-69
      - official/tests/test_outputs.py::8-31
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::8-31
```

## Prior independent review findings to repair

### native_user_goal: goal_array_shape_omitted
The native user goal does not unambiguously preserve the instruction’s top-level JSON array format.

Required correction: State that `/app/recover.json` must be a JSON array of objects containing `word` and `value` fields.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-1

### native_evaluator_semantics: native_test_exceptions_omitted
The direct-output rules reduce the verifier to parsing plus match count and omit exceptions raised while iterating items, indexing `word`/`value`, or hashing tuple members.

Required correction: Define direct-state success and failure by replaying all operations in `test_json_data`: open and JSON loading, both set comprehensions, set intersection, and the `score > 6` assertion. Describe matches using Python set equality.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.success_if[1], checklist.yaml::native.fail_if[1], official/tests/test_outputs.py::22-31

### decision_rules_sfu: malformed_state_classification_gap
A retained valid-JSON output that raises during tuple-set construction is assigned neither S nor F nor U by the stated rules, even though it conclusively establishes native failure.

Required correction: Classify any retained final output that would raise during the official test’s loading or tuple-set construction as F, and reserve U for evidence insufficient to replay or observe the test outcome.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0], official/tests/test_outputs.py::22-31

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[0].support[2] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.fail_if[0].support[2] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.fail_if[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
