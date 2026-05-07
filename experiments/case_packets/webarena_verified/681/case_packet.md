# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `681`
- task_id: `681`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=681`

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
          "submission[body]": "193 commits already!",
          "submission[forum]": "^(10043|10018)$",
          "submission[mediaType]": "url",
          "submission[title]": "eriklindernoren/PyTorch-GAN",
          "submission[url]": "__GITLAB__/eriklindernoren/PyTorch-GAN"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "^__REDDIT__/submit/?.*$"
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
    "topic": "gan implementation"
  },
  "intent": "Find a GitLab repository related to gan implementation and create a new post in the discussion forum with the URL of the repository to the most relevant forum. Use the repository path as the post title and \"<number of commits> commit(s) already!\" as the post body.",
  "intent_template": "Find a GitLab repository related to {{topic}} and create a new post in the discussion forum with the URL of the repository to the most relevant forum. Use the repository path as the post title and \"<number of commits> commit(s) already!\" as the post body.",
  "intent_template_id": 116,
  "revision": 2,
  "sites": [
    "reddit",
    "gitlab"
  ],
  "start_urls": [
    "__REDDIT__",
    "__GITLAB__"
  ],
  "task_id": 681
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "681",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=681",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "f81de0391caf59eab1d1039e0ff92e0795fb772270758aa2ddf40d17de20cb42",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=681"
  ],
  "task_id": "681"
}
```
