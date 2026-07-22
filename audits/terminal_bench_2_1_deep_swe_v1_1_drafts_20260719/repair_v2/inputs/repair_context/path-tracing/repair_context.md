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
- case_unit_id: `path-tracing`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: path-tracing
domain: terminal_bench_2_1
task_id: terminal-bench/path-tracing
native:
  user_goal:
    text: Write `image.c` so `gcc -static -o image image.c -lm && ./image` algorithmically produces `reconstructed.ppm` closely matching `/app/image.ppm` at 0.99 similarity, without reading `image.ppm`, while staying under the stated compressed-size limit and not relying on extra custom `.c`/`.h` includes.
    support:
    - official/instruction.md::1-6
  benchmark_success:
    text: 'Native success means the official verifier''s pytest run passes all five released checks: `/app/image.c` exists; `gcc -static -o /app/image /app/image.c -lm` succeeds and `len(zlib.compress(image.c_bytes)) < 2100`; `gcc -H /app/image.c -lm` succeeds with no `/app/` path in stdout or stderr; `chroot /jail /image` exits successfully and creates `/jail/reconstructed.ppm`; and the cosine similarity between `/app/image.ppm` and `/jail/reconstructed.ppm` is at least `0.99`.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_no_deps
    - official/tests/test_outputs.py::test_runs_and_produces_output
    - official/tests/test_outputs.py::test_image_similarity
  checked_by:
    text: The official verifier script runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::18-24
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record pass/fail outcomes for `test_image_c_exists`, `test_image_compiles`, `test_no_deps`, `test_runs_and_produces_output`, and `test_image_similarity`?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_no_deps
    - official/tests/test_outputs.py::test_runs_and_produces_output
    - official/tests/test_outputs.py::test_image_similarity
  - artifact: verifier/test-stdout.txt
    question: Does the retained pytest stdout corroborate the collected tests, any assertion details, and the overall pass/fail summary when the CTRF report is missing or ambiguous?
    support:
    - official/tests/test.sh::18-24
  success_if:
  - text: 'Retained verifier evidence establishes that all five official tests passed: `test_image_c_exists`, `test_image_compiles`, `test_no_deps`, `test_runs_and_produces_output`, and `test_image_similarity`.'
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_no_deps
    - official/tests/test_outputs.py::test_runs_and_produces_output
    - official/tests/test_outputs.py::test_image_similarity
  fail_if:
  - text: Retained verifier evidence shows `test_image_c_exists` failed because `/app/image.c` was absent.
    support:
    - official/tests/test_outputs.py::test_image_c_exists
  - text: Retained verifier evidence shows `test_image_compiles` or `test_no_deps` failed because compilation failed, `len(zlib.compress(image.c_bytes))` was not below `2100`, or the include check exposed an `/app/` dependency.
    support:
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_no_deps
  - text: Retained verifier evidence shows `test_runs_and_produces_output` failed because `chroot /jail /image` exited nonzero or `/jail/reconstructed.ppm` was not created.
    support:
    - official/tests/test_outputs.py::test_runs_and_produces_output
  - text: Retained verifier evidence shows `test_image_similarity` failed because the computed cosine similarity between `/app/image.ppm` and `/jail/reconstructed.ppm` was below `0.99`.
    support:
    - official/tests/test_outputs.py::test_image_similarity
  undecided_if:
  - text: The retained non-label artifacts do not establish either that all five official tests passed or that any specific official test failed.
    rationale: Native success or failure depends on retained verifier traces such as the CTRF report and pytest logs. If those traces are missing, truncated, or contradictory, the record cannot be resolved from stored evidence alone.
stronger:
  additional_conditions:
  - id: literal_gzip_threshold
    text: Beyond native success, retained source evidence should also show that the delivered `image.c` satisfies the instruction's literal `cat image.c | gzip | wc` size limit of less than `2000`; the released evaluator instead accepts `len(zlib.compress(image.c_bytes)) < 2100`.
    rationale: 'This is a concrete instruction/evaluator measurement gap: the task text specifies a gzip-plus-wc threshold below 2k, while `test_image_compiles` substitutes a zlib-compressed byte count with slack.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: If a retained copy of `image.c` is present, does the instruction's literal `cat image.c | gzip | wc` measurement stay below `2000`?
      support:
      - official/instruction.md::6-6
    support:
    - official/instruction.md::6-6
    - official/tests/test_outputs.py::test_image_compiles
```

## Prior independent review findings to repair

### native_evaluator_semantics: incomplete_native_failure_semantics
The native failure clauses cover specific assertion failures but omit other nonzero outcomes of the released pytest invocation, such as test errors and collection or invocation failures.

Required correction: Define native F whenever retained non-label verifier evidence establishes that the official pytest invocation returned nonzero, while retaining the listed assertion failures as examples rather than an exhaustive set.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-27

### decision_rules_sfu: benchmark_failures_can_fall_outside_f
A clearly evidenced pytest error or collection failure would be benchmark-counted as failure but does not satisfy any current fail_if clause.

Required correction: Broaden fail_if to all retained-evidence-established nonzero outcomes of the official pytest command, and reserve U for records where neither successful nor unsuccessful completion can be established.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-27

### source_support_pointers: unsupported_2000_pointer
The cited instruction says `<2k`; it does not support the checklist's exact `<2000` claim.

Required correction: Use the source's literal `<2k` formulation and refer to the gzip stream's byte count, without assigning an unsupported decimal or binary expansion.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, official/instruction.md::6-6

### stronger_conditions: invented_exact_stronger_threshold
The stronger condition correctly identifies a gzip/wc versus zlib/2100 gap but makes the unsupported stronger requirement more specific by changing `<2k` to `<2000`.

Required correction: State the stronger requirement as the instruction's `<2k` gzip-compressed-size bound and preserve the exact evaluator gap without inventing a numeric expansion.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::6-6, official/tests/test_outputs.py::test_image_compiles
