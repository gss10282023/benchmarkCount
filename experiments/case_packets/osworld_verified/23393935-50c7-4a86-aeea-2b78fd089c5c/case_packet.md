# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `23393935-50c7-4a86-aeea-2b78fd089c5c`
- task_id: `23393935-50c7-4a86-aeea-2b78fd089c5c`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `os`
- snapshot: `os`
- related apps: `os`
- official instruction: Recursively go through the folders of the 'photos' directory and copy any .jpg files found into another directory named 'cpjpg'.
- evaluator functions: `check_moved_jpgs`
- evaluator conjunction: `and`
- evaluator result getter types: `list_directory`
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
- `official/desktop_env/evaluators/getters/info.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/basic_os.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/os/23393935-50c7-4a86-aeea-2b78fd089c5c.json`

Source SHA-256: `9682045d7f9f3e73ecd29dafd485aa4376b02d75de13502d2a3eeb0f42341bf5`

```json
{
  "config": [
    {
      "parameters": {
        "command": "mkdir -p ~/Desktop/photos && mkdir -p ~/Desktop/cpjpg",
        "shell": true
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": "mkdir -p ~/Desktop/photos/vacation && mkdir -p ~/Desktop/photos/family && mkdir -p ~/Desktop/photos/events",
        "shell": true
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": "mkdir -p ~/Desktop/photos/vacation/thailand && mkdir -p ~/Desktop/photos/vacation/hk",
        "shell": true
      },
      "type": "execute"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/photos/vacation/thailand/monk252520thailand252520wat252520arun252520scaled25255B225255D.jpg",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/os/23393935-50c7-4a86-aeea-2b78fd089c5c/monk252520thailand252520wat252520arun252520scaled25255B225255D.jpg"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/photos/vacation/hk/hong-kong-china.jpg",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/os/23393935-50c7-4a86-aeea-2b78fd089c5c/hong-kong-china.jpg"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/photos/vacation/hk/hk_group_photo.jpg",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/os/23393935-50c7-4a86-aeea-2b78fd089c5c/hk_group_photo.jpg"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/photos/family/us_3.png",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/os/23393935-50c7-4a86-aeea-2b78fd089c5c/us_3.png"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/photos/events/emnlp2023.jpg",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/os/23393935-50c7-4a86-aeea-2b78fd089c5c/emnlp2023.jpg"
          }
        ]
      },
      "type": "download"
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
        "expected": [
          "emnlp2023.jpg",
          "hk_group_photo.jpg",
          "hong-kong-china.jpg",
          "monk252520thailand252520wat252520arun252520scaled25255B225255D.jpg"
        ]
      },
      "type": "rule"
    },
    "func": "check_moved_jpgs",
    "result": {
      "path": "/home/user/Desktop/cpjpg",
      "type": "list_directory"
    }
  },
  "fixed_ip": false,
  "id": "23393935-50c7-4a86-aeea-2b78fd089c5c",
  "instruction": "Recursively go through the folders of the 'photos' directory and copy any .jpg files found into another directory named 'cpjpg'.",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "os"
  ],
  "snapshot": "os",
  "source": "https://superuser.com/questions/91307/copying-only-jpg-from-a-directory-structure-to-another-location-linux",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `b661638eb1c171fba99fb13af279c8873c0920025dfe6046192f96c2fceb285e`

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
      "end_line": 50,
      "excerpt_sha256": "ea31806163bc343030487687dc621a584bd9aadda6dab66f06644843edded461",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 49,
      "symbol": "get_list_directory",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
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
      "end_line": 55,
      "excerpt_sha256": "d38e0f411317ff1b6f6855e8e1e3b282fdd300bb95bdf07fd1eb5d5710e877c8",
      "packet_path": "official/desktop_env/evaluators/metrics/basic_os.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/basic_os.py",
      "source_sha256": "08843c93bab8e8f0f917f09dd146768e272f5dff735652f02545b46b45764bbc",
      "start_line": 45,
      "symbol": "check_moved_jpgs",
      "upstream_path": "desktop_env/evaluators/metrics/basic_os.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "25a7cab7013e97708da3c64a7ccc5cff56423c3315103af37397fef1fc6a36c9",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "8769b75bb49f4204d8d34fb011b2647c301e9db3c158eacfa529301b20d21c2c",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_moved_jpgs",
      "packet_path": "official/desktop_env/evaluators/metrics/basic_os.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/basic_os.py",
      "source_sha256": "08843c93bab8e8f0f917f09dd146768e272f5dff735652f02545b46b45764bbc"
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
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
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
      "packet_path": "official/desktop_env/evaluators/metrics/basic_os.py",
      "sha256": "08843c93bab8e8f0f917f09dd146768e272f5dff735652f02545b46b45764bbc",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/basic_os.py",
      "upstream_path": "desktop_env/evaluators/metrics/basic_os.py"
    }
  ],
  "postconfig_present": false,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "ac0287e5ca15350a4f226ff5cf5d01fa17bfba8934021f8c34ee52fb4a2d66d0",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "symbol": "get_list_directory",
      "type": "list_directory"
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
  "task_id": "23393935-50c7-4a86-aeea-2b78fd089c5c"
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

### `get_list_directory` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L49-L50`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `ea31806163bc343030487687dc621a584bd9aadda6dab66f06644843edded461`

```python
def get_list_directory(env, config: dict) -> dict:
    return env.controller.get_vm_directory_tree(config["path"])
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

### `check_moved_jpgs` from `official/desktop_env/evaluators/metrics/basic_os.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/basic_os.py#L45-L55`

Full source SHA-256: `08843c93bab8e8f0f917f09dd146768e272f5dff735652f02545b46b45764bbc`

Exact excerpt SHA-256: `d38e0f411317ff1b6f6855e8e1e3b282fdd300bb95bdf07fd1eb5d5710e877c8`

```python
def check_moved_jpgs(directory_list, rule):
    expected_jpgs = rule["expected"]
    moved_jpgs = [node['name'] for node in directory_list['children']]

    if len(moved_jpgs) != len(expected_jpgs):
        return 0

    if set(moved_jpgs) == set(expected_jpgs):
        return 1
    else:
        return 0
```
