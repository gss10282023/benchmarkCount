# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "ClockStopWatchPausedVerify",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 77,
    "task_id": "ClockStopWatchPausedVerify"
  },
  "integrity": {
    "semantic_record_sha256": "8452c098b9dc8b0efbd5175c5de103d0f4de180c79186da922520f3177059662",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "720de09bbd77c4862980e03be7f1c2df3e68adf4a0e7cd613055d5ee6962b4a6",
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
      "canonical_module": "android_world.task_evals.single.clock",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.clock",
            "qualname": "ClockStopWatchPausedVerify",
            "source_ref": {
              "ast_sha256": "30c6412d6ac78c2fc2c1f65ac1bc43826afbd83886ed353abdfe7000c31621b6",
              "end_line": 212,
              "file_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
              "path": "android_world/task_evals/single/clock.py",
              "snippet_sha256": "45b43471008105efc1cf51581fef6797a5c71fdc3a02d487380824d757a7f0d5",
              "start_line": 177,
              "symbol": "ClockStopWatchPausedVerify"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.clock",
            "qualname": "_ClockEval",
            "source_ref": {
              "ast_sha256": "56f61d8a5ed3377300b52e673057b31fdd3ce718e41be4dcb0db877139cb4b2d",
              "end_line": 122,
              "file_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
              "path": "android_world/task_evals/single/clock.py",
              "snippet_sha256": "d2299e626ec247c315d6d71b32cb04fdb8bf985eda8825936383427f9876b0d9",
              "start_line": 111,
              "symbol": "_ClockEval"
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
        "runtime_reported_module": "android_world.task_evals.single.clock",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
            "ast_sha256": "30c6412d6ac78c2fc2c1f65ac1bc43826afbd83886ed353abdfe7000c31621b6",
            "end_line": 212,
            "owner_module": "android_world.task_evals.single.clock",
            "owner_qualname": "ClockStopWatchPausedVerify",
            "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
            "snippet_sha256": "45b43471008105efc1cf51581fef6797a5c71fdc3a02d487380824d757a7f0d5",
            "start_line": 177
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "_is_stopwatch_paused",
              "adb_utils.get_current_activity",
              "env.get_state",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "ClockStopWatchPausedVerify",
            "owner_module": "android_world.task_evals.single.clock",
            "source_ref": {
              "ast_sha256": "b3b52b4625d0ba7d84d3e76d0986d17898d1bfdf6bcccd1f03fbceaf9933703a",
              "end_line": 208,
              "file_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
              "path": "android_world/task_evals/single/clock.py",
              "snippet_sha256": "74fcf3484ac47a8c96c41346fdfe7075e4b86f8fdc0420684864c09779fc108b",
              "start_line": 194,
              "symbol": "ClockStopWatchPausedVerify.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
            "ast_sha256": "b3b52b4625d0ba7d84d3e76d0986d17898d1bfdf6bcccd1f03fbceaf9933703a",
            "end_line": 208,
            "owner_module": "android_world.task_evals.single.clock",
            "owner_qualname": "ClockStopWatchPausedVerify.is_successful",
            "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
            "snippet_sha256": "74fcf3484ac47a8c96c41346fdfe7075e4b86f8fdc0420684864c09779fc108b",
            "start_line": 194
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
              "_is_stopwatch_paused",
              "adb_utils.get_current_activity",
              "env.get_state",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "ClockStopWatchPausedVerify",
            "owner_module": "android_world.task_evals.single.clock",
            "source_ref": {
              "ast_sha256": "b3b52b4625d0ba7d84d3e76d0986d17898d1bfdf6bcccd1f03fbceaf9933703a",
              "end_line": 208,
              "file_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
              "path": "android_world/task_evals/single/clock.py",
              "snippet_sha256": "74fcf3484ac47a8c96c41346fdfe7075e4b86f8fdc0420684864c09779fc108b",
              "start_line": 194,
              "symbol": "ClockStopWatchPausedVerify.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
            "ast_sha256": "b3b52b4625d0ba7d84d3e76d0986d17898d1bfdf6bcccd1f03fbceaf9933703a",
            "end_line": 208,
            "owner_module": "android_world.task_evals.single.clock",
            "owner_qualname": "ClockStopWatchPausedVerify.is_successful",
            "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
            "snippet_sha256": "74fcf3484ac47a8c96c41346fdfe7075e4b86f8fdc0420684864c09779fc108b",
            "start_line": 194
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
      "task_class": "ClockStopWatchPausedVerify"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "_close_clock_app",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "_ClockEval",
          "owner_module": "android_world.task_evals.single.clock",
          "source_ref": {
            "ast_sha256": "b329069cf8c38553303864521613b4ecdb619f2c786855c1ad4ada36f017e0ce",
            "end_line": 118,
            "file_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
            "path": "android_world/task_evals/single/clock.py",
            "snippet_sha256": "1afaf9c8b99b4f8749c5bebc7e3667e3a7bcb92443f5603debe7ec910d1b8353",
            "start_line": 116,
            "symbol": "_ClockEval.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
          "ast_sha256": "b329069cf8c38553303864521613b4ecdb619f2c786855c1ad4ada36f017e0ce",
          "end_line": 118,
          "owner_module": "android_world.task_evals.single.clock",
          "owner_qualname": "_ClockEval.initialize_task",
          "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
          "snippet_sha256": "1afaf9c8b99b4f8749c5bebc7e3667e3a7bcb92443f5603debe7ec910d1b8353",
          "start_line": 116
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
        "Pause the stopwatch."
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
      "metadata_template": "Pause the stopwatch.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
      },
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
      },
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
      },
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "_ClockEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
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
        "owner_module": "android_world.task_evals.single.clock",
        "owner_qualname": "ClockStopWatchPausedVerify.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
        "source_sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
          "ast_sha256": "30c6412d6ac78c2fc2c1f65ac1bc43826afbd83886ed353abdfe7000c31621b6",
          "end_line": 212,
          "owner_module": "android_world.task_evals.single.clock",
          "owner_qualname": "ClockStopWatchPausedVerify.schema",
          "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
          "snippet_sha256": "45b43471008105efc1cf51581fef6797a5c71fdc3a02d487380824d757a7f0d5",
          "start_line": 177
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
          "ast_sha256": "780b377b6d0d19ac806e714dae4b7afe029a7dfe0b52024634a7747181518285",
          "end_line": 212,
          "owner_module": "android_world.task_evals.single.clock",
          "owner_qualname": "ClockStopWatchPausedVerify.generate_random_params",
          "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
          "snippet_sha256": "7d62093d70a8c6791b5138cfdcc89397caf212cd660d1c74419ad94dc4996852",
          "start_line": 210
        }
      ],
      "value": {
        "properties": {},
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/ClockStopWatchPausedVerify/canonical_task_semantics.json",
      "sha256": "8452c098b9dc8b0efbd5175c5de103d0f4de180c79186da922520f3177059662"
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "dispatch_goal_model": "Pause the stopwatch.",
              "dispatch_goal_sha256": "cd11d59662de10c222bb65642adea5bec5e7d3db8f24a282282b32eeebf8c1cd",
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
              "template": "Pause the stopwatch.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/clock.py",
            "ast_sha256": "30c6412d6ac78c2fc2c1f65ac1bc43826afbd83886ed353abdfe7000c31621b6",
            "end_line": 212,
            "owner_module": "android_world.task_evals.single.clock",
            "owner_qualname": "ClockStopWatchPausedVerify.template",
            "sha256": "8761bec39aeeea2bbc2e2924e965a50ce57d6d724c0b0e15806ca3e2d4b9be0d",
            "snippet_sha256": "45b43471008105efc1cf51581fef6797a5c71fdc3a02d487380824d757a7f0d5",
            "start_line": 177
          }
        ],
        "template": "Pause the stopwatch."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Pause the stopwatch.",
      "optimal_steps": "1",
      "tags": [
        "verification"
      ],
      "task_name": "ClockStopWatchPausedVerify"
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
