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
- case_unit_id: `code-from-image`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: code-from-image
domain: terminal_bench_2_1
task_id: terminal-bench/code-from-image
native:
  user_goal:
    text: Produce the same final value that the pseudocode shown in `/app/code.png` would print, after implementing the snippet's intended logic in any language, and write that value to `/app/output.txt`.
    support:
    - official/instruction.md::1-3
    - official/README.md::5-9
  benchmark_success:
    text: 'Native success requires retained verifier evidence that both official pytest checks passed: `/app/output.txt` exists, and its stripped contents both start with `bee26a` and exactly equal `bee26a133f103b9ecda444c70ec22cafef6e31a3de7af6d047974dc90ce3defe`.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::10-31
  checked_by:
    text: The task-specific verifier runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`, so the native claim is checked by the two tests defined in `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::10-31
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show pass/fail outcomes for `test_output_file_exists` and `test_output_is_correct`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::10-31
  - artifact: verifier/test-stdout.txt
    question: Does the verifier stdout confirm the same two test outcomes or record the assertion details when one of them fails?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::10-31
  - artifact: verifier/test-stderr.txt
    question: Does the verifier stderr show a pytest or verifier-script interruption that leaves the two official test outcomes unestablished?
    support:
    - official/tests/test.sh::12-22
    - official/tests/test_outputs.py::10-31
  success_if:
  - text: Retained verifier evidence establishes that `test_output_file_exists` passed and `test_output_is_correct` passed.
    support:
    - official/tests/test_outputs.py::10-31
  fail_if:
  - text: Retained verifier evidence establishes that `test_output_file_exists` failed, so `/app/output.txt` did not exist when checked.
    support:
    - official/tests/test_outputs.py::10-15
  - text: Retained verifier evidence establishes that `test_output_is_correct` failed because the stripped output did not start with `bee26a` or did not exactly equal `bee26a133f103b9ecda444c70ec22cafef6e31a3de7af6d047974dc90ce3defe`.
    support:
    - official/tests/test_outputs.py::18-31
  undecided_if:
  - text: Retained non-label evidence does not establish pass/fail outcomes for both official tests, including when the CTRF report is missing or incomplete or the verifier logs show pytest never reached a decisive result for them.
    support:
    - official/tests/test.sh::12-22
    - official/tests/test_outputs.py::10-31
stronger:
  additional_conditions:
  - id: implemented-logic-not-just-output
    text: Beyond native scoring, require retained agent evidence that the final value was produced by implementing and running the pseudocode logic from `/app/code.png`, not only by directly writing the expected hash to `/app/output.txt`.
    rationale: The official task asks the agent to implement the snippet's intended logic, but the released verifier operationalizes only the final contents of `/app/output.txt`.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show the agent creating or running code that implements the pseudocode logic rather than only writing the expected output literal?
      support:
      - official/instruction.md::1-3
      - official/README.md::5-9
      - official/tests/test_outputs.py::18-31
    - artifact: agent/*-stdout.txt
      question: Do retained agent stdout logs show execution of an implementation that computes the final value?
      support:
      - official/README.md::5-9
      - official/tests/test_outputs.py::18-31
    - artifact: artifacts/**
      question: Do retained task artifacts include implementation source or execution byproducts that substantiate that the logic was implemented and used?
      support:
      - official/README.md::5-9
      - official/tests/test_outputs.py::18-31
    support:
    - official/instruction.md::1-3
    - official/README.md::5-9
    - official/tests/test_outputs.py::18-31
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-failure-semantics-incomplete
The native rules omit verifier failures caused by pytest errors, collection/setup failures, and other established nonzero exits of the exact `uvx ... pytest` command.

Required correction: Define native success and failure from the scored pytest command’s zero versus nonzero status, while retaining the two test assertions as the case-specific substantive checks. Include failed tests, test errors, collection/setup errors, and interruptions that establish a nonzero command status.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-29, official/tests/test_outputs.py::18-31

### decision_rules_sfu: known-nonzero-misclassified-as-u
The current U rule can move an established benchmark-counted nonzero verifier execution to U merely because both individual test outcomes were not produced.

Required correction: Reserve U for records where retained non-label evidence cannot establish whether the scored pytest command returned zero or nonzero. Classify an unambiguously established nonzero command outcome as F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29, case_packet.md::Native Evaluator Semantics

### source_support_pointers: u-claim-not-supported-by-cited-shell
The `test.sh` citation contradicts the blanket interruption-to-U rule because the script’s `$?` branch counts an established interrupted/nonzero pytest command as failure.

Required correction: Replace the unsupported U claim with a rule tied to inability to establish the command status, and cite the pytest invocation and immediate `$?` branch.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0].support, official/tests/test.sh::18-29
