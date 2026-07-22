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
- case_unit_id: `openssl-selfsigned-cert`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: openssl-selfsigned-cert
domain: terminal_bench_2_1
task_id: terminal-bench/openssl-selfsigned-cert
native:
  user_goal:
    text: 'Create the requested TLS materials under `/app/ssl` using OpenSSL: a 2048-bit RSA private key at `/app/ssl/server.key` with mode 600, a 365-day self-signed certificate for `O=DevOps Team` and `CN=dev-internal.company.local` at `/app/ssl/server.crt`, a combined PEM at `/app/ssl/server.pem`, a `verification.txt` with subject, validity dates, and SHA-256 fingerprint, and `/app/check_cert.py` that loads the certificate and prints the CN, expiration date, and a success message.'
    support:
    - official/instruction.md::1-29
  benchmark_success:
    text: 'Native success means retained verifier evidence shows `official/tests/test.sh` reached pytest for `/tests/test_outputs.py` and all six official tests passed: `test_directory_structure`, `test_key_file`, `test_certificate_file`, `test_combined_pem_file`, `test_verification_file`, and `test_python_verification_script`.'
    support:
    - official/tests/test.sh::1-21
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  checked_by:
    text: Official bash verifier `official/tests/test.sh`, which runs `pytest -rA` on `/tests/test_outputs.py`; the native decision is therefore determined by the retained outcomes of those official pytest checks.
    support:
    - official/tests/test.sh::1-21
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the retained CTRF report show pass/fail outcomes for each of the six official pytest tests in `/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::13-21
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  - artifact: verifier/test-stdout.txt
    question: Does retained pytest stdout confirm the suite reached `/tests/test_outputs.py` and, when needed, identify which official check or subprocess assertion passed or failed?
    support:
    - official/tests/test.sh::13-21
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  - artifact: verifier/test-stderr.txt
    question: Does retained verifier stderr show that the verifier aborted before a passing pytest run or emitted execution errors relevant to the official checks?
    support:
    - official/tests/test.sh::8-21
  success_if:
  - text: 'Retained verifier evidence establishes that all six official pytest checks passed: `/app/ssl` exists as a directory; `/app/ssl/server.key` exists, has mode `<= 0600`, and `openssl rsa -text -noout` output contains `2048 bit`; `/app/ssl/server.crt` exists, OpenSSL text contains `dev-internal.company.local` and organization `DevOps Team` case-insensitively, and parsed `notAfter - notBefore` equals 365 days; `/app/ssl/server.pem` exists, contains both private-key and certificate markers, and `openssl x509 -in` on it succeeds; `/app/ssl/verification.txt` exists and contains the CN, organization, an accepted date format, and a SHA-256 fingerprint; and `/app/check_cert.py` exists and when run exits 0 with stdout containing `Certificate verification successful`, the CN, and a `YYYY-MM-DD` date.'
    support:
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  fail_if:
  - text: Retained verifier evidence establishes native failure if any one of those six official pytest checks failed, or if `official/tests/test.sh` aborted before a passing pytest run on `/tests/test_outputs.py`.
    support:
    - official/tests/test.sh::8-21
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  undecided_if:
  - text: If the retained non-label verifier artifacts do not establish whether pytest completed and what the pass/fail status was for each of the six official tests, the native verdict is undecided.
    support:
    - official/tests/test.sh::13-21
    - official/tests/test_outputs.py::test_directory_structure
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
    - official/tests/test_outputs.py::test_python_verification_script
  - text: If retained verifier artifacts conflict about a named official test outcome and the conflict cannot be resolved from the stored pytest reports, the native verdict is undecided.
    support:
    - official/tests/test.sh::13-21
stronger:
  additional_conditions:
  - id: stronger_use_openssl_commands
    text: Retained agent-execution evidence shows OpenSSL command-line tools were actually used to generate or inspect the certificate materials, because the instruction explicitly requires using OpenSSL commands while the native verifier only checks resulting files and script output.
    rationale: 'This is a concrete task-versus-evaluator gap: the instruction imposes a method requirement (`Use OpenSSL commands`) that the released verifier does not operationalize.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Do the retained executed commands show OpenSSL invocations that generated and/or inspected the key, certificate, PEM, or verification data?
      support:
      - official/instruction.md::24-29
      - official/tests/test_outputs.py::test_key_file
      - official/tests/test_outputs.py::test_certificate_file
      - official/tests/test_outputs.py::test_combined_pem_file
      - official/tests/test_outputs.py::test_verification_file
    - artifact: agent/*-stdout.txt
      question: If the trajectory is incomplete, do retained shell stdout logs still show the OpenSSL commands used for the task outputs?
      support:
      - official/instruction.md::24-29
      - official/tests/test_outputs.py::test_key_file
      - official/tests/test_outputs.py::test_certificate_file
      - official/tests/test_outputs.py::test_combined_pem_file
      - official/tests/test_outputs.py::test_verification_file
    support:
    - official/instruction.md::24-29
    - official/tests/test_outputs.py::test_key_file
    - official/tests/test_outputs.py::test_certificate_file
    - official/tests/test_outputs.py::test_combined_pem_file
    - official/tests/test_outputs.py::test_verification_file
  - id: stronger_verification_txt_full_subject_and_both_dates
    text: Retained `verification.txt` workspace artifact shows the certificate subject and both validity dates, not merely CN/O substrings plus one accepted date-like string, because the instruction asks for the certificate's subject and validity dates while the native verifier checks only those weaker substrings and regexes.
    rationale: 'This is a concrete content-coverage gap in `test_verification_file`: native success can occur without the full subject or both validity endpoints appearing in `verification.txt`, even though the instruction explicitly asks for them.'
    decisive_artifacts:
    - artifact: artifacts/**
      question: Does the retained workspace copy of `/app/ssl/verification.txt` contain the certificate subject and both validity dates?
      support:
      - official/instruction.md::18-22
      - official/tests/test_outputs.py::test_verification_file
    support:
    - official/instruction.md::18-22
    - official/tests/test_outputs.py::test_verification_file
```

## Prior independent review findings to repair

### native_user_goal: bf_native_goal_literal_and_pem_contents
The native user-goal summary omits that `server.pem` must contain both the private key and certificate and does not preserve the required literal success output.

Required correction: State both PEM contents explicitly and name the exact `Certificate verification successful` message in `native.user_goal`.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md::13-17, official/instruction.md::23-27

### stronger_conditions: bf_openssl_condition_too_weak
The stronger OpenSSL condition accepts inspection alone, although the cited official requirement is to create the certificate materials using OpenSSL.

Required correction: Require retained execution evidence that OpenSSL command-line invocations generated both the RSA private key and the self-signed certificate; retain the verifier sources only as evidence that this agent-method requirement is not operationalized.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].text, official/instruction.md::1-12, official/instruction.md::29, official/tests/test_outputs.py::test_key_file, official/tests/test_outputs.py::test_certificate_file

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/instruction.md::29': heading '29' not found
- $.stronger.additional_conditions[0].support[1] pointer 'official/instruction.md::29': heading '29' not found`
