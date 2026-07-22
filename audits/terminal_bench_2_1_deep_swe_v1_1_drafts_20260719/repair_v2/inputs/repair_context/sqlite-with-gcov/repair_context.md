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
- case_unit_id: `sqlite-with-gcov`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sqlite-with-gcov
domain: terminal_bench_2_1
task_id: terminal-bench/sqlite-with-gcov
native:
  user_goal:
    text: Compile SQLite in `/app/sqlite` from the pre-vendored `/app/vendor/sqlite-fossil-release.tar.gz` source with gcov instrumentation, and make `sqlite3` available on `PATH`.
    support:
    - official/instruction.md::1-2
    - official/task.toml::4-6
  benchmark_success:
    text: 'The official verifier succeeds iff the pytest run launched by `official/tests/test.sh` passes all three checks in `official/tests/test_outputs.py`: `test_sqlite_compiled`, `test_sqlite_in_path`, and `test_gcov_enabled`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_sqlite_compiled
    - official/tests/test_outputs.py::test_sqlite_in_path
    - official/tests/test_outputs.py::test_gcov_enabled
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs pytest with CTRF output against `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::18-22
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_sqlite_compiled`, `test_sqlite_in_path`, and `test_gcov_enabled`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_sqlite_compiled
    - official/tests/test_outputs.py::test_sqlite_in_path
    - official/tests/test_outputs.py::test_gcov_enabled
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is missing or incomplete, does retained pytest stdout unambiguously show that the three named tests all passed or identify which named test failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_sqlite_compiled
    - official/tests/test_outputs.py::test_sqlite_in_path
    - official/tests/test_outputs.py::test_gcov_enabled
  success_if:
  - text: Retained non-label verifier evidence establishes that `test_sqlite_compiled`, `test_sqlite_in_path`, and `test_gcov_enabled` all passed.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_sqlite_compiled
    - official/tests/test_outputs.py::test_sqlite_in_path
    - official/tests/test_outputs.py::test_gcov_enabled
  fail_if:
  - text: Retained non-label verifier evidence establishes that `test_sqlite_compiled` failed, meaning `sqlite3` did not successfully run `SELECT sqlite_version();` or produced empty version output.
    support:
    - official/tests/test_outputs.py::test_sqlite_compiled
  - text: Retained non-label verifier evidence establishes that `test_sqlite_in_path` failed, meaning `sqlite3` was not found on `PATH` or could not successfully run `SELECT 1;` from `PATH`.
    support:
    - official/tests/test_outputs.py::test_sqlite_in_path
  - text: Retained non-label verifier evidence establishes that `test_gcov_enabled` failed, meaning running `sqlite3` did not result in at least one `.gcda` file and at least one `.gcno` file under `/app/sqlite`.
    support:
    - official/tests/test_outputs.py::test_gcov_enabled
  undecided_if:
  - text: Retained non-label verifier artifacts do not establish pass/fail status for one or more of `test_sqlite_compiled`, `test_sqlite_in_path`, and `test_gcov_enabled`.
    rationale: Native success or failure is defined only by the official verifier checks; if retained CTRF/stdout evidence is missing, incomplete, or ambiguous about one or more named pytest outcomes, neither native success nor native failure is established from stored evidence.
stronger:
  additional_conditions:
  - id: use_vendored_sqlite_snapshot
    text: Beyond native scoring, retained agent evidence should show that the SQLite source used for the build came from `/app/vendor/sqlite-fossil-release.tar.gz` rather than being fetched from the network.
    rationale: The official instruction explicitly requires using the pre-vendored source snapshot, but the released verifier operationalizes only runtime execution, `PATH` availability, and gcov file creation under `/app/sqlite`; it does not check source provenance.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the recorded agent actions show extraction and build from `/app/vendor/sqlite-fossil-release.tar.gz` and no fetch of SQLite source from the network?
      support:
      - official/instruction.md::1-2
      - official/tests/test_outputs.py::test_sqlite_compiled
      - official/tests/test_outputs.py::test_sqlite_in_path
      - official/tests/test_outputs.py::test_gcov_enabled
    - artifact: agent/*-stdout.txt
      question: If trajectory data is incomplete, do retained agent command logs corroborate use of the vendored tarball rather than a network source download?
      support:
      - official/instruction.md::1-2
      - official/tests/test_outputs.py::test_sqlite_compiled
      - official/tests/test_outputs.py::test_sqlite_in_path
      - official/tests/test_outputs.py::test_gcov_enabled
    support:
    - official/instruction.md::1-2
    - official/tests/test_outputs.py::test_sqlite_compiled
    - official/tests/test_outputs.py::test_sqlite_in_path
    - official/tests/test_outputs.py::test_gcov_enabled
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_semantics_incomplete
Native failure is limited to named assertion failures, omitting other established nonzero pytest outcomes and the verifier's explicit pre-pytest working-directory failure.

Required correction: Define native success from a completed zero-status official pytest invocation and native failure from either the explicit pre-pytest exit or any established nonzero pytest status, including collection, setup, execution, and infrastructure errors.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::12-16, official/tests/test.sh::18-28

### decisive_post_run_evidence: corroborative_artifact_named_decisive
The stronger-layer agent stdout artifact is described as corroboration when the trajectory is incomplete; it cannot independently rule out fetching or using other SQLite source.

Required correction: Remove it as a decisive artifact, or require an independently complete retained record that unambiguously establishes both use of the vendored snapshot and absence of a network SQLite-source fetch.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], case_packet.md::Available Artifact Inventory

### decision_rules_sfu: undecided_overrides_established_failure
The U rule applies when one or more test outcomes are unknown, even if another retained outcome conclusively failed.

Required correction: State that U applies only when evidence establishes neither the complete native-success criterion nor any native-failure condition; an established failure remains F regardless of missing outcomes for other tests.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics
