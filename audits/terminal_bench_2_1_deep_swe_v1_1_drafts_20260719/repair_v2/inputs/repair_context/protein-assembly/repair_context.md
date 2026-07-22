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
- case_unit_id: `protein-assembly`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: protein-assembly
domain: terminal_bench_2_1
task_id: terminal-bench/protein-assembly
native:
  user_goal:
    text: Design `/app/gblock.txt` as a single-line DNA gBlock encoding, in N-to-C order, an antibody binder, donor, DHFR from `plasmid.gb`, acceptor, and molecule binder, with no reused start/stop codons, no terminal GS linkers, 5-20 aa GS linkers between adjacent subproteins, donor/acceptor spectral matches to 505/610 nm, GC content 30-70% in every 50-nt window, and total length at most 3000 nt.
    support:
    - official/instruction.md::1-19
  benchmark_success:
    text: 'Retained non-label evidence establishes that the official verifier''s `test_gblock` check passed: `/app/gblock.txt` existed as one DNA-only line of length at most 3000 nt whose translation contained the exact FLAG, donor, DHFR, acceptor, and SNAP sequences in that order, with only 5-20 aa GS linkers between adjacent components, no extra translated residues before FLAG or after SNAP, and every 50-nt window within 30-70% GC.'
    support:
    - official/tests/test_outputs.py::test_gblock
    - official/tests/test.sh::1-19
  checked_by:
    text: Official task-specific pytest verifier `test_gblock`, invoked by `official/tests/test.sh`.
    support:
    - official/tests/test_outputs.py::test_gblock
    - official/tests/test.sh::1-19
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does retained CTRF output show whether the official `test_gblock` case passed, and if not, which assertion failed?
    support:
    - official/tests/test.sh::13-19
    - official/tests/test_outputs.py::test_gblock
  - artifact: verifier/test-stdout.txt
    question: If CTRF is missing or incomplete, does pytest stdout report the `test_gblock` outcome or assertion message?
    support:
    - official/tests/test.sh::13-19
    - official/tests/test_outputs.py::test_gblock
  - artifact: artifacts/**
    question: Is there a retained copy of `/app/gblock.txt` whose contents can be independently checked for one-line DNA format, translated FLAG-donor-DHFR-acceptor-SNAP structure, GS-only 5-20 aa linkers, terminal exactness, length, and 50-nt GC-window compliance?
    support:
    - case_packet.md::80-91
    - official/tests/test_outputs.py::test_gblock
  success_if:
  - text: Success is supported if retained verifier evidence shows that `test_gblock` passed under the official verifier.
    support:
    - official/tests/test_outputs.py::test_gblock
    - official/tests/test.sh::13-19
  - text: 'Equivalent direct retained evidence also supports success if a retained `gblock.txt` artifact independently establishes every condition encoded in `test_gblock`: one DNA-only line, length at most 3000 nt, exact FLAG-donor-DHFR-acceptor-SNAP translation with only 5-20 aa GS linkers between adjacent components, no extra translated residues before FLAG or after SNAP, and 30-70% GC in every 50-nt window.'
    support:
    - official/tests/test_outputs.py::test_gblock
  fail_if:
  - text: Failure is supported if retained evidence shows `/app/gblock.txt` is missing, has more than one line, contains non-ATCG characters, or exceeds 3000 nt.
    support:
    - official/tests/test_outputs.py::test_gblock
  - text: Failure is supported if retained evidence shows the translated sequence does not start with FLAG, does not contain the exact donor, DHFR, acceptor, and SNAP sequences in strict FLAG < donor < DHFR < acceptor < SNAP order, has a non-GS linker or a linker shorter than 5 aa or longer than 20 aa between adjacent components, or has extra translated residues after SNAP.
    support:
    - official/tests/test_outputs.py::test_gblock
  - text: Failure is supported if retained evidence shows any 50-nt window has GC count outside 15-35 inclusive.
    support:
    - official/tests/test_outputs.py::test_gblock
  undecided_if:
  - text: Undecided if retained non-label evidence does not establish whether `test_gblock` passed or failed, for example because verifier traces are absent or incomplete and no retained gBlock artifact is sufficient to reconstruct the tested conditions.
    support:
    - official/tests/test_outputs.py::test_gblock
    - case_packet.md::80-91
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_user_goal: incomplete_native_goal
native.user_goal does not faithfully capture the complete official intent and says "no reused start/stop codons" instead of requiring their omission because the plasmid's codons will be reused.

Required correction: Restate the complete official goal, including allowed-component provenance and sequences, antibody-target/common-variant constraints, component exclusivity, removal of N-terminal methionines, and omission of start/stop codons.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-32

### native_evaluator_semantics: inexact_verifier_semantics
The native rules describe stricter raw-file formatting than the verifier enforces and do not cover every nonzero pytest outcome counted by test.sh as failure.

Required correction: Describe validation of rstrip-normalized line content, preserve the verifier's acceptance of ignored partial-codon suffixes, and include retained evidence of any nonzero official pytest status as native failure.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.fail_if, official/tests/test_outputs.py::test_gblock, official/tests/test.sh::pytest invocation and exit-status branch

### stronger_conditions: missing_supported_stronger_gaps
The stronger layer is empty despite official requirements that the verifier does not fully measure.

Required correction: Add conditions for raw-file purity without trailing stripped characters and for complete-codon DNA with no ignored one- or two-nucleotide suffix.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::gBlock file and component-exclusivity requirements, official/tests/test_outputs.py::test_gblock

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.benchmark_success.support[1] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.checked_by.support[1] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.decisive_artifacts[0].support[0] pointer 'official/tests/test.sh::pytest invocation': symbol 'pytest invocation' not found
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.decisive_artifacts[2].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.decisive_artifacts[3].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.success_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.native.fail_if[0].support[0] pointer 'official/tests/test.sh::pytest invocation and exit-status branch': symbol 'pytest invocation and exit-status branch' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::gBlock file-format requirement': heading 'gBlock file-format requirement' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::gBlock file-format requirement': heading 'gBlock file-format requirement' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::component-exclusivity requirement': heading 'component-exclusivity requirement' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::component-exclusivity requirement': heading 'component-exclusivity requirement' not found`
