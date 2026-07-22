# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SportsTrackerActivityDuration",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 50,
    "task_id": "SportsTrackerActivityDuration"
  },
  "integrity": {
    "semantic_record_sha256": "ebdede275b15cbac8ae54b2e50a0d8f1df790a9981662631e05bc253bb5ea17d",
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
            "qualname": "SportsTrackerActivityDuration",
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
            "end_line": 2485,
            "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
            "owner_qualname": "SportsTrackerActivityDuration",
            "sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
            "snippet_sha256": "e3e91f527c6fcb296a9d7b5fa19b626441bdfc0bb07465ac7d5bbef380899172",
            "start_line": 2277
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
      "task_class": "SportsTrackerActivityDuration"
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
        "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer."
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
        "category",
        "date"
      ],
      "metadata_template": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
        "owner_qualname": "SportsTrackerActivityDuration",
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
        "owner_qualname": "SportsTrackerActivityDuration.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
        "source_sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0"
      },
      {
        "owner_module": "abc",
        "owner_qualname": "SportsTrackerActivityDuration.task_template",
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
        "owner_qualname": "SportsTrackerActivityDuration.generate_random_params",
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
        "activity_description",
        "activity_name",
        "category",
        "date",
        "distance",
        "duration",
        "elevation",
        "seed",
        "start_time"
      ],
      "observed_parameter_types": {
        "activity_description": [
          "builtins.str"
        ],
        "activity_name": [
          "builtins.str"
        ],
        "category": [
          "builtins.str"
        ],
        "date": [
          "builtins.str"
        ],
        "distance": [
          "builtins.str"
        ],
        "duration": [
          "builtins.str"
        ],
        "elevation": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ],
        "start_time": [
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
          "owner_qualname": "SportsTrackerActivityDuration.generate_random_params",
          "sha256": "e62ccb1446078c8a549029895b1be2ffe01a79bdfd2a47d0a1248d7f3561dd08",
          "snippet_sha256": "9053d9f1b4df46971e938c4a3d7656b17d0f230860f6bcd170184434e4c5b342",
          "start_line": 90
        }
      ],
      "value": {}
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SportsTrackerActivityDuration/canonical_task_semantics.json",
      "sha256": "ebdede275b15cbac8ae54b2e50a0d8f1df790a9981662631e05bc253bb5ea17d"
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
              "dispatch_goal_model": "How long was my skiing activity Wednesday in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "7ff3c7eb3d8f9fe7a4badab8c67dbccb6bb098a47e5d583e7f1a5702e2e0e081",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my climbing activity October 07 in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "b7292fd9cc2d1025a0f43390efca5f8a775847fd37cd447ad9a5db37d2cd79c5",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my cycling activity October 05 in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "21315f1184b312374154dccd759239aa5c16983ab880afcbf39f20fb2fe28dd4",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my climbing activity Sunday in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "b621ac3e9fc3a8aa1d9e778a2199c7be3d17458431e2a8a762bd3c0309381146",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my mountain biking activity Sunday in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "689affbb84a6e3d8c5d2486017c552d4661baf73c7182ab358d69b508479d29b",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my mountain biking activity October 14 in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "473f88b6d9c950bc9c6612acc045e22696aed72b13e80db551023c4041bc3a37",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my swimming activity Tuesday in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "7b3093f0314c23c3caed740d372599f51f87d0bdefb980a118cadadd403021b9",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
              "dispatch_goal_model": "How long was my skate boarding activity Thursday in the OpenTracks app? Express your answer in minutes as a single integer.",
              "dispatch_goal_sha256": "f5d3f48e1a32830166f539ab9f960d4a2b0efc020ecfdb8c3c10622871a6740e",
              "parameter_keys": [
                "activity_description",
                "activity_name",
                "category",
                "date",
                "distance",
                "duration",
                "elevation",
                "seed",
                "start_time"
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
                "category",
                "date"
              ],
              "template": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
              "variant_id": "textproto_prompt"
            }
          ]
        },
        "prompt": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
        "proto_binding": {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/proto/tasks.textproto",
          "selector": "tasks[name=\"SportsTrackerActivityDuration\"]",
          "source_sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
          "task_definition": {
            "name": "SportsTrackerActivityDuration",
            "prompt": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
            "relevant_state": {
              "exclusion_conditions": [
                {
                  "field": "start_date",
                  "operation": "EQUAL_TO",
                  "value": "{date}"
                },
                {
                  "field": "category",
                  "operation": "CONTAINS",
                  "value": "{category}"
                }
              ],
              "state": {
                "sports_activity_app": {
                  "sports_activities": [
                    {
                      "category": "{category}",
                      "description": "{activity_description}",
                      "duration": "{duration}",
                      "elevation_gain": "{elevation_without_replacement}",
                      "elevation_loss": "{elevation_without_replacement}",
                      "name": "{activity_name}",
                      "start_date": "{date}",
                      "start_time": "{start_time}",
                      "total_distance": "{distance}"
                    }
                  ]
                }
              }
            },
            "success_criteria": {
              "expectations": [
                {
                  "field_transformation": {
                    "field_name": "duration",
                    "operation": "IDENTITY"
                  },
                  "match_type": "NUMBER_MATCH"
                }
              ]
            },
            "task_params": [
              {
                "name": "date",
                "possible_values": [
                  "October 5 2023",
                  "October 6 2023",
                  "October 7 2023",
                  "October 8 2023",
                  "October 9 2023",
                  "October 10 2023",
                  "October 11 2023",
                  "October 12 2023",
                  "October 13 2023",
                  "October 14 2023",
                  "October 15 2023"
                ]
              },
              {
                "name": "category",
                "possible_values": [
                  "running",
                  "cycling",
                  "swimming",
                  "hiking",
                  "mountain biking",
                  "kayaking",
                  "skiing",
                  "snow boarding",
                  "skate boarding",
                  "climbing",
                  "inline skating",
                  "sailing"
                ]
              },
              {
                "name": "duration",
                "possible_values": [
                  "15",
                  "30",
                  "45",
                  "60",
                  "90",
                  "120",
                  "40",
                  "50",
                  "75",
                  "80",
                  "20",
                  "105",
                  "135",
                  "150",
                  "165",
                  "180",
                  "210",
                  "240",
                  "270"
                ]
              },
              {
                "name": "distance",
                "possible_values": [
                  "100",
                  "300",
                  "500",
                  "800",
                  "1000",
                  "1200",
                  "1500",
                  "2000",
                  "2500",
                  "3000",
                  "3500",
                  "4000",
                  "4500",
                  "5000",
                  "6000",
                  "7000",
                  "8000",
                  "9000",
                  "10000",
                  "12000"
                ]
              },
              {
                "name": "start_time",
                "possible_values": [
                  "8:00am",
                  "10:30am",
                  "5:00pm",
                  "6:30am",
                  "9:45am",
                  "2:15pm",
                  "7:00am",
                  "11:00am",
                  "4:00pm",
                  "1:30pm",
                  "5:45pm",
                  "6:15am",
                  "7:30am",
                  "3:45pm",
                  "10:15am",
                  "2:45pm",
                  "8:45am",
                  "9:15am",
                  "12:00pm",
                  "5:30pm"
                ]
              },
              {
                "name": "elevation",
                "possible_values": [
                  "50",
                  "100",
                  "250",
                  "150",
                  "75",
                  "300",
                  "200",
                  "400",
                  "350",
                  "450",
                  "550",
                  "600",
                  "800",
                  "700",
                  "900",
                  "1000",
                  "650",
                  "1100",
                  "1200",
                  "850"
                ]
              },
              {
                "name": "activity_name",
                "possible_values": [
                  "More tired than usual today",
                  "Need more strength and conditioning",
                  "Slow day",
                  "Laps around the lake",
                  "Trying and failing to keep up with John",
                  "Quick outing",
                  "Recovery day",
                  "Active Rest Day",
                  "Skill work",
                  "Mindful Movement",
                  "Outdoor Adventure",
                  "Light Workout",
                  "Intense day",
                  "Quick Sweat",
                  "Lunch Break Fitness"
                ]
              },
              {
                "name": "activity_description",
                "possible_values": [
                  "Shared laughs and made memories with friends.",
                  "Enjoyed a fun outing with good company.",
                  "Had a blast with my favorite people.",
                  "Created lasting memories that I'll cherish.",
                  "Experienced something unforgettable.",
                  "Captured moments that will bring a smile to my face.",
                  "Wandered off the beaten path.",
                  "Ventured into uncharted territory.",
                  "Stepped outside my comfort zone.",
                  "Pushed my boundaries and tried something different.",
                  "Tested my limits and grew as a person.",
                  "Pushed myself harder than I thought I could.",
                  "Gained new knowledge and skills.",
                  "Expanded my understanding of the world.",
                  "Opened my mind to new perspectives.",
                  "Enjoyed the warmth of the sunshine on my skin.",
                  "Relaxed and recharged under the sun.",
                  "Embraced the rain and got soaked.",
                  "Found joy in the downpour.",
                  "Faced the weather head-on and conquered it.",
                  "Showed resilience in the face of adversity."
                ]
              }
            ]
          },
          "task_definition_sha256": "561f35228d09a83682c0f787ff011cb47b930b02a5369786e2bc65ed8b6853f4",
          "task_name": "SportsTrackerActivityDuration",
          "task_proto_wire_sha256": "f135b99299009a7639c50c649d20f78fea84e51b6ad2d904f3d84559e8b8fc24"
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
            "end_line": 2485,
            "owner_module": "android_world.task_evals.information_retrieval.proto.tasks_textproto",
            "owner_qualname": "SportsTrackerActivityDuration.goal",
            "sha256": "953ccec9987c4bd3a23178f13c77b28f315ce66f3dd57cbdbdaa1497a83403d0",
            "snippet_sha256": "e3e91f527c6fcb296a9d7b5fa19b626441bdfc0bb07465ac7d5bbef380899172",
            "start_line": 2277
          },
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/information_retrieval/information_retrieval_registry.py",
            "ast_sha256": "40d8138d4e78fd8838d99f342cfc1383d3fd0bdb64a6015e95b82797a265704a",
            "end_line": 101,
            "owner_module": "abc",
            "owner_qualname": "SportsTrackerActivityDuration.task_template",
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
        "template": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer."
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "How long was my {category} activity {date} in the OpenTracks app? Express your answer in minutes as a single integer.",
      "optimal_steps": "6",
      "tags": [
        "information_retrieval",
        "parameterized"
      ],
      "task_name": "SportsTrackerActivityDuration"
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
