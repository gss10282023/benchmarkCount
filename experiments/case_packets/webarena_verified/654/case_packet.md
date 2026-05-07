# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `654`
- task_id: `654`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=654`

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
        "http_method": "GET",
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__SHOPPING__/contact"
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
    "order_id": "161",
    "product": "bluetooth speaker"
  },
  "intent": "Fill the \"contact us\" form in the site for a refund on the bluetooth speaker I bought, stating that \"it broke after just three days of use\". Also, ensure to include the order number #161 and the product SKU. Don\"t submit yet, I will check.",
  "intent_template": "Fill the \"contact us\" form in the site for a refund on the {{product}} I bought, stating that \"it broke after just three days of use\". Also, ensure to include the order number #{{order_id}} and the product SKU. Don\"t submit yet, I will check.",
  "intent_template_id": 153,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 654
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "654",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=654",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "0fb83086d1cf0f25d20874f71bf6458e05e93eeb5e02a426bd79e891f1f6e6ff",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=654"
  ],
  "task_id": "654"
}
```
