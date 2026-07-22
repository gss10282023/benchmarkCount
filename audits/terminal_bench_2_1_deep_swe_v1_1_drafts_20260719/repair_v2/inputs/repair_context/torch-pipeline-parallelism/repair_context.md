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
- case_unit_id: `torch-pipeline-parallelism`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: torch-pipeline-parallelism
domain: terminal_bench_2_1
task_id: terminal-bench/torch-pipeline-parallelism
native:
  user_goal:
    text: Implement `/app/pipeline_parallel.py` with `train_step_pipeline_afab(model, inputs, targets, device, dtype)` for LLaMA that roughly balances layers across ranks, runs all microbatch forwards before any backwards, uses distributed stage communication, computes scaled cross-entropy on the last rank, moves inputs/hidden states/gradients to the provided device and dtype, and does not use hooks in the implementation.
    support:
    - official/instruction.md::1-33
  benchmark_success:
    text: 'Native success is retained evidence that the pytest verifier in `official/tests/test.sh` passed every official check in `official/tests/test_outputs.py`: `/app/pipeline_parallel.py` exists, its source contains neither forbidden hook API string, and the parametrized pipeline test passes for `world_size` 1 and 2, including the embedded layer-count, AFAB-order, microbatch-count, and forward/backward tensor-equality assertions against the reference model.'
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_pipeline_parallel_exists
    - official/tests/test_outputs.py::test_no_hooks_in_pipeline_parallel
    - official/tests/test_outputs.py::test_pipeline_parallel
    - official/tests/test_outputs.py::_test_pipeline_parallel
  checked_by:
    text: Pytest execution of `official/tests/test_outputs.py` from `official/tests/test.sh`, with native pass/fail determined by whether that test run exits successfully.
    support:
    - official/tests/test.sh::18-30
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_pipeline_parallel_exists`, `test_no_hooks_in_pipeline_parallel`, and both `world_size` cases of `test_pipeline_parallel`?
    support:
    - case_packet.md::91-103
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_pipeline_parallel
  - artifact: verifier/test-stdout.txt
    question: Do the retained pytest logs corroborate an all-pass run or identify a specific official failure such as missing file, forbidden hook usage, too many layers on a rank, AFAB violation, microbatch-count mismatch, or tensor mismatch versus the reference model?
    support:
    - case_packet.md::91-103
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_pipeline_parallel_exists
    - official/tests/test_outputs.py::test_no_hooks_in_pipeline_parallel
    - official/tests/test_outputs.py::_test_pipeline_parallel
  success_if:
  - text: Retained verifier evidence shows that `test_pipeline_parallel_exists`, `test_no_hooks_in_pipeline_parallel`, and both parametrized `test_pipeline_parallel` cases passed in the pytest run defined by `official/tests/test.sh`.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_pipeline_parallel_exists
    - official/tests/test_outputs.py::test_no_hooks_in_pipeline_parallel
    - official/tests/test_outputs.py::test_pipeline_parallel
  fail_if:
  - text: Retained verifier evidence shows `test_pipeline_parallel_exists` failed, so `/app/pipeline_parallel.py` was not present where the verifier expected it.
    support:
    - official/tests/test_outputs.py::test_pipeline_parallel_exists
  - text: Retained verifier evidence shows `test_no_hooks_in_pipeline_parallel` failed because the implementation source contains `register_forward_hook` or `register_full_backward_hook`.
    support:
    - official/tests/test_outputs.py::test_no_hooks_in_pipeline_parallel
  - text: Retained verifier evidence shows either `test_pipeline_parallel` case failed for `world_size` 1 or 2, including failure of the rank layer-count bound, AFAB ordering check, microbatch-count match, or forward/backward tensor equality against the reference model.
    support:
    - official/tests/test_outputs.py::test_pipeline_parallel
    - official/tests/test_outputs.py::_test_pipeline_parallel
  undecided_if:
  - text: The retained non-label verifier artifacts do not preserve enough per-test outcome detail to establish either that all official pytest checks passed or that any specific official check failed.
    support:
    - case_packet.md::91-103
    - official/tests/test.sh::18-24
    - case_packet.md::79-85
stronger:
  additional_conditions:
  - id: device-dtype-handling
    text: Beyond native passing, retained code evidence should show that `train_step_pipeline_afab` explicitly moves inputs, inter-stage hidden states, and backward tensors to the provided `device` and `dtype`, because the instruction requires that behavior for all such tensors while the released tests exercise only `cpu` and `torch.float32`.
    rationale: 'This is a concrete instruction/evaluator gap: the official instruction requires device/dtype handling for inputs, hidden states, and gradients, but `_test_pipeline_parallel` fixes `device = torch.device("cpu")` and `dtype = torch.float32`, so an implementation can satisfy the native checks without demonstrating general compliance with those parameters.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained code artifacts for `/app/pipeline_parallel.py` show explicit conversion of inputs, stage activations, and backward tensors to the provided `device` and `dtype` at the points where they are created, received, or sent?
      support:
      - case_packet.md::91-103
      - official/instruction.md::24-28
      - official/tests/test_outputs.py::_test_pipeline_parallel
    support:
    - official/instruction.md::24-28
    - official/tests/test_outputs.py::_test_pipeline_parallel
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-exit-semantics
Native success and failure must reproduce the uvx/pytest command-status branch in test.sh, not only enumerate pass/fail outcomes for the four collected test cases.

Required correction: Make exit status zero the exact native-success rule and any evidenced nonzero command status the native-failure rule; retain named test outcomes as diagnostic detail.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, official/tests/test.sh::18-30

### decision_rules_sfu: incomplete-f-rule
The current F rules do not classify evidenced collection, launch, interruption, or internal pytest errors even though those nonzero command outcomes take the verifier’s failure branch.

Required correction: Add an evidence-based generic F rule covering every nonzero uvx/pytest command outcome, while leaving U only for evidence that establishes neither command success nor command failure.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-30

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
