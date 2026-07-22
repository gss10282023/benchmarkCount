# Contract source bundles

`main_case_units_source_bundle.json` contains the validated drafter-input index
for the 300 currently selected P0 main-study evidence contracts.

The current bundle is `contract_source_bundle.v2`:

- it does not embed `visible_inputs`
- each source entry points to a local `case_packet.md`
- each source entry also points to `raw_case_manifest.json`

The case packets live under `experiments/case_packets/` and are materialized
from the fixed manifest plus official case sources under
`experiments/official_splits/`.

Before calling the LLM drafter, validate the bundle:

```bash
python scripts/draft_contracts.py \
  --manifest experiments/experiment_manifest.yaml \
  --source-bundle experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json \
  --agents configs/agents.yaml
```

This validation must pass before any `--call-llm` draft run.
