# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5`
- task_id: `6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `libreoffice_calc`
- snapshot: `libreoffice_calc`
- related apps: `libreoffice calc`
- official instruction: Help me format column "spent" by keeping two decimal points. 
- evaluator functions: `compare_table`
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
- `official/desktop_env/evaluators/metrics/table.py`
- `official/desktop_env/evaluators/metrics/utils.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/libreoffice_calc/6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5.json`

Source SHA-256: `610adfe4461f26cd2c0dd95053d010be0b1ed1eac294a780a82c67df6b8f46f7`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Keep_Two_decimal_points.xlsx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5/Keep_Two_decimal_points.xlsx"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "path": "/home/user/Keep_Two_decimal_points.xlsx"
      },
      "type": "open"
    }
  ],
  "evaluator": {
    "expected": {
      "dest": [
        "Keep_Two_decimal_points_gold.xlsx",
        "Keep_Two_decimal_points_gold-Sheet1.csv"
      ],
      "multi": true,
      "path": [
        "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5/Keep_Two_decimal_points_gold.xlsx",
        "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5/Keep_Two_decimal_points_gold-Sheet1.csv"
      ],
      "type": "cloud_file"
    },
    "func": "compare_table",
    "options": {
      "rules": [
        {
          "sheet_idx0": "RNSheet1",
          "sheet_idx1": "ENSheet1",
          "type": "sheet_print"
        }
      ]
    },
    "postconfig": [
      {
        "parameters": {
          "strict": true,
          "window_name": "Keep_Two_decimal_points.xlsx - LibreOffice Calc"
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
            "import pyautogui; pyautogui.hotkey(\"ctrl\", \"s\");"
          ]
        },
        "type": "execute"
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
            "libreoffice",
            "--convert-to",
            "csv:Text - txt - csv (StarCalc):44,34,UTF-8,,,,false,true,true,false,false,1",
            "--outdir",
            "/home/user",
            "/home/user/Keep_Two_decimal_points.xlsx"
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
      "dest": [
        "Keep_Two_decimal_points.xlsx",
        "Keep_Two_decimal_points-Sheet1.csv"
      ],
      "multi": true,
      "path": [
        "/home/user/Keep_Two_decimal_points.xlsx",
        "/home/user/Keep_Two_decimal_points-Sheet1.csv"
      ],
      "type": "vm_file"
    }
  },
  "fixed_ip": false,
  "id": "6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5",
  "instruction": "Help me format column \"spent\" by keeping two decimal points. ",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "libreoffice calc"
  ],
  "snapshot": "libreoffice_calc",
  "source": "https://www.youtube.com/watch?v=nl-nXjJurhQ",
  "trajectory": "trajectories/6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `45f8d8ae65b6377e05d3dfc17eb0623ee11ff57d729b8a008b2b17afd2553b19`

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
      "excerpt_sha256": "82847998d6bcdb183ec85088ef9b096ea226c8441699684c71ca64a9d42a35a9",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 1,
      "symbol": "import:functools",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "6abd45136639991239f4e6e89f9ee993f93a9ee766477a4704bbd4b861415957",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 2,
      "symbol": "import:itertools",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 3,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "8d441712c8d1deb79acde9c55086744ff78331d50f054d42318a6035af4ba76b",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 4,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "29ad8fe072deddaf9c69962ecfa6348764f180e904cb8223d3caa66ec06b9b8a",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 9,
      "symbol": "import:Number",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 10,
      "excerpt_sha256": "80978535a57192548668be1e08b32e74dc05a41866e948a960fb390d0873d860",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 10,
      "symbol": "import:Any",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 11,
      "excerpt_sha256": "b5ee4dabc7266a2419a4a1dece8d0edb2b63488d255ce5c63fa10712509082aa",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 11,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 13,
      "excerpt_sha256": "b66663105a4ec37f2d0e25d0839c0368a1edd2d582b882aa38b2cbb8f2a168a5",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 13,
      "symbol": "import:openpyxl",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 14,
      "excerpt_sha256": "d7a11d5edc0f0628b4a8d665a78db6dd1062d88065d316b4293c450edf76030b",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 14,
      "symbol": "import:pd",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 15,
      "excerpt_sha256": "198611b4d1a3909eec5d2f872c568a6a0c00b3c7b633172909fe1ade1c962f95",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 15,
      "symbol": "import:Workbook",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 16,
      "excerpt_sha256": "a0e48e8ce01039251a44e3b359f14f10105b107eb27a45530b5be2c56a038e66",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 16,
      "symbol": "import:Cell",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 17,
      "excerpt_sha256": "d4921955023221d60682f86175048d302bb08a21abf4f187d41ed7757eefadfc",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 17,
      "symbol": "import:get_column_letter",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 18,
      "excerpt_sha256": "d8640b2003ff2e7d2bc8dc71ed95cb15724f30edea358ca9fc4fccc4f0451607",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 18,
      "symbol": "import:MultiCellRange",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 19,
      "excerpt_sha256": "57cfdb5aa484c59e69780d5143ac5f5a541a80f4129bd3539ccd48105eab1a93",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 19,
      "symbol": "import:DataValidation",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 20,
      "excerpt_sha256": "26f5eb174570fe83e2c506632eb54cb87adc2935195a57324e27f8eeaa5ca026",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 20,
      "symbol": "import:Worksheet",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 21,
      "excerpt_sha256": "26c7871254a887e480fda51ff137f51d691107a7dc924578bf7c85bb1b0e3ac2",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 21,
      "symbol": "import:fuzz",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 39,
      "excerpt_sha256": "5844588d327f2608103b393753ef3d437d49161a75725ba7f751b42e6de04716",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 39,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 41,
      "excerpt_sha256": "421b182ec36152c8462ba4f16685677f98a2e7fa2082bf708f82eedd77af3fd7",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 41,
      "symbol": "BOOK",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 87,
      "excerpt_sha256": "8b59f9ab63a5ed443afe3f2c4f953cfae044b82ca192c4ba6e622df4b1305603",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 44,
      "symbol": "_parse_sheet_idx",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 91,
      "excerpt_sha256": "3dad7de78b5f0680be816615bcbe7b4a33061fd60dcd511f4030fa88b135b997",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 91,
      "symbol": "SHEET",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 122,
      "excerpt_sha256": "2fa812e390215ec0c70b0080717ab528bca5d07ce2592e8b752d9de4b2635936",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 94,
      "symbol": "_load_sheet",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 144,
      "excerpt_sha256": "21b6c8df200c9537c14d49f80a27e88d4a0d4d65f5a735766c920aaa7cf6fab2",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 126,
      "symbol": "_freeze_compare_key",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 202,
      "excerpt_sha256": "35c546dfe205b49c0589b83cca3f1b898d8dfae3f27c6d084e975c493aa12a66",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 147,
      "symbol": "_safe_read_file",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 771,
      "excerpt_sha256": "b66f1f75a383ad662ec8bc05391973f970767b4ecf55fd1db2976dbe9fb09c3b",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "start_line": 260,
      "symbol": "compare_table",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "b5f87818a7ee37d7474306232023de61cdc0034e25ecac6847638e7f9ce8b4db",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 1,
      "symbol": "import:builtins",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "82847998d6bcdb183ec85088ef9b096ea226c8441699684c71ca64a9d42a35a9",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 3,
      "symbol": "import:functools",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "6abd45136639991239f4e6e89f9ee993f93a9ee766477a4704bbd4b861415957",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 4,
      "symbol": "import:itertools",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 5,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 6,
      "excerpt_sha256": "e36c9f3845d99da19d20579925a703c8e3ee0b4400222a60bab97e19731164de",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 6,
      "symbol": "import:operator",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 7,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 7,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 8,
      "excerpt_sha256": "a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 8,
      "symbol": "import:re",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "a61e3196c03ce192157fd97c256ec82a5f23c6e9bf8b9cf8514c41167e7d5318",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 9,
      "symbol": "import:zipfile",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
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
      "end_line": 15,
      "excerpt_sha256": "59fd796f48af29f9a9d5c4a9442e54b3175b002fba254e9d794269941fa1b3d1",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 15,
      "symbol": "import:formulas",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 17,
      "excerpt_sha256": "51cd3847a7ab1e2566005cbe43c924d57d0c319ccc70e8ba7be28a7d5f0ce736",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 17,
      "symbol": "import:lxml",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 18,
      "excerpt_sha256": "e07e4c41f2a6dcf43a1315214dfeb853dc59a9d1ee9593594634c5b84ad56d7d",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 18,
      "symbol": "import:xmltodict",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 19,
      "excerpt_sha256": "f2e79994e6ae76e1750bd9edb90287fa7d24224a5c66d376abc805c64fc677eb",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 19,
      "symbol": "import:_Element",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 20,
      "excerpt_sha256": "198611b4d1a3909eec5d2f872c568a6a0c00b3c7b633172909fe1ade1c962f95",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 20,
      "symbol": "import:Workbook",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 21,
      "excerpt_sha256": "1ef068dc7747042ec6eae2a5ad39eefd16d94c83292e74d24284e36a7da14866",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 21,
      "symbol": "import:Cell",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 22,
      "excerpt_sha256": "df4f9ce1341498ab8991a2290e31d127cac1f348a2ccd29294aad496e4b9e5a3",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 22,
      "symbol": "import:ChartBase",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 23,
      "excerpt_sha256": "a3134a6e588b2f00a1bce0c3c635b01a882249aa60aeac4084a26ff1899750ce",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 23,
      "symbol": "import:ConditionalFormattingList",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 24,
      "excerpt_sha256": "27fb80ee35d717cead954d74a9213f2151ebbcb9ed5cbb718f235836fc17129f",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 24,
      "symbol": "import:PivotCacheSource",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 25,
      "excerpt_sha256": "09186725fe664bce5ba47e87bbce78f02d972d66fad39d73f7e36ec9c9cdc6b5",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 25,
      "symbol": "import:PivotTableDefinition",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 26,
      "excerpt_sha256": "eb1e512ada2e8101b56f955654c5eac2e2650d304bdd65f2789d4d1411751dfd",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 26,
      "symbol": "import:DifferentialStyle",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 27,
      "excerpt_sha256": "14410cd1468fdd96b9d7558ded0ea5ec5c72277e607a544d132de2ba1d317d3e",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 27,
      "symbol": "import:get_column_letter",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 28,
      "excerpt_sha256": "63f180054250da329b72f9f846c9875bf8980e9d5c98bd7164a8dc738eb3216c",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 28,
      "symbol": "import:CellRange",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 29,
      "excerpt_sha256": "d2488695c871872dd904f79839781f98cd0ef2a85d8b391c946d16927b820779",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 29,
      "symbol": "import:DimensionHolder",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 30,
      "excerpt_sha256": "67753e1cf02be54f8d7cc52847736fa62108d2b7210a0d769715adb78b6b32f6",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 30,
      "symbol": "import:AutoFilter",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 31,
      "excerpt_sha256": "26f5eb174570fe83e2c506632eb54cb87adc2935195a57324e27f8eeaa5ca026",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 31,
      "symbol": "import:Worksheet",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 34,
      "excerpt_sha256": "41a2b2176cc210379036f67117ef27b91faf0e73ec81c3892564e850ba4a6e6d",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 34,
      "symbol": "V",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 36,
      "excerpt_sha256": "418d8a52292fe11a53f43945488dfba58622f63f293295b81d45fb479930b805",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 36,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 42,
      "excerpt_sha256": "8a4aa084145ce08380174b562d4c001814eb0da231679882d9974d8c9e9f47bd",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 38,
      "symbol": "_xlsx_namespaces",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 43,
      "excerpt_sha256": "8b38765d7780dc76b0f62fb044bbe8a88af727ff765d8502816029a56a1698ff",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 43,
      "symbol": "_xlsx_ns_mapping",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 45,
      "excerpt_sha256": "a264b9b21c188a13b24c72459b041b142fb52fb6aa9415908fa9e8f0850cb00e",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 45,
      "symbol": "_xlsx_ns_imapping",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 46,
      "excerpt_sha256": "124ed7a11d5adf07afc348ffb81ad3ec8ed300f268a2aa864b9db13b58481a9e",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 46,
      "symbol": "_sheet_name_selector",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 47,
      "excerpt_sha256": "7e6bc8931a580a30bffca4b446e7b57e6c8a7261885323f5f5cfb2979f1ed9cc",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 47,
      "symbol": "_sparklines_selector",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 85,
      "excerpt_sha256": "89c0ddd2bc37e5529439a1ee36a76de433b117ed8bc7b0c2bcc8bbb9e69b4dc8",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 50,
      "symbol": "load_sparklines",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 184,
      "excerpt_sha256": "394708508d3f9ad678aeda707218e36ad832f18e650ef56f751f4f331b959ae7",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 98,
      "symbol": "load_charts",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 278,
      "excerpt_sha256": "9ec34c0eed42522616966e97bd17a53480c72455783cc3aa199b2d83f626e44a",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 197,
      "symbol": "load_pivot_tables",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 282,
      "excerpt_sha256": "7de7a3f876b3eb22cdf39057e419f11af921e0ac7f7d9c235b0ac7ff34de9720",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 282,
      "symbol": "_shared_str_selector",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 283,
      "excerpt_sha256": "655f25fdf35b029ad8785eed8e815b3e2cce8c30232ae24cf6c1fa73b0e1ce93",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 283,
      "symbol": "_shared_str_value_selector",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 352,
      "excerpt_sha256": "bf6b95a8858b6d325be2324fb9be6adfb3e8c265d674d97a8b30d1390b578fe1",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 286,
      "symbol": "read_cell_value",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 412,
      "excerpt_sha256": "88163d8f8dc33483d131e8ce8a2199a50d1794a47346f1b91b2fa9ddeca3ecc1",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 370,
      "symbol": "_read_cell_style",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 449,
      "excerpt_sha256": "4140bf6a94ef77e11dca981bcd056ca0ba4eac3a3791fdbb2bda6ec4f30cb9b2",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 414,
      "symbol": "_process_xlsx_cf_operator",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 458,
      "excerpt_sha256": "0ac5de58bff5be57cf94cd84bd3f31bfb46dc32eab869b2d83bc8809fc4da3b6",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 452,
      "symbol": "_absolute_range_pattern",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 597,
      "excerpt_sha256": "6bcc16f6e8e7cb7444d127291d1e81329f05b63acbf662edf491c06d4156f033",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 461,
      "symbol": "load_xlsx_styles",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 641,
      "excerpt_sha256": "56f2d5ee21f2cd417cc4185d3b7a5deccae3cb1ee7f99b7e8fea11ad9f97c8a9",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 613,
      "symbol": "load_rows_or_cols",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 700,
      "excerpt_sha256": "3f87c5828e5a572717a2bebcb103d1f63f5c944b5a321c80284d076d03651ab3",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 645,
      "symbol": "load_filters",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 709,
      "excerpt_sha256": "982e04d4e42012b1a1d089021300a629e53c6c1cc3e175e821ddace15a580c07",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 708,
      "symbol": "_multicellrange_containsby",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 767,
      "excerpt_sha256": "bb5670f4440cac8898c7dca4074dc3d5ef239fc421866c1f6f9bd7ece17ff98f",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 712,
      "symbol": "_match_value_to_rule",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "fef0856d5ed7a44906ba9abb4b0f9a2f1aebb14c3c3a2454e63b47168ad8f942",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "cf714e1f938c380333f13d54f22ac73a5c05021c971bae90f616f0c42b03eb68",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": {
    "rules": [
      {
        "sheet_idx0": "RNSheet1",
        "sheet_idx1": "ENSheet1",
        "type": "sheet_print"
      }
    ]
  },
  "metrics": [
    {
      "name": "compare_table",
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "source_sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d"
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
      "packet_path": "official/desktop_env/evaluators/metrics/table.py",
      "sha256": "cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py",
      "upstream_path": "desktop_env/evaluators/metrics/table.py"
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
      "config_sha256": "68b37b74c5d3c6a6e19ecbb0aeac4910126b21ca63f73b069c892924962e5cf4",
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
  "task_id": "6e99a1ad-07d2-4b66-a1ce-ece6d99c20a5"
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

### `import:functools` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L1-L1`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `82847998d6bcdb183ec85088ef9b096ea226c8441699684c71ca64a9d42a35a9`

```python
import functools
```

### `import:itertools` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L2-L2`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `6abd45136639991239f4e6e89f9ee993f93a9ee766477a4704bbd4b861415957`

```python
import itertools
```

### `import:logging` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L3-L3`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:os` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L4-L4`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `8d441712c8d1deb79acde9c55086744ff78331d50f054d42318a6035af4ba76b`

```python
import os.path
```

### `import:Number` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L9-L9`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `29ad8fe072deddaf9c69962ecfa6348764f180e904cb8223d3caa66ec06b9b8a`

```python
from numbers import Number
```

### `import:Any` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L10-L10`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `80978535a57192548668be1e08b32e74dc05a41866e948a960fb390d0873d860`

```python
from typing import Any, Union, cast, Callable, Iterable
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L11-L11`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `b5ee4dabc7266a2419a4a1dece8d0edb2b63488d255ce5c63fa10712509082aa`

```python
from typing import Dict, List, Tuple, Set
```

### `import:openpyxl` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L13-L13`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `b66663105a4ec37f2d0e25d0839c0368a1edd2d582b882aa38b2cbb8f2a168a5`

```python
import openpyxl
```

### `import:pd` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L14-L14`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `d7a11d5edc0f0628b4a8d665a78db6dd1062d88065d316b4293c450edf76030b`

```python
import pandas as pd
```

### `import:Workbook` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L15-L15`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `198611b4d1a3909eec5d2f872c568a6a0c00b3c7b633172909fe1ade1c962f95`

```python
from openpyxl import Workbook
```

### `import:Cell` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L16-L16`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `a0e48e8ce01039251a44e3b359f14f10105b107eb27a45530b5be2c56a038e66`

```python
from openpyxl.cell.cell import Cell
```

### `import:get_column_letter` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L17-L17`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `d4921955023221d60682f86175048d302bb08a21abf4f187d41ed7757eefadfc`

```python
from openpyxl.utils import get_column_letter
```

### `import:MultiCellRange` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L18-L18`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `d8640b2003ff2e7d2bc8dc71ed95cb15724f30edea358ca9fc4fccc4f0451607`

```python
from openpyxl.worksheet.cell_range import MultiCellRange
```

### `import:DataValidation` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L19-L19`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `57cfdb5aa484c59e69780d5143ac5f5a541a80f4129bd3539ccd48105eab1a93`

```python
from openpyxl.worksheet.datavalidation import DataValidation
```

### `import:Worksheet` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L20-L20`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `26f5eb174570fe83e2c506632eb54cb87adc2935195a57324e27f8eeaa5ca026`

```python
from openpyxl.worksheet.worksheet import Worksheet
```

### `import:fuzz` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L21-L21`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `26c7871254a887e480fda51ff137f51d691107a7dc924578bf7c85bb1b0e3ac2`

```python
from rapidfuzz import fuzz
```

### `logger` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L39-L39`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `5844588d327f2608103b393753ef3d437d49161a75725ba7f751b42e6de04716`

```python
logger = logging.getLogger("desktopenv.metric.table")
```

### `BOOK` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L41-L41`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `421b182ec36152c8462ba4f16685677f98a2e7fa2082bf708f82eedd77af3fd7`

```python
BOOK = Union[pd.ExcelFile, Workbook, str]
```

### `_parse_sheet_idx` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L44-L87`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `8b59f9ab63a5ed443afe3f2c4f953cfae044b82ca192c4ba6e622df4b1305603`

```python
def _parse_sheet_idx(
    sheet_idx: Union[int, str],
    result: BOOK,
    expected: BOOK,
    result_sheet_names: List[str],
    expected_sheet_names: List[str],
) -> Tuple[BOOK, str]:
    #  function _parse_sheet_idx {{{ #
    if isinstance(sheet_idx, int):
        try:
            if not result_sheet_names or sheet_idx >= len(result_sheet_names):
                logger.error(
                    f"Sheet index {sheet_idx} out of range. Available sheets: {result_sheet_names}"
                )
                index = ""
            else:
                index: str = result_sheet_names[sheet_idx]
                logger.debug(f"Sheet index {sheet_idx} resolved to sheet: {index}")
        except Exception as e:
            logger.error(f"Error resolving sheet index {sheet_idx}: {e}")
            index = ""
        book: BOOK = result
    elif sheet_idx.startswith("RI"):
        try:
            index: str = result_sheet_names[int(sheet_idx[2:])]
        except:
            index = ""
        book: BOOK = result
    elif sheet_idx.startswith("RN"):
        index: str = sheet_idx[2:]
        book: BOOK = result
    elif sheet_idx.startswith("EI"):
        try:
            index: str = expected_sheet_names[int(sheet_idx[2:])]
        except:
            index = ""
        book: BOOK = expected
    elif sheet_idx.startswith("EN"):
        index: str = sheet_idx[2:]
        book: BOOK = expected
    else:
        logger.error("Unrecognized sheet index")
        raise ValueError("Unrecognized sheet index")
    return book, index
```

### `SHEET` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L91-L91`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `3dad7de78b5f0680be816615bcbe7b4a33061fd60dcd511f4030fa88b135b997`

```python
SHEET = Union[pd.DataFrame, Worksheet, List[str]]
```

### `_load_sheet` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L94-L122`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `2fa812e390215ec0c70b0080717ab528bca5d07ce2592e8b752d9de4b2635936`

```python
def _load_sheet(book: BOOK, index: str) -> SHEET:
    #  function _load_sheet {{{ #
    try:
        if isinstance(book, str):
            book: str = cast(str, book)
            csv_name: str = "{:}-{:}.csv".format(os.path.splitext(book)[0], index)

            try:
                all_lines: List[str] = _safe_read_file(csv_name)
                csv_lines: List[str] = list(
                    itertools.dropwhile(
                        lambda l: len(l) == 0,
                        map(lambda l: l.strip(), reversed(all_lines)),
                    )
                )
                return csv_lines
            except (FileNotFoundError, IOError) as e:
                logger.error(f"Failed to read CSV file {csv_name}: {e}")
                return None
        if isinstance(book, pd.ExcelFile):
            return pd.read_excel(book, index)
        if isinstance(book, Workbook):
            return book[index]
        logger.error("Not supported workbook format")
        raise NotImplementedError("Not supported workbook format")
    except NotImplementedError as e:
        raise e
    except:
        return None
```

### `_freeze_compare_key` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L126-L144`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `21b6c8df200c9537c14d49f80a27e88d4a0d4d65f5a735766c920aaa7cf6fab2`

```python
def _freeze_compare_key(sheet: Worksheet) -> Tuple[Any, ...]:
    """
    Build a scroll-stable key for comparing freeze panes.

    openpyxl's ``freeze_panes`` reads ``pane.topLeftCell``, which in OOXML is
    the top-left *visible* cell of the unfrozen region — it changes when the
    user scrolls. The actual freeze boundary is ``xSplit`` / ``ySplit``
    (frozen column count / frozen row count).
    """
    pane = sheet.sheet_view.pane
    if pane is None:
        return ("none",)
    state = (pane.state or "").lower()
    xs = int(pane.xSplit) if pane.xSplit is not None else 0
    ys = int(pane.ySplit) if pane.ySplit is not None else 0
    if state in ("frozen", "frozensplit"):
        return ("frozen", xs, ys)
    # Split-only or unusual pane records: keep scroll-dependent topLeftCell.
    return ("other", xs, ys, pane.topLeftCell)
```

### `_safe_read_file` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L147-L202`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `35c546dfe205b49c0589b83cca3f1b898d8dfae3f27c6d084e975c493aa12a66`

```python
def _safe_read_file(file_path: str) -> List[str]:
    """
    Safely read a file with multiple encoding attempts.

    Args:
        file_path: Path to the file to read

    Returns:
        List of lines from the file

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read with any encoding
    """
    # Common encodings to try in order of preference
    encodings = [
        "utf-8",  # Most common modern encoding
        "utf-8-sig",  # UTF-8 with BOM
        "latin-1",  # ISO-8859-1, works with any byte sequence
        "windows-1252",  # Common Windows encoding
        "gbk",  # Chinese encoding
        "cp1251",  # Cyrillic encoding
        "iso-8859-1",  # Alternative latin-1
    ]

    last_error = None

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.read().splitlines()
                logger.debug(
                    f"Successfully read file {file_path} with encoding {encoding}"
                )
                return lines
        except UnicodeDecodeError as e:
            last_error = e
            logger.debug(f"Failed to read {file_path} with encoding {encoding}: {e}")
            continue
        except (FileNotFoundError, IOError) as e:
            # These are non-encoding related errors, re-raise immediately
            raise e

    # If all encodings fail, try with error handling as last resort
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
            logger.warning(f"Read file {file_path} with UTF-8 and error replacement")
            return lines
    except Exception as e:
        logger.error(
            f"Failed to read file {file_path} with any encoding. Last error: {last_error}"
        )
        raise IOError(
            f"Cannot read file {file_path} with any supported encoding"
        ) from last_error
```

### `compare_table` from `official/desktop_env/evaluators/metrics/table.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/table.py#L260-L771`

Full source SHA-256: `cae9cc52f4f1d5aaaeb89f47ba6241b8885ed0dfab25c6b2fa5d03949eb3389d`

Exact excerpt SHA-256: `b66f1f75a383ad662ec8bc05391973f970767b4ecf55fd1db2976dbe9fb09c3b`

```python
def compare_table(result: str, expected: str = None, **options) -> float:
    #  function compare_table {{{ #
    """
    Args:
        result (str): path to result xlsx
        expected (str): path to golden xlsx
        rules (List[Dict[str, Any]]): list of dict like
          {
            "type": str,
            <str as parameters>: anything
          }
          as sequential rules

    Returns:
        float: the score
    """

    if result is None:
        logger.error("Result file path is None")
        return 0.0

    # Check if result file exists
    if not os.path.exists(result):
        logger.error(f"Result file not found: {result}")
        return 0.0

    try:
        logger.info(f"Loading result file: {result}")
        xlworkbookr: Workbook = openpyxl.load_workbook(filename=result)
        pdworkbookr = pd.ExcelFile(result)
        logger.info(
            f"Successfully loaded result file with sheets: {pdworkbookr.sheet_names}"
        )
    except Exception as e:
        logger.error(f"Failed to load result file {result}: {e}")
        return 0.0
    worksheetr_names: List[str] = pdworkbookr.sheet_names

    if expected is not None:
        xlworkbooke: Workbook = openpyxl.load_workbook(filename=expected)
        pdworkbooke = pd.ExcelFile(expected)
        worksheete_names: List[str] = pdworkbooke.sheet_names
    else:
        xlworkbooke: Workbook = None
        pdworkbooke = None
        worksheete_names: List[str] = None

    parse_idx: Callable[[Union[str, int], BOOK, BOOK], Tuple[BOOK, str]] = (
        functools.partial(
            _parse_sheet_idx,
            result_sheet_names=worksheetr_names,
            expected_sheet_names=worksheete_names,
        )
    )

    passes = True
    for r in options["rules"]:
        if r["type"] == "sheet_name":
            #  Compare Sheet Names {{{ #
            metric: bool = worksheetr_names == worksheete_names
            logger.debug(
                "Assertion: %s.sheet_names == %s.sheet_names - %s",
                result,
                expected,
                metric,
            )
            #  }}} Compare Sheet Names #

        elif r["type"] == "sheet_data":
            #  Compare Sheet Data by Internal Value {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # precision: int as number of decimal digits, default to 4

            error_limit: int = r.get("precision", 4)
            sheet1: pd.DataFrame = _load_sheet(
                *parse_idx(r["sheet_idx0"], pdworkbookr, pdworkbooke)
            )
            if sheet1 is None:
                return 0.0
            sheet2: pd.DataFrame = _load_sheet(
                *parse_idx(r["sheet_idx1"], pdworkbookr, pdworkbooke)
            )

            sheet1 = sheet1.round(error_limit)
            sheet2 = sheet2.round(error_limit)
            metric: bool = sheet1.equals(sheet2)
            logger.debug("Sheet1: \n%s", str(sheet1))
            logger.debug("Sheet2: \n%s", str(sheet2))
            try:
                logger.debug("Sheet1 =v= Sheet2: \n%s", str(sheet1 == sheet2))
            except:
                logger.debug("Sheet1 =/v= Sheet2")
            logger.debug(
                "Assertion: %s =v= %s - %s", r["sheet_idx0"], r["sheet_idx1"], metric
            )
            #  }}} Compare Sheet Data by Internal Value #

        elif r["type"] == "sheet_print":
            #  Compare Sheet Data by Printed Value {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # ignore_case: optional, defaults to False

            sheet1: List[str] = _load_sheet(
                *parse_idx(r["sheet_idx0"], result, expected)
            )
            if sheet1 is None:
                return 0.0
            sheet2: List[str] = _load_sheet(
                *parse_idx(r["sheet_idx1"], result, expected)
            )
            if r.get("ignore_case", False):
                sheet1 = [l.lower() for l in sheet1]
                sheet2 = [l.lower() for l in sheet2]
            metric: bool = sheet1 == sheet2
            logger.debug(
                "Assertion: %s =p= %s - %s", r["sheet_idx0"], r["sheet_idx1"], metric
            )
            #  }}} Compare Sheet Data by Printed Value #

        elif r["type"] == "sheet_fuzzy":
            #  Fuzzy Match for Ranges {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # rules: list of dict, each dict is like
            #   { "range": ["A1:B6", "C2:E5"],
            #     "type": "includes" | "included_by" | "fuzzy_match" | "exact_match", # 0 includes 1, 0 includes_by 1
            #     "threshold": 85, // for fuzzy match
            #     "ignore_case": true | false,
            #     "ignore_chars": " ()", # filtered out
            #     "trim_leadings": "+ ", # filtered by lstrip
            #     "trim_trailings": "", # filtered by rstrip
            #     "normalization": [["Rd", "Road"]], # filtered by replace
            #   }

            sheet1: Tuple[BOOK, str] = parse_idx(r["sheet_idx0"], result, expected)
            sheet2: Tuple[BOOK, str] = parse_idx(r["sheet_idx1"], result, expected)
            total_metric = True
            for rl in r["rules"]:
                for rng in MultiCellRange(rl["range"]):
                    for cdn in rng.cells:
                        coordinate: str = "{:}{:d}".format(
                            get_column_letter(cdn[1]), cdn[0]
                        )
                        value1: str = str(read_cell_value(*sheet1, coordinate))
                        value2: str = str(read_cell_value(*sheet2, coordinate))
                        logger.debug("%s: %s vs %s", cdn, value1, value2)

                        for rplc in rl.get("normalization", []):
                            value1 = value1.replace(rplc[0], rplc[1])
                            value2 = value2.replace(rplc[0], rplc[1])
                        if "trim_leadings" in rl:
                            value1 = value1.lstrip(rl["trim_leadings"])
                            value2 = value2.lstrip(rl["trim_leadings"])
                        if "trim_trailings" in rl:
                            value1 = value1.rstrip(rl["trim_trailings"])
                            value2 = value2.rstrip(rl["trim_trailings"])
                        if "ignore_chars" in rl:
                            ignore_chars: Set[str] = set(rl["ignore_chars"])
                            value1 = "".join(
                                filter(lambda ch: ch not in ignore_chars, value1)
                            )
                            value2 = "".join(
                                filter(lambda ch: ch not in ignore_chars, value2)
                            )
                        if rl.get("ignore_case", False):
                            value1 = value1.lower()
                            value2 = value2.lower()

                        if rl["type"] == "includes":
                            metric: bool = value2 in value1
                        elif rl["type"] == "included_by":
                            metric: bool = value1 in value2
                        elif rl["type"] == "fuzzy_match":
                            metric: bool = fuzz.ratio(value1, value2) >= rl.get(
                                "threshold", 85.0
                            )
                        elif rl["type"] == "exact_match":
                            metric: bool = value1 == value2
                        total_metric = total_metric and metric

            metric: bool = total_metric
            logger.debug(
                "Assertion: %s =~= %s - %s", r["sheet_idx0"], r["sheet_idx1"], metric
            )
            #  }}} Fuzzy Match for Ranges #

        elif r["type"] == "sparkline":
            #  Compare Sparklines {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0

            sparkline1: Dict[str, str] = load_sparklines(
                *parse_idx(r["sheet_idx0"], result, expected)
            )
            sparkline2: Dict[str, str] = load_sparklines(
                *parse_idx(r["sheet_idx1"], result, expected)
            )
            metric: bool = sparkline1 == sparkline2
            logger.debug(
                "Assertion: %s.sp == %.sp - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Compare Sparklines #

        elif r["type"] == "chart":
            #  Compare Charts {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # chart_props: list of str, see utils.load_charts

            charts1: Dict[str, Any] = load_charts(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke), **r
            )
            charts2: Dict[str, Any] = load_charts(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke), **r
            )
            metric: bool = charts1 == charts2
            logger.debug(
                "Assertion: %s[chart] == %s[chart] - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Compare Charts #

        elif r["type"] == "style":
            #  Compare Style (Also Conditional Formatiing) {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # props: list of str indicating concerned styles, see utils._read_cell_style

            sheet_idx1: Tuple[BOOK, str] = parse_idx(
                r["sheet_idx0"], xlworkbookr, xlworkbooke
            )
            book_name1: str = parse_idx(r["sheet_idx0"], result, expected)[0]
            styles1: Dict[str, List[Any]] = load_xlsx_styles(
                *sheet_idx1, book_name1, **r
            )

            sheet_idx2: Tuple[BOOK, str] = parse_idx(
                r["sheet_idx1"], xlworkbookr, xlworkbooke
            )
            book_name2: str = parse_idx(r["sheet_idx1"], result, expected)[0]
            styles2: Dict[str, List[Any]] = load_xlsx_styles(
                *sheet_idx2, book_name2, **r
            )
            # number_formats1: List[str] = [c.number_format.lower() for col in sheet1.iter_cols() for c in col if c.value is not None and c.data_type=="n"]
            # number_formats2: List[str] = [c.number_format.lower() for col in sheet2.iter_cols() for c in col if c.value is not None and c.data_type=="n"]
            metric: bool = styles1 == styles2
            logger.debug(
                "Assertion: %s.style == %s.style - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Compare Style (Also Conditional Formatiing) #

        elif r["type"] == "freeze":
            #  Compare Freezing {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0

            sheet1: Worksheet = _load_sheet(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke)
            )
            if sheet1 is None:
                return 0.0
            sheet2: Worksheet = _load_sheet(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke)
            )
            key1 = _freeze_compare_key(sheet1)
            key2 = _freeze_compare_key(sheet2)
            metric: bool = key1 == key2
            logger.debug(
                "Assertion: %s.freeze_key%s == %s.freeze_key%s "
                "(openpyxl topLeftCell %s vs %s) - %s",
                r["sheet_idx0"],
                key1,
                r["sheet_idx1"],
                key2,
                sheet1.freeze_panes,
                sheet2.freeze_panes,
                metric,
            )
            #  }}} Compare Freezing #

        elif r["type"] == "zoom":
            #  Check Zooming {{{ #
            # sheet_idx: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # method: str
            # ref: value

            sheet: Worksheet = _load_sheet(
                *parse_idx(r["sheet_idx"], xlworkbookr, xlworkbooke)
            )
            if sheet is None:
                return 0.0
            zoom_scale: Number = sheet.sheet_view.zoomScale or 100.0
            metric: bool = _match_value_to_rule(zoom_scale, r)
            logger.debug(
                "Assertion: %s.zoom(%.1f) %s %.1f - %s",
                r["sheet_idx"],
                zoom_scale,
                r["method"],
                r["ref"],
                metric,
            )
            #  }}} Check Zooming #

        elif r["type"] == "data_validation":
            #  Check Data Validation {{{ #
            # sheet_idx: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # dv_props: list of dict like {attribute: {"method": str, "ref": anything}}
            #   available attributes:
            #     * ranges
            #     * type
            #     * formula1
            #     * formula2
            #     * operator
            #     * allowBlank
            #     * showDropDown
            #     * showInputMessage
            #     * showErrorMessage
            #     * error
            #     * errorTitle
            #     * errorStyle
            #     * prompt
            #     * promptTitle
            #     * imeMode

            sheet: Worksheet = _load_sheet(
                *parse_idx(r["sheet_idx"], xlworkbookr, xlworkbooke)
            )
            if sheet is None:
                return 0.0
            data_validators: List[DataValidation] = (
                sheet.data_validations.dataValidation
            )

            total_metric = len(data_validators) >= len(r["dv_props"])
            for dat_vldt in data_validators:
                metric = False
                for prpt in r["dv_props"]:
                    metric = metric or all(
                        _match_value_to_rule(getattr(dat_vldt, attrbt), mr)
                        for attrbt, mr in prpt.items()
                    )
                    if metric:
                        break
                total_metric = total_metric and metric
                if not total_metric:
                    break

            logger.debug(
                "Assertion: %s.data_validation - %s", r["sheet_idx"], total_metric
            )
            metric: bool = total_metric
            #  }}} Check Data Validation #

        elif r["type"] == "row_props":
            #  Check Row Properties {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # props: list of str, see utils.load_rows_or_cols

            rows1: Dict[str, Any] = load_rows_or_cols(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke), obj="row", **r
            )
            rows2: Dict[str, Any] = load_rows_or_cols(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke), obj="row", **r
            )
            logger.debug("Rows1: %s", repr(rows1))
            logger.debug("Rows2: %s", repr(rows2))
            metric: bool = rows1 == rows2
            logger.debug(
                "Assertion: %s[rows] == %s[rows] - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Check Row Properties #

        elif r["type"] == "col_props":
            #  Check Row Properties {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # props: list of str, see utils.load_rows_or_cols

            cols1: Dict[str, Any] = load_rows_or_cols(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke), obj="column", **r
            )
            cols2: Dict[str, Any] = load_rows_or_cols(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke), obj="column", **r
            )
            metric: bool = cols1 == cols2
            logger.debug(
                "Assertion: %s[cols] == %s[cols] - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Check Row Properties #

        elif r["type"] == "filter":
            #  Compare Filters {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0

            filters1: Dict[str, Any] = load_filters(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke), **r
            )
            filters2: Dict[str, Any] = load_filters(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke), **r
            )
            metric: bool = filters1 == filters2
            logger.debug(
                "Assertion: %s[filter] == %s[filter] - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Compare Filters #

        elif r["type"] == "pivot_table":
            #  Compare Pivot Tables {{{ #
            # sheet_idx0: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # sheet_idx1: as sheet_idx0
            # pivot_props: list of str, see utils.load_pivot_tables

            pivots1: Dict[str, Any] = load_pivot_tables(
                *parse_idx(r["sheet_idx0"], xlworkbookr, xlworkbooke), **r
            )
            pivots2: Dict[str, Any] = load_pivot_tables(
                *parse_idx(r["sheet_idx1"], xlworkbookr, xlworkbooke), **r
            )
            metric: bool = pivots1 == pivots2
            logger.debug(
                "Assertion: %s[pivot]==%s[pivot] - %s",
                r["sheet_idx0"],
                r["sheet_idx1"],
                metric,
            )
            #  }}} Compare Pivot Tables #

        elif r["type"] == "check_cell":
            #  Check Cell Properties {{{ #
            # sheet_idx: 0 == "RI0" == "RNSheet1" | "EI0" == "ENSheet1"
            # coordinate: str, "E3"
            # props: dict like {attribute: {"method": str, "ref": anything}}
            #   supported attributes: value & those supported by utils._read_cell_style

            try:
                sheet: Worksheet = _load_sheet(
                    *parse_idx(r["sheet_idx"], xlworkbookr, xlworkbooke)
                )
                if sheet is None:
                    logger.error(
                        f"Failed to load sheet for sheet_idx: {r['sheet_idx']}"
                    )
                    return 0.0
                # data_frame: pd.DataFrame = _load_sheet(*parse_idx(r["sheet_idx"], pdworkbookr, pdworkbooke))
                cell: Cell = sheet[r["coordinate"]]
                metric: bool = True
                for prpt, rule in r["props"].items():
                    if prpt == "value":
                        try:
                            parsed_result = parse_idx(r["sheet_idx"], result, expected)
                            logger.debug(f"parse_idx result: {parsed_result}")
                            val = read_cell_value(*parsed_result, r["coordinate"])
                            logger.debug(f"Cell {r['coordinate']} value: {val}")
                        except Exception as e:
                            logger.error(
                                f"Failed to read cell value at {r['coordinate']}: {e}"
                            )
                            val = None
                    else:
                        try:
                            val = _read_cell_style(prpt, cell)
                        except Exception as e:
                            logger.error(
                                f"Failed to read cell style {prpt} at {r['coordinate']}: {e}"
                            )
                            val = None

                    metric = metric and _match_value_to_rule(val, rule)
            except Exception as e:
                logger.error(f"Error in check_cell processing: {e}")
                return 0.0

            logger.debug(
                "Assertion: %s[%s] :%s - %s",
                r["sheet_idx"],
                r["coordinate"],
                repr(r["props"]),
                metric,
            )
            #  }}} Check Cell Properties #

        else:
            raise NotImplementedError(
                "Unimplemented sheet check: {:}".format(r["type"])
            )

        passes = passes and metric
        if not passes:
            break

    return float(passes)
```

### `import:builtins` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L1-L1`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `b5f87818a7ee37d7474306232023de61cdc0034e25ecac6847638e7f9ce8b4db`

```python
import builtins
```

### `import:functools` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L3-L3`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `82847998d6bcdb183ec85088ef9b096ea226c8441699684c71ca64a9d42a35a9`

```python
import functools
```

### `import:itertools` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L4-L4`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `6abd45136639991239f4e6e89f9ee993f93a9ee766477a4704bbd4b861415957`

```python
import itertools
```

### `import:logging` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L5-L5`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:operator` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L6-L6`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `e36c9f3845d99da19d20579925a703c8e3ee0b4400222a60bab97e19731164de`

```python
import operator
```

### `import:os` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L7-L7`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:re` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L8-L8`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `import:zipfile` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L9-L9`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a61e3196c03ce192157fd97c256ec82a5f23c6e9bf8b9cf8514c41167e7d5318`

```python
import zipfile
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

### `import:formulas` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L15-L15`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `59fd796f48af29f9a9d5c4a9442e54b3175b002fba254e9d794269941fa1b3d1`

```python
import formulas
```

### `import:lxml` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L17-L17`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `51cd3847a7ab1e2566005cbe43c924d57d0c319ccc70e8ba7be28a7d5f0ce736`

```python
import lxml.etree
```

### `import:xmltodict` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L18-L18`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `e07e4c41f2a6dcf43a1315214dfeb853dc59a9d1ee9593594634c5b84ad56d7d`

```python
import xmltodict
```

### `import:_Element` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L19-L19`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `f2e79994e6ae76e1750bd9edb90287fa7d24224a5c66d376abc805c64fc677eb`

```python
from lxml.etree import _Element
```

### `import:Workbook` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L20-L20`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `198611b4d1a3909eec5d2f872c568a6a0c00b3c7b633172909fe1ade1c962f95`

```python
from openpyxl import Workbook
```

### `import:Cell` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L21-L21`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `1ef068dc7747042ec6eae2a5ad39eefd16d94c83292e74d24284e36a7da14866`

```python
from openpyxl.cell.cell import Cell, MergedCell
```

### `import:ChartBase` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L22-L22`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `df4f9ce1341498ab8991a2290e31d127cac1f348a2ccd29294aad496e4b9e5a3`

```python
from openpyxl.chart._chart import ChartBase
```

### `import:ConditionalFormattingList` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L23-L23`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a3134a6e588b2f00a1bce0c3c635b01a882249aa60aeac4084a26ff1899750ce`

```python
from openpyxl.formatting.formatting import ConditionalFormattingList
```

### `import:PivotCacheSource` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L24-L24`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `27fb80ee35d717cead954d74a9213f2151ebbcb9ed5cbb718f235836fc17129f`

```python
from openpyxl.pivot.cache import CacheSource as PivotCacheSource
```

### `import:PivotTableDefinition` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L25-L25`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `09186725fe664bce5ba47e87bbce78f02d972d66fad39d73f7e36ec9c9cdc6b5`

```python
from openpyxl.pivot.table import TableDefinition as PivotTableDefinition
```

### `import:DifferentialStyle` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L26-L26`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `eb1e512ada2e8101b56f955654c5eac2e2650d304bdd65f2789d4d1411751dfd`

```python
from openpyxl.styles.differential import DifferentialStyle
```

### `import:get_column_letter` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L27-L27`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `14410cd1468fdd96b9d7558ded0ea5ec5c72277e607a544d132de2ba1d317d3e`

```python
from openpyxl.utils import coordinate_to_tuple, get_column_letter
```

### `import:CellRange` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L28-L28`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `63f180054250da329b72f9f846c9875bf8980e9d5c98bd7164a8dc738eb3216c`

```python
from openpyxl.worksheet.cell_range import MultiCellRange, CellRange
```

### `import:DimensionHolder` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L29-L29`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `d2488695c871872dd904f79839781f98cd0ef2a85d8b391c946d16927b820779`

```python
from openpyxl.worksheet.dimensions import DimensionHolder
```

### `import:AutoFilter` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L30-L30`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `67753e1cf02be54f8d7cc52847736fa62108d2b7210a0d769715adb78b6b32f6`

```python
from openpyxl.worksheet.filters import AutoFilter, SortState
```

### `import:Worksheet` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L31-L31`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `26f5eb174570fe83e2c506632eb54cb87adc2935195a57324e27f8eeaa5ca026`

```python
from openpyxl.worksheet.worksheet import Worksheet
```

### `V` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L34-L34`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `41a2b2176cc210379036f67117ef27b91faf0e73ec81c3892564e850ba4a6e6d`

```python
V = TypeVar("Value")
```

### `logger` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L36-L36`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `418d8a52292fe11a53f43945488dfba58622f63f293295b81d45fb479930b805`

```python
logger = logging.getLogger("desktopenv.metrics.utils")
```

### `_xlsx_namespaces` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L38-L42`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `8a4aa084145ce08380174b562d4c001814eb0da231679882d9974d8c9e9f47bd`

```python
_xlsx_namespaces = [
    ("oo", "http://schemas.openxmlformats.org/spreadsheetml/2006/main"),
    ("x14", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"),
    ("xm", "http://schemas.microsoft.com/office/excel/2006/main")
]
```

### `_xlsx_ns_mapping` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L43-L43`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `8b38765d7780dc76b0f62fb044bbe8a88af727ff765d8502816029a56a1698ff`

```python
_xlsx_ns_mapping = dict(_xlsx_namespaces)
```

### `_xlsx_ns_imapping` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L45-L45`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a264b9b21c188a13b24c72459b041b142fb52fb6aa9415908fa9e8f0850cb00e`

```python
_xlsx_ns_imapping["http://schemas.openxmlformats.org/spreadsheetml/2006/main"] = None
```

### `_sheet_name_selector` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L46-L46`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `124ed7a11d5adf07afc348ffb81ad3ec8ed300f268a2aa864b9db13b58481a9e`

```python
_sheet_name_selector = lxml.cssselect.CSSSelector("oo|sheets>oo|sheet", namespaces=_xlsx_ns_mapping)
```

### `_sparklines_selector` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L47-L47`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `7e6bc8931a580a30bffca4b446e7b57e6c8a7261885323f5f5cfb2979f1ed9cc`

```python
_sparklines_selector = lxml.cssselect.CSSSelector("x14|sparkline", namespaces=_xlsx_ns_mapping)
```

### `load_sparklines` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L50-L85`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `89c0ddd2bc37e5529439a1ee36a76de433b117ed8bc7b0c2bcc8bbb9e69b4dc8`

```python
def load_sparklines(xlsx_file: str, sheet_name: str) -> Dict[str, str]:
    #  function load_sparklines {{{ # 
    """
    Args:
        xlsx_file (str): path to xlsx
        sheet_name (str): sheet name

    Returns:
        List[Dict[str, str]]: sparkline definitions in form of
          {
            "F3": "Sheet1!C3:E3"
          }
    """

    # read xlsx
    try:
        with zipfile.ZipFile(xlsx_file, "r") as z_f:
            with z_f.open("xl/workbook.xml") as f:
                workbook_database: _Element = lxml.etree.fromstring(f.read())
                sheets: List[_Element] = _sheet_name_selector(workbook_database)
                sheet_names: Dict[str, str] = {sh.get("name"): sh.get("sheetId") for sh in sheets}
            with z_f.open("xl/worksheets/sheet{:}.xml".format(sheet_names[sheet_name])) as f:
                sheet: _Element = lxml.etree.fromstring(f.read())
                sparklines: List[_Element] = _sparklines_selector(sheet)
    except zipfile.BadZipFile:
        return {}

    sparklines_dict: Dict[str, str] = {}
    for sp_l in sparklines:
        sparkline_xml: str = lxml.etree.tostring(sp_l, encoding="unicode")
        sparkline: Dict[str, Dict[str, str]] = xmltodict.parse(sparkline_xml
                                                               , process_namespaces=True
                                                               , namespaces=_xlsx_ns_imapping
                                                               )
        sparklines_dict[sparkline["x14:sparkline"]["xm:sqref"]] = sparkline["x14:sparkline"]["xm:f"]
    return sparklines_dict
```

### `load_charts` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L98-L184`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `394708508d3f9ad678aeda707218e36ad832f18e650ef56f751f4f331b959ae7`

```python
def load_charts(xlsx_file: Workbook, sheet_name: str, **options) -> Dict[str, Any]:
    #  function load_charts {{{ # 
    """
    Args:
        xlsx_file (Workbook): concerned excel book
        sheet_name (str): sheet name
        options (Dict[str, List[str]]): dict like {"chart_props": list of str}
          giving the concerned chart properties

    Returns:
        Dict[str, Any]: information of charts, dict like
          {
            <str representing data source>: {
                <str as property>: anything
            }
          }
    """

    # workbook: Workbook = openpyxl.load_workbook(filename=xlsx_file)
    try:
        worksheet: Worksheet = xlsx_file[sheet_name]
    except KeyError:
        return {}
    charts: List[ChartBase] = worksheet._charts

    chart_set: Dict[str, Any] = {}
    chart_props: Set[str] = set(options["chart_props"]) if "chart_props" in options else set()
    for ch in charts:
        series: List[str] = []
        for ser in ch.series:
            if hasattr(ser.val, "numRef") and hasattr(ser.val.numRef, "f"):
                value_str: str = ser.val.numRef.f
            elif hasattr(ser.val, "strRef") and hasattr(ser.val.strRef, "f"):
                value_str: str = ser.val.strRef.f
            else:
                value_str: str = ""
            if hasattr(ser.cat, "numRef") and hasattr(ser.cat.numRef, "f"):
                categ_str: str = ser.cat.numRef.f
            elif hasattr(ser.cat, "strRef") and hasattr(ser.cat.strRef, "f"):
                categ_str: str = ser.cat.strRef.f
            else:
                categ_str: str = ""
            series.append("{:},{:}".format(value_str, categ_str))
        series: str = ";".join(series)

        # TODO: maybe more aspects, like chart type
        info: Dict[str, Any] = {}

        if "title" in chart_props:
            try:
                info["title"] = ch.title.tx.rich.p[0].r[0].t
            except:
                info["title"] = None
        if "legend" in chart_props:
            info["legend"] = ch.legend.position if ch.legend is not None else None
        if "anchor" in chart_props:
            info["anchor"] = [ch.anchor.editAs
                , ch.anchor._from.col, ch.anchor.to.row
                , ch.anchor.to.col, ch.anchor.to.row
                              ]
        if "width" in chart_props:
            info["width"] = ch.width
        if "height" in chart_props:
            info["height"] = ch.height
        if "type" in chart_props:
            info["type"] = ch.tagname
        if "direction" in chart_props:
            info["direction"] = ch.barDir

        if "xtitle" in chart_props:
            try:
                info["xtitle"] = ch.x_axis.title.tx.rich.p[0].r[0].t
            except:
                info["xtitle"] = None
        if "ytitle" in chart_props:
            try:
                info["ytitle"] = ch.y_axis.title.tx.rich.p[0].r[0].t
            except:
                info["ytitle"] = None
        if "ztitle" in chart_props:
            try:
                info["ztitle"] = ch.z_axis.title.tx.rich.p[0].r[0].t
            except:
                info["ztitle"] = None
        chart_set[series] = info
    logger.debug(".[%s].charts: %s", sheet_name, repr(chart_set))
    return chart_set
```

### `load_pivot_tables` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L197-L278`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `9ec34c0eed42522616966e97bd17a53480c72455783cc3aa199b2d83f626e44a`

```python
def load_pivot_tables(xlsx_file: Workbook, sheet_name: str, **options) -> Dict[str, Any]:
    #  function load_pivot_tables {{{ # 
    """
    Args:
        xlsx_file (Workbook): concerned excel book
        sheet_name (str): sheet name
        options (Dict[str, List[str]]): dict like {"pivot_props": list of str}
          giving the concerned pivot properties

    Returns:
        Dict[str, Any]: information of pivot tables, dict like
          {
            <str representing data source>: {
                <str as property>: anything
            }
          }
    """

    try:
        worksheet: Worksheet = xlsx_file[sheet_name]
    except KeyError:
        return {}
    pivots: List[PivotTableDefinition] = worksheet._pivots

    pivot_set: Dict[str, Any] = {}
    pivot_props: Set[str] = set(options.get("pivot_props", []))
    for pvt in pivots:
        raw_selection: List[List[tuple[Optional[bool], int]]] = \
            [[(itm.h, itm.x) for itm in f.items if itm.x is not None] \
             for f in pvt.pivotFields
             ]
        raw__selection: List[List[tuple[Optional[bool], int]]] = list(
            itertools.dropwhile(lambda r: len(r) == 0, raw_selection))
        left_bias = len(raw_selection) - len(raw__selection)
        selection: List[List[tuple[Optional[bool], int]]] = list(
            (itertools.dropwhile(lambda r: len(r) == 0, reversed(raw__selection))))[::-1]
        right_bias = len(raw__selection) - len(selection)
        cache_source: PivotCacheSource = pvt.cache.cacheSource
        cell_range1: str
        cell_range2: str
        cell_range1, cell_range2 = cache_source.worksheetSource.ref.split(":")
        cell_range1: Tuple[int, int] = coordinate_to_tuple(cell_range1)
        cell_range1 = (cell_range1[0], cell_range1[1] + left_bias)
        cell_range2: Tuple[int, int] = coordinate_to_tuple(cell_range2)
        cell_range2 = (cell_range2[0], cell_range2[1] - right_bias)
        source: str = "{:};{:}:{:};{:}".format(cache_source.type, cell_range1, cell_range2,
                                               cache_source.worksheetSource.sheet)

        info: Dict[str, Any] = {}
        if "name" in pivot_props:
            info["name"] = pvt.name

        if "show_total" in pivot_props:
            info["show_total"] = pvt.visualTotals
        if "show_empty_row" in pivot_props:
            info["show_empty_row"] = pvt.showEmptyRow
        if "show_empty_col" in pivot_props:
            info["show_empty_col"] = pvt.showEmptyCol
        if "show_headers" in pivot_props:
            info["show_headers"] = pvt.showHeaders

        if "location" in pivot_props:
            info["location"] = pvt.location
        if "filter" in pivot_props or "selection" in pivot_props:
            info["selection"] = selection if "ordered" in pivot_props else list(set(r) for r in selection)
        if "filter" in pivot_props:
            info["filter_fields"] = set(f.fld for f in pvt.pageFields)
        if "col_fields" in pivot_props:
            info["col_fields"] = [f.x - left_bias for f in pvt.colFields]
        if "row_fields" in pivot_props:
            info["row_fields"] = [f.x - left_bias for f in pvt.rowFields]
        if "data_fields" in pivot_props:
            info["data_fields"] = [
                "{:d};{:};{:};{:}".format(f.fld - left_bias, f.name if "data_fields_name" in pivot_props else ""
                                          , f.subtotal, f.showDataAs
                                          ) \
                for f in pvt.dataFields
                ]

        pivot_set[source] = info
    logger.debug(".[%s].pivots: %s", sheet_name, repr(pivot_set))
    return pivot_set
```

### `_shared_str_selector` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L282-L282`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `7de7a3f876b3eb22cdf39057e419f11af921e0ac7f7d9c235b0ac7ff34de9720`

```python
_shared_str_selector = lxml.cssselect.CSSSelector("oo|sst>oo|si", namespaces=_xlsx_ns_mapping)
```

### `_shared_str_value_selector` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L283-L283`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `655f25fdf35b029ad8785eed8e815b3e2cce8c30232ae24cf6c1fa73b0e1ce93`

```python
_shared_str_value_selector = lxml.cssselect.CSSSelector("oo|t", namespaces=_xlsx_ns_mapping)
```

### `read_cell_value` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L286-L352`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `bf6b95a8858b6d325be2324fb9be6adfb3e8c265d674d97a8b30d1390b578fe1`

```python
def read_cell_value(xlsx_file: str, sheet_name: str, coordinate: str) -> Any:
    #  read_cell_value {{{ # 
    logger.debug(f"Reading cell value from {xlsx_file}, sheet: {sheet_name}, coordinate: {coordinate}")
    
    # Check if file exists
    if not os.path.exists(xlsx_file):
        logger.error(f"Excel file not found: {xlsx_file}")
        return None
    
    try:
        with zipfile.ZipFile(xlsx_file, "r") as z_f:
            try:
                with z_f.open("xl/sharedStrings.xml") as f:
                    shared_str_xml: _Element = lxml.etree.fromstring(f.read())
                    str_elements: List[_Element] = _shared_str_selector(shared_str_xml)
                    shared_strs: List[str] = [ "".join(t.text for t in _shared_str_value_selector(elm))\
                                           for elm in str_elements
                                             ]
            except:
                #logger.exception("Read shared strings error: %s", xlsx_file)
                logger.debug("Read shared strings error: %s", xlsx_file)
                shared_strs: List[str] = []

            with z_f.open("xl/workbook.xml") as f:
                workbook_database: _Element = lxml.etree.fromstring(f.read())
                sheets: List[_Element] = _sheet_name_selector(workbook_database)
                sheet_names: Dict[str, str] = {sh.get("name"): sh.get("sheetId") for sh in sheets}

            with z_f.open("xl/worksheets/sheet{:}.xml".format(sheet_names[sheet_name])) as f:
                sheet: _Element = lxml.etree.fromstring(f.read())
                cells: List[_Element] = \
                    lxml.cssselect.CSSSelector('oo|row>oo|c[r="{:}"]'.format(coordinate)
                                               , namespaces=_xlsx_ns_mapping
                                               )(sheet)
                if len(cells) == 0:
                    logger.debug(f"Cell {coordinate} not found in sheet {sheet_name}")
                    return None
                cell: _Element = cells[0]
    except zipfile.BadZipFile as e:
        logger.error(f"Bad zip file {xlsx_file}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Sheet {sheet_name} not found in {xlsx_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {xlsx_file}: {e}")
        return None

    cell: Dict[str, str] = xmltodict.parse(lxml.etree.tostring(cell, encoding="unicode")
                                           , process_namespaces=True
                                           , namespaces=_xlsx_ns_imapping
                                           )
    logger.debug("%s.shared_strings: %s", xlsx_file, repr(shared_strs))
    logger.debug("%s.%s[%s]: %s", xlsx_file, sheet_name, coordinate, repr(cell))
    try:
        if "@t" not in cell["c"] or cell["c"]["@t"] == "n":
            return float(cell["c"]["v"])
        if cell["c"]["@t"] == "s":
            return shared_strs[int(cell["c"]["v"])]
        if cell["c"]["@t"] == "str":
            return cell["c"]["v"]
        if cell["c"]["@t"] == "inlineStr":
            return cell["c"]["is"]["t"]
        if cell["c"]["@t"] == "e":
            return cell["c"]["v"]
    except (KeyError, ValueError):
        return None
```

### `_read_cell_style` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L370-L412`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `88163d8f8dc33483d131e8ce8a2199a50d1794a47346f1b91b2fa9ddeca3ecc1`

```python
def _read_cell_style(style_name: str, cell: Union[Cell, MergedCell], diff_style: Optional[DifferentialStyle] = None) -> Any:
    if style_name == "number_format":
        return (cell.number_format if diff_style is None else diff_style.numFmt.formatCode) \
            if cell.value is not None and cell.data_type == "n" else None
    elif style_name == "font_name":
        return (diff_style or cell).font.name if cell.value is not None else None
    elif style_name == "font_family":
        return (diff_style or cell).font.family if cell.value is not None else None
    elif style_name == "font_color":
        return (diff_style or cell).font.color.rgb if cell.value is not None else None
    elif style_name == "font_bold":
        return (diff_style or cell).font.bold if cell.value is not None else None
    elif style_name == "font_italic":
        return (diff_style or cell).font.italic if cell.value is not None else None
    elif style_name == "font_underline":
        return (diff_style or cell).font.underline if cell.value is not None else None
    elif style_name == "font_size":
        return (diff_style or cell).font.size if cell.value is not None else None
    elif style_name == "fill_type":
        try:
            return (diff_style or cell).fill.tagname
        except:
            return None
    elif style_name == "bgcolor" or style_name == "fgcolor":
        try:
            #return (diff_style or cell).fill.bgColor.rgb
            if diff_style is not None:
                return diff_style.fill.bgColor.rgb
            else:
                return cell.fill.fgColor.rgb
        except:
            return None
    #elif style_name == "fgcolor":
        #try:
            #return (diff_style or cell).fill.fgColor.rgb
        #except:
            #return None
    elif style_name == "hyperlink":
        return cell.hyperlink or "" if cell.value is not None else None
    elif style_name == "merge":
        return isinstance(cell, MergedCell)
    else:
        raise NotImplementedError("Unsupported Style: {:}".format(style_name))
```

### `_process_xlsx_cf_operator` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L414-L449`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `4140bf6a94ef77e11dca981bcd056ca0ba4eac3a3791fdbb2bda6ec4f30cb9b2`

```python
def _process_xlsx_cf_operator(operator: str, value: Any, ref: List[Any]) -> bool:
    #  function _process_xlsx_cf_operator {{{ # 
    # "containsText", "lessThanOrEqual", "notBetween", "lessThan", "notContains", "beginsWith", "equal", "greaterThanOrEqual", "between", "endsWith", "notEqual", "greaterThan"
    try:
        if operator=="lessThanOrEqual":
            result: bool = value<=ref[0]
        elif operator=="lessThan":
            result: bool = value<ref[0]
        elif operator=="equal":
            result: bool = value==ref[0]
        elif operator=="greaterThanOrEqual":
            result: bool = value>=ref[0]
        elif operator=="notEqual":
            result: bool = value!=ref[0]
        elif operator=="greaterThan":
            result: bool = value>ref[0]
        elif operator=="between":
            small_one: float
            large_one: float
            small_one, large_one = min(ref), max(ref)
            result: bool = value>=small_one and value<=large_one
        elif operator=="notBetween":
            small_one: float
            large_one: float
            small_one, large_one = min(ref), max(ref)
            result: bool = value<small_one or value>large_one
        else:
            #raise NotImplementedError("Not Implemented CondFormat Operator: {:}".format(operator))
            logger.exception("Not Implemented CondFormat Operator: {:}".format(operator))
        return result
    except TypeError:
        logger.exception("Unmatched type of %s and %s. Auto to False", repr(value), repr(ref))
        return False
    except IndexError:
        logger.exception("ref array doesn't have enough elements. Auto to False: %s", repr(ref))
        return False
```

### `_absolute_range_pattern` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L452-L458`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `0ac5de58bff5be57cf94cd84bd3f31bfb46dc32eab869b2d83bc8809fc4da3b6`

```python
_absolute_range_pattern: Pattern[str] = re.compile(r"""\$(?P<col1>[A-Z]{1,3})\$(?P<row1>\d+) # coord1
                                                        (?::
                                                          \$(?P<col2>[A-Z]{1,3})\$(?P<row2>\d+) # coord2
                                                        )?
                                                     """
                                                   , re.X
                                                   )
```

### `load_xlsx_styles` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L461-L597`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `6bcc16f6e8e7cb7444d127291d1e81329f05b63acbf662edf491c06d4156f033`

```python
def load_xlsx_styles(xlsx_file: Workbook, sheet_name: str, book_name: str, **options) -> Dict[str, List[Any]]:
    #  function load_xlsx_styles {{{ # 
    """
    Args:
        xlsx_file (Workbook): concerned excel book
        sheet_name (str): sheet name
        book_name (str): book name
        options (Dict[str, List[str]): dick like {"props": list of str} giving
          the concerned styles

    Returns:
        Dict[str, List[Any]]: dict like
          {
            <str as cell coordinates>: list of anything indicating concerned
              property values
          }
    """

    try:
        worksheet: Worksheet = xlsx_file[sheet_name]
    except KeyError:
        return {}

    style_dict: Dict[str, List[Any]] = {}
    concerned_styles: List[str] = options.get("props", [])

    # Handles Cell Styles
    for col in worksheet.iter_cols():
        for c in col:
            style_list: List[Any] = []
            for st in concerned_styles:
                style_list.append(_read_cell_style(st, c))
            style_dict[c.coordinate] = style_list

    # Handles Conditional Formatting
    conditional_formattings: ConditionalFormattingList = worksheet.conditional_formatting
    formula_parser = formulas.Parser()
    for fmt in conditional_formattings:
        for r in fmt.rules:
            active_cells: List[Cell] = []

            #  Process CF Formulae {{{ # 
            formulae: List[Callable[[Any], Any]] = []
            argument_lists: List[List[Any]] = []
            has_error = False
            for fml in r.formula:
                try:
                    formula_func: Callable[[Any], Any] =\
                            formula_parser.ast("=" + fml)[1].compile()
                    logger.debug("CondFormat rule formula: %s", fml)
                except:
                    logger.exception("Formula parsing error: %s. Skipping.", repr(fml))
                    has_error = True
                    break

                arguments: List[Any] = []
                absolute_range_match: List[Tuple[str, str, str, str]] = _absolute_range_pattern.findall(fml)
                for m in absolute_range_match:
                    logger.debug("Absolute ranges: %s", repr(m))
                    if m[2] is None and m[3] is None:
                        arguments.append(read_cell_value(book_name, sheet_name, coordinate="{:}{:}".format(m[0], m[1])))
                    else:
                        arguments.append([read_cell_value(book_name, sheet_name
                                                          , coordinate="{:}{:}".format(get_column_letter(c[1])
                                                                                       , c[0]
                                                                                       )
                                                          ) \
                                          for c in CellRange("{:}{:}:{:}{:}".format(m[0], m[1], m[2], m[3])).cells \
                                          ]
                                         )
                logger.debug("Absolute range arguments: %s", repr(arguments))

                formulae.append(formula_func)
                argument_lists.append(arguments)

            if has_error:
                continue
            #  }}} Process CF Formulae # 

            #  Process Condition Accroding to Type {{{ # 
            if r.type in { "expression"
                         , "containsText", "notContainsText"
                         , "endsWith", "beginsWith"
                         , "containsErrors", "notContainsErrors"
                         }:
                condition: Callable[[Any], bool] = formulae[0]
                arguments: List[Any] = argument_lists[0]
                is_active: Callable[[Any], bool] = lambda v: condition(v, *arguments)
            elif r.type == "cellIs":
                operator: str = r.operator
                try:
                    references: List[Any] = [fml() for fml in formulae]
                except:
                    logger.exception("Error occurs while calculating reference values for cellIs condition formatting.")
                    continue
                is_active: Callable[[Any], bool] =\
                        lambda v: _process_xlsx_cf_operator(operator, v, references)
            else:
                #raise NotImplementedError("Not Implemented Condition Type: {:}".format(r.type))
                # e.g., type=top10 (rank=number, percent=bool, bottom=bool)
                # type=aboveAverage (equalAverage=bool, aboveAverage=bool)
                # type=duplicateValues / type=uniqueValues
                logger.exception("Not Implemented Condition Type: {:}".format(r.type))
            #  }}} Process Condition Accroding to Type # 


            #  Test Each Cell {{{ # 
            nb_contiguous_nothings = 0
            for rge in fmt.cells:
                for c in rge.cells:
                    cell: Cell = worksheet.cell(row=c[0], column=c[1])
                    cell_value = read_cell_value(book_name, sheet_name
                                                 , coordinate="{:}{:d}".format(get_column_letter(c[1])
                                                                               , c[0]
                                                                               )
                                                 )
                    if cell_value is None:
                        nb_contiguous_nothings += 1
                        if nb_contiguous_nothings>50:
                            break
                        continue
                    else:
                        try:
                            satisfies_condition: bool = is_active(cell_value)
                        except:
                            logger.exception("Error in formula calculation with cell value %d", repr(cell_value))
                            satisfies_condition = False
                        if satisfies_condition:
                            logger.debug("Active Cell %s(%s) for %s", repr(cell), repr(cell_value), r.formula[0])
                            active_cells.append(cell)
            #  }}} Test Each Cell # 

            for c in active_cells:
                style_dict[c.coordinate] = [_read_cell_style(st, c, r.dxf) for st in concerned_styles]

    logger.debug(".[%s].styles: %s", sheet_name, repr(style_dict))
    return style_dict
```

### `load_rows_or_cols` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L613-L641`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `56f2d5ee21f2cd417cc4185d3b7a5deccae3cb1ee7f99b7e8fea11ad9f97c8a9`

```python
def load_rows_or_cols(xlsx_file: Workbook, sheet_name: str, **options) \
        -> Dict[Union[int, str], Dict[str, Any]]:
    #  function load_rows_or_cols {{{ # 
    """
    Args:
        xlsx_file (Workbook): concerned excel book
        sheet_name (str): sheet name
        options (Dict[str, List[str]]): dict like
          {"obj": "row" | "column", "props": list of str} giving the concerned
          row/column properties

    Returns:
        Dict[Union[int, str], Dict[str, Any]]: row/column information
    """

    try:
        worksheet: Worksheet = xlsx_file[sheet_name]
    except KeyError:
        return {}
    objs: DimensionHolder = getattr(worksheet, "{:}_dimensions".format(options["obj"]))

    obj_set: Dict[int, Any] = {}
    obj_props: Set[str] = set(options.get("props", []))
    for obj_no, obj_dms in objs.items():
        info_dict: Dict[str, Any] = {}
        for prop in obj_props:
            info_dict[prop] = getattr(obj_dms, prop)
        obj_set[obj_no] = info_dict
    return obj_set
```

### `load_filters` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L645-L700`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `3f87c5828e5a572717a2bebcb103d1f63f5c944b5a321c80284d076d03651ab3`

```python
def load_filters(xlsx_file: Workbook, sheet_name: str, **options) -> Dict[str, Any]:
    #  function load_filters {{{ # 
    try:
        worksheet: Worksheet = xlsx_file[sheet_name]
    except KeyError:
        return {}

    filters: AutoFilter = worksheet.auto_filter
    filter_dict: Dict[str, Any] = {}
    filter_dict["ref"] = filters.ref

    # filterColumn
    filter_column_set: List[Dict[str, Any]] = []
    for flt_clm in filters.filterColumn:
        filter_column: Dict[str, Any] = {}
        filter_column["col_id"] = flt_clm.colId
        filter_column["hidden_button"] = flt_clm.hiddenButton
        filter_column["show_button"] = flt_clm.showButton
        if flt_clm.filters is not None:
            filter_column["filters_blank"] = flt_clm.filters.blank
            filter_column["filters"] = set(flt_clm.filters.filter)
        if flt_clm.customFilters is not None:
            filter_column["custom_filters_op"] = flt_clm.customFilters._and
            filter_column["custom_filters"] = set((flt.operator
                                                   , flt.val
                                                   ) \
                                                  for flt in flt_clm.customFilters.customFilter
                                                  )
        filter_column_set.append(filter_column)
    filter_column_set = list(sorted(filter_column_set
                                    , key=(lambda d: d["col_id"])
                                    )
                             )
    filter_dict["filter_column"] = filter_column_set

    # sortState
    sort_state: Optional[SortState] = filters.sortState
    if sort_state is not None:
        sort_state_dict: Dict[str, Any] = {}
        sort_state_dict["sort"] = sort_state.columnSort
        sort_state_dict["case"] = sort_state.caseSensitive
        sort_state_dict["method"] = sort_state.sortMethod
        sort_state_dict["ref"] = sort_state.ref
        sort_state_dict["condition"] = list({"descending": cdt.descending
                                                , "key": cdt.sortBy
                                                , "ref": cdt.ref
                                                , "custom_list": cdt.customList
                                                , "dxf_id": cdt.dxfId
                                                , "icon": cdt.iconSet
                                                , "iconid": cdt.iconId
                                             } \
                                            for cdt in sort_state.sortCondition
                                            )
        filter_dict["sort_state"] = sort_state_dict

    return filter_dict
```

### `_multicellrange_containsby` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L708-L709`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `982e04d4e42012b1a1d089021300a629e53c6c1cc3e175e821ddace15a580c07`

```python
def _multicellrange_containsby(subset_candidate: MultiCellRange, superset_candidate: MultiCellRange) -> bool:
    return all(r in superset_candidate for r in subset_candidate)
```

### `_match_value_to_rule` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L712-L767`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `bb5670f4440cac8898c7dca4074dc3d5ef239fc421866c1f6f9bd7ece17ff98f`

```python
def _match_value_to_rule(value: V, rule: Dict[str, Union[str, V]]) -> bool:
    """
    Args:
        value (V): value to match
        rule (Dict[str, Union[str, V]]): rule dict like
          {
            "method": str
            "ref": V as ref value
          }

    Returns:
        bool
    """

    if rule["method"].startswith("re"): # re.FLAGs
        flags: List[str] = rule["method"].split(".")[1:]
        flags: Iterable[re.RegexFlag] = (getattr(re, fl) for fl in flags)
        flag: re.RegexFlag = functools.reduce(operator.or_, flags, re.RegexFlag(0))
        logger.debug("REFLAG: %s", repr(flag))

        match_: Optional[Match[str]] = re.search(rule["ref"], value, flag)
        return match_ is not None
    if rule["method"] in {"eq", "ne"
        , "le", "lt"
        , "ge", "gt"
                          }:
        return getattr(operator, rule["method"])(value, rule["ref"])
    if rule["method"].startswith("approx"): # approx:THRESHOLD
        threshold: float = float(rule["method"].split(":")[1])
        logger.debug("Approx: TH%f, REF%f, VAL%s", threshold, rule["ref"], repr(value))
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False
        else:
            return abs(value - rule["ref"]) <= threshold
    if rule["method"] == "spreadsheet_range":
        subset_limit = MultiCellRange(rule["ref"][0])
        superset_limit = MultiCellRange(rule["ref"][1])
        return _multicellrange_containsby(subset_limit, value) \
            and _multicellrange_containsby(value, superset_limit)
    if rule["method"].startswith("range."):  # e.g., range.te [0, 2] -> 0 < x <= 2
        left_et = rule["method"][6]
        right_et = rule["method"][7]
        return getattr(operator, "l" + left_et)(rule["ref"][0], value) \
            and getattr(operator, "l" + right_et)(value, rule["ref"][1])
    if rule["method"] in {"str_list_eq", "str_set_eq"}:
        if value is None:
            return False
        container_type_str: str = rule["method"][4:-3]
        container_type = getattr(builtins, container_type_str)

        value: container_type = container_type(value.strip("\"'").split(","))
        ref: container_type = container_type(rule["ref"])
        return value == ref
    raise NotImplementedError()
```
