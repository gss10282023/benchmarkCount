## AndroidWorld candidate116 compact-packet gate

The supplied packet is the complete frozen LLM-visible source and intentionally has no Markdown Source Inventory. Every support pointer must therefore use `case_packet.md` as the exact path before `::`. Never use an `artifact_path`, AndroidWorld source path, workspace file, absolute path, URL, or leading `./` before `::`.

After `::`, cite a real JSON path in the packet's fenced JSON payload (preferred), or a precise line span. Copy JSON keys and list indexes exactly. For example, a pointer may look like `case_packet.md::source_context.evaluator_description.evaluator.method_chain[0]`; do not invent a JSON path.

Apply these semantic requirements fail-closed:

1. Treat the runtime-generated goal and canonical evaluator code as authoritative. When metadata wording differs, follow the runtime/code meaning and make the disposition explicit in the checklist text where relevant.
2. State native success and native failure using all three AndroidWorld layers when present: the raw `is_successful` result, the `interaction_results.done` gate, and the displayed `agent_successful > 0.5` threshold. Do not collapse or omit a layer.
3. Reserve `undecided_if` for missing, corrupt, contradictory, or unbound retained evidence. Ordinary evaluator failure, `done=false`, or a score at/below the threshold belongs in `fail_if`, not `undecided_if`.
4. Preserve exact parameters, equality/fuzzy rules, file extensions, formatting, counts, time/date semantics, app foreground requirements, and branch conditions stated by the runtime goal or evaluator.
5. Compare every user-visible clause of the runtime goal with what the native evaluator actually enforces. Put each meaningful unenforced or only partially enforced clause in `stronger.additional_conditions`, with post-run-decidable evidence. Use an empty stronger list only when the packet establishes that the evaluator covers every goal clause.
6. A source pointer explains why a rule was drafted; it is not run evidence. `decisive_artifacts` must name retained post-run state, trace, screenshot, tool log, message, native evaluator input/output, or file artifacts that can decide the rule after execution.
7. Do not prescribe an answer-key action sequence. Describe observable end-state or retained-trace conditions only.
