# Terminal-Bench 2.1 and DeepSWE v1.1 drafting supplement

Apply these requirements in addition to the frozen base drafting prompt. They are
part of the fixed system design for this batch.

1. Draft before seeing any concrete agent outcome or per-record released evaluator
   result. Do not infer or mention any current run result.
2. The released evaluator/oracle source code and configuration define the native
   criterion and may be cited as source support. A per-record released label or
   final reward/result record is comparison-only metadata and must never be a
   decisive artifact or a success/failure/undecided shortcut.
3. In particular, do not name `result.json`, `verifier/reward.txt`,
   `verifier/reward.json`, or an equivalent final success/fail/reward field in
   `native.decisive_artifacts`, stronger decisive artifacts, or as evidence that a
   checklist rule is satisfied. Raw retained traces, stdout/stderr, CTRF reports,
   test reports, patches, and other run artifacts may be named only when their
   contents independently establish facts required by the released criterion.
4. Native `S` means retained non-label evidence establishes the released native
   success criterion. Native `F` means retained non-label evidence establishes a
   released native failure condition. Native `U` means neither claim can be
   established from the retained non-label evidence. Do not turn an ordinary
   benchmark-counted failure into `U` when the retained evidence establishes it.
5. `native.user_goal` must preserve the official task/user intent, while
   `native.benchmark_success`, `success_if`, and `fail_if` must reproduce what the
   released evaluator/oracle actually operationalizes. Do not silently strengthen
   the native criterion to the prose task.
6. Put an additional condition in `stronger.additional_conditions` only when the
   official task, user intent, or policy itself gives concrete case-specific source
   support for a requirement that the released evaluator/oracle does not
   operationalize. State that exact measurement gap in the condition or rationale.
   Evaluator tests may demonstrate noncoverage but may not invent a stronger
   requirement absent official task/user/policy support. Exclude reviewer
   preferences, generic quality expectations, and speculative requirements.
7. Stronger measurement is independent. Do not describe stronger failure as a
   benchmark error or conflict, and do not infer a conflict from native success plus
   stronger failure. Benchmark conflict is outside this checklist and requires a
   later record-level review with retained artifacts and source pointers.
8. Name only artifacts from the packet's Available Artifact Inventory. An artifact
   inventory entry states availability by type, not a value for any current record.

Benchmark-specific reminders:

- For DeepSWE v1.1, native success/failure is the exact configured fail-to-pass and
  pass-to-pass node aggregation in the evaluator projection/grader, including its
  missing, skipped, duplicate-ID, and non-empty fail-to-pass rules. Task prose
  requirements not covered by those configured nodes belong in stronger only when
  the official instruction concretely supports them and retained artifacts can in
  principle assess them. Every DeepSWE v1.1 instruction explicitly requires the
  agent to work on a new branch from `main` and commit everything. Preserve that
  workflow requirement in `native.user_goal`, but do not add it to native success:
  the configured test-node aggregation does not fully check the final branch or a
  clean, fully committed worktree. Record the unoperationalized branch/commit
  requirement as one concise stronger condition, supported by
  `official/instruction.md` plus evaluator/grader sources that demonstrate the
  native boundary. Use only retained `agent/trajectory.json`,
  `agent/mini-swe-agent.txt`, and/or `artifacts/model.patch` as its in-principle
  evidence; a future record may be stronger U when those artifacts do not establish
  the final branch and commit state.
- For Terminal-Bench 2.1, derive each native rule from that case's exact verifier
  and tests. Do not replace a task-specific verifier with a benchmark-wide generic
  predicate. Treat any concrete instruction/verifier gap under the stronger rules
  above.
