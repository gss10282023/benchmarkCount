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
- case_unit_id: `install-windows-3.11`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: install-windows-3.11
domain: terminal_bench_2_1
task_id: terminal-bench/install-windows-3.11
native:
  user_goal:
    text: Run the provided Windows 3.11 image under QEMU, leave the VM running in the background, expose VNC on display :1 / port 5901, expose a web interface on port 80, use snapshot mode, and provide a QEMU monitor socket at `/tmp/qemu-monitor.sock` so the VM reaches the Windows 3.11 desktop and accepts programmatic keyboard input.
    support:
    - official/instruction.md::1-14
  benchmark_success:
    text: 'Native success means retained verifier evidence establishes that the official pytest verifier passed all four checks in `official/tests/test_outputs.py`: network status, QEMU process/configuration, Windows 3.11 core-file verification, and monitor-driven keyboard visual feedback.'
    support:
    - official/tests/test.sh::1-25
    - official/tests/test_outputs.py::test_network_status
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
  checked_by:
    text: The official checker is `official/tests/test.sh`, which runs `pytest` on `official/tests/test_outputs.py` and treats a zero pytest exit as success.
    support:
    - official/tests/test.sh::1-25
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained pytest report show pass/fail outcomes for `test_network_status`, `test_qemu_running_with_correct_params`, `test_windows_311_core_files_verification`, and `test_windows_keys_with_visual_feedback`?
    support:
    - official/tests/test.sh::1-25
    - official/tests/test_outputs.py::test_network_status
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
  - artifact: verifier/test-stdout.txt
    question: If the CTRF report is missing or ambiguous, does retained pytest stdout establish the same named test outcomes or the specific assertion that failed?
    support:
    - official/tests/test.sh::1-25
    - official/tests/test_outputs.py::test_network_status
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
  success_if:
  - text: 'Retained verifier evidence shows that all four official pytest checks passed: `test_network_status`, `test_qemu_running_with_correct_params`, `test_windows_311_core_files_verification`, and `test_windows_keys_with_visual_feedback`.'
    support:
    - official/tests/test.sh::1-25
    - official/tests/test_outputs.py::test_network_status
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
  fail_if:
  - text: Retained verifier evidence shows `test_network_status` failed, establishing that the verifier did not observe both a listener on VNC port 5901 and a listener on port 80.
    support:
    - official/tests/test_outputs.py::test_network_status
  - text: Retained verifier evidence shows `test_qemu_running_with_correct_params` failed, establishing that the verifier did not observe a live QEMU process with the required snapshot/image/hash/architecture/memory conditions.
    support:
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
  - text: Retained verifier evidence shows `test_windows_311_core_files_verification` failed, establishing that the verifier could not confirm at least five required Windows 3.11 core files by hash from `/app/isos/win311.img`.
    support:
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::WINDOWS_311_CORE_FILES
  - text: Retained verifier evidence shows `test_windows_keys_with_visual_feedback` failed, establishing that the verifier did not confirm monitor-socket keyboard control with a successful screenshot-based visual change of at least 10%.
    support:
    - official/tests/test_outputs.py::monitor_socket
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
  undecided_if:
  - text: The retained non-label verifier artifacts do not establish pass/fail status for the four official pytest checks, or are incomplete or conflicting enough that neither all-pass nor any specific official test failure is established.
    support:
    - official/tests/test.sh::1-25
    - official/tests/test_outputs.py::test_network_status
    - official/tests/test_outputs.py::test_qemu_running_with_correct_params
    - official/tests/test_outputs.py::test_windows_311_core_files_verification
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
    rationale: Native scoring is defined by the outcomes of these official pytest checks; without retained evidence of those outcomes, source code alone cannot fix success or failure for a run.
stronger:
  additional_conditions:
  - id: desktop_state_explicit
    text: Beyond native scoring, require retained visual evidence that the VM had reached the Windows 3.11 desktop before keyboard probing; the released verifier only requires that some monitor-sent key produce a large enough VNC image change.
    rationale: The instruction defines completion at the Windows 3.11 desktop, but `test_windows_keys_with_visual_feedback` accepts any baseline screen so long as one of the injected keys yields at least 10% pixel difference.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained screenshots or other visual artifacts show that the pre-key VNC view was the Windows 3.11 desktop rather than some other responsive screen?
      support:
      - official/instruction.md::1-14
      - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
    support:
    - official/instruction.md::1-14
    - official/tests/test_outputs.py::test_windows_keys_with_visual_feedback
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_nginx
`native.user_goal` omits nginx even though the instruction explicitly requires the port-80 web interface to use nginx.

Required correction: State that the web interface on port 80 is to be provided through nginx while preserving the rest of the official intent.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::VNC Configuration Requirements

### native_evaluator_semantics: pytest_exit_semantics_incomplete
Native S/F is expressed only through four named pass/fail results, not the exact zero-versus-nonzero pytest status used by `test.sh`. Setup and other pytest errors are therefore omitted.

Required correction: Define native S as retained non-label evidence of a zero pytest status and native F as retained non-label evidence of any nonzero pytest status, including failed tests and collection, fixture/setup, execution, usage, interruption, or internal errors.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, official/tests/test.sh::21-35

### decision_rules_sfu: errors_misclassified_as_u
An evidenced pytest error that is not phrased as a named test failure satisfies neither current S nor F and can fall into U despite causing the released checker’s failure branch.

Required correction: Make F cover every retained-evidence-established nonzero pytest outcome and reserve U solely for evidence that establishes neither zero nor nonzero status.

Cited diagnostic locations: checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::31-35

### source_support_pointers: test_sh_range_does_not_support_claims
The `official/tests/test.sh::1-25` range ends before the complete pytest invocation and exit-status branch used by several claims.

Required correction: Replace that range with a pointer covering the pytest invocation, CTRF output, and `$?` branch, such as `official/tests/test.sh::21-35`.

Cited diagnostic locations: checklist.yaml::native.checked_by.support[0], checklist.yaml::native.success_if[0].support[0], official/tests/test.sh::21-35

### stronger_conditions: missing_nginx_web_measurement
The official nginx web-interface requirement is not operationalized by the verifier’s mere `:80` substring check and is absent from the stronger layer.

Required correction: Add a stronger condition requiring retained evidence that nginx actually serves the port-80 VNC web interface, with an artifact capable of showing service identity and an HTTP/web-interface response.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::VNC Configuration Requirements, official/tests/test_outputs.py::test_network_status

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'official/instruction.md::VNC Configuration Requirements': heading 'VNC Configuration Requirements' not found
- $.stronger.additional_conditions[1].support[0] pointer 'official/instruction.md::VNC Configuration Requirements': heading 'VNC Configuration Requirements' not found`
