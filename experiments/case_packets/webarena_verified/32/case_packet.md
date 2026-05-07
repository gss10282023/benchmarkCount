# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `32`
- task_id: `32`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=32`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "distance": "2km",
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
    "information": "walking distance",
    "place": "Pittsburgh Airport",
    "retrieved_data_format_spec": "Return a list of objects with keys \"hotel\" (hotel name) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details",
    "target1": "Hilton hotel",
    "target2": "the nearest supermarket own by a local company"
  },
  "intent": "I will arrive at Pittsburgh Airport soon. Find a Hilton hotel in the vicinity, if available, and get me its name and the walking distance to the nearest supermarket own by a local company from the hotel. Return a list of objects with keys \"hotel\" (hotel name) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "I will arrive at {{place}} soon. Find a {{target1}} in the vicinity, if available, and get me its name and the {{information}} to {{target2}} from the hotel. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 78,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 32
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "32",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=32",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "88f6a7519e4e82e4e443a59b68de16c359b315ad67e7cd98cdc94fa73c9a223e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=32"
  ],
  "task_id": "32"
}
```
