# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "ExpenseDeleteMultiple",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 35,
    "task_id": "ExpenseDeleteMultiple"
  },
  "integrity": {
    "semantic_record_sha256": "c3224a3b07bc981ca5a585acdf0b35087a5e1f8947b46589702759b90d2dd865",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "3ef184715ce604a9d39d91cb75cb78b3974073ee8436fbaa5c5dd5ba1b11f37c",
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
      "canonical_module": "android_world.task_evals.single.expense",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.expense",
            "qualname": "ExpenseDeleteMultiple",
            "source_ref": {
              "ast_sha256": "f6a148109abd428e56319ae437c181c324be61d2b661d0919f41aa70d8c18d2b",
              "end_line": 134,
              "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
              "path": "android_world/task_evals/single/expense.py",
              "snippet_sha256": "f1ced3a0d7ecaeace732ae78209d717c0d9bb24aa8506365f34d27c885a87459",
              "start_line": 129,
              "symbol": "ExpenseDeleteMultiple"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.expense",
            "qualname": "_ExpenseDeleteMultiple",
            "source_ref": {
              "ast_sha256": "31bede7cca033a2bf93b74aac94d0756b1301408516e2054cd2f107c24a75101",
              "end_line": 118,
              "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
              "path": "android_world/task_evals/single/expense.py",
              "snippet_sha256": "d58768716323c69b3e6b4b47c9560cb5e70a1b9cf8422b31fb4277815b58fd34",
              "start_line": 69,
              "symbol": "_ExpenseDeleteMultiple"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.expense",
            "qualname": "_Expense",
            "source_ref": {
              "ast_sha256": "fda54ecc54b6602bba00b3917a09c9fcf414858da816816dde91a50590751eff",
              "end_line": 66,
              "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
              "path": "android_world/task_evals/single/expense.py",
              "snippet_sha256": "fdfd3ef7b45cc19187af0c4b7fe64007d7628e14b450e3b896d7fd6eec3f0276",
              "start_line": 48,
              "symbol": "_Expense"
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
        "runtime_reported_module": "android_world.task_evals.single.expense",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
            "ast_sha256": "f6a148109abd428e56319ae437c181c324be61d2b661d0919f41aa70d8c18d2b",
            "end_line": 134,
            "owner_module": "android_world.task_evals.single.expense",
            "owner_qualname": "ExpenseDeleteMultiple",
            "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
            "snippet_sha256": "f1ced3a0d7ecaeace732ae78209d717c0d9bb24aa8506365f34d27c885a87459",
            "start_line": 129
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
      "task_class": "ExpenseDeleteMultiple"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 1,
          "direct_calls": [
            "apps.ExpenseApp.setup",
            "sqlite_utils.table_exists",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "_Expense",
          "owner_module": "android_world.task_evals.single.expense",
          "source_ref": {
            "ast_sha256": "87833663248dee8a3b91daefcb590c2579294c85ba5d59805bd83a4a76b7931c",
            "end_line": 66,
            "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
            "path": "android_world/task_evals/single/expense.py",
            "snippet_sha256": "29329588a49d7066bda7b36a11867c29465b0217c5ce8301cf5982a0c67a70ca",
            "start_line": 63,
            "symbol": "_Expense.initialize_task"
          }
        },
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
          "ast_sha256": "87833663248dee8a3b91daefcb590c2579294c85ba5d59805bd83a4a76b7931c",
          "end_line": 66,
          "owner_module": "android_world.task_evals.single.expense",
          "owner_qualname": "_Expense.initialize_task",
          "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
          "snippet_sha256": "29329588a49d7066bda7b36a11867c29465b0217c5ce8301cf5982a0c67a70ca",
          "start_line": 63
        },
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
      "canonical_templates": [],
      "comparison_is_semantic_proof": false,
      "differences": [
        {
          "canonical_runtime_templates": [],
          "comparison_status": "mismatch",
          "difference_id": "task_template_vs_runtime_goal",
          "field": "task_template",
          "metadata_value": "Delete the following expenses from arduia pro expense: {expenses}."
        }
      ],
      "fixed_seed_sample_shape_matches": [
        false,
        false,
        false,
        false,
        false,
        false,
        false,
        false
      ],
      "has_difference": true,
      "matches_runtime": false,
      "metadata_placeholders": [
        "expenses"
      ],
      "metadata_template": "Delete the following expenses from arduia pro expense: {expenses}.",
      "status": "mismatch"
    },
    "metadata_conflicts": [
      {
        "conflict_type": "app_display_name_alias_and_runtime_rendering",
        "difference_id": "task_template_vs_runtime_goal",
        "materiality": "non_material",
        "reason": "metadata uses the older 'arduia pro expense' label and an expenses placeholder; runtime uses 'pro expense' and renders the same selected expense names",
        "resolution": "runtime_goal_text_is_canonical",
        "resolution_rule": "runtime_goal_text_is_canonical",
        "scope": "metadata_vs_runtime_goal",
        "status": "resolved"
      }
    ],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "ExpenseDeleteMultiple",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
      },
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "_ExpenseDeleteMultiple.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
      },
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "_Expense.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
      },
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "_ExpenseDeleteMultiple.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
      },
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "_Expense.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
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
        "row_objects",
        "seed"
      ],
      "observed_parameter_types": {
        "row_objects": [
          "builtins.list"
        ],
        "seed": [
          "builtins.int"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "empty",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
          "ast_sha256": "fda54ecc54b6602bba00b3917a09c9fcf414858da816816dde91a50590751eff",
          "end_line": 66,
          "owner_module": "android_world.task_evals.single.expense",
          "owner_qualname": "_Expense.schema",
          "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
          "snippet_sha256": "fdfd3ef7b45cc19187af0c4b7fe64007d7628e14b450e3b896d7fd6eec3f0276",
          "start_line": 48
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
          "ast_sha256": "b41f2818ba7b630baa54320ac12b0a50c6565c7cb75601194d46d6341d10c834",
          "end_line": 118,
          "owner_module": "android_world.task_evals.single.expense",
          "owner_qualname": "_ExpenseDeleteMultiple.generate_random_params",
          "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
          "snippet_sha256": "b14e8ae041e1153e091287bf7dca09f8b0498104ca660466e3328847149b2f44",
          "start_line": 98
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/ExpenseDeleteMultiple/canonical_task_semantics.json",
      "sha256": "c3224a3b07bc981ca5a585acdf0b35087a5e1f8947b46589702759b90d2dd865"
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
          "direct_parameter_reads": []
        },
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": {
            "branch_node_count": 0,
            "direct_calls": [
              "join"
            ],
            "direct_parameter_reads": []
          },
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Taxi Fare, Event Tickets, Health Insurance.",
              "dispatch_goal_sha256": "3e824b79f531565d1ba25cf75943d918ece51a9eef95abcacd844e43bada79d1",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Interest Income, Sportswear, Car Insurance.",
              "dispatch_goal_sha256": "c1034619cbe7beabdc5d156c7ded7e60ce17a2fe0d0095fb5324b2bb3f70f6ae",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Freelance Payment, Crowdfunding, Legal Fees.",
              "dispatch_goal_sha256": "5ff397d642127cb190142143e9dca405327d761674415ea315b63f0ac1fc6354",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Health Insurance, School Supplies, Night Out.",
              "dispatch_goal_sha256": "2fa53e5048f75ddeb992593c3d45a066e286dad385b7a15f1e8875a9d323e8b3",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Capital Gains, Miscellaneous Gifts, Landscaping.",
              "dispatch_goal_sha256": "629e394f038f6c59df8244c1e9a635311ea0385fcbd06a81a86209296f6de03c",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Museum Tickets, Charity, Furnishing.",
              "dispatch_goal_sha256": "f9eaa03b4b88f4274cf1ce92fdfe9c24001e3c838f92865d5e4b768ea9f02120",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Taxi Fare, Amusement Park, Capital Gains.",
              "dispatch_goal_sha256": "7e61046a40dd849838aeeb223abd24511558359c54ca57b26227daed35680e6d",
              "parameter_keys": [
                "row_objects",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete the following expenses from pro expense: Undergarments, Specialty Foods, Reimbursements.",
              "dispatch_goal_sha256": "0d84f281fbecad8f00d3a0244b7f7eba531f73e72276aefd20137a7cec04c3eb",
              "parameter_keys": [
                "row_objects",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
            "ast_sha256": "e750bc00791a0632e1ca1c6031e7ca29c29c006b321f687713a76cbf8686fa05",
            "end_line": 83,
            "owner_module": "android_world.task_evals.single.expense",
            "owner_qualname": "_ExpenseDeleteMultiple.goal",
            "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
            "snippet_sha256": "cfa3179e3183edec29156e7bd3f93dab1ad820810392d46336424f793e87aef8",
            "start_line": 76
          }
        ]
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Delete the following expenses from arduia pro expense: {expenses}.",
      "optimal_steps": "10",
      "tags": [
        "data_edit",
        "parameterized"
      ],
      "task_name": "ExpenseDeleteMultiple"
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
