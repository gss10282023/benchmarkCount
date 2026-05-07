# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `29`
- task_id: `29`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=29`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          {
            "count": 0,
            "post_title": "How can I bring an HDMI cable from my pc downstairs to my TV upstairs?",
            "username": "ziostraccette"
          }
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "properties": {
            "count": {
              "type": "number"
            },
            "post_title": {
              "type": "string"
            },
            "username": {
              "type": "string"
            }
          },
          "type": "object"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "forum": "DIY",
    "retrieved_data_format_spec": "Return a list of objects with keys \"username\", \"post_title\", and \"count\""
  },
  "intent": "In the DIY forum, get the username and post title of the most recent post, and count the number of comments on that post that are not from the author and have more downvotes than upvotes. Return a list of objects with keys \"username\", \"post_title\", and \"count\".",
  "intent_template": "In the {{forum}} forum, get the username and post title of the most recent post, and count the number of comments on that post that are not from the author and have more downvotes than upvotes. {{retrieved_data_format_spec}}.",
  "intent_template_id": 33,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 29
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "29",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=29",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "d00995d4c85f549c445d650758b680f6d28449c84b39996a7bdcc3d60e8dee99",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=29"
  ],
  "task_id": "29"
}
```
