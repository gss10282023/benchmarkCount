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
- case_unit_id: `hf-model-inference`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: hf-model-inference
domain: terminal_bench_2_1
task_id: terminal-bench/hf-model-inference
native:
  user_goal:
    text: Set up a local background Flask sentiment-analysis service that uses the Hugging Face model `distilbert-base-uncased-finetuned-sst-2-english` saved at `/app/model_cache/sentiment_model`, serves `POST /sentiment` on `0.0.0.0:5000`, returns `sentiment` plus positive/negative confidence scores, and returns `400` JSON errors for invalid input.
    support:
    - official/instruction.md::1-28
  benchmark_success:
    text: 'Native success is established when retained verifier evidence shows the official `pytest /tests/test_outputs.py` run passed all four task-specific checks: model/tokenizer load from `/app/model_cache/sentiment_model`, API reachability on port 5000, correct `/sentiment` behavior and response schema on the fixed test texts, and `400` error handling with an `error` field for invalid input.'
    support:
    - official/tests/test.sh::3-12
    - official/tests/test_outputs.py::8-128
  checked_by:
    text: The task-specific official verifier runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` and treats a zero exit status as success.
    support:
    - official/tests/test.sh::3-12
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Do the recorded pytest outcomes show whether `test_model_downloaded`, `test_flask_api_running`, `test_sentiment_endpoint`, and `test_api_error_handling` all passed, or identify which official check failed or errored?
    support:
    - case_packet.md::86-98
    - official/tests/test.sh::6-12
    - official/tests/test_outputs.py::8-128
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is missing or incomplete, does pytest stdout confirm the same four official tests ran and whether any of them failed or errored?
    support:
    - case_packet.md::86-98
    - official/tests/test.sh::6-12
  success_if:
  - text: '`verifier/ctrf.json` or equivalent official pytest stdout shows all four official tests passed: the model path exists and loads, the service is reachable on port 5000, `/sentiment` returns the required JSON with expected labels and confidence ordering for the fixed texts, and invalid input returns `400` with an `error` field.'
    support:
    - official/tests/test.sh::6-12
    - official/tests/test_outputs.py::8-128
  fail_if:
  - text: '`verifier/ctrf.json` or equivalent official pytest stdout shows any official test failed or errored, including missing or unloadable model files, inability to connect to the service on port 5000, incorrect `/sentiment` response structure or classifications for the fixed texts, or missing `400`/`error` handling for invalid input.'
    support:
    - official/tests/test.sh::6-12
    - official/tests/test_outputs.py::8-128
  undecided_if:
  - text: The retained run artifacts do not provide readable official verifier outcomes, or provide only partial/ambiguous pytest evidence, so the pass/fail status of the four official checks cannot be established; agent-side code or trajectory evidence alone is insufficient for the native verdict.
    support:
    - case_packet.md::69-80
    - case_packet.md::86-98
    - official/tests/test.sh::6-12
stronger:
  additional_conditions:
  - id: background-and-bind-explicit
    text: Beyond native success, retained evidence should show the service was configured to bind `0.0.0.0:5000` and was launched to keep running in the background, because the official instruction requires both while the released verifier only operationalizes HTTP reachability and endpoint behavior.
    rationale: '`official/instruction.md` explicitly requires `0.0.0.0` and background execution. The released verifier succeeds based on the four pytest checks in `official/tests/test_outputs.py`; those checks send requests to `0.0.0.0:5000` and `localhost:5000` but do not inspect the launch mode or explicitly verify the bind configuration beyond observed reachability.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command trace show the service was started as a background process rather than only run interactively in the foreground?
      support:
      - case_packet.md::86-98
      - official/instruction.md::6-7
    - artifact: artifacts/**
      question: Do retained code artifacts or patches show the Flask app configured to listen on `0.0.0.0` and port `5000`?
      support:
      - case_packet.md::86-98
      - official/instruction.md::6-7
    support:
    - official/instruction.md::6-7
    - official/tests/test.sh::6-12
    - official/tests/test_outputs.py::46-52
    - official/tests/test_outputs.py::67-128
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_exit_semantics_incomplete
The native decision rules do not fully reproduce test.sh’s immediate-exit-status criterion: they cover per-test failures/errors but omit other nonzero pytest exits.

Required correction: Define native S as retained non-label evidence establishing pytest exit status 0 and native F as retained non-label evidence establishing any nonzero pytest exit, explicitly including collection, invocation, interruption, and session-level errors.

Cited diagnostic locations: checklist.yaml::native.checked_by, checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], official/tests/test.sh::6-12

### decision_rules_sfu: evidenced_nonzero_exit_can_fall_to_u
The U rule can absorb an evidenced verifier failure when pytest terminates nonzero before producing complete per-test outcomes.

Required correction: Reserve U for cases where retained artifacts cannot establish whether the official pytest command exited zero or nonzero; any retained stdout or stderr that establishes a nonzero exit condition must yield F.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::6-12

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
