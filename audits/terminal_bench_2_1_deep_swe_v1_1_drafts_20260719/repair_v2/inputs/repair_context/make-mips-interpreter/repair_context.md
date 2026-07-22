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
- case_unit_id: `make-mips-interpreter`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: make-mips-interpreter
domain: terminal_bench_2_1
task_id: terminal-bench/make-mips-interpreter
native:
  user_goal:
    text: Implement `vm.js` as a MIPS interpreter that can run `/app/doomgeneric_mips`, handle needed file reads/writes and syscalls, boot DOOM, and save frames as they are rendered so the first frame is created and saved correctly.
    support:
    - official/instruction.md::1-1
    - official/task.toml::task.description
  benchmark_success:
    text: Official verifier success is pytest exit 0 for `/tests/test_outputs.py`, which operationally requires `test_vm_execution`, `test_frame_bmp_exists`, and `test_frame_bmp_similar_to_reference` all to pass.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
  checked_by:
    text: Official verifier script `official/tests/test.sh`, which runs pytest with CTRF reporting on `official/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::18-24
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show pass/fail/error outcomes for `test_vm_execution`, `test_frame_bmp_exists`, and `test_frame_bmp_similar_to_reference`?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
  - artifact: verifier/test-stdout.txt
    question: Does retained verifier stdout show the pytest run over `/tests/test_outputs.py` and any timeout/assertion details needed to interpret the three official checks?
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
  success_if:
  - text: Retained verifier evidence shows `test_vm_execution`, `test_frame_bmp_exists`, and `test_frame_bmp_similar_to_reference` each passed.
    support:
    - official/tests/test.sh::18-30
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
  fail_if:
  - text: Retained verifier evidence shows `test_vm_execution` failed or errored, including timeout waiting for `/tmp/frame.bmp` or missing expected DOOM initialization stdout bytes.
    support:
    - official/tests/test_outputs.py::test_vm_execution
  - text: Retained verifier evidence shows `test_frame_bmp_exists` failed because `/tmp/frame.bmp` was absent or empty.
    support:
    - official/tests/test_outputs.py::test_frame_bmp_exists
  - text: Retained verifier evidence shows `test_frame_bmp_similar_to_reference` failed because the saved frame size differed from the reference or computed similarity was below `0.95`.
    support:
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
  - text: Retained verifier evidence shows the pytest invocation for `/tests/test_outputs.py` failed before all three official checks completed.
    support:
    - official/tests/test.sh::18-30
  undecided_if:
  - text: Retained non-label artifacts do not establish whether the pytest invocation completed and what the outcomes were for the three named official tests.
    support:
    - official/tests/test.sh::18-24
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
    rationale: Without a retained CTRF report or equivalent verifier output that recovers the named test outcomes, native success or failure cannot be reconstructed from stored evidence alone.
stronger:
  additional_conditions:
  - id: frame_sequence_saved
    text: Beyond native pass, retained evidence should show that frame outputs were saved as rendering progressed, not merely that one final `/tmp/frame.bmp` eventually existed, because the instruction requires saving frames "as they are rendered, one at a time" while the released verifier accepts a single saved frame file.
    rationale: '`official/instruction.md` explicitly requires frame-by-frame saving. The released verifier waits for one `/tmp/frame.bmp`, then only checks that this one file exists, is non-empty, and is visually similar to the reference image.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained output artifacts show multiple saved frame outputs or equivalent sequential frame snapshots produced during execution, rather than only one final frame file?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_vm_execution
      - official/tests/test_outputs.py::test_frame_bmp_exists
      - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
    - artifact: agent/trajectory.json
      question: Does the retained trajectory indicate the final implementation saves frames during rendering rather than only producing a single end-state frame artifact?
      support:
      - official/instruction.md::1-1
      - official/tests/test_outputs.py::test_vm_execution
      - official/tests/test_outputs.py::test_frame_bmp_exists
      - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
    support:
    - official/instruction.md::1-1
    - official/tests/test_outputs.py::test_vm_execution
    - official/tests/test_outputs.py::test_frame_bmp_exists
    - official/tests/test_outputs.py::test_frame_bmp_similar_to_reference
```

## Prior independent review findings to repair

### decisive_post_run_evidence: trajectory_not_decisive_for_runtime_frame_sequence
agent/trajectory.json is named as decisive for whether the final implementation saved frames during rendering, but a raw trajectory does not independently prove that runtime behavior occurred.

Required correction: Remove agent/trajectory.json from this stronger condition’s decisive artifacts, or narrow its question to a fact directly exposed by the trace that is not treated as proof of runtime frame production. Retain artifacts/** as the in-principle state/output evidence source.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], review_prompt.md::decisive_post_run_evidence, case_packet.md::Available Artifact Inventory (types only; no per-record values)

### stronger_conditions: stronger_condition_uses_incapable_artifact
Although the frame-sequence requirement and measurement gap are valid, not every named retained artifact can assess the condition: the trajectory cannot establish actual sequential frame outputs.

Required correction: Keep the source-supported frame-sequence condition and its measurement-gap rationale, but delete the trajectory artifact and rely on retained output/state artifacts whose contents can establish multiple sequential frame snapshots.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].rationale, checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[1], official/instruction.md::1-1, official/tests/test_outputs.py::test_vm_execution
