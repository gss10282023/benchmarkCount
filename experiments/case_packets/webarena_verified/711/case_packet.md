# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `711`
- task_id: `711`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=711`

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
      "decode_base64_query": true,
      "evaluator": "NetworkEventEvaluator",
      "expected": {
        "headers": null,
        "http_method": "GET",
        "post_data": null,
        "query_params": {
          "from": [
            "07/5/2021"
          ],
          "report_type": [
            "created_at_order"
          ],
          "to": [
            "05/31/2023"
          ]
        },
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__SHOPPING_ADMIN__/reports/report_product/viewed/filter"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": [
        "^(?!report_type$|from$|to$).*$"
      ],
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": {
        "properties": {
          "from": {
            "items": {
              "format": "date",
              "type": "string"
            },
            "type": "array"
          },
          "report_type": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "to": {
            "items": {
              "format": "date",
              "type": "string"
            },
            "type": "array"
          }
        },
        "type": "object"
      },
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "article": "a",
    "end_date": "May 31, 2023",
    "start_date": "July 5, 2021",
    "type": "product view"
  },
  "intent": "Show the product view report from July 5, 2021 to May 31, 2023.",
  "intent_template": "Show the {{type}} report from {{start_date}} to {{end_date}}.",
  "intent_template_id": 271,
  "revision": 2,
  "sites": [
    "shopping_admin"
  ],
  "start_urls": [
    "__SHOPPING_ADMIN__"
  ],
  "task_id": 711
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "711",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=711",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "3fcacb7991756bf9a73811878e376bb785810205091863a05ed4b018b35af446",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=711"
  ],
  "task_id": "711"
}
```
