# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `51`
- task_id: `51`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=51`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "amount": 1700.84,
            "order_count": 7
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "amount": {
              "format": "currency",
              "type": "number"
            },
            "order_count": {
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
    "period": "over the past six months",
    "retrieved_data_format_spec": "Return an object with keys \"order_count\" (as integer) and \"amount\" (as number, e.g., 10.99) only, without any additional details"
  },
  "intent": "Today is June 12, 2023. Get how many complete orders I have over the past six months, and the total amount of money I spent (including shipping and handling fees). Return an object with keys \"order_count\" (as integer) and \"amount\" (as number, e.g., 10.99) only, without any additional details.",
  "intent_template": "Today is June 12, 2023. Get how many complete orders I have {{period}}, and the total amount of money I spent (including shipping and handling fees). {{retrieved_data_format_spec}}.",
  "intent_template_id": 197,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 51
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "51",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=51",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "572a653162e1a4344ce992c6ef47c526ba53c4e25436a55446035b5a36b5729a",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=51"
  ],
  "task_id": "51"
}
```
