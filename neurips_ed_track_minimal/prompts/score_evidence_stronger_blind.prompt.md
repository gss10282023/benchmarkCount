You are performing the **independent stronger-measurement evidence stage** for
one AppWorld record.

Read `./checklist.yaml` and the retained files under `./evidence/`.  Use
`./evidence_index.txt` only to navigate; never cite it.

This stage is independent of both the released evaluator label and the native
evidence verdict.  Neither is available.  Do not infer, request, search for, or
output either one.  A native success or failure must not change how any stronger
condition is judged.

The output schema lists every locked `stronger.additional_conditions` id in
checklist order.  Emit exactly one condition check for each id:

- `supported`: retained evidence establishes the condition.
- `contradicted`: retained evidence establishes that the condition is false.
- `undecided`: retained evidence establishes neither side.

Judge every condition independently, including when another condition is
contradicted or undecided.  Do not invent conditions and do not turn missing
evidence into support or contradiction.

For every condition check, cite:

- its exact `checklist.yaml::stronger.additional_conditions[i]` pointer, and
- at least one concrete **post-run execution-evidence** pointer under
  `evidence/run/**` that supports the chosen status (including `undecided`).

Official case/runtime files define the condition but do not establish what
happened in this record.  Keep criterion sources distinct from post-run evidence.

Every pointer must be verified and use
`<relative_path>::<json_path|yaml_path|line_span|symbol>`.  Plain text and JSONL
files require a real one-based line span.  Never cite a case-packet source as
post-run evidence, `evidence_index.txt`, a non-existent file, or a released
label/result field.

Do not output an aggregate verdict.  A deterministic local process derives it
only from the condition checks: all supported -> S; any contradicted -> F;
otherwise -> U.  When no stronger conditions exist this model stage is skipped
and the local result is NA.

Follow the supplied output schema exactly and output JSON only.
