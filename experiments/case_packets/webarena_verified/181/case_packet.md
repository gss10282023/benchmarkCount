# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `181`
- task_id: `181`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=181`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          false
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "type": "boolean"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "keyword": "theme editor",
    "retrieved_data_format_spec": "Return a boolean (true if closed, false if opened)"
  },
  "intent": "Get whether my latest created issue with theme editor in its title is closed. Return a boolean (true if closed, false if opened).",
  "intent_template": "Get whether my latest created issue with {{keyword}} in its title is closed. {{retrieved_data_format_spec}}.",
  "intent_template_id": 500,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 181
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "181",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=181",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "537be49d59b9973d329336259a33ecb5d47c8b73a0dd6c8f3f91966ca34d6d29",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=181"
  ],
  "task_id": "181"
}
```
