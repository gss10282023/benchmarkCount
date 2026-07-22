# Case Packet

## Case Metadata

- domain: `miniwob`
- case_unit_id: `miniwob.email-inbox-forward-nl-turk`
- task_id: `miniwob.email-inbox-forward-nl-turk`

## Source Inventory

- `derived/drafting_context.json`
- `derived/official_source_excerpts.json`
- `derived/selected_task_source.json`
- `official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html`

## Packet Source Files

### `derived/drafting_context.json`

Source ref: `src/evidence_system/contracts/case_packets.py::_miniwob_drafting_context`

```json
{
  "artifact_inventory": {
    "artifact_types": [
      "browser_artifact",
      "post_state",
      "trace",
      "native_evaluator_input",
      "native_evaluator_output",
      "structured_output",
      "file"
    ],
    "known_before_run": true,
    "producer_sources": [
      {
        "path": "src/evidence_system/adapters/miniwob_worker.py",
        "sha256": "73af6cb520ecdf1515a43fbf0eaec70e02d4ff2f76f06b64e758400f6f20e5e2"
      },
      {
        "path": "src/evidence_system/adapters/miniwob.py",
        "sha256": "ba5630621d22d8389a307cdd753d906e509ad594943b3a118c994704f2c05cad"
      }
    ],
    "retained_artifacts": [
      {
        "path": "task_context.json",
        "use": "runtime goal, goal object, task identity, URL, and action-space context"
      },
      {
        "path": "native_evaluator_input.json",
        "use": "validator entrypoint, task context, task kwargs, and initial validation"
      },
      {
        "path": "native_evaluator_output.json",
        "use": "final concrete validator reward, done, info, message, and step summaries"
      },
      {
        "path": "task_artifacts/",
        "use": "initial/final validation, task info, task state, reset info, and final chat"
      },
      {
        "path": "trajectory/",
        "use": "ordered actions and per-step observations"
      },
      {
        "path": "browser_artifacts/",
        "use": "per-step HTML, screenshots, and BrowserGym video recordings"
      },
      {
        "path": "openrouter_calls/",
        "use": "per-call request/response payload and parsed action record"
      },
      {
        "path": "run_summary.json",
        "use": "run status/navigation metadata; summary success is not independently decisive"
      }
    ]
  },
  "case_unit_id": "miniwob.email-inbox-forward-nl-turk",
  "contains_agent_outcomes": false,
  "evaluator_visible_state_schema": {
    "fields": [
      "REWARD_GLOBAL",
      "RAW_REWARD_GLOBAL",
      "REWARD_REASON",
      "DONE_GLOBAL",
      "EPISODE_ID",
      "TASK_READY"
    ],
    "source": "AbstractMiniwobTask._get_info",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_info.content",
      "derived/official_source_excerpts.json::excerpts.core_reward_wiring.content"
    ]
  },
  "freeze_guards": [
    "Lock the checklist before agent execution or access to outcomes.",
    "Do not modify native or stronger conditions after observing a run.",
    "Do not treat case-packet source as evidence that a particular run satisfied a condition.",
    "Do not encode benchmark conflict as a pre-run checklist condition."
  ],
  "locked_before_outcomes": true,
  "official_policy": {
    "applicability": "N/A",
    "support": [
      "derived/official_source_excerpts.json::excerpts.task_class.content",
      "derived/official_source_excerpts.json::excerpts.base_validator.methods.validate.content",
      "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::genProblem"
    ],
    "text": "MiniWoB++ provides no separate policy document. The official task class, base validator, task HTML, and directly invoked reward wiring define this case."
  },
  "phase": "pre_run_checklist_drafting",
  "post_run_reporting": {
    "benchmark_conflict_rule": "Never predeclare conflict in the checklist. Mark it only after a separate record-level audit when retained artifacts and source pointers prove that task/target/evaluator/oracle/reward wiring checked a different outcome from the benchmark's apparent claim.",
    "native_evidence_labels": {
      "F": "Evidence Fail",
      "S": "Evidence Pass",
      "U": "Unknown"
    },
    "paper_counts": {
      "F": "F",
      "S": "P",
      "U": "U"
    },
    "released_label_rule": "Preserve the released benchmark label unchanged and separately from S/F/U.",
    "stronger_rule": "Report stronger independently. Stronger failure is not a benchmark error and native S plus stronger F does not imply conflict."
  },
  "released_evaluator": {
    "base_class": "AbstractMiniwobTask",
    "entrypoint": "env.unwrapped.task.validate(page, chat_messages)",
    "failure_evidence_rule": "Retained evidence supports native failure when it establishes an invalid page/URL, a completed task outcome with non-positive raw reward, or another benchmark-counted run failure.",
    "native_semantics": "Invalid page or URL returns reward 0 and terminates. Otherwise validate reads the WOB state and returns binary reward float(RAW_REWARD_GLOBAL > 0) with DONE_GLOBAL.",
    "success_evidence_rule": "Retained evidence supports native success when it establishes a valid final validation with done true and binary reward 1.0, grounded in the task oracle's positive raw reward.",
    "summary_field_guard": "Do not treat a summary-only success/label field as decisive; inspect concrete validator reward, done, info, trace, and retained state.",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods.validate.content",
      "derived/official_source_excerpts.json::excerpts.core_reward_wiring.content",
      "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::genProblem"
    ],
    "task_class": "EmailInboxForwardNlTurkTask"
  },
  "schema_version": "miniwob_pre_run_drafting_context/v1",
  "source_priority": [
    "released evaluator/oracle formal semantics",
    "official case-specific runtime user goal and task source",
    "necessary evaluator-visible state schema and pre-run artifact inventory"
  ],
  "stronger_measurement": {
    "case_interpretation_guards": [],
    "drafting_instruction": "Copy every required_additional_conditions item into stronger.additional_conditions, preserving id, text, rationale, support, and decisive artifact meaning. If the list is empty, keep the checklist stronger list empty. Do not infer any additional condition.",
    "empty_when_no_required_condition": true,
    "required_additional_conditions": [
      {
        "decisive_post_run_artifacts": [
          "native_evaluator_output.json::info.RAW_REWARD_GLOBAL",
          "trajectory/steps.json and trajectory/observations/",
          "browser_artifacts/page_html/ and browser_artifacts/screenshots/"
        ],
        "id": "forwarded_email_is_from_runtime_specified_sender",
        "native_gap": "Native positive reward checks the expected recipient and target email body but does not verify which email record was selected for forwarding.",
        "rationale": "The official task requires finding the named sender's email and forwarding that email, while the positive forward oracle checks only the entered recipient and forward-text body and does not verify the selected email's sender or identity.",
        "support": [
          "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::displayQuery",
          "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::clickEmail",
          "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::genProblem",
          "derived/official_source_excerpts.json::excerpts.base_validator.methods.validate.content"
        ],
        "text": "The message actually selected for forwarding is an email from the runtime-specified sender, rather than a different email whose forward body was edited to match the target email body."
      }
    ],
    "rule": "Include only an additional condition with concrete case-specific support in the official goal/task source beyond what the released evaluator operationalizes. Exclude reviewer preferences."
  },
  "task_id": "miniwob.email-inbox-forward-nl-turk",
  "task_text": {
    "benchmark": "MiniWoB++",
    "runtime_goal_note": "Episode values vary by seed. Freeze a parameterized rule over the runtime-issued goal; do not insert a future episode's target value into the pre-run checklist.",
    "runtime_goal_source": "observation.goal at environment reset",
    "static_query_text": null,
    "static_title": "Email Inbox Task",
    "subdomain": "email-inbox-forward-nl-turk",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_goal.content",
      "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html::genProblem"
    ],
    "task_id": "miniwob.email-inbox-forward-nl-turk"
  }
}
```

### `derived/official_source_excerpts.json`

Source ref: `derived from byte-pinned official MiniWoB++ sources`

```json
{
  "case_unit_id": "miniwob.email-inbox-forward-nl-turk",
  "excerpts": {
    "base_validator": {
      "class_name": "AbstractMiniwobTask",
      "methods": {
        "_get_goal": {
          "content": "    def _get_goal(self) -> str:\n        response = self.page.evaluate(r\"\"\"() => core.getUtterance()\"\"\")\n        if isinstance(response, dict):\n            goal = response[\"utterance\"]\n        else:\n            goal = response\n        return goal",
          "end_line": 156,
          "fallback": false,
          "start_line": 150
        },
        "_get_info": {
          "content": "    def _get_info(self) -> dict:\n        (\n            REWARD_GLOBAL,\n            RAW_REWARD_GLOBAL,\n            REWARD_REASON,\n            DONE_GLOBAL,\n            EPISODE_ID,\n            TASK_READY,\n        ) = self.page.evaluate(\n            r\"\"\"() => [WOB_REWARD_GLOBAL, WOB_RAW_REWARD_GLOBAL, WOB_REWARD_REASON, WOB_DONE_GLOBAL, WOB_EPISODE_ID, WOB_TASK_READY]\"\"\"\n        )\n        info = {\n            \"REWARD_GLOBAL\": REWARD_GLOBAL,\n            \"RAW_REWARD_GLOBAL\": RAW_REWARD_GLOBAL,\n            \"REWARD_REASON\": REWARD_REASON,\n            \"DONE_GLOBAL\": DONE_GLOBAL,\n            \"EPISODE_ID\": EPISODE_ID,\n            \"TASK_READY\": TASK_READY,\n        }\n        return info",
          "end_line": 177,
          "fallback": false,
          "start_line": 158
        },
        "validate": {
          "content": "    def validate(\n        self, page: playwright.sync_api.Page, chat_messages: list[str]\n    ) -> Tuple[float, bool, str, dict]:\n        if page != self.page:\n            return 0, True, \"\", {\"error\": \"invalid page, terminating task\"}\n        if page.url != self.url:\n            return 0, True, \"\", {\"error\": \"invalid url, terminating task\"}\n\n        info = self._get_info()\n        reward = float(info[\"RAW_REWARD_GLOBAL\"] > 0)  # TODO: shouldn't it be 0.5?\n        done = info[\"DONE_GLOBAL\"]\n        msg = \"\"\n        return reward, done, msg, info",
          "end_line": 191,
          "fallback": false,
          "start_line": 179
        }
      }
    },
    "core_reward_wiring": {
      "content": "var WOB_REWARD_GLOBAL = 0; // what was reward in previous iteration?\nvar WOB_RAW_REWARD_GLOBAL = 0; // reward without time penalty\nvar WOB_REWARD_REASON = null; // reason for the reward\nvar WOB_DONE_GLOBAL = false; // a done indicator\nvar WOB_EPISODE_ID = 0; // number of episodes done so far\nvar WOB_TASK_READY = true; // override this to show that the task is not ready yet\ncore.EPISODE_MAX_TIME = 10000; // in ms. Set default time to 10s.\n\n\ncore.endEpisode = function(reward, time_proportional, reason) {\n  // stop timer and set to null, so that only one event gets rewarded\n  // for any given episode.\n  if(core.EP_TIMER !== null) {\n    clearTimeout(core.EP_TIMER);\n    core.EP_TIMER = null;\n  } else {\n    // if timer is null, don't reward anything and exit out.\n    return;\n  }\n\n  WOB_RAW_REWARD_GLOBAL = reward;\n  WOB_REWARD_REASON = reason;\n\n  // adjust reward based on time, so acting early is encouraged\n  var ept1 = new Date().getTime(); // get system time\n  if(typeof time_proportional === 'undefined') { time_proportional = false; }\n  if(time_proportional) {\n    var dt = ept1 - core.ept0; // difference in ms since start of ep\n    reward = reward * Math.max(0, 1.0 - dt/core.EPISODE_MAX_TIME);\n  }\n\n  WOB_REWARD_GLOBAL = reward; // add to global, to be accessed from Python\n  WOB_DONE_GLOBAL = true;\n  WOB_EPISODE_ID++;\n  document.getElementById('episode-id').innerHTML = WOB_EPISODE_ID;\n  console.log('reward: ' + WOB_REWARD_GLOBAL + ' (raw: ' + WOB_RAW_REWARD_GLOBAL + ')');\n  core.updateDisplay(reward);\n  core.clearTimer();\n\n  // start a new problem with a new timer. add a slight delay so that the problem\n  // isn't generated immediately, which can lead to accidental clicking.\n  //setTimeout(function(){\n  //  core.startEpisode();\n  //}, 500);\n\n  // With the sync screen, the timeout above is redundant\n  core.startEpisode();\n}",
      "end_line": 144,
      "fallback": false,
      "non_contiguous": true,
      "segments": [
        {
          "end_line": 51,
          "start_line": 44
        },
        {
          "end_line": 144,
          "start_line": 106
        }
      ],
      "start_line": 44
    },
    "task_class": {
      "content": "class EmailInboxForwardNlTurkTask(AbstractMiniwobTask):\n    desc = \"[email-inbox-forward] varied instruction texts (100 templates).\"\n    subdomain = \"email-inbox-forward-nl-turk\"",
      "end_line": 353,
      "fallback": false,
      "start_line": 351
    }
  },
  "extraction": {
    "contains_agent_outcomes": false,
    "method": "deterministic exact line excerpts from byte-pinned raw_case files"
  },
  "schema_version": "miniwob_official_source_excerpts/v1",
  "source_inventory": {
    "base_validator": {
      "byte_count": 6322,
      "path": "official/python/browsergym/miniwob/base.py",
      "sha256": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
    },
    "core_reward_wiring": {
      "byte_count": 22274,
      "path": "official/install/miniwob/html/core/core.js",
      "sha256": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14"
    },
    "task_class": {
      "byte_count": 19080,
      "path": "official/python/browsergym/miniwob/all.py",
      "sha256": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98"
    },
    "task_html": {
      "byte_count": 18042,
      "path": "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
      "sha256": "8421aa0a0bf67cbff225276db7426caf61b54b316a033287f4864d53850f856f"
    }
  },
  "task_id": "miniwob.email-inbox-forward-nl-turk"
}
```

### `derived/selected_task_source.json`

Source ref: `miniwob://miniwob.email-inbox-forward-nl-turk`

```json
{
  "base_class_name": "AbstractMiniwobTask",
  "base_module": "browsergym.miniwob.base",
  "base_source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
  "case_unit_id": "miniwob.email-inbox-forward-nl-turk",
  "class_name": "EmailInboxForwardNlTurkTask",
  "html_asset_files": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/email-inbox-nl/templates.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js"
  ],
  "html_file": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
  "html_title": "Email Inbox Task",
  "module": "browsergym.miniwob.all",
  "nondeterministic": false,
  "official_files": [
    {
      "archive_path": "official/python/browsergym/miniwob/__init__.py",
      "sha256": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
      "source_path": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py"
    },
    {
      "archive_path": "official/python/browsergym/miniwob/all.py",
      "sha256": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
      "source_path": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py"
    },
    {
      "archive_path": "official/python/browsergym/miniwob/base.py",
      "sha256": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab",
      "source_path": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
    },
    {
      "archive_path": "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
      "sha256": "8421aa0a0bf67cbff225276db7426caf61b54b316a033287f4864d53850f856f",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/email-inbox-forward-nl-turk.html"
    },
    {
      "archive_path": "official/install/miniwob/html/common/special/email-inbox-nl/templates.js",
      "sha256": "7f310ee07564a625ab48d8e12eb98cfcdc760e6c864339bb11ac9516855242e7",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/email-inbox-nl/templates.js"
    },
    {
      "archive_path": "official/install/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
      "sha256": "b2254d2d32275f5993020eccbf8c4a216446af5cbc4249f104c0cdb2ae4a9cb3",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js"
    },
    {
      "archive_path": "official/install/miniwob/html/common/ui_utils.js",
      "sha256": "65301ee11f483df7e9114f3fac2e2938e8b56933fecbed36bce310e2d8d90368",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js"
    },
    {
      "archive_path": "official/install/miniwob/html/core/core.css",
      "sha256": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css"
    },
    {
      "archive_path": "official/install/miniwob/html/core/core.js",
      "sha256": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js"
    },
    {
      "archive_path": "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
      "sha256": "430f36f9b5f21aae8cc9dca6a81c4d3d84da5175eaedcf2fdc2c226302cb3575",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js"
    }
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html"
  ],
  "selection_order_key": "d92b6deadb3d714d0740499b4c949c175a97c36ab6747df49248b89113f266c4",
  "selection_rank": 101,
  "source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
  "source_ref": "miniwob://miniwob.email-inbox-forward-nl-turk",
  "source_sha256": "2a753f5dd87ec229150b9aaeb9767ddb722d50271d4fe2f8d11d75a5c88172a7",
  "static_query_text": null,
  "subdomain": "email-inbox-forward-nl-turk",
  "task_id": "miniwob.email-inbox-forward-nl-turk"
}
```

### `official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html`

Source ref: `<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/email-inbox-forward-nl-turk.html`

```text
<!DOCTYPE html>
<html>
<head>
<title>Email Inbox Task</title>
<!-- credit to flaticon.com for the icons used in this task. -->
<!-- stylesheets -->
<link rel="stylesheet" type="text/css" href="../core/core.css">
<!-- JS -->
<script src="../core/core.js"></script>
<script src="../core/jquery-ui/external/jquery/jquery.js"></script>
<script src="../common/ui_utils.js"></script>
<script src="../common/special/navigate-tree/jquery.treeview.min.js"></script>
<script src="../common/special/email-inbox-nl/templates.js"></script>

<style>
#main { height: 150px; width: 155px; overflow-y: scroll; overflow-x: hidden; }

#main-header { height: 20px; line-height: 20px; background-color: #F92525;  color: #FFF; padding: 0 5px 0 0; border-bottom: 1px solid #C9C9C9; }
#main-header h2 { display: inline-block; font-size: 12px; font-weight: 100; margin: 0 5px; }
#open-search { float: right; content:url(../common/special/email-inbox/search.png); height: 12px; margin: 3px;
  cursor: pointer; }

#search { height: 150px; width: 155px; overflow-y: scroll; overflow-x: hidden; }
#search-header { height: 20px; line-height: 20px; }
#search-cancel { content:url(../common/special/email-inbox/left-arrow.png); height: 12px; margin: 3px;
  cursor: pointer; vertical-align: middle; }
#search-header #search-input { border: none; }
#search-header input:focus { outline: none; }
#results-header { background-color: #E5E6E8; color: #555; padding: 3px 5px;
  margin: 0px; height: 10px; }
#results-header h4 { margin: 0 5px; padding: 0; font-weight: 100; line-height: 10px; font-size: 9px; }

.email-thread { padding: 2px 10px 2px 5px; border-bottom: 1px solid #C9C9C9; cursor: pointer; clear: both; }
.email-thread:hover { background-color: rgba(188, 214, 255, 0.4); }
.email-left { width: 70%; display: inline-block; }
.email-sender { font-weight: bold; font-size: 11px; }
.email-subject { font-weight: bold; }
.email-right { width: 28%; float: right; display: inline-block;  text-align: right; }
.email-time { font-weight: bold; }

.email-actions { display: inline-block; float: right; margin: 2px; }
.email-actions .star { content:url(../common/special/email-inbox/star.png); height: 12px; float: right;
  margin: 3px 1px; opacity: 0.4; user-select: none; cursor: pointer; }
.email-actions .star.clicked { content:url(../common/special/email-inbox/star-clicked.png); height: 12px; float: right; margin: 3px 1px; opacity: 1.0; }
.email-actions .trash { content:url(../common/special/email-inbox/delete.png); height: 12px; float: right; margin: 3px 1px; opacity: 0.6; user-select: none; cursor: pointer; }
.email-actions span:hover { opacity: 1.0; }

#email { height: 150px; width: 155px; overflow-y: scroll; overflow-x: hidden; }
#email-bar { height: 20px; line-height: 20px; background-color: #F92525; }
#close-email { content:url(../common/special/email-inbox/left-arrow-white.png); height: 12px;
  vertical-align: middle;  cursor: pointer; }
#email .email-left { display: inline-block; float: left; width: 70%; height: 20px; padding-left: 4px;
  font-size: 8px; padding-top: 2px; }
#email .email-right { display: inline-block; width: 20%; float: right; height: 20px; padding-right: 4px;
  font-size: 8px; padding-top: 2px; }
#email div, #email span { font-weight: 100; }
#email .email-header { height: 40px; }
#email .email-body { padding: 4px; min-height: 40px; }
#email .email-subject { font-weight: 100; font-size: 12px; padding: 2px 5px; border-bottom: 1px solid #C9C9C9; }
#email .email-sender { font-weight: 100; font-size: 9px; }
#email .email-send { text-align: center; cursor: pointer; border-top: 1px solid #C9C9C9; padding: 3px; }
#email .email-send span { width: 40px; text-align: center; display: inline-block; font-size: 8px; }
.email-reply .icon { content:url(../common/special/email-inbox/reply.png); height: 18px; margin: 0 auto; }
.email-reply { margin-right: 7px; }
.email-forward .icon { content:url(../common/special/email-inbox/forward.png); height: 18px; margin: 0 auto; }
.email-forward { margin-left: 7px; }

#reply label { font-weight: bold; }
#reply #reply-bar { height: 20px; line-height: 20px; border-bottom: 1px solid #C9C9C9; }
#close-reply { content:url(../common/special/email-inbox/left-arrow.png); height: 12px; margin: 3px;
  cursor: pointer; vertical-align: middle; }
#send-reply { content:url(../common/special/email-inbox/send.png); height: 14px; margin: 3px;
  cursor: pointer; vertical-align: middle; float: right;}
#reply .reply-info { padding: 2px; border-bottom: 1px solid #C9C9C9; }
#reply .reply-subject { padding: 2px; border-bottom: 1px solid #C9C9C9; font-size: 10px; }
#reply textarea { border: none; height: 95px; width: 150px; }
#reply textarea:focus { outline: none; }

#forward label { font-weight: bold; }
#forward #forward-bar { height: 20px; line-height: 20px; border-bottom: 1px solid #C9C9C9; }
#close-forward { content:url(../common/special/email-inbox/left-arrow.png); height: 12px; margin: 3px;
  cursor: pointer; vertical-align: middle; }
#send-forward { content:url(../common/special/email-inbox/send.png); height: 14px; margin: 3px;
  cursor: pointer; vertical-align: middle; float: right;}
#forward .forward-sender { border: none; width: 150px; }
#forward .forward-sender:focus { outline: none; }
#forward .forward-info { padding: 2px; border-bottom: 1px solid #C9C9C9; }
#forward .forward-subject { padding: 2px; border-bottom: 1px solid #C9C9C9; font-size: 10px; }
#forward textarea { border: none; height: 95px; width: 150px; }
#forward textarea:focus { outline: none; }

.highlight { background-color: #F4F142; }
.hide { display: none; }
</style>

<script>
core.EPISODE_MAX_TIME = 30000;
var MAIN_TEMPLATE =
`
<div id="main-header">
  <h2>Primary</h2>
  <span id="open-search"></span>
</div>
`

var EMAIL_SUMMARY_TEMPLATE =
`
<div class="email-left">
  <div class="email-sender"></div>
  <div class="email-subject"></div>
  <div class="email-body"></div>
</div>
<div class="email-right">
  <div class="email-time"></div>
  <div class="email-actions">
    <span class="trash"></span>
    <span class="star"></span>
  </div>
</div>
`

var SEARCH_TEMPLATE =
`
<div id="search-bar">
  <div id="search-header">
    <span id="search-cancel"></span>
    <span><input type="text" id="search-input" placeholder="Search"></span>
  </div>
</div>
<div id="results-header">
  <h4>Results</h4>
</div>
<div id="search-results"></div>
`

var EMAIL_TEMPLATE =
`
<div id="email-bar">
  <span id="close-email"></span>
  <div class="email-actions">
    <span class="trash"></span>
    <span class="star"></span>
  </div>
</div>
<div class="email-header">
  <div class="email-subject"></div>
  <span class="email-left">
    <div class="email-sender">Sender</div>
    <div>to me</div>
  </span>
  <span class="email-right">
    <div class="email-time"></div>
  </span>
</div>
<div class="email-body"></div>
<div class="email-send">
  <span class="email-reply">
    <div class="icon"></div>
    <div>Reply</div>
  </span>
  <span class="email-forward">
    <div class="icon"></div>
    <div>Forward</div>
  </span>
</div>
`

var REPLY_TEMPLATE =
`
<div id="reply-bar">
  <span id="close-reply"></span>
  <span id="send-reply"></span>
</div>
<div class="reply-header">
  <div class="reply-info">
    <label class="reply-to">to: </label>
    <span class="reply-sender"></span>
  </div>

  <div class="reply-subject"><label class="reply-subj">subject: </label>Re: </div>
</div>
<div class="reply-body">
  <textarea id="reply-text"></textarea>
</div>
`

var FORWARD_TEMPLATE =
`
<div id="forward-bar">
  <span id="close-forward"></span>
  <span id="send-forward"></span>
</div>
<div class="forward-header">
  <div class="forward-info">
    <label>to: </label><input type="text" class="forward-sender">
  </div>
  <div class="forward-subject"><label>subject: </label></div>
</div>
<div class="forward-body">
  <textarea id="forward-text"></textarea>
</div>
`

var MAX_EMAILS = 12;
var EMAIL_ACTIONS = ['forward'];


var generateEmails = function(){
  var emails = [];
  var n = core.randi(4, MAX_EMAILS);
  for(var i=0;i<n;i++){
    var email = {};
    email.name = core.sample(ui_utils.PEOPLE_NAMES);
    email.subject = ui_utils.generateWords(1,3);
    email.body = ui_utils.generateWords(5,15);

    emails.push(email);
  }

  return emails;
}

var displayEmailSummaries = function(emails){
  for(var i=0;i<emails.length;i++){
    var div = document.createElement('div');
    div.setAttribute('class', 'email-thread');
    div.setAttribute('data-index', i);
    div.innerHTML = EMAIL_SUMMARY_TEMPLATE;

    div.getElementsByClassName('email-sender')[0].innerHTML = emails[i].name;
    div.getElementsByClassName('email-subject')[0].innerHTML = summarizeEmailContent(emails[i].subject);
    div.getElementsByClassName('email-body')[0].innerHTML = summarizeEmailContent(emails[i].body);

    $('#main').append(div);
  }
};

var displaySearchResults = function(emails, searchString){
  $('#search-results').empty();

  for(var i=0;i<emails.length;i++){
    var div = document.createElement('div');
    div.setAttribute('class', 'email-thread');
    div.setAttribute('data-index', i);
    div.innerHTML = EMAIL_SUMMARY_TEMPLATE;

    if(emails[i].name.indexOf(searchString) === -1 && emails[i].subject.indexOf(searchString) === -1
      && emails[i].body.indexOf(searchString) === -1 ) continue;
    div.getElementsByClassName('email-sender')[0].innerHTML = emails[i].name.replace(searchString, '<span class="highlight">'+searchString+'</span>');
    div.getElementsByClassName('email-subject')[0].innerHTML = emails[i].subject.replace(searchString, '<span class="highlight">'+searchString+'</span>');
    div.getElementsByClassName('email-body')[0].innerHTML = summarizeEmailContent(emails[i].body).replace(searchString, '<span class="highlight">'+searchString+'</span>');

    $('#search-results').append(div);
  }
};

var summarizeEmailContent = function(email){
  var emailLength = email.length;
  if(emailLength < 15) return email;
  else return email.substring(0,15) + '..';
}

var showEmail = function(email, expectedDetails){
  var emailDiv = document.createElement('div');
  emailDiv.setAttribute('id', 'email');
  emailDiv.innerHTML = EMAIL_TEMPLATE;

  emailDiv.getElementsByClassName('email-sender')[0].innerHTML = email.name;
  emailDiv.getElementsByClassName('email-subject')[0].innerHTML = email.subject;
  emailDiv.getElementsByClassName('email-body')[0].innerHTML = email.body;

  $('#main').addClass('hide');
  $('#search').addClass('hide');
  $('#area').append(emailDiv);

  $('#close-email').on('click', function(){
    $('#email').remove();
    $('#main').removeClass('hide');
  });


  // click events start below.
  $('#email .email-actions span.star').on('click', function(){
    var name = $('#email .email-sender').text();
    if($(this).hasClass('clicked')){
      $(this).removeClass('clicked');
    } else {
      $(this).addClass('clicked');
    }

    // only reward when action is 'important', otherwise show toggle animation.
    if(expectedDetails.action === 'important' && name == expectedDetails.email.name){
      core.endEpisode(1, true);
    } else if (expectedDetails.action === 'important'){
      core.endEpisode(-1, false);
    }
    return false;
  });

  // click events start below.
  $('#email .email-actions span.trash').on('click', function(){
    var name = $('#email .email-sender').text();

    // only reward when action is 'delete', otherwise do nothing.
    if(expectedDetails.action === 'delete' && name == expectedDetails.email.name){
      core.endEpisode(1, true);
    } else if (expectedDetails.action === 'delete'){
      core.endEpisode(-1, false);
    }

    return false;
  });

}

var showReply = function(email){
  var reply = document.createElement('div');
  reply.setAttribute('id', 'reply');
  reply.innerHTML = REPLY_TEMPLATE;

  reply.getElementsByClassName('reply-sender')[0].innerHTML = email.name;
  reply.getElementsByClassName('reply-subject')[0].innerHTML += email.subject;

  $('#email').addClass('hide');
  $('#area').append(reply);
}

var showForward = function(email){
  var forward = document.createElement('div');
  forward.setAttribute('id', 'forward');
  forward.innerHTML = FORWARD_TEMPLATE;

  forward.getElementsByClassName('forward-subject')[0].innerHTML += email.subject;
  forward.getElementsByTagName('textarea')[0].value = email.body;

  $('#email').addClass('hide');
  $('#area').append(forward);
}

var clickEmail = function(e){
  var emails = e.data.emails;
  var expectedDetails = e.data.expectedDetails;
  var emailIndex = $(this).attr('data-index');
  var email = emails[parseInt(emailIndex,10)];
  showEmail(email, expectedDetails);

  $('#email .email-reply').on('click', function(){
    showReply(email);
    $('#close-reply').on('click', cancelReply);
    $('#send-reply').on('click', function(){
      var name = $(this).parents('#reply').find('.reply-sender').text()
      var text = $('#reply-text').val();

      // reward positive score if they correctly reply when tasked.
      // if they reply to anything else, reward a negative score.
      if(expectedDetails.action === 'reply' && name === expectedDetails.email.name && text === expectedDetails.reply){
        core.endEpisode(1, true);
      } else {
        core.endEpisode(-1);
      }
    });
  });

  $('#email .email-forward').on('click', function(){
    showForward(email);
    $('#close-forward').on('click', cancelForward);
    $('#send-forward').on('click', function(){
      var name = $(this).parents('#forward').find('.forward-sender').val()
      var text = $('#forward-text').val();

      // reward positive score if they correctly forward when tasked.
      // if they forward anything else, reward a negative score.
      if(expectedDetails.action === 'forward' && name === expectedDetails.forward
        && text === expectedDetails.email.body){
        core.endEpisode(1, true);
      } else {
        core.endEpisode(-1);
      }
    });
  });
}

var cancelReply = function(){
  $('#reply').remove();
  $('#email').removeClass('hide');
}

var cancelForward = function(){
  $('#forward').remove();
  $('#email').removeClass('hide');
}

var displayQuery = function(expectedDetails){
  var template = core.sample(WOB_DATA_MODE == 'test' ?
      TEMPLATES[expectedDetails.action].test : 
      TEMPLATES[expectedDetails.action].train);
  core.currentFields = {
    'by': expectedDetails.email.name,
    'to': expectedDetails.forward,
  };
  concrete = template
    .replace(/NAME/, core.currentFields.by)
    .replace(/DEST/, core.currentFields.to);
  $('#query').text(concrete);
}

// Override by wrapping the original getUtterance
core.getUtterance = (function (origGetUtterance) {
  return function () {
    if (WOB_DATA_MODE == 'test') {
      return origGetUtterance();
    } else {
      return {
        'utterance': origGetUtterance(),
        'fields': core.currentFields,
      };
    }
  };
})(core.getUtterance);

var bindClickEvents = function(expectedDetails, emails){
  $('#main .email-actions span.star').on('click', function(){
    var name = $(this).parents('.email-thread').find('.email-sender').text();
    if($(this).hasClass('clicked')){
      $(this).removeClass('clicked');
    } else {
      $(this).addClass('clicked');
    }

    // only reward when action is 'important', otherwise show toggle animation.
    if(expectedDetails.action === 'important' && name == expectedDetails.email.name){
      core.endEpisode(1, true);
    } else if (expectedDetails.action === 'important'){
      core.endEpisode(-1, false);
    }
    return false;
  });

  // click events start below.
  $('#main .email-actions span.trash').on('click', function(){
    var name = $(this).parents('.email-thread').find('.email-sender').text();

    // only reward when action is 'delete', otherwise do nothing.
    if(expectedDetails.action === 'delete' && name == expectedDetails.email.name){
      core.endEpisode(1, true);
    } else if (expectedDetails.action === 'delete'){
      core.endEpisode(-1, false);
    }

    return false;
  });

  $('#open-search').on('click', function(){
    $('#search').removeClass('hide');
    $('#main').addClass('hide');
    $('#search-input').focus();
  });

  $('#search-cancel').on('click', function(){
    $('#search').addClass('hide');
    $('#main').removeClass('hide');
    $('#search-input').val('');
  });

  $('#search-input').on('keyup', function(){
    var searchText = $(this).val();
    if(searchText.replace(/\s/g,'').length > 0) {
      displaySearchResults(emails, searchText);
      $('#search .email-thread').on('click', {emails: emails, expectedDetails: expectedDetails}, clickEmail);
    } else {
      $('#search-results').empty();
    }
  });

  $('.email-thread').on('click', {emails: emails, expectedDetails: expectedDetails}, clickEmail);
}

// empty the UI at the start of the episode and set it up
// with the main and search templates.
var setupInbox = function(){
  $('#area').empty();
  var main = document.createElement('div');
  main.setAttribute('id', 'main');
  main.innerHTML = MAIN_TEMPLATE;
  $('#area').append(main);

  var search = document.createElement('div')
  search.setAttribute('id', 'search');
  search.setAttribute('class', 'hide');
  search.innerHTML = SEARCH_TEMPLATE;
  $('#area').append(search);
}

var genProblem = function(){
  setupInbox();
  var emails = generateEmails();
  displayEmailSummaries(emails);

  var shuffled = emails.slice();
  core.shuffle(shuffled);
  var expectedDetails = {};
  expectedDetails.action = core.sample(EMAIL_ACTIONS);
  expectedDetails.email = shuffled[0];
  if (expectedDetails.action == 'reply') {
    expectedDetails.reply = ui_utils.generateWords(1,5);
  } else if (expectedDetails.action == 'forward') {
    expectedDetails.forward = shuffled[1].name;
  }

  displayQuery(expectedDetails);
  bindClickEvents(expectedDetails, emails);
}

window.onload = function() {
  core.startEpisode();
}
</script>
</head>
<body>
<div id="wrap">
  <div id="query"></div>
  <div id="area"></div>
</div>
</body>
</html>
```

## Raw Source Provenance

```json
{
  "case_unit_id": "miniwob.email-inbox-forward-nl-turk",
  "copied_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/common/special/email-inbox-nl/templates.js",
    "official/install/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "derived_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json"
  ],
  "domain": "miniwob",
  "file_sources": {
    "derived/drafting_context.json": "src/evidence_system/contracts/case_packets.py::_miniwob_drafting_context",
    "derived/official_source_excerpts.json": "derived from byte-pinned official MiniWoB++ sources",
    "derived/selected_task_source.json": "miniwob://miniwob.email-inbox-forward-nl-turk",
    "official/install/miniwob/html/common/special/email-inbox-nl/templates.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/email-inbox-nl/templates.js",
    "official/install/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
    "official/install/miniwob/html/common/ui_utils.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
    "official/python/browsergym/miniwob/__init__.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
  },
  "official_files": [
    "official/install/miniwob/html/common/special/email-inbox-nl/templates.js",
    "official/install/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html"
  ],
  "sha256_per_file": {
    "derived/drafting_context.json": "9be7f9c38d55c1985c6e7c68c02e69c77badfc046820e5fb7db61d4b7eb94f3f",
    "derived/official_source_excerpts.json": "73bee3b6213facdc89ebe578b156329bd4bac743306bec55a3567c7ce179ad4c",
    "derived/selected_task_source.json": "ee94076f3e8ab92419b4b67acedf98c753b059022776a1e779c783c05d3eac87",
    "official/install/miniwob/html/common/special/email-inbox-nl/templates.js": "7f310ee07564a625ab48d8e12eb98cfcdc760e6c864339bb11ac9516855242e7",
    "official/install/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js": "b2254d2d32275f5993020eccbf8c4a216446af5cbc4249f104c0cdb2ae4a9cb3",
    "official/install/miniwob/html/common/ui_utils.js": "65301ee11f483df7e9114f3fac2e2938e8b56933fecbed36bce310e2d8d90368",
    "official/install/miniwob/html/core/core.css": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
    "official/install/miniwob/html/core/core.js": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "430f36f9b5f21aae8cc9dca6a81c4d3d84da5175eaedcf2fdc2c226302cb3575",
    "official/install/miniwob/html/miniwob/email-inbox-forward-nl-turk.html": "8421aa0a0bf67cbff225276db7426caf61b54b316a033287f4864d53850f856f",
    "official/python/browsergym/miniwob/__init__.py": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
    "official/python/browsergym/miniwob/all.py": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
    "official/python/browsergym/miniwob/base.py": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
  },
  "source_refs": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/email-inbox-nl/templates.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/navigate-tree/jquery.treeview.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/email-inbox-forward-nl-turk.html",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
    "miniwob://miniwob.email-inbox-forward-nl-turk",
    "derived://miniwob-pre-run-drafting-context/v1",
    "derived://miniwob-official-source-excerpts/v1"
  ],
  "task_id": "miniwob.email-inbox-forward-nl-turk"
}
```
