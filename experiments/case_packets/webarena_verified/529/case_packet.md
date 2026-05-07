# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `529`
- task_id: `529`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=529`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": null,
        "status": "SUCCESS",
        "task_type": "MUTATE"
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
        "http_method": "POST",
        "post_data": {
          "comment": "^I\\s+need\\s+a\\s+refund[.\\s]+Order\\s*:\\s*#?\\s*0*157[.\\s]+Amount\\s*:\\s*(\\$\\s*)?122\\.05(\\s*\\$|\\s+dollars)?[.\\s]+Reason\\s*:\\s*It\\s+broke\\s+after\\s+three\\s+days\\s+of\\s+use\\.?$",
          "email": "emma.lopez@gmail.com",
          "form_id": "contact-form",
          "name": "Emma Lopez"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": -1,
        "url": "^http://.*/dummy_bin$"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    },
    {
      "decode_base64_query": false,
      "evaluator": "NetworkEventEvaluator",
      "expected": {
        "headers": null,
        "http_method": "POST",
        "post_data": null,
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 200,
        "url": "__SHOPPING__/contact/index/post"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": true
    }
  ],
  "instantiation_dict": {
    "product": "Stereo Sound System",
    "time": "Feb 2023"
  },
  "intent": "Fill out the contact us form with this refund message for the Stereo Sound System bought Feb 2023: \"I need a refund. Order: <order_id>. Amount: <amount>. Reason: It broke after three days of use.\" Leave the filled form ready for review and do not submit it.",
  "intent_template": "Fill out the contact us form with this refund message for the {{product}} bought {{time}}: \"I need a refund. Order: <order_id>. Amount: <amount>. Reason: It broke after three days of use.\" Leave the filled form ready for review and do not submit it.",
  "intent_template_id": 154,
  "revision": 2,
  "sites": [
    "shopping"
  ],
  "start_urls": [
    "__SHOPPING__"
  ],
  "task_id": 529
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "529",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=529",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "9ad009ee34c34db34ee415a555d33cbe542aa574d7a6db4e6331193fee7941fe",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=529"
  ],
  "task_id": "529"
}
```
