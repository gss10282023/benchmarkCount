# AndroidWorld pre-outcome checklist lock v2

This checklist is drafted and locked before any concrete agent outcome or per-record released-evaluator result is available. Treat the supplied case packet as the sole case-specific input. Do not infer, request, or refer to any agent trajectory, run success/failure, released-evaluator label, evidence score, or benchmark-conflict decision.

- State `native.user_goal` from the official task/user intent.
- Define the native criterion from the released evaluator/oracle and official runner semantics, but formulate `native.decisive_artifacts`, `success_if`, `fail_if`, and `undecided_if` so that the later Scorer can decide S/F/U independently from retained underlying execution evidence.
- A recorded `native_label`, `native_score`, `is_successful` scalar, released-evaluator output, episode success field, or equivalent summary result is non-decisive metadata. It must not be a decisive artifact and must not itself establish S or F. Use the underlying evaluator-visible state, completion gate, trace, database, filesystem, message, or other retained artifact instead.
- A retained `done=false` may establish native failure where the official runner formally gates it to failure. Missing evidence, evaluator/runtime exceptions, NaN, or the absence of a usable underlying observation are U unless other retained evidence independently establishes the native criterion or its negation.
- Keep official task or policy requirements that exceed the evaluator/oracle's native criterion out of the native rules. Add one to `stronger.additional_conditions` only when it has concrete, case-specific official source support and is reviewable from realistically retainable evidence.
- Prefer no stronger condition to any subjective, stylistic, generic, speculative, hidden-state, counterfactual, or extra-judge requirement.
- Do not make or encode a benchmark-conflict judgment. Conflict is a later, separate record-level review that requires retained artifacts and source pointers; neither native success nor stronger failure is sufficient by itself.
- If a model-visible compact packet lists a Source Inventory path but omits that path's full body from `Packet Source Files`, do not cite or rely on the omitted body. Use only embedded official source bodies and other embedded packet material.
