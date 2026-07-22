# WebArena-Verified：326 个需修改 draft 的逐 case 修改说明

- 需修改 case 数：1
- 具体 blocking finding 数：3
- 每条均列出：修改位置、为什么修改、应如何修改。
- 中文内容是原始英文 finding/required_change 的忠实翻译；英文原文保留在同目录 JSON/CSV 中。
- 本报告是修改要求，不表示原始 draft 已经被改写。

## Case 0

原始审核记录：`semantic_reviews_gpt56_xhigh_v1/0/review.json`

### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：尽管该案例只有一个 `AgentResponseEvaluator`，且预期内容是一个非 URL 的产品名称，但 `network.har` 仍被列为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并仅使用完整的 `agent_response.json` 作为重建已配置检查所需的唯一最小证据。

### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：failure 和 undecided 规则错误地要求通过接受所保留的 trace 来判定原生 success。
- 应如何修改：success 和普通 failure 应以对完整已提交响应的正式评估为依据。仅当影响 `agent_response.json` 的丢失、截断、损坏或来源不确定时，才判定为 undecided；完整但无效或为 null 的响应应判定为 failure。

### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_overhead`
- 为什么修改：对于仅包含一个响应 evaluator 的检查清单，trace artifact 及其重复的编排条件增加了非决定性范围。
- 应如何修改：删除 trace artifact 和 trace 专用的判定措辞，同时保留响应解析、normalization、schema、无序比较以及所有 evaluator 都必须通过的语义。
