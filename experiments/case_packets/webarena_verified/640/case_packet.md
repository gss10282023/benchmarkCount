# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `640`
- task_id: `640`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=640`

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
          "submission[body]": "virtual meetup for book reading on March 15th",
          "submission[forum]": "10037",
          "submission[title]": "book reading Meet up!"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": [
          "__REDDIT__/submit",
          "__REDDIT__/submit/books"
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
    "date": "March 15th",
    "forum": "f/books",
    "interest": "book reading"
  },
  "intent": "Post a notice in f/books titled \"book reading Meet up!\". Set post details to \"virtual meetup for book reading on March 15th\"",
  "intent_template": "Post a notice in {{forum}} titled \"{{interest}} Meet up!\". Set post details to \"virtual meetup for {{interest}} on {{date}}\"",
  "intent_template_id": 16,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 640
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "640",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=640",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "ce49583bfd223b89df4a6684c446596998bce17ed903353fc4ee7305a508bad3",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=640"
  ],
  "task_id": "640"
}
```
