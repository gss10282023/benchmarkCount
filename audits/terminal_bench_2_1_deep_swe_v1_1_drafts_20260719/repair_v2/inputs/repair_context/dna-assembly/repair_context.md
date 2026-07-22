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
- case_unit_id: `dna-assembly`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: dna-assembly
domain: terminal_bench_2_1
task_id: terminal-bench/dna-assembly
native:
  user_goal:
    text: Design the minimum necessary primer set in `primers.fasta` for PCR-amplifying `input`, `egfp`, `flag`, and `snap` so they can be assembled in one pot with NEBridge Golden Gate assembly using BsaI-HF v2 into the desired `output` plasmid, while meeting the stated annealing-length, Tm, header-format, and no-blank-line constraints.
    support:
    - official/instruction.md::1-15
  benchmark_success:
    text: 'Native success means retained non-label evidence establishes that the official verifier run in `official/tests/test.sh` would pass `official/tests/test_outputs.py::test_primers`: `primers.fasta` exists; it has exactly 16 lines encoding the eight required primers; each primer sequence is A/T/C/G only and parses under the verifier''s BsaI layout; each fragment satisfies the annealing-length and oligotm Tm checks; the four junction overhang relationships and uniqueness checks hold; and the assembled sequence is contained in the official circular `output` sequence.'
    support:
    - official/tests/test.sh::1-22
    - official/tests/test_outputs.py::test_primers
    - official/tests/test_outputs.py::parse_bsai_primer
    - official/tests/test_outputs.py::make_fragment
    - official/tests/test_outputs.py::calc_tm
  checked_by:
    text: Official verifier script `official/tests/test.sh`, which installs `primer3` and runs `pytest` over `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::1-22
  decisive_artifacts:
  - artifact: artifacts/**
    question: Does the retained artifact set include `primers.fasta`, and does that file contain enough sequence content to evaluate the official assertions on file presence, required headers, BsaI-site parsing, annealing/Tm limits, overhang compatibility, and final assembly?
    support:
    - official/tests/test_outputs.py::test_primers
    - official/tests/test_outputs.py::parse_bsai_primer
    - official/tests/test_outputs.py::make_fragment
    - official/tests/test_outputs.py::calc_tm
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show whether `test_primers` passed, or identify the decisive official assertion that failed?
    support:
    - official/tests/test.sh::1-22
    - official/tests/test_outputs.py::test_primers
  success_if:
  - text: 'Retained non-label evidence establishes that `official/tests/test_outputs.py::test_primers` passes: either the retained pytest report records that pass, or the retained `primers.fasta` independently satisfies all explicit assertions in `test_primers`, `parse_bsai_primer`, `make_fragment`, and `calc_tm`.'
    support:
    - official/tests/test.sh::1-22
    - official/tests/test_outputs.py::test_primers
    - official/tests/test_outputs.py::parse_bsai_primer
    - official/tests/test_outputs.py::make_fragment
    - official/tests/test_outputs.py::calc_tm
  fail_if:
  - text: 'Retained evidence establishes any early verifier failure: `primers.fasta` is missing, does not have exactly 16 lines, any primer header is missing from the required set `{input,egfp,flag,snap}_{fwd,rev}`, or any primer sequence contains characters outside `A/T/C/G`.'
    support:
    - official/tests/test_outputs.py::test_primers
  - text: 'Retained evidence establishes any downstream official assertion failure in primer structure or assembly: a primer lacks a valid `ggtctc` BsaI site with the verifier''s required clamp/padding layout, a forward or reverse primer does not anneal in the required order, a full annealing tract is outside 15-45 nt, oligotm Tm is outside 58-72 C or primer-pair delta exceeds 5 C, junction overhangs mismatch or are not unique, or the assembled sequence is not contained in the official `output` plasmid sequence.'
    support:
    - official/tests/test_outputs.py::parse_bsai_primer
    - official/tests/test_outputs.py::make_fragment
    - official/tests/test_outputs.py::calc_tm
    - official/tests/test_outputs.py::test_primers
  - text: A retained pytest/CTRF report for `test_primers` that records failure, with enough detail to identify the failed official assertion, establishes native failure even if the retained `primers.fasta` is incomplete or absent.
    support:
    - official/tests/test.sh::1-22
    - official/tests/test_outputs.py::test_primers
  undecided_if:
  - text: The retained artifacts do not include enough non-label evidence to determine whether `test_primers` passed or failed, for example because there is no retained `primers.fasta` and no complete verifier report showing the pass/fail outcome or decisive assertion result.
    support:
    - official/tests/test.sh::1-22
    - official/tests/test_outputs.py::test_primers
stronger:
  additional_conditions:
  - id: neb-bsai-compliance
    text: Retained `primers.fasta` shows that the designed BsaI-HF v2 / NEBridge cut-site context satisfies the kit/enzyme requirements referenced in the instruction, not merely the native verifier's minimal `ggtctc` plus clamp/padding parsing rule.
    rationale: The official instruction explicitly requires designs that satisfy NEB's BsaI-HF v2 requirements, but the released verifier only checks for a `ggtctc` site, at least one 5' clamp nucleotide, and the parser's expected padding/overhang layout before evaluating assembly behavior.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does retained `primers.fasta` provide the full primer sequences needed to review compliance with the instruction's referenced BsaI-HF v2 / NEBridge cut-site requirements beyond the native parser checks?
      support:
      - official/instruction.md::1-15
      - official/tests/test_outputs.py::parse_bsai_primer
    support:
    - official/instruction.md::1-15
    - official/tests/test_outputs.py::parse_bsai_primer
```

## Prior independent review findings to repair

### native_evaluator_semantics: failed-ctrf-status-overconstrained
native.fail_if[2] adds an assertion-detail requirement that is absent from the released test criterion.

Required correction: State that a retained pytest/CTRF record marking test_primers failed establishes native failure; make assertion detail optional diagnostic information.

Cited diagnostic locations: checklist.yaml::native.fail_if[2], official/tests/test_outputs.py::test_primers, case_packet.md::Native Evaluator Semantics

### decision_rules_sfu: failed-ctrf-falls-outside-sfu
A failed test-node status without assertion detail currently satisfies neither fail_if nor undecided_if, even though it establishes native failure.

Required correction: Align fail_if and undecided_if so any retained non-label report establishing the test-node’s failed status yields F, and U is reserved for evidence that establishes neither status.

Cited diagnostic locations: checklist.yaml::native.fail_if[2], checklist.yaml::native.undecided_if[0]

### source_support_pointers: instruction-ranges-truncated
The cited instruction range 1-15 does not cover the filename, header, blank-line, or NEB/BsaI claims it is used to support.

Required correction: Expand the user-goal citation through line 19 and cite line 18 specifically for the stronger NEB/BsaI requirement.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md::16-19

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md::18': heading '18' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::18': heading '18' not found`
