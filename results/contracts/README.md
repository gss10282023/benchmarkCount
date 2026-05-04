# Evidence Contracts

This directory is for draft, reviewed, locked, and superseded evidence contracts.
The gate is intentionally fail-closed: if `experiments/experiment_manifest.yaml`
references P0 `native_aligned` case units and no matching locked contracts exist,
`scripts/validate_contracts.py` exits non-zero.

Expected locked-contract format is JSON or YAML. Required fields include the
schema listed in `计划.md`: identity/version fields, native claim fields,
source support, drafter provenance, human review provenance, lock provenance,
and the canonical `contract_hash`.

Canonical hash rule:

```text
sha256(JSON(contract_without_contract_hash, sort_keys=True, separators=(",", ":")))
```

Operational commands:

```bash
python3 scripts/draft_contracts.py --manifest experiments/experiment_manifest.yaml --source-bundle official_sources.json --write-templates
python3 scripts/draft_contracts.py --manifest experiments/experiment_manifest.yaml --source-bundle official_sources.json --write-templates --call-llm
python3 scripts/review_contracts.py --input experiments/evidence_contracts/drafts --start --reviewer-id REVIEWER --overwrite
python3 scripts/review_contracts.py --input experiments/evidence_contracts/reviewed --finish --reviewer-id REVIEWER --review-action "checked source hierarchy and edited unsupported requirements" --overwrite
python3 scripts/lock_contracts.py --reviewed experiments/evidence_contracts/reviewed --reviewer-id REVIEWER --locked-by REVIEWER
python3 scripts/validate_contracts.py --manifest experiments/experiment_manifest.yaml --contracts experiments/evidence_contracts/locked
```

`stronger_measurement` claims must be mapped to a sidecar report, appendix, or
manifest view and must not be included in the native-aligned main envelope.
