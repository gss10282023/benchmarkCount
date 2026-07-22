# Case Packet

## Case Metadata

- domain: `miniwob`
- case_unit_id: `miniwob.use-autocomplete`
- task_id: `miniwob.use-autocomplete`

## Source Inventory

- `derived/drafting_context.json`
- `derived/official_source_excerpts.json`
- `derived/selected_task_source.json`
- `official/install/miniwob/html/miniwob/use-autocomplete.html`

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
  "case_unit_id": "miniwob.use-autocomplete",
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
      "official/install/miniwob/html/miniwob/use-autocomplete.html::genProblem"
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
      "official/install/miniwob/html/miniwob/use-autocomplete.html::genProblem"
    ],
    "task_class": "UseAutocompleteTask"
  },
  "schema_version": "miniwob_pre_run_drafting_context/v1",
  "source_priority": [
    "released evaluator/oracle formal semantics",
    "official case-specific runtime user goal and task source",
    "necessary evaluator-visible state schema and pre-run artifact inventory"
  ],
  "stronger_measurement": {
    "case_interpretation_guards": [
      {
        "rule": "Do not require membership in the autocomplete source list as a stronger condition: the episode goal and oracle explicitly require only the stated prefix and optional suffix.",
        "support": [
          "official/install/miniwob/html/miniwob/use-autocomplete.html::genProblem"
        ]
      }
    ],
    "drafting_instruction": "Copy every required_additional_conditions item into stronger.additional_conditions, preserving id, text, rationale, support, and decisive artifact meaning. If the list is empty, keep the checklist stronger list empty. Do not infer any additional condition.",
    "empty_when_no_required_condition": true,
    "required_additional_conditions": [],
    "rule": "Include only an additional condition with concrete case-specific support in the official goal/task source beyond what the released evaluator operationalizes. Exclude reviewer preferences."
  },
  "task_id": "miniwob.use-autocomplete",
  "task_text": {
    "benchmark": "MiniWoB++",
    "runtime_goal_note": "Episode values vary by seed. Freeze a parameterized rule over the runtime-issued goal; do not insert a future episode's target value into the pre-run checklist.",
    "runtime_goal_source": "observation.goal at environment reset",
    "static_query_text": null,
    "static_title": "Use Autocomplete Task",
    "subdomain": "use-autocomplete",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_goal.content",
      "official/install/miniwob/html/miniwob/use-autocomplete.html::genProblem"
    ],
    "task_id": "miniwob.use-autocomplete"
  }
}
```

### `derived/official_source_excerpts.json`

Source ref: `derived from byte-pinned official MiniWoB++ sources`

```json
{
  "case_unit_id": "miniwob.use-autocomplete",
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
      "content": "class UseAutocompleteTask(AbstractMiniwobTask):\n    desc = \"Use autocomplete element efficiently.\"\n    subdomain = \"use-autocomplete\"",
      "end_line": 629,
      "fallback": false,
      "start_line": 627
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
      "byte_count": 2252,
      "path": "official/install/miniwob/html/miniwob/use-autocomplete.html",
      "sha256": "adae9f156209bde36c9ab134d7c06efecb2567921ce4d3a7cb6d203d11b6195f"
    }
  },
  "task_id": "miniwob.use-autocomplete"
}
```

### `derived/selected_task_source.json`

Source ref: `miniwob://miniwob.use-autocomplete`

```json
{
  "base_class_name": "AbstractMiniwobTask",
  "base_module": "browsergym.miniwob.base",
  "base_source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
  "case_unit_id": "miniwob.use-autocomplete",
  "class_name": "UseAutocompleteTask",
  "html_asset_files": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.js"
  ],
  "html_file": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/use-autocomplete.html",
  "html_title": "Use Autocomplete Task",
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
      "archive_path": "official/install/miniwob/html/miniwob/use-autocomplete.html",
      "sha256": "adae9f156209bde36c9ab134d7c06efecb2567921ce4d3a7cb6d203d11b6195f",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/use-autocomplete.html"
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
      "archive_path": "official/install/miniwob/html/core/d3.v3.min.js",
      "sha256": "8ca4da6691fb142cd76283014e887e7c3e61e3b63eff9ebb08eeb5c51d56aafb",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js"
    },
    {
      "archive_path": "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
      "sha256": "430f36f9b5f21aae8cc9dca6a81c4d3d84da5175eaedcf2fdc2c226302cb3575",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js"
    },
    {
      "archive_path": "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
      "sha256": "ac1c8f94750b39b12327a5d0c56fdf946dabfb6d91e5d2a202879ff9a5d67e29",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css"
    },
    {
      "archive_path": "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.js",
      "sha256": "28ce75d953678c4942df47a11707a15e3c756021cf89090e3e6aa7ad6b6971c3",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.js"
    }
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/use-autocomplete.html"
  ],
  "selection_order_key": "ef7485a4aa5a99baf58ebf09b16899a10679d66fed58831d249f73bb38d15781",
  "selection_rank": 114,
  "source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
  "source_ref": "miniwob://miniwob.use-autocomplete",
  "source_sha256": "c9c912adad9515c197323594728eb13622eb41fd5e00e7b0d7dda51c3151edbc",
  "static_query_text": null,
  "subdomain": "use-autocomplete",
  "task_id": "miniwob.use-autocomplete"
}
```

### `official/install/miniwob/html/miniwob/use-autocomplete.html`

Source ref: `<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/use-autocomplete.html`

```text
<!DOCTYPE html>
<html>
<head>
<title>Use Autocomplete Task</title>
<!-- stylesheets -->
<link rel="stylesheet" type="text/css" href="../core/core.css">
<link rel="stylesheet" href="../core/jquery-ui/jquery-ui.min.css">
<!-- JS -->
<script src="../core/core.js"></script>
<script src="../core/d3.v3.min.js"></script>
<script src="../core/jquery-ui/external/jquery/jquery.js"></script>
<script src="../core/jquery-ui/jquery-ui.min.js"></script>
<script src="../common/ui_utils.js"></script>

<style>
#area { padding: 10px; }
#area input { display: block; }
#subbtn { display: block; margin-top: 5px; }
#area input, .ui-menu { width: 120px; }
.bold { font-weight: bold; }
</style>

<script>
var genProblem = function() {
  ITEMS = ui_utils.COUNTRIES;
  d3.select('#tags')[0][0].value ='';

  var gtix = core.randi(0, ITEMS.length);
  // the below is complicated because we only want to match beginning of items in list
  $('#tags').autocomplete({
    source: function(request, response) {
      var matcher = new RegExp('^' + $.ui.autocomplete.escapeRegex(request.term), 'i');
      response($.grep(ITEMS, function(item){
          return matcher.test(item);
      }))
    }
  });

  var gtitem = ITEMS[gtix];

  var nf = core.randi(2, 5);
  var f = gtitem.slice(0,nf);

  var ne = core.randi(2, 5);
  var e = gtitem.slice(gtitem.length - ne);

  var match_end = core.randf(0,1) < 0.75;
  if(match_end) {
    d3.select('#query').html('Enter an item that starts with "<span class="bold">' + f + '</span>" and ends with "<span class="bold">' + e + '</span>".');
  } else {
    d3.select('#query').html('Enter an item that starts with "<span class="bold">' + f + '</span>".');
  }

  d3.select('#subbtn').on('click', function(){
    var entered = d3.select('#tags')[0][0].value;
    var ff = entered.startsWith(f);
    var ee = entered.endsWith(e);
    var correct = ff & (ee || !match_end);
    var r = correct ? 1.0 : -1.0;
    core.endEpisode(r, r>0);
  });
}

window.onload = function() {
  core.startEpisode();
}
</script>
</head>
<body>
<div id="wrap">
  <div id="query"></div>
  <div id="area">
    <label for="tags">Tags: </label>
    <input id="tags">
    <button id="subbtn" class="secondary-action">Submit</button>
  </div>
</div>
</body>
</html>
```

## Raw Source Provenance

```json
{
  "case_unit_id": "miniwob.use-autocomplete",
  "copied_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.js",
    "official/install/miniwob/html/miniwob/use-autocomplete.html",
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
    "derived/selected_task_source.json": "miniwob://miniwob.use-autocomplete",
    "official/install/miniwob/html/common/ui_utils.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.js",
    "official/install/miniwob/html/miniwob/use-autocomplete.html": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/use-autocomplete.html",
    "official/python/browsergym/miniwob/__init__.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
  },
  "official_files": [
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.js",
    "official/install/miniwob/html/miniwob/use-autocomplete.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/use-autocomplete.html"
  ],
  "sha256_per_file": {
    "derived/drafting_context.json": "5e27c29c124e6569072b707cb252a46038d44ee7de600e0b3530c8577c507189",
    "derived/official_source_excerpts.json": "816143f7f0a2c1ab6e272e6f94cb86daced749d50bc036c5871747a6ebae72fa",
    "derived/selected_task_source.json": "634c61b10fc897609cea436611c7359cbf10b67bea6b32843d6d2945c219d9b7",
    "official/install/miniwob/html/common/ui_utils.js": "65301ee11f483df7e9114f3fac2e2938e8b56933fecbed36bce310e2d8d90368",
    "official/install/miniwob/html/core/core.css": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
    "official/install/miniwob/html/core/core.js": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
    "official/install/miniwob/html/core/d3.v3.min.js": "8ca4da6691fb142cd76283014e887e7c3e61e3b63eff9ebb08eeb5c51d56aafb",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "430f36f9b5f21aae8cc9dca6a81c4d3d84da5175eaedcf2fdc2c226302cb3575",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css": "ac1c8f94750b39b12327a5d0c56fdf946dabfb6d91e5d2a202879ff9a5d67e29",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.js": "28ce75d953678c4942df47a11707a15e3c756021cf89090e3e6aa7ad6b6971c3",
    "official/install/miniwob/html/miniwob/use-autocomplete.html": "adae9f156209bde36c9ab134d7c06efecb2567921ce4d3a7cb6d203d11b6195f",
    "official/python/browsergym/miniwob/__init__.py": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
    "official/python/browsergym/miniwob/all.py": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
    "official/python/browsergym/miniwob/base.py": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
  },
  "source_refs": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/use-autocomplete.html",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
    "miniwob://miniwob.use-autocomplete",
    "derived://miniwob-pre-run-drafting-context/v1",
    "derived://miniwob-official-source-excerpts/v1"
  ],
  "task_id": "miniwob.use-autocomplete"
}
```
