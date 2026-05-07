# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `135`
- task_id: `135`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=135`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          1
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "type": "number"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "date": "January 3, 2023",
    "repo": "a11yproject.com",
    "user": "Eric and Kilian"
  },
  "intent": "How many commits did Eric and Kilian make to a11yproject.com on January 3, 2023?",
  "intent_template": "How many commits did {{user}} make to {{repo}} on {{date}}?",
  "intent_template_id": 322,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 135
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "135",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=135",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "5ab4ed68e77de61ae344e862df60c79a088a1e03ad72b27fe13291137fd3049e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=135"
  ],
  "task_id": "135"
}
```
