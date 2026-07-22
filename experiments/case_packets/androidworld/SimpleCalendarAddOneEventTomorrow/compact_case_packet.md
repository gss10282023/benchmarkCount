# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleCalendarAddOneEventTomorrow",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 9,
    "task_id": "SimpleCalendarAddOneEventTomorrow"
  },
  "integrity": {
    "semantic_record_sha256": "6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "ccb5b4118bf685869042fdbc3bbd881c1f3b4532a7985ecf573d300695a9b0cf",
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
      "canonical_module": "android_world.task_evals.single.calendar.calendar",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.calendar.calendar",
            "qualname": "SimpleCalendarAddOneEventTomorrow",
            "source_ref": {
              "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
              "end_line": 199,
              "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
              "path": "android_world/task_evals/single/calendar/calendar.py",
              "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
              "start_line": 182,
              "symbol": "SimpleCalendarAddOneEventTomorrow"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.calendar.calendar",
            "qualname": "SimpleCalendarAddOneEvent",
            "source_ref": {
              "ast_sha256": "a4a1d999e3126c9c8b7a9afabd9a4feaf2eda5d4a20aef994bce4db3e7e45e84",
              "end_line": 139,
              "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
              "path": "android_world/task_evals/single/calendar/calendar.py",
              "snippet_sha256": "8b23addea3162b0268dc4fad8e87e094c44fec5a168ad06ed3ea1116cb0b22a2",
              "start_line": 85,
              "symbol": "SimpleCalendarAddOneEvent"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.common_validators.sqlite_validators",
            "qualname": "AddMultipleRows",
            "source_ref": {
              "ast_sha256": "2e801c534950f863ba825b6366be40b9679d4a4d48069ab04807b94018035d11",
              "end_line": 323,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "7b415c9bb1ebc10ece14a0ed262889b4c4db0fbecd327dd2c5f8261d2523e13f",
              "start_line": 271,
              "symbol": "AddMultipleRows"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.calendar.calendar",
            "qualname": "_SimpleCalendar",
            "source_ref": {
              "ast_sha256": "b37475fef92212b5ad9abc69fb854b2f09e4ca45c6849c9e1da584950ce94ac5",
              "end_line": 82,
              "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
              "path": "android_world/task_evals/single/calendar/calendar.py",
              "snippet_sha256": "24705bc4830c48802dba65136f58cf31f4c8411d4b0e605e826c48941bab03ca",
              "start_line": 61,
              "symbol": "_SimpleCalendar"
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
        "runtime_reported_module": "android_world.task_evals.single.calendar.calendar",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
            "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
            "end_line": 199,
            "owner_module": "android_world.task_evals.single.calendar.calendar",
            "owner_qualname": "SimpleCalendarAddOneEventTomorrow",
            "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
            "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
            "start_line": 182
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 1,
            "direct_calls": [
              "self.list_rows",
              "self.validate_addition_integrity"
            ],
            "direct_parameter_reads": [],
            "owner_class": "AddMultipleRows",
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "source_ref": {
              "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
              "end_line": 310,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
              "start_line": 304,
              "symbol": "AddMultipleRows.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
            "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
            "end_line": 310,
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "owner_qualname": "AddMultipleRows.is_successful",
            "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
            "start_line": 304
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
              "self.list_rows",
              "self.validate_addition_integrity"
            ],
            "direct_parameter_reads": [],
            "owner_class": "AddMultipleRows",
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "source_ref": {
              "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
              "end_line": 310,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
              "start_line": 304,
              "symbol": "AddMultipleRows.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
            "ast_sha256": "f2751ca3568b387056d6f4fdec053268e79d42a6e48ba54bce1e094203f0e07a",
            "end_line": 310,
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "owner_qualname": "AddMultipleRows.is_successful",
            "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "snippet_sha256": "64097499692465a3a591ea95f000120ccced1957f73425ff2dc757e9ae1745c7",
            "start_line": 304
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
      "task_class": "SimpleCalendarAddOneEventTomorrow"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "self.list_rows",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "AddMultipleRows",
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "source_ref": {
            "ast_sha256": "eea233290c4a63c1a86fd0539bc8d92335bcdf7b2673badda11c990be2979db5",
            "end_line": 283,
            "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "path": "android_world/task_evals/common_validators/sqlite_validators.py",
            "snippet_sha256": "57b20e4b7ef5cbeb3d74750a51770e8f57e2b74d5d33310c8bcabccd5b2f6654",
            "start_line": 280,
            "symbol": "AddMultipleRows.initialize_task"
          }
        },
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
          "ast_sha256": "eea233290c4a63c1a86fd0539bc8d92335bcdf7b2673badda11c990be2979db5",
          "end_line": 283,
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "owner_qualname": "AddMultipleRows.initialize_task",
          "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "snippet_sha256": "57b20e4b7ef5cbeb3d74750a51770e8f57e2b74d5d33310c8bcabccd5b2f6654",
          "start_line": 280
        },
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
        "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
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
        "duration_mins",
        "event_description",
        "event_title",
        "hour"
      ],
      "metadata_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEventTomorrow",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "source_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEventTomorrow.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "source_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f"
      },
      {
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "_SimpleCalendar.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "source_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f"
      },
      {
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarAddOneEvent.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "source_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "source_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5"
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
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "source_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5"
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
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "AddMultipleRows.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "source_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5"
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
        "day",
        "duration_mins",
        "event_description",
        "event_title",
        "hour",
        "month",
        "noise_row_objects",
        "row_objects",
        "seed",
        "year"
      ],
      "observed_parameter_types": {
        "day": [
          "builtins.int"
        ],
        "duration_mins": [
          "builtins.int"
        ],
        "event_description": [
          "builtins.str"
        ],
        "event_title": [
          "builtins.str"
        ],
        "hour": [
          "builtins.int"
        ],
        "month": [
          "builtins.int"
        ],
        "noise_row_objects": [
          "builtins.list"
        ],
        "row_objects": [
          "builtins.list"
        ],
        "seed": [
          "builtins.int"
        ],
        "year": [
          "builtins.int"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "empty",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
          "ast_sha256": "b37475fef92212b5ad9abc69fb854b2f09e4ca45c6849c9e1da584950ce94ac5",
          "end_line": 82,
          "owner_module": "android_world.task_evals.single.calendar.calendar",
          "owner_qualname": "_SimpleCalendar.schema",
          "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "snippet_sha256": "24705bc4830c48802dba65136f58cf31f4c8411d4b0e605e826c48941bab03ca",
          "start_line": 61
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
          "ast_sha256": "f25c295d8b655d79d805256776455a9ea16eaa7e4a5da2d8467d039ca3afa60c",
          "end_line": 139,
          "owner_module": "android_world.task_evals.single.calendar.calendar",
          "owner_qualname": "SimpleCalendarAddOneEvent.generate_random_params",
          "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "snippet_sha256": "a0de00951ae81703ebff24524b5b3845158a727a96d429253fbd9effc4e5a6f7",
          "start_line": 122
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleCalendarAddOneEventTomorrow/canonical_task_semantics.json",
      "sha256": "6f3bf04dc0a5669ad3a4c464332f4402c3eee076dedfd08806c6f3f3b028de4c"
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
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 13h with the title 'Workshop on Campaign' and the description 'We will explore team roles. Let's be punctual.'. The event should last for 15 mins.",
              "dispatch_goal_sha256": "be747e1fea3a2633f561ff9d68a37abf9698a679d6244d0ea009faf4492034fb",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Project X' and the description 'We will understand software updates. Looking forward to productive discussions.'. The event should last for 15 mins.",
              "dispatch_goal_sha256": "4bcd3fa002d585b07fc321d2e720d975920d6d54bc11210030dca1fda84e5c46",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 2h with the title 'Workshop on Annual Report' and the description 'We will prepare for team roles.'. The event should last for 15 mins.",
              "dispatch_goal_sha256": "af623f7312b5202dbec6af9bface41e3ed3a82f703af4bf5763e364472d3b61e",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 18h with the title 'Workshop on Campaign' and the description 'We will strategize about marketing strategies.'. The event should last for 30 mins.",
              "dispatch_goal_sha256": "109ddf5fe2ec40faef794e4767560e4b04f629ffbf63d720fbe2e83326aa4d25",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 9h with the title 'Review session for Campaign' and the description 'We will understand annual budget.'. The event should last for 15 mins.",
              "dispatch_goal_sha256": "f9fbd6338ad3a1f91823d22be90179153e1dcf4369e2b1afe00a271b667d56b3",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 23h with the title 'Review session for Project X' and the description 'We will understand product launch.'. The event should last for 45 mins.",
              "dispatch_goal_sha256": "cc8ce2eaba8dfab6fb6ba2c24438f73c56a89432edc027ec2ee4c970f529060e",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 4h with the title 'Review session for Project X' and the description 'We will finalize business objectives.'. The event should last for 60 mins.",
              "dispatch_goal_sha256": "da7a98425cb4029bae7909c37d8e5e27e00ae7abe45bc179ab89ec6dc045de0e",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "In Simple Calendar Pro, create a calendar event for tomorrow at 17h with the title 'Appointment for Annual Report' and the description 'We will plan business objectives. Snacks will be provided.'. The event should last for 60 mins.",
              "dispatch_goal_sha256": "078c174834e235a084200a7f6aefe3754b208638abbf6573884c4143c72371a5",
              "parameter_keys": [
                "day",
                "duration_mins",
                "event_description",
                "event_title",
                "hour",
                "month",
                "noise_row_objects",
                "row_objects",
                "seed",
                "year"
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
                "duration_mins",
                "event_description",
                "event_title",
                "hour"
              ],
              "template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
            "ast_sha256": "bd140103ca3d1023f79dda89955a07e058c56425856513e6f9d8eeda7e9d2356",
            "end_line": 199,
            "owner_module": "android_world.task_evals.single.calendar.calendar",
            "owner_qualname": "SimpleCalendarAddOneEventTomorrow.template",
            "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
            "snippet_sha256": "1a63eb7a5713125134623149f3d89dc1c4086215f9152de05b16d4aaca13a041",
            "start_line": 182
          }
        ],
        "template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "In Simple Calendar Pro, create a calendar event for tomorrow at {hour}h with the title '{event_title}' and the description '{event_description}'. The event should last for {duration_mins} mins.",
      "optimal_steps": "13",
      "tags": [
        "data_entry",
        "parameterized"
      ],
      "task_name": "SimpleCalendarAddOneEventTomorrow"
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
