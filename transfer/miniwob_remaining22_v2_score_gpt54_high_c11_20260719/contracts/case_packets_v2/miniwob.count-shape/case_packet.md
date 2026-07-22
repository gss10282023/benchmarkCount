# Case Packet

## Case Metadata

- domain: `miniwob`
- case_unit_id: `miniwob.count-shape`
- task_id: `miniwob.count-shape`

## Source Inventory

- `derived/drafting_context.json`
- `derived/official_source_excerpts.json`
- `derived/runtime_decision_wiring.json`
- `derived/selected_task_source.json`
- `official/install/miniwob/html/miniwob/count-shape.html`

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
        "sha256": "831613a2189af48050cfddfd460ea1a9398e08c1e2f12cecbc0c8c8908c3d2a5"
      },
      {
        "path": "src/evidence_system/adapters/miniwob.py",
        "sha256": "2084e2a01a12ecc0a998dffc98c0143e89336e1f256b498f91e1b003a1748c35"
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
  "case_unit_id": "miniwob.count-shape",
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
      "official/install/miniwob/html/miniwob/count-shape.html::genProblem"
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
    "failure_evidence_rule": "Retained evidence supports native failure only for a benchmark-counted completed record when it establishes an invalid page/URL or the final validation after the locked action budget does not meet native success: done is false or binary reward is 0.0.",
    "native_semantics": "Invalid page or URL returns reward 0 and terminates. Otherwise validate reads the WOB state and returns binary reward float(RAW_REWARD_GLOBAL > 0) with DONE_GLOBAL.",
    "record_scope_rule": "The worker emits status completed only after writing final validation artifacts. The adapter maps such a record to native success/fail from summary.success; a non-completed worker record is INFRA_EXCLUDED with no native label and is outside S/F/U evidence scoring.",
    "success_evidence_rule": "Retained evidence supports native success when it establishes a valid final validation with done true and binary reward 1.0, grounded in the task oracle's positive raw reward.",
    "summary_field_guard": "Do not treat a summary-only success/label field as decisive; inspect concrete validator reward, done, info, trace, and retained state.",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods.validate.content",
      "derived/official_source_excerpts.json::excerpts.core_reward_wiring.content",
      "official/install/miniwob/html/miniwob/count-shape.html::genProblem",
      "derived/runtime_decision_wiring.json::excerpts.worker_run_smoke_job.content",
      "derived/runtime_decision_wiring.json::excerpts.adapter_execute_smoke_job.content"
    ],
    "task_class": "CountShapeTask"
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
  "task_id": "miniwob.count-shape",
  "task_text": {
    "benchmark": "MiniWoB++",
    "runtime_goal_note": "Episode values vary by seed. Freeze a parameterized rule over the runtime-issued goal; do not insert a future episode's target value into the pre-run checklist.",
    "runtime_goal_source": "observation.goal at environment reset",
    "static_query_text": null,
    "static_title": "Count Shape Task",
    "subdomain": "count-shape",
    "support": [
      "derived/official_source_excerpts.json::excerpts.base_validator.methods._get_goal.content",
      "official/install/miniwob/html/miniwob/count-shape.html::genProblem"
    ],
    "task_id": "miniwob.count-shape"
  }
}
```

### `derived/official_source_excerpts.json`

Source ref: `derived from byte-pinned official MiniWoB++ sources`

```json
{
  "case_unit_id": "miniwob.count-shape",
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
      "content": "class CountShapeTask(AbstractMiniwobTask):\n    desc = \"Count number of shapes.\"\n    subdomain = \"count-shape\"",
      "end_line": 263,
      "fallback": false,
      "start_line": 261
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
      "byte_count": 2791,
      "path": "official/install/miniwob/html/miniwob/count-shape.html",
      "sha256": "49781534a3f1cdb34090c607987add8053f556934362cd3855da37cc8c3f0bf2"
    }
  },
  "task_id": "miniwob.count-shape"
}
```

### `derived/runtime_decision_wiring.json`

Source ref: `deterministic exact excerpts from the locked MiniWoB worker and adapter`

```json
{
  "case_unit_id": "miniwob.count-shape",
  "excerpts": {
    "adapter_execute_smoke_job": {
      "content": "def execute_smoke_job(\n    job: dict[str, Any],\n    *,\n    target: \"InfraBenchmarkTarget\",\n    execution_plan: dict[str, Any],\n    context: \"SmokeExecutionContext\",\n) -> dict[str, Any]:\n    paths = build_job_paths(job)\n    _ensure_remote_http_server(target, paths.logs_dir)\n    formal_control = dict(execution_plan.get(\"formal_worker_control\") or {})\n    if formal_control:\n        if formal_control.get(\"support_files_pre_synced_and_locked\") is not True:\n            raise RuntimeError(\"formal MiniWoB worker lacks the post-gate sync prohibition\")\n    else:\n        sync_repo_support_files(target)\n    _, environment_hash = write_environment_snapshot(target=target, job=job, output_path=paths.environment_path)\n    shutil.rmtree(paths.native_run_dir, ignore_errors=True)\n    paths.native_run_dir.mkdir(parents=True, exist_ok=True)\n\n    remote_output_dir = _remote_output_dir(target, job)\n    run_remote_command(\n        target,\n        f\"rm -rf {shlex.quote(remote_output_dir)} && mkdir -p {shlex.quote(remote_output_dir)}\",\n        stdout_path=paths.logs_dir / \"prepare.stdout.log\",\n        stderr_path=paths.logs_dir / \"prepare.stderr.log\",\n    )\n    started_at = utc_now_iso()\n    completed = _run_worker_command(\n        target=target,\n        execution_plan=execution_plan,\n        stdout_path=paths.stdout_log,\n        stderr_path=paths.stderr_log,\n        termination_stdout_path=paths.logs_dir / \"formal_worker_termination.stdout.log\",\n        termination_stderr_path=paths.logs_dir / \"formal_worker_termination.stderr.log\",\n    )\n    ended_at = utc_now_iso()\n    artifact_fetch_timeout = (\n        int(formal_control.get(\"artifact_fetch_timeout_seconds\") or 0)\n        if formal_control\n        else None\n    )\n    if formal_control and artifact_fetch_timeout <= 0:\n        raise RuntimeError(\"formal MiniWoB worker lacks a bounded artifact fetch timeout\")\n    if formal_control:\n        rsync_remote_tree(\n            target,\n            remote_output_dir,\n            paths.native_run_dir,\n            timeout_seconds=artifact_fetch_timeout,\n        )\n    else:\n        rsync_remote_tree(target, remote_output_dir, paths.native_run_dir)\n\n    summary_path = paths.native_run_dir / \"run_summary.json\"\n    if not summary_path.exists():\n        raise RuntimeError(f\"MiniWoB++ worker did not produce run_summary.json for {job['job_id']}\")\n    summary = json.loads(summary_path.read_text(encoding=\"utf-8\"))\n    if _retryable_worker_error(summary):\n        raise RuntimeError(str(summary.get(\"error_message\") or \"MiniWoB++ worker transient error\"))\n\n    llm_path, _ = write_llm_call_logs(\n        events=_miniwob_llm_events(paths.native_run_dir),\n        job=job,\n        context=context,\n        output_dir=paths.llm_dir,\n    )\n    completed_status = summary.get(\"status\") == \"completed\"\n    status = \"COMPLETED\" if completed_status else \"INFRA_EXCLUDED\"\n    native_label = None\n    native_score = None\n    if completed_status:\n        success = bool(summary.get(\"success\"))\n        native_label = \"success\" if success else \"fail\"\n        native_score = 1.0 if success else 0.0\n\n    descriptors = _miniwob_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)\n    manifest, manifest_path, manifest_sha = build_artifact_manifest(\n        job=job,\n        context=context,\n        target=target,\n        descriptors=descriptors,\n        producer_command=str(execution_plan[\"runner_command\"]),\n        started_at=started_at,\n        output_path=paths.artifact_manifest_path,\n        environment_hash=environment_hash,\n    )\n    raw_run, raw_run_path = build_raw_run(\n        job=job,\n        target=target,\n        artifact_manifest_path=manifest_path,\n        artifact_manifest_sha256=manifest_sha,\n        raw_run_path=paths.raw_run_path,\n        started_at=started_at,\n        ended_at=ended_at,\n        status=status,\n        diagnostic_status=\"completed\" if completed_status else \"infra_excluded\",\n        appendix_failure_class=\"none\" if completed_status else \"infra_pre_run\",\n        native_label=native_label,\n        native_score=native_score,\n        episode_ids=[f\"miniwob:{summary.get('env_id') or job['task_id']}:{job['seed']}\"],\n        llm_calls_log_path=llm_path,\n    )\n    return {\n        \"status\": \"completed\" if completed_status else \"infra_excluded\",\n        \"completed_exit_code\": completed.returncode,\n        \"raw_run_path\": str(raw_run_path),\n        \"artifact_manifest_path\": str(manifest_path),\n        \"raw_run\": raw_run,\n        \"artifact_manifest\": manifest,\n    }",
      "end_line": 293,
      "fallback": false,
      "start_line": 184
    },
    "worker_run_smoke_job": {
      "content": "def run_smoke_job(config: MiniWoBSmokeConfig) -> dict[str, Any]:\n    if config.output_dir.exists():\n        shutil.rmtree(config.output_dir)\n    _artifact_dirs(config.output_dir)\n\n    _write_json(config.output_dir / \"job.json\", config.job)\n    _write_json(config.output_dir / \"source_bundle_entry.json\", config.source_entry)\n    _write_json(config.output_dir / \"worker_config.json\", _jsonable(asdict(config)))\n\n    summary: dict[str, Any] = {\n        \"status\": \"running\",\n        \"job_id\": str(config.job.get(\"job_id\") or \"\"),\n        \"task_id\": config.task_id,\n        \"driver\": config.driver,\n        \"model\": config.model,\n        \"base_url\": config.base_url,\n    }\n    _write_json(config.output_dir / \"run_summary.json\", summary)\n\n    env = None\n    task_context: dict[str, Any] | None = None\n    task_state_initial: dict[str, Any] | None = None\n    task_state_final: dict[str, Any] | None = None\n    final_validation: dict[str, Any] | None = None\n    steps: list[dict[str, Any]] = []\n    last_task_info: dict[str, Any] = {}\n    truncated = False\n    error: Exception | None = None\n\n    try:\n        task_kwargs = _task_kwargs_from_source(config.source_entry, base_url=config.base_url)\n        action_set = _build_action_set()\n        action_space_description = action_set.describe(with_long_description=False, with_examples=True)\n\n        env = _make_miniwob_env(config=config, task_kwargs=task_kwargs, action_set=action_set)\n        obs, reset_info = env.reset(seed=int(config.job.get(\"seed\", 0)))\n        raw = env.unwrapped\n        chat_messages = _chat_messages(raw)\n\n        task_state_initial = _task_state_payload(raw.task)\n        initial_validation = _validation_payload(raw.task.validate(raw.page, chat_messages))\n        last_task_info = dict(reset_info.get(\"task_info\") or {})\n        task_context = _task_context_payload(\n            config=config,\n            raw_env=raw,\n            reset_info=reset_info,\n            initial_observation=obs,\n            task_kwargs=task_kwargs,\n            action_space_description=action_space_description,\n        )\n\n        _write_json(config.output_dir / \"task_context.json\", task_context)\n        _write_json(config.output_dir / \"task_artifacts\" / \"reset_info.json\", reset_info)\n        _write_json(config.output_dir / \"task_artifacts\" / \"task_state_initial.json\", task_state_initial)\n        _write_json(config.output_dir / \"task_artifacts\" / \"validation_initial.json\", initial_validation)\n        _write_json(\n            config.output_dir / \"task_artifacts\" / \"policy_workflow.json\",\n            {\n                \"goal\": task_context.get(\"goal\"),\n                \"base_url\": task_context.get(\"base_url\"),\n                \"source_ref\": task_context.get(\"source_ref\"),\n                \"runtime_goal_note\": task_context.get(\"runtime_goal_note\"),\n                \"task_kwargs\": task_kwargs,\n            },\n        )\n        _capture_browser_state(config.output_dir, raw.page, obs, label=\"step_000_reset\")\n\n        latest_obs = obs\n        reward = 0.0\n        terminated = False\n\n        api_key = os.environ.get(config.openrouter_api_key_env)\n        if not api_key:\n            raise RuntimeError(f\"missing environment variable {config.openrouter_api_key_env}\")\n        if not config.model:\n            raise RuntimeError(\"model is required for openrouter_chat driver\")\n        if config.driver != DRIVER_OPENROUTER_CHAT:\n            raise RuntimeError(f\"unsupported MiniWoB++ driver: {config.driver}\")\n\n        for step_index in range(1, max(1, config.max_steps) + 1):\n            step_prompt = build_step_prompt(\n                config=config,\n                observation=latest_obs,\n                step_index=step_index,\n                action_space_description=action_space_description,\n                previous_steps=steps,\n            )\n            request_messages = [\n                {\"role\": \"system\", \"content\": SYSTEM_PROMPT},\n                {\"role\": \"user\", \"content\": step_prompt},\n            ]\n            request_payload = {\n                \"model\": config.model,\n                \"messages\": request_messages,\n                \"temperature\": config.temperature,\n                \"max_tokens\": config.max_tokens,\n            }\n            provider_routing = None\n            if config.openrouter_provider_only:\n                provider_routing = {\n                    \"only\": [config.openrouter_provider_only],\n                    \"allow_fallbacks\": False,\n                }\n                request_payload[\"provider\"] = provider_routing\n\n            response_payload = None\n            response_content = None\n            request_timestamp = _utc_now_iso()\n            response_timestamp = request_timestamp\n            request_error: Exception | None = None\n            for provider_attempt in range(config.retry + 1):\n                request_timestamp = _utc_now_iso()\n                try:\n                    response_payload = request_openrouter_completion(\n                        api_key=api_key,\n                        model=config.model,\n                        messages=request_messages,\n                        temperature=config.temperature,\n                        max_tokens=config.max_tokens,\n                        timeout_seconds=config.timeout_seconds,\n                        retry=0,\n                        provider_routing=provider_routing,\n                    )\n                    response_timestamp = _utc_now_iso()\n                    response_content = extract_response_content(response_payload)\n                    if not response_content.strip():\n                        raise RuntimeError(\"OpenRouter response content is empty\")\n                except Exception as exc:\n                    request_error = exc\n                    response_timestamp = _utc_now_iso()\n                    _write_openrouter_call(\n                        path=(\n                            config.output_dir\n                            / \"openrouter_calls\"\n                            / \"retry_attempts\"\n                            / f\"call-{step_index:04d}-attempt-{provider_attempt + 1:04d}.json\"\n                        ),\n                        call_id=f\"call-{step_index:04d}-attempt-{provider_attempt + 1:04d}\",\n                        request_timestamp=request_timestamp,\n                        response_timestamp=response_timestamp,\n                        request_payload=request_payload,\n                        response_payload=response_payload,\n                        action_text=\"\",\n                        python_code=None,\n                        error_type=type(exc).__name__,\n                        error_message=str(exc),\n                    )\n                    if provider_attempt < config.retry:\n                        continue\n                else:\n                    request_error = None\n                break\n\n            if request_error is not None:\n                _write_openrouter_call(\n                    path=config.output_dir / \"openrouter_calls\" / f\"call-{step_index:04d}.json\",\n                    call_id=f\"call-{step_index:04d}\",\n                    request_timestamp=request_timestamp,\n                    response_timestamp=response_timestamp,\n                    request_payload=request_payload,\n                    response_payload=response_payload,\n                    action_text=\"\",\n                    python_code=None,\n                    error_type=type(request_error).__name__,\n                    error_message=str(request_error),\n                )\n                raise request_error\n            if response_payload is None or response_content is None:\n                raise RuntimeError(\"OpenRouter retry loop ended without a response\")\n            action_text = extract_action_text(response_content)\n            python_code = None\n            parse_error = None\n            try:\n                python_code = action_set.to_python_code(action_text)\n            except Exception as exc:\n                parse_error = f\"{type(exc).__name__}: {exc}\"\n\n            _write_openrouter_call(\n                path=config.output_dir / \"openrouter_calls\" / f\"call-{step_index:04d}.json\",\n                call_id=f\"call-{step_index:04d}\",\n                request_timestamp=request_timestamp,\n                response_timestamp=response_timestamp,\n                request_payload=request_payload,\n                response_payload=response_payload,\n                action_text=action_text,\n                python_code=python_code,\n                error_type=\"ActionParseError\" if parse_error else None,\n                error_message=parse_error,\n            )\n\n            latest_obs, reward, terminated, truncated, info = env.step(action_text)\n            last_task_info = dict(info.get(\"task_info\") or {})\n            step_label = f\"step_{step_index:03d}\"\n            _capture_browser_state(config.output_dir, raw.page, latest_obs, label=step_label)\n            steps.append(\n                {\n                    \"step_index\": step_index,\n                    \"driver\": config.driver,\n                    \"action\": action_text,\n                    \"python_code\": python_code,\n                    \"parse_error\": parse_error,\n                    \"reward\": reward,\n                    \"terminated\": terminated,\n                    \"truncated\": truncated,\n                    \"task_info\": _jsonable(last_task_info),\n                    \"observation_path\": f\"trajectory/observations/{step_label}.json\",\n                    \"screenshot_path\": f\"browser_artifacts/screenshots/{step_label}.png\",\n                    \"html_path\": f\"browser_artifacts/page_html/{step_label}.html\",\n                }\n            )\n            if terminated or truncated:\n                break\n\n        final_validation = _validation_payload(raw.task.validate(raw.page, _chat_messages(raw)))\n        task_state_final = _task_state_payload(raw.task)\n        _write_json(config.output_dir / \"task_artifacts\" / \"task_state_final.json\", task_state_final)\n        _write_json(config.output_dir / \"task_artifacts\" / \"validation_final.json\", final_validation)\n        _write_json(config.output_dir / \"task_artifacts\" / \"task_info_final.json\", last_task_info)\n        _write_json(config.output_dir / \"task_artifacts\" / \"chat_messages_final.json\", _chat_messages(raw))\n        _write_json(config.output_dir / \"trajectory\" / \"steps.json\", steps)\n\n        native_evaluator_input = _native_evaluator_input_payload(\n            config=config,\n            task_context=task_context,\n            task_kwargs=task_kwargs,\n            initial_validation=initial_validation,\n        )\n        _write_json(config.output_dir / \"native_evaluator_input.json\", native_evaluator_input)\n        native_evaluator_output = _native_evaluator_output_payload(\n            config=config,\n            task_context=task_context,\n            final_validation=final_validation,\n            steps=steps,\n        )\n        _write_json(config.output_dir / \"native_evaluator_output.json\", native_evaluator_output)\n\n        success = bool(final_validation.get(\"done\")) and float(final_validation.get(\"reward\") or 0.0) >= 1.0\n        summary.update(\n            {\n                \"status\": \"completed\",\n                \"env_id\": task_context[\"env_id\"],\n                \"goal\": task_context[\"goal\"],\n                \"success\": success,\n                \"task_class\": task_context[\"task_class\"],\n                \"step_count\": len(steps),\n                \"terminated\": bool(final_validation.get(\"done\")),\n                \"truncated\": bool(truncated),\n                \"final_reward\": float(final_validation.get(\"reward\") or 0.0),\n                \"final_validation_message\": final_validation.get(\"message\"),\n                \"recording_file\": reset_info.get(\"recording_file\"),\n                \"chat_recording_file\": ((reset_info.get(\"chat\") or {}).get(\"recording_file\") if isinstance(reset_info.get(\"chat\"), Mapping) else None),\n            }\n        )\n    except Exception as exc:\n        error = exc\n        summary.update(\n            {\n                \"status\": \"error\",\n                \"error_type\": type(exc).__name__,\n                \"error_message\": str(exc),\n                \"traceback\": traceback.format_exc(),\n            }\n        )\n    finally:\n        close_error = None\n        if env is not None:\n            close_error = _close_env_with_timeout(\n                env, timeout_seconds=ENV_CLOSE_TIMEOUT_SECONDS\n            )\n        summary[\"environment_close_timeout_seconds\"] = ENV_CLOSE_TIMEOUT_SECONDS\n        if close_error:\n            summary[\"close_error\"] = close_error\n        _write_json(config.output_dir / \"artifact_manifest.json\", _worker_artifact_manifest(config.output_dir))\n        summary[\"artifact_manifest_path\"] = str(config.output_dir / \"artifact_manifest.json\")\n        _write_json(config.output_dir / \"run_summary.json\", summary)\n\n    if error is not None:\n        raise error\n    return summary",
      "end_line": 393,
      "fallback": false,
      "start_line": 115
    }
  },
  "extraction": {
    "contains_agent_outcomes": false,
    "method": "deterministic exact Python AST function excerpts from locked local producer sources"
  },
  "schema_version": "miniwob_runtime_decision_wiring/v1",
  "source_inventory": {
    "adapter": {
      "byte_count": 21661,
      "path": "src/evidence_system/adapters/miniwob.py",
      "sha256": "2084e2a01a12ecc0a998dffc98c0143e89336e1f256b498f91e1b003a1748c35"
    },
    "worker": {
      "byte_count": 27806,
      "path": "src/evidence_system/adapters/miniwob_worker.py",
      "sha256": "831613a2189af48050cfddfd460ea1a9398e08c1e2f12cecbc0c8c8908c3d2a5"
    }
  },
  "task_id": "miniwob.count-shape"
}
```

### `derived/selected_task_source.json`

Source ref: `miniwob://miniwob.count-shape`

```json
{
  "base_class_name": "AbstractMiniwobTask",
  "base_module": "browsergym.miniwob.base",
  "base_source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
  "case_unit_id": "miniwob.count-shape",
  "class_name": "CountShapeTask",
  "html_asset_files": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/shapes.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js"
  ],
  "html_file": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/count-shape.html",
  "html_title": "Count Shape Task",
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
      "archive_path": "official/install/miniwob/html/miniwob/count-shape.html",
      "sha256": "49781534a3f1cdb34090c607987add8053f556934362cd3855da37cc8c3f0bf2",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/count-shape.html"
    },
    {
      "archive_path": "official/install/miniwob/html/common/shapes.js",
      "sha256": "0160839b9695cef26de53625170a3f4a01dbb6a474ec8fb81a4d6b058dc0d7c0",
      "source_path": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/shapes.js"
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
    }
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/runtime_decision_wiring.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/count-shape.html"
  ],
  "selection_order_key": "e7b1e4d5df5edc251fa5deda5d2a7aea68b9ccd547f071d7028d8332defc958d",
  "selection_rank": 111,
  "source_file": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
  "source_ref": "miniwob://miniwob.count-shape",
  "source_sha256": "3fdf598a2c541db5a7b7c1a29d439e98cff3372228a39494c45e92c4281a96c7",
  "static_query_text": null,
  "subdomain": "count-shape",
  "task_id": "miniwob.count-shape"
}
```

### `official/install/miniwob/html/miniwob/count-shape.html`

Source ref: `<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/count-shape.html`

```text
<!DOCTYPE html>
<html>
<head>
<title>Count Shape Task</title>
<!-- stylesheets -->
<link rel="stylesheet" type="text/css" href="../core/core.css">
<!-- JS -->
<script src="../core/core.js"></script>
<script src="../core/d3.v3.min.js"></script>
<script src="../common/shapes.js"></script>

<style>
#area { position: relative; height: 154px; width: 154px; }
#area_svg { width: 154px; height: 130px; }
#count-buttons { position: absolute; left: 6px; bottom: 2px; }
#count-buttons button { margin: 0 2px; }
button { width: 25px; }
</style>

<script>
shapes.SZ_Y = 6;
shapes.MAX_NUM_SHAPES = 10; // override variables from shapes.js (since counting is hard)

var createGrid = function(){
  // generate a new random grid of shapes
  d3.select('#count-buttons').html('');
  var grid = shapes.genGrid();
  var svg_elt = d3.select('#area_svg');
  shapes.renderGrid(svg_elt, grid); // instantiate the actual SVG shapes

  return grid;
}

var chooseShape = function(grid){
  // generate the problem instance
  if(core.randf(0,1) < 0.3) {
    var gtdesc = shapes.sampleDesc(); // answer could be 0
  } else {
    var gtix = core.randi(0, grid.shapes.length); // answer is 1+
    var gtdesc = shapes.generalDesc(grid.shapes[gtix]);
  }
  var gtshapes = grid.shapes.filter(function(x) { return shapes.shapeMatchesText(x, gtdesc); });

  return { gtdesc: gtdesc, gtshapes: gtshapes };
}

var bindClickEvents = function(grid, problemSet, query){
  var gtix = core.randi(0,5);
  var used = {};
  for(var query=0;query<5;query++) {
    if(gtix === query) {
      var c = problemSet.gtshapes.length; // true answer
    } else {
      while(true) {
        var c = core.randi(0,10);
        if(c !== problemSet.gtshapes.length && !used.hasOwnProperty(c)) { used[c] = 1; break; }
      }
    }
    // attach button and create a click handler
    var btn = d3.select('#count-buttons').append('button').html(c);
    var click_reward = gtix === query ? 1.0 : -1.0;
    btn.on('click', function(x) {
      return function(){ core.endEpisode(x, x > 0); d3.event.stopPropagation(); }
    }(click_reward)); // close over click_reward
  }

  // attach chandler to default click in random spot (penalize)
  grid.svg.on('click', function(){ core.endEpisode(-1); });
}

// create a problem instance
var genProblem = function() {
  var grid = createGrid();
  var problemSet = chooseShape(grid);
  var q = d3.select('#query').html('')

  q.append('div').html('How many ' + problemSet.gtdesc.text + 's are there?');
  var d = q.append('div');
  bindClickEvents(grid, problemSet, q);
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
    <svg id="area_svg"></svg>
    <div id="count-buttons">
    </div>
  </div>
</div>
</body>
</html>
```

## Raw Source Provenance

```json
{
  "case_unit_id": "miniwob.count-shape",
  "copied_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/runtime_decision_wiring.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/common/shapes.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/miniwob/count-shape.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "derived_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/runtime_decision_wiring.json",
    "derived/selected_task_source.json"
  ],
  "domain": "miniwob",
  "file_sources": {
    "derived/drafting_context.json": "src/evidence_system/contracts/case_packets.py::_miniwob_drafting_context",
    "derived/official_source_excerpts.json": "derived from byte-pinned official MiniWoB++ sources",
    "derived/runtime_decision_wiring.json": "deterministic exact excerpts from the locked MiniWoB worker and adapter",
    "derived/selected_task_source.json": "miniwob://miniwob.count-shape",
    "official/install/miniwob/html/common/shapes.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/shapes.js",
    "official/install/miniwob/html/core/core.css": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js": "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/miniwob/count-shape.html": "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/count-shape.html",
    "official/python/browsergym/miniwob/__init__.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py": "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py"
  },
  "official_files": [
    "official/install/miniwob/html/common/shapes.js",
    "official/install/miniwob/html/core/core.css",
    "official/install/miniwob/html/core/core.js",
    "official/install/miniwob/html/core/d3.v3.min.js",
    "official/install/miniwob/html/miniwob/count-shape.html",
    "official/python/browsergym/miniwob/__init__.py",
    "official/python/browsergym/miniwob/all.py",
    "official/python/browsergym/miniwob/base.py"
  ],
  "packet_files": [
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/runtime_decision_wiring.json",
    "derived/selected_task_source.json",
    "official/install/miniwob/html/miniwob/count-shape.html"
  ],
  "sha256_per_file": {
    "derived/drafting_context.json": "c685885921a7d856a02ca13749f380cc30555df641774052363e8797276c726e",
    "derived/official_source_excerpts.json": "7dcefdc1049fdb5c5242b2fd622663fe7918ccf42c1568feff6775302d7bdd8c",
    "derived/runtime_decision_wiring.json": "dd3304948493776f64747f65f263e007eca74fd832c4413f03d3eafb4984b4b8",
    "derived/selected_task_source.json": "3ed30d3b6454b30eb82a32273e3355fbdfc9892885a7d1b32f9da73fa9ac810e",
    "official/install/miniwob/html/common/shapes.js": "0160839b9695cef26de53625170a3f4a01dbb6a474ec8fb81a4d6b058dc0d7c0",
    "official/install/miniwob/html/core/core.css": "795f8e686125b71e89a21ffe9e03406c6498f1e135175ba63321f3051a720042",
    "official/install/miniwob/html/core/core.js": "db8f489ab947a3194b99e718bce5e59ea9aaf0a3c35410d8c9c79e56e6123d14",
    "official/install/miniwob/html/core/d3.v3.min.js": "8ca4da6691fb142cd76283014e887e7c3e61e3b63eff9ebb08eeb5c51d56aafb",
    "official/install/miniwob/html/miniwob/count-shape.html": "49781534a3f1cdb34090c607987add8053f556934362cd3855da37cc8c3f0bf2",
    "official/python/browsergym/miniwob/__init__.py": "f4656f0eaa35b350c57a0de701d7f6f65fe241cdbdb1713ea32652010bd430cb",
    "official/python/browsergym/miniwob/all.py": "25c6ed2960494808e12d5a178290289e63f81eee328a0f47b384a66d53531b98",
    "official/python/browsergym/miniwob/base.py": "4d7b82b7b63403a9774969f4166ab858243bef381335ae1af3ced345e66552ab"
  },
  "source_refs": [
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/common/shapes.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.css",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/d3.v3.min.js",
    "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/count-shape.html",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
    "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
    "miniwob://miniwob.count-shape",
    "derived://miniwob-pre-run-drafting-context/v1",
    "derived://miniwob-official-source-excerpts/v1"
  ],
  "task_id": "miniwob.count-shape"
}
```
