# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SystemBrightnessMax",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 89,
    "task_id": "SystemBrightnessMax"
  },
  "integrity": {
    "semantic_record_sha256": "6ea5e7567f38f66ac85252fbdcb0954ae3d6b8bef1c1b963165c1892f6b68666",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "d9f3cf556be0de5ddad7bde41acc5d81bebbb790648fa9f345fa2468f3e15df5",
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
            "qualname": "SystemBrightnessMax",
            "source_ref": {
              "ast_sha256": "5dee37fff05bf53c3eb22c053256181c4ccf51e59463944739e865cfd3a0755b",
              "end_line": 116,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "5052fb708b38533b167afd46d76e13b97ecbf3a114856cb58df88471f9408f45",
              "start_line": 104,
              "symbol": "SystemBrightnessMax"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.system",
            "qualname": "_SystemBrightnessToggle",
            "source_ref": {
              "ast_sha256": "af74c05da0f3c051b92cca7c6aa1ef72c359e782dbd37e61be2cf025483c8b9d",
              "end_line": 56,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "a6533a86194504c637920bcfb57d82151153af0f1bf71376a9f7efc368fbfd8d",
              "start_line": 29,
              "symbol": "_SystemBrightnessToggle"
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
            "ast_sha256": "5dee37fff05bf53c3eb22c053256181c4ccf51e59463944739e865cfd3a0755b",
            "end_line": 116,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "SystemBrightnessMax",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "5052fb708b38533b167afd46d76e13b97ecbf3a114856cb58df88471f9408f45",
            "start_line": 104
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 3,
            "direct_calls": [
              "adb_utils.issue_generic_request",
              "int",
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "max_or_min"
            ],
            "owner_class": "_SystemBrightnessToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "7b750219e3211aa735123b220c2d175d022056d6d7ed83f9669e99166abe956b",
              "end_line": 52,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "161b44f4dffaf0c17cd9323ca33241298606f74174f7468926f323cddfec8872",
              "start_line": 41,
              "symbol": "_SystemBrightnessToggle.is_successful"
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
            "ast_sha256": "7b750219e3211aa735123b220c2d175d022056d6d7ed83f9669e99166abe956b",
            "end_line": 52,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBrightnessToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "161b44f4dffaf0c17cd9323ca33241298606f74174f7468926f323cddfec8872",
            "start_line": 41
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
              "adb_utils.issue_generic_request",
              "int",
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "max_or_min"
            ],
            "owner_class": "_SystemBrightnessToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "7b750219e3211aa735123b220c2d175d022056d6d7ed83f9669e99166abe956b",
              "end_line": 52,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "161b44f4dffaf0c17cd9323ca33241298606f74174f7468926f323cddfec8872",
              "start_line": 41,
              "symbol": "_SystemBrightnessToggle.is_successful"
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
            "ast_sha256": "7b750219e3211aa735123b220c2d175d022056d6d7ed83f9669e99166abe956b",
            "end_line": 52,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBrightnessToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "161b44f4dffaf0c17cd9323ca33241298606f74174f7468926f323cddfec8872",
            "start_line": 41
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
      "task_class": "SystemBrightnessMax"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.set_brightness",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "SystemBrightnessMax",
          "owner_module": "android_world.task_evals.single.system",
          "source_ref": {
            "ast_sha256": "8e510838116f7e96792dc760b53c5f119369bf1f15b0de3a39175fa3f256dbe7",
            "end_line": 112,
            "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "path": "android_world/task_evals/single/system.py",
            "snippet_sha256": "9549469ca7733446396591977468a79575e1b1aec0c79d6e85bfd313c8f3ccf6",
            "start_line": 110,
            "symbol": "SystemBrightnessMax.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "8e510838116f7e96792dc760b53c5f119369bf1f15b0de3a39175fa3f256dbe7",
          "end_line": 112,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemBrightnessMax.initialize_task",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "9549469ca7733446396591977468a79575e1b1aec0c79d6e85bfd313c8f3ccf6",
          "start_line": 110
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
        "Turn brightness to the {max_or_min} value."
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
        "max_or_min"
      ],
      "metadata_template": "Turn brightness to the {max_or_min} value.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBrightnessMax",
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
        "owner_qualname": "_SystemBrightnessToggle.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "_SystemBrightnessToggle.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBrightnessMax.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBrightnessMax.initialize_task",
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
        "owner_qualname": "_SystemBrightnessToggle.is_successful",
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
        "owner_qualname": "_SystemBrightnessToggle.is_successful",
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
        "max_or_min",
        "seed"
      ],
      "observed_parameter_types": {
        "max_or_min": [
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
          "ast_sha256": "af74c05da0f3c051b92cca7c6aa1ef72c359e782dbd37e61be2cf025483c8b9d",
          "end_line": 56,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "_SystemBrightnessToggle.schema",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "a6533a86194504c637920bcfb57d82151153af0f1bf71376a9f7efc368fbfd8d",
          "start_line": 29
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "9bda0aba85d58f9c5b148d4ab242e19bf7818dfed97cf2bf14139fc20eb4e194",
          "end_line": 116,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemBrightnessMax.generate_random_params",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "fda0b024b61cc01cacd8089e2df5c8de0cdb70d2a50280b4d52675d2756f8726",
          "start_line": 114
        }
      ],
      "value": {
        "properties": {
          "max_or_min": {
            "enum": [
              "max",
              "min"
            ],
            "type": "string"
          }
        },
        "required": [
          "max_or_min"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SystemBrightnessMax/canonical_task_semantics.json",
      "sha256": "6ea5e7567f38f66ac85252fbdcb0954ae3d6b8bef1c1b963165c1892f6b68666"
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
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn brightness to the max value.",
              "dispatch_goal_sha256": "db11de78f1947dd6abcbaf6da4aee282094bea0eceafc2f6999090f782de7238",
              "parameter_keys": [
                "max_or_min",
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
                "max_or_min"
              ],
              "template": "Turn brightness to the {max_or_min} value.",
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
            "ast_sha256": "af74c05da0f3c051b92cca7c6aa1ef72c359e782dbd37e61be2cf025483c8b9d",
            "end_line": 56,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBrightnessToggle.template",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "a6533a86194504c637920bcfb57d82151153af0f1bf71376a9f7efc368fbfd8d",
            "start_line": 29
          }
        ],
        "template": "Turn brightness to the {max_or_min} value."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Turn brightness to the {max_or_min} value.",
      "optimal_steps": "3",
      "tags": [
        ""
      ],
      "task_name": "SystemBrightnessMax"
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
