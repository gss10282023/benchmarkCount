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
- case_unit_id: `path-tracing-reverse`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: path-tracing-reverse
domain: terminal_bench_2_1
task_id: terminal-bench/path-tracing-reverse
native:
  user_goal:
    text: Produce `/app/mystery.c`, a standalone C program whose compiled-and-run effect matches `/app/mystery`, stays under the stated compressed-size limit, does not invoke `./mystery`, and still works in isolation.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is a passing verifier run on `/tests/test_outputs.py`: `/app/mystery.c` exists, `gcc -static -o /app/reverse /app/mystery.c -lm` succeeds and `zlib.compress(...)` of the source is under `2100`, and the reconstructed output image reaches cosine similarity `>=0.995` against the original binary''s output.'
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_image_similarity
  checked_by:
    text: Checked by the task-specific shell verifier, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` and treats a zero exit from that pytest invocation as success.
    support:
    - official/tests/test.sh::18-30
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record pass/fail/error status for `test_image_c_exists`, `test_image_compiles`, and `test_image_similarity`?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_image_similarity
  - artifact: verifier/test-stdout.txt
    question: Does the retained pytest output corroborate the three official test outcomes and expose any assertion message for file-missing, compile/size, or similarity failure?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_image_similarity
  - artifact: verifier/test-stderr.txt
    question: If stdout or CTRF is incomplete, does stderr show verifier-command or runtime errors that still establish the pytest invocation did not complete successfully?
    support:
    - official/tests/test.sh::18-30
  success_if:
  - text: 'Retained verifier evidence establishes that all three official checks passed: `/app/mystery.c` existed, static compilation to `/app/reverse` succeeded with compressed source length under `2100`, and the reconstructed image met the `>=0.995` cosine-similarity threshold against the original output.'
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_image_similarity
  fail_if:
  - text: Retained verifier evidence shows `test_image_c_exists` failed or errored, establishing that the required `/app/mystery.c` file was not accepted by the verifier.
    support:
    - official/tests/test_outputs.py::test_image_c_exists
  - text: Retained verifier evidence shows `test_image_compiles` failed or errored, establishing that static compilation failed or the verifier's compressed-size check was `>=2100`.
    support:
    - official/tests/test_outputs.py::test_image_compiles
  - text: Retained verifier evidence shows `test_image_similarity` failed or errored, establishing that the reconstructed run did not satisfy the verifier's image-output check, including cosine similarity below `0.995` or failure to produce the compared output.
    support:
    - official/tests/test_outputs.py::test_image_similarity
  - text: Retained verifier logs show the verifier's pytest invocation itself did not exit successfully, even if per-test status is incomplete.
    support:
    - official/tests/test.sh::18-30
  undecided_if:
  - text: Retained non-label artifacts do not reliably establish whether the pytest invocation completed and whether each of the three official checks passed or failed; for example, `verifier/ctrf.json` is missing or ambiguous and the retained verifier logs do not resolve the outcome.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_image_c_exists
    - official/tests/test_outputs.py::test_image_compiles
    - official/tests/test_outputs.py::test_image_similarity
stronger:
  additional_conditions:
  - id: exact-output-identity
    text: Beyond native scoring, require retained evidence that the reconstructed program's output is exactly identical to the original program's output, not merely cosine-similar at `>=0.995`.
    rationale: The official instruction requires an identical operation, while the released verifier accepts approximate image similarity.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If retained, do the original and reconstructed output images match exactly rather than only meeting the cosine-similarity threshold?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_image_similarity
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_image_similarity
  - id: literal-gzip-under-2k
    text: Beyond native scoring, require retained evidence that `/app/mystery.c` satisfies the literal instruction-side size rule `cat mystery.c | gzip | wc` `< 2000`, not just the verifier's `zlib.compress(...) < 2100` check.
    rationale: The official instruction states a `<2k` gzip-based limit, but the released verifier operationalizes a looser zlib-based `<2100` threshold.
    decisive_artifacts:
    - artifact: artifacts/**
      question: If retained, does the submitted `/app/mystery.c` satisfy the literal gzip-and-wc size rule stated in the instruction?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_image_compiles
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_image_compiles
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_error_overgeneralization
The native failure rules treat every test_image_compiles error as proof of compilation/size failure and every unsuccessful pytest invocation as native task failure, although setup, command, rename, file-read, or other infrastructure errors may not establish those violations.

Required correction: Restrict F to retained evidence that establishes a candidate-facing official test violation. Put incomplete runs, setup failures, and unattributable errors in U.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], checklist.yaml::native.fail_if[3], official/tests/test_outputs.py::test_image_compiles, case_packet.md::Native Evaluator Semantics

### decision_rules_sfu: noncompletion_misclassified_as_failure
A nonzero or incomplete verifier invocation is assigned F without requiring evidence that a native criterion was violated.

Required correction: Require failure evidence tied to the existence, compilation/size, or reconstructed-output test; classify unresolved verifier noncompletion as U.

Cited diagnostic locations: checklist.yaml::native.fail_if[3], checklist.yaml::native.undecided_if[0], case_packet.md::Measurement Boundary

### source_support_pointers: unsupported_error_cause
The test_image_compiles source does not support the claim that any error establishes either compiler failure or compressed length at least 2100.

Required correction: Distinguish assertion evidence for compiler/size violations from other exceptions, and cite the same test source only for the narrower supported claim.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], official/tests/test_outputs.py::test_image_compiles

### stronger_conditions: unsupported_2k_conversion
The stronger size rule replaces the official textual `<2k` limit with `<2000`, a numeric interpretation not specified by the packet.

Required correction: State the stronger requirement using the instruction’s literal `<2k` gzip-based bound and identify the gap from the verifier’s zlib-compressed `<2100` check without inventing a decimal conversion.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[1].text, official/instruction.md::1-1, official/tests/test_outputs.py::test_image_compiles
