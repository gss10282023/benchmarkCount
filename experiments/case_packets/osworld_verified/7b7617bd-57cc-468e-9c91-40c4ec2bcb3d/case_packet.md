# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `7b7617bd-57cc-468e-9c91-40c4ec2bcb3d`
- task_id: `7b7617bd-57cc-468e-9c91-40c4ec2bcb3d`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `gimp`
- snapshot: `gimp`
- related apps: `gimp`
- official instruction: Set the minimum number of undo steps to 100.
- evaluator functions: `check_config_status`
- evaluator conjunction: `and`
- evaluator result getter types: `gimp_config_file`
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
- `official/desktop_env/evaluators/getters/gimp.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/gimp.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d.json`

Source SHA-256: `873a5f795b810c689d2903f28cf1a10f93b7add03aefead1d4fc6a77571d7778`

```json
{
  "config": [
    {
      "parameters": {
        "command": [
          "gimp"
        ]
      },
      "type": "launch"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "key": "undo-levels",
        "type:": "key-value",
        "value": "100"
      },
      "type": "rule"
    },
    "func": "check_config_status",
    "postconfig": [
      {
        "parameters": {
          "command": [
            "python3",
            "-c",
            "import time; import pyautogui; time.sleep(1);pyautogui.hotkey([\"ctrl\", \"q\"]);"
          ]
        },
        "type": "execute"
      },
      {
        "parameters": {
          "seconds": 0.5
        },
        "type": "sleep"
      }
    ],
    "result": {
      "dest": "gimprc",
      "file_name": "gimprc",
      "type": "gimp_config_file"
    }
  },
  "fixed_ip": false,
  "id": "7b7617bd-57cc-468e-9c91-40c4ec2bcb3d",
  "instruction": "Set the minimum number of undo steps to 100.",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "gimp"
  ],
  "snapshot": "gimp",
  "source": "https://www.youtube.com/watch?v=G_PjQAy0iiU",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `4ff5f3578d6ca6f8a5963e73a66a19b94e62e032898c192b81a95aebce70fff8`

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
      "end_line": 1,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "start_line": 2,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "start_line": 3,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "b048ee0343a303074f7da7c15540287ebf3ea9224a4e7f3e8ee9e3712a84c4b9",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "start_line": 5,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
    },
    {
      "end_line": 38,
      "excerpt_sha256": "ed7f98a7a345cb0a56730e590e66e428cc7dbe27ab95f7281ba85024c9b41a8a",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "start_line": 8,
      "symbol": "get_gimp_config_file",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
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
      "end_line": 539,
      "excerpt_sha256": "7ffa7d2f8965dbecc05132cdc03f63003fbc967b92520baf3da4c0de45a9ae54",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "start_line": 517,
      "symbol": "check_config_status",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "207aae0a4fe5c19fb6c881a5d1d3ca1959577bae4abc318c6e2427da79ba8db9",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "55f26398410354753dee47dc5b27800656e02b9d7872ea9b3d79a3704b3fc35a",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_config_status",
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "source_sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346"
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
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "upstream_path": "desktop_env/evaluators/getters/gimp.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/__init__.py",
      "sha256": "f8e89039d448b715e99c14a939a566d4148fda3a67a71371a208baa1d6276a08",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/__init__.py",
      "upstream_path": "desktop_env/evaluators/metrics/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/gimp.py",
      "sha256": "c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py",
      "upstream_path": "desktop_env/evaluators/metrics/gimp.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "381ee5310e4a665cf2eb204da0eccb9c574fa065a53dc3da912d2813a454ea91",
      "packet_path": "official/desktop_env/evaluators/getters/gimp.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py",
      "source_sha256": "cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340",
      "symbol": "get_gimp_config_file",
      "type": "gimp_config_file"
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
  "task_id": "7b7617bd-57cc-468e-9c91-40c4ec2bcb3d"
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

### `import:logging` from `official/desktop_env/evaluators/getters/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py#L1-L1`

Full source SHA-256: `cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:os` from `official/desktop_env/evaluators/getters/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py#L2-L2`

Full source SHA-256: `cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:Dict` from `official/desktop_env/evaluators/getters/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py#L3-L3`

Full source SHA-256: `cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `logger` from `official/desktop_env/evaluators/getters/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py#L5-L5`

Full source SHA-256: `cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340`

Exact excerpt SHA-256: `b048ee0343a303074f7da7c15540287ebf3ea9224a4e7f3e8ee9e3712a84c4b9`

```python
logger = logging.getLogger("desktopenv.getters.gimp")
```

### `get_gimp_config_file` from `official/desktop_env/evaluators/getters/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/gimp.py#L8-L38`

Full source SHA-256: `cbcde5e3cc040d9682180a5dfcb0193116f1743afae60a502ab1a05f54e1f340`

Exact excerpt SHA-256: `ed7f98a7a345cb0a56730e590e66e428cc7dbe27ab95f7281ba85024c9b41a8a`

```python
def get_gimp_config_file(env, config: Dict[str, str]):
    """
    Gets the config setting of GIMP.
    """

    os_type = env.vm_platform
    print(os_type)

    if os_type == "Linux":
        config_path = \
            env.controller.execute_python_command(f"import os; print("
                                                  f"os"
                                                  f".path.expanduser("
                                                  f"'~/.config/GIMP/2.10/"
                                                  f"{config['file_name']}'))")[
                'output'].strip()
    # TODO: Add support for macOS and Windows
    else:
        raise Exception("Unsupported operating system", os_type)

    _path = os.path.join(env.cache_dir, config["dest"])
    content = env.controller.get_file(config_path)

    if not content:
        logger.error("Failed to get GIMP config file.")
        return None

    with open(_path, "wb") as f:
        f.write(content)

    return _path
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

### `check_config_status` from `official/desktop_env/evaluators/metrics/gimp.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/gimp.py#L517-L539`

Full source SHA-256: `c0aeea13928927a97e06a15088d6049cef7a8dfdc9251203badbb6f17f931346`

Exact excerpt SHA-256: `7ffa7d2f8965dbecc05132cdc03f63003fbc967b92520baf3da4c0de45a9ae54`

```python
def check_config_status(actual_config_path, rule):
    """
    Check if the GIMP status is as expected
    """
    if actual_config_path is None:
        return 0.

    with open(actual_config_path, 'r') as f:
        content = f.readlines()

    for line in content:
        if line.startswith('#') or line == '\n':
            continue
        items = line.strip().lstrip('(').rstrip(')\n').split()
        if isinstance(rule["key"], str):
            if items[0] == rule["key"] and items[-1] == rule["value"]:
                return 1.
        elif isinstance(rule["key"], list) and len(rule["key"]) == 2:
            if items[0] == rule["key"][0] \
                    and items[1] == rule["key"][1] \
                    and items[-1] == rule["value"]:
                return 1.
    return 0.
```
