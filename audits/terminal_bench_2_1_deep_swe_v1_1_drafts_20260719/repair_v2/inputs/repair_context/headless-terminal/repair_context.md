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
- case_unit_id: `headless-terminal`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: headless-terminal
domain: terminal_bench_2_1
task_id: terminal-bench/headless-terminal
native:
  user_goal:
    text: Provide `/app/headless_terminal.py` defining `HeadlessTerminal(BaseTerminal)` importable as `from headless_terminal import HeadlessTerminal`, with a headless terminal that starts an interactive bash shell, supports interactive programs and modifier keys, sources startup files, preserves shell state between commands, and supports background processes.
    support:
    - official/instruction.md::1-10
    - official/task.toml::4-6
    - official/README.md::12-19
  benchmark_success:
    text: Native success is established when retained verifier evidence shows `official/tests/test.sh` reached `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA` and pytest exited 0, meaning all seven official tests in `official/tests/test_outputs.py` passed.
    support:
    - official/tests/test.sh::7-16
    - official/tests/test_outputs.py::11-130
  checked_by:
    text: The official verifier script `official/tests/test.sh`, specifically its pytest run over `official/tests/test_outputs.py` and exit-status check.
    support:
    - official/tests/test.sh::13-16
    - official/tests/test_outputs.py::11-130
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report show the seven official pytest cases from `official/tests/test_outputs.py`, and are they all passed or is any case failed/errored?
    support:
    - official/tests/test.sh::13-14
    - official/tests/test_outputs.py::11-130
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout corroborate that pytest for `/tests/test_outputs.py` ran under `official/tests/test.sh`, or instead show the explicit working-directory guard or a pytest failure summary?
    support:
    - official/tests/test.sh::7-16
  success_if:
  - text: A readable `verifier/ctrf.json` plus corroborating `verifier/test-stdout.txt` establish that pytest ran on `official/tests/test_outputs.py` and that the import, non-interactive command, interactive vim, Ctrl-C cancel, startup-file, shell-state, and background-command tests all passed.
    support:
    - official/tests/test.sh::13-16
    - official/tests/test_outputs.py::11-130
  fail_if:
  - text: Retained verifier evidence establishes failure if `official/tests/test.sh` hit its explicit invalid-`$PWD` guard before pytest, or if pytest for `/tests/test_outputs.py` recorded any failed or errored official test and therefore exited nonzero.
    support:
    - official/tests/test.sh::7-16
    - official/tests/test_outputs.py::11-130
  undecided_if:
  - text: The retained verifier artifacts are missing, unreadable, or inconsistent enough that they do not establish whether pytest on `/tests/test_outputs.py` ran to completion and whether every official test passed or any official test failed.
    rationale: The native claim depends on the verifier script's explicit guard and the per-test pytest outcomes; without reliable retained verifier records, neither native success nor native failure is established from non-label evidence.
stronger:
  additional_conditions:
  - id: require-base-terminal-subclass
    text: Beyond native pass, retained code evidence should show the final implementation actually declares `HeadlessTerminal(BaseTerminal)` and implements the interface, because that structural requirement is explicit in the task but not checked by the native verifier.
    rationale: '`official/instruction.md` requires `HeadlessTerminal(BaseTerminal)`, and `official/environment/base_terminal.py` defines the interface, but the released tests only import, instantiate, and call `send_keystrokes`; they do not check inheritance from `BaseTerminal`.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does the retained final code or patch show `HeadlessTerminal` is defined as a subclass of `BaseTerminal` with a `send_keystrokes` implementation?
      support:
      - official/instruction.md::1-10
      - official/environment/base_terminal.py::4-14
      - official/tests/test_outputs.py::11-27
    support:
    - official/instruction.md::1-10
    - official/environment/base_terminal.py::4-14
    - official/tests/test_outputs.py::11-27
```

## Prior independent review findings to repair

### native_user_goal: missing-system-python-goal
native.user_goal omits the official instruction to install dependencies into the system Python.

Required correction: Add the dependency-installation instruction without making dependency use mandatory when the implementation needs none.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::10

### native_evaluator_semantics: native-exit-semantics-narrowed
Native success is defined by the immediate pytest exit status, not by an added requirement that every CTRF node explicitly have passed status; native failure includes every nonzero pytest outcome, not only recorded failed/errored tests.

Required correction: State the exact zero/nonzero exit-status criterion, retain the explicit working-directory guard, and remove the mandatory CTRF-plus-stdout conjunction.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.text, checklist.yaml::native.success_if[0].text, checklist.yaml::native.fail_if[0].text, official/tests/test.sh::7-20

### decision_rules_sfu: sfu-evidence-conjunction-and-failure-gap
The current rules can return U even when one retained non-label artifact establishes success or when stderr/log evidence establishes a nonzero pytest outcome outside the listed test-failure cases.

Required correction: Allow any sufficient retained non-label evidence to establish S or F, include all causes of the verifier's nonzero branch, and reserve U strictly for cases where neither claim is established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory

### stronger_conditions: stronger-condition-overlap
The stronger condition combines the untested BaseTerminal inheritance requirement with method implementation that the native tests do exercise.

Required correction: Narrow that condition to the untested subclass relationship and add a separate conditional system-Python dependency condition with its exact evaluator gap.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, checklist.yaml::stronger.additional_conditions[0].rationale, official/tests/test_outputs.py::11-27, official/instruction.md::1-10
