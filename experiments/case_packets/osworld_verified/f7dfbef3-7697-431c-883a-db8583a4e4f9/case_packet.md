# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `f7dfbef3-7697-431c-883a-db8583a4e4f9`
- task_id: `f7dfbef3-7697-431c-883a-db8583a4e4f9`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `multi_apps`
- snapshot: `libreoffice_writer`
- related apps: `libreoffice_writer, terminal`
- official instruction: Could you convert all `.doc` files in current directory to PDF all at once in the command line?
- evaluator functions: `check_include_exclude, compare_archive`
- evaluator conjunction: `and`
- evaluator result getter types: `vm_command_line, vm_file`
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
- `official/desktop_env/evaluators/getters/general.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/chrome.py`
- `official/desktop_env/evaluators/metrics/general.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/multi_apps/f7dfbef3-7697-431c-883a-db8583a4e4f9.json`

Source SHA-256: `63d49002f7ee393a5eab0b6c1b6f663a2bab04e9afd29f5a3e7b3535a376b5ec`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Desktop/doc.tar.gz",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/f7dfbef3-7697-431c-883a-db8583a4e4f9/doc.tar.gz"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": [
          "/bin/bash",
          "-c",
          "tar -zxf /home/user/Desktop/doc.tar.gz -C /home/user/Desktop/ && rm /home/user/Desktop/doc.tar.gz"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "/bin/bash",
          "-c",
          "history -c && echo > ~/.bash_history && sleep 3"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": "export DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus'\ngnome-terminal --maximize --working-directory=/home/user/Desktop",
        "shell": true
      },
      "type": "execute"
    }
  ],
  "evaluator": {
    "expected": [
      {
        "rules": {
          "exclude": [
            "failed to complete this task"
          ],
          "include": [
            "catch the desired command"
          ]
        },
        "type": "rule"
      },
      {
        "dest": "pdf_gold.tar.gz",
        "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/f7dfbef3-7697-431c-883a-db8583a4e4f9/pdf.tar.gz",
        "type": "cloud_file"
      }
    ],
    "func": [
      "check_include_exclude",
      "compare_archive"
    ],
    "options": [
      {},
      {
        "file_type": "pdf"
      }
    ],
    "postconfig": [
      {
        "parameters": {
          "command": [
            "/bin/bash",
            "-c",
            "cd /home/user/Desktop && tar -zcf pdf.tar.gz *.pdf"
          ]
        },
        "type": "execute"
      },
      {
        "parameters": {
          "command": [
            "/bin/bash",
            "-c",
            "killall gnome-terminal-server"
          ]
        },
        "type": "execute"
      }
    ],
    "result": [
      {
        "command": [
          "/bin/bash",
          "-c",
          "output=$(cat ~/.bash_history | grep -E \"(soffice|libreoffice).+--convert-to\\s+pdf.+\\*\\.doc\"); if [ -z \"$output\" ]; then echo \"failed to complete this task\"; else echo \"catch the desired command\"; fi"
        ],
        "type": "vm_command_line"
      },
      {
        "dest": "pdf.tar.gz",
        "path": "/home/user/Desktop/pdf.tar.gz",
        "type": "vm_file"
      }
    ]
  },
  "fixed_ip": false,
  "id": "f7dfbef3-7697-431c-883a-db8583a4e4f9",
  "instruction": "Could you convert all `.doc` files in current directory to PDF all at once in the command line?",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "libreoffice_writer",
    "terminal"
  ],
  "snapshot": "libreoffice_writer",
  "source": "https://www.thegeekdiary.com/libreoffice-command-examples-in-linux/",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `211a25203b06ca10a279e1f6911b7c05699e2a8c9ecdcb0478f13a9190db5dbc`

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
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0",
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "start_line": 2,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "start_line": 3,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "513489c0211aa3c0579ec58feebfcd3ae59d8e41f858aa4c2094d5bb859a009b",
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "start_line": 5,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
    },
    {
      "end_line": 22,
      "excerpt_sha256": "8e287cc013425deaa233ab39da670817ea4beccb8d527fb96cf9d31d14b4b59d",
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "start_line": 8,
      "symbol": "get_vm_command_line",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
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
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 2,
      "symbol": "import:os",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "7002efbd1fd0861b54df3575e2921d2c259d2a8379c4d5fff5f8842a2552c143",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 4,
      "symbol": "import:shutil",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "0578139baa8835231355e06f7fc51643ad48d2c6333bd0777e80b84a93b8aad7",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 5,
      "symbol": "import:tempfile",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "891d1d796c0923f73a03f7cf751549361c79949540451e07b3397794cb96acb4",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 9,
      "symbol": "import:List",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 11,
      "excerpt_sha256": "7194935c17d209f59a0980ef4638f4fed4540999067228ebed04b898db246859",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 11,
      "symbol": "import:fuzz",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 16,
      "excerpt_sha256": "c30dca9648074311179d05d653b45dc7d88ae311b6544a016bbe93428eef8d8c",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 16,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 233,
      "excerpt_sha256": "388c7cee72afc6d8626409abf5ea22c8e484bb43dc0918abbea7638df1596748",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 210,
      "symbol": "compare_pdfs",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 236,
      "excerpt_sha256": "a3f019dc09626e377aa660e914576420f1d43c84e2be892c962b89a8142ecda7",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 236,
      "symbol": "import:fitz",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 380,
      "excerpt_sha256": "53277fc5c9ed4859288f1719cc767de99a3e9863a6b43cd6d845058867a7248b",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 317,
      "symbol": "compare_archive",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
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
      "end_line": 38,
      "excerpt_sha256": "a011b34a9f8fcb67df70f4c57ff616afc980a5e1cd272e886b174467c733fe22",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 28,
      "symbol": "check_include_exclude",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected[0]",
      "config_sha256": "f072a23cf5906cd4b979a4fe1152376b2d36f43bcf014bc8c9e37bb8b31d7d7e",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    },
    {
      "config_path": "evaluator.expected[1]",
      "config_sha256": "d0d328eb36aa1f477ef2ea17e3ae4091363aaca8c8f1bb47726ac15fa0f7c3f2",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cloud_file",
      "type": "cloud_file"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "93036ef3112c724dba1c100cc8e9f75722f7247061b7d62892213bf84b8e8d69",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": true,
  "metric_options": [
    {},
    {
      "file_type": "pdf"
    }
  ],
  "metrics": [
    {
      "name": "check_include_exclude",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7"
    },
    {
      "name": "compare_archive",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "slot": 1,
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
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "upstream_path": "desktop_env/evaluators/getters/file.py"
    },
    {
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "upstream_path": "desktop_env/evaluators/getters/general.py"
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
    },
    {
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    }
  ],
  "postconfig_present": true,
  "result_getters": [
    {
      "config_path": "evaluator.result[0]",
      "config_sha256": "e33fee48ca6d5177b6d036330a9338fc3d2f397b883804b5ba991ce8bd34ca5a",
      "packet_path": "official/desktop_env/evaluators/getters/general.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py",
      "source_sha256": "50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566",
      "symbol": "get_vm_command_line",
      "type": "vm_command_line"
    },
    {
      "config_path": "evaluator.result[1]",
      "config_sha256": "e55c78162d5c733131932c335cc222cdd47edc4ef7714af1b16e5e4be4092f8c",
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
  "task_id": "f7dfbef3-7697-431c-883a-db8583a4e4f9"
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

### `import:logging` from `official/desktop_env/evaluators/getters/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py#L1-L1`

Full source SHA-256: `50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Dict` from `official/desktop_env/evaluators/getters/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py#L2-L2`

Full source SHA-256: `50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566`

Exact excerpt SHA-256: `c49161df04bec6b7e482b45a2fca154b9e304dbdbd9aeb94a340c881110cd7f0`

```python
from typing import Dict
```

### `import:requests` from `official/desktop_env/evaluators/getters/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py#L3-L3`

Full source SHA-256: `50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `logger` from `official/desktop_env/evaluators/getters/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py#L5-L5`

Full source SHA-256: `50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566`

Exact excerpt SHA-256: `513489c0211aa3c0579ec58feebfcd3ae59d8e41f858aa4c2094d5bb859a009b`

```python
logger = logging.getLogger("desktopenv.getters.general")
```

### `get_vm_command_line` from `official/desktop_env/evaluators/getters/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/general.py#L8-L22`

Full source SHA-256: `50e690aa29023d7afb42260a98fa229ab00f2291ae2c06b5056295f2133a1566`

Exact excerpt SHA-256: `8e287cc013425deaa233ab39da670817ea4beccb8d527fb96cf9d31d14b4b59d`

```python
def get_vm_command_line(env, config: Dict[str, str]):
    vm_ip = env.vm_ip
    port = env.server_port
    command = config["command"]
    shell = config.get("shell", False)

    response = requests.post(f"http://{vm_ip}:{port}/execute", json={"command": command, "shell": shell})

    print(response.json())

    if response.status_code == 200:
        return response.json()["output"]
    else:
        logger.error("Failed to get vm command line. Status code: %d", response.status_code)
        return None
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

### `import:logging` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L1-L1`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:os` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L2-L2`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `3727adff524e0616022eadd8f4af21a0778b29fc4c77bdfefd1afce2cbf5e4b7`

```python
import os
```

### `import:shutil` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L4-L4`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `7002efbd1fd0861b54df3575e2921d2c259d2a8379c4d5fff5f8842a2552c143`

```python
import shutil
```

### `import:tempfile` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L5-L5`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `0578139baa8835231355e06f7fc51643ad48d2c6333bd0777e80b84a93b8aad7`

```python
import tempfile
```

### `import:List` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L9-L9`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `891d1d796c0923f73a03f7cf751549361c79949540451e07b3397794cb96acb4`

```python
from typing import Any, Dict, List, Union
```

### `import:fuzz` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L11-L11`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `7194935c17d209f59a0980ef4638f4fed4540999067228ebed04b898db246859`

```python
import rapidfuzz.fuzz as fuzz
```

### `logger` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L16-L16`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c30dca9648074311179d05d653b45dc7d88ae311b6544a016bbe93428eef8d8c`

```python
logger = logging.getLogger("desktopenv.metrics.chrome")
```

### `compare_pdfs` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L210-L233`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `388c7cee72afc6d8626409abf5ea22c8e484bb43dc0918abbea7638df1596748`

```python
def compare_pdfs(pdf1_path: Union[str, List[str]], pdf2_path: Union[str, List[str]]):
    """
    Compare two PDF files.
    """
    if type(pdf2_path) != list:
        pdf1_path, pdf2_path = [pdf1_path], [pdf2_path]

    def extract_text_from_pdf(pdf_path):
        """Extract text from each page of the PDF."""
        text = ""
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text.strip()

    score = 0.
    for path1, path2 in zip(pdf1_path, pdf2_path):
        try:
            text1 = extract_text_from_pdf(path1)
            text2 = extract_text_from_pdf(path2)
            score += fuzz.ratio(text1, text2) / 100
        except Exception as e:
            logger.info(f"[ERROR]: unexpected error occurred when comparing PDF files: {e}")
    return score / len(pdf2_path)
```

### `import:fitz` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L236-L236`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `a3f019dc09626e377aa660e914576420f1d43c84e2be892c962b89a8142ecda7`

```python
import fitz
```

### `compare_archive` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L317-L380`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `53277fc5c9ed4859288f1719cc767de99a3e9863a6b43cd6d845058867a7248b`

```python
def compare_archive(pred_path: str, gold_path: str, **kwargs) -> float:
    """
    Compare two archives. Note that the files in the archives should be of the same type.
    """
    file_path = kwargs.pop('file_path', '')

    if not pred_path:
        return 0.

    # Extract both archives to fresh temp dirs and always clean them up, so a
    # stale/half-written cache from a prior run can't be compared against.
    pred_folder = tempfile.mkdtemp(prefix='archive_pred_')
    gold_folder = tempfile.mkdtemp(prefix='archive_gold_')
    try:
        shutil.unpack_archive(pred_path, pred_folder)
        shutil.unpack_archive(gold_path, gold_folder)

        pred_files = sorted(os.listdir(os.path.join(pred_folder, file_path)))
        gold_files = sorted(os.listdir(os.path.join(gold_folder, file_path)))

        if pred_files != gold_files:
            return 0.

        def get_compare_function():
            file_type = kwargs.pop('file_type', 'text')
            if file_type == 'text':
                from .vscode import compare_text_file
                return compare_text_file
            elif file_type == 'pdf':
                return compare_pdfs
            elif file_type == 'docx':
                from .docs import compare_docx_files
                return compare_docx_files
            elif file_type == 'ppt':
                from .slides import compare_pptx_files
                return compare_pptx_files
            elif file_type == 'image':
                from .vlc import compare_images
                return compare_images
            elif file_type == 'csv':
                from .table import compare_csv
                return compare_csv
            elif file_type == 'table':
                from .table import compare_table
                return compare_table
            elif file_type == 'audio':
                from .vlc import compare_audios
                return compare_audios
            elif file_type == 'video':
                from .vlc import compare_videos
                return compare_videos
            else:
                raise ValueError('[ERROR]: not support file type: %s' % file_type)

        score = 0
        compare_function = get_compare_function()
        for f1, f2 in zip(pred_files, gold_files):
            fp1 = os.path.join(pred_folder, file_path, f1)
            fp2 = os.path.join(gold_folder, file_path, f2)
            score += compare_function(fp1, fp2, **kwargs)
        return score / len(pred_files)
    finally:
        shutil.rmtree(pred_folder, ignore_errors=True)
        shutil.rmtree(gold_folder, ignore_errors=True)
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L13-L13`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `f1e514bded8115f262f0549707ab0fa7cb8c30ae5335a859a177949157577897`

```python
from typing import Dict, List, Pattern
```

### `check_include_exclude` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L28-L38`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `a011b34a9f8fcb67df70f4c57ff616afc980a5e1cd272e886b174467c733fe22`

```python
def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    if result is None:
        return 0.

    print(result, rules)
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.
```
