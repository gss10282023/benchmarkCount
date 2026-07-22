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
- case_unit_id: `git-multibranch`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: git-multibranch
domain: terminal_bench_2_1
task_id: terminal-bench/git-multibranch
native:
  user_goal:
    text: Set up `git@localhost:/git/project` to accept password-authenticated SSH with password `password`, and deploy `main` and `dev` branch `index.html` contents to `https://localhost:8443/index.html` and `https://localhost:8443/dev/index.html` via Nginx over self-signed HTTPS, with each push triggering deployment via a `post-receive` hook within 3 seconds.
    support:
    - official/instruction.md::1-18
  benchmark_success:
    text: The official verifier succeeds only if `official/tests/test.sh` reaches a passing `pytest` run for `test_multi_branch_https_deploy`, which clones `git@localhost:/git/project`, pushes `main` and `dev` with the specified file contents using the password prompt, then observes within its scripted wait/retry window that the HTTPS endpoints return exactly `main branch content` and `dev branch content`.
    support:
    - official/tests/test.sh::11-28
    - official/tests/test_outputs.py::7-99
  checked_by:
    text: Checked by `official/tests/test.sh` running `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`, specifically `test_multi_branch_https_deploy`.
    support:
    - official/tests/test.sh::17-28
    - official/tests/test_outputs.py::7-99
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does it record whether `test_multi_branch_https_deploy` passed or failed?
    support:
    - case_packet.md::76-88
    - official/tests/test.sh::17-21
    - official/tests/test_outputs.py::7-99
  - artifact: verifier/test-stdout.txt
    question: Does it show the verifier's `TEST PASSED` line or the concrete clone/push/content-mismatch failure emitted by `verify.sh`?
    support:
    - case_packet.md::76-88
    - official/tests/test_outputs.py::67-99
  - artifact: verifier/test-stderr.txt
    question: If CTRF or stdout is incomplete, does it show shell, pytest, or setup errors that still determine verifier failure?
    support:
    - case_packet.md::76-88
    - official/tests/test.sh::11-21
  success_if:
  - text: 'Native success if retained verifier evidence shows `test_multi_branch_https_deploy` passed: the scripted clone and password-auth pushes completed, and during the verifier''s scripted wait/retry window `curl -sk` returned exactly `main branch content` from `/index.html` and `dev branch content` from `/dev/index.html`.'
    support:
    - official/tests/test_outputs.py::26-91
    - official/tests/test.sh::17-28
  fail_if:
  - text: Native failure if retained verifier evidence shows the `official/tests/test.sh` working-directory guard fired before pytest.
    support:
    - official/tests/test.sh::11-15
  - text: Native failure if retained verifier evidence shows `test_multi_branch_https_deploy` failed because the clone or password-auth push steps did not complete, or because either HTTPS endpoint did not return its exact expected branch content within the verifier's scripted wait/retry window.
    support:
    - official/tests/test_outputs.py::26-91
    - official/tests/test.sh::17-28
  undecided_if:
  - text: Undecided only if retained non-label artifacts do not reliably establish whether the working-directory guard fired or whether `test_multi_branch_https_deploy` passed or failed, for example because `verifier/ctrf.json` is missing or unreadable and stdout/stderr lack decisive verifier output.
    support:
    - case_packet.md::76-88
    - official/tests/test.sh::11-28
    - official/tests/test_outputs.py::7-99
stronger:
  additional_conditions:
  - id: post_receive_and_3s_deadline
    text: Beyond native success, retained agent evidence should show that deployments are driven by a Git `post-receive` hook and that each push updates its branch HTTPS endpoint within 3 seconds; the native verifier only checks eventual correct content after a longer wait/retry window.
    rationale: The instruction explicitly requires `post-receive`-triggered deployment within 3 seconds of each push. The released verifier never inspects hook configuration and allows success after `sleep 3` plus up to five additional 2-second retries, so it can accept later or differently-triggered deployments.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained execution show creation or configuration of a `hooks/post-receive` deployment path for `main` and `dev`, and any timed validation that endpoint updates complete within 3 seconds of push?
      support:
      - case_packet.md::76-88
      - official/instruction.md::8-18
      - official/tests/test_outputs.py::67-91
    - artifact: artifacts/**
      question: Do retained files include the Git hook or deployment configuration corroborating post-receive-triggered branch deployment, plus any retained timing evidence?
      support:
      - case_packet.md::76-88
      - official/instruction.md::8-18
      - official/tests/test_outputs.py::67-91
    support:
    - official/instruction.md::8-18
    - official/tests/test_outputs.py::67-91
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_requires_unasserted_workflow_success
Native success and failure incorrectly depend on successful clone and password-authenticated push operations even though the released test does not assert those Expect child-command results.

Required correction: Define native success as the official pytest node passing—equivalently, its captured verify.sh stdout containing `TEST PASSED`—and native failure as the working-directory guard or a nonpassing/nonexecuted pytest criterion. Move successful SSH clone/push behavior to stronger measurement.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[1], official/tests/test_outputs.py::26-99

### decisive_post_run_evidence: stdout_failure_not_independently_decisive
A concrete clone or push error in verifier stdout does not independently establish native failure because the Expect script can still exit successfully and endpoint checks can still emit `TEST PASSED`.

Required correction: Limit stdout-based native failure to output that unambiguously establishes the final pytest assertion or invocation failed; do not use isolated clone or push errors as decision shortcuts.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[1], official/tests/test_outputs.py::26-66, official/tests/test_outputs.py::86-99

### decision_rules_sfu: sfu_not_aligned_to_test_outcome
The S/F rules can override the released test outcome based on clone/push completion, producing U or F despite retained evidence of a passing test.

Required correction: Make S and F depend exclusively on retained non-label evidence of the official guard/pytest result. Use U only when neither result can be established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if[1], checklist.yaml::native.undecided_if[0]

### source_support_pointers: evaluator_sources_do_not_support_claim
The evaluator pointers do not support treating successful clone/push completion as a necessary native condition because the Expect script does not validate those child statuses.

Required correction: Rewrite the affected claims to match the actual substring assertion and cite the Expect and final assertion portions; retain clone/push requirements only as instruction-supported stronger conditions.

Cited diagnostic locations: checklist.yaml::native.benchmark_success.support, checklist.yaml::native.success_if[0].support, checklist.yaml::native.fail_if[1].support, official/tests/test_outputs.py::26-99

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
