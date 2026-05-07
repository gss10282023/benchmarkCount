# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `2`
- task_id: `2`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=2`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          [
            "Digital Watch",
            "Band",
            "Stasis Ball",
            "Yoga Strap"
          ]
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
    "entity": "product type name(s)",
    "n": 1,
    "period": "Quarter 1 2022"
  },
  "intent": "Get the top-1 best-selling product type name(s) in Quarter 1 2022",
  "intent_template": "Get the top-{{n}} best-selling {{entity}} in {{period}}",
  "intent_template_id": 279,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 2
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "2",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=2",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "20b99899b881db341039816119b5ceffd553fc8b3331c36e064943d31585370c",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=2"
  ],
  "task_id": "2"
}
```
