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
- case_unit_id: `extract-moves-from-video`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: extract-moves-from-video
domain: terminal_bench_2_1
task_id: terminal-bench/extract-moves-from-video
native:
  user_goal:
    text: Transcribe the entire text content of `/app/video.mp4` into `/app/solution.txt` as the player's input moves, one command per line.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is the official verifier passing both checks: `/app/solution.txt` exists, and its raw contents achieve at least 90.0% Levenshtein similarity to the fixed expected multiline command string in `official/tests/test_outputs.py`.'
    support:
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
  checked_by:
    text: '`official/tests/test.sh` runs pytest on `test_solution_file_exists` and `test_solution_content_similarity` from `official/tests/test_outputs.py`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_solution_file_exists` and `test_solution_content_similarity`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
  - artifact: verifier/test-stdout.txt
    question: Does retained pytest stdout confirm the same two test outcomes and any failure message about a missing `/app/solution.txt` or similarity below 90.0%?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
  success_if:
  - text: 'Retained verifier artifacts show both official tests passed: `/app/solution.txt` existed and its raw contents met the verifier''s 90.0% Levenshtein-similarity threshold against the fixed expected command string.'
    support:
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
  fail_if:
  - text: Retained verifier artifacts show `test_solution_file_exists` failed, establishing that `/app/solution.txt` did not exist at verification time.
    support:
    - official/tests/test_outputs.py::test_solution_file_exists
  - text: Retained verifier artifacts show `test_solution_content_similarity` failed, establishing that the file's raw contents were below the verifier's 90.0% Levenshtein-similarity threshold.
    support:
    - official/tests/test_outputs.py::test_solution_content_similarity
  undecided_if:
  - text: Retained non-label artifacts do not establish pass/fail outcomes for the two official tests, and no retained solution-file content is available to independently resolve file existence plus the 90.0% similarity check.
    support:
    - case_packet.md::59-70
    - official/tests/test_outputs.py::test_solution_file_exists
    - official/tests/test_outputs.py::test_solution_content_similarity
stronger:
  additional_conditions:
  - id: exact_full_transcript
    text: Beyond native scoring, retained `/app/solution.txt` should exactly capture the full sequence of input moves from the video, one command per line, rather than merely satisfying the verifier's >=90.0% whole-file similarity threshold.
    rationale: The official instruction requires transcribing the entire contents and writing all moves one per line, while the released evaluator operationalizes only file existence plus a 90.0% whole-file similarity threshold.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If retained, does `/app/solution.txt` exactly list every input move from the video, one command per line, with no omissions, additions, or malformed lines?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_solution_content_similarity
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_solution_content_similarity
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_semantics_text_mode_and_errors
The native rules do not fully reproduce the content test: Python reads /app/solution.txt in text mode, computes a specifically normalized character-level Levenshtein score, and can produce a test error while opening or decoding the file. The checklist instead refers to “raw contents” and recognizes only the below-threshold assertion as content failure.

Required correction: Describe the text-mode read and exact similarity formula, and classify retained evidence of a failed or errored official test node as native failure while keeping verifier-infrastructure cases undecidable unless the evidence establishes an official test non-pass.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.fail_if[1], official/tests/test_outputs.py::test_solution_content_similarity, official/tests/test.sh::18-27

### decision_rules_sfu: sfu_error_gap
An existing but unreadable or undecodable solution can make test_solution_content_similarity error. The listed F rules do not cover that established official non-pass, while the U rule is broad enough to absorb it.

Required correction: Add an F rule for retained non-label evidence that either official test failed or errored, and define U only for evidence that establishes neither both-test success nor any official test failure/error.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test_outputs.py::test_solution_content_similarity

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
