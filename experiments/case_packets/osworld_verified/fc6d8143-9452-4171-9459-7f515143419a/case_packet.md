# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `fc6d8143-9452-4171-9459-7f515143419a`
- task_id: `fc6d8143-9452-4171-9459-7f515143419a`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `chrome`
- snapshot: `chrome`
- related apps: `chrome`
- official instruction: Find flights from New York–Kennedy Airport to Chicago O'Hare Airport for tomorrow.
- evaluator functions: `check_direct_json_object`
- evaluator conjunction: `and`
- evaluator result getter types: `active_tab_html_parse`
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
- `official/desktop_env/evaluators/metrics/general.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/chrome/fc6d8143-9452-4171-9459-7f515143419a.json`

Source SHA-256: `346a2a161e3301dbcb24274cb9b5375d2309841280104c243f8517791a354f27`

```json
{
  "config": [
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
        "urls_to_open": [
          "https://www.delta.com/"
        ]
      },
      "type": "chrome_open_tabs"
    },
    {
      "parameters": {
        "window_name": "Google Chrome"
      },
      "type": "activate_window"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "expected": {
          "end": "ORD",
          "start": "JFK",
          "time": "{DoW}, {Month} {Day0D}, {Year}"
        },
        "relativeTime": {
          "from": "tomorrow"
        }
      },
      "type": "rule_relativeTime"
    },
    "func": "check_direct_json_object",
    "result": {
      "category": "class",
      "class_multiObject_child": {
        "mach-flight-context-info__wrapper__info--separator": {
          "0": "start",
          "1": "end"
        }
      },
      "class_singleObject": {
        "mach-flight-context-info__wrapper--date": "time"
      },
      "goto_prefix": "https://www.",
      "type": "active_tab_html_parse"
    }
  },
  "fixed_ip": false,
  "id": "fc6d8143-9452-4171-9459-7f515143419a",
  "instruction": "Find flights from New York–Kennedy Airport to Chicago O'Hare Airport for tomorrow.",
  "possibility_of_env_change": "low",
  "proxy": true,
  "related_apps": [
    "chrome"
  ],
  "snapshot": "chrome",
  "source": "test_task_0",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `5ee89781fab24f4e2910384df951cd0ff2c4d8b62f8137e679a215e5cd6835bc`

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
      "end_line": 8,
      "excerpt_sha256": "e6320a88da508c6dbd1fe2379c347eeeb128620230ade88fe20aad68d8f61b02",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 8,
      "symbol": "import:unquote",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 9,
      "excerpt_sha256": "2ee31f90a04b45447df37745a3d1016650eab823bd86b4f0a04836df727e506a",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 9,
      "symbol": "import:Any",
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
      "end_line": 2329,
      "excerpt_sha256": "1f877be0ce9944946967bad37bd5c5c8fd499f42a4a85898bffec6c4ef5c5f12",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 1869,
      "symbol": "get_active_tab_html_parse",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
    },
    {
      "end_line": 1,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 1,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
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
      "end_line": 3,
      "excerpt_sha256": "0791be90ba0eb279d5ee6cf2e800414e147b396b66c8224451c711de65a6ac4a",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 3,
      "symbol": "import:datetime",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "6acb22f8ef1c4e1d7176d96b2c6e5e3ab4fb5856c6e29673da4762396ad8f4c3",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 4,
      "symbol": "import:pytz",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 5,
      "symbol": "import:requests",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 7,
      "excerpt_sha256": "1666d87529b5ea68340c3bbdde21df80306cf2dd6d5d4f5d3522ea238827979a",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 7,
      "symbol": "logger",
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
      "end_line": 19,
      "excerpt_sha256": "4c187d379cc110f19049f953ca5c9ee87d8d5bbe15a84c4ef68c3c8a948cef32",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 11,
      "symbol": "day_of_week_mapping",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 34,
      "excerpt_sha256": "04ecab911f403ab9d2a8f26665341f70050ab3eac9e3b82c4f564a42ff13d3ff",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 21,
      "symbol": "month_mapping",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 49,
      "excerpt_sha256": "e939f29ea6308270790388e2430efc453ca5a56869713f11908cad719fb18676",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 36,
      "symbol": "Month_Mapping_Full",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 64,
      "excerpt_sha256": "21963ba69127d01a9d7a283f26eef6b14fc225dffba48dcd58ab2428e6e23eae",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 51,
      "symbol": "month_mapping_full",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 90,
      "excerpt_sha256": "8638e32b62657f5ddb4db093ccb9e5597c138b7c8e95f668724bf96c280dfaf1",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 66,
      "symbol": "relativeTime_to_IntDay",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 105,
      "excerpt_sha256": "d3f10d3cc394c3ccd0e850174d58d254c7a9c3a55548220f1f3660189185d2e1",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 99,
      "symbol": "_build_datetime_like",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 126,
      "excerpt_sha256": "7ef35f4fb35b8c13048fc46941de50da98cad44ae3dde107fdbcd4af034bbf86",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 108,
      "symbol": "_get_vm_now_datetime",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 430,
      "excerpt_sha256": "8ed49f4770ff7ae41e416dc00ed7a547e1c2bd487fd27175ff31b584bde66be6",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 128,
      "symbol": "get_rule_relativeTime",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 445,
      "excerpt_sha256": "6a7f27c25c09185bea01cd34be242cd10c36327674da5cb5473e979ae1983bb2",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 433,
      "symbol": "apply_rules_to_timeFormat",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 479,
      "excerpt_sha256": "6019a3a47054d7eb9657d9a974f8274fdca66970ed3c10bc59853a4fe3b31284",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 460,
      "symbol": "get_timezone_from_ip",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 498,
      "excerpt_sha256": "da92d1f2bc881141c633f2916bf4b8e9830dc3c4289020325e1a52d7ab068464",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "start_line": 481,
      "symbol": "get_timezone_from_config",
      "upstream_path": "desktop_env/evaluators/getters/misc.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 5,
      "symbol": "import:json",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 6,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 6,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 25,
      "excerpt_sha256": "76240bbce147543d0a4d62344a6d4789fcd7a13a30ab708e18535fda82238f03",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 25,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    },
    {
      "end_line": 480,
      "excerpt_sha256": "7e87793e80d1b6569305c2ba3ae087db92407aa5d4491655ba2be5d12cd2a992",
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "source_sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "start_line": 382,
      "symbol": "check_direct_json_object",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    }
  ],
  "expected_getters": [
    {
      "config_path": "evaluator.expected",
      "config_sha256": "032d20861057f2d00e77e702e50b5581d9ce8506bc60a5f39fdc527e79b2914d",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule_relativeTime",
      "type": "rule_relativeTime"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "e4fb5d90e9c10db4674eaf6979be4047d6b2b44f93b5d42ce44860ddbc974ed7",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_direct_json_object",
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
      "packet_path": "official/desktop_env/evaluators/metrics/general.py",
      "sha256": "22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py",
      "upstream_path": "desktop_env/evaluators/metrics/general.py"
    }
  ],
  "postconfig_present": false,
  "result_getters": [
    {
      "config_path": "evaluator.result",
      "config_sha256": "66996f6f588314cecde2fa150cceee2bd9b60bf32b96b5b5d45ee08caee8a56f",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_active_tab_html_parse",
      "type": "active_tab_html_parse"
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
  "task_id": "fc6d8143-9452-4171-9459-7f515143419a"
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

### `import:unquote` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L8-L8`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `e6320a88da508c6dbd1fe2379c347eeeb128620230ade88fe20aad68d8f61b02`

```python
from urllib.parse import unquote
```

### `import:Any` from `official/desktop_env/evaluators/getters/chrome.py`

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

### `import:requests` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L13-L13`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
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

### `get_active_tab_html_parse` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L1869-L2329`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `1f877be0ce9944946967bad37bd5c5c8fd499f42a4a85898bffec6c4ef5c5f12`

```python
def get_active_tab_html_parse(env, config: Dict[str, Any]):
    """
    This function is used to get the specific element's text content from the active tab's html.
    config:
        Dict[str, str]{
            # Keys used in get_active_url_from_accessTree: "xpath", "selectors"
            'category':
                choose from ["class", "label", "xpath", "input"], used to indicate how to find the element
            'labelObject':
                only exists when category is "label",
                a dict like { "labelSelector": "the key you want to store the text content of this label's ee=lement"}
            'class_singleObject':
                only exists when category is "class", a dict with keys as the class name,
                like { "class name" : "the key you want to store the text content of this element" }
            'class_multiObject':
                only exists when category is "class", used for elements with same class name.
                Two layer of dict, like
                    ( {
                        "class name": {
                            "rank in this class" : "the key you want to store the text content of this element"
                            ...
                            }
                        } )
            'xpathObject':
                only exists when category is "xpath", a dict with keys as the xpath,
                like { "full xpath" : "the key you want to store the text content of this element" }
            'inputObject':
                only exists when category is "input",
                a dict with keys as the input element's xpath, like { "full xpath" : "the key you want to store the text content of this element" }
    }
    """
    active_tab_url = get_active_url_from_accessTree(env, config)
    logger.info(f"[DEBUG] get_active_url_from_accessTree returned: {active_tab_url} (type: {type(active_tab_url)})")
    if not isinstance(active_tab_url, str):
        logger.error(f"[DEBUG] active_tab_url is not a string, got {type(active_tab_url)}: {active_tab_url}")
        return None
    host = env.vm_ip
    port = env.chromium_port  # fixme: this port is hard-coded, need to be changed from config file
    server_port = env.server_port

    remote_debugging_url = f"http://{host}:{port}"

    # DEBUG: Add logging for configuration
    logger.info(f"[DEBUG] get_active_tab_html_parse called with config: {config}")

    with sync_playwright() as p:
        # connect to remote Chrome instance
        try:
            browser = p.chromium.connect_over_cdp(remote_debugging_url)
        except Exception as e:
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
            requests.post("http://" + host + ":" + str(server_port) + "/setup" + "/launch", headers=headers, data=payload)
            time.sleep(5)
            browser = p.chromium.connect_over_cdp(remote_debugging_url)
        target_page = None
        for context in browser.contexts:
            for page in context.pages:
                try:
                    # Wait for page to be stable before checking URL
                    page.wait_for_load_state("networkidle", timeout=60000)

                    # Check if page is still valid before accessing properties
                    if page.is_closed():
                        logger.debug(f"[DEBUG] Page is closed, skipping")
                        continue

                    # the accTree and playwright can get encoding(percent-encoding) characters, we need to convert them to normal characters
                    # Normalize URLs by removing trailing slashes and decoding percent-encoding
                    def normalize_url(url):
                        return unquote(url).rstrip('/')

                    # Safely get page URL with error handling
                    try:
                        page_url = page.url
                    except Exception as url_error:
                        logger.debug(f"[DEBUG] Failed to get page URL: {url_error}")
                        continue

                    if normalize_url(page_url) == normalize_url(active_tab_url):
                        target_page = page
                        print("\33[32mtartget page url: ", target_page.url, "\33[0m")

                        # Safely get page title with error handling
                        try:
                            page_title = target_page.title()
                            print("\33[32mtartget page title: ", page_title, "\33[0m")
                        except Exception as title_error:
                            logger.debug(f"[DEBUG] Failed to get page title: {title_error}")
                            print("\33[32mtartget page title: [Unable to get title - page may be navigating]", "\33[0m")
                        break

                except Exception as page_error:
                    logger.debug(f"[DEBUG] Error processing page: {page_error}")
                    continue
        if target_page is None:
            logger.error("[DEBUG] Could not find target tab matching URL. Available tabs:")
            for context in browser.contexts:
                for page in context.pages:
                    try:
                        if not page.is_closed():
                            page_url = page.url
                            logger.error(f"[DEBUG] - Tab URL: {page_url}")
                    except Exception as e:
                        logger.error(f"[DEBUG] - Tab URL: [Unable to get URL: {e}]")
            logger.error(f"[DEBUG] Expected URL: {active_tab_url}")
            return {}

        return_json = {}

        def safely_get_text_content(selector):
            try:
                if target_page.is_closed():
                    logger.warning(f"[DEBUG] Target page is closed, cannot get text content for selector: {selector}")
                    return []
                elements = target_page.query_selector_all(selector)
                return [element.text_content().strip() for element in elements if element]
            except Exception as e:
                logger.warning(f"[DEBUG] Error getting text content for selector '{selector}': {e}")
                return []

        def safely_get_direct_text_nodes_playwright(selector):
            """
            Extract all direct text node contents under the specified selector element (excluding text inside child div, span, etc.).
            Returns a list of lists, each sublist contains the direct text nodes of one element.
            Suitable for structures like: <div>SEA<div class="aura-separator"></div>NYC</div>
            """
            try:
                if target_page.is_closed():
                    logger.warning(f"[DEBUG] Target page is closed, cannot get direct text nodes for selector: {selector}")
                    return []
                elements = target_page.query_selector_all(selector)
                results = []
                for element in elements:
                    texts = element.evaluate('''
                        (node) => Array.from(node.childNodes)
                            .filter(n => n.nodeType === Node.TEXT_NODE)
                            .map(n => n.textContent.trim())
                            .filter(Boolean)
                    ''')
                    results.append(texts)
                # Safety check: return empty list if no elements found
                return results[0] if results else []
            except Exception as e:
                logger.warning(f"[DEBUG] Error getting direct text nodes for selector '{selector}': {e}")
                return []

        def safely_get_direct_li_playwright(selector):
            try:
                if target_page.is_closed():
                    logger.warning(f"[DEBUG] Target page is closed, cannot get li elements for selector: {selector}")
                    return []
                elements = target_page.query_selector_all(selector + " li.catAllProducts")
                return [element.query_selector('span').inner_text().strip() for element in elements if element.query_selector('span')]
            except Exception as e:
                logger.warning(f"[DEBUG] Error getting li elements for selector '{selector}': {e}")
                return []

        def safely_get_only_child_text_content(selector):
            try:
                if target_page.is_closed():
                    logger.warning(f"[DEBUG] Target page is closed, cannot get child text content for selector: {selector}")
                    return []
                elements = target_page.query_selector_all(selector)
                return [element.query_selector('h3').text_content().strip() for element in elements if element.query_selector('h3')]
            except Exception as e:
                logger.warning(f"[DEBUG] Error getting child text content for selector '{selector}': {e}")
                return []

        if config["category"] == "class":
            class_multiObject = config.get("class_multiObject", {})
            for class_name, object_dict in class_multiObject.items():
                elements_texts = safely_get_text_content("." + class_name)
                for order_key, key in object_dict.items():
                    index = int(order_key)
                    if len(elements_texts) > index:
                        return_json[key] = elements_texts[index]
                    else:
                        logger.warning(f"[DEBUG] Element at index {index} not found for class '{class_name}'. Found {len(elements_texts)} elements.")
                        return_json[key] = ""  # Return empty string instead of None

            class_multiObject_child = config.get("class_multiObject_child", {})
            for class_name, object_dict in class_multiObject_child.items():
                elements_texts = safely_get_direct_text_nodes_playwright("." + class_name)
                for order_key, key in object_dict.items():
                    index = int(order_key)
                    if len(elements_texts) > index:
                        return_json[key] = elements_texts[index]
                    else:
                        logger.warning(f"[DEBUG] Child element at index {index} not found for class '{class_name}'. Found {len(elements_texts)} elements.")
                        return_json[key] = ""  # Return empty string instead of None

            class_multiObject_only_child = config.get("class_multiObject_only_child", {})
            for class_name, object_dict in class_multiObject_only_child.items():
                elements_texts = safely_get_only_child_text_content("." + class_name)
                for order_key, key in object_dict.items():
                    index = int(order_key)
                    if len(elements_texts) > index:
                        return_json[key] = elements_texts[index]
                    else:
                        logger.warning(f"[DEBUG] Only child element at index {index} not found for class '{class_name}'. Found {len(elements_texts)} elements.")
                        return_json[key] = ""  # Return empty string instead of None

            class_multiObject_search_exist = config.get("class_multiObject_search_exist", {})
            for class_name, object_list in class_multiObject_search_exist.items():
                elements_texts = safely_get_text_content("." + class_name)
                logger.info(f"[DEBUG] Found elements with class '{class_name}': {elements_texts}")
                logger.info(f"[DEBUG] Expected elements: {[obj for obj in object_list if obj != 'is_other_exist']}")

                for each_object in object_list:
                    if each_object == "is_other_exist":
                        continue
                    if each_object in elements_texts:
                        return_json[each_object] = True
                    else:
                        return_json[each_object] = False
                if "is_other_exist" in object_list:
                    extra_elements = []
                    for each_element in elements_texts:
                        if each_element not in object_list:
                            extra_elements.append(each_element)
                            return_json["is_other_exist"] = True
                    if extra_elements:
                        logger.warning(f"[DEBUG] Found unexpected elements not in expected list: {extra_elements}")
                    else:
                        logger.info(f"[DEBUG] No unexpected elements found")
                    if "is_other_exist" not in return_json.keys():
                        return_json["is_other_exist"] = False


            class_singleObject = config.get("class_singleObject", {})
            for class_name, key in class_singleObject.items():
                element_text = safely_get_text_content("." + class_name)
                logger.info(f"[DEBUG] Class '{class_name}' found {len(element_text)} elements")
                if element_text:
                    return_json[key] = element_text[0]
                    logger.info(f"[DEBUG] Class extraction for key '{key}': '{element_text[0]}'")
                else:
                    logger.warning(f"[DEBUG] No elements found for class: {class_name}")
                    return_json[key] = ""  # Return empty string instead of None

        elif config['category'] == "label":
            # Assuming get_by_label is a custom function or part of the framework being used
            labelObject = config.get("labelObject", {})
            for labelSelector, key in labelObject.items():
                try:
                    if target_page.is_closed():
                        logger.warning(f"[DEBUG] Target page is closed, cannot process label for key '{key}'")
                        return_json[key] = ""
                        continue

                    text = target_page.locator(f"text={labelSelector}").first.text_content()
                    if text:
                        text = text.strip()
                        return_json[key] = text
                    else:
                        return_json[key] = ""
                except Exception as e:
                    logger.error(f"[DEBUG] Error processing label for key '{key}': {e}")
                    return_json[key] = ""

        elif config["category"] == "xpath":
            xpathObject = config.get("xpathObject", {})
            logger.info(f"[DEBUG] Processing xpath category with xpathObject: {xpathObject}")

            for xpath, key in xpathObject.items():
                logger.info(f"[DEBUG] Processing xpath: {xpath} -> key: {key}")

                # Check if page is still valid
                try:
                    if target_page.is_closed():
                        logger.warning(f"[DEBUG] Target page is closed, cannot process xpath for key '{key}'")
                        return_json[key] = ""
                        continue

                    elements = target_page.locator(f"xpath={xpath}")
                    element_count = elements.count()
                    logger.info(f"[DEBUG] Found {element_count} elements for xpath: {xpath}")

                    if element_count > 0:
                        try:
                            text_content = elements.first.text_content()
                            if text_content is not None:
                                text_content = text_content.strip()
                            logger.info(f"[DEBUG] Raw text content for key '{key}': '{text_content}' (type: {type(text_content)})")

                            # Check if text content is empty or None
                            if text_content is None or text_content == "":
                                logger.warning(f"[DEBUG] Element found but text content is empty for key '{key}' xpath: {xpath}")
                                # Try to get innerHTML and innerText
                                try:
                                    element_html = elements.first.inner_html()
                                    element_text = elements.first.inner_text()
                                    logger.info(f"[DEBUG] Element innerHTML: '{element_html[:100]}...' innerText: '{element_text}'")
                                except Exception as inner_e:
                                    logger.debug(f"[DEBUG] Failed to get inner content: {inner_e}")

                            return_json[key] = text_content if text_content else ""
                            logger.info(f"[DEBUG] Final value for key '{key}': '{return_json[key]}'")
                        except Exception as e:
                            logger.error(f"[DEBUG] Error extracting text from element for key '{key}': {e}")
                            return_json[key] = ""
                    else:
                        logger.warning(f"[DEBUG] No elements found for xpath: {xpath}")
                        # Try some alternative xpath search methods
                        try:
                            # Try without the xpath prefix
                            fallback_elements = target_page.locator(xpath)
                            fallback_count = fallback_elements.count()
                            logger.info(f"[DEBUG] Fallback search (without xpath prefix) found {fallback_count} elements")
                            if fallback_count > 0:
                                text_content = fallback_elements.first.text_content()
                                if text_content:
                                    text_content = text_content.strip()
                                return_json[key] = text_content if text_content else ""
                                logger.info(f"[DEBUG] Fallback extraction successful for key '{key}': '{return_json[key]}'")
                            else:
                                return_json[key] = ""
                        except Exception as e:
                            logger.info(f"[DEBUG] Fallback xpath search also failed: {e}")
                            return_json[key] = ""

                except Exception as e:
                    logger.error(f"[DEBUG] Error processing xpath for key '{key}': {e}")
                    return_json[key] = ""

        elif config["category"] == "input":
            inputObjects = config.get("inputObject", {})
            logger.info(f"[DEBUG] Processing input category with inputObjects: {inputObjects}")
            for xpath, key in inputObjects.items():
                logger.info(f"[DEBUG] Processing input xpath: {xpath} -> key: {key}")
                try:
                    if target_page.is_closed():
                        logger.warning(f"[DEBUG] Target page is closed, cannot process input for key '{key}'")
                        return_json[key] = ""
                        continue

                    inputs = target_page.locator(f"xpath={xpath}")
                    input_count = inputs.count()
                    logger.info(f"[DEBUG] Found {input_count} input elements for xpath: {xpath}")
                    if input_count > 0:
                        try:
                            input_value = inputs.first.input_value()
                            if input_value:
                                input_value = input_value.strip()
                            return_json[key] = input_value if input_value else ""
                            logger.info(f"[DEBUG] Input value for key '{key}': '{return_json[key]}'")
                        except Exception as e:
                            logger.error(f"[DEBUG] Error getting input value for key '{key}': {e}")
                            return_json[key] = ""
                    else:
                        logger.warning(f"[DEBUG] No input elements found for xpath: {xpath}")
                        return_json[key] = ""
                except Exception as e:
                    logger.error(f"[DEBUG] Error processing input for key '{key}': {e}")
                    return_json[key] = ""

        elif config["category"] == "class&url":
            class_multiObject = config.get("class_multiObject", {})
            for class_name, object_list in class_multiObject.items():
                elements_texts = safely_get_text_content("." + class_name)
                for each_key in object_list:
                    if any(each_key.lower() == text.lower() for text in elements_texts):
                        return_json[each_key.lower()] = True

                for each_key in elements_texts:
                    # each_key.lower() not in object_list.lower():
                    if all(each_key.lower() not in item.lower() for item in object_list):
                        return_json["is_other_exist"] = True
                        break
                if "is_other_exist" not in return_json.keys():
                    return_json["is_other_exist"] = False

            class_multiObject_li = config.get("class_multiObject_li", {})
            for class_name, object_list in class_multiObject_li.items():
                elements_texts = safely_get_direct_li_playwright("." + class_name)
                for each_key in object_list:
                    if any(each_key.lower() == text.lower() for text in elements_texts):
                        return_json[each_key.lower()] = True

                for each_key in elements_texts:
                    # each_key.lower() not in object_list.lower():
                    if all(each_key.lower() not in item.lower() for item in object_list):
                        return_json["is_other_exist"] = True
                        break
                if "is_other_exist" not in return_json.keys():
                    return_json["is_other_exist"] = False

            url_include_expected = config.get("url_include_expected", [])
            for key in url_include_expected:
                try:
                    if target_page.is_closed():
                        logger.warning(f"[DEBUG] Target page is closed, cannot check URL for key '{key}'")
                        if key.lower() not in return_json.keys():
                            return_json[key.lower()] = False
                        continue

                    page_url = target_page.url.lower()
                    if key.lower() in page_url:
                        if key.lower() not in return_json.keys():
                            return_json[key.lower()] = True
                    else:
                        if key.lower() not in return_json.keys():
                            return_json[key.lower()] = False
                except Exception as e:
                    logger.error(f"[DEBUG] Error checking URL for key '{key}': {e}")
                    if key.lower() not in return_json.keys():
                        return_json[key.lower()] = False

            url_include_expected_multichoice = config.get("url_include_expected_multichoice", {})
            for key, value in url_include_expected_multichoice.items():
                try:
                    if target_page.is_closed():
                        logger.warning(f"[DEBUG] Target page is closed, cannot check URL for multichoice key '{key}'")
                        if value.lower() not in return_json.keys():
                            return_json[value.lower()] = False
                        continue

                    page_url = target_page.url.lower()
                    if key.lower() in page_url:
                        if value.lower() not in return_json.keys():
                            return_json[value.lower()] = True
                    else:
                        if value.lower() not in return_json.keys():
                            return_json[value.lower()] = False
                except Exception as e:
                    logger.error(f"[DEBUG] Error checking URL for multichoice key '{key}': {e}")
                    if value.lower() not in return_json.keys():
                        return_json[value.lower()] = False

        browser.close()

        # DEBUG: Add logging for final result and check for None values
        logger.info(f"[DEBUG] get_active_tab_html_parse final result: {return_json}")

        # Check for None values
        none_keys = [key for key, value in return_json.items() if value is None]
        if none_keys:
            logger.warning(f"[DEBUG] Found None values for keys: {none_keys}")

        # Check if all expected keys are present
        if config["category"] == "xpath":
            expected_keys = set(config.get("xpathObject", {}).values())
            actual_keys = set(return_json.keys())
            missing_keys = expected_keys - actual_keys
            if missing_keys:
                logger.warning(f"[DEBUG] Missing expected keys: {missing_keys}")

    return return_json
```

### `import:logging` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L1-L1`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:Dict` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L2-L2`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `56aa754a6cfb9066a41716442ba7d2df1a29a3774ff8d93b89b698fb5711f889`

```python
from typing import TypeVar, Dict
```

### `import:datetime` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L3-L3`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `0791be90ba0eb279d5ee6cf2e800414e147b396b66c8224451c711de65a6ac4a`

```python
from datetime import datetime, timedelta
```

### `import:pytz` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L4-L4`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `6acb22f8ef1c4e1d7176d96b2c6e5e3ab4fb5856c6e29673da4762396ad8f4c3`

```python
import pytz
```

### `import:requests` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L5-L5`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `333d1b652ae64febaa8b71b12c8fa33598ab9a6593d74ae7abf6bac592ef4884`

```python
import requests
```

### `logger` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L7-L7`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `1666d87529b5ea68340c3bbdde21df80306cf2dd6d5d4f5d3522ea238827979a`

```python
logger = logging.getLogger("desktopenv.getters.misc")
```

### `R` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L9-L9`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `0f278b25d07ad3546253810b64092bd07e25fe69f6e1b4a51382b60d49a8c21b`

```python
R = TypeVar("Rule")
```

### `day_of_week_mapping` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L11-L19`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `4c187d379cc110f19049f953ca5c9ee87d8d5bbe15a84c4ef68c3c8a948cef32`

```python
day_of_week_mapping = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thu',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun'
}
```

### `month_mapping` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L21-L34`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `04ecab911f403ab9d2a8f26665341f70050ab3eac9e3b82c4f564a42ff13d3ff`

```python
month_mapping = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec'
}
```

### `Month_Mapping_Full` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L36-L49`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `e939f29ea6308270790388e2430efc453ca5a56869713f11908cad719fb18676`

```python
Month_Mapping_Full = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}
```

### `month_mapping_full` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L51-L64`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `21963ba69127d01a9d7a283f26eef6b14fc225dffba48dcd58ab2428e6e23eae`

```python
month_mapping_full = {
    1: 'january',
    2: 'february',
    3:'march',
    4: 'april',
    5:'may',
    6: 'june',
    7: 'july',
    8: 'august',
    9:'september',
    10: 'october',
    11: 'november',
    12: 'december'
}
```

### `relativeTime_to_IntDay` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L66-L90`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `8638e32b62657f5ddb4db093ccb9e5597c138b7c8e95f668724bf96c280dfaf1`

```python
relativeTime_to_IntDay = {
    "tomorrow": 1,
    "5th next month": "special",
    "10th next month": "special",
    "11th next month": "special",
    "this month": "special",
    "this Saturday": "special",
    "this Sunday": "special",
    "next Monday": "special",
    "next Friday": "special",
    "next Saturday": "special",
    "next Sunday": "special",
    "next week Friday": "special",
    "next week Saturday": "special",
    "next week Sunday": "special",
    "week after next Friday": "special",
    "week after next Saturday": "special",
    "week after next Sunday": "special",
    "first monday four months later": "special",
    "first monday eight months later": "special",
    "next Monday split": "special",
    "next Friday split": "special",
    "week after next Monday split": "special",
    "week after next Friday split": "special"
}
```

### `_build_datetime_like` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L99-L105`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `d3f10d3cc394c3ccd0e850174d58d254c7a9c3a55548220f1f3660189185d2e1`

```python
def _build_datetime_like(reference_now: datetime, year: int, month: int, day: int) -> datetime:
    """
    Build a datetime that keeps timezone-awareness aligned with reference_now.
    """
    if reference_now.tzinfo is not None:
        return datetime(year, month, day, tzinfo=reference_now.tzinfo)
    return datetime(year, month, day)
```

### `_get_vm_now_datetime` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L108-L126`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `7ef35f4fb35b8c13048fc46941de50da98cad44ae3dde107fdbcd4af034bbf86`

```python
def _get_vm_now_datetime(env) -> datetime | None:
    """
    Get current datetime from the VM/client machine (not grader host).
    """
    try:
        if env is None or not getattr(env, "controller", None):
            return None
        result = env.controller.execute_python_command(
            "from datetime import datetime; print(datetime.now().astimezone().isoformat())"
        )
        if not result:
            return None
        output = result.get("output", "").strip()
        if not output:
            return None
        return datetime.fromisoformat(output)
    except Exception as e:
        logger.warning(f"Failed to get VM datetime, falling back to host timezone flow: {e}")
        return None
```

### `get_rule_relativeTime` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L128-L430`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `8ed49f4770ff7ae41e416dc00ed7a547e1c2bd487fd27175ff31b584bde66be6`

```python
def get_rule_relativeTime(env, config: Dict[str, R]) -> R:
    """
    According to the rule definded in funciton "apply_rules_to_timeFormat", convert the relative time to absolute time.
    config:
        'relativeTime': {
            "from": must exist; indicates the relativeTime.
            "to": optional; indicates the relativeTime.
        }
        If relativeTime only has key "from", then the key of time in "expected" dict must be "time".
        If relativeTime has key "to", then the key of time in "expected" dict must be "from" and "to".

        Optional 'timezone': timezone string like 'Europe/Zurich', 'America/New_York', etc.
        If not specified, will try to get timezone from IP geolocation.
    """
    logger.info(f"[DEBUG] get_rule_relativeTime called with config: {config}")

    relativeRules = config["rules"]
    relativeTime = relativeRules["relativeTime"] # int, "+" means future, "-" means past

    logger.info(f"[DEBUG] relativeTime: {relativeTime}")

    # Determine "now" — prefer VM local time so grader and agent agree on
    # what day it is, then convert to the config timezone if one is given.
    explicit_timezone = config.get("rules", {}).get("timezone")

    # Step 1: Try to get the VM's local datetime (what the agent sees).
    vm_now = _get_vm_now_datetime(env)

    if vm_now is not None:
        if explicit_timezone:
            try:
                timezone = pytz.timezone(explicit_timezone)
                now = vm_now.astimezone(timezone)
                logger.info(
                    f"Using VM datetime converted to config timezone {explicit_timezone}: "
                    f"{now.strftime('%Y-%m-%d %H:%M:%S %Z')} (VM raw: {vm_now.isoformat()})"
                )
            except pytz.exceptions.UnknownTimeZoneError:
                logger.error(f"Unknown timezone: {explicit_timezone}, using VM datetime as-is")
                now = vm_now
        else:
            now = vm_now
            logger.info(f"Using VM local datetime: {now.isoformat()}")
    else:
        # Step 2: VM unreachable — fall back to grader host time.
        logger.warning("Could not get VM datetime, falling back to host time")
        timezone_str = explicit_timezone or get_timezone_from_config(config)
        try:
            timezone = pytz.timezone(timezone_str)
            now = datetime.now(timezone)
            logger.info(f"Using host time in {timezone_str}: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {timezone_str}, falling back to UTC")
            timezone = pytz.UTC
            now = datetime.now(timezone)
            logger.info(f"Current time in UTC fallback: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # calculate the relative time
    if "to" not in relativeTime.keys():
        start_relative_time = relativeTime["from"]
        logger.info(f"Processing single time: '{start_relative_time}'")

        if relativeTime_to_IntDay[start_relative_time] != "special":
            # relativeTime can be represented by actual int days
            start_relative_time_IntDat = relativeTime_to_IntDay[start_relative_time]
            timediff = timedelta(days=start_relative_time_IntDat)
            absoluteDay = now + timediff
            logger.info(f"Simple calculation: {start_relative_time} = {start_relative_time_IntDat} days → {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            # special case, you can add more special cases here
            if start_relative_time == "5th next month":
                next_year = now.year + 1 if now.month == 12 else now.year
                next_month = now.month + 1 if now.month < 12 else 1
                next_day = 5
                absoluteDay = _build_datetime_like(now, next_year, next_month, next_day)
                logger.info(f"5th next month: {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif start_relative_time == "10th next month":
                next_year = now.year + 1 if now.month == 12 else now.year
                next_month = now.month + 1 if now.month < 12 else 1
                next_day = 10
                absoluteDay = _build_datetime_like(now, next_year, next_month, next_day)
                logger.info(f"10th next month: {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif start_relative_time == "this month":
                absoluteDay = now
                logger.info(f"This month: {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif start_relative_time == "next Monday":
                days_until_monday = (6-now.weekday()) + 1
                absoluteDay = now + timedelta(days=days_until_monday)
                logger.info(f"Next Monday: current weekday={now.weekday()}, days to add={days_until_monday} → {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif start_relative_time == "first monday four months later":
                next_year = now.year + 1 if now.month >=9 else now.year
                next_month = (now.month + 4 - 1) % 12 + 1
                # get the first monday of the next_month
                temp_date = _build_datetime_like(now, next_year, next_month, 1)
                days_to_monday = ((6-temp_date.weekday())+1)%7
                absoluteDay = temp_date + timedelta(days=days_to_monday)
                logger.info(f"First Monday 4 months later: {next_year}-{next_month:02d} → {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif start_relative_time == "first monday eight months later":
                next_year = now.year + 1 if now.month >= 5 else now.year
                next_month = (now.month + 8 - 1) % 12 + 1
                # get the first monday of the next_month
                temp_date = _build_datetime_like(now, next_year, next_month, 1)
                days_to_monday = ((6-temp_date.weekday())+1)%7
                absoluteDay = temp_date + timedelta(days=days_to_monday)
                logger.info(f"First Monday 8 months later: {next_year}-{next_month:02d} → {absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        time_value = relativeRules["expected"]["time"]
        if isinstance(time_value, list):
            regular_time = [apply_rules_to_timeFormat(t, absoluteDay) for t in time_value]
        else:
            regular_time = apply_rules_to_timeFormat(time_value, absoluteDay)
        logger.info(f"Final formatted time: {regular_time}")
        config["rules"]["expected"]["time"] = regular_time

    else:
        from_time = relativeTime["from"]
        to_time = relativeTime["to"]
        logger.info(f"Processing time range: from '{from_time}' to '{to_time}'")

        # deal with from_time first
        if relativeTime_to_IntDay[from_time] != "special":
            from_time_IntDat = relativeTime_to_IntDay[from_time]
            from_timediff = timedelta(days=from_time_IntDat)
            from_absoluteDay = now + from_timediff
            logger.info(f"From time calculation: {from_time} = {from_time_IntDat} days → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            if from_time == "this Saturday":
                days_until_saturday = (5-now.weekday())
                from_absoluteDay = now + timedelta(days=days_until_saturday)
                logger.info(f"This Saturday: current weekday={now.weekday()}, days to add={days_until_saturday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "10th next month":
                next_year = now.year + 1 if now.month == 12 else now.year
                next_month = now.month + 1 if now.month < 12 else 1
                next_day = 10
                from_absoluteDay = _build_datetime_like(now, next_year, next_month, next_day)
                logger.info(f"10th next month (from): {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next Monday" or from_time == "next Monday split":
               days_until_monday = (6-now.weekday()) + 1
               from_absoluteDay = now + timedelta(days=days_until_monday)
               logger.info(f"Next Monday (from): current weekday={now.weekday()}, days to add={days_until_monday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "week after next Monday split":
                # One week after "next Monday"
                days_until_monday = (6-now.weekday()) + 1 + 7
                from_absoluteDay = now + timedelta(days=days_until_monday)
                logger.info(f"Week after next Monday (from): current weekday={now.weekday()}, days to add={days_until_monday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next Friday":
                # Next weekend Friday calculation
                if now.weekday() < 4:  # Monday to Thursday - use this weekend
                    days_until_friday = 4 - now.weekday()
                elif now.weekday() == 4:  # Today is Friday - use next weekend
                    days_until_friday = 7
                else:  # Saturday to Sunday - use next weekend
                    days_until_friday = (7 - now.weekday()) + 4  # Days to next Monday + 4 to get to Friday
                from_absoluteDay = now + timedelta(days=days_until_friday)
                logger.info(f"Next Friday (from): current weekday={now.weekday()}, days to add={days_until_friday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next Saturday":
                # Next weekend Saturday calculation
                if now.weekday() < 5:  # Monday to Friday - use this weekend
                    days_until_saturday = 5 - now.weekday()
                elif now.weekday() == 5:  # Today is Saturday - use next weekend
                    days_until_saturday = 7
                else:  # Sunday - use next weekend
                    days_until_saturday = 6  # 6 days to next Saturday
                from_absoluteDay = now + timedelta(days=days_until_saturday)
                logger.info(f"Next Saturday (from): current weekday={now.weekday()}, days to add={days_until_saturday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next week Friday":
                # Next week Friday - simple: go to next Monday, then +4 days
                days_to_next_monday = 7 - now.weekday()
                days_until_friday = days_to_next_monday + 4  # Monday + 4 = Friday
                from_absoluteDay = now + timedelta(days=days_until_friday)
                logger.info(f"Next week Friday (from): current weekday={now.weekday()}, days to add={days_until_friday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next week Saturday":
                # Next week Saturday - simple: go to next Monday, then +5 days
                days_to_next_monday = 7 - now.weekday()
                days_until_saturday = days_to_next_monday + 5  # Monday + 5 = Saturday
                from_absoluteDay = now + timedelta(days=days_until_saturday)
                logger.info(f"Next week Saturday (from): current weekday={now.weekday()}, days to add={days_until_saturday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "next week Sunday":
                # Next week Sunday - simple: go to next Monday, then +6 days
                days_to_next_monday = 7 - now.weekday()
                days_until_sunday = days_to_next_monday + 6  # Monday + 6 = Sunday
                from_absoluteDay = now + timedelta(days=days_until_sunday)
                logger.info(f"Next week Sunday (from): current weekday={now.weekday()}, days to add={days_until_sunday} → {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "week after next Friday":
                # One week after "next week Friday"
                days_to_next_monday = 7 - now.weekday()
                from_absoluteDay = now + timedelta(days=days_to_next_monday + 4 + 7)
                logger.info(f"Week after next Friday (from): {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "week after next Saturday":
                # One week after "next week Saturday"
                days_to_next_monday = 7 - now.weekday()
                from_absoluteDay = now + timedelta(days=days_to_next_monday + 5 + 7)
                logger.info(f"Week after next Saturday (from): {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif from_time == "week after next Sunday":
                # One week after "next week Sunday"
                days_to_next_monday = 7 - now.weekday()
                from_absoluteDay = now + timedelta(days=days_to_next_monday + 6 + 7)
                logger.info(f"Week after next Sunday (from): {from_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                pass # more rules here
        if from_time in ("next Monday split", "week after next Monday split"):
            puday = apply_rules_to_timeFormat(relativeRules["expected"]["puDay"], from_absoluteDay)
            config["rules"]["expected"]["puDay"] = puday
            pumonth = apply_rules_to_timeFormat(relativeRules["expected"]["puMonth"], from_absoluteDay)
            config["rules"]["expected"]["puMonth"] = pumonth
            puyear = apply_rules_to_timeFormat(relativeRules["expected"]["puYear"], from_absoluteDay)
            config["rules"]["expected"]["puYear"] = puyear
            logger.info(f"Monday split formatting: puDay={puday}, puMonth={pumonth}, puYear={puyear}")
        else:
            regular_from_time = apply_rules_to_timeFormat(relativeRules["expected"]["from"], from_absoluteDay)
            config["rules"]["expected"]["from"] = regular_from_time
            logger.info(f"From time formatted: {regular_from_time}")

        # deal with to_time
        if relativeTime_to_IntDay[to_time] != "special":
            to_time_IntDat = relativeTime_to_IntDay[to_time]
            to_timediff = timedelta(days=to_time_IntDat)
            to_absoluteDay = now + to_timediff
            logger.info(f"To time calculation: {to_time} = {to_time_IntDat} days → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            if to_time == "this Sunday":
                days_until_sunday = (6-now.weekday())
                to_absoluteDay = now + timedelta(days=days_until_sunday)
                logger.info(f"This Sunday: current weekday={now.weekday()}, days to add={days_until_sunday} → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif to_time == "11th next month":
                next_year = now.year + 1 if now.month == 12 else now.year
                next_month = now.month + 1 if now.month < 12 else 1
                next_day = 11
                to_absoluteDay = _build_datetime_like(now, next_year, next_month, next_day)
                logger.info(f"11th next month (to): {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif to_time in ("next Friday", "next Friday split", "week after next Friday split"):
                # Check if from_time is any variant of "next Monday"
                if from_time in ["next Monday", "next Monday split", "week after next Monday split"]:
                    # Calculate Friday of the same week as the Monday
                    # from_absoluteDay is already calculated as next Monday
                    # Friday is 4 days after Monday (Monday=0, Friday=4)
                    to_absoluteDay = from_absoluteDay + timedelta(days=4)
                    logger.info(f"Next Friday (same week as Monday): from Monday {from_absoluteDay.strftime('%Y-%m-%d')} + 4 days → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                else:
                    # Standalone "next Friday" calculation
                    if now.weekday() < 4:  # Monday to Thursday
                        days_to_friday = 4 - now.weekday()
                    else:  # Friday to Sunday
                        days_to_friday = (6 - now.weekday()) + 5
                    to_absoluteDay = now + timedelta(days=days_to_friday)
                    logger.info(f"Next Friday (standalone): current weekday={now.weekday()}, days to add={days_to_friday} → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif to_time == "next Sunday":
                # Next weekend Sunday calculation - should be the same weekend as the from_time
                if from_time in ["next Friday", "next Saturday"]:
                    # Calculate Sunday of the same weekend as from_time
                    # from_absoluteDay is already calculated, get the Sunday of that week
                    days_to_add_for_sunday = 6 - from_absoluteDay.weekday()  # Days from Friday/Saturday to Sunday
                    to_absoluteDay = from_absoluteDay + timedelta(days=days_to_add_for_sunday)
                    logger.info(f"Next Sunday (to, same weekend as {from_time}): from {from_absoluteDay.strftime('%Y-%m-%d %A')} + {days_to_add_for_sunday} days → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                else:
                    # Standalone next Sunday calculation
                    if now.weekday() < 6:  # Monday to Saturday - use this weekend
                        days_until_sunday = 6 - now.weekday()
                    else:  # Sunday - use next weekend
                        days_until_sunday = 7
                    to_absoluteDay = now + timedelta(days=days_until_sunday)
                    logger.info(f"Next Sunday (to, standalone): current weekday={now.weekday()}, days to add={days_until_sunday} → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif to_time == "next week Sunday":
                # Next week Sunday calculation - should be the same week as from_time if from_time is also "next week"
                if from_time in ["next week Friday", "next week Saturday"]:
                    # Calculate Sunday of the same week as from_time
                    # from_absoluteDay is already calculated, get the Sunday of that week
                    days_to_add_for_sunday = 6 - from_absoluteDay.weekday()  # Days from Friday/Saturday to Sunday
                    to_absoluteDay = from_absoluteDay + timedelta(days=days_to_add_for_sunday)
                    logger.info(f"Next week Sunday (to, same week as {from_time}): from {from_absoluteDay.strftime('%Y-%m-%d %A')} + {days_to_add_for_sunday} days → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                else:
                    # Standalone next week Sunday calculation - simple: go to next Monday, then +6 days
                    days_to_next_monday = 7 - now.weekday()
                    days_until_sunday = days_to_next_monday + 6  # Monday + 6 = Sunday
                    to_absoluteDay = now + timedelta(days=days_until_sunday)
                    logger.info(f"Next week Sunday (to, standalone): current weekday={now.weekday()}, days to add={days_until_sunday} → {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            elif to_time == "week after next Sunday":
                # One week after "next week Sunday"; same week as the paired
                # "week after next Friday/Saturday" from_time when present.
                if from_time in ["week after next Friday", "week after next Saturday"]:
                    days_to_add_for_sunday = 6 - from_absoluteDay.weekday()
                    to_absoluteDay = from_absoluteDay + timedelta(days=days_to_add_for_sunday)
                else:
                    days_to_next_monday = 7 - now.weekday()
                    to_absoluteDay = now + timedelta(days=days_to_next_monday + 6 + 7)
                logger.info(f"Week after next Sunday (to): {to_absoluteDay.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                pass # more rules here
        if to_time in ("next Friday split", "week after next Friday split"):
            to_day = apply_rules_to_timeFormat(relativeRules["expected"]["doDay"], to_absoluteDay)
            config["rules"]["expected"]["doDay"] = to_day
            to_month = apply_rules_to_timeFormat(relativeRules["expected"]["doMonth"], to_absoluteDay)
            config["rules"]["expected"]["doMonth"] = to_month
            to_year = apply_rules_to_timeFormat(relativeRules["expected"]["doYear"], to_absoluteDay)
            config["rules"]["expected"]["doYear"] = to_year
            logger.info(f"Friday split formatting: doDay={to_day}, doMonth={to_month}, doYear={to_year}")
        else:
            regular_to_time = apply_rules_to_timeFormat(relativeRules["expected"]["to"], to_absoluteDay)
            config["rules"]["expected"]["to"] = regular_to_time
            logger.info(f"To time formatted: {regular_to_time}")

    logger.info(f"[DEBUG] Final config rules: {config['rules']}")
    print(config["rules"])
    return config["rules"]
```

### `apply_rules_to_timeFormat` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L433-L445`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `6a7f27c25c09185bea01cd34be242cd10c36327674da5cb5473e979ae1983bb2`

```python
def apply_rules_to_timeFormat(timeFormat: str, absoluteDay: datetime):
    timeFormat = timeFormat.replace("{DoW}", day_of_week_mapping[absoluteDay.weekday()], 1)
    timeFormat = timeFormat.replace("{Month}", month_mapping[absoluteDay.month], 1)
    timeFormat = timeFormat.replace("{DayD}", str(absoluteDay.day), 1)
    timeFormat = timeFormat.replace("{Year}", str(absoluteDay.year), 1)
    timeFormat = timeFormat.replace("{Month0D}", "0"+str(absoluteDay.month) if absoluteDay.month < 10 else str(absoluteDay.month), 1)
    timeFormat = timeFormat.replace("{month}", month_mapping_full[absoluteDay.month], 1)
    timeFormat = timeFormat.replace("{MonthFull}", Month_Mapping_Full[absoluteDay.month], 1)
    timeFormat = timeFormat.replace("{Day0D}", "0"+str(absoluteDay.day) if absoluteDay.day < 10 else str(absoluteDay.day), 1)
    timeFormat = timeFormat.replace("{MonthD}", str(absoluteDay.month), 1)
    # you can add other replace rules here

    return timeFormat
```

### `get_timezone_from_ip` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L460-L479`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `6019a3a47054d7eb9657d9a974f8274fdca66970ed3c10bc59853a4fe3b31284`

```python
def get_timezone_from_ip() -> str:
    """
    Get timezone from IP address using IP geolocation API
    Returns timezone string like 'Europe/Zurich' or 'UTC' as fallback
    """
    try:
        # Try ipapi.co first
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            timezone = data.get('timezone')
            if timezone:
                logger.info(f"Timezone from IP: {timezone}")
                return timezone
    except Exception as e:
        logger.warning(f"Failed to get timezone from IP: {e}")

    # Fallback to UTC
    logger.info("Using UTC as fallback timezone")
    return 'UTC'
```

### `get_timezone_from_config` from `official/desktop_env/evaluators/getters/misc.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py#L481-L498`

Full source SHA-256: `573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10`

Exact excerpt SHA-256: `da92d1f2bc881141c633f2916bf4b8e9830dc3c4289020325e1a52d7ab068464`

```python
def get_timezone_from_config(config: Dict, default_timezone: str = None) -> str:
    """
    Get timezone from config, with fallback options
    Priority: config timezone > default_timezone > IP-based timezone > UTC
    """
    # Check if timezone is specified in config
    if "timezone" in config.get("rules", {}):
        timezone = config["rules"]["timezone"]
        logger.info(f"Using timezone from config: {timezone}")
        return timezone

    # Use provided default
    if default_timezone:
        logger.info(f"Using provided default timezone: {default_timezone}")
        return default_timezone

    # Get from IP
    return get_timezone_from_ip()
```

### `import:json` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L5-L5`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc`

```python
import json
```

### `import:logging` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L6-L6`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `logger` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L25-L25`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `76240bbce147543d0a4d62344a6d4789fcd7a13a30ab708e18535fda82238f03`

```python
logger = logging.getLogger("desktopenv.metric.general")
```

### `check_direct_json_object` from `official/desktop_env/evaluators/metrics/general.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/general.py#L382-L480`

Full source SHA-256: `22cafba4a4b49a2c478a6266cfd98c6eb54e1bad4691d243b5113ba8896e41d7`

Exact excerpt SHA-256: `7e87793e80d1b6569305c2ba3ae087db92407aa5d4491655ba2be5d12cd2a992`

```python
def check_direct_json_object(result, rules) -> float:
    """
    One of the most commonly used function to evalute.
    Compare two json objects directly.
    """
    logger.info(f"[DEBUG] check_direct_json_object called with result: {result}")
    logger.info(f"[DEBUG] check_direct_json_object called with rules: {rules}")
    
    if isinstance(result, str):
        # remove blanks before and after result
        result = result.strip()
        # replace all ' with "
        result = result.replace("'", '"')
        # load json object
        result = json.loads(result)
        
    logger.info(f"[DEBUG] Processed result: {result}")
    
    if result is None:
        logger.info("[DEBUG] Result is None, returning 0.0")
        return 0.
    
    # Check if expected value contains evaluation failure indicator
    try:
        expected_json = rules.get("expected", {})
        if expected_json:
            for key, value in expected_json.items():
                if value == "__EVALUATION_FAILED__":
                    logger.error(f"[DEBUG] Expected value for key '{key}' indicates evaluation failure, returning 0.0")
                    return 0.
    except Exception as e:
        logger.error(f"[DEBUG] Error checking for evaluation failure indicator: {e}")
        return 0.
    try:
        expect_in_result = rules.get("expect_in_result", False)
        logger.info(f"[DEBUG] expect_in_result: {expect_in_result}")
        
        if not expect_in_result:
            expected_json = rules["expected"]
            logger.info(f"[DEBUG] Expected JSON: {expected_json}")
            
            for key in expected_json.keys():
                expected_value = expected_json.get(key)
                actual_value = result.get(key)
                logger.info(f"[DEBUG] Checking key '{key}': expected='{expected_value}', actual='{actual_value}'")
                
                if rules.get("ignore_list_order", False):
                    expected_value = sorted(expected_value)
                    result_value = sorted(result.get(key))
                    logger.info(f"[DEBUG] Comparing lists (sorted): expected={expected_value}, actual={result_value}")
                    if expected_value != result_value:
                        logger.info(f"[DEBUG] List comparison failed for key '{key}', returning 0.0")
                        return 0.
                else:
                    if expected_value != actual_value:
                        logger.info(f"[DEBUG] Value comparison failed for key '{key}': expected='{expected_value}', actual='{actual_value}', returning 0.0")
                        return 0.
                    else:
                        logger.info(f"[DEBUG] Value comparison passed for key '{key}'")
                        
            logger.info("[DEBUG] All comparisons passed, returning 1.0")
            return 1.0
        else:
            expected_json = rules["expected"]
            logger.info(f"[DEBUG] Expected JSON (expect_in_result mode): {expected_json}")

            for key in expected_json.keys():
                if isinstance(expected_json.get(key), list):
                    flag = 0
                    expected_value_list = expected_json.get(key)
                    logger.info(f"[DEBUG] Checking list key '{key}': expected_list={expected_value_list}, actual='{result.get(key)}'")
                    for each_expected_value in expected_value_list:
                        # Handle both list and string cases
                        if isinstance(result.get(key), list) and each_expected_value in result.get(key):
                            flag = 1
                            logger.info(f"[DEBUG] Found expected value '{each_expected_value}' in result list for key '{key}'")
                            break
                        elif isinstance(result.get(key), str) and each_expected_value == result.get(key):
                            flag = 1
                            logger.info(f"[DEBUG] Found expected value '{each_expected_value}' matches result string for key '{key}'")
                            break
                    if flag == 0:
                        logger.info(f"[DEBUG] No expected values found in result for key '{key}', returning 0.0")
                        return 0.
                elif isinstance(expected_json.get(key), str):
                    expected_str = expected_json.get(key)
                    actual_str = result.get(key)
                    logger.info(f"[DEBUG] Checking string key '{key}': expected='{expected_str}', actual='{actual_str}'")
                    if expected_str not in actual_str:
                        logger.info(f"[DEBUG] Expected string '{expected_str}' not found in actual string '{actual_str}' for key '{key}', returning 0.0")
                        return 0.
                else:
                    logger.debug("check_direct_json_object: expected value type not supported")
                    return 0.
            logger.info("[DEBUG] All expect_in_result comparisons passed, returning 1.0")
            return 1.0
    except Exception as e:
        logger.debug(f"check_direct_json_object: result is not a valid json object, error: {e}")
        return 0.
```
