# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SaveCopyOfReceiptTaskEval",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 70,
    "task_id": "SaveCopyOfReceiptTaskEval"
  },
  "integrity": {
    "semantic_record_sha256": "0597a3292cf09be0500944f7888c1b4c66f741cef9097549cc70c6ef0efca455",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "db956ce5bc5d24281ae65520248333e626dd4300e024a3cd76ca03d6c0ebc974",
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
      "canonical_module": "android_world.task_evals.single.simple_gallery_pro",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.simple_gallery_pro",
            "qualname": "SaveCopyOfReceiptTaskEval",
            "source_ref": {
              "ast_sha256": "f99697a6ed20f068bae4c480bb5b6b51c43fb383ab7eb34c07db84b403d46a80",
              "end_line": 81,
              "file_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
              "path": "android_world/task_evals/single/simple_gallery_pro.py",
              "snippet_sha256": "fbab84ad211ffd719924723970d03cdf25e396f5438f29a5487386ef2a384040",
              "start_line": 27,
              "symbol": "SaveCopyOfReceiptTaskEval"
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
        "runtime_reported_module": "android_world.task_evals.single.simple_gallery_pro",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
            "ast_sha256": "f99697a6ed20f068bae4c480bb5b6b51c43fb383ab7eb34c07db84b403d46a80",
            "end_line": 81,
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "owner_qualname": "SaveCopyOfReceiptTaskEval",
            "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
            "snippet_sha256": "fbab84ad211ffd719924723970d03cdf25e396f5438f29a5487386ef2a384040",
            "start_line": 27
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
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "file_name"
            ],
            "owner_class": "SaveCopyOfReceiptTaskEval",
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "source_ref": {
              "ast_sha256": "48ec9fc42599b95aa1f317be8c0af5ba3502223bfe92b5bba817b5e450f0c35d",
              "end_line": 69,
              "file_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
              "path": "android_world/task_evals/single/simple_gallery_pro.py",
              "snippet_sha256": "77a30e7a639f5508a226b33cae722ca9f1a977ece0dd4a0dd54672bb1f889266",
              "start_line": 59,
              "symbol": "SaveCopyOfReceiptTaskEval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
            "ast_sha256": "48ec9fc42599b95aa1f317be8c0af5ba3502223bfe92b5bba817b5e450f0c35d",
            "end_line": 69,
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "owner_qualname": "SaveCopyOfReceiptTaskEval.is_successful",
            "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
            "snippet_sha256": "77a30e7a639f5508a226b33cae722ca9f1a977ece0dd4a0dd54672bb1f889266",
            "start_line": 59
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
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "file_name"
            ],
            "owner_class": "SaveCopyOfReceiptTaskEval",
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "source_ref": {
              "ast_sha256": "48ec9fc42599b95aa1f317be8c0af5ba3502223bfe92b5bba817b5e450f0c35d",
              "end_line": 69,
              "file_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
              "path": "android_world/task_evals/single/simple_gallery_pro.py",
              "snippet_sha256": "77a30e7a639f5508a226b33cae722ca9f1a977ece0dd4a0dd54672bb1f889266",
              "start_line": 59,
              "symbol": "SaveCopyOfReceiptTaskEval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
            "ast_sha256": "48ec9fc42599b95aa1f317be8c0af5ba3502223bfe92b5bba817b5e450f0c35d",
            "end_line": 69,
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "owner_qualname": "SaveCopyOfReceiptTaskEval.is_successful",
            "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
            "snippet_sha256": "77a30e7a639f5508a226b33cae722ca9f1a977ece0dd4a0dd54672bb1f889266",
            "start_line": 59
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
      "task_class": "SaveCopyOfReceiptTaskEval"
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
            "receipt_image.save",
            "super",
            "super.initialize_task",
            "user_data_generation.clear_device_storage"
          ],
          "direct_parameter_reads": [
            "file_name",
            "receipt_image"
          ],
          "owner_class": "SaveCopyOfReceiptTaskEval",
          "owner_module": "android_world.task_evals.single.simple_gallery_pro",
          "source_ref": {
            "ast_sha256": "3848490d15d32c2e51fa6e4e9056ccceb3e8f97a4c11ca199ff230dcbadf053b",
            "end_line": 53,
            "file_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
            "path": "android_world/task_evals/single/simple_gallery_pro.py",
            "snippet_sha256": "42a45ba2f01d277575d4373e537a912c38bb9d98f2525788c1a6e7accf26b7d6",
            "start_line": 41,
            "symbol": "SaveCopyOfReceiptTaskEval.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
          "ast_sha256": "3848490d15d32c2e51fa6e4e9056ccceb3e8f97a4c11ca199ff230dcbadf053b",
          "end_line": 53,
          "owner_module": "android_world.task_evals.single.simple_gallery_pro",
          "owner_qualname": "SaveCopyOfReceiptTaskEval.initialize_task",
          "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
          "snippet_sha256": "42a45ba2f01d277575d4373e537a912c38bb9d98f2525788c1a6e7accf26b7d6",
          "start_line": 41
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
        "In Simple Gallery Pro, copy {file_name} in DCIM and save a copy with the same name in Download"
      ],
      "comparison_is_semantic_proof": false,
      "differences": [
        {
          "canonical_runtime_templates": [
            "In Simple Gallery Pro, copy {file_name} in DCIM and save a copy with the same name in Download"
          ],
          "comparison_status": "mismatch",
          "difference_id": "task_template_vs_runtime_goal",
          "field": "task_template",
          "metadata_value": "Copy {file_name} in DCIM and save a copy with the same name in Download"
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
        "file_name"
      ],
      "metadata_template": "Copy {file_name} in DCIM and save a copy with the same name in Download",
      "status": "mismatch"
    },
    "metadata_conflicts": [
      {
        "conflict_type": "runtime_app_name_clarification",
        "difference_id": "task_template_vs_runtime_goal",
        "materiality": "non_material",
        "reason": "runtime prepends 'In Simple Gallery Pro' to the same DCIM-to-Download copy task described by metadata; this clarifies the target app without changing the required state",
        "resolution": "runtime_goal_text_is_canonical",
        "resolution_rule": "runtime_goal_text_is_canonical",
        "scope": "metadata_vs_runtime_goal",
        "status": "resolved"
      }
    ],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
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
        "owner_module": "android_world.task_evals.single.simple_gallery_pro",
        "owner_qualname": "SaveCopyOfReceiptTaskEval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
        "source_sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5"
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
        "receipt_image",
        "seed"
      ],
      "observed_parameter_types": {
        "file_name": [
          "builtins.str"
        ],
        "receipt_image": [
          "PIL.Image.Image"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
          "ast_sha256": "f99697a6ed20f068bae4c480bb5b6b51c43fb383ab7eb34c07db84b403d46a80",
          "end_line": 81,
          "owner_module": "android_world.task_evals.single.simple_gallery_pro",
          "owner_qualname": "SaveCopyOfReceiptTaskEval.schema",
          "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
          "snippet_sha256": "fbab84ad211ffd719924723970d03cdf25e396f5438f29a5487386ef2a384040",
          "start_line": 27
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
          "ast_sha256": "2b981cb6465df63d290eb12f916f180a75258ba33f7bc000f2aa3d550adf134b",
          "end_line": 81,
          "owner_module": "android_world.task_evals.single.simple_gallery_pro",
          "owner_qualname": "SaveCopyOfReceiptTaskEval.generate_random_params",
          "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
          "snippet_sha256": "1b3afc63b7345f52592c4aa4c14bb890365ddb316844bb016d5741c73b5f6023",
          "start_line": 71
        }
      ],
      "value": {
        "properties": {},
        "required": [],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SaveCopyOfReceiptTaskEval/canonical_task_semantics.json",
      "sha256": "0597a3292cf09be0500944f7888c1b4c66f741cef9097549cc70c6ef0efca455"
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
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_alert_zebra_w3ni.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "ae63222f523ce793511936b7666efc1ffb515d6651421aa995b881c329df5161",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_fbZA_active_pig.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "78e962b6d4c8ab694ea766945c1a19aab72e62f1f5dd22502c0fa282f75ce15b",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_safe_quilt_LLKj.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "380f31fb6f71a9a5ade5a425da3d0c66ee51d5e9e4d781b1e4e6825aae4f36e2",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_2023_08_29_great_lamp.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "b263687a0db6f620a2066d94c306549dec67dd450f48c3c47ffad5d9ced5d6d4",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_2023_07_25_funny_fish.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "f550ce20927e2d6e9cd227af2dd9cedebca5c4619e9ed807dbe1a5959dd67eb7",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_2023_03_22_happy_deer.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "932788edc061ea404b349a72468bfd43c04bc687353d81f7b3a452b9f86a96d8",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_4nfz_cool_guitar.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "bd53d6bd21e398d15748c770f9350f96dc1184a2d843194faaa62b46d1e13fce",
              "parameter_keys": [
                "file_name",
                "receipt_image",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Gallery Pro, copy receipt_fsfY_smart_goat.jpg in DCIM and save a copy with the same name in Download",
              "dispatch_goal_sha256": "88bf3a1c9e4374adbaab92f2d1b008232849cfe0258f143bf5f83b328cd1783b",
              "parameter_keys": [
                "file_name",
                "receipt_image",
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
                "file_name"
              ],
              "template": "In Simple Gallery Pro, copy {file_name} in DCIM and save a copy with the same name in Download",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_gallery_pro.py",
            "ast_sha256": "f99697a6ed20f068bae4c480bb5b6b51c43fb383ab7eb34c07db84b403d46a80",
            "end_line": 81,
            "owner_module": "android_world.task_evals.single.simple_gallery_pro",
            "owner_qualname": "SaveCopyOfReceiptTaskEval.template",
            "sha256": "0d78ef0bafc615c6b7a34507b0243b2003eebfd2bc44a9d92beae9885b7cb0c5",
            "snippet_sha256": "fbab84ad211ffd719924723970d03cdf25e396f5438f29a5487386ef2a384040",
            "start_line": 27
          }
        ],
        "template": "In Simple Gallery Pro, copy {file_name} in DCIM and save a copy with the same name in Download"
      },
      "difficulty": "hard",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Copy {file_name} in DCIM and save a copy with the same name in Download",
      "optimal_steps": "8",
      "tags": [
        "parameterized",
        "complex_ui_understanding"
      ],
      "task_name": "SaveCopyOfReceiptTaskEval"
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
