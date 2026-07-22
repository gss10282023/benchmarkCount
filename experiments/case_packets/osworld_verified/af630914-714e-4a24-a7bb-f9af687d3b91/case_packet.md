# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `af630914-714e-4a24-a7bb-f9af687d3b91`
- task_id: `af630914-714e-4a24-a7bb-f9af687d3b91`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `chrome`
- snapshot: `chrome`
- related apps: `chrome`
- official instruction: My grandmother has been using the Chrome lately and told me that the font size is way too small for her poor eyesight. Could you set the default font size to the largest for her?
- evaluator functions: `check_font_size`
- evaluator conjunction: `and`
- evaluator result getter types: `chrome_font_size`
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
- `official/desktop_env/evaluators/getters/chrome.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/chrome.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/chrome/af630914-714e-4a24-a7bb-f9af687d3b91.json`

Source SHA-256: `344a79e7f795d04a7fabf90d38c64a53a6cb2dbd7ee5a31b3e7f82845c895e3a`

```json
{
  "config": [
    {
      "parameters": {
        "command": [
          "google-chrome",
          "--remote-debugging-port=1337"
        ]
      },
      "type": "launch"
    },
    {
      "parameters": {
        "command": [
          "socat",
          "tcp-listen:9222,fork",
          "tcp:localhost:1337"
        ]
      },
      "type": "launch"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "max": 99999,
        "min": 16,
        "type": "range"
      },
      "type": "rule"
    },
    "func": "check_font_size",
    "postconfig": [
      {
        "parameters": {
          "command": [
            "pkill",
            "chrome"
          ]
        },
        "type": "launch"
      },
      {
        "parameters": {
          "command": [
            "google-chrome",
            "--remote-debugging-port=1337"
          ]
        },
        "type": "launch"
      },
      {
        "parameters": {
          "seconds": 3
        },
        "type": "sleep"
      }
    ],
    "result": {
      "type": "chrome_font_size"
    }
  },
  "fixed_ip": false,
  "id": "af630914-714e-4a24-a7bb-f9af687d3b91",
  "instruction": "My grandmother has been using the Chrome lately and told me that the font size is way too small for her poor eyesight. Could you set the default font size to the largest for her?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "chrome"
  ],
  "snapshot": "chrome",
  "source": "https://www.howtogeek.com/680260/how-to-change-chromes-default-text-size/",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `3e266405e9d9ea1383c246746b0c24520e6ebdd0905623fb7069a588cc592fbf`

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
      "excerpt_sha256": "261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 2,
      "symbol": "import:json",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 3,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "2ee31f90a04b45447df37745a3d1016650eab823bd86b4f0a04836df727e506a",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 9,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 22,
      "excerpt_sha256": "1c17dc25a8824d7828b2a14f893cb1cf7e82701cd503150f6b9e8113224c1955",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 20,
      "symbol": "_is_arm_architecture",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 36,
      "excerpt_sha256": "be5e1ed9a973c2d1f914d536ba1bc122b1b749e03327b4de21b87efc4beee316",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 36,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 468,
      "excerpt_sha256": "5509c6e0be3f9dd12f9678137bdb29e5a4f5227f4ead6c4dbb16bd6c908a945e",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 430,
      "symbol": "get_chrome_font_size",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
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
      "end_line": 568,
      "excerpt_sha256": "c6ffc684d49c960b9b46968542cd3302d97f5b0b39d864b0e7fba868ed7dcd59",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 557,
      "symbol": "check_font_size",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "04e719d012f16c58bea8d3fd8489bf45c622a973767a7aa68004070d4edd4298",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "d932f81f487fbac2f1f0ce7414c30ab3b6df20b558b7377d54633c4fa9589574",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_font_size",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf"
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
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
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
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "7b4e2729cb5c329e4019dc1c72eeeaf42b3c7428f814f2776cccb957e7f59eee",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_chrome_font_size",
      "type": "chrome_font_size"
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
  "task_id": "af630914-714e-4a24-a7bb-f9af687d3b91"
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

### `import:json` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L2-L2`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc`

```python
import json
```

### `import:logging` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L3-L3`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Dict` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L9-L9`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `2ee31f90a04b45447df37745a3d1016650eab823bd86b4f0a04836df727e506a`

```python
from typing import Dict, Any, List
```

### `_is_arm_architecture` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L20-L22`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `1c17dc25a8824d7828b2a14f893cb1cf7e82701cd503150f6b9e8113224c1955`

```python
def _is_arm_architecture(env) -> bool:
    arch = env.vm_machine.lower()
    return "arm" in arch or "aarch" in arch
```

### `logger` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L36-L36`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `be5e1ed9a973c2d1f914d536ba1bc122b1b749e03327b4de21b87efc4beee316`

```python
logger = logging.getLogger("desktopenv.getters.chrome")
```

### `get_chrome_font_size` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L430-L468`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `5509c6e0be3f9dd12f9678137bdb29e5a4f5227f4ead6c4dbb16bd6c908a945e`

```python
def get_chrome_font_size(env, config: Dict[str, str]):
    os_type = env.vm_platform
    if os_type == 'Windows':
        preference_file_path = env.controller.execute_python_command("""import os; print(os.path.join(os.getenv('LOCALAPPDATA'),
                                                'Google\\Chrome\\User Data\\Default\\Preferences'))""")[
            'output'].strip()
    elif os_type == 'Darwin':
        preference_file_path = env.controller.execute_python_command(
            "import os; print(os.path.join(os.getenv('HOME'), 'Library/Application Support/Google/Chrome/Default/Preferences'))")[
            'output'].strip()
    elif os_type == 'Linux':
        if _is_arm_architecture(env):
            preference_file_path = env.controller.execute_python_command(
                "import os; print(os.path.join(os.getenv('HOME'), 'snap/chromium/common/chromium/Default/Preferences'))")[
                'output'].strip()
        else:
            preference_file_path = env.controller.execute_python_command(
                "import os; print(os.path.join(os.getenv('HOME'), '.config/google-chrome/Default/Preferences'))")[
                'output'].strip()
    else:
        raise Exception('Unsupported operating system')

    try:
        content = env.controller.get_file(preference_file_path)
        data = json.loads(content)

        # The path within the JSON data to the default search engine might vary
        search_engine = data.get('webkit', {}).get('webprefs', {
            "default_fixed_font_size": 13,
            "default_font_size": 16,
            "minimum_font_size": 13
        })
        return search_engine
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            "default_fixed_font_size": 13,
            "default_font_size": 16
        }
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

### `check_font_size` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L557-L568`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c6ffc684d49c960b9b46968542cd3302d97f5b0b39d864b0e7fba868ed7dcd59`

```python
def check_font_size(font_size, rule):
    """
    Check if the font size is as expected.
    """

    default_font_size = font_size['default_font_size']
    if rule['type'] == 'value':
        return 1. if default_font_size == rule['value'] else 0.
    elif rule['type'] == 'range':
        return 1. if rule['min'] < default_font_size < rule['max'] else 0.
    else:
        raise TypeError(f"{rule['type']} not support yet!")
```
