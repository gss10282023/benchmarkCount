# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "CameraTakePhoto",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 41,
    "task_id": "CameraTakePhoto"
  },
  "integrity": {
    "semantic_record_sha256": "91625bd45349d0d9322a50d1df5fb175b8cdb93459eaae92941ff39d0919d81c",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "15987255019b21049f6e572f87c9e0c0e7346c5505429b46a4f3ea4cd5b255cd",
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
      "canonical_module": "android_world.task_evals.single.camera",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.camera",
            "qualname": "CameraTakePhoto",
            "source_ref": {
              "ast_sha256": "85a182f0486c714787eafd97298d3808ea371de6985f57bbfcbc7357f535bc87",
              "end_line": 133,
              "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
              "path": "android_world/task_evals/single/camera.py",
              "snippet_sha256": "9f3badf02916029755cbb048e14e34c184b11e1c72bf22fdd77c200ec129b513",
              "start_line": 92,
              "symbol": "CameraTakePhoto"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.camera",
            "qualname": "_Camera",
            "source_ref": {
              "ast_sha256": "b136e66058db70ab45c098b49f640f3565edcaa90db3b09055c58d08c5936864",
              "end_line": 43,
              "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
              "path": "android_world/task_evals/single/camera.py",
              "snippet_sha256": "892a4fc8af454c2597aefb56728f97738d55f61b36a76db8b164d30eecdb7f5c",
              "start_line": 27,
              "symbol": "_Camera"
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
        "runtime_reported_module": "android_world.task_evals.single.camera",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
            "ast_sha256": "85a182f0486c714787eafd97298d3808ea371de6985f57bbfcbc7357f535bc87",
            "end_line": 133,
            "owner_module": "android_world.task_evals.single.camera",
            "owner_qualname": "CameraTakePhoto",
            "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "snippet_sha256": "9f3badf02916029755cbb048e14e34c184b11e1c72bf22fdd77c200ec129b513",
            "start_line": 92
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "adb_utils.issue_generic_request",
              "contents.generic.output.decode",
              "contents.generic.output.decode.replace",
              "contents.generic.output.decode.replace.split",
              "len",
              "logging.info",
              "set",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "CameraTakePhoto",
            "owner_module": "android_world.task_evals.single.camera",
            "source_ref": {
              "ast_sha256": "506c3c2d4610f721ee001ea6cf5d841782e7aed0888f0d21c7680da10ee3e921",
              "end_line": 129,
              "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
              "path": "android_world/task_evals/single/camera.py",
              "snippet_sha256": "68f0795184e3c09ca4623819c214beec3f9086dd5668ca2432566fc18b219be9",
              "start_line": 114,
              "symbol": "CameraTakePhoto.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
            "ast_sha256": "506c3c2d4610f721ee001ea6cf5d841782e7aed0888f0d21c7680da10ee3e921",
            "end_line": 129,
            "owner_module": "android_world.task_evals.single.camera",
            "owner_qualname": "CameraTakePhoto.is_successful",
            "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "snippet_sha256": "68f0795184e3c09ca4623819c214beec3f9086dd5668ca2432566fc18b219be9",
            "start_line": 114
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
              "adb_utils.issue_generic_request",
              "contents.generic.output.decode",
              "contents.generic.output.decode.replace",
              "contents.generic.output.decode.replace.split",
              "len",
              "logging.info",
              "set",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "CameraTakePhoto",
            "owner_module": "android_world.task_evals.single.camera",
            "source_ref": {
              "ast_sha256": "506c3c2d4610f721ee001ea6cf5d841782e7aed0888f0d21c7680da10ee3e921",
              "end_line": 129,
              "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
              "path": "android_world/task_evals/single/camera.py",
              "snippet_sha256": "68f0795184e3c09ca4623819c214beec3f9086dd5668ca2432566fc18b219be9",
              "start_line": 114,
              "symbol": "CameraTakePhoto.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
            "ast_sha256": "506c3c2d4610f721ee001ea6cf5d841782e7aed0888f0d21c7680da10ee3e921",
            "end_line": 129,
            "owner_module": "android_world.task_evals.single.camera",
            "owner_qualname": "CameraTakePhoto.is_successful",
            "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "snippet_sha256": "68f0795184e3c09ca4623819c214beec3f9086dd5668ca2432566fc18b219be9",
            "start_line": 114
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
      "task_class": "CameraTakePhoto"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.issue_generic_request",
            "contents.generic.output.decode",
            "contents.generic.output.decode.replace",
            "contents.generic.output.decode.replace.split",
            "logging.info",
            "set",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "CameraTakePhoto",
          "owner_module": "android_world.task_evals.single.camera",
          "source_ref": {
            "ast_sha256": "27aa7a34023d811f033df5eafea6d9d4cd1fb9ffc27161de09322ca19a271e63",
            "end_line": 112,
            "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "path": "android_world/task_evals/single/camera.py",
            "snippet_sha256": "cdca0dfbff7da2a9530a17ff7d061054c8365158e410a9d66cf18ce5223d8aa0",
            "start_line": 103,
            "symbol": "CameraTakePhoto.initialize_task"
          }
        },
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self._clear_app_data",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "_Camera",
          "owner_module": "android_world.task_evals.single.camera",
          "source_ref": {
            "ast_sha256": "672850eac7f7817e7ffa804e16d98a9aea2b6c35e440c56f31c14dd1f28b772d",
            "end_line": 39,
            "file_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "path": "android_world/task_evals/single/camera.py",
            "snippet_sha256": "e6ad4ed002a978800f854416d6070b6b28f98f9ab69d85705cbe9a6939ae615d",
            "start_line": 37,
            "symbol": "_Camera.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
          "ast_sha256": "27aa7a34023d811f033df5eafea6d9d4cd1fb9ffc27161de09322ca19a271e63",
          "end_line": 112,
          "owner_module": "android_world.task_evals.single.camera",
          "owner_qualname": "CameraTakePhoto.initialize_task",
          "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
          "snippet_sha256": "cdca0dfbff7da2a9530a17ff7d061054c8365158e410a9d66cf18ce5223d8aa0",
          "start_line": 103
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
          "ast_sha256": "672850eac7f7817e7ffa804e16d98a9aea2b6c35e440c56f31c14dd1f28b772d",
          "end_line": 39,
          "owner_module": "android_world.task_evals.single.camera",
          "owner_qualname": "_Camera.initialize_task",
          "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
          "snippet_sha256": "e6ad4ed002a978800f854416d6070b6b28f98f9ab69d85705cbe9a6939ae615d",
          "start_line": 37
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
        "Take one photo."
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
      "metadata_placeholders": [],
      "metadata_template": "Take one photo.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "_Camera.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
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
        "owner_module": "android_world.task_evals.single.camera",
        "owner_qualname": "CameraTakePhoto.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
        "source_sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944"
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
        "seed"
      ],
      "observed_parameter_types": {
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
          "ast_sha256": "85a182f0486c714787eafd97298d3808ea371de6985f57bbfcbc7357f535bc87",
          "end_line": 133,
          "owner_module": "android_world.task_evals.single.camera",
          "owner_qualname": "CameraTakePhoto.schema",
          "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
          "snippet_sha256": "9f3badf02916029755cbb048e14e34c184b11e1c72bf22fdd77c200ec129b513",
          "start_line": 92
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
          "ast_sha256": "9ec15deb2f67923fc3121d3124c0b50e2d1bb3fe519a5e4b3e98801a2e307dca",
          "end_line": 133,
          "owner_module": "android_world.task_evals.single.camera",
          "owner_qualname": "CameraTakePhoto.generate_random_params",
          "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
          "snippet_sha256": "a4142f162529fa06cb50768333e1f72ed84dc0a5bae1b6701b1f77c82ee2c291",
          "start_line": 131
        }
      ],
      "value": {
        "properties": {},
        "required": [],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/CameraTakePhoto/canonical_task_semantics.json",
      "sha256": "91625bd45349d0d9322a50d1df5fb175b8cdb93459eaae92941ff39d0919d81c"
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
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Take one photo.",
              "dispatch_goal_sha256": "6b34894a8e799006bbc307463f8aa2483a09cdceb7ee1614da8128ed4837bbee",
              "parameter_keys": [
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
              "placeholders": [],
              "template": "Take one photo.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/camera.py",
            "ast_sha256": "85a182f0486c714787eafd97298d3808ea371de6985f57bbfcbc7357f535bc87",
            "end_line": 133,
            "owner_module": "android_world.task_evals.single.camera",
            "owner_qualname": "CameraTakePhoto.template",
            "sha256": "9cbeb7c43adc42f5b4edadc280359371bda8759c392e41f20564f9dc741a7944",
            "snippet_sha256": "9f3badf02916029755cbb048e14e34c184b11e1c72bf22fdd77c200ec129b513",
            "start_line": 92
          }
        ],
        "template": "Take one photo."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Take one photo.",
      "optimal_steps": "2",
      "tags": [
        ""
      ],
      "task_name": "CameraTakePhoto"
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
