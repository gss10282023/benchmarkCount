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

- benchmark: `terminal_bench_2_1`
- case_unit_id: `modernize-scientific-stack`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: modernize-scientific-stack
domain: terminal_bench_2_1
task_id: terminal-bench/modernize-scientific-stack
native:
  user_goal:
    text: Create `/app/analyze_climate_modern.py` as a modern Python climate-analysis script and create `/app/requirements.txt` or `/app/pyproject.toml`; the script should read the provided CSV with pandas using UTF-8, use `pathlib.Path`, process stations 101 and 102, and print each station's mean temperature in the required format.
    support:
    - official/instruction.md::3-26
  benchmark_success:
    text: 'Native success requires retained verifier evidence that the pytest run in `official/tests/test.sh` passed both official checks in `official/tests/test_outputs.py`: `test_modernized_code_runs` and `test_dependency_file_exists`.'
    support:
    - official/tests/test.sh::18-26
    - official/tests/test_outputs.py::11-50
  checked_by:
    text: Pytest executing `test_modernized_code_runs` and `test_dependency_file_exists` from `official/tests/test_outputs.py`, as invoked by `official/tests/test.sh`.
    support:
    - official/tests/test.sh::18-26
    - official/tests/test_outputs.py::11-50
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the recorded outcomes for `test_modernized_code_runs` and `test_dependency_file_exists` show both passed, or which official assertion failed?
    support:
    - official/tests/test.sh::18-26
    - official/tests/test_outputs.py::11-50
  - artifact: verifier/test-stdout.txt
    question: Does the pytest log corroborate whether both official tests passed, identify the failing assertion, or show that the verifier aborted before those test outcomes were established?
    support:
    - official/tests/test.sh::12-26
    - official/tests/test_outputs.py::11-50
  success_if:
  - text: 'Retained verifier evidence shows `test_modernized_code_runs` passed: `/app/analyze_climate_modern.py` existed, ran with exit code 0, stdout mentioned `Station 101`, `Station 102`, and `mean temperature`, and the parsed station means were within 0.1 of `-15.5` and `30.3`.'
    support:
    - official/tests/test_outputs.py::11-43
  - text: Retained verifier evidence shows `test_dependency_file_exists` passed because either `/app/requirements.txt` or `/app/pyproject.toml` existed.
    support:
    - official/tests/test_outputs.py::46-50
  fail_if:
  - text: Retained verifier evidence shows `test_modernized_code_runs` failed on any official assertion, including missing `/app/analyze_climate_modern.py`, nonzero script exit, missing required output text, or station means outside the allowed tolerances.
    support:
    - official/tests/test_outputs.py::13-43
  - text: Retained verifier evidence shows `test_dependency_file_exists` failed because neither `/app/requirements.txt` nor `/app/pyproject.toml` existed.
    support:
    - official/tests/test_outputs.py::46-50
  undecided_if:
  - text: Retained non-label evidence does not establish the outcomes of both official tests, for example because `verifier/ctrf.json` or the pytest log is missing/truncated, or the verifier aborted before pytest established pass/fail for `test_modernized_code_runs` and `test_dependency_file_exists`.
    support:
    - official/tests/test.sh::12-26
    - official/tests/test_outputs.py::11-50
stronger:
  additional_conditions:
  - id: instruction_only_file_content_requirements
    text: 'Beyond native pass, retained created-file evidence should show the instruction-only requirements that the released verifier does not check: `/app/analyze_climate_modern.py` uses `pathlib.Path` and reads the CSV with pandas using UTF-8 encoding, and the created dependency file lists `numpy`, `pandas`, and at least one of `matplotlib` or `scipy` with a `>=`, `==`, or `~=` version constraint.'
    rationale: '`official/instruction.md` requires these implementation and dependency details, but the released verifier checks only runtime/output properties of the script and the existence of some dependency file.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained created-file artifacts include `/app/analyze_climate_modern.py` and `/app/requirements.txt` or `/app/pyproject.toml`, and do those file contents satisfy the instruction-only pathlib/UTF-8 and dependency/version-constraint requirements?
      support:
      - official/instruction.md::15-26
      - official/tests/test_outputs.py::11-50
    - artifact: agent/trajectory.json
      question: If created files are not separately retained under `artifacts/**`, does the trajectory preserve the final file contents needed to review those instruction-only requirements?
      support:
      - official/instruction.md::15-26
      - official/tests/test_outputs.py::11-50
    support:
    - official/instruction.md::15-26
    - official/tests/test_outputs.py::11-50
```

## Prior independent review findings to repair

### native_user_goal: incomplete_official_user_goal
native.user_goal narrows the official instruction by omitting several mandatory requirements.

Required correction: State the preservation requirement, prohibition on Python 2 syntax/deprecated APIs, conditional configparser instruction, and exact dependency-content/version requirements in addition to the existing script behavior.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::7-26

### native_evaluator_semantics: incomplete_verifier_exit_semantics
The rules model assertion outcomes but not the verifier’s full pytest-command status criterion.

Required correction: Define success from retained evidence of a zero-status official pytest invocation and failure from retained evidence of a nonzero completed invocation, including test errors, timeouts, collection/setup errors, and invocation failures.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if, official/tests/test.sh::18-31

### decision_rules_sfu: overbroad_undecided_rule
undecided_if can move an evidenced nonzero official verifier invocation to U merely because individual test outcomes were not established.

Required correction: Reserve U for evidence that establishes neither zero nor nonzero completion and no decisive test outcome; classify a retained nonzero command outcome or recorded failed/error test as F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-31, case_packet.md::Native Evaluator Semantics

### stronger_conditions: missing_supported_stronger_gaps
The stronger layer does not cover all concrete official requirements omitted by the released tests.

Required correction: Add independently assessable conditions for exact output formatting, modern-syntax/API compliance, preservation of the original script, and creation/content of the dependency declaration, with the verifier’s precise noncoverage stated.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::7-26, official/tests/test_outputs.py::11-50

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: stronger.additional_conditions[3].support[1] must use <relative_path>::<location> support pointers: official/environment/climate_analyzer/analyze_climate.py`
- `guardrail: stronger.additional_conditions[3].decisive_artifacts[0].support[1] must use <relative_path>::<location> support pointers: official/environment/climate_analyzer/analyze_climate.py`
- `guardrail: stronger.additional_conditions[3].decisive_artifacts[1].support[1] must use <relative_path>::<location> support pointers: official/environment/climate_analyzer/analyze_climate.py`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[3].decisive_artifacts[0].support[1] pointer 'official/environment/climate_analyzer/analyze_climate.py': missing :: separator
- $.stronger.additional_conditions[3].decisive_artifacts[1].support[1] pointer 'official/environment/climate_analyzer/analyze_climate.py': missing :: separator
- $.stronger.additional_conditions[3].support[1] pointer 'official/environment/climate_analyzer/analyze_climate.py': missing :: separator`
