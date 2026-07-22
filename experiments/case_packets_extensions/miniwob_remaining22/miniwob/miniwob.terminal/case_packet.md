# Case Packet

## Case Metadata

- domain: `miniwob`
- case_unit_id: `miniwob.terminal`
- task_id: `miniwob.terminal`

## Source Inventory

- `derived/drafting_context.json`
- `derived/official_source_excerpts.json`
- `derived/selected_task_source.json`
- `official/install/miniwob/html/miniwob/terminal.html`

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
  "case_unit_id": "miniwob.terminal",
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
      "official/install/miniwob/html/miniwob/terminal.html::genProblem"
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
      "official/install/miniwob/html/miniwob/terminal.html::genProblem"
    ],
    "task_class": "TerminalTask"
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
  "task_id": "miniwob.terminal",
  "task_text": {
    "benchmark": "MiniWoB++",
    "runtime_goal_note": "Episode values vary by seed. Freeze a parameterized rule over the runtime-issued goal; do not insert a future episode's target value into the pre-run checklist.",
    "runtime_goal_source": "observation.goal at environment reset",
    "static_query_text": null,
    "static_title": "Terminal Task",
    "subdomain": "terminal",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_goal.content",
      "official/install/miniwob/html/miniwob/terminal.html::genProblem"
    ],
    "task_id": "miniwob.terminal"
  }
}
```

### `derived/official_source_excerpts.json`

Source ref: `derived from byte-pinned official MiniWoB++ sources`

```json
{
  "case_unit_id": "miniwob.terminal",
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
      "content": "class TerminalTask(AbstractMiniwobTask):\n    desc = \"Use the terminal to delete a file.\"\n    subdomain = \"terminal\"\n    nondeterministic = True",
      "end_line": 604,
      "fallback": false,
      "start_line": 601
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
      "byte_count": 8471,
      "path": "official/install/miniwob/html/miniwob/terminal.html",
      "sha256": "693d6df21b79ce13bb8480deded301893862acb26f642e09181cbea77fe42d29"
    }
  },
  "task_id": "miniwob.terminal"
}
```

### `derived/selected_task_source.json`

Source ref: `miniwob://miniwob.terminal`

```json
{
  "base_class_name": "AbstractMiniwobTask",
  "base_module": "browsergym.miniwob.base",
  "base_source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
  "case_unit_id": "miniwob.terminal",
  "class_name": "TerminalTask",
  "html_asset_files": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js"
  ],
  "html_file": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/terminal.html",
  "html_title": "Terminal Task",
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
      "archive_path": "official/install/miniwob/html/miniwob/terminal.html",
      "sha256": "693d6df21b79ce13bb8480deded301893862acb26f642e09181cbea77fe42d29",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/terminal.html"
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
    "official/install/miniwob/html/miniwob/terminal.html"
  ],
  "selection_order_key": "de326f96f08f9f81c6c0ef9cda5de4c04b43db041cfb729797a05a43a4807cee",
  "selection_rank": 103,
  "source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
  "source_ref": "miniwob://miniwob.terminal",
  "source_sha256": "4a97439f0d2610829e73c761099c7cf27f9ba4207ed1cb8efa4468aa0c504421",
  "static_query_text": null,
  "subdomain": "terminal",
  "task_id": "miniwob.terminal"
}
```

### `official/install/miniwob/html/miniwob/terminal.html`

Source ref: `<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/terminal.html`

```text
<!DOCTYPE html>
<html>
<head>
<title>Terminal Task</title>
<!-- stylesheets -->
<link rel="stylesheet" type="text/css" href="../core/core.css">
<!-- JS -->
<script src="../core/core.js"></script>
<script src="../core/jquery-ui/external/jquery/jquery.js"></script>
<script src="../common/ui_utils.js"></script>

<style>
#terminal { height: 150px; width: 150px; background-color: #000; border-radius: 3px; position: relative;
  font-family: 'Menlo', 'Arial', Serif; font-size: 8px; margin: 2px; }
#terminal-header { height: 10px; width: 150px; background-color: #C9C9C9; text-align: center;
  border-top-left-radius: 3px; border-top-right-radius: 3px; }
#terminal-contents { margin: 3px; height: 135px; overflow-y: scroll; }
#terminal-target { vertical-align: bottom; opacity: 0; color: transparent; height: 1px; width: 1px; }
#active-input { min-width: 0px; display: inline-block; }
#input-flicker { margin-left: -3px; }
.terminal-line { display: block; color: #49F468; }
.terminal-output { display: block; color: #49F468; margin-left: 4px; }
.hide { display: none; }
</style>

<script>
core.EPISODE_MAX_TIME = 20000; // set episode interval to 20s
var TYPABLE_KEYS = '`1234567890-=~!@#$%^&*()_+qwertyuiop[]\\QWERTYUIOP{}|asdfghjkl;\'ASDFGHJKL:"zxcvbnm,./ZXCVBNM<>? ';
var TERMINAL_TEMPLATE =
`
<div id="terminal">
  <div id="terminal-header">terminal</div>
  <div id="terminal-contents">
    <div class="terminal-line">
      <span class="user">user$</span>
      <span id="active-input" class="command"></span>
      <span id="input-flicker">&block;</span>
    </div>
  </div>
</div>
<input type="text" id="terminal-target">
`
var TERMINAL_LINE_TEMPLATE =
`
  <span class="user">user$</span>
  <span class="command"></span>
`
var TERMINAL_OUTPUT_TEMPLATE =
`
  <span class="output"></span>
`
var FILE_NAMES = ['flowers', 'code', 'script', 'bash', 'index', 'image', 'converter', 'file', 'shark', 'memes', 'cats', 'puppy', 'twitter', 'media', 'search', 'page', 'buzzer', 'sys32', 'hack_script', 'delete', 'trace', 'bin', 'emacs', 'vim', 'nano', 'sudo', 'apache', 'mountains', 'steam', 'window', 'nintendo', 'atari', 'sega', 'photos', 'directory', 'container', 'compression', 'cyber', 'digital', 'inspector', 'navigator', 'mozilla', 'netscape', 'thunderbird', 'chrome', 'alloy', 'opera', 'secret', 'secrets', 'password', 'encrypted', 'T-1000', 'skynet', 'mario', 'sonic', 'pizza'];
var FILE_EXTENSIONS = ['png', 'jpg', 'gif', 'sh', 'json', 'txt', 'py', 'rb' , 'html', 'zip', 'tar.gz', '', 'gpg'];

var currentFiles = [];
var currentExtensions = [];
var MAX_FILES = 6;
var pressedKeys = {};
var flicker;

// this takes the current active command line and turns it into an output above
// the command line.
var generateTerminalLine = function(commandInput){
  var div = document.createElement('div');
  div.innerHTML = TERMINAL_LINE_TEMPLATE;
  div.setAttribute('class', 'terminal-line');
  div.getElementsByClassName('command')[0].innerHTML = commandInput;
  $('#active-input').parents('.terminal-line').before(div);
}

// this generates an output line in the terminal
var generateTerminalOutput = function(output){
  var div = document.createElement('div');
  div.innerHTML = TERMINAL_OUTPUT_TEMPLATE;
  div.setAttribute('class', 'terminal-output');
  div.getElementsByClassName('output')[0].innerHTML = output;
  $('#active-input').parents('.terminal-line').before(div);
}

var parseCommand = function(input, expectedDel){
  if(input === 'help'){
    outputHelp();
  } else if(input === ''){
    generateTerminalOutput('');
  } else if(input.indexOf('ls') === 0){
    showFileContents(input);
  } else if(input.indexOf('rm') === 0){
    removeContents(input, expectedDel);
  } else if(input === 'exit'){
    core.endEpisode(-1);
  } else {
    generateTerminalOutput('Command not found.')
  }
}

var outputHelp = function(){
  generateTerminalOutput('ls: list contents');
  generateTerminalOutput('Usage: ls');
  generateTerminalOutput('rm: remove entries');
  generateTerminalOutput('Usage: rm file');
}

var showFileContents = function(input){
  if(input.replace(/\s/g, '') ==='ls'){
    generateTerminalOutput(currentFiles.join(' '));
  } else {
    generateTerminalOutput('error: ls arguments not understood.')
  }
}

var removeContents = function(input, expectedDel){
  if(input.replace(/\s/g, '') ==='rm'){
    generateTerminalOutput('error: file argument not found.')
  } else if(input.indexOf('*') !== -1){
    generateTerminalOutput('error: rm argument \'*\' not supported. please enter the exact file name.')
  } else {
    var commandArgs = input.split(/\s/g);
    var fileInput = commandArgs[1];
    var fileIndex = currentFiles.indexOf(fileInput);
    if(fileIndex === -1){
      generateTerminalOutput('error: file \''+ fileInput +'\' not found.');
    } else {
      currentFiles.splice(fileIndex,1);
      generateTerminalOutput('');

      // remove the file and reward agent based on whether or not their
      // input matches the expected extension.
      if ((fileInput.indexOf(expectedDel) + expectedDel.length) === fileInput.length)
        // reward for deleting a file that has an extension
        core.endEpisode(1, true)
      else if(expectedDel === '' && fileInput.indexOf('.') === -1){
        // reward for deleting a file that has no extension
        core.endEpisode(1, true)
      } else {
        core.endEpisode(-1);
      }
    }
  }
}

var generateFiles = function(){
  var n = core.randi(3,MAX_FILES);
  while(currentFiles.length < n){
    var name = core.sample(FILE_NAMES);
    var ext = core.sample(FILE_EXTENSIONS);
    var filename = name;
    if(ext !== '') filename += '.' + ext;
    // only push file if it doesn't exist, to ensure uniqueness.
    if(currentFiles.indexOf(filename) === -1){
      currentFiles.push(filename);
      currentExtensions.push(ext);
    }
  }
  currentFiles.sort();
}

// ignore key pressed while ctrl/alt/cmd are pressed.
// do *NOT* ignore shift since that's needed for capital letters.
var modifierKeyPressed = function(){
  return pressedKeys[17] ||
    pressedKeys[18] || pressedKeys[91];
}

var onlyExtensionlessFiles = function(){
  var j = 0;
  for(var i=0; i<currentExtensions.length;i++){
    if(currentExtensions[i]!=='') return false;
  }
  return true;
}

var genProblem = function(){
  $('#area').empty();
  var newTerminal = document.createElement('div');
  newTerminal.innerHTML = TERMINAL_TEMPLATE;
  $('#area').append(newTerminal);

  $('#terminal').on('click', function(){
    $('#terminal-target').focus();
  });

  // cause the input caret to flicker.
  clearInterval(flicker);
  flicker = setInterval(function(){
    $('#input-flicker').toggleClass('hide');
  }, 800);

  var currentTime = new Date();
  generateTerminalOutput('Welcome! Type help for a list of available commands.');
  generateTerminalOutput('Last login: ' + currentTime.toDateString());

  currentFiles = [];
  currentExtensions = [];
  generateFiles();

  var expectedExtension = core.sample(currentExtensions);
  if(expectedExtension !== ''){
    $('#query').html('Use the terminal below to delete a file ending with the extension <span class="bold">.' + expectedExtension + '</span>');
  } else {
     $('#query').html('Use the terminal below to delete a file that has <span class="bold">no file extension</span>.');
  }

  $('#terminal-target').on('keyup', function(e){
    pressedKeys[e.keyCode] = null;
  });

  $('#terminal-target').on('keydown', function(e){
    var currentChar = e.key;
    var currentText = $('#active-input').text();

    pressedKeys[e.keyCode] = true;
    if(modifierKeyPressed()) return;

    if(TYPABLE_KEYS.indexOf(currentChar) !== -1){
      // handle typing regular keys
      $('#active-input').append(e.key);
    } else if(e.keyCode === 8){
      // handle delete key
      $('#active-input').text(currentText.substring(0, currentText.length-1));
    } else if (e.keyCode ===13){
      // handle newline/returns
      generateTerminalLine(currentText);
      parseCommand(currentText, expectedExtension);
      $('#active-input').text('');
    }

    $('#terminal-target').val('');
    // scroll down if needed
    $('#terminal-contents').scrollTop($('#terminal-contents').height());
  });

  // autofocus into terminal for convenience.
  setTimeout(function(){$('#terminal-target').select()}, 200);
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
  "case_unit_id": "miniwob.terminal",
  "copied_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/terminal.html",
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
    "derived/selected_task_source.json": "miniwob://miniwob.terminal",
    "official/install/miniwob/html/common/ui_utils.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/terminal.html": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/terminal.html",
    "official/python/browsergym/miniwob/__init__.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
  },
  "official_files": [
    "official/install/miniwob/html/common/ui_utils.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "official/install/miniwob/html/miniwob/terminal.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/terminal.html"
  ],
  "sha256_per_file": {
    "derived/drafting_context.json": "e07c88c9f206ef7f4afbe925e57781bb791d4ecb232f941b1c8aa3dcb886b78d",
    "derived/official_source_excerpts.json": "3e05fd5b84b5f97d483e3825283ef87d2ee6798e95475a12a4db0bb29ef73cdd",
    "derived/selected_task_source.json": "66ad6b8fb08cb7a395f9edf902a342541d410238eb27a7c0b18fce8854516f5c",
    "official/install/miniwob/html/common/ui_utils.js": "65301ee11f483df7e9114f3fac2e2938e8b56933fecbed36bce310e2d8d90368",
    "official/install/miniwob/html/core/core.css": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
    "official/install/miniwob/html/core/core.js": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
    "official/install/miniwob/html/core/jquery-ui/external/jquery/jquery.js": "430f36f9b5f21aae8cc9dca6a81c4d3d84da5175eaedcf2fdc2c226302cb3575",
    "official/install/miniwob/html/miniwob/terminal.html": "693d6df21b79ce13bb8480deded301893862acb26f642e09181cbea77fe42d29",
    "official/python/browsergym/miniwob/__init__.py": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
    "official/python/browsergym/miniwob/all.py": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
    "official/python/browsergym/miniwob/base.py": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
  },
  "source_refs": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/ui_utils.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/jquery-ui/external/jquery/jquery.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/terminal.html",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
    "miniwob://miniwob.terminal",
    "derived://miniwob-pre-run-drafting-context/v1",
    "derived://miniwob-official-source-excerpts/v1"
  ],
  "task_id": "miniwob.terminal"
}
```
