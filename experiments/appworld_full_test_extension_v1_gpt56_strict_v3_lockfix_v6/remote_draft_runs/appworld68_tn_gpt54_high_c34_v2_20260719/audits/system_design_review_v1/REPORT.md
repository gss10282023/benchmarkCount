# AppWorld 新增 68 个 test_normal draft：系统设计审核

审核日期：2026-07-19  
审核对象：`appworld68_tn_gpt54_high_c34_v2_20260719/results`  
审核方式：source-only、outcome-blind、只读；未修改 checklist、packet、registry、claim freeze 或运行产物。

## 最终结论

不能把这批 draft 表述为“68/68 完全满足系统设计”。准确结论是：

- **native 层 68/68 合格**：469 个 released evaluator registered tests 均被完整、精确地转成 native S/F/U 判据；未计分的 `TestTracker` 动态属性没有进入 native 或 stronger。
- **生成与锁定链路 68/68 合格**：输入隔离、source pointer、schema、YAML/JSON、attempt、hash、runtime 配置及与既有 pre-run claim freeze 的字节身份均通过。
- **现有 35 条 stronger condition**：18 条可保留，15 条需改写，2 条应删除；需处理的现有条件涉及 17 个 case。
- **stronger 完整性**：另发现 11 条高置信 obligation occurrence 漏项，归为 8 个条件族，涉及 10 个 case。
- 两类问题合并去重后，**47 个 case 本轮未发现设计问题，21 个 case 需要修改 registry**。

因此 disposition 为：**native 可接受；当前 stronger registry 不可直接用于正式 stronger scoring，需在 source-only、outcome-blind 条件下修订并重新版本化锁定。**

这些 stronger 问题不改变 released benchmark label，也不自动构成 benchmark conflict；本审核没有做任何 record-level conflict 判定。

## 审核口径

本轮分四层检查：

1. 生成与锁定完整性：sealed stdin、prompt/template/packet hash、attempt、YAML/JSON、runtime 和旧 freeze 字节身份。
2. native：逐 case 重新解析 `evaluation.py` 中正式 `with test(requirement)` block，并与 checklist 的 native surface 精确比对。
3. 已存在的 stronger：对 35 条 condition 逐族读取 official instruction、released evaluator、关键 initial state/schema，判断其是否有具体官方依据、边界是否确定、artifact 是否足以判 S/F/U。
4. stronger 漏项：分别复核 33 个已有 gap case 和 35 个 registry 标作 no-gap 的 case，查找 evaluator 未充分操作化但有 case-specific 官方支持的义务。

审核未读取任何 agent outcome、released score 或运行后证据；因此没有 outcome-driven checklist mutation。

## 已通过的部分

### Native evaluator/oracle 语义

- strict evaluator-AST gate：68/68。
- registered-test blocks：469。
- `benchmark_success`：所有正式 registered tests 的合取。
- 每个正式测试都有镜像 `success_if` / `fail_if`；`undecided_if` 仅在保留证据不足以决定测试结果时使用。
- 非评分 `test.task_completed` 等便利属性进入 native/stronger：0。
- benchmark conflict 或 outcome-specific 预判：0。

### 生成、传输和锁定

- schema、guardrail、support pointer：68/68。
- YAML/JSON 语义一致：68/68。
- canonical checklist 与成功 `attempt_01` 字节一致：68/68。
- sealed input 只有 `draft_instructions.md`、`template.yaml`、`case_packet.md`、`output_schema.json`：68/68。
- prompt、template、packet、case-lock hash：68/68。
- `gpt-5.4`、`high`、Codex login、read-only、ephemeral、ignore-user-config、非 fast：68/68。
- 新 YAML/JSON 与既有 485-case canonical claim freeze 对应文件逐字节相同：68/68。

68 个 sidecar 均有 nonempty stderr，但内容限于临时目录清理、model-list 429、shell snapshot 或 WebSocket fallback；所有 response completed，event stream 无工具调用或 malformed event，因此这些是信息性 warning。

## 现有 stronger condition 的逐族复核

35 条现有 condition、21 个独特条件族的 disposition：

- PASS：18 条，10 族。
- REVISE：15 条，10 族。
- REMOVE：2 条，1 族。

### 需改写或删除

#### ECF-001（低）`exact_markdown_note_import` — `0d01c76_1`

大小写精确的 title/content import 有任务依据，但 “predeclared newline canonicalization” 没有在 checklist 中实际定义，锁定后仍给审核者留下自由度。

处理：明确唯一规范化，例如 CRLF/CR → LF，除此不 trim、不 casefold；或者完全删除该未定义例外。

#### ECF-002（高）`offline_nonrepeating_album_playback` — `0de03ea_1`

任务要求所选 album 在出发前就有足够的已下载歌曲，并从实际播放位置覆盖 15 分钟且不重复。当前 condition 只看 final download flags，又把要求扩到任意更长 queue 的每首歌；current song、cursor 和剩余播放时长也未定义。

处理：绑定 start-state downloaded set；冻结从最终 current/cursor 开始的 15-minute playback sequence、duration、album membership 和 uniqueness 规则，只约束实际 15 分钟路径。

#### ECF-003（高）`exact_splitwise_source_amounts` — `32616b5_1/2/3`

`Expense.amount` 直接来自 SimpleNote 中的 expense total，但 `ExpenseShare.share_amount` 是 total 除以列出的 debtors 后按货币规则派生，不是与 source total 相同。“currency precision before rounding”也自相矛盾。

处理：分别定义 expense total 和 share 派生公式，并冻结 decimal/cent rounding；同时补上 MSF-003 的 source-row description 绑定。

#### ECF-004（高）`private_exact_venmo_records` — `3b8fb7a_1`

当前只要求 Transaction private，漏掉 PaymentRequest 的 privacy；“every retained”也没有限定为本任务新增目标记录。任务还明确要求 payments/requests 均带 `For Maui trip`，但 evaluator 和现有 condition 都没有检查 request description。

处理：把条件限定到本任务新增的 Transaction/PaymentRequest，要求两类记录均 private、金额精确、request description 正确，并结合 MSF-004/005 做一对一和无重复检查。

#### ECF-005（低）`exact_csv_transaction_expense_amounts` — `6b6ca61_1`

精确 CSV 金额有直接依据，但 “every retained Venmo amount” 可误读为历史记录，而不是本任务按 CSV row 创建的记录。

处理：明确只检查本任务新增且按 CSV person/email 绑定的 Transaction、Expense 和 ExpenseShare；结合 MSF-007 限制每行恰好一个正确 branch。

#### ECF-006（高）`preserve_existing_release_log_rows` — `6f4b9a5_1/2/3`

任务支持只补齐 missing release month、不改变既有语义；不支持 `byte-equivalent` 或 `same order`。无损重排或格式化不应成为 stronger F。

处理：要求既有 song/artist/release-month 语义映射不变，只填缺失字段；不锁字节和行序。

#### ECF-007（高）`value_level_shuffle_order` — `8749218_1/2`

任务要求 shuffle，但 reverse permutation 仍可能是合法 shuffle 结果；“不得 reverse”来自 evaluator 意图性文案，不是 case-specific task obligation。

处理：优先用 trace/API log 证明实际调用 shuffle 且其完整输出成为最终 queue。若只有终态、无法决定过程，应判 U；不能因结果恰好 original/reverse 自动判 F。

#### ECF-008（严重）`validate_new_account_credential` — `9016950_3`

密码正确有明确任务依据，但 “privacy-safe authentication probe” 和 “artifact 不得保留任何 credential value”不是 agent outcome。官方 instruction、要求发送的 SMS 以及 AppWorld state 本身都包含该密码；额外 post-hoc probe 还可能改变状态。

处理：从账号创建记录或调用与 instruction credential 生成受控 equality result，评分 artifact 只保留布尔结果和脱敏 pointer；不要把凭据留存政策写成 stronger outcome。另补 MSF-008 的 SMS credential 精确绑定。

#### ECF-009（中）`preserve_all_user_visible_task_fields` — `bde252e_2`

“moved tasks must be identical”有直接官方依据，但 condition 声称只允许 “explicitly enumerated” system fields 改变，实际没有枚举字段或 schema selector，S/F/U 边界不确定。

处理：绑定正式 Todoist Task schema，列明必须相等和允许变化的字段。

#### ECF-010（严重、删除）`no_payment_card_mutation` — `f861c32_1/2`

该条件不仅缺少依据，而且与正确流程冲突：官方初始状态删除了所有 Venmo PaymentCard；Venmo 余额分别只有 30/40，而任务需支付 90/140；admin card 恰好提供 60/100 的缺口，任务也明确允许 refill。新增 Venmo PaymentCard 是完成 refill 所需，released evaluator 因此特意忽略 added card、只禁止 update/remove。

处理：删除该 stronger condition。它会把正确完成任务的运行必然判为 stronger F。

#### ECF-011（中）`recipe_name_only_message` — `ffe6d5e_2`

“Just the name, nothing else”支持整条 message 只能是一个 favorite recipe name，但不充分支持原始字节级 case/spacing 要求。

处理：用预先声明的 benchmark text normalization 对整条 message 与一个 favorite name 做 equality，同时禁止任何额外 token、前后缀或标点。

### 可直接保留的 10 族

`exact_ten_day_total_answer`、`exact_equal_share_amounts`、`bind_archived_songs_to_new_playlist`、`bind_removed_songs_to_selected_playlist`、`selected_todoist_item_completed`、`exact_corrected_housing_amount`、`preserve_existing_month_values`、`exact_withdrawn_balance_transfer`、`preserve_existing_like_records`、`preserve_retained_queue_order`。

这里的 PASS 只表示现有 condition 本身成立；例如 `634f342_2` 的 binding condition 成立，但该 case 仍因 MSF-006 漏项而需要修订。

## Stronger 漏项

共 11 条高置信 obligation occurrence、8 个条件族、10 个 case。

### MSF-001 `exact_playlist_change_multiplicity` — `042a9fc_1/2`

电话消息中的 add/remove 建议是逐条、一次性的明确指令；evaluator 对 added/removed song IDs 使用 set，重复新增同一正确歌曲仍会通过。

应补：目标 playlist 的 `(change_kind, playlist_id, song_id)` 多重集与 source messages 完全一致。

### MSF-002 `new_playlist_membership_exact_and_scoped` — `d194965_2`

任务只要求基于 SimpleNote 的 11 首歌制作唯一新 playlist。evaluator 只比较新 playlist song-ID set，不检查全部 `PlaylistSong` diff，因此重复歌曲、向其他 playlist 加歌或修改/删除旧 membership 都可能通过。

应补：全部 membership 变化仅为向唯一新 playlist 添加 source 清单中的每首歌一次。

### MSF-003 `bind_expense_descriptions_to_source_rows` — `32616b5_1/2/3`

SimpleNote 每条 expense 明确含用途描述；evaluator 检查 group、amount、payer、debtor/share 和 linkage，却完全未读取 `Expense.description`。

应补：每个新增 Expense 按 source row 绑定 group、payer、amount/share 和对应 description。

### MSF-004 `payment_request_private_and_described` — `3b8fb7a_1`

任务明确 payments 或 requests 都要 private，且都带 `For Maui trip`；evaluator 只对 Transaction 检查这两个字段。

应补：每个新增 PaymentRequest 的 `private=true` 且 description 语义等于指定 note。

### MSF-005 `one_record_per_maui_obligation` — `3b8fb7a_1`

evaluator 用 `dict_of(receiver → amount)`，可折叠同 receiver 的重复记录；现有 exact-amount condition 也不排除重复扣款/请求。

应补：SimpleNote 中每项债权/债务恰好对应一条目标记录，且无额外或重复。

### MSF-006 `archive_each_source_song_exactly_once` — `634f342_2`

source 文件列出 18 个唯一歌曲；evaluator 对 added PlaylistSong 只取 song-ID set，现有 stronger 只检查新 playlist binding，均不排除重复添加。

应补：新 `Old Songs` playlist 的 added song-ID multiset 与 source 唯一清单一一相等。

### MSF-007 `one_activity_per_csv_row` — `6b6ca61_1`

任务明确对 CSV “For each person”按有无 Venmo 二选一；evaluator 的 receiver/payer keyed dict 会折叠重复 Transaction/Expense。

应补：每个 CSV row 恰好对应一个正确 branch 的 activity，以及其 share/receipt；无额外或重复。

### MSF-008 `sms_credential_exact_binding` — `9016950_3`

密码大小写敏感，任务要求 SMS 原文含同一 credential；evaluator 对整条 SMS 使用 `ignore_case=True`，现有账号 credential condition 也不能证明 SMS token 与真实账号密码一致。

应补：生成不泄露密码的精确一致性布尔结果，证明 SMS credential token、instruction credential 和新增账号 credential 三者字节/大小写一致。

## 受影响 case

需要修改 registry 的 21 个 case：

`042a9fc_1, 042a9fc_2, 0d01c76_1, 0de03ea_1, 32616b5_1, 32616b5_2, 32616b5_3, 3b8fb7a_1, 634f342_2, 6b6ca61_1, 6f4b9a5_1, 6f4b9a5_2, 6f4b9a5_3, 8749218_1, 8749218_2, 9016950_3, bde252e_2, d194965_2, f861c32_1, f861c32_2, ffe6d5e_2`

其余 47 个 case 在本次 source-only 审核范围内未发现 draft-system-design 问题；完整列表见 `audit_summary.json`。这不是人工双审签字，也不是运行 outcome 的 S/F/U 判定。

## 锁定状态

新生成文件没有创建新的正式 lock，但 68 份 YAML/JSON 与 2026-07-17 canonical pre-run claim freeze 逐字节一致，所以内容身份受旧 lock 覆盖。正式 scoring 若使用旧版本，应引用 canonical freeze bytes 和 case-lock hash，而不是把新 `results/` 目录口头当作新 lock。

现有 freeze 记录：

- `status = locked_claim_checklists_pre_benchmark_run`
- `claim_mutation_after_freeze_prohibited = true`
- `human_review_completed = false`

既有 stronger review receipt 虽标记 `passed_source_only_exhaustive_review`，但本轮 source-level 复核已给出可复现反例，因此该 receipt 只能证明当时流程完成，不能继续作为 stronger 内容正确性的充分证据。

不要覆盖旧 freeze。若采纳本报告，应创建新的 registry、packet、checklist 和 versioned freeze，并记录 source-only、outcome-blind 的 adjudication receipt。

## 本次审核之外

以下只能在实际运行记录阶段确认：

- released label 是否原样保留；
- record-level native S/F/U 和论文 P/F/U；
- stronger 的实际 S/F/U；
- retained artifact 是否真的齐全；
- benchmark conflict。

draft 中没有 conflict 字段是正确边界。stronger F 不等于 benchmark 错误，native S + stronger F 也不能推出 conflict。只有 record-level retained artifacts 与 source pointers 证明 task、target construction、evaluator、oracle 或 reward wiring 实际检查了不同 outcome，才可另行标记 conflict。

## 建议

1. 暂停使用当前 stronger 层做正式评分；native 层可以继续使用。
2. 不修改旧 frozen 文件；在不查看 agent outcomes 的环境中处理 ECF-001 至 ECF-011、MSF-001 至 MSF-008。
3. 为修订版重新生成 registry → packet → checklist → freeze，并保留旧/新版本映射和 exact hashes。
4. scoring 前逐 record 对 decisive-artifact needs 做 evidence-bundle preflight。
5. 若论文需要人工审核声明，由真实审核者对修订后 exact hashes 签署独立 receipt。
