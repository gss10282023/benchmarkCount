# AndroidWorld Benchmark-Conflict Audit

The authoritative result is the strict v2 re-audit under
`benchmark_conflict_audit_strict_v2/`.

- Confirmed benchmark conflicts in the previously flagged set: **0 records / 0 cases**.
- Retracted v1 false positives: **36 records / 12 cases**.
- Benchmark-owned descriptive `task_metadata.json` defects: **12 cases**.
- Confirmed runtime task/target/evaluator/reward conflicts in that set: **0**.
- Evidence-score rerun required because of this correction: **no**.

The v1 audit incorrectly promoted precomputed metadata-difference flags directly
to confirmed conflicts. Its files are retained only for provenance under
`benchmark_conflict_audit/superseded_v1_false_positive/` and must not be used as
results.

See `benchmark_conflict_audit_strict_v2/README.md` for the reviewed case table
and `benchmark_conflict_audit_strict_v2/strict_reaudit_summary.json` for the
machine-readable result.
