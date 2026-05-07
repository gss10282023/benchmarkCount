# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `441`
- task_id: `441`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=441`

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
          "_method": "put",
          "branch_name": "main",
          "content": "^<\\!doctype html>.*<head>.*<title>GIVE ME SPACE</title>.*</head>.*</html>$",
          "file_path": "index.html",
          "original_branch": "main"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/byteblaze/gimmiethat.space/-/update/main/index.html"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": null,
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "target_branch": "the default branch",
    "title": "GIVE ME SPACE"
  },
  "intent": "Update and commit (to the default branch) the website code for the current project using the simple online file editor to change the browser tab title to \"GIVE ME SPACE\"",
  "intent_template": "Update and commit (to {{target_branch}}) the website code for the current project using the simple online file editor to change the browser tab title to \"{{title}}\"",
  "intent_template_id": 308,
  "revision": 2,
  "sites": [
    "gitlab"
  ],
  "start_urls": [
    "__GITLAB__/byteblaze/gimmiethat.space"
  ],
  "task_id": 441
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "441",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=441",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "c419c701abc4468661753bf203ece651c32377ba595fb02b95a32e17bf29249e",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=441"
  ],
  "task_id": "441"
}
```
