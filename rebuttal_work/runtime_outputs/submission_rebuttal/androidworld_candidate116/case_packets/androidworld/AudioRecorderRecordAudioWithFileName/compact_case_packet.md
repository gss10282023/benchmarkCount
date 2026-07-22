# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "AudioRecorderRecordAudioWithFileName",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 64,
    "task_id": "AudioRecorderRecordAudioWithFileName"
  },
  "integrity": {
    "semantic_record_sha256": "fc09c61d9a7a323fb00886452d9267764dc5e608f5f602563a174e9403d8629c",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "fce5c347131d7123426562e317d53b60bd702561892733a43f4945bef7519687",
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
      "canonical_module": "android_world.task_evals.single.audio_recorder",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.audio_recorder",
            "qualname": "AudioRecorderRecordAudioWithFileName",
            "source_ref": {
              "ast_sha256": "e36138ff231863ec577f70208eb6989757150b39dbbdd8f849276570401bd4a2",
              "end_line": 164,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "6576c3c17387f5ac0bbd81cf5d5b07205ac31a80736d425b6bbcf476452564e2",
              "start_line": 85,
              "symbol": "AudioRecorderRecordAudioWithFileName"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.audio_recorder",
            "qualname": "_AudioRecorder",
            "source_ref": {
              "ast_sha256": "6a513dd43dbc7d2f1aba1edfb6619d05c6b6ca01cadec8414165302ae70c04f8",
              "end_line": 32,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "08e9209d0f01c6253ef5a58c096c656bbc60c9c797275273fb684fe33351aba9",
              "start_line": 29,
              "symbol": "_AudioRecorder"
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
        "runtime_reported_module": "android_world.task_evals.single.audio_recorder",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
            "ast_sha256": "e36138ff231863ec577f70208eb6989757150b39dbbdd8f849276570401bd4a2",
            "end_line": 164,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudioWithFileName",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "6576c3c17387f5ac0bbd81cf5d5b07205ac31a80736d425b6bbcf476452564e2",
            "start_line": 85
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
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "file_name"
            ],
            "owner_class": "AudioRecorderRecordAudioWithFileName",
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "source_ref": {
              "ast_sha256": "c98cb3b7d500d8832ec602c69813ad49a1aef0b56d9582a18352cadcfe38d723",
              "end_line": 123,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "8fdccaaf9b522cae473b6c03db0b68cbf36b944063e0d68aa0b21f185090cd2b",
              "start_line": 114,
              "symbol": "AudioRecorderRecordAudioWithFileName.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
            "ast_sha256": "c98cb3b7d500d8832ec602c69813ad49a1aef0b56d9582a18352cadcfe38d723",
            "end_line": 123,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudioWithFileName.is_successful",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "8fdccaaf9b522cae473b6c03db0b68cbf36b944063e0d68aa0b21f185090cd2b",
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
              "file_utils.check_file_or_folder_exists",
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [
              "file_name"
            ],
            "owner_class": "AudioRecorderRecordAudioWithFileName",
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "source_ref": {
              "ast_sha256": "c98cb3b7d500d8832ec602c69813ad49a1aef0b56d9582a18352cadcfe38d723",
              "end_line": 123,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "8fdccaaf9b522cae473b6c03db0b68cbf36b944063e0d68aa0b21f185090cd2b",
              "start_line": 114,
              "symbol": "AudioRecorderRecordAudioWithFileName.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
            "ast_sha256": "c98cb3b7d500d8832ec602c69813ad49a1aef0b56d9582a18352cadcfe38d723",
            "end_line": 123,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudioWithFileName.is_successful",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "8fdccaaf9b522cae473b6c03db0b68cbf36b944063e0d68aa0b21f185090cd2b",
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
      "task_class": "AudioRecorderRecordAudioWithFileName"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self._clear_audio_recorder_data",
            "self.create_file_task.initialize_task",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "AudioRecorderRecordAudioWithFileName",
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "source_ref": {
            "ast_sha256": "88915290cede314db49932d78cbe27ad9f1e21a6250f1d80c2273e5ebd1d8707",
            "end_line": 112,
            "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "path": "android_world/task_evals/single/audio_recorder.py",
            "snippet_sha256": "9b18b2cd4c2569f7998eb8b60c2a7064c87619d0708c78e661f738077cb3ddda",
            "start_line": 109,
            "symbol": "AudioRecorderRecordAudioWithFileName.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
          "ast_sha256": "88915290cede314db49932d78cbe27ad9f1e21a6250f1d80c2273e5ebd1d8707",
          "end_line": 112,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudioWithFileName.initialize_task",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "9b18b2cd4c2569f7998eb8b60c2a7064c87619d0708c78e661f738077cb3ddda",
          "start_line": 109
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
        "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app."
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
      "metadata_template": "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
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
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudioWithFileName.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
          "ast_sha256": "e36138ff231863ec577f70208eb6989757150b39dbbdd8f849276570401bd4a2",
          "end_line": 164,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudioWithFileName.schema",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "6576c3c17387f5ac0bbd81cf5d5b07205ac31a80736d425b6bbcf476452564e2",
          "start_line": 85
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
          "ast_sha256": "4aa84618d5116d6236071c94f9bac75a4c59a7aada2445d0c320e722e9881194",
          "end_line": 159,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudioWithFileName.generate_random_params",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "4682fea46781c5cb6cb2c09e751758f3dca47ef584be4e00169e039cb84555f4",
          "start_line": 125
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/AudioRecorderRecordAudioWithFileName/canonical_task_semantics.json",
      "sha256": "fc09c61d9a7a323fb00886452d9267764dc5e608f5f602563a174e9403d8629c"
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"qFzW_presentation.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "edbcb655348009b7a265ebba9f44fa31aaed6bcd2ceade40db62cabbd820fd4d",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"final_note.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "bc718744daf940d25ea6c4ead6af824da3b675c4dbcf21d23526a164d3dbe1ca",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"2023_07_04_meeting.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "1b79d0c545ab246f96da06097f7308d9a61db381b296dd95559c48c5afe56dc4",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"final_workshop.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "268b1c77dfe1b5871ffe7130fe96dd361e75942ec69db86758dca8027af07f5b",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"SDfb_workshop.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "3547b6ed57310b3c0011379040d3e04c1b2f9da8101206cfcc54b6daa1c6ce04",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"diary_X6T5.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "c7aaf531a0837b6783d53671a9a9662dd5a164e0fd0df04077e664304f172b4d",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"discussion_2023_01_25.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "4357dd59c0f987a49eb7cc550fdbd6c574f2c5ce5dc86c411f5c69b0144cbce9",
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
              "dispatch_goal_model": "Record an audio clip and save it with name \"guidance_edited.m4a\" using Audio Recorder app.",
              "dispatch_goal_sha256": "2668024baf91b98d181349db5acbdc94e9320ebd254ba4a078affe3664e123eb",
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
              "template": "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
            "ast_sha256": "e36138ff231863ec577f70208eb6989757150b39dbbdd8f849276570401bd4a2",
            "end_line": 164,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudioWithFileName.template",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "6576c3c17387f5ac0bbd81cf5d5b07205ac31a80736d425b6bbcf476452564e2",
            "start_line": 85
          }
        ],
        "template": "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Record an audio clip and save it with name \"{file_name}\" using Audio Recorder app.",
      "optimal_steps": "10",
      "tags": [
        "data_entry",
        "complex_ui_understanding",
        "parameterized"
      ],
      "task_name": "AudioRecorderRecordAudioWithFileName"
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
