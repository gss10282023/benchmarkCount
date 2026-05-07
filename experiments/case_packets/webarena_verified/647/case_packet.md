# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `647`
- task_id: `647`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=647`

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
          "submission[forum]": "10082",
          "submission[title]": "What could open-source LLMs help the technology field?"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": [
          "__REDDIT__/submit",
          "__REDDIT__/submit/technology"
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
    "forum": "technology",
    "model_type": "open-source LLMs",
    "title": "What could open-source LLMs help the technology field?"
  },
  "intent": "Post in technology forum with title \"What could open-source LLMs help the technology field?\"",
  "intent_template": "Post in {{forum}} forum with title \"{{title}}\"",
  "intent_template_id": 19,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 647
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "647",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=647",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "cc2ee68836878781a0cb5bb761583aa2362fd0c7a906b23b404c1b3feb048b51",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=647"
  ],
  "task_id": "647"
}
```
