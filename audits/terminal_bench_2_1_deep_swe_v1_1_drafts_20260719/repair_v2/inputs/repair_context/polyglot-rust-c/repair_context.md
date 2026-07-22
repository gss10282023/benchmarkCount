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
- case_unit_id: `polyglot-rust-c`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: polyglot-rust-c
domain: terminal_bench_2_1
task_id: terminal-bench/polyglot-rust-c
native:
  user_goal:
    text: Produce a single polyglot source file at `/app/polyglot/main.rs` that can be compiled either with `rustc` or with `g++ -x c++` and, when run with argument `N`, prints the kth Fibonacci number with `f(0)=1`, `f(1)=1`, `f(2)=2`, etc.
    support:
    - official/instruction.md::1-8
  benchmark_success:
    text: 'Native success is established when retained verifier evidence shows the official pytest check `test_fibonacci_polyglot` passed: `/app/polyglot/main.rs` exists, the verifier''s Rust and C++ build invocations yield runnable binaries, and both binaries print `1`, `1`, `2`, `89`, and `433494437` for inputs `0`, `1`, `2`, `10`, and `42` respectively.'
    support:
    - case_packet.md::50-65
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs pytest with CTRF reporting on `official/tests/test_outputs.py::test_fibonacci_polyglot`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show whether `official/tests/test_outputs.py::test_fibonacci_polyglot` passed or failed?
    support:
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  - artifact: verifier/test-stdout.txt; verifier/test-stderr.txt
    question: If CTRF is missing or incomplete, do the retained verifier logs show the specific official-test outcome or failure mode for `test_fibonacci_polyglot`?
    support:
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  success_if:
  - text: '`verifier/ctrf.json` shows `official/tests/test_outputs.py::test_fibonacci_polyglot` passed, or equivalent retained verifier logs establish that `/app/polyglot/main.rs` existed and both produced binaries returned the expected stdout for all checked inputs `0`, `1`, `2`, `10`, and `42`.'
    support:
    - case_packet.md::50-65
    - case_packet.md::67-79
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  fail_if:
  - text: '`verifier/ctrf.json` shows `official/tests/test_outputs.py::test_fibonacci_polyglot` failed.'
    support:
    - case_packet.md::50-65
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  - text: 'Even without a decisive CTRF entry, retained verifier logs establish an official-test violation: `/app/polyglot/main.rs` was missing, either compiled binary could not be run for a checked input, or either binary''s stdout differed from the expected Fibonacci value for one of the checked inputs.'
    support:
    - case_packet.md::50-65
    - case_packet.md::67-79
    - official/tests/test_outputs.py::test_fibonacci_polyglot
  undecided_if:
  - text: Retained non-label artifacts do not establish whether `official/tests/test_outputs.py::test_fibonacci_polyglot` ultimately passed or failed; for example, `verifier/ctrf.json` is absent or incomplete and the retained verifier logs do not independently show a full official-test success or a specific official-test violation.
    support:
    - case_packet.md::50-65
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_fibonacci_polyglot
stronger:
  additional_conditions:
  - id: single-file-solution
    text: 'Beyond native scoring, retained evidence should show the delivered solution satisfied the instruction''s single-file requirement: the solution source was only `/app/polyglot/main.rs`, not supplemented by additional agent-created source/helper files for the task.'
    rationale: The official instruction asks for a single file at `/app/polyglot/main.rs`, but the released verifier only checks that `main.rs` exists and then compiles that file; it explicitly does not require `main.rs` to be the only file.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show whether the agent created or relied on any additional source/helper files instead of delivering the solution solely in `/app/polyglot/main.rs`?
      support:
      - case_packet.md::67-79
      - official/instruction.md::1-8
    - artifact: artifacts/**
      question: Do retained workspace artifacts show any extra solution source/helper files beyond `/app/polyglot/main.rs` that would violate the single-file instruction?
      support:
      - case_packet.md::67-79
      - official/instruction.md::1-8
    support:
    - official/instruction.md::1-8
    - official/tests/test_outputs.py::test_fibonacci_polyglot
```

## Prior independent review findings to repair

### native_user_goal: goal-omits-toolchain-versions
The user goal omits the stated rustc 1.75.0 and g++ 13.2.0 target environment and does not unambiguously say the same file must work with both compilers.

Required correction: State that the single file must compile and run under both specified compiler toolchains and produce the requested Fibonacci sequence.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-8

### native_evaluator_semantics: unchecked-compilation-strengthening
The checklist says the verifier's build invocations yield runnable binaries, but `os.popen(...).read()` does not inspect either compiler command's status. The test separately runs whatever exists at the expected executable paths.

Required correction: Describe the exact operations: existence assertion, unchecked compiler invocations, checked execution of both executable paths, and stdout assertions for the five inputs. Do not infer successful compilation merely from native passage.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.success_if[0].text, official/tests/test_outputs.py::test_fibonacci_polyglot

### native_evaluator_semantics: nonzero-pytest-status-omitted
The fail rules cover a failed node and several node-level violations but omit other nonzero outcomes of the official pytest command, such as collection or harness errors, which `test.sh` treats as native failure.

Required correction: Define native success as exit status zero from the exact pytest invocation and native failure as a retained-evidence-established nonzero status, while explaining the sole test's operations.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/test.sh::18-27

### decisive_post_run_evidence: combined-artifact-type
`verifier/test-stdout.txt; verifier/test-stderr.txt` is not one artifact type in the packet inventory.

Required correction: Create separate decisive-artifact entries for stdout and stderr, with each question limited to outcomes or failure facts that the individual log can establish.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], case_packet.md::Available Artifact Inventory

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
