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
- case_unit_id: `adaptive-rejection-sampler`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: adaptive-rejection-sampler
domain: terminal_bench_2_1
task_id: terminal-bench/adaptive-rejection-sampler
native:
  user_goal:
    text: Implement in R at `/app/ars.R` an adaptive rejection sampler `ars(density_function, domain, n = sample_count)` with input validation, log-concavity checks, modular helper functions, a formal `test()` function with clear PASS/FAIL plus mean/standard-deviation reporting, and at least one generated normal or exponential sample file.
    support:
    - official/instruction.md::1-26
  benchmark_success:
    text: 'Native success is established when retained verifier evidence shows the official pytest run for `/tests/test_outputs.py` completed with all nine task-specific checks passing: `ars` function exists, standard-distribution sampling passes, `test` function exists, formal test-output format passes, sample-file generation passes, modularity passes, error-handling passes, input-validation passes, and log-concavity handling passes.'
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_ars_function_exists
    - official/tests/test_outputs.py::test_can_generate_standard_distribution_samples
    - official/tests/test_outputs.py::test_has_test_function
    - official/tests/test_outputs.py::test_formal_testing_with_known_truth
    - official/tests/test_outputs.py::test_sample_files_generated
    - official/tests/test_outputs.py::test_implementation_is_modular
    - official/tests/test_outputs.py::test_implementation_handles_errors
    - official/tests/test_outputs.py::test_input_validation_functionality
    - official/tests/test_outputs.py::test_log_concavity_functionality
  checked_by:
    text: Checked by the official verifier's `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` run, using retained CTRF and verifier stdout/stderr artifacts to determine the pytest outcomes.
    support:
    - official/tests/test.sh::1-24
    - case_packet.md::61-82
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report record outcomes for all nine official pytest checks in `official/tests/test_outputs.py`, and if so are they all passing or is any one failing/erroring?
    support:
    - case_packet.md::71-82
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_ars_function_exists
    - official/tests/test_outputs.py::test_can_generate_standard_distribution_samples
    - official/tests/test_outputs.py::test_has_test_function
    - official/tests/test_outputs.py::test_formal_testing_with_known_truth
    - official/tests/test_outputs.py::test_sample_files_generated
    - official/tests/test_outputs.py::test_implementation_is_modular
    - official/tests/test_outputs.py::test_implementation_handles_errors
    - official/tests/test_outputs.py::test_input_validation_functionality
    - official/tests/test_outputs.py::test_log_concavity_functionality
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show pytest suite completion, a full-pass summary, or a named failure/error that determines the official test outcome when CTRF evidence is missing or needs corroboration?
    support:
    - case_packet.md::71-82
    - official/tests/test.sh::1-24
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr show collection, runtime, or environment errors from the official pytest run that determine failure or explain why the stored verifier evidence is incomplete?
    support:
    - case_packet.md::71-82
    - official/tests/test.sh::1-24
  success_if:
  - text: Retained verifier evidence shows the official pytest run completed with all nine named checks in `official/tests/test_outputs.py` passing.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_ars_function_exists
    - official/tests/test_outputs.py::test_can_generate_standard_distribution_samples
    - official/tests/test_outputs.py::test_has_test_function
    - official/tests/test_outputs.py::test_formal_testing_with_known_truth
    - official/tests/test_outputs.py::test_sample_files_generated
    - official/tests/test_outputs.py::test_implementation_is_modular
    - official/tests/test_outputs.py::test_implementation_handles_errors
    - official/tests/test_outputs.py::test_input_validation_functionality
    - official/tests/test_outputs.py::test_log_concavity_functionality
  fail_if:
  - text: Retained verifier evidence shows at least one of the nine official pytest checks failed or errored.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_ars_function_exists
    - official/tests/test_outputs.py::test_can_generate_standard_distribution_samples
    - official/tests/test_outputs.py::test_has_test_function
    - official/tests/test_outputs.py::test_formal_testing_with_known_truth
    - official/tests/test_outputs.py::test_sample_files_generated
    - official/tests/test_outputs.py::test_implementation_is_modular
    - official/tests/test_outputs.py::test_implementation_handles_errors
    - official/tests/test_outputs.py::test_input_validation_functionality
    - official/tests/test_outputs.py::test_log_concavity_functionality
  - text: Retained verifier stdout/stderr shows the official pytest run hit a collection, runtime, or verifier-environment error that made the run fail before the full suite could pass.
    support:
    - official/tests/test.sh::1-24
    - case_packet.md::71-82
  undecided_if:
  - text: The retained verifier artifacts do not establish complete outcomes for the nine official pytest checks and do not independently show a verifier-side failure condition; for example, `verifier/ctrf.json` is missing or incomplete and stdout/stderr are inconclusive.
    support:
    - case_packet.md::61-82
    - official/tests/test.sh::1-24
stronger:
  additional_conditions:
  - id: test-output-includes-std
    text: 'Beyond native pass, stronger success requires retained output from running `test()` to show named `TEST_NAME: PASS/FAIL` lines with both mean and standard deviation statistics; the official task requires both, but the native verifier only checks PASS/FAIL plus a mean mention.'
    rationale: '`official/instruction.md` explicitly requires mean and standard deviation statistics in the test output, while `test_formal_testing_with_known_truth` only asserts PASS/FAIL formatting and the presence of `mean`, leaving standard-deviation reporting unoperationalized by the native evaluator.'
    decisive_artifacts:
    - artifact: verifier/test-stdout.txt
      question: When the verifier ran the submitted `test()` function, did the captured output include named PASS/FAIL lines with both mean and standard deviation statistics?
      support:
      - case_packet.md::71-82
      - official/instruction.md::1-26
      - official/tests/test_outputs.py::test_formal_testing_with_known_truth
    support:
    - official/instruction.md::1-26
    - official/tests/test_outputs.py::test_formal_testing_with_known_truth
```

## Prior independent review findings to repair

### native_user_goal: incomplete-native-goal
native.user_goal narrows the official implementation and testing intent by omitting several explicit requirements.

Required correction: Replace it with a compact but faithful statement covering the accepted density interface, validation and error behavior, log-concavity detection, target-shaped sampling, modular consistent design, formal known-truth testing of the overall function and complicated modules, required reporting, and sample-file output.

Cited diagnostic locations: checklist.yaml::native.user_goal, official/instruction.md::1-26

### native_evaluator_semantics: exit-status-semantics-not-exact
The native rules substitute an all-nine-described-checks predicate for test.sh's exact immediate pytest exit-status predicate and overstate what weak source regexes operationalize.

Required correction: Define native success and failure by the task-specific pytest command returning zero or nonzero, respectively. Name test node IDs without treating their prose descriptions as additional semantic requirements.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, official/tests/test.sh::1-24, official/tests/test_outputs.py::test_ars_function_exists, official/tests/test_outputs.py::test_has_test_function

### decisive_post_run_evidence: stdout-does-not-expose-std-output
verifier/test-stdout.txt does not normally contain the captured output of test(), so it cannot independently establish the stronger standard-deviation condition.

Required correction: Replace verifier stdout with a retained raw trace, such as agent/trajectory.json, conditioned on that trace recording a direct test() invocation and its output.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0], official/tests/test_outputs.py::test_formal_testing_with_known_truth

### stronger_conditions: stronger-artifact-not-assessable
Although the standard-deviation requirement and measurement gap are valid, the condition lacks a retained artifact capable of assessing it in principle.

Required correction: Retain the condition but use agent/trajectory.json as decisive evidence when it records execution of the submitted test() function and the resulting output; otherwise assign stronger U for that future record.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::1-26, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.success_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.fail_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[2] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.fail_if[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
