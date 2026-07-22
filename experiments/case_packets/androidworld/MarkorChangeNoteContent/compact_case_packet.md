# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorChangeNoteContent",
    "domain": "androidworld",
    "group": "extra16",
    "selection_rank": 110,
    "task_id": "MarkorChangeNoteContent"
  },
  "integrity": {
    "semantic_record_sha256": "58a46a0e3b77995e2c386840511eddf7de64d1b1d506318c51778d6370427ef3",
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
            "qualname": "MarkorChangeNoteContent",
            "source_ref": {
              "ast_sha256": "1e426ce2f3f279f8e0214a8501c294ab62d0d1f1a4cd9a8bf4305e841cbc8a66",
              "end_line": 731,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "32c3edf2a85201d792f68880434b6a08f2537b69b24aa8d0d9e7ed3274809903",
              "start_line": 653,
              "symbol": "MarkorChangeNoteContent"
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
            "ast_sha256": "1e426ce2f3f279f8e0214a8501c294ab62d0d1f1a4cd9a8bf4305e841cbc8a66",
            "end_line": 731,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorChangeNoteContent",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "32c3edf2a85201d792f68880434b6a08f2537b69b24aa8d0d9e7ed3274809903",
            "start_line": 653
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 3,
            "direct_calls": [
              "file_utils.check_file_content",
              "file_utils.check_file_or_folder_exists",
              "file_utils.convert_to_posix_path",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "new_name",
              "original_name",
              "updated_content"
            ],
            "owner_class": "MarkorChangeNoteContent",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "17d53cdf0f0b351570869f47dff902abbe889048467395fa3b9ce5e876874229",
              "end_line": 721,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "2dcfeac808b4bd9b0ca991824729dfac052dfc1cd0ddb53f00c92837a5d8f4c0",
              "start_line": 700,
              "symbol": "MarkorChangeNoteContent.is_successful"
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
            "ast_sha256": "17d53cdf0f0b351570869f47dff902abbe889048467395fa3b9ce5e876874229",
            "end_line": 721,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorChangeNoteContent.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "2dcfeac808b4bd9b0ca991824729dfac052dfc1cd0ddb53f00c92837a5d8f4c0",
            "start_line": 700
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
            "branch_node_count": 3,
            "direct_calls": [
              "file_utils.check_file_content",
              "file_utils.check_file_or_folder_exists",
              "file_utils.convert_to_posix_path",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "new_name",
              "original_name",
              "updated_content"
            ],
            "owner_class": "MarkorChangeNoteContent",
            "owner_module": "android_world.task_evals.single.markor",
            "source_ref": {
              "ast_sha256": "17d53cdf0f0b351570869f47dff902abbe889048467395fa3b9ce5e876874229",
              "end_line": 721,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "2dcfeac808b4bd9b0ca991824729dfac052dfc1cd0ddb53f00c92837a5d8f4c0",
              "start_line": 700,
              "symbol": "MarkorChangeNoteContent.is_successful"
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
            "ast_sha256": "17d53cdf0f0b351570869f47dff902abbe889048467395fa3b9ce5e876874229",
            "end_line": 721,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorChangeNoteContent.is_successful",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "2dcfeac808b4bd9b0ca991824729dfac052dfc1cd0ddb53f00c92837a5d8f4c0",
            "start_line": 700
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
      "task_class": "MarkorChangeNoteContent"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 1,
          "direct_calls": [
            "RuntimeError",
            "file_utils.check_file_or_folder_exists",
            "file_utils.create_file",
            "super",
            "super.initialize_task",
            "user_data_generation.generate_noise_files",
            "user_data_generation.generate_random_string"
          ],
          "direct_parameter_reads": [
            "original_name"
          ],
          "owner_class": "MarkorChangeNoteContent",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "2e09e790cd33a07105049254437cef2151a2682c30b93cd3155e402143e414e8",
            "end_line": 690,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "a88f7df6d603f8a1f23abfbd6f38f5f4c6b4ddddacd21db6e2a47f80673dfdb7",
            "start_line": 671,
            "symbol": "MarkorChangeNoteContent.initialize_task"
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
          "ast_sha256": "2e09e790cd33a07105049254437cef2151a2682c30b93cd3155e402143e414e8",
          "end_line": 690,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorChangeNoteContent.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "a88f7df6d603f8a1f23abfbd6f38f5f4c6b4ddddacd21db6e2a47f80673dfdb7",
          "start_line": 671
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
        "Update the content of {original_name} to \"{updated_content}\" in Markor and change its name to {new_name}."
      ],
      "comparison_is_semantic_proof": false,
      "differences": [
        {
          "canonical_runtime_templates": [
            "Update the content of {original_name} to \"{updated_content}\" in Markor and change its name to {new_name}."
          ],
          "comparison_status": "mismatch",
          "difference_id": "task_template_vs_runtime_goal",
          "field": "task_template",
          "metadata_value": "Update the content of {file_name} to \"{updated_content}\" in Markor."
        }
      ],
      "fixed_seed_sample_shape_matches": [
        false,
        false,
        false,
        false,
        false,
        false,
        false,
        false
      ],
      "has_difference": true,
      "matches_runtime": false,
      "metadata_placeholders": [
        "file_name",
        "updated_content"
      ],
      "metadata_template": "Update the content of {file_name} to \"{updated_content}\" in Markor.",
      "status": "mismatch"
    },
    "metadata_conflicts": [
      {
        "conflict_type": "missing_required_subgoal",
        "difference_id": "task_template_vs_runtime_goal",
        "materiality": "material",
        "reason": "metadata omits the required rename and does not identify original_name/new_name",
        "resolution": "runtime_goal_and_evaluator_sources_are_canonical",
        "resolution_rule": "runtime_goal_and_evaluator_sources_are_canonical",
        "scope": "metadata_vs_runtime_goal",
        "status": "requires_contract_review"
      }
    ],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorChangeNoteContent",
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
        "owner_qualname": "MarkorChangeNoteContent.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorChangeNoteContent.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorChangeNoteContent.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "MarkorChangeNoteContent.initialize_task",
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
        "owner_qualname": "MarkorChangeNoteContent.is_successful",
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
        "owner_qualname": "MarkorChangeNoteContent.is_successful",
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
        "new_name",
        "original_name",
        "seed",
        "updated_content"
      ],
      "observed_parameter_types": {
        "new_name": [
          "builtins.str"
        ],
        "original_name": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ],
        "updated_content": [
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
          "ast_sha256": "1e426ce2f3f279f8e0214a8501c294ab62d0d1f1a4cd9a8bf4305e841cbc8a66",
          "end_line": 731,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorChangeNoteContent.schema",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "32c3edf2a85201d792f68880434b6a08f2537b69b24aa8d0d9e7ed3274809903",
          "start_line": 653
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "52b7b43196b483817359108edc5d8003ef16247c71a772ed2884d92ca147bbd1",
          "end_line": 731,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "MarkorChangeNoteContent.generate_random_params",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "c503859b53c035578a8d7f2c5bf629ac95e1b378e50a75082e63720791b5defd",
          "start_line": 723
        }
      ],
      "value": {
        "properties": {
          "new_name": {
            "type": "string"
          },
          "original_name": {
            "type": "string"
          },
          "updated_content": {
            "type": "string"
          }
        },
        "required": [
          "original_name",
          "new_name",
          "updated_content"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorChangeNoteContent/canonical_task_semantics.json",
      "sha256": "58a46a0e3b77995e2c386840511eddf7de64d1b1d506318c51778d6370427ef3"
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
              "dispatch_goal_model": "Update the content of qFzW_polite_wolf.txt to \"Mp48Y3tT3QDgAL47D1qX\" in Markor and change its name to 2023_05_25_lively_lamp.md.",
              "dispatch_goal_sha256": "756502c1c83aa06215b0ca0281cd7f68e59cb2323cfc97658c5a368df3292c0c",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of friendly_koala_2023_03_02.txt to \"qXKgtbOa2Q8TGV6IvPV7\" in Markor and change its name to fbZA_active_pig.md.",
              "dispatch_goal_sha256": "5b882578a94f0ea2e79518889a671023006129a5089909fb7e5d38d448a99a4c",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of brave_fish_2023_03_28.txt to \"X1Fx6F32w54A2klokkFw\" in Markor and change its name to copy_glad_nest.txt.",
              "dispatch_goal_sha256": "5a09dd2b4cb75ef357deb3028cf3655a9b21ca461a85edaa5456b4c178f28849",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of final_wise_lamp.txt to \"9DZDNjN1GTPdVKsb1DS2\" in Markor and change its name to kind_mouse_2023_05_13.md.",
              "dispatch_goal_sha256": "f9c6bff7b76d3cfbf9b5f4ddf80b4b0d6056b68a68105af93da7d0b48a987046",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of wise_tree_2023_09_03.md to \"Zq6bNqqkr170x0uyppr6\" in Markor and change its name to kind_banana_XVnH.txt.",
              "dispatch_goal_sha256": "47d68a32f2d6df8b7397082be480fbc42ee5ab04bee793550b712f33723b1bcd",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of good_queen_backup.txt to \"xgpTzl1yVeMBi8aV7kkt\" in Markor and change its name to 2023_07_10_hot_dog.txt.",
              "dispatch_goal_sha256": "a84d3d3fb77081636d2f538e26896df09ead1cdf5313e323335f93d4d35c2d1c",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of eHwd_helpful_jacket.md to \"6Jy8c1rihtYlKNxHddmQ\" in Markor and change its name to oIdJ_clever_bear.md.",
              "dispatch_goal_sha256": "e4714f685328a4bae77ab6561e70d16f8ba4a8d6882a2c24df6ab5fc419b4b24",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Update the content of tough_jelly_FKlF.md to \"87OMjaGdlpbCB0GNEPCr\" in Markor and change its name to 2023_10_03_tough_tree.md.",
              "dispatch_goal_sha256": "81b8d8fbd8714a55c07c6fc9192e9d250c1510357100681dee3a6acbadd27a30",
              "parameter_keys": [
                "new_name",
                "original_name",
                "seed",
                "updated_content"
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
                "new_name",
                "original_name",
                "updated_content"
              ],
              "template": "Update the content of {original_name} to \"{updated_content}\" in Markor and change its name to {new_name}.",
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
            "ast_sha256": "1e426ce2f3f279f8e0214a8501c294ab62d0d1f1a4cd9a8bf4305e841cbc8a66",
            "end_line": 731,
            "owner_module": "android_world.task_evals.single.markor",
            "owner_qualname": "MarkorChangeNoteContent.template",
            "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "snippet_sha256": "32c3edf2a85201d792f68880434b6a08f2537b69b24aa8d0d9e7ed3274809903",
            "start_line": 653
          }
        ],
        "template": "Update the content of {original_name} to \"{updated_content}\" in Markor and change its name to {new_name}."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Update the content of {file_name} to \"{updated_content}\" in Markor.",
      "optimal_steps": "5",
      "tags": [
        "data_entry",
        "requires_setup",
        "parameterized"
      ],
      "task_name": "MarkorChangeNoteContent"
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
