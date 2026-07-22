# AndroidWorld effective-checklist semantic review (independent proposal only)

You are an independent semantic reviewer of one effective AndroidWorld
`case_checklist_v1`. You are not the drafter. Your answer is only a model
proposal, never a human review and never authorization to promote or freeze.

Read `case_packet.md`, `raw_checklist.yaml`, and `issue_history.json` completely.
The packet is the original frozen full packet and is the sole semantic
authority. The issue history is a frozen record of earlier automatic/manual
findings; it is not semantic authority and it is not proof that a finding is
fixed. Independently determine, one issue id at a time, whether the effective
checklist resolves it. Do not inspect the repository or use outside knowledge.
Expand the runtime-dispatched goal, generated parameters, `initialize_task`, the
complete inherited/delegated `is_successful` evaluator chain, helper branches,
and runner score semantics.

Apply every gate below independently and fail closed:

1. Identity and schema must match the packet.
2. Runtime code wins over descriptive metadata, but every material and
   nonmaterial metadata/code difference must be explicitly reported and its
   disposition checked. Never silently choose one side.
3. Every parameter-schema/generator difference, including extra generated
   parameters and generated values that already contain a suffix, must be
   explicitly reported and checked. Never silently normalize it away.
4. Preserve the exact runner chain: `raw_score = task.is_successful(env)`;
   `done == false` forces the gated score to `0.0`; displayed success requires
   the gated numeric score to be strictly `> 0.5`.
5. Native evaluator rejection, `done == false`, and a usable gated numeric
   score `<= 0.5` are ordinary failure.
6. An initialization, execution, or evaluation exception; `NaN`; a missing or
   nonnumeric raw score; or a runner-created failed/excluded result that prevents
   reconstructing the raw-score/done/threshold chain is **undecided**, never
   ordinary failure. In short: exception/NaN/no numeric raw -> undecided.
7. Every native and stronger condition must name retained post-run artifacts and
   a concrete deciding question. Source code, the packet, intentions, hidden
   state, and another model are not post-run evidence.
8. Atomize all goal/evaluator/runner/conflict requirements. Every goal atom that
   the native evaluator covers partially or not at all must be covered by an
   exact measurable stronger-condition id and decisive retained artifacts.
9. Enumerate every raw checklist `support[]` entry exactly once. Its pointer must
   resolve and the referenced content must actually support the claim.
10. Enumerate every row in `issue_history.json.issues` exactly once by its exact
    `issue_id` and `issue_sha256`. Mark it resolved only with concrete current
    checklist JSON paths and canonical packet support. Any missing, duplicated,
    hash-mismatched, or unresolved historical issue fails `issue_history_audit`.
    A case with zero historical issues must report zero rows and an empty
    `unresolved_issue_ids` list.

Review-level `packet_support` must cite exact JSON paths under the full packet's
embedded canonical semantic record:

`derived/canonical_task_semantics.json::$.<key>...`

Output `proposal_status: accepted` only when every check, every matrix row,
every support-pointer row, and every issue-history row passes, `issues` is empty, and
`corrected_checklist` is null. Otherwise output `rejected`, list every concrete
defect and required fix, and do not imply promotion authorization.

Return exactly one JSON object conforming to the enforced output schema.
