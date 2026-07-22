# Fail-closed AndroidWorld fresh checklist generation

This is a completely fresh draft. No superseded checklist is present or may be
reconstructed, quoted, or imitated. The packet begins with a Fresh Generation
Control section and then contains the verbatim authoritative full case packet.
The control section may list defects observed in a rejected historical draft;
those statements are untrusted warnings only. They are never source facts,
support targets, retained run evidence, or permission to assume a correction.

Read the entire authoritative packet. Locate the exact `case_unit_id` task
class, then independently derive one complete checklist from:

- metadata task text;
- the task class's actual goal/template generation;
- parameter schema and the concrete parameter generator;
- `initialize_task` and all initialized baseline state;
- the complete `is_successful` implementation;
- every inherited, delegated, validator, parser, matcher, database, file, UI,
  or helper function that changes the result; and
- the actual runner path, including raw score, `interaction_results.done`,
  persisted `agent_successful`, exception/NaN handling, and displayed success
  at the strict `agent_successful > 0.5` threshold.

The output must satisfy every rule below simultaneously.

1. Runtime code is semantic authority. Metadata is descriptive. Explicitly
   disposition every material metadata-versus-runtime difference and every
   parameter-schema-versus-generator difference in auditable checklist text.
   State what differs and how it affects the goal/evaluator. Do not silently
   decide that code wins.
2. Expand evaluator semantics literally. Preserve exact expressions, branch
   order, string normalization/formatting/suffixes, time windows, counts,
   equality/set/row rules, thresholds, fuzzy matching, foreground/UI settings,
   initialized baselines, and helper/delegate behavior. Phrases such as "the
   evaluator passes" or "the delegated check succeeds" are insufficient.
3. Encode all three AndroidWorld layers: raw `task.is_successful(env)`, the
   `interaction_results.done` gate, and displayed success only when the gated
   `agent_successful > 0.5`. Native failure rules must retain explicit raw
   evaluator, done-gate, and threshold language.
4. Ordinary raw-evaluator rejection, `done == false`, or a gated numeric score
   at or below `0.5` belongs in `fail_if`. Initialization, execution, or
   evaluation exceptions; NaN; an absent numeric raw score; or a runner-created
   failed/excluded result belongs in `undecided_if` whenever the normal
   raw-score/done/threshold chain cannot be reconstructed. `undecided_if` also
   covers missing, corrupt, contradictory, cross-episode, or unbound evidence.
5. Atomize every clause of the runtime-generated goal against what the native
   evaluator actually enforces. Add one measurable stronger condition for
   every material goal requirement that is unenforced or only partially
   enforced. Use an empty stronger list only when source proves full coverage.
6. Decisive artifacts must be retained post-run artifacts: evaluator
   input/output, state snapshots, files, rows, messages, UI/trace evidence, or
   runner records. Source code, packet text, intentions, model reasoning, prior
   issue text, or another judge are never run evidence. Do not require a final
   screenshot of transient state that the task itself replaces.
7. Do not prescribe an answer-key action sequence. A stronger rule may require
   a user-specified interaction method only when retained trace evidence can
   decide it.
8. Every support path before `::` must be exactly `case_packet.md` or a path
   copied verbatim from the authoritative packet's `## Source Inventory`.
   Every symbol, JSON/YAML selector, or line span after `::` must actually
   resolve and support the precise clause. Never cite the Fresh Generation
   Control section, historical audit files, `checklist.yaml`, workspace files,
   absolute paths, URLs, a leading `./`, or invented selectors.
9. Resolve every warning in Fresh Generation Control by re-reading source. If
   a warning is inapplicable, source must justify the fresh result. The output
   must not mention the warning, the historical draft, repair, audit, or this
   instruction.
10. Preserve `domain`, `case_unit_id`, and `task_id` exactly. Return only one
    complete checklist body conforming to the enforced schema, with no review,
    patch, commentary, or issue list.

This output remains an unfrozen draft until deterministic QC, independent
semantic review, and explicit per-case root acceptance all pass 116/116.
