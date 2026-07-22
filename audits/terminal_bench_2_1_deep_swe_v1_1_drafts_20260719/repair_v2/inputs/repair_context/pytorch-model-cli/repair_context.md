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
- case_unit_id: `pytorch-model-cli`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: pytorch-model-cli
domain: terminal_bench_2_1
task_id: terminal-bench/pytorch-model-cli
native:
  user_goal:
    text: Provide /app/cli_tool, /app/weights.json, and /app/prediction.txt so ./cli_tool weights.json image.png runs MNIST inference and outputs only the predicted digit.
    support:
    - official/instruction.md::1-6
  benchmark_success:
    text: 'Native success is a full pass of the official pytest verifier: required /app files exist, prediction.txt.strip() is "2", /app/cli_tool /app/weights.json /app/image.png stdout.strip() is "2", and the first 50 generated MNIST image predictions match the fixed TRUE_PRED_CLASSES list.'
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-45
    - official/tests/test_outputs.py::48-144
  checked_by:
    text: Official pytest verifier invoked by official/tests/test.sh against official/tests/test_outputs.py.
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-144
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show all six official tests passed, including the file-existence checks, the prediction.txt content check, the /app/image.png CLI invocation check, and the 50-image MNIST prediction check?
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-45
    - official/tests/test_outputs.py::48-144
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is absent or incomplete, does the verifier log show pass/fail lines or mismatch output for those same official pytest checks?
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::138-144
  success_if:
  - text: 'Retained verifier evidence establishes that all six official pytest tests in official/tests/test_outputs.py passed: /app/weights.json, /app/cli_tool, and /app/prediction.txt exist; prediction.txt.strip() equals "2"; /app/cli_tool /app/weights.json /app/image.png stdout.strip() equals "2"; and the first 50 MNIST image predictions match TRUE_PRED_CLASSES.'
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-45
    - official/tests/test_outputs.py::48-144
  fail_if:
  - text: Retained verifier evidence establishes that any official pytest test in official/tests/test_outputs.py failed, including a missing required /app file, prediction.txt.strip() not equal to "2", /app/cli_tool /app/weights.json /app/image.png stdout.strip() not equal to "2", or any mismatch against the 50-image TRUE_PRED_CLASSES check.
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-45
    - official/tests/test_outputs.py::48-144
  undecided_if:
  - text: Retained non-label verifier artifacts are missing, truncated, or too incomplete to determine whether all six official pytest checks passed or whether any specific official pytest check failed.
    support:
    - official/tests/test.sh::17-27
    - official/tests/test_outputs.py::12-144
    rationale: The native claim is defined by the official pytest checks, so without retained evidence of those checks the record is not decidable.
stronger:
  additional_conditions:
  - id: binary-cli-tool
    text: Beyond native success, retained artifacts show that /app/cli_tool is an actual binary executable in /app, not merely any runnable file that satisfies the tests.
    rationale: The instruction requires a binary executable called cli_tool, while the native verifier only checks that /app/cli_tool exists and that invoking it yields the expected predictions.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained artifacts include the produced /app/cli_tool so a reviewer can verify it is a binary executable in /app rather than only a runnable script?
      support:
      - official/instruction.md::5-6
      - official/tests/test_outputs.py::18-21
      - official/tests/test_outputs.py::41-45
    support:
    - official/instruction.md::5-6
    - official/tests/test_outputs.py::18-21
    - official/tests/test_outputs.py::41-45
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_explicit_requirements
native.user_goal does not faithfully include several explicit deliverable requirements from the instruction.

Required correction: State that cli_tool is a binary executable, weights.json is used by cli_tool to load model weights, prediction.txt contains only the predicted digit, and all deliverables are in /app.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-6

### source_support_pointers: missing_sfu_source_pointer
The retained-evidence and undecidability rules lack support from the packet section that defines those rules.

Required correction: Add case_packet.md::Native Evaluator Semantics to the success_if, fail_if, and undecided_if support pointers.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0].support, case_packet.md::Native Evaluator Semantics

### stronger_conditions: incomplete_stronger_measurement
The stronger layer captures only the binary-format gap and omits other explicit requirements not operationalized by the verifier.

Required correction: Retain the binary condition and add compact conditions for C implementation, actual loading of weights.json, and exact no-extra-content formatting of prediction.txt and CLI stdout, with the verifier noncoverage and assessable retained artifacts stated.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/README.md::Overview, official/instruction.md::2-6, official/task.toml::task.description, official/tests/test_outputs.py::23-45, official/tests/test_outputs.py::48-144

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[3].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[3].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
