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
- case_unit_id: `portfolio-optimization`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: portfolio-optimization
domain: terminal_bench_2_1
task_id: terminal-bench/portfolio-optimization
native:
  user_goal:
    text: Complete the provided C-extension skeleton and Python wrapper so portfolio risk and return match the Python baseline within 1e-10 tolerance, achieve at least 1.2x speedup on portfolios with 5000 or more assets, and handle portfolios up to 8000 assets.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is established when the official verifier''s pytest suite passes all six checks: `test_c_extension_exists`, `test_baseline_functionality`, `test_correctness_small`, and `test_performance_and_scalability` for `n=5000`, `6000`, and `8000`; those checks require a compiled `portfolio_optimized_c` module with both exported functions, correctness within 1e-10 for risk and return at the tested sizes, and `portfolio_risk_c` speedup of at least 1.2x at each large size.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::34-132
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`; the native verdict is the pass/fail status of that suite.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::34-132
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail status for all six official pytest cases, and if any failed, which named case failed (`test_c_extension_exists`, `test_baseline_functionality`, `test_correctness_small`, or `test_performance_and_scalability` at `n=5000`, `6000`, or `8000`)?
    support:
    - case_packet.md::62-73
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::34-132
  - artifact: verifier/test-stdout.txt
    question: Does the retained pytest console output corroborate the same per-test outcomes and, for failures, identify whether the failure was missing compiled extension/functions, correctness beyond 1e-10, or risk speedup below 1.2x at a tested large size?
    support:
    - case_packet.md::62-73
    - official/tests/test_outputs.py::34-132
  success_if:
  - text: 'Retained verifier evidence establishes that all six official pytest cases passed: the compiled `portfolio_optimized_c` extension imported successfully with `portfolio_risk_c` and `portfolio_return_c`; the protected baseline sanity check passed; correctness for both risk and return was within 1e-10 at `n=100`; and correctness for both risk and return plus `portfolio_risk_c` speedup of at least 1.2x passed at `n=5000`, `6000`, and `8000`.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::34-132
  fail_if:
  - text: Retained verifier evidence shows `test_c_extension_exists` failed, including import failure of `portfolio_optimized_c`, a non-compiled module file, or missing `portfolio_risk_c`/`portfolio_return_c`.
    support:
    - official/tests/test_outputs.py::34-65
  - text: Retained verifier evidence shows `test_baseline_functionality` or `test_correctness_small` failed, including protected-baseline sanity failure or risk/return mismatch exceeding 1e-10 at the small test size.
    support:
    - official/tests/test_outputs.py::68-102
  - text: Retained verifier evidence shows any `test_performance_and_scalability` case for `n=5000`, `6000`, or `8000` failed because risk or return mismatched the protected baseline by at least 1e-10, or because `portfolio_risk_c` achieved less than 1.2x speedup versus `portfolio_risk_python`.
    support:
    - official/tests/test_outputs.py::105-132
  undecided_if:
  - text: The retained non-label verifier artifacts are missing, malformed, or too incomplete to determine whether each official pytest case passed or failed, and the available stdout does not reliably reconstruct the full six-case outcome set.
    support:
    - case_packet.md::62-73
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::34-132
stronger:
  additional_conditions:
  - id: return_speedup_also_verified
    text: Beyond native scoring, retained evidence should also show `portfolio_return_c` achieves at least 1.2x speedup versus `portfolio_return_python` at the large portfolio sizes `5000`, `6000`, and `8000`, because the official task describes portfolio risk and return calculations meeting the speed target while the released evaluator times only risk.
    rationale: 'This is a concrete task/evaluator gap: official task intent covers both portfolio calculations, but the native verifier''s performance measurement uses only `portfolio_risk_python` and `portfolio_risk_c`.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command/output trace include large-portfolio timing measurements comparing `portfolio_return_c` with `portfolio_return_python`, and if so do those measurements show at least 1.2x speedup at `n=5000`, `6000`, and `8000`?
      support:
      - case_packet.md::62-68
      - official/task.toml::4-7
      - official/tests/test_outputs.py::123-129
    - artifact: agent/*-stdout.txt
      question: Do retained agent command logs report return-function timing results for `n=5000`, `6000`, and `8000` that corroborate at least 1.2x speedup over the Python baseline?
      support:
      - case_packet.md::62-68
      - official/task.toml::4-7
      - official/tests/test_outputs.py::123-129
    support:
    - official/task.toml::4-7
    - official/instruction.md::1-4
    - official/tests/test_outputs.py::123-129
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_exact_semantics_incomplete
Native rules do not fully encode the verifier’s exact assertions and failure status. In particular, `fail_if[1]` uses “exceeding 1e-10” even though equality fails, baseline sanity thresholds and the three-run minimum timing calculation are only summarized, and non-assertion nonzero pytest outcomes are omitted.

Required correction: State the exact strict comparisons, baseline sanity assertions, compiled-module checks, three-run minimum timing ratio, and that any established nonzero pytest invocation status—including collection or execution errors—is native failure.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], checklist.yaml::native.benchmark_success, official/tests/test_outputs.py::34-132, official/tests/test.sh::18-29

### decision_rules_sfu: failure_rule_omits_nonzero_errors
The current F rules do not classify retained evidence of collection, import, invocation, or execution errors as native failure, while `undecided_if` could incorrectly place such an established benchmark-counted failure in U.

Required correction: Add verifier stderr as potential decisive evidence and make F apply whenever retained non-label evidence establishes a nonzero official pytest command status; reserve U for cases where neither zero/all-pass nor nonzero status can be established.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory, official/tests/test.sh::18-29

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
