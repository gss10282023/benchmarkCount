# AndroidWorld canonical-source checklist generation

Generate this checklist independently from the complete canonical case packet supplied
with this request. No earlier checklist, review, score, repair note, or audit finding is
part of the model input or may be inferred. Treat the packet's verbatim source files as
the sole semantic authority.

Read the entire packet. Locate the exact `case_unit_id` task class and derive one
complete checklist from all of the following:

- the metadata task text;
- the task class's actual goal/template construction;
- its parameter schema and concrete parameter generator;
- `initialize_task` and every initialized baseline value;
- the complete `is_successful` implementation;
- every inherited, delegated, validator, parser, matcher, database, file, UI, or helper
  function that can change the result; and
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
   or below `0.5` in `fail_if`. Put initialization, execution, or evaluation exceptions;
   NaN; an absent numeric raw score; runner-created failed/excluded results; and
   missing, corrupt, contradictory, cross-episode, or unbound evidence in
   `undecided_if` whenever the normal raw-score/done/threshold chain cannot be
   reconstructed.
5. Atomize every clause of the runtime-generated user goal against what the native
   evaluator actually enforces. Add one measurable stronger condition for every
   material goal requirement that is unenforced or only partially enforced. Use an
   empty stronger list only when the supplied source proves full coverage.
6. Decisive artifacts must be retained post-run artifacts: evaluator input/output,
   state snapshots, files, rows, messages, UI/trace evidence, or runner records.
   Source text, intentions, model reasoning, or another judge are never run evidence.
   Do not require a final screenshot of transient state that the task itself replaces.
7. Do not prescribe an answer-key action sequence. A stronger rule may require a
   user-specified interaction method only when retained trace evidence can decide it.
8. Every support path before `::` must be copied verbatim from the packet's
   `## Source Inventory`. Every symbol, JSON/YAML selector, or line span after `::`
   must actually resolve and support the precise clause. Never cite the packet itself,
   a checklist, a workspace path, an absolute path, a URL, a leading `./`, or an
   invented selector.
9. Preserve `domain`, `case_unit_id`, and `task_id` exactly. Return only one complete
   checklist body conforming to the enforced schema, with no review, commentary, or
   issue list.
10. "Compact" and "terse" mean remove repetition only. They never permit omission or
    abstraction of a decisive condition, helper, branch, initialized baseline,
    metadata/code conflict, goal/evaluator gap, runner gate, or evidence-failure rule.
11. Every `native.user_goal`, `native.benchmark_success`, `native.checked_by`,
    `native.success_if`, `native.fail_if`, and `native.undecided_if` item must contain
    a non-empty `support` list resolving to the supplied Source Inventory. A
    `rationale` may be added, but it never substitutes for source support. This also
    applies to missing-evidence, exception, NaN, and runner-failure rules: cite the
    source that defines the expected evidence or runner behavior.

This output remains an unfrozen draft until deterministic QC, independent semantic
review, and explicit per-case root acceptance all pass 116/116.
