# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `b4f95342-463e-4179-8c3f-193cd7241fb2`
- task_id: `b4f95342-463e-4179-8c3f-193cd7241fb2`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `chrome`
- snapshot: `chrome`
- related apps: `chrome`
- official instruction: Find the Next Available dates for Diamond.
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
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/general.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/chrome/b4f95342-463e-4179-8c3f-193cd7241fb2.json`

Source SHA-256: `1c98d3c1d2e232e997c8331902e80d169bcc652e208e49877461bd1c5182e25b`

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
          "https://www.recreation.gov/"
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
      "class": "camp-sortable-column-header",
      "order": "2",
      "selector": "class",
      "type": "gotoRecreationPage_and_get_html_content"
    },
    "func": "check_direct_json_object",
    "result": {
      "category": "class",
      "class_multiObject": {
        "camp-sortable-column-header": {
          "2": "camp-sortable-column-header"
        }
      },
      "class_singleObject": {},
      "goto_prefix": "https://www.",
      "type": "active_tab_html_parse"
    }
  },
  "fixed_ip": false,
  "id": "b4f95342-463e-4179-8c3f-193cd7241fb2",
  "instruction": "Find the Next Available dates for Diamond.",
  "possibility_of_env_change": "high",
  "proxy": false,
  "related_apps": [
    "chrome"
  ],
  "snapshot": "chrome",
  "source": "test_task_1",
  "trajectory": "trajectories/"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `bdf0261af2379b250e6a537a2b50053d9102d963dbb573c79e1a6a868e05c38c`

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
      "end_line": 2653,
      "excerpt_sha256": "b51ab7616c81e96fd1533811c42b87a98d47828499a71b2bbf362e1e1d479010",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "start_line": 2332,
      "symbol": "get_gotoRecreationPage_and_get_html_content",
      "upstream_path": "desktop_env/evaluators/getters/chrome.py"
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
      "config_sha256": "5268638cb71348fb2df4544f89b05f37bb580370bf9e5f031ac8f1d0badd0946",
      "packet_path": "official/desktop_env/evaluators/getters/chrome.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py",
      "source_sha256": "7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce",
      "symbol": "get_gotoRecreationPage_and_get_html_content",
      "type": "gotoRecreationPage_and_get_html_content"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "2aa11564b1cb6097588649a6dfe5e08847e05f8f1172e5202dbc6bc6b7f93621",
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
      "config_sha256": "62b13c61e222f64c9d58ebc86893b1c7221b04719639adb516dfcb98fb92f2e2",
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
  "task_id": "b4f95342-463e-4179-8c3f-193cd7241fb2"
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

### `get_gotoRecreationPage_and_get_html_content` from `official/desktop_env/evaluators/getters/chrome.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/chrome.py#L2332-L2653`

Full source SHA-256: `7be9fd01be498651b7d346d4307ecde99f08296f59f98e003bd5de24771636ce`

Exact excerpt SHA-256: `b51ab7616c81e96fd1533811c42b87a98d47828499a71b2bbf362e1e1d479010`

```python
def get_gotoRecreationPage_and_get_html_content(env, config: Dict[str, Any]):
    """
    especially used for www.recreation.gov examples
    """
    # Add logging for debugging
    logger.info(f"[RECREATION_PAGE] Starting recreation.gov page processing")
    logger.debug(f"[RECREATION_PAGE] Config: {config}")

    host = env.vm_ip
    port = env.chromium_port  # fixme: this port is hard-coded, need to be changed from config file
    server_port = env.server_port
    use_proxy = env.current_use_proxy

    remote_debugging_url = f"http://{host}:{port}"
    backend_url = f"http://{host}:{server_port}"

    # Configuration for retry and timeout
    max_retries = 3
    timeout_ms = 60000  # Increase timeout to 60 seconds

    # Test basic connectivity first
    logger.info(f"[RECREATION_PAGE] Testing basic network connectivity...")
    try:
        import urllib.request
        test_response = urllib.request.urlopen('http://www.google.com', timeout=10)
        logger.info(f"[RECREATION_PAGE] Basic connectivity test passed (Google accessible)")
    except Exception as e:
        logger.warning(f"[RECREATION_PAGE] Basic connectivity test failed: {e}")
        logger.info(f"[RECREATION_PAGE] Proceeding anyway...")

    for attempt in range(max_retries):
        try:
            logger.info(f"[RECREATION_PAGE] Attempt {attempt + 1}/{max_retries}")

            with sync_playwright() as p:
                # Connect to remote Chrome instance
                try:
                    browser = p.chromium.connect_over_cdp(remote_debugging_url)
                    logger.info(f"[RECREATION_PAGE] Successfully connected to existing Chrome instance")
                except Exception as e:
                    logger.warning(f"[RECREATION_PAGE] Failed to connect to existing Chrome instance: {e}")
                    logger.info(f"[RECREATION_PAGE] Starting new Chrome instance with enhanced options...")

                    # If the connection fails, start a new browser instance with better options
                    app = 'chromium' if _is_arm_architecture(env) else 'google-chrome'
                    command = [
                        app,
                        "--remote-debugging-port=1337",
                        "--no-sandbox",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-dev-shm-usage",
                        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ]

                    if use_proxy:
                        command.append(f"--proxy-server=127.0.0.1:18888")
                        logger.info(f"[RECREATION_PAGE] Using proxy server: 127.0.0.1:18888")

                    logger.info(f"[RECREATION_PAGE] Starting browser with command: {' '.join(command)}")
                    payload = json.dumps({"command": command, "shell": False})
                    headers = {"Content-Type": "application/json"}
                    requests.post(backend_url + "/setup/launch", headers=headers, data=payload)
                    time.sleep(8)  # Give more time for browser to start
                    browser = p.chromium.connect_over_cdp(remote_debugging_url)
                    logger.info(f"[RECREATION_PAGE] Successfully connected to new Chrome instance")

                page = browser.new_page()

                # Set longer timeout for all operations
                page.set_default_timeout(timeout_ms)

                # Set additional headers to appear more like a real browser
                page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })

                # Try multiple URLs to test connectivity
                test_urls = [
                    "https://www.recreation.gov/",
                    "http://www.recreation.gov/",
                    "https://recreation.gov/",
                ]

                successful_url = None
                for test_url in test_urls:
                    try:
                        # Step 1: Navigate to recreation.gov with better error handling
                        logger.info(f"[RECREATION_PAGE] Trying to navigate to: {test_url}")

                        # Try different wait strategies
                        wait_strategies = ['domcontentloaded', 'load', 'networkidle']

                        for wait_until in wait_strategies:
                            try:
                                logger.debug(f"[RECREATION_PAGE] Trying wait strategy: {wait_until}")
                                page.goto(test_url, wait_until=wait_until, timeout=timeout_ms)
                                logger.info(f"[RECREATION_PAGE] Successfully loaded {test_url} with strategy {wait_until}")
                                logger.info(f"[RECREATION_PAGE] Page title: '{page.title()}'")
                                logger.info(f"[RECREATION_PAGE] Current URL: '{page.url}'")
                                successful_url = test_url
                                break
                            except Exception as strategy_error:
                                logger.debug(f"[RECREATION_PAGE] Wait strategy {wait_until} failed: {strategy_error}")
                                continue

                        if successful_url:
                            break

                    except Exception as url_error:
                        logger.warning(f"[RECREATION_PAGE] Failed to navigate to {test_url}: {url_error}")
                        continue

                if not successful_url:
                    raise Exception("Failed to navigate to any recreation.gov URL variant")

                # Additional wait to ensure page is fully loaded
                try:
                    page.wait_for_load_state('networkidle', timeout=30000)
                    logger.info(f"[RECREATION_PAGE] Page fully loaded and idle")
                except Exception as e:
                    logger.warning(f"[RECREATION_PAGE] NetworkIdle wait failed, continuing: {e}")

                try:
                    # Step 2: Fill search input
                    logger.info(f"[RECREATION_PAGE] Filling search input with 'Diamond'...")
                    page.wait_for_selector("input#hero-search-input", state='visible', timeout=timeout_ms)
                    page.fill("input#hero-search-input", "Diamond")
                    logger.info(f"[RECREATION_PAGE] Successfully filled search input")

                except Exception as e:
                    logger.error(f"[RECREATION_PAGE] Failed to fill search input: {e}")
                    raise e

                try:
                    # Step 3: Click search button
                    logger.info(f"[RECREATION_PAGE] Clicking search button...")
                    page.wait_for_selector("button.nav-search-button", state='visible', timeout=timeout_ms)
                    page.click("button.nav-search-button")
                    logger.info(f"[RECREATION_PAGE] Successfully clicked search button")
                    print("after first click")

                    # Wait for search results to load
                    time.sleep(10)

                except Exception as e:
                    logger.error(f"[RECREATION_PAGE] Failed to click search button: {e}")
                    raise e

                    # Step 4: Wait for search results page to load, then click search result
                    logger.info(f"[RECREATION_PAGE] Waiting for search results page...")
                    # Wait for URL to change to search results (avoids being blocked by ongoing navigation)
                    page.wait_for_url(url=re.compile(r"recreation\.gov/search"), timeout=20000)
                    # Allow DOM to settle; avoid relying on networkidle which may never fire
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    time.sleep(3)

                    logger.info(f"[RECREATION_PAGE] Waiting for and clicking search result...")
                    # Try visible first; fall back to attached (element in DOM, then scroll into view)
                    search_result_selector = ".search-result-highlight--success"
                    try:
                        page.wait_for_selector(search_result_selector, state="visible", timeout=25000)
                    except Exception:
                        logger.debug("[RECREATION_PAGE] Visible wait failed, trying attached then scroll into view")
                        page.wait_for_selector(search_result_selector, state="attached", timeout=25000)
                        page.locator(search_result_selector).first.scroll_into_view_if_needed(timeout=5000)
                        page.wait_for_selector(search_result_selector, state="visible", timeout=5000)

                    with page.expect_popup() as popup_info:
                        page.click(search_result_selector)

                    time.sleep(30)  # Wait for popup to fully load
                    print("after second click")
                    logger.info(f"[RECREATION_PAGE] Successfully clicked search result")

                except Exception as e:
                    logger.error(f"[RECREATION_PAGE] Failed to click search result: {e}")
                    raise e

                try:
                    # Step 5: Handle new page
                    newpage = popup_info.value
                    newpage.set_default_timeout(timeout_ms)
                    # Use 'load' instead of 'networkidle'; recreation.gov keeps background requests
                    # so networkidle often never fires and causes 60s timeouts
                    newpage.wait_for_load_state("load", timeout=20000)
                    time.sleep(2)

                    page_title = newpage.title()
                    logger.info(f"[RECREATION_PAGE] New page loaded successfully")
                    logger.info(f"[RECREATION_PAGE] New page title: '{page_title}'")
                    logger.info(f"[RECREATION_PAGE] New page URL: '{newpage.url}'")
                    print(f"go to newpage: {page_title}")
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"[RECREATION_PAGE] Failed to handle new page: {e}")
                    raise e

                try:
                    # Step 6: Click next-available button with better error handling
                    logger.info(f"[RECREATION_PAGE] Looking for next-available button...")

                    # Try multiple selectors for the button
                    selectors_to_try = [
                        "button.next-available",
                        "button[class*='next-available']",
                        "button[class*='next']",
                        ".next-available",
                        "[data-testid*='next']"
                    ]

                    button_clicked = False
                    for selector in selectors_to_try:
                        try:
                            logger.debug(f"[RECREATION_PAGE] Trying selector: {selector}")
                            newpage.wait_for_selector(selector, state='visible', timeout=30000)
                            newpage.click(selector, timeout=30000)
                            logger.info(f"[RECREATION_PAGE] Successfully clicked next-available button with selector: {selector}")
                            print("after third click")
                            button_clicked = True
                            break
                        except Exception as selector_error:
                            logger.debug(f"[RECREATION_PAGE] Selector '{selector}' failed: {selector_error}")
                            continue

                    if not button_clicked:
                        logger.warning(f"[RECREATION_PAGE] Could not find or click next-available button with any selector")
                        logger.info(f"[RECREATION_PAGE] Continuing without clicking next-available button")
                        print("Continuing without clicking next-available button")

                except Exception as e:
                    logger.warning(f"[RECREATION_PAGE] Error with next-available button: {e}")
                    logger.info(f"[RECREATION_PAGE] Continuing execution despite button click failure")
                    print("Continuing without clicking next-available button")

                # Step 7: Extract content based on config
                return_json = {}
                return_json["expected"] = {}

                try:
                    logger.info(f"[RECREATION_PAGE] Extracting content based on config...")

                    if config["selector"] == "class":
                        className = config["class"]
                        logger.debug(f"[RECREATION_PAGE] Looking for elements with class: {className}")

                        if "order" in config.keys():
                            try:
                                elements = newpage.query_selector_all("." + className)
                                order_index = int(config["order"])
                                logger.info(f"[RECREATION_PAGE] Found {len(elements)} elements with class '{className}', looking for index {order_index}")

                                if len(elements) > order_index:
                                    text_content = elements[order_index].text_content()
                                    if text_content:
                                        text_content = text_content.strip()
                                    return_json["expected"][className] = text_content
                                    logger.info(f"[RECREATION_PAGE] Successfully extracted text from element at index {order_index}: '{text_content}'")
                                else:
                                    logger.warning(f"[RECREATION_PAGE] Element with class '{className}' at index {order_index} not found. Found {len(elements)} elements.")
                                    return_json["expected"][className] = "__EVALUATION_FAILED__"
                            except Exception as e:
                                logger.error(f"[RECREATION_PAGE] Error accessing element with class '{className}' at specific order: {e}")
                                return_json["expected"][className] = "__EVALUATION_FAILED__"
                        else:
                            try:
                                element = newpage.query_selector("." + className)
                                if element:
                                    text_content = element.text_content()
                                    if text_content:
                                        text_content = text_content.strip()
                                    return_json["expected"][className] = text_content
                                    logger.info(f"[RECREATION_PAGE] Successfully extracted text from first element: '{text_content}'")
                                else:
                                    logger.warning(f"[RECREATION_PAGE] Element with class '{className}' not found.")
                                    return_json["expected"][className] = "__EVALUATION_FAILED__"
                            except Exception as e:
                                logger.error(f"[RECREATION_PAGE] Error accessing element with class '{className}': {e}")
                                return_json["expected"][className] = "__EVALUATION_FAILED__"

                    logger.info(f"[RECREATION_PAGE] Content extraction completed successfully")
                    logger.info(f"[RECREATION_PAGE] Final result: {return_json}")

                except Exception as e:
                    logger.error(f"[RECREATION_PAGE] Error during content extraction: {e}")
                    # Return a structure indicating extraction failed
                    return_json["expected"] = {"extraction_error": "__EVALUATION_FAILED__"}

                browser.close()
                return return_json

        except Exception as e:
            logger.error(f"[RECREATION_PAGE] Attempt {attempt + 1} failed: {str(e)}")
            logger.error(f"[RECREATION_PAGE] Exception type: {type(e).__name__}")

            if attempt < max_retries - 1:
                logger.info(f"[RECREATION_PAGE] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error(f"[RECREATION_PAGE] All {max_retries} attempts failed. Returning error result.")
                # Return a structure that indicates complete failure
                return {
                    "expected": {
                        "error": "__EVALUATION_FAILED__",
                        "error_message": f"Failed after {max_retries} attempts: {str(e)}"
                    }
                }

    # This should never be reached, but just in case
    logger.error(f"[RECREATION_PAGE] Unexpected code path reached")
    return {
        "expected": {
            "error": "__EVALUATION_FAILED__",
            "error_message": "Unexpected error in function execution"
        }
    }
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
