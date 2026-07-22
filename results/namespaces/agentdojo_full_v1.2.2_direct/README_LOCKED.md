# AgentDojo v1.2.2 direct：完整 949-case 运行产物（锁定归档）

本目录是 AgentDojo v1.2.2 direct-attack 实验的规范本地运行产物归档，明确由以下两部分组成：

- 论文原有 100 个 case：100 cases × Agent A/B/C = 300 份运行产物；
- 去除论文 100 个 case 后剩余的 849 个 case：849 cases × Agent A/B/C = 2,547 份运行产物。

合计：949 cases × 3 agents = 2,847 份运行产物，统一平铺在 `full/agentdojo/`。

## 来源

- 论文 100：`results/full/agentdojo/`（仅纳入 300 个正式运行目录，不纳入 `drafts/`、`draft_runs/` 或 `.DS_Store`）；
- 剩余 849 / VPS1：`results/namespaces/agentdojo_remaining_849_v1.2.2_direct_vps1/full/agentdojo/`；
- 剩余 849 / VPS2：`results/namespaces/agentdojo_remaining_849_v1.2.2_direct_vps2/full/agentdojo/`。

三个来源目录均被保留，合并过程未移动或修改来源文件。论文 100 与剩余 849 的 case 集合严格互斥；剩余 849 的定义来自 campaign manifest 中的精确集合差：`full_949_case_packet_dirs_minus_paper_100_case_packet_dirs`。

## 索引与完整性

- `indexes/paper_100_cases.txt`：论文 100 个 case；
- `indexes/remaining_849_cases.txt`：剩余 849 个 case；
- `indexes/all_949_cases.txt`：完整 949 个 case；
- `indexes/paper_100_runs.txt`：论文 100 对应的 300 份运行；
- `indexes/remaining_849_runs.txt`：剩余 849 对应的 2,547 份运行；
- `indexes/all_949_runs.txt`：完整 2,847 份运行；
- `SOURCE_MAP.tsv`：每份运行产物的来源映射；
- `CHECKSUMS.sha256`：`full/agentdojo/` 下所有文件的 SHA-256；
- `LOCK_RECEIPT.json`：计数、来源、校验和及锁定方式的机器可读收据。

## 锁定

完成验证后，本归档会同时移除写权限并设置 macOS `uchg` immutable flag。需要维护时必须显式解除两层锁；不得直接修改归档中的文件，应从来源重新构建并生成新的锁定收据。
