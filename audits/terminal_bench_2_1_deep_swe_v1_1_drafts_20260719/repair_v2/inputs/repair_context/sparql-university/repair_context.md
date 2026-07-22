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
- case_unit_id: `sparql-university`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sparql-university
domain: terminal_bench_2_1
task_id: terminal-bench/sparql-university
native:
  user_goal:
    text: Write `/app/solution.sparql` as a SPARQL query over `/app/university_graph.ttl` that returns each full professor meeting the stated EU-location and `>10` currently-enrolled-students criteria, using `2025-08-16` as the reference date, as `?professorName` plus grouped `?countries`.
    support:
    - official/instruction.md::1-19
  benchmark_success:
    text: 'Native success is established when official `test.sh` reaches pytest and all three official checks pass: `/app/solution.sparql` exists, runs without SPARQL error on `/tests/university_graph_test.ttl`, and its normalized `(professorName, countries)` result set exactly matches `REFERENCE_RESULTS`.'
    support:
    - official/tests/test.sh::12-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
    - official/tests/test_outputs.py::DATA_PATH
    - official/tests/test_outputs.py::REFERENCE_RESULTS
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs pytest with CTRF output for `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it show whether `test_sparql_file_exists`, `test_sparql_runs_without_error`, and `test_sparql_query_results` each passed or failed?
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
  - artifact: verifier/test-stdout.txt
    question: If pytest failed or did not complete cleanly, what file-missing, SPARQL-exception, result-mismatch, or script-abort message was reported?
    support:
    - official/tests/test.sh::12-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
  success_if:
  - text: Retained verifier evidence shows `test.sh` reached pytest and `test_sparql_file_exists`, `test_sparql_runs_without_error`, and `test_sparql_query_results` all passed; this establishes file existence, successful execution on `/tests/university_graph_test.ttl`, and exact normalized equality to `REFERENCE_RESULTS`.
    support:
    - official/tests/test.sh::12-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
    - official/tests/test_outputs.py::DATA_PATH
    - official/tests/test_outputs.py::REFERENCE_RESULTS
  fail_if:
  - text: Retained verifier evidence shows `test.sh` aborted before the pytest suite completed, including the explicit `/` working-directory guard.
    support:
    - official/tests/test.sh::12-15
  - text: Retained verifier evidence shows `test_sparql_file_exists` failed, so `/app/solution.sparql` was not present for the official check.
    support:
    - official/tests/test_outputs.py::test_sparql_file_exists
  - text: Retained verifier evidence shows `test_sparql_runs_without_error` failed, so the saved query did not execute cleanly on `/tests/university_graph_test.ttl`.
    support:
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::DATA_PATH
  - text: Retained verifier evidence shows `test_sparql_query_results` failed because the query result set, after the test's country-string normalization, was not exactly equal to `REFERENCE_RESULTS`.
    support:
    - official/tests/test_outputs.py::test_sparql_query_results
    - official/tests/test_outputs.py::REFERENCE_RESULTS
  undecided_if:
  - text: Retained non-label artifacts do not establish whether `test.sh` reached pytest or whether each of the three official checks passed or failed; for example, `verifier/ctrf.json` and pytest logs are missing, truncated, or internally inconsistent.
    support:
    - official/tests/test.sh::12-23
    - official/tests/test_outputs.py::test_sparql_file_exists
    - official/tests/test_outputs.py::test_sparql_runs_without_error
    - official/tests/test_outputs.py::test_sparql_query_results
stronger:
  additional_conditions:
  - id: genuine-graph-query
    text: Beyond native scoring, the retained `/app/solution.sparql` should be a genuine SPARQL retrieval query for the instructed university graph task, not a constant-answer construction that only reproduces the hidden test reference rows.
    rationale: The official instruction and README require querying the provided university knowledge graph to retrieve qualifying professors, but the released evaluator only checks file existence, executability on `/tests/university_graph_test.ttl`, and equality to fixed `REFERENCE_RESULTS`; a literal answer table can satisfy native scoring without demonstrating the stated retrieval task.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If a retained copy of `/app/solution.sparql` exists, does its text derive `?professorName` and `?countries` from graph triples and task predicates rather than enumerating the four expected answer rows?
      support:
      - official/instruction.md::1-19
      - official/README.md::3-16
      - official/tests/test_outputs.py::DATA_PATH
      - official/tests/test_outputs.py::REFERENCE_RESULTS
    - artifact: agent/trajectory.json
      question: If no query-file copy is retained, does the trajectory record the final SPARQL written to `/app/solution.sparql` well enough to inspect whether it is a genuine graph query rather than a literal answer table?
      support:
      - official/instruction.md::1-19
      - official/README.md::3-16
      - official/tests/test_outputs.py::DATA_PATH
      - official/tests/test_outputs.py::REFERENCE_RESULTS
    support:
    - official/instruction.md::1-19
    - official/README.md::3-16
    - official/tests/test_outputs.py::test_sparql_query_results
    - official/tests/test_outputs.py::DATA_PATH
    - official/tests/test_outputs.py::REFERENCE_RESULTS
```

## Prior independent review findings to repair

### native_user_goal: goal-output-contract-incomplete
native.user_goal omits material parts of the official output contract: DISTINCT GROUP_CONCAT with the specified separator and inclusion of all countries where the professor currently works.

Required correction: Restate the exact SELECT expression and the all-current-work-countries meaning while retaining the full professor, EU, student-count, date, graph, and output-path requirements.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::14-19

### native_evaluator_semantics: nonzero-verifier-status-not-covered
The native failure rules do not cover a nonzero uvx/pytest status caused before individual test outcomes, because test.sh can continue to its failure mapping without itself aborting.

Required correction: State the test.sh zero/nonzero status mapping and add a failure rule for retained non-label evidence establishing a nonzero uvx/pytest outcome, including launch, setup, and collection failures.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], official/tests/test.sh::18-30

### decision_rules_sfu: undecided-overlaps-known-failure
The current U rule can apply when one test failure is established but the status of every test is not known.

Required correction: Define U exclusively as the case where retained non-label evidence establishes neither the all-pass native criterion nor any official failure condition.

Cited diagnostic locations: checklist.yaml::native.fail_if[1-3], checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics
