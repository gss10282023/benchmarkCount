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
- case_unit_id: `train-fasttext`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: train-fasttext
domain: terminal_bench_2_1
task_id: terminal-bench/train-fasttext
native:
  user_goal:
    text: Train a FastText text-classification model on the Yelp data in `data/`, save it as `/app/model.bin`, and achieve at least 0.62 accuracy while keeping the model under 150MB.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: 'Native success requires both official verifier tests to pass: `test_accuracy` must parse `P@1` from `fasttext test /app/model.bin /tests/private_test.txt` and accept `P@1 >= 0.62`, and `test_model_size` must find `/app/model.bin` smaller than `150 * 1024 * 1024` bytes.'
    support:
    - official/tests/test.sh::24-28
    - official/tests/test_outputs.py::6-7
    - official/tests/test_outputs.py::10-41
  checked_by:
    text: The task-specific verifier runs `pytest` on `official/tests/test_outputs.py` and writes a CTRF report for those test results.
    support:
    - official/tests/test.sh::24-28
    - official/tests/test_outputs.py::10-41
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the official `test_accuracy` and `test_model_size` cases each pass or fail in the verifier run?
    support:
    - official/tests/test.sh::24-28
    - official/tests/test_outputs.py::10-41
  - artifact: verifier/test-stdout.txt
    question: If `test_accuracy` is not a clean pass, does retained verifier output show the parsed `P@1` value or that accuracy could not be parsed from `fasttext test` output?
    support:
    - official/tests/test_outputs.py::12-35
  - artifact: verifier/test-stderr.txt
    question: If a test failed or the outcome is unclear, does retained verifier stderr show model-load, execution, or parsing errors relevant to `test_accuracy` or `/app/model.bin` access?
    support:
    - official/tests/test_outputs.py::12-31
    - official/tests/test_outputs.py::38-41
  success_if:
  - text: Retained verifier evidence shows `test_accuracy` passed, meaning the verifier parsed `P@1` from `fasttext test /app/model.bin /tests/private_test.txt` and found `P@1 >= 0.62`.
    support:
    - official/tests/test_outputs.py::10-35
  - text: Retained verifier evidence shows `test_model_size` passed, meaning `/app/model.bin` existed and its size was less than `150 * 1024 * 1024` bytes.
    support:
    - official/tests/test_outputs.py::38-41
  fail_if:
  - text: Retained verifier evidence shows `test_accuracy` failed, including because the parsed `P@1` value was below `0.62` or because the verifier could not parse a `P@1` value from `fasttext test` output.
    support:
    - official/tests/test_outputs.py::12-35
  - text: Retained verifier evidence shows `test_model_size` failed, including because `/app/model.bin` was missing, unreadable, or at least `150 * 1024 * 1024` bytes.
    support:
    - official/tests/test_outputs.py::38-41
  undecided_if:
  - text: Retained non-label evidence does not establish whether both official tests passed or whether at least one official test failed.
    rationale: Use `U` when the retained verifier artifacts needed to determine the outcomes of `test_accuracy` and `test_model_size` are missing, incomplete, or contradictory, and no other retained artifact independently establishes those official checks.
stronger:
  additional_conditions:
  - id: trained_on_provided_yelp_data
    text: Retained agent evidence shows the submitted `/app/model.bin` was produced by training a FastText model on the Yelp data in `/app/data`, a requirement stated in the instruction but not operationalized by the native verifier's accuracy and size checks alone.
    rationale: '`official/instruction.md` requires training on the Yelp data in the data folder, while the released verifier only checks the final model''s private-test accuracy and file size.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do retained agent steps show FastText training commands that use files under `/app/data` and produce `/app/model.bin`?
      support:
      - official/instruction.md::1-5
    - artifact: agent/*-stdout.txt
      question: Do retained command logs corroborate conversion or training on the provided Yelp data rather than only supplying an already trained model?
      support:
      - official/instruction.md::1-5
    support:
    - official/instruction.md::1-5
    - official/tests/test.sh::24-28
    - official/tests/test_outputs.py::10-41
```

## Prior independent review findings to repair

### native_user_goal: goal_private_test_context_omitted
The stated user goal does not say that accuracy is evaluated on a private test set drawn from the same Yelp review distribution.

Required correction: Add the private-test and same-distribution context to `native.user_goal.text`.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-5

### native_evaluator_semantics: native_verifier_semantics_incomplete
The native rules misstate the pytest runtime path, omit nonzero command/collection/setup outcomes from native failure, and overstate `test_model_size` by treating generic unreadability as a failure condition not implemented by `os.path.getsize`.

Required correction: Use runtime path `/tests/test_outputs.py`; define native success/failure around the task-specific pytest invocation and its two tests; include retained evidence of nonzero execution, collection, setup, or internal errors as F; and describe the size failure as `os.path.getsize` failure or size at least the threshold.

Cited diagnostic locations: checklist.yaml::native.checked_by.text, checklist.yaml::native.fail_if, official/tests/test.sh::24-35, official/tests/test_outputs.py::38-41

### decision_rules_sfu: benchmark_counted_execution_failures_moved_to_u
The current U rule can absorb a verifier execution or collection failure even when retained non-label logs establish the nonzero outcome counted by the task-specific verifier.

Required correction: Add an F rule for retained evidence that the task-specific pytest command failed to execute or returned nonzero, and restrict U to cases where neither successful completion nor such failure is established.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::24-35

### source_support_pointers: missing_packet_local_support
The U rule has no support pointer, and the decisive artifact entries do not point to the inventory that establishes those artifact types.

Required correction: Cite `case_packet.md::Native Evaluator Semantics` for the U rule and `case_packet.md::Available Artifact Inventory` for each named artifact type.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], checklist.yaml::native.decisive_artifacts, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
