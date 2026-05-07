# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `726`
- task_id: `726`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=726`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "NOT_FOUND_ERROR",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "type": "null"
      }
    }
  ],
  "instantiation_dict": {
    "forum": "earthporn",
    "user": "jacyanthis"
  },
  "intent": "DisLike all submissions created by jacyanthis in forum earthporn",
  "intent_template": "DisLike all submissions created by {{user}} in forum {{forum}}",
  "intent_template_id": 1510,
  "revision": 2,
  "sites": [
    "reddit"
  ],
  "start_urls": [
    "__REDDIT__"
  ],
  "task_id": 726
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "726",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=726",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "800d3a99d1a05f221f99c1ab4cb67bd57d8a765098e22eadf15985b0b55b7b74",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=726"
  ],
  "task_id": "726"
}
```
