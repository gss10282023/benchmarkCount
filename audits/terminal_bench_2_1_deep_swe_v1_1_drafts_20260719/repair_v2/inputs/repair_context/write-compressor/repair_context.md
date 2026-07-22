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
- case_unit_id: `write-compressor`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: write-compressor
domain: terminal_bench_2_1
task_id: terminal-bench/write-compressor
native:
  user_goal:
    text: Produce `/app/data.comp` so `cat data.comp | /app/decomp` reproduces `/app/data.txt` exactly, with `data.comp` no larger than 2500 bytes.
    support:
    - official/instruction.md::1-2
  benchmark_success:
    text: 'Native success is established when the official verifier''s three pytest checks all pass: `/app/data.comp` exists; after setup restores the original fixtures and compiles `decomp2`, decompressing `data.comp` returns code 0 and stdout exactly equals `/app/data.txt`; and `data.comp` size is at most 2500 bytes.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::8-15
    - official/tests/test_outputs.py::18-22
    - official/tests/test_outputs.py::25-57
    - official/tests/test_outputs.py::60-73
  checked_by:
    text: Official verifier execution of `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::18-28
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for `test_compressed_file_exists`, `test_decompression_produces_original`, and `test_compression_size`?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::18-73
  - artifact: verifier/test-stdout.txt
    question: Does pytest console output corroborate that `/tests/test_outputs.py` ran and, if a check failed, which named test failed?
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::18-73
  success_if:
  - text: Retained verifier evidence establishes that `test_compressed_file_exists`, `test_decompression_produces_original`, and `test_compression_size` all passed.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::18-73
  fail_if:
  - text: Retained verifier evidence establishes that `test_compressed_file_exists` failed.
    support:
    - official/tests/test_outputs.py::18-22
  - text: Retained verifier evidence establishes that `test_decompression_produces_original` failed.
    support:
    - official/tests/test_outputs.py::25-57
  - text: Retained verifier evidence establishes that `test_compression_size` failed.
    support:
    - official/tests/test_outputs.py::60-73
  undecided_if:
  - text: Retained non-label verifier artifacts do not reliably establish outcomes for all three named pytest checks, and no retained artifact independently establishes any named check failure.
    support:
    - official/tests/test.sh::18-22
    rationale: Native success and failure are defined by the official pytest checks, so missing, partial, or internally inconsistent retained test evidence leaves the benchmark claim unresolved.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_failure_not_exact
Native failure is limited to failures of the three named tests, but test.sh produces the failure outcome for every nonzero pytest status.

Required correction: Define native success and failure by the pytest process exit status used by test.sh, while describing the three tests as the suite's substantive checks. Include collection, setup, startup, and execution errors in the nonzero failure rule.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.checked_by, checklist.yaml::native.fail_if, official/tests/test.sh::18-29

### decision_rules_sfu: sfu_misclassifies_nonzero_errors
An evidenced nonzero pytest outcome without a named failed test would satisfy neither current F nor current S and would incorrectly fall into U.

Required correction: Make F apply whenever retained non-label evidence establishes a nonzero pytest outcome, and reserve U for evidence that establishes neither zero nor nonzero outcome.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if, official/tests/test.sh::25-29, case_packet.md::Native Evaluator Semantics

### source_support_pointers: support_not_direct_for_inventory_and_u
The current support for the U rule and retained console artifact does not point to the packet sections that establish undecidable semantics and artifact availability.

Required correction: Add case_packet.md::Native Evaluator Semantics to the S/F/U rules and case_packet.md::Available Artifact Inventory to each decisive artifact; retain evaluator-source pointers for operational behavior.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0].support, checklist.yaml::native.decisive_artifacts[1].support, case_packet.md::Native Evaluator Semantics, case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
