# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "NotesTodoItemCount",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 49,
    "task_id": "NotesTodoItemCount"
  },
  "integrity": {
    "semantic_record_sha256": "bb90de3f06cf2ecd809d235df1d3ec5b6bb2e0e24b2a6f39a380cfdfbe4c5cbe",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "2b0f94fafe1ce8364c5732261873246887060de9062da83e1d87fa6378757037",
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
      "canonical_module": "android_world.task_evals.information_retrieval.information_retrieval_registry",
      "definition": {
        "definition_kind": "dynamic_ir_proto",
        "incidental_runtime_module_excluded": "abc",
        "mro": [
          {
            "canonical_androidworld_source": false,
            "qualname": "NotesTodoItemCount",
            "runtime_reported_module": "abc",
            "source_ref": null
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.information_retrieval.information_retrieval",
            "qualname": "InformationRetrieval",
            "source_ref": {
              "ast_sha256": "04d486479faeeb56e267547311bfe824a461a47a5fb48746c0dfd4b58f5de5ee",
              "end_line": 130,
              "file_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
              "path": "android_world/task_evals/information_retrieval/information_retrieval.py",
              "snippet_sha256": "cb709bb2698f4606481d6f7aacf16340fad7630eb122a7c0207fbec4472d9581",
              "start_line": 31,
              "symbol": "InformationRetrieval"
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
        "runtime_reported_module": "abc",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
            "ast_sha256": null,
            "end_line": 3523,
            "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
            "owner_qualname": "NotesTodoItemCount",
            "sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
            "snippet_sha256": "eb9a831749fbfd6732027d1ee5b21becd927ae8c2a36484e795b47c872a8f6e7",
            "start_line": 3434
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
            "ast_sha256": "abc80d4373b2ed723e70e2bb94ec1d20aea1459e1997e0ee3745ace6989d6919",
            "end_line": 113,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval_registry",
            "owner_qualname": "InformationRetrievalRegistry._build_task_class",
            "sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08",
            "snippet_sha256": "a3b892a7372466abab43e7123d0062f515f191ad01eb81d9772789cec2e6e033",
            "start_line": 75
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
            "ast_sha256": "04d486479faeeb56e267547311bfe824a461a47a5fb48746c0dfd4b58f5de5ee",
            "end_line": 130,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "owner_qualname": "InformationRetrieval",
            "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
            "snippet_sha256": "cb709bb2698f4606481d6f7aacf16340fad7630eb122a7c0207fbec4472d9581",
            "start_line": 31
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "proto_utils.check_agent_answer",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "InformationRetrieval",
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "source_ref": {
              "ast_sha256": "c0b5c1d99c6adaa203b1d7b31fab4469c278bf4dad8d1a4d0b66239876fe6f42",
              "end_line": 119,
              "file_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
              "path": "android_world/task_evals/information_retrieval/information_retrieval.py",
              "snippet_sha256": "5c49222032672cb6c2578bfa85e2636628eaacd1dba4d8410877d2560477753b",
              "start_line": 109,
              "symbol": "InformationRetrieval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
            "ast_sha256": "c0b5c1d99c6adaa203b1d7b31fab4469c278bf4dad8d1a4d0b66239876fe6f42",
            "end_line": 119,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "owner_qualname": "InformationRetrieval.is_successful",
            "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
            "snippet_sha256": "5c49222032672cb6c2578bfa85e2636628eaacd1dba4d8410877d2560477753b",
            "start_line": 109
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
              "proto_utils.check_agent_answer",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "InformationRetrieval",
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "source_ref": {
              "ast_sha256": "c0b5c1d99c6adaa203b1d7b31fab4469c278bf4dad8d1a4d0b66239876fe6f42",
              "end_line": 119,
              "file_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
              "path": "android_world/task_evals/information_retrieval/information_retrieval.py",
              "snippet_sha256": "5c49222032672cb6c2578bfa85e2636628eaacd1dba4d8410877d2560477753b",
              "start_line": 109,
              "symbol": "InformationRetrieval.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
            "ast_sha256": "c0b5c1d99c6adaa203b1d7b31fab4469c278bf4dad8d1a4d0b66239876fe6f42",
            "end_line": 119,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "owner_qualname": "InformationRetrieval.is_successful",
            "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
            "snippet_sha256": "5c49222032672cb6c2578bfa85e2636628eaacd1dba4d8410877d2560477753b",
            "start_line": 109
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
      "task_class": "NotesTodoItemCount"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 4,
          "direct_calls": [
            "_maybe_replace_date",
            "activity_app_utils.setup_task_state",
            "calendar_utils_ir.setup_task_state",
            "joplin_app_utils.setup_task_state",
            "list",
            "proto_utils.initialize_proto",
            "self.is_calendar_task",
            "self.is_notes_task",
            "self.is_sports_task",
            "self.is_tasks_task",
            "super",
            "super.initialize_task",
            "task_app_utils.setup_task_state"
          ],
          "direct_parameter_reads": [],
          "owner_class": "InformationRetrieval",
          "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
          "source_ref": {
            "ast_sha256": "5e2fa4be71f4e762a4df111ee20d40ee6f909091772881bb64d9cf17b6da49d0",
            "end_line": 107,
            "file_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
            "path": "android_world/task_evals/information_retrieval/information_retrieval.py",
            "snippet_sha256": "74c5a02c0cd62ad57e5699e2b4ad64b8b373787fbff55eca3468d97fc3b69a98",
            "start_line": 82,
            "symbol": "InformationRetrieval.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
          "ast_sha256": "5e2fa4be71f4e762a4df111ee20d40ee6f909091772881bb64d9cf17b6da49d0",
          "end_line": 107,
          "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
          "owner_qualname": "InformationRetrieval.initialize_task",
          "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
          "snippet_sha256": "74c5a02c0cd62ad57e5699e2b4ad64b8b373787fbff55eca3468d97fc3b69a98",
          "start_line": 82
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
        "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number."
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
        "folder"
      ],
      "metadata_template": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
        "owner_qualname": "NotesTodoItemCount",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
        "source_sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval_registry",
        "owner_qualname": "InformationRetrievalRegistry._build_task_class",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
        "source_sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
        "owner_qualname": "NotesTodoItemCount.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
        "source_sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0"
      },
      {
        "owner_module": "abc",
        "owner_qualname": "NotesTodoItemCount.task_template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
        "source_sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval_registry",
        "owner_qualname": "InformationRetrievalRegistry._build_task_class",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
        "source_sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
      },
      {
        "owner_module": "abc",
        "owner_qualname": "NotesTodoItemCount.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
        "source_sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
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
        "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
        "owner_qualname": "InformationRetrieval.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
        "source_sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b"
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
        "body",
        "folder",
        "seed",
        "title"
      ],
      "observed_parameter_types": {
        "body": [
          "builtins.str"
        ],
        "folder": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ],
        "title": [
          "builtins.str"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "empty",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
          "ast_sha256": "04d486479faeeb56e267547311bfe824a461a47a5fb48746c0dfd4b58f5de5ee",
          "end_line": 130,
          "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
          "owner_qualname": "InformationRetrieval.schema",
          "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
          "snippet_sha256": "cb709bb2698f4606481d6f7aacf16340fad7630eb122a7c0207fbec4472d9581",
          "start_line": 31
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
          "ast_sha256": "368cc93a74e2fb9b3c34fb50e4c36993314625cffa5386f1bf23a013d3ae323a",
          "end_line": 97,
          "owner_module": "abc",
          "owner_qualname": "NotesTodoItemCount.generate_random_params",
          "sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08",
          "snippet_sha256": "9053d9f1b4df46971e938c4a3d7656b17d0f230860f6bcd170184434e4c5b342",
          "start_line": 90
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/NotesTodoItemCount/canonical_task_semantics.json",
      "sha256": "bb90de3f06cf2ecd809d235df1d3ec5b6bb2e0e24b2a6f39a380cfdfbe4c5cbe"
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
              "dispatch_goal_model": "How many to-dos do I have in the 'Recipes' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "88784a64a9f724ba59a281d98fa22499b83227ddccd779d02a711698782e89e7",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'School' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "7481ec2d017e22fc1a0b628eaf03cc510a58c665aa82e0046ae9ec9b163cd89e",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Personal' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "b069ecf8f3709f7cce8d2f230ec2c691e2437b92cc5cf21b847c6cc1a6f53479",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Home' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "2687d106a924fdd9cb24deae916486df241566418b06f07dabfea07ea6153fb6",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Home' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "2687d106a924fdd9cb24deae916486df241566418b06f07dabfea07ea6153fb6",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Travel' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "882ddea5909ee010feeceefa8b70fa3679efe15b2a92504d6d1be623332d1237",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Ideas' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "7ba0466aabc1f41d6b6f577c12ba2eb137a33c9a9443fbf2c2dddfe0c8ced035",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "How many to-dos do I have in the 'Finance' folder in the Joplin app? Express your answer as just a single number.",
              "dispatch_goal_sha256": "23647076fee249b99e023b0915d5ec1264c4ab32410cf37d773a07ea3159fbba",
              "parameter_keys": [
                "body",
                "folder",
                "seed",
                "title"
              ],
              "pure_pre_dispatch_transforms": [
                "proto_utils.initialize_proto(task.task, task.params)",
                "information_retrieval._maybe_replace_date(task.params)"
              ],
              "sample_kind": "fixed_seed",
              "suite_seed": 11
            }
          ],
          "samples_are_examples_not_generic_templates": true,
          "templates": [
            {
              "placeholders": [
                "folder"
              ],
              "template": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
              "variant_id": "textproto_prompt"
            }
          ]
        },
        "prompt": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
        "proto_binding": {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
          "selector": "tasks[name=\"NotesTodoItemCount\"]",
          "source_sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
          "task_definition": {
            "name": "NotesTodoItemCount",
            "prompt": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
            "relevant_state": {
              "exclusion_conditions": [
                {
                  "field": "is_todo",
                  "operation": "EQUAL_TO",
                  "value": "True"
                },
                {
                  "field": "folder",
                  "operation": "EQUAL_TO",
                  "value": "{folder}"
                }
              ],
              "state": {
                "notes_app": {
                  "notes": [
                    {
                      "body": "{body_without_replacement}",
                      "folder": "{folder}",
                      "is_todo": "True",
                      "title": "{title_without_replacement}"
                    },
                    {
                      "body": "{body_without_replacement}",
                      "folder": "{folder}",
                      "is_todo": "True",
                      "title": "{title_without_replacement}"
                    },
                    {
                      "body": "{body_without_replacement}",
                      "folder": "{folder}",
                      "is_todo": "True",
                      "title": "{title_without_replacement}"
                    }
                  ]
                }
              }
            },
            "success_criteria": {
              "expectations": [
                {
                  "field_transformation": {
                    "field_name": "is_todo",
                    "operation": "COUNT"
                  },
                  "match_type": "NUMBER_MATCH"
                }
              ]
            },
            "task_params": [
              {
                "name": "folder",
                "possible_values": [
                  "Personal",
                  "Work",
                  "School",
                  "Home",
                  "Projects",
                  "Ideas",
                  "Recipes",
                  "Finance",
                  "Health",
                  "Travel"
                ]
              },
              {
                "name": "title",
                "possible_values": [
                  "Grocery List",
                  "Meeting Agenda",
                  "Personal Goals",
                  "Work Tasks",
                  "Home Improvement",
                  "Study Notes",
                  "Recipe Ideas",
                  "Financial Plan",
                  "Health Routine",
                  "Travel Itinerary"
                ]
              },
              {
                "name": "body",
                "possible_values": [
                  "Buy milk, eggs, bread, and cereal from the grocery store.",
                  "Discuss project updates, assign tasks, and review deadlines.",
                  "Exercise 3 times a week, read 1 book per month, and save $500.",
                  "Complete quarterly report, schedule team meeting, and follow up with clients.",
                  "Paint the living room, fix leaky faucet, and organize closet.",
                  "Review chapters 1-5 for upcoming exam, create flashcards, and practice problems.",
                  "Try new pasta recipe with homemade sauce and garlic bread.",
                  "Create monthly budget, track expenses, and set savings goals.",
                  "Go for a 30-minute run, do yoga for flexibility, and meditate for relaxation.",
                  "Book flights, reserve accommodations, and plan sightseeing activities."
                ]
              }
            ]
          },
          "task_definition_sha256": "f3d62df7ab9c33c6dffcf9ded4e6d4ff402fbed2256dd5acc8ff0e1888b65f3b",
          "task_name": "NotesTodoItemCount",
          "task_proto_wire_sha256": "86bee5b31e63f4000d9036fd5806dc3981c2aaf64ca1d9be76b7c5712433b974"
        },
        "representation_kind": "ir_proto_prompt",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
            "ast_sha256": null,
            "end_line": 3523,
            "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
            "owner_qualname": "NotesTodoItemCount.goal",
            "sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
            "snippet_sha256": "eb9a831749fbfd6732027d1ee5b21becd927ae8c2a36484e795b47c872a8f6e7",
            "start_line": 3434
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
            "ast_sha256": "40d8138d4e78fd8838d99f342cfc1383d3fd0bdb64a6015e95b82797a265704a",
            "end_line": 101,
            "owner_module": "abc",
            "owner_qualname": "NotesTodoItemCount.task_template",
            "sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08",
            "snippet_sha256": "b9f37ae7c440206bbd990d4b20af1d7a3915be14bbb7dfb1caee6987b7ae8fcf",
            "start_line": 99
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
            "ast_sha256": "abc80d4373b2ed723e70e2bb94ec1d20aea1459e1997e0ee3745ace6989d6919",
            "end_line": 113,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval_registry",
            "owner_qualname": "InformationRetrievalRegistry._build_task_class",
            "sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08",
            "snippet_sha256": "a3b892a7372466abab43e7123d0062f515f191ad01eb81d9772789cec2e6e033",
            "start_line": 75
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval.py",
            "ast_sha256": "04d486479faeeb56e267547311bfe824a461a47a5fb48746c0dfd4b58f5de5ee",
            "end_line": 130,
            "owner_module": "android_world.task_evals.information_retrieval.information_retrieval",
            "owner_qualname": "InformationRetrieval",
            "sha256": "c222532161018cc3523d9f481f1d8c1ce65c2aa7c44066ff2f51892284c4f75b",
            "snippet_sha256": "cb709bb2698f4606481d6f7aacf16340fad7630eb122a7c0207fbec4472d9581",
            "start_line": 31
          }
        ],
        "template": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number."
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "How many to-dos do I have in the '{folder}' folder in the Joplin app? Express your answer as just a single number.",
      "optimal_steps": "5",
      "tags": [
        "information_retrieval",
        "math_counting",
        "parameterized"
      ],
      "task_name": "NotesTodoItemCount"
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
