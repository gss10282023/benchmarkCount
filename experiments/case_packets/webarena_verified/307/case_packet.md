# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `307`
- task_id: `307`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=307`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          5
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
    "period": "on April 7th 2022",
    "user": "Nic Chan"
  },
  "intent": "How many commits did Nic Chan make on April 7th 2022 in the current repository?",
  "intent_template": "How many commits did {{user}} make {{period}} in the current repository?",
  "intent_template_id": 321,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__/a11yproject/a11yproject.com"
  ],
  "task_id": 307
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "307",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=307",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "990c22b47a2655bb27e0748c41a3407b8281d51e4f281de0430159ac99b47e8e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=307"
  ],
  "task_id": "307"
}
```
