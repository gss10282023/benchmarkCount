## AndroidWorld candidate116 full-source semantic gate

This packet contains the complete frozen source closure. Before drafting, locate the exact task class named by `case_unit_id`, then read its `template`, parameter schema/generator, `initialize_task`, complete `is_successful` implementation, every base-class or helper/delegate that contributes to the result, and `suite_utils._run_task`. Do not substitute an AST call summary or a method name for the actual implementation.

Apply these rules fail-closed:

1. Use the runtime-generated goal and canonical task/evaluator code as authority. Metadata is descriptive. If metadata and executable code differ, follow the executable meaning and state the disposition where it affects a checklist rule.
2. Expand the evaluator into literal, independently reviewable conditions. Preserve exact expressions, transformations, string formatting, suffix addition, fuzzy thresholds, equality rules, counts, set/row invariants, UI visibility settings, foreground package/activity requirements, branch logic, and helper/delegate semantics. Preserve surprising behavior exactly; never repair it by intuition. A phrase such as “the evaluator passes,” “integrity is valid,” or “the delegated check succeeds” is insufficient.
3. State native success and native failure using all three AndroidWorld layers: the raw `task.is_successful(env)` result, the `interaction_results.done` gate, and displayed success at `agent_successful > 0.5`. Do not omit or collapse a layer.
4. Reserve `undecided_if` only for missing, corrupt, contradictory, or unbound retained evidence. An ordinary raw-evaluator failure, `done=false`, or score at/below the threshold belongs in `fail_if`.
5. Compare every clause of the runtime goal against what the native evaluator actually enforces. Put each material unenforced or partially enforced clause in `stronger.additional_conditions`. Use an empty stronger list only when the source proves complete coverage.
6. Every rule must be decidable from retained post-run state, trace, screenshot, tool log, message, evaluator input/output, or file artifacts. Source files justify the drafted rule but are never run evidence. Do not require a final screenshot of transient state that the task itself replaces.
7. Do not prescribe an answer-key action sequence. A stronger condition may require a user-specified interaction method only when a retained trace can decide it.
8. Every support pointer path before `::` must be exactly `case_packet.md` or a path copied verbatim from `## Source Inventory`. Prefer the exact source file plus class/method/helper symbol after `::`. Never cite drafter workspace files, absolute paths, URLs, a leading `./`, or invented paths.
9. Cross-check all support pointers against the packet before returning. Each cited symbol or location must actually exist in the cited source section and support the specific text.
