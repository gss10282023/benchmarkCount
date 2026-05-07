# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `749`
- task_id: `749`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=749`

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
          "name": "project_site",
          "namespace_id": 2505,
          "template_name": "express",
          "visibility": "private"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 201,
        "url": "__GITLAB__/api/v4/projects"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
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
          "access_level": 30,
          "user_id": "2367,43,278"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 201,
        "url": "^__GITLAB__/api/v4/projects/\\d+/invitations$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
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
    "account_list": "primer, convexegg, vinta",
    "project_name": "project_site",
    "template": "NodeJS"
  },
  "intent": "Start a private project called \"project_site\" with NodeJS template and add primer, convexegg, vinta as members",
  "intent_template": "Start a private project called \"{{project_name}}\" with {{template}} template and add {{account_list}} as members",
  "intent_template_id": 2100,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 749
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "749",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=749",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "c873b82eaaf9f96b322f53faca334ea8f679f287ca1e4f2c3834653530cb860f",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=749"
  ],
  "task_id": "749"
}
```
