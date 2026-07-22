# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "BrowserMaze",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 73,
    "task_id": "BrowserMaze"
  },
  "integrity": {
    "semantic_record_sha256": "dab05f205e6623882b6f095d1e004bbe3af8f1a6920ed7056650f29a0375cc3a",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "3cb4081b2398046ae677933f7bc16c146d08c5ef729cf623a0b69905ea3f8d88",
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
      "canonical_module": "android_world.task_evals.single.browser",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.browser",
            "qualname": "BrowserMaze",
            "source_ref": {
              "ast_sha256": "9c327026d501cb799cb508354dca9f712a1009633b0b92c26c93e588b434e204",
              "end_line": 328,
              "file_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
              "path": "android_world/task_evals/single/browser.py",
              "snippet_sha256": "ccb43bb9ca5f1ca4f424665e841abf2d0085eef6d62b48d7c70c4802b4fd54e3",
              "start_line": 116,
              "symbol": "BrowserMaze"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.browser",
            "qualname": "BrowserTask",
            "source_ref": {
              "ast_sha256": "1f7eb76c30a31518b4ac1392c6190f9cd4e0fba3264564932f6c250eab176e80",
              "end_line": 113,
              "file_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
              "path": "android_world/task_evals/single/browser.py",
              "snippet_sha256": "5621296be8898430634883732c53da54cefebecd79d854673b87d408568f25c0",
              "start_line": 29,
              "symbol": "BrowserTask"
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
        "runtime_reported_module": "android_world.task_evals.single.browser",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
            "ast_sha256": "9c327026d501cb799cb508354dca9f712a1009633b0b92c26c93e588b434e204",
            "end_line": 328,
            "owner_module": "android_world.task_evals.single.browser",
            "owner_qualname": "BrowserMaze",
            "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
            "snippet_sha256": "ccb43bb9ca5f1ca4f424665e841abf2d0085eef6d62b48d7c70c4802b4fd54e3",
            "start_line": 116
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "adb_utils.extract_package_name",
              "adb_utils.get_current_activity",
              "env.get_state"
            ],
            "direct_parameter_reads": [],
            "owner_class": "BrowserTask",
            "owner_module": "android_world.task_evals.single.browser",
            "source_ref": {
              "ast_sha256": "bfc91cdb5849068210a6b4302dd2ec616781517e1cc09fff471a344de553b172",
              "end_line": 109,
              "file_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
              "path": "android_world/task_evals/single/browser.py",
              "snippet_sha256": "cf27b17ef24665df57cee47c4c1d42839795f8e1a4fc561e7c281391a1306269",
              "start_line": 98,
              "symbol": "BrowserTask.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
            "ast_sha256": "bfc91cdb5849068210a6b4302dd2ec616781517e1cc09fff471a344de553b172",
            "end_line": 109,
            "owner_module": "android_world.task_evals.single.browser",
            "owner_qualname": "BrowserTask.is_successful",
            "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
            "snippet_sha256": "cf27b17ef24665df57cee47c4c1d42839795f8e1a4fc561e7c281391a1306269",
            "start_line": 98
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
            "branch_node_count": 2,
            "direct_calls": [
              "adb_utils.extract_package_name",
              "adb_utils.get_current_activity",
              "env.get_state"
            ],
            "direct_parameter_reads": [],
            "owner_class": "BrowserTask",
            "owner_module": "android_world.task_evals.single.browser",
            "source_ref": {
              "ast_sha256": "bfc91cdb5849068210a6b4302dd2ec616781517e1cc09fff471a344de553b172",
              "end_line": 109,
              "file_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
              "path": "android_world/task_evals/single/browser.py",
              "snippet_sha256": "cf27b17ef24665df57cee47c4c1d42839795f8e1a4fc561e7c281391a1306269",
              "start_line": 98,
              "symbol": "BrowserTask.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
            "ast_sha256": "bfc91cdb5849068210a6b4302dd2ec616781517e1cc09fff471a344de553b172",
            "end_line": 109,
            "owner_module": "android_world.task_evals.single.browser",
            "owner_qualname": "BrowserTask.is_successful",
            "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
            "snippet_sha256": "cf27b17ef24665df57cee47c4c1d42839795f8e1a4fc561e7c281391a1306269",
            "start_line": 98
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
      "task_class": "BrowserMaze"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.clear_app_data",
            "adb_utils.extract_package_name",
            "adb_utils.get_adb_activity",
            "adb_utils.grant_permissions",
            "f.write",
            "file_utils.convert_to_posix_path",
            "file_utils.copy_data_to_device",
            "file_utils.get_local_tmp_directory",
            "open",
            "self.HTML.replace",
            "str",
            "super",
            "super.initialize_task",
            "user_data_generation.clear_device_storage"
          ],
          "direct_parameter_reads": [
            "browser_task_seed"
          ],
          "owner_class": "BrowserTask",
          "owner_module": "android_world.task_evals.single.browser",
          "source_ref": {
            "ast_sha256": "e0c528a1632a365c2db050fe7fbe7e1edd7ecd330e85e19e3857acc310a93b78",
            "end_line": 85,
            "file_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
            "path": "android_world/task_evals/single/browser.py",
            "snippet_sha256": "124985e13cdfe3233fc471ef622c6b43d4d7073b150c928acd4357bd410c4006",
            "start_line": 56,
            "symbol": "BrowserTask.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
          "ast_sha256": "e0c528a1632a365c2db050fe7fbe7e1edd7ecd330e85e19e3857acc310a93b78",
          "end_line": 85,
          "owner_module": "android_world.task_evals.single.browser",
          "owner_qualname": "BrowserTask.initialize_task",
          "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
          "snippet_sha256": "124985e13cdfe3233fc471ef622c6b43d4d7073b150c928acd4357bd410c4006",
          "start_line": 56
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
      "canonical_templates": [],
      "comparison_is_semantic_proof": false,
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
      "metadata_template": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
      "status": "fixed_seed_goal_shape_match"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserMaze",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
      },
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserMaze.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
      },
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserTask.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
      },
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserTask.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
      },
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserTask.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserTask.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
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
        "owner_module": "android_world.task_evals.single.browser",
        "owner_qualname": "BrowserTask.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
        "source_sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b"
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
        "browser_task_seed",
        "seed"
      ],
      "observed_parameter_types": {
        "browser_task_seed": [
          "builtins.int"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
          "ast_sha256": "1f7eb76c30a31518b4ac1392c6190f9cd4e0fba3264564932f6c250eab176e80",
          "end_line": 113,
          "owner_module": "android_world.task_evals.single.browser",
          "owner_qualname": "BrowserTask.schema",
          "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
          "snippet_sha256": "5621296be8898430634883732c53da54cefebecd79d854673b87d408568f25c0",
          "start_line": 29
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
          "ast_sha256": "8511da24ac9389ad195b1ffe9ae8a113fdc3840f70ece00003ae87c2cec787f8",
          "end_line": 113,
          "owner_module": "android_world.task_evals.single.browser",
          "owner_qualname": "BrowserTask.generate_random_params",
          "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
          "snippet_sha256": "3ca5834f5d0c9a81d5e75cf6018432c3fcd7ed877a57f06f71e081b22aa89efd",
          "start_line": 111
        }
      ],
      "value": {
        "properties": {
          "browser_task_seed": {
            "type": "number"
          }
        },
        "required": [
          "browser_task_seed"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/BrowserMaze/canonical_task_semantics.json",
      "sha256": "dab05f205e6623882b6f095d1e004bbe3af8f1a6920ed7056650f29a0375cc3a"
    },
    "task_text": {
      "benchmark": "AndroidWorld",
      "canonical_goal": {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "branches": [],
        "computed_expression": {
          "branch_node_count": 0,
          "direct_calls": [],
          "direct_parameter_reads": []
        },
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": {
            "branch_node_count": 0,
            "direct_calls": [],
            "direct_parameter_reads": []
          },
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
              "dispatch_goal_sha256": "1080b2735d42c3291b709bcb18c4bd8a9e4ec107d31c8a5c868ff4670eb41eb1",
              "parameter_keys": [
                "browser_task_seed",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 11
            }
          ],
          "samples_are_examples_not_generic_templates": true,
          "templates": []
        },
        "representation_kind": "computed_goal",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/browser.py",
            "ast_sha256": "55555fccc17ecdfd95176c3f15fcc6bef1fc6d067cc9581918008792982897e8",
            "end_line": 125,
            "owner_module": "android_world.task_evals.single.browser",
            "owner_qualname": "BrowserMaze.goal",
            "sha256": "bbc47cf333351b071984c00135fde8cd522a2e409e1a15cb4bb5e9feda95212b",
            "snippet_sha256": "fc2966c4a5282407c0e763faf249109eb84fcb7d4144adb37cfb54872e728336",
            "start_line": 119
          }
        ]
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Open the file task.html in Downloads in the file manager; when prompted open it with Chrome. Then navigate the X to the bottom-right cell, by using the direction buttons.",
      "optimal_steps": "9",
      "tags": [
        "game_playing",
        "multi_app",
        "complex_ui_understanding",
        "memorization",
        "parameterized"
      ],
      "task_name": "BrowserMaze"
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
