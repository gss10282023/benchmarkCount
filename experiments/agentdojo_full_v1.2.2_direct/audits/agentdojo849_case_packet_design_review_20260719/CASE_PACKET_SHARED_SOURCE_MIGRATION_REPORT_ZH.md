# AgentDojo 新增 849 个 case packet：共享官方源码束迁移报告

## 结论

已按“完整官方源码只归档一次、逐 case 只保留相关摘录和机械规则”的方案完成实现，并严格只重建完整 949-case catalog 与受保护旧 100-case 集合之差，即 849 个新增 case packet。

- 新增 849 个 packet：逐 case 写后审计 `849/849 PASS`。
- 受保护旧 100 个 packet：仍为 300 个文件、2,619,283 字节，写前/写后对象树摘要均为 `33fc00cb0e52083412d1077e330c9684065ba1a338ab0793edc60cf2394507b2`。
- 受保护旧 100 个 draft：仍为 2,818 个文件、21,016,844 字节；本次未生成、删除或改写任何 draft。
- 本次没有运行 AgentDojo benchmark，没有调用 draft 生成，也没有调用 `neurips_ed_track_minimal` score。

## 修改了什么

### 1. 增加独立、只读的完整官方 source bundle

新增共享目录：

`experiments/agentdojo_full_v1.2.2_direct/source_bundles/agentdojo_v0.1.35_official_source/`

它从已锁定的 AgentDojo 0.1.35 发行包 RECORD 机械收集全部 `agentdojo/*` 官方源码和数据文件，排除 `__pycache__`、`.pyc` 等生成物。

- 官方 tag：`v0.1.35`
- Git commit：`a75aba7631d3ca5fb7ab938965c97ead2f9ff84b`
- Git tree：`3c74b60f2bad4ff321d864e0c0483f256cc8f8d2`
- wheel SHA256：`364bea4219716b716bf639f504d195943f7f6a5535d312ca41d7098704a2affd`
- 官方文件数：112
- 官方文件总字节数：792,036
- source tree SHA256：`01dd77983113287ca62b8156e5b64e8ef38f1d61c15783e7f3a64aea1730fc09`
- source manifest SHA256：`af919cdf895d93ca5899fe9931965291c4a0085fad9452ede59f634650d67d2c`
- 只读检查：112 个文件和 manifest 的写权限均为关闭状态。

### 2. 每个新增 case packet 改成固定的 8 文件 compact 结构

每个新 packet 的 `raw_case/` 只包含：

1. `official/case_definition.json`
2. `official/evaluator_oracle_excerpts.json`
3. `official/state_schema_excerpts.json`
4. `derived/native_decision_rules.json`
5. `derived/stronger_measurement_basis.json`
6. `derived/artifact_inventory.json`
7. `derived/checklist_basis.json`
8. `derived/extraction_manifest.json`

不再在每个 case 下复制 `official/src/agentdojo/**`，完整源码也不再全文进入 `case_packet.md`。

### 3. 机械提取并锁定逐规则 provenance

提取器从选定 user task、injection task、组合 task 依赖、released evaluator/oracle、runner dispatch 和必要 state/tool schema 中抽取精确源码切片。

每条 native rule 以及官方 goal/oracle、stronger candidate 均保留：

- 官方源文件；
- 函数或字段；
- tag、commit、git tree；
- 源文件 SHA256 和摘录 SHA256；
- 起止行号与起止字节；
- packet 内 JSON pointer；
- 锁定 commit 上的精确源码 pointer。

849 个 packet 共核验 20,078 条唯一源码摘录和 20,496 条逐规则 source binding，未发现 identity、pointer、hash 或 span 错误。

### 4. stronger 条件采用保守、非主观的两阶段锁定

每个 case 都保存官方 user goal 与 injection goal 作为 source-grounded candidates，但 `locked_stronger_conditions` 当前保持为空。

原因是“官方文本与 native evaluator 是否存在语义非覆盖”不能仅靠字符串差异可靠判定；自动把 goal 文本直接升级为 stronger 会违反“不凭审核者主观判断增加条件”的设计。candidate 只有在后续 outcome-blind semantic native-noncoverage review 有明确官方依据时，才能进入锁定 stronger checklist。849/849 均满足该边界。

### 5. validator 改为 fail-closed

validator 现在同时执行：

- 共享 source bundle 的完整文件集合、文件 SHA256、tree SHA256、commit/version 和只读状态检查；
- 安装中的 pinned AgentDojo 与共享 bundle 的逐文件一致性检查；
- 每个源码摘录按起止字节回切共享源码并复算 SHA256；
- 每个 case 的 8 个文件重新确定性提取，并与 materialized 文件逐字节比较；
- raw manifest、packet source bundle 和运行时 install-source lock 的兼容检查。

最终确定性重提取审计为 `849/849 PASS`；新格式和旧 100-case 格式的 benchmark runtime source lock 均抽测通过。

### 6. 更新 draft/review 输入约定和实验定义锁

AgentDojo draft supplement、checklist model-review prompt 和 pointer resolver 已切换到新的 compact 路径，同时保留旧 100-case 路径兼容性。

全量 source-bundle 索引和 experiment lock 已刷新：

- 949-entry case-packet source bundle SHA256：`2a22f6766db2e347720ba656f22a6bd19904481a8f58cd3a8438ac2e251bff47`
- experiment manifest SHA256：`2472cdac33a3dde2aac00306436d0f4c03ed7fe7a6d679917f4253913f1645d3`
- experiment lock SHA256：`fb5fc07675d931d17b201eaad653d139f868a5f5759ac786a4abf43fb46c083c`

旧 100 条 source-bundle entry 的前后对象摘要均为 `2a2e5fe4ce23c4bf1d936ca837274687c7d7c618d6307ac94ea5635121bc97c6`，内容未变。

## 为什么这样修改

旧结构把大范围官方源码递归复制到每个 case，并再次全文嵌入 `case_packet.md`。这虽然提供了 source closure，但导致 849 个 packet 约 464.9 MB，且模型输入中存在大量与单个 case 无关的重复源码。

新结构把“完整性”和“模型最小输入”分开：完整官方源码由一个共享、只读、hash-locked bundle 保证；逐 case packet 只携带与当前 case 有关的精确摘录和机械派生规则。validator 将二者绑定，因而减少重复内容的同时，不牺牲可追溯性或 evaluator/oracle 的正式语义优先级。

迁移后 849 个目录共 8,490 个文件、236,572,127 字节，较旧结构约减少 49.1%。其中 raw case 为 113,897,859 字节，Markdown 为 118,939,059 字节；剩余部分是逐 case manifest。Markdown 仍包含 compact 的 8 个文件供模型使用，但不包含完整官方源码全文。

## 未修改及后续边界

- 未修改旧 100 个 draft、旧 benchmark 运行记录或 score 记录。
- 未重建 `lock/draft_input_lock.json`、`jobs/full/**` 或旧 `provenance/acceptance_report.json`；它们属于后续 draft/run 生命周期，并且当前相对于新 packet/source-bundle 已是历史快照，不能被当作本次迁移后的新验收凭据。
- 在运行 benchmark 之前，应先完成 candidate 到 locked stronger condition 的 outcome-blind 语义审核，并生成新的 checklist/draft input lock；该审核不得读取 agent outcome。
