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
- case_unit_id: `build-pmars`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: build-pmars
domain: terminal_bench_2_1
task_id: terminal-bench/build-pmars
native:
  user_goal:
    text: 'Build pMARS from Debian source packages with no X server: extract the Debian source to `/app/pmars-<version>/`, build there without X11 support, leave the source tree in place, install `/usr/local/bin/pmars`, and have the debugger and sample battle command work.'
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the official verifier passing all four pytest checks in `official/tests/test_outputs.py`: working `/usr/local/bin/pmars` functionality/debugger output, no X11-linked libraries, a `/app/pmars-*` source tree with `debian/`, and a `/app/pmars-*/src` tree containing at least one `.c` file.'
    support:
    - official/tests/test.sh::18-29
    - official/tests/test_outputs.py::19-85
  checked_by:
    text: '`official/tests/test.sh`, which runs `pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`.'
    support:
    - official/tests/test.sh::18-22
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: 'Do the retained pytest results show whether each official check passed or failed: functionality/debugger, no X11 linkage, Debian-source tree presence, and source-file presence?'
    support:
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
    - official/tests/test_outputs.py::19-85
  - artifact: verifier/test-stdout.txt
    question: Does pytest stdout corroborate which official checks ran and, if any failed, the relevant assertion context?
    support:
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
  - artifact: verifier/test-stderr.txt
    question: Did verifier-side runtime/setup errors occur that would affect whether the official pytest results can be interpreted?
    support:
    - case_packet.md::67-79
    - official/tests/test.sh::3-29
  success_if:
  - text: 'Retained verifier evidence establishes that `/usr/local/bin/pmars` existed; debugger stepping on both `rave.red` and `flashpaper.red` produced at least two matched addresses each; `pmars -b -r 50 -f flashpaper.red rave.red | tail -n 1` matched `Results: \d+ \d+ \d+`; `ldd /usr/local/bin/pmars` contained none of `libX11`, `libXt`, `libXext`, or `libXaw`; and `/app/pmars-*` contained both `debian/` and `src/*.c`.'
    support:
    - official/tests/test_outputs.py::19-85
    - official/tests/test.sh::18-22
  fail_if:
  - text: 'Retained verifier evidence shows `/usr/local/bin/pmars` was missing, debugger stepping on `rave.red` or `flashpaper.red` produced fewer than two matched addresses, or the battle command''s last line did not match `Results: \d+ \d+ \d+`.'
    support:
    - official/tests/test_outputs.py::19-48
  - text: Retained verifier evidence shows `ldd /usr/local/bin/pmars` included `libX11`, `libXt`, `libXext`, or `libXaw`.
    support:
    - official/tests/test_outputs.py::51-57
  - text: Retained verifier evidence shows no `/app/pmars-*` directory existed or its `debian/` subdirectory was missing.
    support:
    - official/tests/test_outputs.py::60-70
  - text: Retained verifier evidence shows the `/app/pmars-*/src` directory was missing or contained no `.c` files.
    support:
    - official/tests/test_outputs.py::73-85
  undecided_if:
  - text: The retained verifier artifacts are missing, truncated, or internally inconsistent, so the pass/fail status of one or more official pytest checks cannot be established from non-label evidence.
    support:
    - case_packet.md::50-61
    - case_packet.md::67-79
    - official/tests/test.sh::18-22
stronger:
  additional_conditions:
  - id: debian-provenance-build-location
    text: Beyond native success, retained run evidence should show that the built `/usr/local/bin/pmars` came from the Debian source package extracted under `/app/pmars-<version>/` and was built in that tree, not merely that a matching tree with `debian/` and `src/*.c` existed afterward.
    rationale: The instruction explicitly requires obtaining the source from Debian packages and building from the extracted `/app/pmars-<version>/` tree, but the released tests only check for post-run presence of `/app/pmars-*`, `debian/`, and `src/*.c`, plus binary behavior and linkage.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained trajectory show Debian source retrieval/extraction and compilation commands executed inside `/app/pmars-<version>/` before installation to `/usr/local/bin/pmars`?
      support:
      - case_packet.md::67-79
      - official/instruction.md::1-3
    - artifact: agent/*-stdout.txt
      question: Do retained command outputs corroborate Debian source-package retrieval/extraction and a build performed from `/app/pmars-<version>/`?
      support:
      - case_packet.md::67-79
      - official/instruction.md::1-3
    support:
    - official/instruction.md::1-3
    - official/tests/test_outputs.py::60-85
```

## Prior independent review findings to repair

### native_evaluator_semantics: incomplete_native_failure_semantics
The native fail_if rules enumerate assertion-level conditions but omit the released evaluator’s broader nonzero-pytest-status path, including command execution, collection, and subprocess errors.

Required correction: Define native success and failure in terms of the exact pytest invocation status captured by official/tests/test.sh. Retain the four case-specific test functions as the tested scope, and expressly include evidenced command, collection, or test errors under F.

Cited diagnostic locations: official/tests/test.sh::18-29, official/tests/test_outputs.py::7-16, checklist.yaml::native.fail_if

### decision_rules_sfu: ordinary_failures_can_fall_outside_f
A retained stderr/stdout trace could establish that pytest could not execute or returned nonzero, yet none of the current fail_if clauses assigns F unless a listed assertion fact is shown.

Required correction: Add an F rule for any retained non-label evidence establishing that the official pytest invocation returned nonzero, and reserve U strictly for cases where neither zero nor nonzero status can be established.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts[2], checklist.yaml::native.fail_if, checklist.yaml::native.undecided_if[0], official/tests/test.sh::18-29

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found`
