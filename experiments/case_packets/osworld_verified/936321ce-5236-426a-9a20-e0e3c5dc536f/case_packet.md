# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `936321ce-5236-426a-9a20-e0e3c5dc536f`
- task_id: `936321ce-5236-426a-9a20-e0e3c5dc536f`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `libreoffice_writer`
- snapshot: `libreoffice_writer`
- related apps: `libreoffice_writer`
- official instruction: Could you help me convert the text seperated by commas to a table?
- evaluator functions: `compare_docx_tables, compare_docx_tables`
- evaluator conjunction: `or`
- evaluator result getter types: `vm_file, vm_file`
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
- `official/desktop_env/evaluators/metrics/docs.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/libreoffice_writer/936321ce-5236-426a-9a20-e0e3c5dc536f.json`

Source SHA-256: `31a7eea1d9b457dc478b5c43d15cd294cfe7e6dcedd64d0d7aa41bcdbcaad53e`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/Graphemes_Sound_Letter_Patterns.docx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_writer/936321ce-5236-426a-9a20-e0e3c5dc536f/Graphemes_Sound_Letter_Patterns.docx"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "path": "/home/user/Desktop/Graphemes_Sound_Letter_Patterns.docx"
      },
      "type": "open"
    }
  ],
  "evaluator": {
    "conj": "or",
    "expected": [
      {
        "dest": "Graphemes_Sound_Letter_Patterns_Gold.docx",
        "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_writer/936321ce-5236-426a-9a20-e0e3c5dc536f/Graphemes_Sound_Letter_Patterns_Gold.docx",
        "type": "cloud_file"
      },
      {
        "dest": "Graphemes_Sound_Letter_Patterns_Gold_2.docx",
        "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_writer/936321ce-5236-426a-9a20-e0e3c5dc536f/Graphemes_Sound_Letter_Patterns_Gold_2.docx",
        "type": "cloud_file"
      }
    ],
    "func": [
      "compare_docx_tables",
      "compare_docx_tables"
    ],
    "postconfig": [
      {
        "parameters": {
          "strict": true,
          "window_name": "Graphemes_Sound_Letter_Patterns_Gold.docx - LibreOffice Writer"
        },
        "type": "activate_window"
      },
      {
        "parameters": {
          "seconds": 0.5
        },
        "type": "sleep"
      },
      {
        "parameters": {
          "command": [
            "python",
            "-c",
            "import pyautogui; import time; pyautogui.hotkey('ctrl', 's'); time.sleep(2); "
          ]
        },
        "type": "execute"
      }
    ],
    "result": [
      {
        "dest": "Graphemes_Sound_Letter_Patterns.docx",
        "path": "/home/user/Desktop/Graphemes_Sound_Letter_Patterns.docx",
        "type": "vm_file"
      },
      {
        "dest": "Graphemes_Sound_Letter_Patterns.docx",
        "path": "/home/user/Desktop/Graphemes_Sound_Letter_Patterns.docx",
        "type": "vm_file"
      }
    ]
  },
  "fixed_ip": false,
  "id": "936321ce-5236-426a-9a20-e0e3c5dc536f",
  "instruction": "Could you help me convert the text seperated by commas to a table?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "libreoffice_writer"
  ],
  "snapshot": "libreoffice_writer",
  "source": "https://www.youtube.com/watch?v=l25Evu4ohKg",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `af951f8b64ad7bd24216b31625eb046b55de597f86ad7b749174d636e339e5e0`

```json
{
  "conjunction": "or",
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
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/docs.py"
    },
    {
      "end_line": 15,
      "excerpt_sha256": "5644387c433e29ad581fec911a47b06314be5deae2a535a70db9ae3127879ea8",
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db",
      "start_line": 15,
      "symbol": "import:Document",
      "upstream_path": "desktop_env/evaluators/metrics/docs.py"
    },
    {
      "end_line": 25,
      "excerpt_sha256": "462ad042fe4e5a1e40b16e7059e12d3c2e656451f1f4ff491b966a4aa98980e5",
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db",
      "start_line": 25,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/docs.py"
    },
    {
      "end_line": 337,
      "excerpt_sha256": "b9769436481141b0de0daf8f7d6828641addc305f23f1f38ce1ad30a1411e88e",
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db",
      "start_line": 307,
      "symbol": "compare_docx_tables",
      "upstream_path": "desktop_env/evaluators/metrics/docs.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected[0]",
      "config_sha256": "115de4431406944b1d9be5190a4f7a12d578d83ecd1a3341f5477c59f54149a6",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    },
    {
      "config_path": "evaluator.expected[1]",
      "config_sha256": "0ee3ec16dd414d7ddadf936587dde5a56fb7f30a424a2dcad656723515f0aa0b",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "c186975a1b8a76f2720e5a247d43bb9c08f1554f37e1f147531b83b85317be58",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": true,
  "metric_options": null,
  "metrics": [
    {
      "name": "compare_docx_tables",
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db"
    },
    {
      "name": "compare_docx_tables",
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "source_sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db"
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
      "packet_path": "official/desktop_env/evaluators/metrics/docs.py",
      "sha256": "e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py",
      "upstream_path": "desktop_env/evaluators/metrics/docs.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result[0]",
      "config_sha256": "89242bf0298c7a3da424c560e52dea5e0cb1e3a748331155cf2af0b03aa39412",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_vm_file",
      "type": "vm_file"
    },
    {
      "config_path": "evaluator.result[1]",
      "config_sha256": "89242bf0298c7a3da424c560e52dea5e0cb1e3a748331155cf2af0b03aa39412",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 1,
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
  "task_id": "936321ce-5236-426a-9a20-e0e3c5dc536f"
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

### `import:logging` from `official/desktop_env/evaluators/metrics/docs.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py#L1-L1`

Full source SHA-256: `e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Document` from `official/desktop_env/evaluators/metrics/docs.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py#L15-L15`

Full source SHA-256: `e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db`

Exact excerpt SHA-256: `5644387c433e29ad581fec911a47b06314be5deae2a535a70db9ae3127879ea8`

```python
from docx import Document
```

### `logger` from `official/desktop_env/evaluators/metrics/docs.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py#L25-L25`

Full source SHA-256: `e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db`

Exact excerpt SHA-256: `462ad042fe4e5a1e40b16e7059e12d3c2e656451f1f4ff491b966a4aa98980e5`

```python
logger = logging.getLogger("desktopenv.metric.docs")
```

### `compare_docx_tables` from `official/desktop_env/evaluators/metrics/docs.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/docs.py#L307-L337`

Full source SHA-256: `e19d98130d838c5f20424e2d9da9e2e7ef496cd08f938884772e430f87f383db`

Exact excerpt SHA-256: `b9769436481141b0de0daf8f7d6828641addc305f23f1f38ce1ad30a1411e88e`

```python
def compare_docx_tables(docx_file1, docx_file2):
    if not docx_file1 or not docx_file2:
        return 0

    try:
        doc1 = Document(docx_file1)
        doc2 = Document(docx_file2)
    except Exception as e:
        logger.error(f"Error: {e}")
        return 0

    # get list of tables in docx
    tables1 = doc1.tables
    tables2 = doc2.tables

    if len(tables1) != len(tables2):
        return 0

    # Compare each table content
    for table1, table2 in zip(tables1, tables2):

        if len(table1.rows) != len(table2.rows) or len(table1.columns) != len(table2.columns):
            return 0

        # Compare each cell
        for i in range(len(table1.rows)):
            for j in range(len(table1.columns)):
                if table1.cell(i, j).text.strip() != table2.cell(i, j).text.strip():
                    return 0

    return 1
```
