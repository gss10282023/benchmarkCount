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
- case_unit_id: `gpt2-codegolf`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: gpt2-codegolf
domain: terminal_bench_2_1
task_id: terminal-bench/gpt2-codegolf
native:
  user_goal:
    text: Write `/app/gpt2.c`, a dependency-free C program compilable with `gcc -O3 -lm` that reads `gpt2-124M.ckpt` and `vocab.bpe` and continues a supplied input with GPT-2 arg-max output for the next 20 tokens while staying under 5000 bytes.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is established when retained verifier evidence shows the single official pytest case `test_gpt2_implementation` passed: `/app/gpt2.c` exists, its size is under 5000 bytes, `gcc -O3 /app/gpt2.c -lm` succeeds, and `/app/a.out gpt2-124M.ckpt vocab.bpe "THIS SOFTWARE IS PROVIDED \"AS IS\", WITHOUT"` exits 0 with stdout containing `WARRANTY OF ANY KIND, EXPRESS OR IMPLIED`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
  checked_by:
    text: The task-specific verifier runs `pytest` on `official/tests/test_outputs.py`, with the decisive native check implemented by `test_gpt2_implementation`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the official pytest case `test_gpt2_implementation` pass or fail, and if it fails which official assertion is reported?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
  - artifact: verifier/test-stdout.txt
    question: Does retained pytest stdout confirm the same case outcome and expose the compile, execution, or substring-check failure details if the case failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
  - artifact: verifier/test-stderr.txt
    question: Does retained verifier stderr contain compile/runtime errors or traceback details needed to interpret the official test outcome?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
  success_if:
  - text: 'Retained verifier evidence establishes that `test_gpt2_implementation` passed, meaning all official checks held: `/app/gpt2.c` existed, was under 5000 bytes, compiled with `gcc -O3 -lm`, and the compiled program returned 0 and printed stdout containing `WARRANTY OF ANY KIND, EXPRESS OR IMPLIED` for the verifier prompt.'
    support:
    - official/tests/test_outputs.py::test_gpt2_implementation
  fail_if:
  - text: 'Retained verifier evidence establishes that `test_gpt2_implementation` failed on any official assertion: missing `/app/gpt2.c`, size at least 5000 bytes, compile failure, nonzero program exit, or stdout missing `WARRANTY OF ANY KIND, EXPRESS OR IMPLIED`.'
    support:
    - official/tests/test_outputs.py::test_gpt2_implementation
  undecided_if:
  - text: The retained verifier artifacts do not reliably establish whether `test_gpt2_implementation` passed or failed, or they are missing or contradictory in a way that prevents determining which official assertion outcome occurred.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_gpt2_implementation
stronger:
  additional_conditions:
  - id: instruction_requires_real_gpt2_continuation
    text: Beyond native scoring, retained source evidence should show the final `/app/gpt2.c` reads the provided checkpoint and BPE files and performs 20-step arg-max GPT-2 continuation, rather than merely producing output that satisfies the verifier's single substring check for one prompt.
    rationale: The official instruction requires a GPT-2 arg-max continuation program over the supplied `.ckpt` and `.bpe` for the next 20 tokens, but the released verifier operationalizes only file existence/size, compilation, zero exit, and one expected substring for one fixed prompt.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained artifacts include the final `/app/gpt2.c` or equivalent source showing that it reads the checkpoint and BPE files and implements multi-token arg-max continuation rather than a canned-response stub?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_gpt2_implementation
    - artifact: agent/trajectory.json
      question: If the final source is not separately retained, does the trajectory preserve the final `/app/gpt2.c` contents or equivalent evidence of that implementation?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_gpt2_implementation
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_gpt2_implementation
```

## Prior independent review findings to repair

### decisive_post_run_evidence: nondecisive_verifier_stderr
verifier/test-stderr.txt is named as decisive for compile/runtime errors or traceback details even though the child processes are run with capture_output and those details are incorporated into pytest assertion/reporting output; verifier stderr cannot independently be relied upon to establish the official test outcome or asserted failure reason.

Required correction: Remove verifier/test-stderr.txt from decisive_artifacts. Use verifier/ctrf.json and verifier/test-stdout.txt for the official pytest outcome and reported assertion details.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], official/tests/test_outputs.py::test_gpt2_implementation, official/tests/test.sh::18-22

### source_support_pointers: unsupported_stderr_pointer_claim
The cited test sources do not support the claim that verifier/test-stderr.txt exposes the captured subprocess or traceback details described by the checklist.

Required correction: Delete the unsupported stderr artifact claim and its pointers; retain the supported CTRF and pytest-stdout artifact entries.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2].question, checklist.yaml::native.decisive_artifacts[2].support, official/tests/test_outputs.py::test_gpt2_implementation
