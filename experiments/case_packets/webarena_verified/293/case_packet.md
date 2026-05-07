# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `293`
- task_id: `293`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=293`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "git@__SSH_HOST__:convexegg/super_awesome_robot.git"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "url",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "repo": "Super_Awesome_Robot",
    "retrieved_data_format_spec": "Return the URL only, without any additional details"
  },
  "intent": "Get the URL to clone Super_Awesome_Robot with SSH. Return the URL only, without any additional details.",
  "intent_template": "Get the URL to clone {{repo}} with SSH. {{retrieved_data_format_spec}}.",
  "intent_template_id": 329,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__"
  ],
  "task_id": 293
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "293",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=293",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "1ef6bba96900cd44277099852d43ea4a8eee9f9b3660f0bc40d21dd9c56b05ea",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=293"
  ],
  "task_id": "293"
}
```
