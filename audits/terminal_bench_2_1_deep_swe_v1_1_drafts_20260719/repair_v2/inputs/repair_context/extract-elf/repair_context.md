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
- case_unit_id: `extract-elf`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: extract-elf
domain: terminal_bench_2_1
task_id: terminal-bench/extract-elf
native:
  user_goal:
    text: Provide `extract.js` so that running `node extract.js /app/a.out > out.json` produces a JSON object mapping memory addresses to integer values from the ELF binary, with every reported value matching the reference solution and at least 75% of reference addresses covered.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success requires both official pytest checks to pass: `/app/extract.js` exists as a file, and on the verifier-compiled `/app/new.o` the program exits successfully, emits parseable JSON, has no overlapping address whose value differs from the verifier reference JSON, and includes at least 75% of the reference addresses.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_extract_js_exists
    - official/tests/test_outputs.py::test_output_matches_reference
  checked_by:
    text: Checked by `official/tests/test.sh`, which runs pytest on `test_extract_js_exists` and `test_output_matches_reference` from `official/tests/test_outputs.py` and writes a CTRF report.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_extract_js_exists
    - official/tests/test_outputs.py::test_output_matches_reference
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report show pass/fail for `test_extract_js_exists` and `test_output_matches_reference`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_extract_js_exists
    - official/tests/test_outputs.py::test_output_matches_reference
  - artifact: artifacts/**
    question: Do retained artifacts include the generated `out.json` and `reference.json`, or equivalent retained JSON outputs, sufficient to recompute the no-mismatched-overlap check and the 75% coverage check if the test report is absent or ambiguous?
    support:
    - official/tests/test_outputs.py::test_output_matches_reference
  success_if:
  - text: Retained evidence establishes that `test_extract_js_exists` passed, so `/app/extract.js` existed and was a regular file.
    support:
    - official/tests/test_outputs.py::test_extract_js_exists
  - text: 'Retained evidence establishes that `test_output_matches_reference` passed on `/app/new.o`: the agent program returned exit code 0, `out.json` was valid JSON, no address present in both outputs had a different value, and the agent output included at least 75% of the reference addresses.'
    support:
    - official/tests/test_outputs.py::test_output_matches_reference
  fail_if:
  - text: Retained evidence establishes that `test_extract_js_exists` failed, so `/app/extract.js` was missing or not a regular file.
    support:
    - official/tests/test_outputs.py::test_extract_js_exists
  - text: Retained evidence establishes that `test_output_matches_reference` failed, including because compilation of `/app/new.c` failed, the agent program or reference program exited nonzero, required JSON output was missing or unparsable, at least one overlapping address had a different value, or the agent output covered less than 75% of the reference addresses.
    support:
    - official/tests/test_outputs.py::test_output_matches_reference
  undecided_if:
  - text: Retained artifacts do not establish pass or fail for one or both official tests, and also do not preserve enough raw evidence to determine whether `/app/extract.js` existed and whether the JSON outputs satisfy the no-mismatch and 75%-coverage checks.
    rationale: The native criterion is exactly the two official pytest checks; without a retained test report or equivalent retained JSON outputs and existence evidence, neither native success nor native failure can be independently fixed from stored artifacts.
stronger:
  additional_conditions:
  - id: no-extra-addresses
    text: Because the instruction says every reported address must match the reference solution, stronger success additionally requires that the output contain no addresses absent from the reference output; native scoring only checks shared addresses for differing values and does not reject extra addresses.
    rationale: 'This is a concrete instruction/evaluator gap: the official instruction requires every included address to match, but the released test only flags addresses that are both in the agent output and in the reference output with different values.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained artifacts include both the agent `out.json` and the verifier `reference.json`, or equivalent retained JSON outputs, so a reviewer can confirm that the agent output contains no address missing from the reference output?
      support:
      - official/tests/test_outputs.py::test_output_matches_reference
    support:
    - official/instruction.md::5-9
    - official/tests/test_outputs.py::test_output_matches_reference
  - id: provided-aout-covered
    text: Because the user instruction targets the provided `/app/a.out` but native scoring only exercises `/app/new.o`, stronger success additionally requires retained evidence that `extract.js` was run on `/app/a.out` and that the resulting JSON met the same correctness and 75%-coverage rule for that provided binary.
    rationale: 'This makes the measurement gap explicit: the official task names the provided `/app/a.out`, while the released verifier compiles and checks only `/app/new.o`.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show a run of `node extract.js /app/a.out` and preserve the resulting output location or contents?
      support:
      - official/instruction.md::1-9
    - artifact: artifacts/**
      question: Do retained artifacts include the JSON output produced for `/app/a.out`, plus sufficient retained comparison data for the provided binary, to assess the same no-mismatched-values and 75%-coverage rule?
      support:
      - official/instruction.md::1-9
      - official/tests/test_outputs.py::test_output_matches_reference
    support:
    - official/instruction.md::1-9
    - official/tests/test_outputs.py::test_output_matches_reference
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-verifier-exit-semantics
Native success and failure do not fully reproduce the shell verifier’s zero/nonzero pytest exit-status rule or its explicit working-directory guard.

Required correction: Define native success as the verifier passing its working-directory guard and the pytest invocation returning zero; define native failure as retained non-label evidence of the guard exiting or pytest returning nonzero, including test, collection, startup, and internal errors.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if, official/tests/test.sh::13-29

### decisive_post_run_evidence: non-independent-native-json-artifacts
The retained JSON outputs can establish only the comparison assertions, not the complete test outcome, because they do not expose compilation or subprocess exit statuses.

Required correction: Remove artifacts/** as a decisive artifact for complete native success/failure. Use CTRF or sufficiently explicit verifier logs for the complete outcome; describe JSON outputs only as evidence for the particular comparison facts they expose.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], official/tests/test_outputs.py::test_output_matches_reference

### decisive_post_run_evidence: non-independent-trajectory-artifact
agent/trajectory.json cannot independently establish that output for /app/a.out matched its reference with at least 75% coverage.

Required correction: Remove the trajectory as decisive for that stronger condition. Retain an artifact requirement that includes both the /app/a.out output and sufficient reference comparison data.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[1].decisive_artifacts[0], official/instruction.md::1-9

### decision_rules_sfu: incomplete-native-f-rule
The current F rule omits benchmark-counted pytest nonzero outcomes where neither individual test receives a failed status.

Required correction: Classify F whenever retained non-label evidence establishes the verifier guard exit or pytest nonzero status; reserve U for cases where neither zero nor nonzero native outcome can be established.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if, official/tests/test.sh::13-29
