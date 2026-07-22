# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "ExpenseDeleteDuplicates2",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 93,
    "task_id": "ExpenseDeleteDuplicates2"
  },
  "integrity": {
    "semantic_record_sha256": "9230ca35ec87d6c7c76e50864538b5571b1fc333783fda82272ab82eb3803e65",
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
            "qualname": "ExpenseDeleteDuplicates2",
            "source_ref": {
              "ast_sha256": "f7c011ada7316d4ca0af85d93bf5cb7a705dd25495be789fdf8a39108941bbdf",
              "end_line": 227,
              "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
              "path": "android_world/task_evals/single/expense.py",
              "snippet_sha256": "23260396f7646639facb5d75bc23d9c50b1da4ad8b97179d897429449235fb63",
              "start_line": 195,
              "symbol": "ExpenseDeleteDuplicates2"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.expense",
            "qualname": "_ExpenseDeleteDuplicates",
            "source_ref": {
              "ast_sha256": "42703ec84fddeaad7d51e4c016d7b33db00b3b3a0670e8dbdddc6649817c3897",
              "end_line": 185,
              "file_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
              "path": "android_world/task_evals/single/expense.py",
              "snippet_sha256": "187eea8f297cc84d026293229c5d63949c1f2a2cda11d9cbe245cb43812b2fd3",
              "start_line": 145,
              "symbol": "_ExpenseDeleteDuplicates"
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
            "qualname": "DeleteDuplicateRows",
            "source_ref": {
              "ast_sha256": "d17c3a656318f94449d57903fa756690f326e76cc91f04a20428ab844a88ebbe",
              "end_line": 415,
              "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
              "path": "android_world/task_evals/common_validators/sqlite_validators.py",
              "snippet_sha256": "57571baf2fee35d9fd4a28a79627d0a101b4395bcd85ee86192c014e2e1d10da",
              "start_line": 380,
              "symbol": "DeleteDuplicateRows"
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
            "ast_sha256": "f7c011ada7316d4ca0af85d93bf5cb7a705dd25495be789fdf8a39108941bbdf",
            "end_line": 227,
            "owner_module": "android_world.task_evals.single.expense",
            "owner_qualname": "ExpenseDeleteDuplicates2",
            "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
            "snippet_sha256": "23260396f7646639facb5d75bc23d9c50b1da4ad8b97179d897429449235fb63",
            "start_line": 195
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
      "task_class": "ExpenseDeleteDuplicates2"
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
          "branch_node_count": 0,
          "direct_calls": [
            "self._validate_candidates",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "DeleteDuplicateRows",
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "source_ref": {
            "ast_sha256": "913ac8fa07894980d38691dd85aa7f1965109fedbed6a4ac96052a42672d0221",
            "end_line": 415,
            "file_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
            "path": "android_world/task_evals/common_validators/sqlite_validators.py",
            "snippet_sha256": "d98a5382bc0b522e08e449b394c42ad4efbd5136608e051dc46f3c865ea1f764",
            "start_line": 411,
            "symbol": "DeleteDuplicateRows.initialize_task"
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
          "ast_sha256": "913ac8fa07894980d38691dd85aa7f1965109fedbed6a4ac96052a42672d0221",
          "end_line": 415,
          "owner_module": "android_world.task_evals.common_validators.sqlite_validators",
          "owner_qualname": "DeleteDuplicateRows.initialize_task",
          "sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5",
          "snippet_sha256": "d98a5382bc0b522e08e449b394c42ad4efbd5136608e051dc46f3c865ea1f764",
          "start_line": 411
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
          "metadata_value": "Delete all but one of any expenses in arduia pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains."
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
      "metadata_placeholders": [],
      "metadata_template": "Delete all but one of any expenses in arduia pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
      "status": "mismatch"
    },
    "metadata_conflicts": [
      {
        "conflict_type": "app_display_name_alias",
        "difference_id": "task_template_vs_runtime_goal",
        "materiality": "non_material",
        "reason": "metadata says 'arduia pro expense' while the runtime goal uses the shorter installed-app label 'pro expense'; the duplicate-deletion requirement is unchanged",
        "resolution": "runtime_goal_text_is_canonical",
        "resolution_rule": "runtime_goal_text_is_canonical",
        "scope": "metadata_vs_runtime_goal",
        "status": "resolved"
      }
    ],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "ExpenseDeleteDuplicates2",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/expense.py",
        "source_sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794"
      },
      {
        "owner_module": "android_world.task_evals.single.expense",
        "owner_qualname": "_ExpenseDeleteDuplicates.goal",
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
        "owner_qualname": "ExpenseDeleteDuplicates2.generate_random_params",
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
        "owner_qualname": "DeleteDuplicateRows.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sqlite_validators.py",
        "source_sha256": "5c107b155910aafe590c88967f47ae069f5f68eb62319e7928ee7c5988dee1f5"
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
        "noise_row_objects",
        "row_objects",
        "seed"
      ],
      "observed_parameter_types": {
        "noise_row_objects": [
          "builtins.list"
        ],
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
          "ast_sha256": "168a1083d64f252f86a8b24de5873a85e51875ecf42efc4ea87f76b2c6160b58",
          "end_line": 227,
          "owner_module": "android_world.task_evals.single.expense",
          "owner_qualname": "ExpenseDeleteDuplicates2.generate_random_params",
          "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
          "snippet_sha256": "68895313118351dd9aa6831d6e27163505ee6fc81d9be3cf6abe591ba65060e4",
          "start_line": 202
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/ExpenseDeleteDuplicates2/canonical_task_semantics.json",
      "sha256": "9230ca35ec87d6c7c76e50864538b5571b1fc333783fda82272ab82eb3803e65"
    },
    "task_text": {
      "benchmark": "AndroidWorld",
      "canonical_goal": {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "branches": [],
        "computed_expression": {
          "branch_node_count": 0,
          "direct_calls": [],
          "direct_parameter_reads": []
        },
        "dispatch_phase": "after_initialize_task",
        "generation_semantics": {
          "computed_goal_semantics": {
            "branch_node_count": 0,
            "direct_calls": [],
            "direct_parameter_reads": []
          },
          "runtime_samples": [
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
              "dispatch_goal_model": "Delete all but one of any expenses in pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
              "dispatch_goal_sha256": "50ca96e1dbe1a3311fb29736ccddf8ee981126a5c51293dde9f5eee4ade38356",
              "parameter_keys": [
                "noise_row_objects",
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
            "ast_sha256": "0d6579cb583647842cb8af2d2f3e1fe89893946628e58b2a042eda02fd30d6ff",
            "end_line": 158,
            "owner_module": "android_world.task_evals.single.expense",
            "owner_qualname": "_ExpenseDeleteDuplicates.goal",
            "sha256": "facab47c4db013fdcf3630deb71efc1a119cbae472d02e573c0a8d57d02a7794",
            "snippet_sha256": "f518beecd60527f5b0172f63f6ce07c0462ab29186d53de4a5d95ff71998c877",
            "start_line": 152
          }
        ]
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Delete all but one of any expenses in arduia pro expense that are exact duplicates, ensuring at least one instance of each unique expense remains.",
      "optimal_steps": "9",
      "tags": [
        "data_edit",
        "requires_setup",
        "parameterized"
      ],
      "task_name": "ExpenseDeleteDuplicates2"
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
