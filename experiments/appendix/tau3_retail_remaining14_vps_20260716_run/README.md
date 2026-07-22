# tau3 retail remaining-14 VPS run evidence

This directory is the immutable evidence sidecar for the 2026-07-16 collection on
VPS `45.76.20.117`, namespace `tau3-retail-remaining14-vps-20260716`.

## Outcome and scope

- Planned and completed: 14 cases x 3 agents = 42 canonical runs.
- Scheduler ceiling and observed maximum: 2 concurrent jobs.
- Canonical native rewards: 35 rewards of `1.0`, 7 rewards of `0.0`.
- Artifact acceptance: 42/42 passed after a read-only independent audit and a
  second cross-check of the two internal-retry cases.
- Formal scoring eligibility: **false**. These are accepted raw benchmark
  collections, but the checklists are still validated drafts rather than formally
  reviewed and locked contracts.

The canonical results are stored at
`results/namespaces/tau3-retail-remaining14-vps-20260716/`. The repository's
existing `results/jobs` tree is protected by an immutable flag, so the 42 job
specifications are preserved under `jobs/` in this sidecar instead of changing
that protected tree.

## Evidence map

- `inputs/`: exact run-bound copies of the original manifest, amended run
  manifest, agent configuration, VPS infrastructure configuration, and source
  bundle.
- `jobs/`: all 42 planned job specifications.
- `monitoring/`: plan/input acceptance, supervisor state, resource and remote
  monitoring, anomaly ledgers, artifact audits, orphan-attempt preservation, and
  retry diagnostics.
- `provenance/`: checked-in and isolated runtime adapter snapshots plus the exact
  patch between them.
- `scripts/`: the supervisor, monitoring, recovery, repair, and persisted-run
  validation programs used for this collection.
- `bundle_inventory.json`: SHA-256 inventory for the persisted evidence and
  canonical result files.
- `final_acceptance.json`: final machine-readable acceptance report.
- `release_checksums.sha256`: detached SHA-256 checksums for the inventory and
  final acceptance report.

## Documented non-blocking anomalies

- Agent C cases 104 and 55 each had one Tau2 internal simulation end with
  `infrastructure_error` after an empty DeepSeek message. Tau2 retried internally;
  each selected `used` simulation completed with native reward `1.0`. Failed
  simulation files remain immutable, hash-indexed diagnostics and are excluded
  from the decisive artifact manifests.
- The first interactive controller was closed when the active Codex terminal call
  was steered. Remote work was not killed. Orphan native/controller attempts were
  preserved, cases 104 and 85 were rerun under the durable supervisor because the
  first controller artifact set was incomplete, and all canonical slots finished.
- A detached `nohup` controller was reaped before launching a benchmark attempt;
  execution resumed in `screen`.
- Tau2/litellm could not map cost telemetry for Agent A/C in 30 task logs. Native
  conversations and rewards were unaffected; monetary cost data is incomplete.
- The first resource-monitor SSH probe had a quoting error and was corrected in
  the next sample. It did not affect benchmark execution.

No HTTP authentication/billing, rate-limit, 5xx, timeout, traceback, OOM, or
remaining Tau2-process condition was found in the terminal acceptance checks.
