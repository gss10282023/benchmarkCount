# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `328`
- task_id: `328`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=328`

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
        "headers": null,
        "http_method": "GET",
        "post_data": null,
        "query_params": {
          "product_list_order": [
            "price"
          ],
          "q": [
            " iphone 12 phone case"
          ]
        },
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__SHOPPING__/catalogsearch/result/index/"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        "^(?!q$|product_list_order$).+$"
      ],
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "product": "iphone 12 phone case",
    "sorting_order": "price"
  },
  "intent": "Pull up the page with all \"iphone 12 phone case\" listings sorted by price.",
  "intent_template": "Pull up the page with all \"{{product}}\" listings sorted by {{sorting_order}}.",
  "intent_template_id": 208,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 328
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "328",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=328",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d7d38fe2da325fedc577c54920763d461886b2949ebdd47b06815856bed0c7e0",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=328"
  ],
  "task_id": "328"
}
```
