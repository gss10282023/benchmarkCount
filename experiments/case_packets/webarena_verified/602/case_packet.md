# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `602`
- task_id: `602`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=602`

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
          "submission[forum]": "10073",
          "submission[title]": "places for new drivers to learn driving in pittsburgh"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": [
          "__REDDIT__/submit",
          "__REDDIT__/submit/pittsburgh"
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
    "question": "places for new drivers to learn driving in pittsburgh"
  },
  "intent": "Post my question with the title \"places for new drivers to learn driving in pittsburgh\", in a forum where I'm likely to get an answer",
  "intent_template": "Post my question with the title \"{{question}}\", in a forum where I'm likely to get an answer",
  "intent_template_id": 3765,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 602
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "602",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=602",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "34249b6974abae83afd8c196fe7125c9b4a9fa5d153b84ad1edfc8abe91ada5c",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=602"
  ],
  "task_id": "602"
}
```
