# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `421`
- task_id: `421`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=421`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "SUCCESS",
        "task_type": "MUTATE"
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
        "http_method": "PUT",
        "post_data": {
          "availability": "busy",
          "clear_status_after": null,
          "message": "Resting due to leg injury."
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__GITLAB__/api/v4/user/status"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "status": "Resting due to leg injury"
  },
  "intent": "Set my gitlab status as Resting due to leg injury.",
  "intent_template": "Set my gitlab status as {{status}}.",
  "intent_template_id": 361,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 421
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "421",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=421",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "b277f2d4820537637a7c6c2c2304e71b9c93fdee297cfd40b2fb396788ee1eb7",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=421"
  ],
  "task_id": "421"
}
```
