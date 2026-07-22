# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleDrawProCreateDrawing",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 28,
    "task_id": "SimpleDrawProCreateDrawing"
  },
  "integrity": {
    "semantic_record_sha256": "686ea78a7ca7a6914846e538e3c4f7b4f49ae429abad842c02052594a54b7da4",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "c088d6a7a1a029da54c53fc43212c08f15c4af18c919b4856a634274eff3ca10",
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
      "canonical_module": "android_world.task_evals.single.simple_draw_pro",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.simple_draw_pro",
            "qualname": "SimpleDrawProCreateDrawing",
            "source_ref": {
              "ast_sha256": "6f4d4cad8f02df5afa6371b781e777b3258f6791b52957cd8ebc02feb98d5a23",
              "end_line": 87,
              "file_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
              "path": "android_world/task_evals/single/simple_draw_pro.py",
              "snippet_sha256": "39d9bbdd52dd2e75c0d176512d7141640c787b555d0b92be6a7513195541962d",
              "start_line": 27,
              "symbol": "SimpleDrawProCreateDrawing"
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
        "runtime_reported_module": "android_world.task_evals.single.simple_draw_pro",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
            "ast_sha256": "6f4d4cad8f02df5afa6371b781e777b3258f6791b52957cd8ebc02feb98d5a23",
            "end_line": 87,
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "owner_qualname": "SimpleDrawProCreateDrawing",
            "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
            "snippet_sha256": "39d9bbdd52dd2e75c0d176512d7141640c787b555d0b92be6a7513195541962d",
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
            "owner_class": "SimpleDrawProCreateDrawing",
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "source_ref": {
              "ast_sha256": "167fbb5d425c9a88b34c82ca9fe303f82b9989a1cf2ca801209cca5b41e19dde",
              "end_line": 58,
              "file_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
              "path": "android_world/task_evals/single/simple_draw_pro.py",
              "snippet_sha256": "fd87d50a498fc6149b666cd1198c8a60fe36855849affb7bbdf481213222ca21",
              "start_line": 52,
              "symbol": "SimpleDrawProCreateDrawing.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
            "ast_sha256": "167fbb5d425c9a88b34c82ca9fe303f82b9989a1cf2ca801209cca5b41e19dde",
            "end_line": 58,
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "owner_qualname": "SimpleDrawProCreateDrawing.is_successful",
            "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
            "snippet_sha256": "fd87d50a498fc6149b666cd1198c8a60fe36855849affb7bbdf481213222ca21",
            "start_line": 52
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
            "owner_class": "SimpleDrawProCreateDrawing",
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "source_ref": {
              "ast_sha256": "167fbb5d425c9a88b34c82ca9fe303f82b9989a1cf2ca801209cca5b41e19dde",
              "end_line": 58,
              "file_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
              "path": "android_world/task_evals/single/simple_draw_pro.py",
              "snippet_sha256": "fd87d50a498fc6149b666cd1198c8a60fe36855849affb7bbdf481213222ca21",
              "start_line": 52,
              "symbol": "SimpleDrawProCreateDrawing.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
            "ast_sha256": "167fbb5d425c9a88b34c82ca9fe303f82b9989a1cf2ca801209cca5b41e19dde",
            "end_line": 58,
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "owner_qualname": "SimpleDrawProCreateDrawing.is_successful",
            "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
            "snippet_sha256": "fd87d50a498fc6149b666cd1198c8a60fe36855849affb7bbdf481213222ca21",
            "start_line": 52
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
      "task_class": "SimpleDrawProCreateDrawing"
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
          "owner_class": "SimpleDrawProCreateDrawing",
          "owner_module": "android_world.task_evals.single.simple_draw_pro",
          "source_ref": {
            "ast_sha256": "a287b16c379c4bbc0f673973cc9404e77448ac88c553510f7ec4d1ab81ec37d1",
            "end_line": 50,
            "file_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
            "path": "android_world/task_evals/single/simple_draw_pro.py",
            "snippet_sha256": "b885f8973e5af6e82f5f989652326216214f76fc12272931dd9ebfa659dc2432",
            "start_line": 48,
            "symbol": "SimpleDrawProCreateDrawing.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
          "ast_sha256": "a287b16c379c4bbc0f673973cc9404e77448ac88c553510f7ec4d1ab81ec37d1",
          "end_line": 50,
          "owner_module": "android_world.task_evals.single.simple_draw_pro",
          "owner_qualname": "SimpleDrawProCreateDrawing.initialize_task",
          "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
          "snippet_sha256": "b885f8973e5af6e82f5f989652326216214f76fc12272931dd9ebfa659dc2432",
          "start_line": 48
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
        "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area."
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
        "file_name"
      ],
      "metadata_template": "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
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
        "owner_module": "android_world.task_evals.single.simple_draw_pro",
        "owner_qualname": "SimpleDrawProCreateDrawing.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
        "source_sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
          "ast_sha256": "6f4d4cad8f02df5afa6371b781e777b3258f6791b52957cd8ebc02feb98d5a23",
          "end_line": 87,
          "owner_module": "android_world.task_evals.single.simple_draw_pro",
          "owner_qualname": "SimpleDrawProCreateDrawing.schema",
          "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
          "snippet_sha256": "39d9bbdd52dd2e75c0d176512d7141640c787b555d0b92be6a7513195541962d",
          "start_line": 27
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
          "ast_sha256": "df435ddb9b1b6993d959abf3eef607d7db84ba3ff733be8436ddb215ab7e69e2",
          "end_line": 83,
          "owner_module": "android_world.task_evals.single.simple_draw_pro",
          "owner_qualname": "SimpleDrawProCreateDrawing.generate_random_params",
          "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
          "snippet_sha256": "6bf7bcd2bb74a76c7057814e6212865e650a5be0ba63266de46d9fe0cc9e487b",
          "start_line": 60
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleDrawProCreateDrawing/canonical_task_semantics.json",
      "sha256": "686ea78a7ca7a6914846e538e3c4f7b4f49ae429abad842c02052594a54b7da4"
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it adipiscing_sure_ant_2023_09_19.svg. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "b99e84ee15a301fa61d5c1a4521f93d379e2d6b2e64cba34bce912585fcb176a",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it ipsum_EBOW_sure_elephant.png. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "7b7bc697d93ad99c7de62ea9aab6450d633ada632be445fe13eebf84602e4a79",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it elit_brave_fish_2023_03_28.jpg. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "2c0ab152f71ae725836541fa9191a8b1d83b4f5a613316720532624d30893f7c",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it ipsum_cool_island_MeaZ.svg. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "6057e69d5c6e078ef20ec3b936bf67bff2be0bd0013d195fc513ff37eb66f8dc",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it ipsum_gentle_unicorn_jey4.png. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "a8f24390cbff68a7508ecc73e32042365dad1e74da5bb2d1e9a07444b39ba8df",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it amet_edited_safe_watch.png. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "b68d90698df805b0e050db56fe1cc7c7ed60cee5b108bf929b4828a71cb3798f",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it dolor_backup_funny_zebra.jpg. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "eab813919f599c933782abcb810e2d2aa4b70fa2b2cf6868fbed74a259ef33cf",
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
              "dispatch_goal_model": "Create a new drawing in Simple Draw Pro. Name it sit_fair_fox_FKlF.jpg. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
              "dispatch_goal_sha256": "d85f881db3910404e6f26d8dd5c70069661783279528f953981ad03639f79743",
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
                "file_name"
              ],
              "template": "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/simple_draw_pro.py",
            "ast_sha256": "6f4d4cad8f02df5afa6371b781e777b3258f6791b52957cd8ebc02feb98d5a23",
            "end_line": 87,
            "owner_module": "android_world.task_evals.single.simple_draw_pro",
            "owner_qualname": "SimpleDrawProCreateDrawing.template",
            "sha256": "b23bda609a5933e5e22e90cc2af5bc6be58eb43346e9e360fae21abbf6ba990d",
            "snippet_sha256": "39d9bbdd52dd2e75c0d176512d7141640c787b555d0b92be6a7513195541962d",
            "start_line": 27
          }
        ],
        "template": "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a new drawing in Simple Draw Pro. Name it {file_name}. Save it in the Pictures folder within the sdk_gphone_x86_64 storage area.",
      "optimal_steps": "9",
      "tags": [
        "data_entry",
        "parameterized"
      ],
      "task_name": "SimpleDrawProCreateDrawing"
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
