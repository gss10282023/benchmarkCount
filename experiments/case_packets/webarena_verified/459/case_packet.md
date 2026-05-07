# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `459`
- task_id: `459`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=459`

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
          "product[price]": "62.10"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "^__SHOPPING_ADMIN__/catalog/product/save/id/237/type/(simple|configurable)/store/0/set/\\d+/back/edit$"
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
    "action": "Reduce",
    "amount": "10%"
  },
  "intent": "Reduce the price of the product on the current page by 10%",
  "intent_template": "{{action}} the price of the product on the current page by {{amount}}",
  "intent_template_id": 247,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__/catalog/product/edit/id/237/"
  ],
  "task_id": 459
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "459",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=459",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "7d445686714db8b828c907c40d3faf406f7d6897263a6cfe5fbcb514d7b97a45",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=459"
  ],
  "task_id": "459"
}
```
