# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `123`
- task_id: `123`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=123`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "rating": 4,
            "title": "Good but not perfect"
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "rating": {
              "type": "number"
            },
            "title": {
              "type": "string"
            }
          },
          "type": "object"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "product": "Circe's products",
    "retrieved_data_format_spec": "Return a list of objects with keys \"title\" and \"rating\""
  },
  "intent": "Get title and rating for all reviews with 4 stars or above for Circe's products. Return a list of objects with keys \"title\" and \"rating\".",
  "intent_template": "Get title and rating for all reviews with 4 stars or above for {{product}}. {{retrieved_data_format_spec}}.",
  "intent_template_id": 250,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 123
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "123",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=123",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "1783efbe213fe8a0727c0deef8ab43481910c48ba23ce5558114c6ff2367d74a",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=123"
  ],
  "task_id": "123"
}
```
