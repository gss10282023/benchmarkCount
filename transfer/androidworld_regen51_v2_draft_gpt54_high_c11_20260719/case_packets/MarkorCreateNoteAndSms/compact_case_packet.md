# AndroidWorld Compact Draft Packet

This is the complete LLM-visible pre-run source packet for one contract draft. The full audit packet and frozen source closure remain available separately.

```json
{
  "authority_rule": "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; every disagreement is retained in metadata_comparison and metadata_conflicts.",
  "identity": {
    "case_unit_id": "MarkorCreateNoteAndSms",
    "domain": "androidworld",
    "group": "official100",
    "selection_rank": 14,
    "task_id": "MarkorCreateNoteAndSms"
  },
  "integrity": {
    "semantic_record_sha256": "2f1310af83b80569bddbd131c6f8681cc2ba9c663c1fe755003d6d1be6cc81db",
    "shared_source_snapshot_manifest_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/androidworld_source_snapshot_manifest.json",
    "shared_source_snapshot_manifest_sha256": "cdc4c9543ac50fb88837feb787179d5e73b6651f167b0d50f64b2332473b62bf",
    "source_closure_sha256": "f6869dc06a0a78862f611678f5205a4dd238b082b25a22c6cdb3bf9521563425",
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
      "canonical_module": "android_world.task_evals.composite.markor_sms",
      "definition": {
        "definition_kind": "python_class",
        "incidental_runtime_module_excluded": null,
        "mro": [
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.composite.markor_sms",
            "qualname": "MarkorCreateNoteAndSms",
            "source_ref": {
              "ast_sha256": "da2fda3f81d6da2ccec3e29e36d208af41037cdb7086b3ce48780e4acab6cd46",
              "end_line": 86,
              "file_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
              "path": "android_world/task_evals/composite/markor_sms.py",
              "snippet_sha256": "fb8c4948b32aaef663247fe242943defec7e38185d68d4d590fa97a0a74efe76",
              "start_line": 24,
              "symbol": "MarkorCreateNoteAndSms"
            }
          },
          {
            "canonical_androidworld_source": true,
            "module": "android_world.task_evals.single.markor",
            "qualname": "Markor",
            "source_ref": {
              "ast_sha256": "ab836071c307a07af660b9cf4c8137b17fd2bb2ebb401ed3ff494a88f838de8e",
              "end_line": 66,
              "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
              "path": "android_world/task_evals/single/markor.py",
              "snippet_sha256": "e4bb63aa31ab515f465187b23e197af8bc908d74878f677b51372f1b92c27a24",
              "start_line": 57,
              "symbol": "Markor"
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
        "runtime_reported_module": "android_world.task_evals.composite.markor_sms",
        "source_bindings": [
          {
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
            "ast_sha256": "da2fda3f81d6da2ccec3e29e36d208af41037cdb7086b3ce48780e4acab6cd46",
            "end_line": 86,
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "owner_qualname": "MarkorCreateNoteAndSms",
            "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
            "snippet_sha256": "fb8c4948b32aaef663247fe242943defec7e38185d68d4d590fa97a0a74efe76",
            "start_line": 24
          }
        ]
      },
      "evaluator": {
        "branches": [],
        "method_chain": [
          {
            "branch_node_count": 0,
            "direct_calls": [
              "logging.info",
              "self.markor_task.is_successful",
              "self.sms_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "MarkorCreateNoteAndSms",
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "source_ref": {
              "ast_sha256": "15d49eb50453d6578de26b602767ffa13575b8f043e610e9f2757bf2b12982d5",
              "end_line": 68,
              "file_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
              "path": "android_world/task_evals/composite/markor_sms.py",
              "snippet_sha256": "45520f2cc23969b5cb558eab5adabb261d7e2456e501b3792e8520ab6162f046",
              "start_line": 60,
              "symbol": "MarkorCreateNoteAndSms.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
            "ast_sha256": "15d49eb50453d6578de26b602767ffa13575b8f043e610e9f2757bf2b12982d5",
            "end_line": 68,
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "owner_qualname": "MarkorCreateNoteAndSms.is_successful",
            "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
            "snippet_sha256": "45520f2cc23969b5cb558eab5adabb261d7e2456e501b3792e8520ab6162f046",
            "start_line": 60
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
            "branch_node_count": 0,
            "direct_calls": [
              "logging.info",
              "self.markor_task.is_successful",
              "self.sms_task.is_successful",
              "super",
              "super.is_successful"
            ],
            "direct_parameter_reads": [],
            "owner_class": "MarkorCreateNoteAndSms",
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "source_ref": {
              "ast_sha256": "15d49eb50453d6578de26b602767ffa13575b8f043e610e9f2757bf2b12982d5",
              "end_line": 68,
              "file_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
              "path": "android_world/task_evals/composite/markor_sms.py",
              "snippet_sha256": "45520f2cc23969b5cb558eab5adabb261d7e2456e501b3792e8520ab6162f046",
              "start_line": 60,
              "symbol": "MarkorCreateNoteAndSms.is_successful"
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
            "ast_sha256": "15d49eb50453d6578de26b602767ffa13575b8f043e610e9f2757bf2b12982d5",
            "end_line": 68,
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "owner_qualname": "MarkorCreateNoteAndSms.is_successful",
            "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
            "snippet_sha256": "45520f2cc23969b5cb558eab5adabb261d7e2456e501b3792e8520ab6162f046",
            "start_line": 60
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
      "task_class": "MarkorCreateNoteAndSms"
    },
    "initialization": {
      "device_execution_performed_during_extraction": false,
      "method_chain": [
        {
          "branch_node_count": 0,
          "direct_calls": [
            "markor.MarkorCreateNote",
            "self.markor_task.initialize_task",
            "self.sms_task.initialize_task",
            "sms_validators.SimpleSMSSendSms",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [
            "file_name",
            "number",
            "text"
          ],
          "owner_class": "MarkorCreateNoteAndSms",
          "owner_module": "android_world.task_evals.composite.markor_sms",
          "source_ref": {
            "ast_sha256": "942ddfca31e8f653f67f2d62f4313af68846125dd6179ff70e9cfe64cb20b9a0",
            "end_line": 58,
            "file_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
            "path": "android_world/task_evals/composite/markor_sms.py",
            "snippet_sha256": "232c0a99800ba744cbfb92e0eb895f45f171a40dc9e627bf9f2314e7a5767045",
            "start_line": 45,
            "symbol": "MarkorCreateNoteAndSms.initialize_task"
          }
        },
        {
          "branch_node_count": 0,
          "direct_calls": [
            "file_utils.clear_directory",
            "super",
            "super.initialize_task"
          ],
          "direct_parameter_reads": [],
          "owner_class": "Markor",
          "owner_module": "android_world.task_evals.single.markor",
          "source_ref": {
            "ast_sha256": "645a8166b07e880454139eafae321d41ea4188dbcc7245b602a56e86f1a3edbb",
            "end_line": 62,
            "file_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
            "path": "android_world/task_evals/single/markor.py",
            "snippet_sha256": "c8d6d0037a19a9d990983f29dcb9d874dfc04ffe5389b1c4114bcacc60f71344",
            "start_line": 60,
            "symbol": "Markor.initialize_task"
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
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
          "ast_sha256": "942ddfca31e8f653f67f2d62f4313af68846125dd6179ff70e9cfe64cb20b9a0",
          "end_line": 58,
          "owner_module": "android_world.task_evals.composite.markor_sms",
          "owner_qualname": "MarkorCreateNoteAndSms.initialize_task",
          "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
          "snippet_sha256": "232c0a99800ba744cbfb92e0eb895f45f171a40dc9e627bf9f2314e7a5767045",
          "start_line": 45
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
          "ast_sha256": "645a8166b07e880454139eafae321d41ea4188dbcc7245b602a56e86f1a3edbb",
          "end_line": 62,
          "owner_module": "android_world.task_evals.single.markor",
          "owner_qualname": "Markor.initialize_task",
          "sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd",
          "snippet_sha256": "c8d6d0037a19a9d990983f29dcb9d874dfc04ffe5389b1c4114bcacc60f71344",
          "start_line": 60
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
        "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger"
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
        "file_name",
        "number",
        "text"
      ],
      "metadata_template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger",
      "status": "exact"
    },
    "metadata_conflicts": [],
    "native_sources": [
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.goal",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.template",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
      },
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.schema",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
      },
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.generate_random_params",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
      },
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
      },
      {
        "owner_module": "android_world.task_evals.single.markor",
        "owner_qualname": "Markor.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/single/markor.py",
        "source_sha256": "148bf60ac0469641f47936bff44345315253e97a3231e2b94f0f5373c0a187dd"
      },
      {
        "owner_module": "android_world.task_evals.task_eval",
        "owner_qualname": "TaskEval.initialize_task",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/task_eval.py",
        "source_sha256": "e359e11f9f8874af9dc17311f58c11eb1169672826f43e582d91b95f205008eb"
      },
      {
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
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
        "owner_module": "android_world.task_evals.composite.markor_sms",
        "owner_qualname": "MarkorCreateNoteAndSms.is_successful",
        "source_ref": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
        "source_sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc"
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
        "file_name",
        "number",
        "seed",
        "text"
      ],
      "observed_parameter_types": {
        "file_name": [
          "builtins.str"
        ],
        "number": [
          "builtins.str"
        ],
        "seed": [
          "builtins.int"
        ],
        "text": [
          "builtins.str"
        ]
      },
      "runner_injected_parameters": [
        "seed"
      ],
      "schema_completeness": "declared_not_assumed_complete",
      "source_bindings": [
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
          "ast_sha256": "da2fda3f81d6da2ccec3e29e36d208af41037cdb7086b3ce48780e4acab6cd46",
          "end_line": 86,
          "owner_module": "android_world.task_evals.composite.markor_sms",
          "owner_qualname": "MarkorCreateNoteAndSms.schema",
          "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
          "snippet_sha256": "fb8c4948b32aaef663247fe242943defec7e38185d68d4d590fa97a0a74efe76",
          "start_line": 24
        },
        {
          "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
          "ast_sha256": "5a2940de754d092f188c1aa75ff256eeab062f4c53bae856afca316aa4c84ffd",
          "end_line": 86,
          "owner_module": "android_world.task_evals.composite.markor_sms",
          "owner_qualname": "MarkorCreateNoteAndSms.generate_random_params",
          "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
          "snippet_sha256": "ad83ae08baeded2694565cd8a121f7c60bd61fd523140254af8c38b6d9a371fd",
          "start_line": 75
        }
      ],
      "value": {
        "properties": {
          "file_name": {
            "type": "string"
          },
          "number": {
            "type": "string"
          },
          "text": {
            "type": "string"
          }
        },
        "required": [
          "file_name",
          "text",
          "number"
        ],
        "type": "object"
      }
    },
    "semantic_record": {
      "path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases/MarkorCreateNoteAndSms/canonical_task_semantics.json",
      "sha256": "2f1310af83b80569bddbd131c6f8681cc2ba9c663c1fe755003d6d1be6cc81db"
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
              "dispatch_goal_model": "Create a new note in Markor named qFzW_polite_wolf.txt with the following text: Actions speak louder than words.. Share the entire content of the note with the phone number +15938242194 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "66841fab3d10b065b0830729dee912a1f63e1f11251ba03ea41fec18f534848b",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 0
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named friendly_koala_2023_03_02.txt with the following text: The early bird catches the worm.. Share the entire content of the note with the phone number +17631706690 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "262e24c94f8e3794215e27ed509e920a1f42d22af0c2cbec4aa3a4898685284a",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 1
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named brave_fish_2023_03_28.txt with the following text: To be or not to be.. Share the entire content of the note with the phone number +19390926685 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "b353382cc7bf3e2ea1dfc91bebe7f80afbfa40c434151fd418f4da75b5e1f461",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 2
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named final_wise_lamp.txt with the following text: The squeaky wheel gets the grease.. Share the entire content of the note with the phone number +11907483378 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "76919e26e464b6015e44037c5e764e43e38aa4df7fb0bd996a5ce25bad879710",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 3
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named wise_tree_2023_09_03.md with the following text: Monthly budget meeting pushed to Friday.. Share the entire content of the note with the phone number +11068403885 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "11133c04d2f23c0d270d7179dbb5f862c7bad7c105ab0791a89efc221feb8808",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 4
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named good_queen_backup.txt with the following text: Hello, World!. Share the entire content of the note with the phone number +10215736819 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "4a9e7dc5d152bc3fa8742c1ddd8c16474cdf8647b1d80a0ad91f6e4d10e9d5dd",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 5
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named eHwd_helpful_jacket.md with the following text: Lunch meeting with Sarah at 1 PM Cafe L'amour.. Share the entire content of the note with the phone number +11661318609 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "bab1c8bc8b7a75a04412b08529780efe6a9d150f0bc6b61cd954c77f560de772",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
              ],
              "pure_pre_dispatch_transforms": [],
              "sample_kind": "fixed_seed",
              "suite_seed": 7
            },
            {
              "branch_selector": null,
              "device_initialization_executed": false,
              "dispatch_goal_model": "Create a new note in Markor named tough_jelly_FKlF.md with the following text: Pick up groceries: Milk and Bread and Apples.. Share the entire content of the note with the phone number +17421809679 via SMS using Simple SMS Messenger",
              "dispatch_goal_sha256": "acbc3a9db7c9e17c4596c00a028a05d3a0c14a70d99cb76cbf4965352c3eaef3",
              "parameter_keys": [
                "file_name",
                "number",
                "seed",
                "text"
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
                "file_name",
                "number",
                "text"
              ],
              "template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger",
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
            "artifact_path": "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree/android_world/task_evals/composite/markor_sms.py",
            "ast_sha256": "da2fda3f81d6da2ccec3e29e36d208af41037cdb7086b3ce48780e4acab6cd46",
            "end_line": 86,
            "owner_module": "android_world.task_evals.composite.markor_sms",
            "owner_qualname": "MarkorCreateNoteAndSms.template",
            "sha256": "dfd5d280988f8d7ae581b2faabf2f3ec2407a55273a8389e68ce98eb8f7b30dc",
            "snippet_sha256": "fb8c4948b32aaef663247fe242943defec7e38185d68d4d590fa97a0a74efe76",
            "start_line": 24
          }
        ],
        "template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger"
      },
      "difficulty": "hard",
      "metadata_semantic_role": "descriptive_non_authoritative_when_conflicting",
      "metadata_task_template": "Create a new note in Markor named {file_name} with the following text: {text}. Share the entire content of the note with the phone number {number} via SMS using Simple SMS Messenger",
      "optimal_steps": "9",
      "tags": [
        "multi_app",
        "data_entry",
        "parameterized"
      ],
      "task_name": "MarkorCreateNoteAndSms"
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
