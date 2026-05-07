# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `781`
- task_id: `781`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=781`

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
          "product[price]": 32.88
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "^__SHOPPING_ADMIN__/catalog/product/save/id/1573/type/simple/store/0/set/\\d+/back/edit$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        "isAjax"
      ],
      "last_event_only": true,
      "post_data_schema": {
        "properties": {
          "product[price]": {
            "format": "currency",
            "type": "number"
          }
        },
        "type": "object"
      },
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "action": "Increase",
    "amount": "37%",
    "config": "black fitness tshirts from Desiree with size XS"
  },
  "intent": "Increase the price of black fitness tshirts from Desiree with size XS by 37%",
  "intent_template": "{{action}} the price of {{config}} by {{amount}}",
  "intent_template_id": 742,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 781
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "781",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=781",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "8c1a7c3e2ba3ddd1770998225f945f69deabec7b173175476ea7142d200921ef",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=781"
  ],
  "task_id": "781"
}
```
