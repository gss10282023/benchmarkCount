# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SystemBluetoothTurnOn",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 2,
    "task_id": "SystemBluetoothTurnOn"
  },
  "integrity": {
    "semantic_record_sha256": "eedb7484580b43f18a93943a6cb7d348b1d36aad3955dae08e41dabc91b14262",
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
            "qualname": "SystemBluetoothTurnOn",
            "source_ref": {
              "ast_sha256": "e5b7ef6e4ed9503a4d6664edf8cc672b7c3939af06c17614d4fce7a231d270c3",
              "end_line": 294,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "08861a9b3de45c230a29e2ecb249bde9d215d74de2893c3fd00084184abe3c33",
              "start_line": 282,
              "symbol": "SystemBluetoothTurnOn"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.system",
            "qualname": "_SystemBluetoothToggle",
            "source_ref": {
              "ast_sha256": "b3cc7e698fef8986990909e9ecfd11f12d801b7c6b06f4d2e688ace92089da72",
              "end_line": 234,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "7ae7367cd751528146333e5847de539c2ef610425a324779cf20610d8241a878",
              "start_line": 211,
              "symbol": "_SystemBluetoothToggle"
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
            "ast_sha256": "e5b7ef6e4ed9503a4d6664edf8cc672b7c3939af06c17614d4fce7a231d270c3",
            "end_line": 294,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "SystemBluetoothTurnOn",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "08861a9b3de45c230a29e2ecb249bde9d215d74de2893c3fd00084184abe3c33",
            "start_line": 282
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "adb_utils.issue_generic_request",
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "on_or_off"
            ],
            "owner_class": "_SystemBluetoothToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "51c075e7c838ae15808eee3ecf2b5accb4264d01ee070fb3c80f1fe1c474e112",
              "end_line": 230,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "665c9ef4d94cd479ffdf2b2dd3afe7d9a58e1ed78ba4b3b54c18e205d31a2dd3",
              "start_line": 223,
              "symbol": "_SystemBluetoothToggle.is_successful"
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
            "ast_sha256": "51c075e7c838ae15808eee3ecf2b5accb4264d01ee070fb3c80f1fe1c474e112",
            "end_line": 230,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBluetoothToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "665c9ef4d94cd479ffdf2b2dd3afe7d9a58e1ed78ba4b3b54c18e205d31a2dd3",
            "start_line": 223
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
              "adb_utils.issue_generic_request",
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "on_or_off"
            ],
            "owner_class": "_SystemBluetoothToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "51c075e7c838ae15808eee3ecf2b5accb4264d01ee070fb3c80f1fe1c474e112",
              "end_line": 230,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "665c9ef4d94cd479ffdf2b2dd3afe7d9a58e1ed78ba4b3b54c18e205d31a2dd3",
              "start_line": 223,
              "symbol": "_SystemBluetoothToggle.is_successful"
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
            "ast_sha256": "51c075e7c838ae15808eee3ecf2b5accb4264d01ee070fb3c80f1fe1c474e112",
            "end_line": 230,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBluetoothToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "665c9ef4d94cd479ffdf2b2dd3afe7d9a58e1ed78ba4b3b54c18e205d31a2dd3",
            "start_line": 223
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
      "task_class": "SystemBluetoothTurnOn"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.toggle_bluetooth",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "SystemBluetoothTurnOn",
          "owner_module": "android_world.task_evals.single.system",
          "source_ref": {
            "ast_sha256": "aba0593db31f776f88b6572981b0d8a6758b74fb1c70559f9ab5e92652c29acc",
            "end_line": 290,
            "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "path": "android_world/task_evals/single/system.py",
            "snippet_sha256": "934a456e28f5fea772b3127fe68ea901a9f29316830ce14867092f6682d300de",
            "start_line": 288,
            "symbol": "SystemBluetoothTurnOn.initialize_task"
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
          "ast_sha256": "aba0593db31f776f88b6572981b0d8a6758b74fb1c70559f9ab5e92652c29acc",
          "end_line": 290,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemBluetoothTurnOn.initialize_task",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "934a456e28f5fea772b3127fe68ea901a9f29316830ce14867092f6682d300de",
          "start_line": 288
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
        "Turn bluetooth {on_or_off}."
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
        "on_or_off"
      ],
      "metadata_template": "Turn bluetooth {on_or_off}.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBluetoothTurnOn",
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
        "owner_qualname": "_SystemBluetoothToggle.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "_SystemBluetoothToggle.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBluetoothTurnOn.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemBluetoothTurnOn.initialize_task",
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
        "owner_qualname": "_SystemBluetoothToggle.is_successful",
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
        "owner_qualname": "_SystemBluetoothToggle.is_successful",
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
        "on_or_off",
        "seed"
      ],
      "observed_parameter_types": {
        "on_or_off": [
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
          "ast_sha256": "b3cc7e698fef8986990909e9ecfd11f12d801b7c6b06f4d2e688ace92089da72",
          "end_line": 234,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "_SystemBluetoothToggle.schema",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "7ae7367cd751528146333e5847de539c2ef610425a324779cf20610d8241a878",
          "start_line": 211
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "fded8ecc542b9d28bd82ce527e0057838b23f175522c49da65ca5b7d75caab07",
          "end_line": 294,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemBluetoothTurnOn.generate_random_params",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "e1225e8494435f5664dd269c145c8fe5abf651ccb73e0971b5713e571a9de576",
          "start_line": 292
        }
      ],
      "value": {
        "properties": {
          "on_or_off": {
            "enum": [
              "on",
              "off"
            ],
            "type": "string"
          }
        },
        "required": [
          "on_or_off"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SystemBluetoothTurnOn/canonical_task_semantics.json",
      "sha256": "eedb7484580b43f18a93943a6cb7d348b1d36aad3955dae08e41dabc91b14262"
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
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Turn bluetooth on.",
              "dispatch_goal_sha256": "91a606c3fb94669a989dbafa0e92a32abe52b56c06be51e6c6cd970d89e85b9d",
              "parameter_keys": [
                "on_or_off",
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
                "on_or_off"
              ],
              "template": "Turn bluetooth {on_or_off}.",
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
            "ast_sha256": "b3cc7e698fef8986990909e9ecfd11f12d801b7c6b06f4d2e688ace92089da72",
            "end_line": 234,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemBluetoothToggle.template",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "7ae7367cd751528146333e5847de539c2ef610425a324779cf20610d8241a878",
            "start_line": 211
          }
        ],
        "template": "Turn bluetooth {on_or_off}."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Turn bluetooth {on_or_off}.",
      "optimal_steps": "2",
      "tags": [
        "screen_reading"
      ],
      "task_name": "SystemBluetoothTurnOn"
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
