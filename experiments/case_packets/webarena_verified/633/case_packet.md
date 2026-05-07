# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `633`
- task_id: `633`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=633`

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
          "submission[body]": "Hey, looking for good running pants under $500, any suggestions?",
          "submission[forum]": "10080",
          "submission[title]": "running pants recommendations?"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": [
          "__REDDIT__/submit",
          "__REDDIT__/submit/sports"
        ]
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
    "category": "running pants",
    "forum": "f/sports",
    "price": "$500"
  },
  "intent": "Create a post in f/sports. Title it \"running pants recommendations?\" and in post details ask \"Hey, looking for good running pants under $500, any suggestions?\"",
  "intent_template": "Create a post in {{forum}}. Title it \"{{category}} recommendations?\" and in post details ask \"Hey, looking for good {{category}} under {{price}}, any suggestions?\"",
  "intent_template_id": 15,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 633
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "633",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=633",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "59a9d8865e7ad7ad9c8f3dfae09af1c5f6a6d75d67e1c65793f3b4dc09286860",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=633"
  ],
  "task_id": "633"
}
```
