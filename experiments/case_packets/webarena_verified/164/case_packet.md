# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `164`
- task_id: `164`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=164`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "Meh"
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
  "instantiation_dict": {},
  "intent": "Get all review titles with 2 stars or below for the product on the current page.",
  "intent_template": "Get all review titles with 2 stars or below for the product on the current page.",
  "intent_template_id": 136,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__/mineralogie-all-natural-lip-gloss-ruby-rose.html"
  ],
  "task_id": 164
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "164",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=164",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "5f5ff0e77739c898e3ad2d07182be09bb172e81da358aa9a05f32e6513ff46de",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=164"
  ],
  "task_id": "164"
}
```
