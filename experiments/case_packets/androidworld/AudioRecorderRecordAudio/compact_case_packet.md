# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "AudioRecorderRecordAudio",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 45,
    "task_id": "AudioRecorderRecordAudio"
  },
  "integrity": {
    "semantic_record_sha256": "772ca3a3aa31cc9d94a8fef23bf52771042384734455200cb824e249c48e84f0",
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
            "qualname": "AudioRecorderRecordAudio",
            "source_ref": {
              "ast_sha256": "de88fc443e8d39922eb3ed990703471dc59553b55723bfc0f22ab40ffe4bcecf",
              "end_line": 82,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "df075cf009cc803869e471a28e201d06b7260dcfe06962a07331c29b25d59d71",
              "start_line": 35,
              "symbol": "AudioRecorderRecordAudio"
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
            "ast_sha256": "de88fc443e8d39922eb3ed990703471dc59553b55723bfc0f22ab40ffe4bcecf",
            "end_line": 82,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudio",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "df075cf009cc803869e471a28e201d06b7260dcfe06962a07331c29b25d59d71",
            "start_line": 35
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "changed.append",
              "file_utils.get_file_list_with_metadata",
              "len",
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "AudioRecorderRecordAudio",
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "source_ref": {
              "ast_sha256": "e9754c9bf020cd7a66f65165621f1aaeee8da21d48571cb841121fceab5bf55c",
              "end_line": 78,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "681f645cc35f3a8c7c642b684e6e93260812f19023899e5daba78e7d1f490779",
              "start_line": 59,
              "symbol": "AudioRecorderRecordAudio.is_successful"
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
            "ast_sha256": "e9754c9bf020cd7a66f65165621f1aaeee8da21d48571cb841121fceab5bf55c",
            "end_line": 78,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudio.is_successful",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "681f645cc35f3a8c7c642b684e6e93260812f19023899e5daba78e7d1f490779",
            "start_line": 59
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
              "changed.append",
              "file_utils.get_file_list_with_metadata",
              "len",
              "logging.info",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "AudioRecorderRecordAudio",
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "source_ref": {
              "ast_sha256": "e9754c9bf020cd7a66f65165621f1aaeee8da21d48571cb841121fceab5bf55c",
              "end_line": 78,
              "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
              "path": "android_world/task_evals/single/audio_recorder.py",
              "snippet_sha256": "681f645cc35f3a8c7c642b684e6e93260812f19023899e5daba78e7d1f490779",
              "start_line": 59,
              "symbol": "AudioRecorderRecordAudio.is_successful"
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
            "ast_sha256": "e9754c9bf020cd7a66f65165621f1aaeee8da21d48571cb841121fceab5bf55c",
            "end_line": 78,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudio.is_successful",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "681f645cc35f3a8c7c642b684e6e93260812f19023899e5daba78e7d1f490779",
            "start_line": 59
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
      "task_class": "AudioRecorderRecordAudio"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "RuntimeError",
            "file_utils.get_file_list_with_metadata",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "AudioRecorderRecordAudio",
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "source_ref": {
            "ast_sha256": "837fb79c3d31d1a6199d31649dabd4333c5e1e08f294a88b7e170114e30a71fa",
            "end_line": 57,
            "file_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "path": "android_world/task_evals/single/audio_recorder.py",
            "snippet_sha256": "6de848ac6bc6533fa38393447e810ad685584a79cd57eeea0582836c5ab1b28f",
            "start_line": 46,
            "symbol": "AudioRecorderRecordAudio.initialize_task"
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
          "ast_sha256": "837fb79c3d31d1a6199d31649dabd4333c5e1e08f294a88b7e170114e30a71fa",
          "end_line": 57,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudio.initialize_task",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "6de848ac6bc6533fa38393447e810ad685584a79cd57eeea0582836c5ab1b28f",
          "start_line": 46
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
        "Record an audio clip using Audio Recorder app and save it."
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
      "metadata_template": "Record an audio clip using Audio Recorder app and save it.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudio",
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
        "owner_qualname": "AudioRecorderRecordAudio.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudio.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudio.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
        "source_sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb"
      },
      {
        "owner_module": "android_world.task_evals.single.audio_recorder",
        "owner_qualname": "AudioRecorderRecordAudio.initialize_task",
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
        "owner_qualname": "AudioRecorderRecordAudio.is_successful",
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
        "owner_qualname": "AudioRecorderRecordAudio.is_successful",
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
          "ast_sha256": "de88fc443e8d39922eb3ed990703471dc59553b55723bfc0f22ab40ffe4bcecf",
          "end_line": 82,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudio.schema",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "df075cf009cc803869e471a28e201d06b7260dcfe06962a07331c29b25d59d71",
          "start_line": 35
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/audio_recorder.py",
          "ast_sha256": "f965f7e9bb57b22df07348d0836e219cf98d6674fbbe0538e8fe4324db6fdd35",
          "end_line": 82,
          "owner_module": "android_world.task_evals.single.audio_recorder",
          "owner_qualname": "AudioRecorderRecordAudio.generate_random_params",
          "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
          "snippet_sha256": "73d29dfcd0b0af0736d1a42203a3a071951d446f55d6608d37245f286472b2b4",
          "start_line": 80
        }
      ],
      "value": {
        "properties": {},
        "required": [],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/AudioRecorderRecordAudio/canonical_task_semantics.json",
      "sha256": "772ca3a3aa31cc9d94a8fef23bf52771042384734455200cb824e249c48e84f0"
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "dispatch_goal_model": "Record an audio clip using Audio Recorder app and save it.",
              "dispatch_goal_sha256": "ec3c14ab9830b7b732c4d89b7fb5f0f417dd5ce04e88d79e0c932b43483ba51d",
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
              "template": "Record an audio clip using Audio Recorder app and save it.",
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
            "ast_sha256": "de88fc443e8d39922eb3ed990703471dc59553b55723bfc0f22ab40ffe4bcecf",
            "end_line": 82,
            "owner_module": "android_world.task_evals.single.audio_recorder",
            "owner_qualname": "AudioRecorderRecordAudio.template",
            "sha256": "8f0f48f51577a831ba5a7e52dc5e4b9ad1c90d41fbcb456c640e5a14add340cb",
            "snippet_sha256": "df075cf009cc803869e471a28e201d06b7260dcfe06962a07331c29b25d59d71",
            "start_line": 35
          }
        ],
        "template": "Record an audio clip using Audio Recorder app and save it."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Record an audio clip using Audio Recorder app and save it.",
      "optimal_steps": "6",
      "tags": [
        "requires_setup"
      ],
      "task_name": "AudioRecorderRecordAudio"
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
