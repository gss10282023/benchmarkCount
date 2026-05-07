# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `608`
- task_id: `608`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=608`

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
          "submission[forum]": "10030",
          "submission[title]": "safe and budget apartment to live"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": [
          "__REDDIT__/submit",
          "__REDDIT__/submit/washington"
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
    "question": "safe and budget apartment to live",
    "topic": "city lives in DMV area"
  },
  "intent": "Find a forum focused on topics related to city lives in DMV area, and post my question, \"safe and budget apartment to live\" there",
  "intent_template": "Find a forum focused on topics related to {{topic}}, and post my question, \"{{question}}\" there",
  "intent_template_id": 5,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 608
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "608",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=608",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "a0b604a8f7d06753c98a1465766e73d1aede5aa733ee20f3e8192fe4c03d1518",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=608"
  ],
  "task_id": "608"
}
```
