# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "FilesDeleteFile",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 99,
    "task_id": "FilesDeleteFile"
  },
  "integrity": {
    "semantic_record_sha256": "7dbc57f0203feaf2f10a93f579ad850b02a7cad696cb6b881e067f0a66273951",
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
            "qualname": "FilesDeleteFile",
            "source_ref": {
              "ast_sha256": "eac0c775ffd355723ab1e3d79f5459698f2471c9c5096f6b081dd42faadea221",
              "end_line": 124,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "61652ca1182f1c16789e53165ee627e9e423cd0ee56c584f5c572caa66e62827",
              "start_line": 83,
              "symbol": "FilesDeleteFile"
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
            "ast_sha256": "eac0c775ffd355723ab1e3d79f5459698f2471c9c5096f6b081dd42faadea221",
            "end_line": 124,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesDeleteFile",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "61652ca1182f1c16789e53165ee627e9e423cd0ee56c584f5c572caa66e62827",
            "start_line": 83
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "self.delete_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "FilesDeleteFile",
            "owner_module": "android_world.task_evals.single.files",
            "source_ref": {
              "ast_sha256": "750824a38134272e0c9b4a04b7eac80d1dccc6cbfc6a0a1b0b8061d4b906bae2",
              "end_line": 110,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "b35a3d35a422fa75f8ed28dc3b655c8ca07ca9c32f554d6ae5451f89bad2001d",
              "start_line": 108,
              "symbol": "FilesDeleteFile.is_successful"
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
            "ast_sha256": "750824a38134272e0c9b4a04b7eac80d1dccc6cbfc6a0a1b0b8061d4b906bae2",
            "end_line": 110,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesDeleteFile.is_successful",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "b35a3d35a422fa75f8ed28dc3b655c8ca07ca9c32f554d6ae5451f89bad2001d",
            "start_line": 108
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
              "self.delete_file_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "FilesDeleteFile",
            "owner_module": "android_world.task_evals.single.files",
            "source_ref": {
              "ast_sha256": "750824a38134272e0c9b4a04b7eac80d1dccc6cbfc6a0a1b0b8061d4b906bae2",
              "end_line": 110,
              "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
              "path": "android_world/task_evals/single/files.py",
              "snippet_sha256": "b35a3d35a422fa75f8ed28dc3b655c8ca07ca9c32f554d6ae5451f89bad2001d",
              "start_line": 108,
              "symbol": "FilesDeleteFile.is_successful"
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
            "ast_sha256": "750824a38134272e0c9b4a04b7eac80d1dccc6cbfc6a0a1b0b8061d4b906bae2",
            "end_line": 110,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesDeleteFile.is_successful",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "b35a3d35a422fa75f8ed28dc3b655c8ca07ca9c32f554d6ae5451f89bad2001d",
            "start_line": 108
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
      "task_class": "FilesDeleteFile"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self.delete_file_task.initialize_task",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "FilesDeleteFile",
          "owner_module": "android_world.task_evals.single.files",
          "source_ref": {
            "ast_sha256": "30e32f14a19bc55371486a84c8f217defd2b81403faa50ede72d5eaad2860157",
            "end_line": 102,
            "file_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "path": "android_world/task_evals/single/files.py",
            "snippet_sha256": "46c89806d34fd148963e5ef7e3f26bc2621625372a6c9300986f66b14544d763",
            "start_line": 100,
            "symbol": "FilesDeleteFile.initialize_task"
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
          "ast_sha256": "30e32f14a19bc55371486a84c8f217defd2b81403faa50ede72d5eaad2860157",
          "end_line": 102,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesDeleteFile.initialize_task",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "46c89806d34fd148963e5ef7e3f26bc2621625372a6c9300986f66b14544d763",
          "start_line": 100
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
        "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area."
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
        "subfolder"
      ],
      "metadata_template": "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesDeleteFile",
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
        "owner_qualname": "FilesDeleteFile.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesDeleteFile.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesDeleteFile.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
        "source_sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7"
      },
      {
        "owner_module": "android_world.task_evals.single.files",
        "owner_qualname": "FilesDeleteFile.initialize_task",
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
        "owner_qualname": "FilesDeleteFile.is_successful",
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
        "owner_qualname": "FilesDeleteFile.is_successful",
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
        "file_name",
        "noise_candidates",
        "seed",
        "subfolder"
      ],
      "observed_parameter_types": {
        "file_name": [
          "builtins.str"
        ],
        "noise_candidates": [
          "builtins.list"
        ],
        "seed": [
          "builtins.int"
        ],
        "subfolder": [
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
          "ast_sha256": "eac0c775ffd355723ab1e3d79f5459698f2471c9c5096f6b081dd42faadea221",
          "end_line": 124,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesDeleteFile.schema",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "61652ca1182f1c16789e53165ee627e9e423cd0ee56c584f5c572caa66e62827",
          "start_line": 83
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/files.py",
          "ast_sha256": "5e93b0bf7e5d01ac5afe2734da697635530d7f9173bbb01793f92091b66bf68c",
          "end_line": 124,
          "owner_module": "android_world.task_evals.single.files",
          "owner_qualname": "FilesDeleteFile.generate_random_params",
          "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
          "snippet_sha256": "2b601d075c55dc6f5314bef12a95892b5021e95874f52603bbf5b5acc9a7601b",
          "start_line": 112
        }
      ],
      "value": {
        "properties": {
          "file_name": {
            "type": "string"
          },
          "subfolder": {
            "type": "string"
          }
        },
        "required": [
          "file_name"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/FilesDeleteFile/canonical_task_semantics.json",
      "sha256": "7dbc57f0203feaf2f10a93f579ad850b02a7cad696cb6b881e067f0a66273951"
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
              "dispatch_goal_model": "Delete the file sure_ant_2023_09_19.mp3 from the Android filesystem located in the Music folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "af0f8409cc020a5f8f907db29f353bcf1899a095ba9e76d634b65694db2ae1b7",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file fancy_wolf_2023_03_02.jpg from the Android filesystem located in the DCIM folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "c5be559f0338cc3073cbd03ad9af1a96d4b1c57fc245ae660c77ea79aeaad762",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file TPtL_clever_fish.mp3 from the Android filesystem located in the Alarms folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "2519cb0e63b7b9f55c9a6ca8722d135dd85616fd4976bf8d6166a75ad639b76b",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file fine_igloo_2023_08_31.pdf from the Android filesystem located in the Documents folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "6ee092adffabaccecff4390d41a0e280f3866402e42214fbe1d6d95e879baac6",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file fancy_guitar_edited.pdf from the Android filesystem located in the Documents folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "ea226611f77fadd24308cbb9e347eed5f91f476f230c474b783ec2d78bf9f706",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file 0Wpd_strong_vase.mp3 from the Android filesystem located in the Podcasts folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "4f6c880e1e66498fb278ea4f9241270db2912048e4f1e53423ab818b59b9819e",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file backup_funny_zebra.mp4 from the Android filesystem located in the Movies folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "005becabd3cb3050f45539d06d156a41344aada3b1eec2ca5e75a835a05a3f9d",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the file fair_fox_FKlF.mp3 from the Android filesystem located in the Notifications folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "58acc9e48ff0663662eeb7ba2346d06ea1a544c5fa5ca139e6605629d10fe739",
              "parameter_keys": [
                "file_name",
                "noise_candidates",
                "seed",
                "subfolder"
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
                "subfolder"
              ],
              "template": "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area.",
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
            "ast_sha256": "eac0c775ffd355723ab1e3d79f5459698f2471c9c5096f6b081dd42faadea221",
            "end_line": 124,
            "owner_module": "android_world.task_evals.single.files",
            "owner_qualname": "FilesDeleteFile.template",
            "sha256": "b763d38477cb88419b9c0153af8d78fea0b5468509f2868c44fb1765080f22a7",
            "snippet_sha256": "61652ca1182f1c16789e53165ee627e9e423cd0ee56c584f5c572caa66e62827",
            "start_line": 83
          }
        ],
        "template": "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Delete the file {file_name} from the Android filesystem located in the {subfolder} folder within the sdk_gphone_x86_64 storage area.",
      "optimal_steps": "4",
      "tags": [
        "data_edit",
        "parameterized"
      ],
      "task_name": "FilesDeleteFile"
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
