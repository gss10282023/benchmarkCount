# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `534`
- task_id: `534`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=534`

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
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/users/lahwaacz/follow.json"
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
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/users/koush/follow.json"
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
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/users/vinta/follow.json"
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
    "account_list": "[\"Jakub Klinkovsk\u00fd\", \"Koushik\", \"Vinta Chen\"]"
  },
  "intent": "Follow [\"Jakub Klinkovsk\u00fd\", \"Koushik\", \"Vinta Chen\"] on Gitlab",
  "intent_template": "Follow {{account_list}} on Gitlab",
  "intent_template_id": 330,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 534
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "534",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=534",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "ae66612a06391480151d386682f7d9d1181493a7267ef60b4ad170762b4dfca2",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=534"
  ],
  "task_id": "534"
}
```
