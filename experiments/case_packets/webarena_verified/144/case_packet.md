# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `144`
- task_id: `144`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=144`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          0
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "type": "number"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "category": "food",
    "retrieved_data_format_spec": "",
    "time": "from January 15 to January 31 2023"
  },
  "intent": "Return how much I spent on food shopping from January 15 to January 31 2023 without considering shipping and handling fee. ",
  "intent_template": "Return how much I spent on {{category}} shopping {{time}} without considering shipping and handling fee. {{retrieved_data_format_spec}}",
  "intent_template_id": 162,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 144
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "144",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=144",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "fda07faa0c268e6c5a60dfa6a5aefbe7639325acce10dca6438a79fff5ad351c",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=144"
  ],
  "task_id": "144"
}
```
