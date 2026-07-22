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
- case_unit_id: `largest-eigenval`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: largest-eigenval
domain: terminal_bench_2_1
task_id: terminal-bench/largest-eigenval
native:
  user_goal:
    text: Implement `find_dominant_eigenvalue_and_eigenvector` in `/app/eigen.py` so the Python entrypoint returns the dominant eigenvalue by largest magnitude and its corresponding eigenvector for real `np.float64` square matrices up to 10x10, including nonsymmetric cases with possible complex outputs, and does so faster than the reference NumPy solution in `/app/eval.py` while still satisfying `np.allclose(A @ eigenvec, eigenval * eigenvec)`.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: 'Native success is that the official verifier''s pytest run passes every parametrized check in `official/tests/test_outputs.py`: for each matrix size 2 through 10, the returned pair passes `test_eigen_pair`, the returned eigenvalue passes `test_dominance_eigenvalue`, and median isolated runtime passes `test_speedup` with candidate median time strictly below reference median time.'
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::MAT_SIZES
    - official/tests/test_outputs.py::test_eigen_pair
    - official/tests/test_outputs.py::test_dominance_eigenvalue
    - official/tests/test_outputs.py::test_speedup
  checked_by:
    text: Official task-specific verifier `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` and treats a zero pytest exit as success.
    support:
    - official/tests/test.sh::9-17
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record pass/fail outcomes for every parametrized pytest case in `official/tests/test_outputs.py`, covering `test_eigen_pair`, `test_dominance_eigenvalue`, and `test_speedup` for each size 2 through 10?
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::MAT_SIZES
    - official/tests/test_outputs.py::test_eigen_pair
    - official/tests/test_outputs.py::test_dominance_eigenvalue
    - official/tests/test_outputs.py::test_speedup
  - artifact: verifier/test-stdout.txt
    question: Does stdout show the pytest run and the printed per-size candidate and reference median timings from `test_speedup`, consistent with the recorded case outcomes?
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::test_speedup
  - artifact: verifier/test-stderr.txt
    question: Does stderr show any collection/import/runtime error, timeout, or assertion trace that establishes verifier failure or explains missing outcome coverage?
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::test_eigen_pair
    - official/tests/test_outputs.py::test_dominance_eigenvalue
    - official/tests/test_outputs.py::test_speedup
  success_if:
  - text: '`verifier/ctrf.json` records passes for every required pytest case in `official/tests/test_outputs.py`, and retained verifier stdout/stderr show no contradictory collection or runtime failure; specifically, all sizes 2 through 10 pass `test_eigen_pair`, `test_dominance_eigenvalue`, and `test_speedup`.'
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::MAT_SIZES
    - official/tests/test_outputs.py::test_eigen_pair
    - official/tests/test_outputs.py::test_dominance_eigenvalue
    - official/tests/test_outputs.py::test_speedup
  fail_if:
  - text: '`verifier/ctrf.json` or verifier stdout/stderr establishes a pytest collection/import/runtime failure, or any failure of `test_eigen_pair` for a required size, including zero eigenvector, NaN or Inf eigenvalue, or failure of `np.allclose(A @ eigenvec, eigenval * eigenvec)`.'
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::test_eigen_pair
  - text: '`verifier/ctrf.json` or verifier stdout/stderr establishes any failure of `test_dominance_eigenvalue` for a required size because the returned eigenvalue magnitude is not `np.isclose` to the largest-magnitude reference eigenvalue.'
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::test_dominance_eigenvalue
  - text: '`verifier/ctrf.json` or verifier stdout/stderr establishes any failure of `test_speedup` for a required size because isolated median candidate runtime is not strictly less than isolated median reference runtime.'
    support:
    - official/tests/test.sh::11-17
    - official/tests/test_outputs.py::test_speedup
  undecided_if:
  - text: Retained non-label verifier artifacts do not provide a complete, trustworthy account of the required pytest outcomes, for example because `verifier/ctrf.json` is missing or incomplete and stdout/stderr do not independently establish whether every required case passed or which required case failed.
    rationale: The native decision is defined by the official pytest verifier outcomes, so without sufficient retained per-case outcome evidence, neither all-pass success nor any benchmark-counted failure is established from non-label artifacts alone.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### decision_rules_sfu: success_evidence_alternative_missing
success_if mandates verifier/ctrf.json although the checklist recognizes that complete pytest output can independently expose the required outcomes.

Required correction: Allow native success when a complete, trustworthy account across CTRF and/or retained pytest stdout/stderr establishes zero-exit completion and every required case passing; reserve U for evidence that establishes neither all-pass success nor a specific native failure.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.undecided_if[0], checklist.yaml::native.decisive_artifacts[1]

### stronger_conditions: missing_full_input_domain_condition
No stronger condition measures correctness and dominance beyond the verifier's single fixed-seed normal matrix per tested size, despite the broader official input-domain requirement.

Required correction: Add a stronger condition for correctness and largest-magnitude dominance across the instructed real-float64 square-matrix domain, explicitly identifying the fixed-sample coverage gap and an available retained artifact type capable of recording a final-state expanded-domain assessment.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::1-7, official/tests/test_outputs.py::test_eigen_pair, official/tests/test_outputs.py::test_dominance_eigenvalue

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
