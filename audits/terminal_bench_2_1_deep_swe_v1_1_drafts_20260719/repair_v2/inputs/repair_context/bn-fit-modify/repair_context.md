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
- case_unit_id: `bn-fit-modify`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: bn-fit-modify
domain: terminal_bench_2_1
task_id: terminal-bench/bn-fit-modify
native:
  user_goal:
    text: Recover the Bayesian-network DAG from `/app/bn_sample_10k.csv`, fit a BN on that DAG, intervene on `Y` at `0.0` (or with tiny variance around `0.0` if exact intervention is unavailable), save the learned and intervened DAG edge CSVs, and save a 10,000-row sample from the intervened BN.
    support:
    - official/instruction.md::1-19
    - official/README.md::1-16
  benchmark_success:
    text: The native benchmark succeeds iff the official verifier in `official/tests/test.sh` would have `pytest /tests/test_outputs.py` exit 0, meaning all nine official checks pass for the retained outputs.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::test_bn_sample_exists
    - official/tests/test_outputs.py::test_learned_dag_structure_exists
    - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_learned_dag_structure
    - official/tests/test_outputs.py::test_intervened_dag_structure_exists
    - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_intervened__data_structure
    - official/tests/test_outputs.py::test_sampled_csv_col_names
    - official/tests/test_outputs.py::test_sampled_data
  checked_by:
    text: 'Task-specific pytest verifier: `official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.'
    support:
    - official/tests/test.sh::1-24
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the retained per-test results show which of the nine official pytest checks in `official/tests/test_outputs.py` passed or failed?
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::1-143
  - artifact: artifacts/**
    question: Do retained copies of `/app/learned_dag.csv` show a non-empty CSV with `from` and `to` columns and the exact learned edge set `U->M, U->Y, U->D, U->R, Y->D, R->M`?
    support:
    - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_learned_dag_structure
  - artifact: artifacts/**
    question: Do retained copies of `/app/intervened_dag.csv` show a non-empty CSV with `from` and `to` columns and the exact intervened edge set `U->M, U->D, U->R, Y->D, R->M`?
    support:
    - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_intervened__data_structure
  - artifact: artifacts/**
    question: Do retained copies of `/app/final_bn_sample.csv` show a non-empty CSV with columns `U,R,Y,M,D`, exactly 10,000 rows and 5 columns, and enough data to recompute the evaluator's KS check on `D`?
    support:
    - official/tests/test_outputs.py::test_sampled_csv_col_names
    - official/tests/test_outputs.py::test_sampled_data
  success_if:
  - text: 'Retained evidence establishes the learned-DAG checks pass: `/app/learned_dag.csv` exists, is non-empty, has `from` and `to` columns, and its edge set is exactly `U->M, U->Y, U->D, U->R, Y->D, R->M`.'
    support:
    - official/tests/test_outputs.py::test_learned_dag_structure_exists
    - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_learned_dag_structure
  - text: 'Retained evidence establishes the intervened-DAG checks pass: `/app/intervened_dag.csv` exists, is non-empty, has `from` and `to` columns, and its edge set is exactly `U->M, U->D, U->R, Y->D, R->M`.'
    support:
    - official/tests/test_outputs.py::test_intervened_dag_structure_exists
    - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_intervened__data_structure
  - text: 'Retained evidence establishes the sample checks pass: `/app/final_bn_sample.csv` exists, is non-empty, has columns `U,R,Y,M,D`, has exactly 10,000 rows and 5 columns, and recomputing the evaluator''s KS test on `D` against its hard-coded normal reference yields `p >= 0.001`.'
    support:
    - official/tests/test_outputs.py::test_bn_sample_exists
    - official/tests/test_outputs.py::test_sampled_csv_col_names
    - official/tests/test_outputs.py::test_sampled_data
  fail_if:
  - text: 'Retained evidence establishes failure on the learned-DAG portion: `/app/learned_dag.csv` is missing, empty, lacks `from` or `to`, or its edge set differs from `U->M, U->Y, U->D, U->R, Y->D, R->M`.'
    support:
    - official/tests/test_outputs.py::test_learned_dag_structure_exists
    - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_learned_dag_structure
  - text: 'Retained evidence establishes failure on the intervened-DAG portion: `/app/intervened_dag.csv` is missing, empty, lacks `from` or `to`, or its edge set differs from `U->M, U->D, U->R, Y->D, R->M`.'
    support:
    - official/tests/test_outputs.py::test_intervened_dag_structure_exists
    - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_intervened__data_structure
  - text: 'Retained evidence establishes failure on the sampled-output portion: `/app/final_bn_sample.csv` is missing, empty, lacks any of `U,R,Y,M,D`, has row count other than 10,000 or column count other than 5, or yields KS `p < 0.001` for `D` against the evaluator''s hard-coded normal reference.'
    support:
    - official/tests/test_outputs.py::test_bn_sample_exists
    - official/tests/test_outputs.py::test_sampled_csv_col_names
    - official/tests/test_outputs.py::test_sampled_data
  - text: A retained official test report shows any pytest check in `official/tests/test_outputs.py` failed.
    support:
    - official/tests/test.sh::1-24
    - official/tests/test_outputs.py::1-143
  undecided_if:
  - text: No trustworthy retained test report resolves the case, and the retained output artifacts are insufficient to reconstruct one or more official checks, such as a missing DAG/sample CSV copy or insufficient sample data to recompute the KS test on `D`.
    support:
    - official/tests/test_outputs.py::1-143
stronger:
  additional_conditions:
  - id: instruction_header_order
    text: Retained DAG CSVs should also satisfy the agent-visible instruction's literal `to,from` header/order for both `/app/learned_dag.csv` and `/app/intervened_dag.csv`, because the instruction specifies that format while the native evaluator instead requires `from,to`.
    rationale: 'This is a concrete instruction/evaluator gap: `official/instruction.md` says to save DAG edges in `to,from` format, but `official/tests/test_outputs.py` only accepts `from` and `to` columns and interprets edges as `(from,to)`.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained copies of `/app/learned_dag.csv` and `/app/intervened_dag.csv` use the instruction's literal `to,from` header/order?
      support:
      - official/instruction.md::10-18
      - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
      - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
    support:
    - official/instruction.md::10-18
    - official/tests/test_outputs.py::test_learned_dag_structure_csv_col_names
    - official/tests/test_outputs.py::test_intervened_dag_structure_csv_col_names
  - id: explicit_y_intervention_observed
    text: Retained `final_bn_sample.csv` should also show that `Y` is fixed at `0.0`, or deviates only within a negligible neighborhood around `0.0` consistent with the instruction's allowed tiny-variance approximation, because the task explicitly requires intervening on `Y` while the native evaluator only inspects `D`.
    rationale: The instruction requires a causal intervention on `Y` at `0.0`, but the native evaluator never checks the sampled `Y` values and could accept outputs with the expected `D` distribution even if the retained sample does not reflect a `Y=0` intervention.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does retained `/app/final_bn_sample.csv` show `Y` fixed at `0.0`, or only negligible deviation from `0.0` consistent with the instruction's permitted tiny-variance approximation?
      support:
      - official/instruction.md::13-19
      - official/tests/test_outputs.py::test_sampled_csv_col_names
      - official/tests/test_outputs.py::test_sampled_data
    support:
    - official/instruction.md::13-19
    - official/tests/test_outputs.py::test_sampled_csv_col_names
    - official/tests/test_outputs.py::test_sampled_data
```

## Prior independent review findings to repair

### native_evaluator_semantics: incomplete_native_failure_semantics
The native fail_if rules omit pytest failures caused by CSV parsing/access errors, invalid data supplied to the KS computation, non-finite p-values, collection errors, or verifier invocation errors.

Required correction: Define native failure as retained non-label evidence that the official pytest invocation returned nonzero, failed or errored any check, or that retained state reconstructs any assertion/operation failure. Include unreadable CSVs and failure of the exact KS operation, not only p < 0.001.

Cited diagnostic locations: checklist.yaml::native.fail_if, case_packet.md::Packet Source Files / official/tests/test.sh, case_packet.md::Packet Source Files / official/tests/test_outputs.py

### decision_rules_sfu: failure_may_be_misclassified_undecided
Without a CTRF report, established evaluator errors outside the enumerated assertions can fall through to U even though they are ordinary native failures.

Required correction: Make F cover every independently established nonzero pytest outcome or reconstructed test failure/error; reserve U strictly for evidence that establishes neither success nor failure.

Cited diagnostic locations: checklist.yaml::native.fail_if[3], checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics

### source_support_pointers: test_sh_ranges_do_not_support_claims
The repeated pointer official/tests/test.sh::1-24 ends before the supplied pytest target and status branch.

Required correction: Replace the truncated ranges with concrete pointers to the pytest --ctrf invocation and its immediate status branch, or cite the complete test.sh source.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.support[0], checklist.yaml::native.checked_by.support[0], case_packet.md::Packet Source Files / official/tests/test.sh

### stronger_conditions: stronger_gaps_are_misstated_or_vague
The header-order rationale falsely says the evaluator requires from,to order, and the Y condition’s “negligible neighborhood” is not a concrete criterion.

Required correction: State that the evaluator checks column-name membership but not order. Define the Y requirement using the instruction’s exact Y=0.0 intervention or its explicitly allowed mean-zero, 10e-9-variance approximation. Retained trace or implementation artifacts may establish approximate-intervention provenance when the sample alone cannot.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], checklist.yaml::stronger.additional_conditions[1], case_packet.md::Packet Source Files / official/instruction.md, case_packet.md::Packet Source Files / official/tests/test_outputs.py

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md::full instruction': heading 'full instruction' not found
- $.native.benchmark_success.support[0] pointer 'official/tests/test.sh::pytest --ctrf invocation and immediate status branch': symbol 'pytest --ctrf invocation and immediate status branch' not found
- $.native.benchmark_success.support[1] pointer 'official/tests/test_outputs.py::all nine test functions': symbol 'all nine test functions' not found
- $.native.checked_by.support[0] pointer 'official/tests/test.sh::pytest --ctrf invocation': symbol 'pytest --ctrf invocation' not found
- $.native.decisive_artifacts[0].support[0] pointer 'official/tests/test.sh::pytest --ctrf invocation': symbol 'pytest --ctrf invocation' not found
- $.native.decisive_artifacts[0].support[1] pointer 'official/tests/test_outputs.py::all nine test functions': symbol 'all nine test functions' not found
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.decisive_artifacts[2].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and status branch': symbol 'pytest invocation and status branch' not found
- $.native.fail_if[0].support[1] pointer 'official/tests/test_outputs.py::all nine test functions': symbol 'all nine test functions' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::DAG output format': heading 'DAG output format' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::DAG output format': heading 'DAG output format' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::BN fitting, intervention, and sampling steps': heading 'BN fitting, intervention, and sampling steps' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[0] pointer 'official/instruction.md::BN fitting, intervention, and sampling steps': heading 'BN fitting, intervention, and sampling steps' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::BN fitting, intervention, and sampling steps': heading 'BN fitting, intervention, and sampling steps' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[0] pointer 'official/instruction.md::causal intervention step': heading 'causal intervention step' not found
- $.stronger.additional_conditions[2].decisive_artifacts[1].support[0] pointer 'official/instruction.md::causal intervention step': heading 'causal intervention step' not found
- $.stronger.additional_conditions[2].support[0] pointer 'official/instruction.md::causal intervention step': heading 'causal intervention step' not found`
