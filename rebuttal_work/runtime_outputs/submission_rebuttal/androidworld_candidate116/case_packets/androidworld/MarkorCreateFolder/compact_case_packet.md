# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorCreateFolder",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 91,
    "task_id": "MarkorCreateFolder"
  },
  "integrity": {
    "semantic_record_sha256": "d8ae5f87109cac864b2b2b3ecb22db0c7f28b797304b7be0a46a264b00dba0af",
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
            "qualname": "MarkorCreateFolder",
            "source_ref": {
              "ast_sha256": "3e12dd7e3e7a586bc4095828fcd761f376dd596555bc24094abcce83ce3cc414",
              "end_line": 166,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "70de3950453782637c9a2030658623d8ffa1cabdc825ba059d2fe429a03fd723",
              "start_line": 125,
              "symbol": "MarkorCreateFolder"
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
            "ast_sha256": "3e12dd7e3e7a586bc4095828fcd761f376dd596555bc24094abcce83ce3cc414",
            "end_line": 166,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateFolder",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "70de3950453782637c9a2030658623d8ffa1cabdc825ba059d2fe429a03fd723",
            "start_line": 125
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "file_utils.check_file_or_folder_exists",
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "folder_name"
            ],
            "owner_class": "MarkorCreateFolder",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "07b9d076b147025fb536d7cb6d9c918a4d36b704e594ed6bdaeb2b38511eeff3",
              "end_line": 159,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "ebbb2ce84fe3534cd3b1a9e12bfc4c9a839ffb003e4ab1a71539ed463f5c0a89",
              "start_line": 147,
              "symbol": "MarkorCreateFolder.is_successful"
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
            "ast_sha256": "07b9d076b147025fb536d7cb6d9c918a4d36b704e594ed6bdaeb2b38511eeff3",
            "end_line": 159,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateFolder.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "ebbb2ce84fe3534cd3b1a9e12bfc4c9a839ffb003e4ab1a71539ed463f5c0a89",
            "start_line": 147
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
              "file_utils.check_file_or_folder_exists",
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "folder_name"
            ],
            "owner_class": "MarkorCreateFolder",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "07b9d076b147025fb536d7cb6d9c918a4d36b704e594ed6bdaeb2b38511eeff3",
              "end_line": 159,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "ebbb2ce84fe3534cd3b1a9e12bfc4c9a839ffb003e4ab1a71539ed463f5c0a89",
              "start_line": 147,
              "symbol": "MarkorCreateFolder.is_successful"
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
            "ast_sha256": "07b9d076b147025fb536d7cb6d9c918a4d36b704e594ed6bdaeb2b38511eeff3",
            "end_line": 159,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateFolder.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "ebbb2ce84fe3534cd3b1a9e12bfc4c9a839ffb003e4ab1a71539ed463f5c0a89",
            "start_line": 147
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
      "task_class": "MarkorCreateFolder"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "super",
            "super.initialize_task",
            "user_data_generation.generate_noise_files"
          ],
          "direct_parameter_reads": [],
          "owner_class": "MarkorCreateFolder",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "3c44e16cfa71d9cdfabbe86cb950c3e1a3536d90b839f8ce9080fa7a79bfb6d3",
            "end_line": 145,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "a9c8ea31cd5ce7dc06d9d2643b8df09519abd59e6c20374cc8707725deee1191",
            "start_line": 138,
            "symbol": "MarkorCreateFolder.initialize_task"
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
          "ast_sha256": "3c44e16cfa71d9cdfabbe86cb950c3e1a3536d90b839f8ce9080fa7a79bfb6d3",
          "end_line": 145,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateFolder.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "a9c8ea31cd5ce7dc06d9d2643b8df09519abd59e6c20374cc8707725deee1191",
          "start_line": 138
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
        "Create a new folder in Markor named {folder_name}."
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
        "folder_name"
      ],
      "metadata_template": "Create a new folder in Markor named {folder_name}.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateFolder",
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
        "owner_qualname": "MarkorCreateFolder.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateFolder.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateFolder.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorCreateFolder.initialize_task",
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
        "owner_qualname": "MarkorCreateFolder.is_successful",
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
        "owner_qualname": "MarkorCreateFolder.is_successful",
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
        "folder_name",
        "seed"
      ],
      "observed_parameter_types": {
        "folder_name": [
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "3e12dd7e3e7a586bc4095828fcd761f376dd596555bc24094abcce83ce3cc414",
          "end_line": 166,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateFolder.schema",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "70de3950453782637c9a2030658623d8ffa1cabdc825ba059d2fe429a03fd723",
          "start_line": 125
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "4b08a93b61112d3a3429fc0e0463103ca2eff66bc7daf52464148dbb02b4cb1a",
          "end_line": 166,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorCreateFolder.generate_random_params",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "b149a1db378546321e43ef40fd4fbb712c6ccf986e37ad3ade4e3ee80a5272d6",
          "start_line": 161
        }
      ],
      "value": {
        "properties": {
          "folder_name": {
            "type": "string"
          }
        },
        "required": [
          "folder_name"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorCreateFolder/canonical_task_semantics.json",
      "sha256": "d8ae5f87109cac864b2b2b3ecb22db0c7f28b797304b7be0a46a264b00dba0af"
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
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new folder in Markor named folder_20231015_120000.",
              "dispatch_goal_sha256": "a16471160ff8ef1d3c7e91b8cbfe2b990d1abd0bfe1cec97599e3406031498a6",
              "parameter_keys": [
                "folder_name",
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
                "folder_name"
              ],
              "template": "Create a new folder in Markor named {folder_name}.",
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
            "ast_sha256": "3e12dd7e3e7a586bc4095828fcd761f376dd596555bc24094abcce83ce3cc414",
            "end_line": 166,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorCreateFolder.template",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "70de3950453782637c9a2030658623d8ffa1cabdc825ba059d2fe429a03fd723",
            "start_line": 125
          }
        ],
        "template": "Create a new folder in Markor named {folder_name}."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a new folder in Markor named {folder_name}.",
      "optimal_steps": "4",
      "tags": [
        "data_entry",
        "parameterized"
      ],
      "task_name": "MarkorCreateFolder"
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
