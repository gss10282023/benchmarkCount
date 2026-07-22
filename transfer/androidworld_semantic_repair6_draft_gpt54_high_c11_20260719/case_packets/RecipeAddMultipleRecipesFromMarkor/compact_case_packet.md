# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "RecipeAddMultipleRecipesFromMarkor",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 16,
    "task_id": "RecipeAddMultipleRecipesFromMarkor"
  },
  "integrity": {
    "semantic_record_sha256": "5cdb774ed8e5fcf74a9227d5233f43035d9b3906a23699494f9a8721521f4df0",
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
            "qualname": "RecipeAddMultipleRecipesFromMarkor",
            "source_ref": {
              "ast_sha256": "bd7003c35dc304a58f032c1f24d309aa8815579b12dde0fa436b7b4540ba298d",
              "end_line": 456,
              "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
              "path": "android_world/task_evals/single/recipe.py",
              "snippet_sha256": "6c43ac1cb30d7df5cc07965859ffdf365b3e1d0f7e2d6af757c73f778851b612",
              "start_line": 428,
              "symbol": "RecipeAddMultipleRecipesFromMarkor"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.recipe",
            "qualname": "_RecipeAddMultipleRecipes",
            "source_ref": {
              "ast_sha256": "156bdaa9ae3239cb930c30b61d108298244c4699a71abc56ce57dd5e28d90c1f",
              "end_line": 409,
              "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
              "path": "android_world/task_evals/single/recipe.py",
              "snippet_sha256": "330821acc9713e2863d10092980f7f20a4a41b196dd7584ab85b7125fb94b603",
              "start_line": 339,
              "symbol": "_RecipeAddMultipleRecipes"
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
            "ast_sha256": "bd7003c35dc304a58f032c1f24d309aa8815579b12dde0fa436b7b4540ba298d",
            "end_line": 456,
            "owner_module": "android_world.task_evals.single.recipe",
            "owner_qualname": "RecipeAddMultipleRecipesFromMarkor",
            "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
            "snippet_sha256": "6c43ac1cb30d7df5cc07965859ffdf365b3e1d0f7e2d6af757c73f778851b612",
            "start_line": 428
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
      "task_class": "RecipeAddMultipleRecipesFromMarkor"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "_get_rows_as_text",
            "file_utils.clear_directory",
            "super",
            "super.initialize_task",
            "user_data_generation.write_to_markor"
          ],
          "direct_parameter_reads": [],
          "owner_class": "RecipeAddMultipleRecipesFromMarkor",
          "owner_module": "android_world.task_evals.single.recipe",
          "source_ref": {
            "ast_sha256": "87dfd7f1ec296d4fef31a6c63b089995249e230af7dfa0f9b167141d62bae269",
            "end_line": 452,
            "file_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
            "path": "android_world/task_evals/single/recipe.py",
            "snippet_sha256": "bc982be1b940a478314ba0aa307626610e6ee1ab53904590d97c8a1631ca64c2",
            "start_line": 442,
            "symbol": "RecipeAddMultipleRecipesFromMarkor.initialize_task"
          }
        },
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
          "ast_sha256": "87dfd7f1ec296d4fef31a6c63b089995249e230af7dfa0f9b167141d62bae269",
          "end_line": 452,
          "owner_module": "android_world.task_evals.single.recipe",
          "owner_qualname": "RecipeAddMultipleRecipesFromMarkor.initialize_task",
          "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
          "snippet_sha256": "bc982be1b940a478314ba0aa307626610e6ee1ab53904590d97c8a1631ca64c2",
          "start_line": 442
        },
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
      "metadata_placeholders": [],
      "metadata_template": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
      "status": "fixed_seed_goal_shape_match"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "RecipeAddMultipleRecipesFromMarkor",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
      },
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "RecipeAddMultipleRecipesFromMarkor.goal",
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
        "owner_qualname": "_RecipeAddMultipleRecipes.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
      },
      {
        "owner_module": "android_world.task_evals.single.recipe",
        "owner_qualname": "RecipeAddMultipleRecipesFromMarkor.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/recipe.py",
        "source_sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674"
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
        "noise_row_objects",
        "row_objects",
        "seed",
        "text_representation_type"
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
        ],
        "text_representation_type": [
          "builtins.str"
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
          "ast_sha256": "2a5d3069256eea370ea839c172ad6b8c93ca31953af0eca028694a4364baa054",
          "end_line": 409,
          "owner_module": "android_world.task_evals.single.recipe",
          "owner_qualname": "_RecipeAddMultipleRecipes.generate_random_params",
          "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
          "snippet_sha256": "c4ee7efce5643f7669acf719651b05b7286238de1cdd5e4f78ee03cc0bd8dd16",
          "start_line": 391
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/RecipeAddMultipleRecipesFromMarkor/canonical_task_semantics.json",
      "sha256": "5cdb774ed8e5fcf74a9227d5233f43035d9b3906a23699494f9a8721521f4df0"
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
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
              "dispatch_goal_sha256": "baf52bb034f0deb6093a2cc267df77c12db96bfbf511fe6fd1b9f40608865154",
              "parameter_keys": [
                "noise_row_objects",
                "row_objects",
                "seed",
                "text_representation_type"
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
            "ast_sha256": "87861fb43dd77fb0e0c83cccbdd1853e6110dff18a9083e399b961efe7db9715",
            "end_line": 440,
            "owner_module": "android_world.task_evals.single.recipe",
            "owner_qualname": "RecipeAddMultipleRecipesFromMarkor.goal",
            "sha256": "3c3f389e510bef1f45ed192bbc1e57531dfd92fcb3fdec5f576091b434f21674",
            "snippet_sha256": "c4bf7c9a5d3f0e39b3572c386479ab1fe4c19cc3282a642ad44d6baf2711e59c",
            "start_line": 436
          }
        ]
      },
      "difficulty": "hard",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Add the recipes from recipes.txt in Markor to the Broccoli recipe app.",
      "optimal_steps": "24",
      "tags": [
        "data_entry",
        "multi_app",
        "screen_reading",
        "memorization",
        "parameterized"
      ],
      "task_name": "RecipeAddMultipleRecipesFromMarkor"
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
