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
- case_unit_id: `rstan-to-pystan`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: rstan-to-pystan
domain: terminal_bench_2_1
task_id: terminal-bench/rstan-to-pystan
native:
  user_goal:
    text: Convert `/app/gp_rstan.R` into `/app/pystan_analysis.py` using PyStan 3.10.0, preserving the intended model and sampling setup, avoiding R/RStan and `cmdstanr`/`cmdstanpy`, using `stan.build` with `random_seed=1`, then run the script and save posterior-mean CSV outputs for `alpha`, `sigma`, `rho`, and `beta`.
    support:
    - official/instruction.md::1-25
  benchmark_success:
    text: 'Native success is pytest exit status 0 in the official verifier: all six tests in `test_outputs.py` pass, meaning R/RStan are unavailable, the four required CSVs exist, and their parsed contents satisfy the exact row-count and numeric-range checks.'
    support:
    - official/tests/test.sh::17-28
    - official/tests/test_outputs.py::test_r_rstan_not_installed
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
  checked_by:
    text: Task-specific verifier `official/tests/test.sh`, which runs `pytest` against `test_outputs.py` and treats pytest exit status 0 as success.
    support:
    - official/tests/test.sh::17-28
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Which of the six official pytest tests passed or failed, including the prohibited-R/RStan check and each required output-file/value check?
    support:
    - official/tests/test.sh::17-22
    - official/tests/test_outputs.py::test_r_rstan_not_installed
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
  - artifact: artifacts/**
    question: If retained, do `alpha_est.csv`, `sigma_est.csv`, `rho_est.csv`, and `beta_est.csv` exist with parseable numeric contents matching the verifier's 1/1/3/3 value expectations and exact accepted ranges?
    support:
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
  success_if:
  - text: 'Retained verifier evidence shows all six official tests passed: `test_r_rstan_not_installed`, `test_output_files_exist`, `test_alpha_estimation_accuracy`, `test_sigma_estimation_accuracy`, `test_rho_estimation_accuracy`, and `test_beta_estimation_accuracy`.'
    support:
    - official/tests/test.sh::17-28
    - official/tests/test_outputs.py::test_r_rstan_not_installed
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
  fail_if:
  - text: Retained verifier evidence shows `test_r_rstan_not_installed` failed because `R --version` or `R --slave -e "library(rstan)"` succeeded.
    support:
    - official/tests/test_outputs.py::test_r_rstan_not_installed
  - text: 'Retained verifier evidence shows any required output check failed: a required CSV is missing or empty, `alpha_est.csv` or `sigma_est.csv` is unparseable or outside `[1.08, 1.1]` or `[0.133, 0.136]`, `rho_est.csv` or `beta_est.csv` is unparseable or not exactly three numeric rows, or any rho/beta value lies outside the official accepted ranges.'
    support:
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
  undecided_if:
  - text: Retained evidence does not reveal the per-test verifier outcomes, and the remaining retained artifacts are insufficient to reconstruct every native check, especially the prohibited-R/RStan environment check.
    support:
    - official/tests/test_outputs.py::test_r_rstan_not_installed
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
    rationale: The native criterion includes both environment-state checks and file-content checks; output CSV contents alone cannot establish whether the prohibited-R/RStan test passed.
stronger:
  additional_conditions:
  - id: conversion-method-evidence
    text: Beyond native output-range scoring, retained run evidence should show that the agent actually produced `/app/pystan_analysis.py` as a PyStan 3.10.0 conversion of `gp_rstan.R`, using `stan.build(..., random_seed=1)` and not `cmdstanr`/`cmdstanpy`, rather than only emitting acceptable CSV outputs.
    rationale: The official instruction requires a PyStan 3.10.0 script conversion with a specific build seed and forbidden alternative sampler stacks, but the released verifier checks only R/RStan absence plus the existence and numeric ranges of the four output CSV files.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Is retained workspace or patch evidence available for `/app/pystan_analysis.py`, and does that code reflect a PyStan-based conversion with `stan.build(..., random_seed=1)` rather than `cmdstanr`/`cmdstanpy` or precomputed outputs?
      support:
      - official/instruction.md::9-18
    - artifact: agent/trajectory.json
      question: Do the retained command traces show installation or use of `pystan==3.10.0` rather than another sampler stack?
      support:
      - official/instruction.md::5-18
    support:
    - official/instruction.md::5-25
    - official/tests/test_outputs.py::test_r_rstan_not_installed
    - official/tests/test_outputs.py::test_output_files_exist
    - official/tests/test_outputs.py::test_alpha_estimation_accuracy
    - official/tests/test_outputs.py::test_sigma_estimation_accuracy
    - official/tests/test_outputs.py::test_rho_estimation_accuracy
    - official/tests/test_outputs.py::test_beta_estimation_accuracy
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-semantics-not-exact
The native prose strengthens several file-format and environment predicates and fails to cover every way the official pytest command can return nonzero.

Required correction: Define native success and failure by the exact uvx/pytest exit criterion; describe the R timeout behavior and the tests' actual first-token/first-column parsing, empty-row, extra-column, and count semantics without strengthening them.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if, official/tests/test.sh::17-28, official/tests/test_outputs.py::test_r_rstan_not_installed, official/tests/test_outputs.py::test_alpha_estimation_accuracy, official/tests/test_outputs.py::test_rho_estimation_accuracy

### decision_rules_sfu: failure-can-be-misclassified-unknown
A known timeout, collection error, internal pytest error, or verifier-command setup failure can currently match U even though it establishes benchmark-counted failure.

Required correction: Make F apply whenever retained non-label evidence establishes that the official uvx/pytest command returned nonzero, including test failures, timeouts, collection/internal errors, and setup failures; reserve U strictly for evidence that establishes neither exit outcome.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::17-28

### stronger_conditions: stronger-layer-incomplete
The stronger layer does not concretely measure all major source-supported requirements omitted by the native tests.

Required correction: Use concrete conditions for implementation fidelity, actual sampling execution/output derivation and exact formatting, and historical compliance with the R/RStan prohibitions; state each native measurement gap and name artifacts capable of assessing it.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::1-25, official/environment/task-deps/gp_rstan.R, official/tests/test_outputs.py

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.success_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: native.decisive_artifacts[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: stronger.additional_conditions[0].support[1] must use <relative_path>::<location> support pointers: official/environment/task-deps/gp_rstan.R`
- `guardrail: stronger.additional_conditions[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test_outputs.py`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[0].support[1] must use <relative_path>::<location> support pointers: official/environment/task-deps/gp_rstan.R`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.native.success_if[0].support[1] pointer 'official/tests/test_outputs.py': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/environment/task-deps/gp_rstan.R': missing :: separator
- $.stronger.additional_conditions[0].support[1] pointer 'official/environment/task-deps/gp_rstan.R': missing :: separator
- $.stronger.additional_conditions[0].support[2] pointer 'official/tests/test_outputs.py': missing :: separator`
