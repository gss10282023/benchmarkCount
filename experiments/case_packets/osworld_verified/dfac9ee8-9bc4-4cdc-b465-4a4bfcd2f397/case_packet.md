# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397`
- task_id: `dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `thunderbird`
- snapshot: `thunderbird`
- related apps: `thunderbird`
- official instruction: Help me to remove the account "anonym-x2024@outlook.com"
- evaluator functions: `check_csv`
- evaluator conjunction: `and`
- evaluator result getter types: `cache_file`
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
- `official/desktop_env/evaluators/getters/file.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/general.py`
- `official/desktop_env/evaluators/metrics/utils.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/thunderbird/dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397.json`

Source SHA-256: `a6481280f1d740920ce499da2e299364cf5c3b9dedb862c7a3017542c126c672`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/thunderbird-profile.tar.gz",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/thunderbird/dd84e895-72fd-4023-a336-97689ded257c/thunderbird-profile.tar.gz"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": [
          "tar",
          "-xzv",
          "-f",
          "/home/user/Desktop/thunderbird-profile.tar.gz",
          "-C",
          "/home/user/"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "/usr/bin/thunderbird"
        ]
      },
      "type": "launch"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "unexpect": [
          {
            "url": "imap://outlook.office365.com",
            "user": "anonym-x2024@outlook.com"
          }
        ]
      },
      "type": "rule"
    },
    "func": "check_csv",
    "postconfig": [
      {
        "parameters": {
          "files": [
            {
              "path": "/home/user/Desktop/firefox_decrypt.py",
              "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/thunderbird/dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397/firefox_decrypt.py"
            }
          ]
        },
        "type": "download"
      },
      {
        "parameters": {
          "command": [
            "python3",
            "/home/user/Desktop/firefox_decrypt.py",
            "/home/user/.thunderbird",
            "-n",
            "-c",
            "2",
            "-f",
            "csv",
            "-d",
            ","
          ],
          "stdout": "thunderbird-accounts.csv"
        },
        "type": "execute"
      }
    ],
    "result": {
      "path": "thunderbird-accounts.csv",
      "type": "cache_file"
    }
  },
  "fixed_ip": false,
  "id": "dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397",
  "instruction": "Help me to remove the account \"anonym-x2024@outlook.com\"",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "thunderbird"
  ],
  "snapshot": "thunderbird",
  "source": "https://www.wikihow.com/Remove-an-Email-Account-from-Thunderbird",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `bc9bbbe8870cc6a9989158d0265c6201bd9874f6f7d17830c56c4cad4ad3acab`

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
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 1,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "f3e1094d4dc7c94939f5e6d73e3ce61bc0f6d2ef7b39c1e1a3c7be9dff56e58a",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 4,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 169,
      "excerpt_sha256": "f26dd4a4c8fb6830672fa96a6c1b5dbb88aa13fe99fd65d5b04c772537957084",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 161,
      "symbol": "get_cache_file",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
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
      "end_line": 1,
      "excerpt_sha256": "ac580dadffeea2191ae6e8a139f2d83a843a2bba10383db992ac08c7091b9843",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 1,
      "symbol": "import:csv",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 13,
      "excerpt_sha256": "f1e514bded8115f262f0549707ab0fa7cb8c30ae5335a859a177949157577897",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 13,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 148,
      "excerpt_sha256": "47d1f311595e08c13ca607a75b42f74aee5575e1e03856528d04002665b8eaba",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 122,
      "symbol": "check_csv",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 11,
      "excerpt_sha256": "e433aafde859fb8c470f709800ddf6fd5c57ba89c44a00c2f5e2d26aea761cbc",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 11,
      "symbol": "import:Any",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 12,
      "excerpt_sha256": "f36acc7761a735c99ffcec1d5517284fc6df42f9f4a727b8719e0df6a901c8ab",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 12,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 705,
      "excerpt_sha256": "4445858319c62c65b557a86f2ab106b321df53415a9d45ac6d90d53955bcc805",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 704,
      "symbol": "_match_record",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "efefd9b2b53b8d1d34993c096d1ae4513dde963dc20e1a5e31c315ed5ae1af7e",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "6ce6b2db52fe9f1f28a73ea305b8c0e063d8365bc4140aac4383976d2fffe142",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_csv",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7"
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
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
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
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "badfedf5d74b46655a261c63bb3e0df6373b5d7ff11dd9cb9333afa11875c749",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cache_file",
      "type": "cache_file"
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
  "task_id": "dfac9ee8-9bc4-4cdc-b465-4a4bfcd2f397"
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

### `import:os` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L1-L1`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:Dict` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L4-L4`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `f3e1094d4dc7c94939f5e6d73e3ce61bc0f6d2ef7b39c1e1a3c7be9dff56e58a`

```python
from typing import Dict, List, Set
```

### `get_cache_file` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L161-L169`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `f26dd4a4c8fb6830672fa96a6c1b5dbb88aa13fe99fd65d5b04c772537957084`

```python
def get_cache_file(env, config: Dict[str, str]) -> str:
    """
    Config:
        path (str): relative path in cache dir
    """

    _path = os.path.join(env.cache_dir, config["path"])
    assert os.path.exists(_path)
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

### `import:csv` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L1-L1`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `ac580dadffeea2191ae6e8a139f2d83a843a2bba10383db992ac08c7091b9843`

```python
import csv
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L13-L13`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `f1e514bded8115f262f0549707ab0fa7cb8c30ae5335a859a177949157577897`

```python
from typing import Dict, List, Pattern
```

### `check_csv` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L122-L148`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `47d1f311595e08c13ca607a75b42f74aee5575e1e03856528d04002665b8eaba`

```python
def check_csv(result: str, rules: Dict[str, List[Dict[str, str]]]) -> float:
    """
    Args:
        result (str): path to csv file
        rules (Dict[str, List[Dict[str, str]]]): dict like
          {
            "expect": [{key: value}]
            "unexpect": [{key: value}]
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    expect_metrics = [False] * len(rules.get("expect", []))
    unexpect_metric = True
    with open(result) as f:
        reader = csv.DictReader(f)

        for rcd in reader:
            for i, r in enumerate(rules.get("expect", [])):
                expect_metrics[i] = expect_metrics[i] or _match_record(r, rcd)
            unexpect_metric = unexpect_metric and not any(_match_record(r, rcd) for r in rules.get("unexpect", []))
    return float(all(expect_metrics) and unexpect_metric)
```

### `import:Any` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L11-L11`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `e433aafde859fb8c470f709800ddf6fd5c57ba89c44a00c2f5e2d26aea761cbc`

```python
from typing import Any, TypeVar, Union, Iterable, Optional, Callable
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L12-L12`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `f36acc7761a735c99ffcec1d5517284fc6df42f9f4a727b8719e0df6a901c8ab`

```python
from typing import Dict, List, Set, Match, Tuple, Pattern
```

### `_match_record` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L704-L705`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `4445858319c62c65b557a86f2ab106b321df53415a9d45ac6d90d53955bcc805`

```python
def _match_record(pattern: Dict[str, Any], item: Dict[str, Any]) -> bool:
    return all(k in item and item[k] == val for k, val in pattern.items())
```
