# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `266`
- task_id: `266`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=266`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "distance": "290km",
            "relation_id": 2176999
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
            "relation_id": {
              "type": "integer"
            }
          },
          "type": "object"
        },
        "type": "array"
      }
    },
    {
      "decode_base64_query": false,
      "evaluator": "NetworkEventEvaluator",
      "expected": {
        "headers": null,
        "http_method": "GET",
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "^.*/route/v1/.*/-68.2177005,44.3494709;-70.2545299,43.6599147.*$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        ".*"
      ],
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "city": "the largest city in Maine",
    "metric_phrase": "distance",
    "retrieved_data_format_spec": "Return a list of objects with keys \"relation_id\" (integer) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details",
    "travel_mode": "drive"
  },
  "intent": "Get the relation ID of the closest national park to the largest city in Maine and the distance to drive there. Return a list of objects with keys \"relation_id\" (integer) and \"distance\" (numeric value with unit km or m, e.g., 2.4km, 500m) only, without any additional details. (Use the OSRM direction service and the provided wiki to look up any needed information and search both source and destination by coordinates from the place official page on the wiki.)",
  "intent_template": "Get the relation ID of the closest national park to {{city}} and the {{metric_phrase}} to {{travel_mode}} there. {{retrieved_data_format_spec}}. (Use the OSRM direction service and the provided wiki to look up any needed information and search both source and destination by coordinates from the place official page on the wiki.)",
  "intent_template_id": 85,
  "revision": 4,
  "sites": [
    "wikipedia",
    "map"
  ],
  "start_urls": [
    "__MAP__",
    "__WIKIPEDIA__"
  ],
  "task_id": 266
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "266",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=266",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "311c9c1219aed84f5e41fd337f985ac8cea8a2f98a3685c28e4732bacf09d79c",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=266"
  ],
  "task_id": "266"
}
```
