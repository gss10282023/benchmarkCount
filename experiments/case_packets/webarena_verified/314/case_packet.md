# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `314`
- task_id: `314`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=314`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "Shawn Allen",
          "Inayaili Le\u00f3n",
          "Aurora Pleguezuelo"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "attribute": "full names",
    "repo": "primer/design",
    "retrieved_data_format_spec": ""
  },
  "intent": "Get the full names of the top 3 contributors (by commit count) to primer/design repo",
  "intent_template": "Get the {{attribute}} of the top 3 contributors (by commit count) to {{repo}} repo{{retrieved_data_format_spec}}",
  "intent_template_id": 324,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 314
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "314",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=314",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "769f6005f559c1bac615e89c5ed733950eecbf99765512cd32ebeb3d98335c2e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=314"
  ],
  "task_id": "314"
}
```
