# Candidate116 independent semantic-review proposals

This directory is deliberately separate from
`draft_generation/reviews/<case>/review.json`.  Files generated here are model
review proposals only.  They never satisfy the final human-review contract and
always carry `promotion_authorized: false`.

## Protocol

After the replacement 116-case draft wave and its automatic QC both pass, make
one immutable review prelock.  Supply the exact replacement draft prelock and
its matching QC root; the tool derives packet paths, packet flavor, case order,
generation id, and raw-wave path from those bindings.

```bash
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python \
  rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/scripts/prepare_semantic_review_prelock.py \
  --draft-prelock <NEW_DRAFT_PRELOCK_JSON> \
  --automatic-qc-root <MATCHING_AUTOMATIC_QC_ROOT>
```

The prelock command prints the exact snapshotted runner command.  Execute that
command; the locked configuration requires Codex CLI login auth, read-only
ephemeral sessions, and exactly six workers.  If interrupted, inspect retained
attempts and rerun the same command with `--resume`.

Then execute the snapshotted independent validator printed in the prelock's
`tool_bindings.independent_validator`, passing the same review prelock.  An
optional report may be written only beneath `review_generation/validation/`.

## Per-case output

Each completed case retains every attempt and a content-addressed selected
receipt.  The selected attempt binds:

- the exact prelocked case packet and raw YAML/JSON checklist;
- the raw draft generation sidecars and deterministic automatic-QC report;
- the review prompt, proposal schema, model-output schema, model/reasoning
  configuration, Codex binary/login provenance, response id, and token usage;
- the raw Codex JSONL event stream, stderr, reasoning summary, model body,
  normalized proposal, deterministic validation report, and receipt hashes.

The proposal checks identity, canonical runtime goal, effective evaluator
expansion, raw score/done/`>0.5` semantics, fail versus undecided, decisive
post-run artifacts, a requirement-by-requirement goal–evaluator/stronger matrix,
metadata conflict disposition, and every raw checklist support pointer.

## Human gate

The model may propose `accepted` or `rejected`; neither value is final.  A human
reviewer must inspect the packet, raw checklist, proposal, issues, and any
optional corrected checklist.  Only a separately authored
`androidworld_checklist_review/v1` under `draft_generation/reviews/<case>/` can
be considered by the promotion/freezing tool.
