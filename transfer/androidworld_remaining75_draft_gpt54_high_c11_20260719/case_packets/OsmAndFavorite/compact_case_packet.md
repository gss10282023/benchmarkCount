# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "OsmAndFavorite",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 5,
    "task_id": "OsmAndFavorite"
  },
  "integrity": {
    "semantic_record_sha256": "260d72d9619148ca25de0e72ad1f1aa6eab04a17c7bc470a4d2821011c5e3ceb",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "b8b85cdcc004a0e47929a19e0eb081fcb5a44b8b1382c5afe0a7d97fbbb09c4e",
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
            "qualname": "OsmAndFavorite",
            "source_ref": {
              "ast_sha256": "f5e463e5076850a75b1ea7aeb3c12e8c3e394e2bfa79474b97d5076a2d1fa6fe",
              "end_line": 248,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "064b8ed6c7e1e75c2060d2b403835479dc9ce393cd8f759cbb2e9a73d13813dc",
              "start_line": 206,
              "symbol": "OsmAndFavorite"
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
            "ast_sha256": "f5e463e5076850a75b1ea7aeb3c12e8c3e394e2bfa79474b97d5076a2d1fa6fe",
            "end_line": 248,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndFavorite",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "064b8ed6c7e1e75c2060d2b403835479dc9ce393cd8f759cbb2e9a73d13813dc",
            "start_line": 206
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "ElementTree.parse",
              "ElementTree.parse.getroot",
              "_favorites_contains",
              "file_utils.check_file_exists",
              "file_utils.tmp_file_from_device",
              "logging.warning",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "location"
            ],
            "owner_class": "OsmAndFavorite",
            "owner_module": "android_world.task_evals.single.osmand",
            "source_ref": {
              "ast_sha256": "df802dc80b7e978a69389d9d6a7e4dcd67634869dbe22e8a9628baffe3755ab0",
              "end_line": 239,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "8a72fba8995753c268921c4683d81e37fb650acc994c31efe303f9eb21c9f24b",
              "start_line": 228,
              "symbol": "OsmAndFavorite.is_successful"
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
            "ast_sha256": "df802dc80b7e978a69389d9d6a7e4dcd67634869dbe22e8a9628baffe3755ab0",
            "end_line": 239,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndFavorite.is_successful",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "8a72fba8995753c268921c4683d81e37fb650acc994c31efe303f9eb21c9f24b",
            "start_line": 228
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
              "ElementTree.parse",
              "ElementTree.parse.getroot",
              "_favorites_contains",
              "file_utils.check_file_exists",
              "file_utils.tmp_file_from_device",
              "logging.warning",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "location"
            ],
            "owner_class": "OsmAndFavorite",
            "owner_module": "android_world.task_evals.single.osmand",
            "source_ref": {
              "ast_sha256": "df802dc80b7e978a69389d9d6a7e4dcd67634869dbe22e8a9628baffe3755ab0",
              "end_line": 239,
              "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
              "path": "android_world/task_evals/single/osmand.py",
              "snippet_sha256": "8a72fba8995753c268921c4683d81e37fb650acc994c31efe303f9eb21c9f24b",
              "start_line": 228,
              "symbol": "OsmAndFavorite.is_successful"
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
            "ast_sha256": "df802dc80b7e978a69389d9d6a7e4dcd67634869dbe22e8a9628baffe3755ab0",
            "end_line": 239,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndFavorite.is_successful",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "8a72fba8995753c268921c4683d81e37fb650acc994c31efe303f9eb21c9f24b",
            "start_line": 228
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
      "task_class": "OsmAndFavorite"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "_clear_favorites",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "OsmAndFavorite",
          "owner_module": "android_world.task_evals.single.osmand",
          "source_ref": {
            "ast_sha256": "7899f589b5a6ddc6152964ef7122a3311a8e0ec0cc0b1d928d0da90156ed59f2",
            "end_line": 226,
            "file_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "path": "android_world/task_evals/single/osmand.py",
            "snippet_sha256": "59a1a1178bb2c6ddc8933327315fc064acb46b3b89efb391344be477d7f975f5",
            "start_line": 223,
            "symbol": "OsmAndFavorite.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
          "ast_sha256": "7899f589b5a6ddc6152964ef7122a3311a8e0ec0cc0b1d928d0da90156ed59f2",
          "end_line": 226,
          "owner_module": "android_world.task_evals.single.osmand",
          "owner_qualname": "OsmAndFavorite.initialize_task",
          "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
          "snippet_sha256": "59a1a1178bb2c6ddc8933327315fc064acb46b3b89efb391344be477d7f975f5",
          "start_line": 223
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
        "Add a favorite location marker for {location} in the OsmAnd maps app."
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
      "metadata_template": "Add a favorite location marker for {location} in the OsmAnd maps app.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndFavorite",
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
        "owner_qualname": "OsmAndFavorite.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndFavorite.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndFavorite.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndFavorite.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
        "source_sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.osmand",
        "owner_qualname": "OsmAndFavorite.is_successful",
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
        "owner_qualname": "OsmAndFavorite.is_successful",
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
          "ast_sha256": "f5e463e5076850a75b1ea7aeb3c12e8c3e394e2bfa79474b97d5076a2d1fa6fe",
          "end_line": 248,
          "owner_module": "android_world.task_evals.single.osmand",
          "owner_qualname": "OsmAndFavorite.schema",
          "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
          "snippet_sha256": "064b8ed6c7e1e75c2060d2b403835479dc9ce393cd8f759cbb2e9a73d13813dc",
          "start_line": 206
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/osmand.py",
          "ast_sha256": "d56410a92a2f91910439e38ca4138a2ca95457347e34cfe70ba538189de679d5",
          "end_line": 248,
          "owner_module": "android_world.task_evals.single.osmand",
          "owner_qualname": "OsmAndFavorite.generate_random_params",
          "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
          "snippet_sha256": "87e584ed0f8df32d5d461e10625c826049caeac2365db71a24b42cc0d28f0920",
          "start_line": 246
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/OsmAndFavorite/canonical_task_semantics.json",
      "sha256": "260d72d9619148ca25de0e72ad1f1aa6eab04a17c7bc470a4d2821011c5e3ceb"
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
              "dispatch_goal_model": "Add a favorite location marker for Rotenboden, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "cfd2c919fe0030edd6a3f3410b4da176fded3804bc8aed7ec0be5e8e1bb7ad59",
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
              "dispatch_goal_model": "Add a favorite location marker for Malbun, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "3ea0126e02bcca53c81e18c82d1fd29ec3e7b7d37103d3b78fe7ee58fdaab224",
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
              "dispatch_goal_model": "Add a favorite location marker for 47.0688832, 9.5061564 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "38b17ae031c04b77bc2597bdbeba70b3d2043f965e177fb1adf2a50603199512",
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
              "dispatch_goal_model": "Add a favorite location marker for Nendeln, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "bab767bf641bef74e171890ac7c9802f57780964ec9193924c4b0ebe1fc71328",
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
              "dispatch_goal_model": "Add a favorite location marker for 47.1973857, 9.5430636 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "03182554c052816282e75dcee0cc98eecdb7263f8c67ec1a9080e7ad87f83962",
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
              "dispatch_goal_model": "Add a favorite location marker for 47.2165476, 9.5699984 in the OsmAnd maps app.",
              "dispatch_goal_sha256": "3b8009145dc7efc05acfa27e4148baf045d3b4eed925e3aa9f5d7fed29a352c8",
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
              "dispatch_goal_model": "Add a favorite location marker for Planken, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "fab803868fee1df23e5d7f979b112b6c43e0d45543e017e66323d4673bcf33c3",
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
              "dispatch_goal_model": "Add a favorite location marker for Ruggell, Liechtenstein in the OsmAnd maps app.",
              "dispatch_goal_sha256": "3699abb04776d0defb0ed1025fe9aee70a7c31208da9df1071d897cb2b4070a3",
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
              "template": "Add a favorite location marker for {location} in the OsmAnd maps app.",
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
            "ast_sha256": "f5e463e5076850a75b1ea7aeb3c12e8c3e394e2bfa79474b97d5076a2d1fa6fe",
            "end_line": 248,
            "owner_module": "android_world.task_evals.single.osmand",
            "owner_qualname": "OsmAndFavorite.template",
            "sha256": "04d39ee7658e0c2f520f7d25475cd5e3d0a4e8fbcd45b52fb2764855bd4d0b19",
            "snippet_sha256": "064b8ed6c7e1e75c2060d2b403835479dc9ce393cd8f759cbb2e9a73d13813dc",
            "start_line": 206
          }
        ],
        "template": "Add a favorite location marker for {location} in the OsmAnd maps app."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Add a favorite location marker for {location} in the OsmAnd maps app.",
      "optimal_steps": "6",
      "tags": [
        "search",
        "complex_ui_understanding",
        "parameterized"
      ],
      "task_name": "OsmAndFavorite"
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
