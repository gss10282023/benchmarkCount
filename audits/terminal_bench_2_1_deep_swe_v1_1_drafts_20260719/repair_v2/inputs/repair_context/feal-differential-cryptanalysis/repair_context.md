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
- case_unit_id: `feal-differential-cryptanalysis`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: feal-differential-cryptanalysis
domain: terminal_bench_2_1
task_id: terminal-bench/feal-differential-cryptanalysis
native:
  user_goal:
    text: Implement `/app/attack.py` so `attack(encrypt_fn)` performs a chosen-plaintext attack and returns the uint32 value of `key[5]`, with intended runtime under 30 seconds.
    support:
    - official/instruction.md::1-6
  benchmark_success:
    text: 'The native verifier counts success iff the single official pytest case passes: after building the C helper, importing `attack` and `feal_in_c`, generating random FEAL keys, and calling `attack.attack(feal_in_c.encrypt)`, the returned value equals `feal_in_c.get_keys()[5]`.'
    support:
    - official/tests/test.sh::17-29
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
  checked_by:
    text: '`official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -v -rA`; native pass/fail is the result of that pytest run.'
    support:
    - official/tests/test.sh::17-29
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record whether `test_feal_differential_cryptanalysis_attack` passed or failed?
    support:
    - case_packet.md::63-75
    - official/tests/test.sh::17-22
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
  - artifact: verifier/test-stdout.txt
    question: Does pytest stdout show the same single official test ran and, if it failed, whether the failure was the key-equality assertion or an import/build/runtime error?
    support:
    - case_packet.md::63-75
    - official/tests/test.sh::17-22
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
  success_if:
  - text: Retained verifier evidence shows `test_feal_differential_cryptanalysis_attack` passed, establishing that `attack.attack(feal_in_c.encrypt)` returned exactly `feal_in_c.get_keys()[5]` under the official test.
    support:
    - official/tests/test.sh::17-29
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
  fail_if:
  - text: Retained verifier evidence shows the single official pytest case failed for any reason, including a returned value unequal to `feal_in_c.get_keys()[5]` or an import/build/runtime exception before that assertion completes.
    support:
    - official/tests/test.sh::17-29
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
  undecided_if:
  - text: The retained non-label verifier artifacts are missing, truncated, or inconsistent enough that they do not establish whether `test_feal_differential_cryptanalysis_attack` passed or failed.
    support:
    - case_packet.md::47-75
    - official/tests/test.sh::17-29
stronger:
  additional_conditions:
  - id: chosen_plaintext_not_key_leakage
    text: Beyond native scoring, retained submitted-code evidence should show the reported `key[5]` was derived from chosen-plaintext queries to the provided `encrypt_fn`, not by importing test-only helpers such as `feal_in_c.get_keys()` or otherwise reading internal key state.
    rationale: The official instruction requires a chosen plaintext attack implemented as `attack(encrypt_fn)`, but the released verifier only checks equality against `feal_in_c.get_keys()[5]`. Because the test makes `feal_in_c` importable and exposes `get_keys`, native pass does not guarantee the key was recovered by cryptanalysis.
    decisive_artifacts:
    - artifact: artifacts/**
      question: Do retained submitted code artifacts show `attack` derives the answer from calls to `encrypt_fn` rather than direct access to `feal_in_c.get_keys()` or other internal key state?
      support:
      - case_packet.md::63-75
      - official/instruction.md::1-6
      - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
      - official/tests/feal_module.c::py_get_keys
      - official/tests/feal_module.c::FealMethods
    support:
    - official/instruction.md::1-6
    - official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack
    - official/tests/feal_module.c::py_get_keys
    - official/tests/feal_module.c::FealMethods
```

## Prior independent review findings to repair

### native_user_goal: goal_runtime_wording
The phrase “intended runtime under 30 seconds” weakens an explicit user requirement.

Required correction: State directly that attack(encrypt_fn) should run in less than 30 seconds.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::1-6

### native_evaluator_semantics: pytest_exit_semantics
Native failure is limited to the official test case failing, but test.sh’s criterion also fails on any evidenced nonzero uvx/pytest status, including invocation or collection errors before a test result exists.

Required correction: Define the native criterion using the uvx/pytest command status and explain that, for the single collected test, zero status entails the equality assertion passing.

Cited diagnostic locations: checklist.yaml::native.checked_by.text, checklist.yaml::native.fail_if[0], official/tests/test.sh::17-29

### decision_rules_sfu: incomplete_failure_branch
An evidenced collection or pytest-invocation failure can fall outside the current F wording and be incorrectly left U.

Required correction: Classify any retained non-label evidence establishing the official uvx/pytest command’s nonzero status as F; reserve U for evidence that establishes neither zero nor nonzero status.

Cited diagnostic locations: checklist.yaml::native.fail_if[0], checklist.yaml::native.undecided_if[0], official/tests/test.sh::17-29

### stronger_conditions: missing_runtime_stronger_condition
The checklist omits the official less-than-30-second requirement even though the released test does not time or assert that limit.

Required correction: Add a stronger condition for attack-call runtime below 30 seconds, identify the native measurement gap, name retained timing evidence that could assess it, and use stronger U when such evidence is absent.

Cited diagnostic locations: official/instruction.md::1-6, official/tests/test_outputs.py::test_feal_differential_cryptanalysis_attack, official/task.toml::verifier

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
