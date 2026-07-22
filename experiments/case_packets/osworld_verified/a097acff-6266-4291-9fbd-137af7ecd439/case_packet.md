# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `a097acff-6266-4291-9fbd-137af7ecd439`
- task_id: `a097acff-6266-4291-9fbd-137af7ecd439`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `libreoffice_impress`
- snapshot: `libreoffice_impress`
- related apps: `libreoffice_impress`
- official instruction: Could you help me save my slides as pre.pptx on the Desktop?
- evaluator functions: `compare_pptx_files`
- evaluator conjunction: `and`
- evaluator result getter types: `vm_file`
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
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/slides.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/libreoffice_impress/a097acff-6266-4291-9fbd-137af7ecd439.json`

Source SHA-256: `edd2876abc9d86408c0d31d20c332b323d36f95d5f33a4a46efc8f12d4c4ddd5`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "Downloads/Secrets-of-Monetizing-Video.pptx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_impress/a097acff-6266-4291-9fbd-137af7ecd439/Secrets-of-Monetizing-Video.pptx"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "path": "Downloads/Secrets-of-Monetizing-Video.pptx"
      },
      "type": "open"
    }
  ],
  "evaluator": {
    "expected": {
      "dest": "Secrets-of-Monetizing-Video.pptx",
      "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_impress/a097acff-6266-4291-9fbd-137af7ecd439/Secrets-of-Monetizing-Video.pptx",
      "type": "cloud_file"
    },
    "func": "compare_pptx_files",
    "options": {
      "examine_shape": false
    },
    "result": {
      "dest": "pre.pptx",
      "path": "/home/user/Desktop/pre.pptx",
      "type": "vm_file"
    }
  },
  "fixed_ip": false,
  "id": "a097acff-6266-4291-9fbd-137af7ecd439",
  "instruction": "Could you help me save my slides as pre.pptx on the Desktop?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "libreoffice_impress"
  ],
  "snapshot": "libreoffice_impress",
  "source": "https://www.youtube.com/watch?v=DDmEvjs4iBw",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `d75e7a6b857126e4b9a137850733fac7d312d26bff07e79bbf48559a107bd948`

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
      "end_line": 2,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 2,
      "symbol": "import:logging",
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
      "end_line": 6,
      "excerpt_sha256": "2ed0247cc05b861fea3391ee7651aec4bb57304b71be6e96d2b74d171c551f55",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 6,
      "symbol": "import:datetime",
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
      "end_line": 10,
      "excerpt_sha256": "df15c4979fae995ded306279ba830d847eda92de71b795dad700bdbe5be696f5",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 10,
      "symbol": "logger",
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
      "end_line": 158,
      "excerpt_sha256": "d0565cba192756ad787f28cd70cef2db7b0086183127c576ce303e3b95018291",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "start_line": 83,
      "symbol": "get_vm_file",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "d8313b379a858f183008f2f6198051d5bd7ca075d573902814a9666bfda819eb",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 2,
      "symbol": "import:ET",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 6,
      "excerpt_sha256": "281b02f27f075fa4c668f888b61ff549b4ae9ad55b0de0785c89a0021616c871",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 6,
      "symbol": "import:Presentation",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 8,
      "excerpt_sha256": "a6956d87bc9da410d3af4faf99065fbf5eed4c47fbaf595edf6e9893d7d53659",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 8,
      "symbol": "import:MSO_SHAPE_TYPE",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 26,
      "excerpt_sha256": "dd82f07b29844394e5225021be720cf3fbc1ffd7948e82e9a61a3ec2372731ea",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 26,
      "symbol": "debug_logger",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 35,
      "excerpt_sha256": "72e23040aeca579da858c64ae38ff72a630ec83a001d7d4524f2bf38fbdb9245",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 28,
      "symbol": "enable_debug_logging",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 187,
      "excerpt_sha256": "e6de90e8888765bcb1a6a8da7f553ddbf7c6eaf270e81c0963fa478a803e6cce",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 166,
      "symbol": "get_all_text_shapes",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    },
    {
      "end_line": 756,
      "excerpt_sha256": "8d4bd9d990460a2d20dd06e053908df7bce879367f000116701fd2307a13a082",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "start_line": 190,
      "symbol": "compare_pptx_files",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "e910c3b53e178612f3999edc3ac93c4eed524ce2c918da55427bdcb687e9952a",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "fb5901e1b854c6d6a3b1bf79c6f470655081058728bcc220650622d096a5b9af",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": {
    "examine_shape": false
  },
  "metrics": [
    {
      "name": "compare_pptx_files",
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "source_sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41"
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
      "packet_path": "official/desktop_env/evaluators/metrics/__init__.py",
      "sha256": "f8e89039d448b715e99c14a939a566d4148fda3a67a71371a208baa1d6276a08",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/__init__.py",
      "upstream_path": "desktop_env/evaluators/metrics/__init__.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/slides.py",
      "sha256": "189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py",
      "upstream_path": "desktop_env/evaluators/metrics/slides.py"
    }
  ],
  "postconfig_present": false,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "b627427e96c6177ba1625d72cf1562e55ca6bed6e67921fa4e3c82a8fb1f3a48",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_vm_file",
      "type": "vm_file"
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
  "task_id": "a097acff-6266-4291-9fbd-137af7ecd439"
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

### `import:logging` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L2-L2`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
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

### `import:datetime` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L6-L6`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `2ed0247cc05b861fea3391ee7651aec4bb57304b71be6e96d2b74d171c551f55`

```python
from datetime import datetime
```

### `import:requests` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L7-L7`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `logger` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L10-L10`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `df15c4979fae995ded306279ba830d847eda92de71b795dad700bdbe5be696f5`

```python
logger = logging.getLogger("desktopenv.getter.file")
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

### `get_vm_file` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L83-L158`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `d0565cba192756ad787f28cd70cef2db7b0086183127c576ce303e3b95018291`

```python
def get_vm_file(env, config: Dict[str, Any]) -> Union[Optional[str], List[Optional[str]]]:
    """
    Config:
        path (str): absolute path on the VM to fetch
        dest (str): file name of the downloaded file
        multi (bool) : optional. if path and dest are lists providing
          information of multiple files. defaults to False
        gives (List[int]): optional. defaults to [0]. which files are directly
          returned to the metric. if len==1, str is returned; else, list is
          returned.
        only support for single file now:
        time_suffix(bool): optional. defaults to False. if True, append the current time in required format.
        time_format(str): optional. defaults to "%Y%m%d_%H%M%S". format of the time suffix.
    """
    time_format = "%Y%m%d_%H%M%S"
    if not config.get("multi", False):
        paths: List[str] = [config["path"]]
        dests: List[str] = [config["dest"]]
        if config.get("time_suffix", False):
            time_format = config.get("time_format", time_format)
            # Insert time before file extension.
            dests = [f"{os.path.splitext(d)[0]}_{datetime.now().strftime(time_format)}{os.path.splitext(d)[1]}" for d in dests]
    else:
        paths: List[str] = config["path"]
        dests: List[str] = config["dest"]


    cache_paths: List[str] = []

    gives: Set[int] = set(config.get("gives", [0]))

    for i, (p, d) in enumerate(zip(paths, dests)):
        _path = os.path.join(env.cache_dir, d)
        
        try:
            # Try to get file from VM
            file = env.controller.get_file(p)
            if file is None:
                logger.warning(f"Failed to get file from VM: {p}")
                if i in gives:
                    cache_paths.append(None)
                continue

            if i in gives:
                cache_paths.append(_path)
                
            # Write file with robust error handling
            try:
                # Ensure cache directory exists
                os.makedirs(env.cache_dir, exist_ok=True)
                
                tmp_path = f"{_path}.tmp.{uuid.uuid4().hex}"
                try:
                    with open(tmp_path, "wb") as f:
                        f.write(file)
                    os.replace(tmp_path, _path)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                logger.info(f"Successfully saved file: {_path} ({len(file)} bytes)")
                
            except IOError as e:
                logger.error(f"IO error writing file {_path}: {e}")
                if i in gives:
                    cache_paths[-1] = None  # Replace the path we just added with None
            except Exception as e:
                logger.error(f"Unexpected error writing file {_path}: {e}")
                if i in gives:
                    cache_paths[-1] = None
                    
        except Exception as e:
            logger.error(f"Error processing file {p}: {e}")
            if i in gives:
                cache_paths.append(None)
                
    return cache_paths[0] if len(cache_paths)==1 else cache_paths
```

### `import:logging` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L1-L1`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:ET` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L2-L2`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `d8313b379a858f183008f2f6198051d5bd7ca075d573902814a9666bfda819eb`

```python
import xml.etree.ElementTree as ET
```

### `import:Presentation` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L6-L6`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `281b02f27f075fa4c668f888b61ff549b4ae9ad55b0de0785c89a0021616c871`

```python
from pptx import Presentation
```

### `import:MSO_SHAPE_TYPE` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L8-L8`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `a6956d87bc9da410d3af4faf99065fbf5eed4c47fbaf595edf6e9893d7d53659`

```python
from pptx.enum.shapes import MSO_SHAPE_TYPE
```

### `debug_logger` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L26-L26`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `dd82f07b29844394e5225021be720cf3fbc1ffd7948e82e9a61a3ec2372731ea`

```python
debug_logger = logging.getLogger("desktopenv.metric.slides.debug")
```

### `enable_debug_logging` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L28-L35`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `72e23040aeca579da858c64ae38ff72a630ec83a001d7d4524f2bf38fbdb9245`

```python
def enable_debug_logging():
    """Enable detailed debug logging for PPTX comparison"""
    debug_logger.setLevel(logging.DEBUG)
    if not debug_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        debug_logger.addHandler(handler)
```

### `get_all_text_shapes` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L166-L187`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `e6de90e8888765bcb1a6a8da7f553ddbf7c6eaf270e81c0963fa478a803e6cce`

```python
def get_all_text_shapes(slide):
    """递归获取slide中所有包含文本的shapes，包括GROUP内部的"""
    
    def extract_text_shapes(shape):
        results = []
        
        # 检查当前shape是否有文本
        if hasattr(shape, "text") and hasattr(shape, "text_frame"):
            results.append(shape)
        
        # 如果是GROUP，递归检查内部shapes
        if hasattr(shape, 'shapes'):
            for sub_shape in shape.shapes:
                results.extend(extract_text_shapes(sub_shape))
        
        return results
    
    all_text_shapes = []
    for shape in slide.shapes:
        all_text_shapes.extend(extract_text_shapes(shape))
    
    return all_text_shapes
```

### `compare_pptx_files` from `official/desktop_env/evaluators/metrics/slides.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/slides.py#L190-L756`

Full source SHA-256: `189c0cab3f7eefdb340ec597248942a176814b8a92a442fd97f6b4a6df4ace41`

Exact excerpt SHA-256: `8d4bd9d990460a2d20dd06e053908df7bce879367f000116701fd2307a13a082`

```python
def compare_pptx_files(file1_path, file2_path, **options):
    # todo: not strictly match since not all information is compared because we cannot get the info through pptx
    prs1 = Presentation(file1_path)
    prs2 = Presentation(file2_path)

    # Enable debug logging if requested
    enable_debug = options.get("enable_debug", True)
    if enable_debug:
        enable_debug_logging()
        debug_logger.debug(f"=== COMPARING PPTX FILES ===")
        debug_logger.debug(f"File 1: {file1_path}")
        debug_logger.debug(f"File 2: {file2_path}")
        debug_logger.debug(f"File 1 slides: {len(prs1.slides)}")
        debug_logger.debug(f"File 2 slides: {len(prs2.slides)}")

    approximately_tolerance = options.get("approximately_tolerance", 0.005)
    
    def is_approximately_equal(val1, val2, tolerance=approximately_tolerance):
        """Compare two values with a tolerance of 0.1% (0.005)"""
        if val1 == val2:
            return True
        if val1 == 0 and val2 == 0:
            return True
        if val1 == 0 or val2 == 0:
            return False
        return abs(val1 - val2) / max(abs(val1), abs(val2)) <= tolerance
    
    def nonempty_runs(para):
        """Filter out runs that only contain formatting and no text"""
        return [r for r in para.runs if (r.text or "").strip() != ""]

    examine_number_of_slides = options.get("examine_number_of_slides", True)
    examine_shape = options.get("examine_shape", True)
    examine_text = options.get("examine_text", True)
    examine_indent = options.get("examine_indent", True)
    examine_font_name = options.get("examine_font_name", True)
    examine_font_size = options.get("examine_font_size", True)
    examine_font_bold = options.get("examine_font_bold", True)
    examine_font_italic = options.get("examine_font_italic", True)
    examine_color_rgb = options.get("examine_color_rgb", True)
    examine_font_underline = options.get("examine_font_underline", True)
    examine_strike_through = options.get("examine_strike_through", True)
    examine_alignment = options.get("examine_alignment", True)
    examine_title_bottom_position = options.get("examine_title_bottom_position", False)
    examine_table_bottom_position = options.get("examine_table_bottom_position", False)
    examine_run_count = options.get("examine_run_count", True)
    examine_right_position = options.get("examine_right_position", False)
    examine_top_position = options.get("examine_top_position", False)
    examine_shape_for_shift_size = options.get("examine_shape_for_shift_size", False)
    examine_image_size = options.get("examine_image_size", False)
    examine_modify_height = options.get("examine_modify_height", False)
    examine_bullets = options.get("examine_bullets", True)
    examine_background_color = options.get("examine_background_color", True)
    examine_note = options.get("examine_note", True)

    # compare the number of slides
    if len(prs1.slides) != len(prs2.slides) and examine_number_of_slides:
        if enable_debug:
            debug_logger.debug(f"MISMATCH: Number of slides differ - File1: {len(prs1.slides)}, File2: {len(prs2.slides)}")
        return 0

    slide_idx = 0
    # compare the content of each slide
    for slide1, slide2 in zip(prs1.slides, prs2.slides):
        slide_idx += 1
        if enable_debug:
            debug_logger.debug(f"--- Comparing Slide {slide_idx} ---")
            debug_logger.debug(f"Slide {slide_idx} - Shapes count: File1={len(slide1.shapes)}, File2={len(slide2.shapes)}")

        def get_slide_background_color(slide):
            # background = slide.background
            # if background.fill.background():
            #     return background.fill.fore_color.rgb
            # else:
            #     return None
            fill = slide.background.fill
            if fill.type == 1:
                return fill.fore_color.rgb
            elif fill.type == 5:
                master_fill = slide.slide_layout.slide_master.background.fill
                if master_fill.type == 1:
                    return master_fill.fore_color.rgb
                else:
                    return None
            else:
                return None

        if get_slide_background_color(slide1) != get_slide_background_color(slide2) and examine_background_color:
            return 0

        def get_slide_notes(slide):
            notes_slide = slide.notes_slide
            if notes_slide:
                return notes_slide.notes_text_frame.text
            else:
                return None

        if get_slide_notes(slide1).strip() != get_slide_notes(slide2).strip() and examine_note:
            if enable_debug:
                debug_logger.debug(f"    MISMATCH: Slide {slide_idx} - Notes differ:")
                debug_logger.debug(f"      Notes1: '{get_slide_notes(slide1).strip()}'")
                debug_logger.debug(f"      Notes2: '{get_slide_notes(slide2).strip()}'")
            return 0

        # Get all text shapes including those inside GROUPs
        text_shapes1 = get_all_text_shapes(slide1)
        text_shapes2 = get_all_text_shapes(slide2)
        
        if enable_debug:
            debug_logger.debug(f"Slide {slide_idx} - Text shapes found: File1={len(text_shapes1)}, File2={len(text_shapes2)}")
        
        # check if the number of slides is the same
        if len(slide1.shapes) != len(slide2.shapes):
            if enable_debug:
                debug_logger.debug(f"MISMATCH: Slide {slide_idx} - Different number of shapes: File1={len(slide1.shapes)}, File2={len(slide2.shapes)}")
            return 0

        # check if the shapes are the same
        shape_idx = 0
        for shape1, shape2 in zip(slide1.shapes, slide2.shapes):
            shape_idx += 1
            if enable_debug:
                debug_logger.debug(f"  Shape {shape_idx} - Type: {shape1.shape_type} vs {shape2.shape_type}")
                if hasattr(shape1, "text") and hasattr(shape2, "text"):
                    debug_logger.debug(f"  Shape {shape_idx} - Text: '{shape1.text.strip()}' vs '{shape2.text.strip()}'")
                    debug_logger.debug(f"  Shape {shape_idx} - Position: ({shape1.left}, {shape1.top}) vs ({shape2.left}, {shape2.top})")
                    debug_logger.debug(f"  Shape {shape_idx} - Size: ({shape1.width}, {shape1.height}) vs ({shape2.width}, {shape2.height})")
            if examine_title_bottom_position:
                if hasattr(shape1, "text") and hasattr(shape2, "text") and shape1.text == shape2.text:
                    if shape1.text == "Product Comparison" and (shape1.top <= shape2.top or shape1.top < 3600000):
                        return 0
                elif (not is_approximately_equal(shape1.left, shape2.left) or 
                      not is_approximately_equal(shape1.top, shape2.top) or 
                      not is_approximately_equal(shape1.width, shape2.width) or 
                      not is_approximately_equal(shape1.height, shape2.height)):
                    return 0

            if examine_table_bottom_position:
                if slide_idx == 3 and shape1.shape_type == 19 and shape2.shape_type == 19:
                    if shape1.top <= shape2.top or shape1.top < 3600000:
                        return 0
                elif (not is_approximately_equal(shape1.left, shape2.left) or 
                      not is_approximately_equal(shape1.top, shape2.top) or 
                      not is_approximately_equal(shape1.width, shape2.width) or 
                      not is_approximately_equal(shape1.height, shape2.height)):
                    return 0

            if examine_right_position:
                if slide_idx == 2 and not hasattr(shape1, "text") and not hasattr(shape2, "text"):
                    if shape1.left <= shape2.left or shape1.left < 4320000:
                        return 0

            if examine_top_position:
                if slide_idx == 2 and shape1.shape_type == 13 and shape2.shape_type == 13:
                    if shape1.top >= shape2.top or shape1.top > 1980000:
                        return 0


            if examine_shape_for_shift_size:
                if (not is_approximately_equal(shape1.left, shape2.left) or 
                    not is_approximately_equal(shape1.top, shape2.top) or 
                    not is_approximately_equal(shape1.width, shape2.width) or 
                    not is_approximately_equal(shape1.height, shape2.height)):
                    if not (hasattr(shape1, "text") and hasattr(shape2,
                                                                "text") and shape1.text == shape2.text and shape1.text == "Elaborate on what you want to discuss."):
                        return 0

            # CRITICAL: examine_shape check happens BEFORE examine_modify_height!
            # If examine_shape=True (default), any shape dimension mismatch will cause immediate return 0,
            # preventing examine_modify_height from ever being executed.
            # For height modification tasks, you MUST set examine_shape=False to allow examine_modify_height to work.

            # Skip dimension check for shapes with no text (decorative/empty) - they often differ between saves or LibreOffice versions and are irrelevant to content-focused tasks.
            both_empty_text = (
                (not getattr(shape1, "text", None) or (shape1.text or "").strip() == "") and
                (not getattr(shape2, "text", None) or (shape2.text or "").strip() == "")
            )

            if (
                    not is_approximately_equal(shape1.left, shape2.left) or
                    not is_approximately_equal(shape1.top, shape2.top) or
                    not is_approximately_equal(shape1.width, shape2.width) or
                    not is_approximately_equal(shape1.height, shape2.height)) and examine_shape and not both_empty_text:
                if enable_debug:
                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} - Shape dimensions differ:")
                    debug_logger.debug(f"      Left: {shape1.left} vs {shape2.left} (equal: {is_approximately_equal(shape1.left, shape2.left)})")
                    debug_logger.debug(f"      Top: {shape1.top} vs {shape2.top} (equal: {is_approximately_equal(shape1.top, shape2.top)})")
                    debug_logger.debug(f"      Width: {shape1.width} vs {shape2.width} (equal: {is_approximately_equal(shape1.width, shape2.width)})")
                    debug_logger.debug(f"      Height: {shape1.height} vs {shape2.height} (equal: {is_approximately_equal(shape1.height, shape2.height)})")
                    if hasattr(shape1, "text") and hasattr(shape2, "text"):
                        debug_logger.debug(f"      Shape text: '{shape1.text.strip()}' vs '{shape2.text.strip()}'")
                return 0

            if examine_image_size:
                if shape1.shape_type == 13 and shape2.shape_type == 13:
                    if not is_approximately_equal(shape1.width, shape2.width) or not is_approximately_equal(shape1.height, shape2.height):
                        return 0
                elif (not is_approximately_equal(shape1.left, shape2.left) or 
                      not is_approximately_equal(shape1.top, shape2.top) or 
                      not is_approximately_equal(shape1.width, shape2.width) or 
                      not is_approximately_equal(shape1.height, shape2.height)):
                    return 0

            # examine_modify_height: Special logic for height modification tasks
            # - For non-text shapes and FREEFORM shapes (type 5): Only check height differences
            # - For other shapes: Check all dimensions (left, top, width, height)
            # WARNING: This check only works if examine_shape=False, otherwise examine_shape will
            # terminate the comparison before this code is reached!
            if examine_modify_height:
                if not hasattr(shape1, "text") and not hasattr(shape2,
                                                               "text") or shape1.shape_type == 5 and shape2.shape_type == 5:
                    if not is_approximately_equal(shape1.height, shape2.height):
                        return 0
                elif (not is_approximately_equal(shape1.left, shape2.left) or 
                      not is_approximately_equal(shape1.top, shape2.top) or 
                      not is_approximately_equal(shape1.width, shape2.width) or 
                      not is_approximately_equal(shape1.height, shape2.height)):
                    return 0

            if shape1.shape_type == MSO_SHAPE_TYPE.TABLE:
                table1 = shape1.table
                table2 = shape2.table
                if enable_debug:
                    debug_logger.debug(f"  Shape {shape_idx} - Comparing TABLE with {len(table1.rows)} rows and {len(table1.columns)} columns")
                    debug_logger.debug(f"  Shape {shape_idx} - Table2 has {len(table2.rows)} rows and {len(table2.columns)} columns")
                
                # Check if tables have the same dimensions
                if len(table1.rows) != len(table2.rows) or len(table1.columns) != len(table2.columns):
                    if enable_debug:
                        debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Table dimensions differ:")
                        debug_logger.debug(f"      Table1: {len(table1.rows)} rows x {len(table1.columns)} columns")
                        debug_logger.debug(f"      Table2: {len(table2.rows)} rows x {len(table2.columns)} columns")
                    return 0
                
                for row_idx in range(len(table1.rows)):
                    for col_idx in range(len(table1.columns)):
                        cell1 = table1.cell(row_idx, col_idx)
                        cell2 = table2.cell(row_idx, col_idx)

                        # Check if cells have the same number of paragraphs
                        if len(cell1.text_frame.paragraphs) != len(cell2.text_frame.paragraphs):
                            if enable_debug:
                                debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}] - Different number of paragraphs:")
                                debug_logger.debug(f"      Cell1 paragraphs: {len(cell1.text_frame.paragraphs)}")
                                debug_logger.debug(f"      Cell2 paragraphs: {len(cell2.text_frame.paragraphs)}")
                            return 0

                        for para_idx, (para1, para2) in enumerate(zip(cell1.text_frame.paragraphs, cell2.text_frame.paragraphs)):
                            # Check if paragraphs have the same number of runs
                            runs1 = para1.runs
                            runs2 = para2.runs
                            if (para1.text or "").strip() == "" and (para2.text or "").strip() == "":
                                runs1 = nonempty_runs(para1)
                                runs2 = nonempty_runs(para2)

                            if len(runs1) != len(runs2) and examine_run_count:
                                if enable_debug:
                                    debug_logger.debug(
                                        f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx} - Different number of runs:"
                                    )
                                    debug_logger.debug(f"      Para1 runs: {len(runs1)}")
                                    debug_logger.debug(f"      Para2 runs: {len(runs2)}")
                                return 0

                            for run_idx, (run1, run2) in enumerate(zip(runs1, runs2)):
                                # Check font color
                                if hasattr(run1.font.color, "rgb") and hasattr(run2.font.color, "rgb"):
                                    if run1.font.color.rgb != run2.font.color.rgb and examine_color_rgb:
                                        if enable_debug:
                                            debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx}, Run {run_idx} - Font color differs:")
                                            debug_logger.debug(f"      Color1: {run1.font.color.rgb} vs Color2: {run2.font.color.rgb}")
                                            debug_logger.debug(f"      Cell text: '{cell1.text.strip()}' vs '{cell2.text.strip()}'")
                                            debug_logger.debug(f"      Run text: '{run1.text}' vs '{run2.text}'")
                                        return 0
                                
                                # Check font bold
                                if run1.font.bold != run2.font.bold:
                                    if not ((run1.font.bold is None or run1.font.bold is False) and 
                                           (run2.font.bold is None or run2.font.bold is False)):
                                        if enable_debug:
                                            debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx}, Run {run_idx} - Font bold differs:")
                                            debug_logger.debug(f"      Bold1: {run1.font.bold} vs Bold2: {run2.font.bold}")
                                            debug_logger.debug(f"      Run text: '{run1.text}' vs '{run2.text}'")
                                        return 0
                                
                                # Check font italic
                                if run1.font.italic != run2.font.italic:
                                    if not ((run1.font.italic is None or run1.font.italic is False) and 
                                           (run2.font.italic is None or run2.font.italic is False)):
                                        if enable_debug:
                                            debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx}, Run {run_idx} - Font italic differs:")
                                            debug_logger.debug(f"      Italic1: {run1.font.italic} vs Italic2: {run2.font.italic}")
                                            debug_logger.debug(f"      Run text: '{run1.text}' vs '{run2.text}'")
                                        return 0
                                
                                # Check font underline
                                if run1.font.underline != run2.font.underline:
                                    if run1.font.underline is not None and run2.font.underline is not None:
                                        if enable_debug:
                                            debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx}, Run {run_idx} - Font underline differs:")
                                            debug_logger.debug(f"      Underline1: {run1.font.underline} vs Underline2: {run2.font.underline}")
                                            debug_logger.debug(f"      Run text: '{run1.text}' vs '{run2.text}'")
                                        return 0
                                    if (run1.font.underline is None and run2.font.underline is True) or (run1.font.underline is True and run2.font.underline is None):
                                        if enable_debug:
                                            debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} (TABLE) - Cell [{row_idx},{col_idx}], Para {para_idx}, Run {run_idx} - Font underline differs (None vs True):")
                                            debug_logger.debug(f"      Underline1: {run1.font.underline} vs Underline2: {run2.font.underline}")
                                            debug_logger.debug(f"      Run text: '{run1.text}' vs '{run2.text}'")
                                        return 0

            if hasattr(shape1, "text") and hasattr(shape2, "text"):
                if shape1.text.strip() != shape2.text.strip() and examine_text:
                    return 0

                # check if the number of paragraphs are the same
                if len(shape1.text_frame.paragraphs) != len(shape2.text_frame.paragraphs):
                    if enable_debug:
                        debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx} - Different number of paragraphs:")
                        debug_logger.debug(f"      Shape1 paragraphs: {len(shape1.text_frame.paragraphs)}")
                        debug_logger.debug(f"      Shape2 paragraphs: {len(shape2.text_frame.paragraphs)}")
                    return 0

                    # check if the paragraphs are the same
                para_idx = 0
                for para1, para2 in zip(shape1.text_frame.paragraphs, shape2.text_frame.paragraphs):
                    para_idx += 1
                    # Handle alignment comparison - treat None and LEFT (1) as equivalent
                    if examine_alignment:
                        from pptx.enum.text import PP_ALIGN
                        align1 = para1.alignment
                        align2 = para2.alignment
                        
                        if enable_debug:
                            align1_name = "None" if align1 is None else getattr(align1, 'name', str(align1))
                            align2_name = "None" if align2 is None else getattr(align2, 'name', str(align2))
                            debug_logger.debug(f"    Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Alignment: '{align1_name}' vs '{align2_name}'")
                            debug_logger.debug(f"    Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Text: '{para1.text}' vs '{para2.text}'")
                        
                        # Convert None to LEFT for comparison since None means default left alignment
                        if align1 is None:
                            align1 = PP_ALIGN.LEFT  # LEFT alignment
                        if align2 is None:
                            align2 = PP_ALIGN.LEFT  # LEFT alignment
                            
                        if align1 != align2:
                            if enable_debug:
                                align1_final = getattr(align1, 'name', str(align1))
                                align2_final = getattr(align2, 'name', str(align2))
                                debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Alignment differs: '{align1_final}' vs '{align2_final}'")
                            return 0

                    # check if the runs are the same
                    if para1.text != para2.text and examine_text:
                        return 0

                    if para1.level != para2.level and examine_indent:
                        # Allow 0 vs 1 (or None vs 1): same visual "continuation" indent, different XML.
                        n1 = 0 if para1.level is None else para1.level
                        n2 = 0 if para2.level is None else para2.level
                        if not (n1 in (0, 1) and n2 in (0, 1)):
                            return 0

                    # check if the number of runs are the same
                    # Normalize runs for empty paragraphs: treat 0 runs vs 1 empty run as equivalent
                    runs1 = para1.runs
                    runs2 = para2.runs
                    if (para1.text or "").strip() == "" and (para2.text or "").strip() == "":
                        runs1 = nonempty_runs(para1)
                        runs2 = nonempty_runs(para2)

                    # check if the number of runs are the same
                    if len(runs1) != len(runs2) and examine_run_count:
                        if enable_debug:
                            debug_logger.debug(
                                f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Different number of runs:"
                            )
                            debug_logger.debug(f"      Para1 runs: {len(runs1)}")
                            debug_logger.debug(f"      Para2 runs: {len(runs2)}")
                        return 0

                    for run1, run2 in zip(runs1, runs2):

                        # check if the font properties are the same                        
                        if run1.font.name != run2.font.name and examine_font_name:
                            if enable_debug:
                                debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font name differs:")
                                debug_logger.debug(f"      Name1: '{run1.font.name}' vs Name2: '{run2.font.name}'")
                                debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                            return 0

                        if run1.font.size != run2.font.size and examine_font_size:
                            if enable_debug:
                                debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font size differs:")
                                debug_logger.debug(f"      Size1: {run1.font.size} vs Size2: {run2.font.size}")
                                debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                            return 0

                        if run1.font.bold != run2.font.bold and examine_font_bold:
                            # Special handling for None vs False - both mean "not bold"
                            if not ((run1.font.bold is None or run1.font.bold is False) and 
                                   (run2.font.bold is None or run2.font.bold is False)):
                                if enable_debug:
                                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font bold differs:")
                                    debug_logger.debug(f"      Bold1: {run1.font.bold} vs Bold2: {run2.font.bold}")
                                    debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                                return 0

                        if run1.font.italic != run2.font.italic and examine_font_italic:
                            # Special handling for None vs False - both mean "not italic"
                            if not ((run1.font.italic is None or run1.font.italic is False) and 
                                   (run2.font.italic is None or run2.font.italic is False)):
                                if enable_debug:
                                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font italic differs:")
                                    debug_logger.debug(f"      Italic1: {run1.font.italic} vs Italic2: {run2.font.italic}")
                                    debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                                return 0

                        if hasattr(run1.font.color, "rgb") and hasattr(run2.font.color, "rgb"):
                            if run1.font.color.rgb != run2.font.color.rgb and examine_color_rgb:
                                if enable_debug:
                                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font color differs:")
                                    debug_logger.debug(f"      Color1: {run1.font.color.rgb} vs Color2: {run2.font.color.rgb}")
                                    debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                                return 0

                        if run1.font.underline != run2.font.underline and examine_font_underline:
                            if run1.font.underline is not None and run2.font.underline is not None:
                                if enable_debug:
                                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font underline differs:")
                                    debug_logger.debug(f"      Underline1: {run1.font.underline} vs Underline2: {run2.font.underline}")
                                    debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                                return 0
                            if (run1.font.underline is None and run2.font.underline is True) or (run1.font.underline is True and run2.font.underline is None):
                                if enable_debug:
                                    debug_logger.debug(f"    MISMATCH: Slide {slide_idx}, Shape {shape_idx}, Para {para_idx} - Font underline differs (None vs True):")
                                    debug_logger.debug(f"      Underline1: {run1.font.underline} vs Underline2: {run2.font.underline}")
                                    debug_logger.debug(f"      Text: '{run1.text}' vs '{run2.text}'")
                                return 0
                                
                        if run1.font._element.attrib.get('strike', 'noStrike') != run2.font._element.attrib.get(
                                'strike', 'noStrike') and examine_strike_through:
                            return 0

                        def _extract_bullets(xml_data):
                            root = ET.fromstring(xml_data)

                            namespaces = {
                                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                                'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                            }

                            bullets = []

                            for paragraph in root.findall('.//a:p', namespaces):
                                pPr = paragraph.find('a:pPr', namespaces)
                                if pPr is not None:
                                    lvl = pPr.get('lvl')
                                    buChar = pPr.find('a:buChar', namespaces)
                                    char = buChar.get('char') if buChar is not None else "No Bullet"
                                    buClr = pPr.find('a:buClr/a:srgbClr', namespaces)
                                    color = buClr.get('val') if buClr is not None else "No Color"
                                else:
                                    lvl = "No Level"
                                    char = "No Bullet"
                                    color = "No Color"

                                text = "".join(t.text for t in paragraph.findall('.//a:t', namespaces))
                                
                                # Only add non-empty paragraphs to bullets list
                                if text.strip():
                                    bullets.append((lvl, char, text, color))

                            return bullets

                        def _compare_bullets_with_tolerance(bullets1, bullets2):
                            """Compare bullets with tolerance for minor differences"""
                            if len(bullets1) != len(bullets2):
                                return False
                            
                            for (lvl1, char1, text1, color1), (lvl2, char2, text2, color2) in zip(bullets1, bullets2):
                                # Compare text (most important)
                                if text1 != text2:
                                    return False
                                
                                # Compare bullet character
                                if char1 != char2:
                                    return False
                                
                                # Compare level only when at least one has a visible bullet.
                                # When both have "No Bullet", level/color can differ in XML (None vs '1',
                                # 'No Color' vs '000000') while the slide looks identical.
                                if char1 != "No Bullet" or char2 != "No Bullet":
                                    normalized_lvl1 = '0' if lvl1 is None else lvl1
                                    normalized_lvl2 = '0' if lvl2 is None else lvl2
                                    if normalized_lvl1 != normalized_lvl2:
                                        return False
                                
                                # Color comparison is more lenient - we don't fail on color differences
                                # since they might be due to theme or formatting differences
                                # if color1 != color2:
                                #     return False
                            
                            return True

                        if examine_bullets:
                            try:
                                bullets1 = _extract_bullets(run1.part.blob.decode('utf-8'))
                                bullets2 = _extract_bullets(run2.part.blob.decode('utf-8'))
                                
                                # Compare bullets with tolerance for minor differences
                                if not _compare_bullets_with_tolerance(bullets1, bullets2):
                                    return 0
                            except:
                                # If bullet extraction fails, skip bullet comparison
                                pass

                    # fixme: Actually there are more properties to be compared, we can add them later via parsing the xml data

        # Additional check: compare all text shapes including those in GROUPs
        if examine_alignment and len(text_shapes1) == len(text_shapes2):
            for idx, (tshape1, tshape2) in enumerate(zip(text_shapes1, text_shapes2)):
                if enable_debug:
                    debug_logger.debug(f"  Additional text shape check {idx+1}: '{tshape1.text.strip()[:30]}' vs '{tshape2.text.strip()[:30]}'")
                
                # Compare text content
                if tshape1.text.strip() != tshape2.text.strip() and examine_text:
                    if enable_debug:
                        debug_logger.debug(f"    MISMATCH: Text differs - '{tshape1.text.strip()}' vs '{tshape2.text.strip()}'")
                    return 0
                
                # Check if text shapes have the same number of paragraphs
                if len(tshape1.text_frame.paragraphs) != len(tshape2.text_frame.paragraphs):
                    if enable_debug:
                        debug_logger.debug(f"    MISMATCH: Different number of paragraphs - {len(tshape1.text_frame.paragraphs)} vs {len(tshape2.text_frame.paragraphs)}")
                    return 0
                
                # Compare alignment of each paragraph
                for para_idx, (para1, para2) in enumerate(zip(tshape1.text_frame.paragraphs, tshape2.text_frame.paragraphs)):
                    from pptx.enum.text import PP_ALIGN
                    align1 = para1.alignment
                    align2 = para2.alignment
                    
                    if enable_debug:
                        align1_name = "None" if align1 is None else getattr(align1, 'name', str(align1))
                        align2_name = "None" if align2 is None else getattr(align2, 'name', str(align2))
                        debug_logger.debug(f"    Para {para_idx+1}: Alignment '{align1_name}' vs '{align2_name}'")
                    
                    # Convert None to LEFT for comparison
                    if align1 is None:
                        align1 = PP_ALIGN.LEFT
                    if align2 is None:
                        align2 = PP_ALIGN.LEFT
                        
                    if align1 != align2:
                        if enable_debug:
                            align1_final = getattr(align1, 'name', str(align1))
                            align2_final = getattr(align2, 'name', str(align2))
                            debug_logger.debug(f"    MISMATCH: Alignment differs - '{align1_final}' vs '{align2_final}'")
                        return 0
        elif len(text_shapes1) != len(text_shapes2):
            if enable_debug:
                debug_logger.debug(f"MISMATCH: Different number of text shapes - {len(text_shapes1)} vs {len(text_shapes2)}")
            return 0
    
    if enable_debug:
        debug_logger.debug(f"=== COMPARISON SUCCESSFUL - Files match ===")
    return 1
```
