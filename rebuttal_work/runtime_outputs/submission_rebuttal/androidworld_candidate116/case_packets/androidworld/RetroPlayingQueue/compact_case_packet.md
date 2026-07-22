# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "RetroPlayingQueue",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 37,
    "task_id": "RetroPlayingQueue"
  },
  "integrity": {
    "semantic_record_sha256": "3e3fde83bd1a61cd7f4f3ff218cc80fd28602eed360a03aa85fd4be5e3b84284",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "c8dfe1291b61759ccd10890b94c4ee65e5aac8e47fd012d614a1909b99e7aff3",
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
      "canonical_module": "android_world.task_evals.single.retro_music",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.retro_music",
            "qualname": "RetroPlayingQueue",
            "source_ref": {
              "ast_sha256": "49626803f39a367ee487ec39436ef1fb93c46ca8c6919e693ece2686b6e93ce8",
              "end_line": 206,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "9bb25ee5db8ccfef36b6d779fd7c8d55d64de8fe593d7193ce0dad876603cc2b",
              "start_line": 190,
              "symbol": "RetroPlayingQueue"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.retro_music",
            "qualname": "RetroCreatePlaylist",
            "source_ref": {
              "ast_sha256": "f243fcba78345451c46eee1f3023f000a48befdf31eafbed54a985ab7000cc4f",
              "end_line": 187,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "5a1ea92d72c28afa11ba56e5c907ffcd5614e3431f32bd41beef6d574bf44913",
              "start_line": 120,
              "symbol": "RetroCreatePlaylist"
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
        "runtime_reported_module": "android_world.task_evals.single.retro_music",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "49626803f39a367ee487ec39436ef1fb93c46ca8c6919e693ece2686b6e93ce8",
            "end_line": 206,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroPlayingQueue",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "9bb25ee5db8ccfef36b6d779fd7c8d55d64de8fe593d7193ce0dad876603cc2b",
            "start_line": 190
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "_get_playing_queue",
              "f.split",
              "int"
            ],
            "direct_parameter_reads": [
              "files"
            ],
            "owner_class": "RetroPlayingQueue",
            "owner_module": "android_world.task_evals.single.retro_music",
            "source_ref": {
              "ast_sha256": "5b212470b17974dcf11107c49ea9b12ec9db836eee7b5e2d4f9a9a7c28a11c4a",
              "end_line": 206,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "7518db5af315dab04c4a3fb62e690ec9fc8fdbf40b72e85c1b1b9423d4ae485e",
              "start_line": 203,
              "symbol": "RetroPlayingQueue.is_successful"
            }
          },
          {
            "branch_node_count": 0,
            "direct_calls": [
              "_get_playlist_data",
              "f.split",
              "int",
              "sqlite_validators.verify_playlist"
            ],
            "direct_parameter_reads": [
              "files",
              "playlist_name"
            ],
            "owner_class": "RetroCreatePlaylist",
            "owner_module": "android_world.task_evals.single.retro_music",
            "source_ref": {
              "ast_sha256": "6bceb8b6cca0dd9814652dc8c8dae5e4efb66bd1803f0ff85ec08048c5e37003",
              "end_line": 170,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "450f39abf161efbfc5b99e724d42d03d426efe250cd113e122ef94a2a035dac6",
              "start_line": 162,
              "symbol": "RetroCreatePlaylist.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "5b212470b17974dcf11107c49ea9b12ec9db836eee7b5e2d4f9a9a7c28a11c4a",
            "end_line": 206,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroPlayingQueue.is_successful",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "7518db5af315dab04c4a3fb62e690ec9fc8fdbf40b72e85c1b1b9423d4ae485e",
            "start_line": 203
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "6bceb8b6cca0dd9814652dc8c8dae5e4efb66bd1803f0ff85ec08048c5e37003",
            "end_line": 170,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroCreatePlaylist.is_successful",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "450f39abf161efbfc5b99e724d42d03d426efe250cd113e122ef94a2a035dac6",
            "start_line": 162
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
              "_get_playing_queue",
              "f.split",
              "int"
            ],
            "direct_parameter_reads": [
              "files"
            ],
            "owner_class": "RetroPlayingQueue",
            "owner_module": "android_world.task_evals.single.retro_music",
            "source_ref": {
              "ast_sha256": "5b212470b17974dcf11107c49ea9b12ec9db836eee7b5e2d4f9a9a7c28a11c4a",
              "end_line": 206,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "7518db5af315dab04c4a3fb62e690ec9fc8fdbf40b72e85c1b1b9423d4ae485e",
              "start_line": 203,
              "symbol": "RetroPlayingQueue.is_successful"
            }
          },
          {
            "branch_node_count": 0,
            "direct_calls": [
              "_get_playlist_data",
              "f.split",
              "int",
              "sqlite_validators.verify_playlist"
            ],
            "direct_parameter_reads": [
              "files",
              "playlist_name"
            ],
            "owner_class": "RetroCreatePlaylist",
            "owner_module": "android_world.task_evals.single.retro_music",
            "source_ref": {
              "ast_sha256": "6bceb8b6cca0dd9814652dc8c8dae5e4efb66bd1803f0ff85ec08048c5e37003",
              "end_line": 170,
              "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
              "path": "android_world/task_evals/single/retro_music.py",
              "snippet_sha256": "450f39abf161efbfc5b99e724d42d03d426efe250cd113e122ef94a2a035dac6",
              "start_line": 162,
              "symbol": "RetroCreatePlaylist.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "5b212470b17974dcf11107c49ea9b12ec9db836eee7b5e2d4f9a9a7c28a11c4a",
            "end_line": 206,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroPlayingQueue.is_successful",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "7518db5af315dab04c4a3fb62e690ec9fc8fdbf40b72e85c1b1b9423d4ae485e",
            "start_line": 203
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "6bceb8b6cca0dd9814652dc8c8dae5e4efb66bd1803f0ff85ec08048c5e37003",
            "end_line": 170,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroCreatePlaylist.is_successful",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "450f39abf161efbfc5b99e724d42d03d426efe250cd113e122ef94a2a035dac6",
            "start_line": 162
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
      "task_class": "RetroPlayingQueue"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "_clear_playlist_dbs",
            "_scan_music_directory",
            "file.split",
            "file_utils.convert_to_posix_path",
            "random.choice",
            "random.randint",
            "super",
            "super.initialize_task",
            "user_data_generation.clear_internal_storage",
            "user_data_generation.write_mp3_file_to_device"
          ],
          "direct_parameter_reads": [
            "files",
            "noise_files"
          ],
          "owner_class": "RetroCreatePlaylist",
          "owner_module": "android_world.task_evals.single.retro_music",
          "source_ref": {
            "ast_sha256": "8aeaa8a22d1989c47a782501f0a4c61607516bf325c194d132ece257fee2983d",
            "end_line": 160,
            "file_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "path": "android_world/task_evals/single/retro_music.py",
            "snippet_sha256": "d942d660f6f5af80ab95deb3393d352301476900c647ea09d75b9b7b97f4afe4",
            "start_line": 147,
            "symbol": "RetroCreatePlaylist.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
          "ast_sha256": "8aeaa8a22d1989c47a782501f0a4c61607516bf325c194d132ece257fee2983d",
          "end_line": 160,
          "owner_module": "android_world.task_evals.single.retro_music",
          "owner_qualname": "RetroCreatePlaylist.initialize_task",
          "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
          "snippet_sha256": "d942d660f6f5af80ab95deb3393d352301476900c647ea09d75b9b7b97f4afe4",
          "start_line": 147
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
        "names"
      ],
      "metadata_template": "Add the following songs, in order, {names} to my playing queue in Retro music.",
      "status": "fixed_seed_goal_shape_match"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroPlayingQueue",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroPlayingQueue.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroCreatePlaylist.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroCreatePlaylist.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroCreatePlaylist.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroPlayingQueue.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroCreatePlaylist.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
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
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroPlayingQueue.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
      },
      {
        "owner_module": "android_world.task_evals.single.retro_music",
        "owner_qualname": "RetroCreatePlaylist.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
        "source_sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
          "ast_sha256": "f243fcba78345451c46eee1f3023f000a48befdf31eafbed54a985ab7000cc4f",
          "end_line": 187,
          "owner_module": "android_world.task_evals.single.retro_music",
          "owner_qualname": "RetroCreatePlaylist.schema",
          "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
          "snippet_sha256": "5a1ea92d72c28afa11ba56e5c907ffcd5614e3431f32bd41beef6d574bf44913",
          "start_line": 120
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
          "ast_sha256": "b2bf2f838acacb6c9b60a6b2103ab3791aa83407453e0cd781deeeacd51d7103",
          "end_line": 187,
          "owner_module": "android_world.task_evals.single.retro_music",
          "owner_qualname": "RetroCreatePlaylist.generate_random_params",
          "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
          "snippet_sha256": "3ccd85d2d3e7f586956428457125f42c14c0f524ac5aa1c1b23386c83bda8a73",
          "start_line": 177
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/RetroPlayingQueue/canonical_task_semantics.json",
      "sha256": "3e3fde83bd1a61cd7f4f3ff218cc80fd28602eed360a03aa85fd4be5e3b84284"
    },
    "task_text": {
      "benchmark": "AndroidWorld",
      "canonical_goal": {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "branches": [],
        "computed_expression": {
          "branch_node_count": 0,
          "direct_calls": [
            "f.split",
            "join"
          ],
          "direct_parameter_reads": [
            "files"
          ]
        },
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": {
            "branch_node_count": 0,
            "direct_calls": [
              "f.split",
              "join"
            ],
            "direct_parameter_reads": [
              "files"
            ]
          },
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the following songs, in order, Heartbeat Away, Whispering Wind, Voices in the Hall, Eternal Flame to my playing queue in Retro music.",
              "dispatch_goal_sha256": "886b1a1a0a8313efb12fdc6af9c954519b491aa01376363ddd2b5f701fb8b61f",
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
              "dispatch_goal_model": "Add the following songs, in order, Chasing Shadows, Voices in the Hall, Bright Lights, Eternal Flame, Golden Days to my playing queue in Retro music.",
              "dispatch_goal_sha256": "495404e1fbec2eac5600a6927306f7cac7328a9353799dbeaa36e2746f8861da",
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
              "dispatch_goal_model": "Add the following songs, in order, Night Drive, Waves of Change, Beyond the Horizon to my playing queue in Retro music.",
              "dispatch_goal_sha256": "375af6d3044efbffe571d4b0134408eaaa7b9457a148d6e7d4f9b4d10157500e",
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
              "dispatch_goal_model": "Add the following songs, in order, Waves of Change, Moments, Beyond the Horizon, Path to Zenith, Falling Feathers to my playing queue in Retro music.",
              "dispatch_goal_sha256": "ca28fa7d19dcafb0fc3cab261ac745a8bfdc94f5b31033d1d663eec687bd2e3c",
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
              "dispatch_goal_model": "Add the following songs, in order, Echoes of Silence, Twilight Calling, Path to Zenith, Forever Young to my playing queue in Retro music.",
              "dispatch_goal_sha256": "12c4c88ba62d90ef134945ca6934349103065fddd707250ad0b9cdfd2993e7d5",
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
              "dispatch_goal_model": "Add the following songs, in order, Reflections, Whispers of the Past to my playing queue in Retro music.",
              "dispatch_goal_sha256": "2e8938596bb36286f6fa20b7d5d27a3cc62ebd47a2532d015466975fcdbd7f8a",
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
              "dispatch_goal_model": "Add the following songs, in order, Twilight Calling, Lost in the Echo to my playing queue in Retro music.",
              "dispatch_goal_sha256": "9a6a998d04804cde2b3710c7021c5a6373a0f76b95fcd2ae513c65da6edb9f1e",
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
              "dispatch_goal_model": "Add the following songs, in order, Distant Memories, Hidden Paths to my playing queue in Retro music.",
              "dispatch_goal_sha256": "c27811acb110e42360ddd026bec7f5f7ac26a4fad2fc2c5201297dbccfc744ed",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/retro_music.py",
            "ast_sha256": "c3451cda3c1ba2df843fcf64d2a247c8ab23378cfb06286224f2b6c19afd97f2",
            "end_line": 201,
            "owner_module": "android_world.task_evals.single.retro_music",
            "owner_qualname": "RetroPlayingQueue.goal",
            "sha256": "6e886d452febd533253e24f1faee5d642982df92b35c5873e9af5e4805e791a0",
            "snippet_sha256": "6888d8e9492f037d727a2ae00d54c0257de9cf911674ac13393bf55b202f4292",
            "start_line": 195
          }
        ]
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Add the following songs, in order, {names} to my playing queue in Retro music.",
      "optimal_steps": "16",
      "tags": [
        "parameterized"
      ],
      "task_name": "RetroPlayingQueue"
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
