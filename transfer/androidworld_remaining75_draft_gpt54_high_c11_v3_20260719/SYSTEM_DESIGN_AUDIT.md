# AndroidWorld remaining-75 draft generation and system-design audit

## Final decision

PASS. The reviewed set contains exactly the 75 AndroidWorld cases that were absent from the pre-existing 41-case canonical draft set. Every selected checklist was produced by the VPS `neurips_ed_track_minimal` draft path with Codex CLI, `gpt-5.4`, `reasoning_effort=high`, and read-only sandboxing. No selected checklist was manually edited.

The reviewed 75-case set has:

- 75/75 successful generated drafts;
- 75/75 canonical schema and source-pointer validations passing;
- 0 blocking mechanical issues and 0 mechanical review warnings;
- 0 semantic-lint issues and 0 semantic-lint warnings;
- 52 cases with at least one stronger-measurement condition;
- 73 stronger-measurement conditions reviewed in total;
- 0 score outputs and no AndroidWorld score invocation in this work.

## Pre-outcome lock and inputs

- The 75 case IDs are unique, sorted, disjoint from the original 41 drafts, and their union with those 41 IDs exactly equals the 116 official AndroidWorld case-packet directories.
- Each uploaded input has a model-visible `case_packet.md` and complete retained `raw_case` source tree.
- The model-visible inputs were scanned for concrete agent names, AndroidWorld run-result paths, native evaluator result sidecars, and other outcome-bearing artifacts before submission; the scan passed.
- Four exceptionally large recipe packets used a documented compact model-visible form. Only a very large derived canonical-semantics body was omitted; the source inventory, embedded official sources, and complete retained `raw_case` tree were preserved.
- VPS inputs were hash-verified after upload and then made root-owned/group-readable and read-only before or immediately after process start.

## Generation provenance

All accepted sources used the same model configuration: Codex CLI, `gpt-5.4`, high reasoning, maximum regular/oversized concurrency 11, read-only sandbox, and token attempts 12,000/16,000/20,000.

The final per-case selection is:

- V3: 65 cases;
- V2: 4 cases;
- case-specific V4 repair: 6 cases.

The selection is recorded in `FINAL_SELECTION.json` and `FINAL_SELECTION_RECEIPT.json`. V2/V3/V4 output directories were copied without changing checklist content. The four V2 selections remove V3 overreach or restore a supported condition that V3 omitted. The six V4 selections were regenerated with case-specific completeness requirements where both prior versions omitted at least one official task/evaluator gap.

Earlier V1 outputs are superseded and audit-only because manual review found decision rules that could refer to `is_successful` or equivalent released-summary fields. Those outputs were not selected. V2/V3 candidates with unsupported stronger conditions or incomplete stronger coverage were likewise not selected.

## Native S/F/U audit

For every selected checklist:

- native success and native failure are stated from official AndroidWorld runner and released evaluator/oracle semantics;
- decisive rules use underlying retained completion, trace, UI, database, filesystem, message, clipboard, or app-state evidence;
- `native_label`, `native_score`, `is_successful`, evaluator-output summaries, and episode-success summaries are not decisive evidence;
- official `done=false` runner gating may establish native failure;
- missing/unavailable underlying observations, exceptions, NaN, unreadable evidence, or unresolved ambiguity map to U unless other retained evidence independently decides the native claim;
- the retained released-evaluator label is not used to decide checklist S/F/U;
- no concrete Agent A/B/C outcome or per-record AndroidWorld run result appears in the checklist.

## Stronger-measurement audit

Every retained stronger condition was checked for all of the following:

- concrete, case-specific support in the official dispatched/runtime goal, task, or policy sources embedded in the packet;
- a real gap beyond the native evaluator/oracle criterion, such as exact text versus fuzzy matching, strict integer formatting versus numeric casting/tolerance, complete unique title sets, explicit order, named source/app provenance, export contents, copy-versus-move semantics, or table-wide deduplication;
- realistically retainable decisive artifacts with resolvable packet source pointers;
- no subjective quality preference, generic best practice, hidden-state demand, invented initial-state transition, unsupported final-state persistence, unused metadata-template requirement, or incidental serialization detail.

Stronger results remain separate from native S/F/U. No checklist encodes benchmark conflict, and neither native S nor stronger F is treated as sufficient for a conflict judgment.

## Integrity and canonical integration

- V3 remote result manifest SHA-256: `515eae9e5df29372dcbaf07dc164e134fb91887dd4107f1121d34b2e1eb00403` (1,085 verified files).
- V4 repair remote result manifest SHA-256: `5187231a516d9b13add41c8c9071f0f0e6a6df8a98b817dfdfafd095236f7454` (131 verified files).
- Final reviewed staging manifest SHA-256: `5aff034fd81d9f0d2b630decdaacf4162a6ff94b46f454114082732153dfffa4` (1,142 files including the two synthesized batch provenance files).
- Canonical new-75 manifest SHA-256: `09e7eef6b5b0f51bccbde1b128362e49d80d836779ec400fdc1960b79007807c` (1,140 per-case files).
- Original canonical 41-case manifest SHA-256: `c2bcd6895baa6220cec3cd927de19bc7a0b7506e5a7011add04aed0fa47e1089` (587 files), rechecked after integration with every hash unchanged.
- Canonical AndroidWorld draft directory after integration: 116 case directories and 116 `checklist.yaml` files, exactly matching the 116 official packet IDs, with no missing or extra case.
- All 75 new canonical `llm_call.json` records match `codex_cli / gpt-5.4 / draft / androidworld / high / codex_login`.
- The canonical tree and its `results` parents were restored to the immutable `uchg` state after integration.

The canonical directory retains its historical name `androidworld_full100`, but now contains the complete 116-case AndroidWorld draft set.
