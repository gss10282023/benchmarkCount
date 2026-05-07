# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `229`
- task_id: `229`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=229`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "max": 38.99,
            "min": 6.99
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "max": {
              "format": "currency",
              "type": "number"
            },
            "min": {
              "format": "currency",
              "type": "number"
            }
          },
          "type": "object"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "brand": "ugreen",
    "retrieved_data_format_spec": "Return an object with keys \"min\" and \"max\" (as numbers, e.g., 10.99) only, without any additional details"
  },
  "intent": "What is the price range for products from ugreen?. Return an object with keys \"min\" and \"max\" (as numbers, e.g., 10.99) only, without any additional details.",
  "intent_template": "What is the price range for products from {{brand}}?. {{retrieved_data_format_spec}}.",
  "intent_template_id": 370,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 229
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "229",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=229",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "bbefbee73f5761ada80f6dddb3ee57c890a247e6dd2e802d9347da605eddefc7",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=229"
  ],
  "task_id": "229"
}
```
