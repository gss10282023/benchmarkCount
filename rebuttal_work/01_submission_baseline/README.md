# Step 1 submitted baseline

This directory is the sole source of truth for the submitted 1,282-record universe.

Membership is explicit and fail-closed:

- AgentDojo, AppWorld, MiniWoB++, and tau3-retail each contribute the 300 rows named by their frozen submitted flat CSV.
- AndroidWorld contributes exactly the 41 cases in the public-package `MANIFEST.json`, expanded over Agent A and Agent B, for 82 records.
- The resulting benchmark counts are `300 + 82 + 300 + 300 + 300 = 1,282`; agent counts are A=441, B=441, C=400.
- Every row binds raw run, native evaluator, score, score manifest, checklist, and artifact manifest to both SHA-256 and the Git blob at the submission commit. The read-only `SUBMISSION_REPO` materializes all 7,692 referenced files.

`results/` was audited but is not an inclusion source. `legacy_results_crosswalk.csv` records the comparison: 7,610 decisive files are byte-identical; the 82 Android native-evaluator files differ only because the public package contains the submitted redacted form, which remains canonical. The exclusion ledger explicitly blocks the stale 81-row Android CSV, its off-selector extra score, retry/infra directories, 31 AppWorld xhigh rescores, old tables/macros, jobs, smoke runs, backups, and other working outputs.

Android post-submission work is separate: `androidworld_extension_contract.csv` contains exactly `remaining59×A/B = 118` plus `full100×C = 100`, or 218 unique target slots. `post_submission_extension_manifest.csv` has a header and zero active rows; Step 4B alone may append accepted slots.

The manifest-only rebuild command is:

```bash
make rebuild
```

The complete repeatable acceptance command is:

```bash
make verify
```

It runs formatting boundary tests, rebuilds the master table without directory discovery, recomputes all 7,692 decisive hashes from the read-only submission snapshot, verifies the recursive filesystem-immutable state of all three legacy scientific-input roots, checks both Android contracts, and confirms byte-identical output under two isolated Python interpreters. The locked result is `verification_report.json` with `status: pass`.
