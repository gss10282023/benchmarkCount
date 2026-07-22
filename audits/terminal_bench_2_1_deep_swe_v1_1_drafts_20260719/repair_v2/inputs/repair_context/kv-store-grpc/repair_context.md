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
- case_unit_id: `kv-store-grpc`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: kv-store-grpc
domain: terminal_bench_2_1
task_id: terminal-bench/kv-store-grpc
native:
  user_goal:
    text: 'Build a gRPC KV store in `/app`: install `grpcio==1.73.0` and `grpcio-tools==1.73.0` system-wide, create `kv-store.proto` with `KVStore`/`GetVal`/`SetVal`, generate the Python protobuf bindings in `/app`, implement `/app/server.py` with a `Server` class using a Python dict on port 5328, and keep the server running in the background.'
    support:
    - official/instruction.md::1-10
  benchmark_success:
    text: 'Native success is an official pytest run in which all seven checks in `official/tests/test_outputs.py` pass: proto file content, `grpc` import, generated `kv_store_pb2.py` and `kv_store_pb2_grpc.py`, `server.py` containing `class Server`, a listener on port 5328, the gRPC protocol handshake test, and KV `SetVal`/`GetVal` functionality including overwrite persistence.'
    support:
    - official/tests/test.sh::1-9
    - official/tests/test_outputs.py::test_proto_file_creation
    - official/tests/test_outputs.py::test_grpc_tools_installation
    - official/tests/test_outputs.py::test_protobuf_generation
    - official/tests/test_outputs.py::test_server_file_creation
    - official/tests/test_outputs.py::test_real_grpc_server_running
    - official/tests/test_outputs.py::test_grpc_protocol_handshake
    - official/tests/test_outputs.py::test_grpc_server_functionality
  checked_by:
    text: '`official/tests/test.sh` runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`; that pytest run is the native checker.'
    support:
    - official/tests/test.sh::1-9
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the CTRF report show pass/fail status for each official pytest check from `official/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::1-9
    - official/tests/test_outputs.py::test_proto_file_creation
    - official/tests/test_outputs.py::test_grpc_server_functionality
  - artifact: verifier/test-stdout.txt
    question: Does the pytest console output corroborate the same run, including test collection and any assertion or collection failures for `/tests/test_outputs.py`?
    support:
    - official/tests/test.sh::1-9
  success_if:
  - text: Retained verifier evidence establishes that the official pytest run completed and every test in `official/tests/test_outputs.py` passed.
    support:
    - official/tests/test.sh::1-9
    - official/tests/test_outputs.py::test_proto_file_creation
    - official/tests/test_outputs.py::test_grpc_tools_installation
    - official/tests/test_outputs.py::test_protobuf_generation
    - official/tests/test_outputs.py::test_server_file_creation
    - official/tests/test_outputs.py::test_real_grpc_server_running
    - official/tests/test_outputs.py::test_grpc_protocol_handshake
    - official/tests/test_outputs.py::test_grpc_server_functionality
  fail_if:
  - text: Retained verifier evidence establishes that any official test in `official/tests/test_outputs.py` failed or errored.
    support:
    - official/tests/test.sh::1-9
    - official/tests/test_outputs.py::test_proto_file_creation
    - official/tests/test_outputs.py::test_grpc_tools_installation
    - official/tests/test_outputs.py::test_protobuf_generation
    - official/tests/test_outputs.py::test_server_file_creation
    - official/tests/test_outputs.py::test_real_grpc_server_running
    - official/tests/test_outputs.py::test_grpc_protocol_handshake
    - official/tests/test_outputs.py::test_grpc_server_functionality
  - text: Retained verifier evidence establishes that pytest could not successfully collect or execute `/tests/test_outputs.py`, so the official all-tests-pass criterion was not met.
    support:
    - official/tests/test.sh::1-9
  undecided_if:
  - text: Available non-label artifacts do not reliably establish both that the official pytest run completed and whether all seven official tests passed or any failed.
    rationale: If `verifier/ctrf.json` is missing, incomplete, or inconsistent and the retained pytest console output does not clearly show the outcome of the official checks, the native all-tests-pass criterion cannot be confirmed or refuted from stored evidence alone.
stronger:
  additional_conditions:
  - id: exact-grpc-package-install
    text: Beyond native scoring, retained evidence should show that `grpcio==1.73.0` and `grpcio-tools==1.73.0` were installed system-wide, because the instruction requires those exact packages and versions while the released verifier does not directly check `grpcio-tools`, exact versions, or installation scope.
    rationale: The official task text explicitly requires both named packages at version `1.73.0` system-wide. Native evaluation only imports `grpc` and checks for generated protobuf files, so a run can satisfy native checks without retained proof of the exact package/version/scope requirement.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained action trace show a system-wide installation step for `grpcio==1.73.0` and `grpcio-tools==1.73.0`?
      support:
      - official/instruction.md::3-10
      - official/tests/test_outputs.py::test_grpc_tools_installation
      - official/tests/test_outputs.py::test_protobuf_generation
    - artifact: agent/*-stdout.txt
      question: Do retained command outputs corroborate successful installation of both exact package versions system-wide?
      support:
      - official/instruction.md::3-10
    support:
    - official/instruction.md::3-10
    - official/tests/test_outputs.py::test_grpc_tools_installation
    - official/tests/test_outputs.py::test_protobuf_generation
```

## Prior independent review findings to repair

### native_evaluator_semantics: native-success-uses-stronger-all-pass-rule
Native success is stated as completion with all seven tests passing, whereas official/tests/test.sh awards native success solely when the pytest invocation’s exit status is zero.

Required correction: Define benchmark_success, checked_by, success_if, and fail_if directly in terms of the shell-observed zero/nonzero exit status of the exact pytest command. Treat complete all-pass test evidence as one sufficient way to establish zero status, not as the native criterion itself.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.success_if[0], official/tests/test.sh::1-9

### decision_rules_sfu: sfu-does-not-track-pytest-exit-status
The current S/U rules can withhold S when non-label evidence establishes the released zero-exit criterion but does not establish that every test node passed.

Required correction: Assign S when retained non-label evidence establishes pytest exit status 0, F when it establishes a nonzero status, and U only when neither status can be established.

Cited diagnostic locations: checklist.yaml::native.success_if[0], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::1-9
