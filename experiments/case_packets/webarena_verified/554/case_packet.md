# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `554`
- task_id: `554`

## Source Inventory

- `derived/task.json`

## Packet Source Files

### `derived/task.json`

Source ref: `<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=554`

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
          "$.actions[0].action": "create",
          "$.actions[0].content": "{\"urls\": [\"__REDDIT__/f/movies/128825/scenes-in-film-that-feel-off-or-wrong-in-some-way-and-make\",\"__REDDIT__/f/movies/128824/disney-s-live-action-lilo-amp-stitch-movie-finds-its-lilo-in\",\"__REDDIT__/f/movies/128823/fantastic-four-movie-gets-new-writer-with-avatar-the-way-of\",\"__REDDIT__/f/movies/128822/can-someone-explain-what-made-steven-seagal-so-appealing-for\",\"__REDDIT__/f/movies/128821/ban-on-fetish-sex-depictions-in-film-should-end-australia\"]}",
          "$.actions[0].file_path": "movie_space/urls.json",
          "$.actions[1].action": null,
          "branch": "main"
        },
        "query_params": null,
        "response_content": null,
        "response_cookies": null,
        "response_status": 201,
        "url": "__GITLAB__/api/v4/projects/byteblaze%2Fgimmiethat.space/repository/commits"
      },
      "ignored_post_data_params_patterns": null,
      "ignored_query_params": null,
      "ignored_query_params_patterns": null,
      "last_event_only": true,
      "post_data_schema": {
        "properties": {
          "$.actions[0].content": {
            "format": "json",
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
    "directory": "movie_space",
    "forum": "movies",
    "gitlab_repo": "gimmiethat.space"
  },
  "intent": "Use the Web IDE to create a folder named movie_space in gimmiethat.space repo. Within it, create a file named urls.json that contains the full URLs of the 5 most recent posts from the movies forum on the discussion forum as a JSON object with a \"urls\" array. Write them in order from newest to oldest. Commit the changes to the default branch.",
  "intent_template": "Use the Web IDE to create a folder named {{directory}} in {{gitlab_repo}} repo. Within it, create a file named urls.json that contains the full URLs of the 5 most recent posts from the {{forum}} forum on the discussion forum as a JSON object with a \"urls\" array. Write them in order from newest to oldest. Commit the changes to the default branch.",
  "intent_template_id": 84,
  "revision": 2,
  "sites": [
    "gitlab",
    "reddit"
  ],
  "start_urls": [
    "__GITLAB__",
    "__REDDIT__"
  ],
  "task_id": 554
}
```

## Raw Source Provenance

```json
{
  "case_unit_id": "554",
  "copied_files": [
    "derived/task.json",
    "official/webarena-verified.json"
  ],
  "derived_files": [
    "derived/task.json"
  ],
  "domain": "webarena_verified",
  "file_sources": {
    "derived/task.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=554",
    "official/webarena-verified.json": "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json"
  },
  "official_files": [
    "official/webarena-verified.json"
  ],
  "packet_files": [
    "derived/task.json"
  ],
  "sha256_per_file": {
    "derived/task.json": "ac4dfbe4dfdbb9db6904b01136668792966d30618cd3e0dea692b7c5350092c4",
    "official/webarena-verified.json": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
  },
  "source_refs": [
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json",
    "<REPO_ROOT>/experiments/official_splits/webarena_verified_official_812.json#task_id=554"
  ],
  "task_id": "554"
}
```
