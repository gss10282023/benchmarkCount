# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `24`
- task_id: `24`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=24`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "NOT_FOUND_ERROR",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "type": "null"
      }
    }
  ],
  "instantiation_dict": {
    "description": "price being unfair"
  },
  "intent": "Get name(s) of reviewer(s) who mention price being unfair for the product on the current page",
  "intent_template": "Get name(s) of reviewer(s) who mention {{description}} for the product on the current page",
  "intent_template_id": 222,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__/haflinger-men-s-wool-felt-open-back-slippers-beige-550-peat-us-7.html"
  ],
  "task_id": 24
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "24",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=24",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "ac6864f85f226ce08bd9c1124a0c3ef1f32c07b5ea04a41463e82ba27a01fb78",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=24"
  ],
  "task_id": "24"
}
```
