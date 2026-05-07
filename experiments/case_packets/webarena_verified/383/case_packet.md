# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `383`
- task_id: `383`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=383`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "hotel": "Hyatt Regency Pittsburgh International Airport",
            "supermarkets": [
              "Giant Eagle",
              "ALDI"
            ]
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "hotel": {
              "format": "location-name",
              "type": "string"
            },
            "supermarkets": {
              "items": {
                "format": "location-name",
                "type": "string"
              },
              "type": "array"
            }
          },
          "type": "object"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "retrieved_data_format_spec": "Return a list of objects with keys \"hotel\" and \"supermarkets\""
  },
  "intent": "I am arriving at Pittsburgh Airport. Find if there is a Hyatt hotel nearby. If there is, get me its name and the names of any supermarkets that are within 15 minutes driving from the hotel. Return a list of objects with keys \"hotel\" and \"supermarkets\". (Use the OSRM direction service.)",
  "intent_template": "I am arriving at Pittsburgh Airport. Find if there is a Hyatt hotel nearby. If there is, get me its name and the names of any supermarkets that are within 15 minutes driving from the hotel. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 782,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 383
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "383",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=383",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "9e6579537823bf0117ca4d63243faf92d54fe65151e4d4817c7156d66a8b7dcb",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=383"
  ],
  "task_id": "383"
}
```
