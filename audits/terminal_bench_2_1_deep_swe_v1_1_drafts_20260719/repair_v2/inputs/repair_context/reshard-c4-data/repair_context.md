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
- case_unit_id: `reshard-c4-data`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: reshard-c4-data
domain: terminal_bench_2_1
task_id: terminal-bench/reshard-c4-data
native:
  user_goal:
    text: Create `/app/compress.py` and `/app/decompress.py` so the first reshards an input directory into an output directory with at most 30 items per directory and 15MB per file, the second restores the original files in place exactly, and the solution is packaged in `/app` as a uv project with `pyproject.toml`, developed against `c4_sample/` but intended for similar slices.
    support:
    - official/instruction.md::1-15
  benchmark_success:
    text: 'Native success is that the task-specific verifier in `official/tests/test.sh` exits successfully because the single pytest case `test_compress_decompress_workflow` passes: on generated unseen C4 shard data, `uv run /app/compress.py` creates the output directory, every output file is at most 15MB, every directory has at most 30 total entries, and `uv run /app/decompress.py` restores exactly the original basenames and SHA256-tracked file contents.'
    support:
    - official/tests/test.sh::9-15
    - official/tests/test_outputs.py::85-184
  checked_by:
    text: '`official/tests/test.sh` running pytest against `official/tests/test_outputs.py` with CTRF reporting.'
    support:
    - official/tests/test.sh::9-15
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show whether `test_compress_decompress_workflow` passed, and if it failed, which official assertion failed?
    support:
    - official/tests/test.sh::9-15
    - official/tests/test_outputs.py::85-184
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show the `uv sync`, compress, and decompress steps and any printed timeout or assertion context for the official checks?
    support:
    - official/tests/test_outputs.py::94-99
    - official/tests/test_outputs.py::101-121
    - official/tests/test_outputs.py::139-184
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr contain subprocess or traceback output needed to confirm a non-zero return, timeout, or other official test failure?
    support:
    - official/tests/test_outputs.py::106-118
    - official/tests/test_outputs.py::149-161
  success_if:
  - text: 'Retained verifier evidence establishes that `test_compress_decompress_workflow` passed: `uv run /app/compress.py` returned 0 within 600 seconds, created the output directory, every produced file was at most 15MB, every directory had at most 30 items, and `uv run /app/decompress.py` returned 0 within 600 seconds and restored exactly the original basenames and SHA256-tracked contents.'
    support:
    - official/tests/test_outputs.py::101-137
    - official/tests/test_outputs.py::146-184
  fail_if:
  - text: Retained verifier evidence establishes failure if the official test shows `uv run /app/compress.py` or `uv run /app/decompress.py` timed out or returned a non-zero status.
    support:
    - official/tests/test_outputs.py::101-118
    - official/tests/test_outputs.py::146-161
  - text: Retained verifier evidence establishes failure if the official test shows the output directory was not created, any compressed file exceeded 15MB, any directory exceeded 30 total entries, the post-decompression basename set differed from the original, or any post-decompression file hash differed from the recorded original hash.
    support:
    - official/tests/test_outputs.py::120-137
    - official/tests/test_outputs.py::163-181
  undecided_if:
  - text: Retained non-label evidence does not reliably establish whether `test_compress_decompress_workflow` passed or which official assertion determined the outcome, such as when the CTRF report is missing or incomplete and verifier stdout/stderr do not independently show a decisive pass or failure condition.
    rationale: Native scoring is entirely determined by one pytest verifier case. If retained test-report and log artifacts do not let a reviewer determine that case's result or the decisive assertion, neither success nor failure is established from non-label evidence.
stronger:
  additional_conditions:
  - id: uv_project_requirement
    text: Beyond native success, retained artifacts establish that `/app` contains the required uv project metadata for the solution, `uv sync` succeeded in `/app`, and the run evidence does not show `uv run` installing additional dependencies.
    rationale: The instruction explicitly requires a uv venv in `/app` and a `pyproject.toml` such that dependencies are installable via `uv sync` and later `uv run` does not install anything extra. The native verifier invokes `uv sync` but only prints a failure message if it fails, then continues to score only the compress/decompress behavior, so native success can miss this workflow requirement.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained workspace artifacts include `/app/pyproject.toml` and the dependency metadata needed for the solution's uv project?
      support:
      - official/instruction.md::15-15
    - artifact: verifier/test-stdout.txt
      question: Does verifier stdout show that `uv sync` succeeded before script execution rather than merely logging a sync failure?
      support:
      - official/tests/test_outputs.py::94-99
    - artifact: verifier/test-stderr.txt
      question: Does verifier stderr avoid evidence that `uv run` installed extra dependencies during script execution?
      support:
      - official/instruction.md::15-15
      - official/tests/test_outputs.py::106-107
      - official/tests/test_outputs.py::149-150
    support:
    - official/instruction.md::15-15
    - official/tests/test_outputs.py::94-99
    - official/tests/test_outputs.py::106-107
    - official/tests/test_outputs.py::149-150
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_official_uv_and_creation_requirements
native.user_goal does not fully state the official intent concerning output-directory creation and the uv environment/dependency workflow.

Required correction: Add the requirement to create the output directory when absent and the requirements for a uv virtual environment in /app, pyproject.toml, successful dependency installation through uv sync, and no additional installation during later uv run commands.

Cited diagnostic locations: checklist.yaml::native.user_goal, official/instruction.md::1-15

### native_evaluator_semantics: inexact_test_sh_and_pytest_semantics
The native rules conflate pytest success with test.sh’s shell exit status, omit evaluator-counted pytest setup/fixture/collection failures, and do not precisely state the verifier’s normalized-text hash comparison.

Required correction: Define native success and failure by the exit status of the task-specific pytest invocation used to select reward 1 or 0; include all causes of pytest nonzero status; state the exact read().strip().encode() SHA256 comparison; and note that uv sync’s return code is not asserted.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if, official/tests/test.sh::9-19, official/tests/test_outputs.py::26-184

### decisive_post_run_evidence: unsupported_stderr_decisive_artifact
verifier/test-stderr.txt cannot independently expose the captured compress/decompress stderr claimed by the checklist, and its silence cannot prove that uv run installed no dependencies.

Required correction: Remove verifier/test-stderr.txt from these decisive roles. Use CTRF or complete pytest stdout for native status, and use an affirmative retained trace or state artifact for stronger uv claims.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/tests/test_outputs.py::106-118, official/tests/test_outputs.py::151-161

### decision_rules_sfu: native_failure_rule_is_incomplete
The current F rules do not classify conclusively evidenced collection, fixture, setup, or unexpected pytest errors as native failure.

Required correction: Make F apply whenever retained non-label evidence establishes that the official pytest invocation returned nonzero, including setup and infrastructure paths exercised inside that invocation; reserve U for genuinely inconclusive retained evidence.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if, official/tests/test.sh::9-19

### source_support_pointers: stderr_pointers_do_not_support_claims
The cited test lines contradict rather than support the stated verifier-stderr behavior.

Required correction: Delete the unsupported stderr claims and attach each replacement artifact question to evaluator lines that actually establish what that artifact can expose.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2].support, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2].support, official/tests/test_outputs.py::106-118, official/tests/test_outputs.py::151-161

### stronger_conditions: stronger_uv_measurement_needs_affirmative_evidence
The stronger condition omits the explicit uv-venv requirement and relies on missing stderr as proof of no additional installation.

Required correction: Separate the uv project-layout and dependency-workflow requirements, include the uv-managed environment in /app, state each native measurement gap, and require affirmative workspace or complete command-trace evidence; unavailable evidence should yield stronger U.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::15-15, official/tests/test_outputs.py::94-107, official/tests/test_outputs.py::146-161
