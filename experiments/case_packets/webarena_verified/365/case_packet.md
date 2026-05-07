# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `365`
- task_id: `365`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=365`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "2.2km"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "distance",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "location_address_1": "Carnegie Music Hall",
    "location_address_2": "UPMC Shadyside",
    "retrieved_data_format_spec": "Return the value as a string (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details"
  },
  "intent": "Measure distance between Carnegie Music Hall and UPMC Shadyside by walking. Return the value as a string (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "Measure distance between {{location_address_1}} and {{location_address_2}} by walking. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 58,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 365
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "365",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=365",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "e3e506723804683681966ee22f9e3f5bfc80c7704cef60f18c253509fd035a5a",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=365"
  ],
  "task_id": "365"
}
```
