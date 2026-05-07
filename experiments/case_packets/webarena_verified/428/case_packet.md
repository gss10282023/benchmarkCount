# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `428`
- task_id: `428`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=428`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "SUCCESS",
        "task_type": "NAVIGATE"
      },
      "ordered": false,
      "results_schema": {
        "type": "null"
      }
    },
    {
      "decode_base64_query": false,
      "evaluator": "NetworkEventEvaluator",
      "expected": {
        "headers": null,
        "http_method": "GET",
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__MAP__/relation/2279034"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        ".*"
      ],
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "description": "the undergrad college of the person who developed the Nash equilibrium"
  },
  "intent": "On the map site, view the info page for the undergrad college of the person who developed the Nash equilibrium (use the provided wiki site to look up any needed information).",
  "intent_template": "On the map site, view the info page for {{description}} (use the provided wiki site to look up any needed information).",
  "intent_template_id": 371,
  "revision": 2,
  "sites": [
    "wikipedia",
    "map"
  ],
  "start_urls": [
    "__MAP__",
    "__WIKIPEDIA__"
  ],
  "task_id": 428
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "428",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=428",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "8ecc1e991347ce434945705a60a8679dc7a9d0878c37dc6af45e8d8ef2f701fe",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=428"
  ],
  "task_id": "428"
}
```
