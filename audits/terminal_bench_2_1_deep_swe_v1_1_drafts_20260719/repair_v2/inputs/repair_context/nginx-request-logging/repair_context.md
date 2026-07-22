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
- case_unit_id: `nginx-request-logging`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: nginx-request-logging
domain: terminal_bench_2_1
task_id: terminal-bench/nginx-request-logging
native:
  user_goal:
    text: Set up Nginx on localhost:8080 to serve `/var/www/html` with the specified index and 404 pages, detailed access logging, configured error logging, rate limiting, the required config-file placement/default-site removal, a syntax check before start, and a displayed access-log path, while minimizing commands.
    support:
    - official/instruction.md::1-24
  benchmark_success:
    text: 'Native success is a completed official verifier run in which every pytest check in `/tests/test_outputs.py` passes: nginx is installed; localhost:8080 returns 200 with the exact index body; a nonexistent page returns 404 with the exact custom body; `nginx -t` succeeds; the required config-file/setting checks pass; and `/var/log/nginx/benchmark-access.log` exists with the log-format regex checks satisfied.'
    support:
    - official/tests/test.sh::17-25
    - official/tests/test_outputs.py::test_nginx_installed
    - official/tests/test_outputs.py::test_nginx_running
    - official/tests/test_outputs.py::test_index_page_content
    - official/tests/test_outputs.py::test_custom_404_page
    - official/tests/test_outputs.py::test_nginx_config_syntax
    - official/tests/test_outputs.py::test_nginx_config_settings
    - official/tests/test_outputs.py::test_log_file_creation
    - official/tests/test_outputs.py::test_log_file_format
  checked_by:
    text: The official shell verifier runs pytest against `/tests/test_outputs.py` and records the run in retained verifier report artifacts.
    support:
    - official/tests/test.sh::17-25
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail status for each official pytest case from `/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::17-22
    - official/tests/test_outputs.py::11-178
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show the pytest run for `/tests/test_outputs.py` completed, and if not, what concrete test or harness failure occurred?
    support:
    - official/tests/test.sh::17-25
  - artifact: verifier/test-stderr.txt
    question: Does verifier stderr contain setup, pytest, or `nginx -t` errors that establish a native failure when the CTRF report is missing or incomplete?
    support:
    - official/tests/test.sh::11-25
    - official/tests/test_outputs.py::test_nginx_config_syntax
  success_if:
  - text: Retained verifier evidence establishes a completed run of the official pytest suite for `/tests/test_outputs.py` in which all eight named tests pass and none fail or error.
    support:
    - official/tests/test.sh::17-25
    - official/tests/test_outputs.py::11-178
  fail_if:
  - text: Retained verifier evidence establishes that any official pytest case in `/tests/test_outputs.py` failed or errored.
    support:
    - official/tests/test.sh::17-25
    - official/tests/test_outputs.py::11-178
  - text: Retained verifier evidence establishes that the shell verifier did not complete a passing pytest run for `/tests/test_outputs.py`, such as a harness or setup failure before or during test execution.
    support:
    - official/tests/test.sh::11-25
  undecided_if:
  - text: The retained non-label verifier artifacts are missing, truncated, or mutually inconsistent enough that they do not establish either a completed all-pass run or a concrete verifier/test failure.
    support:
    - official/tests/test.sh::17-25
stronger:
  additional_conditions:
  - id: instruction_only_nginx_directives
    text: Beyond native success, retained evidence should also show the final Nginx setup writes `error_log /var/log/nginx/benchmark-error.log`, defines the rate-limit zone with 10MB storage, applies `limit_req` in the server block with burst 10, and removes `/etc/nginx/sites-enabled/default`; the released verifier does not check those instruction clauses.
    rationale: The instruction makes these configuration details part of the task, but the released tests only require `benchmark-site.conf`, `listen 8080`, `root /var/www/html`, a `log_format` containing the four named fields, and a `limit_req_zone` match for `rate=10r/s`, plus the HTTP responses and access-log checks.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show final-file writes or file reads for `/etc/nginx/nginx.conf`, `/etc/nginx/conf.d/benchmark-site.conf`, and `/etc/nginx/sites-enabled/default` that establish these uncovered directives/removal?
      support:
      - official/instruction.md::4-13
      - official/tests/test_outputs.py::test_nginx_config_settings
    - artifact: agent/*-stdout.txt
      question: Do retained agent stdout logs print the relevant Nginx config or filesystem state well enough to verify these uncovered instruction clauses?
      support:
      - official/instruction.md::4-13
      - official/tests/test_outputs.py::test_nginx_config_settings
    - artifact: artifacts/**
      question: Do retained artifacts include copies or diffs of the final Nginx config files or default-site state that verify these uncovered instruction clauses?
      support:
      - official/instruction.md::4-13
      - official/tests/test_outputs.py::test_nginx_config_settings
    support:
    - official/instruction.md::4-13
    - official/tests/test_outputs.py::test_nginx_config_settings
```

## Prior independent review findings to repair

### stronger_conditions: missing_source_supported_stronger_measurements
The stronger layer omits explicit instruction requirements that the released verifier does not operationalize: rate limiting per client IP, successful syntax testing before start/restart, the start/restart and agent-performed localhost verification, and displaying the access-log path.

Required correction: Retain the existing final-configuration measurement while making the per-IP requirement explicit, and add a separate condition for the instructed execution order, service action, localhost verification, and access-log-path display. State that the native tests only inspect final syntax/reachability and do not measure those actions or their ordering.

Cited diagnostic locations: official/instruction.md::4-24, official/tests/test_outputs.py::test_nginx_running, official/tests/test_outputs.py::test_nginx_config_syntax, official/tests/test_outputs.py::test_nginx_config_settings, checklist.yaml::stronger.additional_conditions[0]
