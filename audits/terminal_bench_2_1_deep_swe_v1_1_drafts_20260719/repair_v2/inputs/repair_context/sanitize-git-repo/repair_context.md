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
- case_unit_id: `sanitize-git-repo`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: sanitize-git-repo
domain: terminal_bench_2_1
task_id: terminal-bench/sanitize-git-repo
native:
  user_goal:
    text: Sanitize repository `dclm` by finding AWS access key IDs, AWS secret access keys, GitHub tokens, and Huggingface tokens, replacing each with the specified placeholder form, leaving placeholders consistent across the repository, and not modifying files that are not contaminated.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: 'Native success is the official verifier passing all three pytest checks in `official/tests/test_outputs.py`: the three contaminated files omit the five explicit fake secret strings under case-insensitive search, those files exactly match the official decontaminated fixture files, and the final repo diff from commit `d6987af002b122fef54bc0be402062c76488a4d9` contains no path outside the contaminated-file list.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::14-71
  checked_by:
    text: The official verifier in `official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`, so native review is checked from the retained pytest/CTRF outputs for those tests.
    support:
    - official/tests/test.sh::18-23
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_removal_of_secret_information`, `test_correct_replacement_of_secret_information`, and `test_no_other_files_changed`?
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::22-71
  - artifact: verifier/test-stdout.txt
    question: Does retained pytest stdout corroborate which of the three official tests passed or failed, including any assertion or `ValueError` that identifies a native failure condition?
    support:
    - official/tests/test.sh::18-23
    - official/tests/test_outputs.py::22-71
  success_if:
  - text: Retained verifier evidence shows the three contaminated files do not contain any of the five explicit fake secret strings under the case-insensitive checks in `test_removal_of_secret_information`.
    support:
    - official/tests/test_outputs.py::14-31
  - text: Retained verifier evidence shows `/app/dclm/ray_processing/ray_cluster.yaml`, `/app/dclm/ray_processing/process.py`, and `/app/dclm/exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json` exactly equal the official decontaminated fixture files used by `test_correct_replacement_of_secret_information`.
    support:
    - official/tests/test_outputs.py::34-57
  - text: Retained verifier evidence shows the diff from commit `d6987af002b122fef54bc0be402062c76488a4d9` to the final working tree contains no path outside the contaminated-file list, satisfying `test_no_other_files_changed`.
    support:
    - official/tests/test_outputs.py::14-19
    - official/tests/test_outputs.py::60-71
  fail_if:
  - text: Retained verifier evidence shows any contaminated file still contains one of the five explicit fake secret strings under the case-insensitive checks in `test_removal_of_secret_information`.
    support:
    - official/tests/test_outputs.py::22-31
  - text: Retained verifier evidence shows any contaminated file differs from its official decontaminated fixture, so `test_correct_replacement_of_secret_information` fails.
    support:
    - official/tests/test_outputs.py::34-57
  - text: Retained verifier evidence shows the final diff from commit `d6987af002b122fef54bc0be402062c76488a4d9` includes a path outside the contaminated-file list, so `test_no_other_files_changed` fails.
    support:
    - official/tests/test_outputs.py::14-19
    - official/tests/test_outputs.py::60-71
  undecided_if:
  - text: Retained non-label verifier evidence is missing or too incomplete to determine whether all three official pytest checks passed or whether any of the native failure conditions above occurred.
    rationale: Native success is defined only by the official pytest verifier, so without readable retained pytest/CTRF outcomes the review cannot independently establish success or failure.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_repository_wide_scope
native.user_goal recasts the request as removal of only four named credential types, although the official instruction asks for all API keys and sensitive values and presents those types as examples.

Required correction: State the repository-wide removal requirement while retaining the specified examples, placeholders, consistency requirement, and protection of uncontaminated files.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-13

### native_evaluator_semantics: fail_rules_omit_non_assertion_pytest_failure
The verifier writes failure whenever the uvx/pytest command returns nonzero, but fail_if only enumerates three content-level assertion violations.

Required correction: Add a native failure rule covering retained non-label evidence that the official uvx/pytest invocation returned nonzero, including test errors and invocation failures.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-29

### decision_rules_sfu: known_verifier_failure_can_become_u
Under the current rules, complete retained evidence of a pytest error or invocation failure may establish neither listed content violation and therefore be routed to U despite being benchmark-counted failure.

Required correction: Make F apply whenever retained non-label verifier evidence establishes a nonzero official pytest invocation; reserve U for evidence that cannot establish successful zero exit or nonzero failure.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29
