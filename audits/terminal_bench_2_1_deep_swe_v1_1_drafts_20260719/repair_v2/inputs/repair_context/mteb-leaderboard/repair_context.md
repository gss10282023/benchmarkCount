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
- case_unit_id: `mteb-leaderboard`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: mteb-leaderboard
domain: terminal_bench_2_1
task_id: terminal-bench/mteb-leaderboard
native:
  user_goal:
    text: Identify the best embedding model for Scandinavian texts on the Scandinavian MTEB leaderboard as of August 2025, considering only models with results for all benchmark tasks, and write its `organization/model_name` to `/app/result.txt`.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Official verifier success is pytest passing both checks in `official/tests/test_outputs.py`: `/app/result.txt` exists, and its single line strips exactly to `GritLM/GritLM-7B`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  checked_by:
    text: '`official/tests/test.sh` runs pytest on `official/tests/test_outputs.py` and emits a raw CTRF test report at `verifier/ctrf.json`.'
    support:
    - official/tests/test.sh::18-22
    - case_packet.md::59-70
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the raw pytest report show both `test_result_exists` and `test_data_matches` passed, or identify which of those checks failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  - artifact: artifacts/**
    question: Is there a retained copy of `/app/result.txt`, and if so does it contain exactly one line whose stripped value is `GritLM/GritLM-7B`?
    support:
    - case_packet.md::59-70
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  success_if:
  - text: '`verifier/ctrf.json` shows both official tests passed: `test_result_exists` and `test_data_matches`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  - text: 'Or a retained copy of `/app/result.txt` directly establishes the tested post-run state: the file exists and its only line strips exactly to `GritLM/GritLM-7B`.'
    support:
    - case_packet.md::59-70
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  fail_if:
  - text: '`verifier/ctrf.json` shows `test_result_exists` failed.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_result_exists
  - text: '`verifier/ctrf.json` shows `test_data_matches` failed.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_data_matches
  - text: 'A retained copy of `/app/result.txt` exists but does not satisfy the official content check: it has more than one line or its single line strips to a value other than `GritLM/GritLM-7B`.'
    support:
    - case_packet.md::59-70
    - official/tests/test_outputs.py::test_data_matches
  undecided_if:
  - text: Neither a retained raw verifier report nor a retained copy of `/app/result.txt` is available, so the official checks cannot be reconstructed from non-label evidence.
    support:
    - case_packet.md::59-70
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
  - text: Retained evidence is partial or ambiguous and does not determine both required checks, such as showing only an incomplete snippet of `/app/result.txt` or a non-decisive verifier trace.
    support:
    - case_packet.md::59-70
    - official/tests/test_outputs.py::test_result_exists
    - official/tests/test_outputs.py::test_data_matches
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: incorrect_retained_file_line_count_failure
The retained-file failure rule omits the zero-line case even though `assert len(lines) == 1` fails for zero lines as well as multiple lines.

Required correction: Replace “it has more than one line” with a condition covering any line count other than exactly one.

Cited diagnostic locations: checklist.yaml::native.fail_if[2], official/tests/test_outputs.py::test_data_matches

### decision_rules_sfu: empty_file_not_classified_as_f
A retained empty `/app/result.txt` is decisive non-label evidence of native failure, but the current S/F/U rules do not classify it as F.

Required correction: Make the retained-file F rule cover zero lines, multiple lines, and an incorrect stripped value when exactly one line is present.

Cited diagnostic locations: checklist.yaml::native.fail_if[2], checklist.yaml::native.undecided_if, official/tests/test_outputs.py::test_data_matches
