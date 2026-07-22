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
- case_unit_id: `regex-chess`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: regex-chess
domain: terminal_bench_2_1
task_id: terminal-bench/regex-chess
native:
  user_goal:
    text: Produce `/app/re.json` as a JSON list of `[regex, replacement]` pairs under 100,000 pairs and under 10 MB that, when applied sequentially to white-to-move FEN strings, returns all legal next FEN positions with queen-only promotion, correct castling-right tracking, and en-passant handling; halfmove and fullmove counts may be incorrect.
    support:
    - official/instruction.md::1-27
  benchmark_success:
    text: 'Native success means the official verifier''s pytest run passes all four checks in `/tests/test_outputs.py`: `test_immortal_game`, `test_game_of_century`, and `test_naroditsky_ivanchuk` all satisfy `verify_legal_moves` on every tested position under the evaluator''s comparison rule, and `test_not_long` passes the file-size and pair-count limits.'
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::verify_legal_moves
    - official/tests/test_outputs.py::test_immortal_game
    - official/tests/test_outputs.py::test_game_of_century
    - official/tests/test_outputs.py::test_naroditsky_ivanchuk
    - official/tests/test_outputs.py::test_not_long
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::18-23
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report show pass/fail status for `test_immortal_game`, `test_game_of_century`, `test_naroditsky_ivanchuk`, and `test_not_long`?
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_immortal_game
    - official/tests/test_outputs.py::test_game_of_century
    - official/tests/test_outputs.py::test_naroditsky_ivanchuk
    - official/tests/test_outputs.py::test_not_long
  - artifact: verifier/test-stdout.txt
    question: Does the pytest transcript corroborate the suite outcome and, on failure, identify the offending move-generation assertion, tested position, or size-limit assertion?
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::verify_legal_moves
    - official/tests/test_outputs.py::test_not_long
  success_if:
  - text: Retained verifier evidence shows `test_immortal_game`, `test_game_of_century`, and `test_naroditsky_ivanchuk` all passed, so every generated move on each tested white-to-move position satisfied the evaluator's acceptance rule and the generated move count matched the python-chess legal-move count after excluding underpromotions.
    support:
    - official/tests/test_outputs.py::verify_legal_moves
    - official/tests/test_outputs.py::test_immortal_game
    - official/tests/test_outputs.py::test_game_of_century
    - official/tests/test_outputs.py::test_naroditsky_ivanchuk
  - text: Retained verifier evidence shows `test_not_long` passed, so `/app/re.json` was under 10e6 bytes and parsed to fewer than 1e5 regex pairs.
    support:
    - official/tests/test_outputs.py::test_not_long
  fail_if:
  - text: Retained verifier evidence shows the official pytest suite on `/tests/test_outputs.py` failed or errored before all three PGN-based move-generation tests passed under `verify_legal_moves`; this includes any generated move rejected by the evaluator's membership rule, any move-count mismatch on a tested position, or a suite error before those checks completed.
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::verify_legal_moves
    - official/tests/test_outputs.py::test_immortal_game
    - official/tests/test_outputs.py::test_game_of_century
    - official/tests/test_outputs.py::test_naroditsky_ivanchuk
  - text: Retained verifier evidence shows `test_not_long` failed or errored, or otherwise establishes that `/app/re.json` was at least 10e6 bytes or contained at least 1e5 regex pairs.
    support:
    - official/tests/test_outputs.py::test_not_long
  undecided_if:
  - text: The retained non-label evidence is missing or too incomplete to determine whether the official pytest suite finished with all three PGN-based move-generation tests and `test_not_long` passing, and it does not separately establish any suite failure or size-limit violation.
    rationale: Native success is defined by the official pytest composition. If retained artifacts do not reliably show whether that composition passed, and they also do not independently prove a native failure condition, neither success nor failure is established from stored evidence.
stronger:
  additional_conditions:
  - id: exact-en-passant-field
    text: Beyond native scoring, the generated FENs should match the correct en-passant field exactly on the official tested positions; native scoring is weaker because it also accepts a generated move after replacing its final FEN field with `-`.
    rationale: The official instruction requires a fully correct move generator including en-passant, but `verify_legal_moves` accepts a generated four-field FEN `x` when either `x` exactly matches a python-chess legal move or `x` with its final field forced to `-` matches. That leaves a concrete measurement gap for incorrect en-passant targets.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does the retained solution artifact include `/app/re.json`, allowing exact replay of the official tested FENs with the source-defined substitution loop and strict four-field comparison?
      support:
      - official/instruction.md::1-8
      - official/tests/test_outputs.py::run_solution
    - artifact: verifier/test-stdout.txt
      question: Does the verifier transcript confirm the replay scope is the official three PGN-based test positions exercised by the native suite?
      support:
      - official/tests/test_outputs.py::do_test_game
      - official/tests/test_outputs.py::test_immortal_game
      - official/tests/test_outputs.py::test_game_of_century
      - official/tests/test_outputs.py::test_naroditsky_ivanchuk
    support:
    - official/instruction.md::20-25
    - official/tests/test_outputs.py::verify_legal_moves
```

## Prior independent review findings to repair

### native_evaluator_semantics: incomplete-verifier-failure-semantics
Native F omits conclusive nonzero verifier-command outcomes outside individual test assertions and omits the configured verifier timeout.

Required correction: Define native success in terms of the uvx/pytest command returning zero with all four tests passing; define F for any evidenced nonzero command outcome, setup/invocation failure, or configured verifier timeout/termination before a zero-status completion. Add the verifier stderr log as a possible decisive non-label artifact.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.fail_if[1], official/tests/test.sh::18-29, official/task.toml::[verifier].timeout_sec

### decision_rules_sfu: timeout-or-invocation-failure-can-fall-to-u
The current U rule can absorb an incomplete suite even when retained evidence conclusively establishes a timeout or setup/invocation failure.

Required correction: Explicitly assign evidenced verifier timeout, termination, setup failure, or nonzero verifier-command status to F, and reserve U for records where neither zero-status success nor a concrete failure is established.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29, official/task.toml::[verifier].timeout_sec

### stronger_conditions: missing-supported-stronger-gaps
The stronger layer addresses only relaxed en-passant comparison. It omits duplicate-masked omissions on tested positions and correctness over supported white-to-move positions outside the finite three-PGN suite.

Required correction: Add concrete stronger conditions requiring exact, duplicate-free successor-set equality on official tested positions and full semantic correctness across the stated supported input domain, with rationales identifying the membership/length and finite-suite measurement gaps.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::1-27, official/README.md::Verification, official/tests/test_outputs.py::verify_legal_moves, official/tests/test_outputs.py::do_test_game
