# Results Directory

This directory is reserved for collected raw artifacts, scored metrics, generated table/figure data, appendix coverage, and reports.

The current scripts are conservative by design:

- no metric is fabricated from paper-source fallback macros;
- missing scored-manifest values are emitted as `NA` with a missing-data reason;
- numeric figure data must share provenance with table/metric data;
- strict gates are reported by `scripts/validate_results.py`.

Expected subdirectories are created by the scripts as needed.
