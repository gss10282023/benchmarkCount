# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `48c46dc7-fe04-4505-ade7-723cba1aa6f6`
- task_id: `48c46dc7-fe04-4505-ade7-723cba1aa6f6`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `multi_apps`
- snapshot: `chrome`
- related apps: `chrome, os`
- official instruction: Help me to automatically set up my work space. To be specific, open project directory of OSWorld in terminal and file manager, then open github homepage and the online document of Python in chrome browser.
- evaluator functions: `check_list, is_expected_tabs`
- evaluator conjunction: `and`
- evaluator result getter types: `cache_file, open_tabs_info`
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
- `official/desktop_env/evaluators/getters/file.py`
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/chrome.py`
- `official/desktop_env/evaluators/metrics/general.py`
- `official/desktop_env/evaluators/metrics/utils.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6.json`

Source SHA-256: `c4ba87547fd9d40b846afd25a0ba5245265f291f428ead6ba75bbc89732fd678`

```json
{
  "config": [
    {
      "parameters": {
        "command": [
          "mkdir",
          "-p",
          "/home/user/Documents/Finance/receipts",
          "/home/user/Documents/Projects/OSWorld",
          "/home/user/.local/share/applications"
        ]
      },
      "type": "execute"
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
    },
    {
      "parameters": {
        "command": [
          "cp",
          "/usr/share/applications/google-chrome.desktop",
          "/home/user/.local/share/applications"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "sed",
          "-i.bak",
          "-e",
          "s#Exec=/usr/bin/google-chrome-stable#& --remote-debugging-port=1337#g",
          "/home/user/.local/share/applications/google-chrome.desktop"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "update-desktop-database"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/Documents/Finance/receipts/aws-invoice-2308.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/invoice0123456789-2308.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/receipts/aws-invoice-2309.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/invoice0123456789-2309.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/receipts/aws-invoice-2310.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/invoice0123456789-2310.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/receipts/aws-invoice-2311.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/invoice0123456789-2311.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/receipts/aws-invoice-2312.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/invoice0123456789-2312.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/receipts/X-receipt-2312.pdf",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/Receipt-0123-4567.pdf"
          },
          {
            "path": "/home/user/Documents/Finance/tally_book.xlsx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/tally_book.xlsx"
          },
          {
            "path": "/home/user/.projects.tar.xz",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/48c46dc7-fe04-4505-ade7-723cba1aa6f6/projects.tar.xz"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": [
          "tar",
          "-xJvf",
          "/home/user/.projects.tar.xz",
          "-C",
          "/home/user/Documents/Projects/OSWorld"
        ]
      },
      "type": "execute"
    }
  ],
  "evaluator": {
    "expected": [
      {
        "rules": {
          "expect": [
            "\\borg\\.gnome\\.Nautilus\\.Org\\.gnome\\.Nautilus\\b.*\\bOSWorld\\b",
            "gnome-terminal-server\\.Gnome-terminal\\b.*~/Documents/Projects/OSWorld\\b"
          ]
        },
        "type": "rule"
      },
      {
        "rules": {
          "type": "url",
          "urls": [
            "https://github.com",
            "https://docs.python.org/3/"
          ]
        },
        "type": "rule"
      }
    ],
    "func": [
      "check_list",
      "is_expected_tabs"
    ],
    "postconfig": [
      {
        "parameters": {
          "command": [
            "wmctrl",
            "-lx"
          ],
          "stdout": "wmctrl.out"
        },
        "type": "execute"
      }
    ],
    "result": [
      {
        "path": "wmctrl.out",
        "type": "cache_file"
      },
      {
        "type": "open_tabs_info"
      }
    ]
  },
  "fixed_ip": false,
  "id": "48c46dc7-fe04-4505-ade7-723cba1aa6f6",
  "instruction": "Help me to automatically set up my work space. To be specific, open project directory of OSWorld in terminal and file manager, then open github homepage and the online document of Python in chrome browser.",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "chrome",
    "os"
  ],
  "snapshot": "chrome",
  "source": "authors",
  "trajectory": "trajectories/48c46dc7-fe04-4505-ade7-723cba1aa6f6"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `9e1d4fb169315ddd8c33a146b526acbf3dcec3fba9ba2985dcee9dceb1810a01`

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
      "end_line": 7,
      "excerpt_sha256": "7b2ddb8a2e64c6166feedaf30ee50ac62165fe149fdd8b0d7b777ebee21ca34d",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 7,
      "symbol": "import:time",
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
      "end_line": 13,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 13,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 16,
      "excerpt_sha256": "81316fc5e4b535785ec5c865813e5fae93bcdf8a8139449c9c48916b401607c7",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 16,
      "symbol": "import:TimeoutError",
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
      "end_line": 980,
      "excerpt_sha256": "73562a3e151ba6d1cf2882de5fc1078f22d7e3cc065be83bc7b9c34979c080c6",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 897,
      "symbol": "get_open_tabs_info",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
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
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "891d1d796c0923f73a03f7cf751549361c79949540451e07b3397794cb96acb4",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 9,
      "symbol": "import:Any",
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
      "end_line": 152,
      "excerpt_sha256": "6ed9636aad516434faa873bc852982957aeb679b4343fda5e9c6551c63a69ae3",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 132,
      "symbol": "is_expected_tabs",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 9,
      "symbol": "import:re",
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
      "end_line": 178,
      "excerpt_sha256": "d7166758168f506f55b2b8eb558b3ebfeb2be3221e3aaee02b952a051e3d14f3",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 151,
      "symbol": "check_list",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
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
      "end_line": 13,
      "excerpt_sha256": "4259aa374855844cda33160382e5c0ea66167b8a69b5b798a1a10de4f8d854c1",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 13,
      "symbol": "import:ParseResult",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 32,
      "excerpt_sha256": "f42b752f1d80be324d711ecf8206eeafb2177d1d54ac2b7832146c632e1ad1cb",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 32,
      "symbol": "import:tldextract",
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
      "end_line": 782,
      "excerpt_sha256": "b4ecdd6e4b0e7ceed1f63e75e2f179f3a39fd65ed603b80843643532bbbd72cf",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 770,
      "symbol": "are_lists_equal",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    },
    {
      "end_line": 842,
      "excerpt_sha256": "521e4b4fe788f1486c1026328061ce096fc1ed3cd9a66c7d414692907847a0b4",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 785,
      "symbol": "compare_urls",
      "upstream_path": "desktop_env/evaluators/metrics/utils.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected[0]",
      "config_sha256": "b9d8b327803cfefb2313b032ed6ed46e9c4ee071ba05a41dd7447443b136834d",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    },
    {
      "config_path": "evaluator.expected[1]",
      "config_sha256": "3d614318cd438206739c907b96d9c129bf9ee5c4766d69959ddaeffa36186921",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "e0c88410b298251f02a7373afeb2430eb6b6958009fd984dea426f49463dfd7d",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": true,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_list",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7"
    },
    {
      "name": "is_expected_tabs",
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
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
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
      "config_path": "evaluator.result[0]",
      "config_sha256": "dc2a2b01db2090180553b7ebfd2195dbb3c273f4ce1cc9e808cc1e16fb68ef81",
      "packet_path": "official/desktop_env/evaluators/getters/file.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/file.py",
      "source_sha256": "d18c8992c426b341c1f8625affbb7446d1be4af79862796cded9c34c7b9f6d1f",
      "symbol": "get_cache_file",
      "type": "cache_file"
    },
    {
      "config_path": "evaluator.result[1]",
      "config_sha256": "3696aade0d2c7a4b592efaa3dfeefaa1a6d84a01b170045ca8732b66f51c00ad",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_open_tabs_info",
      "type": "open_tabs_info"
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
  "task_id": "48c46dc7-fe04-4505-ade7-723cba1aa6f6"
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

### `import:time` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L7-L7`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `7b2ddb8a2e64c6166feedaf30ee50ac62165fe149fdd8b0d7b777ebee21ca34d`

```python
import time
```

### `import:Dict` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L9-L9`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `2ee31f90a04b45447df37745a3d1016650eab823bd86b4f0a04836df727e506a`

```python
from typing import Dict, Any, List
```

### `import:requests` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L13-L13`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `import:TimeoutError` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L16-L16`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `81316fc5e4b535785ec5c865813e5fae93bcdf8a8139449c9c48916b401607c7`

```python
from playwright.sync_api import sync_playwright, expect, TimeoutError
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

### `get_open_tabs_info` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L897-L980`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `73562a3e151ba6d1cf2882de5fc1078f22d7e3cc065be83bc7b9c34979c080c6`

```python
def get_open_tabs_info(env, config: Dict[str, str]):
    host = env.vm_ip
    port = env.chromium_port  # fixme: this port is hard-coded, need to be changed from config file
    server_port = env.server_port

    remote_debugging_url = f"http://{host}:{port}"

    # Configuration for retry and timeout
    max_retries = 2
    timeout_ms = 30000  # 30 seconds for tab info

    for attempt in range(max_retries):
        try:
            logger.info(f"[OPEN_TABS_INFO] Attempt {attempt + 1}/{max_retries}")

            with sync_playwright() as p:
                # connect to remote Chrome instance
                try:
                    browser = p.chromium.connect_over_cdp(remote_debugging_url)
                    logger.info(f"[OPEN_TABS_INFO] Successfully connected to existing Chrome instance")
                except Exception as e:
                    logger.warning(f"[OPEN_TABS_INFO] Failed to connect to existing Chrome instance: {e}")
                    # If the connection fails, start a new browser instance
                    if _is_arm_architecture(env):
                        # start a new browser instance if the connection fails
                        payload = json.dumps({"command": [
                            "chromium",
                            "--remote-debugging-port=1337"
                        ], "shell": False})
                    else:
                        payload = json.dumps({"command": [
                            "google-chrome",
                            "--remote-debugging-port=1337"
                        ], "shell": False})

                    headers = {"Content-Type": "application/json"}
                    requests.post(f"http://{host}:{server_port}/setup/launch", headers=headers, data=payload)
                    time.sleep(5)
                    try:
                        browser = p.chromium.connect_over_cdp(remote_debugging_url)
                        logger.info(f"[OPEN_TABS_INFO] Successfully connected to new Chrome instance")
                    except Exception as e:
                        logger.error(f"[OPEN_TABS_INFO] Failed to connect to new Chrome instance: {e}")
                        return []

                tabs_info = []
                for context in browser.contexts:
                    for page in context.pages:
                        try:
                            # Set timeout for each page
                            page.set_default_timeout(timeout_ms)

                            # Wait for the page to finish loading, this prevents the "execution context was destroyed" issue
                            page.wait_for_load_state('networkidle', timeout=timeout_ms)  # Wait for the 'load' event to complete
                            title = page.title()
                            url = page.url
                            tabs_info.append({'title': title, 'url': url})
                            logger.info(f"[OPEN_TABS_INFO] Tab info: '{title}' -> {url}")
                        except TimeoutError:
                            # If page loading times out, catch the exception and store the current information in the list
                            logger.warning(f"[OPEN_TABS_INFO] Tab load timeout for URL: {page.url}")
                            tabs_info.append({'title': 'Load timeout', 'url': page.url})
                        except Exception as e:
                            # Catch other potential exceptions that might occur while reading the page title
                            logger.error(f'[OPEN_TABS_INFO] Error reading tab info: {e}')
                            tabs_info.append({'title': 'Error encountered', 'url': page.url})

                browser.close()
                logger.info(f"[OPEN_TABS_INFO] Successfully retrieved info for {len(tabs_info)} tabs")
                return tabs_info

        except Exception as e:
            logger.error(f"[OPEN_TABS_INFO] Attempt {attempt + 1} failed: {str(e)}")
            logger.error(f"[OPEN_TABS_INFO] Exception type: {type(e).__name__}")

            if attempt < max_retries - 1:
                logger.info(f"[OPEN_TABS_INFO] Retrying in 3 seconds...")
                time.sleep(3)
            else:
                logger.error(f"[OPEN_TABS_INFO] All {max_retries} attempts failed. Returning empty list.")
                return []

    # This should never be reached, but just in case
    return []
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

### `import:logging` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L1-L1`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Any` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L9-L9`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `891d1d796c0923f73a03f7cf751549361c79949540451e07b3397794cb96acb4`

```python
from typing import Any, Dict, List, Union
```

### `logger` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L16-L16`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c30dca9648074311179d05d653b45dc7d88ae311b6544a016bbe93428eef8d8c`

```python
logger = logging.getLogger("desktopenv.metrics.chrome")
```

### `is_expected_tabs` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L132-L152`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `6ed9636aad516434faa873bc852982957aeb679b4343fda5e9c6551c63a69ae3`

```python
def is_expected_tabs(open_tabs: List[Dict[str, str]], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected tabs are open in Chrome.
    """
    if not open_tabs:
        return 0.

    match_type = rule['type']

    if match_type == "url":
        expected_urls = rule['urls']
        actual_urls = [tab['url'] for tab in open_tabs]
        if not are_lists_equal(expected_urls, actual_urls, compare_urls):
            logger.error("list not match")
            logger.error(expected_urls)
            logger.error(actual_urls)
            return 0
        return 1 if are_lists_equal(expected_urls, actual_urls, compare_urls) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0
```

### `import:re` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L9-L9`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L13-L13`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `f1e514bded8115f262f0549707ab0fa7cb8c30ae5335a859a177949157577897`

```python
from typing import Dict, List, Pattern
```

### `check_list` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L151-L178`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `d7166758168f506f55b2b8eb558b3ebfeb2be3221e3aaee02b952a051e3d14f3`

```python
def check_list(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Args:
        result (str): path to list file
        rules (Dict[str, List[str]]): dict like
          {
            "expect": list of str as regexes
            "unexpect": list of str as regexes
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    expect_patterns: List[Pattern[str]] = [re.compile(ptt) for ptt in rules.get("expect", [])]
    unexpect_patterns: List[Pattern[str]] = [re.compile(ptt) for ptt in rules.get("unexpect", [])]

    expect_metrics = [False] * len(expect_patterns)
    unexpect_metric = True
    with open(result) as f:
        for l in f:
            for i, r in enumerate(expect_patterns):
                expect_metrics[i] = expect_metrics[i] or (r.search(l) is not None)
            unexpect_metric = unexpect_metric and all(r.search(l) is None for r in unexpect_patterns)
    return float(all(expect_metrics) and unexpect_metric)
```

### `import:logging` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L5-L5`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:re` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L8-L8`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `import:ParseResult` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L13-L13`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `4259aa374855844cda33160382e5c0ea66167b8a69b5b798a1a10de4f8d854c1`

```python
from urllib.parse import urlparse, urlunparse, ParseResult
```

### `import:tldextract` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L32-L32`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `f42b752f1d80be324d711ecf8206eeafb2177d1d54ac2b7832146c632e1ad1cb`

```python
import tldextract
```

### `logger` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L36-L36`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `418d8a52292fe11a53f43945488dfba58622f63f293295b81d45fb479930b805`

```python
logger = logging.getLogger("desktopenv.metrics.utils")
```

### `are_lists_equal` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L770-L782`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `b4ecdd6e4b0e7ceed1f63e75e2f179f3a39fd65ed603b80843643532bbbd72cf`

```python
def are_lists_equal(list1, list2, comparison_func):
    # First check if both lists have the same length
    if len(list1) != len(list2):
        return False

    # Now make sure each element in one list has an equal element in the other list
    for item1 in list1:
        # Use the supplied function to test for an equal item
        if not any(comparison_func(item1, item2) for item2 in list2):
            return False

    # If all items match, the lists are equal
    return True
```

### `compare_urls` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L785-L842`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `521e4b4fe788f1486c1026328061ce096fc1ed3cd9a66c7d414692907847a0b4`

```python
def compare_urls(url1, url2, full=True):
    if url1 is None or url2 is None:
        return url1 == url2
    
    logger.info(f"compare_urls. url1: {url1}; url2: {url2}")

    def parse_with_default_scheme(url):
        """
        Ensure the URL has a scheme. If not, prepend 'http://'
        so it parses as host + path instead of just a path.
        """
        # Regex to check if URL has scheme like 'http://', 'https://', etc.
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', url):
            url = f"http://{url}"
        return urlparse(url)

    def normalize_url(url):
        # Parse the URL; if no scheme is present, assume 'http'
        parsed_url = parse_with_default_scheme(url)
        scheme = parsed_url.scheme.lower()

        # Extract the domain parts using tldextract
        extracted = tldextract.extract(parsed_url.netloc.lower())
        # e.g., extracted = TLDExtractResult(subdomain='www', domain='airbnb', suffix='com.sg')
        
        # Drop 'www' if it's the only subdomain
        subdomain = extracted.subdomain
        if subdomain == 'www':
            subdomain = ''

        # Instead of using the suffix (e.g., 'com', 'com.sg'), ignore it completely
        # so that both 'airbnb.com' and 'airbnb.com.sg' become just 'airbnb' or 'www.airbnb'
        if subdomain:
            normalized_netloc = f"{subdomain}.{extracted.domain}"
        else:
            normalized_netloc = extracted.domain

        # Handle trailing slash in the path
        normalized_path = parsed_url.path if parsed_url.path != '/' else ''

        # Reassemble the URL with the normalized components
        normalized_parsed_url = ParseResult(
            scheme=scheme.lower(),
            netloc=normalized_netloc,
            path=normalized_path,
            params=parsed_url.params if full else '',       # Keep the params
            query=parsed_url.query if full else '',         # Keep the query string
            fragment=parsed_url.fragment if full else '',   # Keep the fragment
        )
        return urlunparse(normalized_parsed_url)

    logger.info(f"After normalization. url1: {normalize_url(url1)}; url2: {normalize_url(url2)}")
    # Normalize both URLs
    norm_url1 = normalize_url(url1)
    norm_url2 = normalize_url(url2)

    # Compare the normalized URLs
    return norm_url1 == norm_url2
```
