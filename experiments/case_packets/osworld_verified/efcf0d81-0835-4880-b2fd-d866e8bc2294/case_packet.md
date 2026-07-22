# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `efcf0d81-0835-4880-b2fd-d866e8bc2294`
- task_id: `efcf0d81-0835-4880-b2fd-d866e8bc2294`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `vlc`
- snapshot: `base_setup`
- related apps: `vlc`
- official instruction: Make this part of the video my computer's background picture
- evaluator functions: `compare_images`
- evaluator conjunction: `and`
- evaluator result getter types: `vm_wallpaper`
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
- `official/desktop_env/evaluators/getters/info.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/vlc.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/vlc/efcf0d81-0835-4880-b2fd-d866e8bc2294.json`

Source SHA-256: `70b0a24d03301ec50ae5be1d43ba2f8a5e3d8fac7b2e6c948b7166ea75f084ba`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/Interstellar Movie - Official Trailer.mp4",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/vlc/efcf0d81-0835-4880-b2fd-d866e8bc2294/Interstellar%20Movie%20-%20Official%20Trailer.mp4"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": "VLC_VERBOSE=-1 vlc --no-audio --no-video-title-show --start-time=120.5 --stop-time=121 --play-and-pause '/home/user/Desktop/Interstellar Movie - Official Trailer.mp4'",
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
      "dest": "interstellar_wallpaper_gold.png",
      "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/vlc/efcf0d81-0835-4880-b2fd-d866e8bc2294/interstellar.png",
      "type": "cloud_file"
    },
    "func": "compare_images",
    "options": {
      "reference_base_result": 0.11
    },
    "result": {
      "dest": "result_wallpaper.png",
      "type": "vm_wallpaper"
    }
  },
  "fixed_ip": false,
  "id": "efcf0d81-0835-4880-b2fd-d866e8bc2294",
  "instruction": "Make this part of the video my computer's background picture",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "vlc"
  ],
  "snapshot": "base_setup",
  "source": "https://www.youtube.com/watch?v=XHprwDJ0-fU&t=436s, https://help.ubuntu.com/stable/ubuntu-help/look-background.html.en",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `345dfceaee568e02735a6b4f754bedb9d31bee415b6ef003f48afaaf25a8f21c`

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
      "end_line": 3,
      "excerpt_sha256": "ab270e34de38d99f0364043ca1808983f498a9e3943133071931657340b5bc95",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 3,
      "symbol": "import:uuid",
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
      "end_line": 5,
      "excerpt_sha256": "e4f846484778f7f065efd3be851677c4495d57ac1dbaccc5a8b4880a9b9907d0",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 5,
      "symbol": "import:Any",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 7,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 7,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 80,
      "excerpt_sha256": "03900b07d6dae0c8c18f2ea96ad9183eba56ea056629742181995066d3f23c37",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 32,
      "symbol": "get_cloud_file",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 1,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 2,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "79ca0fa1b0d013343e3019de681e99eef22c5f449e1b21806bb2f9729d8d362d",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 3,
      "symbol": "import:Union",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "392f3af91064b05418b0573a28bbd83d53ed171b883e1b49a62261fb806d122e",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 5,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
    },
    {
      "end_line": 46,
      "excerpt_sha256": "6c1d1755b6b8ed0b3cb946c221dde9337b0249ea13882b718e27ea3538239aa3",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "start_line": 16,
      "symbol": "get_vm_wallpaper",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
    },
    {
      "end_line": 12,
      "excerpt_sha256": "d34aea06c990aeedd2f8f5ff809c1180b92fccca0381269b7c18654043b9a374",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 12,
      "symbol": "import:np",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 13,
      "excerpt_sha256": "c4ae414c75cb228a7c6be3a10433b2f2421c75cd819cb76622e1d3330c06e61a",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 13,
      "symbol": "import:Image",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 16,
      "excerpt_sha256": "9ecac4ed6c67ab8bcef7eb35cb5da7dee079ed03dc997f7e8c33741b115e4f7e",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 16,
      "symbol": "import:ssim",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 224,
      "excerpt_sha256": "1bc43a7d39a2b0d7f1809a118b3fcb883f1fee7b79086b0e469e10c446375f2a",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 188,
      "symbol": "compare_images",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "dea57af4491a3ba17472bba36e68880617a37ea3fa50cd390a1f0104eeafd6f3",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "de99323abc87dce8abec1c29b123f7994150dfcae405d67a3d1be889e1452d35",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": {
    "reference_base_result": 0.11
  },
  "metrics": [
    {
      "name": "compare_images",
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
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "upstream_path": "desktop_env/evaluators/getters/info.py"
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
      "config_sha256": "09c9bcca042771426d5e27f5a7d870dc58183d067ce3f8b34d050c48139718b4",
      "packet_path": "official/desktop_env/evaluators/getters/info.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py",
      "source_sha256": "ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667",
      "symbol": "get_vm_wallpaper",
      "type": "vm_wallpaper"
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
  "task_id": "efcf0d81-0835-4880-b2fd-d866e8bc2294"
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

### `import:uuid` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L3-L3`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `ab270e34de38d99f0364043ca1808983f498a9e3943133071931657340b5bc95`

```python
import uuid
```

### `import:Dict` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L4-L4`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `f3e1094d4dc7c94939f5e6d73e3ce61bc0f6d2ef7b39c1e1a3c7be9dff56e58a`

```python
from typing import Dict, List, Set
```

### `import:Any` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L5-L5`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `e4f846484778f7f065efd3be851677c4495d57ac1dbaccc5a8b4880a9b9907d0`

```python
from typing import Optional, Any, Union
```

### `import:requests` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L7-L7`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `get_cloud_file` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L32-L80`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `03900b07d6dae0c8c18f2ea96ad9183eba56ea056629742181995066d3f23c37`

```python
def get_cloud_file(env, config: Dict[str, Any]) -> Union[str, List[str]]:
    """
    Config:
        path (str|List[str]): the url to download from
        dest (str|List[str])): file name of the downloaded file
        multi (bool) : optional. if path and dest are lists providing
          information of multiple files. defaults to False
        gives (List[int]): optional. defaults to [0]. which files are directly
          returned to the metric. if len==1, str is returned; else, list is
          returned.
    """

    if not config.get("multi", False):
        paths: List[str] = [config["path"]]
        dests: List[str] = [config["dest"]]
    else:
        paths: List[str] = config["path"]
        dests: List[str] = config["dest"]
    cache_paths: List[str] = []

    gives: Set[int] = set(config.get("gives", [0]))

    for i, (p, d) in enumerate(zip(paths, dests)):
        _path = os.path.join(env.cache_dir, d)
        if i in gives:
            cache_paths.append(_path)

        if os.path.exists(_path):
            #return _path
            continue

        url = p
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Atomic write: stream into a temp file then rename, so a concurrent
        # reader never observes a partially-downloaded file.
        tmp_path = f"{_path}.tmp.{uuid.uuid4().hex}"
        try:
            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            os.replace(tmp_path, _path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return cache_paths[0] if len(cache_paths)==1 else cache_paths
```

### `import:os` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L1-L1`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:logging` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L2-L2`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Union` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L3-L3`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `79ca0fa1b0d013343e3019de681e99eef22c5f449e1b21806bb2f9729d8d362d`

```python
from typing import Union
```

### `logger` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L5-L5`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `392f3af91064b05418b0573a28bbd83d53ed171b883e1b49a62261fb806d122e`

```python
logger = logging.getLogger("desktopenv.getters.info")
```

### `get_vm_wallpaper` from `official/desktop_env/evaluators/getters/info.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/info.py#L16-L46`

Full source SHA-256: `ad92d49a23d10b7b80ff5d75c2f6958cc70519b5706de2aecfba5aa5f3a8a667`

Exact excerpt SHA-256: `6c1d1755b6b8ed0b3cb946c221dde9337b0249ea13882b718e27ea3538239aa3`

```python
def get_vm_wallpaper(env, config: dict) -> Union[str, bytes]:
    _path = os.path.join(env.cache_dir, config["dest"])

    content = env.controller.get_vm_wallpaper()
    
    # Check if content is None or empty
    if content is None:
        logger.error("Failed to get VM wallpaper: controller returned None")
        # Create an empty file to prevent downstream errors
        with open(_path, "wb") as f:
            f.write(b"")
        return _path
    
    if not isinstance(content, bytes):
        logger.error(f"Invalid wallpaper content type: {type(content)}, expected bytes")
        # Create an empty file to prevent downstream errors
        with open(_path, "wb") as f:
            f.write(b"")
        return _path
    
    if len(content) == 0:
        logger.warning("VM wallpaper content is empty")
        # Create an empty file to prevent downstream errors
        with open(_path, "wb") as f:
            f.write(b"")
        return _path

    with open(_path, "wb") as f:
        f.write(content)

    return _path
```

### `import:np` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L12-L12`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `d34aea06c990aeedd2f8f5ff809c1180b92fccca0381269b7c18654043b9a374`

```python
import numpy as np
```

### `import:Image` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L13-L13`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `c4ae414c75cb228a7c6be3a10433b2f2421c75cd819cb76622e1d3330c06e61a`

```python
from PIL import Image
```

### `import:ssim` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L16-L16`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `9ecac4ed6c67ab8bcef7eb35cb5da7dee079ed03dc997f7e8c33741b115e4f7e`

```python
from skimage.metrics import structural_similarity as ssim
```

### `compare_images` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L188-L224`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `1bc43a7d39a2b0d7f1809a118b3fcb883f1fee7b79086b0e469e10c446375f2a`

```python
def compare_images(image1_path, image2_path, **options):
    # You would call this function with the paths to the two images you want to compare:
    # score = compare_images('path_to_image1', 'path_to_image2')
    # print("Similarity score:", score)

    if not image1_path or not image2_path:
        return 0

    base_score = options.get("reference_base_result", None)

    # Open the images and convert to grayscale
    image1 = Image.open(image1_path).convert('L')
    image2 = Image.open(image2_path).convert('L')

    # Resize images to the smaller one's size for comparison
    image1_size = image1.size
    image2_size = image2.size
    new_size = min(image1_size, image2_size)

    image1 = image1.resize(new_size, Image.Resampling.LANCZOS)
    image2 = image2.resize(new_size, Image.Resampling.LANCZOS)

    # Convert images to numpy arrays
    image1_array = np.array(image1)
    image2_array = np.array(image2)

    # Calculate SSIM between two images
    similarity_index = ssim(image1_array, image2_array)

    epsilon = 0.01
    if base_score is not None:
        if similarity_index >= base_score + epsilon:
            return (similarity_index - base_score) / (1 - base_score)
        else:
            return 0
    else:
        return similarity_index
```
