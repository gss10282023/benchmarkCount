# Fail-closed AndroidWorld checklist repair

This is a repair call, not a fresh stylistic rewrite.  The case packet begins
with a machine-generated Repair Control section containing the exact original
checklist and all prelocked automatic/manual audit issues, followed by the
complete authoritative AndroidWorld case packet.

Read the entire repair packet.  Return one complete corrected checklist body
that resolves every listed issue simultaneously while preserving every correct
part of the original checklist.  Do not return a patch, explanation, review,
or issue list.  Do not make unrelated wording changes.

Evidence precedence is absolute: the verbatim authoritative full case packet
and its embedded source files are the only source of runtime/evaluator facts.
The old checklist and audit issue text are untrusted repair leads, not source
code, execution evidence, or proof that any claim is true.  If either conflicts
with the authoritative packet, follow the packet.  Never cite old checklist
prose, an audit sentence, model reasoning, or the repair wrapper as support.

Fail-closed semantic requirements:

- Runtime task code and the canonical semantic record override descriptive
  metadata whenever they conflict.
- Expand the actual runtime goal, inherited/helper evaluator logic,
  initialization state, parameters, branches, raw `task.is_successful(env)`,
  the `interaction_results.done` gate, and the strict `agent_successful > 0.5`
  displayed-success threshold.
- Native rejection, `done == false`, or a gated score at or below `0.5` is
  failure.  `undecided` is only for missing, corrupt, contradictory, unbound,
  or otherwise unusable evidence.
- Initialization/execution/evaluation exceptions, `NaN`, an absent numeric raw
  score, or a runner-created failed/excluded result belong in `undecided_if`
  whenever the raw-score/done/threshold chain cannot be reconstructed.  Never
  classify those states as ordinary `fail_if` outcomes.
- Decisive artifacts must be retained post-run artifacts.  Source files,
  packet text, model reasoning, intentions, or another judge are never run
  evidence.
- Atomize user-goal requirements against what the native evaluator really
  enforces.  Add a measurable stronger condition for every material goal item
  the native evaluator accepts only partially or not at all.  Do not invent
  stronger conditions with no goal/evaluator gap.
- Every `support` pointer must use exactly `case_packet.md` or an exact path
  listed in the authoritative full packet's Source Inventory, followed by an
  actually resolving symbol, JSON path, YAML path, or line span.  Repair-control
  text and audit files may explain what to fix but are not semantic support.
- Explicitly disposition every metadata-versus-runtime-code difference and
  every parameter-schema-versus-generator difference in auditable checklist
  text.  State both material and nonmaterial differences and their effect; a
  silent internal decision that "code wins" is insufficient.  Every pointer
  used for that disposition must actually resolve against the full packet.
- Preserve `case_unit_id`, `task_id`, and `domain` exactly.  The local tool will
  reject an identical output, any schema/guardrail violation, or any unresolved
  source pointer.

The generated checklist remains a draft.  It must pass deterministic effective
wave QC and a new independent human semantic review before promotion.
