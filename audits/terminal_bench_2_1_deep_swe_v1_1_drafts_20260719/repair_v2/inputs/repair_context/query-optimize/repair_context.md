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
- case_unit_id: `query-optimize`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: query-optimize
domain: terminal_bench_2_1
task_id: terminal-bench/query-optimize
native:
  user_goal:
    text: Produce `/app/sol.sql` as a single comment-free SQLite query ending with `;` that preserves the original query output, improves efficiency, and does not modify `/app/oewn.sqlite`.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Official success is passing the verifier pytest suite in `official/tests/test_outputs.py`: bundled `my-sql-query.sql` matches `golden.sql`, the database hash is unchanged, `/app/sol.sql` exactly matches `golden.sql` output and column order, solution median runtime is at most `1.05 *` the golden median over 5 iterations, solution SQL is exactly one valid `SELECT`/`WITH` statement with one semicolon, and solution length is <= 2000 characters.'
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::test_compare_golden_vs_my_sql_query_correctness
    - official/tests/test_outputs.py::test_check_for_db_modifications
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
    - official/tests/test_outputs.py::test_outputs_match_exactly
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
    - official/tests/test_outputs.py::test_solution_is_small
  checked_by:
    text: The official task-specific verifier is `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::17-27
    - case_packet.md::62-74
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: 'Does the retained CTRF report show pass/fail status for each official pytest check: bundled-query correctness, DB integrity, runtime threshold, exact output match, single-statement validity, and size limit?'
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::test_compare_golden_vs_my_sql_query_correctness
    - official/tests/test_outputs.py::test_check_for_db_modifications
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
    - official/tests/test_outputs.py::test_outputs_match_exactly
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
    - official/tests/test_outputs.py::test_solution_is_small
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is incomplete or ambiguous, does retained verifier stdout show the same pytest case outcomes and the printed runtime summary needed to interpret the official checks?
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
  success_if:
  - text: 'Retained verifier evidence establishes that all six official pytest checks passed: bundled `my-sql-query.sql` matches `golden.sql`; the database SHA-256 matches the expected value; `/app/sol.sql` exactly matches golden columns, row count, row values, and row order; solution median runtime is <= `1.05 *` the golden median across 5 timed iterations; solution SQL is one valid `SELECT`/`WITH` statement with exactly one semicolon; and solution length is <= 2000 characters.'
    support:
    - official/tests/test_outputs.py::test_compare_golden_vs_my_sql_query_correctness
    - official/tests/test_outputs.py::test_check_for_db_modifications
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
    - official/tests/test_outputs.py::test_outputs_match_exactly
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
    - official/tests/test_outputs.py::test_solution_is_small
  fail_if:
  - text: Retained verifier evidence shows the bundled `my-sql-query.sql` sanity check against `golden.sql` failed.
    support:
    - official/tests/test_outputs.py::test_compare_golden_vs_my_sql_query_correctness
  - text: Retained verifier evidence shows the database hash of `/app/oewn.sqlite` differs from the expected SHA-256.
    support:
    - official/tests/test_outputs.py::test_check_for_db_modifications
  - text: Retained verifier evidence shows `/app/sol.sql` differs from `golden.sql` in column names/order, row count, row values, or row order.
    support:
    - official/tests/test_outputs.py::test_outputs_match_exactly
  - text: Retained verifier evidence shows the solution median runtime exceeds `1.05 *` the golden median over the 5 official timed iterations.
    support:
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
  - text: Retained verifier evidence shows `/app/sol.sql` is missing, is not valid SQLite for the verifier's `EXPLAIN QUERY PLAN` check, does not start with `SELECT`/`WITH`, lacks a terminating semicolon, or contains more than one statement.
    support:
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
  - text: Retained verifier evidence shows `/app/sol.sql` is longer than 2000 characters.
    support:
    - official/tests/test_outputs.py::test_solution_is_small
  undecided_if:
  - text: Retained non-label evidence is missing, truncated, or inconsistent such that the official pytest check statuses cannot be established overall and no retained artifact independently proves any specific native failure condition above.
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::test_compare_golden_vs_my_sql_query_correctness
    - official/tests/test_outputs.py::test_check_for_db_modifications
    - official/tests/test_outputs.py::test_compare_golden_vs_solution_runtime
    - official/tests/test_outputs.py::test_outputs_match_exactly
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
    - official/tests/test_outputs.py::test_solution_is_small
stronger:
  additional_conditions:
  - id: no_sql_comments
    text: Retained solution SQL contains no `--` or `/* ... */` comments. This is stronger than native because the instruction forbids comments, but the released verifier strips comments before its single-statement format checks and does not separately fail on comment presence.
    rationale: The official instruction makes comment absence part of the task, but the native verifier operationalizes statement shape and syntax after removing comment text, so native pass does not by itself prove the file is comment-free.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does the retained solution SQL text contain any SQL comment syntax (`--` line comments or `/* ... */` block comments)?
      support:
      - case_packet.md::62-74
      - official/instruction.md::1-7
      - official/tests/test_outputs.py::test_solution_contains_single_sql_query
    support:
    - official/instruction.md::1-7
    - official/tests/test_outputs.py::test_solution_contains_single_sql_query
```

## Prior independent review findings to repair

### native_user_goal: goal_weakens_maximal_efficiency_intent
`native.user_goal.text` replaces the official request to make the query “as efficient as possible” with the narrower requirement that it merely improve efficiency.

Required correction: State the official maximal-efficiency intent directly while retaining the same-output, SQLite, file-format, destination-path, and no-database-modification requirements.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-7
