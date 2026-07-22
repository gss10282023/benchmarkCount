You are performing the **native, outcome-blind evidence-scoring stage** for one
AppWorld record.

Read `./checklist.yaml` and the retained files under `./evidence/`.  Use
`./evidence_index.txt` only to navigate; never cite it.

The released evaluator label and result-bearing component evaluator outputs are
intentionally absent.  Do not infer, request, search for, or output a released
label.  Decide only whether the retained non-verdict evidence establishes each
locked native registered-test condition.

## Required per-test decisions

The output schema lists every locked `[appworld_test_*]` id in checklist order.
Emit exactly one `test_checks` entry for each id:

- `supported`: the retained evidence establishes that registered test's locked
  success condition.
- `contradicted`: the retained evidence establishes that registered test's
  locked failure condition.
- `undecided`: the retained evidence does not establish either side.

Judge every registered test independently.  Do not turn missing evidence into
success or failure.  An agent-caused invalid action, timeout, tool misuse, or
abort may support `contradicted` only when the locked rule and retained evidence
establish that it makes the registered test fail.

Keep criterion sources and execution evidence distinct.  Official files under
`evidence/official/**` and `evidence/frozen_semantics/**` define what the test
means; they do not establish what happened in this record.  For each test check,
cite:

- its matching checklist rule (`native.success_if[i]` for `supported`,
  `native.fail_if[i]` for `contradicted`, or a locked
  `native.undecided_if[i]` rule for `undecided`), and
- the relevant official criterion source where the rule depends on released
  helper semantics, and
- at least one concrete **post-run execution-evidence** pointer under
  `evidence/run/**` that supports the chosen status (including `undecided`).

Apply the exact frozen runtime helper semantics.  In particular, a raw database
mutation inventory or `model_hashes.json` entry is not equivalent to the released
`ModelCollectionPair.changed_model_names`, `changed_records`, or
`changed_field_names` result.  Respect their include/ignore behavior and the
default exclusions of `supervisor.Task`, `admin.PaymentCard`, and
`amazon.BrowsedProduct` when the official source says they apply.

Every pointer must be verified and use
`<relative_path>::<json_path|yaml_path|line_span|symbol>`.  Plain text and JSONL
files require a real one-based line span.  Never cite a case-packet source as
post-run evidence, `evidence_index.txt`, a non-existent file, or a released
label/result field.

Do not output an aggregate verdict.  A deterministic local process derives it
after validating all test checks: all supported -> S; any contradicted -> F;
otherwise -> U.

Follow the supplied output schema exactly and output JSON only.
