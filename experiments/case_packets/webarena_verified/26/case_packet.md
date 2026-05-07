# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `26`
- task_id: `26`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=26`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "RemyRRemyR",
          "Bob in Vegas"
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
    "description": "complain of the customer service"
  },
  "intent": "Get name(s) of reviewer(s) who mention complain of the customer service for the product on the current page",
  "intent_template": "Get name(s) of reviewer(s) who mention {{description}} for the product on the current page",
  "intent_template_id": 222,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__/epson-workforce-wf-3620-wifi-direct-all-in-one-color-inkjet-printer-copier-scanner-amazon-dash-replenishment-ready.html"
  ],
  "task_id": 26
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "26",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=26",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "b95e0ddef4432b957add36c2faf5744c8ba6b8439743f0b998744119c0c9a2ab",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=26"
  ],
  "task_id": "26"
}
```
