# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `138`
- task_id: `138`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=138`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "1h 58min"
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
    "city1": "the big apple",
    "city2": "the city with the most authentic Philly cheesesteaks",
    "retrieved_data_format_spec": "Return the value as a string in HH:MM:SS format only, without any additional details"
  },
  "intent": "What is the estimated driving time between the big apple and the city with the most authentic Philly cheesesteaks? Return the value as a string in HH:MM:SS format only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "What is the estimated driving time between {{city1}} and {{city2}}? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 51,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 138
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "138",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=138",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "36e9b3e8ba89ad6ab1cd03f20fa58be15090365de39e17dfbea9356b1bbd7fb2",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=138"
  ],
  "task_id": "138"
}
```
