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
- case_unit_id: `qemu-startup`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: qemu-startup
domain: terminal_bench_2_1
task_id: terminal-bench/qemu-startup
native:
  user_goal:
    text: Start `/app/alpine.iso` in QEMU, leave it running in the background, and wait until `telnet 127.0.0.1 6665` reaches a login prompt so the user can log in.
    support:
    - official/instruction.md::1-1
  benchmark_success:
    text: 'Native success is the single official pytest check `test_version` passing: `official/tests/test.sh` runs `official/tests/test_outputs.py::test_version`, which invokes its bundled expect script and then requires `/tmp/data.txt` to be readable and to contain `6.6.4-1-lts`.'
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::expect
    - official/tests/test_outputs.py::test_version
  checked_by:
    text: Checked by `official/tests/test.sh` running pytest against `official/tests/test_outputs.py::test_version` with CTRF reporting.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the official pytest record show whether `test_version` passed, failed, or errored, and any attached failure message?
    support:
    - case_packet.md::59-69
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
  - artifact: verifier/test-stdout.txt
    question: Does the verifier output corroborate the `test_version` result and, on failure, show whether `/tmp/data.txt` was missing/unreadable or lacked `6.6.4-1-lts`?
    support:
    - case_packet.md::59-69
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
  success_if:
  - text: Retained verifier evidence shows `test_version` passed, meaning the released check completed and accepted the resulting `/tmp/data.txt` because it contained `6.6.4-1-lts` after the expect invocation.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
  fail_if:
  - text: Retained verifier evidence shows `test_version` failed or errored, including because `/tmp/data.txt` was missing or unreadable after the expect invocation, or because its contents did not contain `6.6.4-1-lts`.
    support:
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
  undecided_if:
  - text: Retained non-label verifier artifacts are missing or too incomplete to determine whether official `test_version` passed or failed.
    support:
    - case_packet.md::47-53
    - case_packet.md::59-69
stronger:
  additional_conditions:
  - id: qemu_iso_background_state
    text: Retained agent evidence should show that the agent launched QEMU using `/app/alpine.iso` as a backgrounded process and left that VM running when it finished; the native check does not directly verify the launch command or background/linger state.
    rationale: The official instruction requires starting `/app/alpine.iso` in QEMU, leaving it running in the background, and blocking until ready, but the released evaluator operationalizes only the `test_version` check on the verifier side and does not inspect the agent's final QEMU command or process-management state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained action trace show a QEMU launch command that uses `/app/alpine.iso` and backgrounds or daemonizes the VM?
      support:
      - case_packet.md::63-65
      - official/instruction.md::1-1
    - artifact: agent/*-stdout.txt
      question: Do retained agent outputs include a final process or job-status check showing the launched QEMU instance was still running after startup?
      support:
      - case_packet.md::63-65
      - official/instruction.md::1-1
    support:
    - official/instruction.md::1-1
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::test_version
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_exit_semantics_incomplete
Native success and failure are expressed only as test_version node outcomes, but test.sh assigns reward from the complete uvx/pytest exit status and can fail before or without such a node.

Required correction: Define native success as the working-directory guard passing and the uvx/pytest command returning zero; define native failure to include the guard exit and every established nonzero invocation, collection, test, or session outcome. Preserve the exact test_version body semantics, including the ignored expect status.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if[0], official/tests/test.sh::13-29, official/tests/test_outputs.py::test_version

### decision_rules_sfu: known_harness_failures_misclassified
The current U rule can absorb conclusively evidenced collection, invocation, or session failures merely because test_version has no pass/fail node.

Required correction: Send any retained non-label evidence establishing the verifier guard or pytest command failed to F; reserve U solely for evidence that cannot establish either the successful or unsuccessful verifier outcome.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29

### source_support_pointers: trajectory_inventory_pointer_off_target
The packet range cited for agent/trajectory.json does not cover that inventory entry.

Required correction: Point artifact availability claims to case_packet.md::Available Artifact Inventory (types only; no per-record values) or the exact corresponding entry.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[0].support[0], case_packet.md::Available Artifact Inventory (types only; no per-record values)

### stronger_conditions: stronger_gaps_not_separated
The checklist does not separately assess agent-side blocking until readiness or a fresh live login prompt, and its single condition bundles launch provenance with process-state claims.

Required correction: Use separate case-specific conditions for exact QEMU/ISO provenance, background launch plus agent-side readiness waiting, and a fresh telnet login prompt. State for each how test_version fails to measure it and name retained agent evidence capable of assessing it.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0], official/instruction.md::1-1, official/tests/test_outputs.py::expect, official/tests/test_outputs.py::test_version
