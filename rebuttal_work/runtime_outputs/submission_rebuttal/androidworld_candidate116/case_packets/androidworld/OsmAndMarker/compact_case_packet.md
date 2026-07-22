# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "OsmAndMarker",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 63,
    "task_id": "OsmAndMarker"
  },
  "integrity": {
    "semantic_record_sha256": "c862ab9a1f62140008c3045157d7feeb16708e3e079e6943bb7a3dd268b0e649",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "3c98837727280459a5b721a8c826b40ed3c4fb22d7aa078956887d1e9dec6ee0",
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
      "canonical_module": "android_world.task_evals.single.osmand",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.osmand",
            "qualname": "OsmAndMarker",
            "source_ref": {
              "ast_sha256": "16bad81bfb477c37792257fd8fa286c6967a27d065c0c21f981efc96840c35db",
              "end_line": 307,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "92649f5746e8f8032cadb1b8c69142fbaedcf5631c5a5b0bf9fb2741426f32be",
              "start_line": 279,
              "symbol": "OsmAndMarker"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.osmand",
            "qualname": "_OsmTaskEval",
            "source_ref": {
              "ast_sha256": "b32d95ddcecf99bc0cff3a9c27629fb4e2906bc13d824ed5d655a337174104d8",
              "end_line": 203,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "fd321ff4f99a102442ab8440a4bd59fe4915b3ca1b0ef96b0f025e2741a3dbef",
              "start_line": 200,
              "symbol": "_OsmTaskEval"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.common_validators.sqlite_validators",
            "qualname": "SQLiteApp",
            "source_ref": {
              "ast_sha256": "44df368e12e9cf79cc0f4a5a3050a530e05ec7bd8341716c986019ffef8b5f7e",
              "end_line": 268,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "18cd7e4fc846f3bcad8cd564f530cc0c286ffd7ea74dfa8c338f571b9a90b7ac",
              "start_line": 200,
              "symbol": "SQLiteApp"
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
        "runtime_reported_module": "android_world.task_evals.single.osmand",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
            "ast_sha256": "16bad81bfb477c37792257fd8fa286c6967a27d065c0c21f981efc96840c35db",
            "end_line": 307,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndMarker",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "92649f5746e8f8032cadb1b8c69142fbaedcf5631c5a5b0bf9fb2741426f32be",
            "start_line": 279
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "_marker_matches_location",
              "self.list_rows",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "location"
            ],
            "owner_class": "OsmAndMarker",
            "owner_module": "android_world.task_evals.single.osmand",
            "source_ref": {
              "ast_sha256": "b22765179727648fe0fa7dd5ef4dd6e2b30951780756912a12fd150f70ba2d16",
              "end_line": 303,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "a48e579a43f29c4875b277e1ca81a498b0ff28c5eedb8e8ba90f26276a3a09e1",
              "start_line": 299,
              "symbol": "OsmAndMarker.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
            "ast_sha256": "b22765179727648fe0fa7dd5ef4dd6e2b30951780756912a12fd150f70ba2d16",
            "end_line": 303,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndMarker.is_successful",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "a48e579a43f29c4875b277e1ca81a498b0ff28c5eedb8e8ba90f26276a3a09e1",
            "start_line": 299
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
              "_marker_matches_location",
              "self.list_rows",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "location"
            ],
            "owner_class": "OsmAndMarker",
            "owner_module": "android_world.task_evals.single.osmand",
            "source_ref": {
              "ast_sha256": "b22765179727648fe0fa7dd5ef4dd6e2b30951780756912a12fd150f70ba2d16",
              "end_line": 303,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "a48e579a43f29c4875b277e1ca81a498b0ff28c5eedb8e8ba90f26276a3a09e1",
              "start_line": 299,
              "symbol": "OsmAndMarker.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
            "ast_sha256": "b22765179727648fe0fa7dd5ef4dd6e2b30951780756912a12fd150f70ba2d16",
            "end_line": 303,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndMarker.is_successful",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "a48e579a43f29c4875b277e1ca81a498b0ff28c5eedb8e8ba90f26276a3a09e1",
            "start_line": 299
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
      "task_class": "OsmAndMarker"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 1,
          "direct_calls": [
            "self._clear_db",
            "self.add_rows",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "SQLiteApp",
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "source_ref": {
            "ast_sha256": "8ec142f52bd60efe8bf0eb5325d739d2511462452523437f3f96f9604aa5f8d1",
            "end_line": 263,
            "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "path": "android_world/task_evals/common_validators/sqlite_validators.py",
            "snippet_sha256": "97320f8846ae2e43d66bdcaedf01c6c896901a39582cd8890390fcde9cbf4710",
            "start_line": 257,
            "symbol": "SQLiteApp.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
          "ast_sha256": "8ec142f52bd60efe8bf0eb5325d739d2511462452523437f3f96f9604aa5f8d1",
          "end_line": 263,
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "owner_qualname": "SQLiteApp.initialize_task",
          "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "snippet_sha256": "97320f8846ae2e43d66bdcaedf01c6c896901a39582cd8890390fcde9cbf4710",
          "start_line": 257
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
        "Add a location marker for {location} in the OsmAnd maps app."
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
        "location"
      ],
      "metadata_template": "Add a location marker for {location} in the OsmAnd maps app.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "SQLiteApp.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "source_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
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
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndMarker.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
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
        "location",
        "seed"
      ],
      "observed_parameter_types": {
        "location": [
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
          "ast_sha256": "16bad81bfb477c37792257fd8fa286c6967a27d065c0c21f981efc96840c35db",
          "end_line": 307,
          "owner_module": "android_world.task_evals.single.osmand",
          "owner_qualname": "OsmAndMarker.schema",
          "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
          "snippet_sha256": "92649f5746e8f8032cadb1b8c69142fbaedcf5631c5a5b0bf9fb2741426f32be",
          "start_line": 279
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
          "ast_sha256": "d56410a92a2f91910439e38ca4138a2ca95457347e34cfe70ba538189de679d5",
          "end_line": 307,
          "owner_module": "android_world.task_evals.single.osmand",
          "owner_qualname": "OsmAndMarker.generate_random_params",
          "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
          "snippet_sha256": "87e584ed0f8df32d5d461e10625c826049caeac2365db71a24b42cc0d28f0920",
          "start_line": 305
        }
      ],
      "value": {
        "properties": {
          "location": {
            "type": "string"
          }
        },
        "required": [
          "location"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/OsmAndMarker/canonical_task_semantics.json",
      "sha256": "c862ab9a1f62140008c3045157d7feeb16708e3e079e6943bb7a3dd268b0e649"
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
              "dispatch_goal_model": "Add a location marker for Rotenboden, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "878b3ec3a2a7acbfd35f1a8bdf97812c0241fa8977ac9db2845fea6001f4c544",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for Malbun, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "91bd6690222be67baa06dd8e655f5da721c3f33136fc141327982616432a2497",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for 47.0688832, 9.5061564 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "3441dd899dcaa981ab2d4113683444c81df122fd562fcc5c2f5a78f19303e82d",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for Nendeln, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "9b07aee9fec33efde171f3ff5227324c5528a459c16db2c62c0dba52d1bb9200",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for 47.1973857, 9.5430636 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "85e3be2c994d6a243c1411575f8f141acd0d2d1557d3c1b1fe99415c5f55a9c3",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for 47.2165476, 9.5699984 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "e7362b180ec85f0c18f0fb32a6c2961810d7176641ab33c111b3550ebd71780d",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for Planken, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "0e551d7c6700a9023f390d51eacfae1f8f4c73b6828831caa74c5791a6bb5fbd",
              "parameter_keys": [
                "location",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add a location marker for Ruggell, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "df6474dd860206534b7bf4ef26a6cf867540a6e03fde31e30877fd4c5c3eb82c",
              "parameter_keys": [
                "location",
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
                "location"
              ],
              "template": "Add a location marker for {location} in the OsmAnd maps app.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
            "ast_sha256": "16bad81bfb477c37792257fd8fa286c6967a27d065c0c21f981efc96840c35db",
            "end_line": 307,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndMarker.template",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "92649f5746e8f8032cadb1b8c69142fbaedcf5631c5a5b0bf9fb2741426f32be",
            "start_line": 279
          }
        ],
        "template": "Add a location marker for {location} in the OsmAnd maps app."
      },
      "difficulty": "hard",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Add a location marker for {location} in the OsmAnd maps app.",
      "optimal_steps": "10",
      "tags": [
        "complex_ui_understanding",
        "search",
        "parameterized"
      ],
      "task_name": "OsmAndMarker"
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
