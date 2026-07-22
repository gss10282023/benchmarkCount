# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `bba3381f-b5eb-4439-bd9e-80c22218d5a7`
- task_id: `bba3381f-b5eb-4439-bd9e-80c22218d5a7`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `vlc`
- snapshot: `base_setup`
- related apps: `vlc`
- official instruction: Can you start streaming the video from this link for me? https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8
- evaluator functions: `is_vlc_playing`
- evaluator conjunction: `and`
- evaluator result getter types: `vlc_playing_info`
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

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/vlc/bba3381f-b5eb-4439-bd9e-80c22218d5a7.json`

Source SHA-256: `9b08d902825a72bf2dbac73e632ecbe15e61602565fc3fc92a2953405262d7fb`

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
        "type": "url",
        "url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"
      },
      "type": "rule"
    },
    "func": "is_vlc_playing",
    "result": {
      "dest": "status.xml",
      "type": "vlc_playing_info"
    }
  },
  "fixed_ip": false,
  "id": "bba3381f-b5eb-4439-bd9e-80c22218d5a7",
  "instruction": "Can you start streaming the video from this link for me? https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "vlc"
  ],
  "snapshot": "base_setup",
  "source": "https://developer.apple.com/streaming/examples/ - Apple HLS test streams for developers",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `dc8db25dc17357d12fea7a5a44c9ffdbd0fcc54e040cc130e7f501638fe0e265`

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
      "end_line": 1,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
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
      "end_line": 3,
      "excerpt_sha256": "7b2ddb8a2e64c6166feedaf30ee50ac62165fe149fdd8b0d7b777ebee21ca34d",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 3,
      "symbol": "import:time",
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
      "end_line": 7,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 7,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "f17d61fba840351a5f1fe7800e9f42b133a02e7f37a7a83c9a97e295a0ec04f5",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 9,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/vlc.py"
    },
    {
      "end_line": 54,
      "excerpt_sha256": "02b332a7cf8650e9a48d020488104153a504a19060ce7d2d9023ce49b28f6465",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "start_line": 12,
      "symbol": "get_vlc_playing_info",
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
      "end_line": 2,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 2,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 4,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "e3cf99aa443f1359c683d20b4b123cdb5fab51ab00fdc4401e045e11943ce96a",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 5,
      "symbol": "import:ElementTree",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 6,
      "excerpt_sha256": "ce2857e54587b6c88d98f7cd8f2a4692258523d77f499e9bef9909ff01190bb9",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 6,
      "symbol": "import:urlparse",
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
      "end_line": 140,
      "excerpt_sha256": "2c031a936f6a982a6a2fc71ad41f67a7d92205b954b39f51bd9f7da214f343b4",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 21,
      "symbol": "is_vlc_playing",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "f8a2b0e8cb4500f735ac3dffd874ed1889c25e1059338ff0e996ab0bc6aa71b6",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "e003b8784052dbbed6f97be2e405610dc1ab4ed5d76dbe846579a7aa8f4257e5",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "is_vlc_playing",
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
  "postconfig_present": false,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "9e8c3d16ccdef73f9f8231810b5d1af2bb070374ba295ef9941168aa3a44a68d",
      "packet_path": "official/desktop_env/evaluators/getters/vlc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py",
      "source_sha256": "45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3",
      "symbol": "get_vlc_playing_info",
      "type": "vlc_playing_info"
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
  "task_id": "bba3381f-b5eb-4439-bd9e-80c22218d5a7"
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

### `import:logging` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L1-L1`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:os` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L2-L2`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:time` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L3-L3`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `7b2ddb8a2e64c6166feedaf30ee50ac62165fe149fdd8b0d7b777ebee21ca34d`

```python
import time
```

### `import:Dict` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L4-L4`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `import:requests` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L7-L7`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `logger` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L9-L9`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `f17d61fba840351a5f1fe7800e9f42b133a02e7f37a7a83c9a97e295a0ec04f5`

```python
logger = logging.getLogger("desktopenv.getters.vlc")
```

### `get_vlc_playing_info` from `official/desktop_env/evaluators/getters/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/vlc.py#L12-L54`

Full source SHA-256: `45bcf615152eb9f7b1bb2d7e2f6b79447bcb9c75c969dec12e7eef5511a900b3`

Exact excerpt SHA-256: `02b332a7cf8650e9a48d020488104153a504a19060ce7d2d9023ce49b28f6465`

```python
def get_vlc_playing_info(env, config: Dict[str, str]):
    """
    Gets the current playing information from VLC's HTTP interface.
    """

    host = env.vm_ip
    port = env.vlc_port
    configured_password = getattr(env, "vlc_password", None) or os.environ.get("OSWORLD_VLC_PASSWORD")
    candidate_passwords = []
    if configured_password:
        candidate_passwords.append(configured_password)
    candidate_passwords.append("password")
    client_password = getattr(env, "client_password", None)
    if client_password and client_password not in candidate_passwords:
        candidate_passwords.append(client_password)

    _path = os.path.join(env.cache_dir, config["dest"])
    url = f'http://{host}:{port}/requests/status.xml'

    # VLC's HTTP interface is often not ready immediately after launch; retry
    # with a short backoff and a per-request timeout instead of failing on the
    # first connection error.
    content = None
    for attempt in range(5):
        for password in candidate_passwords:
            try:
                response = requests.get(url, auth=('', password), timeout=10)
                if response.status_code == 200:
                    content = response.content
                    break
                logger.error("Failed to get vlc status. Status code: %d", response.status_code)
            except requests.RequestException as e:
                logger.warning("VLC status request attempt %d failed: %s", attempt + 1, e)
        if content is not None:
            break
        time.sleep(1)
    if content is None:
        return None

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

### `import:os` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L2-L2`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L4-L4`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `import:ElementTree` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L5-L5`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `e3cf99aa443f1359c683d20b4b123cdb5fab51ab00fdc4401e045e11943ce96a`

```python
from xml.etree import ElementTree
```

### `import:urlparse` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L6-L6`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `ce2857e54587b6c88d98f7cd8f2a4692258523d77f499e9bef9909ff01190bb9`

```python
from urllib.parse import urlparse
```

### `logger` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L18-L18`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `75fc8dffb9f4f69221641e22851433b92ab68c00fe97bed620894c9b05d9c580`

```python
logger = logging.getLogger("desktopenv.metrics.vlc")
```

### `is_vlc_playing` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L21-L140`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `2c031a936f6a982a6a2fc71ad41f67a7d92205b954b39f51bd9f7da214f343b4`

```python
def is_vlc_playing(actual_status_path: str, rule: Dict[str, str]) -> float:
    """
    Checks if VLC is currently playing a file.
    """
    if not actual_status_path or not os.path.exists(actual_status_path):
        logger.warning("VLC status file is unavailable: %s", actual_status_path)
        return 0

    with open(actual_status_path, 'rb') as file:
        actual_status = file.read().decode('utf-8')

    tree = ElementTree.fromstring(actual_status)
    status = tree.find('state').text
    logger.info(f"VLC Status: {status}")
    if status == 'playing':
        if rule['type'] == 'file_name':
            # Try multiple possible paths for file information in VLC XML
            file_paths = [
                'information/category[@name="meta"]/info[@name="filename"]',
                'information/category[@name="meta"]/info[@name="title"]',
                'information/category[@name="meta"]/info[@name="uri"]',
                'information/category[@name="meta"]/info[@name="location"]',
                'information/category[@name="meta"]/info[@name="name"]'
            ]
            
            file_info = None
            for path in file_paths:
                element = tree.find(path)
                if element is not None and element.text:
                    file_info = element.text
                    break
            
            if file_info:
                expected_filename = rule['file_name']
                
                # Method 1: Direct filename match (most precise)
                actual_basename = os.path.basename(file_info)
                if actual_basename == expected_filename:
                    return 1
                
                # Method 2: Endswith match (for backward compatibility)
                if file_info.endswith(expected_filename):
                    return 1
                
                # Method 3: For paths, check if expected filename is in the path
                if expected_filename in file_info:
                    # Additional check to avoid false positives
                    # Make sure it's actually the filename, not just part of a path
                    if file_info.endswith('/' + expected_filename) or file_info.endswith('\\' + expected_filename):
                        return 1
                
                logger.warning(f"File name mismatch - Expected: {expected_filename}, Found: {file_info}")
                return 0
            else:
                logger.warning(f"Could not find file information in VLC status XML for rule: {rule}")
                return 0
        elif rule['type'] == 'url':
            # Try multiple possible paths for URL information in VLC XML
            url_paths = [
                'information/category[@name="meta"]/info[@name="url"]',
                'information/category[@name="meta"]/info[@name="URI"]', 
                'information/category[@name="meta"]/info[@name="location"]',
                'information/category[@name="meta"]/info[@name="title"]',  # Sometimes URL is in title for streams
                'information/category[@name="meta"]/info[@name="filename"]',  # Sometimes URL is in filename for streams
                'information/category[@name="Stream 0"]/info[@name="Codec"]',  # Try stream info
                'information/category[@name="Stream 0"]/info[@name="Type"]',
                'information/category[@name="Stream 0"]/info[@name="Language"]'
            ]
            
            file_info = None
            logger.debug(f"Looking for URL: {rule['url']}")
            
            for path in url_paths:
                element = tree.find(path)
                if element is not None and element.text:
                    file_info = element.text
                    logger.debug(f"Found URL info at '{path}': {file_info}")
                    break
            
            if file_info:
                # For URL comparison, check if the rule URL is contained in the file_info
                # This handles cases where VLC might show a longer or modified URL
                expected_url = rule['url']
                
                # Method 1: Direct URL match
                if expected_url in file_info or file_info.endswith(expected_url):
                    return 1
                
                # Method 2: For HLS streams, VLC often shows just the filename instead of full URL
                # Check if the file_info matches the filename part of the expected URL
                try:
                    expected_parsed = urlparse(expected_url)
                    expected_filename = os.path.basename(expected_parsed.path)
                    
                    # If VLC shows just the filename (common for HLS streams)
                    if file_info == expected_filename:
                        logger.info(f"URL filename match - Expected URL: {expected_url}, VLC shows filename: {file_info}")
                        return 1
                    
                    # Method 3: Check if both are URLs from the same domain and similar path
                    if '://' in file_info:  # file_info is also a URL
                        actual_parsed = urlparse(file_info)
                        # Same domain and similar path structure
                        if (expected_parsed.netloc == actual_parsed.netloc and 
                            expected_parsed.path in actual_parsed.path):
                            return 1
                except Exception as e:
                    logger.debug(f"URL parsing error: {e}")
                    pass
                
                logger.warning(f"URL mismatch - Expected: {expected_url}, Found: {file_info}")
                return 0
            else:
                logger.warning(f"Could not find URL information in VLC status XML for rule: {rule}")
                return 0
        else:
            logger.error(f"Unknown type: {rule['type']}")
            return 0
    else:
        return 0
```
