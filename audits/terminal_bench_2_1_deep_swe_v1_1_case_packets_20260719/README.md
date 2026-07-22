# Terminal-Bench 2.1 and DeepSWE v1.1 case-packet audit

Audit date: 2026-07-19

## Conclusion

All 202 expected case packets passed the source-fidelity and outcome-blindness
audit:

| Benchmark | Expected | Passed | Failed |
|---|---:|---:|---:|
| Terminal-Bench 2.1 | 89 | 89 | 0 |
| DeepSWE v1.1 | 113 | 113 | 0 |
| **Total** | **202** | **202** | **0** |

No case-content mismatch was found. Within the packet system's declared
storage boundary, each packet is a faithful representation of its official
case: task identity and instruction, task configuration, evaluator/verifier
contract, state/environment construction sources, artifact schema, and source
provenance are present and source-bound. Public agent outcomes and released
per-record evaluator results were not inputs to packet construction or this
audit.

This conclusion does not mean that every upstream byte is duplicated in each
packet. Reference solutions are intentionally excluded from packet bytes and
retained only as controller-side path/size/SHA-256 metadata. Terminal-Bench
binary inputs and one allowlisted oversized text fixture are likewise bound by
metadata rather than copied. Those are controlled representation choices, not
missing or reconstructed case semantics.

## Checks performed

For every Terminal-Bench 2.1 case, the audit verifies:

- exact packet/agent-input agreement with the official instruction;
- exact parsed `task.toml` agreement and case identity;
- byte-for-byte equality of every materialized UTF-8 source against a fresh
  official Harbor revision-6 export, with exact path/size/SHA-256 agreement for
  every non-materialized source;
- required source membership and exact raw/Markdown inventory agreement;
- verifier entry-point presence;
- solution-byte exclusion and metadata-only binding;
- Harbor revision-6 task source references, with no job/trial references;
- absence of per-record released labels, trial names, and outcomes; and
- agreement among the per-case manifest, root index, all 89 Harbor package
  digests, and the reconstructed 946-file canonical source tree.

For every DeepSWE v1.1 case, the audit verifies:

- exact task identity, instruction, and parsed `task.toml` agreement;
- byte-for-byte equality of every non-solution official source file against
  the pinned Git task tree;
- exact hash/size metadata for both protected solution files, with no solution
  bytes materialized;
- consistent repository and base-commit references across `task.toml`, grader
  configuration, environment Dockerfile, and `pre_artifacts.sh`;
- exact grader projection: all fail-to-pass IDs, pass-to-pass count and
  canonical-list hash, grade format, report paths, and decision semantics;
- presence of the official test patch and the separate-verifier/model-patch
  contract;
- exact raw/Markdown source inventory and root source-lock joins; and
- an explicit outcome-blind contract that excludes per-record trial contents
  and released evaluator values from drafting and evidence scoring.

## Informational findings

- The official DeepSWE source contains two seven-character base commit values
  and one 39-character value. These were not normalized: all relevant official
  files agree on the exact values, so the packets preserve them verbatim.
- DeepSWE's full `tests/config.json` is retained byte-for-byte. To keep the
  rendered Markdown tractable, it lists every fail-to-pass ID but binds very
  large pass-to-pass lists by count and SHA-256; the raw JSON remains the
  authoritative source.
- Terminal-Bench's binary files, one oversized fixture, and protected
  solutions are metadata-bound as described above.

These findings are not benchmark conflicts and do not change native or
stronger-measurement criteria.

## Reproduce

From the repository root, with an official DeepSWE checkout at the pinned
commit:

```bash
.venv/bin/python \
  audits/terminal_bench_2_1_deep_swe_v1_1_case_packets_20260719/audit_case_packets.py \
  --terminal-source-dir /srv/benchmark-sources/terminal-bench-2-1 \
  --deep-source-dir /srv/benchmark-sources/deep-swe
```

The command rewrites these machine-readable results:

- `summary.json`: corpus-level validation and findings;
- `audit_records.jsonl`: all per-case checks and their Boolean results; and
- `audit_report.csv`: compact 202-row review table.

The audit intentionally stops before agent outcomes and released per-record
evaluator results. Those are acquired only after checklists are locked and are
handled by the later evidence-scoring and disagreement-review stages.
