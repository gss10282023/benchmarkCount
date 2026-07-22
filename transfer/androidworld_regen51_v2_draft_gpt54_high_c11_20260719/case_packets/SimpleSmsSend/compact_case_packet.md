# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleSmsSend",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 97,
    "task_id": "SimpleSmsSend"
  },
  "integrity": {
    "semantic_record_sha256": "0cdd431144650fd7852da0930e1cfa95316ea8cc131284e544fda9a60311ee6c",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "3293c1085fd451c5e8c3525621c854355458ddff12b88b8fe89af593b1ca9177",
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
      "canonical_module": "android_world.task_evals.single.sms",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.sms",
            "qualname": "SimpleSmsSend",
            "source_ref": {
              "ast_sha256": "7f8bd8a5cba6d985e9ae5bda5040f956c3345936bce262be61d8bb8da773fea5",
              "end_line": 34,
              "file_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
              "path": "android_world/task_evals/single/sms.py",
              "snippet_sha256": "323538225809bc4f45c70c6779d70da3378c438d05512a66dd9765ed412fb409",
              "start_line": 28,
              "symbol": "SimpleSmsSend"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.common_validators.sms_validators",
            "qualname": "SimpleSMSSendSms",
            "source_ref": {
              "ast_sha256": "6dbcb0ee6e466f2a4bc67047e8821f9aaf95bbd7b0f34e98cd03c42e79ebd689",
              "end_line": 286,
              "file_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
              "path": "android_world/task_evals/common_validators/sms_validators.py",
              "snippet_sha256": "8d2deadbe991ff6ada671d00510ffce97a03263cd5f23adeea36e834f003694e",
              "start_line": 183,
              "symbol": "SimpleSMSSendSms"
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
        "runtime_reported_module": "android_world.task_evals.single.sms",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
            "ast_sha256": "7f8bd8a5cba6d985e9ae5bda5040f956c3345936bce262be61d8bb8da773fea5",
            "end_line": 34,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsSend",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "323538225809bc4f45c70c6779d70da3378c438d05512a66dd9765ed412fb409",
            "start_line": 28
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 2,
            "direct_calls": [
              "ValueError",
              "_check_if_stuck_at_sending",
              "adb_utils.extract_package_name",
              "adb_utils.get_current_activity",
              "logging.info",
              "self.get_android_time",
              "self.get_sent_messages",
              "super",
              "super.is_successful",
              "time.sleep",
              "was_sent"
            ],
            "direct_parameter_reads": [
              "message",
              "number"
            ],
            "owner_class": "SimpleSMSSendSms",
            "owner_module": "android_world.task_evals.common_validators.sms_validators",
            "source_ref": {
              "ast_sha256": "b6c0d95f57fdf710632dc7e2ad44ef7ce58a445d48f9acb69b47f9b750d7ad03",
              "end_line": 276,
              "file_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
              "path": "android_world/task_evals/common_validators/sms_validators.py",
              "snippet_sha256": "0102f7e61b337fc4ac383382ed1bc2e711839ae630e8c33fd1f94dbe0d54838d",
              "start_line": 255,
              "symbol": "SimpleSMSSendSms.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
            "ast_sha256": "b6c0d95f57fdf710632dc7e2ad44ef7ce58a445d48f9acb69b47f9b750d7ad03",
            "end_line": 276,
            "owner_module": "android_world.task_evals.common_validators.sms_validators",
            "owner_qualname": "SimpleSMSSendSms.is_successful",
            "sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
            "snippet_sha256": "0102f7e61b337fc4ac383382ed1bc2e711839ae630e8c33fd1f94dbe0d54838d",
            "start_line": 255
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
              "ValueError",
              "_check_if_stuck_at_sending",
              "adb_utils.extract_package_name",
              "adb_utils.get_current_activity",
              "logging.info",
              "self.get_android_time",
              "self.get_sent_messages",
              "super",
              "super.is_successful",
              "time.sleep",
              "was_sent"
            ],
            "direct_parameter_reads": [
              "message",
              "number"
            ],
            "owner_class": "SimpleSMSSendSms",
            "owner_module": "android_world.task_evals.common_validators.sms_validators",
            "source_ref": {
              "ast_sha256": "b6c0d95f57fdf710632dc7e2ad44ef7ce58a445d48f9acb69b47f9b750d7ad03",
              "end_line": 276,
              "file_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
              "path": "android_world/task_evals/common_validators/sms_validators.py",
              "snippet_sha256": "0102f7e61b337fc4ac383382ed1bc2e711839ae630e8c33fd1f94dbe0d54838d",
              "start_line": 255,
              "symbol": "SimpleSMSSendSms.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
            "ast_sha256": "b6c0d95f57fdf710632dc7e2ad44ef7ce58a445d48f9acb69b47f9b750d7ad03",
            "end_line": 276,
            "owner_module": "android_world.task_evals.common_validators.sms_validators",
            "owner_qualname": "SimpleSMSSendSms.is_successful",
            "sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
            "snippet_sha256": "0102f7e61b337fc4ac383382ed1bc2e711839ae630e8c33fd1f94dbe0d54838d",
            "start_line": 255
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
      "task_class": "SimpleSmsSend"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 1,
          "direct_calls": [
            "ValueError",
            "adb_utils.toggle_airplane_mode",
            "clear_sms_and_threads",
            "logging.info",
            "self.get_android_time",
            "self.get_sent_messages",
            "super",
            "super.initialize_task",
            "time.sleep",
            "was_sent"
          ],
          "direct_parameter_reads": [
            "message",
            "number"
          ],
          "owner_class": "SimpleSMSSendSms",
          "owner_module": "android_world.task_evals.common_validators.sms_validators",
          "source_ref": {
            "ast_sha256": "1cb25d3592eef9f45dca9e20a0dfde01d084b15441b105a019c6474520975dfd",
            "end_line": 253,
            "file_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
            "path": "android_world/task_evals/common_validators/sms_validators.py",
            "snippet_sha256": "60e38bf902514c44ad6aced72f5556bba370c06cfd3d08f3cf7d2f27dbcfc39b",
            "start_line": 234,
            "symbol": "SimpleSMSSendSms.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
          "ast_sha256": "1cb25d3592eef9f45dca9e20a0dfde01d084b15441b105a019c6474520975dfd",
          "end_line": 253,
          "owner_module": "android_world.task_evals.common_validators.sms_validators",
          "owner_qualname": "SimpleSMSSendSms.initialize_task",
          "sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
          "snippet_sha256": "60e38bf902514c44ad6aced72f5556bba370c06cfd3d08f3cf7d2f27dbcfc39b",
          "start_line": 234
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
        "Send a text message using Simple SMS Messenger to {number} with message: {message}"
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
        "message",
        "number"
      ],
      "metadata_template": "Send a text message using Simple SMS Messenger to {number} with message: {message}",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSend",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSend.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sms_validators",
        "owner_qualname": "SimpleSMSSendSms.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
        "source_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sms_validators",
        "owner_qualname": "SimpleSMSSendSms.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
        "source_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sms_validators",
        "owner_qualname": "SimpleSMSSendSms.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
        "source_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.common_validators.sms_validators",
        "owner_qualname": "SimpleSMSSendSms.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
        "source_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82"
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
        "owner_module": "android_world.task_evals.common_validators.sms_validators",
        "owner_qualname": "SimpleSMSSendSms.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
        "source_sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82"
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
        "message",
        "number",
        "seed"
      ],
      "observed_parameter_types": {
        "message": [
          "builtins.str"
        ],
        "number": [
          "builtins.str"
        ],
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
          "ast_sha256": "6dbcb0ee6e466f2a4bc67047e8821f9aaf95bbd7b0f34e98cd03c42e79ebd689",
          "end_line": 286,
          "owner_module": "android_world.task_evals.common_validators.sms_validators",
          "owner_qualname": "SimpleSMSSendSms.schema",
          "sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
          "snippet_sha256": "8d2deadbe991ff6ada671d00510ffce97a03263cd5f23adeea36e834f003694e",
          "start_line": 183
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/common_validators/sms_validators.py",
          "ast_sha256": "ef551a17364eba1bd3a8198bb9c3ea7e1d4406963bb7606e5823e5b189dcf195",
          "end_line": 286,
          "owner_module": "android_world.task_evals.common_validators.sms_validators",
          "owner_qualname": "SimpleSMSSendSms.generate_random_params",
          "sha256": "ca149d45611e6990b84291c0622ab08f22456d17c90e5b77b5ef7ef35d16ec82",
          "snippet_sha256": "b74f86d46e7a8452c9438b20854400de3d42a45ca0405604aa4bf40112ae29f7",
          "start_line": 278
        }
      ],
      "value": {
        "properties": {
          "message": {
            "type": "string"
          },
          "number": {
            "type": "string"
          }
        },
        "required": [
          "number",
          "message"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleSmsSend/canonical_task_semantics.json",
      "sha256": "0cdd431144650fd7852da0930e1cfa95316ea8cc131284e544fda9a60311ee6c"
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
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +16604876475 with message: The squeaky wheel gets the grease.",
              "dispatch_goal_sha256": "deb08d3282655fb4edffd2cb272de65d9abc0b1686237716326ff29508543836",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +12914177763 with message: Pick up groceries: Milk and Bread and Apples.",
              "dispatch_goal_sha256": "ee2cf39c3494862346f61860c669b5e9c3122389ac6ef9e211256af984893df2",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +10115244939 with message: Lunch meeting with Sarah at 1 PM Cafe L'amour.",
              "dispatch_goal_sha256": "7b71a5d9e3cf23c4b69279f5742acb0150f2620742705161d2bf53f91cf52676",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +13982597919 with message: Don't forget to water the plants while I'm away.",
              "dispatch_goal_sha256": "6e5778b3b3381c028ca30bc5199891b0d9044fdfb5b0b4122c1b412da1ba2dd2",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +13416721106 with message: The pen is mightier than the sword.",
              "dispatch_goal_sha256": "52da9e2d8015527b8120eaa5d7ad2ac6c7431c821c440e7c4115a1e8d5837e8c",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +19458073021 with message: Winter is coming.",
              "dispatch_goal_sha256": "a7876fb27a19713c5dc25dd6aebde8fe1fbdc507e49d8e51dc65e5758c4b91f5",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +15260181590 with message: Better late than never.",
              "dispatch_goal_sha256": "eaa1fb0025a08b6a90834d460a2e338c11feef08e3c49ca6daf8ffb7c3fbd411",
              "parameter_keys": [
                "message",
                "number",
                "seed"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Send a text message using Simple SMS Messenger to +17877893287 with message: You can't make an omelette without breaking a few eggs.",
              "dispatch_goal_sha256": "e0eb88c8f5c2868f78c93c1b783804bb03799359724e44c542405404ebdfdc1b",
              "parameter_keys": [
                "message",
                "number",
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
              "placeholders": [
                "message",
                "number"
              ],
              "template": "Send a text message using Simple SMS Messenger to {number} with message: {message}",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
            "ast_sha256": "7f8bd8a5cba6d985e9ae5bda5040f956c3345936bce262be61d8bb8da773fea5",
            "end_line": 34,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsSend.template",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "323538225809bc4f45c70c6779d70da3378c438d05512a66dd9765ed412fb409",
            "start_line": 28
          }
        ],
        "template": "Send a text message using Simple SMS Messenger to {number} with message: {message}"
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Send a text message using Simple SMS Messenger to {number} with message: {message}",
      "optimal_steps": "6",
      "tags": [
        "parameterized"
      ],
      "task_name": "SimpleSmsSend"
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
