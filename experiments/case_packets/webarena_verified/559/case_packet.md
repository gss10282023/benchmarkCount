# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `559`
- task_id: `559`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=559`

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
          "project[name]": "nolan_followers",
          "project[namespace_id]": "2505",
          "project[path]": "nolan_followers"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 302,
        "url": "__GITLAB__/projects"
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
        "post_data": {
          "$.actions[0].action": "^(update|create)$",
          "$.actions[0].content": "# nolan_followers\n\n- 1993\u20132003: Early career and breakthrough\n- 2003\u20132013: Widespread recognition\n- 2014\u20132019: Established Hollywood auteur\n- 2020\u2013present",
          "$.actions[0].file_path": "README.md",
          "$.actions[1].action": null,
          "branch": "main"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 201,
        "url": "__GITLAB__/api/v4/projects/byteblaze%2Fnolan_followers/repository/commits"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": {
        "properties": {
          "$.actions[0].content": {
            "format": "markdown",
            "type": "string"
          }
        },
        "type": "object"
      },
      "query_params_schema": null,
      "should_not_exist": false
    }
  ],
  "instantiation_dict": {
    "name": "nolan_followers",
    "topics": "career timeline headings of Christopher Nolan in order"
  },
  "intent": "Create a repository named nolan_followers with a README file containing career timeline headings of Christopher Nolan in order (use the provided wiki site to look up any needed information). Use the Web IDE to create the README. Structure it with the repository name as the main heading and a bulleted list of the film titles. Commit to the default branch.",
  "intent_template": "Create a repository named {{name}} with a README file containing {{topics}} (use the provided wiki site to look up any needed information). Use the Web IDE to create the README. Structure it with the repository name as the main heading and a bulleted list of the film titles. Commit to the default branch.",
  "intent_template_id": 87,
  "revision": 3,
  "sites": [
    "gitlab",
    "wikipedia"
  ],
  "start_urls": [
    "__GITLAB__",
    "__WIKIPEDIA__"
  ],
  "task_id": 559
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "559",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=559",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "50e7b8145fc4fe979a296f93db9c7b4081038e202070924ab5c3869ca35f42ee",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=559"
  ],
  "task_id": "559"
}
```
