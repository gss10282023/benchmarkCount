# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `650`
- task_id: `650`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=650`

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
          "reply_to_submission_59421[comment]": "I am a big fan of the bookorg"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__REDDIT__/f/books/59421/-/comment"
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
    "comment_prefix": "my comment ",
    "content_description": "I am a big fan of the bookorg",
    "location": "on this page",
    "position_description": "the post"
  },
  "intent": "Reply to the post on this page with my comment \"I am a big fan of the bookorg\"",
  "intent_template": "Reply to {{position_description}} {{location}} with {{comment_prefix}}\"{{content_description}}\"",
  "intent_template_id": 23,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__/f/books/59421/friendly-reminder-bookshop-org-exists"
  ],
  "task_id": 650
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "650",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=650",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "2be5855d4eeb1c2b17e2dfc21bd9beda350319d1e477610d8856b93e7532d597",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=650"
  ],
  "task_id": "650"
}
```
