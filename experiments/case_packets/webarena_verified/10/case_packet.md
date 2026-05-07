# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `10`
- task_id: `10`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=10`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "name": "Niagara Falls International Airport",
            "postcode": "14304",
            "state": "New York"
          },
          {
            "name": "Buffalo Niagara International Airport",
            "postcode": "14225",
            "state": "New York"
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "name": {
              "type": "string"
            },
            "postcode": {
              "type": "string"
            },
            "state": {
              "type": "string"
            }
          },
          "title": "full_address",
          "type": "object"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "airport_type": "US international airports",
    "radius": "60 km",
    "retrieved_data_format_spec": "Return a list of objects with keys \"name\", \"state\", and \"postcode\"",
    "start": "Niagara Falls"
  },
  "intent": "Get the name, state, and zip code of all US international airports that are within a driving distance of 60 km to Niagara Falls. Return a list of objects with keys \"name\", \"state\", and \"postcode\". (Use the OSRM direction service.)",
  "intent_template": "Get the name, state, and zip code of all {{airport_type}} that are within a driving distance of {{radius}} to {{start}}. {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 79,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 10
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "10",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=10",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "cb76b48f57fb9b996748b1dd63599e6c2f2627fafd1f486405e6c23a0ce76b5b",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=10"
  ],
  "task_id": "10"
}
```
