# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `82`
- task_id: `82`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=82`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "63min"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "duration",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "place_A": "Massachusetts Institute of Technology",
    "place_B": "Harvard University",
    "place_C": "Boston Logan International Airport",
    "retrieved_data_format_spec": "Return the value as a string in HH:MM:SS format only, without any additional details"
  },
  "intent": "What is the duration required to first walk from Massachusetts Institute of Technology to Harvard University, and then drive to Boston Logan International Airport? Return the value as a string in HH:MM:SS format only, without any additional details. (Use the OSRM direction service.)",
  "intent_template": "What is the duration required to first walk from {{place_A}} to {{place_B}}, and then drive to {{place_C}}? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 72,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 82
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "82",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=82",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "22ff3ae22059e3f12d002a7f66e518b7eaea573ada46a6aa199ae92997c3c51e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=82"
  ],
  "task_id": "82"
}
```
