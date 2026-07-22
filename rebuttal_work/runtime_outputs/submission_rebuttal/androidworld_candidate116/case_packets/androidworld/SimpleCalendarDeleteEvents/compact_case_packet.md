# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleCalendarDeleteEvents",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 74,
    "task_id": "SimpleCalendarDeleteEvents"
  },
  "integrity": {
    "semantic_record_sha256": "3e4808b940c5db1122826c3d9e9b3dcc4f0275703fe76cc85ca9e8226623ab1d",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "6cac5fe3c297a484e247e588172c440d7cd7f4780a2a306783febc2efc689fae",
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
            "qualname": "SimpleCalendarDeleteEvents",
            "source_ref": {
              "ast_sha256": "1701521d2fcdbdf677239bcc6f23748716bd94b01065b335e80524ca59ed21d0",
              "end_line": 320,
              "file_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
              "path": "android_world/task_evals/single/calendar/calendar.py",
              "snippet_sha256": "94cb97ada4d1ab13898c73768f5acdbc9c1949025e14a4c76be9434017c5f3c5",
              "start_line": 264,
              "symbol": "SimpleCalendarDeleteEvents"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.common_validators.sqlite_validators",
            "qualname": "DeleteMultipleRows",
            "source_ref": {
              "ast_sha256": "ca923ef63fa69675a3d12473d8a8408dd83b014e5d1d3165980d5f99c5d9d420",
              "end_line": 377,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "5055827ec532b73954b76374afa06255e2912e8a35043dccf6a1434fbcf88518",
              "start_line": 326,
              "symbol": "DeleteMultipleRows"
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
            "ast_sha256": "1701521d2fcdbdf677239bcc6f23748716bd94b01065b335e80524ca59ed21d0",
            "end_line": 320,
            "owner_module": "android_world.task_evals.single.calendar.calendar",
            "owner_qualname": "SimpleCalendarDeleteEvents",
            "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
            "snippet_sha256": "94cb97ada4d1ab13898c73768f5acdbc9c1949025e14a4c76be9434017c5f3c5",
            "start_line": 264
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
              "self.validate_deletion_integrity",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "DeleteMultipleRows",
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "source_ref": {
              "ast_sha256": "6d35e103b92d01f49545834dda821b0d4217b4a8b071e5636ea63ff47734639c",
              "end_line": 369,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "ecedf3193234967c7a93a0dfadd540474b7396e406dec52822ecee80dc2f8c50",
              "start_line": 360,
              "symbol": "DeleteMultipleRows.is_successful"
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
            "ast_sha256": "6d35e103b92d01f49545834dda821b0d4217b4a8b071e5636ea63ff47734639c",
            "end_line": 369,
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "owner_qualname": "DeleteMultipleRows.is_successful",
            "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "snippet_sha256": "ecedf3193234967c7a93a0dfadd540474b7396e406dec52822ecee80dc2f8c50",
            "start_line": 360
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
              "self.validate_deletion_integrity",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "DeleteMultipleRows",
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "source_ref": {
              "ast_sha256": "6d35e103b92d01f49545834dda821b0d4217b4a8b071e5636ea63ff47734639c",
              "end_line": 369,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "ecedf3193234967c7a93a0dfadd540474b7396e406dec52822ecee80dc2f8c50",
              "start_line": 360,
              "symbol": "DeleteMultipleRows.is_successful"
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
            "ast_sha256": "6d35e103b92d01f49545834dda821b0d4217b4a8b071e5636ea63ff47734639c",
            "end_line": 369,
            "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
            "owner_qualname": "DeleteMultipleRows.is_successful",
            "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "snippet_sha256": "ecedf3193234967c7a93a0dfadd540474b7396e406dec52822ecee80dc2f8c50",
            "start_line": 360
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
      "task_class": "SimpleCalendarDeleteEvents"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 1,
          "direct_calls": [
            "len",
            "self._validate_initial_state",
            "self.add_rows",
            "self.list_rows",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "DeleteMultipleRows",
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "source_ref": {
            "ast_sha256": "0ce07315f2c990a0f4634e6a60b4afaec9b926cbc6a06c3562412c741b6d818b",
            "end_line": 358,
            "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "path": "android_world/task_evals/common_validators/sqlite_validators.py",
            "snippet_sha256": "b8464cd90e2b5a18b7c4239356ceaa19dd7121e945c2b12d53e2b8f58dcbf684",
            "start_line": 348,
            "symbol": "DeleteMultipleRows.initialize_task"
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
          "ast_sha256": "0ce07315f2c990a0f4634e6a60b4afaec9b926cbc6a06c3562412c741b6d818b",
          "end_line": 358,
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "owner_qualname": "DeleteMultipleRows.initialize_task",
          "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "snippet_sha256": "b8464cd90e2b5a18b7c4239356ceaa19dd7121e945c2b12d53e2b8f58dcbf684",
          "start_line": 348
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
        "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}"
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
        "day",
        "month",
        "year"
      ],
      "metadata_template": "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.calendar.calendar",
        "owner_qualname": "SimpleCalendarDeleteEvents",
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
        "owner_qualname": "SimpleCalendarDeleteEvents.template",
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
        "owner_qualname": "SimpleCalendarDeleteEvents.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/calendar/calendar.py",
        "source_sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
        "owner_qualname": "DeleteMultipleRows.initialize_task",
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
        "owner_qualname": "DeleteMultipleRows.is_successful",
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
        "owner_qualname": "DeleteMultipleRows.is_successful",
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
          "ast_sha256": "b89eb9cd6b143faa94477ad7084a139d4468b3c5dc5e3f38c19451a24ce7679b",
          "end_line": 320,
          "owner_module": "android_world.task_evals.single.calendar.calendar",
          "owner_qualname": "SimpleCalendarDeleteEvents.generate_random_params",
          "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
          "snippet_sha256": "598014172b29052cb23b44a3927d9129577a16be8751fd73c547f70fee8e4029",
          "start_line": 298
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleCalendarDeleteEvents/canonical_task_semantics.json",
      "sha256": "3e4808b940c5db1122826c3d9e9b3dcc4f0275703fe76cc85ca9e8226623ab1d"
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-27",
              "dispatch_goal_sha256": "1ff1cce243b7142d010ee1f26fc86ba68ca626e689ddc49a59dfeaa566c7d390",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-19",
              "dispatch_goal_sha256": "ee866f9b6a0b1bd07d6d4bd101ef5ddd4a2dfb00165cc42c7af2f83ca2c5856b",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-16",
              "dispatch_goal_sha256": "78a3f6e0ad1126d14078aadc0aa80781efa403fcdecbd2a9372d089943460b04",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-22",
              "dispatch_goal_sha256": "4e31856b22ae618eb8e4ce974421f6ffa97423af8ecb259c7fb637e1731b683b",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-22",
              "dispatch_goal_sha256": "4e31856b22ae618eb8e4ce974421f6ffa97423af8ecb259c7fb637e1731b683b",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-23",
              "dispatch_goal_sha256": "0957e521029b5b970d716c989b6bf22f1cf5b29784d2af0eab1f94a31e82b015",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-25",
              "dispatch_goal_sha256": "3ccc3ec6049b882bf2c609f7fd64f3c58f59d7472edada6be8cfe1131369aa10",
              "parameter_keys": [
                "day",
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
              "dispatch_goal_model": "In Simple Calendar Pro, delete all the calendar events on 2023-10-29",
              "dispatch_goal_sha256": "52cf8633c7726a32cc2ccf4a97fc85a99d8d77af235bbb683cf3700c1e046951",
              "parameter_keys": [
                "day",
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
                "day",
                "month",
                "year"
              ],
              "template": "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}",
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
            "ast_sha256": "1701521d2fcdbdf677239bcc6f23748716bd94b01065b335e80524ca59ed21d0",
            "end_line": 320,
            "owner_module": "android_world.task_evals.single.calendar.calendar",
            "owner_qualname": "SimpleCalendarDeleteEvents.template",
            "sha256": "0383b2b0646649c1b6d4f1ffec9b1aca5fb3a7f1ff83279177409e92c622824f",
            "snippet_sha256": "94cb97ada4d1ab13898c73768f5acdbc9c1949025e14a4c76be9434017c5f3c5",
            "start_line": 264
          }
        ],
        "template": "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}"
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}",
      "optimal_steps": "7",
      "tags": [
        "parameterized",
        "data_edit"
      ],
      "task_name": "SimpleCalendarDeleteEvents"
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
