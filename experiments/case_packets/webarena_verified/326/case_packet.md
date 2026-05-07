# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `326`
- task_id: `326`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=326`

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
          "q": [
            "Canon photo printer"
          ]
        },
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__SHOPPING__/catalogsearch/result/"
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
    "product": "Canon photo printer",
    "sorting_order": "search relevance, from most to least"
  },
  "intent": "Pull up the page with all \"Canon photo printer\" listings sorted by search relevance, from most to least.",
  "intent_template": "Pull up the page with all \"{{product}}\" listings sorted by {{sorting_order}}.",
  "intent_template_id": 208,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 326
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "326",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=326",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "6272c7a6d93f4c75495b154d46cf69c3b805cb5af3d995e0f3dd37d32db68483",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=326"
  ],
  "task_id": "326"
}
```
