# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `142`
- task_id: `142`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=142`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          68.51
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
    "category": "hair care and hair style",
    "retrieved_data_format_spec": "Return the value as a number (e.g., 10.99) only, without any additional details",
    "time": "during Jan 2023"
  },
  "intent": "Return how much I spent on hair care and hair style shopping during Jan 2023 without considering shipping and handling fee. Return the value as a number (e.g., 10.99) only, without any additional details",
  "intent_template": "Return how much I spent on {{category}} shopping {{time}} without considering shipping and handling fee. {{retrieved_data_format_spec}}",
  "intent_template_id": 162,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 142
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "142",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=142",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "bd17edf5457bba1a824f1cc0638e525f99e5958d86b9e6869687da376265784d",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=142"
  ],
  "task_id": "142"
}
```
