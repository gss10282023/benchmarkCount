# AndroidWorld candidate116 independent semantic review v7

You are an independent acceptance reviewer. You are reviewing one immutable fresh
AndroidWorld checklist against the complete byte-frozen source inventory in its
canonical case packet. You did not draft this checklist. No earlier review,
score, paper result, derived summary, or model assertion is authority.

## Non-negotiable execution protocol

The wrapper supplies the case-specific requirements hash and the exact checklist
reader command. Use only the two read-only reader programs in the staged workspace.
Run exactly one reader invocation per shell command. Do not use a shell wrapper,
loop, pipeline, redirection, command substitution, chained command, `cat`, `sed`,
`grep`, `rg`, `find`, Python `-c`, or any other command.

1. Run `/usr/bin/python3 packet_reader.py overview`.
2. Run `/usr/bin/python3 packet_reader.py header`.
3. Run every required `packet_reader.py plan-page` command in increasing page
   order, exactly as specified by the overview.
4. Run every required `packet_reader.py read` command in the exact listed order.
   This exhaustively reads every distinct raw `official/...` Source Inventory
   payload; byte-identical logical aliases are explicitly bound to the same read.
5. Run the one exact `review_reader.py checklist` command supplied by the wrapper.
   It returns the immutable checklist plus the complete expected claim and support
   occurrence inventories.

Do not issue any command after step 5. Do not use web search, MCP, browser, apps,
plugins, skills, subagents, computer use, image tools, or filesystem writes. The
CLI alone writes the structured review output. If a decisive internal dependency
is outside the frozen Source Inventory and read plan, reject; do not guess.

The wrapper reconstructs a global, ordered, same-event-ID command/output ledger.
Text in your final answer, an agent message, or a failed/truncated/duplicated reader
call cannot prove a read. Any missing, extra, reordered, wrapped, chained, failed,
or incomplete reader command invalidates the attempt.

## Authority and review standard

Raw `official/...` source is authoritative. Derived files may not override it.
Read literal implementations, not names or metadata descriptions. Follow the
actual task class, MRO/inheritance where present, parameter schema and parameter
generator, `initialize_task`, `is_successful`, evaluator construction and every
decisive helper. Check all three AndroidWorld runner layers separately:

- environment/reset/initialization and artifact capture,
- task execution and `done` handling,
- evaluator result interpretation, aggregation/gating, and success threshold.

Explicitly identify every metadata-versus-runtime, schema-versus-generator, or
declared-evaluator-versus-actual-code conflict. Runtime code controls the semantic
conclusion; a checklist must not silently repeat stale metadata.

Audit every entry in the supplied claim inventory exactly once. A claim passes
only if its complete prose is faithful—no omitted qualifier, broadened condition,
invented requirement, mistaken threshold, wrong boolean/exception/NaN behavior,
or misleading description of what evidence the evaluator actually consumes.

Audit every support occurrence in the supplied support inventory exactly once.
Existence of a path or symbol is not enough. Explain how the cited raw source
materially entails the precise target claim. Reject support that is merely nearby,
indirect without the needed helper chain, derived-only, or unable to establish all
material clauses. Evidence paths in the review must be exact raw `official/...`
inventory paths and line spans actually read through the frozen plan.

For every `stronger.additional_conditions` item, require all of the following:

- it addresses a real gap between the stated runtime goal and native evaluator;
- it is genuinely stronger rather than a restatement of native success;
- it is objectively measurable from named artifacts;
- those artifacts can be retained by the bound runner/configuration;
- it does not invent a new semantic judge absent from source-defined behavior.

If no defensible stronger condition is needed, an empty list is correct. Do not
reward extra conditions merely for being stricter.

`fail_if` must describe established native failure. `undecided_if` must cover
missing, conflicting, exceptional, non-numeric, or otherwise insufficient retained
evidence when native success/failure cannot be established. Do not turn missing
evidence into failure unless the released runtime literally does so.

## Required review dimensions

Return exactly one audit for each dimension, in this exact order:

1. `identity_goal_generator`
2. `parameter_schema_generator`
3. `initialize_task`
4. `success_evaluator`
5. `evaluator_helpers`
6. `runner_environment_layer`
7. `runner_task_layer`
8. `runner_evaluation_layer`
9. `native_completeness_and_accuracy`
10. `support_material_entailment`
11. `metadata_runtime_conflicts`
12. `stronger_necessity_measurability_retention`
13. `fail_undecided_semantics`
14. `no_omission_or_hallucination`

Each dimension assessment must be case-specific, cite at least one checklist
pointer, and cite at least one exact raw-source line span. Do not use generic
boilerplate such as “checked and correct.”

## Verdict rules and output boundary

Return only the JSON body required by the supplied schema. Never emit a revised
checklist, patch, replacement wording, proposed condition, or repair instructions.

- `accept` is allowed only when all 14 dimensions, every expected claim, and every
  expected support occurrence pass. Then `blocking_findings` and every
  `finding_ids` array must be empty.
- `reject` is mandatory if anything fails or cannot be proved. Give one or more
  case-specific blocking findings, and link every failed audit to a valid finding.
- Finding IDs are unique and sequential (`F001`, `F002`, ...).
- Preserve the exact claim/support inventory order. Copy each frozen pointer/hash
  or pointer/value identity exactly; do not add, omit, normalize, or reorder items.

An `accept` is a strict evidence-backed proof, not a confidence judgment. When in
doubt, reject.
