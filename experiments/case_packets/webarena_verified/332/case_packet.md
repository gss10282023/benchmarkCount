# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `332`
- task_id: `332`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=332`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "month": "Jan",
            "total": 542.88
          },
          {
            "month": "Feb",
            "total": 912.5
          },
          {
            "month": "Mar",
            "total": 53.31
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "month": {
              "format": "month",
              "type": "string"
            },
            "total": {
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
    "retrieved_data_format_spec": "Return a list of objects with keys \"month\" (month name) and \"total\" (as a number, e.g., 10.99) only, without any additional details",
    "time": "each month from Jan to the March 31, 2023"
  },
  "intent": "Return the total amount I spent on shopping at One Stop Market each month from Jan to the March 31, 2023, excluding shipping. Return a list of objects with keys \"month\" (month name) and \"total\" (as a number, e.g., 10.99) only, without any additional details",
  "intent_template": "Return the total amount I spent on shopping at One Stop Market {{time}}, excluding shipping. {{retrieved_data_format_spec}}",
  "intent_template_id": 147,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 332
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "332",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=332",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d80415b66533f23b09635e45e6093833a262170bfe0f064c34c73ef6520a320b",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=332"
  ],
  "task_id": "332"
}
```
