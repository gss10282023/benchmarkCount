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
- case_unit_id: `mailman`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: mailman
domain: terminal_bench_2_1
task_id: terminal-bench/mailman
native:
  user_goal:
    text: Configure postfix and mailman3 so `reading-group@local.edu` supports confirmed join, confirmed leave, and announcement posting for `<user>@local.edu` addresses, delivers user mail to `/var/mail/<username>`, and uses `/etc/mailman3/mailman.cfg` as the mailman configuration file without owner approval for join/post requests.
    support:
    - official/instruction.md::1-16
  benchmark_success:
    text: Native success is retained evidence that the official verifier's pytest invocation over `/tests/test_outputs.py` completed successfully, meaning `test_simple_local_delivery`, `test_mlist_exists`, and `test_join_announce_leave_flow` all passed.
    support:
    - official/tests/test.sh::23-31
    - official/tests/test_outputs.py::test_simple_local_delivery
    - official/tests/test_outputs.py::test_mlist_exists
    - official/tests/test_outputs.py::test_join_announce_leave_flow
  checked_by:
    text: The official verifier script `official/tests/test.sh`, via `uv run pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.
    support:
    - official/tests/test.sh::23-31
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report record pass/fail outcomes for `test_simple_local_delivery`, `test_mlist_exists`, and `test_join_announce_leave_flow`?
    support:
    - official/tests/test.sh::28-28
    - official/tests/test_outputs.py::test_simple_local_delivery
    - official/tests/test_outputs.py::test_mlist_exists
    - official/tests/test_outputs.py::test_join_announce_leave_flow
  - artifact: verifier/test-stdout.txt
    question: Do the raw pytest logs confirm an all-pass run, or show a concrete test failure or pytest collection/internal error for the official suite?
    support:
    - official/tests/test.sh::28-28
    - official/tests/test_outputs.py::test_simple_local_delivery
    - official/tests/test_outputs.py::test_mlist_exists
    - official/tests/test_outputs.py::test_join_announce_leave_flow
  - artifact: verifier/test-stderr.txt
    question: Does stderr contain verifier/runtime error evidence needed to distinguish a documented pytest failure from missing or incomplete retained results?
    support:
    - official/tests/test.sh::28-28
  success_if:
  - text: Retained verifier evidence establishes a successful official pytest run in which `test_simple_local_delivery`, `test_mlist_exists`, and `test_join_announce_leave_flow` each passed.
    support:
    - official/tests/test.sh::23-31
    - official/tests/test_outputs.py::test_simple_local_delivery
    - official/tests/test_outputs.py::test_mlist_exists
    - official/tests/test_outputs.py::test_join_announce_leave_flow
  fail_if:
  - text: Retained verifier evidence shows any of `test_simple_local_delivery`, `test_mlist_exists`, or `test_join_announce_leave_flow` failed or errored, or shows a pytest collection/internal error that made the official suite non-successful.
    support:
    - official/tests/test.sh::28-31
    - official/tests/test_outputs.py::test_simple_local_delivery
    - official/tests/test_outputs.py::test_mlist_exists
    - official/tests/test_outputs.py::test_join_announce_leave_flow
  undecided_if:
  - text: Retained non-label artifacts do not establish either an all-pass official pytest run or a concrete official pytest failure/error for this suite.
    rationale: Native scoring is defined by the official pytest run, but if CTRF and raw verifier logs are missing, incomplete, or inconsistent, the retained evidence is insufficient to reconstruct that run without using barred reward/result labels.
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_user_goal: goal_omits_all_subscribers
The native user-goal statement weakens the explicit announcement requirement by saying only “announcement posting,” rather than delivery to all subscribers, and does not state the expressly requested SubscriptionPolicy.open setting.

Required correction: Revise native.user_goal to state announcement delivery to all subscribers and the explicit SubscriptionPolicy.open requirement, while retaining confirmed join/leave, mailbox-path, address-pattern, and configuration-path requirements.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::3-15

### stronger_conditions: missing_supported_stronger_measurements
The empty stronger layer omits source-supported requirements beyond the released test coverage: fan-out to multiple subscribers and explicit configuration of SubscriptionPolicy.open.

Required correction: Add separate stronger conditions for multi-subscriber announcement delivery and the exact SubscriptionPolicy.open setting, each identifying the released-test coverage gap and an inventory-listed retained artifact capable of assessing it.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions, official/instruction.md::3-15, official/tests/test_outputs.py::test_join_announce_leave_flow
