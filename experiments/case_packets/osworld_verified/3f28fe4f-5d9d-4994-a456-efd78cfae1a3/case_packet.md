# Case Packet

## Case Metadata

- domain: `osworld_verified`
- case_unit_id: `3f28fe4f-5d9d-4994-a456-efd78cfae1a3`
- task_id: `3f28fe4f-5d9d-4994-a456-efd78cfae1a3`

## Benchmark Task Summary

- benchmark: `OSWorld-Verified`
- split: `test_nogdrive`
- application domain: `thunderbird`
- snapshot: `thunderbird`
- related apps: `thunderbird`
- official instruction: Set up a plain text signature for my email account in Thunderbird. The first line is my name "Anonym" and the second line is my affiliation "XYZ Lab".
- evaluator functions: `check_thunderbird_prefs`
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
- `official/desktop_env/evaluators/getters/misc.py`
- `official/desktop_env/evaluators/metrics/__init__.py`
- `official/desktop_env/evaluators/metrics/thunderbird.py`
- `official/desktop_env/evaluators/metrics/utils.py`
- `official/task.json`

## Packet Source Files

### `official/task.json`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/evaluation_examples/examples/thunderbird/3f28fe4f-5d9d-4994-a456-efd78cfae1a3.json`

Source SHA-256: `d47ced9d6f815349f2d268679649883fc567af340484b4e39108c72c0f842666`

```json
{
  "config": [
    {
      "parameters": {
        "files": [
          {
            "path": "/home/user/thunderbird-profile.tar.gz",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/thunderbird/dd84e895-72fd-4023-a336-97689ded257c/thunderbird-profile.tar.gz"
          }
        ]
      },
      "type": "download"
    },
    {
      "parameters": {
        "command": [
          "tar",
          "-xzv",
          "--recursive-unlink",
          "-f",
          "/home/user/thunderbird-profile.tar.gz",
          "-C",
          "/home/user/"
        ]
      },
      "type": "execute"
    },
    {
      "parameters": {
        "command": [
          "/usr/bin/thunderbird"
        ]
      },
      "type": "launch"
    }
  ],
  "evaluator": {
    "expected": {
      "rules": {
        "expect": {
          "mail.identity.id1.htmlSigText": {
            "method": "re.S",
            "ref": "Anonym\\nXYZ Lab"
          }
        }
      },
      "type": "rule"
    },
    "func": "check_thunderbird_prefs",
    "postconfig": [
      {
        "parameters": {
          "by_class": true,
          "strict": true,
          "window_name": "Mail.thunderbird"
        },
        "type": "close_window"
      },
      {
        "parameters": {
          "seconds": 0.5
        },
        "type": "sleep"
      }
    ],
    "result": {
      "dest": "thunder-prefs.js",
      "path": "/home/user/.thunderbird/t5q2a5hp.default-release/prefs.js",
      "type": "vm_file"
    }
  },
  "fixed_ip": false,
  "id": "3f28fe4f-5d9d-4994-a456-efd78cfae1a3",
  "instruction": "Set up a plain text signature for my email account in Thunderbird. The first line is my name \"Anonym\" and the second line is my affiliation \"XYZ Lab\".",
  "possibility_of_env_change": "low",
  "proxy": false,
  "related_apps": [
    "thunderbird"
  ],
  "snapshot": "thunderbird",
  "source": "https://www.adsigner.com/user-manual/signatures/setup-email-client-thunderbird/#:~:text=is%20probably%20hidden.-,Right%20click%20on%20the%20empty%20space%20at%20the%20top%20of,signature%20from%20a%20file%20instead.",
  "trajectory": "trajectories/6766f2b8-8a72-417f-a9e5-56fcaa735837"
}
```

### `derived/evaluator_contract.json`

Source ref: `mechanically extracted from the pinned task and evaluator sources`

Source SHA-256: `9a76e5236fada4d562f88c9d9d5bfdeddf1051f460eebbb3ca6f8025d7f62fa9`

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
      "excerpt_sha256": "261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 1,
      "symbol": "import:json",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 2,
      "excerpt_sha256": "c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 2,
      "symbol": "import:logging",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 3,
      "excerpt_sha256": "a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 3,
      "symbol": "import:re",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 4,
      "excerpt_sha256": "d302f7bc3bed2a644bf67167ab809b01dc4139c783a2105412e92aa7d3c43173",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 4,
      "symbol": "import:Dict",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 5,
      "excerpt_sha256": "bdd1ef6bf23562ebfb90a40863c04bb9443d3825b990fa3fc7abedd71e86059f",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 5,
      "symbol": "import:Any",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 10,
      "excerpt_sha256": "02bb8ed3b5a788893ac0b3bfcb70e5dfe18643db6027bac46d4ed004e5ddae41",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 10,
      "symbol": "logger",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 14,
      "excerpt_sha256": "663034468155d90d4be748a3365b0e89a373b2a0b46010948f8a3fdb6c5d6a89",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 14,
      "symbol": "_pref_pattern",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
    },
    {
      "end_line": 67,
      "excerpt_sha256": "4f881f23ac2db41464a1c413531c899605d69eb65eb3438d35bb9cb35faeacab",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "start_line": 17,
      "symbol": "check_thunderbird_prefs",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
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
      "end_line": 11,
      "excerpt_sha256": "e433aafde859fb8c470f709800ddf6fd5c57ba89c44a00c2f5e2d26aea761cbc",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 11,
      "symbol": "import:Iterable",
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
      "end_line": 28,
      "excerpt_sha256": "63f180054250da329b72f9f846c9875bf8980e9d5c98bd7164a8dc738eb3216c",
      "packet_path": "official/desktop_env/evaluators/metrics/utils.py",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py",
      "source_sha256": "45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577",
      "start_line": 28,
      "symbol": "import:MultiCellRange",
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
      "config_sha256": "7ae53a9c275ffb99cf82856d7ca0df33278fff480cafc1ac46d605feecffa228",
      "packet_path": "official/desktop_env/evaluators/getters/misc.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/getters/misc.py",
      "source_sha256": "573fa6bf7ab627a1f69f7696efe41759c5d06e3109269b0e999bfc703620bb10",
      "symbol": "get_rule",
      "type": "rule"
    }
  ],
  "extraction": {
    "evaluator_config_sha256": "97ffe2b6529dd2f5bca6e9aeec22f46c3a655ec2912902fadb5b4bbff30553dd",
    "method": "Python AST and immutable task JSON; no evaluator code executed",
    "official_commit": "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
  },
  "list_mode": false,
  "metric_options": null,
  "metrics": [
    {
      "name": "check_thunderbird_prefs",
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "slot": 0,
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "source_sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827"
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
      "packet_path": "official/desktop_env/evaluators/metrics/thunderbird.py",
      "sha256": "04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827",
      "source_ref": "https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py",
      "upstream_path": "desktop_env/evaluators/metrics/thunderbird.py"
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
      "config_sha256": "7322e43822c97bc02e7125b08ff0d996132a8083bd7678adac8c8e308791744f",
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
  "task_id": "3f28fe4f-5d9d-4994-a456-efd78cfae1a3"
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

### `import:json` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L1-L1`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `261a9112a2918e2aba03e19a2f221a027ab4b6f9e946a6c39814f54e18e07dfc`

```python
import json
```

### `import:logging` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L2-L2`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `c03077efc85657ff1627da1b315658097fb9277b30042c8e14b5257057aa9652`

```python
import logging
```

### `import:re` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L3-L3`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `import:Dict` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L4-L4`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `d302f7bc3bed2a644bf67167ab809b01dc4139c783a2105412e92aa7d3c43173`

```python
from typing import List, Pattern, Dict, Match
```

### `import:Any` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L5-L5`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `bdd1ef6bf23562ebfb90a40863c04bb9443d3825b990fa3fc7abedd71e86059f`

```python
from typing import Union, Any, TypeVar, Callable
```

### `logger` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L10-L10`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `02bb8ed3b5a788893ac0b3bfcb70e5dfe18643db6027bac46d4ed004e5ddae41`

```python
logger = logging.getLogger("desktopenv.metric.thunderbird")
```

### `_pref_pattern` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L14-L14`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `663034468155d90d4be748a3365b0e89a373b2a0b46010948f8a3fdb6c5d6a89`

```python
_pref_pattern: Pattern[str] = re.compile(r'^user_pref\("(?P<key>(?:[^"]|\\")+)\", (?P<val>.+)\);$');
```

### `check_thunderbird_prefs` from `official/desktop_env/evaluators/metrics/thunderbird.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/thunderbird.py#L17-L67`

Full source SHA-256: `04d49c42b0690498a7513c67cfa62331dff83b2d5dbada881841780d1d2cf827`

Exact excerpt SHA-256: `4f881f23ac2db41464a1c413531c899605d69eb65eb3438d35bb9cb35faeacab`

```python
def check_thunderbird_prefs(result: str, rule: Dict[str, Dict[str, Dict[str, Any]]]):
    """
    Args:
        result (str): path to result file
        rule (Dict[str, Dict[str, Dict[str, Any]]]): dict like
          {
            "expect": {
                str: {
                    "method": str
                    "ref": something
                }
            }
            "unexpect": {
                str: {
                    "method": str
                    "ref": something
                }
            }
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    expect_rules = rule.get("expect", {})
    unexpect_rules = rule.get("unexpect", {})

    expect_metrics = {k: False for k in expect_rules}
    unexpect_metric = True
    with open(result) as f:
        for l in f:
            match_: Match[str] = _pref_pattern.match(l.strip())
            if match_ is None:
                continue

            key: str = match_.group("key")
            # value: str = match_.group("val")
            # if value in {"true", "false"}:
            # value = value.title()
            # value: V = eval(value)
            value = json.loads(match_.group("val"))
            if key in expect_rules:
                logger.debug("K: %s, V: %s", key, repr(value))
                expect_metrics[key] = _match_pref(value, expect_rules[key])
            elif key in unexpect_rules:
                unexpect_metric = unexpect_metric and not _match_pref(value, unexpect_rules[key])

    return float(all(expect_metrics.values()) and unexpect_metric)
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

### `import:re` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L8-L8`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `a830333312c4c9c2233bb02762bd498203b1c3bf0527614735693b4b79f6d167`

```python
import re
```

### `import:Iterable` from `official/desktop_env/evaluators/metrics/utils.py`

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

### `import:MultiCellRange` from `official/desktop_env/evaluators/metrics/utils.py`

Source ref: `https://raw.githubusercontent.com/xlang-ai/OSWorld/87df18ff0e906dafdb1ea96b8299f35ec1e67e6b/desktop_env/evaluators/metrics/utils.py#L28-L28`

Full source SHA-256: `45aa2e44248a549d1c0462179f9ae0d0429d5077900c7dc1fa447aa0b136c577`

Exact excerpt SHA-256: `63f180054250da329b72f9f846c9875bf8980e9d5c98bd7164a8dc738eb3216c`

```python
from openpyxl.worksheet.cell_range import MultiCellRange, CellRange
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
