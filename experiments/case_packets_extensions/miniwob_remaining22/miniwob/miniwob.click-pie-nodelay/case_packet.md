# Case Packet

## Case Metadata

- domain: `miniwob`
- case_unit_id: `miniwob.click-pie-nodelay`
- task_id: `miniwob.click-pie-nodelay`

## Source Inventory

- `derived/drafting_context.json`
- `derived/official_source_excerpts.json`
- `derived/selected_task_source.json`
- `official/install/miniwob/html/miniwob/click-pie-nodelay.html`

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
  "case_unit_id": "miniwob.click-pie-nodelay",
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
      "official/install/miniwob/html/miniwob/click-pie-nodelay.html::genProblem"
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
      "official/install/miniwob/html/miniwob/click-pie-nodelay.html::genProblem"
    ],
    "task_class": "ClickPieNodelayTask"
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
    "required_additional_conditions": [],
    "rule": "Include only an additional condition with concrete case-specific support in the official goal/task source beyond what the released evaluator operationalizes. Exclude reviewer preferences."
  },
  "task_id": "miniwob.click-pie-nodelay",
  "task_text": {
    "benchmark": "MiniWoB++",
    "runtime_goal_note": "Episode values vary by seed. Freeze a parameterized rule over the runtime-issued goal; do not insert a future episode's target value into the pre-run checklist.",
    "runtime_goal_source": "observation.goal at environment reset",
    "static_query_text": null,
    "static_title": "Click Pie Menu Task",
    "subdomain": "click-pie-nodelay",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_goal.content",
      "official/install/miniwob/html/miniwob/click-pie-nodelay.html::genProblem"
    ],
    "task_id": "miniwob.click-pie-nodelay"
  }
}
```

### `derived/official_source_excerpts.json`

Source ref: `derived from byte-pinned official MiniWoB++ sources`

```json
{
  "case_unit_id": "miniwob.click-pie-nodelay",
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
      "content": "class ClickPieNodelayTask(AbstractMiniwobTask):\n    desc = \"[click-pie] Removed animation.\"\n    subdomain = \"click-pie-nodelay\"\n    nondeterministic = True",
      "end_line": 188,
      "fallback": false,
      "start_line": 185
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
      "byte_count": 3273,
      "path": "official/install/miniwob/html/miniwob/click-pie-nodelay.html",
      "sha256": "e275a3c2a548d8a1edc6248c4cd28ec27e6329c1024ba9f26c59e527c03080f9"
    }
  },
  "task_id": "miniwob.click-pie-nodelay"
}
```

### `derived/selected_task_source.json`

Source ref: `miniwob://miniwob.click-pie-nodelay`

```json
{
  "base_class_name": "AbstractMiniwobTask",
  "base_module": "browsergym.miniwob.base",
  "base_source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
  "case_unit_id": "miniwob.click-pie-nodelay",
  "class_name": "ClickPieNodelayTask",
  "html_asset_files": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.icons.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/wheelnav.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css"
  ],
  "html_file": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/click-pie-nodelay.html",
  "html_title": "Click Pie Menu Task",
  "module": "browsergym.miniwob.all",
  "nondeterministic": true,
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
      "archive_path": "official/install/miniwob/html/miniwob/click-pie-nodelay.html",
      "sha256": "e275a3c2a548d8a1edc6248c4cd28ec27e6329c1024ba9f26c59e527c03080f9",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/click-pie-nodelay.html"
    },
    {
      "archive_path": "official/install/miniwob/html/common/special/click-pie/raphael.icons.min.js",
      "sha256": "51777d20fdcc55bc673839642611f675c61ab0e20ed7e256092edb3fc36146b2",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.icons.min.js"
    },
    {
      "archive_path": "official/install/miniwob/html/common/special/click-pie/raphael.min.js",
      "sha256": "0a02d6021c8cf2597497dfad2df84ef4f952dc049e7dff68fbd010f953fb46a6",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.min.js"
    },
    {
      "archive_path": "official/install/miniwob/html/common/special/click-pie/wheelnav.min.js",
      "sha256": "0d1ce8836d0e136fb064113ee7f71c0c6183a0c3cb61731532b8db964dd14912",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/wheelnav.min.js"
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
      "archive_path": "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
      "sha256": "ac1c8f94750b39b12327a5d0c56fdf946dabfb6d91e5d2a202879ff9a5d67e29",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css"
    }
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html"
  ],
  "selection_order_key": "de51c26f951ebd000be6234ee8a038238479dcd489abf80552f196a60ed1dc9d",
  "selection_rank": 104,
  "source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
  "source_ref": "miniwob://miniwob.click-pie-nodelay",
  "source_sha256": "2d16d4be64cebb4888bf88c26351e702dc3eeaf4d87429ccc46ab2d889c55fe8",
  "static_query_text": null,
  "subdomain": "click-pie-nodelay",
  "task_id": "miniwob.click-pie-nodelay"
}
```

### `official/install/miniwob/html/miniwob/click-pie-nodelay.html`

Source ref: `<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/click-pie-nodelay.html`

```text
<!DOCTYPE html>
<html>
<head>
<title>Click Pie Menu Task</title>

<!-- stylesheets -->
<link rel="stylesheet" type="text/css" href="../core/core.css">
<link rel="stylesheet" href="../core/jquery-ui/jquery-ui.min.css">
<style>
#piemenu > svg { width: 100%; height: 100%; }
#piemenu { height: 150px; width: 150px; margin:auto; }
@media (max-width: 150px) { #piemenu { height: 100px; width: 100px; } }

[class|=wheelnav-piemenu-slice-basic] { fill: #497F4C; stroke: none; }
[class|=wheelnav-piemenu-slice-selected] { fill: #497F4C; stroke: none; }
[class|=wheelnav-piemenu-slice-hover] { fill: #497F4C;  stroke: none; fill-opacity: 0.77; cursor: pointer; }

[class|=wheelnav-piemenu-title-basic] { fill: #333; stroke: none; }
[class|=wheelnav-piemenu-title-selected] { fill: #fff; stroke: none; }
[class|=wheelnav-piemenu-title-hover] { fill: #222; stroke: none; cursor: pointer; }

.wheelnav-piemenu-spreader-in,
.wheelnav-piemenu-spreader-out { fill: #444; stroke: #444; stroke-width: 2; cursor: pointer; }
.wheelnav-piemenu-spreadertitle-in,
.wheelnav-piemenu-spreadertitle-out { fill: #eee; stroke: #444; cursor: pointer; }
</style>

<!-- JS -->
<script src="../core/core.js"></script>
<script src="../core/d3.v3.min.js"></script>
<script src="../common/special/click-pie/raphael.min.js"></script>
<script src="../common/special/click-pie/raphael.icons.min.js"></script>
<script src="../common/special/click-pie/wheelnav.min.js"></script>
<script src="../common/ui_utils.js"></script>
<script>
var createItems = function(){
  var alphanumericList = core.shuffle(ui_utils.alphanumericList.slice());
  var setLength = core.randi(4,9)*-1;
  var problemSet = alphanumericList.splice(setLength);
  var wheel = new wheelnav('divWheel');
  wheel.spreaderEnable = true;
  wheel.currentPercent = 0;
  wheel.animatetime = 0;
  wheel.animateeffect = 'linear';
  wheel.createWheel(problemSet);

  var expectedItem = core.sample(problemSet);

  return {items: wheel, expectedItem: expectedItem, problemSet: problemSet};
}

var genProblem = function() {
  var wheel = createItems();

  d3.select('#query').html('Expand the pie menu below and click on the item labeled "<span class="bold">' + wheel.expectedItem + '</span>".');

  var clickEvent = function(){
    var r = wheel.problemSet[this.itemIndex] === wheel.expectedItem ? 1.0 : -1.0;
    core.endEpisode(r, r>0);
    // add some slight delay to removing the nav wheel, otherwise
    // it looks like it disappears a bit too suddenly.
    setTimeout(function(){wheel.items.removeWheel();}, 50);
  }

  // binding click events normally causes some weird delay and events sometimes not
  // properly triggering, so do this instead.
  var wheelElems = wheel.items;
  for(var i=0;i<wheelElems.navItems.length;i++){
    wheelElems.navItems[i].navigateFunction = clickEvent;
  }
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
    <div id="divWheel" data-wheelnav
      data-wheelnav-markerpath="DropMarker"
      data-wheelnav-wheelradius="80"
      data-wheelnav-navangle="90"
      data-wheelnav-slicepath="DonutSlice"
      data-wheelnav-colors="#E34C26,#F06529"
      data-wheelnav-rotateoff>
      </div>
  </div>
</div>
</body>
</html>
```

## Raw Source Provenance

```json
{
  "case_unit_id": "miniwob.click-pie-nodelay",
  "copied_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/common/special/click-pie/raphael.icons.min.js",
    "official/install/miniwob/html/common/special/click-pie/raphael.min.js",
    "official/install/miniwob/html/common/special/click-pie/wheelnav.min.js",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html",
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
    "derived/selected_task_source.json": "miniwob://miniwob.click-pie-nodelay",
    "official/install/miniwob/html/common/special/click-pie/raphael.icons.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.icons.min.js",
    "official/install/miniwob/html/common/special/click-pie/raphael.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.min.js",
    "official/install/miniwob/html/common/special/click-pie/wheelnav.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/wheelnav.min.js",
    "official/install/miniwob/html/common/ui_utils.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/click-pie-nodelay.html",
    "official/python/browsergym/miniwob/__init__.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
  },
  "official_files": [
    "official/install/miniwob/html/common/special/click-pie/raphael.icons.min.js",
    "official/install/miniwob/html/common/special/click-pie/raphael.min.js",
    "official/install/miniwob/html/common/special/click-pie/wheelnav.min.js",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html"
  ],
  "sha256_per_file": {
    "derived/drafting_context.json": "0dfb1d144abc99a9407abd217449fce4280804feb3c39c4df1ab2869bbf8b34f",
    "derived/official_source_excerpts.json": "87e630dc3e06d6f46a7174ebb1f51b86e2befd29ed9b2e81d110adad53ac55b0",
    "derived/selected_task_source.json": "4f0875c8dcde03fa7e3b8389664108fc2928b940be360769033c5e1dcf897487",
    "official/install/miniwob/html/common/special/click-pie/raphael.icons.min.js": "51777d20fdcc55bc673839642611f675c61ab0e20ed7e256092edb3fc36146b2",
    "official/install/miniwob/html/common/special/click-pie/raphael.min.js": "0a02d6021c8cf2597497dfad2df84ef4f952dc049e7dff68fbd010f953fb46a6",
    "official/install/miniwob/html/common/special/click-pie/wheelnav.min.js": "0d1ce8836d0e136fb064113ee7f71c0c6183a0c3cb61731532b8db964dd14912",
    "official/install/miniwob/html/common/ui_utils.js": "65301ee11f483df7e9114f3fac2e2938e8b56933fecbed36bce310e2d8d90368",
    "official/install/miniwob/html/core/core.css": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
    "official/install/miniwob/html/core/core.js": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
    "official/install/miniwob/html/core/d3.v3.min.js": "8ca4da6691fb142cd76283014e887e7c3e61e3b63eff9ebb08eeb5c51d56aafb",
    "official/install/miniwob/html/core/jquery-ui/jquery-ui.min.css": "ac1c8f94750b39b12327a5d0c56fdf946dabfb6d91e5d2a202879ff9a5d67e29",
    "official/install/miniwob/html/miniwob/click-pie-nodelay.html": "e275a3c2a548d8a1edc6248c4cd28ec27e6329c1024ba9f26c59e527c03080f9",
    "official/python/browsergym/miniwob/__init__.py": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
    "official/python/browsergym/miniwob/all.py": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
    "official/python/browsergym/miniwob/base.py": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
  },
  "source_refs": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.icons.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/raphael.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/special/click-pie/wheelnav.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/jquery-ui.min.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/click-pie-nodelay.html",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
    "miniwob://miniwob.click-pie-nodelay",
    "derived://miniwob-pre-run-drafting-context/v1",
    "derived://miniwob-official-source-excerpts/v1"
  ],
  "task_id": "miniwob.click-pie-nodelay"
}
```
