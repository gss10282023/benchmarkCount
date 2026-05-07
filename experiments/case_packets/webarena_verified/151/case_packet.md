# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `151`
- task_id: `151`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=151`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "4min"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "duration",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "location1": "CMU",
    "location2": "University of Pittsburgh",
    "retrieved_data_format_spec": "Return the value as a string in HH:MM:SS format only, without any additional details"
  },
  "intent": "What is the minimum travel time by car from CMU to University of Pittsburgh? Return the value as a string in HH:MM:SS format only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "What is the minimum travel time by car from {{location1}} to {{location2}}? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 36,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 151
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "151",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=151",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "5feca11a43a0a2dd1c8a9de6a5e067d17db7fc46213d9c28604d0f4d8f102b10",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=151"
  ],
  "task_id": "151"
}
```
