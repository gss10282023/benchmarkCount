# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorCreateNote",
    "domain": "androidworld",
    "group": "extra16",
    "selection_rank": 105,
    "task_id": "MarkorCreateNote"
  },
  "integrity": {
    "semantic_record_sha256": "8b396db3b4b6ff57cd9e460908824c74353802807a0cb060081730edb60bf998",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "46463310502816e39c99115de9613184afd673c0a3f71d82e959169d57699f33",
    "source_commit": "d9c569f764b3a5629321858de03ff653d0f24056"
  },
  "schema_version": "androidworld_compact_draft_packet/v2",
  "source_context": {
    "available_post_run_artifact_types": [
      "post_state",
      "trace",
      "screenshot",
      "tool_log",
      "message",
      "native_evaluator_input",
      "native_evaluator_output",
      "file"
    ],
    "contract_template": {
      "claim_scope": "native_aligned"
    },
    "evaluator_description": {
      "canonical_module": "android_world.task_evals.single.markor",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.markor",
            "qualname": "MarkorCreateNote",
            "source_ref": {
              "ast_sha256": "5e3c11bc0f8d57eae3ff6990a53a9fed6913112e3462522b8b7351632beb6bca",
              "end_line": 449,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "371e743ed5c25f17866470888b4542b17046cf4263116b2671bb2ba37ab9304e",
              "start_line": 415,
              "symbol": "MarkorCreateNote"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.markor",
            "qualname": "Markor",
            "source_ref": {
              "ast_sha256": "ab836071c307a07af660b9cf4c8137b17fd2bb2ebb401ed3ff494a88f838de8e",
              "end_line": 66,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "e4bb63aa31ab515f465187b23e197af8bc908d74878f677b51372f1b92c27a24",
              "start_line": 57,
              "symbol": "Markor"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.task_eval",
            "qualname": "TaskEval",
            "source_ref": {
              "ast_sha256": "85d1a56897097bc400580d972badbaf66e2063a3fb9ddf45bfa65bfe92d05f09",
              "end_line": 190,
              "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
              "path": "android_world/task_evals/task_eval.py",
              "snippet_sha256": "555d49d2ef6e2fdd5d52484234181bdb3f7d874ac66bb5e068d01403f050351b",
              "start_line": 30,
              "symbol": "TaskEval"
            }
          },
          {
            "canonical_androidworld_source": false,
            "qualname": "ABC",
            "runtime_reported_module": "abc",
            "source_ref": null
          },
          {
            "canonical_androidworld_source": false,
            "module": "builtins",
            "qualname": "object",
            "source_ref": null
          }
        ],
        "runtime_reported_module": "android_world.task_evals.single.markor",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
            "ast_sha256": "5e3c11bc0f8d57eae3ff6990a53a9fed6913112e3462522b8b7351632beb6bca",
            "end_line": 449,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateNote",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "371e743ed5c25f17866470888b4542b17046cf4263116b2671bb2ba37ab9304e",
            "start_line": 415
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self.create_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "MarkorCreateNote",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
              "end_line": 440,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "acffeadfdbba4c06927750314dcd591e02a87cb99f3d1021c615068a2aaf68f6",
              "start_line": 438,
              "symbol": "MarkorCreateNote.is_successful"
            }
          },
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self._check_is_initialized"
            ],
            "direct_parameter_reads": [],
            "owner_class": "TaskEval",
            "owner_module": "android_world.task_evals.task_eval",
            "source_ref": {
              "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
              "end_line": 180,
              "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
              "path": "android_world/task_evals/task_eval.py",
              "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
              "start_line": 166,
              "symbol": "TaskEval.is_successful"
            }
          }
        ],
        "runner_score_semantics": {
          "display_success_threshold": "agent_successful > 0.5",
          "done_gate": "task_successful if interaction_results.done else 0.0",
          "source_ref": {
            "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
            "end_line": 289,
            "file_sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
            "path": "android_world/suite_utils.py",
            "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
            "start_line": 223,
            "symbol": "suite_utils._run_task"
          },
          "task_raw_score": "task.is_successful(env)"
        },
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
            "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
            "end_line": 440,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateNote.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "acffeadfdbba4c06927750314dcd591e02a87cb99f3d1021c615068a2aaf68f6",
            "start_line": 438
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
            "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
            "end_line": 180,
            "owner_module": "android_world.task_evals.task_eval",
            "owner_qualname": "TaskEval.is_successful",
            "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
            "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
            "start_line": 166
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
            "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
            "end_line": 289,
            "owner_module": "android_world.suite_utils",
            "owner_qualname": "suite_utils._run_task",
            "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
            "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
            "start_line": 223
          }
        ]
      },
      "is_successful": {
        "branches": [],
        "live_evaluator_execution_performed": false,
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self.create_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "MarkorCreateNote",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
              "end_line": 440,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "acffeadfdbba4c06927750314dcd591e02a87cb99f3d1021c615068a2aaf68f6",
              "start_line": 438,
              "symbol": "MarkorCreateNote.is_successful"
            }
          },
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self._check_is_initialized"
            ],
            "direct_parameter_reads": [],
            "owner_class": "TaskEval",
            "owner_module": "android_world.task_evals.task_eval",
            "source_ref": {
              "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
              "end_line": 180,
              "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
              "path": "android_world/task_evals/task_eval.py",
              "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
              "start_line": 166,
              "symbol": "TaskEval.is_successful"
            }
          }
        ],
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
            "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
            "end_line": 440,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateNote.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "acffeadfdbba4c06927750314dcd591e02a87cb99f3d1021c615068a2aaf68f6",
            "start_line": 438
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
            "ast_sha256": "4ba02bae85e87232a171f4ab6decd0f081113181a5d2fcbd220a205512f58e16",
            "end_line": 180,
            "owner_module": "android_world.task_evals.task_eval",
            "owner_qualname": "TaskEval.is_successful",
            "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
            "snippet_sha256": "cb4c4fd2a9f4efa9fe8fb8328f459b54febf84903006338ae246acd0c445e098",
            "start_line": 166
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
            "ast_sha256": "6287c8b53ca1ea7313f4a186e885a27263c51c622f46921cbe7cc4433a04edaa",
            "end_line": 289,
            "owner_module": "android_world.suite_utils",
            "owner_qualname": "suite_utils._run_task",
            "sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b",
            "snippet_sha256": "b24c573174d61b7642dd5dd746911d21c904d793e37582c91e5972a73d634062",
            "start_line": 223
          }
        ]
      },
      "task_class": "MarkorCreateNote"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self.create_file_task.initialize_task",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "MarkorCreateNote",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "a287b16c379c4bbc0f673973cc9404e77448ac88c553510f7ec4d1ab81ec37d1",
            "end_line": 436,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "60d7ef70bd5fc8272b434e8649d0e261fc8ee61d3c3bef17c7961be2e3ac06b8",
            "start_line": 434,
            "symbol": "MarkorCreateNote.initialize_task"
          }
        },
        {
          "branch_node_count": 0,
          "direct_calls": [
            "file_utils.clear_directory",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "Markor",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "645a8166b07e880454139eafae321d41ea4188dbcc7245b602a56e86f1a3edbb",
            "end_line": 62,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "c8d6d0037a19a9d990983f29dcb9d874dfc04ffe5389b1c4114bcacc60f71344",
            "start_line": 60,
            "symbol": "Markor.initialize_task"
          }
        },
        {
          "branch_node_count": 2,
          "direct_calls": [
            "RuntimeError",
            "logging.info",
            "random.seed",
            "self._initialize_apps",
            "self.initialize_device_time",
            "self.params.get"
          ],
          "direct_parameter_reads": [
            "seed"
          ],
          "owner_class": "TaskEval",
          "owner_module": "android_world.task_evals.task_eval",
          "source_ref": {
            "ast_sha256": "789c520bbfefb2cf815434042709e7d9d74585ebb19c2598d02dfe9c38769b1c",
            "end_line": 157,
            "file_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
            "path": "android_world/task_evals/task_eval.py",
            "snippet_sha256": "51c8fe9ebb14bc1362b24c3c53691dc666b9eaf949e8e6dc7251472e335f8c47",
            "start_line": 142,
            "symbol": "TaskEval.initialize_task"
          }
        }
      ],
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "a287b16c379c4bbc0f673973cc9404e77448ac88c553510f7ec4d1ab81ec37d1",
          "end_line": 436,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateNote.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "60d7ef70bd5fc8272b434e8649d0e261fc8ee61d3c3bef17c7961be2e3ac06b8",
          "start_line": 434
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "645a8166b07e880454139eafae321d41ea4188dbcc7245b602a56e86f1a3edbb",
          "end_line": 62,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "Markor.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "c8d6d0037a19a9d990983f29dcb9d874dfc04ffe5389b1c4114bcacc60f71344",
          "start_line": 60
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
          "ast_sha256": "789c520bbfefb2cf815434042709e7d9d74585ebb19c2598d02dfe9c38769b1c",
          "end_line": 157,
          "owner_module": "android_world.task_evals.task_eval",
          "owner_qualname": "TaskEval.initialize_task",
          "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
          "snippet_sha256": "51c8fe9ebb14bc1362b24c3c53691dc666b9eaf949e8e6dc7251472e335f8c47",
          "start_line": 142
        }
      ]
    },
    "metadata_comparison": {
      "canonical_templates": [
        "Create a new note in Markor named {file_name} with the following text: {text}"
      ],
      "comparison_is_semantic_proof": true,
      "differences": [],
      "fixed_seed_sample_shape_matches": [
        true,
        true,
        true,
        true,
        true,
        true,
        true,
        true
      ],
      "has_difference": false,
      "matches_runtime": true,
      "metadata_placeholders": [
        "file_name",
        "text"
      ],
      "metadata_template": "Create a new note in Markor named {file_name} with the following text: {text}",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "Markor.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.suite_utils",
        "owner_qualname": "suite_utils._run_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
        "source_sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateNote.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.suite_utils",
        "owner_qualname": "suite_utils._run_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/suite_utils.py",
        "source_sha256": "caf4d3a8765c914a2b978d119921cc4c062176e5a362c20c53905d4d0dbe083b"
      }
    ],
    "official_policy": "AndroidWorld has no separate policy document. The frozen task class, parameter generator/schema, initialize_task implementation, runtime-dispatched goal, is_successful implementation, and suite runner are authoritative. task_metadata.json is descriptive and is not allowed to override conflicting runtime semantics.",
    "parameter_schema": {
      "observed_parameter_keys": [
        "file_name",
        "seed",
        "text"
      ],
      "observed_parameter_types": {
        "file_name": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ],
        "text": [
          "builtins.str"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "declared_not_assumed_complete",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "5e3c11bc0f8d57eae3ff6990a53a9fed6913112e3462522b8b7351632beb6bca",
          "end_line": 449,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateNote.schema",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "371e743ed5c25f17866470888b4542b17046cf4263116b2671bb2ba37ab9304e",
          "start_line": 415
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "23cc300084f93bcf3f882776b69dcf66010494aa64fefdcfc9fa67aa524226e1",
          "end_line": 445,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateNote.generate_random_params",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "c6fad69c206bd90ede071b726ea55572e9bab29a9c7bece41d16c4f4ff32d156",
          "start_line": 442
        }
      ],
      "value": {
        "properties": {
          "file_name": {
            "type": "string"
          },
          "text": {
            "type": "string"
          }
        },
        "required": [
          "file_name",
          "text"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorCreateNote/canonical_task_semantics.json",
      "sha256": "8b396db3b4b6ff57cd9e460908824c74353802807a0cb060081730edb60bf998"
    },
    "task_text": {
      "benchmark": "AndroidWorld",
      "canonical_goal": {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "branches": [],
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": null,
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named qFzW_polite_wolf.txt with the following text: Actions speak louder than words.",
              "dispatch_goal_sha256": "56ec8c70d50b7747f12c902dfcaf21ea404c0eeb3edc53c3130f7798c01fd3bf",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named friendly_koala_2023_03_02.txt with the following text: The early bird catches the worm.",
              "dispatch_goal_sha256": "9618417b941172b54eb3fd068f501080bbf8c7a8cbfc7ba8e506d7fb45061635",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named brave_fish_2023_03_28.txt with the following text: To be or not to be.",
              "dispatch_goal_sha256": "eb6f8f1ca3285b1bc4390d5e835ad324d8807775e047821c13102c8dc2ac9ace",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named final_wise_lamp.txt with the following text: The squeaky wheel gets the grease.",
              "dispatch_goal_sha256": "71f7fe312e56866647ea3bd9f382ebb8fc319cc4516e845b2a9d52f48d0be504",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named wise_tree_2023_09_03.md with the following text: Monthly budget meeting pushed to Friday.",
              "dispatch_goal_sha256": "dc372316a1420d3da7b23b3bcd1d44b75c143f1a1864b6d3f0c391fd4369ff7d",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named good_queen_backup.txt with the following text: Hello, World!",
              "dispatch_goal_sha256": "32ab5e1406afedfd44c20ebee5adf3d81d317cce8a0059924f9d655a5a841d5e",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named eHwd_helpful_jacket.md with the following text: Lunch meeting with Sarah at 1 PM Cafe L'amour.",
              "dispatch_goal_sha256": "69055b1d6ff3a5ba7b1d6227f2479c156a44320f3b49af2078eba979c88e5d91",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named tough_jelly_FKlF.md with the following text: Pick up groceries: Milk and Bread and Apples.",
              "dispatch_goal_sha256": "06fde9579426a12df0a887dbe2dd7fae929c8f08f3c388544ec4706b59b9bd8a",
              "parameter_keys": [
                "file_name",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 11
            }
          ],
          "samples_are_examples_not_generic_templates": true,
          "templates": [
            {
              "placeholders": [
                "file_name",
                "text"
              ],
              "template": "Create a new note in Markor named {file_name} with the following text: {text}",
              "variant_id": "default"
            }
          ]
        },
        "representation_kind": "format_template",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
            "ast_sha256": "25a7b24a351ed012c02d1854080b239788b8650c232f75a55874f431f46d375a",
            "end_line": 109,
            "owner_module": "android_world.task_evals.task_eval",
            "owner_qualname": "TaskEval.goal",
            "sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb",
            "snippet_sha256": "0ab83521d040a0a8449aed8286bde0da755f1f2ab5361cba898a64c0d5033f91",
            "start_line": 106
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
            "ast_sha256": "5e3c11bc0f8d57eae3ff6990a53a9fed6913112e3462522b8b7351632beb6bca",
            "end_line": 449,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateNote.template",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "371e743ed5c25f17866470888b4542b17046cf4263116b2671bb2ba37ab9304e",
            "start_line": 415
          }
        ],
        "template": "Create a new note in Markor named {file_name} with the following text: {text}"
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a new note in Markor named {file_name} with the following text: {text}",
      "optimal_steps": "8",
      "tags": [
        "data_entry",
        "parameterized"
      ],
      "task_name": "MarkorCreateNote"
    },
    "trace_schema": {
      "artifacts": [
        "device state",
        "system state",
        "checkpoint artifacts",
        "observations",
        "actions",
        "messages",
        "evaluator input",
        "evaluator output"
      ],
      "episodes_per_record": 1
    }
  }
}
```
