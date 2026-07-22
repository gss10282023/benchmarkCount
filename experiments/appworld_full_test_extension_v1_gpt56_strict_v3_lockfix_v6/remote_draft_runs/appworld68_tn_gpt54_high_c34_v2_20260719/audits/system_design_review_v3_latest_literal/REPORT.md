# AppWorld 新增 68 个 test_normal checklist：按最新标准重新审核

审核日期：2026-07-19  
审核对象：`appworld68_tn_gpt54_high_c34_v2_20260719/results`  
审核方式：source-only、outcome-blind、只读；未读取具体 agent outcome、per-record released evaluator label/value 或 component evaluator result，未修改任何 draft、packet、registry、freeze、运行产物或评分代码。

本报告按用户最后一版标准作字面裁决：scorer 的 native S/F/U **不得依赖 released evaluator label**；最后一版没有继续明文禁止 scorer 查看所有能够等价重构 label 的 component evaluator outputs。`system_design_review_v2_label_blind` 保留为更严格的“label 与等价 proxy 均隔离”敏感性审核，不覆盖、不删除。

## 结论

按最后一版标准把“checklist 内容”和“运行时 pipeline”分开后：

- **checklist 内容层：41/68 可通过，27/68 需要 source-only 修订。**
- **native 层：68/68 通过**，469 个 released evaluator registered tests 均被纳入正式 native criterion。
- **现有 35 条 stronger conditions：15 条可原样保留，15 条需改写，5 条应删除。**
- **另有 14 条 stronger obligation occurrence 漏项**，归为 10 个条件族、13 个 case；与现有条件问题合并去重后，共 27 个 case 需要处理。
- 68 份 checklist 均未写入具体 released label、native score、agent outcome 或 benchmark-conflict 预判。
- 68 份内容均与 outcome 前的旧 canonical freeze 对应 YAML/JSON 逐字节相同；但 7 月 19 日新 `results/` 路径本身没有独立 formal freeze binding。

**端到端系统目前仍不能认定为就绪。** 原因不是这 41 份 checklist 的 native 内容，而是 reference scorer 没有 fail-closed 地保证直接 released label 对模型不可见；post-score comparison 也只有单向检查，confirmed benchmark-conflict 的独立 record-level workflow 尚未实现。

本审核没有对任何运行记录给出 S/F/U，也没有确认或排除任何 benchmark conflict。

## 总判定表

| 层次 | 结论 | 说明 |
|---|---:|---|
| outcome 前制定 | PASS | sealed drafting input 不含运行 outcome 或 per-record evaluator result |
| canonical pre-run lock | PASS | 68/68 YAML 与 JSON 均和旧 canonical freeze 逐字节一致 |
| 新 `results/` 路径自己的 lock binding | PARTIAL | 没有独立 formal freeze；正式使用必须引用旧 hashes 或新增只做路径绑定的 receipt |
| native evaluator/oracle 语义 | PASS | 68/68，469 registered tests |
| native 三值聚合措辞 | PARTIAL | 应显式冻结 `all pass -> S; any established fail -> F; otherwise U` |
| checklist 直接依赖 released label | PASS | 0/68 含 released label/native label/native score/outcome-specific 条件 |
| stronger source-only 合规 | 41 PASS / 27 ACTION | 只计具有具体官方 source support 的 stronger；主观无副作用偏好被剔除 |
| benchmark artifacts 与 label 原样保留 | pipeline 设计可支持 | adapter 保存 raw run、native evaluator artifacts 与 label；具体 record 完整性不属于 draft 审核 |
| scorer 对直接 released label 的隔离 | FAIL/未强制 | reference scorer 无过滤复制整个 evidence directory；只禁止引用 label 不足以证明模型未使用它 |
| 模型先产出 S/F/U、之后 wrapper 合入 label | PASS/逻辑顺序 | model schema 不含 label，wrapper 在模型输出后合入；但输入侧隔离仍未保证 |
| post-score 双向不一致检测 | PARTIAL/FAIL | 现有 audit 只覆盖 released success 对 native 非 S |
| mismatch 自动等于 conflict | PASS（未这样做） | 当前 generic flag 不是 confirmed conflict |
| confirmed benchmark-conflict workflow | FAIL/未实现 | 未发现基于 retained artifacts 与 source pointers 的独立 adjudication schema/runner |
| stronger 独立报告且不自动推出 conflict | PASS | stronger 为单独输出；`native S + stronger F` 只能是诊断 flag |

## 最新标准与 TestTracker 的边界

每份 checklist 的 `native.decisive_artifacts` 都包含：

> `Retained submitted answer, start/end database diff, API log, environment trace, and official TestTracker results`

示例：`results/7847649_1/checklist.yaml:23-28`。冻结的 AppWorld contract 又明确说明 full TestTracker output 含 `success`、`passes`、`failures`，且 `success = pass_count == num_tests`，见 `case_packets/appworld/7847649_1/case_packet.md:19-34`。

这里必须区分两种实验定义：

1. **最后一版标准的字面定义**：只禁止 native verdict 依赖 released evaluator label；其他 retained execution evidence 未被明文排除。按此定义，TestTracker component results 不再自动使 checklist 不合格，所以主计数是 41/68。
2. **更严格的等价-proxy 隔离定义**：label、TestTracker pass/fail vector、evaluation success 等任何能确定性重构 label 的输出都不给 scorer。按此定义，当前 68/68 的 decisive-artifact contract 都不合格，结论仍是 0/68，详见 `../system_design_review_v2_label_blind/REPORT.md`。

若论文声称 scorer 对 released evaluation **实质独立**，建议采用第二种定义。若保留 TestTracker results，必须明确写成“label field blind，但允许 released evaluator component outputs”；否则读者容易把它理解成独立重算，而实际 comparison 很大程度上会成为同一 evaluator 输出的再表达。

## 通过的核心内容

### Outcome-free provenance 与 lock

- 68/68 的 sealed stdin 仅含 `draft_instructions.md`、`template.yaml`、`case_packet.md`、`output_schema.json`。
- canonical freeze 明示 `draft_saw_benchmark_run_outputs=false`、`draft_saw_score_outputs=false`、`claim_mutation_after_freeze_prohibited=true`。
- `claim_final_lock.json` 明示 lifecycle 为 pre-benchmark/pre-score，且 `benchmark_run_completed=false`、`score_invoked=false`。
- 本轮逐字节复核：新 68 个 `checklist.yaml` 与 `checklist.json` 均 68/68 等于旧 freeze 对应文件。

证据：

- `claim_freezes/appworld485_20260718_claimonly_max_v1/provenance/claim_freeze.json`
- `claim_freezes/appworld485_20260718_claimonly_max_v1/provenance/claim_final_lock.json`

新拉回目录没有自己的正式 freeze。正式评分应引用旧 canonical bytes/case-lock hashes，或新增不可变的 path-to-hash binding receipt；不能覆盖旧 freeze。

### Native evaluator/oracle

- 68/68 strict AppWorld evaluator/packet semantic gate 通过。
- 共 469 个正式 `with test(requirement)` registered tests。
- `benchmark_success` 是全部 registered tests 的合取。
- 未计分的动态 `TestTracker` 属性没有被误写成 native 或 stronger。
- 每个正式 test 都有 success/fail 规则；保留证据不足时可给 U。

建议把批次级聚合再写死为：

> native S iff every registered test is established pass; native F iff at least one registered test is established fail; native U iff no failure is established and at least one registered test remains unresolved.

这是消除三值组合歧义，不改变 released native criterion。

## Existing stronger conditions：重新裁决

### 可原样保留：9 族、15 条 occurrence、13 个 case

| condition | case |
|---|---|
| `bind_archived_songs_to_new_playlist` | `634f342_2` |
| `bind_removed_songs_to_selected_playlist` | `986aa4e_1/2` |
| `exact_corrected_housing_amount` | `9dabbc9_1/2/3` |
| `exact_equal_share_amounts` | `2d9f728_1` |
| `exact_ten_day_total_answer` | `166f4ff_2` |
| `exact_withdrawn_balance_transfer` | `ccf4b82_1/2/3` |
| `preserve_existing_like_records` | `f3f60f0_2` |
| `preserve_existing_month_values` | `b6d1104_2` |
| `selected_todoist_item_completed` | `986aa4e_1/2` |

“现有 condition 可保留”不表示该 case 没有其他漏项；例如 `634f342_2` 仍缺少 source-song multiplicity 条件。

### 需要改写：10 族、15 条 occurrence、15 个 case

| ID | condition / case | 原因与修订边界 |
|---|---|---|
| ECF-001 | `exact_markdown_note_import` — `0d01c76_1` | exact import 有官方依据，但 `predeclared newline canonicalization` 实际未定义；冻结唯一换行规则或删掉例外。 |
| ECF-002 | `offline_nonrepeating_album_playback` — `0de03ea_1` | task 只支持从实际 current/cursor 起覆盖 15 分钟；现文错误约束更长的整个 queue，且未绑定 start-state downloaded set。 |
| ECF-003 | `exact_splitwise_source_amounts` — `32616b5_1/2/3` | Expense total 来自 note；share 是按 debtors 数量与货币规则派生。分别冻结 total、公式和 cent rounding，并补 source description。 |
| ECF-004 | `private_exact_venmo_records` — `3b8fb7a_1` | 限定本任务新增记录；Transaction 与 PaymentRequest 均须 private、exact amount、指定 description，并一一对应 source obligations。 |
| ECF-005 | `exact_csv_transaction_expense_amounts` — `6b6ca61_1` | `every retained` 会误扫历史记录；限定到每个 CSV row 对应的新 Transaction 或 Expense/Share。 |
| ECF-006 | `preserve_existing_release_log_rows` — `6f4b9a5_1/2/3` | task 支持既有 song→artist/month 语义不变，不支持 byte-equivalent 或 same order；允许无损重排/格式化。 |
| ECF-007 | `value_level_shuffle_order` — `8749218_1/2` | task 要求执行 shuffle，但 reverse 也可能是合法 shuffle 结果；用 API/trace 证明 shuffle 及完整输出，只有终态时可 U。 |
| ECF-008 | `validate_new_account_credential` — `9016950_3` | exact credential 有依据；post-hoc probe 与“artifact 不得保留 credential”是证据治理而非 task outcome。改用创建调用/state 或预先设计的脱敏 equality，并补 SMS exact binding。 |
| ECF-009 | `preserve_all_user_visible_task_fields` — `bde252e_2` | task 的 `identical` 有依据，但 condition 没有枚举允许差异；绑定 Todoist Task schema，列全 equal/allowed fields 与 moved-record bijection。 |
| ECF-010 | `recipe_name_only_message` — `ffe6d5e_2` | “Just the name, nothing else”支持 whole-message equality，不支持未声明的原始 case/spacing 字节规则；冻结唯一 text normalization。 |

### 应删除：2 族、5 条 occurrence、5 个 case

| ID | condition / case | 原因 |
|---|---|---|
| ECF-011 | `no_payment_card_mutation` — `f861c32_1/2` | 没有官方 outcome 依据且与正确 refill 流程冲突；初始余额不足、task 允许 refill、evaluator 特意允许 added PaymentCard。 |
| ECF-012 | `preserve_retained_queue_order` — `fd1f8fa_1/2/3` | official task 只要求移除目标歌曲并播放，没有具体 source 支持“其余歌曲保持相对顺序”；这是审核者的稳定顺序/无副作用偏好。 |

## Stronger 漏项

共 14 条 obligation occurrence、10 个条件族、13 个 case。只保留有具体 task/user source 支持且超出 native evaluator 实际检查范围的项。

| ID | 拟新增/扩写条件 | case | 官方依据与 evaluator gap |
|---|---|---|---|
| MSF-001 | `exact_playlist_change_multiplicity` | `042a9fc_1/2` | phone message 逐条给出 add/remove；evaluator 用 set 丢失重复次数。 |
| MSF-002 | `new_playlist_membership_multiset_exact` | `d194965_2` | source note 明列新 playlist 歌曲；evaluator 只比 song-ID set。只约束该新 playlist 自身的 exact multiset，不扩成全局无副作用规则。 |
| MSF-003 | `bind_expense_descriptions_to_source_rows` | `32616b5_1/2/3` | SimpleNote 每条 expense 有用途描述；evaluator 只查 amount/payer/debtor/share。 |
| MSF-004 | `payment_request_private_and_described` | `3b8fb7a_1` | task 明确 payment/request 均 private 且带 `For Maui trip`；evaluator 未查 request privacy/description。 |
| MSF-005 | `one_record_per_maui_obligation` | `3b8fb7a_1` | source 每项债务/债权是一个义务；receiver-keyed dict 可吞重复记录。 |
| MSF-006 | `archive_each_source_song_exactly_once` | `634f342_2` | source 明列唯一歌曲；evaluator 与现有 binding condition 不排除重复添加。 |
| MSF-007 | `one_activity_per_csv_row` | `6b6ca61_1` | task 明确每个 CSV person 二选一执行；多个 evaluator dict 可折叠重复 activity。 |
| MSF-008 | `sms_credential_exact_binding` | `9016950_3` | credential 大小写敏感且 task 要求 SMS 携带同一值；evaluator 对 SMS 使用 ignore-case。 |
| MSF-009 | `case_preserving_exact_title_format` | `59fae45_3` | task 明确引用格式 `"<original_title> | <most_common_genre>"`；evaluator 对 title 使用 normalize-text。 |
| MSF-010 | `exact_lowercase_date_header` | `f323bae_2/3` | task 明确把首列名写成带引号的 `"date"`；evaluator 对 header 使用 ignore-case。应按标准 CSV 解析后对第一字段做 case-sensitive equality。 |

不纳入的候选包括：通用“不得有任何其他修改”、稳定 CSV 字节/行序、未由 task 指定的大小写/空白偏好，以及任何仅凭 reviewer 认为“更干净”的要求。

## Case 级结果

### 需要修改的 27 个 case

`042a9fc_1, 042a9fc_2, 0d01c76_1, 0de03ea_1, 32616b5_1, 32616b5_2, 32616b5_3, 3b8fb7a_1, 59fae45_3, 634f342_2, 6b6ca61_1, 6f4b9a5_1, 6f4b9a5_2, 6f4b9a5_3, 8749218_1, 8749218_2, 9016950_3, bde252e_2, d194965_2, f323bae_2, f323bae_3, f861c32_1, f861c32_2, fd1f8fa_1, fd1f8fa_2, fd1f8fa_3, ffe6d5e_2`

### Checklist 内容层可通过的 41 个 case

`09b0ee6_3, 1150ed6_2, 13547f5_1, 166f4ff_2, 2d9f728_1, 31dc501_1, 3aa1a22_2, 3d9a636_2, 3d9a636_3, 425a494_3, 522e5e5_1, 522e5e5_2, 5a83b05_2, 652485c_1, 652485c_2, 7847649_1, 7847649_2, 83a7951_2, 8ce6779_2, 8ce6779_3, 986aa4e_1, 986aa4e_2, 9dabbc9_1, 9dabbc9_2, 9dabbc9_3, afc4005_2, b6d1104_2, b9c5c9a_1, c77c005_2, c77c005_3, ccf4b82_1, ccf4b82_2, ccf4b82_3, cef9191_1, cef9191_2, cef9191_3, d18139b_1, d18139b_3, d6ac34d_1, dac78d9_3, f3f60f0_2`

这里的“可通过”只表示在最后一版字面标准下，未发现 native/stronger source-content 缺陷；它不证明某个具体 run 的 evidence 是 S/F/U，也不弥补 scorer input isolation、comparison 或 conflict workflow 的 pipeline 缺陷。

## Pipeline 复核

### 直接 released label 的输入隔离仍未得到保证

`neurips_ed_track_minimal/scripts/score_evidence_with_codex.py:464-480` 对 `evidence_dir` 执行无过滤 `copytree`。该脚本也能从 canonical label file、`native_evaluator_output.json::success` 或 `tracker.failures` 解析 released label（约 `:1126-1153,1272-1325`）。prompt 仅要求模型不要 infer/output label，并禁止把 `raw_run.native_label/native_score` 作为 decisive pointer；这不能证明模型没有看见或使用直接 label。

因此当前实现应增加一个 scorer-view builder：

- full retained bundle 原样保存，不删除 label 或 evaluator artifacts；
- scorer bundle 至少剔除直接 released-label files、`raw_run.native_label/native_score`、label source/index fields 和其他直接 label copies；
- 两个 bundle 分别做 manifest 与 hash；
- 若采用更严格实验定义，再额外剔除 TestTracker pass/fail/success、evaluation success 与其他等价 proxies，同时保留独立重算所需 evaluator input/target/oracle、schema、answer、state/diff、trace/API log。

### 输出顺序正确，但 comparison 不完整

model output schema 只含 native/stronger；wrapper 在模型完成后才合入 `released_evaluator_label`，见 `score_evidence_with_codex.py:2023-2029`。这个顺序是正确的。

但 `audit_score_batch_slot.py:90-98` 只 flag `released == success && native != S`，没有对称覆盖 `released == fail && native != F`，也没有把 U 与 binary label 的不可对应统一送入 mismatch queue。

应在 scoring 完成后统一比较：

- released success 对 native S：一致；否则进入 review；
- released fail 对 native F：一致；否则进入 review；
- native U 对任一 binary released label：进入 review，但不是自动 conflict。

### Confirmed conflict 尚无独立实现

当前 AppWorld/reference scoring 路径没有发现一个单独 schema/runner，要求审核者用 retained artifacts 加明确 source pointers 证明 task、target construction、evaluator、oracle 或 reward wiring/aggregation 检查了不同 outcome。故任何 mismatch 目前都只能叫 review candidate，不能叫 confirmed benchmark conflict。

`native S + stronger F` 的 generic flag 也不是 conflict。stronger F 只能单独报告。

## 建议动作

1. 不覆盖旧 frozen checklist；对 27 个 case 在严格 source-only、outcome-blind 环境中生成版本化 stronger registry/checklist/freeze。
2. 给全部 AppWorld checklist 加统一、无歧义的三值聚合公式。
3. 明确论文究竟采用“只隐藏 direct label”还是“连等价 component outputs 一并隐藏”；不要混用两种表述。
4. 为 scorer 建立独立 sanitized view、manifest 与 hash；full retained bundle 继续原样保存。
5. 实现双向 mismatch queue 与单独的 confirmed-conflict adjudication schema/runner。
6. 在上述 pipeline 修复前，不把 41/68 的 checklist 内容通过表述成端到端系统已合规。
