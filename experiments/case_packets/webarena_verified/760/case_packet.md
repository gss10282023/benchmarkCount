# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `760`
- task_id: `760`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=760`

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
        "headers": {
          "Cookie": "^(?!.*_osm_directions_engine=fossgis_osrm_(?:bicycle|foot)).*$"
        },
        "http_method": "GET",
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "^.*/route/v1/.*/-75.4716115,40.6022552;-74.4041622,40.0757384.*$"
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
    "city1": "Allentown, PA",
    "city2": "the city where my E-commerce customer Amanda Kim lives",
    "view_type": "route and driving time"
  },
  "intent": "Show on the map the route and driving time from Allentown, PA to the city where my E-commerce customer Amanda Kim lives. (Use the OSRM direction service.)",
  "intent_template": "Show on the map the {{view_type}} from {{city1}} to {{city2}}. (Use the OSRM direction service.)",
  "intent_template_id": 42,
  "revision": 2,
  "sites": [
    "map",
    "shopping_admin"
  ],
  "start_urls": [
    "__MAP__",
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 760
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "760",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=760",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "21fbd16a4305089b7cc4bd3011dd4a4c4bea9d46910b5f89193b1e1823407955",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=760"
  ],
  "task_id": "760"
}
```
