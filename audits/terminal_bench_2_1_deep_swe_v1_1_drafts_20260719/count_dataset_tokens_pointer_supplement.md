# Count-dataset-tokens pointer-format supplement

Apply these requirements as the fixed system design for this targeted retry.

1. Draft before seeing any concrete agent outcome or per-record released
   evaluator result. Do not infer or mention any current run result.
2. The released evaluator/oracle source code and configuration define the
   native criterion and may be cited as source support. A per-record released
   label or final reward/result record is comparison-only metadata and must
   never be a decisive artifact or a success/failure/undecided shortcut.
3. Do not name `result.json`, `verifier/reward.txt`, `verifier/reward.json`, or
   an equivalent final success/fail/reward field in native or stronger decisive
   artifacts, or as evidence that a checklist rule is satisfied. Raw retained
   traces, stdout/stderr, test reports, and other inventoried run artifacts may
   be named only when their contents independently establish facts required by
   the released criterion.
4. Native `S` means retained non-label evidence establishes the released native
   success criterion. Native `F` means retained non-label evidence establishes
   a released native failure condition. Native `U` means neither claim can be
   established. Do not turn an evidenced benchmark-counted failure into `U`.
5. `native.user_goal` must preserve the official task/user intent, while
   `native.benchmark_success`, `success_if`, and `fail_if` must reproduce what
   the released evaluator/oracle operationalizes. Do not silently strengthen
   the native criterion to the prose task.
6. Add a stronger condition only when the official task, user intent, or policy
   gives concrete case-specific support for a requirement not operationalized
   by the evaluator/oracle. State the exact measurement gap. Evaluator tests may
   demonstrate noncoverage but may not invent a stronger requirement. Exclude
   reviewer preferences and generic or speculative quality requirements.
7. Stronger measurement is independent. Stronger failure is not a benchmark
   error or conflict, and native success plus stronger failure does not imply a
   conflict. Benchmark conflict is outside this checklist and requires later
   record-level review with retained artifacts and source pointers.
8. Name only artifacts from the packet's Available Artifact Inventory. An
   inventory entry establishes availability by type, not a current-record value.
9. Derive the Terminal-Bench native rules from this case's exact verifier and
   tests. Do not replace them with a benchmark-wide generic predicate. Treat any
   concretely supported instruction/verifier gap under the stronger rules above.

The following addendum only removes ambiguity in support-pointer syntax; it does
not change the native or stronger measurement semantics.

For Markdown sources, a bare numeric selector such as
`official/instruction.md::4` is interpreted as a heading and is invalid here.
Use an explicit, real one-based line span instead:

- `official/instruction.md` has exactly 4 lines. Use pointers such as
  `official/instruction.md::lines 1-4` or
  `official/instruction.md::lines 3-4`.
- `official/README.md` has exactly 21 lines. Use pointers such as
  `official/README.md::lines 3-4` or
  `official/README.md::lines 20-21`. Never cite a line past 21.
- For the packet document, use an exact visible heading such as
  `case_packet.md::Available Artifact Inventory (types only; no per-record values)`
  or a verified explicit line span. Do not shorten or invent a heading.

Every support pointer must use an exact path from the packet Source Inventory,
and every selected line span must be non-empty and within the actual file.
