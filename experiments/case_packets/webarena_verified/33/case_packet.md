# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `33`
- task_id: `33`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=33`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "distance": "1.4km",
            "hotel": "DoubleTree by Hilton Hotel Pittsburgh Airport"
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "distance": {
              "format": "distance",
              "type": "string"
            },
            "hotel": {
              "format": "location-name",
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
    "information": "shortest walking distance",
    "place": "Pittsburgh Airport",
    "retrieved_data_format_spec": "Return a list of objects with keys \"hotel\" (hotel name) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details",
    "target1": "Hilton hotel",
    "target2": "a supermarket"
  },
  "intent": "I will arrive at Pittsburgh Airport soon. Find a Hilton hotel in the vicinity, if available, and get me its name and the shortest walking distance to a supermarket from the hotel. Return a list of objects with keys \"hotel\" (hotel name) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "I will arrive at {{place}} soon. Find a {{target1}} in the vicinity, if available, and get me its name and the {{information}} to {{target2}} from the hotel. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 78,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 33
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "33",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=33",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "9424907fcdb82dfcca0e9d1139c9413d5cb36797a32f5fdcebb7aa58a9bfe27b",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=33"
  ],
  "task_id": "33"
}
```
