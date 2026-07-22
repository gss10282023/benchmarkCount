# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "RecipeDeleteSingleRecipe",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 27,
    "task_id": "RecipeDeleteSingleRecipe"
  },
  "integrity": {
    "semantic_record_sha256": "c1a387b49f0e8646ad0b6b9a60a214788e9d8e8356964b6ed3f3090e454a6612",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "57b4913d6722d6933a7731e63b303d5759af10926667118fad72e6881ad7ce98",
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
      "canonical_module": "android_world.task_evals.single.recipe",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.recipe",
            "qualname": "RecipeDeleteSingleRecipe",
            "source_ref": {
              "ast_sha256": "8f0005118a44ec6e935b0b6047161823e9d4bce2ea2c0696043c08e32c20b27c",
              "end_line": 106,
              "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
              "path": "android_world/task_evals/single/recipe.py",
              "snippet_sha256": "d48cb42e2c8b0ad66f0cd6ae9d99e99f69db1a3fd814a0427090bafa553c02dc",
              "start_line": 101,
              "symbol": "RecipeDeleteSingleRecipe"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.recipe",
            "qualname": "_RecipeDeleteMultipleRecipes",
            "source_ref": {
              "ast_sha256": "8196e7cec6ad9e863bfc7626b6c3af7243a7ae6d2e08726c290d9bf43a67b775",
              "end_line": 98,
              "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
              "path": "android_world/task_evals/single/recipe.py",
              "snippet_sha256": "951ef6cbd0a7b2df306e997f6721afa0e4d2bf0ca484f6bf3b50c9b02dfa60a9",
              "start_line": 52,
              "symbol": "_RecipeDeleteMultipleRecipes"
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
            "module": "android_world.task_evals.single.recipe",
            "qualname": "_RecipeApp",
            "source_ref": {
              "ast_sha256": "d425a552f70acef4f36579d7bb60974857f9a8afea589833f5ac01bf06c5fb0b",
              "end_line": 49,
              "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
              "path": "android_world/task_evals/single/recipe.py",
              "snippet_sha256": "d87ddd9bb7e710c085dbfe24049beb4ce64873771336a5827dffde9305148531",
              "start_line": 38,
              "symbol": "_RecipeApp"
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
        "runtime_reported_module": "android_world.task_evals.single.recipe",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
            "ast_sha256": "8f0005118a44ec6e935b0b6047161823e9d4bce2ea2c0696043c08e32c20b27c",
            "end_line": 106,
            "owner_module": "android_world.task_evals.single.recipe",
            "owner_qualname": "RecipeDeleteSingleRecipe",
            "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
            "snippet_sha256": "d48cb42e2c8b0ad66f0cd6ae9d99e99f69db1a3fd814a0427090bafa553c02dc",
            "start_line": 101
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
      "task_class": "RecipeDeleteSingleRecipe"
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
        "titles"
      ],
      "metadata_template": "Delete the following recipes from Broccoli app: {titles}.",
      "status": "fixed_seed_goal_shape_match"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "RecipeDeleteSingleRecipe",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
      },
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "_RecipeDeleteMultipleRecipes.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
      },
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "_RecipeApp.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
      },
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "_RecipeDeleteMultipleRecipes.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
          "ast_sha256": "d425a552f70acef4f36579d7bb60974857f9a8afea589833f5ac01bf06c5fb0b",
          "end_line": 49,
          "owner_module": "android_world.task_evals.single.recipe",
          "owner_qualname": "_RecipeApp.schema",
          "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
          "snippet_sha256": "d87ddd9bb7e710c085dbfe24049beb4ce64873771336a5827dffde9305148531",
          "start_line": 38
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
          "ast_sha256": "fc807c5d7935c68a0dbb0c15ac7e8269330d5c78dc57208606042c2602490c4b",
          "end_line": 98,
          "owner_module": "android_world.task_evals.single.recipe",
          "owner_qualname": "_RecipeDeleteMultipleRecipes.generate_random_params",
          "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
          "snippet_sha256": "413ee41ce2aafc235672e41f03a59fe4626b72ed59f24f07e204bc97575da1a4",
          "start_line": 78
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/RecipeDeleteSingleRecipe/canonical_task_semantics.json",
      "sha256": "c1a387b49f0e8646ad0b6b9a60a214788e9d8e8356964b6ed3f3090e454a6612"
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Chicken Alfredo Pasta.",
              "dispatch_goal_sha256": "4bf43db9efb317fc37b23c5056bd3a1451338e5ffdc7177eb08037075d5145eb",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Turkey and Cheese Panini.",
              "dispatch_goal_sha256": "db9a1e1164f960480af344e9fe7614d5f3b92ba164b36815d507af4b230e280b",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Quick Fried Rice.",
              "dispatch_goal_sha256": "448fe32106939c10ed3525391383b4fee4664dfaaf12a8004757116e0cf4439d",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Cauliflower Fried \"Rice\".",
              "dispatch_goal_sha256": "c87fe3f2ed505661c01588c580da033621846b0d49f87555e7f13310125d73ec",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Cauliflower Fried \"Rice\".",
              "dispatch_goal_sha256": "c87fe3f2ed505661c01588c580da033621846b0d49f87555e7f13310125d73ec",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Sweet Potato and Black Bean Tacos.",
              "dispatch_goal_sha256": "30e95f1aa8b47f1247a1be7c8be4fdef6d3e793a28a8bad5f44704bc968b6c1a",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Chicken Caesar Salad Wrap.",
              "dispatch_goal_sha256": "d28e5f59ac4c21b97c1337eaf2fffbdb269151d38158ffe35567b5a4c40a602e",
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
              "dispatch_goal_model": "Delete the following recipes from Broccoli app: Butternut Squash Soup.",
              "dispatch_goal_sha256": "4f37846810fa36b94411457cc3f8ca2dc354c8910e6efcee1a238f4c4c8c4f39",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
            "ast_sha256": "d4c76dc2459580f6cdddeceb4ae9475b7e27e20b88728491ee0d967034c3e530",
            "end_line": 66,
            "owner_module": "android_world.task_evals.single.recipe",
            "owner_qualname": "_RecipeDeleteMultipleRecipes.goal",
            "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
            "snippet_sha256": "62c5472815d1389db4014bc2320ed8a25586f3a26ac787130dfa15a77cca8502",
            "start_line": 61
          }
        ]
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Delete the following recipes from Broccoli app: {titles}.",
      "optimal_steps": "5",
      "tags": [
        "data_edit",
        "search",
        "parameterized"
      ],
      "task_name": "RecipeDeleteSingleRecipe"
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
