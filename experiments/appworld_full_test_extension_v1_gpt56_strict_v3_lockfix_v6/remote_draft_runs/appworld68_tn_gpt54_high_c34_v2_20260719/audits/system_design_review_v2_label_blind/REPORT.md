# AppWorld 新增 68 个 test_normal checklist：新标准重新审核

审核日期：2026-07-19  
审核对象：`appworld68_tn_gpt54_high_c34_v2_20260719/results`  
审核方式：source-only、outcome-blind、只读；未读取具体 agent outcome、per-record released evaluator result 或 component evaluator result，未修改任何 draft、packet、registry、freeze、运行产物或评分代码。  
版本关系：本报告按新的 label-blind evidence-scoring 标准重新审核；在该标准下，本报告取代 `system_design_review_v1` 的合规结论，但不删除或覆盖 v1。

## 最终结论

**当前 68 份 checklist 中，0/68 可以原样认定为满足新的完整系统设计。**

这不是因为 native evaluator/oracle 翻译错误。相反：

- 68/68 的 native 正式语义仍然正确，共覆盖 469 个 released evaluator registered tests。
- 68/68 的内容均能追溯到 outcome 前的 canonical claim freeze，且新文件与该 freeze 的 YAML/JSON 逐字节相同。
- 但 68/68 都把 `official TestTracker results` 明列为 scorer 可见的 decisive artifact；完整 TestTracker 输出包含 `success`、`passes`、`failures`，可直接或等价重构 released label。这与新标准要求隔离 released label 及等价泄露它的 component evaluator outputs 正面冲突。
- 现有 reference scorer 也没有做物理隔离：它把整个 evidence directory 无过滤复制进 scorer workspace。prompt 只要求模型“不使用/不引用”label 字段，不能替代信息隔离。

因此准确 disposition 是：

> **native criterion translation 通过；当前 checklist 的 scorer-visible artifact contract 不通过；stronger registry 还需 source-only 修订；现有 scoring/unblinding/conflict pipeline 未完整实现新标准。**

## 总判定表

| 检查项 | 结论 | 说明 |
|---|---:|---|
| outcome-free drafting input | PASS | 68/68 的 sealed input 只有 draft instruction、template、case packet、output schema |
| canonical pre-run content lock | PASS | 68/68 YAML/JSON 与旧 canonical freeze 逐字节相同 |
| 新 `results/` 路径自己的 formal lock binding | PARTIAL | 新目录没有单独的正式 freeze；只能引用旧 canonical bytes/hash，或另建不可变 binding |
| native evaluator/oracle 正式语义 | PASS | 68/68，469 registered tests |
| 明确的三值聚合规则 | PARTIAL | 有逐 test S/F/U surface，但未明确写出 `all S -> S; any F -> F; otherwise U` |
| label-blind decisive-artifact contract | **FAIL** | 0/68；68/68 要求 scorer 使用 TestTracker component outputs |
| case-specific scorer-visible artifact sufficiency | PARTIAL/未证明 | 去除 TestTracker 后，尚无逐 case sanitized inventory preflight 证明 scorer 能独立重算所有 native tests |
| checklist 中 outcome/conflict 预判 | PASS | 68/68 未写入具体 label、agent outcome 或 conflict 结论 |
| 现有 scorer 的 label/component-output 物理隔离 | **FAIL** | 整个 evidence directory 被复制给模型 |
| 模型先给 S/F/U、之后才合入 released label | PASS/逻辑层 | model output schema 不含 label，wrapper 在模型返回后合入；但模型此前已能看见泄露文件 |
| post-score 双向 comparison | PARTIAL/FAIL | 只检测 released success 对 native 非 S；没有覆盖 released fail 对 native 非 F，也没有统一 mismatch queue |
| confirmed benchmark-conflict workflow | FAIL/未实现 | 未发现要求 retained artifacts + source pointers 的独立 record-level adjudication schema/runner |
| stronger 与 conflict 分离 | PASS/需保持 | stronger 有独立输出；`native S + stronger F` flag 不是 conflict，今后也不得自动升级为 conflict |

## 审核口径

本轮把三类对象严格分开：

1. **checklist 内容**：是否在 outcome 前、依据官方 source 制定；native 是否镜像正式 evaluator/oracle；stronger 是否只有 case-specific 官方依据。
2. **scorer view**：实际给 scorer 的文件是否物理隔离 released label 和等价泄露它的 component evaluator outputs，同时保留足够的非 verdict evidence。
3. **unblinding 与 conflict**：S/F/U 完成后才比较 released label；不一致只进入单独审核，不能自动称为 conflict。

本审核没有把 pipeline 缺陷误写成 agent outcome，也没有对任何运行记录作 S/F/U 或 benchmark-conflict 判定。

## 批次级硬缺陷：68/68 暴露 TestTracker component results

每份 checklist 的 `native.decisive_artifacts` 都逐字包含：

> `Retained submitted answer, start/end database diff, API log, environment trace, and official TestTracker results`

其问题句还要求：

> `Do the retained artifacts and TestTracker results establish the outcome of every frozen registered test?`

示例：`results/7847649_1/checklist.yaml:23-28`。

同一 case packet 冻结的 TestTracker contract 明确规定：

- `success = pass_count == num_tests`；
- full output 包含 `success`、`passes`、`failures`；
- native released label 正是由这些 registered-test results 决定。

示例：`case_packets/appworld/7847649_1/case_packet.md:19-34`。

因此这里的 `official TestTracker results` 不是普通执行证据，而是能够等价泄露 released result 的 component evaluator output。即使删除一个顶层 `released_evaluator_label` 字段，只要完整 TestTracker pass/fail vector 仍对 scorer 可见，盲化就仍然失败。

该措辞不是 68 次偶发生成错误，而是上游 native semantic contract 的统一模板，见 `src/evidence_system/contracts/appworld_checklist_semantics.py:125-136`。修复必须版本化修改上游 contract、packet、checklist 和 freeze；不能只在评分时口头要求模型忽略它，也不能覆盖旧 frozen bytes。

### 去掉 TestTracker 后还缺一个 preflight

68 份 checklist 使用同一个泛化 artifact 列表，没有逐 case 绑定 sanitized scorer bundle 的实际路径、字段和可用性。静态扫描还显示：

- 67 个 case 的 native surface 含粗粒度 `answers match`；
- 49 个 case 引用 `private_data.*`；
- 22 个 case 引用 `public_data.*`。

这些并不表示对应 native rule 错误，但说明删除 TestTracker outputs 后，必须逐 case 验证 scorer 是否仍能看到正式 evaluator source、必要 target/oracle input、初始/最终 state 或 diff、answer、trace/API log，以及必要 schema。若缺少可独立重算某个 test 的非 verdict input，该 test 应按锁定规则进入 U，而不能重新引入 TestTracker result 来“补证”。

## 通过的核心内容

### 1. Outcome 前制定与锁定

68/68 的生成调用使用 sealed stdin；输入集合只有：

- `draft_instructions.md`
- `template.yaml`
- `case_packet.md`
- `output_schema.json`

旧 canonical freeze 明示：

- `status = locked_claim_checklists_pre_benchmark_run`
- `draft_saw_benchmark_run_outputs = false`
- `draft_saw_score_outputs = false`
- `claim_mutation_after_freeze_prohibited = true`
- `benchmark_run_completed = false`
- `score_invoked = false`

证据：

- `claim_freezes/appworld485_20260718_claimonly_max_v1/provenance/claim_freeze.json`
- `claim_freezes/appworld485_20260718_claimonly_max_v1/provenance/claim_final_lock.json`

本轮重新逐字节比较，新 68 个 case 的 `checklist.yaml` 和 `checklist.json` 均 68/68 等于旧 canonical freeze 对应文件。因此内容身份确实受 outcome 前的旧锁覆盖。

限制是：2026-07-19 新拉回的 `results/` 目录本身没有新的正式 freeze。正式使用时应引用旧 canonical checklist bytes 和 case-lock hash，或创建只做路径到旧 hash 绑定的新 receipt；不得把新目录口头称作一个新的 formal lock，也不得覆盖旧锁。

### 2. Native evaluator/oracle 语义

严格 AppWorld evaluator-AST/packet 语义复核结果：

- case：68/68 通过；
- registered tests：469；
- registry-declared stronger-gap cases：33；
- registry-declared no-gap cases：35；
- 非评分 `TestTracker` 动态属性误入 native/stronger：0；
- outcome-specific 或 conflict-specific draft rule：0。

每个正式 `with test(requirement)` block 都有镜像的 native `success_if` 与 `fail_if`；`benchmark_success` 是全部 registered tests 的合取。

### 3. S/F/U 聚合需补一句形式规则

当前每份 checklist 都写了逐 test success/failure，并统一写：

> `Undecided only if retained evidence cannot determine one or more frozen registered-test outcomes.`

这没有明确排除“一个 test 已证失败、另一个 test unknown”时误判 U。新版本应锁定以下三值组合，避免 scorer 自由解释：

- native **S**：所有 registered tests 均由非泄露证据建立为 pass；
- native **F**：至少一个 registered test 由非泄露证据建立为 fail，不要求其余 test 全部可判；
- native **U**：没有已建立的 fail，但至少一个 registered test 无法由 retained non-leaking evidence 决定。

这是 native 聚合澄清，不是新增 stronger condition。

## Stronger-measurement 重新审核

审核只读取 official instruction/task、released evaluator source/test data、必要 initial state/schema 和 artifact design；没有读取任何运行 outcome。

### 现有 35 条 condition

| disposition | condition occurrence | family | unique case |
|---|---:|---:|---:|
| PASS | 15 | 9 | 13 |
| REVISE | 15 | 10 | 15 |
| REMOVE | 5 | 2 | 5 |
| 合计 | 35 | 21 | 33 个含 stronger 的 case |

#### PASS：可原样保留的 9 族

- `bind_archived_songs_to_new_playlist` — `634f342_2`
- `bind_removed_songs_to_selected_playlist` — `986aa4e_1/2`
- `exact_corrected_housing_amount` — `9dabbc9_1/2/3`
- `exact_equal_share_amounts` — `2d9f728_1`
- `exact_ten_day_total_answer` — `166f4ff_2`
- `exact_withdrawn_balance_transfer` — `ccf4b82_1/2/3`
- `preserve_existing_like_records` — `f3f60f0_2`
- `preserve_existing_month_values` — `b6d1104_2`
- `selected_todoist_item_completed` — `986aa4e_1/2`

PASS 只说明现有 condition 自身有 source support。例如 `634f342_2` 仍有一个独立 multiplicity 漏项，见 MSF-006。

#### REVISE：10 族、15 条 occurrence

1. `exact_markdown_note_import` — `0d01c76_1`  
   title/content 的精确导入有任务依据，但 `predeclared newline canonicalization` 实际没有被声明。必须在 outcome 前冻结唯一 representation normalization，或使用稳定表示下的精确比较，不能留给 scorer 自行选择。

2. `offline_nonrepeating_album_playback` — `0de03ea_1`  
   当前条件把 15 分钟实际播放要求扩大到任意更长 queue，并没有绑定 start-state downloaded set、current/cursor 和实际 15-minute prefix。应只约束有官方依据的实际播放窗口。

3. `exact_splitwise_source_amounts` — `32616b5_1/2/3`  
   Expense total 来自 source note；ExpenseShare 是按 debtors 派生并按货币精度舍入，不能把二者都叫同一个 source amount。应分别冻结 total、share 公式和 cent rounding，并加入 source-row description binding。

4. `private_exact_venmo_records` — `3b8fb7a_1`  
   当前只覆盖 Transaction privacy，遗漏 PaymentRequest privacy、`For Maui trip` description 及一笔 obligation 对一条 record；`every retained` 也未限定为本任务新增记录。

5. `exact_csv_transaction_expense_amounts` — `6b6ca61_1`  
   exact CSV amount 有依据，但 `every retained` 会误扫历史记录。应限定为逐 CSV row、本任务新增、按 person/email 绑定的正确 branch，并加入每行恰一条 activity。

6. `preserve_existing_release_log_rows` — `6f4b9a5_1/2/3`  
   task 支持保留既有 song/artist/month 语义并补 missing month，不支持 byte-equivalent 或 same order。允许无损重排/格式化。

7. `value_level_shuffle_order` — `8749218_1/2`  
   task 要求执行 shuffle，但 reverse permutation 仍可能是合法 shuffle。应以 API/trace 证明 shuffle 调用及完整输出成为 queue；只有终态而无法证明过程时给 U，不能因 reverse 自动给 F。

8. `validate_new_account_credential` — `9016950_3`  
   exact credential 有任务依据；额外 post-hoc auth probe 和“artifact 不得留 credential”是证据治理，不是 agent outcome。应通过创建调用/state 或预先设计的脱敏 equality artifact 证明 credential，并加入 SMS token 的大小写精确绑定。

9. `preserve_all_user_visible_task_fields` — `bde252e_2`  
   task 明确 moved task 应 identical，但 condition 声称只允许 `explicitly enumerated` system fields 变化，却没有枚举。应绑定 Todoist Task schema、removed↔added pairing 和允许差异字段。

10. `recipe_name_only_message` — `ffe6d5e_2`  
    “Just the name, nothing else”支持 whole-message 等于一个 favorite recipe name；比较 normalization 必须预先定义并只实现该语义，不能额外加入无官方依据的 raw-byte case/spacing 偏好。

#### REMOVE：2 族、5 条 occurrence

1. `no_payment_card_mutation` — `f861c32_1/2`  
   没有 case-specific 官方依据，且与正确任务路径冲突：初始 Venmo PaymentCard 被删除、余额不足，任务明确允许 refill；新增卡是可行的 refill 路径，released evaluator 也只禁止 update/remove、允许 added。整条删除。

2. `preserve_retained_queue_order` — `fd1f8fa_1/2/3`  
   official task 只要求移除指定歌曲并播放，没有要求其余歌曲保持相对顺序。stable-order/no-side-effect 偏好属于审核者主观增量，不能进入 stronger，整条删除。

### 高置信 stronger 漏项

共 12 个 obligation occurrence、9 个语义族、11 个 case。其中 4 个 occurrence/3 族应新建独立 condition；其余 8 个 occurrence/6 族应并入上述现有 condition 的修订版。

1. **MSF-001 `exact_playlist_change_multiplicity`** — `042a9fc_1/2`  
   source phone messages 给出逐条 add/remove 指令；evaluator 使用 set，丢失重复/次数。目标 playlist 的 add/remove multiset 应与 source instructions 一一相等。

2. **MSF-002 `new_playlist_membership_multiset_exact`** — `d194965_2`  
   新 playlist 自身的 song membership multiset 应与 source note 清单精确一致。不得扩张成“全局无其他 PlaylistSong 变化”，因为后者没有 case-specific 官方支持。

3. **MSF-003 `bind_expense_descriptions_to_source_rows`** — `32616b5_1/2/3`  
   每条 SimpleNote expense 明确含用途 description；evaluator 只核 amount/payer/debtor。并入 `exact_splitwise_source_amounts` 修订版。

4. **MSF-004 `payment_request_private_and_described`** — `3b8fb7a_1`  
   task 明确 payment/request 都应 private 且带 `For Maui trip`；evaluator 没有完整检查 request branch。

5. **MSF-005 `one_record_per_maui_obligation`** — `3b8fb7a_1`  
   evaluator 的 receiver-keyed dict 会折叠重复；每项 source obligation 应恰好对应一条目标 record。

6. **MSF-006 `archive_each_source_song_exactly_once`** — `634f342_2`  
   source list 每首歌应在新 `Old Songs` playlist 中恰好一次；evaluator 的 set comparison 不保留 multiplicity。

7. **MSF-007 `one_activity_per_csv_row`** — `6b6ca61_1`  
   每个 CSV row 应恰好产生正确 Venmo/Splitwise branch 的一条 activity；receiver/payer-keyed dict 可能折叠重复。

8. **MSF-008 `sms_credential_exact_binding`** — `9016950_3`  
   instruction credential、创建账号 credential 和 outbound SMS token 应大小写/字节精确一致；evaluator 的 SMS comparison 使用 ignore-case。

9. **MSF-009 `case_preserving_exact_title_format`** — `59fae45_3`  
   task 明确要求 `<original_title> | <most_common_genre>`；evaluator 对 expected title 使用 normalize-text。应锁定 source title/genre 到最终 title 的 case-preserving exact formatting。

### Stronger 受影响范围

现有 condition 需动作 20 个 case；漏项影响 11 个 case；去重后共 **25 个 case** 需要 source-only registry 修订：

`042a9fc_1, 042a9fc_2, 0d01c76_1, 0de03ea_1, 32616b5_1, 32616b5_2, 32616b5_3, 3b8fb7a_1, 59fae45_3, 634f342_2, 6b6ca61_1, 6f4b9a5_1, 6f4b9a5_2, 6f4b9a5_3, 8749218_1, 8749218_2, 9016950_3, bde252e_2, d194965_2, f861c32_1, f861c32_2, fd1f8fa_1, fd1f8fa_2, fd1f8fa_3, ffe6d5e_2`

其余 43 个 case 在本轮 source-only stronger-content 审核中没有发现高置信问题；但它们仍与另外 25 个一样受批次级 TestTracker 泄露缺陷影响，所以不能计为完整新标准合格。

## 现有 scoring pipeline 与新标准的差距

### 1. Full retention 与 blind scorer view 没有分层

AppWorld adapter 会保留：

- `raw_run.json` 中的 `native_label` / `native_score`；
- `native_evaluator_output.json` 中序列化的 TestTracker；
- task-level evaluation report；
- DB、API、trace、LM logs 和 artifact manifest。

完整保留这些文件符合“原样保存 released label 和运行产物”的要求。问题不是 full retained bundle，而是同一目录被直接交给 scorer。

`neurips_ed_track_minimal/scripts/score_evidence_with_codex.py:464-480` 的 `stage_workspace()` 对 `evidence_dir` 调用无过滤 `shutil.copytree`。同一脚本还能从：

- `native_evaluator_output.json::success`
- `native_evaluator_output.json::tracker.failures`
- `run_summary.json`
- canonical released-label files

重构 released label，见 `score_evidence_with_codex.py:1126-1153,1272-1325`。

prompt 虽写明不要 infer/output released label，并禁止把 `raw_run.json::native_label/native_score` 当 decisive pointer，但模型仍可读取这些值、TestTracker pass/fail vector、evaluation report、manifest `evaluation_success` 和 evidence index 的 label source。禁止引用不是隔离。

### 2. 正确的部分：label 在模型输出后合入

模型 output schema 只有 `native` 和 `stronger`；wrapper 在读取模型 JSON 后才添加 `released_evaluator_label`，见 `score_evidence_with_codex.py:2023-2029`。这个顺序符合 unblinding 的逻辑目标，但只有在 scorer workspace 先被真正净化后才有效。

### 3. Comparison 目前不对称

`neurips_ed_track_minimal/scripts/audit_score_batch_slot.py:90-98` 只 flag：

- `released == success && native != S`

没有对称覆盖：

- `released == fail && native != F`

也没有把所有非一致组合统一送入独立 record-level review。新版本至少应记录：released success 对 F/U、released fail 对 S/U；其中 U 表示 evidence insufficiency，不表示 benchmark 错误。

### 4. Confirmed conflict 尚无正式 workflow

在 AppWorld/通用 reference scorer 中未发现一个正式 schema/runner，要求 reviewer 基于 retained artifacts 和明确 source pointers 单独判断：task、target construction、evaluator、oracle 或 reward wiring/aggregation 是否实际检查了不同 outcome。

因此：

- mismatch 不是 conflict；
- stronger F 不是 conflict；
- native S + stronger F 不是 conflict；
- 当前任何 generic audit flag 都不能当作 `confirmed benchmark conflict`。

## 必须的修复与重新接纳门槛

1. **版本化修复 native artifact contract**  
   从 scorer-visible decisive artifacts 中删除 `official TestTracker results`，并明确禁止任何直接或等价 released-result component output。

2. **分离 full retained bundle 与 sanitized scorer bundle**  
   full bundle 原样、不可变地保存 label/evaluator outputs；scorer bundle 排除 label、native score、TestTracker passes/failures/success、task evaluation result、run-summary success/reward、manifest outcome 字段、evidence-index label source，以及其他可等价重构结果的字段。

3. **保留独立重算所需的非 verdict inputs**  
   给 scorer 保留 official task/evaluator source、必要 target/oracle input、state schema、submitted answer、initial/final state 或 diff、API log、trace 和 run status。每个 case 做 allowlist/denylist leakage scan 与 artifact-sufficiency preflight。

4. **冻结明确三值聚合**  
   `all pass -> S; any established fail -> F; otherwise -> U`。

5. **source-only 修订 stronger registry**  
   处理 15 条 REVISE、5 条 REMOVE 和 12 个漏项；不得查看 outcome。由新 registry 重新生成 packet/checklist，并建立新的 versioned freeze；旧 freeze 只读保留。

6. **真正 blind scoring 后再 unblind**  
   先持久化 scorer 的 S/F/U 及 hash，再由独立本地过程加载 released label，做双向 comparison。

7. **另建 conflict adjudication**  
   mismatch queue 与 conflict queue 分离；confirmed conflict 必须有 record-level finding、retained-artifact pointers、official source pointers 和被检查 outcome 的明确差异说明。

## 本报告没有做的事

- 没有读取或披露这 68 个 case 的任何 agent outcome 或 per-record released label。
- 没有对任何运行记录给 S/F/U。
- 没有确认任何 benchmark conflict。
- 没有修改旧 draft、旧 freeze、stronger registry 或 scorer。

机器可读计数和 findings 见同目录 `audit_summary.json`。
