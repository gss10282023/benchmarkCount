# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `15`
- task_id: `15`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=15`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          2
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
    "term": "best"
  },
  "intent": "Get the total number of reviews that our store received so far that mention term \"best\"",
  "intent_template": "Get the total number of reviews that our store received so far that mention term \"{{term}}\"",
  "intent_template_id": 288,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 15
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "15",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=15",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "f85b2f6b6e9750c844ef958c5907455a04f2804c8abdfc8012755117dbbfda2e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=15"
  ],
  "task_id": "15"
}
```
