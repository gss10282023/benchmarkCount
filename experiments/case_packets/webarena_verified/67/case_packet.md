# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `67`
- task_id: `67`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=67`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "The Hobbit",
          "A Christmas Carol"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "description": "the book titles, exactly as they appear in the post description,",
    "filter_criterion": "recommend exactly one book",
    "forum": "Books",
    "number": 10,
    "retrieved_data_format_spec": ""
  },
  "intent": "Among the top 10 hottest posts in the \"Books\" forum, get the book titles, exactly as they appear in the post description, from those that recommend exactly one book.",
  "intent_template": "Among the top {{number}} hottest posts in the \"{{forum}}\" forum, get {{description}} from those that {{filter_criterion}}.{{retrieved_data_format_spec}}",
  "intent_template_id": 17,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 67
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "67",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=67",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "fc2e23b9b55821f12313c1786d67c279f8475e2b4af565b19c2465beb7ff8f33",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=67"
  ],
  "task_id": "67"
}
```
