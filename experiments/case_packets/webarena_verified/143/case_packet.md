# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `143`
- task_id: `143`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=143`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          260.69
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "currency",
          "type": "number"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "category": "home decoration",
    "retrieved_data_format_spec": "Return the value as a number (e.g., 10.99) only, without any additional details",
    "time": "during January 29, 2023"
  },
  "intent": "Return how much I spent on home decoration shopping during January 29, 2023 without considering shipping and handling fee. Return the value as a number (e.g., 10.99) only, without any additional details",
  "intent_template": "Return how much I spent on {{category}} shopping {{time}} without considering shipping and handling fee. {{retrieved_data_format_spec}}",
  "intent_template_id": 162,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 143
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "143",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=143",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "7c05331efbd7163f4a2ab02b92441c98f12150c61677a70a7f2c862f96a843c4",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=143"
  ],
  "task_id": "143"
}
```
