# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `587`
- task_id: `587`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=587`

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
          "detail": "Does the job",
          "nickname": "GamingEmma",
          "ratings[4]": "18",
          "title": "Ok I guess"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__SHOPPING__/review/product/post/id/101441/"
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
    "nickname": "GamingEmma",
    "num_star": 3,
    "product": "PS3 accessory",
    "review": "Does the job",
    "summary": "Ok I guess"
  },
  "intent": "Rate my recently purchased PS3 accessory with 3 stars using my nickname GamingEmma, with the summary \"Ok I guess\" and review \"Does the job\"",
  "intent_template": "Rate my recently purchased {{product}} with {{num_star}} stars using my nickname {{nickname}}, with the summary \"{{summary}}\" and review \"{{review}}\"",
  "intent_template_id": 194,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 587
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "587",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=587",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d5ca627091b2c6defa35ef3bb7fc128176874e1c7d12a665ed9a1e0b5e2d9d4c",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=587"
  ],
  "task_id": "587"
}
```
