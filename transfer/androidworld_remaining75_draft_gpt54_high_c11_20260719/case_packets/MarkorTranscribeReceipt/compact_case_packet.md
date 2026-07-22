# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorTranscribeReceipt",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 71,
    "task_id": "MarkorTranscribeReceipt"
  },
  "integrity": {
    "semantic_record_sha256": "48bd737ad9683ca0de11eb73fcf8fa4c5c7450c22f533f553a05e3682173692e",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "9a427b75c17d5eca707699379a2c5125f49b88140a0810b468afc92681f6d173",
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
            "qualname": "MarkorTranscribeReceipt",
            "source_ref": {
              "ast_sha256": "7e61879f992050b7d83648ecc0de7571c1bcd18c9bb737826e1d098bc3998fc1",
              "end_line": 874,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "1ed1b9e8faa4e41e7db830800cd665b588628c9165cd689a6db72276d225e218",
              "start_line": 818,
              "symbol": "MarkorTranscribeReceipt"
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
            "ast_sha256": "7e61879f992050b7d83648ecc0de7571c1bcd18c9bb737826e1d098bc3998fc1",
            "end_line": 874,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorTranscribeReceipt",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "1ed1b9e8faa4e41e7db830800cd665b588628c9165cd689a6db72276d225e218",
            "start_line": 818
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
            "owner_class": "MarkorTranscribeReceipt",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
              "end_line": 860,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "c21d6f6d69bcda4306fe74304d1646a1fb15a5020e78e86b977b4b5f771f33a4",
              "start_line": 858,
              "symbol": "MarkorTranscribeReceipt.is_successful"
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
            "end_line": 860,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorTranscribeReceipt.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "c21d6f6d69bcda4306fe74304d1646a1fb15a5020e78e86b977b4b5f771f33a4",
            "start_line": 858
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
            "owner_class": "MarkorTranscribeReceipt",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "4ed1a215e11dbc83629fca39655b705973a76ca214f9f320bde542a8544aa5d0",
              "end_line": 860,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "c21d6f6d69bcda4306fe74304d1646a1fb15a5020e78e86b977b4b5f771f33a4",
              "start_line": 858,
              "symbol": "MarkorTranscribeReceipt.is_successful"
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
            "end_line": 860,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorTranscribeReceipt.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "c21d6f6d69bcda4306fe74304d1646a1fb15a5020e78e86b977b4b5f771f33a4",
            "start_line": 858
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
      "task_class": "MarkorTranscribeReceipt"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "file_utils.convert_to_posix_path",
            "file_utils.copy_data_to_device",
            "file_utils.get_local_tmp_directory",
            "self.create_file_task.initialize_task",
            "self.img.save",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "MarkorTranscribeReceipt",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "948165270471bc7febbc119ea5f673f000ae131f9df74b9f6352106c256ffbf7",
            "end_line": 856,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "0eb2bc2f27aa35aa1e0ab9575efbff52bb19f24ecec71c2cb4aa489ec500010e",
            "start_line": 844,
            "symbol": "MarkorTranscribeReceipt.initialize_task"
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
          "ast_sha256": "948165270471bc7febbc119ea5f673f000ae131f9df74b9f6352106c256ffbf7",
          "end_line": 856,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorTranscribeReceipt.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "0eb2bc2f27aa35aa1e0ab9575efbff52bb19f24ecec71c2cb4aa489ec500010e",
          "start_line": 844
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
        "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\"."
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
      "metadata_placeholders": [],
      "metadata_template": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorTranscribeReceipt",
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
        "owner_qualname": "MarkorTranscribeReceipt.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorTranscribeReceipt.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorTranscribeReceipt.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorTranscribeReceipt.initialize_task",
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
        "owner_qualname": "MarkorTranscribeReceipt.is_successful",
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
        "owner_qualname": "MarkorTranscribeReceipt.is_successful",
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
          "ast_sha256": "7e61879f992050b7d83648ecc0de7571c1bcd18c9bb737826e1d098bc3998fc1",
          "end_line": 874,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorTranscribeReceipt.schema",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "1ed1b9e8faa4e41e7db830800cd665b588628c9165cd689a6db72276d225e218",
          "start_line": 818
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "9db7579cdff0e68922b300b764efc66f7bf9a0da289dd19171d9d43393c3cc70",
          "end_line": 874,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorTranscribeReceipt.generate_random_params",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "5f5917f59fbb64eae2b2cffaaafdc9532c1819c66310148bf9dc1511205cb0ea",
          "start_line": 866
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorTranscribeReceipt/canonical_task_semantics.json",
      "sha256": "48bd737ad9683ca0de11eb73fcf8fa4c5c7450c22f533f553a05e3682173692e"
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "dispatch_goal_model": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
              "dispatch_goal_sha256": "5581a0fc784750275e7495d5b4c20477b8114799c52c0c9dfa07aba63c30e8ca",
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
              "placeholders": [],
              "template": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
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
            "ast_sha256": "7e61879f992050b7d83648ecc0de7571c1bcd18c9bb737826e1d098bc3998fc1",
            "end_line": 874,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorTranscribeReceipt.template",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "1ed1b9e8faa4e41e7db830800cd665b588628c9165cd689a6db72276d225e218",
            "start_line": 818
          }
        ],
        "template": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\"."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a file in Markor, called receipt.md with the transactions from the receipt.png. Use Simple Gallery to view the receipt. Please enter transactions in csv format including the header \"Date, Item, Amount\".",
      "optimal_steps": "9",
      "tags": [
        "transcription",
        "data_entry",
        "multi_app",
        "screen_reading",
        "memorization",
        "parameterized"
      ],
      "task_name": "MarkorTranscribeReceipt"
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
