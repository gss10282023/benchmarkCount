# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `116`
- task_id: `116`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=116`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "Dominic",
          "Trey",
          "Edmund",
          "Merrie",
          "Shaunte",
          "Teofila",
          "Carma",
          "Yan",
          "Valorie",
          "Mikkel",
          "Matthew",
          "Monroe",
          "Scotty",
          "Alexander",
          "Tracey",
          "Joey"
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
    "product": "tanks products"
  },
  "intent": "Return the customer nickname(s) who gave a rating of 3 stars or below for tanks products",
  "intent_template": "Return the customer nickname(s) who gave a rating of 3 stars or below for {{product}}",
  "intent_template_id": 245,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 116
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "116",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=116",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "b928887a07d0e8498d5a1301f543ddc4b41d3781459c8d41bbe0643a731f2701",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=116"
  ],
  "task_id": "116"
}
```
