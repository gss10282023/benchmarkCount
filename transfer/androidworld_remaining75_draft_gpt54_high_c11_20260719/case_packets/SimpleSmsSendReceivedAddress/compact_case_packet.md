# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "SimpleSmsSendReceivedAddress",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 46,
    "task_id": "SimpleSmsSendReceivedAddress"
  },
  "integrity": {
    "semantic_record_sha256": "b9b254bc0b3c0e0fadd438ae4a27e40ec6bf7f3d739a7622fb03124b0c21c930",
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
            "qualname": "SimpleSmsSendReceivedAddress",
            "source_ref": {
              "ast_sha256": "45601c691fb731843bc2f0af6f4196dac48848a0fbc04716c61b53bd71218b3c",
              "end_line": 243,
              "file_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
              "path": "android_world/task_evals/single/sms.py",
              "snippet_sha256": "64c41543de71fccab9e57aca30cd2bccfa75169018ddd644880307bf0ef55817",
              "start_line": 173,
              "symbol": "SimpleSmsSendReceivedAddress"
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
            "ast_sha256": "45601c691fb731843bc2f0af6f4196dac48848a0fbc04716c61b53bd71218b3c",
            "end_line": 243,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsSendReceivedAddress",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "64c41543de71fccab9e57aca30cd2bccfa75169018ddd644880307bf0ef55817",
            "start_line": 173
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
      "task_class": "SimpleSmsSendReceivedAddress"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "adb_utils.disable_headsup_notifications",
            "adb_utils.enable_headsup_notifications",
            "adb_utils.text_emulator",
            "contacts_utils.add_contact",
            "super",
            "super.initialize_task",
            "time.sleep",
            "user_data_generation.generate_random_number"
          ],
          "direct_parameter_reads": [
            "message",
            "name1",
            "name2",
            "number"
          ],
          "owner_class": "SimpleSmsSendReceivedAddress",
          "owner_module": "android_world.task_evals.single.sms",
          "source_ref": {
            "ast_sha256": "7b3d882687d197714ef53ba539923577b80fd46c2abdb9fd76cb117302977bf8",
            "end_line": 239,
            "file_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "path": "android_world/task_evals/single/sms.py",
            "snippet_sha256": "9c4a5bce1ea75e56ff6450d5572e52491be4ad08b325fafa6bfc64236e97d29a",
            "start_line": 216,
            "symbol": "SimpleSmsSendReceivedAddress.initialize_task"
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
          "ast_sha256": "7b3d882687d197714ef53ba539923577b80fd46c2abdb9fd76cb117302977bf8",
          "end_line": 239,
          "owner_module": "android_world.task_evals.single.sms",
          "owner_qualname": "SimpleSmsSendReceivedAddress.initialize_task",
          "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
          "snippet_sha256": "9c4a5bce1ea75e56ff6450d5572e52491be4ad08b325fafa6bfc64236e97d29a",
          "start_line": 216
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
        "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger"
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
        "name1",
        "name2"
      ],
      "metadata_template": "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSendReceivedAddress",
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
        "owner_qualname": "SimpleSmsSendReceivedAddress.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
      },
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSendReceivedAddress.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
      },
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSendReceivedAddress.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
        "source_sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9"
      },
      {
        "owner_module": "android_world.task_evals.single.sms",
        "owner_qualname": "SimpleSmsSendReceivedAddress.initialize_task",
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
        "name1",
        "name2",
        "number",
        "seed"
      ],
      "observed_parameter_types": {
        "message": [
          "builtins.str"
        ],
        "name1": [
          "builtins.str"
        ],
        "name2": [
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
          "ast_sha256": "45601c691fb731843bc2f0af6f4196dac48848a0fbc04716c61b53bd71218b3c",
          "end_line": 243,
          "owner_module": "android_world.task_evals.single.sms",
          "owner_qualname": "SimpleSmsSendReceivedAddress.schema",
          "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
          "snippet_sha256": "64c41543de71fccab9e57aca30cd2bccfa75169018ddd644880307bf0ef55817",
          "start_line": 173
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/sms.py",
          "ast_sha256": "5bd244e09a74e6cfc55534fff282cc4a94bb9fb96cd0207eebf73faf8d1553a8",
          "end_line": 214,
          "owner_module": "android_world.task_evals.single.sms",
          "owner_qualname": "SimpleSmsSendReceivedAddress.generate_random_params",
          "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
          "snippet_sha256": "15d527991178c4cce613db437db193246fc03531c2ea55e82a597837ead14659",
          "start_line": 204
        }
      ],
      "value": {
        "properties": {
          "message": {
            "type": "string"
          },
          "name1": {
            "type": "string"
          },
          "name2": {
            "type": "string"
          },
          "number": {
            "type": "string"
          }
        },
        "required": [
          "name1",
          "number",
          "name2",
          "message"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/SimpleSmsSendReceivedAddress/canonical_task_semantics.json",
      "sha256": "b9b254bc0b3c0e0fadd438ae4a27e40ec6bf7f3d739a7622fb03124b0c21c930"
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
              "dispatch_goal_model": "Text the address of the event to Louis Lopez that Hana Ali just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "230a390ee04db46ae499beae65a82b40b40a0f077246840370e62c88ecb98e32",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Nikola Fernandez that Grace Alves just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "f5d6c0da10f5c5cc1975fe393874bd0aceab7037b9d5edf8bd900149722e2446",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Aria Ali that Laura Alves just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "ec2292ea81aa214e9baadf3ca2cea1b326764e541b535ce35b30fdfb9a1d360d",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Nora Gonzalez that Charlie Pereira just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "03f44cba2328de3f7f27db8f8c229c8359297d09ce2617f109becdf37349befb",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Ibrahim Gonzalez that Thomas Chen just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "194ec6ffaa716c4afa8635bc6fbdab87b2bfc58110eaaa38cb7c8bcd495ab6e2",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Grace Zhang that Sophie Liu just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "9888676572614107c0b744b442081503d255b24c1800edd7664cdcb46b76aa80",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to David Li that Sara Lopez just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "f80b6e71497459d00f9e30dfdfed781f6c147bcfc6daf0e3a3295607530a4e1b",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
              "dispatch_goal_model": "Text the address of the event to Muhammad Mohamed that Luka Mohamed just sent me in Simple SMS Messenger",
              "dispatch_goal_sha256": "87412ce7874996fce8e73cee49a12954da9c115bc850bec1cf94b8087b11327f",
              "parameter_keys": [
                "message",
                "name1",
                "name2",
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
                "name1",
                "name2"
              ],
              "template": "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger",
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
            "ast_sha256": "45601c691fb731843bc2f0af6f4196dac48848a0fbc04716c61b53bd71218b3c",
            "end_line": 243,
            "owner_module": "android_world.task_evals.single.sms",
            "owner_qualname": "SimpleSmsSendReceivedAddress.template",
            "sha256": "1510f9677cf3d959062ffdc43bb74d735b56b726dba35d739525417ad17cc2d9",
            "snippet_sha256": "64c41543de71fccab9e57aca30cd2bccfa75169018ddd644880307bf0ef55817",
            "start_line": 173
          }
        ],
        "template": "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger"
      },
      "difficulty": "medium",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Text the address of the event to {name1} that {name2} just sent me in Simple SMS Messenger",
      "optimal_steps": "9",
      "tags": [
        "information_retrieval",
        "parameterized"
      ],
      "task_name": "SimpleSmsSendReceivedAddress"
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
