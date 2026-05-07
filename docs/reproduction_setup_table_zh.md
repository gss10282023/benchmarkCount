# 复现实验表（按当前仓库配置整理）

这份表是按你当前的说法和仓库现状整理的：

- 原始输入到 `draft`：使用 `<REPO_ROOT>/neurips_ed_track_minimal`
- 证据采集：使用各 benchmark 的 adapter，在 VPS 或本地机器上运行
- `score`：同样使用 `<REPO_ROOT>/neurips_ed_track_minimal`

如果你最后论文里只报告你实际跑过的 benchmark，就删掉未使用的机器角色行即可。

## 1. 复现流程总表

| 环节 | 目的 | 使用包/代码 | 入口命令 | 主要输入 | 主要输出 | 默认配置/模型 | 运行环境要求 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 原始输入 -> `draft` | 从 `case_packet.md` 生成 checklist draft | `neurips_ed_track_minimal` | `make draft CASE_PACKET=... OUTPUT=...` | `case_packet.md` | `checklist.yaml`，`api_response.json`，`llm_call.json`，`reasoning_summary.txt` | `openai/gpt-5.4`，`reasoning-effort=high`，`max_output_tokens=12000`，`temperature=0`，`http_timeout_seconds=180` | 任意可联网 CPU 机器；需 Python 3、`requests`、`PyYAML`、`jsonschema`；需 `OPENROUTER_DRAFT_API_KEY` 或 `OPENROUTER_API_KEY` |
| `draft` 校验/锁定 | 校验 schema 与 guardrails，并冻结 case/checklist 对应关系 | `neurips_ed_track_minimal` | `python scripts/checklist_validator.py ...`；`python scripts/update_case_locks.py --case-packet ... --checklist ...` | `case_packet.md`，`checklist.yaml` | 通过校验的 checklist；`locks/cases.jsonl` 中的锁记录 | 离线校验；无额外模型调用 | 本地 CPU 机器即可 |
| 证据采集（adapter） | 运行官方 benchmark 或诊断 runner，保存原始证据，不做最终 S/F/U 判定 | `src/evidence_system/adapters/` 与 `python -m evidence_system.cli.run_domain` | `python -m evidence_system.adapters.<canonical_domain> ...` 或封装 CLI | `job.json`，benchmark 安装目录，`configs/agents.yaml`，`configs/infra.yaml` | `raw_run_record/v1`，`artifact_manifest/v1`，原始 artifacts，native evaluator 输出，stdout/stderr，LLM call log | Agent 配置来自 `configs/agents.yaml`；adapter 本身不得输出最终 evidence verdict | 按 domain 路由到对应 VPS 或本地机器；可能依赖 docker、benchmark 资产、网络与本地服务 |
| `score` | 用锁定 checklist 对保存的 run artifacts 做最终 evidence scoring | `neurips_ed_track_minimal` | `make score CHECKLIST=... EVIDENCE_DIR=... OUT_PREFIX=...` | `checklist.yaml`，`run_artifacts/` | `score.json`，`score.yaml`，`score_manifest.json`，`score.codex.stdout.log`，`score.codex.stderr.log`，`score.codex.events.jsonl`，`score.codex.telemetry.json`，`score.codex.reasoning.txt` | `gpt-5.4`，`reasoning-effort=xhigh`，`sandbox=read-only`，`max_attempts=2` | 任意本地 CPU 机器；需 Codex CLI 已安装并完成认证 |
| 批量打分/导出（可选） | 对成批 evidence 目录统一打分并导出平面表 | `neurips_ed_track_minimal` | `make score-agentdojo-batch`；`python scripts/export_agentdojo_scores_csv.py` | draft 根目录，evidence 根目录 | 标准化 score bundle；扁平 CSV | batch score 默认 `openai/gpt-5.4`，`reasoning-effort=xhigh`，`per-key-concurrency=4`，`tasks-per-key=100` | 适用于批量实验；需要预先配置 score-only API keys |

## 2. 机器配置表（从 `configs/infra.yaml` 提炼）

| 机器角色 | 典型用途 | 连接方式 | CPU limit | 内存 | GPU | 并发 | Docker | 适用 domain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `other_vps` | 运行大多数通用 adapter | SSH VPS | 8 | 32 GB | 否 | 10 | 是 | `agentdojo`，`appworld`，`tau3_retail`，`workarena`，`judge_only`，`maintenance_update`，`matched_budget_controls` |
| `webarena_vps` | 运行 WebArena / MiniWoB++ 相关 adapter | SSH VPS | 4 | 16 GB | 否 | 3 | 是 | `webarena_verified`，`MiniWoB++` |
| `osworld_vps` | 运行 OSWorld-Verified appendix adapter | SSH VPS | 8 | 32 GB | 否 | 3 | 是 | `osworld_verified` |
| `local_androidworld` | 运行 AndroidWorld appendix adapter | 本地机器 | 4 | 16 GB | 否 | 1 | 否 | `androidworld` |

补充说明：

- `draft` 与 `score` 没有被固定到某个 machine role，上述配置主要约束 adapter 运行阶段。
- 仓库里还有一个 `local_toolsandbox` 角色，但它更偏 smoke/diagnostic，不是你当前这条“draft -> adapter evidence -> score”主链路的必要组成部分。
- `osworld_vps` 的 host/user/path 在当前配置里仍有占位字段；正式复现时应以 locked manifest 为准。

## 3. 可直接放进论文或附录的填写版表格

你可以直接把下面这张表复制到实验设置节，然后把方括号内容替换掉。

| 阶段 | 运行位置 | 机器配置 | 关键软件/模型 | 关键输入 | 关键输出 | 建议在论文中显式报告的字段 |
| --- | --- | --- | --- | --- | --- | --- |
| 原始输入 -> `draft` | 本地机器 | `[CPU 型号]`；`[内存]`；GPU 无需 | `neurips_ed_track_minimal`；OpenRouter；`openai/gpt-5.4`；`reasoning-effort=high`；`max_output_tokens=12000` | `case_packet.md` | `checklist.yaml` 与 sidecar 日志 | OS 版本，Python 版本，包路径，prompt 路径，schema 路径，API provider，模型名，temperature，超时设置 |
| 证据采集（adapter） | VPS 或本地，按 benchmark 分配 | `other_vps: 8 CPU / 32 GB`；`webarena_vps: 4 CPU / 16 GB`；`osworld_vps: 8 CPU / 32 GB`；`local_androidworld: 4 CPU / 16 GB` | `src/evidence_system/adapters/*`；benchmark 官方 runner；Agent A/B/C 配置来自 `configs/agents.yaml` | `job.json`，benchmark 环境，官方数据/资产，agent 配置 | `raw_run_record`，`artifact_manifest`，native evaluator artifacts，trace/logs | VPS 提供商与地域，OS，CPU 型号，docker/conda/venv，benchmark commit/version，adapter commit，domain -> machine role 映射 |
| `score` | 本地机器 | `[CPU 型号]`；`[内存]`；GPU 无需 | `neurips_ed_track_minimal`；Codex CLI；`gpt-5.4`；`reasoning-effort=xhigh`；`sandbox=read-only` | 锁定的 checklist 与保存的 evidence 目录 | `score.json/yaml`，manifest，Codex telemetry/reasoning log | Codex CLI 版本，模型名，reasoning effort，sandbox 模式，打分 prompt 路径，score schema 路径，是否使用 native label override |

## 4. 建议一并报告的 agent 配置

如果你要复现完整主实验，不建议只写机器配置，至少还要把 agent 配置并列出来。

| 角色 | Provider | 模型 | Temperature | Max tokens | Timeout | Retry |
| --- | --- | --- | --- | --- | --- | --- |
| Agent A | OpenRouter | `openai/gpt-5.4` | 0 | 4096 | 120 s | 2 |
| Agent B | OpenRouter | `anthropic/claude-opus-4.7` | 0 | 4096 | 120 s | 2 |
| Agent C | OpenRouter | `deepseek/deepseek-v4-pro` | 0 | 4096 | 120 s | 2 |
| Contract drafter | OpenRouter | `openai/gpt-5.4` | 0 | 8192 | 180 s | 2 |

## 5. 一句话写法

如果你想在论文正文里用一句话概括，可以写成：

> Checklist drafting and final evidence scoring were both run with the minimal package at `<REPO_ROOT>/neurips_ed_track_minimal`, while raw evidence collection was executed through benchmark-specific adapters on benchmark-routed VPS or local machines as specified by `configs/infra.yaml`.
