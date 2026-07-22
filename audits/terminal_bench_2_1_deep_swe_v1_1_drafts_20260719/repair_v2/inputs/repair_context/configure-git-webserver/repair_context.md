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
- case_unit_id: `configure-git-webserver`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: configure-git-webserver
domain: terminal_bench_2_1
task_id: terminal-bench/configure-git-webserver
native:
  user_goal:
    text: Configure the system so a user can clone `user@server:/git/server`, add and commit `hello.html`, push `master`, and then retrieve `hello.html` from the web server on port 8080 with body `hello world`; SSH login setup itself is out of scope.
    support:
    - official/instruction.md::1-10
  benchmark_success:
    text: 'Native success means the official verifier run passes: `official/tests/test.sh` runs the single pytest case `test_hello_html_exists`, and that case passes only if `/tests/verify.sh` prints `TEST PASSED` after cloning `user@localhost:/git/server`, committing and pushing `hello.html`, then observing HTTP 200 and body `hello world` at `http://localhost:8080/hello.html`.'
    support:
    - official/tests/test.sh::14-18
    - official/tests/test_outputs.py::9-13
    - official/tests/verify.sh::25-58
  checked_by:
    text: Official verifier `official/tests/test.sh`, which runs pytest case `test_hello_html_exists`; that case shells out to `/tests/verify.sh` and asserts that its stdout contains `TEST PASSED`.
    support:
    - official/tests/test.sh::14-18
    - official/tests/test_outputs.py::9-13
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the recorded pytest result show `test_hello_html_exists` passed or failed?
    support:
    - case_packet.md::68-80
    - official/tests/test.sh::14-18
    - official/tests/test_outputs.py::9-13
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show `/tests/verify.sh` completed the clone/push flow and either printed `TEST PASSED` after HTTP 200 with body `hello world`, or printed an explicit failure message for that check?
    support:
    - case_packet.md::68-80
    - official/tests/verify.sh::25-58
    - official/tests/test_outputs.py::11-13
  success_if:
  - text: Retained verifier evidence establishes that `test_hello_html_exists` passed, equivalently that `/tests/verify.sh` reached the web check and printed `TEST PASSED` after HTTP 200 and response body `hello world` for `http://localhost:8080/hello.html`.
    support:
    - official/tests/test_outputs.py::9-13
    - official/tests/verify.sh::40-58
  fail_if:
  - text: Retained verifier evidence establishes that `official/tests/test.sh` failed its WORKDIR guard before pytest, so the official verifier did not pass.
    support:
    - official/tests/test.sh::8-12
  - text: Retained verifier evidence establishes that `test_hello_html_exists` failed because `/tests/verify.sh` did not produce `TEST PASSED`, including explicit clone/push failure, non-200 HTTP response, or body other than `hello world`.
    support:
    - official/tests/test_outputs.py::11-13
    - official/tests/verify.sh::25-58
  undecided_if:
  - text: The retained non-label verifier artifacts are missing or inconclusive, so they do not establish whether the WORKDIR guard passed or whether `test_hello_html_exists` passed or failed.
    support:
    - case_packet.md::56-60
    - case_packet.md::68-80
    - official/tests/test.sh::8-18
    - official/tests/test_outputs.py::9-13
stronger:
  additional_conditions: []
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_semantics_overstatement
Native success and failure incorrectly depend on successful clone/push execution rather than the exact pytest substring assertion and pytest command status.

Required correction: Define native success as retained evidence that the official pytest invocation returned zero and its sole test passed because captured stdout contained `TEST PASSED`. Define failure as retained evidence of the WORKDIR abort or a nonzero pytest invocation; do not make clone/push errors independently dispositive.

Cited diagnostic locations: official/tests/test.sh::8-18, official/tests/test_outputs.py::9-13, official/tests/verify.sh::25-58

### decisive_post_run_evidence: stdout_visibility_overclaim
The proposed verifier-stdout question assumes visibility into output that `test_outputs.py` captures and does not emit.

Required correction: Limit `verifier/test-stdout.txt` to facts it can expose, such as the WORKDIR message and pytest terminal result. Use CTRF for the recorded pytest case result, without claiming either artifact proves the inner workflow succeeded.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], official/tests/test_outputs.py::9-13

### decision_rules_sfu: incorrect_failure_rule
An explicit clone/push error is not sufficient native F under the released assertion.

Required correction: Base F only on retained non-label evidence that the guard aborted or the official pytest invocation returned nonzero. Reserve U for evidence that establishes neither the success nor failure branch.

Cited diagnostic locations: checklist.yaml::native.fail_if[1], official/tests/test.sh::8-18, official/tests/test_outputs.py::9-13

### source_support_pointers: unsupported_claim_pointers
The cited evaluator sources contradict rather than support the claims about detailed stdout visibility and independently dispositive clone/push failures.

Required correction: Rewrite those claims to match capture and assertion behavior, then cite the exact test and verifier sources supporting the corrected semantics.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1].support, checklist.yaml::native.fail_if[1].support, official/tests/test_outputs.py::9-13

### stronger_conditions: missing_end_to_end_stronger_condition
The empty stronger layer omits the official end-to-end workflow requirement that the native assertion does not fully operationalize.

Required correction: Add a stronger condition requiring successful clone, commit, push, deployment, and HTTP retrieval, explicitly noting that the native verifier neither checks the Git command statuses nor binds the asserted substring to successful completion of that workflow.

Cited diagnostic locations: official/instruction.md::1-10, official/README.md::Task Requirements, official/tests/test_outputs.py::9-13, official/tests/verify.sh::25-58

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
