# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "FilesMoveFile",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 22,
    "task_id": "FilesMoveFile"
  },
  "integrity": {
    "semantic_record_sha256": "d8f8751a70982d190275a32fbdf8aa1b1babb6cf88cb808fe44e42adc6f2cf8b",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "7950c6760a8517437ad01c8dfa266e440e7e5b940e2f6354aa08119cb42887b1",
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
      "canonical_module": "android_world.task_evals.single.files",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.files",
            "qualname": "FilesMoveFile",
            "source_ref": {
              "ast_sha256": "2ff9c8beb2206bae71ec6bc2fcce7fa25c9b1534a8bce52fc42eb62762b1c0de",
              "end_line": 80,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "cd9b227d0993b78b61f02623aa4cf76e6dab505817d6f574ac62df5cc0e41f54",
              "start_line": 28,
              "symbol": "FilesMoveFile"
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
        "runtime_reported_module": "android_world.task_evals.single.files",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
            "ast_sha256": "2ff9c8beb2206bae71ec6bc2fcce7fa25c9b1534a8bce52fc42eb62762b1c0de",
            "end_line": 80,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesMoveFile",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "cd9b227d0993b78b61f02623aa4cf76e6dab505817d6f574ac62df5cc0e41f54",
            "start_line": 28
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self.move_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "FilesMoveFile",
            "owner_module": "android_world.task_evals.single.files",
            "source_ref": {
              "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
              "end_line": 56,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
              "start_line": 54,
              "symbol": "FilesMoveFile.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
            "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
            "end_line": 56,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesMoveFile.is_successful",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
            "start_line": 54
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
              "self.move_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "FilesMoveFile",
            "owner_module": "android_world.task_evals.single.files",
            "source_ref": {
              "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
              "end_line": 56,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
              "start_line": 54,
              "symbol": "FilesMoveFile.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
            "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
            "end_line": 56,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesMoveFile.is_successful",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
            "start_line": 54
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
      "task_class": "FilesMoveFile"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self.move_file_task.initialize_task",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "FilesMoveFile",
          "owner_module": "android_world.task_evals.single.files",
          "source_ref": {
            "ast_sha256": "9206534f2563c82f5fba286843b896c9d7b40cd7d73d4c64f81753a60eaf4722",
            "end_line": 48,
            "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "path": "android_world/task_evals/single/files.py",
            "snippet_sha256": "aa33a4ffea30dc04f6519394c98b7ebd06378ee442203975c042f63b7da4c14f",
            "start_line": 46,
            "symbol": "FilesMoveFile.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
          "ast_sha256": "9206534f2563c82f5fba286843b896c9d7b40cd7d73d4c64f81753a60eaf4722",
          "end_line": 48,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesMoveFile.initialize_task",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "aa33a4ffea30dc04f6519394c98b7ebd06378ee442203975c042f63b7da4c14f",
          "start_line": 46
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
        "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem."
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
        "destination_folder",
        "file_name",
        "source_folder"
      ],
      "metadata_template": "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
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
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesMoveFile.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
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
        "destination_folder",
        "file_name",
        "noise_candidates",
        "seed",
        "source_folder"
      ],
      "observed_parameter_types": {
        "destination_folder": [
          "builtins.str"
        ],
        "file_name": [
          "builtins.str"
        ],
        "noise_candidates": [
          "builtins.list"
        ],
        "seed": [
          "builtins.int"
        ],
        "source_folder": [
          "builtins.str"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "declared_not_assumed_complete",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
          "ast_sha256": "2ff9c8beb2206bae71ec6bc2fcce7fa25c9b1534a8bce52fc42eb62762b1c0de",
          "end_line": 80,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesMoveFile.schema",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "cd9b227d0993b78b61f02623aa4cf76e6dab505817d6f574ac62df5cc0e41f54",
          "start_line": 28
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
          "ast_sha256": "e71f171bbf187c9aa41edcfb0ccce0bd1a46b874dfc49eb418d6058f0a488323",
          "end_line": 80,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesMoveFile.generate_random_params",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "e1366984058155054ae348f91657cdab48fc1864bcb2fef66911eb0536ccff2d",
          "start_line": 58
        }
      ],
      "value": {
        "properties": {
          "destination_folder": {
            "type": "string"
          },
          "file_name": {
            "type": "string"
          },
          "source_folder": {
            "type": "string"
          }
        },
        "required": [
          "file_name",
          "source_folder",
          "destination_folder"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/FilesMoveFile/canonical_task_semantics.json",
      "sha256": "d8f8751a70982d190275a32fbdf8aa1b1babb6cf88cb808fe44e42adc6f2cf8b"
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
              "dispatch_goal_model": "Move the file new_message.mp3 from Music within the sdk_gphone_x86_64 storage area to the Notifications within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "aea056d506fae0fb666f061201f99b5b5e532b7d01c57c066ae578a379e8e0c1",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file lecture_capture.mp3 from DCIM within the sdk_gphone_x86_64 storage area to the Recordings within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "b72db7f4678cea35e525de81ebe83b7eb74aecc7482d6f5ab2f6288d8d9667da",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file birthday_party.jpg from Alarms within the sdk_gphone_x86_64 storage area to the DCIM within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "17b2fed9253ff5cd04ebb3aad5c34fde8644f5a3a14ccc0fbbc3e19494490b91",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file memoir_audio.mp3 from Documents within the sdk_gphone_x86_64 storage area to the Recordings within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "286fa75385db769b59104a3b0317390cf5391f84121ee1dff40a4368f2b9727f",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file romantic_comedy.mp4 from Documents within the sdk_gphone_x86_64 storage area to the Movies within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "4e80ca4e4130edf44992796e86884f189ed64c2ed86adade239b6be2fcbc9005",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file software_patch.exe from Podcasts within the sdk_gphone_x86_64 storage area to the Download within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "469b45cd93320c242ff7a2b7675678ce7fdfe8ed123f49485cc9680874059892",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file first_day_school.jpg from Movies within the sdk_gphone_x86_64 storage area to the DCIM within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "0025d62a1ebfb1b6e874a6e1d20377198345656496400857fff002622370c39c",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Move the file travel_tips.mp3 from Notifications within the sdk_gphone_x86_64 storage area to the Podcasts within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
              "dispatch_goal_sha256": "95da5d19166edbea30afc9b6b2238cd3dc35924d40538d1c24d2501c9b65dff3",
              "parameter_keys": [
                "destination_folder",
                "file_name",
                "noise_candidates",
                "seed",
                "source_folder"
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
                "destination_folder",
                "file_name",
                "source_folder"
              ],
              "template": "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
            "ast_sha256": "2ff9c8beb2206bae71ec6bc2fcce7fa25c9b1534a8bce52fc42eb62762b1c0de",
            "end_line": 80,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesMoveFile.template",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "cd9b227d0993b78b61f02623aa4cf76e6dab505817d6f574ac62df5cc0e41f54",
            "start_line": 28
          }
        ],
        "template": "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Move the file {file_name} from {source_folder} within the sdk_gphone_x86_64 storage area to the {destination_folder} within the same sdk_gphone_x86_64 storage area in the Android filesystem.",
      "optimal_steps": "10",
      "tags": [
        "search",
        "screen_reading",
        "parameterized"
      ],
      "task_name": "FilesMoveFile"
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
