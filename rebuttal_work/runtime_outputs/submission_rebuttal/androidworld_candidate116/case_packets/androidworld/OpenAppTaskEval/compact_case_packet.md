# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "OpenAppTaskEval",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 47,
    "task_id": "OpenAppTaskEval"
  },
  "integrity": {
    "semantic_record_sha256": "232a71c3036b45d8016028d717a9fff4d0691ae8b6ee1d061f4a460222b8c79c",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "cf389c353ff5a664e4d67a92d41a88cd54afe84ccce563c9d14d0185b0c27a87",
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
      "canonical_module": "android_world.task_evals.single.system",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.system",
            "qualname": "OpenAppTaskEval",
            "source_ref": {
              "ast_sha256": "8ee65b70113c333720b84e23bc58530fe75c9c048be8f9fd989810231d8fc437",
              "end_line": 499,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "e263554b52e35b9d80b3e04e3f58ee27d2b31baf693cbabfd2ce1e4b38aa38a1",
              "start_line": 459,
              "symbol": "OpenAppTaskEval"
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
        "runtime_reported_module": "android_world.task_evals.single.system",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
            "ast_sha256": "8ee65b70113c333720b84e23bc58530fe75c9c048be8f9fd989810231d8fc437",
            "end_line": 499,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "OpenAppTaskEval",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "e263554b52e35b9d80b3e04e3f58ee27d2b31baf693cbabfd2ce1e4b38aa38a1",
            "start_line": 459
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "adb_utils.get_current_activity",
              "logging.info",
              "parse_component_name",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "app_name"
            ],
            "owner_class": "OpenAppTaskEval",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "a617c68f50265f3db586d2281b2a627ca1bbbccb2caf8f9a5a33b1a2b4fd514e",
              "end_line": 499,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "34094cdbdeebf502a23b0bfed615fd75c894c3075ab40c7a4be8c735e21bb714",
              "start_line": 484,
              "symbol": "OpenAppTaskEval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
            "ast_sha256": "a617c68f50265f3db586d2281b2a627ca1bbbccb2caf8f9a5a33b1a2b4fd514e",
            "end_line": 499,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "OpenAppTaskEval.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "34094cdbdeebf502a23b0bfed615fd75c894c3075ab40c7a4be8c735e21bb714",
            "start_line": 484
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
            "branch_node_count": 1,
            "direct_calls": [
              "adb_utils.get_current_activity",
              "logging.info",
              "parse_component_name",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "app_name"
            ],
            "owner_class": "OpenAppTaskEval",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "a617c68f50265f3db586d2281b2a627ca1bbbccb2caf8f9a5a33b1a2b4fd514e",
              "end_line": 499,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "34094cdbdeebf502a23b0bfed615fd75c894c3075ab40c7a4be8c735e21bb714",
              "start_line": 484,
              "symbol": "OpenAppTaskEval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
            "ast_sha256": "a617c68f50265f3db586d2281b2a627ca1bbbccb2caf8f9a5a33b1a2b4fd514e",
            "end_line": 499,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "OpenAppTaskEval.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "34094cdbdeebf502a23b0bfed615fd75c894c3075ab40c7a4be8c735e21bb714",
            "start_line": 484
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
      "task_class": "OpenAppTaskEval"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
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
        "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required."
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
        "app_name"
      ],
      "metadata_template": "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
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
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "OpenAppTaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
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
        "app_name",
        "seed"
      ],
      "observed_parameter_types": {
        "app_name": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "declared_not_assumed_complete",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "8ee65b70113c333720b84e23bc58530fe75c9c048be8f9fd989810231d8fc437",
          "end_line": 499,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "OpenAppTaskEval.schema",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "e263554b52e35b9d80b3e04e3f58ee27d2b31baf693cbabfd2ce1e4b38aa38a1",
          "start_line": 459
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "7266e1f97c88e28896a9042b88eb982ebdaf8775a6755125ff74fcc35dd68b25",
          "end_line": 482,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "OpenAppTaskEval.generate_random_params",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "b19605d788d1bbc3ae310897276c93f27438b6e32c16172ca667fc6af27952c5",
          "start_line": 479
        }
      ],
      "value": {
        "properties": {
          "app_name": {
            "type": "string"
          }
        },
        "required": [
          "app_name"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/OpenAppTaskEval/canonical_task_semantics.json",
      "sha256": "232a71c3036b45d8016028d717a9fff4d0691ae8b6ee1d061f4a460222b8c79c"
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
              "dispatch_goal_model": "Open the settings app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "085e20266de7214623c18ac44d64eab566286a06488b8424b60cb2b0fcb6b96d",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the clock app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "3ff1675e90d7bd6acef40e7f019b2e729d36fbc08ee4f8fdccb29fc1bed36494",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the camera app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "50b81c571d7cf286712887ae1e120df1fce1c3d88f3ad170a79698b3d9d68f9d",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the clock app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "3ff1675e90d7bd6acef40e7f019b2e729d36fbc08ee4f8fdccb29fc1bed36494",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the clock app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "3ff1675e90d7bd6acef40e7f019b2e729d36fbc08ee4f8fdccb29fc1bed36494",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the dialer app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "aa54b952bb82e12cfd02c86147c568607d9f89de87d36660d18ae2e0c3fe6d99",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the contacts app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "a62ade525689a1104d170476616dc91bf655bfea726ed6dcc2e18b4549aed607",
              "parameter_keys": [
                "app_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the settings app. Clear any pop-ups that may appear by granting all permissions that are required.",
              "dispatch_goal_sha256": "085e20266de7214623c18ac44d64eab566286a06488b8424b60cb2b0fcb6b96d",
              "parameter_keys": [
                "app_name",
                "seed"
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
                "app_name"
              ],
              "template": "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
            "ast_sha256": "8ee65b70113c333720b84e23bc58530fe75c9c048be8f9fd989810231d8fc437",
            "end_line": 499,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "OpenAppTaskEval.template",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "e263554b52e35b9d80b3e04e3f58ee27d2b31baf693cbabfd2ce1e4b38aa38a1",
            "start_line": 459
          }
        ],
        "template": "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Open the {app_name} app. Clear any pop-ups that may appear by granting all permissions that are required.",
      "optimal_steps": "2",
      "tags": [
        "parameterized"
      ],
      "task_name": "OpenAppTaskEval"
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
