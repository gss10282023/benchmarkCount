# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `803`
- task_id: `803`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=803`

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
        "http_method": "POST",
        "post_data": {
          "group[name]": "webagent",
          "group[path]": "webagent"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/groups"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": [
        "serializer"
      ],
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    },
    {
      "decode_base64_query": false,
      "evaluator": "NetworkEventEvaluator",
      "expected": {
        "headers": null,
        "http_method": "POST",
        "post_data": {
          "user_id": "223,224"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 201,
        "url": "^__GITLAB__/api/v4/groups/\\d+/invitations$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": [
        "serializer"
      ],
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": {
        "properties": {
          "user_id": {
            "format": "string_list",
            "type": "string"
          }
        },
        "type": "object"
      },
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "members": "pandey2000, sayakpaul, sayakpaul",
    "name": "webagent"
  },
  "intent": "create a new group \"webagent\" with members pandey2000, sayakpaul, sayakpaul",
  "intent_template": "create a new group \"{{name}}\" with members {{members}}",
  "intent_template_id": 600,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 803
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "803",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=803",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d477b8697f7056ac4b888234e5a8c462a34ea93a86c3470cd2d1d7b0ffa08761",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=803"
  ],
  "task_id": "803"
}
```
