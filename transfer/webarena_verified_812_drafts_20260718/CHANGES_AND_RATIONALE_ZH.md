# WebArena-Verified draft 审核：修改内容与原因报告

## 结论摘要

本轮工作的核心是**补做 812 份 draft 的逐 case 内容审核，并修正审核结论和报告**，不是直接重写原始 draft。

- 已实际修改：语义审核工具、WebArena-Verified 专用审核规则、批处理与汇总工具、复核逻辑、测试和中文报告。
- 尚未实际修改：812 份原始 `checklist.yaml` / `checklist.json` draft 内容。
- 审核后的待办：486 份 draft 可接受；326 份需要后续重新生成或定点修订。
- 未改动：case packet、benchmark 运行产物、原始 LLM/API 审核凭证。
- 未执行：`neurips_ed_track_minimal` checklist score。

之所以没有直接改写 326 份 draft，是为了保持当前生成批次和原始审核凭证可追溯。应先记录问题和修改要求，再单独生成修订版、重新审核、冻结，最后才与 benchmark 运行产物关联并调用 score。

## 一、已经实际修改的内容

### 1. 增强通用 checklist reviewer

文件：`neurips_ed_track_minimal/scripts/review_case_checklist_with_codex.py`

修改内容：

- 增加可配置的 review item ID、experiment type 和 reviewer role。
- 根据指定 review item 动态构建输出 Schema，不再把 reviewer 固定到其他 benchmark 的检查项。
- 改为把审核 prompt、单个 case packet 和对应 draft 直接组成密封 stdin 输入。
- 审核环境使用只读 sandbox、临时配置、忽略用户配置，并禁用 shell/unified-exec。
- 保留旧参数的默认行为，避免破坏已有调用路径。

修改原因：

- WebArena-Verified 的 evaluator 结构和证据边界与其他 benchmark 不同，需要独立的检查项。
- 审核者必须只根据 case claim 和官方 evaluator 来源判断 draft，不能读取 benchmark 实际运行结果。
- 直接密封输入可以明确证明每次审核只看到该 case 的 packet 和 draft，符合“先写 claim，再运行 benchmark，最后 score”的系统设计。

### 2. 新增 WebArena-Verified 专用语义审核规则

文件：`neurips_ed_track_minimal/prompts/review_webarena_verified_checklist.prompt.md`

修改内容：定义九个逐 case 审核维度：

1. case 身份与范围；
2. 原生 user goal；
3. 官方 evaluator 语义；
4. evaluator 组合；
5. 决定性运行后证据；
6. 成功/失败/无法判定规则；
7. 来源支持指针；
8. stronger condition；
9. 最小性与无运行结果泄漏。

修改原因：

- 原先的 Schema/guardrail 检查只能证明 draft 格式正确和来源指针存在，不能证明内容推理正确。
- WebArena-Verified 存在 sparse Pydantic 字段、response normalization、last-event-only、URL/query normalization 等容易误写的 evaluator 细节，需要逐项核对。
- 专用规则还明确：batch 要求保留某项运行产物，不等于该产物对每个 case 都是决定性证据。

### 3. 新增全量语义审核批处理和汇总工具

文件：

- `neurips_ed_track_minimal/scripts/run_webarena_verified_draft_semantic_reviews.py`
- `neurips_ed_track_minimal/scripts/summarize_webarena_verified_draft_semantic_reviews.py`

修改内容：

- 支持 812 个 case 的可恢复批处理、重试、状态记录和最高 72 并发。
- 每个 case 独立保存 `review.json`、API response、调用元数据、attempt、状态和日志。
- 生成逐 case JSON/CSV/Markdown 索引，并校验 review Schema、sidecar 和总数。

修改原因：

- 用户要求逐一审核，而不是抽样或只做文件完整性检查。
- 可恢复批处理避免中断或提高并发时丢失已完成的有效结果。
- 独立 sidecar 让每个裁决都能追溯到对应输入、模型、配置和原始输出。

### 4. 新增源码口径复核层

文件：`neurips_ed_track_minimal/scripts/adjudicate_webarena_verified_draft_semantic_reviews.py`

修改内容：

- 对 812 个模型初判进行最终复核并生成 adjudication。
- 将 467 个模型 accept 保留为可接受。
- 确认 326 个模型 revise 确有 packet/源码支持的问题。
- 推翻 19 个仅要求显式重复 `retrieved_data: null` 的误报。
- 生成 486 accept / 326 revise 的最终逐 case 裁决。
- 把人类可读 Markdown 输出改为中文。

修改原因：

- 独立模型 reviewer 可能对 sparse-field 语义过严，不能把所有模型判定不经复核地当作最终结论。
- 对非 RETRIEVE 任务，发布版 normalizer 会把省略的 `retrieved_data` 和显式 null 归一化为相同值；仅省略该字段不会改变得分，因此不应强迫 draft 重复无影响条件。
- 复核层同时保留模型原始输出和最终裁决，避免覆盖原始证据。

### 5. 增加 reviewer 回归测试

文件：`tests/unit/test_case_checklist_model_review.py`

修改内容：覆盖动态 review item、密封 stdin、Schema、兼容默认值、失败处理和 sidecar 等行为。

修改原因：防止后续修改重新引入读取外部文件、Schema 数量不一致或 reviewer 配置串线等问题。

测试结果：11 项测试全部通过。

### 6. 修正并中文化审计报告

文件：

- `transfer/webarena_verified_812_drafts_20260718/AUDIT.md`
- `transfer/webarena_verified_812_drafts_20260718/_audit_report.json`
- `transfer/webarena_verified_812_drafts_20260718/semantic_reviews_gpt56_xhigh_v1/SEMANTIC_ADJUDICATION.md`

修改内容：

- 将旧的总体结论从“全部 PASS”改为“确定性/来源证明通过，但内容审核需要修改”。
- 加入 812 个逐 case 审核的完整统计、边界、模型配置、哈希、19 个推翻项和问题类别。
- 最终结果改为 486 份可接受、326 份需修改。
- 总审计报告和逐 case 最终裁决报告改为中文。
- `_audit_report.json` Schema 从 v1 更新为 v2，并加入 `semantic_review` 机器可读对象。

修改原因：旧报告的 PASS 只依据 Schema、guardrail、来源指针和泄漏扫描，不能代表 812 份 draft 的内容都正确。逐 case 语义审核发现真实内容问题后，继续保留“全部 PASS”会误导后续冻结和 score 流程。

## 二、为什么 326 份 draft 需要后续修改

下表给出需要修改的内容和原因。类别计数允许重叠，同一个 case 可能同时包含多类问题。

| 问题类别 | Case 数 | 应修改什么 | 为什么必须修改 |
|---|---:|---|---|
| 成功/失败/无法判定规则 | 287 | 按官方 evaluator 重写 `success_if`、`fail_if`、`undecided_if`，消除遗漏和重叠 | 错误的决策分区会把本来可以明确判定的结果误判为无法判定，或把 evaluator failure 误判为成功 |
| 最小性或内部一致性 | 250 | 删除重复、假设性或互相冲突的条件，只保留重建官方检查所需内容 | Draft 应描述 benchmark 实际 claim，不应加入不会影响官方结果的通用运行条件 |
| 非决定性或替代产物 | 199 | 从 native 决定性证据中删除无关 `network.har`、TaskEvalResult 或替代产物 | 仅有 AgentResponseEvaluator 的 case 通常可由完整 `agent_response.json` 判定；无关产物缺失不应令结果变成无法判定 |
| Response 归一化或期望值 | 128 | 修正 expected value、array/schema 比较、null/empty 归一化和字段比较范围 | Draft 必须精确复现发布版 comparator；否则后续 score 检查的是另一个 claim |
| Network evaluator 语义 | 106 | 补全完整 URL normalization、query 处理、base64 decode、忽略参数、status/post data 和 last matching event 规则 | 少写任何一个过滤或归一化步骤都可能让 draft 选择错误事件或比较错误 URL |
| Response parser 或 sparse-field 语义 | 76 | 补充 code-block/JSON 提取、`performed_operation` alias 和 `model_fields_set` 的稀疏字段行为 | 发布版只比较配置中实际设置的字段，并存在旧字段 fallback；错误描述会改变可通过响应集合 |
| 产物完整性或来源证明 | 18 | 对真正需要 HAR 的 case 补充完整性、截断、身份、provenance 和可解析性要求 | 不完整或无法归属到该 task 的 trace 不能可靠重建官方 NetworkEventEvaluator |
| Stronger condition | 17 | 删除无 packet 支持、不可测量或与 native claim 混淆的附加条件 | Stronger condition 必须独立、可测量且有固定 packet 来源，不能依赖外部常识或未保留状态 |
| Evaluator 组合 | 10 | 明确所有 evaluator 必须同时为 1.0，以及相同过滤器是否选择同一最终事件 | 错误地把多个 evaluator 当作任选其一或独立选事件，会改变 task-level score 语义 |
| User goal 范围或格式 | 7 | 恢复被遗漏或改写的所有权、精确 key、单位、数量和输出格式 | Draft 的 claim 首先必须忠实覆盖用户原始任务，不能缩小或改变请求 |
| 无依据或超范围 claim | 1 | 删除 packet 中不存在的外部事实 | 系统设计明确不假设 packet 之外的知识，无法用固定 case 来源支持的 claim 不应进入 checklist |

## 三、代表性 case：应修改什么、为什么

### Case 0

- 应修改：从 native `decisive_artifacts` 和对应决策规则中删除 `network.har`，只保留完整 `agent_response.json`。
- 原因：该 case 只有 AgentResponseEvaluator，网络 trace 不参与官方比较；HAR 缺失不应导致 native result 无法判定。

### Case 9、51、87

- 应修改：在 response 解析规则中加入 `performed_operation` 可在缺少 `task_type` 时提供 fallback；同时删除无关 HAR 依赖。
- 原因：这是发布版 parser 的实际兼容行为。遗漏 alias 会错误地扩大失败响应集合。

### Case 32、109、176、230、443、563、585

- 应修改：分别恢复精确输出 key/单位、月份和计数 key、“my”的所有权范围、数值要求、原始术语、标题/副标题/项目符号结构以及不应进入值中的标点。
- 原因：这些 draft 改写或遗漏了 user goal 的决定性格式/范围，导致 checklist claim 与原始任务不一致。

### Case 47

- 应修改：删除“额外字段会被忽略”的错误描述，按实际 normalization/comparison 说明额外字段是否保留和参与比较。
- 原因：发布版 normalization 会保留并比较相关字段；现有描述会允许官方 evaluator 实际不接受的响应。

### Case 294

- 应修改：准确描述 `git@__SSH_HOST__...` 期望 URL 的 normalization 和条件性 environment fallback，并仅在该条件实际需要时把 HAR 作为决定性证据。
- 原因：该 case 的 URL 解析存在环境占位符分支，不能简单归为纯 response-only，也不能无条件要求 HAR。

### Case 319

- 应修改：明确说明在 packet 所代表的发布版 sparse-field 行为下，native success 实际不可达；完整且可信的响应只能得到 failure，证据丢失才是 undecided。
- 原因：原始配置的 `model_fields_set` 只有 `task_type` 和 `status`，但 expected normalization 增加 `retrieved_data`，actual normalization 又省略该 key，结构比较会固定报告缺失 key。现有 draft 错误声称存在能通过的响应。

### Case 558

- 应修改：删除“Inception 是 2010 年电影”及其 stronger condition。
- 原因：该外部事实不在 case packet 中，系统不能假设 reviewer 或 scorer 使用 packet 外知识。

### Case 738

- 应修改：删除没有 packet 来源支持的坐标到实体映射事实，或把条件限定为 packet 内可直接证明的内容。
- 原因：仅凭坐标无法在固定证据边界内证明所声明实体。

### Case 746

- 应修改：明确三个 member evaluator 的 URL/method filter 完全相同，因此三者选择的是同一个最后匹配 POST，再分别比较该事件与三个 expected `user_id`。
- 原因：现有 draft 暗示三个 evaluator 可以各自选择不同 POST，错误改变了 last-event-only 的组合语义。

## 四、19 个没有要求修改的模型误报

Case：156、162、326、356、401、405、429、612、630、649、653、654、672、693、697、719、722、734、744。

这些 case 的模型初判都要求 draft 显式写出 `retrieved_data: null`。源码复核后未要求修改，原因是：

- 它们都是 MUTATE 或 NAVIGATE，而不是 RETRIEVE；
- 原始配置中的 `retrieved_data` 明确为 null；
- 发布版 non-RETRIEVE normalizer 会把缺失值和显式 null 都归一化为 null；
- Draft 已经给出 task type、status 和发布版 parser/normalizer 限定；
- 省略该无影响字段不会改变任何可观察得分结果。

因此，这 19 个 case 最终从“需修改”改为“可接受”，避免为纯文字冗余重新生成 draft。

## 五、明确没有修改的内容

- 没有改写任何一个原始 WebArena-Verified case packet。
- 没有改写 812 份原始 draft 的 `checklist.yaml` 或 `checklist.json`。
- 没有把 benchmark 实际运行产物提供给 drafter 或 semantic reviewer。
- 没有改写 benchmark 的 agent response、HAR、receipt、manifest 或 native score。
- 没有调用 `neurips_ed_track_minimal` checklist score。
- 没有用新的审核结论覆盖原始 `review.json` 或 API response；最终裁决保存在单独 adjudication 层。

## 六、验证结果

- Draft 生成：812/812 完成，0 failed，0 warning。
- 逐 case 语义审核：812/812 完成，0 最终失败。
- 最终逐 case 裁决：812 行且 case ID 唯一。
- 最终统计：486 可接受，326 需修改。
- 每个 revise case 都至少有一个 blocking finding 和 required change。
- 19 个 override 均通过 non-RETRIEVE、显式 null、无其他 finding 的 fail-closed 验证。
- Reviewer 相关单元测试：11/11 通过。
- Draft LLM phase 全部为 `draft`；审核 LLM phase 全部为 `checklist_model_review`；没有 score phase。

## 七、建议的下一步

1. 仅对最终标记为“需修改”的 326 个 case 生成修订版 draft；不要覆盖本批原始文件。
2. 使用本报告和逐 case `review.json` 中的 `required_change` 作为修订输入，但继续禁止读取 benchmark 实际运行结果。
3. 对 326 份修订版重新执行同一套逐 case 语义审核和源码口径复核。
4. 全部通过后冻结 checklist。
5. 等 WebArena-Verified benchmark 运行产物完整后，再关联冻结 checklist 并调用 `neurips_ed_track_minimal` score。

逐 case 最终状态见 `semantic_reviews_gpt56_xhigh_v1/SEMANTIC_ADJUDICATION.md`。326 个需修改 case 的完整中文上下文见 `semantic_reviews_gpt56_xhigh_v1/zh_revision_report_v1/DRAFT_REVISION_DETAILS_ZH.md`：每个 case 都先说明原始任务、benchmark 如何测、原始 draft 写了什么，再列出逐 finding 修改位置、修改原因和具体改法。机器可读中英对照位于同目录的 `draft_revision_details_enriched_zh.json`、`draft_revision_context_zh.csv` 和 `draft_revision_details_zh.csv`。
