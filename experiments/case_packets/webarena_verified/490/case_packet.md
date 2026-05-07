# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `490`
- task_id: `490`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=490`

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
          "is_active": "1",
          "page_id": "5",
          "store_id[0]": "0",
          "title": "Secret"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__SHOPPING_ADMIN__/cms/page/save/back/edit"
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
    "heading": "Secret",
    "old_heading": "About us"
  },
  "intent": "Change the page title of \"About us\" page on my site to \"Secret\".",
  "intent_template": "Change the page title of \"{{old_heading}}\" page on my site to \"{{heading}}\".",
  "intent_template_id": 275,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 490
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "490",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=490",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d47cfa1e6741b5edc9885ac6a68f607ee7eb6e4ae030bc789dc55a7edd85ac75",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=490"
  ],
  "task_id": "490"
}
```
