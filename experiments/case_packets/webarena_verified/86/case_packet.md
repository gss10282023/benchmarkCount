# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `86`
- task_id: `86`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=86`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "29min"
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
    "hotel": "La Quinta Inn near the airport",
    "place": "Upitt",
    "retrieved_data_format_spec": "Return the value as a string in HH:MM:SS format only, without any additional details"
  },
  "intent": "From my stay at La Quinta Inn near the airport, what's the estimated driving time to reach Upitt? Return the value as a string in HH:MM:SS format only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "From my stay at {{hotel}}, what's the estimated driving time to reach {{place}}? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 64,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 86
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "86",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=86",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "e5ccec6d4067cb13c7a3d657919b5d217acadaf73ea782a8c5668fff9e6f2649",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=86"
  ],
  "task_id": "86"
}
```
