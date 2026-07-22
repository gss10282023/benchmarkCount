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
- case_unit_id: `password-recovery`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: password-recovery
domain: terminal_bench_2_1
task_id: terminal-bench/password-recovery
native:
  user_goal:
    text: Recover the deleted PASSWORD from `launchcode.txt` somewhere under `/app`, using the stated format constraints, and write each matching recovered password one per line to `/app/recovered_passwords.txt`.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is official verifier success: pytest runs `test_recovery_file_exists` and `test_password_match`, so `/app/recovered_passwords.txt` must exist, contain at least one newline-split guess, and include the exact string `8XDP5Q2RT9ZK7VB3BV4WW54`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
  checked_by:
    text: Pytest invoked by `official/tests/test.sh` against `official/tests/test_outputs.py`, with CTRF written to `/logs/verifier/ctrf.json`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail/error for both `test_recovery_file_exists` and `test_password_match`?
    support:
    - case_packet.md::64-75
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
  - artifact: verifier/test-stdout.txt
    question: If needed to interpret the run, does retained pytest stdout confirm whether `/app/recovered_passwords.txt` existed and whether the exact-password assertion passed or failed?
    support:
    - case_packet.md::64-75
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
  success_if:
  - text: A retained verifier report establishes that both `test_recovery_file_exists` and `test_password_match` passed; equivalently, `/app/recovered_passwords.txt` existed, had at least one newline-split entry, and included `8XDP5Q2RT9ZK7VB3BV4WW54`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
  fail_if:
  - text: A retained verifier report shows `test_recovery_file_exists` failed or errored.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-10
  - text: A retained verifier report shows `test_password_match` failed or errored, including because there were no guesses or because `8XDP5Q2RT9ZK7VB3BV4WW54` was not among the newline-split entries.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::13-18
  undecided_if:
  - text: Retained non-label evidence does not establish the outcomes of both official tests; for example, `verifier/ctrf.json` is missing or ambiguous and pytest stdout does not clearly show whether the output file existed and whether the exact-password check passed.
    support:
    - case_packet.md::64-75
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-18
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: inexact_password_test_semantics
The native failure rule describes an impossible no-guesses failure and does not cover nonzero pytest invocation or collection failures counted by test.sh.

Required correction: State the test.sh exit-status mapping exactly; remove the impossible empty-list failure explanation and include retained evidence of any nonzero official pytest invocation as native failure.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], official/tests/test_outputs.py::test_password_match, official/tests/test.sh::18-27

### decision_rules_sfu: runner_failure_misclassified_as_u
The current U rule may absorb an execution-established nonzero verifier invocation when per-test results are missing.

Required correction: Classify unambiguously established nonzero official pytest invocation, collection, or execution status as F; reserve U for evidence that establishes neither zero nor nonzero status.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-27

### source_support_pointers: unsupported_no_guesses_claim
The cited implementation does not support the claim that len(guesses) can be zero.

Required correction: Replace that claim with behavior actually supported by the code: the exact password must be one newline-split entry, while read, invocation, collection, test failure, or test error can cause nonzero verifier status.

Cited diagnostic locations: checklist.yaml::native.fail_if[1].support, official/tests/test_outputs.py::test_password_match

### stronger_conditions: missing_source_supported_stronger_measurements
The verifier checks only file existence and literal membership, leaving the officially requested forensic-recovery provenance and candidate-format discipline unmeasured.

Required correction: Add separate stronger conditions for demonstrable recovery from the deleted data and for all submitted nonempty guess lines satisfying the instructed candidate format, using retained trajectory evidence to assess each in principle.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::1-9, official/README.md::What It Tests, official/tests/test_outputs.py::test_password_match

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
