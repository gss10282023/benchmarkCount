# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleSmsReply",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 15,
    "task_id": "SimpleSmsReply"
  },
  "integrity": {
    "semantic_record_sha256": "e4d58a42fec64e734a096929b59c36abd78349aa6482ae03094690c727b8bb2c",
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
            "qualname": "SimpleSmsReply",
            "source_ref": {
              "ast_sha256": "4c178cdcf5aa6c7e906ec60c7cccc08e311babfdd23772a248c9270bc95736c9",
              "end_line": 155,
              "file_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
              "path": "android_world/task_evals/single/sms.py",
              "snippet_sha256": "efa52677e742ffacfdf2429291900d4d80f131619e67dae485a2bc0b7c0e822a",
              "start_line": 115,
              "symbol": "SimpleSmsReply"
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
            "ast_sha256": "4c178cdcf5aa6c7e906ec60c7cccc08e311babfdd23772a248c9270bc95736c9",
            "end_line": 155,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsReply",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "efa52677e742ffacfdf2429291900d4d80f131619e67dae485a2bc0b7c0e822a",
            "start_line": 115
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
      "task_class": "SimpleSmsReply"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 3,
          "direct_calls": [
            "adb_utils.disable_headsup_notifications",
            "adb_utils.enable_headsup_notifications",
            "adb_utils.text_emulator",
            "random.choice",
            "random.randint",
            "range",
            "super",
            "super.initialize_task",
            "time.sleep",
            "user_data_generation.generate_random_number"
          ],
          "direct_parameter_reads": [
            "number"
          ],
          "owner_class": "SimpleSmsReply",
          "owner_module": "android_world.task_evals.single.sms",
          "source_ref": {
            "ast_sha256": "ad0a453aeb36d951b35fae6fde99c389688a091109776f0f572a747aeefb4df1",
            "end_line": 155,
            "file_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "path": "android_world/task_evals/single/sms.py",
            "snippet_sha256": "e19d7360fb30134cc7c6416938f34c1026ecb5e0ff646c7db2baca45e8b78b65",
            "start_line": 121,
            "symbol": "SimpleSmsReply.initialize_task"
          }
        },
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
          "ast_sha256": "ad0a453aeb36d951b35fae6fde99c389688a091109776f0f572a747aeefb4df1",
          "end_line": 155,
          "owner_module": "android_world.task_evals.single.sms",
          "owner_qualname": "SimpleSmsReply.initialize_task",
          "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
          "snippet_sha256": "e19d7360fb30134cc7c6416938f34c1026ecb5e0ff646c7db2baca45e8b78b65",
          "start_line": 121
        },
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
        "Reply to {number} with message: {message} in Simple SMS Messenger"
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
      "metadata_template": "Reply to {number} with message: {message} in Simple SMS Messenger",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsReply",
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
        "owner_qualname": "SimpleSmsReply.template",
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
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsReply.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
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
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleSmsReply/canonical_task_semantics.json",
      "sha256": "e4d58a42fec64e734a096929b59c36abd78349aa6482ae03094690c727b8bb2c"
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
              "dispatch_goal_model": "Reply to +16604876475 with message: The squeaky wheel gets the grease. in Simple SMS Messenger",
              "dispatch_goal_sha256": "3d40a7fa795657c39bc8fbd3c1b821c736a73e99beb3776c80424f8c212c766d",
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
              "dispatch_goal_model": "Reply to +12914177763 with message: Pick up groceries: Milk and Bread and Apples. in Simple SMS Messenger",
              "dispatch_goal_sha256": "1a2c50e3f318221b0b176d0effc218ddb5f8032f9b8fff0e019201c16306df9d",
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
              "dispatch_goal_model": "Reply to +10115244939 with message: Lunch meeting with Sarah at 1 PM Cafe L'amour. in Simple SMS Messenger",
              "dispatch_goal_sha256": "1dbd3f61f89d9de49af8a007cf70216136f20b3874da52cf241736068d55410e",
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
              "dispatch_goal_model": "Reply to +13982597919 with message: Don't forget to water the plants while I'm away. in Simple SMS Messenger",
              "dispatch_goal_sha256": "6598f25882373254d01312119d307c0f5f95bccdfa73afcdbafca08ca12ce86b",
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
              "dispatch_goal_model": "Reply to +13416721106 with message: The pen is mightier than the sword. in Simple SMS Messenger",
              "dispatch_goal_sha256": "70e28b4ed0bc3ab0fda500cdf96e4c75f51db9c8f437fd5811ddd5d7655dc9d6",
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
              "dispatch_goal_model": "Reply to +19458073021 with message: Winter is coming. in Simple SMS Messenger",
              "dispatch_goal_sha256": "f2935565367014b6ede691f5b3e4d7638768a3cd1e848dc23c1ccbee644132c5",
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
              "dispatch_goal_model": "Reply to +15260181590 with message: Better late than never. in Simple SMS Messenger",
              "dispatch_goal_sha256": "47a66f7945394ef41d1d06a572d07d63f23c857238e09ed5afdd57ee0e6df2ba",
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
              "dispatch_goal_model": "Reply to +17877893287 with message: You can't make an omelette without breaking a few eggs. in Simple SMS Messenger",
              "dispatch_goal_sha256": "9fb4345f0b33af65b39dbb18b74921b0f1ddf38b92a7254c1d3279f162374d95",
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
              "template": "Reply to {number} with message: {message} in Simple SMS Messenger",
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
            "ast_sha256": "4c178cdcf5aa6c7e906ec60c7cccc08e311babfdd23772a248c9270bc95736c9",
            "end_line": 155,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsReply.template",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "efa52677e742ffacfdf2429291900d4d80f131619e67dae485a2bc0b7c0e822a",
            "start_line": 115
          }
        ],
        "template": "Reply to {number} with message: {message} in Simple SMS Messenger"
      },
      "difficulty": "easy",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Reply to {number} with message: {message} in Simple SMS Messenger",
      "optimal_steps": "4",
      "tags": [
        "search",
        "data_entry",
        "parameterized"
      ],
      "task_name": "SimpleSmsReply"
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
