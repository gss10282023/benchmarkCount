# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9`
- task_id: `93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `chrome`
- snapshot: `chrome`
- related apps: `chrome`
- official instruction: Could you assist me in turning off the dark mode feature in Google Chrome? I've noticed that while dark mode is great for reducing glare, it actually makes it more challenging for me to read text clearly, especially with my astigmatism.
- evaluator functions: `match_in_list, is_expected_url_pattern_match`
- evaluator conjunction: `and`
- evaluator result getter types: `chrome_appearance_mode_ui, active_url_from_accessTree`
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
- `official/desktop_env/evaluators/metrics/general.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9.json`

Source SHA-256: `8177dd721fdbc721199fe1f30e12fc27f80d5d08e923271fe6803ba68e0a94f7`

```json
{
  "config": [
    {
      "parameters": {
        "command": "mkdir -p /home/user/.config/google-chrome/Default && if [ ! -f /home/user/.config/google-chrome/Default/Preferences ]; then echo '{}' > /home/user/.config/google-chrome/Default/Preferences; fi && python3 -c \"import json; p='/home/user/.config/google-chrome/Default/Preferences'; d=json.load(open(p)); d.setdefault('browser', {}).setdefault('theme', {})['color_scheme'] = 2; d['browser']['theme']['color_scheme2'] = 2; json.dump(d, open(p, 'w'))\"",
        "shell": true
      },
      "type": "execute"
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
        "window_name": "Google Chrome"
      },
      "type": "activate_window"
    }
  ],
  "evaluator": {
    "expected": [
      {
        "rules": {
          "expected": [
            "light",
            "system"
          ]
        },
        "type": "rule"
      },
      {
        "rules": {
          "expected": [
            "^chrome://settings/appearance/?$"
          ]
        },
        "type": "rule"
      }
    ],
    "func": [
      "match_in_list",
      "is_expected_url_pattern_match"
    ],
    "postconfig": [
      {
        "parameters": {
          "seconds": 1
        },
        "type": "sleep"
      }
    ],
    "result": [
      {
        "type": "chrome_appearance_mode_ui"
      },
      {
        "goto_prefix": "",
        "type": "active_url_from_accessTree"
      }
    ]
  },
  "fixed_ip": false,
  "id": "93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9",
  "instruction": "Could you assist me in turning off the dark mode feature in Google Chrome? I've noticed that while dark mode is great for reducing glare, it actually makes it more challenging for me to read text clearly, especially with my astigmatism.",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "chrome"
  ],
  "snapshot": "chrome",
  "source": "https://superuser.com/questions/1417973/how-to-disable-google-chrome-dark-mode",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `cd9a748637f9ccfa6cc7842f766b93979c5c1127cba775b89b14746fd6d9e2ee`

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
      "end_line": 5,
      "excerpt_sha256": "a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 5,
      "symbol": "import:re",
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
      "end_line": 12,
      "excerpt_sha256": "51cd3847a7ab1e2566005cbe43c924d57d0c319ccc70e8ba7be28a7d5f0ce736",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 12,
      "symbol": "import:lxml",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 14,
      "excerpt_sha256": "92c0930a2528d6459ec70a0190b9e14323b80a2f08cf794a0bb1850234365c6c",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 14,
      "symbol": "import:CSSSelector",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 16,
      "excerpt_sha256": "81316fc5e4b535785ec5c865813e5fae93bcdf8a8139449c9c48916b401607c7",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 16,
      "symbol": "import:sync_playwright",
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
      "end_line": 34,
      "excerpt_sha256": "b46d91910b81b2703d89bee3fb03baa4dc3dd238b94c289ea43b9d2113558dae",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 25,
      "symbol": "_accessibility_ns_map",
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
      "end_line": 596,
      "excerpt_sha256": "abaf535a2b9e0a1deb6e5d451fecee4e521ca6c52bfbe6b24567f6d1e80b2990",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 471,
      "symbol": "get_chrome_color_scheme",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 715,
      "excerpt_sha256": "34f8457a01c01876b1b0d99670c1560c8334caaa739c92ace354212298e050dd",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 599,
      "symbol": "get_chrome_appearance_mode_ui",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 987,
      "excerpt_sha256": "a96fa006f81a0ca92d35f6ceb722db998e711be83fa399649601e7fe09d8c819",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 983,
      "symbol": "_access_tree_element_is_focused",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 998,
      "excerpt_sha256": "139e1fadb4f8f9cba8987cb6306daaac394edb812a9c17e0506d8d7804775521",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 990,
      "symbol": "_normalize_access_tree_url_text",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 1076,
      "excerpt_sha256": "a36d0a4f668bc01442ced9bc882f368cba43378f317d19907e4dc69d4b6db163",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 1001,
      "symbol": "get_active_url_from_accessTree",
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
      "end_line": 3,
      "excerpt_sha256": "a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 3,
      "symbol": "import:re",
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
      "end_line": 100,
      "excerpt_sha256": "8076bea5ea77bc5fae0f0157a6eaf16a2bd6791ef2d469af9dd183315c573323",
      "packet_path": "official/desktop_env/evaluators/metrics/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py",
      "source_sha256": "6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf",
      "start_line": 71,
      "symbol": "is_expected_url_pattern_match",
      "upstream_path": "desktop_env/evaluators/metrics/chrome.py"
    },
    {
      "end_line": 57,
      "excerpt_sha256": "8701d5f029dabbe222fe51f82ce9f9b0eddaee8d2f156a0313b9a3a8d0ee4f90",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 50,
      "symbol": "match_in_list",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected[0]",
      "config_sha256": "4cca544a94994910574640b674ceb2ec3fabb16866943f4b4fca0e7b7396dc38",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    },
    {
      "config_path": "evaluator.expected[1]",
      "config_sha256": "ea4642c4161c9d28057158e4db59af081a755ff62107640f552d56d1f8a85025",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "1d52f928686bf6a64c52ea0ac36651a09ca77daf23d66dbef0b2ea125710f7d1",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": true,
  "metric_options": null,
  "metrics": [
    {
      "name": "match_in_list",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7"
    },
    {
      "name": "is_expected_url_pattern_match",
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
      "config_sha256": "f1b8283ccb554304eb01f75e38da2d064d8a56fb47ee4083f71c9c4f36d812ec",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_chrome_appearance_mode_ui",
      "type": "chrome_appearance_mode_ui"
    },
    {
      "config_path": "evaluator.result[1]",
      "config_sha256": "8862977db9a8b36a9b7409949118526f46ef2d03e4bbd14113c9699034e84ac5",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 1,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_active_url_from_accessTree",
      "type": "active_url_from_accessTree"
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
  "task_id": "93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9"
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

### `import:re` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L5-L5`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
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

### `import:lxml` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L12-L12`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `51cd3847a7ab1e2566005cbe43c924d57d0c319ccc70e8ba7be28a7d5f0ce736`

```python
import lxml.etree
```

### `import:CSSSelector` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L14-L14`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `92c0930a2528d6459ec70a0190b9e14323b80a2f08cf794a0bb1850234365c6c`

```python
from lxml.cssselect import CSSSelector
```

### `import:sync_playwright` from `official/desktop_env/evaluators/getters/chrome.py`

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

### `_accessibility_ns_map` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L25-L34`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `b46d91910b81b2703d89bee3fb03baa4dc3dd238b94c289ea43b9d2113558dae`

```python
_accessibility_ns_map = {
    "st": "uri:deskat:state.at-spi.gnome.org",
    "attr": "uri:deskat:attributes.at-spi.gnome.org",
    "cp": "uri:deskat:component.at-spi.gnome.org",
    "doc": "uri:deskat:document.at-spi.gnome.org",
    "docattr": "uri:deskat:attributes.document.at-spi.gnome.org",
    "txt": "uri:deskat:text.at-spi.gnome.org",
    "val": "uri:deskat:value.at-spi.gnome.org",
    "act": "uri:deskat:action.at-spi.gnome.org"
}
```

### `logger` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L36-L36`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `be5e1ed9a973c2d1f914d536ba1bc122b1b749e03327b4de21b87efc4beee316`

```python
logger = logging.getLogger("desktopenv.getters.chrome")
```

### `get_chrome_color_scheme` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L471-L596`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `abaf535a2b9e0a1deb6e5d451fecee4e521ca6c52bfbe6b24567f6d1e80b2990`

```python
def get_chrome_color_scheme(env, config: Dict[str, str]):
    """
    Get Chrome browser color scheme preference.
    Returns one of: "system", "light", "dark".
    """
    def _normalize_color_scheme(raw_value):
        if isinstance(raw_value, str):
            normalized = raw_value.strip().lower()
            if normalized in {"system", "default", "0"}:
                return "system"
            if normalized in {"light", "1"}:
                return "light"
            if normalized in {"dark", "2"}:
                return "dark"
            return None
        if isinstance(raw_value, (int, float)):
            mapping = {0: "system", 1: "light", 2: "dark"}
            return mapping.get(int(raw_value), None)
        return None

    def _extract_mode_from_preferences(data):
        theme_data = data.get('browser', {}).get('theme', {})
        # Newer Chrome writes color_scheme2; older versions may still use color_scheme.
        raw_value = theme_data.get('color_scheme2', theme_data.get('color_scheme', None))
        mode = _normalize_color_scheme(raw_value)
        # Fallback for Linux builds where appearance updates may be reflected through
        # extensions.theme.system_theme while color_scheme remains stale.
        system_theme_flag = data.get('extensions', {}).get('theme', {}).get('system_theme', None)
        if system_theme_flag in [0, "0", False]:
            return "light"
        return mode if mode else "system"

    os_type = env.vm_platform
    try:
        candidate_paths = []
        if os_type == 'Windows':
            preference_file_path = env.controller.execute_python_command("""import os; print(os.path.join(os.getenv('LOCALAPPDATA'),
                                                    'Google\\Chrome\\User Data\\Default\\Preferences'))""")[
                'output'].strip()
            candidate_paths = [preference_file_path]
        elif os_type == 'Darwin':
            preference_file_path = env.controller.execute_python_command(
                "import os; print(os.path.join(os.getenv('HOME'), 'Library/Application Support/Google/Chrome/Default/Preferences'))")[
                'output'].strip()
            candidate_paths = [preference_file_path]
        elif os_type == 'Linux':
            if _is_arm_architecture(env):
                preference_file_path = env.controller.execute_python_command(
                    "import os; print(os.path.join(os.getenv('HOME'), 'snap/chromium/common/chromium/Default/Preferences'))")[
                    'output'].strip()
                candidate_paths = [preference_file_path]
            else:
                # Enumerate profile preference files and rank by last modified time.
                path_probe = r"""
import glob, json, os
roots = [
    os.path.expanduser('~/.config/google-chrome'),
    '/home/user/.config/google-chrome',
    '/home/ubuntu/.config/google-chrome',
]
seen = set()
results = []
for root in roots:
    if not os.path.isdir(root):
        continue
    patterns = [
        os.path.join(root, 'Default', 'Preferences'),
        os.path.join(root, 'Guest Profile', 'Preferences'),
        os.path.join(root, 'Profile *', 'Preferences'),
    ]
    for pattern in patterns:
        for p in glob.glob(pattern):
            if p in seen or not os.path.isfile(p):
                continue
            seen.add(p)
            try:
                mtime = os.path.getmtime(p)
            except Exception:
                mtime = 0
            results.append({'path': p, 'mtime': mtime})
print(json.dumps(results))
"""
                probe_output = env.controller.execute_python_command(path_probe).get('output', '').strip()
                probed = json.loads(probe_output) if probe_output else []
                probed.sort(key=lambda x: x.get('mtime', 0), reverse=True)
                candidate_paths = [item.get('path') for item in probed if item.get('path')]
                if not candidate_paths:
                    fallback = env.controller.execute_python_command(
                        "import os; print(os.path.join(os.getenv('HOME'), '.config/google-chrome/Default/Preferences'))")[
                        'output'].strip()
                    candidate_paths = [fallback]
        else:
            raise Exception('Unsupported operating system')

        # Chrome may flush Preferences asynchronously right after the UI toggle.
        # Poll briefly to avoid evaluating stale on-disk values.
        final_mode = "system"
        for _ in range(5):
            best_mode = None
            for preference_file_path in candidate_paths:
                try:
                    content = env.controller.get_file(preference_file_path)
                    if not content:
                        continue
                    data = json.loads(content)
                    mode = _extract_mode_from_preferences(data)
                    # Prefer explicit user selection over "system".
                    if mode in {"light", "dark"}:
                        best_mode = mode
                        break
                    if best_mode is None:
                        best_mode = mode
                except Exception:
                    continue

            if best_mode is not None:
                final_mode = best_mode
                # If it already became light, return immediately.
                if best_mode == "light":
                    return "light"
            time.sleep(1)

        return final_mode
    except Exception as e:
        logger.error(f"Error: {e}")
        return "system"
```

### `get_chrome_appearance_mode_ui` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L599-L715`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `34f8457a01c01876b1b0d99670c1560c8334caaa739c92ace354212298e050dd`

```python
def get_chrome_appearance_mode_ui(env, config: Dict[str, str]):
    """
    Read Chrome appearance mode from the settings UI (chrome://settings/appearance).
    Returns one of: "light", "dark", "system".
    Falls back to get_chrome_color_scheme if UI probing fails.
    """
    host = env.vm_ip
    port = env.chromium_port
    remote_debugging_url = f"http://{host}:{port}"

    js_probe = r"""
() => {
  const lower = (s) => String(s || '').toLowerCase();
  const allowedPrefPaths = new Set([
    'prefs.browser.theme.color_scheme',
    'prefs.browser.theme.color_scheme2',
    'prefs.extensions.theme.system_theme',
  ]);

  const inferFromText = (s) => {
    const t = lower(s);
    if (t.includes('light')) return 'light';
    if (t.includes('dark')) return 'dark';
    if (t.includes('device') || t.includes('system') || t.includes('default')) return 'system';
    return null;
  };

  const collectShadowRoots = (root, acc) => {
    if (!root) return;
    const all = root.querySelectorAll('*');
    for (const el of all) {
      if (el.shadowRoot) {
        acc.push(el.shadowRoot);
        collectShadowRoots(el.shadowRoot, acc);
      }
    }
  };

  const modes = [];

  // 1) Try settings-ui prefs recursively (WebUI internal state)
  try {
    const ui = document.querySelector('settings-ui');
    const prefs = ui && ui.prefs ? ui.prefs : null;
    const visited = new Set();
    const walk = (obj, path) => {
      if (!obj || typeof obj !== 'object') return;
      if (visited.has(obj)) return;
      visited.add(obj);

      // Common pref leaf shapes: {key, value} or nested objects.
      if (Object.prototype.hasOwnProperty.call(obj, 'value')) {
        const v = obj.value;
        const p = lower(path);
        if (allowedPrefPaths.has(p)) {
          if (p.endsWith('extensions.theme.system_theme')) {
            if (v === 0 || v === '0' || v === false) modes.push('light');
            if (v === 1 || v === '1' || v === true) modes.push('dark');
          } else {
            if (v === 1 || v === '1' || lower(v) === 'light') modes.push('light');
            if (v === 2 || v === '2' || lower(v) === 'dark') modes.push('dark');
            if (v === 0 || v === '0' || lower(v) === 'system' || lower(v) === 'default' || lower(v) === 'device') modes.push('system');
          }
        }
      }

      for (const [k, v] of Object.entries(obj)) {
        walk(v, path ? `${path}.${k}` : k);
      }
    };
    walk(prefs, 'prefs');
  } catch (e) {}

  // 2) Scan selected/checked controls through shadow DOM text.
  try {
    const roots = [document];
    collectShadowRoots(document, roots);
    const candidates = [];
    for (const r of roots) {
      for (const el of r.querySelectorAll('[selected],[checked],[aria-checked="true"],option:checked')) {
        const txt = (el.innerText || el.textContent || '').trim();
        if (txt) candidates.push(txt);
      }
    }
    for (const t of candidates) {
      const m = inferFromText(t);
      if (m) modes.push(m);
    }
  } catch (e) {}

  // Priority: explicit light/dark from UI; otherwise system.
  if (modes.includes('light')) return 'light';
  if (modes.includes('dark')) return 'dark';
  if (modes.includes('system')) return 'system';
  return null;
}
"""

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(remote_debugging_url)
            except Exception:
                # Fallback to file-based mode if Chrome CDP is unavailable.
                return get_chrome_color_scheme(env, config)

            page = browser.contexts[0].new_page()
            page.goto("chrome://settings/appearance", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)
            mode = page.evaluate(js_probe)
            browser.close()

            if mode in {"light", "dark", "system"}:
                return mode
            return get_chrome_color_scheme(env, config)
    except Exception:
        return get_chrome_color_scheme(env, config)
```

### `_access_tree_element_is_focused` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L983-L987`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `a96fa006f81a0ca92d35f6ceb722db998e711be83fa399649601e7fe09d8c819`

```python
def _access_tree_element_is_focused(element) -> bool:
    return (
        element.get("focused") == "true"
        or element.get(f"{{{_accessibility_ns_map['st']}}}focused") == "true"
    )
```

### `_normalize_access_tree_url_text` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L990-L998`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `139e1fadb4f8f9cba8987cb6306daaac394edb812a9c17e0506d8d7804775521`

```python
def _normalize_access_tree_url_text(raw_text: str, goto_prefix: str) -> str:
    text = raw_text.strip()
    # If the text already includes a scheme (e.g. "https://..."), don't prepend.
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*:", text):
        return text
    # Avoid duplicating "www." when the prefix already ends with it.
    if goto_prefix.endswith("www.") and text.lower().startswith("www."):
        text = text[4:]
    return f"{goto_prefix}{text}"
```

### `get_active_url_from_accessTree` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L1001-L1076`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `a36d0a4f668bc01442ced9bc882f368cba43378f317d19907e4dc69d4b6db163`

```python
def get_active_url_from_accessTree(env, config):
    """
        Playwright cannot get the url of active tab directly,
        so we need to use accessibility tree to get the active tab info.
        This function is used to get the active tab url from the accessibility tree.
        config:
            Dict[str, str]{
                # we no longer need to specify the xpath or selectors, since we will use defalut value
                # 'xpath':
                #     the same as in metrics.general.accessibility_tree.
                # 'selectors':
                #     the same as in metrics.general.accessibility_tree.
                'goto_prefix':
                    the prefix you want to add to the beginning of the url to be opened, default is "https://",
                    (the url we get from accTree does not have prefix)
                ...(other keys, not used in this function)
        }
        Return
            url: str
    """
    # Ensure the controller and its method are accessible and return a valid result
    if hasattr(env, 'controller') and callable(getattr(env.controller, 'get_accessibility_tree', None)):
        accessibility_tree = env.controller.get_accessibility_tree()
        if accessibility_tree is None:
            print("Failed to get the accessibility tree.")
            return None
    else:
        print("Controller or method 'get_accessibility_tree' not found.")
        return None

    logger.debug("AT@eval: %s", accessibility_tree)

    at = None
    try:
        at = lxml.etree.fromstring(accessibility_tree)
    except ValueError as e:
        logger.error(f"Error parsing accessibility tree: {e}")
        return None

    # Determine the correct selector based on system architecture
    selector = None
    is_arm = _is_arm_architecture(env)
    print(f"VM architecture: {env.vm_machine} (arm={is_arm})")

    if is_arm:
        selector_string = "application[name=Chromium] entry[name=Address\\ and\\ search\\ bar]"
    else:
        selector_string = "application[name=Google\\ Chrome] entry[name=Address\\ and\\ search\\ bar]"

    try:
        selector = CSSSelector(selector_string, namespaces=_accessibility_ns_map)
    except Exception as e:
        logger.error(f"Failed to parse the selector for active tab URL: {e}")
        return None

    elements = selector(at) if selector else []
    elements_with_text = [element for element in elements if element.text]
    if not elements_with_text:
        print("No elements found.")
        return None

    # Use a default prefix if 'goto_prefix' is not specified in the config
    goto_prefix = config.get("goto_prefix", "https://") or ""

    # There can be multiple address-bar entries (e.g. background tabs/windows);
    # prefer the focused one, which corresponds to the active tab. Fall back to
    # the last entry that has text. (The original code checked elements[-1] but
    # then returned elements[0], which could read the wrong tab's URL.)
    focused_elements = [
        element for element in elements_with_text if _access_tree_element_is_focused(element)
    ]
    active_element = focused_elements[-1] if focused_elements else elements_with_text[-1]

    active_tab_url = _normalize_access_tree_url_text(active_element.text, goto_prefix)
    print(f"Active tab url now: {active_tab_url}")
    return active_tab_url
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

### `import:re` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L3-L3`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `logger` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L16-L16`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `c30dca9648074311179d05d653b45dc7d88ae311b6544a016bbe93428eef8d8c`

```python
logger = logging.getLogger("desktopenv.metrics.chrome")
```

### `is_expected_url_pattern_match` from `official/desktop_env/evaluators/metrics/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/chrome.py#L71-L100`

Full source SHA-256: `6bc66f2229b5c556666f2597007d937af04cb80af796e13dcf0bb35a1fce5bdf`

Exact excerpt SHA-256: `8076bea5ea77bc5fae0f0157a6eaf16a2bd6791ef2d469af9dd183315c573323`

```python
def is_expected_url_pattern_match(result, rules) -> float:
    """
    This function is used to search the expected pattern in the url using regex.
    result is the return value of function "activte_tab_info" or return value of function "get_active_url_from_accessTree"
    """
    if not result:
        return 0.

    # Extract URL from result parameter - result can be either a string URL or a dict with 'url' field
    if isinstance(result, str):
        result_url = result
        logger.info("result url: {}".format(result_url))
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
        logger.info("result url: {}".format(result_url))
    else:
        logger.error(f"Invalid result format: {type(result)}, expected string URL or dict with 'url' field")
        return 0.

    logger.info(f"Result URL to match: {result_url}")

    # expect_regex = re.compile(rules["expected"])
    patterns = rules["expected"]
    logger.info("expected_regex: {}".format(patterns))
    for pattern in patterns:
        match = re.search(pattern, result_url)
        logger.info("match: {}".format(match))
        if not match:
            return 0.
    return 1.
```

### `match_in_list` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L50-L57`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `8701d5f029dabbe222fe51f82ce9f9b0eddaee8d2f156a0313b9a3a8d0ee4f90`

```python
def match_in_list(result, rules) -> float:
    expect = rules["expected"]
    print(result, expect)

    if result in expect:
        return 1.
    else:
        return 0.
```
