# AppWorld full-test extension v1

This namespace preserves the existing selected-100 AppWorld cohort and adds
exactly 485 previously unrun tasks:

- 68 remaining `test_normal` tasks;
- all 417 `test_challenge` tasks;
- 1,455 planned record slots (`485 × Agent A/B/C`).

The extension is an appendix/extension track. It does not replace the main P0
100-case manifest and normal/challenge results must remain separately reported.

## Frozen inputs

`frozen_scope.json` locks the two canonical, split-specific AppWorld data-version
hashes, existing selected-100
catalog and packet tree, AppWorld commit/package/data version, source tree,
Agent A/B/C configuration, the resolved contract-drafter execution protocol
(including prompt, schema, template, guardrails, and runner hashes), scorer protocol,
retry policy, and denominator policy.

`official_splits/appworld_selected_task_sources.json` is the independent
485-case catalog. Every item carries `task_id`, `dataset_name`, `source_ref`,
repository-relative `task_dir`, and the path/size/SHA-256 of all 19 official
task files.

## Rebuild commands

Run from the repository root:

```bash
PYTHONPATH=src python3 -m evidence_system.cli.build_appworld_extension --json

PYTHONPATH=src python3 -m evidence_system.cli.build_case_packets \
  --manifest experiments/appworld_full_test_extension_v1/experiment_manifest.json \
  --official-splits experiments/appworld_full_test_extension_v1/official_splits \
  --output-root experiments/appworld_full_test_extension_v1/case_packets \
  --source-mode local \
  --json

PYTHONPATH=src python3 -m evidence_system.cli.validate_appworld_extension \
  --packets-only \
  --json

PYTHONPATH=src python3 -m evidence_system.cli.build_case_packet_source_bundle \
  --manifest experiments/appworld_full_test_extension_v1/experiment_manifest.json \
  --case-packets-root experiments/appworld_full_test_extension_v1/case_packets \
  --output experiments/appworld_full_test_extension_v1/source_bundles/case_packet_source_bundle.json \
  --expected-count 485 \
  --expected-domain appworld \
  --allow-generated-contract-ids \
  --json

PYTHONPATH=src python3 -m evidence_system.cli.validate_appworld_extension \
  --write-report \
  --json
```

Full validation is read-only unless `--write-report` is passed. The last command
writes `provenance/acceptance_report.json` only after all
definition, packet, and bundle gates pass. The packet gate requires the exact
485 directory set and directory layout, 68/417 split counts, an exact
catalog-derived raw-manifest field set (no extra fields), exact identities and source pointers,
9,215 matching official-file hashes, parseable JSON/JSONL/evaluator Python,
and byte-identical packet re-rendering.

## Protected data

The AppWorld task corpus is protected data. The copied `raw_case` trees and
rendered `case_packet.md` files are derivatives and must remain
access-controlled; any public redistribution must follow AppWorld's encrypted
distribution requirement. These pre-run drafting inputs must not be exposed to
benchmark agents or scoring judges.
