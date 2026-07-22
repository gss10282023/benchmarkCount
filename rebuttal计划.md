# NeurIPS 2026 E&D Rebuttal 计划与 Post-rebuttal 路线图

> 版本：v1.10（Step 4A 缩减为投稿时 AndroidWorld 100 题清单存在性核验） 修订日期：2026-07-15（Australia/Sydney） 适用论文：*Can Agent Benchmarks Support Their Scores? Evidence-Supported Bounds for Interactive-Agent Evaluation* 执行起点：从论文提交时 commit/tag/archive 新建的干净仓库；不以当前已运行 full100、表格重建或重审的已改仓库作为执行基线。范围边界：Step 0–18 是当前 rebuttal 工作；Step 19–24 是 rebuttal 后工程，不得写入当前 author response，也不得反向描述为原提交结果。本文件为内部计划；任何将粘贴到 OpenReview 的文本必须另行生成并通过 Step 15 的 lint。

---

## 0. v1.9 → v1.10 变更清单

1. **缩减 Step 4A。** 只核对冻结匿名制品提交中是否已有确定的 AndroidWorld 100 题清单；删除 41 题抽取方式、是否先看结果、\$250 停止口径和 USD 370.91 费用构成的调查。
2. **Step 4A 已通过。** 冻结匿名制品 commit `ffd9ff4e…` 含有精确 100 个不重复 case IDs 的 manifest；投稿 AndroidWorld 41 题全部位于该清单中。后续 Step 4B 原样复用该清单。
3. **收窄对外说法。** 只声称“冻结匿名制品提交中已包含该 100 题清单”；不用 manifest 内部 `created_at` 单独推断更早的冻结时间，也不声称它一定早于 outcome inspection。

### 历史参考：v1.8 → v1.9 变更清单

1. **正式锁定 Step 2 的两份投稿来源。** `SUBMISSION_ARTIFACT_SOURCE` 为匿名制品提交 `ffd9ff4e…`，提供 1,282 条原始记录及原生/证据标签；`SUBMISSION_PAPER_SOURCE` 为论文源提交 `35b962c8…`，提供论文打印值、最终审核标签/条目和表格文字。两者均冻结并记录完整 commit/tree/file hashes；不得使用提交后的已改仓库补数字。
2. **取消“仅靠匿名制品分支”的字面要求。** Step 2/G2 的正式验收口径改为从上述两份冻结投稿来源和固定脚本精确重建五张投稿表；匿名制品分支缺少审核台账不再构成范围矛盾。
3. **把双作者签字写成可执行记录。** 两位作者可以使用同一台物理电脑，但必须各自在相互独立的干净目录亲自运行同一命令，并各自记录作者代号、时间、两份来源的 commit/tree hash、环境、命令、退出码、验收报告状态、`SHA256SUMS` 文件摘要及“未手改/未复制生成结果”的声明；比较报告确认两次来源与输出摘要一致后，Step 2/G2 才可整体标记完成。
4. **Step 2/G2 已完成。** A1/A2 均在独立验证目录完成交互签字并给出 `APPROVE`；两次 `verification_report=PASS`，无 checksum failure，来源 hashes 与 `SHA256SUMS` 摘要完全一致（`f33bbedd…`）。签字比较报告为 `PASS`；可选 2-O 标记 `skipped`，不阻塞 G2。

### 历史参考：v1.7 → v1.8 变更清单

1. **取消独立 Step 3。** 复核确认 B5/I5 的最终任务证据失败、发布评估器成功、C5 conflict 与 stronger-measurement finding 可以同时成立，不构成 taxonomy 矛盾；不重跑 B5/I5、不重分类、不重算 Table 2，也不引入 `q_E/q_S/q_+` 专项框架。
2. **迁移仍有效的核验工作。** 投稿打印的 32 条 conflict 的逐条来源、核验状态及 records / case units / mechanisms 三种计数移入 Step 8A；全文术语与表格一致性检查移入 Step 14。各机制的可执行复现保留在 Step 8B。
3. **保持投稿终审结果。** AgentDojo `195/55/50 → 191/59/50` 是人工终审将四条任务未完成记录从临时 `S` 纠正为最终 `F` 的结果；不撤销这些修正。Table 6/13 的 AgentDojo conflict 标记保持独立。
4. **取消预设的“双轨 taxonomy”。** 只有 Step 8A 的逐条核验实际发现应撤销、新增或降级的 conflict 时，才分别报告投稿打印值与提交后核验值；不得预设一定存在“纠正后的 taxonomy”。

### 历史参考：v1.6 → v1.7 变更清单

1. **取消 2-O 的来源禁令。** 可使用直接历史原件、结构化推断、post-submission AI 重审、`MobileRisk_offline_20260607T003138Z.tar.gz`、`conflict_readmes.zip` 及其他可追踪资料来恢复或补充历史审核信息。
2. **改用证据层级而非排除方法。** 每个恢复字段标记 `DIRECT_SOURCE`、`ARCHIVE_SUPPORTED`、`INFERRED`、`POST_SUBMISSION_REAUDIT` 或 `NOT_RECOVERED`，并保留来源、方法和置信说明。
3. **G2 边界不变。** 2-O 仍是可选项；五张表重建不等待 2-O，2-O 的恢复方法或覆盖率不影响 G2。

### 历史参考：v1.5 → v1.6 变更清单

1. **保留 Step 2 的必做主线。** 先从投稿时仓库重建 Table 2/3/6/9/13 及 cell-level lineage；G2 只对这一主线验收。
2. **恢复历史审核过程为可选项。** 若五张表重建不受影响且时间充足，可选恢复 R1/R2 逐 case 判断、reviewer 身份/时间戳、分歧解决与 final adjudicator metadata；v1.7 将可用来源扩展为多源证据。
3. **可选项不影响 G2。** 恢复不完整时，该可选项标记 partial/skipped。

### 历史参考：v1.4 → v1.5 变更清单

1. **Step 2 改为表格重建任务。** 第一目标是仅使用论文提交时仓库的冻结输入和固定脚本，重建 Table 2/3/6/9/13 及其 cell-level lineage。
2. **历史审核过程曾从 G2 必交付项中移出。** v1.6 将它作为不阻塞 G2 的可选恢复项，而非删除。
3. **表格重建与历史恢复分轨。** 投稿仓库中已存在的 final label / correction / conflict 标记作为表格重建输入；2-O 可使用多源证据恢复或推断人员、时间与审核过程，并单独标记证据层级。Step 6/7 如执行，是新的 post-submission 抽样验证。

### 历史参考：v1.3 → v1.4 变更清单

1. **重置执行基线。** 下一轮实际工作从论文提交时仓库的干净 checkout 开始；当前已修改仓库仅可作为隔离的只读参考，不得直接成为结果源、完成性证据或提交基线。
2. **新增 AndroidWorld 执行步骤。** 从已公布的 41 cases × Agent A/B（82 slots）出发，扩展到同一 official 100-case universe，对 Agent A/B/C 全部测试（300 slots）。相对提交基线新执行 218 slots：A/B 各 59，C 100。
3. **拆分运行与审核。** Step 4B 专门负责 41→100 与 A/B/C 的可复现执行；新增 Step 4C 负责统一 scoring/adjudication 和 41/59/100、A/B/C 对照；Step 5 作为三 agent 横向可比性与报告门。
4. **所有原划掉步骤恢复为待执行。** 本版不再使用删除线表示“已完成”；仅当步骤在新建的提交时仓库 checkout 中重现并通过验收，才可在 `STATUS` 中标记 complete。
5. **重置 AndroidWorld 数字口径。** submitted universe 仍为 1,282 records；目标 post-submission universe 为 1,500 records（其他四 benchmark 的 1,200 + AndroidWorld 的 300）。当前已改仓库中的 A/B 100/100、C 99/100、raw P/F/U 和重审数字均不再是本计划的先验或验收输入。
6. **保留 v1.3 的其他硬边界。** 容量先行、表格重建关键路径、主动披露、盲化人工验证、reviewer 索码应急包、英文 evidence bank、数字单一来源与 Part II 边界继续有效。

### 历史参考：v1.2 → v1.3 变更清单

1. **新增 Step 0.5（容量预算与样本量锁定）。** v1.2 的 P0 总量（尤其 Step 6 的 300 双标 + 高风险全集）对两人团队在 9 天内大概率不可行；所有样本量与覆盖承诺必须先定容、预冻结，杜绝中途无记录缩水。
2. **Step 2 曾被定义为 ledger 关键路径单点。** 该历史决定已被 v1.5 取代；当前 G2 只检查 Table 2/3/6/9/13 的可重建性，不检查历史 reviewer-process metadata 是否齐全。
3. **Step 4 拆分为 4A / 4B。** 该版对 4A 的宽口径历史定义已被 v1.10 取代；现行 4A 只核验投稿制品中的 100 题清单。4B 继续负责 41→100 与 A/B/C 执行。
4. **新增"主动披露政策"（工作原则）。** 论文对已做实验的事实性描述与实际不符（如 rerun 范围）→ 在最相关回复中主动、简短、事实性更正；措辞不精确 → 进 camera-ready change log。禁止隐瞒可验证的不一致，也禁止无差别倾倒内部瑕疵。
5. **Step 6 修订。** 样本量由 Step 0.5 定容（300/150/100 三档预案）；高风险"全集双标"改为"分档队列 + 预冻结截断线"；"独立人工验证"改为诚实措辞 "label-blinded re-annotation by the two authors under a pre-registered protocol"；两人团队的裁决协议改为规则裁决 + 保留 unresolved disagreement。
6. **新增 reviewer 索码应急包（Step 14）。** v1.2 只"评估打包脚本但不发布"，存在缺口：若 7/28 有 reviewer 索码，须能 24h 内经 AC 分享一个 secrets-clean 匿名 bundle。注意提交稿本身已印 GitHub org 链接，reviewer 在 7/22–8/10 随时可能访问，repo 卫生贯穿整个窗口。
7. **Step 14 新增三份 mock reviews 与数字格式 lint；新增一致性必查项**：AppWorld pool 论文 167 vs 本地 168 test\_normal；Table 1 全部 pool→selected 与本地 manifest 对照。v1.10 已从现行范围删除 AndroidWorld 费用追溯。
8. **Step 15 全部 block 改为英文起草**；扩展 Android 新实验 block 与安全事件应答；新增 Block 11（主动更正汇总）与每个主 block 的"降级版本"（结果不利/未完成时的诚实收缩措辞，与主版本同时冻结）。
9. **Step 16 新增第 0 项**：7/22 当天 2 小时内实测 OpenReview 机制（字符上限、附件/链接、general response 位、initial meta-review 可否回复），实测优先于本计划第 2 节。
10. **Step 8B 新增版本可得性契约。** τ³-bench 为 2026 research release，若官方 evaluator 实现不可公开获取，复现测试降级为"released package artifacts + retained evaluator I/O"并明确措辞。
11. **Step 9 新增可选 canary 合成注入敏感性（P1）**，明确标注 synthetic。
12. **Step 11 预定义 bootstrap 汇总统计与阈值语言**（separation retention rate），禁止看结果后选指标。
13. **角色表改为职能表**，允许一人多职，保留"数字生成者 ≠ 核对者"底线。
14. **明确 MVP 底线交付集与全局丢弃顺序**（第 9 节）。
15. **Part II 完整收录**（Step 19–24 全文），并新增 II.0 启动前重估与许可核验（预算重估、接收/拒收两情景规划、版本与许可可得性），作为 Part II 总启动门。
16. **统一数字格式规则**：所有百分数/区间由 master table 格式化函数输出（百分数保留一位小数），任何 block 不得手工改写数字。

---

## 1. 总目标与工作原则

rebuttal 的现实目标不是把论文包装成"稳接"，而是消除最可能导致拒稿的可验证问题：

1. 证明最终 Evidence Pass / Fail / Unknown 标签和 conflict 分类可信；
2. 证明论文 Table 2/3/6/9/13 可从投稿时冻结记录与固定脚本精确重建；
3. 将 benchmark conflict 从主观案例升级为 pinned-version、可执行复现的 failure mechanism；
4. 明确 sample-conditional identification、sampling uncertainty、specification conflict 和 stronger-measurement finding 的关系；其中 stronger-only 仅指未同时构成 conflict 的项目，conflict 与 stronger-measurement finding 可以并存；
5. 先确认冻结匿名制品中已有的 AndroidWorld 100 题清单（4A，已完成），再从已公布的 41 cases × A/B 出发，在干净的提交时仓库中执行 official100 × A/B/C（4B）；
6. 对 300 个 AndroidWorld slots 使用统一的 scoring/adjudication 口径，完成 submitted41 / remaining59 / full100 及 A/B/C 对照（4C/5），并始终将新运行标为 post-submission；
7. rebuttal 结束后增加 WebArena-Verified 与 OSWorld-Verified 全量实验并重写七 benchmark 分析（Part II）；
8. 消除匿名、凭证、artifact hygiene 和回复格式方面的程序性风险。

工作原则（v1.10 统一版）：

* **执行仓库锁定。** 先新建并 hash 论文提交时仓库（`SUBMISSION_REPO`）；当前已改仓库（`LEGACY_MODIFIED_REPO`）隔离、只读，不从其复制结果来填补新执行。
* **提交基线与提交后结果隔离。** 分表、分目录、分 hash；已公布 41×A/B 保持字节不变，新执行 218 slots 只进 extension 分区。
* **过程先冻结，结果后揭盲。** 抽样、seed、标注规则和分析脚本不得根据结果临时调整。
* **"验收完成"不等于"结果漂亮"。** 过程合规即完成；结果不利时如实报告并收缩 claim。
* **单一数字源。** 所有回复数字来自同一份 locked master table，且仅经其格式化函数输出。
* **报告字段相互独立。** 最终任务证据结果、发布评估器结果、stronger-measurement finding 与 benchmark conflict 分列记录；conflict 与 stronger finding 可以并存，共现本身不触发重新标注或重算 Table 2。
* **不静默修改提交快照。** 安全修复先咨询 chairs；科学内容不得伪装为 deadline 前已存在。
* **最终回复无链接、无附件、无身份信息。**
* **容量先行（新增）。** 任何抽样/覆盖承诺必须先经 Step 0.5 定容；如需缩水，必须书面改版、注明"预冻结修订、未看结果"并留时间戳。
* **主动披露政策（新增）。** material misstatement → 主动、简短、事实性更正，放在最相关的回复中；措辞不精确/可澄清 → camera-ready change log，被问才展开。判据：该表述是否会改变读者对"实际做了什么实验"的理解。
* **语言与格式统一（新增）。** evidence bank 与全部回复以英文起草；数字格式由格式化函数统一；同一数字在任意两个 block 中的写法必须逐字一致。

---

## 2. 官方规则与硬边界

截至 2026-07-12 的已知要点（沿用 v1.2）：

* 2026-07-22：reviews 与 initial meta-review 向作者开放；
* 2026-07-22 至 07-27：撰写并提交逐条 initial rebuttal；initial 阶段 reviewer/AC 不可见作者回复，07-27 rolling discussion 开始后可见并互动；
* 2026-07-27 至 08-03：作者、reviewer、AC rolling discussion；08-03 至 08-10 为 reviewer+AC 内部讨论；
* 每条 review 的 rebuttal 独立上限 10,000 characters；可在文字中报告新结果，但原始投稿仍是推荐依据；
* 不能上传 revised paper / supplement / 附件；author response 不得放链接；仅当 reviewer 明确索要代码时，经 Official Comment 向 AC 提供匿名链接；
* E&D 默认双盲；回复及相关 artifact 持续匿名。

**待实测项（新增）：** 上述字符上限、附件/链接规则、general response 位、initial meta-review 可回复方式，均在 7/22 reviews 开放后 2 小时内由 compliance editor 在 OpenReview 实际表单上核验（Step 16 第 0 项）；实测与本计划冲突时以实测为准。OpenReview invitation 时间戳优先于本文日期。

官方来源（同 v1.2）：E&D Reviewing Guidelines / Main Track Handbook / E&D FAQ / E&D CFP / NeurIPS 2026 Dates / 2026 Area Chair Pilot blog。

---

## 3. 重置后的执行基线与必须解决的风险

### 3.1 两个严格分离的结果宇宙


| 结果层 | AndroidWorld | 其他四个主 benchmark | 总记录数 | 对外称呼 |
| --- | ---: | ---: | ---: | --- |
| 提交基线 | 41 cases × A/B = 82 | 4 × 100 × A/B/C = 1,200 | 1,282 | submitted results |
| 目标扩展 | 100 cases × A/B/C = 300 | 不变 | 1,500 | post-submission analysis |

* AndroidWorld 从已公布 82 slots 扩展到 300 slots：保留 submitted41 × A/B；新运行 remaining59 × A/B（118 slots）和 full100 × C（100 slots），共新增 218 slots。
* 执行开始时不预设 A/B/C 的 full100 完成数、released success/fail、P/F/U、conflict 或 scorer 敏感性数字；这些只能由 `SUBMISSION_REPO` 中的新执行产生。
* `LEGACY_MODIFIED_REPO` 中的 full100 产物可在新结果冻结后做差异诊断，但不可预先复制、挑选、补槽或反向决定 case list、retry 与审核规则。

### 3.2 风险清单（v1.9 重排）

0. **执行基线污染（新增，最高优先）。** 当前已改仓库包含 post-submission 运行、脚本、ledger 和重审决定；若直接从它继续，无法清楚区分 submitted 事实、新实验与看过结果后的决定。→ Step 1 先建干净 `SUBMISSION_REPO`，隔离旧仓库。
1. **AndroidWorld 100 题清单来源（已解决）。** Step 4A 已确认冻结匿名制品 commit `ffd9ff4e…` 中有精确 100 个不重复 case IDs 的 manifest，且已公布 41 题全部属于该清单。Step 4B 必须原样复用该清单。
2. **论文主表采用两份冻结投稿来源。** Step 2 已使用匿名制品提交 `ffd9ff4e…` 与论文源提交 `35b962c8…` 完成五表重建、cell-level lineage、自动验收和双作者独立 hash 签字；G2 已通过。历史 R1/R2 过程按可选子项 2-O 标记 `skipped`，不影响完成性。→ Step 2 已完成。
3. **raw 与论文终审值的 lineage。** AndroidWorld 19/26/37→13/28/41、AppWorld 208/91/1→220/80/0、AgentDojo 195/55/50→191/59/50、MiniWoB 120/168/12→118/182/0 均按投稿时 final label/correction 重建；其中 AgentDojo 的四条 `S→F` 是任务主张未满足后的人工终审修正，不是错误覆盖。τ³ “10 corrections 但 aggregate 不变”的投稿口径说明已在 Step 2 冻结；仍需在 Step 14 核对 AgentDojo Table 9 `corrected=0` 与审核汇总中 3 个 grouped corrections 的单位/含义差异。
4. **投稿 conflict 总数仍需证据核验。** Table 6/13 打印的 32 条是投稿时计数，不预先等同于 32 条已确认冲突；Step 8A/14 必须逐条核对来源与当前核验状态，并区分 affected records、unique case units 和 distinct mechanisms，尤其核验 τ³ 的 24 条。B5/I5 不再列为 taxonomy 风险。
5. **rerun 声明不一致**：论文写 per benchmark 十条重跑，本地 plan 只有四域且含表外 WebArena。→ Step 10 + 主动披露政策。
6. **安全与匿名**：公开匿名 artifact 中出现真实 OpenRouter key 与公网 IP。→ Step 0。
7. **artifact 叙述与实际文件缺口**（crosswalk / hygiene / 占位脚本）。→ Step 14。
8. **容量风险。** 新增 218 个 AndroidWorld raw runs、300 条统一 scoring 和人工审核，叠加 Step 6 高风险队列与其余 P0，对两人团队明显超载。→ Step 0.5 定容 + 预冻结 slot order + 降级回复。
9. **一致性待查。** AppWorld pool 论文 167 vs 本地 168；Table 1 各 pool→selected 与本地 manifest 全量对照；τ³ 官方 evaluator 实现可得性（影响 Step 8B）。→ Step 14 crosswalk。

---

## 4. 优先级、关键路径与总时间表


| 优先级                | 含义                         | 原则                                         |
| --------------------- | ---------------------------- | -------------------------------------------- |
| P0-E（existential）   | 不做则 rebuttal 无法诚实立足 | Step 0、0.5、1、2、4A、8A、14、15、16、17、18 |
| P0-V（value）         | 对核心质疑的最强证据         | Step 4B、4C、6、7、8B、10                    |
| P0/P1-S（supporting） | 特定 concern 的补强          | Step 9、11                                   |
| 条件项                | 余量或额外敏感性项         | Step 5（P1）、12（P1/P2）、13（P2）          |

**关键路径：** Step 0 ∥ 0.5 ∥ 1 → Step 2（7/15 检查点）后分两支并行：冲突核验支为 Step 8A（最迟在 Step 14 签字前完成）；主实验支为 {4A，Step 6 设计冻结} → 4B（218 个新运行槽位）→ 4C 阶段 1（统一 scoring + blind queue）→ Step 7（人工标注/裁决）→ 4C 阶段 2（锁定对照）→ {5、10} ∥ {9、11}。Step 8B 在 Step 8A 之后按 P0-V 容量与主实验支并行推进，不阻塞 P0-E 冻结；Step 14 汇总已完成输入后 → 15 → 16 → 17 → 18。12/13 仅在余量时。


| 日期       | 里程碑                                                                            |
| ---------- | --------------------------------------------------------------------------------- |
| 7/13       | 新建 `SUBMISSION_REPO`；Step 0、0.5、1 启动；Step 2 第一轮重建              |
| **7/15**   | **G2 已通过：Table 2/3/6/9/13 从两份冻结投稿来源精确重建，双作者独立运行签字比较为 PASS**          |
| 7/13–7/16 | 4A 完成；Step 6 设计冻结；Step 8A 的投稿 conflict 逐条核验完成                  |
| 7/14–7/20 | Step 4B 运行与 4C 审核为主体；Step 7、8B、10 及 9、11 按容量并行                 |
| 7/18–7/21 | Step 14（红队 + mock reviews + 应急包）、Step 15                                  |
| **7/21**   | **P0 冻结日：master table lock、evidence bank（含降级版本）lock、应急包 dry-run** |
| 7/22       | Step 16（含 OpenReview 机制实测）                                                 |
| 7/22–7/27 | Step 17                                                                           |
| 7/27–8/3  | Step 18                                                                           |

**降级预案 A（7/15 检查点未过时自动生效，需提前全体签字）：** 停止 9、11、5 的额外 sensitivity 以及 12、13；人力集中于投稿表格输入、聚合规则与数字差异定位，并界定"可验证的表/子表"。4B 的 A/B/C 扩展目标不静默删除；若硬件、时间或预算不足，按预冻结的 slot 顺序停止并报告实际覆盖，不得称 full100。Step 6 可缩至高风险队列前两档 + n=100 随机样；Step 15 各 block 启用预写的诚实收缩版本。

---

## ~~Step 0（P0-E）：安全、匿名、访问与程序合规~~ ✅ 已完成

### ~~目的~~

~~先消除可能独立导致程序性问题、费用损失或 artifact 下线的风险，并确保 7/22 全体作者按时看到 reviews。~~

### ~~要做什么~~

1. ~~立即撤销并轮换泄露的 OpenRouter key；核对用量、账单与异常访问；记录"公开时长 × 用量"风险窗口。撤销本身即为主要止血——撤销后 repo 中的 key 字符串已失效，其删除属卫生问题，按 chairs 流程处理。~~
2. ~~收紧公网 IP 对应服务的 allowlist / 防火墙，轮换相关凭证。~~
3. ~~对本地与公开 artifact 做 secrets scan（文本、JSONL、日志、压缩包索引、二进制元数据）；报告不复制 secret 明文。~~
4. ~~保存提交快照的目录清单、文件 hash、公开更新时间与安全事件记录。~~
5. ~~生成最小安全补丁：只删除/替换 secret、公网 IP 与敏感 trace；不改变任何 score、verdict、CSV、prompt、selection 或统计值。~~
6. ~~修改公开匿名 artifact 前联系 E&D chairs（evaluationsdatasets@neurips.cc），说明为 credential/security redaction 并询问允许方式。~~
7. ~~核验实际 OpenReview PDF（非本地 arXiv 版）：可见文本、metadata、文件名、acknowledgment；code/data URL 匿名性；anonymous repo 的 README、history、路径与日志。~~
8. ~~确认全体共同作者已完成 NeurIPS reviewer/AC obligations（否则可能延迟看到 reviews）；确认 OpenReview 账号、访问权限、时区与 7/22–8/3 值班表。~~
9. ~~**新增：** 起草 2–3 句英文安全事件应答要点（key 已撤销、无科学内容改动、chairs 已知情），供 Step 15 Block 9 使用。~~

### ~~产出物~~

~~安全事件记录（无明文）；immutable snapshot hash 清单；security-only patch diff；chairs 沟通记录；匿名性检查表；obligations 确认表；英文应答要点。~~

### ~~过程验收标准~~

* ~~泄露 key 已失效，异常用量已核对；secrets scan 真实凭证 0 命中（synthetic 命中有白名单）；~~
* ~~安全补丁前后科学文件内容 hash 完全一致；未经 chairs 指示无静默修改；~~
* ~~OpenReview PDF 与 response 环境无身份信息；~~
* ~~至少两位作者确认 7/22 可访问 reviews；英文应答要点经双人复核。~~

### ~~结果分支~~

* ~~chairs 允许安全修订：保留原 snapshot hash、补丁 hash 与"不改科学结果"证明。~~
* ~~暂不允许：维持 key 失效与服务隔离，保留本地补丁，不擅自更新公开 artifact。~~

---

## ~~Step 0.5（P0-E，新增）：容量预算与样本量锁定~~ ✅ 已完成

### ~~目的~~

~~在开工前把人时供给与全部 P0 需求对齐，预冻结所有样本量与截断线，杜绝"看结果或看进度后缩水"。~~

### ~~要做什么~~

1. ~~盘点 7/13–7/21 每位作者可用人时（扣除值守与本职），得到总预算 H。~~
2. ~~试标定时：从五 benchmark 各抽 2 条（须含 1 条 AndroidWorld Unknown、1 条 AgentDojo paired 记录）做双人独立两阶段标注，记录分钟/条（阶段 A、B 分开计）。~~
3. ~~用实测速率反推：Step 6 随机样 n ∈ {300, 150, 100} 与高风险各档的耗时；Step 4B 的 218 个新 raw-run slots、4C 的 300 条统一 scoring 与分档人工审核耗时；Step 7/8/10 的固定成本。~~
4. ~~据此书面冻结：n、高风险队列截断线、4C 人工覆盖模式（全集或预冻结分层子集）、4B 的 slot 顺序与逐日启动计划；全部在看任何新结果之前完成并 hash。~~
5. ~~确认 MVP 底线集（第 9 节）与丢弃顺序：13 → 12 → 5 的额外 sensitivity → 11 → 9 → 6（降 n）。4B 若无法跑满，只能按预冻结 slot 顺序停止并降级为 partial extension，不得按结果选择完成项。~~

### ~~产出物~~

~~capacity sheet；rate memo；冻结的 sample-size decision；AndroidWorld slot order；丢弃顺序签字页。~~

### ~~过程验收标准~~

* ~~H 与各步需求逐项核算，总需求 ≤ 0.8 × H（保留 20% 缓冲）；~~
* ~~所有样本量/截断线/slot order 的冻结时间戳早于任何相应新运行或标注结果；~~
* ~~丢弃顺序与降级预案 A 一致并由全体作者签字。~~

---

## ~~Step 1（P0-E）：从论文提交时仓库冻结基线并建立唯一 source of truth~~ ✅ 已完成

### ~~目的~~

~~新建并锁定论文提交时仓库，把"提交时 1,282 records"和"提交后 AndroidWorld 扩展"彻底分离；后续所有表、审核与回复数字从该执行仓库的唯一 master table 生成。~~

### ~~要做什么~~

1. ~~从论文提交时 commit/tag/archive 新建 `SUBMISSION_REPO`，记录 commit ID、archive SHA-256、submodule/large-file 状态、依赖 lockfile 与文件树 hash；启用新的运行输出根目录。~~
2. ~~将当前已改仓库标记为 `LEGACY_MODIFIED_REPO`，只读挂载；生成两仓库的顶层 diff/index，但不将其 full100、ledger、重审或聚合产物复制到新执行目录。~~
3. ~~只读 submitted baseline manifest：逐条列出 1,282 records（benchmark、case unit、agent；raw run / native evaluator / score / checklist 路径与 hash；raw evidence label、stronger label、released label；是否进入 Table 2 denominator；submitted/post-submission 标记）。~~
4. ~~单独锁定已公布 AndroidWorld 41 cases × A/B = 82 records；验证其与公开 artifact 的内容 hash 一致，后续不覆写这 82 条。~~
5. ~~建立空的 post-submission extension manifest 与目标契约：`remaining59 × A/B = 118`、`full100 × C = 100`，目标合计 218 条；只在 Step 4B 每个 slot 完成验收后追加。~~
6. ~~排除 `__infra_failed`、`__retry_archived`、旧清单与空目录，保留排除理由。所有聚合脚本固定到 manifest 输入，禁止目录 glob 混入新增记录。~~
7. ~~为各 manifest、脚本版本与输出表生成 SHA-256；不使用旧 `results/tables/*` 或 `outputs/latex/results_macros.tex` 作为数字源。~~
8. ~~master table 配统一格式化函数（百分数一位小数、区间端点同规则），全部下游 block 只准引用其输出；函数有单元测试。~~

### ~~产出物~~

~~`submission_repo_lock.json`；`submitted_baseline_manifest`（1,282 行）；`androidworld_submitted41_ab_manifest`（82 行）；目标 218 行的空 extension contract/manifest；repo diff index；exclusion ledger；hash manifest；一条可重复的重建命令；格式化函数与测试。~~

### ~~过程验收标准~~

* ~~`SUBMISSION_REPO` 的 commit/archive/tree/dependency hashes 已锁定；`LEGACY_MODIFIED_REPO` 只读，新执行输出根不与其重叠；~~
* ~~baseline 恰 1,282 个唯一 record key；submitted AndroidWorld 恰 82 个，与公开 artifact 字节一致；extension 初始为空，目标契约恰 218 个唯一 slots；~~
* ~~聚合仅通过显式 manifest 选择数据；开工时只审计 1,282 条 baseline，4B 完成后再独立审计目标 1,500 条 master universe 与 300 条 AndroidWorld crosswalk；~~
* ~~干净环境执行同一命令产出字节一致的 submitted master table；格式化函数单测通过。~~

### ~~结果分支~~

* ~~提交快照与当前已改仓库的 41-case 内容不一致：以公开提交快照为唯一 submitted baseline，差异单列，不得反向覆盖。~~

---

## ~~Step 2（P0-E，关键路径单点）：从两份冻结投稿来源重建 Table 2/3/6/9/13~~ ✅ 已完成

**完成记录（2026-07-15）：** 投稿打印口径的五表工程重建与 G2 均已完成。263/263 个 cells 为 `EXACT_MATCH`，0 discrepancy；A1/A2 在两个独立验证目录运行 `make verify`，均为 `PASS`/`APPROVE`，无 checksum failure，来源 hashes 与 `SHA256SUMS` 摘要一致（`f33bbedd…`）。可选 2-O 标记 `skipped`，不阻塞完成。

**~~本轮范围调整：按当前要求，先不裁决候选修改后来是否真正应用，只恢复投稿时 Table 2/3/6/9/13 的打印值。正式输入是两份已经冻结的投稿来源：`SUBMISSION_ARTIFACT_SOURCE`（匿名制品提交 `ffd9ff4e…`，提供 1,282 条记录及原生/证据标签）与 `SUBMISSION_PAPER_SOURCE`（论文源提交 `35b962c8…`，提供打印值、最终审核标签/条目和表格文字）。产物位于 `rebuttal_work/02_table_reconstruction/`：五表共 263 个表头及正文单元格全部为 `EXACT_MATCH`，`DOCUMENTED_DISCREPANCY=0`；独立空目录自动复跑字节一致，详见 `verification_report.json`。两份来源以完整 commit/tree/file hashes 锁定，不得用提交后的已改仓库补齐任何数字。~~**

**~~范围声明（v1.9）：Step 2 的必做主线是使用上述两份冻结投稿来源完成投稿表格的工程性重建；不再要求匿名制品分支单独包含论文审核台账。历史人工审核过程保留为可选子项 2-O：只在不延误五张表重建且容量允许时，尝试恢复 R1/R2 对每个 case 的独立判断、reviewer 身份、时间戳、讨论过程或 final-adjudicator metadata。2-O 可使用直接原件、结构化推断、AI 重审、两个压缩包和其他可追踪资料；这些信息的缺失不是 Step 2/G2 blocker。~~**

**~~只读历史参考（不计入完成性）：当前已改仓库曾从 `35b962c8` 找回并展开 126 行历史记录为 133 个 record keys，也曾产生一轮 `post_submission_reaudit`。该工作只用于新重建完成后的差异诊断；不得直接复制其 override、aggregate 或人工判断来使论文数字对齐。~~**

### ~~目的~~

~~先建立可重复的 submitted-results 基线：仅使用 `SUBMISSION_ARTIFACT_SOURCE` 与 `SUBMISSION_PAPER_SOURCE` 两份冻结投稿来源，以及固定聚合脚本，重建 Table 2/3/6/9/13，并将每个表格 cell 连回输入 record keys、公式和 source hash。匿名制品提交负责原始记录与原生/证据标签；论文源提交负责打印值、投稿终审标签/条目和表格文字；两者的职责不得互换，也不得混入提交后修改。**7/13 启动；7/15 为硬检查点。**~~

### ~~要做什么~~

1. ~~分别锁定两份来源：从 `SUBMISSION_ARTIFACT_SOURCE` 读取 raw runs、native/evidence/stronger/released labels、selection manifest 和 1,282 条记录；从 `SUBMISSION_PAPER_SOURCE` 读取 Table 2/3/6/9/13 的打印值、final labels、审核条目、conflict/correction/taxonomy 标记、表格文字和当时聚合输入；记录各自的 commit、tree、文件路径与 SHA-256。~~
2. ~~建立 `table_reconstruction_manifest`：每条只包含重建表格所需字段，包括 benchmark、case unit、agent、denominator/inclusion 状态、投稿时已存在的各类 label/flag、source role/path/hash 和 exclusion reason；同一字段的来源角色必须明确，不设 R1/R2、reviewer id 或 decision time 为必需字段。~~
3. ~~从同一 manifest 自动生成 Table 2 总行与 per-agent 行、Table 3 pairwise、Table 6 conflict counts、Table 9 reviewed/corrected counts 和 Table 13 taxonomy；禁止在输出层手填论文数字。~~
4. ~~为每个 table cell 生成 lineage：input record-key set、过滤条件、聚合公式、输入 hash、输出值，并自动与论文打印值 diff。~~
5. ~~对 raw 与 submitted final 值不同的 record，使用 `SUBMISSION_PAPER_SOURCE` 中已经冻结的 final label/correction flag 重建；若只能看到最终值而尚未恢复当时的人工理由，记为 `OPTIONAL_HISTORICAL_REASON_NOT_RECOVERED`，不影响表格重建验收。~~
6. ~~对任何无法由冻结输入产生的 cell 记录精确 discrepancy（预期值、实际值、delta、受影响 records/公式、最小缺失输入）；如用该差异推断历史 reviewer 行为，将结果写入 2-O 并标记 `INFERRED`。~~
7. ~~解释 τ³ “10 corrections 但 aggregate 不变”的字段级/对消机制；直接冻结证据不足时，可用多源证据形成候选解释，并标记对应的证据层级与置信说明。~~

### ~~可选子项 2-O：恢复历史审核过程（不阻塞 G2）~~ — `skipped`

1. ~~**启动条件：** Step 2 必做表格重建已不受该工作影响，且 Step 0.5 确认有剩余容量。~~
2. ~~**可用来源：** 原始表格/笔记/issue/message export/截稿前版本历史；投稿表格与 record-level 差异；`post_submission_reaudit`；`MobileRisk_offline_20260607T003138Z.tar.gz`；`conflict_readmes.zip`；以及其他可追踪资料。~~
3. ~~对每个能恢复或推断的 record，可选记录 R1 label、R2 label、reviewer identity/code、decision timestamp、disagreement resolution、final adjudicator/verdict，同时记录 source path/hash、恢复方法和置信说明。~~
4. ~~每个字段必须标记 `DIRECT_SOURCE`、`ARCHIVE_SUPPORTED`、`INFERRED`、`POST_SUBMISSION_REAUDIT` 或 `NOT_RECOVERED`；允许不同层级的多个证据共同支持同一候选值。~~
5. ~~可选子项的完成度单独报告（records/fields 的 recovered denominator，按证据层级分层）；partial 或 skipped 不改变 G2 结果，也不影响后续 AndroidWorld 扩展。~~

### ~~产出物~~

~~`table_reconstruction_manifest`；两份冻结来源的 input/hash manifest；自动重建脚本与测试；machine-readable Table 2/3/6/9/13；cell-level lineage；printed-vs-rebuilt reconciliation report；未复现 cell 的 blocker/discrepancy 清单；τ³ 口径说明（仅在有冻结证据时）；两份独立作者运行签字记录与 hash 比较报告。**可选产出：** `historical_review_process_ledger` 与 recovery coverage report。~~

### ~~过程验收标准~~

* ~~Table 2/3/6/9/13 的每个打印 cell 均已归类为 `EXACT_MATCH` 或 `DOCUMENTED_DISCREPANCY`；无未记录 cell；~~
* ~~G2 通过标准为五张表的所有 cell 均能从 `SUBMISSION_ARTIFACT_SOURCE` 与 `SUBMISSION_PAPER_SOURCE` 两份冻结投稿来源及固定脚本得到 `EXACT_MATCH`；每个输入字段注明来源角色，不以 R1/R2、reviewer 身份、时间戳或历史 adjudicator metadata 是否存在作为验收条件；~~
* ~~Table 2 每行满足 N=P+F+U，bounds、Unknown share 全部重算一致；Table 3/6/9/13 与同一 reconstruction manifest 及它们各自的冻结口径一致；~~
* ~~每个 cell 可追踪到 record-key set、公式与 hash；无“为对上论文而手填”的值；~~
* ~~两位作者可以使用同一台物理电脑，但须分别在独立的干净 checkout/worktree 或验证目录中亲自运行同一固定命令 `make verify`，不得由一人代跑或复制对方的生成结果；每人各写一份内部签字记录，至少包含：作者代号、运行日期时间与时区、两份来源的 commit/tree hash、操作系统与 Python 版本、完整命令、退出码、`verification_report.json` 的状态、`SHA256SUMS` 文件自身的 SHA-256、是否发生手工修改，以及最终结论 `APPROVE` 或 `REJECT`；~~
* ~~另生成一份签字比较报告，确认两人的两份来源 hash 完全相同、命令均成功、验收状态均为 `PASS`、`SHA256SUMS` 摘要相同且两人均为 `APPROVE`。签字记录保存在内部目录，不进入匿名公开 artifact；任一项不一致则 G2 不通过；~~
* ~~可选子项 2-O 若启动，所有 recovered/inferred 字段必须有来源、方法、证据层级和置信说明；它的覆盖率不是 G2 验收指标。~~

### ~~结果分支~~

* ~~五张表全部 `EXACT_MATCH` 且双作者签字比较通过：G2 通过，整体划掉 Step 2；后续 conflict 核验与复现、AndroidWorld 扩展及新的 human validation 使用该 submitted baseline。~~ ✅ 实际分支
* ~~五张表全部 `EXACT_MATCH` 但双作者签字未完成：只标记“技术重建完成、G2 等待签字”，不得整体划掉 Step 2。~~
* ~~少量 cell 为 `DOCUMENTED_DISCREPANCY`：G2 不完全通过；rebuttal 只使用可精确重建的表/子表，并预写 correction/limitation 说明。~~
* ~~核心表无法重建（7/15 检查点未过）：触发降级预案 A，优先定位冻结输入或聚合口径缺口；不用新实验掩盖。~~
* ~~五张表可精确重建，但可选的历史 reviewer-process metadata 不完整：G2 正常通过；2-O 按实际覆盖标记 complete / partial / skipped。~~

---

## ~~Step 3（已撤销/不适用）：原 B5/I5 分类矛盾担忧不成立~~

~~复核确认，B5/I5 的官方任务要求新增 \$5，最终任务证据结果为 `F`；发布评估器因旧 \$50 marker 判定 success；该 task/evaluator mismatch 同时构成 C5 conflict，stronger-measurement finding 也可并存。这些字段回答不同问题，不构成 taxonomy 矛盾。~~

~~因此不重跑 B5/I5、不撤销人工终审的四条 `S→F`、不修改 AgentDojo Table 2 的 `191/59/50`、不引入 `q_E/q_S/q_+` 专项框架，也不制作 B5/I5 correction memo 或预设“双轨 taxonomy”。~~

~~原 Step 3 中仍有效的工作已迁移：投稿打印的 32 条 conflict 的逐条来源、核验状态和 records / case units / mechanisms 三种计数由 Step 8A 负责；各机制的可执行复现由 Step 8B 负责；全文中任务证据结果、发布评估器结果、stronger finding 与 conflict 的术语一致性由 Step 14 负责。本步骤不设独立产出物或 go/no-go 门。~~

---

## ~~Step 4A（P0-E，已完成）：核验投稿制品中的 AndroidWorld 100 题清单~~ ✅

### ~~目的~~

~~只回答一个问题：冻结匿名制品提交中是否已经有一份具体的 AndroidWorld 100 题清单。~~

~~本步骤不再调查 41 题如何抽取、名单与查看 outcome 的先后、\$250 停止口径或 USD 370.91 的费用构成。~~

### ~~核验结果~~

1. ~~冻结匿名制品 commit `ffd9ff4e706d85ff2d12e60f087cde664dbae433` 包含有序清单 `experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json` 及配套 manifest `experiments/appendix/androidworld_full100_manifest.json`。~~
2. ~~有序清单实际包含 100 个 case IDs，去重后仍为 100，rank 为 0–99；清单 SHA-256 为 `6aa7d2b447742c2333192424941198ca8c8226c29141badfcae09b644a12c320`。~~
3. ~~已公布 AndroidWorld 41 题与该清单的交集为 41/41，没有任何一题位于该 100 题之外。~~
4. ~~证据边界：该清单存在于冻结匿名制品提交，但不存在于单独冻结的论文源 commit `35b962c8…`。配套 manifest 标为 `draft` / `0.1.0-prelock` 且无 contract locks；其内部 `created_at` 不单独用于证明更早的正式冻结时间。~~

### ~~产出物与验收~~

~~核验记录：`rebuttal_work/04_androidworld_execution/submission_full100_manifest_verification.md`。验收要求为 manifest 在冻结制品 commit 中存在、100 个 IDs 无重复、已公布 41 题全部为子集；三项均已通过。~~

### ~~结论~~

~~`PASS`。Step 4B 原样复用该有序 100 题清单，并在新运行前建立新的执行锁；新增运行仍明确标为 post-submission execution。~~

---

## Step 4B（P0-V，v1.4 新增执行步）：从公布 41×A/B 扩展到 official100×A/B/C

### 目的

在 `SUBMISSION_REPO` 中从已公布的 41 cases × Agent A/B（82 slots）出发，锁定同一 official 100-case universe，对 Agent A/B/C 全部测试（300 slots）。这是新的 post-submission execution，不复用当前已改仓库中的 full100 产物作为完成项。

### 要做什么

1. 锁定 AndroidWorld benchmark commit、候选 pool、eligibility rule 与 100-case manifest。若提交时已有可验证 official100 manifest，原样使用；若没有，在查看任何新 outcome 前写明 selection rule/seed，并确保已公布 41 cases 是该 100 的严格子集。
2. 冻结 A/B/C 的 agent model/version、provider、wrapper、prompt、observation/action scaffold、temperature、token/step/timeout/retry budget，以及 emulator/device image、app versions、benchmark reset 和 native evaluator 配置。三 agent 除预先声明的 model/agent treatment 外保持一致。
3. 将 submitted41 × A/B 的 82 slots 设为 immutable baseline，不因新执行而重跑或覆写。建立 300-slot contract，其中新运行恰为 `remaining59 × A/B = 118` 加 `full100 × C = 100`，合计 218 slots。
4. 在首个新 slot 前预冻结 task order、agent order 和 task-level paired seeds；A/B/C 使用 counterbalanced order，避免所有 A→B→C 顺序与时间漂移混杂。每个 slot 前从同一 clean snapshot 重置。
5. 每个 slot 保留 run contract、raw run、trajectory、native evaluator input/output、final state、artifact manifest、配置与 hash。retry 仅限预先定义的 infrastructure/pre-run failure；不因 agent outcome 不理想重跑。
6. 每完成一个 slot 就进行 fail-closed 验收并追加 extension manifest；case ID、agent ID、benchmark commit、environment hash 或 decisive artifact 不匹配时不进 canonical set。
7. 新执行期间不查阅 `LEGACY_MODIFIED_REPO` 的对应 outcome、缺失 case、retry 或 aggregate。只在 300-slot manifest 冻结后才可做揭盲后 diff，且该 diff 不改变 canonical selection。
8. 为 300 slots 准备同一 fixed evidence-scoring configuration 与 checklist contract；实际 scoring、人工审核与对照由 Step 4C 执行。

### 产出物

official100 case manifest 与 selection memo；300-slot execution contract；218-slot extension manifest；A/B/C frozen configs；run-order/seed/reset plan；raw/native/artifact bundles；retry/exclusion ledger；cost/runtime/coverage report。

### 过程验收标准

* official manifest 恰 100 个唯一 cases，已公布 41 是其严格子集；submitted 82 条的内容 hash 前后不变；
* 目标完成 300/300 canonical slots：A/B/C 各 100/100；其中新执行恰 218/218，每 slot 有且仅有一个 canonical raw/native/artifact bundle；
* case/agent/config/environment/decisive-artifact mapping mismatch = 0；非预定 infra retry = 0；off-list case 不进 denominator；
* task/agent order、paired seeds 和 reset 记录与冻结计划一致；A/B/C 配置差异仅限预声明 treatment；
* extension manifest 可在干净环境独立验证；完成前不引用 full100 结果。

### 结果分支

* 300/300 完成：进入 Step 4C，统一评分并审核。
* 只有部分 slots 完成：保留预冻结 denominator、slot order 与未完成原因，只称 partial post-submission extension，不称 full100。
* 三 agent 配置无法达成等价：可继续生成分开 coverage，但不做横向 leaderboard；将差异带入 Step 5 敏感性门。

---

## Step 4C（P0-V，v1.4 新增）：AndroidWorld 300 slots 统一 scoring、审核与 41/59/100 对照

### 目的

在不改动 submitted41×A/B 事实的前提下，对 official100×A/B/C 使用同一 evidence-scoring 和 adjudication 口径，产生可追溯的 post-submission comparison。

### 要做什么

1. 冻结一个 scorer model/version/service/reasoning 设置、prompt、schema、parser、checklist 和 evidence-pointer 契约，对 300 slots 统一重评；scorer 不读取 agent identity、submitted/extension 标记或 aggregate。
2. 先在 submitted41×A/B 上读取 Step 2 冻结的 submitted labels 与表格纳入口径，将“submitted-as-printed”与“v1.6 统一重评”分列；不等待可选 2-O 才启动，也不用后者静默覆写论文打印值。
3. 按 Step 6 冻结协议为 218 个新 records 生成 blinded review queue：优先序为 released/evidence disagreement → conflict/stronger candidates → Unknown → 预冻结阴性随机样；不预设各档数量。实际人工标注/裁决由 Step 7 执行；Step 4C 在消费 Step 7 的 frozen outputs 后才能锁定最终对照表。
4. 生成严格分层：`submitted41×A/B`、`remaining59×A/B`、`full100×A/B`、`same41×C`、`remaining59×C`、`full100×C` 和 `full100×A/B/C`。submitted 一词只能用于前 82 条 A/B records。
5. 对每层汇总 released success/fail、evidence P/F/U、bounds、Unknown share、conflict 三单位计数、per-agent 与 paired-agent 差异；百分数只由 master formatter 输出。
6. 比较 submitted41 与 remaining59：endpoint/effect 变化、Unknown 原因分布、conflict mechanism 及 selection sensitivity；比较 A/B 与 C 时同时报告配置等价性与人工覆盖率。
7. 所有表标注 `submitted results` 或 `post-submission analysis`；Step 4A 只证明投稿制品中已有 100 题清单，不将新 218 slots 描述为截稿前已完成。

### 产出物

300-slot scored master table；submitted-vs-post-submission crosswalk；41/59/100 × A/B/C comparison tables；AndroidWorld audit/adjudication ledger；coverage/provenance/scorer report；主版与降级版英文结果摘要。

### 过程验收标准

* 300/300 slots 使用同一 scorer contract，schema failure = 0，hard-invalid pointer = 0，mapping mismatch = 0；
* submitted 82 条与新 218 条在 manifest、路径、hash 和表头上严格分离；组合后目标 master universe 恰 1,500 records；
* 每个 raw→final 变化有唯一原因、source pointer 和 adjudication；人工覆盖与 unresolved disagreement 如实报告；
* 所有 41/59/100 与 A/B/C 数字可从 locked master table 一键重算；没有从 `LEGACY_MODIFIED_REPO` 导入的手填 aggregate。

### 结果分支

* full100 保持核心现象：报告实际幅度与 uncertainty，不使用超出设计的 robust claim。
* effect 减弱、反转或 agent 间差异明显：完整报告并收缩论文 claim，不只展示 A/B 或有利子集。
* 无法统一 scorer 或人工覆盖不足：分开报告 coverage/raw native results，不声称已得到可比的三-agent evidence aggregate。

---

## Step 5（P1）：AndroidWorld A/B/C 横向可比性与报告门

### 定位说明

Step 4B 已将 A/B/C 各 100 作为目标，Step 4C 已将统一 scoring 作为硬要求。本步不再“补齐某一条 C”，而是在准备对外做三-agent 横向解读前，验证唯一有意 treatment 是 agent/model，并评估剩余配置差异是否足以禁止 leaderboard 或 pooled claim。

### 要做什么

1. 对 300 slots 逐字段比较 A/B/C 运行配置：benchmark/environment/reset、observation/action scaffold、tool set、step/token/timeout/retry budget、provider wrapper 和 final-answer handling；差异必须分类为 intended treatment / required provider adaptation / unintended confounder。
2. 检查 task order、agent order、paired seed、时段、emulator host 与 infra-failure rate 的平衡性；必要时用预定义的 paired/block sensitivity，不按结果后选模型。
3. 检查 native evaluator 与 evidence scorer 对 agent identity 的盲化；确认 300 records 的 scorer config/hash 一致。若有不可避免的 scorer 差异，在预冻结分层样本上做 invariance sensitivity。
4. 按 case cluster 生成 A–B、A–C、B–C paired 对照，并分别报告 released result、evidence bounds、Unknown 和 conflict；不用一个 pooled success rate 掩盖 evidence coverage 差异。
5. 为每个横向 claim 生成许可矩阵：configuration-equivalent / sensitivity-supported / descriptive-only / prohibited。只有前两类可用于横向对比。
6. 生成 rebuttal 主版、分 agent 降级版和 coverage-only 版；全部明确为 post-submission extension，不替换原论文 41×2 设定。

### 产出物

cross-agent config diff；order/seed/infra balance report；scorer invariance report；paired A/B/C sensitivity tables；claim-permission matrix；三档英文报告文本。

### 过程验收标准

* 300 slots 的 config diff 完整，每个差异有分类与影响判断；未解决 unintended confounder = 0，或相关 claim 已禁用；
* scorer identity-blind 且 config/hash 一致，否则 invariance sensitivity 达到预写门槛；
* pairwise 分析以 case 为 cluster，denominator、missingness、infra failure 与 uncertainty 完整报告；
* 每个对外三-agent claim 都有 permission 等级；不称 submitted result / fully preregistered / 原稿已有三-agent。

### 结果分支

配置等价且 sensitivity 通过 → 可报告 post-submission 三-agent 横向结果；存在可量化差异但结论在预写 sensitivity 中稳定 → 附限定语报告；差异不可解或结论不稳 → 只做 per-agent descriptive/coverage 报告，不做 leaderboard 或优劣 claim。

---

## Step 6（P0-V）：预冻结盲化人工验证设计

### 目的

用可审计的人类判断验证 LLM-assisted labels，而不是在看到 aggregate 后挑"看起来正确"的案例。

### 要做什么

1. 先锁定 Step 1–2 形成的 submitted labels、投稿时既有分类标记和 source pointers，再抽样。
2. 验证对象两层：
   * **高风险队列（分档 + 预冻结截断线，替换 v1.2 的"全集双标"）：** 档1 = 全部 conflict candidates 与全部 released/evidence 矛盾；档2 = 全部 raw-to-final changed records；档3 = 全部 Unknown（容量不足时用预冻结分层子集）。逐档 100% 或如实报告覆盖率，截断线由 Step 0.5 定容并早于任何结果冻结。
   * **未触发集合概率抽样：** n 由 Step 0.5 在 {300, 150, 100} 中锁定。
3. 抽样方案二选一并预先写死：简单随机（可直接给 binomial error upper bound）或分层不等概率（必须用 design weights 或逐层报告，不得把未加权结果称为总体错误率）。
4. 不采用 outcome-dependent stopping。
5. 两阶段 blind packet：阶段 A（outcome evidence：task/spec、official source、frozen checklist、retained artifacts；隐藏 model/agent、native output、LLM label、aggregate、路径身份提示）→ 阶段 A 锁定后进入阶段 B（conflict diagnosis：显示 evaluator 实现与 native output，分别记录 scorer error、evidence gap、spec conflict 和 stronger-measurement finding；允许同一案例同时具有 conflict 与 stronger finding）。
6. 两名标注者独立判断，禁止先讨论后填写。**两人团队裁决协议（修订）：** 分歧双方各写书面理由 → 按预写规则裁决（checklist 语义分歧按 source hierarchy；证据充分性分歧按 checklist 字面）；规则无法裁决的记为 unresolved disagreement，计入统计，不强行清零。
7. **独立性措辞（修订）：** 两位标注者均为作者且参与过 pipeline 设计，对外只称 "label-blinded re-annotation by the two authors under a pre-registered protocol"，不称 independent / third-party。若能在保密前提下引入 1–2 名非署名同事标注（需培训、保密告知、camera-ready 致谢安排），完成后再评估是否可称 external annotation。
8. 记录每项耗时、证据指针与不确定原因；参与过原 scorer/checklist 设计的事实必须披露。
9. 预定义指标：3×3 confusion matrix；exact agreement、per-class precision/recall；Cohen's κ（多人/缺失时 Krippendorff's α）；before/after per-benchmark counts；Table 2 endpoint 最大变化；conflict confirmed/removed/new；未触发集合错误率与 95% interval。
10. 样本量事实（沿用）：零错误时单侧 95% 上界约 3/n（n=300→1.0%，150→2.0%，100→3.0%）；出现错误后用 exact Clopper–Pearson 或预先指定的加权方法，不再引用 3/n 近似。
11. "全部 1,282 records 至少一次人工复核"仅为理想扩展，只有人力足够且能保证盲化质量时执行。

### 产出物

frozen sampling protocol、seed 与脚本；blind packet schema 与去标识检查；reviewer assignment；裁决协议；统计分析计划；workload estimate。

### 过程验收标准

* universe、排除项、seed、n、截断线在看人工结果前固定并 hash；
* 高风险各档覆盖率如实记录，档1 必须 100%；
* 两名标注者独立完成，blind packet 不泄露 model/native/current label/aggregate；每条判断有 evidence pointer；
* disagreement 全部经规则裁决或如实记为 unresolved；无 outcome-dependent 停止、换样本、删除困难记录；
* 独立性措辞 lint 通过（不出现 independent/third-party 除非条件满足）。

### 结果分支（理想目标，非公开门槛）

exact agreement ≥ 90%；κ/α ≥ 0.80；未触发残余错误率上界 ≤ 1%–2%；Table 2 endpoint 变化 ≤ 2–3 pp；benchmark 级核心结论保持。任一未达 → 实验仍视为完成，扩大 adjudication、报告真实结果并收缩相应 claim。

---

## Step 7（P0-V）：执行人工标注、adjudication 与标签可靠性报告

### 要做什么

1. 先完成从 submitted 1,282-record universe 冻结的高风险队列与概率样本，再处理 AndroidWorld 新增 218 records（remaining59×A/B + full100×C）中由 Step 4C 产生的盲化队列；两批不混。
2. 阶段 A 全部完成并冻结后才揭示 native/evaluator 信息进入阶段 B。
3. disagreement queue 按 Step 6 协议处理，保留原始 reviewer labels；unresolved 单列。
4. 对所有 human-vs-LLM 与 reviewer-vs-reviewer 不一致做 error taxonomy：checklist ambiguity / evidence omission / scorer reasoning error / source interpretation / taxonomy boundary / artifact corruption or absence。
5. adjudicated human label 仅作 validation gold（sensitivity/validation 用途）；保留 submitted final label，不回写。
6. 重算 Table 2/3/6/9/13 与 Android 41/59/100 × A/B/C 对照；输出 label change count、aggregate delta、endpoint delta、ranking change、conflict change。
7. 按 benchmark 分别报告，不用 pooled 平均掩盖；stress sample 的 agreement 不得描述为总体 population agreement。
8. **新增：** 产出英文 Label-reliability block 初稿（直接进 Step 15）。

### 产出物

两位 reviewer 原始 labels；adjudication ledger；agreement/confusion/CI 报告；submitted-table sensitivity report；Android full100 validation report；英文 Label reliability 数字块。

### 过程验收标准

* 计划样本 100% 完成（或按预冻结截断如实报告），无 silent missing；
* 原始 / adjudicated / submitted 三层标签均保留；统计全部从 frozen files 自动生成；
* confusion matrix 行列和与样本总数一致；κ/α 的计算对象与缺失处理写清；
* endpoint/ranking/conflict sensitivity 全部重算；两位作者交叉核对随机 10% 与全部 label changes。

### 结果分支

高一致且表稳 → 强力回应 label reliability；个别 benchmark 不稳 → 按 benchmark 报告；一致性低或主表变化大 → 主动承认并收缩贡献为方法/审计发现，禁用 "robust"、"nearly unchanged"。

---

## Step 8（8A=P0-E；8B=P0-V）：投稿 conflict 逐条核验与机制复现

### Step 8A（P0-E）：投稿 conflict accounting 与证据核验

#### 要做什么

1. 从 Step 2 `table_reconstruction_manifest`、Table 6/13 的投稿 conflict 标记和对应 cell lineage 枚举全部投稿 conflict records，建立 `submitted_conflict_verification_ledger`。
2. 每条记录至少包含 benchmark、record key、case unit、agent、投稿 conflict flag/type、task/spec source pointer、evaluator/oracle source pointer、decisive retained-evidence pointer、submitted mechanism id，以及当前核验状态 `confirmed`、`removed_or_reclassified` 或 `insufficient_evidence`；重点核验 τ³ 的 24 条。
3. 分别统计 affected records、unique case units 和 distinct mechanisms；三种单位不得互换，也不得把投稿打印的 32 条预先称为 32 条已确认冲突。
4. 投稿打印标记与提交后核验状态分列保存；Step 8A 不覆盖 Step 2 的历史重建。只有核验结果确有变化时，才在 rebuttal 中并列说明 submitted-as-printed 与 post-submission validated 状态。

#### 产出物

`submitted_conflict_verification_ledger`；records / case units / mechanisms 三计数表；投稿打印值与当前核验状态对照；英文 conflict accounting 数字块。

#### 过程验收标准

* 投稿打印的 32 条均有 record-level 映射、task/spec 与 evaluator/oracle source pointers、decisive evidence pointer、核验状态和 mechanism id；
* 对外仅将证据核验通过的记录称为 confirmed conflict；撤销、重分类和证据不足项明确标注；
* records / case units / mechanisms 三种计数可从 ledger 自动生成且不混用；
* 两位作者各自抽查全部变更项和随机 20% 未变项，结论与输出 hash 一致；
* 任何提交后核验变化只更新 post-submission validation 输出，不反写投稿 Table 2/6/13 的历史重建。

### Step 8B（P0-V）：为每个保留的 distinct conflict mechanism 建立可执行复现

#### 要做什么

1. 从 Step 8A 中证据充分、对外保留的 conflict records 枚举全部 distinct mechanisms（不是只选最漂亮的四个）。
2. 每个 mechanism 记录：affected records、unique case units、mechanism id、pinned benchmark commit/version、official input/state、actual evaluator output、official expected outcome、decisive source/code pointers。
3. 在真实 pinned 官方实现上写最小 regression/bug-reproduction test；禁止 toy 仿制逻辑。测试先证明 native evaluator 确实输出当前值，再证明官方 task/spec 与该值不一致；可用 strict xfail 或明确的 "reproduces mismatch" assertion。
4. 优先复现已知机制但不假设仅有这些：τ³ reward/action/state aggregation mismatch；AndroidWorld target-set construction / case-normalization；AgentDojo pre-existing state / omitted requirement；MiniWoB find-greatest wrong-card success。
5. Figure 2 的截图只称 illustrative；决定性证据是 evaluator input rows、directions 中的 exact Parmesan text、target-set output 与匹配代码。
6. **新增版本可得性契约：** 逐 benchmark 确认官方 evaluator 实现可获取且许可允许复现测试。τ³-bench（2026 research release）若实现不可公开获取，以 pinned release 包内代码 + retained evaluator inputs/outputs 构成降级证据，措辞明确为 "reproduced against the released package artifacts"。
7. 无法在 pinned implementation 上重现的 finding：查版本/环境漂移 → 仍不能重现则降级为 case-specific observation 或移出当前 confirmed conflict；不得手工构造例子顶替。该变化只进入提交后核验结果，不覆盖 Step 2 的投稿历史重建。
8. 双盲期间不以作者身份公开 issue；maintainer 沟通先备 draft、咨询 chairs（维持 v1.2 立场）。

#### 产出物

mechanism registry；executable tests 与运行日志；pinned dependency/commit manifest；maintainer issue drafts（不公开）；英文 conflict mechanism summary；逐 benchmark 可得性契约记录。

#### 过程验收标准

* 每个对外保留的 mechanism 至少一个真实 pinned-version executable repro（或明确标注的降级证据形态）；
* 测试在干净环境可重复，actual output 与 expected spec 均有 source pointer；记录 commit、input hash、environment、exit status；
* 无法复现的 finding 已在 post-submission validation 中降级/删除且 sensitivity table 已更新，投稿历史重建保持不变。

#### 结果分支

全部复现 → 可称 "all retained distinct mechanisms were reproduced against pinned versions"；部分复现 → 只报告成功数并解释其余撤销/漂移/证据不足，不称全部成立。

---

## Step 9（P0/P1-S）：AgentDojo prompt-injection 对 scorer 完整性的影响

### 要做什么

1. 100% 人工复核 AgentDojo 最终 native-aligned labels（injected arms、Unknown、conflicts 优先）。
2. 确认 scorer：无工具调用、无网络、无 secret、无可写 benchmark 环境；trace 作为 untrusted structured data 处理。
3. 三种隔离 sensitivity 输入：canonical raw structured trace；escaped/quoted canonical trace（转义规则写明）；neutralized injection-text diagnostic。删除 injection text 会改变证据，只作 sensitivity，不作 gold。
4. **新增（可选，P1）：** 5–10 条 canary 合成 trace（在真实 trace 中插入指令式文本，如要求 scorer 改标签），测试遵从性；结果只作 synthetic sensitivity，明确非真实分布，逐条留痕。
5. 比较各输入的 P/F/U、reason、source pointer；所有变化交人工 adjudication。
6. 检查日志中是否发生工具请求、外部访问、secret echo、越权指令遵循或 label 改变；重算 AgentDojo aggregate 与 Table 3 sensitivity。

### 产出物

scorer threat model；sandbox/config proof；raw/escaped/neutralized（+canary）比较；changed-label list 与 adjudication；aggregate sensitivity；英文 prompt-injection response block。

### 过程验收标准

* AgentDojo 全部 final labels 有人工 review provenance；
* sensitivity 输入除编码/指定处理外语义与 evidence 不变；label/reason 变化逐条记录，无选择性删除；
* scorer 无工具、网络、secret、可写环境；aggregate delta 与 changed-label count 可重算；
* 出现 injection-induced change 时已修正 reliability claim 并透明报告。

### 结果分支

零 label change → 可报告该具体 sensitivity 下未观察到 label manipulation，不称形式化安全；有 change → 报告数量、原因与人工纠正，scorer 输出降级为 provisional。

---

## Step 10（P0-V）：核实论文声称的 rerun，澄清 WebArena-Verified 角色

### 要做什么

1. 对照 PDF、`experiments/audit_sampling_plan/plan.yaml`、job manifests、结果目录，列出实际计划 / 实际运行 / 实际完成的 rerun。
2. 明确提交稿 "per benchmark" 实指：五主 benchmark、旧四域、还是部分完成。
3. 对每个已完成 domain 固定：10 case IDs、selection seed/rule、original/rerun pair、agent/model/version、infra failure 与缺失。
4. 报告 released/native-label agreement、evidence-label agreement、Unknown-reason agreement、新增/消失 conflict、endpoint/width change、exact CI（并声明这不是 agent-performance CI）。
5. 若 AndroidWorld/MiniWoB 未按论文措辞完成：不得临时补做后伪称原计划；新补做标 post-submission。
6. WebArena-Verified 明确标为 development/auxiliary analysis 或正式实验；不进主表就不能在 cost/rerun 叙述里模糊为主 benchmark。
7. **新增：** 若确认为 material misstatement（论文写 per benchmark、实际为四域且含表外 WebArena），按主动披露政策在最相关回复中主动更正，更正 ≤3 句、事实性，进 Step 15 Block 11。

### 产出物

claimed-vs-planned-vs-completed crosswalk；rerun paired table；missing/infra ledger；WebArena role memo；camera-ready correction text；英文 rerun summary。

### 过程验收标准

* PDF 每个 rerun 声明映射到真实 case IDs 与结果，或明确标为不准确；
* 配对样本用 frozen selection rule，无临时替换失败/不利 case；四类结果全报告；
* denominator 含合理 agent-caused failure，infra exclusion 有证据；不把 rerun 当 performance CI；
* WebArena 的角色、成本与结论边界在所有材料中一致。

### 结果分支

五 benchmark 均完整 → 给简表；仅四域或不完整 → 透明更正范围，优先保住可信度。

---

## Step 11（P0/P1-S）：case-unit sampling sensitivity 与 Table 3 keep/narrow/retract

### 要做什么

1. 保留原 bounds（identification uncertainty = [P/N, (P+U)/N]，条件于 sampled cases、fixed runs、retained artifacts）。
2. paired case-cluster bootstrap：cluster = case unit；同一 case 的所有 agents 一起重采样；每 benchmark 内独立；seed 与 resample count（≥10,000）预冻结。
3. **新增预定义汇总统计：** 每个有向对报告 separation retention rate（重采样中 LB\_i > UB\_j 的比例），并预冻结语言映射（如 ≥95% → "direction stable under case resampling"；<80% → 降级/撤回；中间带 → narrow）。禁止看结果后另选指标。
4. 多 pair 同时声称时报告 simultaneous/multiplicity 处理或明确标 exploratory。
5. Android full100 A/B/C 按 100 case clusters 做 paired sensitivity；只在 Step 5 横向可比性门通过时才做三-agent 对比，否则只分开报告。
6. unit tests：cluster integrity、deterministic seed、N=P+F+U、bound endpoints、overlap/touching rule。现有 `src/evidence_system/stats/` 占位实现不得当成品。
7. 没时间做可辩护 bootstrap 时，不仓促加 p-value，而是把 Table 3 主动限定为 audited-sample descriptive identification。

### 产出物

deterministic aggregation/bootstrap script；frozen bootstrap plan（含汇总统计与阈值语言）；per-pair sensitivity table；Table 3 keep/narrow/retract decision；英文 sampling-uncertainty block。

### 过程验收标准

* 所有 agents 以 case cluster 绑定，无 record 级独立重采样；seed、B、touching/overlap rule、汇总统计与阈值语言全部先于结果冻结；
* 每 pair 结论可从 master table 一键重算；identification 与 sampling uncertainty 在文字、表头、回复中不混淆；不稳定排序已降级或撤回。

### 结果分支

bootstrap 支持方向 → 只称 sampled-case sensitivity 支持，不夸大为总体 ranking；不支持 → 删去或收缩对应 claim。

---

## Step 12（P1/P2）：受控方法验证（资源不足时不挤占 P0）

**12A AppWorld artifact ablation（P1）：** 先建 human-verified gold（不得由被测 scorer 自定义）→ 分别 mask decisive final-state evidence 与 non-decisive negative control → 同一 scorer protocol 重判 → restore 验证标签恢复 → 报告转 Unknown 比例、false P/F、negative-control change、restoration rate。mask 规则与 case set 预冻结；结论只称 artifact-sensitivity/implementation validation。

**12B Evidence-retention repair（P2）：** 从 AndroidWorld/AgentDojo Unknown 预选小规模 case set → 增加论文指出的 missing post-state/receipt/snapshot → 重跑比较 U share、bounds、开销；case 选择不依赖修复结果；repair 前后配置一致；U→P/F 只视为 decidability 改善；环境漂移无法控制时降级为 future work。

**决策规则：** 任一 P0 未完成时，Step 12 不得占用关键人力；reviewer 未质疑 method validation 时优先可靠性、provenance 与 executable conflicts。7/21 前未完成的，response bank 不预写其结果，只保留 future-work 方案。

---

## Step 13（P2，时间允许才启动）：现有 benchmark 完整 official eligible set × A/B/C

**先区分：** Selected-full（固定 100-case split × A/B/C）vs Benchmark-full（pinned 版本中符合预写 eligibility policy 的全部 official cases × A/B/C）。本步默认后者；不得把 100-case sample 称为全量。

**本地候选与顺序（沿用 v1.2，启动前用 pinned 官方版本重验）：** MiniWoB++ 122（+22×3=66）与 τ³ 114（+14×3=42，先冻结 train/test/base 政策）第一优先；AndroidWorld 116（+16×3=48）与 AppWorld 168 test\_normal（+68×3=204，注意与论文 167 的差异先经 Step 14 核对）第二优先；AgentDojo 949（+849×3=2,547 records，约 5,094 episodes）rebuttal 前不做。

**启动门槛（沿用 v1.2）：** 相关 G0–G7 通过、核心数字稳定；Step 15 有可用版本且至少两名作者不被抽离；benchmark/agent/scorer/审核各有 owner+verifier；预算书面批准；距硬截止 ≥48h buffer；新运行独立目录与 manifest，不覆盖 canonical artifacts。**新增：7/22–8/3 期间默认冻结本步，除非 reviewer 点名要求且不影响值守。**

**执行与验收要点（压缩，细节沿用 v1.2 Step 13）：** 固定 commit/split/eligibility/case IDs/pool hash/agent 配置/scorer 协议/denominator 与 retry rule；preflight 一致才可入 denominator；outcome-blind 固定批次；infra-only retry；逐 slot 全 artifact + hash；统一 agent-blind scorer；高风险全集 + 预冻结阴性样人工审核；selected100-vs-full 对照；每 benchmark 独立冻结；只有完整通过验收才称 benchmark-full。验收硬项：eligible × {A,B,C} 笛卡尔积 100% 完整、无 silent missing/off-list/stale retry；无 outcome-based rerun；schema/hash/pointer = 0 mismatch；aggregate 一键重算；对外明确 post-submission。

---

## Step 14（P0-E）：全稿 claim、数字、figure、artifact 与复现红队

### 要做什么

1. 建立 "论文 claim → submitted source → final master-table field → source artifacts" crosswalk，覆盖正文、所有表、图、appendix、limitations。
2. 逐项红队（沿用 v1.2 清单）：任务证据结果、发布评估器结果、stronger finding 与 conflict 未被混写，且 conflict 与 stronger finding 允许并存；Figure 2 决定性证据；投稿打印的 32 条 conflict 的逐条来源、核验状态与三种计数；Table 3 sampling 解释；"low/wide Unknown" 配色阈值；native/released score 措辞；LLM scorer residual error 与 prompt injection；rerun 映射；auxiliary WebArena 定位；实际 OpenReview 匿名性。
3. **新增一致性必查：** AppWorld pool 论文 167 vs 本地 168；Table 1 全部 pool→selected 与本地 manifest 对照；τ³ Table 9 的 10 条候选修正为何未改变 aggregate；AgentDojo Table 9 `corrected=0` 与审核汇总中 3 个 grouped review-item corrections 的单位/含义差异。
4. **新增三份 mock reviews：** 人格分别为"被审 benchmark 的作者""统计学家""E&D 资深 AC"，各含 score 与 3–5 个可行动问题；用于测试 Step 15 覆盖率，缺口回填。
5. 配色采用客观规则（如 zero/nonzero conflict 与明确 Unknown threshold）；给不出预先有意义阈值就准备 camera-ready 移除规范性颜色。
6. reviewer-facing artifact 离线验证：`make smoke`、`checklist_validator.py`、`validate_score_pointers.py`、score schema、manifest hash、artifact pointer、expected-count checks。Android full100 最低要求：100 checklists schema 全过；300 score/manifest schema 全过；hard-invalid pointer = 0；300 slots mapping mismatch = 0；submitted 82 与 extension 218 分区验证全过。
7. 新写 deterministic rebuttal aggregator（现有 aggregate/make\_tables/stats 多为占位，不得当"已一键复现"证据）。
8. **新增 reviewer 索码应急包：** 7/21 前完成一个 secrets-clean、匿名、含 README 与最小复现路径（30 分钟内复现一条 conflict）的 bundle，不发布但保证收到索码请求后 24h 内可经 AC 分享；修复打包脚本已知问题（`scored81` 旧命名、绝对路径、无 checksum/secret gate、`<REPO_ROOT>` 占位）后才算就绪；隐身窗口 dry-run 通过。注意提交稿已印 GitHub org 链接，7/22–8/10 全程保持公开 repo 卫生。
9. **新增数字格式 lint：** 全文与 bank 的百分数/区间均出自 Step 1 格式化函数，人工抽查 20 处。
10. 对匿名提交与本地输出执行 secret/IP/identity/path scan、dependency/commit crosswalk、per-file SHA-256、incognito access smoke；说明哪些 reproduction 是 artifact-level、哪些需 live benchmark/credentials。
11. 建 camera-ready change log（含 Step 10 及其他实际需要的替换文本）。

### 产出物

claim-source crosswalk；red-team issue list（severity/owner/status）；三份 mock reviews 与覆盖率回填记录；validator/smoke report；deterministic aggregator 与 tests；artifact hash/secret scan report；reviewer 应急包；camera-ready change log；reproducibility summary。

### 过程验收标准

* 所有正文数字映射到唯一 master-table cell 与逐条 records；Table 2/3/6/9/13 无互相矛盾；
* Table 6/13 的每条投稿 conflict 均可追到冻结记录、source pointer 和 Step 8A 核验状态；未经核验的投稿计数不得统一称为“已确认冲突”；
* smoke/schema/pointer/hash 全过，失败有 blocker；`\fillfromdata`、placeholder、旧四域输出不进数字源；
* Figure 2 决定性证据不只靠截图；secrets、真实身份路径、active credentials 为 0；
* mock reviews 完成且暴露的缺口已回填；应急包 dry-run 通过；
* 随机 20 个 records 由未参与聚合者从 paper claim 反向追踪到 artifacts，成功率 100%。

### 结果分支

文字问题不改结论 → response 澄清 + camera-ready 承诺；数字/estimand 问题 → 重算所有依赖表；不可修复的 provenance 问题 → 列入 limitation，停止用对应结果作主要证据。

---

## Step 15（P0-E）：无链接、可直接粘贴的 rebuttal evidence bank

### 要做什么

为下列 concern 各备一个 500–1,500 character 的**英文** block：

1. Label reliability 与 blinded human validation（措辞按 Step 6 第 7 条）；
2. 126 reviewed / 48 corrections 的 provenance；
3. **Android：submitted41×A/B / added59×A/B / full100×C / full100×A/B/C（数字来自 4C；新运行明确标为 post-submission）**；
4. Conflict records / cases / mechanisms 与 executable repro；
5. 投稿 conflict 的计数口径、records / case units / mechanisms 区分及 Step 8A/14 核验结果；若审稿人问及 B5/I5，用一句话说明“任务证据失败、发布评估器成功、C5 conflict”可以同时成立；
6. Table 3 sampling uncertainty 与 claim narrowing；
7. GPT-5.4 rerun 范围、结果与限制；
8. AgentDojo prompt-injection robustness；
9. Artifact reproducibility、anonymity 与 security-only remediation（含 Step 0 应答要点）；
10. Scope、novelty、E&D fit 与 benchmark repair recommendations；
11. **新增：主动更正汇总**（rerun 范围、其他 material 更正各 ≤3 句，供最相关回复引用）。

固定结构（沿用 v1.2）：**Concern**（一句复述）→ **Direct answer** → **Evidence**（真实数字、样本、方法）→ **Effect on the claim**（保持/变弱/撤回什么）→ **Revision commitment**。

**新增模块：**

* common core（150–300 characters）：贡献一句话 + 证据层定位一句话，用于每条回复开头，保证跨回复一致；
* 每个主 block 配一个**降级版本**（对应实验未完成/结果不利时的诚实收缩措辞），7/21 与主版本一起冻结。

写作规则（沿用 v1.2 并强化）：submitted 与 post-submission 明确区分；数字仅引格式化输出；不用 "nearly all / very high / robust" 等不可核查词；无 URL、路径、附件、身份、新文件承诺；可写 "submitted anonymous artifact" 但不贴链接；不说已更新 paper/repository（除非官方允许且真实发生）；不把新结果说成原稿已有；主动收缩次要 claim。

### 产出物

response evidence bank（主版本 + 降级版本）；plain-text/no-link 版本；per-block provenance note（内部）；character-count 工具；prohibited-phrase / URL / identity / 数字格式 lint。

### 过程验收标准

* 每个 block 的所有数字可定位到 master table；submitted/new、raw/adjudicated 标记无误；
* 自动扫描无 `http(s)://`、作者身份、机构名、本地绝对路径；任意两个 block 对相同数字与术语的表述逐字一致；
* 每个 block 至少一位非起草作者复核；单块脱离附件可独立理解；
* 每个主 block 有配对降级版本并同时冻结。

---

## Step 16（P0-E，7/22 当天）：reviews 与 initial meta-review → concern matrix

### 要做什么

0. **新增（当天前 2 小时）：** 在 OpenReview 实际表单上核验：每条回复字符上限、附件/链接技术限制、是否存在 general response / official comment 位、能否直接回应 initial meta-review、提交后能否编辑。更新第 2 节；与预案不符立即调整 Step 17 模板。
1. reviews 开放后立即保存只读副本，记录 review id、score、confidence 与 initial meta-review。
2. 每条 concern 分类：factual misunderstanding / missing explanation / valid limitation / evidence-reliability challenge / statistics challenge / reproducibility-artifact challenge / novelty-scope-E&D fit / requested experiment / minor presentation。
3. 标 severity：Decision-critical（initial meta-review 或 reviewer 明确称影响 score）/ Major / Minor。
4. 每条 concern 映射：一句 direct answer；已完成证据（指向 Step 15 block）；是否需 post-submission analysis；claim consequence；owner + verifier；字符预算。
5. 先解决 initial meta-review 的 critical concerns，再处理 reviewer 间重复问题；新 review 出现时追加同一矩阵并保留版本历史。

### 产出物

review concern matrix；priority/owner table；reviewer-specific response outline；追加实验清单（做/不做及理由）；OpenReview 机制实测记录。

### 过程验收标准

* 每位 reviewer 的每条 substantive concern 有唯一条目；initial meta-review 每条 critical concern 有 owner 与直接证据；
* 不把 reviewer 的问题改写成更容易回答的版本；重复 concern 用同一数字源但保持 reviewer-specific 回答；
* 追加实验均对应 decision-critical concern 且标 post-submission；机制实测在提交任何回复之前完成。

---

## Step 17（P0-E，7/22–7/27）：撰写并提交逐 review initial rebuttal

### 推荐结构（每条 review）

1. 50–150 characters：感谢并准确概括最重要 concern；
2. 直接回答主 concern；3. 最相关的 submitted 证据；4. 明确标注的 post-submission result（如需要）；5. 对 claim 的影响（保持/收缩/撤回）；6. camera-ready clarification；7. 剩余字符处理 minor points。

### 要做什么

1. 每条 review 单独起草（可复用 common core，但正文必须 reviewer-specific），不复制统一长文。
2. 目标 9,000–9,500 characters，为格式差异与最后修订留余量。
3. 先写 decision-critical concerns；不用大量字符复述论文。
4. 新数字一律 "Post-submission, we conducted/completed…" 标记；全部来自 locked master table 的格式化输出。
5. 无链接、附件、图片、表格文件、身份信息；小表用纯文本/Markdown。
6. 不游说分数、不质疑动机、不情绪化。
7. 真实错误按四步：承认具体问题 → 给正确表述/数字 → 说明是否影响结论 → 承诺 camera-ready 精确修改。
8. **新增 material 更正放置规则：** Block 11 的每条更正放在最相关的 review 回复中（通常是提问最接近者）；若无人问及但属 material，放在与该实验最相关的回复或 general response 位（以 Step 16 实测为准）；其他回复中用一句话交叉指引（如 "as clarified in our response to Reviewer X"）；若平台不便交叉引用，则各自完整给出且措辞逐字一致。
9. 三轮检查：scientific owner（数字与方法）→ independent verifier（是否真正回答 concern）→ compliance editor（字符、链接、匿名、语气、格式 lint）。
10. 7/27 官方截止前至少留 6 小时完成最终提交与页面复核。

### 产出物

每条 review 的 final initial response；character-count 与 lint report；signed-off response matrix；OpenReview 提交确认记录。

### 过程验收标准

* 每条 response < 10,000 characters（建议 ≤ 9,500）；URL/附件/身份/本地路径 = 0；
* 每个 decision-critical concern 在前半部分被直接回答；所有数字与 evidence bank 一致；
* submitted 与 post-submission 无混淆；不同回复间无矛盾（含 material 更正的逐字一致）；
* 全体作者完成最终读稿并确认。

---

## Step 18（P0-E，7/27–8/3）：执行 rolling discussion

### 要做什么

1. 7/27 起按值班表检查新 comment（主要时区内每 4–6 小时一次）。
2. 每个问题先给短 direct answer，再给一到三个数字；不重贴整篇 initial response。
3. reviewer 要求额外分析：先确认是否已有结果；新做的标 post-submission；不上传附件/链接；不承诺无法控制时间的大型实验。
4. reviewer 明确索码：按官方唯一例外，经 Official Comment 向 AC 提供匿名链接（Step 14 应急包），确认 linked files 全部匿名。
5. 核心 concern 已被证据直接回答时，可礼貌总结 "we hope this addresses the concern"；不机械追问分数或施压。
6. 新 review 立即入 concern matrix 并回复。
7. 每次回复记录：comment id、时间、owner、数字版本、是否产生新承诺。
8. 8/3 前给 AC 最后一条简洁 summary：已解决问题、仍承认的限制、camera-ready commitments；不重复游说。

### 产出物

discussion duty roster；comment response log；new-commitment ledger；AC-facing final concise summary。

### 过程验收标准

* substantive 追问在可行时区内 6–12 小时内回应；每条回复与 locked master table 及先前 response 一致；
* 无链接/身份/附件违规；无未记录的新实验、新数字或 camera-ready 承诺；
* remaining concern 明确标 resolved / partially resolved / unresolved；8/3 截止前完成最后复核。

---

## 5. 对他人建议的采纳判断

本表沿用 v1.2 第 5 节全部行，另新增/修改以下行：


| 建议                              | 判断     | 说明                                            | 优先级 |
| --------------------------------- | -------- | ----------------------------------------------- | ------ |
| 从提交时仓库重新执行          | 采纳     | 当前已改仓库只读隔离；新结果不从其复制         | P0     |
| 拆分 Step 4 为 4A / 4B / 4C       | 采纳     | 4A 核验投稿制品中的 100 题清单；4B 跑 41→100×A/B/C；4C 统一评分对照 | P0     |
| 容量预算与预冻结降级              | 采纳     | Step 0.5 + 降级预案 A + 丢弃顺序                | P0     |
| 主动披露政策（material vs minor） | 采纳     | 写入工作原则；落地在 10/15 Block 11/17       | P0     |
| "独立人工验证"措辞收缩            | 采纳     | 两作者盲标 ≠ 第三方独立；预写合规措辞          | P0     |
| 高风险"全集双标"改分档队列        | 采纳     | 档1 100% 硬性；其余按定容截断并如实报告         | P0     |
| mock reviews 测试 bank 覆盖       | 采纳     | Step 14；三种人格                               | P0     |
| reviewer 索码应急包               | 采纳     | Step 14；24h 内可经 AC 分享                     | P0     |
| canary 合成注入                   | 条件采纳 | Step 9 可选项；只作 synthetic sensitivity       | P1     |
| bootstrap 预定义汇总统计          | 采纳     | separation retention rate + 预冻结阈值语言      | P0/P1  |
| 全部 block 英文起草 + 格式统一    | 采纳     | Step 15/1；数字仅出格式化函数                   | P0     |

## 6. 硬性 go/no-go 门


| Gate                               | 必须满足什么                                                      | 未满足时怎么办                         |
| ---------------------------------- | ----------------------------------------------------------------- | -------------------------------------- |
| **G-1 Capacity（新增）**           | Step 0.5 完成；总需求 ≤ 0.8×H；样本量/截断线/丢弃顺序冻结并签字 | 立即按丢弃顺序砍量；禁止无记录缩水     |
| G0 Security                        | key 已撤销；active secret 0；chairs 知情或有处理记录              | 立即止血；不静默改科学快照             |
| G1 Baseline                        | 1,282 submitted records 唯一、可追踪、可 hash                     | 停止所有 aggregate claim               |
| G2 Table reconstruction（**7/15：PASS**） ✅ | Table 2/3/6/9/13 已从 `SUBMISSION_ARTIFACT_SOURCE` + `SUBMISSION_PAPER_SOURCE` 两份冻结投稿来源和固定脚本精确重建；双作者独立运行的来源/输出 hash 相同并签字；历史 R1/R2 metadata 为可选 2-O、不阻塞且已标 `skipped` | 已通过；若冻结输入或签字摘要后来改变，重新打开 G2 |
| G3 Conflict accounting             | Step 8A 完成；Table 6/13 的投稿 conflict 均有 record-level 映射、source pointer 和核验状态；records / case units / mechanisms 分开计数 | 未经核验的投稿 32 条不统一称为 confirmed，只报告已核验部分 |
| G4 Human validation                | 预冻结、盲化、协议裁决、unresolved 如实计入                       | 不声称 human-validated reliability     |
| G5 Conflict repro                  | Step 8B 完成；每个保留 mechanism 有 pinned executable repro（或声明降级形态） | 无法复现的机制降级/撤回                |
| **G6A-1 Android 100 题清单（PASS）** ✅ | 冻结匿名制品中 manifest 存在；100 个 IDs 无重复；已公布 41 题全部为子集 | 已通过；若后续 manifest hash 改变则重新打开 4A |
| G6A-2 Android execution            | official100 已冻结；submitted 82 不变；新 218 slots 与总 300 slots 全部通过 lineage/config/artifact 验收 | 按实际 denominator 只报 partial extension，不称 full100 |
| G6B Android scoring/comparability  | 300 slots 统一 scorer/adjudication；Step 5 配置等价性或 sensitivity 门通过 | 分开报告 per-agent coverage，不做三-agent 优劣 claim |
| G7 Statistics                      | case cluster 正确；汇总统计预冻结；不稳定排序已降级               | Table 3 只称 sample-descriptive        |
| G8 Response compliance             | 每条 <10k；无链接/附件/身份；数字一致；三轮 sign-off              | 不提交，直到 lint 与双人复核通过       |

## 7. 内部目录与职能

目录沿用 v1.2 的 `rebuttal_work/` 结构，新增/调整：

```text
rebuttal_work/
  00_submission_repo_lock/              # 提交 commit/archive/tree/dependency hashes
  01_submission_baseline/               # 1,282 submitted records；Android 41×A/B 只读
  02_table_reconstruction/               # Step 2：Table 2/3/6/9/13 manifest、scripts、cell lineage、diff
    optional_historical_review_recovery/ # 2-O：多源 R1/R2/process 恢复、推断与证据层级
  04_androidworld_execution/             # official100、300-slot contract、新 218-slot runs
  05_androidworld_scoring_audit/         # 300-slot scoring、adjudication、41/59/100×A/B/C
  ...（其他目录按 v1.3 职能顺延）
  12_response_bank/english_lint/        # 禁词、URL、身份、数字格式 lint
  13_reviews_and_discussion/mock_reviews/
  17_reviewer_bundle/                   # 索码应急包（不发布）
```

每目录仍须含 README / MANIFEST（SHA-256）/ STATUS（owner、verifier、blocked/complete）/ 生成脚本与测试 / 无 secret 日志。

**职能表（替换 v1.2 角色表）：** 两人团队允许一人多职，但同一数字的生成者与核对者不得为同一人。


| 职能                | 责任                                                    |
| ------------------- | ------------------------------------------------------- |
| Rebuttal lead       | 总优先级、initial meta-review、跨 reviewer 一致性       |
| Evidence/provenance | baseline、table reconstruction manifest、Table 2/3/6/9/13 重建、4A 100 题 manifest 核验 |
| Human-audit         | 盲化、抽样、双标、裁决协议                              |
| Statistics          | CI、cluster bootstrap、Table 3 claim                    |
| Artifact/security   | secret、匿名、hash、smoke、chairs 沟通、应急包          |
| Response editor     | 字符、无链接、语气、格式 lint、camera-ready commitments |

## 8. 最终 readiness checklist

### 7 月 15 日（G2 检查点）

* [x]  ~~Table 2/3/6/9/13 已从两份冻结投稿来源 + 固定脚本精确重建：263/263 cells `EXACT_MATCH`，0 discrepancy，独立空目录自动复跑字节一致；~~ ✅ 技术验收完成
* [x]  ~~两位作者分别在独立干净目录运行 `make verify`，提交规定字段的内部签字记录；两次均为 `PASS`/`APPROVE`，来源 hash 与 `SHA256SUMS` 摘要一致。~~ ✅ G2 已通过；可选 2-O 标记 `skipped`

### 7 月 21 日前（P0 冻结日）

* [ ]  Step 0.5 定容完成：n、截断线、丢弃顺序冻结并签字；
* [ ]  泄露 key 已撤销、服务隔离、secret scan 完成、英文应答要点就绪；
* [x]  ~~1,282-record baseline 冻结并 hash；格式化函数单测通过；~~ ✅ 已完成
* [x]  ~~`table_reconstruction_manifest` + 两份冻结投稿来源 + 固定脚本精确重建 Table 2/3/6/9/13，每个 cell 有 record set / formula / hash lineage；~~ ✅ 技术验收完成
* [x]  ~~Step 2 双作者独立运行签字与 hash 比较报告完成；~~ ✅ `PASS`
* [x]  ~~**可选、不阻塞：** 2-O 按当前容量决定不启动。~~ ✅ `skipped`，不影响 G2
* [ ]  Step 8A：Table 6/13 的投稿 conflict 已逐条映射并记录 source pointer、核验状态及 mechanism；records / case units / mechanisms 三种数量分开；
* [x]  ~~4A：冻结匿名制品中的 100 题 manifest 已核验；100 个 IDs 无重复；已公布 41 题全部为子集。~~ ✅ `PASS`
* [ ]  4B：已公布 41×A/B 保持不变；official100 已冻结；A/B 各新增 59 与 C 新增 100，目标 218/218 新 slots、300/300 总 slots 完成（或按预冻结顺序报 partial denominator）；
* [ ]  4C：300 slots 统一 scoring/adjudication，41/59/100 × A/B/C 审核与对照完成；
* [ ]  Step 5：若使用 A/B/C 横向 aggregate，运行配置、scorer 口径与 sensitivity 门均通过；否则启用 per-agent 降级版；
* [ ]  human validation：sampling、blind packets、labels、裁决与统计完成；
* [ ]  Step 8B：每个保留 conflict mechanism 有 executable repro（或声明降级形态）；
* [ ]  AgentDojo injection sensitivity 完成或有诚实的未完成边界；
* [ ]  rerun 实际范围核清，material 更正文本进入 Block 11；
* [ ]  Table 3 keep/narrow/retract 决定完成；
* [ ]  smoke/schema/pointer/hash 全过；
* [ ]  evidence bank（主版本 + 降级版本）、common core、lint 就绪且全部英文；
* [ ]  三份 mock reviews 完成且缺口回填；
* [ ]  reviewer 应急包 dry-run 通过；
* [ ]  全体作者 reviewer/AC obligations 完成。

### 7 月 22 日

* [ ]  OpenReview 机制实测（字符上限、附件、general response、meta-review 可回复性）并更新第 2 节；
* [ ]  reviews 与 initial meta-review 完整入矩阵。

### 7 月 22–27 日

* [ ]  每条 decision-critical concern 有 direct answer 与数字；
* [ ]  每条 response ≤ 9,500 characters；无 URL/附件/身份/本地路径；
* [ ]  submitted 与 post-submission 明确分开；material 更正按放置规则落位；
* [ ]  三轮 sign-off 完成，截止前留 6 小时。

### 7 月 27–8 月 3 日

* [ ]  值班启动；追问全部入 comment log；
* [ ]  新数字仍来自 locked master table；新实验标 post-submission；
* [ ]  不催分、不游说、不重复贴长文；
* [ ]  最终 AC summary 聚焦已解决 concern、剩余限制与 camera-ready change。

### Step 13 启动前（沿用 v1.2 并加一条）

* [ ]  v1.2 全部启动门 + "7/22–8/3 默认冻结，除非 reviewer 点名且不影响值守"。

## 9. 最终策略判断

顺序：安全止血 → 从论文提交时仓库新建执行基线 → Table 2/3/6/9/13 重建（7/15 检查点）→ 确认 4A 的投稿制品 100 题清单（已完成），并并行启动 Step 8A 投稿 conflict 逐条核验与 Step 6 设计冻结 → 4B 从 41×A/B 运行到 100×A/B/C → 4C 统一 scoring 并生成 blind queue → Step 7 新的 post-submission 人工标注/裁决 → 4C 锁定 41/59/100 对照 → Step 5 横向可比性门。Step 8B 在 8A 后按容量与后续实验并行完成机制复现及其他补强 → reviewer-specific 写作与 discussion。

**MVP 底线交付集：** 必须完成 Step 0 / 0.5 / 1 / 2 / 4A / 8A / 14 / 15 / 16 / 17 / 18；Step 8A 的投稿 conflict 逐条核验和三单位映射必须在 Step 14 签字前完成，Step 8B 的完整可执行复现仍按 P0-V 管理。同时 Step 4B 作为用户明确指定的扩展目标必须按预冻结 slot order 执行，目标为新 218/218 和总 300/300。若硬件、预算或时间使其未跑满，计划不删除该步，而是锁定已完成 denominator、记录 blocker，并启用 partial-extension 回复；只有跑满后才进入 4C/5 的 full100 三-agent claim。

---

# Part II：Post-rebuttal 论文质量提升路线图（完整版）

## 10. 边界、版本选择与当前工程状态

本部分的 Step 19–24 不属于当前 NeurIPS rebuttal。除非这些实验在 author-response 期间恰好完整结束、直接回答 reviewer concern 且通过全部验收，否则不得写入当前 rebuttal。它们服务于 camera-ready、arXiv v2 或后续扩展论文，且不得反向描述为原提交结果。

**v1.9 仓库边界：** 下文的“当前本地状态”只是 `LEGACY_MODIFIED_REPO` 的只读工程参考。Part I 的新实验仍必须从 `SUBMISSION_REPO` 重新执行；仅 Step 2 的历史投稿表重建按其范围声明同时读取 `SUBMISSION_ARTIFACT_SOURCE` 与 `SUBMISSION_PAPER_SOURCE` 两份冻结投稿来源。Part II 真正启动时应另建 post-rebuttal branch/worktree，再重新验证这些状态。

### II.0 启动前重估与许可核验（v1.3 新增，Part II 总启动门）

在 Part II 产生任何付费运行开销之前，必须完成并全体签字：

1. **预算重估。** 基于 rebuttal 阶段的实际消耗与剩余额度，重估模型调用、人工审核、存储与失败重试预算；预算模型必须来自 Step 20/22 的真实 pilot 实测（tokens、秒/episode、bytes/episode、scoring cost、人工分钟），不得沿用官方云端宣传时长。
2. **结果两情景规划。**
   * **接收：** camera-ready 页数约束下的整合方式（主表 / appendix / arXiv v2）与时间节奏；
   * **拒收：** 转投目标（如 ICLR / ICML / 专门 evaluation track）、七 benchmark 版本是否合并为一篇新投稿、时间表相应重排。 两情景各写一页 memo 并签字；Part II 的规模与顺序按实际落地情景执行，不做"两头下注"的半成品。
3. **版本与许可可得性核验。** WebArena-Verified v1.2.3、OSWorld-Verified v1、τ³ research release 的代码/数据许可是否允许：本地复现测试、artifact 再分发、evaluator 代码引用与 diff 发布；不满足则调整发布形态（如只发布 evaluator inputs/outputs 与对照说明，不再分发原代码）。
4. 未完成第 1–3 项之前，Step 20/22 不得启动任何付费运行；Step 19 的设计冻结可以先行。

### 推荐的 benchmark 版本

* **WebArena：** 使用 WebArena-Verified full 812，而不是原始 WebArena evaluator。WebArena-Verified 对全部 812 tasks 做了 evaluator/task audit；Hard 258 只能用于 pilot，不能冒充 full。
* **OSWorld：** 为与当前稿件、domain id 和既有设计保持连续，首先使用 OSWorld-Verified v1：full 369，或官方允许的 no-Google-Drive 361 denominator。
* **OSWorld 2.0：** 这是另一个 108-task、长时程且 task class gated 的新 benchmark，应作为未来独立实验，不能与 OSWorld-Verified v1 的 361/369 混在同一 aggregate。

官方参考：

* [WebArena Verified paper](https://openreview.net/forum?id=CSIo4D7xBG)
* [BrowserGym WebArena-Verified integration](https://github.com/ServiceNow/BrowserGym/blob/main/browsergym/webarena_verified/README.md)
* [WebArena-Verified full 812 dataset](https://huggingface.co/datasets/AmineHA/WebArena-Verified)
* [OSWorld / OSWorld-Verified v1](https://osworld-v1.xlang.ai/)
* [OSWorld 2.0](https://osworld-v2.xlang.ai/)

### 当前本地状态


| Benchmark         | 当前状态                                                                                                                                                                                                | 为什么不能直接发全量                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| WebArena-Verified | 官方 full 812、三台一致环境、六站部署/登录、六站逐 slot reset、812 个 source-rich packets、812 个 machine-validated native drafts、2,436-slot/fallback-0 调度预览、official CLI/adapter parity、三机故障测试和三个 exact OpenRouter 模型探针均已通过；模型仍只看到冻结的 `agent_input.json`；正式 full results 仍为 0 | 812 份真实人工 source-check signoff 与 formal locks 仍为 0；三块结果盘尚待明确擦除授权；正式 2,436 jobs、24-slot A/B/C pilot、pilot 运行时扫描/预算和正式 runs 尚未完成 |
| OSWorld-Verified  | adapter 只是 skeleton；deploy 命令是 placeholder；infra disabled；catalog/contracts/jobs/results 均为 0                                                                                                 | 需要从 runner、VM、agent multimodal action、evaluator、evidence capture 到 scoring 完整搭建                                |

---

## Step 19（Post-rebuttal P0）：冻结 WebArena-Verified full 812 简化运行清单（已完成）

### 目的

在部署 WebArena 环境和生成 case packet 之前，只先固定官方 812 个任务、三台隔离 VPS、三个模型与完整运行 manifest，确保 Step 20 可以直接按同一清单搭建和验证 pipeline。

### 已完成事项

- [x] **锁定官方任务源。** 使用 WebArena-Verified `v1.2.3` full 812；任务 ID 为 `0–811`，共 812 个唯一任务。官方任务源为 `experiments/official_splits/webarena_verified_official_812.json`，SHA256 为 `10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f`。
- [x] **锁定三台隔离 VPS 与模型映射。** Agent A：`45.76.67.186` → `openai/gpt-5.4`；Agent B：`66.42.108.130` → `anthropic/claude-opus-4.7`；Agent C：`149.28.79.226` → `deepseek/deepseek-v4-pro`。
- [x] **验证 OpenRouter 可用性。** 三台 VPS 均已通过 SSH 连通测试，并分别使用本地 `.env` 中唯一的 `OPENROUTER_API_KEY` 发起对应模型请求；三次均返回 HTTP 200 和预期模型响应。密钥不写入 manifest、配置文件或远端服务器。
- [x] **生成并冻结 full-812 manifest。** `experiments/step19/webarena_verified_full_812_manifest.json` 明确包含 812 个 case 和 2,436 个唯一运行槽位（812 tasks × 3 agents）；每台服务器及每个模型各 812 个槽位，同一 task 的三个模型使用相同 seed。
- [x] **完成完整性校验。** task ID、case 数量、slot 数量、服务器/模型映射、paired seed、任务源 hash、配置 hash、manifest core hash 和 SHA256 sidecar 均校验通过；新增配置与 manifest 中未发现 OpenRouter 密钥。

### 冻结产出物

- `experiments/official_splits/webarena_verified_official_812.json`
- `configs/webarena_verified_full_812.yaml`
- `experiments/step19/webarena_verified_full_812_manifest.json`
- `experiments/step19/webarena_verified_full_812_manifest.json.sha256`
- `scripts/build_webarena_step19_manifest.py`

### Step 19 范围边界

- [x] 本简化版 Step 19 已完成。
- 812 个 case packet、source bundle、native contracts/checklists、Docker/WebArena 环境、environment image digest、official evaluator/runner parity、reset receipts 和 pilot 不属于本步，统一留到 Step 20。
- 正式 2,436 次实验不属于本步，留到 Step 21。

---

## Step 20（Post-rebuttal P0）：把 WebArena-Verified pipeline 修成生产级并通过 golden pilot

### 目的

先证明本地 adapter 真正运行 WebArena-Verified 的 deterministic evaluator、每个 agent 从相同干净状态开始、关键 artifacts 完整，再启动 2,436 条正式运行。

### 当前阻塞与已完成子项

1. [x] adapter/worker 已切到 WebArena-Verified v1.2.3 固定 digest `eval-tasks`；要求 AgentResponse + full/embed HAR NetworkEvent artifacts，旧 `evaluation_harness` 结果不再通过 auditable gate。
2. [x] official CLI 与 adapter 已在三台 VPS 对 6 类 golden fixtures 做 18/18 raw-result exact parity，并覆盖 success/failure、AgentResponse、NetworkEvent 和 multi-site；该 parity 不替代真实模型 pilot。
3. [x] 每个 task-agent slot 前的 reset controller、锁、receipt 与六站覆盖已经实现并做真实重建验收；四站 smoke 为 12/12，Wikipedia/Map 扩展为 6/6，合并覆盖六站。
4. [~] 812 个现有 `case_packet.md` 已正规化为唯一的 canonical source-rich packets；812 份 native IR、contract drafts、checklist drafts 和 machine reviews 均已生成且 machine validation 为 812/812、fallback 为 0。被测 agent 仍只接收逐字节冻结的五字段 `agent_input.json`。真实人工 source-check signoff、formal contract locks 和 formal checklist locks 仍为 0/812，不能用机器记录冒充人工签字。
5. [x] 三台 VPS 的 Docker、官方 WebArena-Verified v1.2.3 evaluator 环境、project-selected WebArena driver、Python 3.11/3.12 依赖锁、Playwright/Chromium、完整 dpkg inventory、官方镜像 digest 和部署脚本 hash 已形成 identity-bound v3 一致环境回执。
6. [x] WebArena packet source 已改用独立的 812-entry、domain-qualified source bundle；native package 与调度预览均使用 `(domain, case_unit_id)` 绑定，跨域覆盖与 fallback contract 均为 0。
7. [~] scheduler 的非启动型机器预览已严格生成 812 cases × 3 agents = 2,436 unique slots，每个 agent/server 812、paired seed、per-slot reset、fallback 0；prelock formal dry-run 会正确写 0 jobs 并 fail closed。人工锁定前，正式 2,436 jobs 仍不得物化。
8. [x] 812 tasks 的类型已锁定为 374 MUTATE、325 RETRIEVE、113 NAVIGATE；controller 从 controller-only task contract 绑定 task type，模型只收到五字段 `agent_input.json` 并自行分类，non-JSON/非法 JSON stop 一律转为明确失败，不再伪造成 SUCCESS，也不读取 gold expected metadata。

机器可读总验收为 `experiments/step20/webarena_verified/acceptance.json`（SHA256 `40e35f6d6a68bf4a87cd9244e606eb5a7b5cb671a7f28a0aca6fb5a812c83aaf`），当前必须保持 `status=blocked`：所有 machine gates 已通过，六站部署/登录、六站 reset、official parity、三机四类故障测试和 exact 三模型凭据 gate 也已通过；blocking reasons 仍包括 0/812 人工签字与 formal locks、0 个正式 jobs、结果盘未授权、真实 24-slot pilot、pilot 运行时扫描和成本/时长/存储报告。`agent_input.json` 整树 SHA256 仍为 `98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975`，原 task-contract SHA256 仍为 `32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49`。

### 要做什么

1. **已完成本次子集：** 固定 WebArena-Verified v1.2.3 dataset/evaluator commit、官方镜像 digest 和完整 environment lock；正式 lane 不依赖 BrowserGym aggregate。
2. **已完成本次子集：** 将 worker 切换到官方 WebArena-Verified evaluator：AgentResponseEvaluator；full/embed HAR NetworkEvent evaluator；official structured response/status schema；task-specific revision。
3. [x] 用官方 CLI 与 adapter 对同一 golden artifacts 做 parity：已覆盖 AgentResponse-only retrieval、NetworkEvent/mutation、multi-site、确定成功与确定失败 fixture，三机共 18/18 exact match。
4. **代码门已完成，仍需 pilot 验证：** 禁止 expected-answer fallback；agent 自然语言 stop 不能伪造成 structured SUCCESS。
5. [x] 将所有索引、contract/source join、dedup key 改为 (domain, case\_unit\_id)，并修复 15 个已知跨域覆盖。
6. **部分完成：** 812 个 canonical packets、source entries、native contract/checklist drafts 和 machine reviews 已完成；仍须由真实人工逐 case 做 hash-bound source-check，生成 812/812 formal locks。formal phase 禁止 fallback contract；每个 contract 已要求非空 required-artifact requirements。
7. [x] 建立每-record clean-state policy：每个 task-agent slot 前按 task scope 从固定 digest 重建站点，A/B/C 不共享前一 agent 改写的环境。
8. [x] 每次运行前自动验证六站服务、login state、fixed sentinels、container/state identity、锁与 reset receipt；六站真实 reset 已在三机验收。
9. [x] 已冻结 8-case/24-slot pilot 的 counterbalanced task/agent order；同一 task 的 A/B/C 使用相同 task-level paired seed，三个 agent 的顺序预先平衡。该 manifest 冻结不代表 pilot 已执行。
10. 完成 stratified pilot：覆盖 shopping 187、admin 182、gitlab 180、map 109、reddit 106、multi-site 48 的站点类型；覆盖 retrieval、mutation、multi-site；每个 pilot case × A/B/C；Hard 258 可作为后续扩大 pilot，但不能称 full。
11. 每条 pilot 保存 structured final response、HAR、trace/render、native evaluator input/output、raw\_run、artifact manifest、model calls 和 reset receipt。
12. [x] 对登录失败、站点宕机、无效占位 API key 和 evaluator error 做三机真实 fault injection；12/12 正确归类为 infra-excluded/unresolved，恢复后六站 18/18、locks/workers/temp 均为 0，未记为 agent failure 或 score。
13. 完成 secret scan，站点凭证、session cookie、额外 headers 和 API keys 不得进入发布 artifact。
14. 固定 final-answer protocol：agent 必须自行按公开 schema 输出 task\_type/status/retrieved\_data；缺失或非法 JSON 是明确 agent failure，不能由 worker 包装成 SUCCESS。
15. evaluator/gold metadata 与 executor/agent prompt 物理隔离；对 prompts、model calls 和 traces 做 expected answer/gold-field 零泄漏扫描。
16. 使用全新 phase/output namespace，不在现有 results/full/webarena\_verified 上 resume。只有 manifest、agent config/model、benchmark/evaluator、contract 和 environment hashes 全部相同才允许复用 attempt。

### 产出物

production WebArena-Verified adapter/worker；812-case source/contract/checklist package；golden parity tests；clean-state/reset controller；stratified A/B/C pilot results；infra/evaluator fault tests；pilot cost/runtime/storage report。

### 过程验收标准

* official WebArena-Verified CLI 与 adapter 对 golden cases 的 evaluator output 完全一致；
* success/fail fixtures 均正确，expected fallback = false；
* 812 contracts 的 key 均为 WebArena domain + task id，跨域覆盖 = 0；
* 812 source/contract/checklist/task revisions 一一对应；
* requested = planned = 812 per agent、total jobs = 2,436、unique (domain, case, agent) = 2,436；少一条即拒绝启动；
* fallback contracts = 0，812/812 locked native contracts 均含非空 artifact requirements；
* 每个 pilot slot 都有 reset receipt，重复运行的 baseline sentinels 无漂移；
* A/B/C 均能生成合法 browser actions 和 official structured final JSON；
* 同 task 三 agents 的 seed 相同、baseline 相同，执行顺序平衡；
* natural-language stop、bad JSON 和缺失 JSON 不会被包装为成功；gold/expected leakage = 0；
* pilot artifacts 的 schema/hash/pointer failure = 0；
* 登录/API/站点/evaluator fault 均进入正确状态，不污染 agent performance；
* active secret、cookie、身份和公网凭证泄漏 = 0；
* pilot 的真实成本和时长在书面预算内，才能启动 Step 21。

---

## Step 21（Post-rebuttal P0）：运行 WebArena-Verified full 812 × A/B/C

### 目的

完成 812 tasks × 3 agents = 2,436 个可比较、状态隔离、可审计的正式记录。

### 要做什么

1. 从 Step 19 的 frozen 812-task manifest 生成严格的 2,436-slot 笛卡尔积。
2. 只使用 Step 20 通过 golden parity 的 production runner；旧 runner 结果不得与新 full aggregate 拼接，除非所有 commit/config/artifact hashes 完全等价并通过重验证。
3. 按固定 block/counterbalanced order 运行 A/B/C；每个 slot 前恢复相同 baseline。同一 task 使用 paired seed；不得沿用当前按 agent\_index 改变 seed 的做法。
4. 每批执行 health/baseline checks；每条 mutation 后按 frozen policy reset。
5. retry 仅允许可证实 infra/pre-run failure；所有原始 attempts 保留，只标一个 canonical final\_attempt。
6. 每个 slot 采集：prompt/observation/action trajectory；screenshots/render/Playwright trace；HAR/network events；structured final response；official evaluator input/output；reset/baseline receipts；model call/usage；raw\_run 和 per-file hash manifest。
7. 使用统一、agent-blind evidence scorer；必要时按 task family 使用 source-locked checklist，不允许 outcome 后修改 native contract。
8. 完成人工审核和 adjudication，报告：P/F/U；released/evidence confusion；Unknown reason taxonomy；conflict records/cases/mechanisms；per-site、task type、agent；state-reset、infra 和 evaluator failure。
9. 按 case unit 做 A/B/C paired analysis；full812 不等于跨时间/跨部署总体推断，仍需报告 environment/version 条件。
10. 冻结 full812 release snapshot，并对任务数据、站点凭证和 HAR 做隐私/secret 审查。

### 产出物

2,436-slot final manifest；WebArena-Verified raw/native/evidence bundles；adjudication ledger；per-site/per-agent/full aggregate；conflict regression tests；reset/infra/evaluator report；full release package 和 paper-ready tables。

### 验收标准

* 812 × 3 = 2,436 canonical slots 完整，无重复、无 silent missing；
* 每个 slot 的 task revision、agent config、runner/evaluator/environment hash 与 frozen manifest 一致；
* 原始 WebArena evaluator 和 WebArena-Verified evaluator 没有混用；
* 全部结果来自新的 full812 namespace；旧 runner、\_pre\_final\_action\_fix 和不匹配 hash 的 completed slots 未被 skip/reuse；
* 每个 slot 都有可验证 clean baseline/reset lineage，跨 task/agent 污染 = 0；
* 100% slots 有 raw\_run、official evaluator、trajectory、HAR、final response 和 manifest，或有明确 infra/evaluator failure record；
* outcome-based rerun = 0；
* scorer identity leakage = 0，schema/hash/hard-invalid pointer = 0；
* 所有 Unknown/disagreement/conflict 和预冻结普通样本已审核；
* 2,436 aggregate 可一键重算且重复运行字节一致；
* 对外只称自运行的 WebArena-Verified evaluation，不冒充 benchmark 官方主持的 leaderboard result。

---

## Step 22（Post-rebuttal P0）：实现 OSWorld-Verified production pipeline 并通过 10-task × 3 pilot

### 目的

把当前完全占位的 OSWorld 路径从 0 搭建为可执行、可恢复、可区分 evaluator instability 与 evidence Unknown 的生产系统。

### 当前必须修复的阻塞

* OSWorld adapter 不支持 direct execution；
* deploy\_osworld 是 placeholder；
* osworld-vps disabled，host/user/path/environment/assets 全是占位；
* 没有 official catalog、case packets、contracts、agent mapping、jobs、results 或 scores；
* A/B/C 是否真正支持 screenshot observation 与统一 OS action space 尚未验证；
* check\_infra、deploy、runner、collector 和 scorer 相关路径也有 bootstrap placeholder，不能只补一个 adapter 文件就称端到端可用。

### 要做什么

1. 在结果前选择并冻结 denominator：若能安全、稳定地配置独立 Google/OAuth 环境 → primary = 369；否则 primary = 官方允许的 no-GDrive 361；同时保存 361/369 sensitivity 设计，不能在看到 agent outcomes 后再选择。
2. pin OSWorld-Verified v1 commit、task catalog hash、VM image/snapshot、app versions、locale/timezone/resolution、runner/evaluator commits。
3. 实现 production adapter/official worker：VM restore/setup/post-config；screenshot observation；mouse/keyboard/coordinate action；official evaluator getters/metrics；raw\_run/artifact manifest；retry/final\_attempt；video/screenshot/action/evaluator evidence capture。同时补齐 deploy、preflight、runner、collector、score 和 completed-result reuse audit 的全链路 integration tests。
4. 启用并锁定 OSWorld infra：KVM/nested virtualization 或官方支持的云路径；per-slot clean VM snapshot；concurrency 与资源隔离；network/proxy/CAPTCHA/403 baseline；credential vault，secret 不写日志。
5. 验证 A/B/C：都能接收真实截图；都使用同一 observation/action scaffold；都能输出合法动作；模型差异是唯一主要 treatment。三 agents 都实现语义等价的 infeasible declaration action；不能只让某一个官方 wrapper 支持。
6. 建立 OSWorld 专用状态机：setup/pre-run failure；completed agent success/fail；evaluator\_failure；evaluator\_unstable；evidence P/F/U。evaluator\_failure/unstable 不得映射成 U。
7. 建立 evidence contracts/checklists，覆盖文件、应用状态、browser state、office documents、messages、OS settings、跨 app side effects。catalog importer 必须从每个 task JSON 的 evaluator.func 解析 evaluator 类型；不能只依赖辅助 side list。当前 369 catalog 实际包含 27 个 infeasible-evaluator tasks，而官方 test\_infeasible side list 只列 26 个；将 27 个全部冻结为有效 task stratum，并记录该 upstream metadata inconsistency。
8. 运行固定 10-task stratified pilot × A/B/C = 30 slots：覆盖 Chrome、GIMP、LibreOffice、VS Code、Thunderbird、VLC、OS 和 multi\_apps；覆盖不同 evaluator getter/metric；至少包含一个 infeasible evaluator、一个 composite evaluator 和一个非标量文件/文档 evaluator；覆盖网络/credential-sensitive 类，但若 primary = 361 则不含 GDrive；agent success/fail 不作为入选依据。
9. 对 snapshot restore、evaluator repeatability、network drift、credential failure 和 artifact capture 做故障测试。明确区分 agent 正确宣告 infeasible 后得到的 native result、真实 infrastructure failure、evaluator failure 和 evidence U。
10. 用 pilot 实测每 episode 的时间、image/input/output tokens、存储、scoring 和人工审核成本，再外推 1,083/1,107 slots。

### 产出物

production OSWorld adapter/worker/deployer；frozen 361/369 catalog 和 agent mapping；VM/environment lock；contracts/checklists；30-slot pilot；evaluator stability/fault report；cost/runtime/storage forecast。

### 过程验收标准

* 30/30 pilot slots 都有唯一 canonical attempt record；
* normal setup success 与 evaluator completion 在 pilot 中均达到预定工程门槛（建议至少 95%）；未达到则修复后重做 pilot；
* A/B/C 均真实消费 screenshots 并产生合法 actions；
* 三 agents 的 infeasible declaration protocol 语义等价，pilot 中至少一个 infeasible task 端到端通过；
* VM reset 后 baseline/sentinel 可重复，无上一 slot 状态泄漏；
* evaluator 对固定 terminal state 重放结果稳定；
* evaluator\_failure/unstable、infra failure、agent failure 和 evidence U 分类正确；
* deploy→preflight→runner→collector→score 全链通过，placeholder command 不再参与正式运行；
* trajectory/screenshots/video/action/evaluator artifacts 和 hashes 完整；
* secret/PII/token/cookie 泄漏 = 0；
* pilot 外推预算获批准后才进入 Step 23。

---

## Step 23（Post-rebuttal P0）：运行 OSWorld-Verified full 361/369 × A/B/C

### 目的

完成官方支持 denominator 上的三-agent 全量 OSWorld-Verified 研究：369 × 3 = 1,107 slots，或 361 × 3 = 1,083 slots。

369-task catalog 的当前官方分布为 Chrome 46、GIMP 26、LibreOffice Calc 47、Impress 47、Writer 23、multi\_apps 101、OS 24、Thunderbird 15、VLC 17、VS Code 23；361 split 只从 multi\_apps 中排除 8 个 Google Drive tasks。正式 importer 必须重新核对这些计数。

### 要做什么

1. 只使用 Step 22 已冻结的 primary denominator；不得看到结果后在 361 与 369 间择优。
2. 若 primary = 369，8 个 Google Drive tasks × 3 agents = 24 slots 必须通过预先验证的独立账号/OAuth 配置；否则在正式运行前将研究定义为 official no-GDrive 361。
3. 按 app/task family 和 agent counterbalance 调度；每个 slot 前恢复干净 VM snapshot。
4. 记录每个 attempt，重试只针对可证明的 infra/pre-run/evaluator transient failure；agent-caused outcome 不重跑。
5. 保存 screenshot/video、actions、VM/setup/post-state、files、application state、official evaluator input/output、model calls、raw\_run 和 hashes。
6. 对 evaluator 重放不稳定的 terminal states 单列 evaluator\_unstable，不进入 evidence U。
7. 使用统一 agent-blind scorer 和 source-locked contracts；完成高风险全集与随机样本人工审核。27 个实际 infeasible-evaluator tasks 全部保留并单列；不得把它们误作不可运行 infra cases。
8. 按 app/domain、evaluator type、task horizon、agent 汇总：native success/fail；evidence P/F/U 和 bounds；infra/evaluator instability；conflict records/cases/mechanisms；artifact/storage/runtime/cost。
9. 若采用 369，同时报告 361 no-GDrive sensitivity；若采用 361，清楚写 official supported no-GDrive evaluation，不称 369 全量。
10. 对包含账号、文件、邮件、浏览器和视频的 artifacts 做严格 access classification、secret/PII redaction 和发布许可检查。
11. 用 pilot 外推预算：若 max steps 为 S，则 action-call 上限约为 slots × S；另计 361/369 份 contract drafting、最多 1,083/1,107 份 evidence scoring 和人工审核。预算建议至少保留 20% 运行/评分余量和 50% 存储余量。

### 产出物

1,083 或 1,107-slot final manifest；full raw/native/evidence bundles；evaluator stability ledger；human adjudication；per-app/per-agent aggregates；361/369 sensitivity；conflict tests；privacy-safe release package。

### 验收标准

* primary catalog × {A,B,C} 笛卡尔积 100% 有 canonical slot；无重复和 silent missing；
* 369 study 的 24 个 GDrive slots 全部配置完成，否则不得称 369 full；
* 每个 slot 有 environment/VM/agent/runner/evaluator/scorer provenance；
* clean snapshot lineage 完整，cross-slot contamination = 0；
* evaluator\_failure/unstable 没有计入 evidence U；
* 27 个 infeasible-evaluator tasks 均在 denominator 中，agent-declared infeasible、infra failure 和 evidence U 没有混淆；
* outcome-based rerun = 0；
* schema/hash/pointer mismatch = 0；
* 全部 Unknown/disagreement/conflict 与预冻结普通样本完成审核；
* aggregate 可一键重算；
* self-run 结果不冒充官方 verified leaderboard result；
* release artifacts 不含 credentials、PII、OAuth tokens、cookies 或敏感视频内容。

---

## Step 24（Post-rebuttal P0）：整合为七 benchmark 的高质量论文版本

### 目的

不是简单给 Table 2 增加两行，而是重新验证论文的核心方法和结论在 mobile、tool/API、browser 和 desktop environments 中是否成立。

### 要做什么

1. 冻结 expanded-study master manifest：原提交五 benchmark 的 immutable baseline；post-submission full extensions；WebArena-Verified full；OSWorld-Verified full/no-GDrive。
2. 原始提交结果保持不可变；所有后续数据用明确版本和时间标记。
3. 用同一 adjudication schema、taxonomy 和 aggregator 重建：all benchmark Table 2；per-agent results；pairwise/cluster analysis；Unknown taxonomy；conflict records/cases/mechanisms；cost/runtime/artifact overhead。
4. 检查新增两域是否产生新的 reason/conflict classes；若扩 taxonomy，必须回看旧五域，避免只为新数据加后验类别。
5. 做跨 benchmark heterogeneity：stateful web vs desktop；read-only retrieval vs mutation；deterministic vs unstable evaluator；final-state availability；visual/GUI grounding 与 evidence retention 的交互。
6. 重新评估 Table 3。WebArena/OSWorld full 并不自动使模型 ranking 成为总体因果结论，仍需 case-cluster sensitivity 和明确的 agent/scaffold 版本。
7. 扩大 human validation：各 benchmark 高风险全集；各 benchmark 预冻结随机普通样本；报告 per-benchmark agreement，不只给 pooled average。
8. 重新写 abstract、contributions、limitations 和 conclusion，使论文主线从"五个案例研究"升级为跨七个异质环境的 evidence-support study。
9. 决定发布形式（**v1.3：按 II.0 两情景 memo 执行**）：camera-ready 页面允许则加入主表/appendix；页面或时间不足则发布 arXiv v2 + versioned artifact；若方法和 taxonomy 改动过大，考虑独立扩展论文，不把全部内容硬塞进 camera-ready。
10. 发布前执行全仓库 provenance、license、privacy、secret、PII、binary 和 large-file audit。

### 产出物

seven-benchmark master table；updated taxonomy and regression suite；expanded human-validation report；cross-benchmark analysis；revised manuscript/arXiv v2；versioned reproducibility package；submitted-vs-expanded change log。

### 验收标准

* 原提交和扩展数据完全分层，可分别一键复现；
* 七 benchmark 的所有 headline 数字来自同一 versioned master table；
* 新 taxonomy 对全部旧/新 records 一致应用；
* per-benchmark human reliability、sampling limits 和 evaluator instability 均报告；
* WebArena/OSWorld 的 infra/evaluator failures 没有被 evidence U 吸收；
* 所有 conflict mechanisms 有 executable repro；
* 论文没有因增加规模而恢复"nearly all/robust"等不可核查措辞；
* artifact secret/PII/license gate 全通过；
* 独立复核者能从论文任意 headline cell 追踪到 record、artifact、ledger 和 hash。
