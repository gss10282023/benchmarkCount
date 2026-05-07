# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `188`
- task_id: `188`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=188`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          365.42
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
    "retrieved_data_format_spec": "Return the value as a number (e.g., 10.99) only, without any additional details",
    "status": "marked as \"cancelled\""
  },
  "intent": "Get the total cost of my latest order marked as \"cancelled\". Return the value as a number (e.g., 10.99) only, without any additional details",
  "intent_template": "Get the total cost of my latest order {{status}}. {{retrieved_data_format_spec}}",
  "intent_template_id": 214,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 188
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "188",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=188",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "00fa741035353d34acc5819de788f9cb6b839283a66e49b91b0b795a872541de",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=188"
  ],
  "task_id": "188"
}
```
