# AndroidWorld pre-outcome checklist lock

This checklist is being drafted before any concrete agent outcome or per-record released-evaluator result is available. Treat the supplied case packet as the sole case-specific input. Do not infer, request, or refer to any agent trajectory, run success/failure, released-evaluator label, evidence score, or benchmark-conflict decision.

- State `native.user_goal` from the official task/user intent.
- Define the native decision rules from the released evaluator/oracle semantics, using official policy and state schema only where needed to interpret evaluator-visible state.
- Keep official task or policy requirements that exceed the evaluator/oracle's native criterion out of the native rules. Add one to `stronger.additional_conditions` only when it has concrete, case-specific official source support and is reviewable from realistically retainable evidence.
- Prefer no stronger condition to any subjective, stylistic, generic, speculative, hidden-state, counterfactual, or extra-judge requirement.
- Do not make or encode a benchmark-conflict judgment. Conflict is a later, separate record-level review that requires retained artifacts and source pointers; neither native success nor stronger failure is sufficient by itself.
