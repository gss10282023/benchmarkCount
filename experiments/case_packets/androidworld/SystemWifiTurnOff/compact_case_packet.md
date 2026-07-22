# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SystemWifiTurnOff",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 29,
    "task_id": "SystemWifiTurnOff"
  },
  "integrity": {
    "semantic_record_sha256": "cefd873fb1885dfd7664dc11835cf4f70d4fa9b8bd9c93f5bcd4dd9e78288bdb",
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
            "qualname": "SystemWifiTurnOff",
            "source_ref": {
              "ast_sha256": "1bf2a375244c1effb8467b98b9d13f19c6b5e9b43b3ac8fc8d4c8b63227ec4bc",
              "end_line": 193,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "3a329ac4fbfac4aaf90e94263a2186ab249ccb38335d6980a9cc47f1a92a2320",
              "start_line": 181,
              "symbol": "SystemWifiTurnOff"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.system",
            "qualname": "_SystemWifiToggle",
            "source_ref": {
              "ast_sha256": "dc1b5840fc69934d030086e7bdbbd7b168ceddb1a6dc0a40aa759238a750a900",
              "end_line": 148,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "9c4b3be6194c729294566ada029cac6c5cf31292c1361e26636c7a53b5c33515",
              "start_line": 119,
              "symbol": "_SystemWifiToggle"
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
            "ast_sha256": "1bf2a375244c1effb8467b98b9d13f19c6b5e9b43b3ac8fc8d4c8b63227ec4bc",
            "end_line": 193,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "SystemWifiTurnOff",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "3a329ac4fbfac4aaf90e94263a2186ab249ccb38335d6980a9cc47f1a92a2320",
            "start_line": 181
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
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "on_or_off"
            ],
            "owner_class": "_SystemWifiToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "6371d5f8ff3cd067f93abd949c6458352f73537750f3f79ef38f26e942284b3a",
              "end_line": 144,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "4110531ea3a7a7d625a8f615f43ee38e896a925762512fff68393d57efe4f32f",
              "start_line": 131,
              "symbol": "_SystemWifiToggle.is_successful"
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
            "ast_sha256": "6371d5f8ff3cd067f93abd949c6458352f73537750f3f79ef38f26e942284b3a",
            "end_line": 144,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemWifiToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "4110531ea3a7a7d625a8f615f43ee38e896a925762512fff68393d57efe4f32f",
            "start_line": 131
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
              "res.generic.output.decode",
              "res.generic.output.decode.strip",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "on_or_off"
            ],
            "owner_class": "_SystemWifiToggle",
            "owner_module": "android_world.task_evals.single.system",
            "source_ref": {
              "ast_sha256": "6371d5f8ff3cd067f93abd949c6458352f73537750f3f79ef38f26e942284b3a",
              "end_line": 144,
              "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
              "path": "android_world/task_evals/single/system.py",
              "snippet_sha256": "4110531ea3a7a7d625a8f615f43ee38e896a925762512fff68393d57efe4f32f",
              "start_line": 131,
              "symbol": "_SystemWifiToggle.is_successful"
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
            "ast_sha256": "6371d5f8ff3cd067f93abd949c6458352f73537750f3f79ef38f26e942284b3a",
            "end_line": 144,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemWifiToggle.is_successful",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "4110531ea3a7a7d625a8f615f43ee38e896a925762512fff68393d57efe4f32f",
            "start_line": 131
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
      "task_class": "SystemWifiTurnOff"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.toggle_wifi",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "SystemWifiTurnOff",
          "owner_module": "android_world.task_evals.single.system",
          "source_ref": {
            "ast_sha256": "52fe97fb9f2fca9c928f2510ad4c0676d9356f90fca41e23563e89256ca1e51f",
            "end_line": 189,
            "file_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "path": "android_world/task_evals/single/system.py",
            "snippet_sha256": "8cfe1335ab270ef22229f28d54f383b6fabbeef5d26f38cf9093fc30b011f057",
            "start_line": 187,
            "symbol": "SystemWifiTurnOff.initialize_task"
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
          "ast_sha256": "52fe97fb9f2fca9c928f2510ad4c0676d9356f90fca41e23563e89256ca1e51f",
          "end_line": 189,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemWifiTurnOff.initialize_task",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "8cfe1335ab270ef22229f28d54f383b6fabbeef5d26f38cf9093fc30b011f057",
          "start_line": 187
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
        "Turn wifi {on_or_off}."
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
      "metadata_template": "Turn wifi {on_or_off}.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemWifiTurnOff",
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
        "owner_qualname": "_SystemWifiToggle.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "_SystemWifiToggle.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemWifiTurnOff.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
        "source_sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c"
      },
      {
        "owner_module": "android_world.task_evals.single.system",
        "owner_qualname": "SystemWifiTurnOff.initialize_task",
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
        "owner_qualname": "_SystemWifiToggle.is_successful",
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
        "owner_qualname": "_SystemWifiToggle.is_successful",
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
          "ast_sha256": "dc1b5840fc69934d030086e7bdbbd7b168ceddb1a6dc0a40aa759238a750a900",
          "end_line": 148,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "_SystemWifiToggle.schema",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "9c4b3be6194c729294566ada029cac6c5cf31292c1361e26636c7a53b5c33515",
          "start_line": 119
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/system.py",
          "ast_sha256": "371eaca1122acd0ab8fc5d8053491f88e7ead496f608836598c35fff2b5dcd97",
          "end_line": 193,
          "owner_module": "android_world.task_evals.single.system",
          "owner_qualname": "SystemWifiTurnOff.generate_random_params",
          "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
          "snippet_sha256": "49e4baa743cb8c10ad934efc08d8a9647c732d5649c03b3c0ec3f68a49ddc0f2",
          "start_line": 191
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SystemWifiTurnOff/canonical_task_semantics.json",
      "sha256": "cefd873fb1885dfd7664dc11835cf4f70d4fa9b8bd9c93f5bcd4dd9e78288bdb"
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "dispatch_goal_model": "Turn wifi off.",
              "dispatch_goal_sha256": "837623c813dda1078c8e71c7375ee0e3467cd375e0dbb8d8ca30c94106ea4aca",
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
              "template": "Turn wifi {on_or_off}.",
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
            "ast_sha256": "dc1b5840fc69934d030086e7bdbbd7b168ceddb1a6dc0a40aa759238a750a900",
            "end_line": 148,
            "owner_module": "android_world.task_evals.single.system",
            "owner_qualname": "_SystemWifiToggle.template",
            "sha256": "cea0c735f61fd6a42d3cec6e9837218073b01ebf5ec9086c7981ad485f867e1c",
            "snippet_sha256": "9c4b3be6194c729294566ada029cac6c5cf31292c1361e26636c7a53b5c33515",
            "start_line": 119
          }
        ],
        "template": "Turn wifi {on_or_off}."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Turn wifi {on_or_off}.",
      "optimal_steps": "3",
      "tags": [
        "screen_reading"
      ],
      "task_name": "SystemWifiTurnOff"
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
