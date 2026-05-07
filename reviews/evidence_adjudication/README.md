# Evidence Adjudication Logs

This directory stores the human adjudication layer that sits after
LLM-assisted evidence scoring and before paper-ready aggregate results.

The workflow is:

1. Run the benchmark normally and retain artifacts.
2. Score each completed record with the locked case checklist.
3. Flag records for human review when they show a native/evidence disagreement,
   an Unknown verdict, a stronger-measurement downgrade, or a sampled audit
   trigger.
4. Human reviewers inspect the task, official evaluator output, retained
   artifacts, and score rationale.
5. Reviewers classify each flagged item as a benchmark/evaluator issue,
   scorer/checklist misalignment, evidence insufficiency, stronger-only issue,
   or pending adjudication.
6. Final paper tables are generated only after approved corrections are applied
   to the evidence scores. The audit summary remains as a transparency report
   describing how much human correction was needed.

## Files

- `audit_summary.csv`: one row per benchmark/domain. This is the paper-facing
  summary table source.
- `audit_items_tau3_retail.csv`: item-level tau3 retail adjudication ledger.
  Add one similarly named file per benchmark, e.g.
  `audit_items_agentdojo.csv`, `audit_items_appworld.csv`, and
  `audit_items_miniwob.csv`.
- `../../outputs/latex/audit_case_insights_tau3.tex`: selected appendix case
  insights. This file intentionally omits records whose only issue was our own
  scorer/checklist misalignment.
- `../tau3_disagreement_audit/README.md`: human-readable tau3 case notes.
- `../miniwob_human_audit/README.md`: human-readable MiniWoB audit decisions.

## Item-Level Schema

Each benchmark-specific item ledger should use these columns:

| Column | Meaning |
|---|---|
| `benchmark` | Benchmark/domain key. |
| `case_unit_id` | Case unit identifier in the released package. |
| `agent_id` | Agent name or anonymized agent id. |
| `layer` | `native` or `stronger`. |
| `trigger` | Why the record was flagged, e.g. `released_native_conflict`, `unknown`, `nativeS_stronger_downgrade`. |
| `released_label` | Released benchmark label when available. |
| `native_verdict` | Current native evidence verdict before human correction. |
| `stronger_verdict` | Current stronger-measurement verdict when applicable. |
| `human_audit_label` | Reviewer's substantive classification. |
| `recommended_action` | How the cleaned score should be updated or preserved. |
| `adjudication_status` | `preliminary`, `accepted`, `corrected`, or `pending`. |
| `final_native_verdict` | Filled after score correction. Empty while preliminary. |
| `final_stronger_verdict` | Filled after score correction. Empty while preliminary. |
| `evidence_summary` | One-sentence evidence basis. |
| `source_paths` | Paths or line pointers used during review. |

## Summary Schema

`audit_summary.csv` uses these columns:

| Column | Meaning |
|---|---|
| `benchmark` | Benchmark/domain key. |
| `completed_records` | Number of completed records scored. |
| `llm_scored_records` | Number of records with an LLM-assisted score file. |
| `human_reviewed_records` | Number of flagged or sampled records reviewed by humans. |
| `accepted_without_score_change` | Reviewed records whose LLM-assisted judgment was substantively accepted. |
| `scorer_or_checklist_corrections` | Records where human review found the scorer/checklist too strict or too lenient. |
| `benchmark_or_evaluator_issues` | Records exposing released benchmark/evaluator bugs or reward-wiring conflicts. |
| `evidence_insufficient_native` | Native records left Unknown due insufficient stored evidence. |
| `stronger_only_issues` | Reviewed records where only the stronger-measurement layer failed or was Unknown. |
| `pending_adjudication` | Records requiring another human decision before final scoring. |
| `notes` | Short interpretation for the paper or appendix. |
