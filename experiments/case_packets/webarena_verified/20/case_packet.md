# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `20`
- task_id: `20`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=20`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "duration": "13min",
            "mode": "driving"
          },
          {
            "duration": "1hr 45min",
            "mode": "walking"
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "duration": {
              "format": "duration",
              "type": "string"
            },
            "mode": {
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
    "end": "Carnegie Mellon University",
    "retrieved_data_format_spec": "Return a list of objects with keys \"mode\" (driving or walking) and \"duration\" (in HH:MM:SS format) only, without any additional details",
    "start": "Randyland"
  },
  "intent": "Get the time for walking and driving route from Randyland to Carnegie Mellon University. Return a list of objects with keys \"mode\" (driving or walking) and \"duration\" (in HH:MM:SS format) only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "Get the time for walking and driving route from {{start}} to {{end}}. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 73,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 20
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "20",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=20",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "4c5446d349d163989dcd93aab9731b1b4da7577b24c0f48d6a6499f4dc6388ba",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=20"
  ],
  "task_id": "20"
}
```
