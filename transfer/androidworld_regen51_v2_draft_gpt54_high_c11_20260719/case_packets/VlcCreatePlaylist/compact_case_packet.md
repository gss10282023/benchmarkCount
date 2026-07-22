# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "VlcCreatePlaylist",
    "domain": "androidworld",
    "group": "extra16",
    "selection_rank": 107,
    "task_id": "VlcCreatePlaylist"
  },
  "integrity": {
    "semantic_record_sha256": "89f597713664c76bd015ffe21f5717cd790482b6088100925eedb90237b7a86f",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "b304018d0f3c9dab1ae760279cacb1a4b130ddd40b662b6bdc44c5e7b1071049",
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
      "canonical_module": "android_world.task_evals.single.vlc",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.vlc",
            "qualname": "VlcCreatePlaylist",
            "source_ref": {
              "ast_sha256": "49b81075203e490626361a26b8e1e45a98aa39271e7f7c0ce869ddf917c1f66c",
              "end_line": 161,
              "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
              "path": "android_world/task_evals/single/vlc.py",
              "snippet_sha256": "372e4a77021e590f09afe995be26a2f253dcecc825cecb44dde55b66e6db7502",
              "start_line": 87,
              "symbol": "VlcCreatePlaylist"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.vlc",
            "qualname": "_VLC",
            "source_ref": {
              "ast_sha256": "5e275095d7301f47f50aadfee530cf267ed0b7fc8f60ac6bb88606adac66e0b3",
              "end_line": 84,
              "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
              "path": "android_world/task_evals/single/vlc.py",
              "snippet_sha256": "e66f89be5759fc75a262614e0d539135c84faaf23e84d70e983a839b9e838da8",
              "start_line": 74,
              "symbol": "_VLC"
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
        "runtime_reported_module": "android_world.task_evals.single.vlc",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
            "ast_sha256": "49b81075203e490626361a26b8e1e45a98aa39271e7f7c0ce869ddf917c1f66c",
            "end_line": 161,
            "owner_module": "android_world.task_evals.single.vlc",
            "owner_qualname": "VlcCreatePlaylist",
            "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "snippet_sha256": "372e4a77021e590f09afe995be26a2f253dcecc825cecb44dde55b66e6db7502",
            "start_line": 87
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "_get_playlist_file_info",
              "float",
              "sqlite_validators.verify_playlist"
            ],
            "direct_parameter_reads": [
              "files",
              "playlist_name"
            ],
            "owner_class": "VlcCreatePlaylist",
            "owner_module": "android_world.task_evals.single.vlc",
            "source_ref": {
              "ast_sha256": "c56cf9bd67f173bf5a2df88f282fd406580e53e9990b906126899a910b151e51",
              "end_line": 150,
              "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
              "path": "android_world/task_evals/single/vlc.py",
              "snippet_sha256": "c47434ba2c1d6aa0a4367a7f56b722eae051ab1fc68bb859cd107e64f52d2c79",
              "start_line": 144,
              "symbol": "VlcCreatePlaylist.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
            "ast_sha256": "c56cf9bd67f173bf5a2df88f282fd406580e53e9990b906126899a910b151e51",
            "end_line": 150,
            "owner_module": "android_world.task_evals.single.vlc",
            "owner_qualname": "VlcCreatePlaylist.is_successful",
            "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "snippet_sha256": "c47434ba2c1d6aa0a4367a7f56b722eae051ab1fc68bb859cd107e64f52d2c79",
            "start_line": 144
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
              "_get_playlist_file_info",
              "float",
              "sqlite_validators.verify_playlist"
            ],
            "direct_parameter_reads": [
              "files",
              "playlist_name"
            ],
            "owner_class": "VlcCreatePlaylist",
            "owner_module": "android_world.task_evals.single.vlc",
            "source_ref": {
              "ast_sha256": "c56cf9bd67f173bf5a2df88f282fd406580e53e9990b906126899a910b151e51",
              "end_line": 150,
              "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
              "path": "android_world/task_evals/single/vlc.py",
              "snippet_sha256": "c47434ba2c1d6aa0a4367a7f56b722eae051ab1fc68bb859cd107e64f52d2c79",
              "start_line": 144,
              "symbol": "VlcCreatePlaylist.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
            "ast_sha256": "c56cf9bd67f173bf5a2df88f282fd406580e53e9990b906126899a910b151e51",
            "end_line": 150,
            "owner_module": "android_world.task_evals.single.vlc",
            "owner_qualname": "VlcCreatePlaylist.is_successful",
            "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "snippet_sha256": "c47434ba2c1d6aa0a4367a7f56b722eae051ab1fc68bb859cd107e64f52d2c79",
            "start_line": 144
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
      "task_class": "VlcCreatePlaylist"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "_clear_playlist_dbs",
            "self.setup_files",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "VlcCreatePlaylist",
          "owner_module": "android_world.task_evals.single.vlc",
          "source_ref": {
            "ast_sha256": "cfc134e2dd62eee83e9bcf316cee01e37fd4fae40b034742317f3b02bd434fda",
            "end_line": 138,
            "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "path": "android_world/task_evals/single/vlc.py",
            "snippet_sha256": "61f21c8c21178b50468e6381190c028c0289d56a32f5f8b6ac373c1b2ca411c0",
            "start_line": 135,
            "symbol": "VlcCreatePlaylist.initialize_task"
          }
        },
        {
          "branch_node_count": 0,
          "direct_calls": [
            "file_utils.clear_directory",
            "super",
            "super.initialize_task",
            "user_data_generation.clear_internal_storage"
          ],
          "direct_parameter_reads": [],
          "owner_class": "_VLC",
          "owner_module": "android_world.task_evals.single.vlc",
          "source_ref": {
            "ast_sha256": "a124c9c312c76d92d93980a9ae8ce4aad172c34fe6915e99318196db88bd7e29",
            "end_line": 79,
            "file_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "path": "android_world/task_evals/single/vlc.py",
            "snippet_sha256": "3c707dff78f6d7e240b63743d6157f30cdaae2cb6872f205b3f2aa4cc2dfce08",
            "start_line": 76,
            "symbol": "_VLC.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
          "ast_sha256": "cfc134e2dd62eee83e9bcf316cee01e37fd4fae40b034742317f3b02bd434fda",
          "end_line": 138,
          "owner_module": "android_world.task_evals.single.vlc",
          "owner_qualname": "VlcCreatePlaylist.initialize_task",
          "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
          "snippet_sha256": "61f21c8c21178b50468e6381190c028c0289d56a32f5f8b6ac373c1b2ca411c0",
          "start_line": 135
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
          "ast_sha256": "a124c9c312c76d92d93980a9ae8ce4aad172c34fe6915e99318196db88bd7e29",
          "end_line": 79,
          "owner_module": "android_world.task_evals.single.vlc",
          "owner_qualname": "_VLC.initialize_task",
          "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
          "snippet_sha256": "3c707dff78f6d7e240b63743d6157f30cdaae2cb6872f205b3f2aa4cc2dfce08",
          "start_line": 76
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
      "canonical_templates": [],
      "comparison_is_semantic_proof": false,
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
        "files",
        "playlist_name"
      ],
      "metadata_template": "Create a playlist titled \"{playlist_name}\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: {files}",
      "status": "fixed_seed_goal_shape_match"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "_VLC.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
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
        "owner_module": "android_world.task_evals.single.vlc",
        "owner_qualname": "VlcCreatePlaylist.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
        "source_sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb"
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
        "files",
        "noise_files",
        "playlist_name",
        "seed"
      ],
      "observed_parameter_types": {
        "files": [
          "builtins.list"
        ],
        "noise_files": [
          "builtins.list"
        ],
        "playlist_name": [
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
          "ast_sha256": "49b81075203e490626361a26b8e1e45a98aa39271e7f7c0ce869ddf917c1f66c",
          "end_line": 161,
          "owner_module": "android_world.task_evals.single.vlc",
          "owner_qualname": "VlcCreatePlaylist.schema",
          "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
          "snippet_sha256": "372e4a77021e590f09afe995be26a2f253dcecc825cecb44dde55b66e6db7502",
          "start_line": 87
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
          "ast_sha256": "e3d9e447eb0ba4ec508e3c7d2e4894656a317e03013b441f1b2f9bb753730c91",
          "end_line": 161,
          "owner_module": "android_world.task_evals.single.vlc",
          "owner_qualname": "VlcCreatePlaylist.generate_random_params",
          "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
          "snippet_sha256": "5d2135bfbc86943ac4b4c7afc9485aa25de8f9bfa26d5c43e68e4b41ef8f9ab5",
          "start_line": 152
        }
      ],
      "value": {
        "properties": {
          "files": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "playlist_name": {
            "type": "string"
          }
        },
        "required": [
          "playlist_name",
          "files"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/VlcCreatePlaylist/canonical_task_semantics.json",
      "sha256": "89f597713664c76bd015ffe21f5717cd790482b6088100925eedb90237b7a86f"
    },
    "task_text": {
      "benchmark": "AndroidWorld",
      "canonical_goal": {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "branches": [],
        "computed_expression": {
          "branch_node_count": 0,
          "direct_calls": [
            "join"
          ],
          "direct_parameter_reads": [
            "files",
            "playlist_name"
          ]
        },
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": {
            "branch_node_count": 0,
            "direct_calls": [
              "join"
            ],
            "direct_parameter_reads": [
              "files",
              "playlist_name"
            ]
          },
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Summer Highlights Ultimate Collection\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: clip_66_4K_4Z8w.mp4, UMp4_footage_18_export.mp4, T3QD_moment_19_export.mp4, 7D1q_clip_56_4K.mp4, episode_2_export_2023_01_01.mp4",
              "dispatch_goal_sha256": "b7100539582f3db23d83559cd1f3848f40e2b36a91e60f4396e7b7d6d74ca64e",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Epic Moments Series\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: scene_64__OWfb.mp4, edited_episode_56_raw.mp4",
              "dispatch_goal_sha256": "2cd10f30b471e830cbc84ff217d9c3cb39c2736369418952c69f7ab6e299ec42",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Comedy Essentials\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: scene_95_HD_final.mp4, 2023_08_09_highlight_78_HD.mp4",
              "dispatch_goal_sha256": "e9375d14e77f74c744b9532a28a8c3ce33d8c6215705e03c53bfa08ce77dc7b1",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Gaming Sessions Series\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: backup_scene_61_export.mp4, copy_episode_34_raw.mp4, moment_70_raw_edited.mp4",
              "dispatch_goal_sha256": "470748966df2fe1135f1318726ed2d2a603a6271db0ef2cfcb183fd6b4a3058e",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Gaming Sessions Marathon\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: 2023_02_04_moment_62_raw.mp4, nHrk_clip_71_raw.mp4",
              "dispatch_goal_sha256": "f645886074b8b1ad95fc43741df7c8f2d17826b6ec4e5e509ee499c4bf621a5f",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"How To Specials\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: O3hD_episode_4_export.mp4, 2023_01_07_footage_70_raw.mp4, 4VjX_moment_53_HD.mp4, i8aV_footage_80_export.mp4",
              "dispatch_goal_sha256": "2d9de0255f9a27453612428dc5f8f33b0a652e55b6073c150729c4691e20a6c7",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Recipe Collection Favorites\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: final_moment_10_.mp4, 2023_02_14_highlight_65_.mp4, 2023_10_10_recording_9_raw.mp4, 2023_02_01_recording_73_.mp4, 2023_01_24_highlight_51_export.mp4",
              "dispatch_goal_sha256": "89dcb3756208ffcbee87d6236f3b34f13e19c00d00c1c98a54b5b40852e7988c",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a playlist titled \"Travel Guide Ultimate Collection\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: 2023_09_20_recording_76_export.mp4, recording_24_export_2023_06_05.mp4, edited_footage_69_.mp4, 2023_09_28_recording_84_export.mp4, 2023_01_16_clip_5_.mp4",
              "dispatch_goal_sha256": "761b673065df73d0f61914b8bc90d35fd868619e806c993e7f67ae43c1360810",
              "parameter_keys": [
                "files",
                "noise_files",
                "playlist_name",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 11
            }
          ],
          "samples_are_examples_not_generic_templates": true,
          "templates": []
        },
        "representation_kind": "computed_goal",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/vlc.py",
            "ast_sha256": "8d0c4260a62f2fccecc495233759b8340d28eff45016829648da1b8a484d2563",
            "end_line": 113,
            "owner_module": "android_world.task_evals.single.vlc",
            "owner_qualname": "VlcCreatePlaylist.goal",
            "sha256": "9d5fe919e084c4e49406cca12ff52a045dab430f8fa1ca5ac939d5d350ff98fb",
            "snippet_sha256": "490d8859c01019ea6924877449c25e155f6ab5090fca7c50f95e8957b5df087a",
            "start_line": 106
          }
        ]
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a playlist titled \"{playlist_name}\" with the following files in VLC (located in Internal Memory/VLCVideos), in order: {files}",
      "optimal_steps": "14",
      "tags": [
        "data_edit",
        "repetition",
        "parameterized"
      ],
      "task_name": "VlcCreatePlaylist"
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
