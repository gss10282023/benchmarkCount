# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorMoveNote",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 36,
    "task_id": "MarkorMoveNote"
  },
  "integrity": {
    "semantic_record_sha256": "0e58002df77ee968ed0912c284612a8750ee33eb0a3513b35c0484dcb9a8e263",
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
            "qualname": "MarkorMoveNote",
            "source_ref": {
              "ast_sha256": "7ce8db906c58c07661a2b0279ac5efd9545a3db6ee934d22f57763a230aa8c0f",
              "end_line": 122,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "ce42917194219b2e4fd7248d32b3e22209873671d51b4a635a7967e4f9e03d86",
              "start_line": 69,
              "symbol": "MarkorMoveNote"
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
            "ast_sha256": "7ce8db906c58c07661a2b0279ac5efd9545a3db6ee934d22f57763a230aa8c0f",
            "end_line": 122,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorMoveNote",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "ce42917194219b2e4fd7248d32b3e22209873671d51b4a635a7967e4f9e03d86",
            "start_line": 69
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
            "owner_class": "MarkorMoveNote",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
              "end_line": 92,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
              "start_line": 90,
              "symbol": "MarkorMoveNote.is_successful"
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
            "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
            "end_line": 92,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorMoveNote.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
            "start_line": 90
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
            "owner_class": "MarkorMoveNote",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
              "end_line": 92,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
              "start_line": 90,
              "symbol": "MarkorMoveNote.is_successful"
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
            "ast_sha256": "0963f8e1ced9e3b6adca6b0b6db2c8fb6f4e24f61c46959605704ef7d9af3d00",
            "end_line": 92,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorMoveNote.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "66a7ef5f57d82946b8546ebb7036be4f56f0a2c30d9a57c01fcf756f90bee0db",
            "start_line": 90
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
      "task_class": "MarkorMoveNote"
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
          "owner_class": "MarkorMoveNote",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "9206534f2563c82f5fba286843b896c9d7b40cd7d73d4c64f81753a60eaf4722",
            "end_line": 88,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "aa33a4ffea30dc04f6519394c98b7ebd06378ee442203975c042f63b7da4c14f",
            "start_line": 86,
            "symbol": "MarkorMoveNote.initialize_task"
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
          "ast_sha256": "9206534f2563c82f5fba286843b896c9d7b40cd7d73d4c64f81753a60eaf4722",
          "end_line": 88,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorMoveNote.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "aa33a4ffea30dc04f6519394c98b7ebd06378ee442203975c042f63b7da4c14f",
          "start_line": 86
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
        "In Markor, move the note {file_name} from {source_folder} to {destination_folder}."
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
      "metadata_template": "In Markor, move the note {file_name} from {source_folder} to {destination_folder}.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorMoveNote",
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
        "owner_qualname": "MarkorMoveNote.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorMoveNote.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorMoveNote.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorMoveNote.initialize_task",
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
        "owner_qualname": "MarkorMoveNote.is_successful",
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
        "owner_qualname": "MarkorMoveNote.is_successful",
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "7ce8db906c58c07661a2b0279ac5efd9545a3db6ee934d22f57763a230aa8c0f",
          "end_line": 122,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorMoveNote.schema",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "ce42917194219b2e4fd7248d32b3e22209873671d51b4a635a7967e4f9e03d86",
          "start_line": 69
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "21ece9167c9fa3b9c32abd8990d6d49067b2f8230edaf08f123e646f33396a0e",
          "end_line": 118,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorMoveNote.generate_random_params",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "adc76f94479886c043ac498eea9f17573bde3b6626213f7082468a2486c066f5",
          "start_line": 94
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorMoveNote/canonical_task_semantics.json",
      "sha256": "0e58002df77ee968ed0912c284612a8750ee33eb0a3513b35c0484dcb9a8e263"
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
              "dispatch_goal_model": "In Markor, move the note silly_queen_edited.txt from RecipeCollections to StudyGuides.",
              "dispatch_goal_sha256": "047a791dec40be96b871676b1c619356801c6c736e6ecb1579f39395e42f93e0",
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
              "dispatch_goal_model": "In Markor, move the note strong_house_DxnE.txt from DailyNotes to CodeSnippets.",
              "dispatch_goal_sha256": "bc1caa1433fdf1438dcdd64a2229355bd6ede41b51cb13fee11320f6d11620c9",
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
              "dispatch_goal_model": "In Markor, move the note clever_xylophone_2023_05_09.md from BookNotes to DailyNotes.",
              "dispatch_goal_sha256": "87e8dafa34389ba4667eedc94898f086833445552997ca326e67b5ab816924b9",
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
              "dispatch_goal_model": "In Markor, move the note friendly_xylophone_backup.md from FitnessPlans to WorkProjects.",
              "dispatch_goal_sha256": "8059877ffa1c642fcee1b815452bdf1d7fe0e795d17093c0b90ef8c5d7f6be38",
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
              "dispatch_goal_model": "In Markor, move the note gentle_unicorn_jey4.md from FitnessPlans to PersonalJournal.",
              "dispatch_goal_sha256": "9bd5db759da10e1ab82a4a81e3dfe3295f3e0c36b86de6ae065554079555bf64",
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
              "dispatch_goal_model": "In Markor, move the note edited_safe_watch.md from WorkProjects to MeetingMinutes.",
              "dispatch_goal_sha256": "f6e0859e9e6a6daa96b68f06492a351d5aa2404faff03f985d83f170bf8f1692",
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
              "dispatch_goal_model": "In Markor, move the note 2023_10_02_sharp_pig.md from PersonalJournal to DailyNotes.",
              "dispatch_goal_sha256": "b8894eafa4dd67739702a74313c66ee2c61d66a162fa44bfdd327561e01f6701",
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
              "dispatch_goal_model": "In Markor, move the note lFNX_warm_deer.md from StudyGuides to WorkProjects.",
              "dispatch_goal_sha256": "5923ff1fcf7b78c37d07071c74d97c152ab130292fcca9d07527266bf547e942",
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
              "template": "In Markor, move the note {file_name} from {source_folder} to {destination_folder}.",
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
            "ast_sha256": "7ce8db906c58c07661a2b0279ac5efd9545a3db6ee934d22f57763a230aa8c0f",
            "end_line": 122,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorMoveNote.template",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "ce42917194219b2e4fd7248d32b3e22209873671d51b4a635a7967e4f9e03d86",
            "start_line": 69
          }
        ],
        "template": "In Markor, move the note {file_name} from {source_folder} to {destination_folder}."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "In Markor, move the note {file_name} from {source_folder} to {destination_folder}.",
      "optimal_steps": "7",
      "tags": [
        "parameterized",
        "complex_ui_understanding"
      ],
      "task_name": "MarkorMoveNote"
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
