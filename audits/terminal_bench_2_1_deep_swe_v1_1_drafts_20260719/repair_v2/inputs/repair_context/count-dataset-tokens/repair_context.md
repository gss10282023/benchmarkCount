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
- case_unit_id: `count-dataset-tokens`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: count-dataset-tokens
domain: terminal_bench_2_1
task_id: terminal-bench/count-dataset-tokens
native:
  user_goal:
    text: Determine the total number of tokens in the science-domain rows of `ryanmarten/OpenThoughts-1k-sample` by tokenizing `deepseek_reasoning` and `deepseek_solution` with `Qwen2.5-1.5B-Instruct`, then write that integer to `/app/answer.txt`.
    support:
    - official/instruction.md::lines 1-4
    - official/README.md::lines 3-4
  benchmark_success:
    text: 'Native success is the single official pytest check passing: `/app/answer.txt` is readable and its contents include the string `79586`.'
    support:
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 6-13
  checked_by:
    text: '`official/tests/test.sh` runs `pytest /tests/test_outputs.py`; that lone test reads `/app/answer.txt` and asserts that `79586` appears in the file contents.'
    support:
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 6-13
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest record for `test_command_output_content_example` show pass, fail, or error?
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 6-13
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout confirm the pytest outcome or show that `/app/answer.txt` was missing, unreadable, or lacked `79586`?
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 9-12
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr show the same test failure/error details or the explicit workdir-guard failure from `test.sh`?
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test.sh::lines 12-15
    - official/tests/test_outputs.py::lines 9-12
  - artifact: artifacts/**
    question: If a retained copy of the produced `answer.txt` exists here, does its readable content contain `79586`?
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test_outputs.py::lines 8-12
  success_if:
  - text: A raw verifier report shows `test_command_output_content_example` passed; under the released check, that establishes that `/app/answer.txt` was readable and contained `79586`.
    support:
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 6-13
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
  - text: If a retained copy of the produced `answer.txt` is available, its readable content contains `79586`.
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test_outputs.py::lines 8-12
  fail_if:
  - text: A raw verifier report shows `test_command_output_content_example` failed because `/app/answer.txt` did not contain `79586`.
    support:
    - official/tests/test_outputs.py::lines 8-12
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
  - text: A raw verifier report shows `test_command_output_content_example` errored because `/app/answer.txt` was missing or unreadable.
    support:
    - official/tests/test_outputs.py::lines 9-12
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
  - text: Verifier logs show `official/tests/test.sh` triggered its explicit workdir guard and exited before running pytest.
    support:
    - official/tests/test.sh::lines 12-15
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
  - text: If a retained copy of the produced `answer.txt` is readable and does not contain `79586`, native failure is established.
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test_outputs.py::lines 8-12
  undecided_if:
  - text: No retained answer-file copy is available, and the retained verifier reports/logs do not reliably show whether the single official pytest check passed, failed, or errored.
    support:
    - case_packet.md::Available Artifact Inventory (types only; no per-record values)
    - official/tests/test.sh::lines 18-22
    - official/tests/test_outputs.py::lines 6-13
stronger:
  additional_conditions:
  - id: exact_answer_file
    text: Retained output evidence shows the produced answer file's full content is exactly the plain integer `79586` aside from an optional trailing newline, not merely a string that contains `79586`.
    rationale: The instruction and README require a plain integer answer with no extra text, while the released test only checks substring containment.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If a retained copy of the produced `answer.txt` exists, is its full content exactly `79586` aside from an optional trailing newline?
      support:
      - case_packet.md::Available Artifact Inventory (types only; no per-record values)
      - official/instruction.md::lines 4-4
      - official/README.md::lines 20-21
      - official/tests/test_outputs.py::lines 8-12
    support:
    - official/instruction.md::lines 4-4
    - official/README.md::lines 20-21
    - official/tests/test_outputs.py::lines 8-12
  - id: required_counting_method
    text: Retained execution evidence shows the reported count was computed by filtering the science-domain dataset rows and tokenizing both `deepseek_reasoning` and `deepseek_solution` with `Qwen2.5-1.5B-Instruct`.
    rationale: The official task requires this computation method, but the released evaluator only checks whether `/app/answer.txt` contains `79586`.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the executed commands or code show loading `ryanmarten/OpenThoughts-1k-sample`, filtering the science-domain rows, and tokenizing both required fields with `Qwen2.5-1.5B-Instruct`?
      support:
      - case_packet.md::Available Artifact Inventory (types only; no per-record values)
      - official/instruction.md::lines 1-3
      - official/README.md::lines 3-4
    - artifact: agent/*-stdout.txt
      question: Do retained logs corroborate the same dataset, filtering, tokenizer, and field-selection details?
      support:
      - case_packet.md::Available Artifact Inventory (types only; no per-record values)
      - official/instruction.md::lines 1-3
      - official/README.md::lines 3-4
    support:
    - official/instruction.md::lines 1-3
    - official/README.md::lines 3-4
    - official/tests/test_outputs.py::lines 8-12
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_semantics_state_shortcut_and_incomplete_failure
Native S/F rules substitute retained answer-file content for the official execution outcome and fail to cover other conclusively evidenced nonzero `uvx`/pytest outcomes handled by `test.sh`.

Required correction: Restrict native success to non-label execution evidence establishing a zero-status official pytest invocation or its single passing test. Define failure for the workdir guard and any conclusively evidenced nonzero or uncompleted official invocation, including but not limited to assertion and file-read errors. Do not use a retained answer-file copy alone as a native verdict.

Cited diagnostic locations: checklist.yaml::native.success_if[1], checklist.yaml::native.fail_if, official/tests/test.sh::lines 12-28

### decisive_post_run_evidence: invalid_native_decisive_artifacts
A retained answer-file copy establishes only its content, not the actual verifier result, and the workdir guard is printed to stdout rather than stderr.

Required correction: Remove `artifacts/**` as a native decisive verdict artifact, retain it only for the exact-format stronger condition, assign the guard question to verifier stdout, and limit stderr to conclusive errors it can actually expose.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], checklist.yaml::native.decisive_artifacts[3], official/tests/test.sh::lines 12-15

### decision_rules_sfu: sfu_misclassification
The current rules can assign S or F without verifier-execution evidence and can assign U to an evidenced benchmark-counted nonzero verifier outcome.

Required correction: Make S require conclusive non-label evidence of official verifier success, F require conclusive non-label evidence of the guard or a nonzero/uncompleted official invocation, and reserve U for evidence that establishes neither.

Cited diagnostic locations: checklist.yaml::native.success_if, checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::lines 17-28

### source_support_pointers: unsupported_pointer_inferences
The cited sources contradict the stderr guard claim and support only the test’s content predicate, not the inference that an independently retained file copy proves the executed verifier result.

Required correction: Rewrite the affected artifact questions and verdict rules so each cited source directly supports the stated evidentiary capability.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2].support, checklist.yaml::native.success_if[1].support, checklist.yaml::native.fail_if[3].support, official/tests/test.sh::lines 12-15, official/tests/test_outputs.py::lines 8-12
