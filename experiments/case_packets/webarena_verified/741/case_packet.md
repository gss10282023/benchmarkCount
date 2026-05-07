# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `741`
- task_id: `741`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=741`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "SUCCESS",
        "task_type": "NAVIGATE"
      },
      "ordered": false,
      "results_schema": {
        "type": "null"
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
        "url": "^.*/route/v1/.*/-71.0621475,42.3662922;-79.9427192,40.4441897.*$"
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
    "location": "Carnegie Mellon University",
    "sport_team": "Boston home NBA team",
    "time_phrase": ""
  },
  "intent": "View the route on the map from Carnegie Mellon University to the home stadium of Boston home NBA team. (Use the OSRM direction service and the provided wiki to look up any needed information and search both source and destination by coordinates from the place official page on the wiki.)",
  "intent_template": "View the route on the map from {{location}} to the home stadium of {{sport_team}}{{time_phrase}}. (Use the OSRM direction service and the provided wiki to look up any needed information and search both source and destination by coordinates from the place official page on the wiki.)",
  "intent_template_id": 94,
  "revision": 2,
  "sites": [
    "wikipedia",
    "map"
  ],
  "start_urls": [
    "__MAP__",
    "__WIKIPEDIA__"
  ],
  "task_id": 741
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "741",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=741",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "da866509e4e201b94d2325dc514d932ca84970c37c91ff7353b999794a9be412",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=741"
  ],
  "task_id": "741"
}
```
