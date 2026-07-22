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
- case_unit_id: `large-scale-text-editing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: large-scale-text-editing
domain: terminal_bench_2_1
task_id: terminal-bench/large-scale-text-editing
native:
  user_goal:
    text: Transform `/app/input.csv` to match `/app/expected.csv` exactly by saving a headless Vim script at `/app/apply_macros.vim` that defines three distinct non-empty macros in registers `a`, `b`, and `c`, keeps total macro keystrokes under 200, and uses only the specified command forms.
    support:
    - official/instruction.md::1-18
  benchmark_success:
    text: 'Native success means the official verifier run passes all five pytest checks in `official/tests/test_outputs.py`: script existence; well-formed/allowed-command validation with `a`/`b`/`c` defined and executed; headless Vim exit code 0 with post-run `expected.csv` generation; SHA-256 equality of transformed `input.csv` and `expected.csv`; and macro evidence showing `a`/`b`/`c` are non-empty, pairwise distinct, and total keystrokes are `< 200`.'
    support:
    - official/tests/test.sh::27-31
    - official/tests/test_outputs.py::test_apply_macros_exists
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  checked_by:
    text: The official checker is `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`; native pass is pytest exit 0 on that suite.
    support:
    - official/tests/test.sh::27-37
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report show PASS for `test_apply_macros_exists`, `test_apply_macros_well_formed`, `test_apply_macros_runs`, `test_input_equiv_expected`, and `test_macros_nonempty_and_efficient`?
    support:
    - official/tests/test.sh::27-31
    - official/tests/test_outputs.py::test_apply_macros_exists
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  - artifact: verifier/test-stdout.txt
    question: If any official test did not pass or the CTRF record is incomplete, what pytest assertion output identifies the specific failed native check?
    support:
    - official/tests/test.sh::27-31
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  success_if:
  - text: 'Retained verifier evidence establishes that all five official tests pass: the script exists, satisfies the allowed-line checks, runs headlessly with Vim exit code 0, yields `input.csv` with the same SHA-256 as `expected.csv`, and produces non-empty pairwise-distinct macros whose counted total keystrokes are `< 200`.'
    support:
    - official/tests/test.sh::27-31
    - official/tests/test_outputs.py::test_apply_macros_exists
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  fail_if:
  - text: Retained verifier evidence shows `test_apply_macros_exists` failed, so `/app/apply_macros.vim` was missing.
    support:
    - official/tests/test_outputs.py::test_apply_macros_exists
  - text: Retained verifier evidence shows `test_apply_macros_well_formed` failed, including missing `:wq`/`:x`, missing any required `setreg` or `:%normal! @a/@b/@c` line, an invalid line type, or a macro string rejected by the native forbidden-pattern check.
    support:
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::_is_valid_line
    - official/tests/test_outputs.py::_is_valid_keystroke_sequence
  - text: Retained verifier evidence shows `test_apply_macros_runs` failed because headless Vim exited nonzero or post-run `expected.csv` generation failed.
    support:
    - official/tests/test_outputs.py::test_apply_macros_runs
  - text: Retained verifier evidence shows `test_input_equiv_expected` failed because transformed `input.csv` and `expected.csv` did not match under the verifier's SHA-256 comparison.
    support:
    - official/tests/test_outputs.py::test_input_equiv_expected
  - text: Retained verifier evidence shows `test_macros_nonempty_and_efficient` failed because any macro was empty, macros were not pairwise distinct, the keystroke report was unparsable or inconsistent, or total keystrokes were `>= 200`.
    support:
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  undecided_if:
  - text: '`verifier/ctrf.json` is missing, truncated, or does not clearly record all five official test outcomes, and the retained verifier stdout is insufficient to determine whether every native check passed or which native check failed.'
    support:
    - official/tests/test.sh::27-31
    - official/tests/test_outputs.py::test_apply_macros_exists
    - official/tests/test_outputs.py::test_apply_macros_well_formed
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
  - text: Only retained workspace artifacts such as the script are available, without enough verifier evidence to establish the tested run's headless Vim exit status, post-run `expected.csv` generation, hash comparison result, and macro-count check result.
    support:
    - official/instruction.md::13-18
    - official/tests/test_outputs.py::test_apply_macros_runs
    - official/tests/test_outputs.py::test_input_equiv_expected
    - official/tests/test_outputs.py::test_macros_nonempty_and_efficient
stronger:
  additional_conditions:
  - id: macro_content_strictness
    text: Retained `artifacts/apply_macros.vim` shows only the instruction-listed command lines, and each macro body stays within basic Vim editing keystrokes or essential Ex transformation commands; this is stronger than native because the released checker ignores comment lines and otherwise only blacklist-matches selected forbidden patterns inside macro strings.
    rationale: The official instruction imposes a positive `ONLY`-commands and limited-macro-content requirement, but `_is_valid_line` drops comment lines before validation and `_is_valid_keystroke_sequence` accepts any macro text that does not match its forbidden regex list.
    decisive_artifacts:
    - artifact: artifacts/apply_macros.vim
      question: Does the retained script contain only the allowed command lines, with no extra comment or other non-command lines, and do macro bodies remain within the instruction's basic-editing / essential-Ex scope?
      support:
      - official/instruction.md::5-12
      - official/tests/test_outputs.py::_is_valid_line
      - official/tests/test_outputs.py::_is_valid_keystroke_sequence
    support:
    - official/instruction.md::5-12
    - official/tests/test_outputs.py::_is_valid_line
    - official/tests/test_outputs.py::_is_valid_keystroke_sequence
```

## Prior independent review findings to repair

### native_user_goal: incomplete_user_goal
The native user goal omits required execution of all three macros, the restrictions on macro contents, and successful execution under the specified headless Vim command.

Required correction: Expand native.user_goal to include those material official requirements without replacing the broader transformation goal with a test-only formulation.

Cited diagnostic locations: checklist.yaml::native.user_goal, official/instruction.md::1-18

### native_evaluator_semantics: incomplete_native_failure_semantics
The failure rules cover selected test assertions but not every nonzero outcome of the official verifier command or every assertion path in the five tests.

Required correction: Define native F exhaustively as retained non-label evidence that the official uvx/pytest invocation returned nonzero, including individual test failures, collection/invocation/internal errors, or interruption; retain task-specific examples as non-exhaustive detail.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::27-37, official/tests/test_outputs.py::test_apply_macros_runs, official/tests/test_outputs.py::test_input_equiv_expected, official/tests/test_outputs.py::test_macros_nonempty_and_efficient

### decision_rules_sfu: failure_misclassified_as_undecidable
The current U rule can require identification of a specific failed test even when retained evidence already establishes the official verifier’s nonzero outcome.

Required correction: Make U apply only when retained non-label evidence establishes neither zero nor nonzero verifier status and establishes neither all five passes nor any native failure.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics, official/tests/test.sh::33-37

### source_support_pointers: incorrect_comment_filter_pointer
The stronger condition cites the wrong functions for its claim that comment lines are ignored by native validation.

Required correction: Add official/tests/test_outputs.py::test_apply_macros_well_formed to the condition, rationale, artifact, and support pointers for comment filtering.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].support, official/tests/test_outputs.py::test_apply_macros_well_formed
