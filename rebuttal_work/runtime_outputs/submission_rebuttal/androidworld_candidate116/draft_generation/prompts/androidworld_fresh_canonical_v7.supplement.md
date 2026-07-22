# AndroidWorld canonical-source checklist generation, staged-input edition

Generate one checklist independently from the frozen canonical case packet supplied
for this case. No earlier checklist, review, score, repair note, warning, or audit
finding is part of the model input or may be inferred. The packet's embedded source
files are the sole semantic authority.

The full `case_packet.md` is hash-bound and available read-only. Because some packets
are larger than one model context, do not bulk-print the packet. Use the frozen staged
view instead:

1. Use the frozen reader in this exact order: one bounded `overview`; one bounded
   `header` containing Case Metadata and Source Inventory; every declared `plan-page`
   in ascending page-index order; then every declared source `read` row in the order
   fixed by those pages. Never print an entire coverage manifest or packet view in one
   command. Use exactly one reader invocation per shell command; do not use loops,
   pipelines, command substitution, or command chains. Read every declared page/row
   exactly once. After the model returns, the wrapper will reconstruct the reader
   ledger from paired command/output events and reject any omitted, duplicated,
   failed, or out-of-order operation. `model_input_coverage.json` is only a navigation
   index; it is never evidence and must never appear in an output support pointer.
2. Read the indicated files under `packet_sources/`. Each file is a byte-exact
   materialization of the correspondingly named member of the packet's Source
   Inventory. The prefix `packet_sources/` is a workspace detail and must be omitted
   from output support pointers. Every distinct raw `official/...` Source Inventory
   member is mandatory input; do not infer that an unexamined member is irrelevant.
   Byte-identical logical aliases may share one physical read only when the frozen plan
   binds every alias to that same content hash. Read every frozen chunk or line range
   separately in the listed order; do not join chunks into one bulk command whose tool
   output can be truncated.
3. Completely inspect every coverage anchor for the exact task class, goal/template,
   parameter schema and concrete generator, `initialize_task`, `is_successful`, every
   inherited/delegated/helper path that can change the decision, and the runner's raw
   score, done gate, persistence, exception/NaN handling, and display threshold.
4. The frozen plan must cover every raw official Inventory member. If the source still
   reveals an internal decisive dependency outside the Inventory or plan, do not guess,
   abstract it away, or use an unplanned read: that is a fail-closed generation defect
   and the wrapper must reject the attempt.

Derive the checklist from all of the following:

- the selected metadata task text;
- the task class's actual goal/template construction;
- its parameter schema and concrete parameter generator;
- `initialize_task` and every initialized baseline value;
- the complete `is_successful` implementation;
- every inherited, delegated, validator, parser, matcher, database, file, UI, or
  helper function that can change the result; and
- the actual runner path: raw score, `interaction_results.done`, persisted
  `agent_successful`, exception/NaN handling, and displayed success only when the
  gated numeric `agent_successful > 0.5`.

The output must satisfy every rule below simultaneously.

1. Runtime code is semantic authority and metadata is descriptive. Explicitly
   disposition every material metadata-versus-runtime difference and every
   parameter-schema-versus-generator difference in auditable checklist text. State
   what differs and how it changes the generated goal or evaluator; do not silently
   choose one side.
2. Expand evaluator semantics literally. Preserve exact expressions, branch order,
   string normalization and formatting, suffixes, time windows, counts, equality/set/
   row rules, thresholds, fuzzy matching, foreground/UI settings, initialized
   baselines, and helper/delegate behavior. "The evaluator passes" or "the delegated
   check succeeds" is never sufficient.
3. Encode all three AndroidWorld layers: raw `task.is_successful(env)`, the
   `interaction_results.done` gate, and displayed success only when the gated numeric
   `agent_successful > 0.5`. Native failure rules must retain explicit raw-evaluator,
   done-gate, and threshold language.
4. Put ordinary raw-evaluator rejection, `done == false`, and a gated numeric score at
   or below `0.5` in `fail_if`. Put initialization, execution, or evaluation
   exceptions; NaN; an absent numeric raw score; runner-created failed/excluded
   results; and missing, corrupt, contradictory, cross-episode, or unbound evidence
   in `undecided_if` whenever the normal raw-score/done/threshold chain cannot be
   reconstructed.
5. Atomize every clause of the runtime-generated user goal against what the native
   evaluator actually enforces, and explicitly disposition every gap. Add one stronger
   condition for each material unenforced or partially enforced requirement only when
   an allowable retained artifact and a source-defined, non-speculative predicate can
   decide it. Never invent a semantic judge or rubric. An empty stronger list is valid
   only when raw source proves full native coverage or proves that every remaining gap
   is not measurably decidable under the allowed retained-evidence rules; record the
   latter gap explicitly in supported native checklist text.
6. Decisive artifacts must be retained post-run artifacts: evaluator input/output,
   state snapshots, files, rows, messages, UI/trace evidence, or runner records.
   Source text, intentions, model reasoning, another judge, and the coverage index are
   never run evidence. Do not require a final screenshot of transient state that the
   task itself replaces.
7. Do not prescribe an answer-key action sequence. A stronger rule may require a
   user-specified interaction method only when retained trace evidence can decide it.
8. Every support path before `::` must be copied verbatim from the packet's
   `## Source Inventory`. Every symbol, JSON/YAML selector, or line span after `::`
   must actually resolve and support the precise clause. Never cite `case_packet.md`,
   `model_input_coverage.json`, `packet_sources/`, a checklist, a workspace path, an
   absolute path, a URL, a leading `./`, or an invented selector.
9. Each atomic runtime-semantic item must cite at least one applicable raw
   `official/...` source. This requirement covers every item in `native.user_goal`,
   `native.benchmark_success`, `native.checked_by`, `native.decisive_artifacts`,
   `native.success_if`, `native.fail_if`, and `native.undecided_if`, plus every
   runtime-semantic `stronger.additional_conditions` item and each of its decisive
   artifacts. It applies to claims about the goal, parameters, initialization,
   evaluator, helper/delegate behavior, runner, expected retained artifact, and the
   question that artifact must decide. `derived/selected_task_source.json` may support
   identity, selection, or a recorded metadata conflict; `derived/source_closure.json`
   may support provenance; and `derived/canonical_task_semantics.json` may aid
   navigation or corroborate a derived conflict. A `derived/...` file must never be
   the sole support for a runtime-semantic item when a raw source binding exists.
10. The wrapper locally injects the schema-enforced `schema_version` and extracts and
    injects `domain`, `case_unit_id`, and `task_id` from the frozen packet. Do not
    return those four fields. Return exactly the two schema-enforced body fields
    `native` and `stronger`, with no review, commentary, reading log, or issue list.
11. "Compact" and "terse" mean remove repetition only. They never permit omission or
    abstraction of a decisive condition, helper, branch, initialized baseline,
    metadata/code conflict, goal/evaluator gap, runner gate, or evidence-failure rule.
12. Every `native.user_goal`, `native.benchmark_success`, `native.checked_by`,
    `native.decisive_artifacts`, `native.success_if`, `native.fail_if`, and
    `native.undecided_if` item, every `stronger.additional_conditions` item, and every
    stronger decisive artifact must contain a non-empty `support` list resolving to
    the supplied Source Inventory. A `rationale` may be added, but it never substitutes
    for source support. This also applies to missing-evidence, exception, NaN, and
    runner-failure rules: cite the raw source that defines the expected evidence or
    runner behavior.

This output remains an unfrozen draft until deterministic QC, independent semantic
review, and explicit per-case root acceptance all pass 116/116.
