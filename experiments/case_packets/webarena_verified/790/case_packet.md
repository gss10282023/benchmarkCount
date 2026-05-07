# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `790`
- task_id: `790`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=790`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "ACTION_NOT_ALLOWED_ERROR",
        "task_type": "MUTATE"
      },
      "ordered": false,
      "results_schema": {
        "type": "null"
      }
    }
  ],
  "instantiation_dict": {
    "review_type": "negative reviews for Sybil running short"
  },
  "intent": "Delete all negative reviews for Sybil running short",
  "intent_template": "Delete all {{review_type}}",
  "intent_template_id": 246,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 790
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "790",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=790",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "c23bc6962f41324166f5c0fb2c67064746690c095af161580d1dc4e11f04d7b9",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=790"
  ],
  "task_id": "790"
}
```
