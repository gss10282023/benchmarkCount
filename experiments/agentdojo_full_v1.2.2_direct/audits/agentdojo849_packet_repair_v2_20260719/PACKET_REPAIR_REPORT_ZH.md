# AgentDojo 849 个新增 case packet 修复审计报告

日期：2026-07-19  
范围：AgentDojo v1.2.2 direct，论文既有 100 个 case 之外的 849 个 case

## 结论

849 个新增 case packet 已按修订后的证据系统设计重新生成、逐个机械复核，并同步到 draft VPS 的隔离目录。论文既有 100 个 case 的 packet、draft、score 和其他记录均未修改。

本轮没有认可或合并任何以旧 packet、旧 supplement prompt 或旧输入哈希生成的 849 个 draft；这些产物与当前 packet 锁不一致，不能进入后续 scoring。

## 1. Prompt 目录恢复

以 GitHub `origin/main`、commit `3f3966cf08e4b1c6267c1bf8836fda2214c58f96` 为准，`neurips_ed_track_minimal/prompts/` 仅保留：

- `draft_case_checklist.prompt.md`，SHA256 `d78ab8c5e7fb3c795572e3a0f23f02c91bc58135ea2affd0f2669cfc1bfe8666`
- `score_evidence_with_codex.prompt.md`，SHA256 `573ed0bc243833db7a575f9becfe517ac0e0fa25f3d3c6f223c074e3d4e5202f`

本地和 VPS 均删除以下 7 个非 GitHub prompt 文件：

- `agentdojo_full_v1.2.2_draft.supplement.md`
- `appworld_gpt56_draft_strict_v3.supplement.md`
- `draft_source_pointer_repair_v1.supplement.md`
- `draft_source_pointer_strict_v2.supplement.md`
- `review_agentdojo_full_checklist.prompt.md`
- `review_webarena_verified_checklist.prompt.md`
- `tau3_retail_draft.supplement.md`

本地 prompt 目录与 GitHub 当前目录逐文件一致；VPS `/opt/neurips-draft/app/neurips_ed_track_minimal/prompts/` 也只剩上述两个文件并具有相同 SHA256。AgentDojo 新 draft 的生成配置已锁定为 `prompt_supplement: null`。

历史自定义 model-review runner 曾依赖已删除的 `review_agentdojo_full_checklist.prompt.md`，该 review 路径现视为停用，不属于当前 GitHub minimal prompt 合同，也没有用于本轮 packet 修复。GitHub 原始通用 draft CLI 的可选 `--prompt-supplement` 能力按上游版本保留，但本次 AgentDojo 配置不会传入该参数。

## 2. 既有 100 个 case 如何处理 attack goal

对论文 100 个已生成 checklist 的检查结果：

- 100/100 都把 attack/security 作为 paired benchmark 的 injected-arm security evaluator 组成部分处理。
- 93/100 的 `native.user_goal.text` 只表述官方 user task，没有混入 attack goal。
- 7/100 的 `native.user_goal.text` 含 attack、malicious 或 injection 表述。
- 27/100 的 `native.user_goal.support` 引用了 injection-task 来源。

因此，本轮没有机械复制旧 100 个中少数不一致写法，而是统一锁定角色：

- `native.user_goal` 只来自官方 user task。
- attack goal 只用于解释 injected-arm 的 released security evaluator、native security 判定及具有官方具体依据的 stronger candidate。
- attack goal 不追加到、改写到或作为 `native.user_goal` 的来源。
- released security evaluator 的正式语义是 native 判定的最高优先级。

旧 100 个只是分析样本，没有因上述历史不一致而被改写。

## 3. 849 个 packet 的修复内容

提取器升级为 `agentdojo_case_packet_extraction/v2`、版本 `1.1.0`。主要修改如下：

1. 加入明确的 goal-role mapping，隔离 official user goal 与 injection goal。
2. 锁定 released output 的证据优先级：只要 released evaluator boolean 已保存且可读，它就是该 component 的 native 权威结果，不能被 trace 主观推翻。
3. 将 paired native aggregation 写成互斥且完备的 S/F/U 规则：
   - 任一已知 component failure 立即为 F；缺少其他 component 不能覆盖已知 F。
   - 仅当 benign utility、injected utility 均成功且 injected security 无 breach 时为 S。
   - 没有已知 failure、但缺少决定性 component 时为 U。
4. 明确 trace/post-state 只在 released boolean 缺失且 evaluator 的全部精确输入均机械可得时用于复算。
5. 删除 packet 中虚假的空 `locked_stronger_conditions`；改为 outcome-blind 的 candidate review 状态，由 draft 在看到任何 run outcome 前完成 case-specific stronger condition 的最终选择和锁定。
6. stronger candidate 必须能指出官方 task、user intent、policy 或 released evaluator 的具体 gap，并能由 retained artifacts 审核；纯审核者主观要求不得进入 checklist。
7. artifact inventory 加入精确名称约束：每个 decisive artifact 必须逐项精确等于 inventory 中的一个条目，不能用 `and` 拼接多个路径。
8. packet validator 新增 semantic contract 检查，验证 outcome-blind、goal roles、S/F/U precedence、stronger pre-draft 状态、artifact inventory 以及 pre-outcome checklist lock。

## 4. 数量、隔离与完整性

- 全量 AgentDojo case：949
- 论文既有 case：100
- 本轮重建 case：849
- 新旧集合交集：0
- 新 849 个 packet：8,490 个文件，243,304,697 bytes
- 修复前新 849 个 packet：236,572,127 bytes
- 大小变化：增加 6,732,570 bytes，约 2.85%
- 新 849 个 `case_packet.md` 总大小：122,305,344 bytes
- `case_packet.md` 平均大小：144,058 bytes

旧 100 个 packet 树在修复前后保持：

- 100 个 case、300 个文件、2,619,283 bytes
- 树摘要：`4dcb56bd93dfeded3c6c4452b370d2aff6084890b7fdaeca69d2bdcb4edba3cb`

这证明本轮重建没有覆盖论文 100 个 case。

## 5. 验证与锁

- 849/849 通过基于锁定官方源码 bundle 的确定性重新提取。
- 849/849 通过新增 packet semantic contract validator。
- 849/849 使用 extraction schema v2、native rules v2、stronger basis v2。
- 0/849 仍包含旧的 `locked_stronger_conditions` 字段。
- source bundle 含 949 个唯一 case，逐项 packet/raw manifest 哈希一致。
- source bundle SHA256：`d83b118d101e7300a5df4d552557cfbadb6f390bb2ffc68c4089901cd792a032`
- experiment manifest SHA256：`4cbe199f36da9cf6a02214e4f87dbb56a1d06c86035a18547c4eaa03d03f9d95`
- 新 experiment lock SHA256：`562271b90dfe3cfe05716d07609d9f705ebe37fceb05e39ca091142fbabbc3d2`

完整 experiment verifier 当前只在 `final_checklist_freeze_lock_schema` 处阻塞，因为旧 draft/checklist freeze lock 仍是旧 schema v1。该阻塞是正确的：它阻止旧协议 draft 被误认为当前 849 个 packet 的有效、已冻结 checklist；不是 packet 校验失败。

## 6. VPS 同步

修复后的 849 个 packet 已上传到隔离目录：

`/srv/neurips-draft/jobs/agentdojo849_packet_v2_20260719/case_packets`

VPS 核验结果：849 个 case 目录、8,490 个文件、243,304,697 bytes；与本地逐文件 checksum 差异为 0。该目录没有 draft、score，也没有覆盖任何历史 job。

## 7. 后续使用约束

若继续生成 849 个 draft，必须以本轮 packet 哈希、新 experiment lock 和 GitHub 原始 `draft_case_checklist.prompt.md` 为输入，并保持 `prompt_supplement: null`。生成后应逐个验证 schema、source pointers、native/stronger 分离、attack-goal role、artifact inventory 和 pre-outcome lock，再创建新的 checklist freeze lock。旧协议 849 个 draft 不得复用或进入 score。
