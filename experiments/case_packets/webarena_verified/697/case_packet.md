# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `697`
- task_id: `697`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=697`

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
          "product[color]": "50",
          "product[name]": "Swatch Smart Watch",
          "product[price]": "769.99",
          "product[quantity_and_stock_status][is_in_stock]": "1",
          "product[quantity_and_stock_status][qty]": "42",
          "product[status]": "1"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "^__SHOPPING_ADMIN__/catalog/product/save/type/simple/store/0/set/\\d+/back/edit$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        "isAjax"
      ],
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "color": "Blue",
    "price": "769.99",
    "product": "Swatch Smart Watch",
    "size": "a single size",
    "stock": "42"
  },
  "intent": "Add a simple product named \"Swatch Smart Watch\" with 42 in stock, available in a single size and color Blue, priced at $769.99 using the appropriate attribute set.",
  "intent_template": "Add a simple product named \"{{product}}\" with {{stock}} in stock, available in {{size}} and color {{color}}, priced at ${{price}} using the appropriate attribute set.",
  "intent_template_id": 256,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 697
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "697",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=697",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d41e9438a7b6063c8bc4bd23c8ecd4755c5468276852252b8431ada5ef9c8018",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=697"
  ],
  "task_id": "697"
}
```
