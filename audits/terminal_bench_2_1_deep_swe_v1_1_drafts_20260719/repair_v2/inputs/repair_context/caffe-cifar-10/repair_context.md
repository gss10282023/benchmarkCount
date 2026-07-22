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
- case_unit_id: `caffe-cifar-10`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: caffe-cifar-10
domain: terminal_bench_2_1
task_id: terminal-bench/caffe-cifar-10
native:
  user_goal:
    text: Install the original BVLC Caffe 1.0.0 in `/app/caffe`, build it for CPU-only execution, train CIFAR-10 for exactly 500 iterations using `examples/cifar10/cifar10_quick_solver.prototxt`, write `/app/caffe/training_output.txt`, and produce the expected model file with 100-iteration test accuracy above 45% and within 5 percentage points of train accuracy.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is a passing official verifier run under `official/tests/test.sh`: the pytest suite in `official/tests/test_outputs.py` passes `test_caffe_version_and_source`, `test_cifar10_model_exists`, `test_prototxt_files_exist`, `test_cpu_only_training_configured`, `test_training_completed_500_iterations`, and `test_model_accuracy_verification`.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::test_caffe_version_and_source
    - official/tests/test_outputs.py::test_cifar10_model_exists
    - official/tests/test_outputs.py::test_prototxt_files_exist
    - official/tests/test_outputs.py::test_cpu_only_training_configured
    - official/tests/test_outputs.py::test_training_completed_500_iterations
    - official/tests/test_outputs.py::test_model_accuracy_verification
  checked_by:
    text: The official verifier script `official/tests/test.sh`, which runs pytest with CTRF reporting against `/tests/test_outputs.py` and treats a zero-exit pytest run as success.
    support:
    - official/tests/test.sh::18-29
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show all six official verifier tests passing, or identify which official test failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_caffe_version_and_source
    - official/tests/test_outputs.py::test_cifar10_model_exists
    - official/tests/test_outputs.py::test_prototxt_files_exist
    - official/tests/test_outputs.py::test_cpu_only_training_configured
    - official/tests/test_outputs.py::test_training_completed_500_iterations
    - official/tests/test_outputs.py::test_model_accuracy_verification
  - artifact: verifier/test-stdout.txt
    question: Do verifier stdout logs show the official script reached and completed the pytest run, or aborted earlier such as at the explicit working-directory check?
    support:
    - official/tests/test.sh::12-29
  - artifact: verifier/test-stderr.txt
    question: Do verifier stderr logs show pytest or subprocess errors that establish native failure when the CTRF report is missing or incomplete?
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::test_caffe_version_and_source
    - official/tests/test_outputs.py::test_model_accuracy_verification
  success_if:
  - text: 'Retained verifier evidence establishes a completed official pytest run in which all six official tests passed: Caffe reports version 1.0.0; `examples/cifar10/cifar10_quick_iter_500.caffemodel` exists and is nontrivially sized; the required prototxt files exist; the solver and build metadata show CPU-only mode with `max_iter: 500`; `training_output.txt` shows iteration 500 but not 501 with realistic training logs; and the 100-iteration test accuracy is above 0.45 and at most 0.05 below the final training accuracy parsed from `training_output.txt`.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::test_caffe_version_and_source
    - official/tests/test_outputs.py::test_cifar10_model_exists
    - official/tests/test_outputs.py::test_prototxt_files_exist
    - official/tests/test_outputs.py::test_cpu_only_training_configured
    - official/tests/test_outputs.py::test_training_completed_500_iterations
    - official/tests/test_outputs.py::test_model_accuracy_verification
  fail_if:
  - text: Retained verifier evidence shows the official script aborted before a passing pytest run, including the explicit failure when no working directory is set before running the tests.
    support:
    - official/tests/test.sh::12-29
  - text: Retained verifier evidence shows any official pytest check failed, including failure of the version check, model-file check, required prototxt check, CPU-only configuration check, exact-500-iteration training-output check, or accuracy-threshold check.
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::test_caffe_version_and_source
    - official/tests/test_outputs.py::test_cifar10_model_exists
    - official/tests/test_outputs.py::test_prototxt_files_exist
    - official/tests/test_outputs.py::test_cpu_only_training_configured
    - official/tests/test_outputs.py::test_training_completed_500_iterations
    - official/tests/test_outputs.py::test_model_accuracy_verification
  undecided_if:
  - text: Retained verifier artifacts are missing, truncated, or inconsistent such that they do not establish either a completed all-pass official pytest run or a specific official verifier failure.
    rationale: The native criterion is exactly the official verifier run in `official/tests/test.sh` over the pytest suite in `official/tests/test_outputs.py`. If the retained CTRF report and verifier stdout/stderr do not let a reviewer reconstruct whether that run passed or failed, the benchmark claim cannot be decided from stored non-label evidence.
stronger:
  additional_conditions:
  - id: bvlc-source-provenance
    text: Beyond native scoring, retained agent evidence should establish that `/app/caffe` was obtained from the original BVLC Caffe source repository, because the instruction requires the original BVLC Caffe but the released verifier only operationalizes a binary that reports version `1.0.0` plus the expected files and metrics.
    rationale: '`official/instruction.md` requires installing the original BVLC Caffe and cloning Caffe to `/app/caffe`. The released verifier''s `test_caffe_version_and_source` function checks only that the discovered binary runs and its output contains `1.0.0`; it does not inspect repository origin, remote, or source-tree identity. This is a concrete, source-supported task/evaluator gap.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show `/app/caffe` being cloned from the BVLC Caffe repository or otherwise establish BVLC source provenance for the installed tree?
      support:
      - official/instruction.md::1-9
      - official/tests/test_outputs.py::test_caffe_version_and_source
    - artifact: agent/*-stdout.txt
      question: Do retained command outputs show the clone URL, git remote, or equivalent evidence that `/app/caffe` came from the BVLC Caffe source repository?
      support:
      - official/instruction.md::1-9
      - official/tests/test_outputs.py::test_caffe_version_and_source
    support:
    - official/instruction.md::1-9
    - official/tests/test_outputs.py::test_caffe_version_and_source
```

## Prior independent review findings to repair

### native_user_goal: goal_directionality_and_clone
The user goal drops the explicit clone instruction and renders a one-sided accuracy constraint as potentially symmetric.

Required correction: State that original BVLC Caffe is to be cloned to `/app/caffe` and that test accuracy must be greater than 45% and no more than 0.05 lower than training accuracy.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-9

### native_evaluator_semantics: literal_verifier_semantics
The native success prose silently strengthens and abstracts the released tests, especially by treating weak literal log checks as proof of genuine exact-500 training.

Required correction: Reproduce the pytest exit criterion and the exact predicates, paths, thresholds, substring checks, build-path precedence, regex selection, command arguments, and stderr-only test-accuracy parsing used by the released verifier.

Cited diagnostic locations: checklist.yaml::native.success_if[0], official/tests/test.sh::18-29, official/tests/test_outputs.py::test_cifar10_model_exists, official/tests/test_outputs.py::test_cpu_only_training_configured, official/tests/test_outputs.py::test_training_completed_500_iterations, official/tests/test_outputs.py::test_model_accuracy_verification

### decision_rules_sfu: complete_sfu_partition
S overclaims facts beyond the native predicates, while F does not unambiguously include all evidenced nonzero pytest outcomes such as collection or execution errors.

Required correction: Define S as evidence of the official pytest invocation returning zero with the released suite satisfied; define F to include the working-directory exit, any nonzero pytest outcome, any failed test, and collection/execution errors; reserve U solely for insufficient or inconsistent evidence.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0], official/tests/test.sh::12-29
