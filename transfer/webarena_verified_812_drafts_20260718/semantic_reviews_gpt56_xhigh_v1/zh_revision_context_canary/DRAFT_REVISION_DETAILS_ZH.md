# WebArena-Verified：1 个需修改 draft 的逐 case 修改说明

- 需修改 case 数：1
- 具体 blocking finding 数：3
- 每个 case 均依次说明：原始 case、benchmark 如何测、原始 draft、修改位置、修改原因和具体改法。
- 原始 case 和 benchmark 摘要仅来自 case packet、官方 task 配置及已完成的源码口径 review，不读取实际运行结果。
- 本报告是修改要求，不表示原始 draft 已经被改写。

## Case 0

### 原本 case 是什么

原始用户任务是在 `shopping_admin` 站点检索“2022 年销量最高的前 1 个产品名称”，官方 instruction 为 `Get the top-1 best-selling product name(s) in 2022`。该任务的 task type 是 `RETRIEVE`，revision 为 `2`。

### Benchmark 怎么测

任务仅配置一个 `AgentResponseEvaluator`，用于按 released parsing 和 normalization 规则比较最终响应；其 evaluator-considered expected 字段为 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: ["Quest Lumaflex™ Band"]`。`retrieved_data` 采用 array-of-string schema，且 `ordered: false`，因此按无序数组比较，但仍须恰好是该单元素值，不能缺失、为 null、换成其他产品或包含额外项；sparse expected 未显式设置 `error_details`，所以 materialized default `error_details: null` 不参与比较。本任务没有基于 last-event 的 evaluator 语义；task score 的组合规则是所有 evaluator score 均须等于 `1.0`，此处即唯一的 `AgentResponseEvaluator` 必须得 `1.0`，官方得分字段为 `TaskEvalResult.score`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 `TaskEvalResult.score` 为 `1.0`：唯一的 `AgentResponseEvaluator` 在无错误完成评估后，对规范化响应中的 `task_type: RETRIEVE`、`status: SUCCESS` 及无序单元素 `retrieved_data` 值 `"Quest Lumaflex™ Band"` 给出 `1.0`，且不存在 compared-key mismatch。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将 trace 被接受为 `NetworkTrace`、评估上下文与 orchestration 完成而无 task-level error 纳入成功条件。draft 将解析或 normalization 失败、字段或产品值不匹配、缺失/null/额外结果、必需输入不可读取或解析，以及 orchestration/evaluator error 归为 failure；若证据不能确定最终响应或 trace 是否被接受且没有保留的 `TaskEvalResult`，则归为 undecided。其 `stronger.additional_conditions` 为空，没有非空 stronger conditions。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：尽管该案例只有一个 AgentResponseEvaluator，且预期项是非 URL 的产品名称，network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 用作重建已配置检查的唯一最小证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：failure 和 undecided 规则错误地要求接受所保留的 trace，才能判定原生 success。
- 应如何修改：根据对完整提交响应的已发布评估来判定 success 和普通 failure。仅当影响 agent_response.json 的丢失、截断、损坏或来源不确定性发生时，才使用 undecided；将完整但无效或为 null 的响应视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_overhead`
- 为什么修改：对于仅含一个响应 evaluator 的检查清单，trace artifact 及其重复的编排条件增加了非决定性范围。
- 应如何修改：删除 trace artifact 和 trace 特定的判定措辞，同时保留响应 parsing、normalization、schema、无序比较以及所有 evaluator 都必须通过的语义。
