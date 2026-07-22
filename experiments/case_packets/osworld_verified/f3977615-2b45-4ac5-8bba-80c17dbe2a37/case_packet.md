# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `f3977615-2b45-4ac5-8bba-80c17dbe2a37`
- task_id: `f3977615-2b45-4ac5-8bba-80c17dbe2a37`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `vlc`
- snapshot: `chrome`
- related apps: `vlc`
- official instruction: I want to watch two or more videos in same time on VLC. I tried to run multiple instances of VLC. It worked but can't play videos on those new instances. When I play video it plays on first instance instead of new instance.
Is there any way to solve this problem?
- evaluator functions: `check_one_instance_when_started_from_file`
- evaluator conjunction: `and`
- evaluator result getter types: `vlc_config`
- native success: official evaluator score equals `1.0`
- required retained run artifacts: `traj.jsonl`, `result.txt`, `runtime.log`

## Visibility Boundary

This canonical source-rich packet is controller/reviewer-only. The tested agent receives only the instruction in `agent_input.json`; do not place this packet, `raw_case/`, setup commands, evaluator expectations, or expected values in the agent prompt.

## Evaluator Contract

This contract is mechanically extracted from the immutable task JSON and the pinned official Python sources without importing or executing them. The exact evaluator/runtime excerpts below make comparison, threshold, failure, and multi-metric composition semantics locally reviewable.

## Source Inventory

- `derived/evaluator_contract.json`
- `official/desktop_env/desktop_env.py`
- `official/desktop_env/evaluators/getters/__init__.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/getters/vlc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/vlc.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/vlc/f3977615-2b45-4ac5-8bba-80c17dbe2a37.json`

Source SHA-256: `c1e6fd4ea914262c5d3c2eae55293be98ed5e352c94857df7a62e23d52078495`

```json
{
  "config": [
    {
      "parameters": {
        "command": "VLC_VERBOSE=-1 vlc --no-audio --no-video-title-show",
        "shell": true
      },
      "type": "launch"
    },
    {
      "parameters": {
        "command": [
          "python",
          "-c",
          "import pyautogui; import time; pyautogui.click({SCREEN_WIDTH_HALF}, {SCREEN_HEIGHT_HALF}); time.sleep(0.5);"
        ]
      },
      "type": "execute"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "expected_one_instance_when_started_from_file": 0
      },
      "type": "rule"
    },
    "func": "check_one_instance_when_started_from_file",
    "postconfig": [
      {
        "parameters": {
          "command": [
            "pkill",
            "vlc"
          ]
        },
        "type": "launch"
      },
      {
        "parameters": {
          "command": "vlc --no-audio --no-video-title-show",
          "shell": true
        },
        "type": "launch"
      }
    ],
    "result": {
      "dest": "vlcrc",
      "type": "vlc_config"
    }
  },
  "fixed_ip": false,
  "id": "f3977615-2b45-4ac5-8bba-80c17dbe2a37",
  "instruction": "I want to watch two or more videos in same time on VLC. I tried to run multiple instances of VLC. It worked but can't play videos on those new instances. When I play video it plays on first instance instead of new instance.\nIs there any way to solve this problem?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "vlc"
  ],
  "snapshot": "chrome",
  "source": "https://www.reddit.com/r/Fedora/comments/rhljzd/how_to_run_multiple_instances_of_vlc_media_player/",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `ab0c14e8b42bd970c34bc5f990fd4dc78005558fbe4f3b6d20f98d082ba06629`

```json
{
  "conjunction": "and",
  "exact_source_excerpts": [
    {
      "end_line": 414,
      "excerpt_sha256": "852396f1e81e91bbe65eaf5f778082c2728df3b4ac5bf54d2e8e663e67d39340",
      "packet_path": "official/desktop_env/desktop_env.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "source_sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "start_line": 369,
      "symbol": "DesktopEnv._set_evaluator_info",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "end_line": 524,
      "excerpt_sha256": "ad91f9461384454de19eba8c1a65b8165259150f6d222f99183de340cfa90288",
      "packet_path": "official/desktop_env/desktop_env.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "source_sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "start_line": 458,
      "symbol": "DesktopEnv.evaluate",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "56aa754a6cfb9066a41716442ba7d2df1a29a3774ff8d93b89b698fb5711f889",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 2,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "0f278b25d07ad3546253810b64092bd07e25fe69f6e1b4a51382b60d49a8c21b",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 9,
      "symbol": "R",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 96,
      "excerpt_sha256": "c95a18414d0b6fbf5ef16e29eef5fb7aab9e7ae3e48450b97d351503cc3b5182",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 92,
      "symbol": "get_rule",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 2,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 4,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "end_line": 83,
      "excerpt_sha256": "04c15408c0311ff8ab96c153c21edc556457997922a6d70516899b774387329a",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 57,
      "symbol": "get_vlc_config",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 18,
      "excerpt_sha256": "75fc8dffb9f4f69221641e22851433b92ab68c00fe97bed620894c9b05d9c580",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 18,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 528,
      "excerpt_sha256": "3cf4f62031b4cb44fecbdc72c0cdce0625b72815af8eada42e3d4aa1f292c1f3",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 503,
      "symbol": "check_one_instance_when_started_from_file",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "0e077a124299621ac124981e8dd3c75a2a2f2b98bc4de157f313b0e6ce60d292",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "535d40da9ae0e53ee9af20d614e8b3779ee04fab0dffcd5c59ebf33d85f2cfbf",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_one_instance_when_started_from_file",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e"
    }
  ],
  "official_source_files": [
    {
      "packet_path": "official/desktop_env/desktop_env.py",
      "sha256": "ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py",
      "upstream_path": "desktop_env/desktop_env.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/__init__.py",
      "sha256": "a767ec1877446426817ec07ca386f63fc0fff8857a209b99bfa1f93865900754",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/__init__.py",
      "upstream_path": "desktop_env/evaluators/getters/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/__init__.py",
      "sha256": "f8e89039d448b715e99c14a939a566d4148fda3a67a71371a208baa1d6276a08",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/__init__.py",
      "upstream_path": "desktop_env/evaluators/metrics/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "47f5d92b98f286bcf4f6e5fb02b6321ebc9f0c6d09dddc901f4eaab612df857c",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "symbol": "get_vlc_config",
      "type": "vlc_config"
    }
  ],
  "runtime_composition": {
    "agent_fail_on_non_infeasible": "a final FAIL action forces score 0 before getters or metrics run",
    "binding": "metrics are resolved with getattr(metrics, func); getters are resolved with getattr(getters, 'get_' + type)",
    "file_not_found": "single-metric and multi-metric 'and' paths return 0; the official multi-metric 'or' exception path has no explicit return and must be interpreted from the embedded exact source",
    "formal_packet_success": "final evaluator score equals exactly 1.0",
    "infeasible": "when evaluator.func is the string 'infeasible', return 1 only when the last action is FAIL (string or action_type), else 0",
    "multi_metric_and": "evaluate in slot order; return 0 immediately when float(metric) == 0.0; otherwise return the arithmetic mean",
    "multi_metric_or": "evaluate in slot order; return 1 immediately when float(metric) == 1.0; otherwise return the maximum",
    "single_metric": "obtain result state; obtain expected state when configured; call metric(result, expected, **options) or metric(result, **options); return the metric value"
  },
  "schema_version": "osworld_verified_evaluator_contract/v1",
  "task_id": "f3977615-2b45-4ac5-8bba-80c17dbe2a37"
}
```

## Exact Official Evaluator Source Excerpts

### `DesktopEnv._set_evaluator_info` from `official/desktop_env/desktop_env.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py#L369-L414`

Full source SHA-256: `ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1`

Exact excerpt SHA-256: `852396f1e81e91bbe65eaf5f778082c2728df3b4ac5bf54d2e8e663e67d39340`

```python
    def _set_evaluator_info(self, task_config: Dict[str, Any]):
        """Set evaluator information from task config"""
        # evaluator dict
        # func -> metric function string, or list of metric function strings
        # conj -> conjunction of multiple metrics if func is a list with length > 1, "and"/"or"
        # result -> result getter config, or list of result getter configs
        # expected (optional) -> expected getter config, or list of expected getter configs
        # options (optional) -> metric options, or list of metric options
        # if func is a str list, then result, expected (if exists), options (if exists) should also be lists of the same length
        # even if one of the metrics does not need expected or options field, it should be included in the list with None
        self.evaluator = task_config["evaluator"]
        self.metric: Metric = [getattr(metrics, func) for func in self.evaluator["func"]] \
            if isinstance(self.evaluator["func"], list) \
            else getattr(metrics, self.evaluator["func"])
        self.metric_conj: str = self.evaluator.get("conj", "and")  # take conjunction of multiple metrics
        if "result" in self.evaluator and len(self.evaluator["result"]) > 0:
            self.result_getter: Getter = [getattr(getters, "get_{:}".format(res["type"])) for res in
                                          self.evaluator["result"]] \
                if isinstance(self.evaluator["result"], list) \
                else getattr(getters, "get_{:}".format(self.evaluator["result"]["type"]))
        else:
            self.result_getter = [None] * len(self.metric) \
                if isinstance(self.metric, list) \
                else None

        if "expected" in self.evaluator and len(self.evaluator["expected"]) > 0:
            self.expected_getter: Getter = [getattr(getters, "get_{:}".format(exp["type"])) if exp else None for exp in
                                            self.evaluator["expected"]] \
                if isinstance(self.evaluator["expected"], list) \
                else getattr(getters, "get_{:}".format(self.evaluator["expected"]["type"]))
        else:
            self.expected_getter = [None] * len(self.metric) \
                if isinstance(self.metric, list) \
                else None
        self.metric_options: Union[List[Dict[str, Any]], Dict[str, Any]] = [opt if opt else {} for opt in
                                                                            self.evaluator["options"]] \
            if isinstance(self.evaluator.get("options", {}), list) \
            else self.evaluator["options"] \
            if "options" in self.evaluator \
            else [{}] * len(self.metric) \
            if isinstance(self.metric, list) \
            else {}

        assert (not isinstance(self.evaluator["func"], list)
                or (len(self.metric) == len(self.result_getter) == len(self.expected_getter) == len(
                    self.metric_options)))
```

### `DesktopEnv.evaluate` from `official/desktop_env/desktop_env.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/desktop_env.py#L458-L524`

Full source SHA-256: `ff73a546074d4cf3b13259f7261a82af5c3f6942bde27101aa74e58da70d84c1`

Exact excerpt SHA-256: `ad91f9461384454de19eba8c1a65b8165259150f6d222f99183de340cfa90288`

```python
    def evaluate(self):
        """
        Evaluate whether the task is successfully completed.
        """

        postconfig = self.evaluator.get("postconfig", [])
        self.setup_controller.setup(postconfig, self.enable_proxy)
        # Mark environment as used if there were postconfig setup operations
        if postconfig:
            self.is_environment_used = True

        if self.evaluator['func'] == "infeasible":
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                if last_action == "FAIL" or (type(last_action) == dict and last_action.get('action_type') == 'FAIL'):
                    return 1
            return 0
        else:
            if len(self.action_history) > 0:
                last_action = self.action_history[-1]
                if last_action == "FAIL" or (type(last_action) == dict and last_action.get('action_type') == 'FAIL'):
                    return 0

        if type(self.metric) == list:
            # Multiple metrics to evaluate whether the task is successfully completed
            results = []
            assert len(self.metric) == len(self.result_getter), "The number of metrics and result getters must be the same"
            if "expected" in self.evaluator:
                assert len(self.metric) == len(self.expected_getter), "The number of metrics and expected getters must be the same"
            for idx, metric in enumerate(self.metric):
                try:
                    config = self.evaluator["result"][idx]
                    result_state = self.result_getter[idx](self, config)
                except FileNotFoundError:
                    logger.error("File not found!")
                    if self.metric_conj == 'and':
                        return 0

                if "expected" in self.evaluator and self.expected_getter and self.evaluator["expected"]:
                    expected_state = self.expected_getter[idx](self, self.evaluator["expected"][idx])
                    metric: int = metric(result_state, expected_state, **self.metric_options[idx])
                else:
                    metric: int = metric(result_state, **self.metric_options[idx])

                if self.metric_conj == 'and' and float(metric) == 0.0:
                    return 0
                elif self.metric_conj == 'or' and float(metric) == 1.0:
                    return 1
                else:
                    results.append(metric)

            return sum(results) / len(results) if self.metric_conj == 'and' else max(results)
        else:
            # Single metric to evaluate whether the task is successfully completed
            try:
                result_state = self.result_getter(self, self.evaluator["result"])
            except FileNotFoundError:
                logger.error("File not found!")
                return 0

            if "expected" in self.evaluator and self.expected_getter and self.evaluator["expected"]:
                expected_state = self.expected_getter(self, self.evaluator["expected"])
                metric: float = self.metric(result_state, expected_state, **self.metric_options)
            else:
                metric: float = self.metric(result_state, **self.metric_options)

        return metric
```

### `import:Dict` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L2-L2`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `56aa754a6cfb9066a41716442ba7d2df1a29a3774ff8d93b89b698fb5711f889`

```python
from typing import TypeVar, Dict
```

### `R` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L9-L9`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `0f278b25d07ad3546253810b64092bd07e25fe69f6e1b4a51382b60d49a8c21b`

```python
R = TypeVar("Rule")
```

### `get_rule` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L92-L96`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `c95a18414d0b6fbf5ef16e29eef5fb7aab9e7ae3e48450b97d351503cc3b5182`

```python
def get_rule(env, config: Dict[str, R]) -> R:
    """
    Returns the rule as-is.
    """
    return config["rules"]
```

### `import:os` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L2-L2`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:Dict` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L4-L4`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `get_vlc_config` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L57-L83`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `04c15408c0311ff8ab96c153c21edc556457997922a6d70516899b774387329a`

```python
def get_vlc_config(env, config: Dict[str, str]):
    """
    Reads the VLC configuration file to check setting.
    """

    os_type = env.vm_platform

    # fixme: depends on how we config and install the vlc in virtual machine, need to be aligned and double-checked
    if os_type == "Linux":
        config_path = \
            env.controller.execute_python_command("import os; print(os.path.expanduser('~/.config/vlc/vlcrc'))")[
                'output'].strip()
    elif os_type == "Darwin":
        config_path = env.controller.execute_python_command(
            "import os; print(os.path.expanduser('~/Library/Preferences/org.videolan.vlc/vlcrc'))")['output'].strip()
    elif os_type == "Windows":
        config_path = env.controller.execute_python_command(
            "import os; print(os.path.expanduser('~\\AppData\\Roaming\\vlc\\vlcrc'))")['output'].strip()
    else:
        raise Exception("Unsupported operating system", os_type)

    _path = os.path.join(env.cache_dir, config["dest"])
    content = env.controller.get_file(config_path)
    with open(_path, "wb") as f:
        f.write(content)

    return _path
```

### `import:logging` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L1-L1`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `logger` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L18-L18`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `75fc8dffb9f4f69221641e22851433b92ab68c00fe97bed620894c9b05d9c580`

```python
logger = logging.getLogger("desktopenv.metrics.vlc")
```

### `check_one_instance_when_started_from_file` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L503-L528`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `3cf4f62031b4cb44fecbdc72c0cdce0625b72815af8eada42e3d4aa1f292c1f3`

```python
def check_one_instance_when_started_from_file(actual_config_path, rule):
    with open(actual_config_path, 'rb') as file:
        config_file = file.read().decode('utf-8')

    expected_one_instance_when_started_from_file = rule['expected_one_instance_when_started_from_file']

    if isinstance(expected_one_instance_when_started_from_file, int):
        expected_one_instance_when_started_from_file = str(expected_one_instance_when_started_from_file)

    try:
        one_instance_when_started_from_file = "1"
        for line in config_file.split("\n"):
            # Check if the line contains the recording path setting
            if 'one-instance-when-started-from-file=' in line:
                one_instance_when_started_from_file = line.split('=')[-1].strip()

        if one_instance_when_started_from_file == expected_one_instance_when_started_from_file:
            return 1
        else:
            return 0
    except FileNotFoundError:
        logger.error("VLC configuration file not found.")
        return 0
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 0
```
