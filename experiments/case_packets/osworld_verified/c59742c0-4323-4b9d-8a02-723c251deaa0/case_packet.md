# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `c59742c0-4323-4b9d-8a02-723c251deaa0`
- task_id: `c59742c0-4323-4b9d-8a02-723c251deaa0`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `libreoffice_impress`
- snapshot: `libreoffice_impress`
- related apps: `libreoffice_impress`
- official instruction: I am making PPT about the history of baseball. I want to add an introduction audio named "Baseball.mp3" on the Desktop into my PPT, but I do not know how. Could you help me add audio into my presentation file?
- evaluator functions: `compare_audios`
- evaluator conjunction: `and`
- evaluator result getter types: `audio_in_slide`
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
- `official/desktop_env/evaluators/getters/impress.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/vlc.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/libreoffice_impress/c59742c0-4323-4b9d-8a02-723c251deaa0.json`

Source SHA-256: `e8a9552c03d3a8a126bd24f77dc80876efe76dac9b92b6340a306c94a5d65913`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/Mady_and_Mia_Baseball.pptx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_impress/c59742c0-4323-4b9d-8a02-723c251deaa0/Mady_and_Mia_Baseball.pptx"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/Baseball.mp3",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_impress/c59742c0-4323-4b9d-8a02-723c251deaa0/Baseball.mp3"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "path": "/home/user/Desktop/Mady_and_Mia_Baseball.pptx"
      },
      "type": "open"
    }
  ],
  "evaluator": {
    "expected": {
      "dest": "Baseball_to_be_placed.mp3",
      "path": "/home/user/Desktop/Baseball.mp3",
      "type": "vm_file"
    },
    "func": "compare_audios",
    "postconfig": [
      {
        "parameters": {
          "strict": true,
          "window_name": "Mady_and_Mia_Baseball.pptx - LibreOffice Impress"
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
            "import pyautogui; import time; pyautogui.hotkey('ctrl', 's'); time.sleep(0.5);"
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
      "dest": "Baseball.mp3",
      "ppt_file_path": "/home/user/Desktop/Mady_and_Mia_Baseball.pptx",
      "slide_index": 0,
      "type": "audio_in_slide"
    }
  },
  "fixed_ip": false,
  "id": "c59742c0-4323-4b9d-8a02-723c251deaa0",
  "instruction": "I am making PPT about the history of baseball. I want to add an introduction audio named \"Baseball.mp3\" on the Desktop into my PPT, but I do not know how. Could you help me add audio into my presentation file?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "libreoffice_impress"
  ],
  "snapshot": "libreoffice_impress",
  "source": "https://www.reddit.com/r/libreoffice/comments/17lcdrp/audio_not_supported_in_libreoffice_impress/",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `0065f58e4c23af41d82e95d8b195062130c1ff1838cbc9d5bae4c1a3aa05e9ea`

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
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "start_line": 1,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "d8313b379a858f183008f2f6198051d5bd7ca075d573902814a9666bfda819eb",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "start_line": 3,
      "symbol": "import:ET",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "a61e3196c03ce192157fd97c256ec82a5f23c6e9bf8b9cf8514c41167e7d5318",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "start_line": 4,
      "symbol": "import:zipfile",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "start_line": 5,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
    },
    {
      "end_line": 126,
      "excerpt_sha256": "c30d8f547b876cde36e48e636d7e2894263f14d675fd2ddbc33ac6088ae56521",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "start_line": 71,
      "symbol": "get_audio_in_slide",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
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
      "end_line": 11,
      "excerpt_sha256": "69261ecb42288897c50c6a0d99741289108eb18e836e0c4f4c71d9dbd5c9541c",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 11,
      "symbol": "import:librosa",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
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
      "end_line": 14,
      "excerpt_sha256": "3a9004ec7b0b808235541e908e13643f42b825a356866462b9e9671eaca1a46c",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 14,
      "symbol": "import:fastdtw",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    },
    {
      "end_line": 15,
      "excerpt_sha256": "d201b34140a7f66dead595a001a4f3a5bd8dc0c2d69b9144f0b09bbc6a112f20",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 15,
      "symbol": "import:cosine",
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
      "end_line": 293,
      "excerpt_sha256": "82df34cba62bfc219f112d0f03c39a7116d9ba92440a14ac61d519ef8a1bf35b",
      "packet_path": "official/desktop_env/evaluators/metrics/vlc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py",
      "source_sha256": "a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e",
      "start_line": 226,
      "symbol": "compare_audios",
      "upstream_path": "desktop_env/evaluators/metrics/vlc.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "c1a4da0fe964789c971390f51052d31779d1004d6a12a94a718cd454b5f0a0c7",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_vm_file",
      "type": "vm_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "c0b32b7b0ce1581714fe54e7ddd1319a6bbde992b908bce1827fc701fc387d6f",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "compare_audios",
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
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "upstream_path": "desktop_env/evaluators/getters/impress.py"
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
      "config_sha256": "5d449d41e38030508df9cef03a09c7e03a42079dc8fd6100c759035617770bcd",
      "packet_path": "official/desktop_env/evaluators/getters/impress.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py",
      "source_sha256": "46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55",
      "symbol": "get_audio_in_slide",
      "type": "audio_in_slide"
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
  "task_id": "c59742c0-4323-4b9d-8a02-723c251deaa0"
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

### `logger` from `official/desktop_env/evaluators/getters/file.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py#L10-L10`

Full source SHA-256: `d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f`

Exact excerpt SHA-256: `df15c4979fae995ded306279ba830d847eda92de71b795dad700bdbe5be696f5`

```python
logger = logging.getLogger("desktopenv.getter.file")
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

### `import:os` from `official/desktop_env/evaluators/getters/impress.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py#L1-L1`

Full source SHA-256: `46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:ET` from `official/desktop_env/evaluators/getters/impress.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py#L3-L3`

Full source SHA-256: `46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55`

Exact excerpt SHA-256: `d8313b379a858f183008f2f6198051d5bd7ca075d573902814a9666bfda819eb`

```python
import xml.etree.ElementTree as ET
```

### `import:zipfile` from `official/desktop_env/evaluators/getters/impress.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py#L4-L4`

Full source SHA-256: `46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55`

Exact excerpt SHA-256: `a61e3196c03ce192157fd97c256ec82a5f23c6e9bf8b9cf8514c41167e7d5318`

```python
import zipfile
```

### `import:Dict` from `official/desktop_env/evaluators/getters/impress.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py#L5-L5`

Full source SHA-256: `46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `get_audio_in_slide` from `official/desktop_env/evaluators/getters/impress.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/impress.py#L71-L126`

Full source SHA-256: `46a5421cb48e9214cded91248b555bb15eca49431db8a9ae2554e9e0bed27d55`

Exact excerpt SHA-256: `c30d8f547b876cde36e48e636d7e2894263f14d675fd2ddbc33ac6088ae56521`

```python
def get_audio_in_slide(env, config: Dict[str, str]):
    ppt_file_path, slide_index, dest = config["ppt_file_path"], int(config["slide_index"]), config["dest"]

    # Open the .pptx file as a zip file, fixme: now we assume there is only one audio file in the slides
    audio_file_path = None

    ppt_file_localhost_path = get_vm_file(env, {"path": ppt_file_path, "dest": os.path.split(ppt_file_path)[-1]})

    with zipfile.ZipFile(ppt_file_localhost_path, 'r') as myzip:
        # Find the relationships XML file for the first slide
        slide1_rels_file = 'ppt/slides/_rels/slide{}.xml.rels'.format(slide_index + 1)
        if slide1_rels_file in myzip.namelist():
            with myzip.open(slide1_rels_file) as f:
                # Parse the XML tree from the relationships file
                tree = ET.parse(f)
                root = tree.getroot()
                # Define the namespace used in the relationships file
                namespaces = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                # Look for all relationship elements that have a type attribute for audio
                for rel in root.findall('r:Relationship', namespaces):
                    # Check if the relationship is for an audio file
                    if 'audio' in rel.attrib['Type']:
                        # The audio can be embedded inside the file or linked to an external file
                        # Get the target attribute which contains the audio file path
                        target = rel.attrib['Target']

                        if target.startswith('..'):
                            # Resolve the relative path to get the correct path within the zip file
                            audio_file_path = os.path.normpath(os.path.join('ppt/slides', target))
                            # Replace backslashes with forward slashes for ZIP compatibility
                            audio_file_path = audio_file_path.replace('\\', '/')

                            # Create a temporary directory to extract the audio file
                            tmpdirname = os.path.dirname(ppt_file_localhost_path)
                            myzip.extract(audio_file_path, tmpdirname)
                            audio_file_path = os.path.join(tmpdirname, audio_file_path)
                            return audio_file_path
                            # with tempfile.TemporaryDirectory() as tmpdirname:
                            #     # Extract the audio file
                            #     myzip.extract(audio_file_path, tmpdirname)
                            #     # Get the full path of the extracted audio file
                            #     extracted_audio_path = os.path.join(tmpdirname, audio_file_path)
                            #     # Return the extracted audio file path
                            #     audio_file_path = extracted_audio_path
                        else:
                            # the audio file is external to the .pptx file
                            # Return the audio file path
                            assert target.startswith("file://"), target
                            audio_file_path = target[7:]
                        break
    if audio_file_path is None:
        return None

    else:
        # Get the audio file from vm and return the file path in the host
        return get_vm_file(env, {"path": audio_file_path, "dest": dest})
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

### `import:librosa` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L11-L11`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `69261ecb42288897c50c6a0d99741289108eb18e836e0c4f4c71d9dbd5c9541c`

```python
import librosa
```

### `import:np` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L12-L12`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `d34aea06c990aeedd2f8f5ff809c1180b92fccca0381269b7c18654043b9a374`

```python
import numpy as np
```

### `import:fastdtw` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L14-L14`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `3a9004ec7b0b808235541e908e13643f42b825a356866462b9e9671eaca1a46c`

```python
from fastdtw import fastdtw
```

### `import:cosine` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L15-L15`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `d201b34140a7f66dead595a001a4f3a5bd8dc0c2d69b9144f0b09bbc6a112f20`

```python
from scipy.spatial.distance import cosine
```

### `logger` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L18-L18`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `75fc8dffb9f4f69221641e22851433b92ab68c00fe97bed620894c9b05d9c580`

```python
logger = logging.getLogger("desktopenv.metrics.vlc")
```

### `compare_audios` from `official/desktop_env/evaluators/metrics/vlc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/vlc.py#L226-L293`

Full source SHA-256: `a5ebf748e8b23cf212c4ee56991c5f7c0e890095fb68676461252c36d3d0976e`

Exact excerpt SHA-256: `82df34cba62bfc219f112d0f03c39a7116d9ba92440a14ac61d519ef8a1bf35b`

```python
def compare_audios(audio_path_1, audio_path_2):
    """
    Compare two audio files and return a similarity score in the range [0, 1].
    audio_path_1, audio_path_2: paths to the audio files to compare
    """
    # similarity = compare_audios_simple('path_to_audio1.mp3', 'path_to_audio2.mp3')
    # print(f'Similarity Score: {similarity}')

    if not audio_path_1 or not audio_path_2:
        return 0

    y1, y2 = None, None
    try:
        y1, sr1 = librosa.load(audio_path_1)
    except Exception:
        logger.warning(f"Could not load audio from {os.path.basename(audio_path_1)}. It might be empty or corrupt.")

    try:
        y2, sr2 = librosa.load(audio_path_2)
    except Exception:
        logger.warning(f"Could not load audio from {os.path.basename(audio_path_2)}. It might be empty or corrupt.")

    # Handle cases where one or both audio files are empty or corrupt.
    is_y1_bad = (y1 is None) or (y1.shape[0] == 0)
    is_y2_bad = (y2 is None) or (y2.shape[0] == 0)

    if is_y1_bad and is_y2_bad:
        logger.info("Both audio files are empty or corrupt. Considering them perfectly similar.")
        return 1.0
    
    if is_y1_bad or is_y2_bad:
        logger.warning(f"One audio file is empty/corrupt, the other is not. Similarity is 0.")
        return 0.0

    try:
        logger.info(f"Audio 1 ({os.path.basename(audio_path_1)}): sr={sr1}, len={len(y1)}")
        logger.info(f"Audio 2 ({os.path.basename(audio_path_2)}): sr={sr2}, len={len(y2)}")

        # Extract MFCC features
        mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1)
        mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2)
    except Exception as e:
        logger.error(f"Error during MFCC extraction: {e}")
        return 0.0

    # Normalize the MFCC features
    mfcc1 = librosa.util.normalize(mfcc1, axis=1)
    mfcc2 = librosa.util.normalize(mfcc2, axis=1)
    logger.info(f"MFCCs normalized.")

    # Define a lambda function to compute cosine distance
    dist_func = lambda x, y: cosine(x, y)

    # Use the DTW algorithm to find the best alignment path
    distance, path = fastdtw(mfcc1.T, mfcc2.T, dist=dist_func)
    logger.info(f"DTW distance: {distance:.4f}, Path length: {len(path)}")

    # Normalize the DTW distance by the length of the alignment path.
    if len(path) == 0:
        normalized_distance = np.inf
    else:
        normalized_distance = distance / len(path)
    logger.info(f"Normalized DTW distance: {normalized_distance:.4f}")
    
    # Convert the normalized distance to a similarity score using an exponential decay function.
    similarity = np.exp(-normalized_distance)

    return similarity
```
