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
- case_unit_id: `tune-mjcf`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: tune-mjcf
domain: terminal_bench_2_1
task_id: terminal-bench/tune-mjcf
native:
  user_goal:
    text: Produce `/app/model.xml` that speeds the MuJoCo simulation to at most 60% of the reference runtime for the same 2.0-second scene, reaches the same full physics state within `atol=1e-5` without NaN/Inf, and leaves `/app/model_ref.xml` unchanged.
    support:
    - official/instruction.md::1-6
  benchmark_success:
    text: 'The official verifier in `official/tests/test.sh` succeeds only if its pytest run over `official/tests/test_outputs.py` passes all four official checks: `test_model_ref_unchanged`, `test_tuned_model_exists`, `test_correctness`, and `test_model_speed`.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::test_model_ref_unchanged
    - official/tests/test_outputs.py::test_tuned_model_exists
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::test_model_speed
  checked_by:
    text: '`official/tests/test.sh` running `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.'
    support:
    - official/tests/test.sh::18-29
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_model_ref_unchanged`, `test_tuned_model_exists`, `test_correctness`, and `test_model_speed`?
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_model_ref_unchanged
    - official/tests/test_outputs.py::test_tuned_model_exists
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::test_model_speed
  - artifact: verifier/test-stdout.txt
    question: Does the pytest stdout confirm the official test run completed and, when needed, show the printed `Final state difference` and `Time pctg` outputs from the correctness and speed checks?
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::test_model_speed
  - artifact: verifier/test-stderr.txt
    question: Does stderr show collection/import/runtime errors that affect interpretation of the official pytest outcomes?
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::18-29
  success_if:
  - text: Retained verifier evidence establishes that `test_model_ref_unchanged` passed, so `/app/model_ref.xml` matched the verifier's reference copy.
    support:
    - official/tests/test_outputs.py::test_model_ref_unchanged
  - text: Retained verifier evidence establishes that `test_tuned_model_exists` passed, so `/app/model.xml` existed for verification.
    support:
    - official/tests/test_outputs.py::test_tuned_model_exists
  - text: Retained verifier evidence establishes that `test_correctness` passed, so the tuned model loaded, simulated 2.0 seconds, produced no NaN/Inf in the final full-physics state, and `np.allclose(..., atol=1e-5)` held against the reference model.
    support:
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::simulate_model
  - text: Retained verifier evidence establishes that `test_model_speed` passed, so after 20 timing runs per model with 5th/95th percentile extremes dropped, mean `act_time_pctg` was `<= 0.6`.
    support:
    - official/tests/test_outputs.py::test_model_speed
    - official/tests/test_outputs.py::simulation_time
    - official/tests/test_outputs.py::drop_extreme_percentiles
  fail_if:
  - text: Retained verifier evidence establishes that `test_model_ref_unchanged` failed, so `/app/model_ref.xml` was changed relative to the verifier's reference copy.
    support:
    - official/tests/test_outputs.py::test_model_ref_unchanged
  - text: Retained verifier evidence establishes that `test_tuned_model_exists` failed, so `/app/model.xml` was missing.
    support:
    - official/tests/test_outputs.py::test_tuned_model_exists
  - text: Retained verifier evidence establishes that `test_correctness` failed, including model-load failure, NaN/Inf in the final state, or final-state mismatch beyond `atol=1e-5`.
    support:
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::simulate_model
  - text: Retained verifier evidence establishes that `test_model_speed` failed because the measured mean `act_time_pctg` after percentile trimming exceeded `0.6`.
    support:
    - official/tests/test_outputs.py::test_model_speed
    - official/tests/test_outputs.py::simulation_time
    - official/tests/test_outputs.py::drop_extreme_percentiles
  - text: Retained verifier evidence establishes that the official pytest run errored before satisfying the four-check success condition, such as collection/import/runtime failure reported by pytest.
    support:
    - official/tests/test.sh::18-29
    rationale: '`test.sh` treats a nonzero pytest exit as verifier failure even if the nonzero exit comes from pytest error states rather than an assertion failure in a named test.'
  undecided_if:
  - text: Retained non-label evidence does not provide a complete, interpretable record of the official pytest outcomes, so it cannot establish either that all four official checks passed or that any specific official failure condition occurred.
    support:
    - case_packet.md::62-74
    - official/tests/test.sh::18-29
stronger:
  additional_conditions:
  - id: preserve-body-physical-properties
    text: Beyond native scoring, retained tuned-MJCF evidence should show that body physical properties were not changed, not merely that the resulting simulation happened to pass the released correctness and speed tests.
    rationale: The official task materials state that physical body properties must not change, but the released verifier operationalizes only reference-file identity, tuned-model existence, final-state agreement, and speed.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does retained output include the final tuned `model.xml` so its body physical-property fields can be compared directly against the reference model?
      support:
      - case_packet.md::62-74
      - official/README.md::7-13
    - artifact: agent/trajectory.json
      question: If the final model file is not otherwise retained, does the trajectory preserve the final file contents or patch needed to determine whether body physical-property fields changed?
      support:
      - case_packet.md::62-74
      - official/README.md::7-13
    support:
    - official/README.md::7-13
    - official/tests/test_outputs.py::test_model_ref_unchanged
    - official/tests/test_outputs.py::test_tuned_model_exists
    - official/tests/test_outputs.py::test_correctness
    - official/tests/test_outputs.py::test_model_speed
```

## Prior independent review findings to repair

### native_user_goal: missing_official_physical_property_goal
native.user_goal omits the official requirement not to change body physical properties.

Required correction: Add preservation of body physical properties to native.user_goal while keeping its direct, unoperationalized assessment in stronger.additional_conditions rather than native success.

Cited diagnostic locations: checklist.yaml::native.user_goal, official/README.md::Task Requirements, official/instruction.md::1-6

### native_evaluator_semantics: inexact_native_failure_semantics
The drafted fail_if rules do not exactly cover all ways the official pytest command can return nonzero and make unsupported causal conclusions for some non-pass outcomes.

Required correction: Define native failure as retained non-label evidence that the official pytest run returned nonzero or otherwise failed to satisfy the four-test criterion; describe threshold, NaN/Inf, load, assertion, collection, and runtime failures as examples without treating them as exhaustive or overclaiming their cause.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.fail_if[3], checklist.yaml::native.fail_if[4], official/tests/test_outputs.py::simulate_model, official/tests/test_outputs.py::test_model_speed, official/tests/test.sh::18-29

### decision_rules_sfu: native_failure_can_fall_through_to_u
An established benchmark-counted failure such as a NaN/Inf assertion during test_model_speed is not clearly captured by F, creating a path to U despite decisive failure evidence.

Required correction: Make F exhaustive for any retained non-label evidence establishing a nonzero official pytest outcome, and reserve U solely for evidence that establishes neither zero nor nonzero completion.

Cited diagnostic locations: checklist.yaml::native.fail_if[3], checklist.yaml::native.fail_if[4], checklist.yaml::native.undecided_if[0], official/tests/test_outputs.py::simulate_model, official/tests/test.sh::18-29

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
