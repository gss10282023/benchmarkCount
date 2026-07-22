# WebArena-Verified：326 个需修改 draft 的逐 case 修改说明

- 需修改 case 数：326
- 具体 blocking finding 数：932
- 每个 case 均依次说明：原始 case、benchmark 如何测、原始 draft、修改位置、修改原因和具体改法。
- 原始 case 和 benchmark 摘要仅来自 case packet、官方 task 配置及已完成的源码口径 review，不读取实际运行结果。
- 本报告是修改要求，不表示原始 draft 已经被改写。

## Case 0

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索 2022 年销量最高的 top-1 产品名称，即 “Get the top-1 best-selling product name(s) in 2022”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查规范化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，并按 `ordered=false` 和字符串数组 schema 将 `retrieved_data` 与无序单元素期望值 `["Quest Lumaflex™ Band"]` 精确比较，不允许缺项或多项。稀疏配置未显式设置 `error_details`，因此物化产生的默认 `error_details: null` 不参与比较；本 case 也没有 filter、last-event 或 `NetworkEventEvaluator` 语义。只有该 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误完成，并使规范化响应的 `task_type`、`status` 和无序 `retrieved_data` 分别匹配 `RETRIEVE`、`SUCCESS` 与 `"Quest Lumaflex™ Band"`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将解析、规范化、字段或产品值不匹配以及输入、编排或 evaluator 错误列为 failure。它把无法确认最终响应、trace 是否被接受或评估是否完成且没有 `TaskEvalResult` 定论列为 undecided；`stronger.additional_conditions` 为空。

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

## Case 1

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点返回 2022 年第一季度销量最高的 top-1 品牌名称，即 “Get the top-1 best-selling brand name(s) in Quarter 1 2022”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查规范化后的 `task_type: RETRIEVE`、`status: SUCCESS`，并依据字符串数组 schema 和 `ordered=false`，将 `retrieved_data` 与无序单元素期望值 `["Sprite"]` 精确比较。非严格实际值规范化可把非 list 的 `retrieved_data` 包装为单元素 tuple；稀疏配置没有显式比较物化默认字段 `error_details`，也没有 filter、last-event 或网络事件检查。只有这个 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误完成，规范化响应匹配 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 无序精确匹配唯一字符串 `Sprite`，由此得到成功状态和 `TaskEvalResult.score: 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；结构、字段或集合不匹配以及 evaluator/编排错误或非 `1.0` 得分被列为 failure，证据缺失、截断或不可读而无法确定响应或评估完成情况被列为 undecided。其非空 stronger condition 为 `schema_conformant_retrieved_data_array`：原始 `retrieved_data` 必须是仅含 `Sprite` 的 JSON 数组，而不能是由 evaluator 强制转换的标量，决定性 artifact 是 `agent_response.json`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：尽管唯一配置的 evaluator 读取 agent_response_raw，且未对此案例执行任何网络事件检查，network.har 仍被列为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 保留为唯一最小充分 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_based_decision_outcomes`
- 为什么修改：undecided/failure 规则将 HAR 的可用性或格式错误视为与结果相关，尽管重建已配置的响应检查并不需要 HAR 证据。
- 应如何修改：仅在 agent_response.json 证据缺失、损坏、不可读或不可信时使用 undecided；将完整但无效的响应，或应用已配置 evaluator 时产生的任何错误归类为 failure，不得使判定取决于所保留的 HAR。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_checklist`
- 为什么修改：包含第二个与评分无关的 artifact，违反了所要求的紧凑最小证据结构。
- 应如何修改：删除 HAR artifact 问题以及相关的 HAR 特定判定措辞，同时保留响应 evaluator 语义和更强条件。

## Case 2

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点取得 2022 年第一季度销量最高的 top-1 产品类型名称，即 “Get the top-1 best-selling product type name(s) in Quarter 1 2022”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中唯一的 `AgentResponseEvaluator` 解析响应字典或 JSON 响应字符串（包括从 fenced block 提取的 JSON），并只规范化稀疏配置选中的 `task_type`、`status` 和 `retrieved_data`；缺少 `task_type` 时可接受 `performed_operation`。前两项必须匹配 `RETRIEVE` 和 `SUCCESS`，而 `retrieved_data` 按字符串数组 schema 与 `ordered=false` 必须恰好包含一个字符串，该字符串可为 `Digital Watch`、`Band`、`Stasis Ball` 或 `Yoga Strap`。未选中的 `error_details` 不参与比较，也没有 filter、last-event 或网络事件 evaluator；唯一 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求评估无错误完成、唯一的 `AgentResponseEvaluator` 得分为 `1.0`，且规范化响应匹配 `RETRIEVE`、`SUCCESS` 和恰含一个字符串的无序 `retrieved_data`，该字符串可为 `Digital Watch`、`Band`、`Stasis Ball` 或 `Yoga Strap`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把结构、类型、状态、基数或候选值不匹配及 trace、evaluator 或编排错误列为 failure。它把缺少可读响应或 trace、同时也没有足以确定分数的 `TaskEvalResult` 列为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_network_trace`
- 为什么修改：尽管唯一配置的 evaluator 仅比较 agent response，且任何以数据包表示的网络事件检查都无法改变此案例的已配置比较，network.har 仍被指定为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将 agent_response.json 设为最小充分的保留 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：规则要求保留 trace 才能判定 success，并允许其缺失导致 undecided，尽管可根据完整的 agent response 重建已配置的响应检查。
- 应如何修改：从 success_if、fail_if 和 undecided_if 中移除 trace 保留和 trace parsing 条件；仅当影响所提交响应或等效结果证据的丢失、损坏或来源故障发生时，才使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`non_minimal_trace_branches`
- 为什么修改：冗余的 trace artifact 和三个与 trace 相关的判定分支，使检查清单超出了此案例所需的证据范围。
- 应如何修改：采用紧凑的仅响应证据路径，同时保留通用规则：任何产生非 1.0 分数的 evaluator 或 task error 均为原生 failure。

## Case 4

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点返回 2023 年 1 月销量最高的 top-3 产品名称，即 “Get the top-3 best-selling product name(s) in Jan 2023”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应进行基于字符串数组 schema 的解析和规范化，要求 `task_type: RETRIEVE`、`status: SUCCESS`，并按 `ordered=false` 将 `retrieved_data` 与无序三项 multiset `["Impulse Duffle", "Overnight Duffle", "Hawkeye Yoga Short-32-Blue"]` 精确比较，包括 multiplicity，不能缺少或增加元素。稀疏 expected 未显式包含 `error_details`，且没有 filter、last-event 或网络事件检查。只有该 evaluator 得分为 `1.0` 时，组合后的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得分为 `1.0`：规范化后的 `task_type` 和 `status` 分别为 `RETRIEVE` 与 `SUCCESS`，`retrieved_data` 精确等于无序三项 multiset `["Impulse Duffle", "Overnight Duffle", "Hawkeye Yoga Short-32-Blue"]`，最终 `TaskEvalResult` 为成功状态且得分 `1.0`。它列出的决定性 artifacts 是 `agent_response.json` 和 `retained TaskEvalResult evaluation record`；非结构化响应、字段或 multiset 不匹配以及 evaluator/编排错误被列为 failure。没有完整且可归属于 task 4 的响应或 `TaskEvalResult`、因而无法确定提交值或官方得分时被列为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal-task-result-artifact`
- 为什么修改：检查清单同时指定了 agent_response.json 和保留的 TaskEvalResult evaluation record，尽管唯一配置的 AgentResponseEvaluator 完全根据响应和已发布配置得出其针对此案例的结果。
- 应如何修改：将完整且可归属于该 task 的 agent_response.json 设为唯一决定性 artifact。将 EvaluatorResult 和 TaskEvalResult 分数视为应用已发布语义所产生的确定性结果，并仅在该响应 artifact 丢失或损坏时使用 undecided。

## Case 5

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索 2023 年 1 月销量最高的 top-1 产品类型名称，即 “Get the top-1 best-selling product type name(s) in Jan 2023”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它通过字符串或 code-block JSON 提取及规范化，检查稀疏 expected 中的 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: ["Duffle"]`；缺少 `task_type` 时支持 `performed_operation` alias。`retrieved_data` 使用字符串数组 schema 和 `ordered=false`，必须是精确的无序规范化单元素结果；默认产生的 `error_details` 及其他未配置原始键不参与比较，也不存在 filter、last-event 或网络事件检查。唯一 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`；evaluator error 对应 `0.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 在响应规范化为 `task_type: RETRIEVE`、`status: SUCCESS` 和精确无序单元素 `["Duffle"]` 后得分 `1.0`，从而使 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将不可解析的响应、类型或状态不匹配、检索数据缺失/错误/多余，以及输入、HAR、上下文构造、编排或 evaluator 错误列为 failure。证据缺失、不可读、截断或无法归属于该次运行，以致不能确定响应比较或 HAR 有效性时被列为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unsupported_har_native_semantics`
- 为什么修改：尽管该案例只有一个 AgentResponseEvaluator，且其与评分相关的提取和比较使用响应，原生规则仍额外将 HAR 有效性作为先决条件。
- 应如何修改：从原生 success 和 failure 语义中移除 HAR parsing 或有效性要求；保留已发布的响应 parsing、normalization、schema、无序比较以及 task 级分数组合。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_har_artifact`
- 为什么修改：尽管仅凭 agent_response.json 即可重建唯一配置的 evaluator 检查，network.har 仍被指定为决定性证据。
- 应如何修改：将完整的 agent_response.json 保留为唯一决定性的原生 artifact，并从 decisive_artifacts 中移除 network.har。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har_misclassification`
- 为什么修改：规则将 HAR 有效性视为 success 的必要条件，并将 HAR 缺失或格式错误视为原生 failure 或 undecided，从而扩大了已配置 predicate 的范围。
- 应如何修改：仅根据 AgentResponseEvaluator 结果判定 success 和 failure，并仅在重建该结果所需的已保留 agent response 丢失、损坏或来源故障时使用 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_trace_branch`
- 为什么修改：HAR artifact 和三个相关的判定规则分支增加了不必要的原生审查范围。
- 应如何修改：删除 HAR artifact 以及所有依赖 HAR 的 success、failure 和 undecided 措辞，同时保留响应比较和证据完整性之间的区别。

## Case 6

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：获取 2023 年销量最高的前 2 个产品名称。任务要求返回两个产品名。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它对最终响应进行解析和归一化，并检查显式配置的 `task_type`、`status`、`retrieved_data`，其中缺失的 `task_type` 可由 `performed_operation` 提供。预期分别为 `RETRIEVE`、`SUCCESS`，以及符合字符串数组 schema 的无序二元素结果：`"Sprite Yoga Strap 6 foot"` 加上 `"Overnight Duffle"` 或 `"Ida Workout Parachute Pant-29-Purple"`；比较要求元素数量精确，物化默认值 `error_details` 不属于显式比较字段。没有断言或 evaluator error 时该 evaluator 得分为 `1.0`；由于它是唯一 evaluator，只有所有 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是无错误完成官方评估，归一化响应匹配 `task_type=RETRIEVE`、`status=SUCCESS` 和上述无序二元素 `retrieved_data`，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把响应精确匹配、HAR 可解析且评估无输入/配置/编排错误列为 success；响应无效、字段或结果不匹配、HAR 缺失或不可解析、任何非 `1.0` 分数列为 failure。它将响应或网络轨迹在运行后缺失或损坏、且没有留存 `TaskEvalResult` 的情形列为 undecided，同时明确已记录的空输入、缺失输入或官方评估错误属于 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：对于唯一配置的 evaluator 比较 agent_response.json 的案例，network.har 被错误地指定为决定性的运行后证据。
- 应如何修改：仅保留完整的 agent_response.json 作为原生决定性 artifact。移除 HAR 特定的 artifact 问题，并使用已发布的响应提取、normalization 和比较语义重建已配置检查。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_trace_conditions`
- 为什么修改：专门的网络 trace success 和 failure 条款增加了通用的运行时/配置应急条件，而表述此案例唯一配置的比较并不需要这些条件。
- 应如何修改：删除网络特定的 success 和 failure 条款，并围绕完整响应、单个 evaluator 分数、task 级组合以及仅针对证据丢失的 undecided 处理来整合检查清单。

## Case 8

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，找出距 Carnegie Mellon University 驾车距离不超过 `5 km` 的所有国际机场。要求返回对象列表，每个对象包含 `"name"`、`"state"` 和 `"postcode"`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，检查解析和归一化后的显式字段是否为 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR`、`retrieved_data=null`，其结果 schema 为 `{"type":"null"}`；遗漏、`null` 或空的 `retrieved_data` 均归一化为 `null`。物化默认值 `error_details` 不属于显式比较字段，也没有配置用于验证 OSRM 请求或距离的网络 evaluator。该 evaluator 无断言或错误时得分 `1.0`；因其为唯一 evaluator，所有 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求响应归一化为 `RETRIEVE`、`NOT_FOUND_ERROR` 和 `null` 的 `retrieved_data`，唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；响应匹配、轨迹可解析且评估完成被列为 success，响应缺失或非对象、字段不匹配、非空 `retrieved_data`、轨迹解析或编排错误被列为 failure，而留存响应或 HAR 在运行后不可用或损坏且无官方结果时列为 undecided。非空 stronger condition `substantiate_osrm_airport_result` 进一步要求 `retrieved_data` 是完整列表（无符合项时为空列表），包含所有且仅包含 `5 km` 内的国际机场及三个指定字段，并要求 HAR 留存候选搜索和 OSRM 路线证据，以审查距离与完整性。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_not_decisive`
- 为什么修改：尽管唯一配置的 evaluator 仅比较最终响应，且预期的 retrieved_data 为 null，network.har 仍被表述为必需的决定性原生证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har。仅为更强的 OSRM 佐证条件保留它，因为其内容在该条件下确实相关。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`native_rules_depend_on_har`
- 为什么修改：原生规则要求可解析的 HAR 才能判定 success，并将 HAR parsing failure 视为原生 failure，或将运行后 HAR 丢失视为 undecided，尽管仅凭 agent_response.json 即可重建已配置的响应比较。
- 应如何修改：移除依赖 HAR 的原生 success、failure 和 undecided 条款。仅当所保留的完整 agent response 丢失、损坏、不完整或发生来源故障时，才使用 undecided。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`retrieved_data_rule_overlap`
- 为什么修改：fail 规则对非 null 的 retrieved_data 的无条件引用，与允许 retrieved_data 为空的 success 规则重叠，因为空列表在已发布的 normalization 之前为非 null，但经过 normalization 后为 null。
- 应如何修改：明确规定：当 retrieved_data normalization 后为非 null 值，或导致 normalization/comparison error 时发生 failure；同时对省略、null 或空值保持 success。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal_or_coherent`
- 为什么修改：不必要的原生 HAR artifact 和相互重叠的 retrieved_data 规则，使检查清单不够精简且内部含义不明确。
- 应如何修改：将 agent_response.json 用作唯一的原生决定性 artifact，并使 retrieved_data 的 success/failure 边界取决于其 normalization 后的值。

## Case 9

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM driving directions，找出距 Carnegie Art Museum 驾车距离不超过 `30 km` 的所有国际机场。输出须为对象列表，每项包含 `"name"`、`"state"` 和 `"postcode"`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 在字符串或代码块 JSON 提取后检查显式配置的 `task_type`、`status`、`retrieved_data`；`task_type` 缺失时接受 `performed_operation` 作为旧别名。预期为 `RETRIEVE`、`SUCCESS`，以及按对象数组 schema 归一化后与 `[{"name":"Pittsburgh International Airport","state":"Pennsylvania","postcode":"15231"}]` 精确匹配的无序结果，数量和记录字段也必须精确；非空的非列表 `retrieved_data` 会先被包成单元素序列，物化默认 `error_details` 和其他未配置顶层字段不比较。无 failure assertion 或 evaluator error 时 evaluator 得分 `1.0`；它是唯一 evaluator，因此其分数为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是响应归一化为 `RETRIEVE`、`SUCCESS` 和恰好一个 Pittsburgh International Airport 记录，唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；精确响应匹配和可重建的无错误评估列为 success，空或非对象响应、缺失或错误字段、不同/重复/额外记录或字段，以及响应、HAR、上下文或 evaluator 错误列为 failure；响应或 HAR 缺失、截断或无法归属于本次运行且无留存结果时列为 undecided。它还提出两个非空 stronger conditions：`literal-list-response-shape` 要求原始 `retrieved_data` 本身是 JSON 对象数组而非依靠单例强制转换，`osrm-route-evidence` 要求 `network.har` 含 Carnegie Art Museum 至 Pittsburgh International Airport 的成功 OSRM directions 响应且距离不超过 `30,000` 米。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_parsing_semantics_incomplete`
- 为什么修改：原生规则未说明已发布的字符串/代码块 JSON 提取行为，也未说明当 task_type 缺失时 performed_operation 会提供 task_type；因此，当前关于 task_type 缺失即 failure 的措辞过于宽泛。
- 应如何修改：说明已发布的响应提取行为、performed_operation 回退机制，以及稀疏的原始配置明确只配置 task_type、status 和 retrieved_data，因此不比较采用默认值的 error_details 和其他顶层字段。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_har`
- 为什么修改：尽管唯一配置的 evaluator 仅提取 agent_response_raw，且没有网络事件 predicate，network.har 仍被错误地指定为决定性的原生 artifact。
- 应如何修改：仅将完整且可归属的 agent_response.json 保留为原生决定性证据。仅在更强的 OSRM 条件下保留 network.har。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_native_decisions`
- 为什么修改：success 和 undecided 规则使原生分类取决于 HAR 重建，导致无关的 HAR 缺失时可能产生 undecided。
- 应如何修改：从原生 success、failure 和 undecided 规则中移除 HAR 可用性和有效性要求。仅当响应或明确等效的保留结果丢失、损坏或发生来源故障时，才使用原生 undecided；将完整但无效的响应，以及 evaluator 可见的不匹配或错误视为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_apparatus`
- 为什么修改：额外的原生 HAR artifact 将冗余的 trace 要求扩散至多条规则，使检查清单不够紧凑且内部不够连贯。
- 应如何修改：删除原生 HAR artifact，并围绕唯一的响应 evaluator 整合原生判定，同时仅将 HAR 保留为单独的更强 OSRM 条件的证据。

## Case 12

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：报告商店截至目前收到的评论中，提及字符串 `"satisfied"` 的评论总数。任务请求的是一个总数。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它在字符串或代码块 JSON 解析后检查显式配置的 `task_type`、`status`、`retrieved_data`；`task_type` 可使用 `performed_operation` 别名。预期为 `RETRIEVE`、`SUCCESS`，以及按数字数组 schema 归一化后无序精确等于单元素数组 `[2]` 的结果；额外原始字段不比较，物化默认 `error_details` 也不是显式比较字段。比较无断言时 evaluator 得分 `1.0`，而 `TaskEvalResult.create` 要求每个已配置 evaluator 都为 `1.0`；本案只有一个 evaluator。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求解析和归一化后的响应匹配 `RETRIEVE`、`SUCCESS` 与无序数字单元素结果 `[2]`，唯一 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把响应精确匹配、trace 可接受且评估无错误列为 success；响应结构无效、字段或数据缺失/错误/多余，以及响应、trace、上下文、evaluator 或编排错误列为 failure。响应或 trace 在运行后缺失、截断或无法关联到被评估运行，且无法确认当时输入状态时，被列为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`trace_broadens_native_semantics`
- 为什么修改：检查清单将网络 trace parsing 和条件式 URL 恢复作为原生 success 的组成部分，尽管唯一配置的 evaluator 比较最终响应，且预期的 retrieved value 为数字。
- 应如何修改：从原生 evaluator 描述中移除网络 trace 接受和环境回退要求，并保留已发布的 AgentResponseEvaluator parsing、normalization、schema、无序比较和评分语义。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：network.har 因批处理 artifact contract 和假设的回退机制而被列为决定性证据，但仅凭 agent_response.json 即可重建唯一配置的检查。
- 应如何修改：对于此案例，仅将完整的 agent_response.json 保留为决定性的原生证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_gate`
- 为什么修改：判定规则要求接受 trace 才能判定 success，将 trace parsing error 归类为原生 failure，并将 trace 保留丢失视为 undecided，尽管并未配置 NetworkEventEvaluator。
- 应如何修改：根据已发布的响应比较及其 evaluator 分数判定 success 和 failure；仅当 agent_response.json 丢失、损坏或发生来源故障时，才使用 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nondecisive_trace_language`
- 为什么修改：对于仅含响应 evaluator 的案例，trace artifact 及其重复的 parsing/回退条件使检查清单不够精简。
- 应如何修改：删除非决定性的 trace artifact 和所有依赖它的 trace 条款，同时保留简洁的响应比较和评分规则。

## Case 13

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：报告商店截至目前收到的评论中，提及字符串 `"decent"` 的评论总数。任务请求的是一个总数。

### Benchmark 怎么测

只配置一个 `AgentResponseEvaluator`，且没有 `NetworkEventEvaluator`；它可从响应文本提取 fenced JSON 并解码，只归一化稀疏 expected 中显式存在的字段，并接受 `performed_operation` 作为旧式 `task_type` 键。预期为 `task_type=RETRIEVE`、`status=SUCCESS` 和按数字数组 schema 归一化后无序精确等于 `[2]` 的 `retrieved_data`；标量数据会包成单元素序列，缺失、不同、重复或额外元素均失败，`error_details` 等额外字段不参与比较。唯一 evaluator 必须得分 `1.0`，所有 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求响应经解析和归一化后匹配 `RETRIEVE`、`SUCCESS` 与无序数字单元素 `[2]`，使唯一 `AgentResponseEvaluator` 以及 `TaskEvalResult` 的 success 状态和分数 `1.0` 成立。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；无比较断言或错误且评估输入和编排正常被列为 success，非对象响应、字段或数据不匹配、输入无效、编排或 evaluator 异常被列为 failure，留存响应或 trace 不完整且无官方结果时列为 undecided。非空 stronger condition `public-response-schema-conformance` 还要求原始响应直接符合 `FinalAgentResponse`：为 JSON 对象，任务类型和状态分别解析为 `RETRIEVE`、`SUCCESS`，`retrieved_data` 为数字数组 `[2]`，`error_details` 解析为 `null`，不能仅靠 fenced-JSON 提取或标量转数组通过。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive-network-trace`
- 为什么修改：尽管唯一配置的 evaluator 仅比较 agent response，且任何以数据包表示的 trace 内容都不会改变该比较，network.har 仍被指定为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并基于完整的 agent_response.json 重建已配置检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-undecided-rule`
- 为什么修改：undecided 规则将响应和 trace 数据均缺失视为证据丢失，从而错误地使非决定性 trace 成为作出判定的必要条件。
- 应如何修改：仅当完整的 agent response 丢失、损坏、不可读或发生来源故障时，才使用 undecided；完整但无效或不匹配的响应必须仍判定为 failure。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported-stronger-condition`
- 为什么修改：公共响应 schema 一致性并不是此案例的用户意图与其已发布 evaluator 之间由数据包所显示的缺口。
- 应如何修改：将 stronger.additional_conditions 设为空列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal-checklist`
- 为什么修改：非决定性 trace 要求和缺乏依据的更强条件使检查清单不必要地扩大。
- 应如何修改：移除这些元素，并围绕唯一的响应 evaluator 整合原生 success、failure 和 undecided 规则。

## Case 15

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：统计商店迄今收到的评论中提及字符串 `"best"` 的评论总数。任务参数为 `term="best"`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它按已配置的数字数组 schema 解析并规范化响应，只比较 `task_type`、`status` 和 `retrieved_data`；`task_type` 期望为 `RETRIEVE`，也接受旧字段 `performed_operation`，`status` 期望为 `SUCCESS`，`retrieved_data` 需精确匹配 `[2]`。数组比较设置 `ordered=false`，非列表数据可被包装为单项后再规范化；未显式配置的原始字段（包括物化配置中的 `error_details:null`）不参与比较，也没有 filter 或 last-event 语义。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`；任何不匹配或 evaluator 错误均产生 `0.0`。

### 原本 draft 是什么

原 draft 宣称 benchmark success 是规范化后的响应匹配 `task_type RETRIEVE`、`status SUCCESS` 和无序数值集合 `[2]`，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult` 得分 `1.0`。它把 `agent_response.json` 和 `Retained official TaskEvalResult` 都列为决定性 artifacts；success 为 evaluator 接受该映射，failure 包括响应缺失、空、不可解析、规范化或评估错误以及任何字段或数据差异，undecided 则是在两者都不足以重建比较时成立，并称 `network.har` 单独不具决定性。非空 stronger condition `public-response-schema-conformance` 另要求未经代码块提取或标量强制转换的原始响应直接符合 `FinalAgentResponse`，其中 `retrieved_data` 必须字面编码为 `[2]` 且 `error_details` 经验证为 null。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifact_set`
- 为什么修改：检查清单添加了“保留的官方 TaskEvalResult”，尽管完整的 agent_response.json 是唯一 AgentResponseEvaluator 所需的最小充分证据，而且该材料包并未声明将该结果作为保留的运行 artifact。
- 应如何修改：从 decisive_artifacts 中移除 TaskEvalResult artifact，并将完整且可归属的 agent_response.json 作为唯一具有决定性的原生 artifact。可以继续省略 network.har，因为未配置 NetworkEventEvaluator，且数值响应比较不依赖它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`task_result_substitutes_for_response`
- 为什么修改：undecided_if 表示，当 agent_response.json 不可用但仍有可归属的 TaskEvalResult 时，审查仍可作出判定；这违背了根据其完整响应 artifact 重建已配置 AgentResponseEvaluator 的要求。
- 应如何修改：将 undecided_if 限定为 agent_response.json 丢失、损坏、不完整或来源验证失败的情况；继续明确区分：若能证明完整响应在评估时缺失、为空、无效或不匹配，则判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_result_artifact`
- 为什么修改：第二个原生 artifact 重复了可从 agent_response.json 和已发布 evaluator 语义推导出的结果，使检查清单不必要地违反最小化原则。
- 应如何修改：删除冗余的 TaskEvalResult artifact 及相关的替代证据表述。

## Case 17

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service 获取从 `AMC Waterfront` 到 `Carnegie Mellon University` 的驾车和步行时间。输出只能是含 `mode` 与 `duration` 的对象列表，`duration` 要求采用 `HH:MM:SS` 格式，不得附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，比较规范化后的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data`；后者使用数组/对象 schema，其中 `mode` 为字符串、`duration` 使用 `format="duration"` 规范化。期望是两个无序对象 `{"mode":"driving","duration":"13min"}` 与 `{"mode":"walking","duration":"1hr 35min"}`，`ordered=false`，因此顺序不重要，但元素、重复项和对象键必须精确一致；`performed_operation` 可作为 `task_type` 的旧别名，物化默认的 `error_details:null` 不参与显式比较。没有网络 evaluator、filter 或 last-event 检查；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 宣称成功条件是唯一 `AgentResponseEvaluator` 在解析和 schema 规范化后匹配 `RETRIEVE/SUCCESS` 以及无序的 driving-`13min`、walking-`1hr 35min` 两个对象，从而使 `TaskEvalResult.score=1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将 trace 可解析、评估输入可用纳入 success，将响应或 trace 不可用、上下文构造、配置、规范化或编排错误以及任何数据差异纳入 failure；两类 artifacts 无法重建且没有完整官方结果时判为 undecided。其非空 stronger conditions 为 `literal-hhmmss`，要求原始值字面为 `00:13:00` 和 `01:35:00`，以及 `osrm-use-evidence`，要求 `network.har` 显示支持两个模式和时长的成功 OSRM 请求与响应。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native-network-artifact-overreach`
- 为什么修改：对于仅配置了 AgentResponseEvaluator 的 case，network.har 被错误地指定为具有决定性的原生证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har。仅将其保留为更强 OSRM 使用条件的附加证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-native-decisions`
- 为什么修改：原生规则不当地使重建和结果取决于 trace 的可用性或是否保留 trace。
- 应如何修改：原生 success 和常规不匹配 failure 应以完整的 agent response 和已发布的 response evaluator 为依据。将 undecided 限定为进行该比较所需的响应证据丢失、截断或来源存在歧义的情况；继续将完整但无效的响应以及实际 evaluator 错误视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal-native-trace-material`
- 为什么修改：通用 HAR 解析和环境回退材料增加了不具有决定性的原生范围，并在多条规则中重复出现。
- 应如何修改：删除原生 HAR artifact 和 trace 专属条款，同时仅在该 case 所支持的更强 OSRM 条件下保留 network.har。

## Case 18

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service 获取从 `AMC Waterfront` 到 `Univ of Pittsburgh` 的驾车和步行时间。输出只能是含 `mode` 与 `duration` 的对象列表，`duration` 要求采用 `HH:MM:SS` 格式，不得附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，比较规范化后的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data`；数组元素采用对象 schema，`mode` 为字符串，`duration` 按 `format="duration"` 规范化。期望无序精确匹配 `{"mode":"driving","duration":"2min"}` 和 `{"mode":"walking","duration":"16min"}`，`ordered=false`，故顺序不计，但模式、时长、对象字段、项目数和重复项均须一致；物化默认的 `error_details:null` 不是显式比较字段。没有网络 evaluator、filter 或 last-event 检查；唯一 evaluator 得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`，不匹配或 evaluator 错误得到 `0.0`。

### 原本 draft 是什么

原 draft 宣称 benchmark success 是响应规范化为 `RETRIEVE/SUCCESS`，并无序精确匹配 driving-`2min` 与 walking-`16min`，使唯一 `AgentResponseEvaluator` 和 `TaskEvalResult` 均得分 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 artifacts 支持无错误评估纳入 success，把响应差异以及 artifact 解析、规范化、evaluator 或编排错误纳入 failure；artifacts 丢失、事后损坏或无法归属时为 undecided，而明确提交的无效响应或无效 trace 被视为 failure。非空 stronger conditions `literal_hh_mm_ss_durations` 要求原始时长字面为 `00:02:00` 和 `00:16:00`，`osrm_use_evidenced` 则要求 `network.har` 含覆盖两个模式和端点、并支持所报时长的 OSRM 请求/响应链。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_decisive`
- 为什么修改：对于唯一配置的 evaluator 为 AgentResponseEvaluator 的 case，network.har 被错误地列为具有决定性的原生证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har。对于单独的更强 OSRM 使用条件，它仍可作为决定性证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_broadens_native_decision`
- 为什么修改：success、failure 和 undecided 规则使 trace 的可用性或可解析性影响原生判定，尽管 trace 内容并非唯一已配置比较的一部分。
- 应如何修改：原生 success 和 failure 应以对保留的完整响应应用已发布的 AgentResponseEvaluator 为依据，并仅在该响应证据丢失、损坏或来源验证失败时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_artifact_set_not_minimal`
- 为什么修改：额外的原生 trace artifact 及其相关规则使检查清单不满足最小化要求。
- 应如何修改：将 agent_response.json 保留为唯一具有决定性的原生 artifact，并将 network.har 限定于更强的 OSRM 证据条件。

## Case 22

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：从当前 Fujifilm FinePix Z200FD 商品页找出提及短语 `“under water photo”` 的评论者姓名。起始 URL 为 `__SHOPPING__/fujifilm-finepix-z200fd-10mp-digital-camera-with-5x-optical-dual-image-stabilized-zoom-black.html`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它对响应进行提取和规范化，并比较显式配置的 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR` 与 `retrieved_data=null`；`results_schema` 为 `{"type":"null"}`，缺失的 `retrieved_data` 或其他被规范化为 null 的值可被接受。物化配置中的 `error_details:null` 是默认字段而非显式比较字段，也没有网络内容、filter 或 last-event 检查。唯一 evaluator 得分必须为 `1.0`，全 evaluator 合成的 `TaskEvalResult.score` 才为 `1.0`；任何可见不匹配或 evaluator 错误得到 `0.0`。

### 原本 draft 是什么

原 draft 宣称成功是响应规范化投影精确等于 `task_type RETRIEVE`、`status NOT_FOUND_ERROR`、`retrieved_data null`，且唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 还要求官方评估无错误完成，failure 包括响应无效或不匹配、非 null 数据、规范化/比较错误，以及 trace 或评估上下文错误，证据缺失或截断且没有完整官方结果时则为 undecided。非空 stronger condition `corroborate_not_found_against_page` 要求用 `network.har` 中的页面或评论数据核实确实没有评论提及 `“under water photo”`；若存在匹配评论，则 `agent_response.json` 必须返回相应评论者姓名。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_artifact_set_not_minimal`
- 为什么修改：对于唯一配置的检查为 AgentResponseEvaluator 且预期 retrieved_data 为 null 的 case，network.har 被错误地指定为具有决定性的原生证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har。将完整的 agent_response.json 保留为唯一具有决定性的原生 artifact；network.har 只能保留在单独的更强页面佐证条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_improperly_changes_native_decision`
- 为什么修改：原生规则将 trace 解析/上下文问题归类为 failure，并将缺少 trace 归类为 undecided，尽管无需 trace 即可重建已配置的响应比较。
- 应如何修改：删除依赖 trace 的原生 failure 和 undecided 分支。将 undecided 限定为 agent_response.json 丢失、截断或来源验证失败的情况，同时继续将完整但无效或不匹配的响应以及 evaluator 错误归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_native_trace_material`
- 为什么修改：原生部分包含冗余且不具有决定性的 trace 材料，使该 case 超出其唯一已配置响应检查的范围。
- 应如何修改：围绕 agent_response.json 和单个 AgentResponseEvaluator 精简原生部分。仅将 network.har 保留为明确指定的更强页面真实性条件的可选证据。

## Case 25

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：从当前 Epson WorkForce WF-3620 商品页返回明确提及 print quality 且评分不高于 3 星的评论者姓名。起始 URL 为 `__SHOPPING__/epson-workforce-wf-3620-wifi-direct-all-in-one-color-inkjet-printer-copier-scanner-amazon-dash-replenishment-ready.html`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它提取响应并按字符串数组 schema 规范化，比较显式配置的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data`；`performed_operation` 可作为 `task_type` 的旧字段，未配置的原始键不参与比较。`retrieved_data` 必须无序精确匹配两个字符串 `"Roxanne Brandon Coffey"` 与 `"Nelson"`，`ordered=false`，因此顺序不重要，但缺失、额外或重复项都会不匹配；没有网络 predicate、filter 或 last-event 语义。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`，任何不匹配或 evaluator 错误均导致 `0.0`。

### 原本 draft 是什么

原 draft 宣称 Task 25 仅在唯一 `AgentResponseEvaluator` 规范化出 `RETRIEVE/SUCCESS`，且无序数据恰含一个 `“Roxanne Brandon Coffey”` 和一个 `“Nelson”` 时得分 `1.0`；比较或编排错误则使任务得分 `0.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将 trace 可解析纳入 success，把无效 trace、上下文或编排错误、无效响应、字段差异及姓名集合的缺失、额外或重复差异纳入 failure；任一 artifact 缺失、截断或无法归属 task 25 时为 undecided。`stronger.additional_conditions` 为空，没有提出额外 stronger condition。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：network.har 被纳入决定性证据，尽管唯一配置的 AgentResponseEvaluator 读取 agent_response_raw，且不存在已配置的网络检查。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 保留为最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：这些规则要求必须解析 trace 才能判定 success，并使缺少保留的 network.har 导致无法判定，尽管重建已配置的响应比较不需要该 trace。
- 应如何修改：以 AgentResponseEvaluator 可见的响应为依据判定 success 和 failure，并将 undecided 限定为 agent_response.json 丢失、损坏或来源验证失败的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_clauses`
- 为什么修改：多项网络 trace 条款为仅含一个 evaluator、仅检查响应的检查清单增加了不具有决定性的范围和不必要的篇幅。
- 应如何修改：删除网络 artifact 及其相关的 success、failure 和 undecided 条款，同时保留响应解析、normalization、比较和分数组合规则。

## Case 26

### 原本 case 是什么

原始任务位于 `shopping` 站点，task type 为 `RETRIEVE`：在当前 Epson WorkForce WF-3620 商品页上，找出评论中抱怨 customer service 的 reviewer 姓名。要求返回符合该描述的姓名。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它检查响应中显式配置的 `task_type`、`status` 和 `retrieved_data`：前两者规范化后须为 `RETRIEVE`、`SUCCESS`，后者依照字符串数组 schema 规范化，并以 `ordered:false` 无序精确比较为恰好包含一次 `RemyRRemyR` 和一次 `Bob in Vegas`。物化配置中的 `error_details:null` 不是显式比较项；没有配置事件 filter、`NetworkEventEvaluator` 或 last-event 语义。由于只有这一个 evaluator，只有其 score 等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 在规范化后接受 `RETRIEVE`、`SUCCESS` 以及无序的两个预期姓名，并使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于确认 `NetworkTrace` 可构造和验证，同时注明没有网络事件内容匹配。其 success 条件要求结构化响应精确匹配且评估无错误；failure 包括无效响应、字段或姓名集合不匹配、trace／evaluator／orchestration 错误，undecided 则用于 bundle 缺失、截断或 case 归属不明而无法重建评估的情况。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：尽管不存在 NetworkEventEvaluator，也不存在比较依赖 trace 内容的 case 特定响应值，network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为唯一具有决定性的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：trace 的缺失、完整性或有效性会影响检查清单的 undecided/failure 结果，尽管无需 trace 即可重建已配置的响应检查。
- 应如何修改：移除 trace 专属的 failure 和 undecided 表述；仅当保留的已提交响应发生丢失、歧义或损坏并导致无法重建时，才使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的网络 artifact 及相关规则使检查清单超出了该 case 所需的最小证据范围。
- 应如何修改：采用仅包含响应的原生证据和判定结构，同时保留现有 evaluator 谓词以及为空的 stronger 列表。

## Case 27

### 原本 case 是什么

原始任务位于 `reddit` 站点，task type 为 `RETRIEVE`：在 personal finances forum 中取得最新帖子的 username 和标题，并统计该帖中既非作者发布、又 downvotes 多于 upvotes 的评论数量。输出须为对象列表，每个对象包含 `username`、`post_title` 和 `count`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，检查规范化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 依照数组内对象 schema 精确匹配 `[{'username':'Hammer94','post_title':'56 year old mom has no retirement. Where do I even start on her behalf?','count':0}]`。数组采用 `ordered:false` 的无序比较，同时要求精确基数、对象结构、字符串值和数值 `count`；物化产生的 `error_details:null` 不属于显式比较字段。没有事件 filter 或 last-event evaluator 语义；唯一 evaluator 的 score 必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称唯一的 `AgentResponseEvaluator` 在响应规范化为 `RETRIEVE`、`SUCCESS` 和上述无序单对象数组时得 `1.0`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，分别用于重建结构化响应比较及确认 HAR 可作为 `NetworkTrace` 被接受。其 success 要求无 orchestration／evaluator 错误且所有字段、数组基数、对象键和值完全匹配；failure 包括输入或评估错误以及任一比较差异。它把无法保留完整 `agent_response.json` 或 `network.har`、因而不能重建实际输入和得分的情况列为 undecided，并说明实际的 null、malformed 或缺失运行输入属于 failure；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`composition_failure_masked_by_har_loss`
- 为什么修改：当 network.har 缺失时，undecided 规则可能覆盖唯一 AgentResponseEvaluator 得出的确定性 failure。
- 应如何修改：无论是否保留 HAR，都将每个完整但无效、为 null、格式错误或不匹配的已提交响应判定为原生 failure；仅在决定性响应证据丢失时使用 undecided。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：尽管该 case 没有 NetworkEventEvaluator，network.har 却仅因通用解析/配置验收而被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json 作为该已配置检查所需的最小充分运行后证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：只要 agent_response.json 或 network.har 中任一项不可用，检查清单就将证据声明为 undecided，即使仅凭响应便可确定判定为 failure。
- 应如何修改：将 undecided_if 限定为影响实际已提交响应的保留、完整性或来源丢失；明确继续将完整但无效或不匹配的响应判定为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_har_dependency`
- 为什么修改：额外的 HAR 条件使检查清单不满足最小化要求，并造成相互冲突的 failure 和 undecided 结果。
- 应如何修改：删除 HAR artifact 和所有依赖 HAR 的判定表述，同时保留唯一 response evaluator 的解析、normalization、schema、无序比较和分数组合规则。

## Case 28

### 原本 case 是什么

原始任务位于 `reddit` 站点，task type 为 `RETRIEVE`：在 Worcester forum 中取得最新帖子的 username 和标题，并统计其中非帖子作者且 downvotes 多于 upvotes 的评论数。结果须是包含 `username`、`post_title`、`count` 三个键的对象列表。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较显式配置的三个字段：`task_type` 和 `status` 规范化后须分别为 `RETRIEVE`、`SUCCESS`，`retrieved_data` 须按数组对象 schema 规范化为包含 `{'username':'mineinhusdson','post_title':'Best place for a foot rub?','count':0}` 的单元素数组。比较设置为 `ordered:false`，因此忽略数组顺序，但要求元素数量、对象字段及其字符串／数值类型和值精确匹配；`error_details:null` 是物化默认值而非显式评分项。没有配置事件 filter 或 last-event 语义；该 evaluator score 等于 `1.0` 是 `TaskEvalResult.score` 等于 `1.0` 的必要且充分条件。

### 原本 draft 是什么

原 draft 将 benchmark success 定义为唯一的 `AgentResponseEvaluator` 经解析和 schema normalization 后匹配 `RETRIEVE`、`SUCCESS` 及预期无序 singleton，并使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 均视为决定性 artifacts；HAR 被用于确认 trace 可解析、评估可重建，同时注明没有单独评分网络事件内容。success 条件还提到可接受的 `performed_operation` alias，并要求 singleton 中无缺失、额外或不匹配字段；failure 包括响应不可解析、字段差异以及 response／trace／orchestration 错误。undecided 用于无法确定精确响应、无法判断 artifact 不可读究竟是留存损失还是实际输入且又无官方 `TaskEvalResult` 的情况；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：network.har 被列为决定性证据，尽管唯一配置的检查是 AgentResponseEvaluator，且材料包中体现的任何网络事件内容都不会改变其已配置的比较。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并使用完整且精确的 agent_response.json 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_trace_decision_rules`
- 为什么修改：尽管不存在 NetworkEventEvaluator，这些规则仍可能因 network.har 缺失或不可读而判定为 undecided，并另行将 trace 处理视为原生条件。
- 应如何修改：将 undecided_if 限定为精确的已提交响应发生丢失、损坏或来源验证失败并导致无法重建的情况，并移除 trace 专属的原生判定表述，同时保留常规 evaluator 不匹配和错误所导致的 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_checklist`
- 为什么修改：额外的 trace artifact 和依赖 trace 的规则使检查清单比最小的已配置原生主张更庞大、更严格。
- 应如何修改：删除 network.har 的决定性 artifact 条目以及原生规则中所有对 trace 保留的依赖；保留响应比较、evaluator 组合和响应证据完整性规则。

## Case 29

### 原本 case 是什么

原始任务位于 `reddit` 站点，task type 为 `RETRIEVE`：在 DIY forum 中找出最新帖子的 username 和标题，并统计该帖中由非作者发布且 downvotes 多于 upvotes 的评论。返回包含 `username`、`post_title` 和 `count` 的对象列表。

### Benchmark 怎么测

仅有一个 `AgentResponseEvaluator`：响应经官方解析和 schema normalization 后，`task_type`、`status` 必须为 `RETRIEVE`、`SUCCESS`，`retrieved_data` 必须无序精确等于 `[{'username':'ziostraccette','post_title':'How can I bring an HDMI cable from my pc downstairs to my TV upstairs?','count':0}]`。`ordered:false` 表示数组顺序不计，但数组基数、schema 可见对象键、字符串值和数值 `count` 均须精确；物化默认的 `error_details:null` 不在显式比较范围内。没有配置事件 filter 或 last-event 语义；唯一 evaluator 得 `1.0` 时且仅当此时，`TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 在解析和规范化后精确匹配 `RETRIEVE`、`SUCCESS` 与预期无序 singleton，并因此令 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于确认 trace 能作为本次运行的 `NetworkTrace` 被解析并完成评估上下文构造。success 要求响应精确匹配且评估无错误；failure 包括无效响应、任一字段、数组项或对象键值不符，以及 response／trace parsing 或 evaluator／orchestration 错误。undecided 指 artifacts 缺失、不可读或彼此矛盾，致使实际评估输入无法确定且无保留的官方 `TaskEvalResult`；已知 null、malformed 或被拒绝的输入则被归为 failure，`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：尽管不存在已配置的 NetworkEventEvaluator，也不存在比较依赖该 trace 的 case 特定响应值，network.har 仍被作为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 保留为最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_rules`
- 为什么修改：success、failure 和 undecided 规则不当地使保留的 trace 的解析或丢失与这个仅配置了响应检查的评估相关。
- 应如何修改：通过 AgentResponseEvaluator 比较及其所得分数表示 success 和 failure；将 undecided 限定为阻碍重建所提供 agent response 的运行后完整性或来源丢失。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_extra_native_scope`
- 为什么修改：额外的 HAR artifact 和 trace 处理条款使检查清单超出了最小已配置主张的范围。
- 应如何修改：删除 trace 专属 artifact 和条款，同时保留响应解析、normalization、精确预期值、无序比较、错误处理以及全部 evaluator 组合。

## Case 30

### 原本 case 是什么

原始任务位于 `reddit` 站点，task type 为 `RETRIEVE`：在 space forum 中获取最新帖子的 username 和标题，并统计其中不是作者发布且 downvotes 多于 upvotes 的评论数。输出须为含 `username`、`post_title`、`count` 的对象列表。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较规范化后的 `task_type`、`status` 和 `retrieved_data`：预期分别为 `RETRIEVE`、`SUCCESS`，以及无序 singleton `{'username':'Dhghomon','post_title':'Scientists erupt at NASA gutting funding for crucial Venus mission','count':0}`。`retrieved_data` 按数组对象 schema 规范化，并采用 `ordered:false` 精确结构比较；输入还涉及 singleton coercion，因此 evaluator 的原生评分不一定强制原始值字面上就是数组，物化默认 `error_details:null` 也不是显式比较项。没有配置事件 filter、`NetworkEventEvaluator` 或 last-event 语义；仅当这一 evaluator score 为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 经 extraction、singleton coercion 和 schema normalization 后匹配 `RETRIEVE`、`SUCCESS` 及预期无序 singleton，且无评估错误，从而使 evaluator 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；后者用于验证 trace 可解析并能构造评估上下文，同时说明没有 `NetworkEventEvaluator` 内容检查。success 要求规范化比较无 failure assertions；failure 包括响应无效、字段或对象结构不符，以及 trace／context／normalization／orchestration 错误，undecided 用于 artifacts 缺失或截断而无法重建响应和所需输入且无完整官方结果的情况。其非空 stronger condition `literal_list_of_objects` 额外要求在 singleton coercion 或 item normalization 前，`retrieved_data` 字面上是仅含一个 JSON object 的 JSON array，不接受仅因规范化而通过的 lone object 或 serialized-object string；决定性 artifact 为 `agent_response.json`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_har`
- 为什么修改：对于唯一配置的检查为 AgentResponseEvaluator 的 case，network.har 被错误地列为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json 作为重建已配置比较所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decision_rules`
- 为什么修改：判定规则引入了 trace 解析/上下文错误以及缺少所需评估输入的情况，使不具有决定性的 HAR 是否保留影响 failure 判定或 undecided 重建。
- 应如何修改：移除 trace 专属的重建依赖；将完整但无效或不匹配的响应以及已发布 evaluator 的错误归类为 failure，并仅在 agent_response.json 缺失、截断或来源存在缺陷时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_native_evidence`
- 为什么修改：不必要的 HAR artifact 以及重复的 trace/上下文论述使检查清单超出了该 case 所需的最小证据陈述。
- 应如何修改：删除 HAR artifact 条目和 trace 专属表述，同时保留响应比较、组合、failure 和证据丢失规则。

## Case 31

### 原本 case 是什么

原始任务是在 `reddit` 站点的 `photoshopbattles` 论坛执行 `RETRIEVE`：找出最新帖子的用户名和标题，并统计其中既非作者发布、又踩多于赞的评论数。输出须为对象列表，每个对象包含 `username`、`post_title` 和 `count`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查响应能否被解析并按 schema 规范化为 `task_type: "RETRIEVE"`、`status: "SUCCESS"`，以及 `retrieved_data` 中唯一对象 `{"username":"Proud_Idiot","post_title":"UK Prime Minister Rishi Sunak looking at a pothole","count":0}`。`results_schema` 要求外层为数组、对象恰含数值型 `count` 和字符串型 `post_title`、`username`；materialized 配置为 `ordered:false`，因此集合顺序忽略，但项目、字段和值须结构化精确匹配。未配置 `NetworkEventEvaluator`、URL filter 或 last-event 判定，materialized 的 `error_details:null` 也不是 sparse expected 中显式配置的比较字段。任务只有该 evaluator，故其分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得到 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`，且规范化响应精确匹配 `RETRIEVE`、`SUCCESS` 和上述无序单项结果。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，前者用于响应比较，后者用于确认 HAR 可解析并可在需要时提供 Reddit base URL。其 `success_if` 要求无比较断言且唯一 evaluator 得分 `1.0`；`fail_if` 将不可解析、字段缺失或不匹配、额外项目以及响应、HAR、配置或 evaluator 错误判为失败；`undecided_if` 仅保留给证据缺失或截断，而明确的 null、畸形响应或无效必需 HAR 被写成失败。非空 stronger condition `require_retrieved_data_list_shape` 进一步要求原始 `retrieved_data` 本身必须是 JSON 列表，不能依赖 evaluator 把单个对象强制包装为 singleton collection。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_har_artifact`
- 为什么修改：尽管该用例只有一个 `AgentResponseEvaluator`，且不存在与评分相关的网络事件谓词，却错误地将 `network.har` 指定为决定性证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_based_failure_overclaim`
- 为什么修改：即使完整响应能够最终确定所配置的比较结果，该检查清单仍将保留的无效 HAR 视为原生 failure。
- 应如何修改：移除 HAR 特定的 failure 表述。依据完整响应和已发布的 evaluator 语义判定 success 与 failure；仅当决定性响应证据丢失、截断或来源验证失败时，才判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_body_not_minimal`
- 为什么修改：额外的 HAR artifact 及相关判定条款，向原本紧凑且仅依赖响应的检查清单中加入了不具决定性的用例机制。
- 应如何修改：使用仅依赖响应的原生证据部分，并移除冗余的 HAR 引用，同时保留 evaluator 错误和非 `1.0` 的 failure 语义。

## Case 32

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：寻找 Pittsburgh Airport 附近可用的 Hilton 酒店，并使用 OSRM direction service 得到该酒店到最近一家本地公司所有的超市的步行距离。只能返回含 `hotel` 和 `distance` 的对象列表，其中距离是带 `km` 或 `m` 单位的数值字符串，不得附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，期望规范化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，`retrieved_data` 为无序 singleton `[{"hotel":"DoubleTree by Hilton Hotel Pittsburgh Airport","distance":"2km"}]`。文本响应可经去空白、围栏 JSON 提取和 JSON 解码处理；若缺少 `task_type`，可使用 legacy alias `performed_operation`，非空且非列表的 `retrieved_data` 会被强制视为 singleton。schema 分别以 `location-name` 和 `distance` 规范化 `hotel`、`distance`，随后进行精确无序数组比较，包括对象 key 集、项目重数及缺失或额外内容；未配置网络、URL filter 或 last-event evaluator，且 `error_details:null` 不属于 sparse expected 的显式比较字段。唯一 evaluator 必须得分 `1.0`，任务的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是规范化响应匹配 `RETRIEVE`、`SUCCESS` 和配置的无序 singleton 酒店—距离结果，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult.score` 均为 `1.0`。它只把 `agent_response.json` 列为原生决定性 artifact，并要求其中精确包含 `DoubleTree by Hilton Hotel Pittsburgh Airport` 和匹配 `2km` 的距离。其 `success_if` 要求 schema 规范化和无序比较后没有缺失或额外项目；`fail_if` 将不可解析或非结构化响应、缺失或不匹配的 `task_type`/`status`/`retrieved_data`、内容差异、`0.0` 或错误判为失败；`undecided_if` 用于提交响应未保留或被截断且无足够 evaluator 结果的情况。非空 stronger condition `verify_osrm_walking_route` 要求 `network.har` 显示酒店与所选超市之间成功的 OSRM 步行路线请求，且路线距离支持响应值。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`user_goal_output_contract_omitted`
- 为什么修改：`native.user_goal` 遗漏了官方指令中的实质性输出要求。
- 应如何修改：说明答案必须仅为一个对象列表，对象包含 `hotel` 和 `distance` key，且 `distance` 为带有 `km` 或 `m` 单位的数值。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias_misclassified`
- 为什么修改：检查清单要求必须存在字面量 `task_type` 字段，并称缺少该字段即为 failure，但已发布的 evaluator 会在 `task_type` 缺失时使用 `performed_operation`。
- 应如何修改：在证据问题及原生 success/failure 谓词中统一应用已发布的 `task_type`/`performed_operation` 别名规则，并说明相关的 parsing、稀疏 expected 字段、schema normalization、singleton coercion 和无序精确比较。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`native_decision_rule_overrestricts_alias`
- 为什么修改：`fail_if` 将使用可接受旧版别名的响应判定为原生 failure，而 `undecided_if` 允许在没有指定的完整响应 artifact 时得出结论。
- 应如何修改：仅在 `task_type` 存在但不匹配，或 `task_type` 缺失且 `performed_operation` 未提供 `RETRIEVE` 时，才因 `task_type` 判定为 failure。若完整提交响应丢失、损坏或其来源无法验证，则判定为 undecided。

#### 修改项 4：stronger.additional_conditions

- Finding ID：`literal_output_gap_not_recorded`
- 为什么修改：更强条件列表记录了未经验证的 OSRM 方法，却未记录有来源支持的差距：用户要求字面意义上的仅列表输出，而 evaluator 采用宽松的 parsing/coercion。
- 应如何修改：添加一个单独的超出原生要求的条件，该条件可从完整的 `agent_response.json` 中衡量，要求 `retrieved_data` 在字面上是 JSON list，并排除协议信封之外的周边叙述或未配置的面向用户内容。

## Case 33

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：寻找 Pittsburgh Airport 附近可用的 Hilton 酒店，并使用 OSRM direction service 获得该酒店到一家超市的最短步行距离。只能返回含 `hotel` 和 `distance` 的对象列表，距离须为带 `km` 或 `m` 单位的数值字符串，不得附加其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查显式配置的 `task_type`、`status` 和 `retrieved_data`：它们须规范化为 `RETRIEVE`、`SUCCESS` 和无序 singleton `[{"hotel":"DoubleTree by Hilton Hotel Pittsburgh Airport","distance":"1.4km"}]`；缺少 `task_type` 时支持 legacy `performed_operation` alias。`results_schema` 将 `hotel` 按 `location-name`、`distance` 按 `distance` 格式规范化，并以 `ordered:false` 比较数组，拒绝缺失或额外的项目与对象字段；materialized 的 `error_details:null` 不参与 sparse-field 比较。未配置网络、URL filter 或 last-event evaluator，因此 OSRM 请求本身不由 native score 检查。该 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 将响应解析并规范化为 `RETRIEVE`、`SUCCESS` 和酒店为 `DoubleTree by Hilton Hotel Pittsburgh Airport`、距离等价于 `1.4km` 的无序 singleton，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并在原生成功条件中要求响应精确匹配、HAR 可解析且 evaluation 无错误。其失败条件覆盖响应不可解析、字段或结果缺失/额外/不匹配、必需 evaluator 输入不可解析、evaluation error 或 evaluator 非 `1.0`；证据缺失、截断或不可读且无官方 task result 时列为 `undecided`。非空 stronger condition `verify_osrm_walking_route` 要求 `network.har` 包含从指定酒店到超市的成功 OSRM 步行路线请求，且返回数据支持 `1.4km`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_network_artifact`
- 为什么修改：尽管该用例仅配置了 `AgentResponseEvaluator`，且响应比较不依赖 trace 内容，`network.har` 仍被列为原生决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅将其保留为单独的更强 OSRM 路线条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_native_decisions`
- 为什么修改：原生 success 和 undecided 规则要求确认 `network.har` 可解析，因此，即使完整响应足以重建所配置的 evaluator，运行后 trace 缺失也可能导致无法作出判定。
- 应如何修改：让原生 success、failure 和 undecided 规则依赖完整的 agent 响应以及由此产生的 `AgentResponseEvaluator` 语义。任何已记录的 evaluator 错误仍应判定为 failure，但不要将运行后 trace 的保留作为先决条件。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_language`
- 为什么修改：原生部分重复了一项不具决定性的 trace 要求，而该要求只应属于更强的 OSRM 验证。
- 应如何修改：删除原生部分中对 `network.har` artifact 和判定规则的引用，同时保留简洁的更强条件及其 trace 证据。

## Case 34

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：寻找 Pittsburgh Airport 附近可用的 Hyatt 酒店，并使用 OSRM direction service 得到该酒店到一家超市的最短步行时间。输出只能是含 `hotel_name` 和 `travel_time` 的对象列表，其中时间要求采用 `HH:MM:SS` 格式，不得附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，显式 expected 要求 `task_type: "RETRIEVE"`、`status: "SUCCESS"`，以及无序 singleton `[{"hotel_name":"Hyatt Regency Pittsburgh International Airport","travel_time":"3h 30min"}]`；`task_type` 缺失时可接受 `performed_operation` alias。配置的 `results_schema` 属性名却是 `hotel` 和 `information`，并分别标为 `location-name` 与 `duration`，与 expected 的 `hotel_name`、`travel_time` 不一致，因此这两个 expected 字段回退到字符串规范化，而不是按所标格式进行类型化规范化。比较使用 `ordered:false`，要求项目、对象 key 和值无缺失、额外或不匹配；未配置网络、URL filter 或 last-event evaluator，`error_details:null` 也不是 sparse expected 的比较字段。唯一 evaluator 必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 在解析、规范化和无序结构比较后匹配 `RETRIEVE`、`SUCCESS` 及 `{"hotel_name":"Hyatt Regency Pittsburgh International Airport","travel_time":"3h 30min"}`，使 evaluator 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，同时注明 HAR 的路线内容不由唯一 evaluator 比较，但要求 trace 可用于构造 evaluation context。其成功条件接受 `task_type` 或 `performed_operation` alias 并要求无序单项结果精确匹配；失败条件覆盖 null、空、解析后非对象、字段或内容不匹配以及任何 evaluator/orchestration error；响应或 trace 缺失、截断、无法关联到运行且无可信 `TaskEvalResult` 时列为 `undecided`。非空 stronger conditions 包括 `intent_hhmmss_format`，要求用 `"03:30:00"` 而非 expected 的 `"3h 30min"`，以及 `osrm_shortest_walking_evidence`，要求 `network.har` 证明 OSRM 路线时长并证明没有已有证据支持的更短超市路线。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_decisive`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的用例，`network.har` 被错误地指定为必要的原生证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。保留 `agent_response.json` 作为最小充分的原生 artifact；`network.har` 可继续保留在 OSRM 更强条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_undecided`
- 为什么修改：原生 undecided 规则将 trace 保留失败归类为 undecided，尽管 trace 内容并不决定所配置的响应比较结果。
- 应如何修改：将原生 `undecided_if` 限制为确实妨碍重建的 `agent_response.json` 丢失、损坏或来源验证失败。不要将 trace 保留失败本身作为充分条件。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_native_trace_dependency`
- 为什么修改：原生 trace 条目及相应的 undecided 依赖引入了不具决定性的内容，并与用例级最小证据要求冲突。
- 应如何修改：删除原生 trace artifact 及其保留依赖，同时仅将 `network.har` 保留为更强 OSRM 来源条件的证据。

## Case 36

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service 判断从 Carnegie Mellon University 驾车能否在一小时内到达 Pittsburgh 的 Social Security Administration。能到达返回 `true`，否则返回 `false`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对显式配置字段进行解析和规范化，要求 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，并按 Boolean array schema 将 `retrieved_data` 精确匹配为无序 singleton `[true]`；released 处理支持 JSON/code-block 提取及 legacy task-type alias。比较为 `ordered:false`，但 singleton 的布尔值和重数仍须精确一致；materialized 的 `error_details:null` 不属于显式比较字段。未配置网络、URL filter 或 last-event evaluator，因此 OSRM 服务、端点、驾车路线和时长不进入 native response score。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 evaluation 完成且唯一 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS` 和无序 singleton `[true]`，从而 evaluator 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求响应匹配且 HAR 可解析、不会导致 evaluation error。其失败条件包括响应缺失或无效、task type/status/布尔 multiset 不匹配、必需输入不可解析或 evaluation error，并特别把 evaluation 时 HAR 不可用或无效写为失败；保留 artifact 缺失或截断且无官方 `TaskEvalResult` 时列为 `undecided`。非空 stronger condition `verify_osrm_route_evidence` 要求 `network.har` 将 Carnegie Mellon University 与 Pittsburgh 的 Social Security Administration 关联到 OSRM 驾车路线请求，并显示成功路线时长不超过 `3,600` 秒，以支持 `true`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_decisive`
- 为什么修改：尽管唯一配置的 evaluator 只检查 agent 响应，且其 Boolean 比较不依赖 trace，`network.har` 仍被指定为原生决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`；保留完整的 `agent_response.json` 作为最小原生 artifact。HAR 可继续保留在更强 OSRM 条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_overconstrains_native_rules`
- 为什么修改：success 和 failure 规则将 HAR 的存在及可解析性作为所配置响应检查的先决条件，因此 undecided 规则会将 HAR 保留失败视为可能具有决定性。
- 应如何修改：依据已发布的 `AgentResponseEvaluator` 语义对保留的完整响应进行处理，以判定原生 success 和 failure。将 undecided 限制为导致无法重建 evaluator 所接收响应的丢失、截断、完整性或来源问题。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_har_material`
- 为什么修改：额外的原生 HAR artifact 及其重复的编排表述使检查清单不再最小化，却没有保留任何额外的已配置检查。
- 应如何修改：删除原生部分中 HAR 特定的 artifact 和判定规则条款，同时仅将 HAR 保留为用例特定更强条件的证据。

## Case 37

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，判断从 CMU 的 Gates Building 驾车前往 Pittsburgh 的 police station 是否能在一小时内到达。能到达返回 `true`，否则返回 `false`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`；它对最终响应进行解析和规范化，并比较稀疏配置中明确给出的 `task_type`、`status` 和 `retrieved_data`。期望值分别为 `RETRIEVE`、`SUCCESS` 和布尔数组 `[true]`；`retrieved_data` 按 `results_schema` 的 array-of-boolean 结构进行精确比较，`ordered=false` 表示忽略顺序，但元素内容和数量仍须一致。物化配置中的 `error_details:null` 是默认值，不是稀疏配置明确要求比较的字段；本任务没有 last-event evaluator 或网络事件比较。唯一 evaluator 的分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是最终响应规范化为 `RETRIEVE` / `SUCCESS` / `[true]`，且唯一 `AgentResponseEvaluator` 得分 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 HAR 成功解析、trace 摄取及上下文构造纳入 success/failure；响应畸形、字段不符、`retrieved_data` 不是恰好单元素 `true`，或所需输入无效均被写为 failure。它将无法保留完整响应、trace 且没有官方 `TaskEvalResult` 的情形写为 undecided。非空 stronger condition `osrm_route_evidence` 另要求 `network.har` 证明存在从 Gates Building at CMU 到 Pittsburgh police station 的成功 OSRM 驾车路线请求与响应，且 duration 不超过 `3,600` 秒。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_network_artifact`
- 为什么修改：尽管唯一配置的 evaluator 只比较 agent 响应，且没有任何由 packet 表示的 trace 内容检查会影响所配置的 Boolean 比较，`network.har` 仍被列为原生决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并仅将其保留为明确列出的更强 OSRM 路线条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`native_rules_use_extraneous_evidence`
- 为什么修改：`success_if` 要求摄取 trace，而 `undecided_if` 要求响应加 trace，或要求一个未被指定为决定性 artifact 的官方 `TaskEvalResult`。
- 应如何修改：依据保留的完整 `agent_response.json` 和已发布的 `AgentResponseEvaluator` 语义判定原生 success、failure 和 undecidability。将 undecided 限制为该证据丢失、损坏或来源验证失败，并将完整但无效的响应判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：原生检查清单包含不必要的 HAR artifact 及相关摄取表述，重复了仅与更强条件相关的证据。
- 应如何修改：将原生部分精简为唯一的响应 evaluator 及其最小充分的响应 artifact；将 OSRM 网络验证隔离在 stronger 下。

## Case 39

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，判断从 `5600 fifth avenue` 驾车前往 Pittsburgh 的 `walmart` 是否能在一小时内到达。能到达返回 `true`，否则返回 `false`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，用于解析并规范化最终响应中明确配置的 `task_type`、`status` 和 `retrieved_data`。期望值为 `RETRIEVE`、`SUCCESS` 和 `[true]`；`retrieved_data` 使用 array-of-boolean schema，并以 `ordered=false` 做忽略顺序但保持内容与数量精确一致的比较。默认物化出的 `error_details:null` 不属于稀疏配置明确比较的字段，配置也没有 last-event 或 `NetworkEventEvaluator` 语义。只有该 evaluator 得分 `1.0` 时，按“所有 evaluator 分数均等于 `1.0`”的组合规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 native success 写为 `TaskEvalResult.score = 1.0`，要求唯一 `AgentResponseEvaluator` 把响应解析、规范化为 `task_type RETRIEVE`、`status SUCCESS` 和精确匹配 unordered `[true]` 的布尔序列。它把 `agent_response.json` 与 `network.har` 都列作决定性 artifacts，并要求 trace 可解析且 evaluation 无错误；响应字段或数据不匹配，以及 response/trace 解析、上下文构造或 evaluator orchestration 错误，被归为 failure。任一所需留存输入缺失、截断或不可读、因而无法重建响应比较或 trace 可解析性时，被写为 undecided。非空 stronger condition `osrm_route_grounding` 要求 `network.har` 显示从 `5600 Fifth Avenue` 到 Pittsburgh Walmart 的成功 OSRM 驾车结果且时长至多一小时，并要求 `agent_response.json` 中的布尔值与之相符。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_native_har`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的用例，`network.har` 被错误地指定为原生决定性证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并仅将其保留在更强的 OSRM grounding 条件下。保留完整的 `agent_response.json` 作为最小原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_native_rules`
- 为什么修改：原生 success 和 undecided 规则依赖 trace 的解析或保留，尽管 trace 内容不会影响此处所配置的 Boolean 响应比较。
- 应如何修改：依据已发布的 parsing、normalization 以及对完整响应的比较来判定原生 success 和 failure。将 undecided 限制为影响 `agent_response.json` 的运行后丢失、损坏或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_conditions`
- 为什么修改：多个原生条款重复了不具决定性的网络 trace 要求，使检查清单比所配置检查应有的范围更大、限制更严。
- 应如何修改：删除原生 HAR artifact 以及 trace 特定的 success、failure 和 undecided 条款，同时保留用例特定的更强 HAR 条件。

## Case 42

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`，获取并返回用户商店中排名前 `2` 的搜索词。任务指令为 `Get the top 2 search term(s) in my store`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析最终响应，并只规范化稀疏 expected 中明确配置的 `task_type`、`status` 和 `retrieved_data`；文本响应可经过去空白、fenced JSON 提取和 JSON decoding，`performed_operation` 可作为 `task_type` 的 legacy 名称。期望为 `RETRIEVE`、`SUCCESS` 和字符串数组 `["hollister", "Joust Bag"]`；前两者采用字符串规范化，数据采用 array-of-string schema，且 `ordered=false`，因此顺序忽略，但两个字符串的内容、数量和重复 multiplicity 必须精确一致。额外 raw response keys（包括物化默认值 `error_details`）不影响比较；配置没有 last-event evaluator。只有该 evaluator 得分 `1.0` 时，`TaskEvalResult.score` 才因 all-evaluators composition 而为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 evaluation 完成、唯一 `AgentResponseEvaluator` 得分 `1.0`，响应规范化为 `RETRIEVE` / `SUCCESS`，并在官方字符串规范化下无序精确匹配 `"hollister"` 和 `"Joust Bag"`，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并在 success 中要求两者均能载入官方 evaluation context；artifact、上下文或 orchestration 错误，以及响应结构、字段、类型、内容、数量或 multiplicity 不符，均被列为 failure。一个或两个 artifacts 未留存或字节不完整，且没有足够的官方 `TaskEvalResult` 时，被写为 undecided；已知运行时输入为 null、畸形、缺失或不可读则被写为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：尽管唯一配置的检查是 `AgentResponseEvaluator`，且其用例特定的比较可从最终响应中重建，`network.har` 仍被视为决定性且强制要求的证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：success、failure 和 undecided 规则不当地依赖无关网络 trace 的保留或解析。
- 应如何修改：从 `success_if`、`fail_if` 和 `undecided_if` 中移除 `network.har`。将 undecided 限制为 `agent_response.json` 的丢失或完整性/来源验证失败；将完整但无效的响应判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的网络分支使检查清单不再最小化，并在 trace parsing 与保留字节不完整之间形成了相互重叠的 failure/undecided 处理逻辑。
- 应如何修改：围绕唯一的响应 evaluator 及其单个决定性 artifact 整合检查清单，同时保留无效完整响应与响应证据丢失之间的区别。

## Case 43

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`，报告用户商店中排名前 `3` 的搜索词。任务指令为 `Get the top 3 search term(s) in my store`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对最终响应执行文本去空白、可选 fenced-block 提取、JSON decoding 和规范化，并比较稀疏配置明确给出的 `task_type`、`status`、`retrieved_data`；缺少 `task_type` 时可使用 legacy 字段 `performed_operation`。期望分别是 `RETRIEVE`、`SUCCESS` 和 `["hollister", "Joust Bag", "nike"]`；数据使用 array-of-strings schema，`ordered=false`，所以忽略顺序，但缺项、额外项和 multiplicity 差异都会导致不匹配。物化默认字段 `error_details` 及其他未配置的 raw keys 不参与比较，且没有 last-event evaluator。因为仅有这一个 evaluator，只有其得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 描述为官方 evaluation 无错误完成，且唯一 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS` 和精确的 unordered multiset `"hollister"`、`"Joust Bag"`、`"nike"`，随后 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并特别询问 trace 是否能解析及在环境 URL 需要 fallback 时提供可用事件；success 要求两个 artifacts 都允许 evaluation 运行。已确定的响应无效或字段、数据缺失、替换、重复、额外，以及任一 artifact 解析或 evaluation context/orchestration 错误，都被列为 failure。因 artifact 丢失或运行后损坏而无法重建实际提交的响应和 trace，且没有留存官方结果时，被写为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：尽管唯一配置的 evaluator 比较最终响应，且 packet 未表明 trace 内容会影响该用例所配置的字符串比较，`network.har` 仍被表述为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的保留证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：判定规则将 trace 的可用性和 parsing 作为 success 的必要条件，并允许 trace 丢失导致 undecided，尽管重建所配置的 evaluator 结果并不需要 trace 证据。
- 应如何修改：依据完整响应和已发布的 `AgentResponseEvaluator` 语义判定 success 与 failure；仅当响应证据本身丢失、损坏或来源验证失败时，才判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_runtime_clauses`
- 为什么修改：额外的 trace artifact 及其运行时 fallback/parsing 条款，向原本仅依赖响应的检查清单中加入了不具决定性的机制。
- 应如何修改：删除 trace 特定的 artifact 和规则，同时保留响应 parsing、normalization、无序精确比较、evaluator 错误处理和任务级评分组合。

## Case 47

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：以 `June 12, 2023` 为当日，统计过去数月的 complete orders 数量及包含 shipping and handling fees 的总支出。只返回含 `"order_count"`（integer）和 `"amount"`（number，例如 `10.99`）两个键的对象，不附加其他细节。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 从最终响应解析并规范化稀疏 expected 中的 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和 `[{"amount":0,"order_count":0}]`；文本可经 JSON 或 fenced-JSON 提取，`performed_operation` 可作为缺失 `task_type` 时的 legacy alias。`retrieved_data` 使用 array schema，其中对象的 `amount` 是 `format:"currency"` 的 number，`order_count` 也是 number；递归比较会检查对象键和值、数组 cardinality 及 unordered membership，`ordered=false` 只表示数组顺序不重要。物化默认的 `error_details:null` 不参与本 case 的稀疏字段比较，且没有 last-event evaluator。只有该 evaluator 得分 `1.0` 时，按所有 evaluator 均须为 `1.0` 的规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 为 `1.0` 当且仅当唯一 `AgentResponseEvaluator` 得分 `1.0`：响应须规范化为 `RETRIEVE`、`SUCCESS`，并在 unordered structural comparison 下等于含 `order_count` 0、`amount` 0 的单元素对象数组。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，success 要求用响应与 trace 重评估且无断言；字段、值或 cardinality 不符，以及 response/trace 解析、验证、规范化、比较或 orchestration 错误，均写为 failure。响应或 trace 缺失、不可读或不足以重建 evaluator 输入，且没有官方 evaluation result 时，被写为 undecided。非空 stronger condition `exact_requested_payload_format` 进一步要求结果项恰好只有 `order_count` 和 `amount`、`order_count` 以 JSON integer 编码且无额外字段或细节，并声称 schema projection 可能忽略额外属性。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`F1_nonminimal_network_artifact`
- 为什么修改：对于唯一配置的 evaluator 读取 `agent_response_raw` 并比较数值响应内容的用例，`network.har` 被列为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`F2_trace_dependent_decision_rules`
- 为什么修改：这些规则要求成功地重新评估 trace，并将缺失或不可读的 trace 归类为 undecided，尽管该 trace 对所配置的响应比较不具决定性。
- 应如何修改：从 `success_if` 和 `undecided_if` 中移除 trace 保留条件。将 undecided 限制为完整 agent 响应的丢失或完整性/来源验证失败；完整但无效的响应和响应 evaluator 错误仍为 failure。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`F3_unsupported_stronger_extra_key_gap`
- 为什么修改：更强条件的理由称 schema normalization 会忽略所检索项目中的额外字段，但适用的 normalization 路径会保留这些字段，且对象比较会拒绝额外 key。
- 应如何修改：删除冗余的精确 key 要求和错误的投影理由。如果保留更强条件，应将其限制为有依据的要求：`order_count` 必须编码为 JSON integer，而不能仅仅作为 number 进行比较。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`F4_checklist_nonminimal_and_incoherent`
- 为什么修改：额外的 trace artifact 和缺乏依据的更强条件理由增加了不具决定性的范围，并与所表示的 evaluator 路径冲突。
- 应如何修改：使用紧凑且仅依赖响应的原生规则，以及替换正文中提供的、范围严格受限且有依据的更强条件。

## Case 50

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：以 2023 年 6 月 12 日为基准，统计过去一年内的 complete orders 数量，以及包含 shipping and handling fees 的总支出。用户要求只返回含 `order_count`（integer）和 `amount`（number）的对象，不附加任何说明。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 比较稀疏 expected 字段：`task_type` 归一化为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 在 array/object schema 下恰含一个对象，其中 `amount` 按 `currency` 归一化为 `6560.69`、`order_count` 按 `number` 归一化为 `21`。比较使用 `ordered: false`，但仍要求集合元素数量及对象键和值完全匹配；`performed_operation` 可在缺少 `task_type` 时作为旧别名，物化默认值 `error_details: null` 和其他未配置顶层字段不参与比较。字符串响应可经过 fenced JSON 提取和 JSON 解码，非列表 retrieved data 可被整理为单元素集合；本 case 未配置 `NetworkEventEvaluator`、事件 filter 或 last-event 语义。`TaskEvalResult.score` 仅在该唯一 evaluator 无断言失败或错误且得分为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 为 `TaskEvalResult.score == 1.0`，要求唯一的 `AgentResponseEvaluator` 将响应归一化并精确匹配 `RETRIEVE`、`SUCCESS` 以及含 `{amount: 6560.69, order_count: 21}` 的无序单元素集合。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并在 success 中要求 HAR 与 evaluation context 正常加载；响应结构缺失、额外或不匹配，以及 trace、编排、归一化或 evaluator 错误均被列为 failure。若所需响应或 trace 缺失或不可读，且没有保留官方 `TaskEvalResult`，draft 将其列为 undecided。其非空 stronger condition `raw_requested_answer_format` 另行要求原始答案是只含 `order_count: 21` 和 `amount: 6560.69` 的裸 JSON 对象，无 prose 或 code fence，并以归一化前的 raw `agent_response.json` 为证据。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_har`
- 为什么修改：`network.har` 被指定为决定性证据，但唯一配置的 evaluator 是 `AgentResponseEvaluator`，且其配置的数值响应比较可以根据 `agent_response.json` 重建。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，将其作为最小充分原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_rules`
- 为什么修改：原生 success 当前要求 HAR/context 可加载，并将 trace 留存缺失或不可读归类为 undecided。
- 应如何修改：基于留存的完整响应确定原生 success、failure 和 undecided 结果。将 undecided 限于该响应发生丢失、损坏、截断、不可读或溯源失败的情况；完整但无效的响应或 evaluator 错误仍为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_clauses`
- 为什么修改：Trace 解析和留存条款向原本紧凑的响应 evaluator 检查清单中增加了非决定性证据和规则。
- 应如何修改：移除原生 HAR artifact 以及 trace 特定的 success、failure 和 undecided 表述，同时保留响应 evaluator 的解析、normalization、比较和错误语义。

## Case 51

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：以 2023 年 6 月 12 日为基准，统计过去六个月内 complete orders 的数量及包含 shipping and handling fees 的总支出。输出必须仅为包含 `order_count`（integer）和 `amount`（number）的对象。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 要求稀疏配置字段归一化为 `task_type: RETRIEVE`、`status: SUCCESS`，并使 `retrieved_data` 在 array/object/number/currency schema 下恰好匹配一个含 `order_count: 7` 和 `amount: 1700.84` 的对象。`ordered: false` 表示数组无序匹配，但元素数、对象键和值仍须精确一致；缺少 `task_type` 时接受 `performed_operation` 别名，而物化的 `error_details: null` 及其他未选择顶层字段不比较。字符串输入可提取 fenced JSON 后解析，retrieved data 再作 schema normalization；未配置网络事件 filter 或 last-event 规则。唯一 evaluator 必须无断言失败或错误并得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 把 benchmark success 定义为唯一 `AgentResponseEvaluator` 得 `1.0`，即响应归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素 `{order_count: 7, amount: 1700.84}`，从而令 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 与 `network.har` 均列作决定性 artifacts，并要求响应比较及 evaluation/orchestration 均无错误；任一比较字段缺失、为 null、格式错误或不相等，或 evaluator/编排出错，均归为 failure。若没有可读 raw response、可用 evaluation-context artifacts，也没有保留的 `TaskEvalResult`，则归为 undecided。非空 stronger condition `bare_object_only` 要求原始用户可见内容严格为裸对象 `{"order_count":7,"amount":1700.84}`，其中 count 是 integer，且无 prose、code fence、envelope fields 或额外键，证据为 `agent_response.json` 或 `TransformedAgentResponse.original_response`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias`
- 为什么修改：原生 failure 规则称缺少 `task_type` 字段会导致失败，但当 `task_type` 不存在时，evaluator 接受 `performed_operation`。
- 应如何修改：说明 `task_type` 可通过 `task_type` 或已发布的旧版别名 `performed_operation` 满足，并且仅当两者在 normalization 后均无法得到 `RETRIEVE` 时才判定为 failure。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_trace`
- 为什么修改：对于唯一配置的检查仅比较 agent 响应的 case，`network.har` 被错误地设为决定性证据；所引用的 trace 行为仅是有条件的环境回退机制。
- 应如何修改：保留完整的 `agent_response.json` 作为唯一的原生决定性 artifact，并从原生决定性证据中移除 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`decision_rule_evidence_scope`
- 为什么修改：这些规则既错误地归类了旧版 task-type 别名，又允许在完整响应不可用时，以未列出的留存 `TaskEvalResult` 避免 undecided。
- 应如何修改：针对 `performed_operation` 限定 `task_type` failure 条件，并将 `undecided_if` 限于完整响应证据缺失、损坏、截断或溯源不确定的情况。明确完整但为 null、无效或不匹配的响应判定为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：不必要的 trace 要求和未声明的 `TaskEvalResult` 替代项使原生证据模型不够精简且内部不一致。
- 应如何修改：采用一条基于完整且具有溯源关联的 `agent_response.json` 的一致原生证据路径，并仅为更强条件保留所需的任何原始输出导出。

## Case 54

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查询从 Carnegie Mellon University 步行到 Univ of Pittsburgh 所需时间。用户要求只返回 `HH:MM:SS` 格式的字符串，不附加其他内容。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应归一化后的稀疏字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 在 array-of-duration schema 下是否恰为与 `25min` 等价的单元素集合。比较为 `ordered: false`；时长会作 duration normalization，因此衡量的是与 `25min` 的归一化等价，而非原始字面格式，且多出或缺少元素都会失败；`performed_operation` 可作为 `task_type` 的旧别名，`error_details` 等未配置字段不比较。该 case 没有 `NetworkEventEvaluator`，因而没有网络 filter 或 last-event 语义，HAR 内容也不进入此响应比较。只有唯一 evaluator 无断言或执行错误且得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native success 是 `TaskEvalResult.score == 1.0`：唯一 `AgentResponseEvaluator` 将响应匹配为 `RETRIEVE`、`SUCCESS` 和与 `25min` 等价的无序单元素 duration。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求两项输入可解析；输入、编排或 evaluator 错误，或 task type、status、duration 的缺失、额外或不等价，均归为 failure。若重建所需输入 artifact 缺失、不可读、截断或无法归属于该 run，则归为 undecided。两个非空 stronger conditions 分别是 `exact_hhmmss_presentation`，要求唯一值字面上为 `00:25:00` 且无额外 prose；以及 `osrm_walking_route_evidence`，要求 `network.har` 证明存在对应两端点且支持该时长的成功 OSRM walking-directions 请求，并由 `agent_response.json` 核对结果。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_not_decisive`
- 为什么修改：`network.har` 被错误地纳入原生决定性证据，但没有任何已配置的 evaluator 检查网络事件。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分原生证据。HAR 可继续作为 OSRM 更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_in_native_decision_rules`
- 为什么修改：原生规则要求两个评估输入均可解析，并且可能因缺少留存的 HAR 证据而判定为 undecided。
- 应如何修改：从原生 success 条件中移除 HAR 可解析性要求，并将原生 undecided 限于影响 `agent_response.json` 的留存、完整性或溯源丢失。对于完整但无效的响应、不匹配和 evaluator 错误，仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_native_har_branch`
- 为什么修改：未使用的原生 HAR 分支增加了本可避免的 artifact 和规则复杂度。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator` 精简原生检查清单，并仅在有独立依据的 OSRM 更强条件下保留 `network.har`。

## Case 55

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查询从 the Starbucks near CMU 步行到 Chatham university 的时间。返回值必须只是一个 `HH:MM:SS` 格式字符串，不得包含额外说明。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对稀疏配置字段进行解析和归一化，要求 `task_type: RETRIEVE`、`status: SUCCESS`，并要求 `retrieved_data` 在 duration array schema 下恰含一个与 `30min` 等价的值。响应字符串可去除空白、提取 fenced JSON 并尝试 JSON parsing；`performed_operation` 可作为缺失 `task_type` 时的旧字段名，标量 retrieved data 可整理成 duration collection。集合按 `ordered: false` 精确比较，缺失或额外项目失败，`error_details` 和其他未配置 raw fields 不参与比较；本 case 没有网络 filter 或 last-event evaluator 语义。唯一 evaluator 无失败断言或错误且得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明官方 evaluation 无错误、唯一 `AgentResponseEvaluator` 得 `1.0` 且响应归一化为 `RETRIEVE`、`SUCCESS` 和与 `30min` 等价的单元素 duration 时，`TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都视为决定性 artifacts，并要求用完整 artifacts replay 成功；响应无效、字段或 duration 缺失、额外或不匹配，以及 evaluator 错误均为 failure，HAR 无法解析或 evaluation context 无法构造也被写成 failure。任一 post-run `agent_response.json` 或 `network.har` 缺失或不完整且其余证据不能确定 evaluator 输入或官方分数时，归为 undecided。非空 stronger conditions 为 `exact_hhmmss_answer_format`，要求唯一值严格为 `"00:30:00"` 且无额外文本或数据；以及 `osrm_route_evidence`，要求 HAR 记录指定端点间成功的 OSRM walking-directions exchange，且其 duration 与 `agent_response.json` 一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被错误地指定为原生决定性证据，但唯一配置的 evaluator 仅比较 agent 响应。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分原生 artifact。HAR 可继续作为明确规定的更强 OSRM 使用条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：尽管未配置网络检查，原生规则仍使 HAR 的完整性和可解析性影响 success、failure 或 undecided。
- 应如何修改：重写 `success_if`、`fail_if` 和 `undecided_if`，使原生分类取决于完整的 agent 响应和已发布的 `AgentResponseEvaluator` 语义；仅在该响应证据丢失或其溯源受损时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：原生检查清单包含重冗余的 HAR 特定证据和规则，而重建已配置的分数并不需要这些内容。
- 应如何修改：删除原生 HAR artifact、HAR failure 规则以及 undecided 规则中的 HAR 分支，同时仅在更强 OSRM 条件下保留 HAR。

## Case 56

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查询从 Carnegie Museum of Art 步行到 a library at CMU 的时间。用户要求仅返回 `HH:MM:SS` 格式的字符串，不附加任何细节。

### Benchmark 怎么测

该任务只配置一个 `AgentResponseEvaluator`，其 sparse expected 要求归一化字段为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 在 array-of-duration schema 下恰好含一个与 `11min` 等价的值。字符串或 fenced JSON 会按 released extraction 规则解析，标量 retrieved value 可被整理成单元素集合；`performed_operation` 可替代缺失的 `task_type`，物化默认 `error_details` 与未选择的额外 raw object fields 不比较。集合采用 `ordered: false` 的精确比较，duration normalization 不强制原始 `HH:MM:SS` 字面形式；此 case 未配置网络事件 filter 或 last-event 语义。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`，任何断言失败或 evaluator/task error 都使任务不满足该组合条件。

### 原本 draft 是什么

原 draft 声明唯一 `AgentResponseEvaluator` 在响应解析并归一化为 `RETRIEVE`、`SUCCESS` 和与官方 `11min` 匹配的无序单元素 duration 时得 `1.0`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求 replay 响应和 trace 无错误；null 或非对象响应、必需字段缺失或不匹配、duration 缺失、额外、不可归一化或不等，以及 response/trace parsing、context construction、normalization 或 orchestration 错误，均列为 failure。若提交响应或所需 trace 缺失、截断，且无保留的官方 evaluation result 可恢复输入或分数，则列为 undecided。非空 stronger conditions 包括 `raw_hh_mm_ss_only`，要求用户可见值严格为 `00:11:00` 且无解释；以及 `osrm_walking_route_evidence`，要求 `network.har` 包含连接 Carnegie Museum of Art 与 CMU library 坐标的 OSRM walking-directions 请求，并由响应 duration 支持报告值。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_trace_not_configured_check`
- 为什么修改：原生规则将 trace 解析和基于 trace 的环境修复转化为 case success 条件，但任务 56 仅配置了 `AgentResponseEvaluator`，其实际值为 `context.agent_response_raw`。
- 应如何修改：将原生 success 和 failure 限定于已发布的 `AgentResponseEvaluator` 的解析、normalization、比较及所得分数。不要将网络 trace 处理作为此 case 的独立原生谓词。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`surplus_native_network_artifact`
- 为什么修改：基于批处理 artifact 合约和通用编排行为，`network.har` 被列为原生决定性证据，但任务 56 中没有任何已配置的 evaluator 检查网络事件。
- 应如何修改：使用完整的 `agent_response.json` 作为唯一的原生决定性 artifact。仅在 OSRM 更强条件下保留 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_changes_native_decision`
- 为什么修改：尽管唯一配置的是响应检查，success、failure 和 undecided 规则仍都使原生处置取决于留存的 trace。
- 应如何修改：从 `success_if` 中移除 trace 重放，从 `fail_if` 中移除 trace 解析/context failure，并将 `undecided_if` 限于所提交响应证据的丢失或完整性/溯源失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal`
- 为什么修改：原生部分重复了多余的 trace 要求，使检查清单比已配置的 case 语义所要求的更庞大、更严格。
- 应如何修改：围绕 `agent_response.json` 精简原生部分，并将所有依赖 trace 的检查完全移至已有支持的 OSRM 更强条件。

## Case 57

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：找出 Carnegie Mellon University 的 University Center 附近距离最近的餐厅。官方指令为“Get the closest restaurant(s) to university center at Carnegie Mellon University”，task revision 为 `2`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查响应中稀疏配置的 `task_type`、`status` 和 `retrieved_data`：前两者应归一化为 `RETRIEVE`、`SUCCESS`，后者按 `location-name` 字符串数组归一化后，须与 `El Gallo de Oro`、`Back Bar Grill`、`Grano`、`Beefsteak`、`Nourish`、`Schatz Dining Room`、`Au Bon Pain` 构成的预期数组完全一致。`ordered=false`，因此忽略顺序，但缺项、多项或重复次数不符均不匹配；稀疏配置未要求比较物化后默认的 `error_details=null`。配置中没有 filter 或 last-event 检查，也没有 `NetworkEventEvaluator`；`network.har` 虽是 required run artifact，但不是这个响应比较的决定性输入。唯一 evaluator 的 score 必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是最终响应可解析，且归一化后的 `task_type=RETRIEVE`、`status=SUCCESS` 和七个餐厅名称组成的无序精确数组均匹配，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult.score` 都为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，后者用于确认网络 trace 可解析并可构造或验证 evaluation context。其 success 条件要求响应字段和七名称数组精确匹配且评估无错误；failure 包括响应不可解析、字段或数组不匹配、trace/context/orchestration 错误或 evaluator 非 `1.0`；undecided 则包括无法凭保留的最终响应、可评估 trace 或 `TaskEvalResult` 确定结果。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：对于这个仅使用 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json`，作为重建已配置响应比较所需的最小充分 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：仅因未留存可评估的网络 trace，undecided 规则就可能将一次运行归类为 undecided。
- 应如何修改：将 `undecided_if` 限于完整 agent 响应的丢失、截断、损坏或溯源不确定。明确将完整但无效或为 null 的响应继续归为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：Trace 特定的 artifact 和决策文本使原生检查清单不够精简。
- 应如何修改：删除 trace 特定的决定性问题和 trace 留存依赖，同时保留以下一般规则：产生非 `1.0` 分数的 evaluator 或编排错误属于原生 failure。

## Case 59

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：找出 CMU Hunt library 附近距离最近的餐厅。官方指令为“Get the closest restaurant(s) to CMU Hunt library”，task revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较稀疏配置中的 `task_type`、`status`、`retrieved_data`，预期分别为归一化后的 `RETRIEVE`、`SUCCESS` 和单元素数组 `["The exchange"]`。字符串响应可经去空白、fenced JSON 提取及 JSON 解码形成 evaluator-visible object；`performed_operation` 可作为 `task_type` 的兼容别名，未被稀疏配置选中的原始字段及物化默认值 `error_details=null` 不参与比较。`retrieved_data` 按 `location-name` 数组 schema 归一化，且 `ordered=false`，所以顺序不计，但缺失、额外或重复元素均不匹配；没有 filter、last-event 或 `NetworkEventEvaluator` 语义。唯一 evaluator 必须无错误且 score 为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 宣称成功时 `TaskEvalResult.score=1.0` 且为 success status，并要求唯一 `AgentResponseEvaluator` 对 `RETRIEVE`、`SUCCESS` 和无序单例 `["The exchange"]` 的归一化比较不产生 assertion。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，其中 HAR 被用于解析 `NetworkTrace`，并在环境 URL 不可用时为 evaluator 的 URL fallback 提供事件。success 要求结构化响应匹配、单例数组无缺失或额外项、trace 可解析且评估无错误；failure 包括响应结构或值不符、trace 缺失或不可解析、context/orchestration 错误以及任一非 `1.0` score；undecided 是保留证据中缺少可读响应和可用 trace，且没有官方结果解决比较。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`official-semantics-response-processing`
- 为什么修改：原生规则遗漏了与分数相关的响应提取和显式字段行为，并且尽管不存在 `NetworkEventEvaluator`，仍将 HAR 解析作为 success 的一部分。
- 应如何修改：说明已发布的提取逻辑接受解码后的 JSON，包括从 fenced block 中提取的 JSON；`performed_operation` 可以提供 `task_type`；并且仅选择稀疏配置的 `task_type`、`status` 和 `retrieved_data`，因此不比较 `error_details` 和其他原始额外字段。移除将 HAR 解析作为已配置 success 谓词的要求。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal-har-evidence`
- 为什么修改：`network.har` 被指定为决定性证据，但唯一配置的 evaluator 从 agent 响应中获取其实际值。
- 应如何修改：仅保留完整的 `agent_response.json` 作为最小的原生决定性 artifact，并从 undecided 规则中移除留存 HAR 的可用性要求。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-decision-rules`
- 为什么修改：当前的 success 和 undecided 规则使 trace 解析或留存成为判定唯一响应 evaluator 所必需的条件。
- 应如何修改：基于完整响应和已发布的响应比较确定运行后的 success、failure 和 undecided 分类。将 undecided 限于该响应证据丢失、损坏、不完整或溯源失败的情况；完整但无效或不匹配的响应仍为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-nonminimal-trace-scope`
- 为什么修改：HAR artifact 及相关规则为仅含一个 evaluator 的响应 case 增加了不必要的审查范围。
- 应如何修改：删除 HAR 决定性 artifact 条目以及依赖 trace 的 success 和 undecided 条款，同时保留 evaluator 错误和非 `1.0` 分数的 failure 语义。

## Case 60

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：找出 CMU Posner Hall 附近距离最近的餐厅。官方指令为“Get the closest restaurant(s) to CMU Posner Hall”，task revision 为 `2`。

### Benchmark 怎么测

仅有一个 `AgentResponseEvaluator`，它解析响应并比较稀疏配置明确列出的 `task_type`、`status` 和 `retrieved_data`，预期为归一化后的 `RETRIEVE`、`SUCCESS` 及 `["The exchange"]`；物化产生的默认 `error_details=null` 不是额外比较字段。`retrieved_data` 使用元素格式为 `location-name` 的数组 schema 归一化，并因 `ordered=false` 按无序精确单例比较，任何缺失或额外项都不匹配；支持的 `performed_operation` 可作为 `task_type` 别名。配置没有 filter、last-event 或网络事件 evaluator。唯一 evaluator 的 score 必须等于 `1.0`，整体 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 定义为唯一 `AgentResponseEvaluator` 无错误完成，且响应归一化为 `task_type=RETRIEVE`、`status=SUCCESS`、无序单例 `["The exchange"]`，从而令 `TaskEvalResult.score=1.0`。它把 `agent_response.json` 和 `network.har` 都作为决定性 artifacts，认为 HAR 必须能解析为构造 evaluation context 所需的 `NetworkTrace`。success 要求保留的响应与 HAR 均可无错误评估并完全匹配；failure 包括任何结构或字段不匹配、缺失或额外 retrieved item，以及无效或不可用的响应/trace、归一化异常、evaluator 异常或 orchestration 错误；undecided 包括响应或 HAR 未保留、不可读或无法归属于该 run。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_har_artifact`
- 为什么修改：`network.har` 被列为决定性证据，但唯一配置的 evaluator 仅检查 agent 响应，而且该材料未显示 HAR 内容会改变此 case 的响应比较。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_loss_misclassified_as_undecided`
- 为什么修改：这些规则将留存的 HAR 证据缺失或不可读判定为 undecided，但已配置的响应结果仍可根据完整响应重建。
- 应如何修改：从 success 和 undecided 的前提条件中移除留存 HAR；将 undecided 限于唯一已配置 evaluator 所需响应证据的丢失、损坏或溯源失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_conditions`
- 为什么修改：与 HAR 相关的 artifact 和规则文本在原本紧凑的检查清单中处处增加了非决定性条件。
- 应如何修改：删除 HAR artifact 和 HAR 特定的留存条款，同时保留响应不匹配和 evaluator 错误作为原生 failure。

## Case 61

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：找出 CMU Sorrells Library 附近距离最近的餐厅，包括并列最近者。官方指令为“Get the closest restaurant(s) to CMU Sorrells Library”，task revision 为 `2`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对响应进行字符串或代码块 JSON 提取、解析和预期字段归一化，再比较 `task_type=RETRIEVE`、`status=SUCCESS` 与 `retrieved_data=["La Prima Espresso"]`；物化默认字段 `error_details=null` 并非稀疏配置中的比较项。`retrieved_data` 按 `location-name` 数组 schema 归一化，并在 `ordered=false` 下作无序精确比较，因此错误、缺失、重复或额外项目都会失败。配置不含 filter、last-event 条件或 `NetworkEventEvaluator`。唯一 evaluator 的 score 为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 task 61 成功要求唯一 `AgentResponseEvaluator` 得到 `1.0`，即归一化响应精确匹配 `RETRIEVE`、`SUCCESS` 和无序单例 `["La Prima Espresso"]`，并使 `TaskEvalResult.score=1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，要求 HAR 足以重建官方 evaluator replay 所需的 network-trace 和 environment context。success 要求完整响应与 trace 重放后 evaluator 为 `1.0`；failure 包括响应不可解析或非对象、键或字段不匹配、retrieved data 缺失或错误，以及 trace/context 错误；undecided 包括响应或 trace 缺失、截断、损坏或无法归属于 task 61，且没有完整官方 `TaskEvalResult`。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`bf_official_semantics_trace`
- 为什么修改：原生规则将 HAR 重放和 trace/context 错误提升为唯一 `AgentResponseEvaluator` 声明的条件。
- 应如何修改：仅通过对完整 agent 响应进行已发布的解析、normalization 和比较来说明原生 success 和 failure，同时保留 `AgentResponseEvaluator` 错误计分为 `0.0` 的规则。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`bf_nonminimal_har`
- 为什么修改：尽管不存在任何 `NetworkEventEvaluator`，`network.har` 仍被指定为必需的决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`；保留完整的 `agent_response.json` 作为最小充分 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`bf_decision_trace_dependency`
- 为什么修改：这些规则要求有 trace 才能判定 success，并允许因 trace 缺失或损坏而判定为 undecided，尽管已配置的比较可以根据完整响应重建。
- 应如何修改：移除依赖 trace 的 success、failure 和 undecided 条款。将 undecided 限于 `agent_response.json` 的完整性、数据完整性或溯源丢失；完整但无效或不匹配的响应必须判定为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`bf_minimality`
- 为什么修改：额外的 HAR artifact 和三个依赖 trace 的决策条款对此 case 并非必要，并使检查清单不够精简。
- 应如何修改：使用一个决定性 artifact 和简洁的仅响应决策规则，不添加任何运行结果或元数据。

## Case 63

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点完成一个 `RETRIEVE` 任务：返回整个订单历史中已完成订单数量位居第二的客户邮箱，包括并列者。官方指令为“Get customer email(s) who completed the second most number of orders in the entire history”，task revision 为 `2`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查稀疏配置中的 `task_type`、`status` 和 `retrieved_data`，预期分别归一化为 `RETRIEVE`、`SUCCESS`，以及字符串数组 `["helloworld@yahoo.com","michael.nguyen@yahoo.com"]`。`retrieved_data` 使用 array-of-strings schema 归一化，并因 `ordered=false` 作无序精确比较：顺序不影响结果，但缺失、额外、错误或重复次数不平衡均不匹配；物化默认值 `error_details=null` 不参与比较。配置中没有 filter、last-event 或 `NetworkEventEvaluator` 规则。唯一 evaluator 必须无错误且 score 为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称该 case 当且仅当唯一 `AgentResponseEvaluator` 为 `1.0` 时成功，即解析和归一化后的响应匹配 `RETRIEVE`、`SUCCESS`，并恰好包含无序的 `helloworld@yahoo.com` 与 `michael.nguyen@yahoo.com`，从而令 `TaskEvalResult.score=1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，后者用于构造和运行官方 evaluation context 所需的 `NetworkTrace`。success 是用完整保留 artifacts 评估时无 assertion 或 evaluator error；failure 是任一结构或归一化值不匹配、邮箱缺失或多余、evaluation error 或非 `1.0` score；undecided 是没有官方结果且响应或 HAR 因丢失或截断而无法检查或重评，但已保留的 null、畸形或不匹配提交被归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：对于唯一配置的检查为 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，作为重建已配置比较所需的最小充分 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：undecided 规则错误地将 `network.har` 缺失或被截断视为无法重建原生 success 的原因。
- 应如何修改：将 `undecided_if` 限于影响 `agent_response.json` 的留存、完整性或溯源丢失；将完整但格式错误、为 null、不匹配或导致 evaluator 错误的响应继续归为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：额外的 HAR 要求使检查清单不够精简，并与其中关于仅配置了 `AgentResponseEvaluator` 的正确陈述相冲突。
- 应如何修改：移除 HAR artifact 以及所有依赖 HAR 的 success 或 undecided 表述，使检查清单始终一致地依赖唯一 evaluator 的响应证据。

## Case 66

### 原本 case 是什么

原始任务是在 `reddit` 站点执行 `RETRIEVE`：查看“Books”论坛最热门的前 10 个帖子，返回其中恰好推荐一本书的帖子的标题。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它按字符串/JSON 响应解析与规范化规则检查显式字段 `task_type`、`status` 和 `retrieved_data`；`results_schema` 要求结果为字符串数组，物化出的默认 `error_details:null` 不属于显式比较字段。期望为 `task_type=RETRIEVE`、`status=SUCCESS`，且 `retrieved_data` 精确包含 `"I just finished reading The Hobbit to my 6 year old daughter, and she loved it!"` 和 `"Apple Books has a free audiobook of A Christmas Carol narrated by LeVar Burton!"`；`ordered=false` 表示忽略顺序，但缺项、重复项、多项或不匹配字符串均不符合。配置没有单独核验“前 10 个”“最热门”或“恰好推荐一本书”的来源过程，也没有 last-event evaluator；唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误地得到 `1.0`，从而产生 `TaskEvalResult` 的 `score 1.0/status success`，决定性响应内容为上述 `RETRIEVE`、`SUCCESS` 和无序双标题集合。它把 `agent_response.json` 与 `network.har` 都列为 decisive artifacts，并将 HAR 解析、Reddit base URL fallback 和编排无错误纳入成功与失败条件。draft 将响应无效、字段不匹配、结果为空或标题缺失/多余，以及解析、规范化、evaluator 或 orchestration 错误判为 failure；若无法确定实际评估的响应和 trace，例如缺少 `agent_response.json`，或缺少 `network.har` 且未保留官方 `TaskEvalResult`，则判为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管此案例只有一个 `AgentResponseEvaluator`，且其非 URL 标题比较仅凭 `agent_response.json` 即可重建。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并仅保留完整的 `agent_response.json`，将其作为唯一的最小决定性 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_driven_decision_rules`
- 为什么修改：success、failure 和 undecided 规则不恰当地依赖所保留 trace 的解析或可用性。
- 应如何修改：移除 trace 特有的 success/failure 条款，并将 undecided 限制为影响实际受评估 agent response 的丢失、损坏、完整性问题或来源歧义。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`repeated_nondecisive_har_semantics`
- 为什么修改：通用 HAR 解析和环境回退语义为原本紧凑、仅针对 response 的检查清单增加了重复且对本案例不具决定性的内容。
- 应如何修改：删除 native 部分各处的 HAR/回退内容，同时保留 response evaluator 的确切解析、normalization、比较和组合语义。

## Case 68

### 原本 case 是什么

原始任务是在 `reddit` 站点执行 `RETRIEVE`：从“Books”论坛最热门的前 10 个帖子中，找出恰好推荐一本书的帖子，并按帖子描述中的原样文字返回作者名和书名。输出须为对象列表，每个对象使用键 `"book"` 和 `"author"`；任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它解析并规范化显式字段 `task_type`、`status`、`retrieved_data`，其中 `performed_operation` 可作为缺失 `task_type` 的旧名称；`results_schema` 是对象数组，每个对象含字符串字段 `author` 和 `book`，物化默认值 `error_details:null` 及其他未配置顶层字段不参与比较。期望为 `RETRIEVE`、`SUCCESS`，以及与 `[{"author":"Tolkien","book":"The Hobbit"},{"author":null,"book":"A Christmas Carol"}]` 精确结构匹配的结果；`ordered=false` 只忽略数组顺序，不忽略项目重数、对象键集合或字段值。配置没有 last-event evaluator；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得分 `1.0`，使 `TaskEvalResult.score` 为 `1.0`，并要求规范化后的 `RETRIEVE`、`SUCCESS` 及上述两个对象无序精确匹配，不能缺少或增加项目或对象字段。它把 `agent_response.json` 和“Official TaskEvalResult with its AgentResponseEvaluator result”列为 decisive artifacts，后者还要求记录的实际响应与 `agent_response.json` 对应。draft 将响应不可解析、规范化报错、`task_type`/`status` 不匹配、`retrieved_data` 缺失或结构和值不符、任何 assertion 或 evaluator error 判为 failure；只有在既无可读最终响应、也无足以识别响应和结果的对应官方 evaluator result 时才判为 undecided，并明确实际被评估的缺失或畸形响应属于 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`complete_response_cannot_be_replaced`
- 为什么修改：决定性证据集将所保留的 Official `TaskEvalResult` 视为完整 `agent_response.json` 的替代项，尽管已配置 `AgentResponseEvaluator`，且 packet 的 artifact 契约另有要求。
- 应如何修改：对于这个仅针对 response 的案例，仅使用完整的 `agent_response.json` 作为唯一保留的决定性 artifact。移除作为必需或可替代证据来源的 `TaskEvalResult` artifact；任务级评分应根据已发布的组合语义重建。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_requires_complete_response_loss_rule`
- 为什么修改：当前的“既不……也不……”表述可能会在强制要求的完整 response artifact 丢失的情况下仍对一次运行作出分类。
- 应如何修改：当 `agent_response.json` 缺失、不可读、被截断、完整性受损或来源存在歧义时，判定为 undecided。对于完整 artifact 显示受评估 response 本身缺失、为 null、格式错误、不匹配或导致 evaluator 错误的情况，仍判定为 failure。

## Case 69

### 原本 case 是什么

原始任务是在 `reddit` 站点执行 `RETRIEVE`：查看“Books”论坛最热门的前 10 个帖子，从谈论支持本地书店的帖子中取得所涉及组织的 URL，并按帖子描述中的原样文字返回。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它按发布的响应解析规则取得映射，规范化显式字段 `task_type`、`status` 和 `retrieved_data`，允许 `performed_operation` 在 `task_type` 缺失时充当旧名称，并按字符串数组 schema 比较结果。期望语义是 `task_type=RETRIEVE`、`status=SUCCESS`，且恰有一个结果字符串匹配 `bookshop.org` 或 `https://bookshop.org`；`ordered=false` 表示忽略顺序，但不允许缺项或多项，物化的 `error_details:null` 及其他未配置键不比较。该 evaluator 只检查固定响应值，不验证“前 10 个最热门”、帖子是否符合筛选条件、URL 是否在描述中逐字出现或是否完整，也没有 last-event evaluator。唯一 `AgentResponseEvaluator` 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`；解析、规范化、比较或 evaluator/orchestration 错误计为非成功。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得分 `1.0`：响应规范化为 `RETRIEVE`、`SUCCESS`，并恰好包含一个匹配 `bookshop.org` 或 `https://bookshop.org` 的结果，进而使 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为 native decisive artifacts，并把 HAR 解析、环境 URL fallback、evaluation context 构造及 URL derender 无错误纳入成功、失败和 undecided 判断。draft 将空值或不可解析响应、任务类型或状态缺失/不匹配、结果缺失/为空/出现未接受值或数量不符，以及输入解析、evaluator 或 orchestration 错误判为 failure；若证据不能确定实际响应或可解析 trace，且没有官方 `TaskEvalResult` 消除不确定性，则判为 undecided。它还给出非空 stronger condition `verify_source_scope_and_literal_urls`：要求以 `network.har` 的响应体额外证明每个报告字符串逐字出现在 Books 热门前 10 中符合条件的帖子描述里，并证明没有遗漏其他符合条件的组织 URL。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_minimal`
- 为什么修改：对于唯一已配置 evaluator 仅比较 agent response 的案例，`network.har` 被错误地指定为 native 决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅为明确规定的更强来源/完整性条件保留它，因为其内容与该条件相关。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_causes_undecided`
- 为什么修改：native undecided 规则将无法确定存在可解析的保留 trace 视为可能阻碍结果判定，尽管重建已配置 `AgentResponseEvaluator` 的比较并不需要该 trace。
- 应如何修改：将 `native undecided_if` 限制为提供给评估的确切 agent response 丢失、损坏或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_native_trace_logic`
- 为什么修改：有关条件性环境修复的讨论使 native 检查清单超出了已配置案例语义所要求的范围。
- 应如何修改：删除 native trace artifact 及其相关的 undecided 依赖，同时保留该 trace 作为更强条件的证据。

## Case 71

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`，回答 Chatham University 的 ZIP code。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它解析 evaluator 可见响应，规范化显式字段 `task_type`、`status`、`retrieved_data`，并依据字符串数组 `results_schema` 做结构比较；物化的默认 `error_details:null` 不属于显式比较字段。期望为 `task_type=RETRIEVE`、`status=SUCCESS` 和精确的单元素结果 `［"15232"］`；`ordered=false` 虽表示忽略顺序，但缺失、重复、错误或额外值均失败。没有配置 NetworkEvent 或 last-event evaluator；唯一 evaluator 得分必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得分 `1.0`：解析和规范化后的响应匹配 `RETRIEVE`、`SUCCESS` 与无序单元素 `［"15232"］`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为 decisive artifacts，并把 HAR 可解析、评估无输入/配置/编排错误作为成功条件。draft 将非结构化响应、规范化或比较错误、任务类型或状态缺失/不匹配、结果缺失/null/错误/多余判为 failure，也将 trace 缺失或不可解析以及 orchestration error 判为 failure。若缺少完整可读的 `agent_response.json` 或 `network.har`，且没有官方 `TaskEvalResult` 确定结果，则判为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的案例，`network.har` 被错误地指定为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并仅保留完整的 `agent_response.json`，将其作为重建已配置比较的唯一最小 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：即使 trace 内容不属于已配置 response 比较的一部分，决策规则仍以 HAR 的可用性或可解析性作为 native success、failure 和 undecidability 的条件。
- 应如何修改：移除依赖 HAR 的 success 和 failure 表述，并将 undecided 状态限制为 evaluator 可见的 agent response 丢失、损坏或来源不确定。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`excess_native_material`
- 为什么修改：与网络相关的 artifact 问题和规则为原本紧凑的检查清单增加了非决定性内容。
- 应如何修改：删除网络 artifact 条目以及所有对应的网络条款和支持指针，同时保留 response evaluator 语义。

## Case 72

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`，回答 Yale University 的 ZIP code。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，由它解析、规范化并结构比较最终响应中的显式字段 `task_type`、`status` 和 `retrieved_data`；结果 schema 是字符串数组，物化的默认 `error_details:null` 不单独计分。期望为 `task_type=RETRIEVE`、`status=SUCCESS`，并且 `retrieved_data` 精确等于单元素字符串结果 `［"06516"］`；`ordered=false` 表示顺序无关，但缺失或额外元素不符合。没有配置 NetworkEvent 或 last-event evaluator；唯一 evaluator 必须得分 `1.0`，all-evaluators 组合规则才令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 是 `TaskEvalResult.score = 1.0`，要求唯一 `AgentResponseEvaluator` 得分 `1.0`，且响应规范化为 `RETRIEVE`、`SUCCESS` 和无序单元素 `［"06516"］`。它将 `agent_response.json` 与 `network.har` 都列为 decisive artifacts，并要求 trace 能作为必需输入解析而不引起评估设置或编排错误。draft 将响应无法解释为映射、任务类型或状态缺失/不匹配、结果缺失/为空/规范化失败/值错误/元素数量不符，以及畸形保留输入造成的评估错误或任一 evaluator 非 `1.0` 判为 failure。若没有 `TaskEvalResult`，且最终响应或必需 trace 缺失、截断或不可读而无法重建比较，同时现有证据尚未证明 native mismatch，则判为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一已配置的 evaluator 读取最终 agent response，且未配置 `NetworkEventEvaluator`。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为重建已配置检查所需的最小充分保留证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：failure 和 undecided 规则使 HAR 完整性成为结果的决定因素，并提及了一个未被列为决定性 artifact 的保留 `TaskEvalResult`。
- 应如何修改：仅以 `agent_response.json` 为规则依据：完整但无效或不匹配的 response 判定为 failure，而缺失、损坏或来源不确定的 response 证据仅在没有任何可用证据已能证明 failure 时判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：对于这个仅有 `AgentResponseEvaluator` 的案例，额外的 HAR artifact 和依赖 HAR 的规则超出了所需的最小证据范围。
- 应如何修改：删除 HAR artifact 及相关的依赖 HAR 条款，同时保留 response 解析、normalization、比较、evaluator 错误和任务组合语义。

## Case 73

### 原本 case 是什么

原始任务是在 `map` 站点查询 Columbia University 的邮政编码，官方指令为“What is the zip code of Columbia University?”，task type 是 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它按字符串数组 schema 解析和规范化最终响应，并核对显式 expected 字段：`task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`、`retrieved_data` 在 `ordered=false` 下精确等于无序单元素数组 `["10027"]`；物化产生的 `error_details: null` 不是稀疏配置中显式要求比较的字段。没有配置 `NetworkEventEvaluator`，因此没有网络事件 filter 或 last-event 判定语义。所有 evaluator 分数都必须等于 `1.0`；本例只有该 evaluator，所以其分数为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误完成，并在解析、规范化后接受 `RETRIEVE`、`SUCCESS` 和无序单元素 `["10027"]`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将响应或 trace 的解析、上下文或编排错误写为 failure。它将实际提交的响应或 trace 未被完整、可归属地保留且没有官方 `TaskEvalResult` 写为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一已配置的 evaluator 读取 `agent_response_raw`，且未配置 `NetworkEventEvaluator`。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整且来源可归属的 `agent_response.json` 作为本案例的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：success、failure 和 undecided 规则不恰当地依赖 trace 的解析或保留来重建已配置的 response 检查。
- 应如何修改：移除依赖 trace 的 success/failure 条件，将完整但无效或不匹配的 response 判定为 failure，并仅在所提交 response 丢失、被截断或来源验证失败时判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`excess_case_evidence`
- 为什么修改：不必要的 trace artifact 及相关条款使检查清单不够精简。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator` 和 `agent_response.json` 精简检查清单，同时保留确切的预期字段、schema、无序比较、组合和错误语义。

## Case 74

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service，从 Carnegie Mellon University 出发，为 Carnegie Mellon University、apple store shadyside 和 starbucks on craig street 找出使总旅行时间最短的访问顺序；task type 是 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 使用元素格式为 `location-name` 的字符串数组 schema 规范化最终响应，并检查 `task_type=RETRIEVE`、`status=SUCCESS`，以及 `retrieved_data` 按 `ordered=true` 精确匹配 `["Carnegie Mellon University","starbucks on craig street","apple store shadyside"]`；物化默认值 `error_details: null` 不是显式配置的比较字段。没有配置 `NetworkEventEvaluator`，故原生计分没有网络 filter 或 last-event 语义，也不检查是否实际调用 OSRM。所有 evaluator 分数须为 `1.0`；由于仅有一个 evaluator，其分数直接决定 `TaskEvalResult.score` 是否为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是最终响应经规范化后按配置顺序匹配三处地点，唯一的 `AgentResponseEvaluator` 得分 `1.0`，进而令 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与可解析为 `NetworkTrace` 的 `network.har` 都列作决定性 artifacts；响应结构、类型、状态、地点内容或顺序错误，以及响应或 trace 引发的解析、上下文、规范化、evaluator 或编排错误均被写为 failure。它把 artifacts 缺失、截断或无法归属于该运行且无评估结果的情形写为 undecided。非空 stronger condition `osrm-use-evidenced` 另要求 `network.har` 显示一次成功的 OSRM directions 请求，且有序 waypoints 对应 Carnegie Mellon University、Starbucks on Craig Street、Apple Store Shadyside。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native-har-not-decisive`
- 为什么修改：对于唯一已配置 evaluator 读取 agent response 的案例，`network.har` 被错误地列为 native 决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅在明确规定的更强 OSRM 使用条件下保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-native-rules`
- 为什么修改：native success、failure 和 undecided 规则与所保留的 HAR 绑定，尽管缺少该 HAR 并不会妨碍重建已配置的 response 比较。
- 应如何修改：使 native 决策依赖完整的 evaluator 可见 response 和已发布的 `AgentResponseEvaluator` 语义。将 undecided 限制为该 response 或等效的结论性运行证据丢失、损坏或来源验证失败；对于完整但无效的 response 和 evaluator 可见的不匹配，仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-native-trace-redundancy`
- 为什么修改：native HAR artifact 和重复的 trace 条件与仅在更强 OSRM 使用核查中才需要的证据重复。
- 应如何修改：删除与 native HAR 相关的 artifact 和决策规则文本，同时在 `stronger.additional_conditions` 下保留 `network.har`。

## Case 75

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service，从 Massachusetts Institute of Technology 出发，为 Massachusetts Institute of Technology、Harvard University 和 Boston Logan International Airport 找出总旅行时间最短的访问顺序；task type 是 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 按元素格式为 `location-name` 的字符串数组 schema 解析和规范化响应，要求 `task_type=RETRIEVE`、`status=SUCCESS`，并以 `ordered=true` 逐位置匹配 `["Massachusetts Institute of Technology","Harvard University","Boston Logan International Airport"]`；`error_details: null` 是物化默认值，不是稀疏 expected 中的显式比较字段。没有 `NetworkEventEvaluator`，所以没有网络事件 filter 或 last-event 语义，配置也不验证 OSRM 调用或路线时长。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是响应经官方 extractor 和 schema normalization 后匹配 `RETRIEVE`、`SUCCESS` 及上述有序三地点数组，使唯一的 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 都为 `1.0`。它将 `agent_response.json` 和能被解析为 network trace 的 `network.har` 同列为决定性 artifacts，并把响应缺失、不可解析、字段错误或地点缺漏、额外、错误、乱序，以及 HAR 缺失或不可读、evaluator 或编排错误写为 failure。它把无法确认 evaluator 可见响应、HAR 有效性且没有官方结果的证据缺失或截断写为 undecided。非空 stronger condition `osrm_optimality_evidence` 要求 HAR 保留足够的成功 OSRM directions 请求、响应及 route-duration 数据，以在不发起新调用的情况下证明从 MIT 出发的报告顺序在允许顺序中总旅行时间最短，并以 `agent_response.json` 核对所报告顺序。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_har_not_configured_check`
- 为什么修改：native success 和 failure 以 `network.har` 的可读性为条件，尽管唯一已配置的 evaluator 提取并比较 agent response，且未配置网络事件 predicate。
- 应如何修改：从 native benchmark success 和 failure 中移除 HAR 可读性条件。直接说明稀疏配置的 response 字段以及已发布的 normalization/比较行为；仅在更强条件下保留基于 HAR 的 OSRM 验证。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifact`
- 为什么修改：`network.har` 仅为了检查解析或设置而被列为 native 决定性 artifact，尽管完整的 `agent_response.json` 可以重建唯一已配置的 evaluator 检查。
- 应如何修改：将 `agent_response.json` 设为唯一的 native 决定性 artifact。仅保留 `network.har` 作为单独的更强 OSRM 最优性条件的证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har_distorts_native_decision`
- 为什么修改：当前规则可能会基于 HAR 的保留情况/可读性，而非已配置的 response 比较，拒绝判定 native success 或断言 failure。
- 应如何修改：将 native success 和普通 failure 建立在完整的 evaluator 可见 response 以及唯一 evaluator 得出的分数之上。将 native undecided 限制为所提交 response 证据丢失、损坏、被截断或来源验证失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_har_rules`
- 为什么修改：重复的 native HAR 解析、设置、failure 和 undecided 条款使检查清单不够精简，并模糊了 native 评分与更强 OSRM 证据提案之间的界限。
- 应如何修改：删除 native HAR artifact 及其相关的 success、failure 和 undecided 表述，同时保留简洁的 response predicate 和单独的更强条件。

## Case 77

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点统计所有 reviews 中状态为 `Pending` 的总数，task type 是 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 从最终响应中解析并规范化显式 expected 字段，要求 `task_type=RETRIEVE`、`status=SUCCESS`，且 `retrieved_data` 按数字数组 schema 和 `ordered=false` 精确匹配无序单元素 `[5]`；物化的 `error_details: null` 不属于显式配置的比较字段。该 evaluator 会把非 list 的标量结果包装成单元素集合后比较，因此标量 `5` 也可能规范化为该单元素结果；没有 `NetworkEventEvaluator`，故没有 filter 或 last-event 语义。所有 evaluator 分数须为 `1.0`，本例唯一 evaluator 的得分因而决定 `TaskEvalResult.score`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求运行输入无错误地完成评估，响应规范化为 `RETRIEVE`、`SUCCESS` 和无序数字单元素 `5`，使唯一的 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和用于构造评估上下文的 `network.har` 都列为决定性 artifacts；空响应、解析后非对象、字段缺失或不匹配、结果不是数字单元素 `5`，以及 artifact 解析或编排错误都被列为 failure。它把真实最终响应或 required trace 遗失、截断且没有官方逐 case 结果的情况写为 undecided。非空 stronger condition `schema-valid-retrieved-data-array` 额外要求原始响应符合 `FinalAgentResponse`，将 `retrieved_data` 写成 JSON 数组 `[5]`，而不是可被 evaluator 强制包装为单元素的标量。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_trace`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一已配置的检查是 `AgentResponseEvaluator`，其案例特有的数值比较使用所提交的 response，而非网络事件。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的 native artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_controls_decision`
- 为什么修改：这些规则将加载 trace 设为 success 的必要条件，并将 trace 保留失败设为 undecided 的充分条件，从而混淆了批处理保留契约与重建本案例已配置检查所需的证据。
- 应如何修改：以对完整 response 应用已发布的 response evaluator 为依据判定 success 和普通 failure，并将 undecided 限制为重建所需的真实 response 证据丢失或损坏。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_native_evidence`
- 为什么修改：不必要的 trace artifact 和重复的 trace 加载条件使检查清单不够精简且内部约束过度。
- 应如何修改：删除 trace 特有的 native 证据要求，同时保留唯一 evaluator 的解析、normalization、比较和 failure 语义。

## Case 78

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点统计所有 reviews 中状态为 `Approved` 的总数，task type 是 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 解析并规范化最终响应，检查显式配置的 `task_type=RETRIEVE`、`status=SUCCESS`，以及在数字数组 schema、`ordered=false` 下精确等于无序单元素 `[346]` 的 `retrieved_data`；物化默认值 `error_details: null` 不作显式比较。没有配置 `NetworkEventEvaluator`，所以不存在网络 filter 或 last-event 判定语义。所有 evaluator 分数必须等于 `1.0`；本例只有该 evaluator，因此其分数为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是评估完成且响应规范化为 `RETRIEVE`、`SUCCESS` 和唯一数字结果 `346`，从而使唯一的 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 都为 `1.0`。它将 `agent_response.json` 和可解析为 `NetworkTrace` 的 `network.har` 都列为决定性 artifacts；task type、status、结果值或基数不匹配，以及响应或 trace 的解析、规范化或评估编排错误均被写为 failure。它把缺少可读 `agent_response.json` 或 `network.har` 且没有完整官方 `TaskEvalResult` 的情况写为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_semantics_overreach`
- 为什么修改：native 规则将所保留 `network.har` 的可解析性视为额外的语义前提，尽管唯一已配置的 evaluator 比较 agent response，且 packet 并未确立依赖 trace 的 response 比较。
- 应如何修改：从 native success、failure 和 undecided 条件中移除对所保留 `network.har` 的存在性或可解析性的要求，同时保留通过对完整 response 证据应用已配置 response evaluator 而产生的 failure。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_decisive_artifact`
- 为什么修改：`network.har` 被列为决定性证据，仅仅是因为它位于 packet 的批处理 artifact 列表中，而非因为本案例具有 `NetworkEventEvaluator` 或依赖 trace 的 response 比较。
- 应如何修改：仅保留完整的 `agent_response.json`，将其作为最小的 native 决定性 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`network_dependent_decision_rules`
- 为什么修改：这些规则过度声称 `network.har` 必须可评估才能判定 success，并声称其保留失败会使 native 结果无法判定。
- 应如何修改：将 success 和普通 failure 建立在对完整 agent response 的已发布评估之上，并将 undecided 限制为影响该 response 证据的丢失、损坏或来源验证失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`unnecessary_trace_material`
- 为什么修改：对于唯一已配置的 response 检查，额外的 trace artifact 及其重复的决策规则条件使检查清单不够精简。
- 应如何修改：从 native 决策规则中删除 trace artifact 条目和所有 trace 特有条款。

## Case 79

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：统计全部评论中状态为 `Not Approved` 的评论总数。任务要求报告这一数值。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，检查响应经解析和规范化后，显式配置的 `task_type`、`status`、`retrieved_data` 是否分别匹配 `RETRIEVE`、`SUCCESS` 和无序精确单元素数组 `[0]`，其中元素须为数字；标量 retrieved data 会包装为单元素数组，缺失或空数据规范化为 null 并失败，`task_type` 缺失时可用 `performed_operation` 别名。物化配置中的 `error_details: null` 及其他未配置原始字段不参与比较，且不得发生 evaluator error；未配置 `NetworkEventEvaluator`，因此 `network.har` 不影响该数值响应比较。由于只有这一个 evaluator，只有其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 在规范化结构匹配 `RETRIEVE`、`SUCCESS` 和无序精确单元素数字 `0`、且无 evaluation error 时得 `1.0`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将 HAR 可解析、evaluation context 有效且无 orchestration error 写入 success 条件；相应地，它把响应无效或不匹配、HAR 缺失或无效、evaluator/orchestration error 或 evaluator 非 `1.0` 判为 failure。其 undecided 条件是未保留实际提交的响应或 HAR 且没有官方 `TaskEvalResult`，并强调已知在评估时缺失或无效应算 failure；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`official-semantics-har-and-response-details`
- 为什么修改：原生语义加入了 HAR 有效性要求，尽管唯一配置的 evaluator 检查的是 agent response，而若干与评分相关的 response 解析和 normalization 行为仍不明确。
- 应如何修改：从原生评分中移除 HAR 有效性，并说明稀疏配置字段、`performed_operation` alias、对包括 `error_details` 在内的未配置 key 的处理、数值 singleton normalization、无序精确比较以及错误行为。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal-network-artifact`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性 artifact。
- 应如何修改：仅保留完整的 `agent_response.json` 作为决定性的原生 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har-based-decision-rules`
- 为什么修改：success 和 failure 规则将所保留 HAR 的可解析性纳入原生决策。
- 应如何修改：原生 success 和 failure 应基于对完整 response 的已发布 evaluation；仅在该 response 证据丢失、损坏或 provenance 失效时判定为 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-redundant-har-conditions`
- 为什么修改：不必要的 HAR artifact 及其重复规则使该 checklist 无法成为对此 case 的紧凑、最小化表述。
- 应如何修改：删除 HAR artifact 以及 HAR 特定的 success、failure 和 undecided 表述，同时保留 response evaluator predicate 和 composition rule。

## Case 80

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，先从 Carnegie Mellon University 步行到 Starbucks on Craig Street，再驾车到 Pittsburgh International Airport，求总时长。答案须仅以 `HH:MM:SS` 字符串返回，不得附加说明。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：它从直接映射、受支持的 JSON 文本或代码块中提取响应，在 `task_type` 缺失时接受 `performed_operation` 别名，并检查显式配置字段规范化后为 `task_type: RETRIEVE`、`status: SUCCESS`，以及在 array-of-duration schema 下无序精确匹配单元素 duration `38min`。物化默认值 `error_details: null` 不参与比较；该 evaluator 不检查 OSRM 来源、两段路线或原始答案是否字面等于 `00:38:00`，且没有 `NetworkEventEvaluator` 或 last-event 语义。只有这个 evaluator 得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`；不匹配或 evaluator/orchestration error 导致非 `1.0` 和任务分 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求响应规范化为 `RETRIEVE`、`SUCCESS` 和无序单元素 duration `38min`，唯一 `AgentResponseEvaluator` 得 `1.0`，进而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将响应及 HAR 可解析、evaluation 无错误写为 success；null/非 mapping、字段缺失或不匹配、额外 duration、输入无法解析或 evaluator/orchestration error 被写为 failure。undecided 指保留包既缺少可读 run inputs 又没有官方 evaluation result，但已知缺失、null、畸形或不可解析的 evaluator input 算 failure。它还给出两个非空 stronger conditions：`exact_hh_mm_ss_format` 要求 raw `retrieved_data` 恰为 [`00:38:00`] 且无额外说明，`osrm_two_leg_route_evidence` 要求 `network.har` 证明两段 OSRM 步行/驾车路线及其时长之和。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_native_har`
- 为什么修改：对于唯一配置的 evaluator 读取 `agent_response_raw` 的 case，`network.har` 被错误地指定为原生决定性证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并根据完整的 `agent_response.json` 重建原生评分。它可以继续作为 OSRM 更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_native_rules`
- 为什么修改：原生规则要求解析 HAR，而且即使所保留 HAR 的缺失对于已配置的 response 比较并非必要，也可能因此判定为 undecided。
- 应如何修改：移除 HAR 特定的原生 success 和 failure predicate，并将 undecided 限定为重建所需的完整 agent response 丢失、损坏或 provenance 无法确定。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：原生 checklist 在 `checked_by`、artifacts、success、failure 和 undecided 规则中重复了一个未配置的 trace 依赖项。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator`、其显式配置的字段、duration normalization、无序比较以及 task-level composition，对原生 section 进行精简。

## Case 81

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，先从 Univ of Pittsburgh 步行到 starbucks on Craig Street，再驾车到 Pittsburgh International Airport，计算总时长。返回内容须仅为 `HH:MM:SS` 格式字符串，不得附加细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应执行受支持的 fenced-code/JSON 提取和规范化，检查显式配置的 `task_type`、`status`、`retrieved_data` 是否分别为 `RETRIEVE`、`SUCCESS` 和在 duration-array schema 下无序精确匹配单元素 `49min`；`task_type` 缺失时接受旧字段 `performed_operation`。`ordered` 默认为 `false`，物化的 `error_details: null` 和其他未配置 raw keys 不比较；配置未验证 OSRM、路线方式、字面 `00:49:00`，也没有网络或 last-event evaluator。该 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`；任何 evaluator-visible mismatch、额外或缺失项、evaluator/orchestration error 都使任务分为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是唯一 `AgentResponseEvaluator` 将响应解析、规范化为 `RETRIEVE`、`SUCCESS` 和单个 duration `49min` 后得 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都视为决定性 artifacts，把所有输入可解析且无 evaluator/orchestration error 写入 success，并把非对象响应、task type/status 错误、duration 缺失/额外/不匹配及解析或评估错误列为 failure。其 undecided 是没有保存可读的实际响应或权威评估结果，而已知响应缺失、畸形、evaluator error 或分数 `0.0` 属于 failure。非空 stronger conditions 包括 `exact_hh_mm_ss_value`，要求唯一答案严格为 `00:49:00` 且无额外文本或项目；以及 `osrm_route_evidence`，要求 `network.har` 证明按顺序完成指定步行、驾车 OSRM 路段且时长支持总数。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_minimal`
- 为什么修改：对于唯一配置的 evaluator 读取 `agent_response_raw` 的 case，`network.har` 被错误地要求作为决定性原生证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并仅将其保留在更强的 OSRM-route 条件下。将完整的 `agent_response.json` 作为最小原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_requirement_breaks_decision_partition`
- 为什么修改：`success_if` 要求解析不必要的 trace，而 `undecided_if` 未能一致地处理这一所谓决定性证据的丢失。
- 应如何修改：原生 success 和 failure 应基于对完整 response 的已发布 evaluation。仅在 response 证据缺失、被截断、损坏或 provenance 不确定时判定为 undecided；明确将完整但格式错误或为 null 的 response 保留为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：额外的原生 trace artifact 以及由此导致的 decision-rule 歧义违反了紧凑性和内部一致性。
- 应如何修改：仅使用一个原生决定性 artifact，即 `agent_response.json`，并将所有基于 trace 的检查完全移至更强条件。

## Case 83

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，先从 Carnegie Mellon University 步行到 apple store shadyside，再驾车到 starbucks on craig street，并计算总时长。答案必须仅为 `HH:MM:SS` 格式字符串，不得带额外说明。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应经允许的 JSON/代码块解析和规范化后，三个显式字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，以及在 duration schema 下无序精确匹配单元素 `retrieved_data: ["22min"]`；缺少 `task_type` 时接受 `performed_operation`。物化配置独有的 `error_details: null` 不比较，完整响应若为 null、空对象、仍非对象、缺少 task type/alias 或 status，或 retrieved data 缺失、为空、不可规范化、额外或不匹配，均失败；没有网络或 last-event 检查。唯一 evaluator 得 `1.0` 时 `TaskEvalResult.score` 为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求提交响应规范化为 `RETRIEVE`、`SUCCESS` 和恰好一个等于 `22min` 的 duration，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult.score` 得 `1.0`；它仅把 `agent_response.json` 列为决定性 artifact。success 是该响应无解析、规范化、比较或 evaluator error；failure 包括 null、解析后非对象、规范化失败、task type/status 错误，以及 retrieved_data 缺失、为空、不可规范化、额外或不匹配。undecided 是提交的 `agent_response.json` 未保留，或已知在提交后被截断或改变；保留下来的 null 或无效响应则属 failure。非空 stronger conditions 为 `literal_hhmmss_output`，要求唯一 retrieved value 字面等于 `00:22:00` 且无解释文本；以及 `osrm_leg_and_mode_evidence`，要求 `network.har` 证明指定 OSRM 步行和驾车路段，并由 `agent_response.json` 证明报告值等于两段时长之和。

### 需要修改的部分

#### 修改项 1：native.success_if / fail_if / undecided_if

- Finding ID：`decision_rules_missing_required_fields`
- 为什么修改：`native.fail_if` 遗漏了以下完整保留的 response：既缺少 `task_type` 也缺少其可接受的 `performed_operation` alias，或者缺少 `status`。空对象也会被转换为类似 null 的 actual input。这些是普通的原生 failure，而不是 normalization error 或 undecided case。
- 应如何修改：扩展 `fail_if`，将空对象、缺少 `task_type`/`performed_operation`、缺少 `status`，以及无法 normalization 为 `RETRIEVE`/`SUCCESS` 的值归类为原生 failure。

## Case 84

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查询从 DoubleTree by Hilton New York Downtown 驾车到 Keens Steakhouse 的预计时长。返回值须仅为 `HH:MM:SS` 格式字符串，不得附加说明。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查响应经提取和解析后为 dict-like，并将显式配置字段规范化为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 在 array-of-duration schema 和无序比较下精确等于单元素 `14min`。稀疏 expected 中没有 `error_details`，所以物化的 `error_details: null` 及其他未配置 raw keys 不参与比较；配置也不验证 OSRM 来源、字面 `00:14:00`，没有 NetworkEventEvaluator 或 last-event 语义。该唯一 evaluator 无 assertion、无 error 且得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`；否则任务分为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是最终响应结构匹配 `RETRIEVE`/`SUCCESS`，规范化 `retrieved_data` 在无序比较下等于单元素 duration `14min`，使唯一 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将响应和 trace 可重建、评估无 evaluator/orchestration error、字段及 duration 无缺失或额外项写入 success；任何结构或值 assertion、输入或评估错误、或 evaluator 非 `1.0` 被列为 failure。undecided 是无法确定实际评估的响应或所需 trace，例如任一缺失或存储损坏，且没有相关官方 `TaskEvalResult`。非空 stronger conditions 为 `exact_hh_mm_ss_answer`，要求答案 payload 仅含字面字符串 `00:14:00`；以及 `osrm_route_provenance`，要求 `network.har` 中存在从指定酒店到 Keens Steakhouse 的成功 OSRM 驾车路线，其结果支持报告的 14 分钟估计。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_native_trace`
- 为什么修改：`network.har` 被表述为必要的原生证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且其配置的 duration 比较使用最终 response。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分原生 artifact。该 trace 只能保留在 OSRM 更强条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_trace_from_native_decisions`
- 为什么修改：`success_if` 要求存在所保留的 trace，而 `undecided_if` 将 trace 丢失视为妨碍重建的证据丢失，这削弱了原本可仅凭 response 重建的决策。
- 应如何修改：原生 success、failure 和 undecided 决策应基于完整的已 evaluation response。保留将实际 evaluator 或 orchestration error 判定为 failure 的规则，但不要因所保留的 trace 缺失或损坏而将原生结果判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_native_artifact_scope`
- 为什么修改：冗余的原生 trace 问题及其依赖规则使 checklist 比必要的更庞大，case 针对性也更弱。
- 应如何修改：删除原生 trace artifact 及相关的 trace 保留条款，同时仅将 `network.har` 保留为显式的更强 OSRM-provenance 条件的证据。

## Case 86

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：从机场附近的 La Quinta Inn 驾车前往 Upitt，使用 OSRM direction service 获取预计时长。回答必须仅为 `HH:MM:SS` 格式的字符串，不得附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它解析 `agent_response.json`，并比较稀疏配置明确指定的 `task_type`、`status`、`retrieved_data`：前两者须为 `RETRIEVE`、`SUCCESS`，后者按 `results_schema` 的 duration 字符串数组规则归一化后须恰为单元素 `29min`。`ordered:false` 表示忽略数组顺序；物化配置补出的 `error_details:null` 不参与比较，也没有网络事件、filter 或 last-event 检查。唯一 evaluator 必须得到 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是无解析或评估错误，且唯一 `AgentResponseEvaluator` 在 duration 归一化后匹配 `RETRIEVE`、`SUCCESS` 和单元素 `29min`，从而 evaluator 与任务分数均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 要求这些 artifacts 可用于完成评估，failure 包括响应结构或取值不匹配、额外项目以及 artifact、上下文、evaluator 或编排错误，undecided 则用于留存记录不完整或损坏而无法确定实际响应与 trace 的情形。非空 stronger conditions 有两项：`literal_hhmmss_answer` 要求答案严格为 `00:29:00` 且无额外文本或项目；`osrm_route_evidence` 要求 `network.har` 显示指定路线的成功 OSRM 请求，并由 `agent_response.json` 证明报告时长与其一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_native_network_trace`
- 为什么修改：`network.har` 被错误地列为决定性原生 artifact，尽管此 case 仅配置了 `AgentResponseEvaluator`，且没有 network-event predicate。
- 应如何修改：从原生决定性 artifacts 中移除 `network.har`。仅将其保留用于更强的 OSRM-use 条件，在该条件下其内容确实相关。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_affects_native_decision`
- 为什么修改：原生规则将 trace 可用性纳入 success，并允许 trace 保留丢失导致 undecided，尽管已配置的检查可根据完整的 agent response 重建。
- 应如何修改：原生 success、failure 和 undecided 规则应基于完整且精确的 `agent_response.json`；将 undecided 限定为该 response 的保留、完整性或 provenance 丢失。完整但无效、为 null、不匹配或出现 evaluator error 的 response 应继续判定为 failure。

## Case 87

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：从 red roof inn 驾车前往 Pittsburgh science museum，使用 OSRM direction service 获取预计时长。回答必须仅为 `HH:MM:SS` 格式的字符串，不得附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；响应须解析为 mapping，归一化任务类型取自 `task_type`，该字段缺失时可回退到 legacy 字段 `performed_operation`，并须匹配 `RETRIEVE`，`status` 须匹配 `SUCCESS`。`retrieved_data` 按 duration 数组 schema 归一化，标量会被转为单元素序列，随后以 `ordered:false` 精确匹配单元素 `20min`；其他原始键及物化默认值 `error_details:null` 不比较，也无网络事件、filter 或 last-event 检查。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 经解析和 duration 归一化后匹配 `RETRIEVE`、`SUCCESS` 及无序单元素 `20min`，使 evaluator 与 `TaskEvalResult` 均为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；success 要求结构化响应满足上述比较，failure 包括 null、畸形、非对象、缺失或不匹配的 `task_type`/`status`、缺失或额外的 retrieved data 以及 evaluator 或任务错误，undecided 用于实际送评响应未留存或无法关联到该 run 且无官方结果的情形。非空 stronger conditions 为 `literal_hh_mm_ss_format`，要求唯一项目严格为 `00:20:00` 且无附加文本；以及 `osrm_use`，要求 `network.har` 显示从 Red Roof Inn 到 Pittsburgh Science Museum 的成功 OSRM directions 请求。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias_omitted`
- 为什么修改：原生语义未说明在 canonical field 缺失时接受 `performed_operation` 作为 `task_type` 的来源，而 failure 规则却将缺少 `task_type` 直接判定为 failure。
- 应如何修改：说明 task-type 比较使用 `task_type`；当其缺失时，使用已发布的 `performed_operation` legacy alias；不要仅因使用该 alias 就将其他方面均匹配的 response 判定为 failure。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`alias_incorrectly_classified_as_failure`
- 为什么修改：`success_if` 要求存在 `task_type`，却未说明可接受的 alias，而 `fail_if` 则规定缺少 `task_type` 即为 failure。这些规则可能会将使用 `performed_operation` 的官方 1.0 response 判定为 failure。
- 应如何修改：修订 `success_if` 和 `fail_if`，使 normalization 后的 task type 可以来自 `task_type`，或者在 `task_type` 缺失时来自 `performed_operation`。

## Case 89

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：取得与 Connecticut 接壤的每个美国州的 relation ID。回答必须仅返回整数列表，不得附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它对稀疏配置明确指定的 `task_type`、`status`、`retrieved_data` 做提取和归一化，要求前两者为 `RETRIEVE`、`SUCCESS`，后者按 number 数组 schema 精确匹配 `392915`、`61315`、`175905`。`ordered:false` 表示忽略顺序，但不允许缺失、额外、重复计数或不等值；物化默认值 `error_details:null` 不参与评分，也没有网络事件、filter 或 last-event 语义。唯一 `AgentResponseEvaluator` 必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 经官方解析和归一化后匹配 `RETRIEVE`、`SUCCESS` 以及无序且无缺漏的 `392915`、`61315`、`175905`，从而任务分数为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；success 还要求响应和 HAR 能构造评估上下文，failure 包括裸列表、畸形或字段不匹配、数值缺失/额外/重复/无效以及不可用 trace 或处理错误，undecided 用于任一 artifact 缺失或截断且无留存评估结果的情形。非空 stronger condition `literal_integer_list_without_extra_details` 要求原始响应是未包装的 protocol object，`retrieved_data` 为 JSON 整数数组，不含 prose，字段不得超出 `task_type`、`status`、`retrieved_data` 和可选的 null `error_details`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_har_as_decisive`
- 为什么修改：`network.har` 被列为决定性证据，尽管没有已配置的 evaluator 检查 network event，且数值 response 比较不依赖 trace 内容。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_driven_native_decisions`
- 为什么修改：decision rules 将 success、failure 和 undecidability 取决于 HAR 是否存在或能否处理，导致所保留 HAR 的缺失不必要地阻碍重建。
- 应如何修改：移除依赖 HAR 的 success、failure 和 undecided 条款。当没有所保留的 evaluator result 可确定结果时，将 undecided 限定为实际 agent response 丢失、损坏、截断或 provenance 不确定。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：未起作用的 HAR artifact 及其相关规则为原本仅依赖 response 的 checklist 增加了非决定性内容。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator`、其显式配置的字段、精确无序数值比较以及完整的 agent response artifact，对原生主体进行精简。

## Case 90

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：取得与 Pennsylvania 接壤的每个美国州的 relation ID。回答必须仅返回整数列表，不得附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它可解析原始或 fenced JSON 文本，只归一化并比较稀疏配置明确指定的 `task_type`、`status`、`retrieved_data`。前两者须为 `RETRIEVE`、`SUCCESS`，后者按 number 数组 schema 和 `ordered:false` 精确匹配无序多重集 `[162061, 162112, 175905, 224951, 162110, 162068]`；物化默认值 `error_details:null` 不比较，也没有网络事件、filter 或 last-event 检查。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`SUCCESS` 和无序精确多重集 `[162061, 162112, 175905, 224951, 162110, 162068]`，无 assertion 或 evaluator/编排错误时得到 `TaskEvalResult.score 1.0`。它把 `agent_response.json` 和 `network.har` 都视为决定性 artifacts；failure 包括不可解析或非对象响应、字段或数组不匹配、trace/上下文/编排错误，undecided 用于留存损坏而无法确定实际响应或 trace 的情形。非空 stronger conditions 包括 `raw_integer_elements`，要求六个原始元素均为 JSON integer；以及 `no_additional_details`，要求原始最终响应没有说明文字、code fence 或 benchmark response protocol 之外的字段。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，仅用于建立 trace parsing/context construction，尽管并未配置 `NetworkEventEvaluator`，且 trace 内容不会影响此 case 的数值 `AgentResponseEvaluator` 比较。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并将完整且保留 provenance 的 `agent_response.json` 作为唯一决定性的 post-run artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_misclassified_as_undecided`
- 为什么修改：undecided 规则将无法确定所提供 trace 的情况视为阻碍重建的证据丢失，尽管该 trace 对已配置的 response 检查不具决定性。
- 应如何修改：将 undecided 限定为影响完整已提交 response 的丢失、损坏、完整性失效或 provenance 丢失；保留将完整但无效或不匹配的 response 判定为 failure 的规则。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_semantics`
- 为什么修改：尽管 trace 特定的前提对于重建唯一配置的检查并非必要，但它们仍在原生规则中反复出现。
- 应如何修改：用紧凑的仅依赖 response 的证据表述替换依赖 trace 的 artifact 和规则，同时保留精确的 evaluator 比较和 task-level composition 语义。

## Case 91

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：取得与 Massachusetts 接壤的每个美国州的 relation ID。回答必须仅返回整数列表，不得附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它可解析 dict、JSON 或 code fence 中的 JSON，并比较稀疏配置明确指定的 `task_type`、`status`、`retrieved_data`，其中 `task_type` 缺失时接受 legacy 字段 `performed_operation` 作为回退。任务类型和状态须为 `RETRIEVE`、`SUCCESS`，retrieved data 按 number 数组 schema 及 `ordered:false` 精确匹配无序多重集 `[392915, 165794, 175905, 67213, 60759]`；物化默认值 `error_details:null` 不比较，也无网络事件、filter 或 last-event 语义。唯一 evaluator 必须得到 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`SUCCESS` 和无序精确的五个 relation IDs `[392915, 165794, 175905, 67213, 60759]`，使 evaluator 与 `TaskEvalResult` 均为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；failure 包括不可解析或非对象响应、缺失或错误的 `task_type`/`status`、缺失或空的 retrieved data、ID 缺失/额外/重复以及 evaluator 错误，undecided 用于最终响应未留存、截断或损坏的情形。非空 stronger condition `no_additional_details` 要求最终响应除 benchmark response envelope 和所需五整数 `retrieved_data` 列表外，不含解释、code fence 或无关内容。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：`native.fail_if[0]` 规定缺少 `task_type` 属于 evaluator failure，但已发布的 normalization 会在 `task_type` 缺失时使用 `performed_operation` 作为可接受的 fallback。
- 应如何修改：限定该规则：仅当 `task_type` 和 `performed_operation` 均缺失，或所选 task-type 值无法 normalization/匹配 `RETRIEVE` 时才判定为 failure；并在 evaluator semantics 中说明该 fallback。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：ordinary-failure 示例错误地将所有缺少字面 `task_type` key 的 response 都归类为 failure，降低了原生 decision boundary 的准确性。
- 应如何修改：修订 `success_if` 和 `fail_if`，仅在 `task_type` 缺失时将 `performed_operation` 识别为 fallback，同时继续将两个名称均缺失、不匹配、无效 response 和 evaluator error 判定为 failure。

## Case 92

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：取得与 Vermont 接壤的每个美国州的 relation ID。输出必须仅为整数列表，不得附加任何说明。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`；它对最终响应进行提取和规范化，并检查稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和 `[175905,67213,61315]`。`retrieved_data` 按元素类型为 `number` 的数组 schema 规范化，`ordered:false` 表示忽略顺序但仍要求元素完全一致且对重复项敏感；`performed_operation` 可在缺少 `task_type` 时作为旧别名，物化产生的 `error_details:null` 不参与比较。没有配置 `NetworkEventEvaluator`，因此没有 network filter 或 last-event 判定；`TaskEvalResult.score` 仅在该唯一 evaluator 的分数等于 `1.0` 且无 evaluator 或 task-level error 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为 `TaskEvalResult.score` 等于 `1.0`，即唯一的 `AgentResponseEvaluator` 在规范化响应匹配 `RETRIEVE`、`SUCCESS` 及无序数值数组 `[175905, 67213, 61315]` 后得分 `1.0`，且没有 task-level evaluation error。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，前者用于核对最终响应，后者用于确认作为 `NetworkTrace` 的 HAR 完整可解析。其 success 条件要求响应和 HAR 构成有效评估上下文、字段规范化匹配且不存在错误；failure 条件涵盖响应或 HAR 无法读取、响应非 mapping、字段不匹配、数值数组存在错误、缺失、重复或额外项以及 evaluator/task error。它将无法重建 `agent_response.json` 或 `network.har` 且无官方结果可裁决的情况列为 undecided。非空 stronger condition `literal_integer_list_format` 进一步要求原始最终响应没有说明文字、代码围栏或额外字段，并且 `retrieved_data` 中每项都是 JSON integer primitive。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_har_artifact`
- 为什么修改：尽管此案例只有一个比较数值响应值的 AgentResponseEvaluator，但 network.har 仅通过通用 evaluator 管道和批量保留契约就被指定为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json 作为已配置检查所需的最小充分保留证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decision_rules`
- 为什么修改：原生规则要求 HAR 可解析，并允许因 HAR 保留丢失而将结果判定为 undecided，这使证据要求超出了唯一已配置的响应比较。
- 应如何修改：移除依赖 HAR 的 success、failure 和 undecided 条款。将 undecided 限定为完整响应证据丢失或损坏，同时明确将已保留且完整但无效、为 null 或不匹配的响应视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_native_material`
- 为什么修改：HAR artifact 及其重复条件为原本紧凑的检查清单增加了非决定性材料。
- 应如何修改：围绕 agent_response.json 整合原生证据和规则，同时保留 AgentResponseEvaluator 的确切语义以及任务级 all-evaluators 组合。

## Case 94

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得发票 `000000001` 的 grand total。输出必须仅为数字值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查最终响应中明确配置的 `task_type`、`status` 和 `retrieved_data`，期望为 `RETRIEVE`、`SUCCESS` 和 `[36.39]`。响应可直接是 mapping，也可从字符串中提取并 JSON 解码；`performed_operation` 可作为 `task_type` 的旧别名，`retrieved_data` 按元素为 `number`、格式为 `currency` 的数组 schema 规范化，并以 `ordered:false` 做精确的无序单元素比较。未明确配置的原始字段以及物化默认值 `error_details:null` 不比较；也没有 network filter 或 last-event evaluator。只有该 evaluator 无错误且得分 `1.0` 时，要求所有 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得分 `1.0`，即解析和规范化后的 mapping 匹配 `task_type RETRIEVE`、`status SUCCESS` 以及无序单元素 currency 值 `36.39`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，分别用于结构比较以及确认 HAR 能作为 `NetworkTrace` 加载并避免评估上下文错误。其 success 条件要求响应精确匹配且评估上下文无错误；failure 条件包括响应非 mapping、无法规范化、结构或值不符、HAR/上下文无效、evaluator 或 orchestration error，以及唯一 evaluator 低于 `1.0`。它把实际最终响应或所需 HAR 未保留且无 `TaskEvalResult` 可裁决列为 undecided。非空 stronger condition `number_only_no_extra_details` 额外要求原始响应无说明文字、代码围栏或辅助详情字段，除必要协议元数据外唯一实质 payload 为数值 `36.39`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：尽管唯一已配置的检查是 AgentResponseEvaluator，且没有任何由数据包表示的规则会使 trace 内容影响其响应比较，但 network.har 仍被列为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json 作为已配置检查所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：尽管仅基于响应的 evaluator 可根据完整的最终响应重建，但这些规则仍将 HAR/context 解析作为 success 和 failure 的组成部分，并将 HAR 缺失作为 undecided 的理由。
- 应如何修改：移除依赖 HAR 的 success、failure 和 undecided 条款。将 undecided 限定为 agent_response.json 的丢失、损坏、截断或来源验证失败；继续将完整但无效或为 null 的响应、不匹配以及 evaluator 错误视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：重复的 HAR 和 evaluation-context 分支为原本仅基于响应的检查清单增加了非决定性的案例机制。
- 应如何修改：围绕唯一的 AgentResponseEvaluator 及其完整响应 artifact 精简原生部分，同时保留已配置的解析、normalization、比较和任务分数语义。

## Case 95

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得发票 `000000002` 的 grand total。输出必须仅为数字值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

配置中只有 `AgentResponseEvaluator`，它解析最终响应并比较稀疏配置明确给出的 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和 `[39.64]`。`retrieved_data` 使用元素类型 `number`、格式 `currency` 的数组 schema 规范化，并按 `ordered:false` 与精确的无序单元素集合比较；物化默认字段 `error_details:null` 不参与比较。没有配置网络事件、filter 或 last-event 语义。`TaskEvalResult.create` 要求所有 evaluator 分数均为 `1.0`；本 case 只有一个 evaluator，因此它无错误且得分 `1.0` 才能得到 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原始 draft 声明 task 95 的 benchmark success 当且仅当所有 evaluator 均得 `1.0`；由于只有 `AgentResponseEvaluator`，响应须规范化为 `RETRIEVE`、`SUCCESS` 和无序单元素 currency 数组 `[39.64]`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 均视为决定性 artifacts，分别询问响应比较是否无失败，以及 trace 是否可解析并允许上下文无错误地建立。success 条件要求字段和值精确匹配并且评估无错误；failure 条件包括响应 malformed、非 object、字段缺失或错误、数据不是精确的 `[39.64]`，以及输入、evaluator 或 orchestration error。undecided 被定义为无法确定实际响应和可解析 trace、且没有保留的 `TaskEvalResult` 可裁决。非空 stronger condition `enforce_number_only_presentation` 要求原始输出仅含数值类型的 `39.64` 这一 retrieved datum，且 benchmark 所需字段之外没有解释内容。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_artifact`
- 为什么修改：尽管案例 95 只有一个 AgentResponseEvaluator，且 trace 不影响其已配置的响应比较，但 network.har 仍被呈现为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并保留完整的 agent_response.json，作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_undecided_rule`
- 为什么修改：尽管重建唯一已配置的 evaluator 检查并不需要保留 trace，但 undecided 规则仍将无法确认存在可解析的已保留 trace 视为证据缺口。
- 应如何修改：将 undecided_if 限定为影响完整 agent response 的丢失、截断、完整性失败或来源验证失败，除非等效的已保留 evaluator 结果能够确定结果。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_clauses`
- 为什么修改：额外的 network artifact 和依赖 trace 的判定措辞使检查清单比此案例的决定性语义所要求的更庞大、更严格。
- 应如何修改：删除 network.har artifact 和 trace 保留相关内容，同时保留将响应不匹配和产生分数的 evaluator 错误视为原生 failure 的规则。

## Case 96

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：查询用户最新订单的状态及预计到达日期。输出须仅为包含键 `"status"` 和 `"arrival_date"` 的对象列表；日期采用 `YYYY-MM-DD`，不可用时为 `null`，且不得附加其他说明。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 从直接对象或可解析文本（包括 fenced JSON）提取响应，允许 `performed_operation` 作为旧版 `task_type` 别名，并只规范化稀疏配置中的 `task_type`、`status`、`retrieved_data`。期望值为 `RETRIEVE`、`SUCCESS` 和 `[{"arrival_date":null,"status":"canceled"}]`；数组按 `ordered:false` 做无序但精确的结构比较，缺少或增加数组元素、对象键都会失败，而未配置的顶层字段及物化默认 `error_details:null` 不比较。这里没有 network filter 或 last-event evaluator。唯一 evaluator 必须无错误且得分 `1.0`，所有 evaluator 均为 `1.0` 的组合规则才令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`：唯一的 `AgentResponseEvaluator` 解析并规范化响应后，须匹配 `task_type RETRIEVE`、`status SUCCESS` 及无序数组 `[{"status":"canceled","arrival_date":null}]`。它将 `agent_response.json` 和 `network.har` 都列作决定性 artifacts，后者用于确认 trace 可进入评估上下文并在需要时提供 shopping base URL。success 条件要求响应精确匹配且评估无错误；failure 条件涵盖响应为 null、malformed 或非 object、字段或结构不符、额外或缺失对象键/数组元素、trace 或上下文错误以及 evaluator 非 `1.0`。它将 agent response 或 required trace 缺失、截断或不可读且没有官方 `TaskEvalResult` 的情况列为 undecided。非空 stronger condition `no_additional_details` 进一步要求除 benchmark response envelope 外，原始提交只含请求的列表，没有周边说明或无关字段。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：尽管唯一已配置的 evaluator 是 AgentResponseEvaluator，且预期检索数据不包含任何其比较依赖于从 trace 派生的环境映射的 URL，但 network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为重建此案例已配置检查的唯一原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_undecided`
- 为什么修改：检查清单允许在非决定性的必需 trace 缺失、被截断或不可读时将结果判定为 undecided。
- 应如何修改：将 undecided_if 限定为影响完整 agent response 的保留、完整性或来源丢失；完整但无效的响应或 evaluator 可见的不匹配必须继续判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nondecisive_trace_branches`
- 为什么修改：尽管此案例只有一个响应 evaluator，但原生检查清单仍包含不必要的 HAR fallback 和 trace 保留分支。
- 应如何修改：删除 network artifact 和 trace 特定的判定措辞，仅保留响应比较、evaluator 组合和响应证据完整性规则。

## Case 98

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service 找出距 University of Pittsburgh 最近的 tea cafe，并给出步行距离。输出须仅为含 `"location"` 和 `"distance"` 的对象列表，距离为带 `km` 或 `m` 单位的数值字符串，例如 `2.4km` 或 `500m`，不得附加其他说明。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对最终响应进行提取和 schema normalization，只比较明确配置的 `task_type`、`status` 和 `retrieved_data`；期望为 `RETRIEVE`、`SUCCESS`，以及一个 Fuku Tea 结果：`distance` 为 `"653m"`，地址字段为 `name:"Fuku Tea"`、`house_number:"3716"`、`street:"Forbes Avenue"`、`city:"Pittsburgh"`、`state:"Pennsylvania"`、`postcode:"15213"`。`distance` 使用 `format:"distance"`，`retrieved_data` 以 `ordered:false` 做无序精确结构比较，距离规范化后等价于 `653m`；物化的 `error_details:null` 不比较。没有配置 `NetworkEventEvaluator`，所以原生计分没有 network filter 或 last-event 语义，也不验证 OSRM 请求来源。只有该 evaluator 无错误且得分 `1.0` 时，`TaskEvalResult.score` 才按“所有 evaluator 分数均为 `1.0`”的规则成为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native benchmark success 为 `TaskEvalResult.score = 1.0`：唯一的 `AgentResponseEvaluator` 在解析和 schema-normalizing 后，须无序匹配 `RETRIEVE`、`SUCCESS` 以及地址完整、距离为 `653m` 的单个 Fuku Tea 结果。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于确认 trace 可解析，并在环境 URL 需要时支持 map base URL 恢复。success 条件要求响应精确匹配且 trace/context/evaluation 无错误；failure 条件包括响应解析或规范化失败、任一字段、键结构或数组成员不符，以及 trace、配置、evaluator 或 orchestration error。undecided 被描述为缺少或截断重建响应比较或确认评估完成所需的 evaluator 输入，且无保留的 `TaskEvalResult` 可裁决。非空 stronger condition `verify-osrm-walking-provenance` 单独要求 `network.har` 证明存在成功的 University of Pittsburgh–Fuku Tea OSRM walking-directions 请求，且返回距离支持 `653m`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native-network-artifact-not-minimal`
- 为什么修改：对于唯一已配置 evaluator 为 AgentResponseEvaluator 的案例，network.har 被错误地要求作为原生决定性证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har，并仅将其保留为明确更强的 OSRM 来源条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-native-rules`
- 为什么修改：尽管已配置的原生比较仅基于响应，但原生判定规则仍以 trace 解析或基于 trace 的环境恢复为 success、failure 和证据完整性的条件。
- 应如何修改：根据完整的 agent response 和已发布的 AgentResponseEvaluator 语义制定原生 success、failure 和 undecided 规则。将原生 undecided 限定为该响应证据的丢失；不要因缺少 network evidence 而将原生结果判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-redundant-native-trace-branches`
- 为什么修改：额外的原生 trace artifact 以及 trace/config 条款使检查清单在重建此案例已配置检查方面不够精简。
- 应如何修改：删除冗余的原生 trace artifact 和条款，同时保留 evaluator 错误、响应不匹配、确切的预期数据以及 all-evaluators-equal-1.0 组合。

## Case 99

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，找出距 `5700 Penn Ave` 最近的 Five Guys 及步行距离。输出只能是含 `location` 和 `distance` 的对象列表，其中距离为带 `km` 或 `m` 单位的数值。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对响应进行已发布规则下的解析和 schema normalization，并比较显式 expected 字段：`task_type`=`RETRIEVE`、`status`=`SUCCESS`，以及一个 `retrieved_data` 项，其 `distance` 等价于 `4km`，`location` 为 `{name: Five Guys, house_number: 117, street: South Bouquet Street, city: Pittsburgh, state: Pennsylvania, postcode: 15213}`。`retrieved_data` 按 `ordered=false` 做无序递归精确结构比较，数组项由包含 `distance` 和 `full_address` 结构的 schema 规范化；物化出的 `error_details:null` 不是 sparse expected 中显式配置的比较字段。没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义，`network.har` 内容不参与该响应比较；仅当唯一 evaluator 无错误且得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是解析并 schema-normalize 后的 `task_type`、`status` 和无序 `retrieved_data` 分别匹配 `RETRIEVE`、`SUCCESS` 与上述单项结果，且唯一 `AgentResponseEvaluator` 得分 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把响应匹配、trace 可解析、上下文及 evaluator 编排无错误写入 success 条件；响应为空、不可解析或字段/项目不匹配，以及 trace、配置或编排错误被列为 failure。它将实际提交的响应或 trace 未保留、截断或无法归属此 run 列为 undecided，同时说明已保留的 null、无效响应或无效 trace 属于 failure。非空 stronger conditions 有两项：`retrieved_data_is_actual_list` 要求原始 `retrieved_data` 真正是 JSON 对象数组而非经 coercion 接受的单对象或字符串；`osrm_route_evidence` 要求 `network.har` 中存在对应起终点且返回距离支持报告值的成功 OSRM directions 交互。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_decisive`
- 为什么修改：对于仅配置了 AgentResponseEvaluator 的案例，network.har 被错误地指定为原生决定性证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har，并仅为超出原生范围的 OSRM 条件保留它。使用完整的 agent_response.json 作为最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_native_rules`
- 为什么修改：尽管没有配置 NetworkEventEvaluator，但这些规则仍使 trace 的解析或保留影响原生 success、failure 和 undecided。
- 应如何修改：根据完整响应及其已发布的解析、normalization、比较和 evaluator 结果作出原生判定。将 undecided 限定为响应证据的丢失、损坏或来源歧义；不要因省略 network.har 而判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_material`
- 为什么修改：与 trace 相关的原生 artifact 和判定文本增加了大量与案例无关的材料。
- 应如何修改：删除原生 trace artifact，并围绕唯一的 AgentResponseEvaluator 整合原生 success 和 failure，同时仅在更强的 OSRM 条件下保留 network.har。

## Case 100

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，找出距 Carnegie Mellon 最近的 Starbucks 及步行距离。输出只能是含 `location` 和 `distance` 的对象列表，距离须为带 `km` 或 `m` 单位的数值。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 按已发布规则解析响应并进行 schema normalization，比较显式 expected 字段 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，以及单项 `retrieved_data`：`distance`=`557m`，`location` 为 `{name: Starbucks, house_number: 417, street: South Craig Street, city: Pittsburgh, state: Pennsylvania, postcode: 15213}`。它接受适用的字符串或 code-block JSON 解析，`performed_operation` 可作为旧版 `task_type` 名；`retrieved_data` 使用数组对象 schema 规范化，并按 `ordered=false` 无序递归精确比较，未配置的顶层字段和物化默认值 `error_details:null` 不属于显式比较。没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；任务采用全合取，唯一 evaluator 无错误且得分 `1.0` 时 `TaskEvalResult.score` 为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 写为：解析和 schema-normalize 后的响应以无序方式匹配 `RETRIEVE`、`SUCCESS` 及官方单项 `retrieved_data`，唯一 `AgentResponseEvaluator` 无错误并得 `1.0`，所以 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都称为决定性 artifacts；成功要求得到 `417 South Craig Street, Pittsburgh, PA 15213` 的 Starbucks 和等价于 `557m` 的距离，失败包括结构、状态、地点、距离或项目不匹配，以及响应、trace、上下文、evaluator 或编排错误。它把无法确定 evaluator 实际收到的完整响应和 trace、且没有可信完成结果的情形列为 undecided，并把已知提交但缺失或畸形的 artifact 归为 failure。其非空 stronger condition `verify_osrm_route_evidence` 要求 `network.har` 展示 Carnegie Mellon 到所报告 Starbucks 的成功 OSRM 请求/响应，且步行距离与规范化后的 `557m` 一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_native_trace`
- 为什么修改：对于唯一已配置检查为 AgentResponseEvaluator、且预期响应不包含依赖 trace 的 URL 值的案例，network.har 被错误地纳入决定性原生 artifact。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har。仅在单独的更强 OSRM 条件下保留它，因为其内容在那里确实相关。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_undecided`
- 为什么修改：原生 undecided 规则称响应和 trace 的来源都不可或缺，因此丢失非决定性 trace 可能错误地产生 undecided。
- 应如何修改：在不存在等效且可信的已完成 evaluation 结果时，将原生 undecided 状态限定为确切 agent response 或其来源的丢失或损坏。对完整但无效或不匹配的响应继续判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal`
- 为什么修改：尽管已声明不比较 trace events，但原生部分仍包含冗余的 trace artifact 和依赖 trace 的判定措辞。
- 应如何修改：移除冗余的原生 trace 条目以及所有使 network.har 成为必需项的原生保留措辞；仅为明确更强的 OSRM 验证保留该 trace。

## Case 101

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查找距 `Upitts` 最近的 In-N-Out 及其步行距离。要求用 `location` 表示地点名称和位置，用 `distance` 表示步行距离。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 并不期待一个地点结果，而是比较显式 expected：`task_type`=`RETRIEVE`、`status`=`NOT_FOUND_ERROR`、`retrieved_data`=`null`，其 `results_schema` 也是 `{type:"null"}`。它按已发布规则进行字符串或 fenced-JSON 提取、尽可能 JSON 解码及 expected-field normalization，接受 `performed_operation` 作为旧版 `task_type`，并把缺少 `retrieved_data` 键视为 null；只比较 sparse expected 中显式配置的字段，物化的 `error_details:null` 不额外参与比较。没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；唯一 evaluator 无错误且为 `1.0` 时 `TaskEvalResult.score` 为 `1.0`，任何非 `1.0` 或错误均使任务分数为 `0.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是响应解析、规范化后匹配 `RETRIEVE`、`NOT_FOUND_ERROR` 和 null `retrieved_data`，使唯一 `AgentResponseEvaluator` 及 `TaskEvalResult` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；匹配且无 evaluator 错误为 success，响应结构或三个字段不符、HAR/响应处理出错或 evaluator 得分低于 `1.0` 为 failure。它把无法确定实际接受评估的响应或 network trace、例如 artifact 缺失或运行后损坏且无保留结果的情况列为 undecided。非空 stronger condition `fulfill_retrieval_intent` 要求响应实际用 `location` 和 `distance` 报告最近的 In-N-Out，并由 HAR 中的地图及 OSRM 请求/响应证据佐证距离和“最近”选择；其理由是原任务要求地点和距离，而 native evaluator 却期待 `NOT_FOUND_ERROR` 与 null。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_har`
- 为什么修改：对于唯一已配置 evaluator 检查 agent response 的案例，network.har 被错误地指定为原生决定性证据。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json 作为最小充分的原生证据。HAR 可保留在单独的更强条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_distorts_decision_rules`
- 为什么修改：原生 fail_if 和 undecided_if 不当地依赖于 HAR 的处理或保留，尽管丢失该 artifact 并不妨碍重建已配置的响应比较。
- 应如何修改：移除 HAR 特定的原生 failure 和 undecided 条款。将 failure 限定为完整但无效、不匹配或产生 evaluator 错误的响应，并将 undecided 限定为实际接受评估的响应或等效决定性证据的丢失。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_compact`
- 为什么修改：不必要的原生 HAR artifact 及其重复的 failure/integrity 规则使检查清单超出了此案例所需的最小证据范围。
- 应如何修改：围绕唯一的响应 evaluator 精简原生部分，并将任何 OSRM/map trace 佐证完全限制在 stronger.additional_conditions 内。

## Case 108

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得 2023 年 1 月至 5 月（含首尾）每月的 completed orders 数量。输出只能是含 `month`（月份名称）和 `count`（整数）的对象列表，不得附加其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 解析并 schema-normalize 响应，比较显式 expected 字段 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，以及五个 `retrieved_data` 对象：`January=12`、`February=7`、`March=5`、`April=9`、`May=5`。schema 将 `month` 定义为 `format:"month"` 的字符串、`count` 定义为 `number`；比较采用 `ordered=false`，因此外层顺序不重要，但规范化后的对象及项目须无缺失、额外或不匹配，物化的 `error_details:null` 并非 sparse expected 显式比较字段。没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；唯一 evaluator 无错误且得分 `1.0` 才使 `TaskEvalResult.score` 为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声称 success 是响应经解析和 schema normalization 后得到 `RETRIEVE`、`SUCCESS`，并以无序精确方式匹配五个月份对象，唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将响应匹配、trace 与 evaluation context 可用且编排无错误写入 success；null、空、非对象、不可解析、字段或月份项目不匹配，以及 artifact、evaluator 或编排错误被写入 failure。它把一个或多个必需 run artifacts 未保留、且没有官方 `TaskEvalResult` 的情况列为 undecided，并区分了“证据未保留”和明确保留为空或无效。非空 stronger condition `raw_output_format` 要求原始最终响应为无代码围栏或说明文字的 bare JSON，顶层除 `task_type`、`status`、`retrieved_data` 和可选 null `error_details` 外无其他字段，且 `count` 以 JSON 整数序列化。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：对于唯一已配置检查为 AgentResponseEvaluator 的案例，network.har 被错误地指定为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并移除原生规则中对保留或检查它的依赖。将完整的 agent_response.json 保留为最小充分 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：尽管完整响应可以确定每项已配置比较的结果，但 success 和 undecided 规则仍使 trace 的可用性或保留情况具有决定结果的作用。
- 应如何修改：通过将已发布的 AgentResponseEvaluator 语义应用于完整响应来确定 success 和常规 failure。将 undecided 限定为 agent_response.json 或等效的已保留响应发生丢失、损坏、不完整或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal`
- 为什么修改：非决定性的 trace artifact 及其相关规则为证据检查清单增加了可避免的材料。
- 应如何修改：删除 trace artifact 条目，并围绕唯一已配置的响应 evaluator 整合原生规则，且不改变其预期值或比较行为。

## Case 109

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得 2022 年 1 月至 12 月（含首尾）每月的 completed orders 数量。输出只能是对象列表，每个对象使用 `month`（月份名称）和 `count`（整数）键，不得附加其他细节。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析并 schema-normalize 响应，比较 `task_type`=`RETRIEVE`、`status`=`SUCCESS` 和 12 个 expected 对象：`January=11`、`February=16`、`March=14`、`April=7`、`May=8`、`June=13`、`July=9`、`August=8`、`September=10`、`October=4`、`November=5`、`December=10`。`month` 按 `format:"month"` 的字符串、`count` 按 `number` 规范化；`ValueComparator` 对结构进行比较，外层 `retrieved_data` 因 `ordered=false` 而忽略顺序，但项目结构、值和重数须精确匹配，物化的 `error_details:null` 不是 sparse expected 的显式比较字段。没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；`TaskEvalResult.create` 要求所有 evaluator 得分都为 `1.0`，本例即唯一 evaluator 无错误且为 `1.0`，否则 `TaskEvalResult.score` 为 `0.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 描述为响应规范化后的 `task_type`、`status` 和无序 12 对象集合分别匹配 `RETRIEVE`、`SUCCESS` 与配置值，唯一 `AgentResponseEvaluator` 得 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 包括响应为 mapping、12 个月份计数完全匹配且评估无错误，failure 包括非 mapping、状态不符、`retrieved_data` 缺失/null 或在月份、计数、结构、重数及项目上不匹配，以及 evaluator/编排错误。它把 `agent_response.json` 缺失或不可读，或既没有可用 `network.har` 又没有保留的官方 `TaskEvalResult` 写为 undecided；原 draft 的 user goal 虽提到月份名称和整数计数，但未明确说每个对象必须恰用 `month`、`count` 两个键。非空 stronger condition `no_additional_details` 要求原始提交在 JSON 外无解释文字、没有 benchmark response envelope 之外的未请求字段，且 `retrieved_data` 只含 `month`/`count` 对象。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`goal_missing_exact_keys`
- 为什么修改：native.user_goal 未声明输出对象必须恰好使用 month 和 count 这两个 key。
- 应如何修改：修改 native.user_goal，以保留对 month/count key 的确切要求，以及对时间段、整数计数、仅列表和不得包含额外详细信息的要求。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：对于唯一已配置 evaluator 比较 agent response、且 month/count 数据不涉及依赖 trace 的 URL normalization 的案例，network.har 被错误地指定为决定性证据。
- 应如何修改：将完整的 agent_response.json 保留为唯一的原生决定性 artifact，并从原生决定性 artifact 集合中移除 network.har。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：即使保留了完整的原始响应，undecided_if 仍将 network.har 和已保留 TaskEvalResult 同时缺失视为证据不足。
- 应如何修改：将 undecided 限定为妨碍恢复完整已提交 agent response 的丢失、损坏、截断或来源验证失败。声明或保留以下规则：完整但无效或不匹配的响应应判定为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_evidence_requirements`
- 为什么修改：额外的 HAR artifact 和未声明的 TaskEvalResult 替代方案使检查清单不够精简，并与其仅基于响应的 evaluator 配置存在内部不一致。
- 应如何修改：移除 HAR artifact 和 TaskEvalResult 保留替代方案，仅留下紧凑的基于响应的重建规则。

## Case 110

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得 2022 年 1 月至 11 月（含首尾）每月已完成订单数。回答只能是由对象组成的列表，每个对象仅含 `month`（月份名）和 `count`（整数），不得附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它要求响应中显式配置的字段归一化为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 在数组对象 schema（`month` 为 `format: month` 的字符串，`count` 为 `number`）下精确匹配 January=11、February=16、March=14、April=7、May=8、June=13、July=9、August=8、September=10、October=4、November=5。`ordered: false` 表示列表顺序不计，但仍须无缺失、额外或不等的对象、键和值；`performed_operation` 可作为 `task_type` 的旧别名，稀疏 expected 未显式配置物化后的 `error_details: null`。未配置 `NetworkEventEvaluator`，因此没有 URL/filter 或 last-event 判定；`network.har` 不参与该月数值比较。任务按“所有 evaluator 分数均为 `1.0`”组合，因此唯一 evaluator 无断言失败或错误并得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一 `AgentResponseEvaluator` 将解析、schema 归一化后的 `RETRIEVE`、`SUCCESS` 和上述 11 个对象按无序精确比较为一致，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把响应精确匹配、HAR/上下文可解析且评估无错误列为 success；响应为空、非对象、字段或集合不匹配，以及 trace/configuration/评估错误列为 failure。它将响应或网络 trace 未保留、或与 task 110 的关联含糊列为 undecided，同时强调已知传入的畸形或 null 输入属于 failure。非空 stronger condition `raw_integer_count_format` 进一步要求原始最终响应中的每个 `retrieved_data.count` 都以 JSON 整数编码，不能是小数形式或带引号的数字，并以 `agent_response.json` 判定。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：`network.har` 被称为决定性证据，尽管唯一配置的 evaluator 比较的是最终响应，而且预期的月份/计数数据不包含依赖 trace 的 URL。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json`，将其作为重建已配置检查所需的唯一最小 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_trace_based_native_rules`
- 为什么修改：对于这个仅使用 `AgentResponseEvaluator` 的 case，原生 success、failure 和 undecided 规则错误地依赖 HAR 的可用性或解析结果。
- 应如何修改：移除与 trace 相关的 success 和 failure 条款，不要因缺少 `network.har` 而分类为 undecided。将 undecided 限定为影响确切 agent 响应的留存、完整性或来源丢失；已知所提供的响应格式错误或为 null 时，仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_response_only_checklist`
- 为什么修改：不必要的 HAR artifact 及三个相关规则引用使 checklist 规模更大，不如已配置语义所要求的那样保持 case 最小化。
- 应如何修改：将原生证据和决策部分替换为仅针对响应的紧凑表述，同时保留单一 evaluator 组合、确切预期值、解析/normalization 行为、failure 处理方式以及更强的整数条件。

## Case 111

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得 2022 年 2 月至 11 月（含首尾）每月已完成订单数。输出只能是包含 `month`（月份名）和 `count`（整数）的对象列表，不得提供其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，要求归一化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 精确包含 February=16、March=14、April=7、May=8、June=13、July=9、August=8、September=10、October=4、November=5。结果 schema 是对象数组，`month` 为 `format: month` 的字符串、`count` 为 `number`；`ordered: false` 表示按无序且保留重复次数的精确集合比较，任何缺失、额外、重复次数或值差异均不匹配。`performed_operation` 可作为 `task_type` 别名，稀疏 expected 未配置物化默认值 `error_details: null`；没有 `NetworkEventEvaluator`，因而没有网络 filter 或 last-event 语义。唯一 evaluator 必须无错误并得 `1.0`，`TaskEvalResult.score` 才按全 evaluator 合取规则成为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 sole `AgentResponseEvaluator` 在响应归一化为 `RETRIEVE`、`SUCCESS` 并与 10 个 month/count 对象无序精确匹配时得 `1.0`，进而任务得 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把响应与 trace 均通过解析及上下文校验、比较无断言列为 success；输入/上下文/编排/评估错误或任一结构、状态、对象及重复次数差异列为 failure。它将任一 required retained input 缺失、截断或无法证明实际送入内容且无完整 evaluator outcome 的情况列为 undecided。非空 stronger condition `no-additional-response-details` 要求除 benchmark 所需 envelope 字段外，原始最终响应没有外围文字或额外顶层字段，并由 `agent_response.json` 检查。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive-network-artifact`
- 为什么修改：`network.har` 被称为决定性 artifact，尽管此 case 未配置 `NetworkEventEvaluator`，且 checklist 本身说明不会比较事件内容。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为已配置检查所需的最小充分运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-decision-rules`
- 为什么修改：原生 success 要求重放 trace，且 `undecided_if` 将 trace 缺失或未经证实视为证据丢失，尽管重建已配置的响应比较并不需要该 trace。
- 应如何修改：移除依赖 trace 的 success 和 undecided 条款。仅在所提交响应丢失、截断或来源验证失败时判定为 undecided；将完整但无效的响应、不匹配以及 response-evaluator 错误分类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal-native-body`
- 为什么修改：网络 artifact 及其关联的重放和留存规则向原生 checklist 添加了非决定性内容。
- 应如何修改：将原生正文精简为响应 artifact 和 response-evaluator 决策规则，同时单独保留有效的更强条件。

## Case 113

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：返回给 `Olivia zip jacket` 打出 3 星或以下评分的客户昵称。任务要求返回符合条件的 nickname(s)。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它在字符串数组 schema 下要求显式字段归一化为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 精确等于无序二项多重集 `["Emma", "Seam Miller"]`。`ordered: false` 忽略顺序但不忽略缺失、额外、不同或重复项；`performed_operation` 可作为 `task_type` 的旧别名，未显式配置的 `error_details` 等字段不计分。没有 `NetworkEventEvaluator`，所以无网络 filter 或 last-event 语义，昵称比较只取决于响应。唯一 evaluator 无断言或错误并得 `1.0` 时，所有 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 当且仅当唯一 `AgentResponseEvaluator` 将响应解析、归一化为 `RETRIEVE`、`SUCCESS` 和无序多重集 `["Emma", "Seam Miller"]`，且无 evaluator 或 orchestration error，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 均列为决定性 artifacts，并把昵称无缺失、额外或重复且 HAR/上下文有效列为 success；null、非 mapping、字段不匹配、数据缺失或不同，以及 trace 或评估错误列为 failure。它将响应或 trace 的 retained evidence 缺失、截断或不可读且无真实 `TaskEvalResult` 的情况列为 undecided，同时说明已记录的无效输入或 evaluator error 是 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被指定为决定性证据，尽管 case 113 仅配置了 `AgentResponseEvaluator`，且昵称比较读取的是所提交的响应，而不是网络事件。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decision_rules`
- 为什么修改：决策规则将 HAR 有效性设为 success 的前提条件，并允许因缺少 HAR 留存而判定为 undecided，尽管 HAR 对此已配置的响应比较并不具有决定性。
- 应如何修改：移除 HAR 特有的 success、failure 和 undecided 分支；保留通用的 evaluator/错误 failure 语义，并将 undecided 限定为所提交响应证据的丢失、损坏、不可读或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`trace_clauses_break_minimality`
- 为什么修改：额外的 trace artifact 和上下文有效性条款重复了基础设施方面的考虑，并使原生 checklist 超出已配置 case 声明所需的规模。
- 应如何修改：围绕唯一的 response evaluator、其明确的预期字段、基于 schema 的无序比较、任务级组合以及响应证据完整性来整合 checklist。

## Case 115

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：返回给 `Chloe tank` 打出 3 星或以下评分的客户昵称。任务表述要求返回相应 nickname(s)。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，要求响应经解析和归一化后匹配 `task_type: RETRIEVE`、`status: NOT_FOUND_ERROR` 与 `retrieved_data: null`；结果 schema 为 `{"type":"null"}`。省略 `retrieved_data` 可按 null 处理，`performed_operation` 可作为 `task_type` 的旧别名；物化默认的 `error_details: null` 并非稀疏 expected 中显式配置的比较字段，其他未配置字段也不影响此比较。由于唯一合法数据为 null，`ordered: false` 不改变可通过的值；未配置 `NetworkEventEvaluator`，故没有网络 filter 或 last-event 检查。唯一 evaluator 无结构不匹配或错误并得 `1.0` 时，`TaskEvalResult.score` 才依全 evaluator 合取规则为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`NOT_FOUND_ERROR` 和 null `retrieved_data`，无结构不匹配，并使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，把响应匹配、HAR 可接受且无输入/config/orchestration error 列为 success；响应畸形、类型或状态不符、数据非 null、evaluator error 或 HAR/编排错误列为 failure。它将任一 artifact 在 retained review evidence 中缺失、截断或不可读且无法确认实际输入是否有效的情况列为 undecided。非空 stronger condition `corroborate_not_found_against_site_evidence` 要求以 `network.har` 中充分完整的 shopping-admin 证据佐证确实没有符合 Chloe-tank 且不高于 3 星条件的昵称，并检查其与 `agent_response.json` 的 `NOT_FOUND_ERROR`/null 声明一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_native_har`
- 为什么修改：`network.har` 被错误地指定为原生决定性证据，而此 case 唯一配置的 evaluator 读取 `agent_response_raw` 并预期 `retrieved_data` 为 null。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json` 作为唯一的原生决定性 artifact；`network.har` 可以继续作为单独的更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_har_dependent_native_decisions`
- 为什么修改：原生规则要求留存的 HAR 可解析，并将其留存丢失分类为 undecided，尽管重建已配置的响应比较不需要 HAR 内容。
- 应如何修改：删除依赖 HAR 的原生 success 和 failure 条款，并将 `undecided_if` 限定为 `agent_response.json` 的丢失、损坏或来源验证失败。完整但无效或不匹配的响应必须仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`make_native_body_minimal`
- 为什么修改：尽管不存在运行信息泄漏，但不必要的原生 HAR artifact 及相关规则使 checklist 不满足最小化要求。
- 应如何修改：围绕完整的 agent 响应和唯一配置的 `AgentResponseEvaluator` 精简原生证据与决策规则，同时保留独立的基于 HAR 的更强条件。

## Case 116

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：返回给 `tanks products` 打出 3 星或以下评分的客户昵称。任务要求返回全部符合条件的 nickname(s)。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，要求归一化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，并在字符串数组 schema 下让 `retrieved_data` 精确匹配 16 个昵称：`Dominic`、`Trey`、`Edmund`、`Merrie`、`Shaunte`、`Teofila`、`Carma`、`Yan`、`Valorie`、`Mikkel`、`Matthew`、`Monroe`、`Scotty`、`Alexander`、`Tracey`、`Joey`。`ordered: false` 表示无序但重复次数敏感的精确比较；`performed_operation` 可作为 `task_type` 的旧别名，物化默认的 `error_details: null` 未被稀疏 expected 显式配置。未配置 `NetworkEventEvaluator`，因此没有网络 filter 或 last-event 语义。唯一 evaluator 必须无解析、归一化、断言或评估错误并得 `1.0`，全 evaluator 合取后 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 实际声称唯一 `AgentResponseEvaluator` 要把响应归一化为 `RETRIEVE`、`SUCCESS`，并与官方“17-nickname array”进行无序、重复敏感的精确匹配，进而使任务得 `1.0`；这里的“17”是 draft 原文的计数声明。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把响应匹配且评估无错误列为 success；无可用结构化响应、解析或归一化错误、类型/状态不符、数据为空或有缺失、额外、替换、重复次数差异，以及上下文或评估错误列为 failure。它将确切响应或 required trace 未保留、截断，且没有其他 outcome/artifact 足以定案的情况列为 undecided，同时把运行时实际缺失或无效 artifact 归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incorrect_expected_array_count`
- 为什么修改：官方预期的 `retrieved_data` 包含 16 个昵称，而不是 17 个。
- 应如何修改：将所有对 17 个昵称数组的引用替换为已配置的 16 个昵称数组，或者省略计数，同时保留确切、无序且对重复项敏感的比较。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 仅因属于批量留存契约而被描述为决定性证据，尽管未配置 `NetworkEventEvaluator`，且其内容不会影响此次昵称比较。
- 应如何修改：仅保留完整的 `agent_response.json` 作为最小充分的原生 artifact，并移除特定于 trace 的决定性问题。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_success_and_undecided_rules`
- 为什么修改：success 规则使用了错误的数组计数，而 undecided 规则则使不必要 trace 的丢失具有决定性影响。
- 应如何修改：使用已配置的 16 个名称的预期集合，并将 undecided 限定为完整提交响应的丢失、截断或来源验证失败，且该问题会阻止重建。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`checklist_not_minimal_or_exact`
- 为什么修改：错误的预期计数被重复使用，并且纳入了非决定性 artifact，因此 checklist 既不准确，也不满足最小充分性。
- 应如何修改：在所有位置更正计数，并从原生决定性 artifact 和依赖 trace 的决策表述中移除 `network.har`。

## Case 121

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：获取 Circe hooded fleece 的所有 4 星及以上评论的标题和评分，并返回键为 `"title"` 和 `"rating"` 的对象列表。任务 revision 为 `2`。

### Benchmark 怎么测

配置了唯一的 `AgentResponseEvaluator`；它对最终响应进行解析，并按 array-of-objects `results_schema` 规范化显式配置的 `task_type`、`status` 和 `retrieved_data`。期望值是 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 精确匹配 `[{"rating":4,"title":"Good but not perfect"}]`；`ordered:false` 表示列表顺序不计，但项目、字段和值仍须精确匹配，物化产生的 `error_details:null` 不参与比较。未配置网络事件 evaluator、filter 或 last-event 检查；该 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 在解析和 schema normalization 后确认 `task_type=RETRIEVE`、`status=SUCCESS`，并将 `retrieved_data` 精确无序匹配为单例 `[{"title":"Good but not perfect","rating":4}]`，继而使 `TaskEvalResult` 得分 `1.0`。它把 `agent_response.json` 和 `official TaskEvalResult record` 都列为决定性 artifacts；success 要求无比较断言且 evaluator 与任务均为 `1.0`，failure 包括响应无效、字段或数据缺失/不符、evaluator 出错或非 `1.0`，undecided 则限于最终响应缺失、截断或无法归属于该 run 且没有官方结果记录。非空 stronger condition `raw_list_of_objects_format` 进一步要求原始 `retrieved_data` 必须是真正的 JSON 数组，元素必须是真正含 `"title"`、`"rating"` 键的 JSON 对象，不能是 evaluator coercion 可接受的标量对象或字符串化对象。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`redundant_task_eval_result_artifact`
- 为什么修改：原生证据列表添加了一个未声明的“官方 `TaskEvalResult` 记录”，尽管完整的 `agent_response.json` 对唯一的 `AgentResponseEvaluator` 已经足够，而且 `undecided_if` 不当地将该记录用作响应的替代项。
- 应如何修改：从 `decisive_artifacts` 中移除 `TaskEvalResult` 记录，并将 `agent_response.json` 本身的丢失、损坏、截断或来源验证失败定义为原生 undecided 条件。将 `TaskEvalResult` 组合保留为由已发布源代码支持的决策规则，而不是额外要求的运行后证据。

## Case 124

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：查询 One Stop Market 中 wireless earphone 的价格范围。响应只能是含数值型 `"min"` 和 `"max"` 键的对象，不得附加其他细节；任务 revision 为 `2`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析最终响应，并按带 `currency` 格式的 array-of-objects schema 规范化显式配置的 `task_type`、`status` 和 `retrieved_data`。期望为 `task_type=RETRIEVE`、`status=SUCCESS`，以及一个 schema 可见对象，其 `min` 为 `0.01`、`max` 为 `298.0`；`ordered:false` 表示集合顺序不计，未识别的原始对象属性会在 schema normalization 中被丢弃，物化默认值 `error_details:null` 不比较。未配置网络事件 evaluator、filter 或 last-event 语义；唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称响应经解析和规范化后须得到 `task_type="RETRIEVE"`、`status="SUCCESS"`，并使无序 `retrieved_data` 精确等于单项 `[{"min":0.01,"max":298.0}]`，从而让唯一 evaluator 和任务都得 `1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把 HAR 被接受为 `NetworkTrace`、上下文和编排无错误纳入 success；failure 包括响应不可解析、字段或数值不符、缺少或多出 retrieved 元素或对象键，以及 HAR 或其他 evaluator 输入无效，undecided 包括响应或 trace 缺失、截断或无法关联且无保留任务得分。非空 stronger condition `literal-output-only` 要求原始响应除 evaluator-facing JSON 外没有解释文字或 Markdown fencing。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`extra_object_keys_not_native_failure`
- 为什么修改：草案称额外的 retrieved-object key 会导致比较 failure，但基于 schema 的对象 normalization 在比较前只输出已配置的属性。
- 应如何修改：从原生 `fail_if` 中移除额外的原始 retrieved-object key，并在 normalization 后、schema 可见的层面描述确切性。如有需要，可将指令中仅允许指定 key 的要求作为更强条件执行。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`har_is_not_decisive_for_sole_response_check`
- 为什么修改：草案将 `network.har` 称为决定性证据，尽管唯一配置的 evaluator 比较的是 `agent_response_raw`，且没有网络事件 predicate。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性证据，并从 artifact 问题中移除通用的 trace 解析/环境验证。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`native_rules_depend_on_nondecisive_trace`
- 为什么修改：原生 success、failure 和 undecidability 不当地依赖 HAR 的接受或留存，且 `fail_if` 还会拒绝 normalization 所忽略的原始额外对象属性。
- 应如何修改：根据完整响应的已发布提取、normalization、比较及所得 evaluator 分数作出原生决策；将 undecided 限定为响应证据的留存、完整性或来源丢失。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_trace_clauses`
- 为什么修改：对于仅配置响应检查的 case，HAR artifact 及其重复的 success/failure/undecided 条款使 checklist 不满足最小化要求。
- 应如何修改：删除 `network.har` artifact 及所有依赖 trace 的原生条款，同时保留唯一 evaluator 的响应语义和组合方式。

## Case 125

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：确定 One Stop Market 中 teeth grinding mouth guard 的最低价和最高价。响应只能是含数值型 `"min"` 和 `"max"` 键的对象，不得附加其他细节；任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对最终响应进行解析，并依照带 `currency` 格式的 array-of-objects schema 规范化显式配置的 `task_type`、`status` 和 `retrieved_data`。期望为 `task_type=RETRIEVE`、`status=SUCCESS`，且无序单项集合中的对象具有 `min=1.46`、`max=179.99`；`ordered:false` 使项目顺序不影响比较，物化的 `error_details:null` 不属于显式比较字段。没有配置网络事件 evaluator、filter 或 last-event 检查；只有该 evaluator 无错误并得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求官方评估无错误，且唯一 `AgentResponseEvaluator` 将响应解析、规范化为 `task_type=RETRIEVE`、`status=SUCCESS` 和一个无序单项 `retrieved_data`，其中 `min`、`max` 经 currency normalization 后分别为 `1.46`、`179.99`，最终 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都认定为决定性 artifacts，并把 response、trace、context validation 和 orchestration 成功纳入 success；已知的字段、项目数、对象键或数值不符，以及 response/HAR/编排错误属于 failure，而响应或 HAR 作为留存证据缺失或不可读且无官方结果时属于 undecided。原始 draft 的 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被称为决定性证据，尽管唯一配置的检查只比较最终 agent 响应。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，将其作为重建此 case 已配置检查所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_based_decision_rules`
- 为什么修改：success 和 undecided 规则不当地依赖 `network.har` 的留存和解析。
- 应如何修改：根据已发布的完整响应评估结果判定 success 和常规 failure，并将 undecided 限定为 `agent_response.json` 的丢失、不完整、完整性验证失败或来源验证失败，且该问题会阻止重建。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_network_boilerplate`
- 为什么修改：条件式网络解析和环境回退规定增加了不必要的 case 审查分支，却无助于已配置的响应比较。
- 应如何修改：删除特定于网络的 artifact 和决策规则文本，留下紧凑的 response-evaluator checklist，同时不改变预期值或任务级组合。

## Case 127

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得与店内现有商品匹配的前三个搜索词。任务 revision 为 `2`，指令没有要求额外的输出字段。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析并规范化最终响应中显式配置的 `task_type`、`status` 与 `retrieved_data`，其中 `retrieved_data` 使用 array-of-strings schema。期望为 `task_type=RETRIEVE`、`status=SUCCESS`，并以 `ordered:false` 做保留重复次数的精确无序比较，内容必须恰为 `"Hollister"`、`"Joust Bag"`、`"Antonia Racer Tank"` 各一次；物化默认的 `error_details:null` 不比较。没有配置网络事件 evaluator、filter 或 last-event 语义；唯一 evaluator 得分必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native success 是 `TaskEvalResult.score = 1.0`：响应经支持的解析和规范化后须匹配 `RETRIEVE`、`SUCCESS`，且 `retrieved_data` 必须以保留重复次数的无序精确比较匹配 `Hollister`、`Joust Bag`、`Antonia Racer Tank`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；success 还要求 trace 和 evaluation context 被接受，failure 包括响应字段或三项数据缺失、重复、额外或不符，以及任何 response/trace parsing 或 evaluator orchestration error，undecided 则是响应或 trace 因缺失或存储损坏而无法重建。原始 draft 的 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_har`
- 为什么修改：`network.har` 被列为决定性证据，尽管 task 127 仅配置了 `AgentResponseEvaluator`，且所表示的比较使用所提交的响应，而不是网络事件。
- 应如何修改：仅保留 `agent_response.json` 作为最小的原生决定性 artifact，并移除 HAR 问题。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_native_rules`
- 为什么修改：尽管不存在已配置的 `NetworkEventEvaluator`，也不存在依赖网络内容的 case 特定响应，但 success、failure 和 undecided 规则仍将 trace 的可用性或解析纳入原生重建。
- 应如何修改：从 `success_if` 和 `fail_if` 中移除 trace 接受和 trace 解析条件，并将 `undecided_if` 限定为 `agent_response.json` 的丢失、损坏或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_material`
- 为什么修改：HAR artifact 和 trace 相关规则向原本紧凑的 checklist 添加了非决定性内容。
- 应如何修改：删除非决定性的 HAR 条目及所有重复的 trace 引用，同时保留 response evaluator 的解析、normalization、比较、错误和组合语义。

## Case 131

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：计算最近 7 个状态为 complete 的订单共售出多少件商品。任务 revision 为 `2`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析并规范化最终响应中显式配置的 `task_type`、`status` 和 `retrieved_data`，后者采用 number-array schema。期望为 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data=[17]`；`ordered:false` 表示进行精确无序数组比较，因此规范化后必须只有一个数值 `17`，而物化默认的 `error_details:null` 不比较。没有配置网络事件 evaluator、filter 或 last-event 检查；该 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称任务得分为 `1.0` 当且仅当唯一 `AgentResponseEvaluator` 得 `1.0`，即响应解析和规范化为 `task_type=RETRIEVE`、`status=SUCCESS`，且 retrieved data 在无序精确数组比较下匹配单个数值 `17`。它将 `agent_response.json` 和 `network.har` 都列作决定性 artifacts，并把 HAR 与响应形成无错误 evaluation context 纳入 success；trace 或响应不可解析、字段不符、数据缺失或多出属于 failure，而响应或 HAR 未留存且无官方 `TaskEvalResult` 时属于 undecided。非空 stronger condition `raw_retrieved_data_array` 进一步要求提交响应中的原始 `retrieved_data` 必须就是含单个 JSON 数字 `17` 的数组 `[17]`，不能是 evaluator 自动包装为单例数组的标量。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被视为必要的决定性证据，尽管唯一配置的检查仅比较 agent 响应，且预期的 retrieved 值为数值。
- 应如何修改：从原生决定性 artifact 中移除 `network.har`，并使用完整的 `agent_response.json` 作为已配置检查所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decision_rules`
- 为什么修改：尽管不存在 `NetworkEventEvaluator`，这些规则仍使 HAR 的解析或留存影响 success、failure 和 undecided 结果。
- 应如何修改：从 `success_if`、`fail_if` 和 `undecided_if` 中移除 HAR 要求；仅在所提交响应丢失或来源验证失败时判定为 undecided，并将完整但无效的响应判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：额外的 HAR artifact 及其重复的规则引用使 checklist 不满足最小化要求，并添加了超出此 case 已配置 evaluator 的条件。
- 应如何修改：删除非决定性的 trace 内容，同时保留响应比较、evaluator 组合以及单独的更强条件。

## Case 132

### 原本 case 是什么

原始任务是在 `gitlab` 站点完成一个 `RETRIEVE` 任务：回答 kilian 在 2023 年 3 月 5 日为 `a11yproject.com` 提交了多少次 commit。用户要求的是该日期、用户和仓库组合对应的数量。

### Benchmark 怎么测

仅配置了一个 `AgentResponseEvaluator`，它检查响应经解析和规范化后，显式配置字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 是否符合数字数组 schema 并在 `ordered: false` 的无序精确比较下等于 `[1]`，不能有缺失或额外元素。物化配置中的 `error_details: null` 是默认值，不属于稀疏配置显式要求的比较字段。没有配置 `NetworkEventEvaluator`，因此不存在 URL/filter 或 last-event 检查，`network.har` 也不参与该响应值比较。由于只有这一个 evaluator，只有其分数等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得到 `1.0`：响应规范化为 `RETRIEVE`、`SUCCESS`，且无序的单元素数字结果精确等于 `[1]`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于判断 trace 是否可读并足以构造 GitLab evaluation context。其 success 条件要求响应匹配且 evaluation input/context 无错误；failure 包括响应无法解析、字段或数据不匹配、trace/context 错误或 evaluator 非 `1.0`；若决定性 artifact 未保留且其他证据不能定案，则标为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-001`
- 为什么修改：`network.har` 被指定为决定性证据，尽管唯一配置的 evaluator 是 `AgentResponseEvaluator`，且其与评分相关的比较使用提交的响应。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，将其作为最小充分原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-002`
- 为什么修改：通用的决定性 artifact 缺失规则允许因 `network.har` 缺失而不必要地产生 `undecided`。
- 应如何修改：将 `undecided_if` 限制为 `agent_response.json` 或明确等价的完整响应证据发生丢失、不完整、损坏或来源不确定的情况；完整但无效或不匹配的响应仍应判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-003`
- 为什么修改：特定于 trace 的 artifact 和决策条款向原本仅基于响应的检查清单添加了非决定性材料。
- 应如何修改：移除网络 artifact 和特定于 trace 的条款，同时保留响应解析、normalization、精确的无序比较、evaluator 错误时判定 `failure`，以及所有 evaluator 的组合规则。

## Case 136

### 原本 case 是什么

原始任务是在 `gitlab` 站点完成一个 `RETRIEVE` 任务：回答 Steven Woodson 在 2023 年 2 月 6 日为 `a11y-webring.club` 提交了多少次 commit。任务所求是该指定用户、仓库和日期对应的提交数量。

### Benchmark 怎么测

仅配置了 `AgentResponseEvaluator`；它解析并规范化提交响应，检查显式配置字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，并按数字数组 schema 将 `retrieved_data` 以 `ordered: false` 的无序精确方式与 `[5]` 比较。物化产生的 `error_details: null` 不属于稀疏配置的显式比较字段。没有 `NetworkEventEvaluator`，所以没有 URL/filter、网络事件或 last-event 语义，完整的 `agent_response.json` 足以重建该配置检查。唯一 evaluator 必须得到 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 定义为：响应经 released parsing 和 number normalization 后匹配 `RETRIEVE`、`SUCCESS` 以及仅含数字 `5` 的无序 `retrieved_data`，使唯一 evaluator 和 `TaskEvalResult.score` 均为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；success 是比较无 assertion 且无处理错误，failure 是任一结构或数值 mismatch、错误的或缺失的 task type/status、结果不等于 `[5]`，或 evaluator error。若提交响应不可用或被截断，且没有保留的官方 `TaskEvalResult` 定案，则为 undecided。它还提出非空 stronger condition `public_response_schema`：原始文件必须是合法的公开 `FinalAgentResponse` JSON，使用数组形式的 `retrieved_data: [5]`，并且 SUCCESS 时不得有非空 `error_details`。

### 需要修改的部分

#### 修改项 1：stronger.additional_conditions

- Finding ID：`remove_unjustified_public_schema_stronger_condition`
- 为什么修改：`public_response_schema` 条件增加了原始响应格式要求，尽管该材料未显示官方提交次数目标与已发布 evaluator 所验证的值之间存在任何差异。
- 应如何修改：移除该 stronger condition，并使 `stronger.additional_conditions` 保持为空；不要改变原生评分语义。

## Case 137

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：使用 OSRM direction service，求自由钟所在城市与 Pirates 主场城市之间的预计驾车时间。答案必须仅以 `HH:MM:SS` 字符串返回，不得附加其他说明。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应进行提取、解析和 duration schema 规范化，然后检查显式字段 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 是否在 `ordered: false` 的无序精确比较下为与 `"5h 47min"` 等价的单元素 duration 数组。物化默认值 `error_details: null` 未被稀疏配置显式要求，因此不参与比较。没有配置网络 evaluator，故没有 OSRM URL/filter 或 last-event 语义，原生评分也不验证是否实际使用 OSRM。只有该 evaluator 得分 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native benchmark success 是 `TaskEvalResult.score = 1.0`：唯一 `AgentResponseEvaluator` 在 duration normalization 后无 mismatch 地匹配 `RETRIEVE`、`SUCCESS` 和与 `"5h 47min"` 等价的无序单元素结果。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把 trace/context 可加载、无 orchestration error 纳入 success；响应为空、畸形、字段或 duration 不匹配，以及 trace/context 加载失败或 evaluator 非 `1.0` 均列为 failure。若无法确定实际提供给 evaluator 的响应或 trace，且无官方 `TaskEvalResult` 定案，则为 undecided。非空 stronger conditions 包括 `literal_hh_mm_ss`，要求答案恰为 `"05:47:00"`；以及 `osrm_provenance`，要求 `network.har` 证明针对两个端点的成功 OSRM directions 请求，其返回时长支持 `agent_response.json` 中的答案。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace`
- 为什么修改：对于唯一配置的 evaluator 为 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性原生证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并根据完整的 `agent_response.json` 重建已配置的原生检查。仅为 OSRM stronger condition 保留 `network.har`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_failure_retention_conflation`
- 为什么修改：trace/context 加载失败规则可能会将损坏或不可用的留存证据归类为原生 `failure`，即使该证据并不能证明确实向 evaluator 提供了同一个无效输入。
- 应如何修改：将 `failure` 限制为实际提供给 evaluation 的完整无效或不匹配响应证据，以及在应用已配置检查时由已发布 evaluator 产生的错误；将缺失、截断、损坏或来源不确定的留存响应证据归类为 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_rules`
- 为什么修改：原生检查清单包含一个不必要的 HAR artifact 问题，以及特定于 trace 的成功和失败条款。
- 应如何修改：删除原生 HAR artifact 和 trace 加载条款，同时保留精简的响应比较、evaluator 分数组合以及证据完整性相关的 `undecided` 规则。

## Case 138

### 原本 case 是什么

原始任务是在 `map` 站点完成一个 `RETRIEVE` 任务：使用 OSRM direction service，求 “the big apple” 与 “the city with the most authentic Philly cheesesteaks” 之间的预计驾车时间。返回内容必须仅为 `HH:MM:SS` 格式的字符串，不得包含其他细节。

### Benchmark 怎么测

仅配置了 `AgentResponseEvaluator`，它对字符串响应进行空白清理、可适用的 JSON 或无类型 fenced code block 提取及 JSON decoding，再投影稀疏 expected 中显式配置的 `task_type`、`status` 和 `retrieved_data`；缺少 `task_type` 时可接受 legacy 字段 `performed_operation`。随后按 duration 字符串数组 schema 规范化，并以 `ordered: false` 无序精确比较 `RETRIEVE`、`SUCCESS` 和单元素结果 `"1h 58min"`；物化默认的 `error_details: null` 及其他未投影顶层字段不参与比较。没有 `NetworkEventEvaluator`，因此没有 OSRM URL/filter 或 last-event 检查。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求运行输入可评估，且唯一 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS` 和等于 `1h 58min` 的无序单元素 duration 数组，从而其分数及 `TaskEvalResult.score` 都为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 HAR 可解析及 evaluation 无错误列入 success；响应缺失、无效、非对象、字段或 duration 不匹配，以及 HAR 无法加载、orchestration error 或 evaluator 非 `1.0` 均列为 failure。若实际响应或 HAR 不可用或被截断且无可靠 `TaskEvalResult`，则为 undecided。非空 stronger conditions 是 `exact_hh_mm_ss_answer`，要求唯一用户可见值恰为 `01:58:00` 且无额外文本或值；以及 `osrm_direction_service_evidence`，要求 `network.har` 显示成功的 OSRM directions/route 请求及与 `01:58:00` 一致的时长。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_trace_overreach`
- 为什么修改：原生评分被设置为取决于 HAR 的加载和解析，尽管该 case 只有一个 `AgentResponseEvaluator`，且其 actual value 为 `agent_response_raw`。
- 应如何修改：从原生 `benchmark_success`、`success_if` 和 `fail_if` 中移除 HAR 存在性和可解析性要求。改为说明显式配置的响应字段、duration normalization、无序比较以及唯一 evaluator 的组合规则。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifacts`
- 为什么修改：`network.har` 被列为决定性证据，尽管没有已配置的 evaluator 检查网络事件，而且完整的 `agent_response.json` 足以确定已配置比较的结果。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性证据。`network.har` 可继续作为单独的 stronger OSRM 使用条件的证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_native_decisions`
- 为什么修改：这些规则将非决定性 trace 的丢失或损坏视为原生 `failure` 或 `undecided`。
- 应如何修改：以已发布 `AgentResponseEvaluator` 的比较结果为依据判定原生 `success` 和 `failure`，并仅在影响实际提交响应的留存、完整性或来源信息丢失时判定原生 `undecided`。完整但无效或不匹配的响应必须仍判定为 `failure`。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_native_trace_clutter`
- 为什么修改：原生 HAR artifact 及三个相关决策条款向原本精简的检查清单添加了非决定性材料。
- 应如何修改：移除原生 HAR artifact 和依赖 HAR 的原生条款，同时仅在可度量的 stronger OSRM 条件下保留 `network.har`。

## Case 141

### 原本 case 是什么

原始任务是在 `shopping` 站点完成一个 `RETRIEVE` 任务：返回 2023 年 3 月食品相关购物的总支出，并排除 shipping and handling fee。答案必须仅作为数字返回，例如 `10.99`，不得添加其他说明。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 解析响应并投影稀疏 expected 显式配置的字段，要求规范化结果为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 按 currency 数字数组 schema 规范化后，以 `ordered: false` 无序精确比较等于 `[32.41]`。字符串响应可从 JSON 或无类型 fenced code block 中提取 JSON；`performed_operation` 可作为 legacy `task_type`，标量 `retrieved_data` 可包装为单元素序列，而物化默认的 `error_details: null` 不参与显式比较。没有 `NetworkEventEvaluator`，所以不存在 URL/filter 或 last-event 语义，`network.har` 不影响该 currency 响应检查。只有该 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 写为：唯一 `AgentResponseEvaluator` 得分 `1.0`，响应规范化成 `RETRIEVE`、`SUCCESS` 和无序 currency 数组 `[32.41]`，因此 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并在 success 中要求响应匹配、trace 可解析；failure 包括实际响应为空、不可解析、字段或结果不匹配、确认的无效输入、evaluator/orchestration error 或 evaluator 非 `1.0`。若无法确定提交了什么响应或 required trace 是否可用且可解析，则为 undecided。非空 stronger condition `literal_numeric_answer_format` 要求用户可见答案编码为单一 JSON 数字 `32.41`、没有解释性 prose，并排除 currency-equivalent 字符串、标量 coercion 或从带 prose 的 fenced JSON 中提取后才成立的形式。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：对于唯一配置的检查为 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并基于完整的 `agent_response.json` 重建已配置的检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：原生 `success` 和 `undecided` 被错误地设置为取决于 `network.har` 的留存或可解析性。
- 应如何修改：从 `success_if`、`fail_if` 和 `undecided_if` 中移除 trace 要求；仅在所提交响应证据发生丢失、损坏或来源不确定时判定 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_clauses`
- 为什么修改：额外的网络 artifact 和重复的 trace 条款违反了原生证据检查清单的最小化要求。
- 应如何修改：删除非决定性网络 artifact，并围绕唯一的响应比较整合原生规则，不要添加运行结果或新条件。

## Case 142

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：计算 2023 年 1 月在 hair care and hair style 购物上的支出，并排除 shipping and handling fee。用户要求只返回数字，例如 `10.99`，不得附加其他内容。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查显式字段 `task_type`、`status` 和 `retrieved_data`：经支持的字典或 JSON/代码块解析及规范化后，前两者须为 `RETRIEVE`、`SUCCESS`，后者须按 `format: currency` 规范化为恰好一个值的无序多重集 `[68.51]`；`ordered` 为 `false`，稀疏配置未显式要求 `error_details`。空值、非对象、字段缺失或不匹配、数据基数或值不符以及 evaluator 错误都会使该 evaluator 不得 `1.0`。未配置 `NetworkEventEvaluator`，因此没有 URL filter 或 last-event 判定；任务仅在唯一 evaluator 的 score 等于 `1.0` 时令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称，唯一 `AgentResponseEvaluator` 在响应匹配 `RETRIEVE`、`SUCCESS` 和经货币规范化、无序比较的单值 `68.51` 且无错误时得 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并分别用于检查响应比较以及 trace/context 是否可验证。其 success 规则要求字段比较及官方评估均无误；failure 规则涵盖空、null、不可解析或不匹配的响应，以及响应规范化、trace 解析、context 验证或 evaluator 编排错误；两类 artifact 在运行后丢失或不可读时被列为 undecided。非空 stronger condition `bare_number_user_output` 另要求原始用户可见答案严格为裸数字 `68.51`，不能含 JSON envelope、code fence、label、解释或其他文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_trace`
- 为什么修改：`network.har` 被表述为必需的决定性证据，尽管唯一配置的检查是 actual value 来自 `agent_response_raw` 的 `AgentResponseEvaluator`。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json`，将其作为重建已配置响应比较的最小充分 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`restrict_trace_based_decisions`
- 为什么修改：原生 `fail` 和 `undecided` 规则依赖 trace 解析、context 验证和 trace 留存，尽管 trace 证据对该已配置检查并不具有决定性。
- 应如何修改：移除特定于 trace 的 `success`、`failure` 和 `undecided` 条件。将完整但无效或不匹配的响应证据视为 `failure`，并仅在 `agent_response.json` 丢失、损坏、截断或来源验证失败时判定 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_native_evidence_set`
- 为什么修改：额外的 trace artifact 和重复的 trace 依赖条件使检查清单超出了这个仅基于响应的 case 所需的最小证据表述。
- 应如何修改：使用仅基于响应的原生证据集，并移除冗余的 trace 表述，同时保留 evaluator 错误和任务组合语义。

## Case 144

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：返回 2023 年 1 月 15 日至 1 月 31 日的 food shopping 支出，并排除 shipping and handling fee。指令未另行规定输出包装格式。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对显式字段 `task_type`、`status` 和 `retrieved_data` 做提取、规范化与比较：目标分别是 `RETRIEVE`、`SUCCESS` 和恰好为数值 `0` 的无序单元素数组 `[0]`；schema 为 number array，`ordered` 为 `false`，稀疏 expected 未显式配置 `error_details`。不可提取为所需结构、字段缺失或不匹配、`retrieved_data` 缺失、null、空、值不同或含额外值，以及 evaluator 错误，都会得到非 `1.0` 分数。未配置 URL filter 或 last-event evaluator；仅当这个唯一 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，当提交响应规范化为 `task_type: RETRIEVE`、`status: SUCCESS` 和无序数值数据 `[0]` 时，唯一 `AgentResponseEvaluator` 得 `1.0`，并使 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，后者被用于确认 HAR 可作为 `NetworkTrace` 构建评估上下文。success 规则要求两个 artifacts 均可用且官方评估为 `1.0`；failure 包括结构不可解析、类型或状态不符、数据不是严格单值 `0`、运行输入缺失或 evaluator 处理错误；响应或 HAR 在运行后丢失、截断或损坏且无结果记录时为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_har`
- 为什么修改：`network.har` 被列为决定性证据，尽管未配置 `NetworkEventEvaluator`，且 `AgentResponseEvaluator` 仅从 `agent_response_raw` 获取其 actual value。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，将其作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decisions`
- 为什么修改：原生 `success` 和 `undecided` 分类不当地依赖 HAR 的可用性，因此 HAR 丢失可能会掩盖仍可根据完整响应重建的结果。
- 应如何修改：从 `success_if`、`fail_if` 和 `undecided_if` 中移除 HAR 可用性要求；仅在响应证据丢失、损坏、截断或来源验证失败，且没有留存的 evaluator 结果可确定分数时判定 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_har_material`
- 为什么修改：额外的 HAR artifact 和重复的 HAR 门控条件使这个仅基于响应的 case 的检查清单不再最小化。
- 应如何修改：删除 HAR artifact 和所有依赖 HAR 的决策表述，同时保留响应解析、normalization、比较和组合规则。

## Case 145

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：计算 2022 年 3 月 cooking and food shopping 的支出，并排除 shipping and handling fee。用户要求只返回数字，例如 `10.99`，不得附加其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查稀疏配置显式指定的 `task_type`、`status` 和 `retrieved_data`；经支持的响应提取及规范化后，它们须匹配 `RETRIEVE`、`SUCCESS` 和按 `format: currency` 规范化的无序单元素数组 `[42.35]`，而 materialized 默认值 `error_details: null` 不属于显式比较条件。缺失、null、空、不可解析、货币规范化失败、值或基数不符，以及 evaluator 或任务级错误都会使分数非 `1.0`。没有配置网络 URL filter 或 last-event 语义；唯一 evaluator 得分为 `1.0` 时且仅当此时，`TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称，响应对象经解析和规范化后匹配 `RETRIEVE`、`SUCCESS` 及无序、货币规范化的单值 `[42.35]`，且没有 evaluator 或任务级错误时，唯一 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都作为决定性 artifacts，分别检查响应内容和官方上下文所需 `NetworkTrace`。success 规则还要求 trace 可解析且评估无错误；failure 包括响应为空、畸形、非对象、字段或数据不符、货币规范化失败、trace 无法解析或编排错误；响应或 trace 缺失、截断或无法归属于该运行且无替代证据时为 undecided。非空 stronger condition `literal_number_only_response` 要求原始用户可见答案仅为裸数字 `42.35`，不能有 JSON wrapper 或其他文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_har`
- 为什么修改：`network.har` 被称为决定性证据，尽管未配置 `NetworkEventEvaluator`，且该 case 特有的响应比较并不检查 trace。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json`，将其作为最小充分原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decisions`
- 为什么修改：原生 `success`、`failure` 和 `undecided` 规则不当地依赖所留存 HAR 的可解析性或可用性。
- 应如何修改：基于 evaluator 可见的完整响应作出原生判定，并且仅当该响应证据或其无损等价物不可用或缺乏完整性/来源信息时才归类为 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_rules`
- 为什么修改：非决定性 trace 要求在原生部分中反复出现，使检查清单比必要范围更大、语义更宽。
- 应如何修改：删除 HAR 特有的 artifact 和决策条款，同时保留响应 evaluator 的解析、稀疏字段、normalization、比较、错误和组合语义。

## Case 146

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：取得用户于 2022 年 9 月购买的 picture frame 的尺寸。输出应为含键 `"width"` 和 `"height"` 的对象列表。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对显式字段 `task_type`、`status`、`retrieved_data` 进行解析、schema 规范化和无序精确比较：前两者须为 `RETRIEVE`、`SUCCESS`，数据须恰好包含一个仅有 `width`、`height` 的对象。`width` 必须匹配 `^16(?:\.0+)?\s*[-]?\s*(?:inch(?:es)?|in\.?|″|"|'|')$`，`height` 必须匹配 `^24(?:\.0+)?\s*[-]?\s*(?:inch(?:es)?|in\.?|″|"|'|')$`；`ordered` 为 `false`，未显式比较 materialized 的 `error_details`。结构、字段、键集、项目数或正则不匹配及 evaluator 错误都会使其不得 `1.0`；没有 URL filter 或 last-event evaluator，且仅当这个唯一得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称，唯一 `AgentResponseEvaluator` 在解析及规范化后看到 `RETRIEVE`、`SUCCESS`，并将无序 `retrieved_data` 精确匹配为一个符合 16-inch width 和 24-inch height 模式的对象时得 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它列出的决定性 artifacts 是 `agent_response.json` 和 task 146 的 `Official TaskEvalResult record`，并要求结果记录显示 task 与 evaluator 均为 `1.0` 且无错误。failure 包括官方结果为 `0.0` 或 failure/error，以及可评估响应存在结构、类型、状态、数据项、键或尺寸不匹配；既无可用响应也无可信结果记录，或两者冲突时为 undecided。非空 stronger condition `raw_retrieved_data_is_list` 要求原始 `retrieved_data` 本身是 JSON list，而非由 evaluator 强制包装成单元素序列的 lone object 或 encoded object。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_result_record`
- 为什么修改：检查清单向原生证据集添加了一条 Official `TaskEvalResult` 记录，尽管完整的 `agent_response.json` 可以重建唯一配置的 evaluator 检查，而且该清单还将这条冗余记录作为 `success` 的一部分。
- 应如何修改：从决定性 artifact 中移除 `TaskEvalResult` 记录，并按照已发布 evaluator 的语义，根据完整且来源可归属的 `agent_response.json` 判定原生 `success` 或 `failure`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`unclassified_missing_result_record`
- 为什么修改：通过重建检查但缺少 `TaskEvalResult` 记录的完整响应不满足当前任何 `success`、`failure` 或 `undecided` 规则。
- 应如何修改：使通过检查的完整 `agent_response.json` 足以判定 `success`，将 evaluator 可见的不匹配或错误判定为 `failure`，并仅在响应的留存、完整性或来源信息丢失时判定 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundancy_and_rule_incoherence`
- 为什么修改：额外的分数记录 artifact 重复了可根据响应重建的结果，并造成决策覆盖不一致。
- 应如何修改：使用一个最小原生 artifact，并基于该 artifact 建立完整的三分决策划分；保留单独的 stronger 原始列表条件。

## Case 147

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：取得用户在 2022 年购买的 picture frame 的尺寸。输出应为含键 `"width"` 和 `"height"` 的对象列表。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 在字符串/代码块 JSON 提取、configured-field projection 和 schema 规范化后，比较显式配置的 `task_type`、`status`、`retrieved_data`：目标是 `RETRIEVE`、`SUCCESS`，以及无序数组中恰好一个仅含 `width`、`height` 的对象。`width` 须匹配 `^16(?:\.0+)?\s*[-]?\s*(?:inch(?:es)?|in\.?|″|"|'|')$`，`height` 须匹配 `^24(?:\.0+)?\s*[-]?\s*(?:inch(?:es)?|in\.?|″|"|'|')$`；`ordered` 默认 `false`，未配置的 `error_details` 等顶层字段会被忽略。缺失、null、空、非 mapping、项目数或键集不符、正则不匹配及 evaluator 错误均导致非 `1.0`；没有 URL filter 或 last-event 判定，且唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，唯一 `AgentResponseEvaluator` 经解析、规范化、singleton coercion 和无序结构比较后匹配 `RETRIEVE`、`SUCCESS` 及一个符合锚定 16/24 模式的 width/height 对象时，`TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并让 HAR 承担加载 `NetworkTrace`、构建上下文及必要时从事件推导 fallback site URL 的作用。其 success 规则还声称 `error_details` 不得作为额外比较字段保留；failure 相应把残留或导致规范化失败的 `error_details`、响应结构或尺寸不匹配、以及编排错误列为失败，缺少响应或解决争议所需 trace/configuration 证据时可为 undecided。非空 stronger condition `require_raw_list_shape` 要求提交的 `retrieved_data` 本身必须是仅含一个 width/height 对象的 JSON array，而不是 evaluator 可包装的 bare object 或其他 singleton。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unconfigured_error_details`
- 为什么修改：检查清单暗示 `error_details` 可能作为额外 key 在 normalization 后保留下来，或导致 normalization 失败，尽管它未被显式配置，而且按已配置字段进行的 normalization 不会迭代该字段。
- 应如何修改：说明只有 `task_type`、`status` 和 `retrieved_data` 是已配置的比较字段，并且该 evaluator 投影会忽略原始 `error_details` 或其他未配置的顶层字段。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 仅因 trace 加载和条件性环境恢复而被称为决定性证据，尽管该 case 只有一个 `AgentResponseEvaluator`，且不存在与评分相关的网络比较。
- 应如何修改：从原生决定性 artifact 中移除 `network.har`，并使用完整且来源已确立的 `agent_response.json` 作为最小充分的运行后证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_failure_and_undecided_rules`
- 为什么修改：`failure` 规则包含一个不可能发生的 `error_details` 分支，而 `undecided` 被不当地扩展至缺失 trace/configuration 证据的情况，尽管重建该已配置检查并不需要这些证据。
- 应如何修改：移除 `error_details` 失败分支，明确将未配置的顶层字段视为忽略项，并将 `undecided` 限制为完整的 evaluator 输入响应发生丢失、损坏或来源不确定的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：推测性的 HAR/configuration 分支以及重复且无依据的 `error_details` 限定条件增加了非决定性且具有误导性的材料。
- 应如何修改：将其替换为对已配置字段投影、响应 normalization/比较以及响应证据完整性的精简说明。

## Case 149

### 原本 case 是什么

原始任务是在 `shopping` 站点查询用户于 2023 年 2 月购买的“artifical plants”的颜色，task type 为 `RETRIEVE`。官方指令是 `Get the color of the artifical plants I bought Feb 2023.`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，它对最终响应进行解析和规范化，并比较稀疏配置中明确给出的 `task_type`、`status` 和 `retrieved_data`；期望分别规范化为 `RETRIEVE`、`SUCCESS` 和字符串数组 `["Green-vines"]`。`retrieved_data` 采用 `ordered=false` 的无序精确比较，因此必须恰为一个匹配项，不能缺失、重复或增加其他项；物化出的 `error_details:null` 不是稀疏配置中明确参与比较的字段。本 case 没有基于网络事件或 last-event 的 evaluator；`TaskEvalResult.score` 仅在这个唯一 evaluator 的分数等于 `1.0` 时为 `1.0`，不匹配或评估错误产生非成功分数。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 经解析和规范化后匹配 `task_type RETRIEVE`、`status SUCCESS` 及无序单项 `["Green-vines"]`，且无评估错误，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把响应匹配、trace 可解析以及评估上下文无错误共同写入 success 条件。failure 包括响应为空、畸形或非对象，类型、状态或结果项不匹配，以及响应或 trace 解析、evaluator 执行或编排进入 `ERROR` 并得到 `0.0`。undecided 被定义为响应或所需 trace 缺失、截断或损坏而无法重建实际评估输入，但已保留证据表明确实提交了无效输入时算 failure。`stronger.additional_conditions` 为空，没有非空 stronger condition。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`network_trace_not_decisive`
- 为什么修改：仅仅因为 `network.har` 出现在批次的 required-artifacts 行中，就被错误地指定为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json`，将其作为重建此已配置的 `AgentResponseEvaluator` 比较所需的唯一最小运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：尽管仅有的已配置响应检查可根据 `agent_response.json` 重建，这些规则仍将 trace 可解析性设为 success 的必要条件，并将 trace 留存丢失设为足以判定 undecided 的条件。
- 应如何修改：移除依赖 trace 的 success、failure 和 undecided 表述。将 undecided 限定为完整 agent response 的丢失、损坏或来源证明失败；完整但无效或不匹配的响应仍为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_trace_clauses`
- 为什么修改：不必要的 network artifact 及其重复出现的规则条款，使 checklist 无法成为对此 case 的紧凑最小表述。
- 应如何修改：删除 `network.har` artifact 条目，并围绕唯一的 `AgentResponseEvaluator` 和完整的 `agent_response.json` 整合原生规则。

## Case 150

### 原本 case 是什么

原始任务是在 `shopping` 站点查找用户于 2023 年 1 月购买的 fake tree 的价格，task type 为 `RETRIEVE`。答案须只返回数字形式的值，例如 `10.99`，不得附加其他细节。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`：它从最终响应中提取和解析可支持的 JSON 表示，只规范化稀疏 expected 明确配置的字段，并比较 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data=[260.69]`。结果 schema 是元素带 `format:"currency"` 的 number array，且 `ordered=false`，所以规范化后的结果必须是无序精确单项 `260.69`；物化默认值 `error_details:null` 不属于明确配置的比较字段。本 case 没有网络事件或 last-event evaluator；唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求唯一 `AgentResponseEvaluator` 在解析和 currency 规范化后得到 `RETRIEVE`、`SUCCESS` 及无序单项 `260.69`，无 assertion 或 evaluator error，并使 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，success 还要求 trace 与 evaluation context 可无错误解析。failure 包括 task type、status、`retrieved_data` 的缺失或不匹配、额外或缺少结果项，以及响应、trace、上下文、evaluator 或编排错误；undecided 则包括任一 artifact 缺失、截断或无法确认来自同一 run。非空 stronger condition `number_only_presentation` 要求原始最终响应除承载结果所需的协议字段外只含数字 `260.69`，不得有 JSON 外 prose 或非协议解释字段，因为 draft 指出原生 evaluator 可能从周围文本提取 fenced JSON 且忽略未配置字段。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_artifact`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并将完整的 `agent_response.json` 用作最小充分留存证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：这些规则要求解析 trace 才能判定 success，并将缺少 `network.har` 视为 undecided，尽管这并不会妨碍重建已配置的响应比较。
- 应如何修改：移除依赖 trace 的 success 条件，并将 `undecided_if` 限定为 `agent_response.json` 的丢失、损坏或来源证明失败。完整但无效或不匹配的响应以及 evaluator 错误仍应判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_branches`
- 为什么修改：多个与 trace 相关的分支重复表达了一项基础设施问题，而该问题对该 case 已配置的检查并非决定性因素。
- 应如何修改：删除不必要的 network artifact，以及特定于 trace 的 success、failure 和 undecided 表述，同时保留响应 evaluator 和任务组合规则。

## Case 151

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service，查询从 CMU 驾车到 University of Pittsburgh 的最短旅行时间，task type 为 `RETRIEVE`。答案须仅以 `HH:MM:SS` 字符串返回，不得包含其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它解析最终响应并投影稀疏 expected 中明确配置的字段，比较规范化后的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data=["4min"]`，其中 `performed_operation` 可作为 legacy `task_type` 来源。结果 schema 是 duration string array，标量或数组按 duration 规则规范化，并以 `ordered=false` 做无序但值和基数均精确的比较；`error_details:null` 是物化默认值，不是明确配置的比较字段。没有 `NetworkEventEvaluator`，因此没有 OSRM 流量或 last-event 条件参与原生计分；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 将响应匹配为 `task_type=RETRIEVE`、`status=SUCCESS`，且 duration 规范化后的无序单项与 `4min` 相符，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，虽称没有 `NetworkEventEvaluator` 检查 OSRM 流量，仍把 trace 可解析和上下文无错误列入 success。failure 包括响应非对象、比较字段缺失或不匹配、结果值或基数不符，以及响应或 trace 解析、上下文、evaluator 或编排错误；undecided 包括实际响应或 trace 因留存缺失、截断而无法重建。非空 stronger conditions 有 `osrm_route_provenance`，要求 trace 证明对指定端点发起了成功的 OSRM driving-route 请求且答案与其中最短时长一致；还有 `literal_hh_mm_ss_output`，要求唯一用户可见值恰为 `00:04:00` 且无解释文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace`
- 为什么修改：`network.har` 仅仅因为属于批次 artifact 合约和 evaluator API 输入路径，就被列为原生决定性 artifact；并未配置 `NetworkEventEvaluator`，且所表示的 trace 内容均不会改变响应比较。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。它可以继续作为单独的 OSRM 来源证明更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_contaminates_native_rules`
- 为什么修改：尽管完整响应足以供此已配置 evaluator 使用，这些规则仍要求解析 trace 才能判定 success，将 trace 解析计为独立的原生 failure，并将留存 trace 的丢失视为 undecided。
- 应如何修改：仅基于完整的 `agent_response.json` 进行原生重建。将 undecided 限定为该响应证据的丢失或完整性/来源证明失败，同时保留以下规则：已知的官方 evaluator 错误或无效的完整响应为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_clauses`
- 为什么修改：同一项非决定性 trace 要求在四个原生 section 中重复出现，使得无法紧凑表述唯一已配置的响应检查。
- 应如何修改：删除原生 trace artifact 和依赖 trace 的条款；仅在该 case 特有的更强 OSRM 条件下保留 `network.har`。

## Case 152

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service，查询从 Schenley park 驾车到 Upitt 的最短旅行时间，task type 为 `RETRIEVE`。答案须仅以 `HH:MM:SS` 字符串返回，不得附加其他细节。

### Benchmark 怎么测

唯一配置的是 `AgentResponseEvaluator`，它从最终响应提取可解析结构，只规范化并比较稀疏 expected 明确给出的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data=["4min"]`；`performed_operation` 可替代 legacy `task_type`。`retrieved_data` 使用 duration string array schema 和 `ordered=false`，因此规范化结果必须在忽略顺序时仍与单项 `4min` 的值及基数精确一致；未明确配置的原始额外字段以及物化默认 `error_details:null` 不参与该比较。没有 network/last-event evaluator，`TaskEvalResult.score` 仅在唯一 evaluator 得分为 `1.0` 时为 `1.0`，响应驱动的错误或不匹配得到 `0.0`。

### 原本 draft 是什么

原 draft 声明 native success 要求唯一 `AgentResponseEvaluator` 无错误完成，并将响应规范化为 `RETRIEVE`、`SUCCESS` 和无序精确单项 `4min`，从而使 evaluator 与 `TaskEvalResult.score` 都为 `1.0`。它将 `agent_response.json` 和 `network.har` 均列为决定性 artifacts，并在 success 中要求两者及上下文均可评估。failure 包括响应或 HAR 解析、上下文、规范化或编排错误，以及响应结构、类型、状态、结果值或项数不匹配；undecided 是响应或 HAR 未留存、截断或无法关联至被评估 run。非空 stronger condition `hhmmss_format_fidelity` 要求值在词法上恰为 `00:04:00` 且无额外用户可见内容；`osrm_route_evidence` 要求 `network.har` 显示从 Schenley park 到 Upitt 的成功 OSRM driving-directions 请求，其响应支持所报最短时间。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_har_overclaim`
- 为什么修改：尽管不存在 `NetworkEventEvaluator`，原生规则仍将成功解析 HAR 和构建上下文添加为评分的先决条件。
- 应如何修改：将原生语义限定为唯一 `AgentResponseEvaluator` 的已发布解析、normalization、结构比较和任务级分数组合；不得将 HAR 处理设为原生谓词。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifact`
- 为什么修改：`network.har` 被错误地列为重建已配置原生检查所必需的证据。
- 应如何修改：仅保留完整且来源可归属的 `agent_response.json` 作为原生决定性证据。仅在单独的 OSRM 更强条件下保留 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har_contaminates_decision_rules`
- 为什么修改：`success_if`、`fail_if` 和 `undecided_if` 均允许由 HAR 的留存或解析决定原生结果。
- 应如何修改：围绕完整 agent response 重写决策规则：可重建的不匹配、无效响应或 evaluator 错误为 failure；只有响应证据丢失或来源证明失败才为 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_requirements`
- 为什么修改：不必要的原生 HAR artifact 及其重复的决策规则限定条件，使 checklist 的范围超出已配置的 case 语义。
- 应如何修改：移除原生 HAR 要求并精简原生规则，同时保留单独且明确更强的 OSRM trace 检查。

## Case 153

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service，查询从 REI 驾车到 CMU 的最短旅行时间，task type 为 `RETRIEVE`。答案须仅以 `HH:MM:SS` 字符串形式返回，不得包含额外细节。

### Benchmark 怎么测

仅有一个 `AgentResponseEvaluator`，它对最终响应进行解析和 duration 规范化，并比较稀疏配置中明确给出的 `task_type=RETRIEVE`、`status=SUCCESS` 与 `retrieved_data=["7min"]`。结果 schema 为 duration string array，`ordered=false` 表示忽略顺序但仍要求规范化后的值和基数精确匹配单项 `7min`；物化默认的 `error_details:null` 不参与明确字段比较。本 case 没有 network 或 last-event 检查；只有该 evaluator 得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`，不匹配或 evaluator、task orchestration error 均不成功。

### 原本 draft 是什么

原 draft 声明 benchmark success 是 `TaskEvalResult.score = 1.0`，要求唯一 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS` 和无序单项 duration `7min`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求 artifacts 可评估、响应无失败或错误 assertion。failure 包括响应不是可比较对象、比较字段或类型、状态不匹配、结果缺失、额外、为 null 或 duration 不符，以及响应规范化、trace 解析、evaluator 或编排错误；undecided 是响应或 trace 的留存不完整或损坏且没有官方 `TaskEvalResult`。非空 stronger condition `exact_hhmmss_value` 要求唯一值恰为字符串 `00:07:00` 且无解释 prose；`osrm_route_evidence` 要求 trace 显示从 REI 到 CMU 的成功 OSRM driving-directions 请求，并由路线结果支持提交的最短时间。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_trace_not_decisive`
- 为什么修改：尽管唯一已配置的 evaluator 读取 `agent_response_raw`，且未检查任何 trace 事件，`network.har` 仍被错误地指定为决定性原生 artifact。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅在其内容确实相关的 OSRM 更强条件下保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`native_rules_depend_on_irrelevant_trace`
- 为什么修改：尽管未配置 `NetworkEventEvaluator`，原生规则仍使 success、failure 和 undecided 结果取决于 trace 的解析或留存。
- 应如何修改：基于完整 agent response 和已发布的响应比较作出原生决策。将 undecided 限定为该响应证据的丢失、损坏或来源证明失败；完整但无效的响应和 evaluator 可见的不匹配仍为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal`
- 为什么修改：不必要的原生 trace artifact 和依赖 trace 的规则，使 checklist 比已配置的 case 语义所需的更庞大且可操作性更低。
- 应如何修改：用紧凑的仅响应表述替换原生证据和规则，同时仅将 `network.har` 保留为可选的更强 OSRM 条件的证据。

## Case 155

### 原本 case 是什么

原始任务是：在 `map` 站点使用 OSRM direction service，查询从 Animal Rescue League of Pittsburgh 到 Schenley park 的最短驾车时间。task type 为 `RETRIEVE`，并要求只以 `HH:MM:SS` 字符串返回结果，不附加其他内容。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查最终响应中显式配置的 `task_type=RETRIEVE`、`status=SUCCESS`，以及 `retrieved_data` 是否为恰好一个元素且与期望 `9min` 匹配；`results_schema` 将元素规定为 `format=duration` 的字符串，因此比较前会做 duration normalization，且 `ordered=false` 表示忽略顺序。物化产生的 `error_details=null` 未在 sparse 配置中显式设置，因而不参与比较；本 case 没有网络事件 evaluator、事件 filter 或 last-event 判定，`network.har` 的内容也不由该 evaluator 核验。只有该 evaluator 得分为 `1.0` 时，按“all evaluator scores must equal 1.0”规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称，唯一的 `AgentResponseEvaluator` 必须得到 `1.0`，从而使 `TaskEvalResult.score` 为 `1.0`；响应需匹配 `RETRIEVE`、`SUCCESS`，并在 duration normalization 后以无序方式精确匹配单项 `9min`。它把 `official TaskEvalResult record` 和 `agent_response.json` 都列为决定性 artifacts；成功条件是所有比较通过且无 evaluator error，失败条件涵盖空、畸形、非对象、字段错误、数据缺失/多余/时长不符及 evaluator 或 orchestration error。它把既无可读 TaskEvalResult、又未保留完整最终响应的情形列为 `undecided`。非空 stronger conditions 有两项：`literal_hh_mm_ss_output` 要求数据值字面等于 `00:09:00` 且无额外说明；`osrm_route_evidence` 要求 `network.har` 证明成功的 OSRM 驾车路线请求、两个端点及其结果对返回时长的支持。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native-evidence-001`
- 为什么修改：原生决定性 artifact 列表添加了一条未明确说明的官方 `TaskEvalResult` 记录；该记录并非 packet 声明的留存运行 artifact，且与强制要求的完整 `agent_response.json` 重复。随后，undecided 规则又错误地允许该记录取代 `AgentResponseEvaluator` case 所需的完整响应证据。
- 应如何修改：从 `native decisive_artifacts` 中移除 `TaskEvalResult` 记录。保留完整的 `agent_response.json` 作为唯一最小原生 artifact，并使 undecided 取决于该响应的丢失、不完整、不可读、完整性失败或来源证明失败。仅为单独的更强 OSRM 条件保留 `network.har`。

## Case 164

### 原本 case 是什么

原始任务位于 `shopping` 站点，要求取得当前商品页面上所有评分为 2 星或以下的 review titles。task type 为 `RETRIEVE`，起始页面是 `__SHOPPING__/mineralogie-all-natural-lip-gloss-ruby-rose.html`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查最终响应中显式配置的 `task_type=RETRIEVE`、`status=SUCCESS` 和 `retrieved_data=["Meh"]`；`results_schema` 是字符串数组，比较要求归一化后恰好有这一项，且 `ordered=false` 表示忽略顺序。物化默认值 `error_details=null` 未在 sparse 配置中显式设置，因此不比较；没有 NetworkEventEvaluator、事件 filter 或 last-event 语义，网络内容不参与该响应比较。只有这个 evaluator 得分为 `1.0`，`TaskEvalResult.score` 才按全 evaluator 均须为 `1.0` 的规则取 `1.0`。

### 原本 draft 是什么

原始 draft 声称，最终响应经 released parsing 和 normalization 后必须精确得到 `task_type=RETRIEVE`、`status=SUCCESS` 和无序单项 `retrieved_data=["Meh"]`，使唯一 evaluator 与 `TaskEvalResult.score` 均为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace 可解析、evaluation context 可构造作为成功条件的一部分。其失败条件包括响应或 trace 无法解析、context/evaluator error、字段或结构不匹配，以及 `retrieved_data` 为 null、缺失、不同、重复或含额外项；缺少、截断或无法归属于该 run 的必要 artifact 且没有完整 TaskEvalResult 时被列为 `undecided`。非空 stronger condition `direct_public_response_schema_conformance` 要求原始最终响应直接符合 `FinalAgentResponse` JSON，`retrieved_data` 必须是字符串数组，不允许 code-block extraction 或 scalar-to-one-item coercion。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：尽管该 case 只有一个 `AgentResponseEvaluator`，`network.har` 却仅为了证实 trace 解析和上下文构建而被列为决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并将完整的 `agent_response.json` 用作已配置比较的最小充分留存证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_trace_based_decision_requirements`
- 为什么修改：这些规则将 trace 被接受设为 success 的必要条件，并将 trace 解析失败设为足以导致原生 failure 的条件，从而使运行后决策超出唯一已配置响应检查的范围。
- 应如何修改：基于对完整响应的已发布评估判定 success 和常规 failure，并将 undecided 限定为重建该比较所需的响应证据丢失。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_native_evidence_contract`
- 为什么修改：非决定性 trace artifact 和重复的 trace 编排条款，使 checklist 无法成为紧凑且特定于该 case 的证据合约。
- 应如何修改：删除特定于 network 的 artifact 和决策条款，同时保留响应比较、evaluator 错误处理和证据完整性规则。

## Case 166

### 原本 case 是什么

原始任务位于 `shopping` 站点，要求返回当前商品页面上所有评分为 2 星或以下的 review titles。task type 为 `RETRIEVE`，起始页面是 `__SHOPPING__/sensodyne-repair-protect-whitening-toothpaste-with-fluoride-3-4-oz-pack-of-3.html`。

### Benchmark 怎么测

配置中只有 `AgentResponseEvaluator`：它检查最终响应的显式字段是否归一化为 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR` 和 `retrieved_data=null`，其中 `results_schema` 为 `{"type":"null"}`，省略的 `retrieved_data` 也按 null 处理。物化的 `error_details=null` 并非 sparse 配置中的显式比较项；配置没有网络事件 evaluator、filter 或 last-event 判定。该 evaluator 必须得到 `1.0`，且无 evaluation error，`TaskEvalResult.score` 才能依据全 evaluator 均为 `1.0` 的组合规则得到 `1.0`。

### 原本 draft 是什么

原始 draft 声称，只要提交响应的比较字段归一化为 `RETRIEVE`、`NOT_FOUND_ERROR` 和 null `retrieved_data`，唯一 `AgentResponseEvaluator` 即得 `1.0`，进而使 `TaskEvalResult.score` 为 `1.0`；它还提到省略 `retrieved_data` 会被当作 null。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并询问 trace 是否可被 runner 解析，以及在 shopping URL 需要 fallback recovery 时能否取得可用 base URL。成功被定义为比较无失败 assertion，失败包括非 dict-like 响应、字段不符、非 null 数据、evaluator 或 orchestration error；无法确定实际响应或 evaluator 是否完成时列为 `undecided`。非空 stronger condition `verify_page_review_titles` 要求用 `network.har` 中完整的评分和标题证据核验真实的合格标题集合，只有集合为空时才允许 no-data/null，并用 `agent_response.json` 对照提交内容。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_network_trace`
- 为什么修改：对于唯一已配置 evaluator 仅比较 agent response 的 case，`network.har` 被错误地表述为决定性原生证据；所引用的 fallback 仅适用于环境 URL 无效或缺失的情况，而该 case 并未证实存在这种情况。
- 应如何修改：从 `native decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分原生 artifact。`network.har` 可以作为可能的页面证据，保留在单独的更强条件下。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_unknown_completion_rule`
- 为什么修改：undecided 规则将 evaluator 完成状态未知视为足以判定 undecided，尽管仅缺少 evaluator 输出留存，并不会妨碍根据完整且具有来源证明的提交重建已配置的响应比较。
- 应如何修改：将 undecided 限定为 `agent_response.json` 缺失、损坏、不完整或无来源证明，且因此无法进行重建的情况；明确完整但无效或不匹配的响应以及已知 evaluator 错误均为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_native_fallback_complexity`
- 为什么修改：原生 checklist 包含不必要的条件式 trace/configuration 机制以及相应的完成状态未知分支，降低了这个仅响应 case 的紧凑性和内部清晰度。
- 应如何修改：原生重建仅使用完整的已提交响应，并狭义定义基于证据的 undecided 结果。保留单独且明确为非原生的页面验证条件。

## Case 168

### 原本 case 是什么

原始任务位于 `gitlab` 站点，要求取得用户个人项目中 stars 超过 `100` 的 project ID(s)。task type 为 `RETRIEVE`，起始 URL 为 `__GITLAB__`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查最终响应中显式配置的 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR` 和 `retrieved_data=null`；`results_schema` 为 null，missing 或 empty `retrieved_data` 会归一化为 null。物化默认的 `error_details=null` 未在 sparse 配置中显式配置，故不计入比较；没有 NetworkEventEvaluator、事件 filter 或 last-event 语义。只有该 evaluator 得分为 `1.0`，`TaskEvalResult.score` 才按所有 evaluator 得分均须为 `1.0` 的规则得到 `1.0`。

### 原本 draft 是什么

原始 draft 声称，提交响应必须解析并归一化为 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR`、`retrieved_data=None`，使唯一 `AgentResponseEvaluator` 和 `TaskEvalResult` 均得到 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把 trace 可解析、evaluation-context 构造无错纳入成功判断。响应结构或值不符，以及 response/HAR parsing、context、orchestration 或 evaluator error，被列为失败；无法确认实际提交的 response、trace 或 evaluation 是否完成时列为 `undecided`。非空 stronger condition `corroborate_not_found_with_gitlab_state` 要求 `network.har` 包含成功且穷尽所有分页的已认证用户个人项目响应，并以项目 ID 和 star counts 证明没有项目超过 `100` stars。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_network_trace`
- 为什么修改：对于唯一已配置 evaluator 提取并比较 `agent_response_raw` 的 case，`network.har` 被错误地设为决定性原生 artifact。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并移除要求留存 trace 或 trace 可解析的原生规则。它可以继续作为明确的非原生更强条件的附加证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_and_overlapping_undecided_rule`
- 为什么修改：当前 undecided 规则将任何必需 artifact（包括 `network.har`）缺失视为 undecided，并可能与 `fail_if` 所涵盖的结论性响应不匹配发生冲突。
- 应如何修改：将原生 undecided 限定为确切已提交 agent response 的丢失、损坏或来源证明失败，且该丢失确实妨碍重建的情况；将每个完整但无效、为 `null`、不匹配或出现 response-evaluator-error 的输入分类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：不必要的原生 trace artifact 和依赖 trace 的规则增加了冗余证据要求，并造成 failure 与 undecided 结果不一致。
- 应如何修改：围绕完整的 `agent_response.json` 和唯一已发布的 `AgentResponseEvaluator` 比较精简原生 section，同时仅在更强条件下保留 `network.har`。

## Case 170

### 原本 case 是什么

原始任务位于 `gitlab` 站点，要求返回用户个人项目中 stars 最少者的 project IDs，包括并列最少的项目。task type 为 `RETRIEVE`，起始 URL 为 `__GITLAB__`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查最终响应的显式字段是否归一化为 `task_type=RETRIEVE`、`status=SUCCESS`，以及 `retrieved_data` 是否精确匹配无序数字多重集 `[193,190,189,188,184,181]`；`results_schema` 为 number array，`ordered=false` 表示忽略顺序，但缺失、额外或重复差异仍会失败。物化默认的 `error_details=null` 未在 sparse 配置中显式设置，因而不比较；没有 NetworkEventEvaluator、filter 或 last-event 判定。唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才依据全 evaluator 均为 `1.0` 的规则得到 `1.0`。

### 原本 draft 是什么

原始 draft 声称，响应经 parsing 和 normalization 后必须得到 `RETRIEVE`、`SUCCESS`，并精确匹配无序 numeric multiset `[193, 190, 189, 188, 184, 181]`，使唯一 `AgentResponseEvaluator` 与 `TaskEvalResult` 均得 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将 evaluation inputs 可解析及 HAR 可构造 `NetworkTrace` 纳入成功条件。失败条件包括响应结构、task type/status 或 normalization 错误，数据缺失、null、为空、含不同/额外/重复 ID，以及 HAR 或其他输入无效和 orchestration error；artifact 丢失、截断或事后损坏导致无法确认实际 response 或 trace 时列为 `undecided`。原始 draft 的 `stronger.additional_conditions` 为空，没有声明非空 stronger condition。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：对于唯一已配置 evaluator 比较 agent response 的 case，`network.har` 被错误地指定为决定性证据。
- 应如何修改：保留 `agent_response.json` 作为唯一决定性 artifact，并移除 HAR 问题；响应中的数值不依赖 trace 内容。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：原生 success、failure 和 undecided 规则错误地依赖 HAR 的解析或留存。
- 应如何修改：基于完整留存的 agent response 作出原生决策。将 undecided 限定为影响该响应的丢失、完整性失败或来源证明失败；将完整但无效或不匹配的响应以及 evaluator 计入的错误视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：额外的 HAR artifact 和相关规则使 checklist 不再最小化。
- 应如何修改：移除冗余的 HAR artifact 和所有依赖 HAR 的分支，同时保留 response evaluator 的确切已配置比较。

## Case 172

### 原本 case 是什么

原始任务是在 `gitlab` 站点检索用户个人项目中没有 stars 的项目，并返回其 project ID；task type 为 `RETRIEVE`。官方 instruction 是 `Get the project ID(s) of my personal project(s) that received no stars`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，它对最终响应进行提取、解析和归一化，并比较显式配置的 `task_type`、`status`、`retrieved_data`：分别应为 `RETRIEVE`、`SUCCESS` 和数值数组 `[193,190,189,188,184,181]`。`retrieved_data` 按 `results_schema` 的 number array 归一化，且 `ordered:false`，因此忽略顺序，但不得缺少、额外或错误重复项目；物化配置中的默认 `error_details:null` 不是显式比较字段。本任务没有 `NetworkEventEvaluator`，因而没有 URL filter 或 last-event 语义；唯一 evaluator 的分数必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明：唯一的 `AgentResponseEvaluator` 归一化得到 `task_type RETRIEVE`、`status SUCCESS`，且 `retrieved_data` 在无序数值比较下精确等于六个 ID `193`、`190`、`189`、`188`、`184`、`181` 时，benchmark success 和 `TaskEvalResult.score` 为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；无断言或错误且完全匹配判为 success，结构、类型、状态或数据不匹配以及 evaluator／编排错误判为 failure。它把仅有 artifact 缺失或不可访问列为 undecided，并明确将已保留的 null、空、畸形或不匹配响应判为 failure；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`incomplete_decisive_artifact_qualification`
- 为什么修改：唯一的决定性 artifact 名称正确，但其规则并未确立在将 `agent_response.json` 的内容视为本次运行响应之前，该文件是完整、完好且具有来源关联的。
- 应如何修改：仅当 `agent_response.json` 的完整、完好内容可归属于本 case 运行时，才将其认定为决定性 artifact；否则，将证据丢失归为 `undecided`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`missing_integrity_and_provenance_undecided_rule`
- 为什么修改：`undecided_if` 仅涵盖缺失或无法访问的情况，并会将已保留但被截断、损坏或来源不明确的 artifact 分类为 evaluator failure。
- 应如何修改：将导致无法重建的不完整、完整性丧失和来源信息丧失加入 `undecided_if`，同时对于完整、完好但确实为 `null`、空、格式错误或不匹配的响应，仍判定为 `failure`。

## Case 173

### 原本 case 是什么

原始任务是在 `gitlab` 站点找到用户标题含 `"better"` 的最近更新 issue，判断它是否 closed，并以布尔值返回：closed 为 `true`，opened 为 `false`；task type 为 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，比较显式配置的 `task_type`、`status`、`retrieved_data`；经响应提取、解析和归一化后，期望分别为 `RETRIEVE`、`SUCCESS`、`[false]`。`retrieved_data` 按 boolean array schema 归一化并以 `ordered:false` 无序精确比较，结果必须恰为单元素布尔数组 `[false]`；物化产生的 `error_details:null` 不参与显式比较。本任务没有 `NetworkEventEvaluator`，所以没有 URL filter 或 last-event 语义，也不通过网络内容核验“最近更新”或 issue 状态；唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，响应归一化后在 `task_type RETRIEVE`、`status SUCCESS` 和唯一布尔值 `false` 上匹配，唯一 `AgentResponseEvaluator` 得 `1.0`，从而 benchmark success 即 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把响应匹配及 trace 可解析、evaluator setup 完成写入 success，把响应断言／错误或 required trace 缺失、不可读、无效导致的编排错误写入 failure；响应或 trace 未保留、被截断或无法确认 provenance 时为 undecided。非空 stronger condition `corroborate_latest_issue_state` 另要求 `network.har` 证明用户 issue scope 中标题含 `better` 的最近更新 issue 实际为 open，以弥补原生 evaluator 只检查回答值、不核验 GitLab 证据的缺口。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_trace_not_configured_check`
- 为什么修改：原生规则将网络 trace 解析和配置设置提升为无条件的语义要求，尽管唯一配置的 evaluator 是 `AgentResponseEvaluator`。
- 应如何修改：从原生 `success` 和 `failure` 中移除 `network.har` 解析、设置和 trace 缺陷条件；直接陈述稀疏字段响应比较，包括不比较具体化的默认 `error_details`。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifact`
- 为什么修改：在没有配置 `NetworkEventEvaluator`，也未证明其会影响单元素布尔响应比较的情况下，`network.har` 被列为原生决定性证据。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性证据。`network.har` 只能作为显式更强条件的证据保留。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_native_decisions`
- 为什么修改：对于仅配置响应检查的情形，决策规则使 trace 的保留或有效性能够独立决定原生 `success`、`failure` 或 `undecided`。
- 应如何修改：原生 `success` 和 `failure` 应基于对完整响应的已发布 evaluation，并将 `undecided` 限于该响应的丢失、截断或来源验证失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_clauses`
- 为什么修改：非决定性的 trace artifact 在决定性 artifacts 及全部三个决策规则分支中重复出现，使 checklist 不必要地扩张。
- 应如何修改：删除原生 trace artifact 及其关联的 `success`、`failure` 和 `undecided` 表述，同时仅在更强条件下保留 `network.har`。

## Case 174

### 原本 case 是什么

原始任务是在 `gitlab` 站点找到标题含 `"feature"` 的最近更新 issue，判断它是否 closed，并以布尔值返回：closed 为 `true`，opened 为 `false`；task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 提取并解析最终响应，归一化显式配置的 `task_type`、`status`、`retrieved_data`，期望值依次为 `RETRIEVE`、`SUCCESS`、`[false]`；适用时，released normalization 接受 `performed_operation` 作为 `task_type` 的 legacy alias。`retrieved_data` 使用 boolean array schema，并按 `ordered:false` 无序精确比较，必须恰好包含一个布尔值 `false`；默认物化的 `error_details:null` 不比较。没有 `NetworkEventEvaluator`，故没有 URL filter 或 last-event 语义；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 写为唯一 `AgentResponseEvaluator` 在无序布尔数组比较下接受 `task_type RETRIEVE`、`status SUCCESS`、`retrieved_data [false]`，从而 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并在 success 中要求字段匹配、单个 `false`、trace 与 evaluation context 被接受；响应结构或字段／数据不匹配，以及 trace parsing、context construction、evaluator execution 或 orchestration 错误均列为 failure。响应或 trace 缺失、截断、不可读或无法确认是实际送评 artifact，且没有已保留官方结果时列为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`network_trace_not_decisive`
- 为什么修改：`network.har` 被标记为决定性的，尽管唯一配置的检查是 `AgentResponseEvaluator`，且配置的单元素布尔比较与 trace 内容无关。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为重建已配置检查所需的最小充分保留证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_rules`
- 为什么修改：这些规则要求 trace 被接受才能判定 `success`，并允许缺失或无法读取的 trace 保留证据导致 `undecided`。
- 应如何修改：移除 trace 特有的 `success`、`failure` 和 `undecided` 条款。基于完整响应进行重建；将完整但无效、为 `null`、不匹配或引发 evaluator error 的响应分类为 `failure`，并仅将响应证据丢失或来源验证失败归为 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_branches`
- 为什么修改：额外的 HAR artifact 和重复的 trace 分支对于陈述或重建此 case 配置的原生比较并非必要。
- 应如何修改：将 checklist 精简为唯一的响应 evaluator、其三个显式配置的字段、布尔数组 normalization、无序精确比较以及任务级 score 组合。

## Case 175

### 原本 case 是什么

原始任务是在 `gitlab` 站点找到用户标题含 `"dependency"` 的最近更新 issue，判断它是否 closed，并以布尔值返回：closed 为 `true`，opened 为 `false`；task type 为 `RETRIEVE`。

### Benchmark 怎么测

仅有一个 `AgentResponseEvaluator`：它提取、解析和归一化显式配置的 `task_type`、`status`、`retrieved_data`，并要求它们分别匹配 `RETRIEVE`、`SUCCESS`、`[false]`。数据按 boolean array schema 归一化，以 `ordered:false` 做无序精确数组比较；物化默认值 `error_details:null` 不是显式比较字段。本任务未配置 `NetworkEventEvaluator`，因此没有 URL filter 或 last-event 语义，网络 trace 内容也不参与该布尔响应比较；唯一 evaluator 得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，响应解析并归一化为 `task_type RETRIEVE`、`status SUCCESS`、`retrieved_data [false]` 后，唯一 `AgentResponseEvaluator` 得 `1.0`，benchmark success 即 `TaskEvalResult.score = 1.0`。它将 `agent_response.json` 和 `network.har` 都列作决定性 artifacts，并称 required inputs 可加载且响应匹配时 success；响应不可解析或字段、key set、数据不匹配，以及 required input、trace、配置、evaluator 或编排错误时 failure。保留的响应或 trace 缺失或不足以重建 evaluator inputs，且没有 `TaskEvalResult` 时为 undecided，但已记录的运行时输入缺失或无效属于 failure；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：原生规则将 `network.har` 加载和环境 fallback 视为已配置且与 score 相关的 predicate 的一部分，尽管此 case 仅配置了 `AgentResponseEvaluator` 并比较布尔响应数据。
- 应如何修改：将原生 predicate 限于对稀疏配置的 `task_type`、`status` 和 `retrieved_data` 字段进行已发布的解析、normalization 和比较；移除基于 trace 的原生前置条件和 failure。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`BF-2`
- 为什么修改：`network.har` 被列为决定性的，尽管不存在 `NetworkEventEvaluator`，且 checklist 已确认不会比较其中的 issue 内容。
- 应如何修改：仅保留完整的 `agent_response.json`，作为重建已配置检查的最小决定性 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`BF-3`
- 为什么修改：`success`、`failure` 和 `undecided` 规则不必要地依赖 trace 的可用性、解析或保留。
- 应如何修改：基于完整响应和唯一的 `AgentResponseEvaluator` 结果判定 `success` 与 `failure`；将 `undecided` 限于响应证据的完整性、保留或来源信息丧失。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-4`
- 为什么修改：非决定性的 trace 条件在多个原生章节中重复出现，使 checklist 实质上不够精简。
- 应如何修改：移除网络 artifact 和所有 trace 特有的分支，同时保留响应比较和任务级全 evaluator 组合。

## Case 176

### 原本 case 是什么

原始任务是在 `gitlab` 站点找到用户标题含 `"theme editor"` 的最近更新 issue，判断它是否 closed，并以布尔值返回：closed 为 `true`，opened 为 `false`；task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 从最终响应中提取并解析 mapping，比较显式配置的 `task_type`、`status`、`retrieved_data`；期望为 `RETRIEVE`、`SUCCESS`、`[false]`，且 released normalization 可接受 `performed_operation` 作为 `task_type` 的 legacy input key。`retrieved_data` 按 boolean array schema 归一化，并以 `ordered:false` 无序精确比较为单元素 `[false]`；`error_details:null` 只是物化默认值，不是显式比较字段。没有 `NetworkEventEvaluator`，所以不存在 URL filter 或 last-event 语义；唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，提取出的响应归一化为 `task_type RETRIEVE`、`status SUCCESS` 且无序布尔 `retrieved_data` 等于 `[false]` 时，唯一 `AgentResponseEvaluator` 得 `1.0`，benchmark success 即 `TaskEvalResult.score = 1.0`。它仅列 `agent_response.json` 为决定性 artifact；无断言或错误且字段匹配为 success，响应不可解析、`task_type`／`status` 缺失或不匹配、数据缺失／无效／不等于单个 `false`，以及 evaluator 或编排错误为 failure，artifact 遗漏或截断而无法重建提交内容为 undecided。非空 stronger condition `public_response_schema_conformance` 进一步要求原始提交符合 `FinalAgentResponse`，即 `retrieved_data` 必须编码为 JSON 数组 `[false]` 而非标量 `false`；其理由是原生非严格归一化可把标量包装成单元素 tuple。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`native_goal_ownership_scope`
- 为什么修改：用户目标遗漏了“my”，因而未能保留官方的 issue 选择范围。
- 应如何修改：明确目标是请求者自己的、标题中含有字符串字面量“theme editor”的最近更新 issue。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias`
- 为什么修改：原生规则未保留已发布 evaluator 在 `task_type` 缺失时接受 `performed_operation` 的行为。
- 应如何修改：将任务类型检查表述为：当 `task_type` 或旧版输入 key `performed_operation` normalization 后为 `RETRIEVE` 时予以接受。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_missing_task_type_failure`
- 为什么修改：`fail_if` 错误地将所有缺失 `task_type` 字段的情况声明为 `failure`，其中包括 evaluator 会接受其 `performed_operation` 别名的响应。
- 应如何修改：仅当 `task_type` 和 `performed_operation` 均未提供 normalization 后为 `RETRIEVE` 的值时，才声明为 `failure`。

## Case 179

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：找到用户最新创建且标题包含 `feature` 的 issue，判断它是否已关闭，并按“关闭为 `true`、打开为 `false`”返回布尔值。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它解析并规范化最终响应，比较显式字段 `task_type`、`status` 和 `retrieved_data`；期望分别为 `RETRIEVE`、`SUCCESS` 和 `[true]`，其中结果 schema 是布尔数组。`ordered:false` 表示数组采用无序精确比较，仍要求恰好一个布尔值 `true`；物化出的 `error_details:null` 不是显式配置的比较字段。本 case 没有 `NetworkEventEvaluator`，因此没有网络事件 filter 或 last-event 语义。所有 evaluator 分数都必须等于 `1.0`；这里只有一个 evaluator，所以其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是最终响应规范化为 `task_type RETRIEVE`、`status SUCCESS`、`retrieved_data` 精确为 `[true]`，使唯一的 `AgentResponseEvaluator` 及 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，分别用于重建响应比较和确认 HAR 可作为 `NetworkTrace` 解析。其 success 条件要求输入可解析且比较无断言，failure 条件涵盖空或非对象响应、规范化失败、字段不匹配、缺失/null/false/额外数据，以及输入解析或编排错误；artifact 缺失或截断则记为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_har`
- 为什么修改：`network.har` 被列为决定性的，尽管唯一配置的 evaluator 是 `AgentResponseEvaluator`，且没有任何已配置检查会检查网络事件。
- 应如何修改：此 case 的原生决定性证据仅保留完整的 `agent_response.json`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`scope_rules_to_response_evidence`
- 为什么修改：尽管批处理所需 HAR 的内容不会影响此处配置的响应比较，这些规则仍使其解析或保留与 `success`、`failure` 或 `undecided` 相关。
- 应如何修改：原生 `success` 和 `failure` 应基于对完整最终响应的已发布解析、normalization 和比较；仅将该响应证据的丢失、截断、完整性失败或来源验证失败归为 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_case_shape`
- 为什么修改：HAR 特有的证据和分支使 checklist 超出了对此 case 配置语义的最小充分表述。
- 应如何修改：移除 HAR artifact 以及所有 HAR/输入设置决策分支，同时保留将响应 evaluator error 和不匹配判定为 `failure` 的规则。

## Case 180

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：找到用户最新创建且标题包含 `dependency` 的 issue，判断它是否已关闭，并按“关闭为 `true`、打开为 `false`”返回布尔值。任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 解析、规范化并结构化比较最终响应，显式期望为 `task_type RETRIEVE`、`status SUCCESS` 和 `retrieved_data [false]`；结果 schema 是布尔数组。`ordered:false` 要求按无序方式精确匹配数组，因此规范化结果必须恰好包含一个 `false`，不能缺失、为 null 或含额外元素；物化默认值 `error_details:null` 不属于显式比较字段。没有配置网络事件 evaluator、filter 或 last-event 检查。任务采用全 evaluator 合取：唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明最终响应必须规范化为 `RETRIEVE`、`SUCCESS` 和恰好 `[false]`，使唯一的 `AgentResponseEvaluator` 与总体 `TaskEvalResult.score` 都为 `1.0`。它将 `agent_response.json` 和 `Official TaskEvalResult` 列为决定性 artifacts；success 覆盖响应结构及布尔数组的无序精确匹配，failure 覆盖解析、规范化或 evaluator 错误、非 mapping、字段不匹配，以及缺失、null、错误基数或额外的 `retrieved_data`。当既没有可读响应也没有官方 evaluator 结果可供重建时，draft 将结论标为 undecided。非空 stronger condition `gitlab_state_corroboration` 还要求从 `network.har` 独立识别最新的 `dependency` issue，并证明其状态为 `opened`，以佐证返回的 `false`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_uncontracted_native_artifact`
- 为什么修改：原生决定性 artifact 列表在 `agent_response.json` 之外添加了字符串字面量 "Official TaskEvalResult"，尽管该 packet 声明的保留运行 artifacts 仅有 `agent_response.json` 和 `network.har`，且唯一配置的检查可仅从响应重建。
- 应如何修改：从原生 `decisive_artifacts` 中移除字符串字面量 "Official TaskEvalResult"，并直接根据 `agent_response.json` 缺失、不可读、不完整或来源无效来定义原生 `undecided` 状态。仅在有效的更强佐证条件下保留 `network.har`。

## Case 181

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：找到用户最新创建且标题包含 `theme editor` 的 issue，判断它是否已关闭，并按“关闭为 `true`、打开为 `false`”返回布尔值。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，显式比较规范化后的 `task_type RETRIEVE`、`status SUCCESS` 和 `retrieved_data [false]`；结果 schema 为布尔数组，`ordered:false` 表示无序精确数组比较。已完成的源码口径 review 说明，当 `task_type` 缺失时，规范化可使用 `performed_operation` 作为旧版别名；物化默认值 `error_details:null` 不参与显式比较。没有 `NetworkEventEvaluator`，所以没有网络 filter 或 last-event 语义。唯一 evaluator 必须得 `1.0`，任务的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明只有当响应规范化为 `task_type RETRIEVE`、`status SUCCESS` 和精确 `[false]` 时，唯一 evaluator 与 `TaskEvalResult` 才成功并得 `1.0`；它还明确写道未配置 `NetworkEventEvaluator`。不过 draft 同时把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 HAR 可解析及运行输入可加载纳入 success，把 HAR 加载失败或编排错误纳入 failure。响应非对象、`task_type`/`status` 缺失或不匹配、`retrieved_data` 缺失、null、为 true 或含额外值也被列为 failure；响应或 trace 未保留且无官方结果时为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：第一个 `fail_if` 可能会将没有字面 `task_type` key 的响应分类为 `failure`，尽管在 `task_type` 缺失时，`performed_operation` 会被接受为旧版别名。
- 应如何修改：根据 normalization 后的 `task_type` 表述该规则，并明确将 `performed_operation` 识别为 fallback 别名。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`BF-2`
- 为什么修改：`network.har` 被称为决定性的，尽管唯一配置的 evaluator 比较的是 `agent_response.json`，并且不检查网络事件。
- 应如何修改：仅保留完整的 `agent_response.json`，作为此 case 最小的原生决定性 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`BF-3`
- 为什么修改：`success`、`failure` 和 `undecided` 规则不恰当地依赖 HAR 的加载或保留，且未明确考虑 `performed_operation` 别名。
- 应如何修改：移除 trace 特有的规则，识别旧版任务类型别名，将完整但无效或不匹配的响应及 evaluator error 判定为 `failure`，并仅将响应 artifact 的丢失或完整性/来源验证失败归为 `undecided`。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-4`
- 为什么修改：trace artifact 和三个依赖 trace 的决策条款向仅涉及响应的 checklist 添加了非决定性内容。
- 应如何修改：删除 `network.har` artifact 和依赖 trace 的条款，同时保留精确响应比较、evaluator error 处理以及响应证据的 `undecided` 边界。

## Case 183

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：给出库存恰好剩余 `10` 件的产品 SKU。任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对最终响应进行解析、字段规范化和结构比较，显式期望为 `task_type RETRIEVE`、`status NOT_FOUND_ERROR`、`retrieved_data null`，结果 schema 为 `{"type":"null"}`。源码口径 review 指出：缺失的 `retrieved_data` 会映射为 null，`task_type` 缺失时可采用 `performed_operation` 旧版别名，未配置的原始键被忽略；物化默认值 `error_details:null` 不比较，而 `ordered:false` 因未期待数组而无实际影响。没有网络事件 evaluator、filter 或 last-event 语义。唯一 evaluator 的分数必须为 `1.0`，总体 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，当最终响应规范化后结构匹配 `task_type RETRIEVE`、`status NOT_FOUND_ERROR` 和 `retrieved_data null` 时，唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求两个输入均被评估管线接受；其中 HAR 还被用于构造 `NetworkTrace` 及可能的 shopping-admin base URL fallback。draft 把非对象响应、缺失或错误的 `task_type`/`status`、非空 `retrieved_data`、额外规范化键和解析、上下文、编排或 evaluator 错误列为 failure；所需 artifact 丢失、不可读或无法关联到 evaluated run 且无官方结果时为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive-network-har`
- 为什么修改：`network.har` 被称为决定性的，尽管此 case 唯一配置的 evaluator 是 `AgentResponseEvaluator`，且其 case 特定比较可从完整的最终响应重建。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har-contaminates-decision-rules`
- 为什么修改：这些规则使原生 `success` 依赖两个批处理 artifacts，并将 `network.har` 缺失判定为 `undecided`，尽管 HAR 对已配置的响应比较并不具有决定性。
- 应如何修改：基于完整响应比较判定 `success`，将 `failure` 限于 evaluator 可见的完整响应中的不匹配或错误，并将 `undecided` 限于完整响应丢失或其完整性/来源信息丧失。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal-har-material`
- 为什么修改：HAR artifact 及其重复的 pipeline 条件添加了非决定性内容，并与 checklist 中除此以外仅涉及响应的 benchmark-success 表述相冲突。
- 应如何修改：删除 HAR 特有的 artifact 和规则表述，并保留不含运行结果或 metadata 的精简响应 evaluator checklist。

## Case 184

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：找出库存为 `0` 的产品，并以包含键 `"name"` 和 `"color"` 的对象列表返回其名称和颜色。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它解析并按 array-of-objects schema 规范化最终响应，显式期望 `task_type RETRIEVE`、`status SUCCESS`，以及 `retrieved_data` 为单元素对象数组，其中对象是 `{"color":"Blue","name":"Cronus Yoga Pant -33-Blue"}`。`ordered:false` 表示对数组做无序精确结构比较，不能出现缺失或额外元素或对象字段；`performed_operation` 可在需要时作为 `task_type` 的旧版字段，物化默认值 `error_details:null` 不比较。没有网络事件 evaluator、filter 或 last-event 语义。唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明，解析和 schema 规范化后的响应必须匹配 `RETRIEVE`、`SUCCESS` 以及无序单元素对象 `{"name":"Cronus Yoga Pant -33-Blue","color":"Blue"}`，从而使唯一 evaluator 和 `TaskEvalResult.score` 均为 `1.0`；其决定性 artifact 是 `agent_response.json`。完整响应若在结构、`task_type`、`status` 或 `retrieved_data` 上缺失、不同或多出内容，或引发 evaluator 错误，则被归为 failure；若响应字节因 artifact 缺失或保留损坏而无法重建，且没有真实的 released-evaluator `TaskEvalResult`，则为 undecided。非空 stronger condition `raw_retrieved_data_is_list` 要求原始 `retrieved_data` 本身必须是 JSON 对象数组，而不能是会被 evaluator 强制包装成单元素序列的裸对象或其他非列表值。该 stronger condition 同样以 `agent_response.json` 为决定性 artifact。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`undeclared_task_result_fallback`
- 为什么修改：`undecided_if` 依赖仍然存在的 `TaskEvalResult`，尽管只有 `agent_response.json` 被声明为决定性的，且该结果未必包含可重建的原始响应。
- 应如何修改：移除 `TaskEvalResult` fallback，并要求将完整、真实的 `agent_response.json` 作为原生证据，除非明确命名的等效项能够保证保留完整的已提交响应。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`non_exhaustive_missing_evidence_rule`
- 为什么修改：当响应不可用但 `TaskEvalResult` 仍然存在时，当前的决策分支未必有任何一个适用。
- 应如何修改：将 `agent_response.json` 缺失、不完整、损坏或来源不确定分类为 `undecided`；将完整但格式错误、为 `null` 或不匹配的响应继续判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`incoherent_artifact_reference`
- 为什么修改：`undecided` 规则引用了已声明决定性 artifact 集之外的 artifact，使 checklist 内部不一致。
- 应如何修改：在 `decisive_artifacts` 和所有决策规则中一致使用 `agent_response.json`，不保留未声明的 `TaskEvalResult` 例外。

## Case 185

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索库存恰好剩余 `3` 件的所有商品，并给出其 `material`；task type 为 `RETRIEVE`。官方指令是 `Give me the material of the products that have 3 units left`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查响应经解析和规范化后，显式配置的 `task_type`、`status`、`retrieved_data` 是否分别匹配 `RETRIEVE`、`SUCCESS` 和字符串数组 `['Cotton','Fleece']`。`results_schema` 是字符串数组，`ordered=false`，因此顺序不计，但值和重数必须完全一致，缺失、额外或重复元素均不匹配；稀疏配置未显式包含 `error_details`，所以物化出的 `error_details:null` 不参与比较。此 case 没有基于网络事件或 last-event 的 evaluator；`TaskEvalResult.score` 只有在唯一 evaluator 的分数等于 `1.0` 时才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`，要求唯一的 `AgentResponseEvaluator` 得到 `1.0`，并将决定性 artifacts 列为 `agent_response.json` 和 `network.har`：前者检查规范化后的 `RETRIEVE`、`SUCCESS` 及无序的 `Cotton`/`Fleece`，后者用于确认 trace 可解析并能构造评估上下文。其 success 条件还要求所需输入可读、评估无编排或 evaluator 错误且数据精确匹配；failure 包括输入或评估错误、响应结构或状态不匹配，以及 `retrieved_data` 缺失、为空或在值和数量上不同。undecided 被定义为 artifacts 缺失、截断或无法关联到该 run，且其余证据既无决定性不匹配也无官方分数。`stronger.additional_conditions` 为空；源码 review 指出 draft 错把 `network.har` 及其可读性设为该纯响应检查的决定性条件。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被指定为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且其与评分相关的比较由提交的响应决定。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并将完整的 `agent_response.json` 用作重建已配置检查所需的最小充分留存制品。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：即使完整的智能体响应足以判定唯一的 evaluator，success 和 undecided 规则仍使 trace 的可读性或留存情况影响判定。
- 应如何修改：移除依赖 trace 的 success 和 undecided 条件。仅在响应制品丢失或其完整性/来源存在问题时判为 undecided；完整但无效的响应、不匹配以及 evaluator 错误仍判为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：trace 制品和 evaluation-context 的衔接机制向原本紧凑的响应比较检查清单中加入了非决定性内容。
- 应如何修改：将原生证据和规则精简为围绕 `agent_response.json`、稀疏配置的三个字段、对 `retrieved_data` 的精确无序比较以及所有 evaluator 的组合。

## Case 188

### 原本 case 是什么

原始任务是在 `shopping` 站点取得最新一笔标记为 `"cancelled"` 的订单总价；task type 为 `RETRIEVE`。用户还要求只返回数字形式的值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：响应经提取、JSON 解析和规范化后，显式配置字段须匹配 `task_type=RETRIEVE`、`status=SUCCESS`，且 `retrieved_data` 在 `items.format='currency'`、`items.type='number'` 的数组 schema 下精确归一为 `[365.42]`。`ordered=false`，但这里只有单元素，任何缺失、错误或额外元素都不匹配；未显式配置的物化默认值 `error_details:null` 以及其他未配置原始键不参与比较。没有网络事件或 last-event evaluator，`TaskEvalResult.score` 仅在唯一 evaluator 得分为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明原生 benchmark success 是 `TaskEvalResult.score = 1.0`，即唯一 `AgentResponseEvaluator` 接受规范化的 `RETRIEVE`、`SUCCESS` 和无序单元素货币结果 `[365.42]`；它把 `agent_response.json` 与用于构造 `NetworkTrace` 的 `network.har` 都列为决定性 artifacts。success 要求 artifacts 形成有效评估上下文且响应字段精确匹配；failure 包括响应为空或非对象、字段缺失或不匹配、数据不可规范化或并非恰好 `[365.42]`，以及 evaluator/编排错误；undecided 是无法从保留证据确定提交响应或官方 `TaskEvalResult`。它还提出两个非空 stronger conditions：`shopping_state_grounding` 要求 `network.har` 证明 `365.42` 确为按时间最新的 cancelled 订单总价，`number_only_user_output` 要求原始用户可见输出只有 `365.42`，没有 prose、code fence 或额外细节。源码 review 认为这两个 stronger conditions 合理，但指出原生部分错误地把 `network.har` 作为决定性前提。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性原生证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并使完整的 `agent_response.json` 成为唯一的最小原生制品。HAR 可以保留，作为单独的 shopping-state 更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：原生 success 规则将有效的 HAR/evaluation context 作为前提条件，尽管无需 trace 内容即可重建响应比较。
- 应如何修改：基于已发布的解析、normalization 和对完整智能体响应的比较来判定 success 和 failure。将 undecided 限定为该响应的丢失、损坏、截断或来源不明确；完整但无效的响应仍判为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的原生 HAR 要求使检查清单不再最小化，并造成 `success_if` 与 `undecided_if` 之间的矛盾。
- 应如何修改：移除冗余的原生 trace 条件，并始终将 `agent_response.json` 表述为重建这个唯一 evaluator 结果所需的证据。

## Case 189

### 原本 case 是什么

原始任务是在 `shopping` 站点取得最新一笔标记为 `"pending"` 的订单总价；task type 为 `RETRIEVE`。用户要求只返回数字，例如 `10.99`，不能包含其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查 evaluator-visible 响应经解析和规范化后，显式字段是否为 `task_type=RETRIEVE`、`status=SUCCESS`，并使 `retrieved_data` 按 currency-number 数组 schema 精确归一为 `[754.99]`。比较设置为 `ordered=false`，不允许缺失、错误或额外元素；物化的 `error_details:null` 并非稀疏配置中的显式比较字段。没有网络事件或 last-event 语义；唯一 evaluator 必须得分 `1.0`，组合后的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明唯一 `AgentResponseEvaluator` 和整体 `TaskEvalResult` 均须得分 `1.0`，响应必须规范化为 `RETRIEVE`、`SUCCESS` 与无序货币数据 `[754.99]`；它列出的决定性 artifacts 是 `agent_response.json` 和泛称的 `retained TaskEvalResult`。success 要求规范化响应无缺失或额外数据且 evaluator 与总分均为 `1.0`；failure 包括无效响应、evaluator 错误、task type/status 不匹配或数据缺失、错误、额外；undecided 是既无可读响应也无保留的官方结果。非空 stronger condition `number_only_user_facing_answer` 要求保留的原始用户可见最终答案严格为裸数字 `754.99`，不得有 JSON wrapper 或其他文本。源码 review 认可这些判定语义和 stronger condition，但指出 draft 未要求 `agent_response.json` 完整且来源可信，并让非 packet 命名的 `retained TaskEvalResult` 替代了最小必要响应证据。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`required_agent_response_not_complete_or_minimal`
- 为什么修改：原生证据声明没有明确要求完整且来源有效的 `agent_response.json`，并允许留存的 `TaskEvalResult` 替代它。
- 应如何修改：将完整且完整性/来源有效的 `agent_response.json` 设为唯一的决定性原生制品；移除将留存的 `TaskEvalResult` 作为替代品的做法，并在响应留存缺失、不可读、不完整、已损坏或来源未经证明时判为 undecided，同时保持将完整但无效/null 的响应判为 failure。

## Case 191

### 原本 case 是什么

原始任务是在 `shopping` 站点查找并报告最新一笔标记为 `"processing"` 的订单总价；task type 为 `RETRIEVE`。指令没有规定特定的输出格式。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，其显式 expected 为 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR`、`retrieved_data=null`，`results_schema` 为 `{'type':'null'}`。响应可以是对象或可解析为 JSON 的字符串；规范化时若缺少 `task_type` 可使用 legacy alias `performed_operation`，缺失的 `retrieved_data` 按 `null` 处理，未配置键被忽略，而稀疏配置未包含的物化 `error_details:null` 不比较。`ordered=false` 在 null schema 下没有实际排序作用；没有网络事件或 last-event evaluator，且仅当该 evaluator 得分 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求唯一 `AgentResponseEvaluator` 得分 `1.0`，即解析和规范化后的响应匹配 `RETRIEVE`、`NOT_FOUND_ERROR` 与 null `retrieved_data`；它将 `agent_response.json` 和用于避免 trace 解析或编排错误的 `network.har` 都列为决定性 artifacts。success 允许以 `performed_operation` 作为 task type 的 legacy alias，并把缺失或规范化为 null 的 `retrieved_data` 视为匹配，同时要求 trace 可读；failure 包括非对象响应、task type/status 不匹配、非 null 数据及输入、evaluator 或编排错误；undecided 包括一个或两个 required artifacts 缺失、截断或无法归属于该 run。非空 stronger condition `corroborate_not_found_against_shopping_state` 要求 `network.har` 等购物证据确认不存在 processing 订单，以弥补响应 evaluator 不核验底层购物状态的问题。源码 review 认可该 stronger condition，但指出原生部分不应把 `network.har` 的可读性或留存设为 success、failure 或 undecided 的决定因素。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被表述为强制性的决定性证据，尽管没有配置 `NetworkEventEvaluator`，且 trace 内容无法改变对 null `retrieved_data` 的比较。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并将完整且可归属的 `agent_response.json` 用作最小原生证据集。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：这些规则要求 success 时 trace 可读，并在任一留存制品缺失时判为 undecided，尽管仅凭响应即可重建唯一配置的检查。它们也没有清晰区分完整响应内容无效与留存损坏。
- 应如何修改：删除原生 trace 要求；将完整但无效、为 null、不匹配或发生 normalization 错误的响应判为 failure，并仅在影响响应证据的丢失、截断、完整性失效或来源失效时判为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的 trace 制品及其相关规则使原生检查清单比已配置 case 的语义更长、范围更广。
- 应如何修改：移除原生 `network.har` 制品以及所有依赖 trace 的原生判定条款，同时保留有效的响应比较和更强的 shopping-state 条件。

## Case 192

### 原本 case 是什么

原始任务是在 `shopping` 站点取得最新一笔未被取消的订单总价；task type 为 `RETRIEVE`。用户要求只返回数字形式的值，例如 `10.99`，不得添加其他说明。

### Benchmark 怎么测

仅有一个 `AgentResponseEvaluator`，它对响应进行解析和 schema 规范化，并比较显式配置的 `task_type=RETRIEVE`、`status=SUCCESS` 及 `retrieved_data=[754.99]`。`retrieved_data` 使用 currency-number 数组 schema，`ordered=false`，所以按无序数组精确比较且不容许缺失或额外元素；物化但未显式配置的 `error_details:null` 不参与比较。不存在网络事件或 last-event evaluator；`TaskEvalResult.create` 只有在这个 evaluator 得分为 `1.0` 时才产生 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score = 1.0` 要求评估无错误且唯一 `AgentResponseEvaluator` 匹配规范化的 `RETRIEVE`、`SUCCESS` 与无序单元素货币数据 `[754.99]`；它将 `agent_response.json` 和用于构造评估上下文的 `network.har` 均列为决定性 artifacts。success 要求 response 和 trace 成功加载并完成比较；failure 包括响应不可比较、task type/status 不匹配、`retrieved_data` 缺失、null、无效、数值错误或数组元素有缺失/额外，以及 trace、输入、evaluator 或编排错误；undecided 包括保留记录遗漏或截断实际提交的响应或 HAR。非空 stronger condition `strict_raw_response_format` 要求原始响应本身是独立的 `FinalAgentResponse` JSON 对象、无 prose 或 code fence，并且 `retrieved_data` 严格表示为数值数组 `[754.99]`，以排除 evaluator 可接受的 fenced JSON 和标量到单元素数组的强制转换。源码 review 认可该 stronger condition，但指出原生 draft 错把 `network.har` 及其加载情况设为决定性条件。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管没有配置 `NetworkEventEvaluator`，且其内容无法改变已配置的货币响应比较。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并将完整的 `agent_response.json` 用作唯一的决定性留存制品。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision`
- 为什么修改：判定规则要求在 success 时加载 trace，并允许因留存的 HAR 丢失而判为 undecided，尽管响应制品足以重建已配置的检查。
- 应如何修改：从 `success_if` 和 `undecided_if` 中移除留存 trace 的要求；仅在完整的已提交智能体响应丢失、损坏或来源失效时判为 undecided。完整但无效的响应以及响应中可见的 evaluator 错误仍判为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：不必要的 HAR 制品以及重复的 trace 条款使原生检查清单的范围超出此 case 所需的最小证据。
- 应如何修改：删除非决定性的 HAR 条目和依赖 trace 的条款，同时保留唯一 evaluator 的解析、normalization、比较和 failure 语义。

## Case 193

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索最近 2 个已完成订单的付款总额，task type 为 `RETRIEVE`。回答必须只包含一个数值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

配置了唯一的 `AgentResponseEvaluator`：对响应进行 JSON/代码块提取与规范化后，比较显式配置的 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和 `[182.4]`。`retrieved_data` 使用元素 `format: currency` 的数组 schema，`ordered=false`，因此按货币规则规范化并作无序的精确单元素比较；物化得到的默认 `error_details:null` 不是显式配置的比较字段，其他未选中的原始字段也不参与比较。没有 `NetworkEventEvaluator` 或 last-event 条件；仅当该 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得分 `1.0`，即解析后的响应匹配 `RETRIEVE`、`SUCCESS` 和货币规范化后的无序单元素数组 `[182.4]`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并称后者需可解析为 `NetworkTrace`、足以完成评估上下文和环境验证；success 要求正式评估无错误且 evaluator 与任务均得 `1.0`，failure 包括解析、规范化、结构、类型、状态、数据值或额外值不匹配以及编排错误，undecided 则限于响应或上下文证据缺失、损坏且没有完整 `TaskEvalResult`。非空 stronger condition `number-only-presentation` 另行要求原始 `agent_response.json` 在必要响应封装之外只能呈现数值 `182.4`，不得有外围文字、代码围栏或无关详情字段。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：`network.har` 被标记为决定性证据，尽管没有配置 `NetworkEventEvaluator`，且其内容不影响此 case 的货币响应比较。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并仅基于完整留存的 `agent_response.json` 重建原生结果。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_native_evidence_set`
- 为什么修改：网络 trace 环境验证条目使检查清单不再最小化，并分散了对唯一已配置且 evaluator 可见证据的关注。
- 应如何修改：删除网络制品条目，并将 undecided 的措辞收窄为重建所需的留存响应证据发生丢失、损坏或来源失效。

## Case 194

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索最近 5 个已完成订单的付款总额，task type 为 `RETRIEVE`。回答必须只包含一个数值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

配置了唯一的 `AgentResponseEvaluator`，测量响应经提取和规范化后是否在三个显式字段上匹配 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: [555.2]`。`retrieved_data` 采用元素 `format: currency` 的数组 schema，并以 `ordered=false` 作货币规范化后的无序精确单元素比较；物化默认值 `error_details:null` 不属于显式评分字段。没有网络事件或 last-event evaluator；`TaskEvalResult.create` 要求所有 evaluator 得分均为 `1.0`，本 case 即要求唯一 evaluator 得分为 `1.0`。

### 原本 draft 是什么

原始 draft 声明任务当且仅当唯一的 `AgentResponseEvaluator` 得分 `1.0` 时成功：响应规范化为 `RETRIEVE`、`SUCCESS` 和货币等于 `555.2` 的无序单元素 `retrieved_data`，且 evaluator 或编排错误计 `0`。它把 `agent_response.json` 与 `network.har` 均列为决定性 artifacts，要求响应满足上述比较，并要求 HAR 可解析且足以完成评估上下文验证；success 还依赖响应和 trace 让正式评估完成，failure 包括响应不可解析、字段或数值不匹配以及响应/HAR/上下文/编排错误，undecided 包括必要留存证据缺失、不可读、截断或无法归属于该次运行且没有正式 `TaskEvalResult`。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`redundant_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的 evaluator 读取的是智能体响应，并且不存在参与评分的网络事件谓词。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并将完整的 `agent_response.json` 设为最小充分留存制品。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：对于这个仅依赖响应的 case，原生 success、failure 和 undecided 规则不当地取决于 HAR 的可用性或解析。
- 应如何修改：基于已发布的解析、normalization 和对完整响应的比较来作出原生判定；仅在响应证据丢失并导致无法重建时判为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_material`
- 为什么修改：冗余的 HAR 制品及相关规则使检查清单比该 case 的决定性语义更长、范围更广。
- 应如何修改：删除 HAR 特有的制品和条件，同时保留精确的响应比较、组合、错误和证据完整性规则。

## Case 195

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点检索最近 5 个待处理订单的付款总额，task type 为 `RETRIEVE`。回答必须只包含一个数值，例如 `10.99`，不得附加任何说明。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 测量响应经提取、解析和规范化后，有效任务类型是否为 `RETRIEVE`、`status` 是否为 `SUCCESS`，以及 `retrieved_data` 是否为货币值 `885.4` 的精确无序单元素集合。有效任务类型优先取 `task_type`，仅当其缺失时可使用 `performed_operation`；标量 `retrieved_data` 会先被转换为单元素序列，再按元素 `format: currency` 的数组 schema 规范化，且 `ordered=false`。显式 expected 只包括 `task_type`、`status`、`retrieved_data`，物化默认的 `error_details:null` 不比较；没有 last-event 条件。所有 evaluator 得分必须等于 `1.0`，因此唯一 evaluator 得分为 `1.0` 时 `TaskEvalResult.score` 才成功。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 为 `1.0` 的条件是唯一的 `AgentResponseEvaluator` 得分 `1.0`：提交响应规范化为 `task_type: RETRIEVE`、`status: SUCCESS`，并且 `retrieved_data` 在货币规范化和无序比较下恰含一个 `885.4`，且无 evaluator 错误。它仅将 `agent_response.json` 列为决定性 artifact；success 要求该响应通过上述比较，failure 包括响应缺失、畸形或非对象、`task_type`/`status` 缺失或不匹配、数据缺失或不等于单元素集合 `{885.4}`，以及 evaluator 错误，undecided 仅指确切提交响应缺失、截断、损坏或无法重建。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias_omitted`
- 为什么修改：检查清单称缺少 `task_type` 属于原生 failure，但已发布的 evaluator 会在 `task_type` 缺失时使用 `performed_operation` 作为旧版回退字段。
- 应如何修改：说明仅当 `task_type` 缺失时，有效任务类型才可来自 `performed_operation`，并判断该有效值经 normalization 后是否为 `RETRIEVE`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`failure_rule_overclaims_literal_key_requirement`
- 为什么修改：当前的 `fail_if` 将缺少字面量 `task_type` key 视为足以判定 failure，这会错误拒绝使用受支持别名、但其他方面均匹配的响应。
- 应如何修改：重写 `fail_if`：当 `task_type` 及适用的 `performed_operation` 回退字段均未提供所需的 normalization 后任务类型，或所选值不匹配时，才判为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantic_edge_not_preserved`
- 为什么修改：尽管形态和紧凑性在其他方面均合理，该检查清单遗漏了一条与评分相关的解析规则，因此尚未成为完整的最小语义陈述。
- 应如何修改：将旧版别名行为加入操作性的 success 和 failure 措辞中，且不要添加运行结果或不必要的制品。

## Case 198

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最近一个已取消订单的客户邮箱，task type 为 `RETRIEVE`。任务未规定额外的返回格式。

### Benchmark 怎么测

配置了唯一的 `AgentResponseEvaluator`，测量响应经解析和规范化后是否匹配显式 expected：`task_type: RETRIEVE`、`status: SUCCESS`、`retrieved_data: ["harrypotterfan1@gmail.com"]`。`retrieved_data` 使用字符串数组 schema，并以 `ordered=false` 作无序精确单元素比较；物化默认的 `error_details:null` 不属于显式比较字段。没有 `NetworkEventEvaluator` 或 last-event 条件；仅当唯一 evaluator 得分为 `1.0` 时，要求所有 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 为 `1.0`，是因为唯一的 `AgentResponseEvaluator` 在响应规范化为 `RETRIEVE`、`SUCCESS` 和无序数组 `["harrypotterfan1@gmail.com"]` 后得分 `1.0`。它把 `agent_response.json` 与 `network.har` 均列为决定性 artifacts，分别要求响应匹配预期邮箱、HAR 可解析为构建评估上下文所需的 `NetworkTrace`；success 要求无解析、规范化或编排错误，failure 包括响应非字典、字段或邮箱数组缺失/错误/有额外值，以及响应/HAR、evaluator 或编排错误，undecided 指没有完整 `TaskEvalResult` 且无法确定实际提供的完整响应和 HAR。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且已配置的 normalization 后电子邮件比较不使用网络事件。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_decision_rules`
- 为什么修改：failure 和 undecided 规则使 HAR 的解析或留存成为解决这个仅依赖响应的 case 所必需的条件。
- 应如何修改：移除依赖 HAR 的判定措辞。仅在 `agent_response.json` 丢失、截断、完整性失效或留存来源未经证明时判为 undecided；完整但无效或不匹配的响应以及 evaluator 错误仍判为 failure。

## Case 199

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最新待处理订单的订单 ID，task type 为 `RETRIEVE`。任务未规定额外的返回格式。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 测量完整响应经官方提取和规范化后，显式字段是否匹配 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: [299]`。提取可接受直接对象、包含 JSON 对象的字符串或 fenced JSON；任务类型还支持在 `task_type` 缺失时使用 `performed_operation`，而 `retrieved_data` 按数字数组 schema 规范化并以 `ordered=false` 作无序精确单元素比较。物化默认的 `error_details:null` 及其他未配置原始字段不比较，也没有 last-event 条件；唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明只有唯一的 `AgentResponseEvaluator` 得分 `1.0`，使 `TaskEvalResult.score` 为 `1.0`，case 才成功；它要求规范化响应匹配 `RETRIEVE`、`SUCCESS` 和无序单元素数值 `299`。它把 `agent_response.json` 与 `network.har` 均列为决定性 artifacts，要求前者满足响应比较，后者可解析为 `NetworkTrace` 并在需要时支持环境 URL 恢复；success 还要求无 evaluator 或编排错误，failure 包括所提供响应为非对象、字段或数据缺失/错误/有额外值，以及响应或 trace 解析、上下文验证和编排错误，undecided 包括 artifacts 缺失或截断而无法确定响应或 trace/context 是否完成。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`raw_response_parsing_overstatement`
- 为什么修改：“提供的非对象响应判为 failure”这一规则排除了可接受的 JSON 对象字符串表示和 fenced-code 表示。
- 应如何修改：说明应在应用 `AgentResponseEvaluator._get_actual_agent_response_dict` 后判定对象格式 failure，包括该方法对 JSON 字符串和 fenced-code 的提取行为。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管此 case 只有一个 `AgentResponseEvaluator`，且其检索值使用数值 schema。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`；保留完整的 `agent_response.json`，作为已配置比较所需的最小证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_failure_and_undecided_rules`
- 为什么修改：这些规则错误分类了可接受的原始响应编码，并在仅依赖响应的已配置检查中，将 trace/context 留存丢失判为 undecided。
- 应如何修改：将格式 failure 限定为在已发布的提取处理后仍失败，并将 `undecided_if` 限定为影响 `agent_response.json` 的丢失、截断、完整性或来源问题。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_plumbing_from_case_checklist`
- 为什么修改：trace 解析和环境恢复条款向此 case 的检查清单中加入了非决定性的运行时衔接机制和重复内容。
- 应如何修改：移除网络制品和 trace 特有的判定条款，同时保留针对已配置响应评估的 evaluator 错误判为 failure 的语义。

## Case 200

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最早的 complete 订单的 billing name，即“Get the billing name of the oldest complete order.”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查响应中显式配置的 `task_type`、`status` 和 `retrieved_data`：归一化后应分别为 `RETRIEVE`、`SUCCESS` 和字符串数组 `["John Lee"]`。`results_schema` 为字符串数组，`ordered` 默认为 `false`，因此 `retrieved_data` 按精确的无序多重集比较；缺少 `task_type` 时可由 `performed_operation` 别名提供，未配置的额外字段（包括 `error_details`）不参与比较。所有 evaluator 分数都必须等于 `1.0`；本例只有该 evaluator，所以它得 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得 `1.0`，即响应解析并归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素数组 `["John Lee"]`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace 可解析、可构造 evaluation context 也写入 success 条件；响应无效或字段不匹配、evaluator/orchestration 出错或任一分数低于 `1.0` 被列为 failure。若无法确定提交给 evaluator 的响应和 trace 且没有权威 `TaskEvalResult`，则标为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：尽管唯一配置的检查评估的是智能体响应，且预期检索到的字符串不包含依赖追踪的 URL 语义，network.har 仍被视为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整且关联来源的 agent_response.json 用作最小充分的原生证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_trace_from_decision_rules`
- 为什么修改：原生规则要求必须有追踪才能进行评估，并允许因未保留追踪而将结果判定为 undecided，从而强化了一个仅检查响应的已配置检查。
- 应如何修改：根据已发布的 AgentResponseEvaluator 比较判定 success 和 failure，并将 undecided 限定为重建该比较所需的已提交响应证据丢失、损坏或来源验证失败的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_case_shape`
- 为什么修改：不必要的追踪 artifact 和重复的追踪条件使检查清单不再最小化。
- 应如何修改：删除网络特定的 artifact 和规则，同时保留唯一 evaluator 的解析、显式字段 normalization、schema、无序比较、组合及 failure 语义。

## Case 201

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最早的 fraud suspect 订单所对应的 customer email，即“Get the customer email of the earliest fraud suspect order.”。task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查显式配置的 `task_type`、`status` 和 `retrieved_data`，归一化后的期望分别为 `RETRIEVE`、`NOT_FOUND_ERROR` 和 `null`；`results_schema` 为 `{"type":"null"}`，缺少 `retrieved_data` 也可归一化为 `null`。缺少 `task_type` 时可使用 `performed_operation` 别名，`error_details` 等未配置字段不参与比较；`ordered:false` 对这里的 null 值没有额外排序作用。所有 evaluator 分数必须等于 `1.0`，因此唯一的 `AgentResponseEvaluator` 得 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称唯一的 `AgentResponseEvaluator` 仅在响应归一化为 `RETRIEVE`、`NOT_FOUND_ERROR` 和无 retrieved data，并且没有 comparison assertion 或 evaluator error 时得 `1.0`；它还错误地要求 `error_details` 必须省略。它仅将 `agent_response.json` 列为 native 决定性 artifact；不可解析、非对象、字段缺失或不匹配、非 null 数据、出现 `error_details`，以及 assertion、evaluator/orchestration error 都被写为 failure，而 artifact 缺失、截断或不可读被写为 undecided。非空 stronger condition `corroborate_not_found` 要求用 `network.har` 中的 shopping-admin evidence 佐证不存在 fraud-suspect order，并声称若 trace 暴露此类订单则拒绝 native success。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unconfigured_error_details`
- 为什么修改：检查清单将 error_details 视为显式配置并参与比较的响应字段，尽管它只是 derived/task.json 中的一个实体化默认值。
- 应如何修改：以 derived/tag_task.json 为依据定义已配置字段的语义，并说明 error_details 和其他未配置的额外字段会被实际响应 normalization 忽略。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_error_details_decision`
- 为什么修改：success_if 要求 error_details 不存在，而 fail_if 错误地声称提供该字段会导致 key 不匹配或 evaluator 错误。
- 应如何修改：移除将省略 error_details 作为 success 要求的规定，并明确将未配置的额外字段排除在 failure 条件之外。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`stronger_native_contamination`
- 为什么修改：更强条件声称存在已有订单的证据会否决原生 success，从而用额外的证据检查干扰已发布的原生分数。
- 应如何修改：说明矛盾证据仅导致更强评估失败，而原生 success 仍由 AgentResponseEvaluator 决定；将保留证据无法得出结论的情况判定为更强评估的 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`internal_coherence`
- 为什么修改：不受支持的 error_details 约束在三个原生 section 中重复出现，且更强规则与原生评估和更强评估相分离的原则相矛盾。
- 应如何修改：准确整合已配置字段的比较，并使更强评估结果独立于原生评分。

## Case 203

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最近一笔 pending 订单的 purchase date 和 order id，并仅返回含 `purchase_date`（`YYYY-MM-DD`，不可用时为 null）与 `order_id` 的对象列表。task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查显式配置的 `task_type`、`status` 和 `retrieved_data`，期望为 `RETRIEVE`、`SUCCESS`，以及单元素数组 `[{"date":"May 31, 2023","order_id":"000000299"}]`。`results_schema` 将元素规范为只含 `date`（`format:"date"`）和 `order_id` 的对象；`ordered:false` 使数组按精确无序结构比较，缺少 `task_type` 时可接受 `performed_operation` 别名，未配置的顶层字段不参与比较。所有 evaluator 分数都必须等于 `1.0`；本例唯一 evaluator 得 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native success 要求唯一的 `AgentResponseEvaluator` 无 assertion、无 error 地匹配 `RETRIEVE`、`SUCCESS` 和无序单行 `date = May 31, 2023`、`order_id = 000000299`，使 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将 HAR 可解析及 orchestration/context 无错误写入 success；响应无效、字段或结构不匹配，以及 HAR/context、evaluator 或 orchestration error 被列为 failure，任一 artifact 缺失、截断或归属不明则列为 undecided。非空 stronger condition `task_requested_output_shape` 另行要求用户可见结果严格使用 `purchase_date = 2023-05-31` 和 `order_id = 000000299`，不得使用 evaluator 的 `date` 键，也不得有额外字段。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：尽管此 case 的 config 仅包含 AgentResponseEvaluator，且追踪不影响已配置的响应比较，network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整且来源可归属的 agent_response.json 用作最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_contaminates_decision_rules`
- 为什么修改：规则要求必须保留可解析的 HAR 才能判定 success，并将缺少 HAR 归类为 undecided，尽管缺少它并不会妨碍重建唯一配置的 evaluator 检查。
- 应如何修改：从重建规则中移除 HAR 保留和解析要求。将 undecided 限定为 agent_response.json 丢失、截断或来源不明确的情况；完整但无效或不匹配的响应，以及有证据表明发生 evaluator 错误的情况，仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：不必要的 HAR artifact 及其重复条件使检查清单不再最小化，并产生了虚假的证据依赖。
- 应如何修改：围绕唯一配置的 AgentResponseEvaluator 及其完整的 agent_response.json artifact 整合原生证据和规则，同时保留准确的组合与错误语义。

## Case 204

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取最近一笔 completed 订单中各产品的 name 和 final price，按价格从低到高排列，并仅返回含 `name` 和数值型 `price` 的对象列表。task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查显式配置的 `task_type`、`status` 和 `retrieved_data`，期望为 `RETRIEVE`、`SUCCESS`，以及有序数组 `[{"name":"Ida Workout Parachute Pant","price":38.4},{"name":"Proteus Fitness Jackshirt","price":45.0}]`。`results_schema` 将每项规范为含字符串 `name` 和 `format:"currency"` 数值 `price` 的对象；`ordered:true` 表示两项须按位置和结构精确比较，未配置的顶层字段（包括物化默认值 `error_details`）不参与比较。所有 evaluator 分数必须等于 `1.0`，所以该唯一 evaluator 得 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求无 evaluation error，且唯一的 `AgentResponseEvaluator` 在解析和 schema 归一化后按顺序精确匹配 `RETRIEVE`、`SUCCESS` 及上述两项 `name`/`price` 数组，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求响应与 trace 均可处理；artifact/context/evaluator/orchestration error 或响应在长度、顺序、键、名称、价格等方面不匹配被列为 failure，无法恢复官方结果或可重放的 response/HAR 对则标为 undecided。非空 stronger condition `standalone_json_without_surrounding_detail` 另行要求 raw response 本身是独立有效的 `FinalAgentResponse` JSON 对象，不得有 code fence、周围 prose 或 additional details。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_artifact`
- 为什么修改：network.har 被错误地指定为决定性原生证据，尽管唯一配置的 evaluator 使用 agent_response_raw，且不执行任何网络事件检查。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为重建已配置 evaluator 所需的最小充分保留 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：原生 success、failure 和 undecided 规则均以解析或保留响应与追踪的配对数据为前提，这可能导致即使响应证据完整且具有决定性，也无法作出判定。
- 应如何修改：根据对完整响应进行的官方解析、normalization 和比较判定原生 success 与 failure；仅在该响应丢失、损坏或来源不明确时判定为 undecided。将完整但格式错误、为 null 或不匹配的响应判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_checklist`
- 为什么修改：对于这个仅有一个响应 evaluator 的 case，冗余的 HAR 问题和依赖追踪的规则使原生检查清单不再最小化。
- 应如何修改：删除冗余的追踪内容，仅保留 case 204 所需的响应比较语义和证据。

## Case 205

### 原本 case 是什么

原始任务是在 `gitlab` 站点回答当前项目中 `kilian` 在 `March 5, 2023` 提交了多少个 commits。task type 为 `RETRIEVE`，起始项目为 `__GITLAB__/a11yproject/a11yproject.com`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查显式配置的 `task_type`、`status` 和 `retrieved_data`，归一化后的期望分别为 `RETRIEVE`、`SUCCESS` 和数值数组 `[1]`。`results_schema` 为 number array，`ordered:false`，所以 `retrieved_data` 按精确无序多重集比较；未配置的额外顶层字段不参与比较。所有 evaluator 分数必须等于 `1.0`，因此唯一 evaluator 得 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`SUCCESS` 和无序数值数组 `[1]` 并得 `1.0`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将 trace/context 可用和 evaluation 无 error 纳入 success；响应畸形或归一化后字段、数值、多重集不匹配，以及 trace/context/evaluator error 或非 `1.0` 分数被列为 failure。若响应缺失或无法解码，或 trace/configuration evidence 不足以重建有效 evaluation context 且没有官方 `TaskEvalResult`，则标为 undecided；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：network.har 仅因通用的解析/configuration 回退机制而被指定为决定性证据，尽管此 case 唯一配置的检查比较的是智能体响应，且该数据包并未确立依赖追踪的比较行为。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并移除依赖追踪的重建要求；保留完整的 agent_response.json 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`ambiguous_undecided_rule`
- 为什么修改：“无法解码响应”可能指完整但格式错误的响应，而检查清单同时也将这种响应归类为 failure；此外，重建这一仅检查响应的检查并不需要缺失的追踪/configuration 证据。
- 应如何修改：将 undecided 限定为响应保留记录缺失、不完整、损坏或来源不可靠，因而无法进行重建的情况，并说明完整但格式错误、为 null、无效或不匹配的响应属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_and_incoherent_rules`
- 为什么修改：额外的网络 artifact，以及对无法解码的响应与格式错误的响应所作的冲突处理，妨碍了紧凑且内部一致的证据审查。
- 应如何修改：原生重建仅使用 agent_response.json，并使 failure 与 undecided 的边界明确且互不重叠。

## Case 206

### 原本 case 是什么

原始任务是在 `gitlab` 站点的当前项目中，回答 Eric 在 2023 年 3 月 2 日提交了多少次 commit。该任务的 task type 是 `RETRIEVE`，起始页面为 `__GITLAB__/a11yproject/a11yproject.com`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`：它解析最终响应，并检查显式配置的 `task_type`、`status` 和 `retrieved_data`；`task_type` 可由兼容字段 `performed_operation` 提供，且须归一化为 `RETRIEVE`，`status` 须归一化为 `SUCCESS`。`retrieved_data` 按元素类型为 `number` 的数组 schema 归一化，并在 `ordered=false` 下与 `[2]` 作无序精确比较；物化配置中的 `error_details:null` 并非稀疏 expected 显式要求。未配置 filter、`NetworkEventEvaluator` 或 last-event 检查。仅当该唯一 evaluator 的分数等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得到 `1.0`：任务类型和状态归一化为 `RETRIEVE`、`SUCCESS`，数值数组按无序比较归一化为 `[2]`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求响应匹配上述字段，同时 HAR 可解析为 `NetworkTrace`、评估无错误。它将响应缺失、非对象、字段不匹配、解析或评估错误判为 failure；只有无法保留重建评估所需的 artifact 且没有官方 `TaskEvalResult` 时才判为 undecided，并强调实际评分时 artifact 缺失或畸形属于 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：对于仅配置了 AgentResponseEvaluator 的 case，network.har 被错误地指定为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 用作已配置比较所需的最小充分保留证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：failure 和 undecided 规则依赖追踪解析/保留，并引用了一个可选的官方 TaskEvalResult，但后者并未被列为决定性 artifact。
- 应如何修改：以完整的智能体响应为依据重建原生结果；将完整但为 null、格式错误、不匹配或导致 evaluator 错误的响应归类为 failure，并将 undecided 限定为 agent_response.json 丢失或完整性/来源验证失败的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：额外的 HAR artifact 及其通用 context/configuration 条件，使检查清单超出了针对该 case 的最小证据陈述范围。
- 应如何修改：删除 HAR artifact 和追踪特定条款，同时保留响应 parser、normalization、比较、错误及任务组合语义。

## Case 207

### 原本 case 是什么

原始任务是在 `gitlab` 站点的当前项目中，回答 Eric 和 Kilian 在 2023 年 1 月 3 日合计提交了多少次 commit。该任务的 task type 是 `RETRIEVE`，起始页面为 `__GITLAB__/a11yproject/a11yproject.com`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它对最终响应执行提取和归一化，并检查显式配置的 `task_type`、`status`、`retrieved_data`：任务类型可通过 `task_type` 或兼容字段 `performed_operation` 得到，目标为 `RETRIEVE`，状态目标为 `SUCCESS`。`retrieved_data` 使用元素类型为 `number` 的数组 schema，非列表值可被包成单元素序列，并在 `ordered=false` 下与 `[1]` 作无序精确比较；`error_details:null` 不是稀疏 expected 中的显式检查项，其他未配置顶层字段不参与比较。未配置 filter、网络事件或 last-event 语义。只有该 evaluator 得分为 `1.0` 且无 evaluator 或任务级错误时，全部 evaluator 均为 `1.0` 的组合规则才令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是评估无错误，且响应经提取和归一化后匹配 `task_type RETRIEVE`、`status SUCCESS` 和无序数值数组 `[1]`，使唯一的 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 都为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 还要求两者加载无编排错误，failure 包括响应或 HAR 缺失/不可读、字段或结构不匹配以及 evaluator 错误。它把无法确定实际提交的最终响应和 HAR、且没有保留官方 `TaskEvalResult` 的情形列为 undecided。非空 stronger condition `official_response_contract` 进一步要求 `agent_response.json` 可直接解析为 `FinalAgentResponse` JSON 对象、无需代码块提取，并且 `retrieved_data` 必须原生写成单元素数值数组 `[1]`，而不是依赖 evaluator 对标量的包装。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：network.har 被错误地指定为决定性证据，而此 case 唯一配置的 evaluator 检查的是智能体响应。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har。保留完整的 agent_response.json，作为重建已配置比较所需的最小充分运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：尽管不存在 NetworkEventEvaluator，规则仍将 HAR 加载和 HAR 来源验证作为判定 success 或能否作出判定的前提。
- 应如何修改：移除 HAR 特定的 success、failure 和 undecided 条件。以 agent_response.json 为依据进行重建；将 undecided 限定为该响应证据丢失、损坏或来源不明确的情况，而完整但无效或不匹配的响应仍属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：冗余的 HAR artifact 及相关规则使检查清单无法成为对已配置原生语义的紧凑陈述。
- 应如何修改：删除非决定性的 HAR 分支，并围绕唯一的 AgentResponseEvaluator 整合原生规则，不添加新的证据或检查。

## Case 209

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点查找电话号码为 `2137418080` 的客户，并返回其姓名和邮箱。输出被要求为对象列表，每个对象具有键 `"name"` 和 `"email"`；task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 解析并归一化最终响应，检查显式 expected 字段 `task_type`、`status` 和 `retrieved_data`：前两者须归一化为 `RETRIEVE` 和 `SUCCESS`。`retrieved_data` 采用对象数组 schema，每个对象的 `name`、`email` 均为字符串，并在 `ordered=false` 的递归无序结构比较下精确匹配单元素结果 `{"name":"Jennifer White","email":"jennifer.white@yahoo.com"}`；非列表值可被包装为单元素序列。物化出的 `error_details:null` 不属于稀疏 expected 的显式要求；未配置 filter、网络事件或 last-event 检查。全部 evaluator 分数必须等于 `1.0`，因此只有这个唯一 evaluator 得到 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 在解析、schema 归一化和无序结构比较后匹配 `"RETRIEVE"`、`"SUCCESS"` 及 Jennifer White 的姓名邮箱对象，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把完整输入无错误、HAR 可解析及响应完全匹配列为 success；任何解析、归一化、键、类型、状态、基数、姓名或邮箱不匹配以及编排错误均为 failure。若提交的最终响应或用于重建官方评估的可解析网络上下文缺失或不完整，则 draft 判为 undecided。非空 stronger condition `literal_list_of_objects_shape` 要求解码后的 `retrieved_data` 本身就是仅含一个 `{"name","email"}` 对象的 JSON 数组，而不是 evaluator 可强制转换的标量或 JSON 编码对象。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：network.har 被列为决定性 artifact，尽管唯一配置的 evaluator 是 AgentResponseEvaluator，且数据包中表示的 case 语义均未表明追踪内容会影响已配置的 name/email 比较。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 用作最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_loss_misclassified_as_undecided`
- 为什么修改：规则将网络 context 缺失或不完整的情况判定为 undecided，并隐式要求必须有该 context 才能判定 success，从而削弱了原本可重建的、仅检查响应的原生判定。
- 应如何修改：根据保留的完整智能体响应判定 success 和 failure，并将 undecided 限定为该响应 artifact 丢失、损坏、不完整或来源验证失败的情况。明确保留将完整但无效、为 null 或不匹配的响应判定为 failure 的规则。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`checklist_level_har_overreach`
- 为什么修改：非决定性的 HAR 条目及其下游规则文本使检查清单超出了这个仅有一个响应 evaluator 的 case 所需的范围。
- 应如何修改：删除 HAR 特定的原生 artifact 和判定语言，同时保留响应比较和独立的更强条件。

## Case 210

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点查找电话号码为 `2065555555` 的客户，并以对象列表返回其姓名和邮箱，每个对象具有 `"name"` 和 `"email"` 键。该任务的 task type 是 `RETRIEVE`。

### Benchmark 怎么测

配置了唯一的 `AgentResponseEvaluator`，它解析最终响应并只比较稀疏 expected 显式设置的 `task_type`、`status`、`retrieved_data`；若 `task_type` 不存在，可选择兼容字段 `performed_operation`，所选值须归一化为 `RETRIEVE`，状态须归一化为 `SUCCESS`。`retrieved_data` 按含字符串字段 `name`、`email` 的对象数组 schema 归一化，并在 `ordered=false` 下精确匹配单元素对象 `{"name":"Adam Garcia","email":"gamingpro456@gmail.com"}`；非列表值可被包装为单元素集合。`error_details` 等未配置顶层字段不参与比较，也没有 filter、网络事件或 last-event 规则。仅当该 evaluator 得分为 `1.0` 时，全部 evaluator 分数均为 `1.0` 的组合条件成立，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求响应解析为映射，归一化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 无序精确匹配 Adam Garcia 与 `gamingpro456@gmail.com` 的单元素对象集合，使唯一 evaluator 和任务分数均为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；匹配且无断言或错误为 success，响应为空、不可解析、类型或状态缺失/不匹配、结果缺失或多余以及解析、归一化或评估错误为 failure。这里原 draft 的 failure 文本把缺少 `task_type` 直接视为失败，没有写出 `performed_operation` fallback；无法重建实际提交响应时则为 undecided。非空 stronger condition `literal-retrieved-data-array` 要求原始 `retrieved_data` 必须是仅含一个、且恰有 `name` 和 `email` 键的对象的 JSON 数组，而非由 evaluator 强制转换的单对象或字符串。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy-task-type-semantics`
- 为什么修改：原生 failure 规则遗漏了已发布的 performed_operation 回退机制，因此会否决某些可被 evaluator 评为 success 的响应。
- 应如何修改：说明存在 task_type 时选择 task_type；仅当 task_type 不存在时，才接受 performed_operation 作为旧版回退字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`legacy-alias-decision-rule`
- 为什么修改：当前 fail_if 规则将缺少字面 key task_type 无条件视为 failure，这与 evaluator 的行为相悖。
- 应如何修改：重写 fail_if，使得只有 evaluator 选定的任务类型字段——存在 task_type 时为 task_type，否则为 performed_operation——缺失、无效或不匹配时才判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`preserve-alias-in-native-rules`
- 为什么修改：一项决定性的解析规则未在原生 success 和 failure 规则中得到一致体现。
- 应如何修改：将旧版别名选择规则简洁地添加到 benchmark_success、artifact 问题、success_if 和 fail_if 中，且不添加特定于运行的内容。

## Case 213

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取商品 `Antonia Racer Tank` 的所有三星或以下评价，并返回每条评价的标题和评分。输出须为对象列表，每个对象包含 `"title"` 和 `"rating"`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对最终响应执行提取与归一化，并检查稀疏 expected 中显式配置的 `task_type`、`status`、`retrieved_data`；任务类型可来自 `task_type` 或兼容字段 `performed_operation`，目标为 `RETRIEVE`，状态目标为 `SUCCESS`。`retrieved_data` 按含字符串字段 `title`、`rating` 的对象数组 schema 归一化，并在 `ordered=false` 下精确无序匹配两个对象：`{"title":"Zero support/modesty","rating":"2"}` 和 `{"title":"Not for high impact","rating":"3"}`，不得缺少、增加、重复或改变对象字段和值。未显式配置的 `error_details` 等字段被忽略，也没有 filter、网络事件或 last-event 规则。该 evaluator 必须无错误并得分 `1.0`，全部 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 等于 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得到 `1.0`：响应归一化为 `RETRIEVE`、`SUCCESS`，并无序精确匹配两个指定的标题/评分对象，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求 HAR 可解析；success 还声明响应应省略显式 `error_details`，failure 则把显式提供 `error_details` 导致错误或额外键不匹配、结果缺失或畸形、HAR 缺失或不可解析以及 evaluator 错误均包括在内。仅保留截图、文字摘要、局部片段或无归属文件，致使无法确定准确响应或 HAR 可解析性时，draft 判为 undecided。非空 stronger condition `strict_final_response_json` 要求原始最终响应本身就是符合 `FinalAgentResponse` 的 JSON 对象，而不是只能经 evaluator 提取后接受的 Markdown 或代码围栏文本。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incorrect_error_details_semantics`
- 为什么修改：原生规则声称提供 error_details 会导致额外 key 不匹配，尽管 error_details 并未在稀疏的预期响应中显式配置，且此 case 的实际 normalization 不会访问该字段。
- 应如何修改：说明只有显式配置的 task_type、status 和 retrieved_data 字段与评分相关，并移除省略 error_details 的要求及相关 failure 规则。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`non_decisive_har`
- 为什么修改：network.har 仅因属于批处理 artifact 契约而被视为决定性证据，尽管既不存在 NetworkEventEvaluator，也未证明存在依赖追踪的响应比较。
- 应如何修改：仅保留完整的 agent_response.json 作为原生决定性 artifact，并移除 HAR 问题。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_native_classification_rules`
- 为什么修改：规则将提供 error_details 归类为 failure，并将无法获取保留的 HAR 视为阻碍结果判定的情况，尽管二者均不影响此处已配置的响应比较。
- 应如何修改：将 failure 限定为应用已配置响应检查时出现的响应不匹配或 evaluator 错误，并将 undecided 限定为完整且来源可归属的智能体响应丢失或损坏的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：非决定性的 HAR artifact 和重复的 HAR 依赖条款，使这个仅有一个 evaluator 的检查清单不必要地扩大。
- 应如何修改：移除依赖 HAR 的 artifact 和判定条款，同时保留完整的响应比较及任务级组合。

## Case 215

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：找出 Circe ice fleece 的所有三星及以下评论，并以键为 `"title"` 和 `"rating"` 的对象列表返回。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，比较稀疏配置中的 `task_type`、`status` 和 `retrieved_data`；期望分别归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素集合 `[{"title":"Bad!","rating":"1"}]`，materialized 配置中的 `error_details:null` 不参与比较。`retrieved_data` 按 array-of-objects schema 归一化，其中 `title`、`rating` 均为字符串；比较为 `ordered:false` 的精确结构比较，不能缺少、增加或错配对象、键和值，且 released evaluator 会先把非 list/tuple 的 `retrieved_data` 包成单元素集合。此配置没有网络事件、filter 或 last-event evaluator；任务分数写入 `TaskEvalResult.score`，只有该唯一 evaluator 得分为 `1.0` 时任务分数才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误完成解析、单元素 coercion、schema normalization 和无序精确比较，得到 `task_type=RETRIEVE`、`status=SUCCESS`、`retrieved_data=[{"title":"Bad!","rating":"1"}]`，从而 `TaskEvalResult.score=1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并称前者决定响应比较、后者需能构造和验证 evaluation context，但 HAR 请求内容本身不接受答案检查。其 success 条件要求字段及无序集合完全匹配且唯一 evaluator 为 `1.0`；fail 条件涵盖 context/evaluator 错误、不可比较或字段不匹配，以及 retrieved data 缺失、为空、无法归一化或有任意差异；undecided 条件是 artifacts 缺失或截断，导致无法确定实际送入 evaluator 的响应或 context。非空 stronger condition `require_raw_retrieved_data_array` 额外要求原始 `agent_response.json` 中的 `retrieved_data` 在 coercion 前就是 JSON 对象数组，以排除 native evaluator 可接受裸对象的情形。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_network_har`
- 为什么修改：尽管唯一配置的 evaluator 仅比较 agent 响应，且不存在 NetworkEventEvaluator，但 network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并使用完整的 agent_response.json，作为已配置原生检查所需的最小充分运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_context_loss`
- 为什么修改：undecided 规则宽泛地提及无法确立所提供的评估上下文，使缺失或损坏的 HAR 证据尽管与此案例已配置的比较无关，仍可能阻止作出判定。
- 应如何修改：将 undecided_if 限制为导致无法确立实际 agent 响应的留存、完整性或来源信息丢失。明确说明：完整但格式错误的响应、完整的 null 响应或已发布 evaluator 可见的不匹配均为 failure。

## Case 217

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：取得 Pursuit Tone Band 的所有三星及以下评论标题和评分，并返回键为 `"title"`、`"rating"` 的对象列表。任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较 `task_type`、`status` 和 `retrieved_data`，期望归一化结果为 `RETRIEVE`、`SUCCESS`，以及两个对象 `[{"title":"Agreed. More resistance","rating":"3"},{"title":"Want more resistance","rating":"3"}]`；materialized 的 `error_details:null` 不属于稀疏配置的检查字段。结果 schema 是对象数组，`title` 和 `rating` 都必须按字符串归一化，并以 `ordered:false` 做无序精确比较，因此不得有缺失、额外或错配对象。没有配置 filter、网络事件或 last-event 语义；所有 evaluator 分数必须等于 `1.0`，而本任务只有这一个 evaluator，所以仅当其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明唯一 `AgentResponseEvaluator` 在响应归一化为 `RETRIEVE`、`SUCCESS` 和上述两个 title/rating 对象且无序精确匹配时得 `1.0`，进而 `TaskEvalResult.score=1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts：前者用于确认解析和比较，后者用于确认 trace 存在且可解析、evaluation context 可构造。success 条件要求两个对象无缺失或额外项、官方评估无错误且 evaluator/task 均为 `1.0`；fail 条件包括响应无效、字段或对象不匹配，以及 artifact 解析、context、编排或 evaluator 错误；undecided 条件是未保留实际提交的响应和 trace，且没有官方 `TaskEvalResult` 可确定结果。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_trace`
- 为什么修改：尽管唯一配置的检查是 AgentResponseEvaluator，且数据包所表示的案例特定 trace 内容均不影响对这些 title/rating 值的比较，但 network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并以完整且来源可证明的 agent_response.json 为基础重建原生 success。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：undecided 规则将响应和 trace 两者的留存都视为相关，从而使不必要的 trace 丢失也能阻碍作出判定。
- 应如何修改：将 undecided 限制为 agent_response.json 缺失、不完整、损坏或来源无法证明，且该问题确实导致无法比较响应的情形；完整但无效的响应、不匹配以及 evaluator 错误仍应视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_conditions`
- 为什么修改：有关 trace 存在、解析、上下文构建和 trace 留存的表述，在原本紧凑且仅涉及响应的检查清单中加入了非决定性条件。
- 应如何修改：删除 trace 特定的 artifact 和判定表述，同时保留已配置的响应比较、evaluator 错误即 failure 的规则，以及所有 evaluator 均等于 1.0 的组合规则。

## Case 219

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，查找步行至 Pittsburgh airport 最多需要 3 分钟的附近酒店，并用 `"hotel"` 表示名称、`"distance"` 表示距离。任务 revision 为 `2`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，其稀疏 expected 要求 `task_type` 归一化为 `RETRIEVE`、`status` 为 `NOT_FOUND_ERROR`、`retrieved_data` 为 `null`，结果 schema 也是 `{"type":"null"}`；materialized 的 `error_details:null` 不被检查，未配置的原始额外字段也不进入 evaluator 的归一化映射。该 evaluator 只解析、归一化并结构比较最终响应，没有配置用于核验 OSRM、网络事件、filter 或 last-event 的 evaluator。任务采用全 evaluator 合取，本例只有一个 evaluator，因此它必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native benchmark success 是最终响应精确归一化为 `task_type=RETRIEVE`、`status=NOT_FOUND_ERROR`、`retrieved_data=null`，唯一 `AgentResponseEvaluator` 得 `1.0`，继而 `TaskEvalResult.score=1.0`。它列出两个决定性 artifacts：`agent_response.json`，以及 `Serialized TaskEvalResult and AgentResponseEvaluator result`；后者用于查看 evaluator 是否无错误得 `1.0`、任务是否为 success 且得 `1.0`。success 条件要求无 assertion 或 evaluator error 且 evaluator/task 均为 `1.0`；fail 条件包括响应不可解析、任一归一化键值不匹配或 `retrieved_data` 非 null，以及官方结果出现非 `1.0` 分数或 failure/error；undecided 条件是既无可读最终响应，也无完整官方 evaluator/task result。非空 stronger condition `substantiate_not_found_with_osrm_evidence` 要求 `network.har` 证明 Pittsburgh-airport 酒店搜索中不存在 OSRM 步行时长不超过 `180` 秒的候选酒店。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`artifact_set_not_minimal`
- 为什么修改：检查清单同时列出了 agent_response.json 和序列化的 TaskEvalResult/evaluator 结果，尽管仅凭完整响应即可重建唯一配置的 AgentResponseEvaluator 检查。
- 应如何修改：从 decisive_artifacts 中移除序列化结果 artifact，并使原生证据边界依赖于留存完整的、经过评估的 agent_response.json。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_native_evidence`
- 为什么修改：冗余的序列化结果 artifact 及其替代证据表述，使该仅涉及响应的案例的检查清单不够紧凑。
- 应如何修改：仅使用一个原生决定性 artifact，即 agent_response.json，并将 network.har 仅用于明确更强的 OSRM 佐证条件。

## Case 223

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：从 CMU Pittsburgh 出发，使用 OSRM direction service 查询到最近 Mcdonald's 的不同交通方式所需时间，并以 `HH:MM:SS` 格式返回时长。任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较稀疏配置的 `task_type`、`status`、`retrieved_data`，期望归一化为 `RETRIEVE`、`SUCCESS` 和单元素集合 `["4min"]`；materialized 的 `error_details:null` 不参与检查。它可处理直接响应对象、原始文本解码出的 JSON 及 fenced JSON；缺少 `task_type` 时可接受 legacy 字段 `performed_operation`，并用 duration-array schema 归一化时长，以 `ordered:false` 对 retrieved data 做无序精确比较。没有网络、filter 或 last-event evaluator，因此不核验最近目的地、OSRM 使用情况或多种交通方式；只有该 evaluator 得 `1.0` 时，合取规则才使 `TaskEvalResult.score=1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是响应归一化为 `task_type=RETRIEVE`、`status=SUCCESS`，且无序单元素 `retrieved_data` 在 duration schema 下匹配 `4min`，唯一 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，前者检查响应，后者检查官方 evaluation context 能否构造，同时明确 route 内容不由唯一 evaluator 比较。success 条件要求三项归一化结果匹配且评估无错误；fail 条件包括响应不可比较、字段不同、retrieved data 缺失、为空、有额外或不匹配时长，以及输入、归一化或编排错误；undecided 条件是既缺少官方 `TaskEvalResult`，又没有足够的 `agent_response.json` 或 `network.har` 来重放检查。两个非空 stronger conditions 分别是 `multi_method_hhmmss`，要求至少两种交通方式且每个时长严格采用 `HH:MM:SS`；以及 `osrm_nearest_destination`，要求 `network.har` 显示从 CMU Pittsburgh 搜索最近 McDonald's，并针对所报告方式向该目的地发出 OSRM direction 请求。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_native_trace`
- 为什么修改：尽管唯一配置的 evaluator 仅比较最终响应，`network.har` 仍被列为原生决定性 artifact。
- 应如何修改：从原生决定性 artifacts 中移除 `network.har`。仅在 OSRM/最近目的地这一更强条件下保留它，因为其内容在该条件下确实相关。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`repair_undecided_evidence_rule`
- 为什么修改：undecided 规则暗示，只要 `agent_response.json` 或 `network.har` 任一者有足够内容即可重放官方检查，但 trace 无法重建所提交的响应。
- 应如何修改：使 undecided 仅取决于影响完整提交响应的留存、完整性或来源信息丢失。对于完整但无效的响应、完整的 null 响应以及 evaluator 错误，仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`make_native_body_minimal_and_coherent`
- 为什么修改：原生部分保留了不必要的 trace artifact，并对响应证据还是 trace 证据决定唯一 evaluator 的结果给出了相互矛盾的信号。
- 应如何修改：将 `agent_response.json` 用作唯一的原生决定性 artifact，并使 success、failure 和 undecided 规则与该证据边界保持一致。

## Case 227

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：确定 EYZUTAK 产品的价格范围，只返回含数字键值 `"min"` 和 `"max"` 的对象，不附加任何细节。任务 revision 为 `2`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 检查稀疏配置中的 `task_type`、`status`、`retrieved_data`，期望归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素集合 `[{"min":9.99,"max":9.99}]`；`performed_operation` 可作为缺失 `task_type` 时的 alias，而 materialized 的 `error_details:null` 及其他未配置原始字段不参与 native 比较。结果 schema 是对象数组，`min`、`max` 均为带 `currency` format 的 number，并按 `ordered:false` 进行无序精确结构比较。没有网络事件、filter 或 last-event evaluator；唯一 evaluator 必须得 `1.0`，全 evaluator 合取才使 `TaskEvalResult.score=1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是 released parsing 和 schema normalization 后得到 `task_type=RETRIEVE`、`status=SUCCESS` 及无序的 `[{"min":9.99,"max":9.99}]`，唯一 `AgentResponseEvaluator` 得 `1.0`，从而 `TaskEvalResult.score=1.0`。它将 `agent_response.json` 和 `network.har` 都视为决定性 artifacts，分别用于响应比较，以及确认 trace 可解析并可构造 evaluation context。success 条件要求 context 可评估、三个字段完全匹配且 evaluator/task 得 `1.0`；fail 条件涵盖响应无法解析或归一化、字段或 retrieved data 缺失/为空/额外/错配，以及 evaluator、编排错误或非 `1.0` 分数；undecided 条件包括响应丢失、不可读、截断或无法关联 task `227`，以及既无可用 trace、也无官方结果证明存在可评估 context。非空 stronger condition `raw_response_contains_only_requested_result` 额外要求 `agent_response.json` 是无外围 prose 或 code fence 的 bare JSON，没有被忽略的解释字段，并且除成功所需 protocol fields 外，retrieved result 仅含一个数值 `min`/`max` 对象。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：尽管唯一配置的 evaluator 读取 agent_response_raw，且未执行任何已配置的网络事件检查，但 network.har 仍被列为决定性证据并且必须可解析。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为重建此案例已配置比较所需的唯一原生留存 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_trace_undecided_rule`
- 为什么修改：当前 undecided 规则规定，缺少可用 trace 或官方结果可能使原生结果变为 undecided，尽管重建这唯一响应 evaluator 的已配置检查并不需要 trace 内容。
- 应如何修改：将 undecided_if 限制为 agent_response.json 缺失、不可读、被截断、损坏或无法归属。不得使 success 或可判定性取决于 network.har。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_language`
- 为什么修改：额外的 trace artifact 和可评估上下文表述使检查清单不够紧凑，并将批次留存 artifact 强加为案例决定性证据。
- 应如何修改：移除 trace artifact、其支持指针以及依赖 trace 的 success/undecided 表述，同时保留响应解析、normalization、精确比较、evaluator 错误和分数组合规则。

## Case 228

### 原本 case 是什么

原始任务是在 `shopping` 站点检索 Sephora 产品的价格范围，task type 为 `RETRIEVE`。用户要求只返回一个含数值键值 `"min"` 和 `"max"` 的对象，不附加任何其他细节。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`：它对稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data` 做解析、投影、schema normalization 与比较；期望分别归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素集合 `[{"min":18.18,"max":94.99}]`，其中 `min`、`max` 按 `currency` 数值格式归一化，非列表 `retrieved_data` 可先视为单元素集合。`ordered` 为 `false`，但集合长度、对象结构、键和值仍须精确匹配；物化产生的 `error_details:null` 因未在 sparse expected 中显式配置而不参与比较。未配置 filter、`NetworkEventEvaluator` 或 last-event 判定，`network.har` 的事件内容不参与这个响应比较。任务仅在该 evaluator 得分为 `1.0` 时令 `TaskEvalResult.score = 1.0`，解析、归一化、比较或 evaluator 错误均不能满足成功条件。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 `TaskEvalResult.score = 1.0`：唯一的 `AgentResponseEvaluator` 无错误地得到 `1.0`，并将响应归一化为 `RETRIEVE`、`SUCCESS` 及无序精确匹配 `[{"min":18.18,"max":94.99}]`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者被描述为必须可解析成 `NetworkTrace`，并在环境 URL fallback 时提供可用事件数据。其 success 条件要求完整匹配且评估无错误；failure 包括响应为空、不可解析、非对象、字段或结构和值不匹配，以及响应/HAR/上下文/编排错误；undecided 则用于响应或 trace 因留存丢失、截断而无法重建的情形。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_har`
- 为什么修改：对于唯一配置的检查为 AgentResponseEvaluator、且预期数据为货币数值的案例，network.har 被错误地指定为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并使用完整留存的 agent_response.json，作为已配置比较所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_marked_undecided`
- 为什么修改：undecided 规则规定 trace 留存丢失会阻止重建，尽管 trace 内容无法改变此案例已配置的响应比较。
- 应如何修改：将 undecided_if 限制为影响 agent_response.json 的丢失、截断、完整性故障或来源不确定性；移除 HAR 特定前提，同时保留以下 failure 情形：完整但无效或不匹配的响应，以及 evaluator 可见的错误。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`surplus_trace_conditions`
- 为什么修改：检查清单包含多余的 artifact 问题和 trace 特定的判定条件，这些内容源自批次留存契约，而非此案例已配置的检查。
- 应如何修改：围绕唯一的 AgentResponseEvaluator 和完整 agent 响应精简原生证据与规则。

## Case 229

### 原本 case 是什么

原始任务是在 `shopping` 站点检索 UGREEN 产品的价格范围，task type 为 `RETRIEVE`。用户要求只返回一个带数值 `"min"`、`"max"` 值的对象，不附加其他细节。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 比较 sparse expected 中的 `task_type`、`status`、`retrieved_data`：归一化期望为 `RETRIEVE`、`SUCCESS`，以及无序单元素集合 `[{"min":6.99,"max":38.99}]`；`min` 和 `max` 依据 `currency` schema 归一化。`ordered:false` 表示不要求集合顺序，但基数、对象键、结构和值必须匹配；物化默认值 `error_details:null` 不属于显式比较字段。没有配置 filter、网络事件 evaluator 或 last-event 语义。仅当这个 evaluator 无错误且得分 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 定义为唯一 `AgentResponseEvaluator` 无错误地取得 `1.0`，响应归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素结果 `{"min":6.99,"max":38.99}`，从而使 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求 HAR 可解析为构造 evaluation context 所需的 `NetworkTrace`。success 是在完整 artifacts 上重放官方评估且无断言或错误；failure 包括响应格式、task type、status、基数、对象键或数值不匹配，以及响应、trace、上下文、归一化或编排错误；undecided 是响应或 trace 不完整且没有真实官方结果可恢复结论。它还提出非空 stronger condition `exact_original_output_format`：原始用户可见答案必须恰为 `{"min": 6.99, "max": 38.99}`，不得有协议 wrapper、额外键或外围文本，并以 `agent_response.json` 为判定 artifact。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_har`
- 为什么修改：network.har 基于上下文构建和条件式环境回退而被列为原生决定性 artifact，而非基于此案例已配置的 AgentResponseEvaluator 比较。
- 应如何修改：从 native.decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为重建已配置检查所需的最小充分留存 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`narrow_undecided_rule`
- 为什么修改：当前 undecided 规则将响应或 trace 任一者的丢失都视为会阻止结果判定，尽管仅丢失 trace 并不会妨碍重建这唯一的响应检查。
- 应如何修改：将 undecided_if 限制为完整 agent 响应的丢失、损坏或来源信息故障，除非真实留存的官方评估证据能够独立确定结果。完整但无效或不匹配的响应仍应视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_native_checklist`
- 为什么修改：额外的 HAR artifact 和依赖 trace 的 undecided 条款使原生检查清单不再最小化。
- 应如何修改：仅使用响应证据进行已配置的原生比较，并移除对 trace 留存的依赖，同时不改变有效的更强条件。

## Case 230

### 原本 case 是什么

原始任务是在 `shopping` 站点检索 Perricone MD 产品的价格范围，task type 为 `RETRIEVE`。用户要求只返回一个含 `"min"` 和 `"max"` 键且对应值为数字的对象，不提供额外细节。

### Benchmark 怎么测

配置中唯一的 `AgentResponseEvaluator` 在解析和投影后比较显式字段 `task_type`、`status`、`retrieved_data`，期望归一化为 `RETRIEVE`、`SUCCESS` 和无序单元素集合 `[{"min":35.0,"max":149.0}]`；两个数值按 `currency` schema 归一化。`ordered:false` 只取消集合顺序要求，单元素基数、对象键、结构和数值仍须精确符合；物化的 `error_details:null` 未在 sparse expected 中显式出现，因而不比较。未配置 filter、网络事件检查或 last-event 语义。唯一 evaluator 必须无错误且得分 `1.0`，`TaskEvalResult.create` 才产生 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原始 draft 声明：解析、evaluator projection 和 normalization 后，`task_type`、`status` 与无序 `retrieved_data` 分别匹配 `RETRIEVE`、`SUCCESS` 和含 `min 35.0`、`max 149.0` 的单对象时，唯一 `AgentResponseEvaluator` 得分 `1.0`，继而 `TaskEvalResult.score = 1.0`。它仅将 `agent_response.json` 列为决定性 artifact；success 要求上述完整匹配且无断言或 evaluator 错误，failure 包括非对象、字段缺失或不匹配、空数据、结构/基数/键/数值错误以及 evaluator 或 task-evaluation error，证据缺失、截断或不能确定完整提交响应时为 undecided。原始 user goal 将 `"min"` 和 `"max"` 误写成“numeric keys”。非空 stronger condition `raw-response-obeys-no-extra-details` 进一步要求原始完整响应没有外围文字、代码围栏或被 projection 丢弃的字段，retrieved payload 只能是含数值 min/max 的一个对象，并由 `agent_response.json` 判定。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`native-goal-numeric-keys`
- 为什么修改：native.user_goal 称该对象具有数值键 "min" 和 "max"，但它们是具名字符串键；官方要求是它们的值必须为数值。
- 应如何修改：重写该目标，要求对象具有键 "min" 和 "max"，且其值为数字，不添加其他细节。

## Case 231

### 原本 case 是什么

原始任务是在 `shopping` 站点检索用户最近一笔已取消订单的订单号，task type 为 `RETRIEVE`。任务指令是 `Get the order number of my most recent cancelled order`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对显式配置的 `task_type`、`status` 和 `retrieved_data` 进行解析与归一化，期望为 `RETRIEVE`、`SUCCESS`，以及恰好一个符合正则 `^#?\s*0*170$` 的字符串项。结果 schema 是字符串数组且 `ordered:false`，因此顺序不计，但集合必须是单元素且该元素须匹配正则；物化默认的 `error_details:null` 不参与比较。没有配置 filter、`NetworkEventEvaluator` 或 last-event 判定。该 evaluator 必须无断言、无错误并取得 `1.0`，任务的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 把 benchmark success 写为官方评估无错误完成，唯一 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`SUCCESS` 和恰好一个匹配 `^#?\s*0*170$` 的无序 retrieved item，并取得 `1.0`，从而令任务得分为 `1.0`。它把 `agent_response.json` 和 `network.har` 均列为决定性 artifacts，要求后者能解析成 evaluation context 所需的 `NetworkTrace`；success 也明确要求 HAR 有效。failure 包括 artifact、setup、编排或 evaluator 错误，以及响应结构、task type、status、基数或正则匹配失败；响应或 HAR 留存副本缺失、截断而无法重建时归为 undecided，但已知提交时无效则归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_network_artifact`
- 为什么修改：尽管唯一配置的 evaluator 读取最终 agent 响应，且不执行网络事件匹配，但 network.har 仍被列为决定性证据。
- 应如何修改：将 agent_response.json 保留为唯一的决定性 artifact，并从原生证据集中移除 network.har。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_based_classification`
- 为什么修改：原生 success 和 undecided 分类被不恰当地设置为取决于所留存 HAR 的有效性或可用性。
- 应如何修改：依据已发布的解析、normalization、比较和错误处理行为，对完整 agent 响应判定 success 和 failure；仅当 agent_response.json 丢失且确实导致无法重建时，才判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`non_minimal_har_clauses`
- 为什么修改：HAR artifact 及多个相关条款使检查清单比唯一配置的检查所要求的更长、更严格。
- 应如何修改：移除 HAR artifact 以及 HAR 特定的 success、failure 和 undecided 表述，同时为已配置的 AgentResponseEvaluator 保留 evaluator 错误即 failure 的语义。

## Case 232

### 原本 case 是什么

原始任务是在 `shopping` 站点检索用户最近一笔待处理订单的订单号，task type 为 `RETRIEVE`。任务指令是 `Get the order number of my most recent pending order`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 可解析响应对象或从响应文本（包括 fenced code block）提取 JSON，并只投影 sparse expected 明确指定的 `task_type`、`status`、`retrieved_data`；`performed_operation` 可作为 `task_type` 的 legacy 输入名，其他原始键被忽略。归一化后期望为 `RETRIEVE`、`SUCCESS` 和恰好一个匹配 `^#?\s*0*189$` 的字符串项；标量 `retrieved_data` 会包装为单元素集合，`ordered:false` 表示忽略集合顺序，而物化的 `error_details:null` 不参与比较。没有配置 filter、网络事件 evaluator 或 last-event 判定。只有该 evaluator 得分 `1.0` 时，`TaskEvalResult.create` 才令 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原始 draft 声明唯一 `AgentResponseEvaluator` 必须无断言或错误地把响应归一化为 `task_type=RETRIEVE`、`status=SUCCESS` 和仅含一个匹配 `^#?\s*0*189$` 项的无序 `retrieved_data`，使所有 evaluator 及任务得分均为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，虽注明没有配置 `NetworkEventEvaluator` 内容谓词，仍要求 HAR 可解析为 `NetworkTrace`；failure 包括响应或 HAR 缺失、不可解析、字段/结构/数据不匹配及编排错误，完整响应或 HAR 的事后留存丢失、截断则为 undecided。非空 stronger condition `raw-response-schema-conformance` 要求原始响应本身是 schema-conformant `FinalAgentResponse` JSON 对象，`retrieved_data` 必须是含一个字符串的数组，不能依赖代码块提取或标量转单元素集合，并以 `agent_response.json` 判定。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive-network-har`
- 为什么修改：尽管唯一配置的 evaluator 仅比较 agent 响应，且数据包所表示的 trace 内容均不影响此案例的订单号比较，但 network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并保留完整的 agent_response.json 作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har-dependent-native-rules`
- 为什么修改：原生规则使 success 和 failure 取决于 network.har 的加载或解析，从而扩展了已配置的仅响应检查。
- 应如何修改：围绕唯一的 AgentResponseEvaluator 重写 success_if 和 fail_if；仅在所留存完整响应丢失、被截断或来源信息失效时判定为 undecided。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported-stronger-format-rule`
- 为什么修改：原始 JSON 对象/数组格式条件并不是官方用户意图的更强实现；它只是拒绝已发布 evaluator 有意接受的表示形式。
- 应如何修改：将 stronger.additional_conditions 设置为空列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`checklist-not-minimal`
- 为什么修改：冗余的 HAR 条件和传输格式更强条件使检查清单比已配置语义更宽泛且不够紧凑。
- 应如何修改：移除这两项附加内容，同时保留完整响应比较、组合规则以及证据丢失的区分。

## Case 233

### 原本 case 是什么

原始任务是在 `shopping` 站点获取用户最近一笔状态为 `complete` 的订单号，官方指令为 “Get the order number of my most recent complete order”。task type 是 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`：它对响应进行解析和规范化，并比较稀疏配置中明确指定的 `task_type`、`status`、`retrieved_data`；`task_type` 可由 `task_type` 或兼容的旧字段 `performed_operation` 提供，须为 `RETRIEVE`，`status` 须为 `SUCCESS`。`retrieved_data` 按 `{"type":"array","items":{"type":"string"}}` 规范化，非严格规范化可把标量包装成单元素集合；结果采用 `ordered:false` 的无序精确比较，必须恰有一项匹配正则 `^#?\s*0*180$`，缺项、多项或不匹配均不通过。物化产生的 `error_details:null` 不是稀疏配置明确指定的比较字段，其他原始响应键也不参与比较；本 case 没有 `NetworkEventEvaluator`、URL filter 或 last-event 判定。唯一 evaluator 的分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 得到 `1.0`，即规范化响应匹配 `RETRIEVE`、`SUCCESS`，且无序比较下 `retrieved_data` 恰有一项匹配 `^#?\s*0*180$`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于其所称的 `NetworkTrace` 解析及环境 URL fallback。其 success 条件要求输入和上下文可评估且响应完全匹配；failure 包括解析或规范化错误、非对象、缺失或不匹配的 `task_type`/`status`、无效结果项、HAR 或编排错误；只有 artifacts 缺失或不可读、无法确定 evaluator 所见内容时才为 undecided。非空 stronger condition `retrieved_data_array_contract` 进一步要求 `retrieved_data` 在 JSON 中实际是数组，不得依赖标量到单元素集合的 coercion，并以 `agent_response.json` 判定。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_legacy_task_type_alias`
- 为什么修改：原生规则称缺少 `task_type` 即为失败，尽管 evaluator 会在 `task_type` 缺失时接受 `performed_operation`。
- 应如何修改：说明 `RETRIEVE` 可以通过 `task_type` 或已发布的 `performed_operation` 别名提供，并且只有当两者都未提供匹配的归一化值时，才因该字段判定失败。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且该案例特定的响应值不依赖 URL。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性证据；不要将批次 HAR 保留契约或推测性的配置回退提升为案例检查。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_missing_field_failure`
- 为什么修改：`fail_if` 错误地将每个缺少 `task_type` 的响应归类为失败，还将 HAR 解析纳入证据判定。
- 应如何修改：考虑 `performed_operation` 别名，并基于完整的响应 artifact 表述原生 success/failure；仅在所保留的该证据丢失时使用 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_extra_artifact_and_restore_alias_semantics`
- 为什么修改：该检查清单包含一个非决定性的 HAR 分支，却遗漏了一个可接受的响应字段别名。
- 应如何修改：移除 `network.har` 决定性 artifact 条目及相关规则，并在原生响应语义中简洁地加入 `performed_operation` 别名。

## Case 234

### 原本 case 是什么

原始任务是在 `shopping` 站点获取用户最近一笔状态为 `on hold` 的订单号，官方指令为 “Get the order number of my most recent on hold order”。task type 是 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，比较明确配置的 `task_type`、`status` 和 `retrieved_data`：规范化后的逻辑 task type 须为 `RETRIEVE`，可来自 `task_type` 或旧别名 `performed_operation`；`status` 须为 `NOT_FOUND_ERROR`。`results_schema` 是 `{"type":"null"}`，因此 `retrieved_data` 须规范化为 `null`，缺失或空值也会规范化为 `null`；物化默认值 `error_details:null` 不属于明确配置的比较字段。这里没有 `NetworkEventEvaluator`、filter 或 last-event 语义，`network.har` 内容不参与该响应比较。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 接受规范化后的 `RETRIEVE` / `NOT_FOUND_ERROR` / `null`，且其分数和 `TaskEvalResult.score` 均为 `1.0`；它还写明省略 `retrieved_data` 也会规范化为 `null`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求 trace 可解析、评估上下文无错误。其 failure 包括响应缺失或不是可解析对象、必需的 `task_type` 或 `status` 缺失或不匹配、`retrieved_data` 非空，以及 trace、上下文、evaluator 或编排错误；无法保留实际响应，或缺少足够 trace 或官方结果来确认得分时为 undecided。非空 stronger condition `corroborate_not_found_against_shopping_state` 要求用 `network.har` 中的购物状态核实是否确实不存在 on-hold 订单；若存在，则必须返回其中最近一笔的订单号。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias`
- 为什么修改：失败规则称省略 `task_type` 即为失败，但已发布的 evaluator 会在 `task_type` 缺失时接受 `performed_operation`。
- 应如何修改：将要求表述为逻辑任务类型 `RETRIEVE`，它可通过 `task_type` 或可接受的旧版 `performed_operation` 别名提供。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace`
- 为什么修改：对于唯一配置的检查为 `AgentResponseEvaluator` 且预期 `retrieved_data` 为 `null` 的案例，`network.har` 被错误地从数据包的批次保留列表提升为决定性原生 artifact。
- 应如何修改：将完整的 `agent_response.json` 用作唯一的原生决定性 artifact；仅为单独的更强状态佐证条件保留 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_failure_and_undecided_rules`
- 为什么修改：这些规则错误地将可接受的 `performed_operation` 别名判为失败，并要求必须有 trace 或某个未命名的官方结果才能判定原生 success。
- 应如何修改：使响应不匹配/错误规则能够识别别名，并将原生 undecided 状态限定于实际提交的响应发生丢失、损坏或来源不确定的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_compact_or_coherent`
- 为什么修改：不必要的原生 trace 条目，以及 undecided 规则对某个未命名官方评估结果的引用，使证据模型既非最小化，又在内部不一致。
- 应如何修改：移除原生 trace 依赖，并始终基于完整的 `agent_response.json` 和已发布的 evaluator 语义重建原生结果。

## Case 235

### 原本 case 是什么

原始任务是在 `shopping` 站点获取用户最近一笔状态为 `under delivery` 的订单号，官方指令为 “Get the order number of my most recent under delivery order”。task type 是 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，它解析并规范化响应，对明确配置的 `task_type`、`status`、`retrieved_data` 做结构比较：逻辑 task type 须为 `RETRIEVE`，缺少 `task_type` 时可使用旧别名 `performed_operation`；`status` 须为 `NOT_FOUND_ERROR`。`results_schema` 为 `{"type":"null"}`，缺失、`null` 或空的 `retrieved_data` 会规范化为 `null`，非空值不匹配；物化的 `error_details:null` 未在稀疏配置中明确指定，其他未配置键也不比较。没有 `NetworkEventEvaluator`、filter 或 last-event 判定，`network.har` 不改变此响应比较。唯一 evaluator 得分必须为 `1.0`，任务的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得分 `1.0`：响应经官方解析和规范化后须匹配 `RETRIEVE`、`NOT_FOUND_ERROR` 和 `null`，缺失、空或 `null` 的 `retrieved_data` 均按 `null` 处理；任何 evaluator 或编排错误令任务得分为 `0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace 可解析及评估无错误纳入 success。failure 包括提交缺失、不可解析或非结构化、键或值不匹配、`retrieved_data` 非空，以及响应、trace、比较或编排错误；无法确定实际提交的响应和 trace 且没有完整 `TaskEvalResult` 时为 undecided。非空 stronger condition `corroborate_not_found_against_shopping_state` 要求通过 `network.har` 与 `agent_response.json` 核实运行时是否存在 under-delivery 订单：存在时返回最近一笔订单号，不存在时才允许 `NOT_FOUND_ERROR`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_not_decisive`
- 为什么修改：`network.har` 仅仅为了验证通用 trace 解析而被呈现为原生决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且预期 `retrieved_data` 会在不使用 trace 内容的情况下短路为 `null`。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅保留完整的 `agent_response.json` 作为最小化的原生 artifact；`network.har` 可继续作为单独更强条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_loss_wrongly_controls_native_decision`
- 为什么修改：这些规则要求存在可解析的 trace 才能判定 success，并将无法确认所提交 trace 的情况作为原生 undecided 的依据。
- 应如何修改：基于完整的已提交响应重建原生 success、failure 和 undecided。说明仅缺少 `network.har` 不会使这个仅依赖响应的案例变为 undecided，而完整但格式错误的响应、不匹配或已记录的 evaluator 错误均为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_branch`
- 为什么修改：原生 HAR artifact 和重复的 trace 解析规则，为原本紧凑的单 evaluator 检查清单增加了一个非决定性分支。
- 应如何修改：删除原生 trace 特定的 artifact 和规则条款，将原生 success 和 failure 统一围绕已发布的 `AgentResponseEvaluator` 比较进行表述。

## Case 243

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取对 `Circe fleece` 最不满意的客户的电子邮件地址，官方指令为 “Get the email address of the customer who is the most unhappy with Circe fleece”。task type 是 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`；它接受 mapping，或从 JSON 文本（包括 JSON code block）解析 mapping，然后比较稀疏配置明确指定的 `task_type`、`status`、`retrieved_data`。`task_type` 或旧别名 `performed_operation` 须规范化为 `RETRIEVE`，`status` 须为 `SUCCESS`；`retrieved_data` 按字符串数组 schema 规范化，标量可被处理为单元素集合，并在 `ordered:false` 下精确等于无序单元素集合 `hannah.lim@gmail.com`，缺失、额外或重复项均失败。物化默认的 `error_details:null` 和其他未配置原始键不参与比较；没有 `NetworkEventEvaluator`、filter 或 last-event 语义。唯一 evaluator 无错误且比较全部通过时得分 `1.0`，所有 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 完成且得分 `1.0`，规范化后的三个比较键须为 `task_type: RETRIEVE`、`status: SUCCESS`，以及无序精确单元素 `retrieved_data` 值 `hannah.lim@gmail.com`，由此 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，但说明此任务不另外评分 network-event 内容，只要求 trace 可解析以建立评估上下文。failure 包括响应缺失或不是可接受对象、规范化比较键缺失或多出、task type/status 不同、邮件结果不精确，以及输入、trace、规范化、evaluator 或编排错误；证据不完整或损坏，无法确定精确响应或评估是否完成且无官方结果可解时为 undecided。原始 draft 的 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被指定为决定性证据，尽管唯一配置的 evaluator 是 `AgentResponseEvaluator`，且数据包证据均未使网络事件内容成为已配置响应比较的一部分。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：对于仅配置响应检查的情况，判定规则依赖于证明 trace/输入已经完成，并允许缺少 trace 证据促成 undecided 结果。
- 应如何修改：基于对完整响应应用已发布的 `AgentResponseEvaluator` 语义来判定原生 success 和 failure，并将 undecided 限定于重建所需响应证据的丢失、损坏或来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_trace_material`
- 为什么修改：trace artifact 及其重复的解析、错误和保留条件，为原本仅依赖响应的检查清单增加了非决定性内容。
- 应如何修改：删除 trace 特定的 artifact 和规则表述，同时保留响应解析、normalization、比较、evaluator 错误以及所有分数均等于 `1.0` 的语义。

## Case 244

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点获取对 `Olivia zip jacket` 最不满意的客户的电子邮件地址，官方指令为 “Get the email address of the customer who is the most unhappy with Olivia zip jacket”。task type 是 `RETRIEVE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，对解析和规范化后的明确配置字段进行比较：逻辑 task type 须为 `RETRIEVE`，可由 `task_type` 或旧别名 `performed_operation` 提供；`status` 须为 `SUCCESS`。`retrieved_data` 使用 `{"type":"array","items":{"type":"string"}}` 规范化，并按 `ordered:false` 精确匹配无序单元素结果 `["emma.lopez@gmail.com"]`；缺失、错误、重复或额外项均不通过。物化的 `error_details:null` 不是稀疏配置明确指定的比较字段；没有 `NetworkEventEvaluator`、filter 或 last-event 语义，HAR 不参与邮件结果比较。唯一 evaluator 得分为 `1.0` 时，满足“所有 evaluator 分数均为 `1.0`”的组合规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 得分 `1.0`：解析后的响应须规范化为 `RETRIEVE`、`SUCCESS`，且 `retrieved_data` 精确匹配无序单元素 `["emma.lopez@gmail.com"]`，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并在 success 中要求保留的响应与可解析 trace 使官方评估完成。failure 包括响应存在但不可用于评估、task type/status 不匹配、结果缺失、错误或多出，以及 trace、上下文、evaluator 或编排错误，或任何 evaluator 分数不是 `1.0`；所称必需 artifact 缺失或存储不可读且其余证据不能证明不匹配或错误时为 undecided。原始 draft 的 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unconfigured_trace_semantics`
- 为什么修改：尽管配置仅包含 `AgentResponseEvaluator`，原生规则却将 HAR 解析和基于 trace 的上下文验证变成了额外的 success 条件。
- 应如何修改：从原生评分中移除 trace 可解析性以及 trace/上下文条件；仅保留已发布的、针对明确配置的响应字段的解析、normalization 和比较。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_trace_artifact`
- 为什么修改：尽管 `agent_response.json` 已能完全判定此项已配置的电子邮件响应比较，`network.har` 仍被列为决定性证据。
- 应如何修改：保留 `agent_response.json` 作为唯一的决定性原生 artifact，并从 `decisive_artifacts` 中移除 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_rules`
- 为什么修改：success、failure 和 undecided 规则错误地依赖于非决定性的 trace artifact。
- 应如何修改：基于可从完整响应重建的 `AgentResponseEvaluator` 结果判定 success 和 failure，并将 undecided 限定于 `agent_response.json` 丢失或其完整性/来源验证失败的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_scope`
- 为什么修改：网络 artifact 条目和依赖 trace 的规则增加了不必要的原生范围，使检查清单无法保持紧凑和最小化。
- 应如何修改：删除 `network.har` artifact 条目和所有 trace 特定的原生条款，同时保留唯一 evaluator 的完整响应语义。

## Case 245

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：找出对 `Antonia racer tank` 最不满意的客户姓名。官方指令为“Get the name of the customer who is the most unhappy with Antonia racer tank”。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，它对响应进行解析和归一化，并检查稀疏配置中明确给出的 `task_type`、`status` 和 `retrieved_data`；期望分别为 `RETRIEVE`、`SUCCESS` 和字符串数组 `["Shaunte"]`，物化产生的 `error_details: null` 不参与评分。`results_schema` 是字符串数组，`ordered=false` 表示无序精确比较：允许调整顺序，但不允许缺失或增加值；本例单元素数组必须恰为 `"Shaunte"`。未配置 `NetworkEventEvaluator`，因而没有网络 filter 或 last-event 评分语义；`network.har` 的内容不参与这个响应比较。只有该 evaluator 得分为 `1.0` 时，按“所有 evaluator 分数均等于 `1.0`”的组合规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 接受归一化后的 `RETRIEVE`、`SUCCESS` 和无序单例 `["Shaunte"]`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts：前者用于核对响应，后者被描述为保证 `NetworkTrace`、环境配置和评估流程无误；成功条件要求精确匹配且无错误，失败条件包括响应缺失、无效或不匹配以及 trace、配置、evaluator 或编排错误，证据丢失或损坏则可判为 `undecided`。其非空 stronger condition `strict_public_response_format` 进一步要求原始 `agent_response.json` 不依赖代码块提取或标量强制转换，直接成为有效的 `FinalAgentResponse` JSON 对象，并以数组 `["Shaunte"]` 表示 `retrieved_data`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管该案例只有一个 `AgentResponseEvaluator`，且其比较读取的是 `agent_response_raw`，而非网络 trace。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并从 `checked_by` 中移除 HAR 设置声明；将完整的 `agent_response.json` 确定为唯一的决定性原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`restrict_undecided_to_response_evidence_loss`
- 为什么修改：当前 undecided 规则将非决定性的必需 trace 丢失或损坏视为可能阻碍判定的因素。
- 应如何修改：将 `undecided_if` 限定于 `agent_response.json` 的丢失、损坏、不完整或来源验证失败，且这些问题导致无法重建已配置的比较；保留完整但无效或为 `null` 的响应以及 evaluator 可见错误均为 failure 的规则。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_setup_overhead`
- 为什么修改：trace 解析和环境回退说明为原本紧凑且仅依赖响应的检查清单增加了非决定性的设置细节。
- 应如何修改：删除 trace artifact 和 trace 特定的判定表述，同时保留响应比较、evaluator 错误处理以及所有 evaluator 的组合规则。

## Case 246

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：返回对 `Chloe tank` 最不满意的客户姓名。官方指令为“Get the name of the customer who is the most unhappy with Chloe tank”。

### Benchmark 怎么测

唯一配置的是 `AgentResponseEvaluator`，它检查明确配置的 `task_type`、`status` 和 `retrieved_data`，期望为 `RETRIEVE`、`SUCCESS` 和 `["Teofila"]`；物化默认值 `error_details: null` 不参与检查。响应须解析为对象；归一化可接受标量或序列形式的 `retrieved_data`，并按字符串数组 schema 比较，`ordered=false` 要求无序内容精确等于单例 `["Teofila"]`，不能有缺失、不同、重复或额外项目。未配置网络 evaluator，因此没有 filter 或 last-event 语义，`network.har` 不决定该响应比较。唯一 evaluator 必须无错误并得分 `1.0`，随后全 evaluator 均须为 `1.0` 的规则才会令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 写为归一化响应匹配 `RETRIEVE`、`SUCCESS` 和无序单例 `["Teofila"]`，使唯一 `AgentResponseEvaluator` 及最终 task score 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都视为决定性 artifacts，并在成功条件中要求响应和 HAR 可加载、评估完成；失败条件覆盖不可解析或不匹配的响应、任何缺失或额外结果，以及输入、上下文、编排或 HAR 错误，响应或 trace 的留存证据不可用时则列为 `undecided`。其非空 stronger condition `raw-retrieved-data-array` 要求原始响应中的 `retrieved_data` 必须是 JSON 数组，而不能依赖 evaluator 将标量强制转换为单例序列。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`har-native-semantics`
- 为什么修改：尽管任务仅配置了 `AgentResponseEvaluator`，HAR 的存在和解析却被呈现为额外的原生 success 要求。
- 应如何修改：将原生 success 限定于已发布的、针对明确配置的响应字段 `task_type`、`status` 和 `retrieved_data` 的解析、normalization 和比较。不要将 HAR 可加载性添加为已配置的 predicate。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal-har-artifact`
- 为什么修改：`network.har` 被保留为决定性证据，尽管其内容不参与该案例唯一配置的响应比较。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har-dependent-decisions`
- 为什么修改：success、failure 和 undecided 规则错误地依赖于 HAR 的可用性或有效性。
- 应如何修改：移除依赖 HAR 的判定分支。将完好但无效或不匹配的响应证据视为 failure，并仅在完整响应丢失或其完整性/来源验证失败时使用 undecided。

#### 修改项 4：stronger.additional_conditions

- Finding ID：`unsupported-stronger-array-rule`
- 为什么修改：原始数组条件强制实施的是整个 benchmark 范围的接口细节，而不是案例特定的用户意图/evaluator 差距。
- 应如何修改：将 `stronger.additional_conditions` 设置为空列表。

#### 修改项 5：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-redundant-scope`
- 为什么修改：非决定性的 HAR 逻辑和通用 stronger 条件使检查清单不必要地冗长，且内部范围过宽。
- 应如何修改：将检查清单正文替换为紧凑的仅响应原生检查，并使用空的 stronger 列表。

## Case 247

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：获取对 `Zoe` 产品风格最不满意的客户的电子邮件地址。官方指令为“Get the email address of the customer who is the most unhappy with the style of Zoe products”。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它在解析和归一化响应后比较三个明确配置字段：`task_type` 应为 `RETRIEVE`，`status` 应为 `NOT_FOUND_ERROR`，`retrieved_data` 应为 `null`；`results_schema` 为 `{"type":"null"}`，物化默认的 `error_details: null` 不属于明确配置的评分字段。`ordered=false` 已物化，但在期望数据为 `null` 时不存在数组排序差异；任何非 null 数据、字段缺失或状态不匹配都会使比较失败。没有配置网络 filter 或 last-event evaluator，原生评分不会用 `network.har` 验证“不存在”的事实。唯一 evaluator 得分必须为 `1.0`，全 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称任务成功要求唯一 `AgentResponseEvaluator` 将响应归一化为 `task_type RETRIEVE`、`status NOT_FOUND_ERROR` 和 `retrieved_data null`，并令 `TaskEvalResult` 得分 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，成功条件还要求网络 trace 与评估上下文有效；响应不可解析、字段不匹配、数据非 null 或 evaluator/trace/编排出错被列为失败，而响应或 trace 留存缺失且没有官方结果时被列为 `undecided`。其非空 stronger condition `substantiate_not_found` 要求 `network.har` 独立证明运行中不存在满足 Zoe 产品风格“最不满意”标准的客户或邮箱，以弥补原生 evaluator 只核对自报响应字段的不足。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_har`
- 为什么修改：对于唯一配置的检查读取 `agent_response` 且预期 `retrieved_data` 为 `null` 的案例，`network.har` 被错误地称为原生决定性 artifact。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性证据。`network.har` 可继续作为明确指定的更强佐证条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_native_rules`
- 为什么修改：这些规则使原生 success 依赖于有效的 trace，将 trace 解析问题归类为原生 failure，并在缺少运行后 trace 证据时判定 undecided，尽管已配置的响应比较可从 `agent_response.json` 重建。
- 应如何修改：仅基于所保留的响应和唯一的 `AgentResponseEvaluator` 判定原生 success、failure 和 undecided。将 undecided 限定于确实阻止重建的响应证据丢失或其完整性/来源验证失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nondecisive_native_trace_content`
- 为什么修改：原生部分包含一个非决定性的 HAR artifact，以及冗余的 trace 相关 success 和 failure 条款。
- 应如何修改：移除原生 HAR artifact 和所有依赖原生 trace 的条款，同时保留响应比较、evaluator 组合以及可选的更强 HAR 条件。

## Case 248

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 `Carnegie Mellon Café` 的坐标。输出须仅为含 `"latitude"` 和 `"longitude"` 键的对象，数值采用十进制度，且不得包含其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 明确检查 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data`；期望数据是单例坐标 `{"latitude":"40.4424191","longitude":"-79.9397388"}`，物化的 `error_details: null` 不参与比较。字符串响应会被去除首尾空白、可提取 fenced 内容并尝试 JSON 解码；`task_type` 缺失时可使用 `performed_operation`，只投影稀疏配置字段，非列表 `retrieved_data` 会包装成单例，再依照 array/`coordinates` schema 归一化并以 `ordered=false` 做无序精确比较。未配置网络 filter 或 last-event evaluator，`network.har` 不参与坐标响应的原生比较。只有该 evaluator 无错误且得分 `1.0` 时，全 evaluator 均为 `1.0` 的组合规则才令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 描述为响应经解析和 schema 归一化后匹配 `RETRIEVE`、`SUCCESS` 以及纬度 `40.4424191`、经度 `-79.9397388` 的唯一坐标，从而使唯一 evaluator 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求两者可用且评估无误；非对象、字段或坐标不匹配及输入、evaluator、trace 或编排错误属于失败，任一 artifact 缺失或不可读而无法重建输入时属于 `undecided`。其非空 stronger condition `literal_no_extra_output` 要求原始最终响应是没有外围文字或 Markdown 的有效 JSON，且唯一坐标 payload 只能包含 `"latitude"` 和 `"longitude"` 两个键。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete_response_comparison_semantics`
- 为什么修改：检查清单未充分说明已发布的响应解析和 normalization 行为，因而无法判定会改变分数的原始形式。
- 应如何修改：说明响应字符串可以直接解码，也可以从 fenced block 中提取；当 `task_type` 缺失时，`task_type` 可以使用 `performed_operation`；非列表 `retrieved_data` 会被包装为单元素列表；仅投影并比较稀疏配置中预期的三个字段；实例化的 `error_details` 未被配置；归一化后的 `retrieved_data` 按 `coordinates` schema 进行无序比较。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nondecisive_har_retained_as_native_evidence`
- 为什么修改：对于这个仅使用 `AgentResponseEvaluator` 的案例，`network.har` 被错误地称为必要证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的运行后证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`har_incorrectly_gates_decision`
- 为什么修改：尽管没有配置网络检查，这些规则仍将 HAR 可用性设为 success 的必要条件，并在 HAR 保留数据丢失时判定 undecided。
- 应如何修改：从 `success_if` 和 `undecided_if` 中移除 HAR 要求。将 undecided 限定于确切最终响应的丢失、损坏、不完整或来源验证失败；完整但格式错误、为 `null` 或不匹配的响应仍判定为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal`
- 为什么修改：不必要的 HAR artifact 和重复的 HAR 门控条件使检查清单非最小化。
- 应如何修改：删除 HAR 特定的原生 artifact 和规则表述，同时保留唯一的响应比较、evaluator 组合以及响应证据完整性规则。

## Case 250

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 `Apple Store near Pitt` 的坐标。输出须仅为含 `"latitude"` 和 `"longitude"` 键的对象，使用十进制度且不得附加其他细节。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，明确期望 `task_type: RETRIEVE`、`status: SUCCESS`，以及单例坐标 `{"latitude":"40.4511693","longitude":"-79.9334241"}`；物化默认的 `error_details: null` 不是明确配置的比较字段。释放版解析和归一化接受所表示的旧字段名 `performed_operation`，并按 array/`coordinates` schema 处理 `retrieved_data`；`ordered=false` 要求归一化结果无序精确等于该唯一坐标，不得缺失、增加或改变坐标项。没有配置网络 filter 或 last-event evaluator，因此 `network.har` 不影响这一响应检查。唯一 evaluator 必须得分 `1.0`，全 evaluator 得分均为 `1.0` 的规则随后才会令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求提交响应解析并归一化为 `RETRIEVE`、`SUCCESS` 和唯一坐标纬度 `40.4511693`、经度 `-79.9334241`，使唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；成功条件要求所需 artifacts 可评估且响应精确匹配，失败包括响应无效、无法归一化、字段或坐标不匹配以及 trace、上下文、evaluator 或编排产生 `ERROR`，无法恢复响应或 trace 且无官方结果时则列为 `undecided`。原始 draft 的 `stronger.additional_conditions` 为空，没有声明额外 stronger condition。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：`network.har` 被列为决定性 artifact，尽管唯一配置的 evaluator 读取的是 agent 响应，且未检查任何案例特定的网络事件。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：这些规则以所有列出的 artifact 为条件判定 success，并在 trace 丢失时判定 undecided，从而削弱了可重建的仅响应结果。
- 应如何修改：基于完整的已提交响应判定 success 和 failure，并将 undecided 限定于该响应的丢失、完整性失败或来源验证失败；明确保留完整但无效或不匹配的响应为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_language`
- 为什么修改：尽管 trace 要求并非该案例已配置比较的一部分，它们仍在 artifact 和判定规则中重复出现。
- 应如何修改：删除 trace 特定的 artifact 和判定表述，同时保留 evaluator 错误即 failure 的语义。

## Case 251

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：查找 CMU 附近、位于 Carnegie art museum 同侧街道的公交站坐标。用户要求仅返回一个含 `"latitude"` 和 `"longitude"` 键的对象，数值采用十进制度，不附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它对最终响应进行解析，并按 `results_schema` 的坐标格式归一化，然后比较稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data`，其中期望值为 `RETRIEVE`、`SUCCESS` 及唯一坐标 `{"latitude":"40.4443","longitude":"-79.94889"}`。`retrieved_data` 使用 `ordered=false` 的无序精确比较，不得缺少或增加项目；物化产生的 `error_details:null` 并非稀疏配置明确指定的比较字段。本任务没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 在解析和坐标归一化后匹配 `RETRIEVE`、`SUCCESS` 及该唯一坐标，从而令 `TaskEvalResult.score` 为 `1.0`；它把 `agent_response.json` 列为决定性 artifact。其 `success_if` 要求无序的 `retrieved_data` 精确匹配，`fail_if` 将不可解析、字段缺失或不匹配、空数据、归一化不符、evaluation error 或 `TaskEvalResult.score 0.0` 判为失败，`undecided_if` 仅涵盖 `agent_response.json` 未保留或事后截断。非空 stronger condition `literal_output_only_format` 还要求原始响应没有外围说明或 Markdown 围栏，并要求坐标 payload 只有 `latitude` 和 `longitude`；源码 review 指出前一要求有依据，但 draft 关于忽略额外坐标键的依据不足。

### 需要修改的部分

#### 修改项 1：stronger.additional_conditions

- Finding ID：`unsupported_coordinate_extra_keys_gap`
- 为什么修改：更强条件声称，要求每个坐标 payload 仅包含 latitude 和 longitude 超出了原生评分的范围，但所呈现的 normalizer 只是将格式坐标委托给一个未展示的 TYPE_REGISTRY 类。因此，该材料并未证实坐标对象中的额外 key 是会被保留、被忽略，还是会导致 normalization failure。
- 应如何修改：删除关于坐标 payload 额外 key 的条款及其缺乏支持的理由。仅保留此 case 特有的禁止说明性文字/禁止 Markdown 围栏条件；官方指令和已发布的代码块提取行为直接证实了该条件与原生评分之间的差异。

## Case 252

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 Pittsburgh 的 Tokyo Japanese Food Store 坐标。用户要求仅返回一个含 `"latitude"` 和 `"longitude"` 键的对象，数值采用十进制度，不附加其他内容。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，明确比较 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和唯一坐标 `{"latitude":"40.45761","longitude":"-79.92934"}`；默认的 `error_details:null` 不参与比较。响应可经字符串或 fenced JSON 提取，dict-like 响应只投影已配置字段，`performed_operation` 可作为旧版 `task_type` 键；坐标数组按 `results_schema` 归一化后以 `ordered=false` 无序精确比较，不允许缺失或额外项目。本任务没有事件 filter 或 last-event 比较；唯一 evaluator 无 assertion 且无 evaluator error 时得 `1.0`，所有 evaluator 均须为 `1.0`，故此处该唯一得分决定 `TaskEvalResult.score`。

### 原本 draft 是什么

原始 draft 声明唯一 `AgentResponseEvaluator` 必须在解析、归一化和无序比较后匹配 `RETRIEVE`、`SUCCESS` 及坐标 `(40.45761, -79.92934)`，并以 `1.0` 令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并在 `success_if`、`fail_if` 与 `undecided_if` 中把 trace 解析、上下文构建及 trace 留存纳入判断；源码 review 认为这些 trace 条件对于仅配置响应 evaluator 的本案并非决定性。非空 stronger condition `user_requested_bare_coordinate_object` 要求用户可见答案严格是只有两个键和值 `40.45761`、`-79.92934` 的单个对象，不得含协议 wrapper、列表、代码围栏、额外键或其他文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_trace`
- 为什么修改：network.har 被列为决定性 artifact，尽管任务 252 只有一个 AgentResponseEvaluator，而且其坐标比较可以根据完整的最终响应重建。
- 应如何修改：从 decisive_artifacts 中删除 network.har，并保留 agent_response.json 作为唯一的原生决定性 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`restrict_undecided_to_response_evidence_loss`
- 为什么修改：undecided 规则将所需 trace 的丢失视为会阻止重建，这不当地将批次留存约定提升为 case 特有的依赖项。
- 应如何修改：使 undecided 仅取决于 agent_response.json 的丢失、截断、完整性故障或来源不确定；明确完整但为 null、格式错误或不匹配的响应属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_specific_nonminimal_clauses`
- 为什么修改：trace 解析和 fallback 条款为一个唯一已配置比较仅使用 agent response 的 case 增加了非决定性机制。
- 应如何修改：删除 trace 特有的 artifact 和决策表述，同时保留 evaluator errors 以及任何非 1.0 的 evaluator 结果作为原生 failure。

## Case 254

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 Western Pennsylvania Hospital 的电话号码。指令没有另外规定输出表面格式。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应进行提取、解析和归一化，并比较稀疏配置明确指定的 `task_type`、`status`、`retrieved_data`：期望为 `RETRIEVE`、`SUCCESS` 和 `["4125785000"]`；`performed_operation` 可作为旧版 `task_type` 别名，而物化默认值 `error_details:null` 不参与比较。`retrieved_data` 采用 array-of-strings schema 和 `ordered=false` 无序精确比较，因此不得缺失或增加元素；未配置事件 filter 或 last-event 语义。唯一 evaluator 必须无错误并得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是响应归一化后匹配 `RETRIEVE`、`SUCCESS` 和无序单例 `["4125785000"]`，且唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它将 `agent_response.json` 与 `network.har` 同列为决定性 artifacts；`success_if` 要求响应和 trace 可重建无错 evaluation，`fail_if` 包括响应或 trace 解析、上下文、编排、evaluator error 及字段不匹配，`undecided_if` 则涵盖任一必需 artifact 未忠实保留或无法关联本次运行。源码 review 认为 `network.har` 及相应 trace 条件并非本案配置比较的决定性证据；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：network.har 被列为决定性 artifact，尽管唯一配置的 evaluator 从 agent_response_raw 中提取其实际值，并比较一个非 URL 的电话号码结果。
- 应如何修改：从 decisive_artifacts 中删除 network.har，并保留完整的 agent_response.json 作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：success 和 undecided 规则同时要求响应和 trace，因此缺少 network.har 会错误地阻止对已配置 response evaluator 作出判定。
- 应如何修改：以完整留存的响应为依据判定原生 success 和 failure，并将 undecided 限定为 agent_response.json 的丢失、损坏或来源故障。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_language`
- 为什么修改：通用 trace 解析和配置 fallback 表述为原本仅涉及响应的 case checklist 增加了非决定性证据分支。
- 应如何修改：删除 trace artifact 和 trace 特有条款，同时保留响应解析、normalization、比较、evaluator error 和任务组合语义。

## Case 255

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 PIT airport 的 operator。指令没有另行限定输出格式。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，其明确期望 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 为唯一字符串 `"Allegheny County Airport Authority"`；物化的 `error_details:null` 不属于明确配置的比较字段。响应经官方解析和归一化，`retrieved_data` 按 array-of-strings 的 `location-name` 格式处理，并以 `ordered=false` 进行无序精确单例比较，不能有缺失、重复或额外项目。本案没有事件 filter 或 last-event 语义；唯一 evaluator 得分须为 `1.0`，所有 evaluator 均为 `1.0` 的组合规则才使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 经解析、归一化和无序比较后匹配 `RETRIEVE`、`SUCCESS` 与精确单例 `“Allegheny County Airport Authority”`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；`success_if` 要求无 evaluator 或 orchestration error，`fail_if` 包括无效响应、字段或项目不匹配以及响应/trace/context/编排错误，`undecided_if` 要求证据足以确定最终响应和可用 trace，否则在没有官方结果时为 undecided。源码 review 认为 trace 并非本案唯一响应 evaluator 的决定性输入；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：该 checklist 将 network.har 指定为决定性 artifact，尽管此 case 只有一个 AgentResponseEvaluator，而其实际值是 agent_response_raw。
- 应如何修改：从 decisive_artifacts 中删除 network.har，并保留完整的 agent_response.json 作为最低限度所需的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_undecided_rule`
- 为什么修改：尽管未配置网络检查，undecided 规则仍将缺少可用 trace 视为会阻止重建。
- 应如何修改：将 undecided_if 限定为与最终响应有关的丢失、截断、完整性问题或来源不确定性，除非留存的官方结果能够独立确定分数。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_trace_clauses`
- 为什么修改：trace 特有的 artifact 和决策条款为原本紧凑且仅涉及响应的 checklist 增加了非决定性范围。
- 应如何修改：删除 trace artifact 和 trace 留存依赖，同时保留 evaluator 和编排错误；当留存证据能够证实这些错误时，将其视为原生 failure。

## Case 256

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：获取 Pittsburgh 的 Carnegie art museum 网站。指令没有另外要求特定的输出表面格式。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data`，期望分别为 `RETRIEVE`、`SUCCESS` 和 `["http://web.cmoa.org/"]`；物化默认的 `error_details:null` 不参与比较。响应适用字符串或代码块 JSON 提取及归一化，`task_type` 可由旧版键 `performed_operation` 提供；`retrieved_data` 按 array-of-strings schema 归一化，并以 `ordered=false` 无序精确比较，不得缺少或增加项目。本案没有 `NetworkEventEvaluator`、事件 filter 或 last-event 语义；唯一 evaluator 必须得 `1.0`，才能满足所有 evaluator 均为 `1.0` 的规则并使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 是必需输入成功解析，且唯一 `AgentResponseEvaluator` 匹配 `RETRIEVE`、`SUCCESS` 与无序单例 `http://web.cmoa.org/`，从而令 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 均列为决定性 artifacts，虽称 trace 事件不会被独立比较，仍在 `success_if`、`fail_if` 和 `undecided_if` 中让 HAR 解析或留存影响判断；源码 review 认为这使规则非最小且错误地赋予 HAR 决定性。其失败条件还包括响应缺失、无法归一化、比较键值不符、retrieved_data 缺失或含额外项目以及 evaluation orchestration error；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_har`
- 为什么修改：network.har 被表述为决定性 artifact，尽管此 case 仅配置了 AgentResponseEvaluator，且没有对任何 trace event 进行比较。
- 应如何修改：从 decisive_artifacts 中删除 network.har，并保留完整的 agent_response.json 作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_driven_decisions`
- 为什么修改：success、failure 和 undecided 规则允许 HAR 解析或已留存 HAR 的丢失左右原生判定。
- 应如何修改：基于完整的已提交响应进行重建；将 undecided 限定为响应留存、完整性或来源的丢失，同时将完整但无效或不匹配的响应视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nondecisive_trace_scope`
- 为什么修改：非决定性的 trace 条目及规则中对它的反复引用，使该 checklist 的范围超出了此项已配置检查所需的最小证据。
- 应如何修改：删除 trace 特有的 artifact 和规则表述，同时保留 response evaluator 的解析、normalization、比较、错误和任务组合语义。

## Case 257

### 原本 case 是什么

原始任务是在 `map` 站点检索 Pittsburgh 的 Tokyo Japanese Food Store 营业时间，task type 为 `RETRIEVE`。输出须为对象列表，每个对象仅按要求包含 `day`、`open_time` 和 `close_time`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应经解析和 schema 字符串规范化后，`task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 精确匹配五个对象：Wednesday 至 Sunday 的 `open_time` 均为 `10:00`、`close_time` 均为 `17:00`。`results_schema` 是对象数组，`ordered:false` 表示集合顺序不影响比较，但缺失、额外、重复对象或对象键和值差异均不匹配；物化的默认 `error_details:null` 不是稀疏配置中显式要求的比较字段。此 case 仅有该 evaluator，只有其分数等于 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 `TaskEvalResult.score` 为 `1.0`，即唯一的 `AgentResponseEvaluator` 在规范化并无序结构匹配官方值后得到 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求前者匹配 `RETRIEVE`、`SUCCESS` 及五个营业时间对象，后者能解析为构造评估上下文所需的 `NetworkTrace`。其 success 条件还要求 trace 被接受且评估无错误；failure 包括响应无效或不匹配、`retrieved_data` 有任何差异，以及 trace 缺失、不可读或发生解析、evaluator、orchestration 错误；undecided 则用于留存证据缺失或截断、无法确认实际提交响应或 trace 的情形。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：network.har 被表述为决定性 artifact，尽管唯一配置的 evaluator 比较的是 agent response，并不检查网络事件。
- 应如何修改：保留 agent_response.json 作为唯一的决定性 artifact，并从原生 decisive_artifacts 中删除 network.har。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decisions`
- 为什么修改：决策规则将原生 success 和 undecided 状态取决于非决定性的已留存 trace。
- 应如何修改：删除依赖 trace 的 success 和 failure 条款，并将 undecided 限定为完整 agent_response.json 的丢失或完整性/来源故障，且该问题会阻止重建响应比较。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_clauses`
- 为什么修改：多个 trace 相关条款为原本仅涉及响应的 case checklist 增加了非决定性内容。
- 应如何修改：删除网络 artifact，并围绕唯一的 AgentResponseEvaluator 和完整的 agent response 整合原生规则。

## Case 259

### 原本 case 是什么

原始任务是在 `gitlab` 站点取得用户自己的 RSS feed token，task type 为 `RETRIEVE`。官方指令是 `Get me my RSS feed token`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应经提取和规范化后，显式字段 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，并且字符串数组 `retrieved_data` 精确等于单元素集合 `["TMN_bBn9Z48qVbUFZV45"]`。比较采用 `results_schema` 的 string array 规范化和 `ordered:false` 的无序精确比较；物化的 `error_details:null` 不是稀疏配置显式要求的字段。只有该 evaluator 得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native benchmark success 为 `TaskEvalResult.score 1.0`，要求唯一的 `AgentResponseEvaluator` 匹配 `RETRIEVE`、`SUCCESS` 和恰好一个 token `"TMN_bBn9Z48qVbUFZV45"`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，分别用于重建响应比较和确认 HAR 可形成官方评估上下文。其 success 条件要求响应全部结构和值比较通过且官方评估没有 input、configuration、normalization 或 orchestration error；failure 包括响应字段或数据不匹配，以及 HAR/响应无法形成有效上下文或各种评估错误；undecided 用于必要 artifact 缺失或无法确认完整性、又无保留的官方 task outcome 可判定分数时。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_har`
- 为什么修改：network.har 被指定为决定性 artifact，尽管此 case 只有一个 AgentResponseEvaluator，其实际输入为 agent_response_raw，而且该材料并未证实 HAR 内容会影响已配置的 token 比较。
- 应如何修改：仅保留完整的 agent_response.json 作为决定性原生证据，并从 decisive_artifacts 中删除 HAR 问题。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_dependent_rules`
- 为什么修改：当前的 fail 和 undecided 规则依赖于 HAR 解析或留存情况，因此即使响应完整，缺少非决定性的 HAR 也可能阻止作出判定。
- 应如何修改：删除依赖 HAR 的 success、failure 和 undecided 条款。将完整但无效或不匹配的响应以及 response-evaluator errors 视为 failure；仅在已提交响应丢失或其完整性/来源无法验证时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：不必要的 HAR 要求在多个原生字段中重复出现，使 checklist 的范围超出了此 case 所需的最小证据。
- 应如何修改：围绕唯一配置的 response evaluator 及其完整响应 artifact 精简原生部分，同时保留确切的预期字段、normalization、比较和评分行为。

## Case 260

### 原本 case 是什么

原始任务是在 `shopping` 站点打开 Video Game 类目页以浏览商品，task type 为 `NAVIGATE`。目标页面是该站点的 `__SHOPPING__/video-games.html`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查响应经发布版解析与规范化后匹配 `task_type:NAVIGATE` 和 `status:SUCCESS`；对这个非 `RETRIEVE` 任务，缺失或存在的原始 `retrieved_data` 都规范化为 `null`，其原始值不参与比较，默认 `error_details:null` 也不是显式配置字段。`NetworkEventEvaluator` 在 `last_event_only:true`、`should_not_exist:false` 下检查 evaluator 可见的最后一个导航事件是否为规范化 URL `__SHOPPING__/video-games.html` 的 `GET`，且 `response_status` 为 `200`；其余物化为 `null` 的 headers、query、post data、content 和 cookies 未提出具体值约束。两个 evaluator 的分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 对预期 `NAVIGATE/SUCCESS` 响应得 `1.0`，且 `NetworkEventEvaluator` 对选中的最后导航事件匹配 `GET __SHOPPING__/video-games.html` 和 HTTP `200` 得 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并在 success 中写成响应通过且“无 retrieved data”、HAR 的最后导航事件满足 URL、方法和状态条件。failure 是任一 evaluator 非 `1.0` 或报错，包括响应结构不匹配或 HAR 没有相符事件；undecided 仅用于任一 artifact 未留存、无法建立 evaluator 输入，而已留存 artifact 显示无效或不匹配则归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`F1`
- 为什么修改：原生表述可能会将原始 retrieved_data 为 null/缺失视为必需条件，尽管 NAVIGATE normalization 会将任何存在的 retrieved_data 值映射为 null，并跳过对其值的比较。
- 应如何修改：明确响应必须针对显式配置的 task_type 和 status 通过已发布的解析与 normalization，并说明 retrieved_data 会被 normalization 为 null，且对于此非 RETRIEVE 任务，其原始值与评分无关。继续从已配置比较中排除默认的 error_details。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`F2`
- 为什么修改：success_if 比 TaskEvalResult 的 success 更严格，因为它声称响应不得包含 retrieved data。
- 应如何修改：将该条款替换为不附加额外断言的已发布解析/normalization 比较，对照 NAVIGATE 和 SUCCESS 进行比较，并明确说明非 RETRIEVE 情况下 retrieved_data 的行为。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`F3`
- 为什么修改：该 checklist 对响应的简洁表述存在歧义，无法明确 null retrieved_data 是预期的 normalization 后值，还是原始输入要求。
- 应如何修改：在 benchmark_success、decisive_artifacts 和 success_if 中一致采用一种无歧义的 normalization 后比较表述。

## Case 262

### 原本 case 是什么

原始任务是在 `shopping` 站点打开 Men shoes 类目页以浏览商品，task type 为 `NAVIGATE`。目标页面为 `__SHOPPING__/clothing-shoes-jewelry/men/shoes.html`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查最终响应经解析和规范化后为 `task_type:NAVIGATE`、`status:SUCCESS`；非 `RETRIEVE` 的 `retrieved_data` 按相应结构规范化，其原始值不改变本 case 的分数，物化的默认 `error_details:null` 也不是显式配置要求。`NetworkEventEvaluator` 配置 `last_event_only:true` 和 `should_not_exist:false`，检查满足发布版导航事件 predicate 的最后一个事件是否为规范化 URL `__SHOPPING__/clothing-shoes-jewelry/men/shoes.html` 的 `GET`，且响应状态为 `200`。只有 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 均得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 task score 仅在 `AgentResponseEvaluator` 和 `NetworkEventEvaluator` 都得 `1.0` 时为 `1.0`，并由 `TaskEvalResult.create` 组合两者。它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，分别询问响应能否规范化为无结构不匹配的 `NAVIGATE/SUCCESS`，以及最后 qualifying navigation event 是否为目标 URL 的 `GET` 并返回 `200`。success 要求两项均通过；failure 包括响应无法解析或规范化、HAR 缺少匹配的最后 qualifying event，或任何 evaluator error。undecided 被写为任一 artifact 不可用且没有保留的官方 evaluation result 记录缺失 component 分数；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：undecided 规则允许在 agent_response.json 或 network.har 缺失时，以留存的官方组件分数记录代替它们，尽管该记录无法重建已配置的 evaluator 检查，而且该材料也未将其声明为等效 artifact。
- 应如何修改：要求使用完整且来源有效的 agent_response.json 和 network.har 进行重建；从原生决策规则中删除组件分数替代项。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：undecided 规则使存在留存分数记录的 artifact 缺失情形处于未分类状态，并且只提及不可用，而未涵盖留存不完整、损坏或来源丢失。
- 应如何修改：仅将缺失、不完整、因留存而损坏或来源不确定，且会阻止重建的必需 artifact 定义为 undecided；同时继续将完整但无效的响应、缺少所需最后一次导航匹配的完整 trace、evaluator 可见的不匹配以及 evaluator errors 视为 failure。

## Case 268

### 原本 case 是什么

原始任务是在 `wikipedia` 和 `map` 站点找出离 Vinalhaven, ME 最近的 national park，取得其 relation ID 及骑行所需时间，task type 为 `RETRIEVE`。输出只能是包含整数 `relation_id` 与 `HH:MM:SS` 格式 `duration` 的对象列表，并要求使用 OSRM direction service、provided wiki，以及从 wiki 的 place official page 坐标搜索起点和终点。

### Benchmark 怎么测

`AgentResponseEvaluator` 按对象数组 schema 规范化响应，检查 `task_type:RETRIEVE`、`status:SUCCESS`，并以 `ordered:false` 精确匹配单元素结果 `[{"duration":"10:58:00","relation_id":2176999}]`，其中 `duration` 使用 `format:"duration"`、`relation_id` 使用 integer 类型。`NetworkEventEvaluator` 在 `last_event_only:true`、`should_not_exist:false` 下执行正常存在性检查，选取最后一个匹配的 `GET` evaluation event：规范化 OSRM route URL/path 必须匹配 `^.*/route/v1/.*/-68.2177005,44.3494709;-68.8315387,44.0478975.*$`，`Cookie` 必须匹配 `^.*_osm_directions_engine=fossgis_osrm_bicycle.*$`，响应状态为 `200`；`ignored_query_params_patterns:[".*"]` 会忽略所有 query-parameter 名称。两个 evaluator 都必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 仅在 `AgentResponseEvaluator` 匹配规范化响应、`NetworkEventEvaluator` 匹配所需的最后 OSRM bicycle-route event，且两者都得 `1.0` 时成立。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts：前者应匹配 `RETRIEVE`、`SUCCESS`、`relation_id 2176999` 和 `duration 10:58:00` 的无序单元素结果，后者应显示对应坐标、bicycle-engine Cookie 和 HTTP `200` 的最后匹配 `GET` route event。failure 是任一 evaluator 非 `1.0`，包括响应缺失、无效或不匹配、没有 qualifying route event、Cookie 或状态错误及 evaluator/orchestration error；undecided 用于 evaluator 输入在留存证据中缺失或截断、无法重建且无官方 evaluator result 消除不确定性的情形。它还给出两个非空 stronger conditions：`raw_retrieved_data_is_list` 要求原始 `retrieved_data` 确为 JSON array、不得依赖 scalar-to-singleton coercion；`prescribed_wiki_coordinate_method` 要求 `network.har` 显示两个端点的 provided-wiki official-place-page 请求及 coordinate-based map searches。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_active_query_ignore_rule`
- 为什么修改：NetworkEventEvaluator 的表述遗漏了已配置的 ignored_query_params_patterns 值 [".*"]；该值会主动使所有查询参数名称与 URL 匹配和比较无关。
- 应如何修改：在网络 artifact 问题和原生 success 规则中明确：根据已配置的 ".*" 名称模式，所有查询参数均被忽略，同时 normalization 后的路由 URL/path、GET 方法、最后事件选择、Cookie 和状态约束仍然适用。

## Case 269

### 原本 case 是什么

原始任务是在 `shopping` 站点打开“women shoes”分类页，并将价格筛选设为低于 $25；task type 为 `NAVIGATE`。官方指令是 `Open the "women shoes" category page filtered to under $25`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查响应经解析和规范化后，显式配置的 `task_type`、`status`、`retrieved_data` 分别匹配 `NAVIGATE`、`SUCCESS`、`null`；后者只检查最后一个被归类为导航的事件（`last_event_only: true`），要求它是对完整 URL `__SHOPPING__/clothing-shoes-jewelry/women/shoes.html` 的 `GET`、响应状态为 `200`，且查询参数 `price` 的唯一值为 `0-25`。正则 `^(?!price$).+$` 忽略所有非 `price` 查询参数，`decode_base64_query` 为 `false`，并且未配置请求体、响应内容、响应 cookie 或 header 的实质匹配条件。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求两个 evaluator 均为 `1.0`：最终响应通过规范化的 `NAVIGATE`/`SUCCESS` 比较，且 HAR 的最后导航事件是 women’s shoes 路径上的 `200 GET`，并在忽略非价格参数后满足 `price=0-25`；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 success 条件是两项检查都得 `1.0`；failure 包括响应格式错误、响应 evaluator 报错或不匹配，以及 HAR 错误、缺少最后导航事件、路径或价格错误、非 `GET`、非 `200` 等；证据缺失或截断而无法判断任一 evaluator 时记为 undecided。draft 实际只写了路径，没有明确完整 `__SHOPPING__` origin 也参与 URL 比较；`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`url_origin_omitted`
- 为什么修改：网络检查被描述为仅匹配 `/clothing-shoes-jewelry/women/shoes.html`，而配置的预期 URL 是 `__SHOPPING__/clothing-shoes-jewelry/women/shoes.html`，且规范化后的 URL 会纳入完整事件比较。
- 应如何修改：说明最后一个导航事件必须规范化为配置的 `__SHOPPING__` URL，包括其购物网站源、路径以及与评分相关的价格查询参数值。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_rule_under_specified`
- 为什么修改：artifact 问题和 failure 规则未明确将最后一次导航到错误源上的正确路径归类为 failure。
- 应如何修改：在网络 failure 规则中加入错误的规范化购物网站源或未匹配完整配置 URL 的情形，并使 success 条件明确要求匹配完整的配置 URL。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`semantic_minimality_gap`
- 为什么修改：简洁性是通过删去与评分相关的 URL 组成部分实现的，而没有保留完整的决定性语义。
- 应如何修改：保留紧凑结构，同时将仅描述路径的措辞替换为要求完整的规范化 `__SHOPPING__` URL。

## Case 279

### 原本 case 是什么

原始任务是在 `shopping` 站点检索可用的 Sony Bluetooth headphones，提供全部产品全名以及价格范围；task type 为 `RETRIEVE`。输出被要求仅为含 `"names"`（产品名列表）、`"min"` 和 `"max"`（数字）的对象，不附加其他细节。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查响应经 released parsing 和 schema normalization 后，显式配置的 `task_type`、`status`、`retrieved_data` 是否匹配 `RETRIEVE`、`SUCCESS` 及一个 singleton 结果对象。该对象必须只有 `names`、`min`、`max`：`names` 与配置的 12 个完整字符串作无序结构比较，`min` 为 `18.99`，`max` 为 `406`；`min`/`max` 使用 `format: "currency"` 的 number schema，`ordered: false` 表示数组顺序不计，但缺失、额外或不匹配元素仍会失败。materialized 的 `error_details: null` 不是 sparse config 中显式配置的比较字段。本 case 没有 `NetworkEventEvaluator`；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称唯一的 `AgentResponseEvaluator` 在解析、schema normalization 和无序结构比较后匹配 `RETRIEVE`/`SUCCESS`、12 个配置名称、`min: 18.99`、`max: 406` 时，benchmark success 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 作为回答比较的决定性 artifact，也把 `network.har` 列为重建评估上下文、排除 trace/input/orchestration error 的决定性 artifact；success 要求响应匹配且 evaluator 无 assertion/error，failure 包括响应非 mapping、字段或结果不匹配以及 normalization、trace parsing、evaluator 或 orchestration error，缺失任一 artifact 则列为 undecided。非空 stronger condition `literal_object_only` 另要求原始最终响应只能是裸 protocol JSON object，不得有说明文字、代码围栏或未知顶层字段，并要求结果 payload 是仅含 `"names"`、`"min"`、`"max"` 的真实对象而非 JSON 编码文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且没有对任何案例特定的网络事件条件进行评分。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：该检查清单规定，未保留 `network.har` 时结果为 undecided，尽管重建配置的响应比较并不需要其内容。
- 应如何修改：将 `undecided_if` 限定为 `agent_response.json` 缺失、不完整、损坏或来源不确定的情形；完整但格式错误或不匹配的响应仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_only_branches`
- 为什么修改：特定于 trace 的 artifact、failure 和 undecided 措辞为这个仅响应案例增加了非决定性的审查范围。
- 应如何修改：精简替换后的检查清单，使其原生证据和决策规则仅依赖完整响应以及数据包中定义的 evaluator 语义。

## Case 280

### 原本 case 是什么

原始任务是在 `shopping` 站点检索可用的 Anker chargers，返回全部产品全名及价格范围；task type 为 `RETRIEVE`。输出只能是包含 `"names"`、`"min"`、`"max"` 的对象，其中价格为数字，不能附加其他细节。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，比较经解析和 schema normalization 后显式配置的 `task_type: RETRIEVE`、`status: SUCCESS` 与 singleton `retrieved_data`。结果对象必须只有 `names`、`min`、`max`，其中 `names` 对配置的 12 个完整产品名进行无序、重复敏感的精确结构比较，`min` 为 `8.99`，`max` 为 `59.99`；价格字段采用 `format: "currency"` 的 number schema，`ordered: false` 只免除顺序要求，不允许缺失或额外元素、属性。materialized 的 `error_details: null` 并非 sparse config 显式比较字段，且没有 `NetworkEventEvaluator`。唯一 evaluator 的分数必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 task 280 只有在 sole `AgentResponseEvaluator` 得 `1.0`、响应规范化为 `RETRIEVE`/`SUCCESS`，且 `retrieved_data` 无序匹配含 12 个名称、`min: 8.99`、`max: 59.99` 的 singleton 对象时成功。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace 可解析、评估上下文有效及必要时从事件恢复 shopping base URL 写入 success；failure 包括响应、字段或结果不匹配以及 HAR、上下文或 orchestration error，响应或 trace 缺失/截断则为 undecided。非空 stronger condition `no_ignored_extra_details` 要求除必要 benchmark response envelope 外，原始最终响应不得包含该 names/min/max 对象之外的说明文字、未计分字段或其他用户可见内容。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：`network.har` 被表述为决定性证据，尽管任务 `280` 只有一个 `AgentResponseEvaluator`，且其配置的响应值不依赖 trace 内容。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为重建配置检查所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：success、failure 和 undecided 规则错误地将所保留 trace 的可用性或有效性纳入此案例特定的证据判定。
- 应如何修改：移除 trace 前置条件，并将 undecided 限定为 agent-response 证据缺失、被截断、损坏或来源未经证明的情形。继续将完整但无效的响应、不匹配或 evaluator 错误判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：额外的 HAR artifact 和特定于 trace 的条款使检查清单超出了证据审查所需的最小案例特定陈述。
- 应如何修改：删除 HAR artifact 及相关 trace 措辞，同时保留唯一 evaluator 的解析、规范化、比较、错误和分数组合规则。

## Case 282

### 原本 case 是什么

原始任务是在 `shopping` 站点检索可用的 Nike slide slippers，返回全部产品全名以及最低和最高价格；task type 为 `RETRIEVE`。输出须为仅含 `names` 列表、数字 `min` 和 `max` 的单个对象，不附加其他细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应执行 extraction 和 schema normalization，并比较显式配置的 `task_type`、`status`、`retrieved_data` 是否为 `RETRIEVE`、`SUCCESS` 及一个 singleton 对象。该对象必须只有 `names`、`min`、`max`，名称与配置的 9 个字符串作无序结构匹配，currency-normalized 边界分别为 `min: 27.6`、`max: 90.65`；`ordered: false` 不忽略缺失、额外或不匹配的对象、属性、名称或价格。materialized 的 `error_details: null` 未在 sparse task 中显式配置，因此不参与比较；也未配置 `NetworkEventEvaluator`。sole evaluator 得分为 `1.0` 时，满足“所有 evaluator 分数均为 `1.0`”的组合规则，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称唯一 `AgentResponseEvaluator` 在 extraction、schema normalization 和无序结构比较后匹配 `RETRIEVE`、`SUCCESS`、9 个配置名称、`min: 27.6`、`max: 90.65`，且没有 assertion/error 时，evaluator 与 task 均得 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace/context 可处理写入 success；failure 包括响应结构、字段或结果不匹配，以及 response/trace parsing、context、normalization、evaluator 或 orchestration error，响应或 trace 未充分保留且没有官方 `TaskEvalResult` 时列为 undecided。非空 stronger condition `strict_raw_response_format` 要求提交内容本身是独立有效 JSON，而不是含可提取 fenced JSON 的文字，并要求 `names` 是实际 JSON array、不能是 JSON 编码字符串。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的案例，`network.har` 被错误地列为决定性证据。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json`，作为重建配置检查所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_native_rules`
- 为什么修改：success、failure 和 undecided 规则使 trace 解析和保留影响了一个仅响应的配置检查。
- 应如何修改：从原生决策规则中移除 trace 解析、配置恢复和 trace 保留条款。将完整响应不匹配或响应 evaluator 错误判定为 failure，并仅在所保留的响应证据丢失或损坏时判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：trace artifact 和重复的 trace 依赖规则向原生检查清单添加了非决定性材料。
- 应如何修改：删除网络 artifact 和相关 trace 条款，同时保留响应 evaluator、组合和更强条件语义。

## Case 288

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点取得历史上取消次数最多的客户的电子邮箱；task type 为 `RETRIEVE`。官方指令是 `Get the email of the customer who has the most cancellations in the history`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，检查 released response parsing 与 normalization 后，显式配置的 `task_type`、`status`、`retrieved_data` 是否分别匹配 `RETRIEVE`、`SUCCESS` 和无序字符串 singleton `["coolcat321@hotmail.com"]`。`results_schema` 是 string array，`ordered: false` 表示数组顺序不计，但错误、缺失或额外元素不匹配；materialized 的 `error_details: null` 没有在 sparse config 中显式配置，因而不参与比较。本 case 没有 `NetworkEventEvaluator`。唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`；assertion、evaluator error 或非 `1.0` 分数均不满足成功条件。

### 原本 draft 是什么

原始 draft 声称 sole `AgentResponseEvaluator` 经解析和规范化后匹配 `RETRIEVE`、`SUCCESS` 及 `["coolcat321@hotmail.com"]`，且无 comparison assertion 或 evaluation error 时 benchmark success，唯一 evaluator 与 `TaskEvalResult` 均得 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把 trace parsing、context/config validation 和 orchestration 无错误写入 success；failure 包括响应结构、task type、status 或 email 结果不匹配，以及 trace/context/evaluator/orchestration error，无法确定实际提交的 response 或 trace 且无权威结果时为 undecided。非空 stronger condition `public_response_shape` 另要求保留的最终提交本身是不依赖代码块提取或 scalar coercion 的 JSON object，且 `retrieved_data` 必须按 `FinalAgentResponse` 编码为 array。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：`network.har` 被视为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，其预期的单元素 email 不依赖网络事件。尚未证实此案例启用了条件性环境修复路径。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整且保留来源信息的 `agent_response.json` 作为最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_gated_decision`
- 为什么修改：success、failure 和 undecided 规则将 trace 解析或 trace 来源作为判定唯一响应 evaluator 的必要条件。
- 应如何修改：移除以 trace 为前置条件的决策条款。将 undecided 限定为影响所提供确切响应的丢失、损坏或来源不确定情形；完整但无效、为 `null` 或不匹配的响应仍判定为 failure。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`generic_response_shape_stronger_condition`
- 为什么修改：新增的响应结构要求属于通用协议合规性要求，而不是获取已识别客户 email 这一指令中尚未满足的案例特定部分。
- 应如何修改：将 `stronger.additional_conditions` 设置为空列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_repetition`
- 为什么修改：原生 artifact 和决策规则中反复出现非决定性的 trace 处理，且缺乏依据的更强条件进一步增加了非必要材料。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator` 精简原生规则，仅保留 `agent_response.json` 作为决定性证据，并使 stronger 列表保持为空。

## Case 289

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：找出历史取消订单次数最多的客户，并以对象列表返回其姓名、电子邮件地址和电话号码。返回对象必须使用键 `"name"`、`"email"` 和 `"phone_number"`。

### Benchmark 怎么测

本任务只配置 `AgentResponseEvaluator`，它对响应进行解析，并按 `results_schema` 将 `retrieved_data` 规范化为对象数组；显式比较的期望字段为 `task_type: RETRIEVE`、`status: SUCCESS`，以及包含且仅包含 `{"email":"coolcat321@hotmail.com","name":"Samantha Jones","phone_number":"3055551212"}` 的单元素 `retrieved_data`。数组采用 `ordered=false` 的无序精确比较，要求基数、对象键和值均匹配；支持的 `performed_operation` 输入别名可在缺少 `task_type` 时提供该字段，而物化产生但未在 sparse expected 中配置的 `error_details` 不参与评分比较。无比较断言或 evaluator error 时该 evaluator 得分为 `1.0`，任何不匹配或错误得 `0.0`；由于只有这一个 evaluator，只有其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是响应和 trace 处理无误、唯一的 `AgentResponseEvaluator` 得分 `1.0`，且规范化结果精确匹配 `RETRIEVE`、`SUCCESS` 和 Samantha Jones 的单元素无序数据，因此 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，分别用于重建响应比较，以及解析 `NetworkTrace`、构造并验证 evaluation context。其规则将完整响应的解析、字段、条目、键或值不匹配，以及响应或 trace 解析、上下文验证或 evaluator 编排错误判为 failure；若任一 artifact 缺失或截断、无法重建输入，则判为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被列为决定性 artifact，尽管没有配置 `NetworkEventEvaluator`，而且 trace 不提供响应比较所需的任何案例特定值。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并以完整的 `agent_response.json` 为基础重建配置的原生检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：尽管完整的 `agent_response.json` 足以支持此配置检查，这些规则仍规定，只要 `network.har` 缺失或被截断，审查结果即为 undecided。
- 应如何修改：将 `undecided_if` 限定为完整的被评估 agent 响应丢失、被截断或来源验证失败的情形；原生判定不得要求 `network.har`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：特定于 trace 的 artifact 和决策条款增加了非决定性的案例范围，使检查清单无法保持紧凑和最小化。
- 应如何修改：删除特定于 trace 的 artifact，以及依赖 trace 的 success、failure 和 undecided 措辞，同时保留对配置的响应评估中 evaluator 错误的处理。

## Case 291

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：针对历史取消次数最多的客户，计算其最近取消订单中商品的总支出，并排除 shipping and handling。用户要求只返回数字，例如 `10.99`，不得附加其他内容。

### Benchmark 怎么测

本任务只配置 `AgentResponseEvaluator`，显式期望 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data: [148.8]`。`retrieved_data` 按 `{"type":"array","items":{"type":"number","format":"currency"}}` 做 currency 数值规范化，并以 `ordered=false` 对无序单元素数组进行精确值和基数比较；物化默认值 `error_details` 未在 sparse expected 中显式配置，因而不参与比较。解析、规范化和比较均无错误或失败断言时 evaluator 得分为 `1.0`，否则不为 `1.0`；唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 无错误地把响应规范化为 `RETRIEVE`、`SUCCESS` 和无序 currency 单元素 `[148.8]`，使 evaluator 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，后者用于验证 `NetworkTrace` 可解析并可在需要时支持环境 URL fallback。它将输入、上下文、规范化或 evaluator 编排错误，以及字段结构、缺失或 null 数据、数值或基数不匹配判为 failure；任一响应或 trace 缺失、截断、损坏或证据冲突则判为 undecided。非空 stronger condition `bare_numeric_user_response` 进一步要求 evaluator 转换前的原始用户可见回复只能是等于 `148.8` 的数字，不得含 JSON envelope、标签或解释文字，并以该原始回复为决定性证据。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`decisive-network-artifact`
- 为什么修改：`network.har` 被指定为决定性证据，尽管唯一配置的 evaluator 只比较 agent 响应，且不存在配置的 `NetworkEventEvaluator`。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为原生检查所需的最小充分运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network-dependent-decision-rules`
- 为什么修改：这些规则要求必须保留 trace 才能判定 success，并将 trace 丢失判定为 undecided，从而削弱了本可重建的仅响应判定。
- 应如何修改：基于完整的被评估响应判定 success 和一般 failure，并仅在因保留、完整性或来源信息丢失而无法恢复该确切响应时判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal-native-checklist`
- 为什么修改：非决定性的 trace 及规则中对它的重复依赖，使检查清单的范围超出了配置的案例检查所需范围。
- 应如何修改：删除 trace artifact 以及原生决策规则中对它的所有依赖，同时保留响应 evaluator 语义和仅限数字的更强条件。

## Case 292

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：找出历史取消次数最多的客户，并取得该客户的历史取消总数。任务没有另行指定特殊的输出格式。

### Benchmark 怎么测

本任务只配置 `AgentResponseEvaluator`，它提取并规范化响应后，比较显式配置的 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: [9]`。`retrieved_data` 使用数组元素类型为 `number` 的 schema，并以 `ordered=false` 执行无序精确比较，因此必须恰有一个数值 `9`；未出现在 sparse expected 中的物化默认字段 `error_details` 不参与比较。任何结构、字段、数值、基数不匹配或 evaluator error 都使该 evaluator 不得 `1.0`；由于它是唯一 evaluator，只有其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称官方成功要求唯一的 `AgentResponseEvaluator` 将响应解析、规范化为 `RETRIEVE`、`SUCCESS` 和无序 numeric singleton `[9]`，不产生断言或错误，并令 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，后者用于 trace 解析、evaluation context 构造及可能的环境 URL fallback。它将响应的结构、类型、状态或数据缺失、null、错误或额外元素，以及响应或 trace 解析、上下文或 evaluator 编排错误判为 failure；若原始响应或 trace 因事后丢失或损坏而无法重建，且没有保留的官方结果，则判为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 仅因通用解析和环境回退行为而被列为决定性证据，尽管唯一配置的 evaluator 比较 `agent_response_raw`，且配置的数值结果没有依赖 trace 的规范化。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_trace_decision_rules`
- 为什么修改：这些规则规定，只要 `agent_response.json` 或 `network.har` 任一丢失，结果便无法判定，并引入了特定于 trace 的 success 和 failure 条件，尽管重建此配置的响应检查并不需要 trace。
- 应如何修改：仅基于完整保留的 agent 响应和已发布的 `AgentResponseEvaluator` 语义判定原生 success、failure 和 undecided；仅在该响应于运行后丢失或来源验证失败时判定为 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nondecisive_trace_material`
- 为什么修改：trace artifact 及其回退/解析分支为原本紧凑的仅响应检查清单增加了非决定性材料。
- 应如何修改：删除网络特定的 artifact 和规则文本，同时保留响应比较、evaluator 错误处理和全 evaluator 组合规则。

## Case 294

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：取得 ChatGPT 仓库的 SSH clone URL。用户要求只返回 URL，不得附加任何说明。

### Benchmark 怎么测

本任务只配置 `AgentResponseEvaluator`；显式期望 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 无序精确匹配单元素 `git@__SSH_HOST__:convexegg/chatgpt.git`。`retrieved_data` 按 URL 字符串数组 schema 使用运行时环境配置进行 URL 规范化/derendering，并以 `ordered=false` 检查准确基数和值；物化但未显式配置的 `error_details` 不比较。evaluator 执行前，编排会验证 GitLab 环境 URL；若预配置 URL 缺失或无效，则条件性地从 `network.har` 事件导出运行时环境，fallback 必需却无法完成时会产生任务级错误。编排成功且唯一 evaluator 无断言或错误并得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 经支持的解析和 URL 规范化后匹配 `RETRIEVE`、`SUCCESS` 与单元素 `git@__SSH_HOST__:convexegg/chatgpt.git`，从而使 evaluator 和 `TaskEvalResult.score` 都为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact，用于重建运行时 URL derendering 后的比较，没有把条件性需要的 `network.har` 列入决定性证据。它将非对象响应、规范化或 evaluation error、比较键不匹配，以及缺失、null、不可规范化或不等于准确单元素 SSH URL 的数据判为 failure；只有响应未保留或被截断时判为 undecided。非空 stronger condition `no_unscored_response_content` 还要求原始响应不得含代码围栏、周边文字或未评分的额外字段，只允许 `task_type`、`status` 和单元素 SSH URL `retrieved_data`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_environment_validation_semantics`
- 为什么修改：原生 success 仅以 `AgentResponseEvaluator` 表述，遗漏了 evaluator 执行前已发布的环境验证和基于 trace 的回退机制。
- 应如何修改：说明任务编排必须完成，并描述当配置的环境 URL 缺失或无效时，如何有条件地使用网络 trace 事件推导站点环境 URL。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`conditionally_decisive_trace_omitted`
- 为什么修改：唯一列出的 artifact 是 `agent_response.json`，尽管该数据包表明 `network.har` 可以提供响应 URL 反渲染所使用的配置。
- 应如何修改：当无法确认存在有效的预配置环境 URL 时，将完整的 `network.har` 添加为条件性决定证据；保留 `agent_response.json` 作为主要的响应比较 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_failure_and_undecided_rules`
- 为什么修改：这些规则遗漏了配置/回退错误，也未规定在运行后丢失条件性必需的 trace 或来源信息而无法重建时可判定为 undecided。
- 应如何修改：将实际的编排/配置 failure 归类为原生 failure，并仅在运行后响应或条件性必需的 trace/来源信息丢失或损坏时判定为 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`runtime_dependency_not_operationalized`
- 为什么修改：该检查清单要求审查者应用运行时 URL 反渲染，但没有列出足够的保留证据来解析所描述的条件性运行时依赖。
- 应如何修改：明确说明 trace 依赖及相应的证据丢失规则，同时保留检查清单在其他方面紧凑且与具体运行无关的结构。

## Case 302

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `NAVIGATE`：打开状态为 `"out of delivery"` 的最近一笔订单的详情页。任务要求的是页面导航，而不是检索并返回数据。

### Benchmark 怎么测

本任务依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查响应规范化后显式字段为 `task_type: NAVIGATE`、`status: NOT_FOUND_ERROR`、`retrieved_data: null`，其中 null schema 与非 retrieve 任务规则适用，未显式配置的 `error_details` 不参与比较。后者要求 evaluator 识别的最后一个 document navigation（`last_event_only=true`）规范化后为对 `__SHOPPING__/sales/order/history/` 的 `GET`，且 `response_status` 为 `200`；配置中 `should_not_exist=false`、`decode_base64_query=false`，没有 query、post data、header、cookie 或 response content 的额外期望过滤条件。两项 evaluator 分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求两个 evaluator 都得 `1.0`：`AgentResponseEvaluator` 接受 `NAVIGATE/NOT_FOUND_ERROR` 且 `retrieved_data` 为 null 的响应，`NetworkEventEvaluator` 接受最后一个已识别导航为对 `__SHOPPING__/sales/order/history/` 的 `GET` 且响应状态为 `200`。它把 `agent_response.json` 和 `network.har` 分别列为两个检查的决定性 artifacts；任一检查明确失败或报错即为 failure。原 draft 规定只要任一 artifact 缺失、不可读或截断，导致无法同时应用两个检查，就判为 undecided，未处理另一完整 artifact 已足以证明失败时的重叠情形。非空 stronger condition `task_consistent_order_selection` 进一步要求证据证明：若存在 `"out of delivery"` 订单，最终打开的是其中最近一笔的详情页；只有完全不存在此类订单时，history page 上的 `NOT_FOUND_ERROR` 才满足该条件，并以 `network.har` 中的列表响应和详情页导航为证据。

### 需要修改的部分

#### 修改项 1：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_overrides_conclusive_failure`
- 为什么修改：undecided 条件过于宽泛，因为当另一个完整 artifact 已经确定原生 failure 时，artifact 丢失并不会妨碍重建。
- 应如何修改：将 undecided 限定为因保留、完整性或来源信息丢失而无法判定合取结果的情形，并补充说明，任何已经确定的 evaluator failure 仍为原生 failure。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`overlapping_terminal_rules`
- 为什么修改：`fail_if` 和 `undecided_if` 可同时适用于同一证据状态，导致检查清单内部不一致。
- 应如何修改：通过从 undecided 中排除完整保留的证据已证明任一 evaluator 分数不为 `1.0` 的所有情况，使这些规则保持一致。

## Case 304

### 原本 case 是什么

原始任务是在 GitLab 的当前仓库 `a11yproject/a11yproject.com` 中，回答 Eric Bailey 从 2023 年 2 月初到 5 月末共提交了多少次 commit。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：它对提交响应进行提取和规范化，并比较显式配置的 `task_type`、`status` 和 `retrieved_data`；期望分别为 `RETRIEVE`、`SUCCESS` 和数值数组 `[14]`，其中 `results_schema` 是 number array，`ordered:false` 表示无序精确比较，不允许缺少、额外或不同的规范化元素。`performed_operation` 在适用时可作为缺失 `task_type` 的别名；物化产生的默认 `error_details:null` 不是显式比较字段。没有配置 `NetworkEventEvaluator`，因此没有 filter 或 last-event 匹配语义，`network.har` 也不参与这个数值响应比较。唯一 evaluator 的分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`；任何非 `1.0` 分数或 evaluator/task-evaluation error 均使任务分数为 `0.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 将响应规范化为 `task_type=RETRIEVE`、`status=SUCCESS` 和无序单元素数值结果 `[14]`，从而 evaluator 与 `TaskEvalResult.score` 都为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts：前者用于检查响应解析、结构和值，后者用于构造 `NetworkTrace` 及必要时推导 GitLab base URL。其 success 规则要求比较无断言失败且没有缺失或额外元素；fail 规则涵盖无效结构、字段不匹配、`retrieved_data` 缺失或为 null、数值不是 `14`、存在额外元素，以及 evaluator、任务上下文或编排错误。undecided 被定义为精确 evaluator 输入未保留或不可读，且没有足以确认处理响应和结果的权威 `TaskEvalResult`；已保留的 malformed/null 响应或显式 `ERROR` 被归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_har`
- 为什么修改：尽管此案例只有一个 `AgentResponseEvaluator`，且 HAR 不会影响其所配置的对 `RETRIEVE`、`SUCCESS` 和数值单例 `14` 的比较，但 `network.har` 被视为决定性证据。
- 应如何修改：仅保留完整的 `agent_response.json` 作为决定性 artifact，并使所有原生重建规则均基于该 artifact 运作。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`narrow_undecided_rule`
- 为什么修改：`undecided` 规则允许缺失或不可读的非决定性 evaluator 输入阻止作出判定，并引用了一个未列出的 `TaskEvalResult` 替代项。
- 应如何修改：将 `undecided` 限定为 `agent_response.json` 的丢失、损坏或来源失败，且该问题确实阻止重建；明确将完整但格式错误、为 `null`、不匹配或产生错误的响应继续归为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_compact_coherence`
- 为什么修改：不必要的 HAR 条目和未命名的替代结果 artifact，使证据模型比这个单 evaluator 案例所需的范围更广且连贯性更差。
- 应如何修改：移除 HAR 条目和 `TaskEvalResult` 证据替代项，同时保留正确的 evaluator 和组合语义。

## Case 305

### 原本 case 是什么

原始任务是在 GitLab 当前仓库 `a11yproject/a11yproject.com` 中，回答 Philip 在 2023 年 1 月提交了多少次 commit。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，用于解析、规范化并比较响应中显式配置的 `task_type`、`status` 和 `retrieved_data`；期望为 `RETRIEVE`、`SUCCESS` 和 `[0]`。`retrieved_data` 按 number array schema 规范化，并以 `ordered:false` 做无序精确集合比较，因此必须恰为一个数值 `0`；物化默认值 `error_details:null` 不参与比较。没有配置网络事件 evaluator，因而没有 filter 或 last-event 语义，`network.har` 的内容不改变该响应比较。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`；解析、规范化、比较或 evaluator 错误会产生非 `1.0` 分数并使任务分数为 `0.0`。

### 原本 draft 是什么

原始 draft 声明任务成功当且仅当唯一 `AgentResponseEvaluator` 接受规范化后的 `task_type=RETRIEVE`、`status=SUCCESS` 和无序精确数值集合 `[0]`，并取得 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并在 success 中要求响应和网络 trace 均可无错误求值。fail 包括 artifact 解析或 evaluation error、响应缺失或无效、类型或状态不匹配，以及 `retrieved_data` 未规范化为精确的 `[0]`；undecided 则指无法确定实际提交的响应或 trace，且没有与这些输入绑定的 evaluator result。其非空 stronger condition `public_response_schema` 额外要求原始 artifact 本身是 `FinalAgentResponse` JSON object，且 `retrieved_data` 必须字面编码为数值数组 `[0]`，不能依赖 fenced wrapper 提取或 scalar coercion。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unsupported_network_native_prerequisite`
- 为什么修改：原生成功以所提供的网络跟踪可被评估为条件，尽管任务 `305` 仅配置了 `AgentResponseEvaluator`，且该 evaluator 读取 `agent_response_raw`。
- 应如何修改：从 `checked_by` 和所有原生成功前提条件中移除网络跟踪可解析性；仅描述已发布的解析、normalization，以及对稀疏原始预期响应中三个字段的比较。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，仅仅因为它是批处理要求的 artifact，而不是因为某个已配置的检查会使用其内容。
- 应如何修改：仅保留完整的 `agent_response.json` 作为此案例的原生决定性 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`network_dependent_decision_rules`
- 为什么修改：这些规则可能根据无关跟踪的解析或留存情况，将原生结果标记为 `success`、`failure` 或 `undecided`。
- 应如何修改：以对精确且完整的响应应用 `AgentResponseEvaluator` 为依据判定 `success` 和 `failure`，并仅在该响应的留存、完整性或来源丢失时判定为 `undecided`。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：不必要的网络 artifact 和重复的网络要求，使原生部分的范围超出已配置案例语义的需要。
- 应如何修改：移除网络 artifact 和所有依赖网络的条款，同时保留响应 evaluator 的细节和有效的更强条件。

## Case 306

### 原本 case 是什么

原始任务是在 GitLab 当前仓库 `a11yproject/a11yproject.com` 中，回答 Anthony 在 2022 年 8 月至 9 月期间提交了多少次 commit。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对完整响应进行提取和规范化，比较显式配置的 `task_type`、`status` 与 `retrieved_data`，期望依次为 `RETRIEVE`、`SUCCESS` 和 `[0]`。`retrieved_data` 使用 number array schema，并按 `ordered:false` 做无序精确比较，故只能包含一个数值 `0`；物化默认的 `error_details:null` 不属于显式比较项。没有配置 `NetworkEventEvaluator`，所以不存在 filter 或 last-event 语义，网络 trace 不影响该数值响应比较。由于只有一个 evaluator，只有其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`；任何不匹配或 evaluator error 都导致非 `1.0` 任务分数。

### 原本 draft 是什么

原始 draft 声明唯一 `AgentResponseEvaluator` 在解析和规范化后确认 `task_type=RETRIEVE`、`status=SUCCESS`、无序数值数组精确等于 `[0]` 时得分 `1.0`，继而 `TaskEvalResult` 得分 `1.0`。它把 `agent_response.json` 与 `network.har` 均视为决定性 artifacts，后者用于检查 trace 是否足以构造 evaluation context 和必要的 environment-URL fallback。success 要求保留输入可复现无错误的 evaluator `1.0`；fail 包括响应缺失或无效、类型或状态错误、`retrieved_data` 缺失、null、错误或含额外值，以及 evaluator 或 orchestration error。undecided 指事后材料无法确定实际提供的响应或 trace；若明确记录了缺失、无效或不匹配输入，则归为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`redundant_network_artifact`
- 为什么修改：此案例唯一配置的 evaluator 比较 agent 响应，且预期检索值为数值，但 `network.har` 被错误地指定为决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为唯一的决定性运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_undecided`
- 为什么修改：`undecided` 规则将无法确认所提供的跟踪视为阻碍结果判定，尽管重建已配置的响应比较并不需要该跟踪。
- 应如何修改：将 `undecided_if` 限定为影响完整 agent 响应的完整性、留存或来源丢失；将完整但无效、为 `null` 或不匹配的响应继续归为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_evidence`
- 为什么修改：冗余的跟踪 artifact 和依赖跟踪的 `undecided` 条件，使原生核对清单比此案例的已配置语义所要求的更大、更严格。
- 应如何修改：删除跟踪 artifact 和所有依赖跟踪的原生判定措辞，同时保留响应比较、evaluator 错误处理和空的更强条件列表。

## Case 308

### 原本 case 是什么

原始任务是在 GitLab 上取得 `primer/design` 项目中 commit 数最多的一个或多个用户的 username。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 接受对象或可解析成对象的响应文本，包括支持的 JSON 和 fenced-JSON；它只规范化稀疏 expected 中显式配置的 `task_type`、`status`、`retrieved_data`，忽略其他未配置 raw fields，并在缺少 `task_type` 时允许 `performed_operation` 作为别名。期望是 `RETRIEVE`、`SUCCESS` 和字符串数组 `["shawn.allen@github.com"]`；scalar `retrieved_data` 会被包装成单元素集合，再按 string array schema 规范化并以 `ordered:false` 做包含长度和重复次数的无序精确比较。物化默认的 `error_details:null` 不参与比较；未配置 filter、last-event 或 `NetworkEventEvaluator`。唯一 evaluator 无错误且无失败断言时得分 `1.0`，也只有此时 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声明成功条件是唯一 `AgentResponseEvaluator` 将响应规范化为 `task_type=RETRIEVE`、`status=SUCCESS`，且 `retrieved_data` 无序精确等于 `["shawn.allen@github.com"]`，从而 evaluator 和 `TaskEvalResult.score` 均为 `1.0`。它只将 `agent_response.json` 列为决定性 artifact。success 要求没有 evaluator error 或比较断言且结果仅含该字符串；fail 包括非对象响应、缺失或错误的 `task_type/status`、缺失、空、错误或额外的 retrieved data，undecided 则是该 artifact 缺失或不可读。其非空 stronger condition `retrieved_data_array_shape` 额外要求 raw `retrieved_data` 必须是包含该字符串的 JSON array，而不能是经 evaluator coercion 接受的 scalar。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete_agent_response_semantics`
- 为什么修改：原生主张将影响分数的解析和 normalization 隐藏在“允许的解析”之后，且未说明 `performed_operation` 别名；因此，其 `failure` 规则可能将可接受的响应错误分类。
- 应如何修改：说明适用的 JSON/代码块解析、`task_type`/`performed_operation` 回退、仅比较稀疏配置的三个预期字段、将标量 `retrieved_data` 强制转换为单元素集合、字符串数组 normalization，以及精确的无序比较。明确说明默认补齐的 `error_details` 和其他原始 key 不参与比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_missing_task_type_failure`
- 为什么修改：`fail_if` 将缺失 `task_type` 判为 `failure`，但未考虑已发布的旧版 `performed_operation` 别名。
- 应如何修改：根据 normalization 后的有效任务类型定义 `failure`，明确仅当 `task_type` 缺失时才允许使用 `performed_operation`；继续将完整但格式错误或为 `null` 的响应以及真正的不匹配视为 `failure`。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported_array_shape_stronger_condition`
- 为什么修改：拟议的原始数组要求并非官方用户意图的一部分，而是一种通用的协议形状偏好，不是此案例特有的更强任务结果。
- 应如何修改：移除 `retrieved_data_array_shape`，并使用空的 `stronger.additional_conditions` 列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`operational_minimality`
- 为什么修改：该核对清单将含糊的解析引用、范围过宽的失败示例和不必要的更强条件组合在一起，因此不是对决定性语义的紧凑、自包含表述。
- 应如何修改：用简洁的操作规则替换含糊的解析引用，纠正对别名敏感的失败条件，并移除更强条件。

## Case 309

### 原本 case 是什么

原始任务是在 GitLab 上返回 `thoughtbot/administrate` 项目中 commit 数最多的一个或多个用户的 username。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；它可处理对象、JSON 文本及支持的 fenced-JSON，并只比较稀疏 expected 显式设置的 `task_type`、`status` 和 `retrieved_data`，在缺少 `task_type` 时可由 `performed_operation` 补充，其他未配置 raw fields 被忽略。期望为 `RETRIEVE`、`SUCCESS` 和字符串结果 `["wright.grayson@gmail.com"]`；非空 scalar `retrieved_data` 会包装为单元素集合，随后按 string array schema 规范化并以 `ordered:false` 做保留长度与重复次数的无序精确比较，缺失、重复或额外项均不匹配。物化默认的 `error_details:null` 不参与比较，也没有配置 filter、last-event 或 `NetworkEventEvaluator`。唯一 evaluator 必须无 error、无失败断言并得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`；否则为 `0.0`。

### 原本 draft 是什么

原始 draft 声明官方 evaluation 无错误，且唯一 `AgentResponseEvaluator` 接受规范化的 `task_type=RETRIEVE`、`status=SUCCESS` 和无序字符串数组 `["wright.grayson@gmail.com"]` 时，`TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将响应、trace、context、orchestration 或 evaluator 的解析与运行无错误纳入 success。fail 包括响应结构或三个比较值的任何断言失败，以及响应或 trace 解析、context 构造或 evaluator error；undecided 指无法确定实际提交的响应和 trace，且没有官方 `TaskEvalResult` 可判定。其非空 stronger condition `verify_top_commit_usernames` 要求保留的 GitLab 证据证明所有返回值确为 commit 数并列最高者的显示 username，且 `agent_response.json` 精确返回该集合；对应 artifacts 是 `agent_response.json` 与包含 contributor counts、所有并列者及显示 username 的 `network.har`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete_response_parsing_semantics`
- 为什么修改：该核对清单未以可操作方式描述影响分数的响应解析和 normalization 行为，因此无法依据其措辞可靠地对 fenced JSON 响应、旧版 `performed_operation`、标量 `retrieved_data` 值或未配置的额外原始字段等情况进行分类。
- 应如何修改：简洁说明如何将字符串转换为响应对象；normalization 使用稀疏预期配置中明确存在的三个字段；`performed_operation` 可提供 `task_type`；其他原始字段（包括 `error_details`）在此处不参与比较；以及非空标量 `retrieved_data` 在 schema normalization 前会被包装成包含一个元素的数组。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace`
- 为什么修改：`network.har` 被列为原生决定性证据，仅用于确认跟踪/上下文可读，尽管此案例仅配置了 `AgentResponseEvaluator`，且其实际值来自 `agent_response_raw`。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，仅将其保留在更强条件下；在该条件下，GitLab 响应正文可用于证实贡献者数量和用户名。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_failure_undecided_conflict`
- 为什么修改：草案一方面将已留存跟踪的解析失败判为 `failure`，另一方面又将跟踪不可用或被截断判为 `undecided`，但重建已配置的响应比较并不需要该跟踪。
- 应如何修改：原生 `success` 和 `failure` 应基于完整且精确的 agent 响应。将完整但无效或不匹配的响应视为 `failure`，并仅在该响应丢失、被改动、被截断或来源不确定时判定为 `undecided`。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_evidence`
- 为什么修改：额外的原生网络 artifact 及其相互冲突的判定分支，违反了所要求的最小性和内部连贯性。
- 应如何修改：仅使用 `agent_response.json` 作为原生决定性证据，并消除原生跟踪可读性分支；将此案例特有的 HAR 用途隔离在更强条件下。

## Case 311

### 原本 case 是什么

原始任务是在 `gitlab` 站点查找 Pytorch GAN 项目中提交次数最多的用户的用户名，官方指令为 “Get the username(s) of the user(s) with the most commits to the Pytorch GAN project”。这是 revision `2` 的 `RETRIEVE` 任务。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，比较稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data`，不比较物化时补入的 `error_details: null`。经发布版提取、解析和归一化后，`task_type` 应为 `RETRIEVE`（缺少该字段时接受旧别名 `performed_operation`），`status` 应为 `SUCCESS`，`retrieved_data` 按字符串数组 schema 精确匹配无序单元素集合 `["eriklindernoren@live.se"]`；`ordered` 为 `false`。只有该 evaluator 得分为 `1.0` 时，按“所有 evaluator 分数均为 `1.0`”的组合规则，`TaskEvalResult.score` 才为 `1.0`；不匹配或 evaluator/task error 会得到非 `1.0` 分数。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 将响应归一化为 `RETRIEVE`、`SUCCESS` 和精确无序单元素集合 `["eriklindernoren@live.se"]`，从而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts：前者用于核对响应，后者用于确认 trace 可加载且 evaluation context 可构造；success 要求响应与 trace 均可重评，failure 包括响应缺失或不匹配、HAR 无法加载以及编排错误，undecided 则是无法恢复确切响应或 trace。该 draft 还把缺少 `task_type` 一概写成 failure，并未注明可接受 `performed_operation` 别名。非空 stronger condition `username_semantics` 要求证据证明返回值确为 Pytorch GAN 最大提交者的 GitLab 账户用户名，而不只是原生 evaluator 接受的邮箱形式值，并以 `agent_response.json` 与 `network.har` 为证据。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias`
- 为什么修改：原生 `failure` 规则称缺失 `task_type` 会导致 `failure`，但已发布的 normalization 在 `task_type` 缺失时接受 `performed_operation` 作为旧版别名。
- 应如何修改：限定该规则，使任务类型仅在 `task_type`，或当 `task_type` 缺失时的 `performed_operation`，无法 normalization 为 `RETRIEVE` 时才失败。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace`
- 为什么修改：`network.har` 被列为决定性的原生证据，尽管唯一配置的 `AgentResponseEvaluator` 仅提取并比较 agent 响应。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性 artifact。如有需要，仅在单独的更强条件下保留 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_and_alias_decision_rules`
- 为什么修改：原生 `success` 和 `undecided` 规则依赖该跟踪，且 `fail_if` 遗漏了可接受的 `performed_operation` 别名。
- 应如何修改：基于完整的 agent 响应重建原生 `success`、`failure` 和 `undecided`；移除跟踪加载和跟踪留存条件，并准确说明旧版任务类型别名的行为。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_har_rules`
- 为什么修改：原生核对清单包含冗余的 HAR artifact、失败和留存条款，而重建已配置的响应比较并不需要这些内容。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并移除对应的原生 `success`、`failure` 和 `undecided` 条款；将此案例特有的更强条件单独保留。

## Case 312

### 原本 case 是什么

原始任务是在 `gitlab` 站点获取 csvkit 项目中提交次数最多的用户的用户名，官方指令为 “Get the username(s) of the user(s) with the most commits to the csvkit project”。这是 revision `2` 的 `RETRIEVE` 任务。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，其稀疏配置比较 `task_type`、`status` 和 `retrieved_data`，不比较物化默认值 `error_details: null`。发布版 evaluator 对完整响应进行提取、解析和字段投影；`task_type` 应归一化为 `RETRIEVE`（缺失时可由旧别名 `performed_operation` 提供），`status` 应为 `SUCCESS`，`retrieved_data` 按字符串数组 schema 精确匹配无序单元素集合 `["staringmonkey@gmail.com"]`，因此缺少、额外、不同或重复项都会不匹配，而顺序不影响比较。任务采用全合取组合：唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`；evaluator 或编排错误计为 `0.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 写为响应归一化到 `RETRIEVE`、`SUCCESS`，且 `retrieved_data` 精确等于无序单元素集合 `["staringmonkey@gmail.com"]`，使唯一的 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并称 success 要求两者均被接受，failure 包括响应字段或数据不匹配、任一 artifact 无法加载以及 evaluator/编排错误。undecided 被定义为任一必需 artifact 缢失或不可读、且没有保留的官方 `TaskEvalResult` 可确定输入和分数。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_network_trace`
- 为什么修改：`network.har` 被呈现为决定性证据，尽管唯一配置的 evaluator 是 `AgentResponseEvaluator`，且数据包所表示的跟踪内容均不影响此案例的响应比较。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小且充分的留存证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decisions`
- 为什么修改：判定规则要求存在可接受的跟踪才能判定 `success`，并对跟踪加载或留存情况进行分类，尽管该跟踪对已配置的检查并非决定性证据。
- 应如何修改：使 `success` 和 `failure` 取决于对完整的已留存响应应用已发布的 `AgentResponseEvaluator` 语义。将 `undecided` 限定为响应的留存、完整性或来源丢失，同时将完整但无效或不匹配的响应视为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_body`
- 为什么修改：对于这个单响应 evaluator 案例，跟踪专用的 artifact 和判定措辞增加了不必要的原生范围，并削弱了内部连贯性。
- 应如何修改：删除跟踪专用的 artifact 和规则，仅保留精确的响应解析、已配置字段的 normalization、无序单例比较、分数组合以及响应证据完整性规则。

## Case 313

### 原本 case 是什么

原始任务是在 `shopping` 站点获取客户服务电话号码，官方指令为 “Get the customer service phone number”。这是 revision `2` 的 `RETRIEVE` 任务。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 只比较稀疏配置明确指定的字段：经发布版解析和归一化后，`task_type` 为 `RETRIEVE`、`status` 为 `NOT_FOUND_ERROR`、`retrieved_data` 为 `null`；物化默认值 `error_details: null` 不参与比较。`results_schema` 为 `{"type":"null"}`，且没有 shopping 站点内容或网络内容 evaluator，因此原生评分不核验页面上是否存在电话号码。结构比较没有 assertion 或 evaluator error 时该 evaluator 得分为 `1.0`；因仅有这一个 evaluator，只有其得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是响应归一化为 `{task_type: RETRIEVE, status: NOT_FOUND_ERROR, retrieved_data: null}`，唯一的 `AgentResponseEvaluator` 无 assertion 或 error，因而 evaluator 与 task 分数均为 `1.0`；它也明确写道不检查 shopping 站点内容。它将 `agent_response.json` 和一个名为 `TaskEvalResult evaluator report` 的记录列为决定性 artifacts；failure 包括响应不可比较、字段缺失或不匹配、`retrieved_data` 非 null、额外归一化键不匹配，以及 evaluator 或任务编排错误，undecided 则是在既无足够响应也无完整 `TaskEvalResult` 时。非空 stronger condition `substantiate_customer_service_outcome` 要求以 `agent_response.json` 和 `network.har` 中保留的 shopping 内容佐证结果：若页面提供电话号码，就必须以 `SUCCESS` 返回该号码；只有相关内容确无号码时，`NOT_FOUND_ERROR` 与 null 才可接受。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_native_evidence`
- 为什么修改：原生证据列表添加了一个 `TaskEvalResult` evaluator 报告，尽管仅凭完整的 `agent_response.json` 即可重建唯一配置的 `AgentResponseEvaluator` 检查，且数据包并未声明此类报告为已留存 artifact。
- 应如何修改：从 `decisive_artifacts` 中移除 `TaskEvalResult` evaluator 报告，并使 `agent_response.json` 成为唯一的原生决定性 artifact；仅为明确的更强内容证实条件保留 `network.har`。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`redundant_report_and_undecided_branch`
- 为什么修改：冗余的报告 artifact 和 `undecided` 规则中基于报告的替代项，使该核对清单不够紧凑。
- 应如何修改：删除冗余 artifact，并将原生 `undecided` 状态限定为影响 `agent_response.json` 的留存、完整性或来源丢失；明确将完整但无效或为 `null` 的响应继续归为 `failure`。

## Case 314

### 原本 case 是什么

原始任务是在 `gitlab` 站点获取 primer/design 仓库按 commit count 排名前三的贡献者全名，官方指令为 “Get the full names of the top 3 contributors (by commit count) to primer/design repo”。这是 revision `2` 的 `RETRIEVE` 任务。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，比较稀疏配置中的 `task_type`、`status` 和 `retrieved_data`，不比较物化产生的 `error_details: null`，额外原始响应键也不影响该 evaluator。经发布版解析和归一化后，`task_type` 必须为 `RETRIEVE`（缺少时接受 `performed_operation` 别名），`status` 必须为 `SUCCESS`，`retrieved_data` 按字符串数组 schema 精确匹配无序多重集 `Shawn Allen`、`Inayaili León`、`Aurora Pleguezuelo`；`ordered` 默认为 `false`，所以排列不影响结果，但缺失、重复或额外名字会不匹配。唯一 evaluator 得分必须为 `1.0`，全合取组合才令 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原 draft 声称 success 要求唯一的 `AgentResponseEvaluator` 得分 `1.0`：响应归一化为 `RETRIEVE`、`SUCCESS`，并以无序方式精确包含 `Shawn Allen`、`Inayaili León` 和 `Aurora Pleguezuelo`，继而使 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和未由 packet 声明保留的 `Official TaskEvalResult record` 都列为决定性 artifacts，并分别用来检查响应及确认 evaluator/task 分数；success 分成响应匹配和评估无错误两项，failure 包括保留的失败分数、字段或姓名集合不匹配及 evaluator/编排错误。undecided 是证据缺失、不可读或无法关联到该 run，导致既不能确定 evaluator 可见响应，也不能确定可信官方 `TaskEvalResult`；完整但无效的响应则被写为 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`undeclared_redundant_result_artifact`
- 为什么修改：“官方 `TaskEvalResult` 记录”既不是数据包声明的已留存 artifact，也不是依据所要求的完整 agent 响应重建这个唯一 `AgentResponseEvaluator` 检查所必需的。
- 应如何修改：移除该 artifact，并使完整的 `agent_response.json` 成为唯一的决定性 artifact。继续仅将 `TaskEvalResult.score` 描述为由重建的 evaluator 分数得出的已发布组合结果。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`matching_response_without_score_record_unclassified`
- 为什么修改：当新增的分数记录缺失时，一个通过已发布解析、normalization 和比较的完整响应并不能明确确立 `success`；同时，由于该响应可用，`undecided` 规则也不适用。
- 应如何修改：说明对完整响应应用已发布的 evaluator 语义，足以重建 `success` 或 `failure`。将 `undecided` 限定为 `agent_response.json` 本身的丢失、损坏或来源失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_and_incoherent_body`
- 为什么修改：额外的结果 artifact 重复了确定性的分数结论，并在 `success` 与 `undecided` 规则之间造成了本可避免的不一致。
- 应如何修改：使用一个完整的响应 artifact 和简洁、穷尽的规则：将可重建的匹配归为 `success`，将任何可重建的不匹配或 evaluator 错误归为 `failure`，并仅将无法重建的响应证据归为 `undecided`。

## Case 316

### 原本 case 是什么

原始任务是在 `gitlab` 站点获取 facebook"s guide on building react apps 仓库按 commit count 排名前三的贡献者邮箱地址，官方指令为 “Get the email addresses of the top 3 contributors (by commit count) to facebook"s guide on building react apps repo”。这是 revision `2` 的 `RETRIEVE` 任务。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对响应进行 JSON/code-block 提取、明确 expected 字段投影和归一化，只比较 `task_type`、`status`、`retrieved_data`，不比较物化默认值 `error_details: null` 或额外原始键。`task_type` 应为 `RETRIEVE`（适用时接受 `performed_operation` 别名），`status` 应为 `SUCCESS`，`retrieved_data` 按字符串数组 schema 精确匹配无序三元素多重集 `{dan.abramov@gmail.com, timer150@gmail.com, ian@iansutherland.ca}`；缺失、错误、重复、额外、null 或无效项均不匹配，顺序本身不影响结果。只有该 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才因全合取规则成为 `1.0`；evaluator 或任务级编排错误产生非 `1.0` 分数。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 接受 `RETRIEVE`/`SUCCESS` 响应结构，并将 `retrieved_data` 归一化为精确无序多重集 `{dan.abramov@gmail.com, timer150@gmail.com, ian@iansutherland.ca}`，从而令 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，虽注明没有网络内容 evaluator，仍要求 HAR 存在并可解析；success 还要求 artifacts 可读且评估无错误，failure 包括响应解析或字段不匹配、邮箱集合差异、HAR 或响应不可读以及 evaluator/编排错误。undecided 被定义为响应或必需 trace 的保留副本缺失或截断、且没有 evaluator 结果可消除不确定性；已确认的 null、无效响应、解析错误或 evaluator error 则是 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_har`
- 为什么修改：`network.har` 被指定为决定性证据并要求其可解析，尽管此案例只有一个 `AgentResponseEvaluator`，且未配置 `NetworkEventEvaluator`。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为重建已配置检查的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_outcome_dependency`
- 为什么修改：这些规则将已留存 HAR 的可读性作为 `success` 的前提条件，将不可读判为 `failure`，并将跟踪留存丢失作为判定 `undecided` 的理由。
- 应如何修改：移除依赖 HAR 的条款。除非已留存的 evaluator 结果能够确定结果，否则将 `undecided` 限定为影响已提交响应的丢失、截断、完整性或来源问题；将完整但无效的响应和已记录的 evaluator 错误继续归为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_trace_material`
- 为什么修改：HAR artifact 及判定规则中与之关联的三处引用，向原本紧凑的响应 evaluator 核对清单添加了非决定性材料。
- 应如何修改：删除 HAR artifact 以及跟踪专用的 `success`、`failure` 和 `undecided` 措辞，同时保留响应比较、evaluator 组合和错误语义。

## Case 317

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：获取 `metaseq` 仓库按 commit count 排名前 3 的贡献者姓名及提交数。返回值须为对象列表，每个对象使用 `first_name`、`last_name` 和 `number_of_commits` 三个键。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它按数组对象 schema 规范化响应，并检查 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，以及 `retrieved_data` 与 `[{first_name:"Susan",last_name:"Zhang",number_of_commits:70},{first_name:"Stephen",last_name:"Roller",number_of_commits:51},{first_name:"Peter",last_name:"Albert",number_of_commits:12}]` 精确匹配。`ordered:false` 表示数组顺序不计，但缺失、额外或字段值不符均不匹配；未配置 filter 或 last-event 语义。任务只有这一项 evaluator，故仅当其 score 等于 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是响应规范化为 `RETRIEVE`/`SUCCESS`，并以无序方式精确匹配 Susan Zhang/70、Stephen Roller/51、Peter Albert/12，使唯一的 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；success 条件要求精确匹配且无错误，failure 条件包括响应或 trace 无法解析、编排错误以及任一响应字段或对象不匹配，undecided 则用于无法确定实际提交的响应或 trace 等证据缺口。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_har`
- 为什么修改：`network.har` 被称为决定性证据，尽管唯一配置的 evaluator 仅比较提交的响应，并且配置的检索字段不包含依赖 trace 的 URL 或网络谓词。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并仅保留完整的 `agent_response.json`，作为重建已配置检查所需的唯一最小 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_trace_decision_dependency`
- 为什么修改：这些规则将无法解析、缺失、截断或未经证实的网络 trace 视为原生 failure 或 undecided 条件，尽管重建本案例的 `AgentResponseEvaluator` 比较并不需要 trace 内容。
- 应如何修改：移除网络 trace 特有的判定条件。将完整但无效或不匹配的响应以及 evaluator 错误视为 failure，并将 undecided 限定为所保留 agent 响应的丢失或来源证明失败。

## Case 318

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：取得 `2019-nCov` 仓库按 commit count 排名前 3 的贡献者姓氏。任务要求返回这三个 last names。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它按字符串数组 schema 规范化显式配置的字段，要求 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 与 `["Lo","Chen","Chu"]` 构成完全相同的无序 multiset。`ordered:false` 意味着顺序不影响结果，但缺项、额外项或重复次数不同会失败；稀疏 expected 未配置的原始字段（如 `error_details`）不参与比较，也没有 filter 或 last-event 语义。仅当这一 evaluator 的 score 为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是规范化响应精确匹配 `RETRIEVE`、`SUCCESS` 和无序 multiset `[Lo, Chen, Chu]`，且唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它将 `agent_response.json` 和 `network.har` 都视为决定性 artifacts，并额外声称响应必须省略 `error_details`、任何额外 normalized compared keys 都会失败；failure 还包括错误姓氏、缺失或额外元素、HAR/context/normalization/evaluator/orchestration 错误。undecided 覆盖响应或 trace 缺失、截断或无法归属于本次 run 且无官方结果的情况，`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incorrect_unconfigured_field_semantics`
- 为什么修改：清单称有效提交必须省略 `error_details`，提交该字段属于关键不匹配。该字段只是在派生的 `task.json` 中具象化的默认值，并不是稀疏 task 中显式配置的预期字段。
- 应如何修改：说明比较涵盖稀疏的预期字段集——`task_type`、`status` 和 `retrieved_data`——并且原始 `error_details` 或其他未配置字段不影响此 evaluator 的得分。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的检查是 `AgentResponseEvaluator`，且响应包含普通的姓氏字符串，其比较不依赖 trace 内容。
- 应如何修改：仅保留完整的 `agent_response.json` 作为决定性 artifact，并从原生 undecided 规则中移除 trace 丢失条件。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overrestrictive_decision_rules`
- 为什么修改：success 和 failure 规则错误分类了包含 `error_details` 或其他未配置原始 key、但本应匹配的响应，并且 undecided 规则依赖于非决定性 HAR 的丢失。
- 应如何修改：以已发布的三个显式配置字段的 parsing 和 normalization 为基础判定 success 和 failure，允许未配置的原始字段，并将 undecided 限定为完整响应 artifact 的丢失或来源证明失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_repeated_conditions`
- 为什么修改：清单重复了无依据的 `error_details` 限制，并增加了 HAR 特有的证据和 failure 表述，而这对于此单 evaluator 案例并非必要。
- 应如何修改：移除 HAR 分支，并将修正后的响应字段、无序数据、评分、failure 和保留规则整合为一份紧凑的清单。

## Case 319

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：计算 2022 年 4 月被取消订单（如有）的预期退款总额，并包括 shipping fee。用户要求只返回一个数字，例如 `10.99`，不得附加说明。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`；稀疏 expected 明确设置 `task_type:"retrieve"` 和 `status:"NOT_FOUND_ERROR"`，数组 schema 的元素为 `format:"currency"` 的 number。按已完成的源码口径 review，expected 规范化仍生成 `retrieved_data:null` 键，但 actual 规范化仅遍历 `expected.model_fields_set`，因稀疏配置未含 `retrieved_data` 而无法生成该键；结构比较虽忽略其值，却仍要求键存在，因此所有结构化响应都会产生 missing-key assertion，非法响应也会失败或报错。未配置 filter 或 last-event 语义；任务仅有这一 evaluator，理论组合规则要求其 score 为 `1.0` 才能令 `TaskEvalResult.score` 为 `1.0`，但该配置和实现语义下此条件不可满足。

### 原本 draft 是什么

原始 draft 声称 benchmark success 可以通过：最终响应规范化为 `task_type RETRIEVE`、`status NOT_FOUND_ERROR` 和 null-equivalent `retrieved_data`，且唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；success 要求无 assertion 或 evaluator error，failure 包括响应无效、字段不匹配、`retrieved_data` 非 null 或评估错误，undecided 则用于无法确定实际响应和 trace 的证据缺口。其非空 stronger condition 为 `numeric_refund_total`：在 native success 之外，要求用户可见答案仅为依据全部 2022 年 4 月取消订单及 shipping fee 正确计算的数字退款总额，并以 `agent_response.json` 和 `network.har` 验证。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incorrect_response_success_predicate`
- 为什么修改：草案认为 `RETRIEVE` / `NOT_FOUND_ERROR` / `null` `retrieved_data` 能够获得 `1.0` 分，但稀疏配置的 `model_fields_set` 仅包含 `task_type` 和 `status`。预期值 normalization 会添加 `retrieved_data`，实际值 normalization 则会省略该字段，结构比较会报告 key 缺失。
- 应如何修改：说明在数据包所表示的已发布语义下，任何最终响应都无法使唯一的 evaluator 获得 `1.0` 分，并解释稀疏字段集与预期 key 之间的不匹配。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_trace_artifact`
- 为什么修改：`network.har` 仅因 evaluator 设置而被列为原生决定性证据，尽管未配置 `NetworkEventEvaluator`，也不存在依赖 trace 的响应比较。
- 应如何修改：仅保留完整的 `agent_response.json` 作为原生决定性 artifact；`network.har` 可以继续作为单独的更强条件的证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`unsound_success_and_undecided_rules`
- 为什么修改：`success_if` 描述了一种不可能实现的无断言比较，而 `undecided_if` 不当地将 trace 缺失视为原生决定性证据丢失。
- 应如何修改：明确规定在所表示的发布版本下原生 success 不可满足，将每个完整且受支持的响应或 evaluator 错误分类为 failure，并将 undecided 限定为 agent 响应证据或其来源证明的丢失。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_checklist_not_minimal_or_coherent`
- 为什么修改：清单同时包含错误的可实现 success 描述和不必要的原生 trace 要求。
- 应如何修改：用已发布的稀疏字段集行为替换原生语义，并从原生决定性 artifacts 和原生 undecided 条件中移除 `network.har`。

## Case 320

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：计算 2023 年 2 月被取消订单（如有）的预期退款总额，并包括 shipping fee。用户要求只返回一个数字，例如 `10.99`，不得附加说明。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，它对稀疏配置中的 `task_type`、`status` 和 `retrieved_data` 做解析及规范化，要求分别匹配 `RETRIEVE`、`SUCCESS` 和 `[406.53]`；`performed_operation` 可作为 `task_type` 的兼容来源。`retrieved_data` 使用 currency-number 数组 schema，`ordered:false` 表示按无序方式精确比较 singleton `[406.53]`，不得缺失或增加数值；`error_details` 等未配置原始字段不参与比较，也没有 filter 或 last-event 语义。唯一 evaluator 的 score 必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是响应规范化后匹配 `RETRIEVE`、`SUCCESS` 和无序 singleton `[406.53]`，使唯一 `AgentResponseEvaluator` 与 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 还要求 trace 与 evaluation context 有效，failure 包括响应不可解析、字段或金额不匹配及 evaluator/task-level error，undecided 用于 artifacts 缺失或截断而无法确定完整响应或可用 trace 的情况。其非空 stronger condition `number_only_user_facing_answer` 要求答案以数字 `406.53` 表示，除必要 envelope metadata 外不含解释文字或额外 answer fields，并以原始 `agent_response.json` 验证。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`network_trace_not_decisive`
- 为什么修改：`network.har` 被错误地指定为唯一 `AgentResponseEvaluator` 的决定性证据。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_contaminates_decision_rules`
- 为什么修改：原生 success 和 undecided 规则以某个 trace 的保留或可用性为条件，但该 trace 无法改变已配置的响应比较。
- 应如何修改：从 `success_if` 和 `undecided_if` 中移除 trace 有效性；仅在 `agent_response.json` 缺失、截断或来源证明存在缺陷时使用 undecided，而完整但无效、为 `null` 或不匹配的响应仍为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_evidence`
- 为什么修改：trace artifact 和 trace 相关规则增加了冗余的原生范围。
- 应如何修改：删除 trace artifact 以及所有 trace 保留条件，同时不改变响应 evaluator 或更强条件的语义。

## Case 322

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：计算 2023 年 5 月被取消订单（如有）的退款总额，前提是 shipping fee 无法退还。用户要求只返回一个数字，例如 `10.99`，不得附加说明。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：它从直接对象、原始 JSON 字符串或 fenced code block 提取响应，并投影稀疏 expected 明确配置的 `task_type`、`status`、`retrieved_data`；若缺少 `task_type`，可使用 `performed_operation` 作为 legacy fallback。目标分别为 `RETRIEVE`、`SUCCESS` 和 `[350.42]`，其中 retrieved data 按 currency-number schema 规范化，非列表值可转为 singleton；`ordered:false` 要求与 `[350.42]` 无序精确匹配且无缺失或额外值，未配置原始键不影响比较。没有 filter 或 last-event 语义；唯一 evaluator 的 score 为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是提交响应经 JSON/code-block 提取和规范化后匹配 `RETRIEVE`、`SUCCESS` 及唯一 currency 值 `350.42`，从而令 `AgentResponseEvaluator` 和 `TaskEvalResult.score` 都为 `1.0`。它只把 `agent_response.json` 列为决定性 artifact；success 要求匹配且无 evaluator error，failure 包括非对象或 malformed 响应、缺失或错误的 `task_type`/`status`、缺失、null、错误或额外的 retrieved value，undecided 仅用于该 artifact 遗失或损坏而无法确认提交内容。其非空 stronger condition `numeric-only-user-facing-answer` 要求原始最终响应除标准 response envelope 外没有解释或周边文字及额外 answer/detail fields，唯一答案项是数字 `350.42`，并由 `agent_response.json` 判定。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`legacy_task_type_alias`
- 为什么修改：清单没有将已发布的回退规则落实到操作层面：当 `task_type` 字段缺失时回退到 `performed_operation`，反而将缺失 `task_type` 描述为 failure。
- 应如何修改：说明当 `task_type` 缺失时，接受 `performed_operation` 作为旧版 `task_type` 字段，并据此限定字段缺失导致 failure 的条件。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_missing_task_type_failure`
- 为什么修改：`fail_if` 会将包含 `performed_operation: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: [350.42]` 的完整响应分类为 failure，尽管已配置的 evaluator 可以将其 normalization 为原生匹配。
- 应如何修改：仅当可接受的 `task_type` 和已发布的 `performed_operation` 回退均未提供预期的 `RETRIEVE` 值时，才因该条件判定 failure；保留所有其他不匹配和 evaluator 错误导致的 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_rule_internal_incoherence`
- 为什么修改：原生规则简洁且不存在信息泄漏，但与其自身引用来源中所表示的一条影响得分的 parsing 规则相矛盾。
- 应如何修改：一致地修订 `benchmark_success`、artifact 问题、`success_if` 和 `fail_if`，以纳入 `performed_operation` 回退，同时不要添加无关的 parsing 特殊行为。

## Case 325

### 原本 case 是什么

原始任务是在 `shopping` 站点打开包含全部 “mouth night guard” 商品的搜索结果页，并按价格降序排列；task type 为 `NAVIGATE`。任务从 `__SHOPPING__` 开始，官方指令未要求返回检索数据。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查响应中显式配置的字段能否规范化为 `task_type: NAVIGATE`、`status: SUCCESS`、`retrieved_data: null`；后者只检查 `last_event_only: true` 对应的最后一个相关网络事件，要求 `GET`、响应状态 `200`、URL 为 `__SHOPPING__/catalogsearch/result/index/`，且查询参数包含 `q=["mouth night guard "]`（保留末尾空格）和 `product_list_order=["price"]`。查询参数过滤规则 `^(?!q$|product_list_dir$|product_list_order).+$` 会忽略除 `q`、`product_list_dir`、`product_list_order` 外的参数，而 `decode_base64_query` 为 `false`；两个 evaluator 的分数必须都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求两个 evaluator 均为 `1.0`：`agent_response.json` 通过 `NAVIGATE`/`SUCCESS`/`null` 比较，`network.har` 的最后相关导航事件通过指定 URL、查询、`GET` 和 `200` 比较，并将这两个文件列为决定性 artifacts。它把两项都通过定义为 success，把响应不匹配、缺失或不匹配的最后事件以及 evaluator 报错或低于 `1.0` 定义为 failure，并写明此时 `TaskEvalResult.score` 为 `0.0`；但其 undecided 规则把文件“不可解释”也纳入，未明确限于留存、完整性或来源损失。非空 stronger condition `rendered_descending_price_order` 另要求最终截图或 DOM/accessibility snapshot 证明页面确实按价格非递增排列或显示降序状态，因为原生期望只断言 `product_list_order="price"`，未断言 `product_list_dir="desc"` 或渲染后的价格顺序。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`invalid_inputs_must_be_native_failure`
- 为什么修改：undecided 规则与完整的无效响应和 evaluator 错误存在重叠，尽管已发布的组合逻辑会为这些结果赋予非 `1.0` 分数。
- 应如何修改：明确说明：完整保留但无效或为 `null` 的响应、完整但没有匹配事件的 trace、任何 evaluator 可见的不匹配，以及任何 evaluator 或编排错误，均为原生 failure；仅在证据丢失导致无法重建所提交的输入或记录的结果时使用 undecided。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`narrow_undecided_to_evidence_loss`
- 为什么修改：“缺失或无法解释”过于宽泛，因为它未区分保留数据损坏与官方 evaluator 拒绝的完整保留内容。
- 应如何修改：重写 `fail_if` 和 `undecided_if`，使完整的无效内容和 evaluator 错误判为 failure，而 undecided 仅适用于因保留、完整性或来源证明缺失而无法恢复精确响应、完整 trace 或两个已记录 evaluator 结果的情况。

## Case 329

### 原本 case 是什么

原始任务是在 `shopping` 站点计算 2023 年 4 月 19 日在 One Stop Market 的购物总支出，排除运费，并且只返回数字、不得附加说明；task type 为 `RETRIEVE`。官方示例格式为 `10.99`。

### Benchmark 怎么测

唯一配置的 evaluator 是 `AgentResponseEvaluator`，它检查 evaluator 可见响应经官方解析和规范化后，显式配置字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 是否为恰好一个等于 `0` 的值。`results_schema` 要求数组元素是 `format: currency` 的 `number`，并以 `ordered: false` 做无序比较；物化得到的 `error_details: null` 不是稀疏配置中显式要求的比较字段。由于只有这一个 evaluator，只有其分数等于 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得到 `1.0`，响应规范化为 `RETRIEVE`、`SUCCESS` 和仅含 currency-normalized `0` 的 `retrieved_data`，从而 `TaskEvalResult` 为 success 且分数 `1.0`。它把 `agent_response.json` 以及“Official TaskEvalResult with AgentResponseEvaluator result”都列为决定性 artifacts；success 要求字段比较和唯一 evaluator 均通过，failure 包括解析或规范化错误、字段不匹配、缺失或多余值，以及 evaluator 的 `0.0` 或 error。其 undecided 规则允许由完整 `TaskEvalResult` 或“足够”的部分响应数据替代完整原始响应，这正是 review 指出的证据口径过宽之处。非空 stronger condition `number_only_user_output` 另要求转换前的原始用户可见回答只能是 `0` 的数字表示，不能包含 benchmark 响应封装或其他文字。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`complete_agent_response_required`
- 为什么修改：证据规则允许 Official `TaskEvalResult` 替代 `agent_response.json`，并接受仅仅足够的保留响应数据，因此实际上并未要求完整的原始 evaluator 输入。
- 应如何修改：将完整且可归属的 `agent_response.json` 设为必需的原生决定性 artifact，并移除作为替代项的冗余 `TaskEvalResult` artifact。对于这个仅有 `AgentResponseEvaluator` 的案例，不要要求 `network.har`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`tighten_undecided_boundary`
- 为什么修改：当前 undecided 条件允许依据部分响应数据或派生结果对案例进行分类，即使完整的 evaluator 可见响应已丢失。
- 应如何修改：将 undecided 限定为完整的 `agent_response.json` 缺失、截断、损坏或无法归属的情况。明确保留以下 failure 分类：完整但为 `null`、为空、格式错误、不匹配或会导致 evaluator 错误的响应。

## Case 330

### 原本 case 是什么

原始任务是在 `shopping` 站点计算 2023 年 3 月在 One Stop Market 的购物总支出，排除运费，并仅以数字返回、不得附加说明；task type 为 `RETRIEVE`。官方示例格式为 `10.99`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查 evaluator 消费的响应经已发布的响应选择、解析和规范化后，显式字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 恰好包含 currency-normalized `53.31`。`results_schema` 是元素格式为 `currency` 的数字数组，`ordered: false` 表示无序比较；物化默认值 `error_details: null` 和其他未配置字段不构成额外比较要求。该 evaluator 的分数必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得到 `1.0`，提交响应规范化为 `RETRIEVE`、`SUCCESS` 和唯一 currency 值 `53.31`，且 evaluator orchestration 无错误。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把 trace 可解析、可用于 evaluation context validation 写入条件；success 是响应匹配且最终任务分数为 `1.0`，failure 包括空值、格式或字段不匹配、数量或数值错误以及 evaluator/context processing error。其 undecided 也把 response 或 trace 缺失、截断纳入，review 指出 `network.har` 并不参与本 case 唯一的响应比较，因此该证据和 undecided 口径并不最小。非空 stronger condition `original-number-only-format` 要求转换前响应只有数值 `53.31`，不能是带引号文本，也不能有解释或代码围栏。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被错误地指定为原生决定性证据，而此案例唯一配置的 evaluator 是 `AgentResponseEvaluator`。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。保留完整的 `agent_response.json` 作为唯一的原生 artifact；使用 transformation 时，还应包括完整的 `TransformedAgentResponse` 输入。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：undecided 规则错误地允许 trace 证据缺失阻止原生判定。
- 应如何修改：将 `undecided_if` 限定为 agent 响应证据缺失、截断或来源存在歧义，致使无法重建 evaluator 所使用的完整响应的情况。不要让 `network.har` 缺失独立导致 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：推测性的 trace 回退重复了非决定性的运行时上下文，并使清单比此单 evaluator 案例所需的更不紧凑。
- 应如何修改：移除 trace artifact 行以及所有依赖 trace 的判定表述，同时保留响应 evaluator 的 parsing、normalization、比较和 failure 语义。

## Case 331

### 原本 case 是什么

原始任务是在 `shopping` 站点计算 2022 年 7 月在 One Stop Market 的购物总支出，排除运费，并只返回数字、不附加任何说明；task type 为 `RETRIEVE`。官方示例格式为 `10.99`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查完整提交响应经已发布的字符串或代码块 JSON 提取及规范化后，显式配置字段是否为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 是否恰好包含 currency-normalized `25.16`。数组 schema 的元素为 `format: currency` 的 `number`，`ordered: false` 表示忽略顺序；稀疏配置未显式要求物化默认字段 `error_details: null`。只有该 evaluator 得分等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得到 `1.0`，响应规范化为 `RETRIEVE`、`SUCCESS` 和无序 currency 数组 `[25.16]`，从而 `TaskEvalResult.score` 为 `1.0`。它将 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；success 要求字段匹配且 evaluation 无错误，failure 包括非对象响应、字段或 retrieved data 不匹配、evaluator 或 task orchestration error，undecided 则包含无法确认响应、trace 或官方 evaluation 是否完成的情形。review 指出该 case 只有响应 evaluator，HAR 不参与配置的比较，因此原 draft 的决定性证据和 undecided 规则过宽。非空 stronger condition `number_only_user_facing_answer` 要求转换前的完整用户可见响应只能是数值字面量 `25.16`，不能出现对象、数组、标签、代码围栏或其他文本。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的 evaluator 比较的是 agent 响应，并且没有网络事件谓词。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_undecided`
- 为什么修改：undecided 规则将未能保留所需 trace 或未能确认评估完成视为无法作出判定，尽管完整响应足以确定已配置比较的结果。
- 应如何修改：将 undecided 限定为 agent 响应证据缺失、不完整、损坏或缺少来源证明的情况；在此案例中，不要因 `network.har` 缺失而判定 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_evidence_not_minimal`
- 为什么修改：额外的 HAR artifact 及相关的上下文验证问题，使原生清单在证据审查方面比必要情况更大、更严格。
- 应如何修改：用紧凑且仅基于响应的唯一已配置 evaluator 重建规则替换原生 artifact 集及相关规则。

## Case 333

### 原本 case 是什么

原始任务是在 `shopping` 站点计算 2022 年 11 月在 One Stop Market 的购物总支出，排除运费，并仅返回数字、不得附加说明；task type 为 `RETRIEVE`。官方示例格式为 `10.99`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对确切 evaluator 输入进行已发布的解析和 schema 规范化，检查显式配置字段是否匹配 `task_type: RETRIEVE`、`status: SUCCESS`，以及仅含 currency-normalized `358.18` 的 `retrieved_data`。`results_schema` 规定数组元素是 `format: currency` 的数字，`ordered: false` 使 retrieved data 按无序方式比较；物化的 `error_details: null` 不是显式配置的比较字段。唯一 evaluator 的分数必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得到 `1.0`：响应经解析和规范化后匹配 `RETRIEVE`、`SUCCESS` 与无序 currency 数组 `[358.18]`，从而 `TaskEvalResult.score` 也为 `1.0`。它把含适用 `transformed_response` 的 `agent_response.json` 列为决定性 artifact；success 要求无 assertion 或 error，failure 包括非对象格式、缺失或额外 evaluated keys、字段或基数不匹配，以及解析、规范化或 evaluation error。其 undecided 规则在确切响应缺失、截断或含糊时，仍允许留存 evaluator result 替代响应来确定结论；review 指出完整 evaluator 输入不可由分数记录替代。非空 stronger condition `bare-number-user-output` 要求转换或协议封装前的原始用户可见回答严格等于裸数字 `358.18`，不得包含 JSON envelope、代码围栏、标签或解释。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`complete-response-required`
- 为什么修改：undecided 规则允许在 `agent_response.json` 缺失、截断或存在歧义时，以保留的 evaluator 结果作为替代，尽管已有明确要求：对于 `AgentResponseEvaluator`，必须保留完整响应。
- 应如何修改：将完整且已解析来源的 `agent_response.json` 设为重建的必要条件；不要将留存的 evaluator 结果或分数视为替代品。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided-fallback-too-weak`
- 为什么修改：合取条件“且没有保留的 evaluator 结果记录该结果”削弱了 `undecided_if`：响应证据丢失本身就应使原生判定无法决定。
- 应如何修改：移除 evaluator 结果例外，并说明：精确的 evaluator 输入缺失、不完整、存在歧义或来源无法确定时，应判为 undecided；完整但无效或不匹配的响应仍为 failure。

## Case 336

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：查找用户最近一次订购 conditioner 的日期，并仅以 `YYYY-MM-DD` 格式返回；若不可用则返回 `null`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，检查解析后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 按元素格式为 `date` 的数组 schema 归一化后，与无序单元素期望值 `["01/16/2023"]` 精确匹配；materialized 中的 `error_details:null` 不是 sparse 配置的比较字段。唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 得分 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`；决定性 artifacts 列为 `agent_response.json` 和 `Retained official TaskEvalResult/evaluator record`。它把可解析并归一化为 `RETRIEVE`、`SUCCESS` 及匹配 `01/16/2023` 的单元素数据判为 success，把无效对象、字段或数据不匹配以及 evaluator/orchestration error 判为 failure，并仅在存储丢失或截断且无完整官方结果时判为 undecided。其非空 stronger condition `exact_requested_surface_format` 另要求原始响应恰为字面字符串 `2023-01-16`，且没有外围文字、代码围栏或解释内容。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：原生证据列表除 agent_response.json 外，还包含一条假设性的“保留的官方 TaskEvalResult/evaluator 记录”。该材料包并未证实该记录会被保留，而且对于唯一配置的 AgentResponseEvaluator 而言，该记录是冗余的。
- 应如何修改：从 decisive_artifacts 中移除 TaskEvalResult/evaluator 记录，并将完整 agent_response.json 的丢失或截断设为原生 undecided 条件。继续将 evaluator 和编排错误归类为原生 failure。

## Case 337

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：查找用户最近一次订购 olive bread 的日期，并仅以 `YYYY-MM-DD` 格式返回；若不可用则返回 `null`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，检查解析和归一化后的 `task_type` 为 `RETRIEVE`、`status` 为 `SUCCESS`，且 `retrieved_data` 在 date-array schema 下与无序单元素期望值 `["12/12/2022"]` 精确匹配；materialized 的 `error_details:null` 不属于 sparse 配置的比较字段。唯一 evaluator 得分必须为 `1.0`，任务的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 定义为唯一 `AgentResponseEvaluator` 得分 `1.0`，使 `TaskEvalResult.score` 为 `1.0`；它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求响应与 trace 成功加载。它将归一化得到 `RETRIEVE`、`SUCCESS` 和单元素日期 `12/12/2022` 判为 success，将响应或 HAR 的解析、上下文构造、编排或 evaluator error，以及字段或数据不匹配判为 failure；所需保留输入缺失或损坏、无法重建提交内容或是否发生官方评估错误时为 undecided。非空 stronger condition `literal_requested_date_format` 要求归一化前的日期字面值为 `2022-12-12`，且除必要协议字段外没有解释内容。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_network_artifact`
- 为什么修改：对于仅配置了比较 agent 响应的 evaluator 的案例，network.har 被错误地列为决定性证据。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并根据完整的 agent_response.json 重建已配置的检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：尽管没有配置 NetworkEventEvaluator，success、failure 和 undecided 规则却使 trace 的解析或保留影响判定。
- 应如何修改：从 success_if 和 fail_if 中移除 trace 加载关卡，并将 undecided_if 限制为完整 agent 响应发生丢失、损坏或来源证明失败，致使无法重建的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_section`
- 为什么修改：额外的 trace artifact 和 trace 专用规则重复了编排层面的关注点，却无助于重建本案例已配置的比较。
- 应如何修改：采用以唯一的 AgentResponseEvaluator 和 agent_response.json 为中心的紧凑原生章节。

## Case 338

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`：查找用户最近一次订购 toothpaste 的日期，并仅以 `YYYY-MM-DD` 格式返回；若不可用则返回 `null`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 比较 sparse 配置的 `task_type`、`status` 和 `retrieved_data`：前两者须归一化为 `RETRIEVE`、`SUCCESS`，后者须按 date-array schema 与无序单元素期望值 `["12/04/2022"]` 精确匹配。`retrieved_data` 标量会被转换为单元素序列，额外原始字段以及 materialized 默认值 `error_details:null` 不参与比较；任何不匹配或 evaluator error 均不能得到 `1.0`，而 `TaskEvalResult.score` 仅在该唯一 evaluator 得分 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score = 1.0` 要求唯一 `AgentResponseEvaluator` 得分 `1.0`，并把 `agent_response.json` 与 `network.har` 列为决定性 artifacts，其中 HAR 被用于 trace 解析及可能的环境 URL 重建。它将无错误完成官方评估且响应归一化为 `RETRIEVE`、`SUCCESS` 和日期 `12/04/2022` 判为 success，将响应字段不匹配以及 response/HAR parsing、normalization、evaluator 或 orchestration error 判为 failure；若保留证据不足以恢复最终响应，或既无可读 HAR 也无足以确认评估完成情况的官方记录，则为 undecided。非空 stronger condition `exact_iso_answer_surface` 要求原始最终响应符合 public response shape、`retrieved_data` 严格为 `["2022-12-04"]`，且没有非空的额外答案细节。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：network.har 仅基于通用解析和环境修复行为而被列为决定性证据，但本案例没有 NetworkEventEvaluator，且材料包并未证实 HAR 内容会影响其日期响应比较。undecided 规则还依赖一条未命名的官方评估记录。
- 应如何修改：将完整的 agent_response.json 用作唯一决定性的原生运行 artifact，并移除对 network.har 或未命名评估记录的依赖。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：当前的 undecided 规则可能会将非决定性 HAR 的丢失视为导致无法判定，并使用了命名 artifact 集之外的官方评估记录。
- 应如何修改：将 undecided 限制为影响 agent_response.json 的保留、完整性或来源证明丢失。明确说明：完整但为 null、格式错误、非对象、不匹配或会导致 evaluator 错误的响应属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：证据章节并非最小化，因为它保留了与唯一配置的响应 evaluator 无关的条件性 HAR 检查，而判定规则又引入了一个从未声明的 artifact。
- 应如何修改：移除 HAR 的决定性 artifact 条目以及对所有官方评估记录的依赖，仅保留原生评分所需的响应证据。

## Case 342

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `NAVIGATE`：进入当前项目中所有处于 opened 状态、带有 question 标签并与 OPT model 相关的 issue 列表。

### Benchmark 怎么测

共配置三个 evaluator。`AgentResponseEvaluator` 检查响应归一化后的 `task_type` 为 `NAVIGATE`、`status` 为 `SUCCESS`、`retrieved_data` 为 `null`；第一个 `NetworkEventEvaluator` 以 `last_event_only=true` 检查最后一个 navigation event 是否为状态 `200` 的 `GET`，URL 匹配 `^__GITLAB__/root/metaseq/-/issues.*$`，并以 `ignored_query_params_patterns:[".*"]` 忽略全部查询参数名。第二个 `NetworkEventEvaluator` 先筛选方法为 `POST`、归一化路径匹配 `__GITLAB__/api/graphql`，且在 Referer 存在时其归一化路径匹配预期 issues 路径的候选；缺少 Referer 不会在此阶段被排除，随后由 `last_event_only=true` 选择最后一个初筛候选，再完整检查状态 `200`、方法、URL 和大小写不敏感定位后归一化的 Referer 是否等于 `__GITLAB__/root/metaseq/-/issues/?state=opened&label_name%5B%5D=question&search=OPT%20Model`，URL 归一化时忽略名称匹配 `page` 或 `sort` 的查询参数。三个 evaluator 的分数必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator` 全部得分 `1.0`，并把 `agent_response.json` 与 `network.har` 列为决定性 artifacts。它将响应通过 `NAVIGATE/SUCCESS` 比较、最后 navigation event 通过 issues-route `GET` 检查、以及其所称“selected last matching” GraphQL `POST` 通过方法、URL、状态和 Referer 检查判为 success；任何组件失败或报错均为 failure，任一 artifact 未保留或存在妨碍重建输入的保留缺陷则为 undecided。原 draft 的 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete_evaluator_semantics`
- 为什么修改：原生描述将响应检查简化为 NAVIGATE/SUCCESS，并将 eval[2] 描述为最后一个匹配的 200 POST，却未说明已发布代码中的初步选择边界及其 page/sort 忽略模式。
- 应如何修改：说明 eval[0] 比较稀疏原始字段 task_type、status 和 retrieved_data:null，同时排除已填充默认值的 error_details。对于 eval[2]，说明 last_event_only 会先选择最后一个初步的 POST/GraphQL/referer-path 候选项，再进行状态和完整的规范化比较，其中包括缺少 Referer 时的过滤行为以及 page/sort 正则表达式忽略规则。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`insufficient_success_rule`
- 为什么修改：success_if 没有以可操作的方式标识 eval[2] 实际选择的事件，并遗漏了已配置响应比较的一部分。
- 应如何修改：使 success 取决于已发布代码所选择的确切最后一个初步候选项通过完整的规范化比较，并明确包含已配置的响应字段以及 page/sort 查询模式处理。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compactness_dropped_decisive_details`
- 为什么修改：草稿简洁且无泄漏，但这种简洁性删去了会改变得分的网络选择细节和一个已配置的响应字段。
- 应如何修改：保留当前紧凑结构，同时补充缺失的 retrieved_data:null 比较以及 eval[2] 的确切选择/规范化语义。

## Case 344

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `RETRIEVE`：回答商店迄今共收到多少条 reviews。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，比较 sparse 配置的 `task_type`、`status` 和 `retrieved_data`：前两者须归一化为 `RETRIEVE`、`SUCCESS`，数据须按 number-array schema 归一化后与无序单元素期望值 `[351]` 精确匹配；原始标量若被归一化为该单元素序列也可通过。materialized 默认字段 `error_details:null` 不参与比较；唯一 evaluator 得分必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一 `AgentResponseEvaluator` 得分 `1.0`，从而 `TaskEvalResult.score` 为 `1.0`，并把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts。它把所需输入成功解析、评估无错误且响应归一化为 `RETRIEVE`、`SUCCESS` 和无序数值集合 `[351]` 判为 success；输入、配置、编排或 evaluator error，以及解析、字段或数据不匹配均判为 failure，而响应或所需 trace 在保留证据中缺失或截断且没有完整 evaluator result 时判为 undecided。非空 stronger condition `literal_retrieved_data_array` 进一步要求 `agent_response.json` 中的 `retrieved_data` 必须字面编码为数值 JSON 数组 `[351]`，不能是标量 `351`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_trace`
- 为什么修改：尽管未配置 NetworkEventEvaluator，且本案例的数值型 AgentResponseEvaluator 比较由 agent_response.json 决定，network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并根据完整的 agent_response.json 重建已配置的原生检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_undecided`
- 为什么修改：尽管重建这一已配置的响应比较并不需要 trace 内容，检查清单却将保留的 trace 丢失设为 undecided 条件。
- 应如何修改：将 undecided_if 限制为 agent_response.json 的丢失、截断、完整性失败或来源证明失败；完整但无效或不匹配的响应仍应属于 failure。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported_stronger_format_requirement`
- 为什么修改：要求字面量数组语法并未弥合官方用户目标与原生评分之间的差距；标量 351 仍然报告了所请求的数量。
- 应如何修改：将 stronger.additional_conditions 设为空列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_extra_conditions`
- 为什么修改：非决定性的 HAR 处理和缺乏依据的字面量数组 stronger 条件增加了不必要的审查分支。
- 应如何修改：删除 HAR 专用 artifact/保留规则和字面量数组 stronger 条件，同时保留响应 evaluator 的决定性解析、规范化、比较和 failure 语义。

## Case 346

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点回答“2022 年期间店铺收到了多少条评论”，task type 为 `RETRIEVE`。任务要求报告该时间段的评论数量。

### Benchmark 怎么测

仅配置了 `AgentResponseEvaluator`：经字符串/代码块 JSON 提取与规范化后，稀疏配置中显式设置的 `task_type`、`status`、`retrieved_data` 必须分别匹配 `RETRIEVE`、`SUCCESS` 和数值数组 `[0]`。`retrieved_data` 按 array-of-number schema 规范化，并以 `ordered=false` 做无序但精确的集合比较；缺失、额外或非零项目均不匹配，标量与单元素数组若被发布版逻辑规范化为同一结果则不单独计分。materialized 配置中的默认 `error_details: null` 及其他未显式配置的原始响应字段不参与比较；没有配置 filter、`NetworkEventEvaluator` 或 last-event 语义。唯一 evaluator 必须得分 `1.0`，且所有 evaluator 分数都等于 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 在解析和规范化后对 `RETRIEVE`、`SUCCESS` 与无序数值 `[0]` 无结构或数值 mismatch，从而得分 `1.0`，并使 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，分别用于判断响应匹配，以及 HAR 能否解析为 `NetworkTrace`、完成 evaluation context 和环境 URL fallback。其 success 条件还要求 HAR/context 与响应评估无 orchestration 或 evaluator error；failure 包括空或非 mapping 响应、字段或项目不匹配、非零值，以及响应/HAR 解析或 evaluator error；undecided 则用于无法读取 `agent_response.json` 或缺少足够 `network.har` 内容的留存证据。非空 stronger condition `public_response_array_shape` 进一步要求解析前的 `retrieved_data` 必须编码为 JSON 数组 `[0]`，不能是 evaluator 可强制转成单元素序列的标量。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_har`
- 为什么修改：尽管本案例只有一个 AgentResponseEvaluator，且其已配置的数值比较可根据 agent_response.json 重建，network.har 仍被列为决定性证据。
- 应如何修改：仅保留完整的 agent_response.json 作为决定性的运行后证据，并移除 HAR 问题。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_har_decision_gates`
- 为什么修改：对于这个仅涉及响应的案例，success、failure 和 undecided 规则却使 HAR 的解析或保留影响证据判定。
- 应如何修改：以已发布评估对完整响应的评估结果作为 success 和普通 failure 的依据；将 undecided 限制为 agent_response.json 的丢失、损坏或来源不确定。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`empty_stronger_list`
- 为什么修改：要求原始 retrieved_data 数组所强制执行的是响应 schema 偏好，而非案例用户意图中尚未满足的部分。
- 应如何修改：移除 public_response_array_shape，并使 stronger.additional_conditions 保持为空。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimality`
- 为什么修改：冗余的 HAR 证据和非目标 stronger 条件扩大了审查范围，却没有保留任何额外的决定性原生语义。
- 应如何修改：使用仅含响应的原生证据集和空的 stronger 列表，同时保留已配置的比较和组合规则。

## Case 347

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点回答“从店铺开始营业至今共收到了多少条评论”，task type 为 `RETRIEVE`。任务要求报告店铺自开始以来的评论总数。

### Benchmark 怎么测

仅配置了 `AgentResponseEvaluator`，它对完整响应进行提取、解码和规范化，并只比较稀疏配置显式设置的 `task_type: RETRIEVE`、`status: SUCCESS` 与 `retrieved_data: [351]`。`retrieved_data` 使用 array-of-number schema；`ordered=false` 表示顺序无关，但比较仍要求精确的单元素数值集合，因此缺失、不同、重复或额外项目都会失败。materialized 默认值 `error_details: null` 及未配置的额外原始字段不参与比较；没有配置 filter、网络事件 evaluator 或 last-event 规则。唯一 evaluator 的分数必须为 `1.0`，所有 evaluator 均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 定义为唯一 `AgentResponseEvaluator` 把响应规范化为 `RETRIEVE`、`SUCCESS` 和无序数值集合 `[351]`，使所有 evaluator 分数及 `TaskEvalResult.score` 均为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，后者用于检查 trace 能否形成 evaluation context，并在需要时支持 shopping-admin base URL fallback。其 success 要求无 parsing、context、orchestration 或 evaluator error 且精确得到单个数值 `351`；failure 包括非结构化响应、字段 mismatch、空缺或非 `351`/额外数据及 evaluation error；undecided 包括任一 artifact 丢失、截断或无法关联到被评估运行且没有官方结果可补足。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：对于这个仅配置 AgentResponseEvaluator 的案例，network.har 被错误地列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并保留完整的 agent_response.json 作为最小充分的运行后 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：undecided 规则将 network.har 缺失或损坏视为导致无法重建，尽管已配置的数值响应检查仅凭 agent_response.json 即可重建。
- 应如何修改：将 undecided_if 限制为影响 agent_response.json 的保留、完整性或来源证明丢失；完整但无效的响应、不匹配和 evaluator 错误仍应属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：对于唯一配置的数值响应 evaluator，trace 解析和回退条件使检查清单不再最小化。
- 应如何修改：移除冗余的 HAR artifact 和依赖 trace 的表述，同时保留响应解析、规范化、比较、错误及任务组合规则。

## Case 348

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点回答“2023 年 5 月店铺收到了多少条评论”，task type 为 `RETRIEVE`。任务要求确定并报告该月份的评论数量。

### Benchmark 怎么测

配置中只有 `AgentResponseEvaluator`；发布版提取和规范化后的显式字段必须匹配 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: [0]`。`retrieved_data` 使用 array-of-number schema，并按 `ordered=false` 进行顺序无关但基数和值均精确的比较。materialized 的默认 `error_details: null` 不属于稀疏配置显式比较字段；本任务没有 filter、`NetworkEventEvaluator` 或 last-event 语义。唯一 evaluator 得分必须为 `1.0`，且全体 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一 `AgentResponseEvaluator` 将响应解析、规范化为 `RETRIEVE`、`SUCCESS` 和精确的无序数值单例 `[0]`，继而令 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 和 `network.har` 均视为决定性 artifacts，后者用于确认 trace 可读为 `NetworkTrace` 并完成 context 与 shopping-admin 环境解析。success 要求规范化结构比较通过且评估无错；failure 包括响应非对象、task type/status 缺失或不匹配、结果不是单个数值 `0`，以及 trace/context 或 orchestration error；undecided 用于最终响应或 trace 留存缺失、损坏而无法重建 evaluator 输入。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：对于仅配置了 AgentResponseEvaluator 的案例，network.har 被列为决定性证据，尽管数值响应比较可根据完整的最终响应重建。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并保留 agent_response.json 作为最小充分的运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_misclassified_as_undecided`
- 为什么修改：undecided 规则将 network.har 的缺失或损坏视为导致无法重建原生结果，尽管 trace 并未参与唯一配置的比较。
- 应如何修改：将 undecided_if 限制为影响完整 agent_response.json 的保留、完整性或来源证明丢失；完整但无效的响应和 evaluator 可见错误仍应属于 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_trace_specific_native_clutter`
- 为什么修改：trace 专用的 artifact、failure 和 undecided 条款使检查清单超出了已配置案例语义的范围。
- 应如何修改：移除 trace 专用审查条件，同时保留以下通用规则：导致非 1.0 得分的 AgentResponseEvaluator 或任务评估错误属于原生 failure。

## Case 349

### 原本 case 是什么

原始任务是在 `gitlab` 站点获取除本人外、可访问仓库 `gimmiethat.space` 的用户用户名，task type 为 `RETRIEVE`。任务对象是该仓库的其他访问用户。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 对响应做发布版解析与规范化，并比较显式字段 `task_type: RETRIEVE`、`status: SUCCESS`，以及恰好一个匹配正则 `^@?yjlou$` 的字符串型 `retrieved_data` 项。结果采用 array-of-string schema 和 `ordered=false`：顺序无关，但缺失、不匹配或额外项目均不通过；正则允许用户名写成 `yjlou` 或 `@yjlou`。materialized 默认的 `error_details: null` 不参与比较，也没有 filter、网络事件 evaluator 或 last-event 规则。该 evaluator 必须无错并得分 `1.0`；所有 evaluator 分数均为 `1.0` 后，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 描述为唯一 `AgentResponseEvaluator` 在规范化后匹配 `RETRIEVE`、`SUCCESS` 和一个符合 `^@?yjlou$` 的无序结果项，并使 `TaskEvalResult` 得分 `1.0` 且为 success status。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求 trace 可构造 evaluation context、在需要时支持环境 URL fallback。success 要求没有缺失或额外结果且 trace/evaluator 处理无错；failure 包括响应 malformed、字段或结果缺失/null/不匹配/额外，以及 trace parsing、orchestration、normalization 或 comparison error；undecided 用于响应或 trace 留存缺失、截断、不可读且没有完整 `TaskEvalResult`。非空 stronger condition `public-response-shape` 要求原始最终响应是符合 `FinalAgentResponse` 的 JSON object，特别是 `retrieved_data` 必须为 JSON array，不能是 evaluator 会强制包装成单例的标量。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive-network-artifact`
- 为什么修改：尽管本案例只有 AgentResponseEvaluator，且材料包并未支持依赖 trace 的响应比较，network.har 仍被列为决定性证据。
- 应如何修改：从 decisive_artifacts 中移除 network.har，并保留完整的 agent_response.json 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace-dependent-decision-rules`
- 为什么修改：在未配置 trace evaluator 的情况下，原生 success、failure 和 undecided 规则却依赖 trace 的保留或解析。
- 应如何修改：基于保留的响应进行重建；响应不匹配和 evaluator 错误仍应属于 failure，并将 undecided 限制为响应证据缺失、损坏或来源证明不足的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-redundant-trace-clauses`
- 为什么修改：不必要的 trace artifact 和重复的 trace 条款使检查清单不如已配置案例语义所要求的紧凑。
- 应如何修改：删除 trace artifact 和 trace 专用表述，同时保留响应比较、evaluator 错误处理以及所有 evaluator 均等于 1.0 的组合规则。

## Case 350

### 原本 case 是什么

原始任务是在 `gitlab` 站点返回除本人外、可访问仓库 `prism-theme` 的用户用户名，task type 为 `RETRIEVE`。任务对象是该仓库的其他访问用户。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：发布版结构化响应解析和规范化后，显式字段须匹配 `task_type: RETRIEVE`、`status: SUCCESS`，并包含恰好一个匹配 `^@?abisubramanya27$` 的字符串结果项。`retrieved_data` 使用 array-of-string schema，按 `ordered=false` 无序比较，但基数必须精确，故缺失、不匹配或任何额外项目都会失败；正则接受有或没有前导 `@` 的用户名。materialized 默认字段 `error_details: null` 不参与显式比较，且没有 filter、`NetworkEventEvaluator` 或 last-event 语义。唯一 evaluator 必须得分 `1.0`，所有 evaluator 分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是 `TaskEvalResult.score = 1.0`：唯一 `AgentResponseEvaluator` 接受规范化后的 `RETRIEVE`、`SUCCESS` 和一个匹配 `^@?abisubramanya27$` 的无序 `retrieved_data` 项。它把 `agent_response.json` 和 `network.har` 都作为决定性 artifacts，分别检查响应比较与 trace/context、环境配置验证。success 要求单个匹配用户名、无额外项目且 evaluator/orchestration 无错；failure 包括非结构化响应、task type/status 错误、数据缺失、不匹配或额外，以及 trace/context 或 orchestration error；undecided 用于既无官方 `TaskEvalResult`，又无法由两项 artifact 忠实重评的证据缺口。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nonminimal_network_artifact`
- 为什么修改：network.har 仅为检测通用 trace 解析或环境/配置错误而被标记为决定性证据。本案例唯一配置的 evaluator 比较 agent_response 字段，且预期用户名不依赖 URL。
- 应如何修改：保留完整的 agent_response.json 作为忠实重建已配置检查的唯一原始决定性 artifact；从 decisive_artifacts 中移除 network.har，并移除依赖 trace 的重建表述，同时继续将响应比较错误和非 1.0 evaluator 得分归类为 failure。

## Case 358

### 原本 case 是什么

原始任务是在 `shopping` 站点检索订单号 `187` 的配送方式，task type 为 `RETRIEVE`。用户指令是 “Get the shipping method for order number 187.”。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它检查响应能否解析并规范化为 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，以及 `retrieved_data` 是否在 `results_schema`（字符串数组）下无序精确匹配唯一预期正则 `^flat rate[^a-z0-9]*(?:fixed)$`，不得缺少或多出值；标量实际值可被转成单元素数组。稀疏配置未显式配置 `error_details`，所以物化得到的 `error_details:null` 不参与比较，也没有配置 `NetworkEventEvaluator` 或 last-event 语义。只有该 evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得 `1.0`，响应规范化为 `RETRIEVE`/`SUCCESS`，且 `retrieved_data` 经标量转单元素数组后无序精确匹配正则 `^flat rate[^a-z0-9]*(?:fixed)$`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts：前者用于响应比较，后者用于 `NetworkTrace`、上下文和配置验证；完整 artifacts 通过为 success，明确的响应不匹配或 trace/context/orchestration 错误为 failure，任一 artifact 缺失、不可读或无法归属于本次运行且无官方结果时为 undecided。非空 stronger condition `raw_retrieved_data_array` 进一步要求原始 `agent_response.json.retrieved_data` 必须是仅含一个匹配值的 JSON 数组，而不能是 evaluator 可强制转换的标量。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`network_trace_not_decisive`
- 为什么修改：`network.har` 被错误地指定为唯一 `AgentResponseEvaluator` 检查的决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为重建原生评分所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_loss_misclassified`
- 为什么修改：`undecided` 规则将 `network.har` 缺失或不可读视为会导致无法作出判定，尽管这并不妨碍重建已配置的响应比较。
- 应如何修改：将 `undecided_if` 限定为完整代理响应丢失、损坏、不可读或来源验证失败的情况；完整但无效或不匹配的响应仍应判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_artifacts`
- 为什么修改：额外的跟踪 artifact 及相应的依赖跟踪的规则使检查清单不再最小化。
- 应如何修改：删除依赖跟踪的原生证据和判定表述，同时保留基于响应的 evaluator 语义以及单独陈述的更强条件。

## Case 359

### 原本 case 是什么

原始任务是在 `shopping` 站点检索订单号 `148` 的订单日期，task type 为 `RETRIEVE`。指令要求以 `YYYY-MM-DD` 格式返回日期，若不可用则返回 `null`，且不得附加任何细节。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应规范化后的 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，并按 `results_schema` 的 `format`=`date` 规范化 `retrieved_data`，再与唯一预期值 `January 29, 2023` 做无序、无缺项或多项的精确数组比较；标量可被强制转成单元素数组。稀疏配置未显式配置 `error_details`，物化的 `error_details:null` 不参与比较，也没有网络或 last-event evaluator。所有已配置 evaluator——此处仅该 evaluator——都必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一的 `AgentResponseEvaluator` 将响应解析为 `RETRIEVE`、`SUCCESS`，并在日期规范化及无序精确数组比较后使单个日期匹配 `January 29, 2023`，从而 evaluator 与 `TaskEvalResult.score` 均为 `1.0`。它仅把 `agent_response.json` 列为决定性 artifact；匹配且无断言为 success，解析失败、字段不匹配、`retrieved_data` 缺失、为 `null`、错误或存在额外项以及 evaluation error 为 failure，而既无提交响应也无可归属的官方 evaluation result 时为 undecided。非空 stronger condition `literal_date_format_without_extra_prose` 要求原始最终响应无外围解释文字，且 `retrieved_data` 字面上恰为单元素数组 `["2023-01-29"]`，不能是标量或其他日期拼写。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`decisive_artifact_integrity_and_scope`
- 为什么修改：决定性 artifact 条目没有明确要求完整且可归属于该次运行的 `agent_response.json`，而 `undecided_if` 引入了一个未声明的官方评估结果回退方案。
- 应如何修改：将完整且可归属于该次运行的 `agent_response.json` 作为唯一具名的原生决定性 artifact。移除未具名的评估结果回退方案，并将留存截断、损坏或来源信息丢失视为会阻止重建。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_integrity_gap`
- 为什么修改：当前规则未区分实际格式错误的完整已提交响应，与因运行后留存或完整性故障而变得格式错误或不可靠的响应 artifact。
- 应如何修改：仅当完整且可归属的实际响应为 `null`、格式错误、不匹配或导致 evaluator 出错时，才判定为 `failure`。当响应证据缺失、被截断、因留存而损坏或无法归属，并因此阻止重建时，应判定为 `undecided`。

## Case 364

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service 测量 Carnegie Mellon University 与 UPMC Shadyside 之间的步行距离，task type 为 `RETRIEVE`。输出只能是带 `km` 或 `m` 单位的数值字符串，例如 `2.4km` 或 `500m`，不得附加细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应进行支持的解析与规范化，检查显式配置的 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，并按字符串数组的 `format`=`distance` 规范化 `retrieved_data`，再与单元素预期 `["1.7km"]` 做无序精确基数比较，不能有缺失、错误或额外项。稀疏配置未显式配置 `error_details`，因此物化的 `error_details:null` 不比较；也未配置 `NetworkEventEvaluator`，没有 filter、normalization 之外的网络比较或 last-event 语义。该唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 将响应匹配为 `task_type`=`RETRIEVE`、`status`=`SUCCESS` 和经距离规范化后无序精确匹配 `["1.7km"]` 的单元素 `retrieved_data`，且 `TaskEvalResult.score` 为 `1.0`；它还明确称未配置 `NetworkEventEvaluator`。它仍把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，分别用于响应匹配和 trace/context 无错误完成 evaluation；匹配并无错误为 success，响应或距离不匹配以及 evaluator/orchestration/trace 错误为 failure，无法恢复完整 `TaskEvalResult` 或足够的 response 与 HAR 时为 undecided。非空 stronger condition `verify_osrm_walking_route` 要求 `network.har` 显示两地点之间成功的 OSRM 步行路线请求，且返回距离与提交值一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_native_trace`
- 为什么修改：`network.har` 被列为原生决定性证据，尽管任务 `364` 仅配置了 `AgentResponseEvaluator`，且数据包所表示的跟踪内容不会影响已配置的距离比较。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，仅为明确说明的更强 OSRM 方法条件保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`narrow_undecided_to_response_integrity`
- 为什么修改：`undecided` 规则使重建依赖于 `network.har` 或未具名的已留存 `TaskEvalResult`，可能会将非决定性证据缺失归类为 `undecided`。
- 应如何修改：使 `undecided` 仅取决于 `agent_response.json` 的丢失、损坏、不完整或来源验证失败；对于完整但格式错误、为 `null`、不匹配或导致 evaluator 出错的响应，仍应判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_native_minimality`
- 为什么修改：冗余的原生跟踪 artifact 及相应的 `undecided` 分支，使检查清单不必要地降低了紧凑性和内部一致性。
- 应如何修改：使用 `agent_response.json` 作为唯一的原生决定性 artifact，并将 `network.har` 的适用范围完全限定于更强条件。

## Case 365

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service 测量 Carnegie Music Hall 与 UPMC Shadyside 之间的步行距离，task type 为 `RETRIEVE`。只可返回带 `km` 或 `m` 单位的数值字符串，不得包含其他细节。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 检查响应规范化后的 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，并依据字符串数组的 `format`=`distance` 规范化 `retrieved_data`，然后与唯一预期值 `2.2km` 做无序精确比较，不允许缺项、错项或额外项。只有稀疏配置中显式出现的 `task_type`、`status` 和 `retrieved_data` 被比较，物化默认值 `error_details:null` 不参与；没有 `NetworkEventEvaluator`、网络 filter 或 last-event 规则。唯一 evaluator 得分须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是 evaluation 无错误完成，响应规范化为 `RETRIEVE`、`SUCCESS`，且无序 `retrieved_data` 单元素按距离 schema 匹配 `2.2km`，使唯一 evaluator 与 `TaskEvalResult.score` 都为 `1.0`。它把 `agent_response.json` 和 `network.har` 均列为决定性 artifacts，后者用于确认 HAR 可解析为 evaluation context 所需的 `NetworkTrace`，同时承认原生响应比较不检查路线内容；正确匹配为 success，空、不可解析或不匹配的响应及 evaluator/orchestration error 为 failure，无法恢复 evaluator 收到的 response 和 trace 且无真实结果时为 undecided。非空 stronger condition `verify_osrm_walking_route` 额外要求 `network.har` 证明 Carnegie Music Hall 与 UPMC Shadyside 之间成功的 OSRM 步行路线计算，且返回距离与 `2.2km` 一致。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_not_decisive`
- 为什么修改：`network.har` 被错误地列为决定性原生 artifact；此 case 的唯一已配置 evaluator 读取 `agent_response_raw`，且不比较网络事件。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅在更强的 OSRM/步行验证条件下保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_wrongly_undecided`
- 为什么修改：原生 `undecided` 规则错误地将恢复跟踪作为必要条件，尽管跟踪内容并不决定已配置的 `AgentResponseEvaluator` 比较结果。
- 应如何修改：当没有真实的 evaluator 结果保留判定结论时，将原生 `undecided` 状态限定为代理响应丢失、损坏、不完整或来源验证失败的情况；不要仅因缺失 `network.har` 就将原生判定设为 `undecided`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace`
- 为什么修改：原生部分为 `network.har` 冗余地赋予了一个仅在更强条件下才有依据的角色，使检查清单不再最小化。
- 应如何修改：使原生证据和重建规则仅基于响应，同时仅将 `network.har` 保留为更强条件的证据。

## Case 366

### 原本 case 是什么

原始任务是在 `map` 站点使用 OSRM direction service 测量距离 UPMC Shadyside 最近的 CVS 与 UPMC Shadyside 之间的步行距离，task type 为 `RETRIEVE`。响应只能是带 `m` 或 `km` 单位的数值字符串，不得附加细节。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 解析并规范化响应，比较显式配置的 `task_type`=`RETRIEVE`、`status`=`SUCCESS`，以及按字符串数组 `format`=`distance` 规范化后与 `["1.2km"]` 无序精确匹配的单元素 `retrieved_data`；不得缺失、为 `null`、不匹配或含额外项。物化默认字段 `error_details:null` 并非稀疏配置中的显式比较字段；没有 `NetworkEventEvaluator`，因而没有网络 filter 或 last-event 语义。该 evaluator 无失败断言或 evaluator error 且得 `1.0` 时，作为唯一 evaluator 才会使 `TaskEvalResult.score` 为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 为 `TaskEvalResult.score = 1.0`，要求唯一的 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS`，并使无序距离数组精确匹配 `["1.2km"]`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并在 success 中要求所需 artifacts 可用；响应缺失、非对象、字段或距离不匹配以及 artifact parsing、evaluator 或 orchestration error 为 failure，response 或 trace 未保留、截断或无法归属且无官方结果时为 undecided。非空 stronger condition `verify_osrm_walking_route_provenance` 要求 `network.har` 和 `agent_response.json` 共同证明选择的是最近的 CVS、使用了 OSRM 步行路线，且路线距离支持所报告的 `1.2km`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_trace_requirement_changes_claim`
- 为什么修改：原生规则要求 `network.har` 可用，尽管 case `366` 仅配置了 `AgentResponseEvaluator`，且其比较读取 `agent_response_raw`。
- 应如何修改：从原生 `success` 和原生结果重建中移除对 `network.har` 留存或可解析性的要求；仅将其保留为明确说明的更强路由来源条件的证据。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_artifact`
- 为什么修改：`network.har` 被列为决定性原生 artifact，尽管其路由内容无法影响唯一已配置的响应比较。
- 应如何修改：使用完整的 `agent_response.json` 作为唯一且最小的决定性原生 artifact。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`trace_loss_misclassified`
- 为什么修改：尽管完整响应足以确定此 case 的已配置检查结果，检查清单仍可能将网络跟踪缺失或被截断归类为 `undecided`，并要求跟踪可用才能判定为 `success`。
- 应如何修改：将原生 `undecided` 状态限定为影响 `agent_response.json` 的丢失、截断、完整性或来源问题；将完整但无效的响应或比较错误归类为 `failure`。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace`
- 为什么修改：原生部分包含不必要的跟踪 artifact 及相关结果条件。
- 应如何修改：删除原生 `network.har` 条目以及原生 `success` 和 `undecided` 规则中对它的引用，同时在更强条件下保留 `network.har`。

## Case 367

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：使用 OSRM direction service，测量 Carnegie Mellon University 到最近一家 CVS 的步行距离。输出只能是一个带 `km` 或 `m` 单位的数值字符串，例如 `2.4km` 或 `500m`，不得附加其他说明。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`；它对最终响应进行解析和规范化，并比较显式配置的 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: ["1.4km"]`。`retrieved_data` 按 `results_schema` 的字符串距离格式规范化，数组以 `ordered: false` 比较，因此忽略顺序，但仍要求恰好一个与 `1.4km` 等价的元素；物化产生的 `error_details: null` 并非稀疏配置中的比较字段。该任务没有基于 `network.har` 的 evaluator，也没有 last-event 语义；只有该 evaluator 无错误、无失败断言且得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是 `TaskEvalResult.score` 为 `1.0`，即唯一的 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`/`SUCCESS`，并在距离 schema 和无序比较下得到唯一匹配 `1.4km` 的距离。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并把两者均可用、评估无错误且无比较断言写成 success；响应畸形、字段或距离不匹配、元素缺失或多余，以及编排或 evaluator 错误写成 failure，而任一所需 artifact 缥失、截断或不可读且无保留结果时写成 undecided。非空 stronger condition `verify_osrm_walking_route_provenance` 另要求 `network.har` 证明选择了最近的 CVS，并证明从 Carnegie Mellon University 发起的 OSRM 步行路线距离支持所报值。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_native_har`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的 case，`network.har` 被错误地指定为决定性原生证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`；仅为单独的更强来源条件保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`remove_har_native_decision_gate`
- 为什么修改：尽管没有配置网络事件检查，`success` 和 `undecided` 规则仍使 HAR 的可用性或留存情况影响原生裁决。
- 应如何修改：原生 `success`、`failure` 和 `undecided` 应仅以完整代理响应是否允许重建已发布的 `AgentResponseEvaluator` 比较为依据；HAR 缺失仅用于更强条件的裁决。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_native_shape`
- 为什么修改：冗余的原生 HAR artifact 及相关规则使检查清单超出了最小充分证据集的范围。
- 应如何修改：使用 `agent_response.json` 作为唯一的原生决定性 artifact，并移除所有原生 HAR 可用性要求。

## Case 368

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`，返回站内可用的全部折扣（sale）商品列表。输入没有规定其他输出细节。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，其显式期望是 `task_type: RETRIEVE`、`status: NOT_FOUND_ERROR` 和 `retrieved_data: null`，且 `results_schema` 为 `{"type":"null"}`。该 evaluator 对最终响应进行支持的 JSON 文本或代码块解析、字段规范化及结构比较；物化默认值 `error_details: null` 不计入比较。没有配置网络 evaluator 或 last-event 过滤语义，`network.har` 内容不参与这一响应比较；唯一 evaluator 必须无错误且得分为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 写为唯一 `AgentResponseEvaluator` 把提交响应解析并规范化为 `task_type: RETRIEVE`、`status: NOT_FOUND_ERROR`、`retrieved_data: null`，从而使 evaluator 和 `TaskEvalResult` 均得 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并将所需输入可解析、无编排或 evaluator 错误且结构匹配列为 success；不可比较、字段不匹配、`retrieved_data` 非 null 或任何结构比较失败列为 failure；无法确定实际响应和 HAR 时列为 undecided。非空 stronger condition `substantiate_no_sale_items` 要求 `network.har` 中的购物响应正文及分页或结果元数据具有足够覆盖面，以证明确实没有折扣商品。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_is_not_decisive`
- 为什么修改：`network.har` 被错误地指定为决定性原生证据，尽管唯一已配置的 evaluator 读取代理响应，且预期的 `retrieved_data` 为 `null`。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。可将其保留为明确说明的更强事实一致性条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_improperly_controls_native_decision`
- 为什么修改：判定规则要求 HAR 可解析且其来源已得到确认，才能判定为 `success`；否则允许判定为 `failure` 或 `undecided`，从而增加了重建已配置响应评分并不需要的条件。
- 应如何修改：基于对完整已提交响应应用已发布的 `AgentResponseEvaluator` 语义来判定原生 `success` 和 `failure`。将 `undecided` 限定为确切响应丢失或其完整性/来源信息丢失的情况；完整无损但格式错误或不匹配的响应仍应判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_rules`
- 为什么修改：对于此 evaluator 配置，额外的原生 HAR artifact 和重复的 HAR 解析要求使检查清单不再最小化。
- 应如何修改：仅保留 `agent_response.json` 作为原生决定性证据，并从原生 `success`、`failure` 和 `undecided` 规则中移除依赖 HAR 的表述。

## Case 383

### 原本 case 是什么

原始任务是在 `map` 站点执行 `RETRIEVE`：查找 Pittsburgh Airport 附近是否有 Hyatt 酒店；如有，返回酒店名称以及从该酒店驾车 15 分钟内的所有超市名称。须使用 OSRM direction service，并以含键 `"hotel"` 和 `"supermarkets"` 的对象列表返回。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，显式期望 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 中唯一对象 `{"hotel":"Hyatt Regency Pittsburgh International Airport","supermarkets":["Giant Eagle","ALDI"]}`。它会提取最终响应，对适用的字符串或 fenced JSON 尝试 JSON 解码；缺少 `task_type` 时可采用 `performed_operation`，非空且非列表的 `retrieved_data` 会先包装为单元素序列，再按包含 `location-name` 的对象 schema 规范化。`ordered: false` 使外层数组和嵌套的 `supermarkets` 数组均递归无序比较，但元素数、对象键和规范化值仍须匹配；额外顶层字段及物化默认的 `error_details: null` 不参与显式比较。没有网络 evaluator、filter 或 last-event 语义；唯一 evaluator 无错误且得分 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 是唯一 `AgentResponseEvaluator` 对最终响应进行 schema 规范化和无序比较后得 `1.0`，从而令 `TaskEvalResult.score = 1.0`；它要求结果为 `RETRIEVE`/`SUCCESS`、唯一指定酒店及超市 `Giant Eagle` 和 `ALDI`。它把 `agent_response.json` 和 `network.har` 都作为决定性 artifacts，将输入可评估、无错误并完全匹配列为 success；非字典、缺失或错误的 `task_type`/`status`、数据结构或值不匹配、HAR 无法解析及 evaluator 错误列为 failure；任一 artifact 缺失或截断且无保留结果时列为 undecided。非空 stronger condition `verify_osrm_driving_times` 要求结合 `agent_response.json` 与 `network.har`，证明从所报酒店到每个所报超市均有 OSRM 路线，且驾车时长不超过 15 分钟（`900` 秒）。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`actual_response_semantics_incomplete`
- 为什么修改：原生规则遗漏了 `task_type` 缺失时对 `performed_operation` 的回退处理，以及对非列表 `retrieved_data` 应用的单元素列表强制转换。
- 应如何修改：说明这些被接受的解析/规范化行为；当规范化后的逻辑值匹配时，不要将原始 `task_type` 字段缺失或单对象 `retrieved_data` 直接判定为 `failure`。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`nonminimal_native_har`
- 为什么修改：尽管没有配置 `NetworkEventEvaluator`，且 `AgentResponseEvaluator` 仅提取响应，`network.har` 仍被视为强制性的原生证据。
- 应如何修改：使用完整的 `agent_response.json` 作为唯一的原生决定性 artifact。仅在更强的 OSRM 条件下保留 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_failure_and_undecided_boundaries`
- 为什么修改：`failure` 规则忽略了 `performed_operation` 别名，而 `undecided` 规则将不必要的原生 HAR 丢失视为决定性因素，并与 HAR 解析失败规则重叠。
- 应如何修改：将 `failure` 定义为完整响应未能通过已发布的解析、规范化、比较或 evaluator 执行；将 `undecided` 保留给确切的完整代理响应或其来源信息丢失的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_section_not_minimal_or_coherent`
- 为什么修改：不必要的原生 HAR 要求以及相互重叠的 HAR `failure`/`undecided` 规则，使检查清单不够最小化且含义模糊，尽管其中不包含运行信息泄漏。
- 应如何修改：从原生证据和原生判定规则中移除 HAR，仅为单独标注的更强条件保留它。

## Case 384

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`，列出抱怨 EYZUTAK 手机壳质量的顾客姓名。任务未要求执行写入或修改操作。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，显式期望 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data: ["Lisa Lee","Evelyn Kurver","Amanda","N Randall"]`。响应经解析和规范化后，`retrieved_data` 按字符串数组 schema、以 `ordered: false` 的无序多重集语义比较，不允许姓名缺失、额外或重复不匹配；缺少 `task_type` 时可接受 `performed_operation` 作为旧别名，物化默认的 `error_details: null` 不比较。没有网络 evaluator、filter 或 last-event 语义；`EvaluatorResult.create` 仅在无 evaluator 错误且断言均成功时给出 `1.0`，而唯一 evaluator 得分为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将 benchmark success 写为响应规范化成 `RETRIEVE`/`SUCCESS`，且无序结果恰为 `Lisa Lee`、`Evelyn Kurver`、`Amanda`、`N Randall`，使唯一 evaluator 和 `TaskEvalResult` 得 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts；将字段和四人数组完全匹配、输入及评估上下文无错误写成 success，将不可解析或非对象响应、字段或姓名集合不匹配以及输入、编排或 evaluator 错误写成 failure，并称保留证据不足以确定响应、HAR 或官方结果时为 undecided。draft 的 `checked_by` 同时错误地声称“无断言或 evaluator error”会映射为 `1.0`；其 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incorrect_evaluator_error_scoring_and_alias`
- 为什么修改：`checked_by` 声称 evaluator 错误映射为评分 `1.0`，且 `fail_if` 将缺失 `task_type` 视为 `failure`，即使提供了可接受的 `performed_operation` 别名。
- 应如何修改：说明评分 `1.0` 要求不存在 evaluator 错误且断言成功，并明确 `performed_operation` 被接受为 `task_type` 的旧版别名。仅保留对三个稀疏配置的预期字段的比较。

#### 修改项 2：native.checked_by 及 evaluator 组合规则

- Finding ID：`composition_contradiction`
- 为什么修改：检查清单的评分描述暗示 evaluator 错误可以获得 `1.0`，这与其自身的 `failure` 规则冲突。
- 应如何修改：使用一条无歧义的组合规则：唯一的 `AgentResponseEvaluator` 必须无错误地完成并且评分恰好为 `1.0`；任何不匹配或 evaluator/编排错误均为原生 `failure`。

#### 修改项 3：native.decisive_artifacts

- Finding ID：`nonminimal_har_evidence`
- 为什么修改：检查清单指定了 `network.har`，尽管此 case 仅配置了 `AgentResponseEvaluator`，且其响应比较不检查网络事件。它还依赖未被列为决定性证据的官方 `TaskEvalResult`。
- 应如何修改：保留完整的 `agent_response.json` 作为唯一的决定性原生 artifact，并基于该 artifact 进行重建和 `undecided` 处理。

#### 修改项 4：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_and_evidence_inconsistent_rules`
- 为什么修改：`failure` 规则拒绝缺少 `task_type` 的响应，尽管 `performed_operation` 可能提供相同的已配置字段；同时，`undecided` 处理依赖于不必要或未具名的 artifact。
- 应如何修改：仅当 `task_type` 和 `performed_operation` 均缺失，或规范化后的任务类型不匹配时，才判定为 `failure`；从判定规则中移除对 HAR 和未具名结果的依赖。

#### 修改项 5：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_and_internally_incoherent`
- 为什么修改：额外的 HAR artifact 和相互矛盾的错误评分陈述，使检查清单无法保持紧凑和内部一致。
- 应如何修改：从决定性证据中移除 HAR，并纠正错误评分表述，同时保留有来源依据的预期名称和 evaluator 规则。

## Case 385

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `RETRIEVE`，列出认为 EYZUTAK 手机壳外观好看的顾客姓名。任务依据购物评论中的这一评价筛选姓名。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，显式期望 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data: ["Lisa Lee","MH","Misba009","Amanda","Cally","Bethany Robertson"]`。响应经过代码块/JSON 提取和规范化，姓名按字符串数组 schema 及 `ordered: false` 的无序多重集语义比较，顺序不重要，但不得缺失、额外或出现重复不匹配；物化默认的 `error_details: null` 不是显式比较字段。没有配置网络 evaluator、filter 或 last-event 语义；唯一 evaluator 必须无失败断言且得分为 `1.0`，所有 evaluator 得分均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是唯一 `AgentResponseEvaluator` 将响应解析、规范化为 `RETRIEVE`/`SUCCESS`，并使 `retrieved_data` 精确匹配无序多重集 `{Lisa Lee, MH, Misba009, Amanda, Cally, Bethany Robertson}`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；完全匹配且评估无错误为 success，无可用响应、结构或字段不匹配、姓名缺失或多余、输入加载或 evaluator 错误为 failure，而响应或 HAR 缺失、截断且没有完整官方结果时为 undecided。其 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_artifact`
- 为什么修改：`network.har` 被表述为决定性证据，尽管唯一已配置的 evaluator 比较的是代理响应，且客户名称比较不依赖跟踪内容。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为最小充分留存证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`restrict_undecided_to_decisive_evidence_loss`
- 为什么修改：当前的 `undecided` 规则将 `network.har` 丢失视为会阻止重建这个仅基于响应的 case。
- 应如何修改：使 `undecided` 仅取决于 `agent_response.json` 的丢失、损坏、截断或来源验证失败；完整但无效或不匹配的响应必须仍判定为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_evidence_set`
- 为什么修改：不必要的跟踪条目及依赖跟踪的 `undecided` 规则使检查清单不再最小化。
- 应如何修改：删除跟踪专用 artifact 和判定表述，同时保留响应比较和 evaluator 错误规则。

## Case 386

### 原本 case 是什么

原始任务是在 `shopping` 站点查询 Ugreen lightning to 3.5mm cable 的 rating，task type 为 `RETRIEVE`。官方指令是 `What is the rating of Ugreen lightning to 3.5mm cable?`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`：它对最终响应执行已发布的提取、解析和 normalization，并比较显式配置的 `task_type`、`status`、`retrieved_data`。期望分别为 `RETRIEVE`、`SUCCESS` 和按 array-of-numbers schema 归一化后的无序单元素数组 `[65]`；`ordered:false` 表示不考虑顺序，materialized 的 `error_details:null` 不是 sparse 配置中的显式比较字段。该 evaluator 必须得到 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 接受 `RETRIEVE`/`SUCCESS` 且 `retrieved_data` 归一化为无序 `[65]`，从而 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并将响应匹配且 trace 可用于构造 evaluation context 判为 success；响应、结构、字段或数据不匹配以及解析、evaluator、orchestration 或 trace 错误判为 failure。若任一 artifact 缺失或不完整且没有足够的 retained evaluation result，则判为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`remove_nondecisive_network_trace`
- 为什么修改：`network.har` 仅因通用解析和环境上下文方面的考虑而被列为决定性证据，尽管不存在 `NetworkEventEvaluator`，也不存在依赖网络的检索值。
- 应如何修改：仅保留完整的 `agent_response.json` 作为决定性证据，并移除对未具名的留存评估结果的依赖。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`correct_trace_based_decision_rules`
- 为什么修改：当前的 failure 和 undecided 规则允许 `network.har` 的可用性或可用程度控制这个仅响应型案例的判定。
- 应如何修改：success 和 failure 应以对完整最终响应的已发布评估为依据，并将 undecided 限于完整响应丢失或其完整性/来源无法确认的情形。已知完整但无效或不匹配的响应必须仍判为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`restore_minimal_coherent_evidence_set`
- 为什么修改：该检查清单包含非决定性跟踪，并有条件地调用一个未出现在 `decisive_artifacts` 中的评估记录。
- 应如何修改：使用一条基于 `agent_response.json` 的一致证据路径，并从原生判定规则中省略 `network.har` 和未具名的替代记录。

## Case 387

### 原本 case 是什么

原始任务是在 `shopping` 站点找出给 EYZUTAK phone cases 打了 4 或 5 stars 的 reviewers，task type 为 `RETRIEVE`。官方指令是 `Who gave 4 or 5 stars for phone cases from EYZUTAK`。

### Benchmark 怎么测

仅配置 `AgentResponseEvaluator`，用于对最终响应进行解析、schema-based string normalization 和结构比较。显式期望为 `task_type: RETRIEVE`、`status: SUCCESS`，以及 `retrieved_data` 的精确无序多重集 `["MH","Misba009","Amanda","Amazon Customer","Cally","Bethany Robertson"]`；不得缺少、增加或改变重复次数，materialized 的 `error_details:null` 不属于显式比较字段。唯一 evaluator 的分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native benchmark success 要求唯一的 `AgentResponseEvaluator` 无错误地得到 `1.0`，响应匹配 `RETRIEVE`/`SUCCESS`，且六个 reviewer 名称构成完全相同的无序多重集，因此 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts；响应或多重集存在结构、字段、缺项、增项或重复次数差异，以及响应/HAR 解析、context、normalization、evaluator 或 orchestration 错误，都被写为 failure。若一个或两个 retained artifacts 缺失、截断或无法确认属于 task 387，则写为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被列为决定性证据，尽管唯一配置的 evaluator 仅比较代理响应，而预期检索值只是纯文本形式的审阅者姓名。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：这些规则要求加载留存的 HAR 才能判定 success，并在任一 artifact 缺失时将案例判为 undecidable，从而不当地抬高了非决定性批处理 artifact 丢失的影响。
- 应如何修改：移除依赖 HAR 的 success、failure 和 undecided 条件。将 undecided 限于影响完整代理响应的丢失、损坏或来源不确定情形。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的 HAR artifact 及规则中对它的反复引用，使该检查清单对于这个仅响应型案例而言并非最小化。
- 应如何修改：围绕唯一的 `AgentResponseEvaluator` 和 `agent_response.json` 精简检查清单，同时保留已配置字段、normalization、无序精确比较以及非 1 即 failure 的语义。

## Case 388

### 原本 case 是什么

原始任务是在 `shopping` 站点找出给 EYZUTAK phone cases 打了 1 或 2 stars 的人，task type 为 `RETRIEVE`。官方指令是 `Who gave 1 or 2 stars for phone cases from EYZUTAK`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对响应执行已发布的提取、解析和 normalization，并比较显式配置字段 `task_type`、`status`、`retrieved_data`；`task_type` 可由 legacy `performed_operation` 提供。期望是 `RETRIEVE`、`SUCCESS`，以及按 array-of-strings schema 归一化后精确等于无序两元素多重集 `{"Evelyn Kurver","N Randall"}` 的 `retrieved_data`，不得有缺少、额外、不匹配或重复项；materialized 的 `error_details:null` 不作显式比较。该唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 success 要求响应映射中的 `task_type`（或 `performed_operation`）与 `status` 归一化为 `RETRIEVE` 和 `SUCCESS`，`retrieved_data` 精确匹配无序集合 `{Evelyn Kurver, N Randall}`，同时 HAR 不导致错误；唯一 evaluator 和 `TaskEvalResult.score` 均为 `1.0`。它将 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把无效响应、字段或数据不匹配、HAR 不可用以及 evaluator/task error 或非 `1.0` 分数写为 failure。缺少可读且与该 run 关联的响应或 HAR、又无 retained official `TaskEvalResult` 时写为 undecided。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：原生规则将 `network.har` 解析和有条件的环境回退提升为无条件的案例 success 语义，尽管并未配置 `NetworkEventEvaluator`。
- 应如何修改：从原生的 benchmark-success、checked-by、success 和 failure 谓词中移除 HAR 有效性及依赖跟踪的上下文验证。保留唯一 `AgentResponseEvaluator` 的解析、显式字段 normalization、无序精确比较以及由所有 evaluator 组成分数的方式。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`BF-2`
- 为什么修改：`network.har` 被列为决定性证据，尽管重建唯一配置的响应比较并不需要它。
- 应如何修改：使用完整的 `agent_response.json` 作为唯一、最小的决定性运行后 artifact，并从 `decisive_artifacts` 中移除 `network.har`。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`BF-3`
- 为什么修改：即使完整响应证据足以确定唯一配置的 evaluator，规则仍将无效 HAR 判为原生 failure，并将 HAR 缺失视为可能的 undecided。
- 应如何修改：success 和普通 failure 应以对完整响应的已发布评估为依据。将 undecided 限于与该次运行关联的响应证据发生丢失、损坏、截断、不可读或来源验证失败的情形。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-4`
- 为什么修改：反复出现的 HAR 要求使检查清单不够最小化，并在内部对原生 success 施加了过度约束。
- 应如何修改：删除非决定性的 HAR artifact 以及所有依赖 HAR 的判定条款，同时保留响应 evaluator 的决定性语义。

## Case 393

### 原本 case 是什么

原始任务是在 `gitlab` 站点的 `byteblaze/empathy-prompts` 项目中，向与 fixing the broken links 相关的 merge request 发布 `"lgtm"`，task type 为 `MUTATE`。官方指令是 `Post "lgtm" for the merge request related to fixing the broken links in byteblaze/empathy-prompts project`。

### Benchmark 怎么测

先运行 `AgentResponseEvaluator`：响应须解析为 mapping，显式配置的 `task_type`（可由 `performed_operation` 提供）和 `status` 分别归一化为 `MUTATE`、`SUCCESS`；sparse expected 还显式含 `retrieved_data:null`，但非 `RETRIEVE` 任务会将缺失或提供的该字段归一化为 null 且不比较其值，materialized 的 `error_details:null` 不检查。随后 `NetworkEventEvaluator` 过滤 normalized URL 为 `__GITLAB__/byteblaze/empathy-prompts/notes` 的 `POST` evaluation events，并因 `last_event_only:true` 只比较最后一个候选：要求 query 为 `target_id=["138843"]`、`target_type=["merge_request"]`，JSONPath post data 为 `$.note.note="lgtm"`、`$.note.noteable_type="MergeRequest"`，且 `response_status:200`。配置还规定 `decode_base64_query:false`、没有 ignored query/post patterns、`should_not_exist:false`；两个 evaluator 必须都为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 需要 `AgentResponseEvaluator` 接受配置的 `MUTATE`/`SUCCESS` 响应，并且 `NetworkEventEvaluator` 接受最后一个符合条件的 GitLab notes `POST`，两者均得 `1.0` 后 `TaskEvalResult.score` 才为 `1.0`。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts，要求后者的最后匹配事件满足 path、`target_id 138843`、`target_type merge_request`、`note.note "lgtm"`、`note.noteable_type "MergeRequest"` 和 `response status 200`；任一 evaluator 非 `1.0` 或报错即为 failure。artifact 缺失、不可读或不完整而无法重建 evaluator outcome，且没有其他 artifact 已确定失败时，写为 undecided。非空 stronger condition `persisted_merge_request_note` 另要求 post-run GitLab state 或 API export 显示该 `"lgtm"` note 持久存在于 `byteblaze/empathy-prompts` 的 merge request `138843`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_semantics_under_specified`
- 为什么修改：响应检查被简化为接受“已配置的 MUTATE/SUCCESS 响应”，遗漏了会影响分数的解析和稀疏预期字段行为。
- 应如何修改：说明已发布的提取/解析必须生成一个包含 `task_type`（或 `performed_operation`）和 `status` 的 mapping；明确 `task_type`、`status` 和 `retrieved_data` 是显式配置的稀疏字段；将具体化的 `error_details` 排除在比较之外；并描述 MUTATE 任务将 `retrieved_data` 置为 null 的行为。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`response_decision_rule_not_operational`
- 为什么修改：响应分支仅表述为“accepted”和“not accepted”，因此未提供可基于 artifact 重建的判定规则。
- 应如何修改：使 `success_if` 和 `fail_if` 明确区分以下情形：响应经解析和 normalization 后得到已配置的 mapping；以及完整但无效/null 的响应、缺少必需的 type/status、normalization 后不匹配或 evaluator error。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_over_compressed`
- 为什么修改：通过省略决定性的 `AgentResponseEvaluator` 行为实现了精简。
- 应如何修改：仅添加会影响分数的响应解析、显式字段、别名和非 retrieve normalization 细节，同时保持当前案例特定的范围且不包含运行结果。

## Case 396

### 原本 case 是什么

原始任务是在 `gitlab` 站点 fork ChatGPT，task type 为 `MUTATE`。官方指令是 `Fork ChatGPT.`。

### Benchmark 怎么测

`AgentResponseEvaluator` 测量最终响应是否经解析、字段投影和 normalization 后匹配显式配置的 `task_type:MUTATE`、`status:SUCCESS`、`retrieved_data:null`；materialized 的 `error_details:null` 不是显式 sparse 比较字段。`NetworkEventEvaluator` 筛选 normalized URL 为 `__GITLAB__/api/v4/projects/175/fork` 的 `POST` evaluation events，并按 `last_event_only:true` 比较最后一个候选，要求 post data 精确包含 `id:"175"`、`name:"Chatgpt"`、`namespace_id:2505`、`path:"chatgpt"`，且 `response_status:201`；配置为 `decode_base64_query:false`、无 ignored query/post patterns、`should_not_exist:false`。两个 evaluator 按配置顺序运行且都必须得 `1.0`，否则 `TaskEvalResult.score` 为 `0.0`，全部为 `1.0` 时才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 接受最终响应且 `NetworkEventEvaluator` 接受选中的 GitLab fork event，两者均得 `1.0` 后 `TaskEvalResult.score` 才为 `1.0`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，后者检查最后一个匹配 `POST __GITLAB__/api/v4/projects/175/fork` 的事件是否具有 `HTTP 201` 及 post data `id 175`、`name Chatgpt`、`namespace_id 2505`、`path chatgpt`；任一 evaluator 低于 `1.0`、报错或出现响应/事件缺失与不匹配均为 failure。required artifact 在 run 后丢失或不可读且没有 retained official evaluator result 能确定相应 component 时，写为 undecided。非空 stronger condition `confirm_persistent_fork_state` 另要求 post-run GitLab project/API state snapshot 显示 namespace `2505` 下存在 path `chatgpt`，并记录 project `175`（ChatGPT）为 fork origin。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_explicit_retrieved_data_expectation`
- 为什么修改：`AgentResponseEvaluator` 条件列举了 MUTATE 和 SUCCESS，却遗漏了稀疏配置中显式设置的 `retrieved_data: null` 字段。
- 应如何修改：说明已发布的响应解析、投影和 normalization 必须成功匹配 `task_type` MUTATE、`status` SUCCESS 和 `retrieved_data` null。不要将 `error_details` 添加为必需字段，因为它只是具体化的默认值。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`artifact_completeness_not_required`
- 为什么修改：决定性 artifact 问题列出了正确的文件，但未确认留存的响应和 HAR 是完整的。
- 应如何修改：将 `agent_response.json` 限定为留存的完整最终响应，将 `network.har` 限定为留存的完整跟踪，并要求其具有足够的完整性和来源信息，以重建已配置的检查。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_evidence_misclassification`
- 为什么修改：`undecided_if` 未涵盖可读但被截断、完整性失败和来源信息丢失的情形，而 `fail_if` 则宽泛地将事件缺失视为 failure。
- 应如何修改：仅当留存证据缺失、被截断、不可读、完整性受损或来源无法确定，导致无法重建，且没有留存的官方结果可作出判定时，才适用 undecided；明确仅在跟踪完整时，事件缺失才判为 failure。

## Case 397

### 原本 case 是什么

原始任务是在 GitLab 上 fork `MetaSeq`，官方指令为“Fork MetaSeq.”，task type 是 `MUTATE`。任务对应站点 `gitlab`，revision 为 `2`。

### Benchmark 怎么测

配置了一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者对 `agent_response.json` 进行解析和规范化，并比较稀疏配置字段 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；物化出的默认 `error_details: null`不是显式配置的比较字段。后者检查 `network.har`，以 `last_event_only=true` 选择最后一个符合方法和路径筛选的事件，并要求其完整匹配 `POST __GITLAB__/api/v4/projects/33/fork`、post data 中 `id: "33"`、`name: "metaseq"`、`namespace_id: 2505`、`path: "metaseq"`以及 `response_status: 201`。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 均得 `1.0`，并把 `agent_response.json` 和 `network.har`列为决定性 artifacts。其 success 条件是响应通过 `MUTATE/SUCCESS` 比较且最后一个匹配的 fork 事件满足全部 URL、方法、post-data 和 `201` 状态要求；任一响应或网络检查不匹配、缺少事件或报错均被写为 failure，并称任一 evaluator 低于 `1.0` 会使任务分数为 `0.0`。其 undecided 条件允许在任一完整 artifact 缺失时，由“retained official evaluator result”解决缺失检查。非空 stronger condition `post_run_fork_state` 进一步要求“End-of-run GitLab project lookup or state export”证明 namespace `2505` 中的 `metaseq` 是源项目 `33` 的 fork。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`undeclared_evaluator_result_substitute`
- 为什么修改：undecided 规则允许使用留存的官方 evaluator 结果替代缺失的完整 `agent_response.json` 或 `network.har`，尽管该结果并非数据包中声明并具名的决定性 artifact。
- 应如何修改：移除 evaluator 结果例外，并要求提供完整的 `agent_response.json` 和 `network.har`；仅在它们发生留存、完整性或来源信息丢失时判为 undecided。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_rule_too_permissive`
- 为什么修改：“and no retained official evaluator result resolves the missing check”这一表述允许在缺少所需留存 evaluator 输入的情况下作出判定。
- 应如何修改：重写 `undecided_if`，使必需 artifact 缺失、不完整、损坏或来源未经证实时判为 undecidable，而完整但无效的响应、完整跟踪中不存在匹配项、不匹配以及 evaluator error 仍判为 failure。

## Case 402

### 原本 case 是什么

原始任务是在 discussion forum 中把当前用户的 bio 改为精确字符串 `"Freelance Web Developer"`，task type 是 `MUTATE`。配置站点为 `reddit`，revision 为 `2`。

### Benchmark 怎么测

配置了 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者解析并规范化 `agent_response.json`，比较显式配置的 `task_type: MUTATE` 与 `status: SUCCESS`；`retrieved_data` 虽在配置中出现，但对该非 `RETRIEVE` 任务不进行值检查并规范化为 `null`，物化默认值 `error_details: null`不是显式比较字段。后者在 `network.har` 中要求至少一个事件完整匹配 `POST __REDDIT__/user/MarvelsGrantMan136/edit_biography`、字段 `user_biography[biography]: "Freelance Web Developer"`和 `response_status: 302`；由于 `last_event_only=false`、`should_not_exist=false`，任一完整匹配事件即可，且没有额外 schema、ignore rule、header、response content 或 cookie 条件。`TaskEvalResult.score` 采用合取组合，两个 evaluator 都必须得 `1.0`。

### 原本 draft 是什么

原始 draft 声明仅当 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 响应且 `NetworkEventEvaluator` 接受至少一个 biography-update 事件时，`TaskEvalResult.score` 才为 `1.0`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它把两个 evaluator 都得 `1.0`列为 success，把响应不匹配或报错、没有完整匹配事件、网络 evaluator 报错或 task-evaluation error 列为 failure。其 undecided 条件是在任一 artifact 缺失或不可读且没有 retained official `TaskEvalResult`确定两个 evaluator 结果时无法判定。非空 stronger condition `persisted_final_biography` 要求额外的“End-of-run forum profile page/DOM capture or profile-state export”显示 `MarvelsGrantMan136` 的最终 biography 恰为 `"Freelance Web Developer"`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`raw_artifact_substitution`
- 为什么修改：`undecided_if` 允许使用留存的官方 `TaskEvalResult` 替代缺失或不可读的 `agent_response.json` 或 `network.har`，尽管这些完整 artifact 是重建已配置 evaluator 所需的、具名的最小证据。
- 应如何修改：移除 `TaskEvalResult` 例外，并规定只要任一完整原始 artifact 不可用，或缺乏足以进行独立重建的完整性/来源信息，就必须判为 undecided。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_scope`
- 为什么修改：当前的例外规定使证据丢失不会仅因存在结果摘要而被判为 undecided，削弱了这项规则：undecided 应根据能否从留存的决定性证据中重建已配置的检查来确定。
- 应如何修改：将 `undecided_if` 限于 `agent_response.json` 或 `network.har` 缺失、不完整、损坏、不可读或来源不确定并导致无法重建的情形，不得仅以 evaluator 输出作为替代。

## Case 406

### 原本 case 是什么

原始任务是在 Reddit 的 future technology forum 中 upvote 最新的 post，task type 是 `MUTATE`。配置站点为 `reddit`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 对 `agent_response.json`执行字符串或代码块 JSON 解析及规范化，要求显式配置字段 `task_type`（或兼容的 legacy `performed_operation`）归一为 `MUTATE`、`status`归一为 `SUCCESS`，并将该非 `RETRIEVE` 任务的 `retrieved_data`归一为 `null`；默认 `error_details`不参与显式比较。`NetworkEventEvaluator` 在 `network.har` 中先按 `POST` 和规范化路径 `/sv/119517.json`筛选，再因 `last_event_only=true`选择最后一个候选，并要求其完整规范化 URL 匹配 `__REDDIT__/sv/119517.json`及配置的 query 语义，同时满足 post data `choice: "1"`、方法 `POST`和 `response_status: 200`；`decode_base64_query=false`。两个 evaluator 的分数都必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score = 1.0` 当且仅当响应被接受为 `MUTATE/SUCCESS`、`retrieved_data`归一为 `null`，并且最后一个匹配 `POST` 与 Reddit 路径 `/sv/119517.json`的事件具有 `choice: "1"`和状态 `200`；它将 `agent_response.json` 与 `network.har`列为决定性 artifacts。它把两个 evaluator 重新评估均得 `1.0`写为 success，把任一 evaluator 非 `1.0`或报错、响应不被接受、或缺少所述 POST/路径/choice/status 事件写为 failure。其 undecided 仅限 artifact 未保留或被截断而无法重建 evaluator 结果。非空 stronger condition `confirm_target_and_persisted_vote` 要求额外的 forum listing/API snapshot 证明 submission `119517`确为该 forum 最新 post，并由 authenticated submission 或 vote-state snapshot 证明 acting account 的 upvote 在运行后存在。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_comparison_omitted`
- 为什么修改：原生网络规则仅描述了匹配 Reddit 路径 `/sv/119517.json`。在按 method/path 过滤并选择最后一个事件后，已发布的 evaluator 会比较 normalization 后的完整 URL；因此，未被忽略的 query 差异可能改变分数。
- 应如何修改：说明最后一个经过 POST/path 过滤的候选项必须在已配置的 query normalization 下，与 normalization 后渲染得到的预期完整 URL `__REDDIT__/sv/119517.json` 完全匹配，此外还必须满足 `post_data` choice `"1"`、method POST 和 status 200。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_url_semantics_not_preserved`
- 为什么修改：这份原本简洁的检查清单没有保留按路径过滤与随后进行完整 normalization URL 比较之间会影响分数的区别。
- 应如何修改：在 `benchmark_success`、网络 artifact 问题和解释性 failure 规则中，将仅路径的简写替换为简洁的完整 URL normalization/比较表述。

## Case 409

### 原本 case 是什么

原始任务是在指定 Reddit post 中，回复网站 manager，正文必须为精确字符串 `"thanks! I am a big fan of your website."`，task type 是 `MUTATE`。配置站点为 `reddit`，起始页面是 `__REDDIT__/f/books/59421/friendly-reminder-bookshop-org-exists`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator`解析并规范化 `agent_response.json`，比较稀疏配置字段 `task_type: MUTATE`、`status: SUCCESS`和该非 `RETRIEVE` 任务归一后的 `retrieved_data: null`；`error_details: null`只是物化默认值，不是显式比较字段。`NetworkEventEvaluator`从 `network.har` 的非静态 evaluation events 中，按 `POST`和规范化路径 `__REDDIT__/f/books/59421/-/comment/1235250`筛选，并以 `last_event_only=true`选择最后一个候选；该事件还必须完整匹配规范化 URL、`POST`方法、`response_status: 302`及字段 `reply_to_comment_1235250[comment]: "thanks! I am a big fan of your website."`。URL 规范化使用 `decode_base64_query=false`，没有 ignored query 参数或 pattern、query schema、post-data schema 或 ignored post-data pattern；较早的匹配事件不能挽救最后候选的不匹配。只有两个 evaluator 均得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明任务分数仅在 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS`且 `NetworkEventEvaluator`接受最后一个匹配的 Reddit reply POST 时为 `1.0`，决定性 artifacts 为 `agent_response.json` 和 `network.har`。它把响应通过配置比较且最后一个 URL-and-method-matching 事件通过回复文本与 `302`状态比较写为 success；响应格式或比较失败、没有匹配 POST、最后事件的文本或状态不符以及 evaluator 报错均被写为 failure。其 undecided 条件允许在 artifact 不可用或截断时，由 retained official evaluator result 解决受影响检查，并明确已记录的无效响应、无效 trace 或完整 trace 中无候选事件属于 failure。非空 stronger condition `persisted_reply_state` 要求“Post-run Reddit thread or database state snapshot”证明 comment `1235250`下存在正文完全等于请求文本的直接持久化回复。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_expected_field_omitted`
- 为什么修改：检查清单将 `AgentResponseEvaluator` 描述为仅进行 MUTATE/SUCCESS 比较，尽管稀疏任务中显式配置了 `retrieved_data:null`。
- 应如何修改：说明已发布的解析和 normalization 会比较显式配置的 `task_type` MUTATE、`status` SUCCESS 以及 normalization 后的 `retrieved_data` null。明确非 RETRIEVE normalization 会将 `retrieved_data` 映射为 null，并且具体化的 `error_details:null` 默认值不是显式配置的比较字段。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_filter_comparison_conflated`
- 为什么修改：网络相关表述混淆了初始 URL/method 匹配与最终比较。已发布的代码先按 normalization 后的 URL path 和 method 进行过滤，选择最后一个此类事件，然后比较该事件的 normalization 后完整 URL 及其他已配置字段。
- 应如何修改：描述这一两阶段行为，并包括已配置的 URL normalization 设置：`decode_base64_query=false`、没有被忽略的 query 名称或模式，并且没有 query schema。同时保留 `last_event_only=true`、`should_not_exist=false`、POST、status 302 以及预期 POST 字段。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`network_decision_rule_incomplete`
- 为什么修改：当前 success/failure 规则未明确将所选的最后一个 path-and-method 事件的 normalization 后完整 URL 不匹配计为 failure。
- 应如何修改：要求所选事件通过 normalization 后完整 URL、method、POST-data 和 status 比较，并说明：对于完整跟踪，如果所选事件的上述任一字段比较失败，即使更早的事件本可通过，也应判为 failure。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：检查清单虽然简洁且不含运行结果，但遗漏了决定性的响应和 URL 比较语义。
- 应如何修改：将原生规则替换为简洁表述，其中包括稀疏响应字段以及 `NetworkEventEvaluator` 先匹配最后一个 path 事件、再进行 normalization 后完整比较的行为，且不添加特定于运行的材料。

## Case 411

### 原本 case 是什么

原始任务是在 GitLab 仓库 `byteblaze/cloud-to-butt` 中把 `LICENSE` 改为 MIT license，task type 是 `MUTATE`。配置站点为 `gitlab`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator`解析并规范化 `agent_response.json`，要求结构化响应的 `task_type`（或 legacy `performed_operation`）归一为 `MUTATE`、`status`归一为 `SUCCESS`，并将非 `RETRIEVE` 的 `retrieved_data`按显式 `null`配置比较；物化的 `error_details: null`不属于显式比较字段。`NetworkEventEvaluator`在 `network.har` 中筛选 `POST`且规范化路径匹配三个 URL 之一的事件：`__GITLAB__/byteblaze/cloud-to-butt/-/update/master/LICENSE.txt`、`__GITLAB__/byteblaze/cloud-to-butt/-/create/master`、`__GITLAB__/byteblaze/cloud-to-butt/-/blob/master/LICENSE`，并以 `last_event_only=true`选择最后一个。所选事件必须完整满足 URL、`response_status: 302`及 post-data schema/条件：恰有一个顶层键匹配 `^file_path|file_name$`且值为 `LICENSE`，`_method`匹配 `^.*(?!delete$).*$`，`branch_name`为 `master`，`content`匹配 `^.*MIT.*License.*$`；URL 规范化禁用 base64 query 解码且没有 query ignore rule。只有 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`都得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 为 `TaskEvalResult.score = 1.0`，要求响应通过 `MUTATE/SUCCESS`检查，并要求最后一个匹配允许 repository URL 的 `POST`满足所有请求和响应条件；决定性 artifacts 是 `agent_response.json` 与 `network.har`。它把两个 evaluator 均得 `1.0`写为 success，把响应不匹配、没有选中 POST、任一网络字段不匹配或 evaluator 报错写为 failure，并称这些情况会使任务分数为 `0.0`。其 undecided 仅限 retained agent response 或 HAR 缺失、不完整到无法重建实际 evaluator 输入，并说明 screenshot 或 repository state 单独不足以决定两个 native component scores。非空 stronger condition `confirm_persisted_mit_license` 要求“Post-run GitLab repository snapshot or API response for master:LICENSE”证明 `byteblaze/cloud-to-butt` 的 `master`分支存在 `LICENSE`且内容是 MIT license。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_match_constraints_under_specified`
- 为什么修改：原生网络证据问题仅表述为“configured GitLab URL”和“post data matching LICENSE”。它没有说明哪三个 URL 备选项符合条件，也没有说明必须从且仅从一个匹配 `^file_path|file_name$` 的顶层 key 中提取 LICENSE。这两个细节都可能改变 evaluator 分数。
- 应如何修改：通过以下方式使网络规则可操作：列举三个已配置的 URL 备选项，明确 POST 过滤和 `last_event_only=true`，并说明正则表达式 key 提取、status、post-data 模式、已配置的 schema normalization 以及相关的 URL-normalization 默认值。

## Case 417

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：找到分配给当前用户、主题为 `404 link` 的合并请求，并依据最后一条评论的作者回复。若最后评论来自合并请求作者，则回复 `"Thank you"`；否则以 `@user` 形式标记作者作提醒。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`，且两者分数必须都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。前者根据 `agent_response.json` 的 released parsing/normalization 检查显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；后者根据 `network.har` 先按 `POST` 和规范化路径筛选，并因 `last_event_only=true` 检查最后一个入选事件是否精确匹配 `__GITLAB__/a11yproject/a11yproject.com/notes?target_id=72560&target_type=merge_request`、`response_status=200`、`$.note.noteable_type=MergeRequest`，以及 `$.note.note` 匹配 `^.*@Roshanjossey.*$`。完整输入中的无事件、字段不匹配或 evaluator/orchestration error 导致非 `1.0`；只有 artifacts 的缺失、截断、损坏、不可读或 provenance 丢失使结果无法重建。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受成功的 `MUTATE` 最终响应，并由 `NetworkEventEvaluator` 接受最后一个匹配的 GitLab notes `POST`；决定性 artifacts 是 `agent_response.json` 和 `network.har`，两项得分均为 `1.0` 才成功。它把可读响应被拒绝或报错、以及完整 HAR 中缺少事件或所选事件不符合 URL、method、status 或 body 比较列为 failure，把任一 artifact 缺失、不可读或截断列为 undecided；但其网络描述只写成通用 GitLab notes URL，未保留决定性的 `a11yproject/a11yproject.com/notes` 路径，也未完整覆盖网络或编排错误。非空 stronger condition `verify_conditional_branch_context` 另要求保留的 GitLab 状态证明 target `72560` 确为分配给用户的 `404 link` 合并请求、`Roshanjossey` 是作者，且运行回复前的最后评论并非由其发表。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_exact_network_url`
- 为什么修改：网络条件标明了查询参数，但未标明已配置的项目特定 notes 路径。
- 应如何修改：陈述完整的规范化预期 URL：`__GITLAB__/a11yproject/a11yproject.com/notes?target_id=72560&target_type=merge_request`。

#### 修改项 2：native.checked_by 及 evaluator 组合规则

- Finding ID：`incomplete_error_composition`
- 为什么修改：该检查清单明确对 AgentResponseEvaluator 错误进行了分类，但未对导致任务得分非 1.0 的 NetworkEventEvaluator 错误或编排错误进行分类。
- 应如何修改：陈述：任一已配置 evaluator 或评估编排发生错误，并因此产生非 1.0 得分时，均属于原生失败。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`network_errors_missing_from_fail_if`
- 为什么修改：`fail_if` 涵盖网络事件缺失或不匹配，但遗漏了在保留输入完整时发生的 evaluator 错误。
- 应如何修改：添加一条失败规则，涵盖产生非 1.0 得分的任何 evaluator 或编排错误，同时仅在证据丢失时保留 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_fully_preserved`
- 为什么修改：精简后的检查清单丢失了项目特定 URL 路径以及完整的错误到失败判定规则。
- 应如何修改：保留这两项决定性语义，且不添加运行结果或无关细节。

## Case 422

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`，将当前用户的 GitLab 状态设置为 `Out of Office`。官方 instruction 为 `Set my gitlab status as Out of Office.`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`，仅当两项得分都为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。前者检查 `agent_response.json` 经 released parsing/normalization 后的显式字段 `task_type=MUTATE`、`status=SUCCESS` 和非 `RETRIEVE` 任务下归一化为 `null` 的 `retrieved_data`；materialized 默认值 `error_details` 不是 sparse config 显式配置的比较字段。后者在完整非静态事件中按 `PUT` 与路径筛选，因 `last_event_only=true` 取最后一个入选事件，再完整比较规范化 URL `__GITLAB__/api/v4/user/status`（默认不忽略 query 差异）、`response_status=200`，以及 post data 的 `availability=busy`、`clear_status_after=null`、`message="Out of Office."`。

### 原本 draft 是什么

原始 draft 声称两个 released checks 必须都得 `1.0`：最终响应须被接受，最后一个匹配的 `PUT /api/v4/user/status` 事件须为 HTTP `200`，且 payload 为 `availability=busy`、`clear_status_after=null`、`message="Out of Office."`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它将响应缺失、无效或不匹配，以及无匹配 PUT、最后事件非 `200` 或 post data 不符列为 failure；仅当 artifacts 未保留或无法归属于该运行时列为 undecided。该 draft 没有明确写出所选事件还须通过完整规范化 URL 比较及未忽略的 query 差异。非空 stronger condition `persisted_status_state` 另要求运行后 GitLab 当前用户状态记录显示 `message="Out of Office."`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_semantics_omitted`
- 为什么修改：网络描述止于选择与端点路径匹配的最后一个 PUT 事件，却未要求在完整对象比较期间，其规范化 URL 必须等于已配置的 URL。
- 应如何修改：区分方法/路径过滤与最终比较，并要求所选事件的规范化 URL（在已配置的不忽略任何内容的默认设置下包括其查询部分）与 `__GITLAB__/api/v4/user/status` 匹配。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_decision_rule_incomplete`
- 为什么修改：网络成功和失败规则遗漏了选择最后一个事件之后的规范化 URL/查询不匹配情况。
- 应如何修改：在 `success_if` 中添加完整规范化 URL 相等条件，并明确将所选事件的 URL 或未忽略查询部分不匹配计为失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_fully_preserved`
- 为什么修改：虽然检查清单简洁且不存在运行信息泄漏，但遗漏了一个影响得分的网络比较维度。
- 应如何修改：通过对网络 artifact 问题和决策规则进行精简补充，保留完整的规范化 URL 比较。

## Case 431

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `MUTATE`：比较当前打开的商品标签页，将单位价格最低的商品加入购物车。任务提供了三个 `__SHOPPING__` 商品起始 URL，但未要求输出比较过程。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`，两者分数均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。前者检查 `agent_response.json` 经 released extraction/normalization 后是否匹配显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；后者在 `should_not_exist=false`、`last_event_only=true` 下，以 `POST` 和去渲染后的 URL-path 正则 `^__SHOPPING__/checkout/cart/add/uenc/.*/product/32202$` 筛选事件并取最后一个，再检查 `response_status=200` 及 post data `item=32202`、`qty=1`。任一 evaluator 非 `1.0` 或报错、完整 trace 中无匹配事件或比较失败都会使组合分数不成功；证据缺失、截断或 integrity/provenance 不足才属于无法重建。

### 原本 draft 是什么

原始 draft 声称 `TaskEvalResult.score` 仅在两个 evaluator 均为 `1.0` 时为 `1.0`，决定性 artifacts 为 `agent_response.json` 与 `network.har`：前者须被接受为 `MUTATE/SUCCESS`，后者最后一个“target-URL” POST 须为状态 `200`、`item=32202`、`qty=1`。它将任一检查非 `1.0` 或报错、响应不被接受、无匹配 POST、所选 POST 的 item、数量或状态错误，以及完整 artifacts 上的 task-level evaluation error 列为 failure；artifact 缺失或仅保留局部摘录则为 undecided。该 draft 未写出完整 URL 正则，也未明确写出 `retrieved_data=null` 的归一化条件。非空 stronger condition `confirm_final_cart_state` 另要求运行结束的购物车 DOM 或 accessibility tree 显示商品 `32202`、数量 `1`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`under_specified_evaluator_predicates`
- 为什么修改：原生表述未说明已配置的确切购物车添加 URL 正则表达式，并遗漏了显式配置的 `retrieved_data:null` 响应字段及其非 RETRIEVE 规范化行为。
- 应如何修改：陈述响应必须通过已发布的解析/规范化，且满足 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`，不得将默认的 `error_details` 视为显式配置。陈述确切的 URL 正则表达式，并说明与该方法/路径候选项匹配的最后一个 POST 必须具有状态 200，且 `post_data` 中 `item=32202`、`qty=1`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`under_specified_success_rule`
- 为什么修改：`success_if` 依赖未定义的短语“目标 URL 的 POST”，且仅将响应标为 MUTATE/SUCCESS，因此无法独立区分所有通过和失败的完整 artifact。
- 应如何修改：使 `success_if` 枚举确切的规范化响应字段、确切的 URL 正则表达式、POST 方法、`last_event_only` 选择、响应状态以及必需的 post-data 值，同时保留合取式得分组合。

## Case 441

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：使用简单在线文件编辑器更新当前项目的网站代码，并提交到默认分支。目标是把浏览器标签页标题改为 `"GIVE ME SPACE"`，起始项目为 `__GITLAB__/byteblaze/gimmiethat.space`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`，且所有 evaluator 分数都必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。前者对完整的 `agent_response.json` 做 released parsing/normalization，比较 sparse config 显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；`error_details` 只是 materialized 默认值，并非显式比较字段。后者从 `network.har` 取最后一个匹配 `POST` 和 URL `__GITLAB__/byteblaze/gimmiethat.space/-/update/main/index.html` 的事件，要求 `response_status=302`，并检查 form data `_method=put`、`branch_name=main`、`original_branch=main`、`file_path=index.html`，以及 `content` 匹配 `^<\!doctype html>.*<head>.*<title>GIVE ME SPACE</title>.*</head>.*</html>$`。

### 原本 draft 是什么

原始 draft 声称只有 `AgentResponseEvaluator` 接受 mutation-success 最终响应且 `NetworkEventEvaluator` 接受配置的 GitLab 更新事件，两项均为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它将完整响应的无效、不匹配或 evaluator error，以及无合格 POST、最后匹配事件任一字段不符或网络 evaluator error 列为 failure；undecided 仅写成未保留 `agent_response.json` 或 `network.har` 且尚无证据证明失败。该 draft 未要求 artifacts 必须完整、未损坏且可归属于该运行，因此没有覆盖截断、损坏、不可读或 provenance 丢失。非空 stronger condition `repository_state_confirms_commit` 另要求运行后仓库快照证明 `main` 指向持久化 commit，且其中 `index.html` 的 head 含 `<title>GIVE ME SPACE</title>`。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`artifacts_must_be_complete_and_attributable`
- 为什么修改：决定性 artifact 问题提到了 `agent_response.json` 和 `network.har`，但未确定所保留文件是可归属于本 case 和本次运行的完整、完好 evaluator 输入。
- 应如何修改：将两个决定性 artifact 限定为 evaluator 输入的完整、完好且可归属于本次运行的副本；这对于根据 `network.har` 重建 `last_event_only` 尤其必要。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_must_cover_integrity_and_provenance_loss`
- 为什么修改：`undecided_if` 仅处理文件缺失，未区分完整但不符合 evaluator 要求的响应与因截断、损坏、不可读或来源信息丢失而变得无效的保留文件。
- 应如何修改：将 `undecided_if` 扩展到所有妨碍重建的保留、完整性和来源信息故障，同时在完整且可归属的证据表明响应无效、事件缺失、不匹配或 evaluator 错误时，仍判定为失败。

## Case 443

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：使用简单在线文件编辑器更新并提交当前项目的网站代码，将浏览器标签页标题改为 `"Not an interesting site"`。提交目标是“a new branch with no merged request”，即新分支且没有处于 merged 状态的请求。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`，仅当两项分数都为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。前者依据 `agent_response.json` 的 released parse、normalization 和 structural comparison 检查 `task_type=MUTATE`、`status=SUCCESS` 及 mutate task 的 `retrieved_data` 处理；后者从 `network.har` 取最后一个匹配 `POST` 与 URL `__GITLAB__/byteblaze/gimmiethat.space/-/update/main/index.html` 的事件，要求 `response_status=302`、`_method=put`、`original_branch=main`、`file_path=index.html`、`branch_name` 匹配 `^(?!main$).+$`，且 `content` 匹配 `^<\!doctype html>.*<head>.*<title>Not an interesting site</title>.*</head>.*</html>$`。提交给 evaluator 的输入缺失、畸形、无匹配事件、字段不符或 evaluator error 属于 failure；仅运行后保留证据丢失或截断且无官方结果可确定分数时为 undecided。

### 原本 draft 是什么

原始 draft 声称最终响应和最后一个匹配的 GitLab 更新事件都必须获 `1.0`，决定性 artifacts 是 `agent_response.json` 与 `network.har`；网络事件须满足 `302`、非 `main` 的 `branch_name`、`original_branch=main`、`file_path=index.html`、`_method=put` 和标题全文正则。它将提交的响应缺失、畸形、不匹配或报错，以及 trace 缺失、畸形、无匹配 POST 或最后事件任一条件不符列为 failure；运行后输入丢失或截断且无官方评分记录则为 undecided。该 draft 把官方的 `no merged request` 改写为更严格的 `no merge request`。其非空 stronger condition `durable_new_branch_without_merge_request` 同样要求创建此前不存在的非 `main` 分支、持久化包含 `<title>Not an interesting site</title>` 的 commit，并且该分支完全没有 merge request，因而也比 packet 的“没有 merged request”更严格。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`native_goal_merge_request_semantics`
- 为什么修改：原生目标将数据包中的“无已合并请求”替换为“无合并请求”，从而引入了更严格的要求。
- 应如何修改：保留官方表述，或将其操作化，但不得禁止未处于 merged 状态的合并请求。

#### 修改项 2：stronger.additional_conditions

- Finding ID：`stronger_merge_request_overreach`
- 为什么修改：更强条件要求不存在任何合并请求，而来源仅说明新分支“无已合并请求”。
- 应如何修改：将可衡量的更强条件限制为持久的分支和提交状态，以及不存在来自该分支且处于 merged 状态的合并请求。

## Case 449

### 原本 case 是什么

原始任务是在 `gitlab` 站点把用户 GitLab 个人资料的主页 URL 设置为 `helloworld.xyz`，task type 为 `MUTATE`。任务从 `__GITLAB__` 开始。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`：前者对 `agent_response.json` 进行已发布的字符串或 fenced-JSON 提取、字典式解析与稀疏字段归一化，要求 `task_type`（兼容旧字段 `performed_operation`）归一化为 `MUTATE`、`status` 为 `SUCCESS`，并按非 `RETRIEVE` 语义处理显式配置的 `retrieved_data:null`；缺少该键视为 null，其原始值不比较，物化默认值 `error_details` 也不比较。后者从 `network.har` 的非静态 evaluation events 中先按 `POST` 和归一化 URL 路径 `__GITLAB__/-/profile` 过滤，再因 `last_event_only=true` 只选择最后一个过滤结果且不回退，要求其 `response_status` 为 `302`，并按 `post_data_schema` 将 `user[website_url]` 作为字符串比较为 `https://helloworld.xyz` 或 `http://helloworld.xyz`；`should_not_exist=false`，无过滤结果即不通过。`WebArenaVerifiedEvaluator` 按上述顺序执行，只有两个 evaluator 分数都等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 最终响应，并由 `NetworkEventEvaluator` 接受最后一个符合条件的 GitLab 资料更新事件，两个分数均为 `1.0`；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 success 条件要求响应比较通过，且最后一个符合条件的 profile `POST` 含可接受的主页 URL 并返回 `302`；failure 包括任一 evaluator 非 `1.0` 或报错、响应不匹配、没有相应 POST，或最后相应 POST 的值或状态错误。它将证据缺失、不可读或截断而无法重建最终响应或事件时列为 `undecided`，完整证据中的不匹配则列为 failure。非空 stronger condition `verify_persisted_profile_homepage` 另要求 `Post-run GitLab profile/settings state snapshot` 显示实际存储值为 `http://helloworld.xyz` 或 `https://helloworld.xyz`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_and_last_event_semantics`
- 为什么修改：原生规则遗漏了影响得分的响应结构和稀疏字段语义，并对 NetworkEventEvaluator 的最后事件选择使用了含糊表述。
- 应如何修改：陈述已发布的解析必须生成类似 dict 的响应，该响应匹配显式配置的 `task_type`、`status` 以及非 RETRIEVE 的 `retrieved_data:null` 语义；排除仅为默认值的 `error_details`。还应陈述：首先按 POST 和规范化的 profile URL 路径过滤事件，选择最后一个匹配项，并仅对该所选事件进行完整比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`operational_decision_rules`
- 为什么修改：当前成功和失败规则无法独立确定响应和所选网络事件是否满足已发布的比较要求。
- 应如何修改：将通用响应谓词和“最后一个符合条件的”表述替换为明确的响应规范化、最后事件选择、所选事件比较、无匹配项失败、无效响应失败以及 evaluator 错误失败规则。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`preserve_decisive_semantics`
- 为什么修改：简洁性是通过省略决定性的稀疏字段和事件选择行为实现的。
- 应如何修改：保留精简结构，同时添加缺失的响应语义以及“先过滤、再选择最后一个”的语义；不得添加运行结果或无关的 evaluator 细节。

## Case 456

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点因质量问题禁用 `Cora Pant`，task type 为 `MUTATE`。任务从 `__SHOPPING_ADMIN__` 开始。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`：前者检查 `agent_response.json`，要求经已发布的解析和 expected-field 归一化后，`task_type`（或 `performed_operation`）为 `MUTATE`、`status` 为 `SUCCESS`，非 `RETRIEVE` 的 `retrieved_data` 归一化为 null；稀疏配置未显式设置的 `error_details` 不参与比较。后者检查 `network.har`，先按 `POST` 和锚定 URL 正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/1840/type/(simple|configurable)/store/0/set/\d+/back/edit$` 过滤，再以 `last_event_only=true` 选择最后一个匹配事件，要求解析后的 `product[status]` 为字符串 `2` 且 `response_status` 为 `302`；`should_not_exist=false`，完整轨迹中无匹配事件即不通过。只有两个 evaluator 分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 最终响应，并由 `NetworkEventEvaluator` 接受最后一个匹配的 Cora Pant 保存 POST，其中 `product[status]=2` 且响应为 `302`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 规则还宣称 `error_details` 必须缺失，failure 规则把提供 `error_details` 本身列为失败情形，并同时涵盖响应无法解析或字段不符、无匹配 POST，以及最后匹配 POST 的状态或 `product[status]` 错误。它仅在无法确定两个运行时 artifact 且没有官方组件结果补足时判为 `undecided`，已证实缺失、畸形或 evaluator 报错则判为 failure。非空 stronger condition `verify_persisted_disabled_state` 另要求 `Post-run shopping-admin product-detail capture or product-state export` 证明 `Cora Pant`（catalog product `1840`）实际处于 disabled 状态。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unconfigured_error_details_requirement`
- 为什么修改：检查清单称必须省略 `error_details`，但 `error_details` 不在稀疏预期配置中，因此不属于从实际响应中规范化以供比较的字段。
- 应如何修改：从原生成功条件和 artifact 问题中移除省略 `error_details` 的要求，并陈述这个未配置的默认字段不影响得分。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_error_details_failure_rule`
- 为什么修改：`fail_if` 规则错误地将提供 `error_details` 归类为 AgentResponseEvaluator 失败。
- 应如何修改：将 AgentResponseEvaluator 失败限制为无效/非结构化响应、`task_type` 或 `status` 不匹配以及真正的 evaluator 错误；明确避免仅因存在 `error_details` 而判定失败。

## Case 457

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点因质量问题禁用 `Karmen yoga pants`，task type 为 `MUTATE`。任务从 `__SHOPPING_ADMIN__` 开始。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`：前者检查 `agent_response.json`，经已发布的解析和归一化后要求显式配置的 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data:null`；这是非 `RETRIEVE` 任务，缺少或提供的 `retrieved_data` 均归一化为 null，而物化默认值 `error_details` 不比较。后者在 `network.har` 中按 `POST` 和锚定正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/1819/type/(simple|configurable)/store/0/set/\d+/back/edit$` 过滤 evaluation events，以 `last_event_only=true` 选取最后一个匹配事件，并要求 `product[status]` 的字符串值为 `2`、`response_status` 为 `302`；`should_not_exist=false`，且没有 header、query、response-content、cookie、schema、ignored-parameter 或 base64 约束。只有两个 evaluator 分数都为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 最终响应，并由 `NetworkEventEvaluator` 接受最后一个匹配 product `1819` 保存 URL 的 POST；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 条件要求最后匹配事件含 `product[status]=2` 并返回 `302`，failure 包括任一 evaluator 非 `1.0` 或报错、响应未被接受、无配置 URL 匹配，或最后匹配事件的字段或状态错误。它在没有证据已证明失败、但 artifact 不可用或不可读时判为 `undecided`，没有覆盖可读但截断、损坏或来源不明的证据。非空 stronger condition `verify_final_product_state` 另要求 `End-of-run shopping-admin product-record snapshot or export` 证明 `Karmen yoga pants` 为 product `1819` 且状态为 `Disabled`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_retrieved_data_semantics_omitted`
- 为什么修改：AgentResponseEvaluator 被描述为仅接受 MUTATE/SUCCESS，尽管稀疏任务中显式配置了 `retrieved_data:null`。
- 应如何修改：陈述对 `task_type`、`status` 和 `retrieved_data` 应用已发布的解析与规范化；对于该非 RETRIEVE 任务，缺失或已提供的 `retrieved_data` 均规范化为 null。不得将 `error_details` 添加为比较字段，因为它仅是一个具体化的默认值。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`artifact_completeness_not_required`
- 为什么修改：仅提及 `agent_response.json` 和 `network.har` 并不充分，因为这些问题未确定响应和按时间顺序排列的跟踪记录完整、完好且归属于该 case。
- 应如何修改：将两个 artifact 均限定为完整、完好且可归属于 case 457，并要求 `network.har` 保留 `last_event_only` 所需的完整事件顺序。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_trace_can_be_misclassified`
- 为什么修改：检查清单在未要求跟踪记录完整的情况下，将不存在匹配 POST 声明为失败，并将 undecided 限制为文件不可用或不可读。
- 应如何修改：使无匹配项和最后事件不匹配的失败判定以证据完整、完好且可归属为前提；将 undecided 扩展到运行后截断、损坏、完整性丢失或来源信息丢失的情况，除非另一个完整 artifact 已经证明原生失败。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decision_clauses_not_internally_coherent`
- 为什么修改：虽然内容简洁且不包含运行结果，但失败和 undecided 条款无法一致地对可读但不完整或不可归属的 HAR 进行分类。
- 应如何修改：在决定性 artifact、成功、失败和 undecided 规则中一致使用同一个证据完整性前提，同时保留当前的精简结构。

## Case 459

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点把当前页面中产品的价格降低 `10%`，task type 为 `MUTATE`。起始 URL 是 `__SHOPPING_ADMIN__/catalog/product/edit/id/237/`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`：前者对 `agent_response.json` 执行已发布的代码块/JSON 解析和稀疏字段归一化，要求 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data:null`；非 `RETRIEVE` 语义会把缺少或提供的 `retrieved_data` 归一化为 null，稀疏配置中不存在的 `error_details` 不比较。后者从 `network.har` 的非静态 evaluation events 中按 `POST` 和归一化 URL 正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/237/type/(simple|configurable)/store/0/set/\d+/back/edit$` 过滤，以 `last_event_only=true` 选择最后一个匹配事件，要求 `product[price]` 为字符串 `62.10`、`response_status` 为 `302`；`should_not_exist=false`，且未配置 header、cookie、response-content、schema、ignored-parameter 或 base64 解码约束。只有两个 evaluator 分数都等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 最终响应，并由 `NetworkEventEvaluator` 接受最后一个 eligible product-save POST；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 条件要求最后匹配 product `237` 保存 URL 的 POST 含 `product[price]=62.10` 并返回 `302`，failure 包括响应不匹配或 evaluator 报错、无 eligible POST，或最后事件的 URL、价格、方法或状态不符，但 draft 仅以非精确的 “product-237 save URL” 指代配置正则。它只在 artifact 未保留或发生阻止重建检查的运行后保留损失时判为 `undecided`，evaluator 实际收到并拒绝的输入则判为 failure。非空 stronger condition `confirm_persisted_price` 另要求 `Post-run backend product record or freshly reloaded product-237 edit-page capture` 通过新读取证明 product `237` 的持久化价格为 `62.10`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`underspecified_native_predicates`
- 为什么修改：响应检查遗漏了显式配置的 `retrieved_data:null`，网络检查则用含糊的短语“product-237 保存 URL”替换了确切的 URL 正则表达式。
- 应如何修改：陈述在已发布的非 RETRIEVE 规范化下，稀疏响应字段为 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`，而 `error_details` 不计分，因为它未被显式配置。为网络检查加入确切的 URL 正则表达式和 `last_event_only` 行为。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`insufficient_success_and_failure_rules`
- 为什么修改：决策规则无法区分已配置的保存 URL 与其他 product-237 保存端点，也未完整描述响应投影。
- 应如何修改：使用确切的已配置 URL 谓词和明确的稀疏响应比较来重写 `success_if` 和 `fail_if`，同时保留对无匹配项、不匹配和 evaluator 错误的失败判定，并仅为证据丢失保留 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`lossy_compression`
- 为什么修改：草稿很简洁，但移除了 URL 正则表达式和已配置响应字段中影响得分的区别。
- 应如何修改：以精简形式保留这些决定性细节，不得添加运行结果或无关的 evaluator 行为。

## Case 463

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点把当前页面中产品的价格提高 `15%`，task type 为 `MUTATE`。起始 URL 是 `__SHOPPING_ADMIN__/catalog/product/edit/id/996/`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`：前者检查 `agent_response.json`，按已发布的解析、归一化和结构比较要求显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data:null`；`error_details` 只是物化默认值而不参与比较，且非 `RETRIEVE` 任务会把 `retrieved_data` 归一化为 null。后者检查 `network.har`，先按 `POST` 和精确锚定正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/996/type/(simple|configurable)/store/0/set/\d+/back/edit$` 过滤 evaluation events，再以 `last_event_only=true` 选择最后一个匹配事件，要求 `product[price]` 为字符串 `36.80`、`response_status` 为 `302`；`should_not_exist=false`，无匹配事件即不通过。`TaskEvalResult.create` 进行合取组合，只有两个 evaluator 分数均为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 即 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator` 和 `NetworkEventEvaluator` 都得 `1.0`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 条件要求响应通过 `MUTATE/SUCCESS` 比较，且最后一个匹配 product `996` 保存 URL 的 POST 含 `product[price] = 36.80` 并返回 `302`；failure 包括任一 evaluator 失败或报错、响应不符、缺少保存 POST，或最后 URL 匹配事件的方法、URL、价格或状态不符，但 draft 没有写出完整 URL 正则。它只在实际 evaluator 输入因未保留或运行后截断而未知时判为 `undecided`，已保留但畸形或不匹配的输入则判为 failure。非空 stronger condition `persisted_product_price` 另要求 `Authoritative post-run product-state snapshot` 证明 product `996` 的权威运行后价格为 `36.80`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_url_predicate_omitted`
- 为什么修改：未陈述已配置且带锚点的网络 URL 正则表达式；“product-996 保存 URL”无法唯一标识已发布的谓词。
- 应如何修改：陈述 URL 比较使用确切的已配置正则表达式 `^__SHOPPING_ADMIN__/catalog/product/save/id/996/type/(simple|configurable)/store/0/set/\d+/back/edit$`，并同时要求 POST、`last_event_only=true`、`product[price]="36.80"` 以及响应状态 302。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_decision_rule_underspecified`
- 为什么修改：原生成功和失败规则可能被应用于仅类似 product-996 保存请求、但不匹配已配置锚定路由的事件。
- 应如何修改：要求成功条件为：按 POST 和确切的已配置 URL 正则表达式过滤后所得的最后一个事件满足价格和状态检查；若不存在此类过滤后事件，或所选最后事件存在不匹配，则判定为失败。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`overcompressed_decisive_semantics`
- 为什么修改：检查清单很简洁，但丢失了确切且影响得分的 URL 条件。
- 应如何修改：在精简的 artifact 问题和决策规则中保留确切的 URL 正则表达式，不得添加无关细节或运行结果。

## Case 467

### 原本 case 是什么

原始任务是在 `shopping` 站点把商品 “HONGJ Hawaiian Beach Outfits Set for Mens, Summer Tropical Tree Printed Relaxed-fit Hawaii Shirts Shorts 2 Piece Suits” 加入用户愿望清单，task type 为 `MUTATE`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json`，按发布版解析、归一化和结构比较核对显式配置的 `task_type=MUTATE`、`status=SUCCESS` 和非 `RETRIEVE` 任务下的 `retrieved_data=null`。`NetworkEventEvaluator` 检查 `network.har`：按归一化的 `__SHOPPING__/wishlist/index/add/` URL 路径和 `POST` 方法筛选事件，并因 `last_event_only=true` 选择最后一个候选，再比较完整归一化 URL、方法、`response_status=302` 及归一化后的 `post_data` 中 `product=85498`、`qty=null`；配置还包括 `decode_base64_query=false`、无 query/post-data 忽略规则和 `should_not_exist=false`。`TaskEvalResult.score` 仅在两个 evaluator 的分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 最终响应，且 `NetworkEventEvaluator` 接受最后一个符合条件的愿望清单添加 `POST`：`product=85498`、`qty=null`、状态码 `302`；它没有在响应说明中明确写出已配置的 `retrieved_data:null`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并称两项均通过时成功，任一响应解析/结构不匹配、缺少合格事件、最后事件不匹配或 evaluator error 时失败。它将 undecided 限定为 artifact 缺失、可证明截断或留存损坏而无法重建 evaluator 输入，并明确完整 HAR 中没有被接受事件属于失败。非空 stronger condition `confirm_post_run_wishlist_state` 另要求 “Post-run shopping wish-list state snapshot” 显示该 HONGJ 商品当前确实在愿望清单中。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_explicit_retrieved_data_expectation`
- 为什么修改：尽管在稀疏的原始任务中明确配置了 `retrieved_data: null`，但 AgentResponseEvaluator 的描述仅提及 MUTATE 和 SUCCESS。
- 应如何修改：在 benchmark_success 以及响应证据/成功规则中说明：对于此非 RETRIEVE 任务，发布版 parser 和 normalization 针对 `task_type` 为 MUTATE、`status` 为 SUCCESS 且 `retrieved_data` 为 null 的配置执行。不要将 `error_details` 添加为预期字段，也不要要求原始 `retrieved_data` 值本身为 null。

## Case 478

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建一个名为 `webagent` 的全新空仓库，task type 为 `MUTATE`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json`，按发布版解析和归一化比较显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；物化出的 `error_details:null` 不是稀疏原始配置中显式要求比较的字段。`NetworkEventEvaluator` 检查 `network.har`：先按 `POST` 和归一化 `/projects` 路径筛选，并以 `last_event_only=true` 选择最后一个候选，再要求完整归一化 URL 为 `__GITLAB__/projects`、状态码为 `302`，且提取和归一化后的表单值为 `project[name]=webagent`、`project[path]=webagent`、`project[namespace_id]=2505`、`project[initialize_with_readme]=0`；query 无忽略项且 `decode_base64_query=false`，`should_not_exist=false`。`TaskEvalResult.score` 仅在两个 evaluator 分数都为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native success 为 `TaskEvalResult.score = 1.0`，要求响应归一化为 `MUTATE`、`SUCCESS`、evaluator-visible `retrieved_data` null，并要求最后一个匹配 `POST /projects` 的事件含四个指定项目表单值且状态码为 `302`。它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts，但把网络 URL 语义表述为方法/路径 `POST /projects`，没有写出随后对完整归一化 URL `__GITLAB__/projects` 的比较及 query 配置。它称两个 artifact 均通过则成功；响应失败或报错、无匹配事件、最后候选的表单值或状态不符时失败，任一 evaluator 非 `1.0` 时 task score 为 `0.0`。undecided 仅用于 artifact 缺失、不可读或截断导致无法重建比较；非空 stronger condition `persisted_empty_repository` 另要求 “post-run GitLab project/API state snapshot” 证明 namespace `2505` 中存在本次创建的 `webagent`，且无 commits、branches 或 files。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`full_normalized_network_url_omitted`
- 为什么修改：网络成功描述和 artifact 问题仅规定 `POST /projects` 的归一化 method/path 匹配，随后进行表单和状态检查。候选项选择基于 path，但随后会将选定事件作为完整的归一化对象进行比较，其 URL 必须与配置的 `__GITLAB__/projects` 匹配。当前措辞可能会接受 path 相同但归一化 host 或 query 不匹配的事件。
- 应如何修改：说明在选择最后一个与归一化 `/projects` path 匹配的 POST 事件后，在所配置的 query 行为（`decode_base64_query=false` 且没有被忽略的 query 参数）下，其完整归一化 URL 必须等于配置的 `__GITLAB__/projects`。将完整 URL 不匹配纳入网络 failure。

## Case 488

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点把 CMS 页面 “Home Page” 的页面标题改为精确字符串 “This is the home page!! Leave here!!”，task type 为 `MUTATE`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json`，按发布版解析、归一化和结构比较核对 `task_type=MUTATE`、`status=SUCCESS`；配置的 `retrieved_data:null` 在此非 `RETRIEVE` 任务中归一化为 null。`NetworkEventEvaluator` 检查 `network.har`：按配置的 shopping-admin URL 路径和 `POST` 筛选，并因 `last_event_only=true` 选择最后一个候选，再比较完整归一化 URL `__SHOPPING_ADMIN__/cms/page/save/back/edit`、方法、`response_status=302` 及 `is_active="1"`、`page_id="2"`、`store_id[0]="0"`、`title="This is the home page!! Leave here!!"`；URL 采用 `decode_base64_query=false`、无 query 忽略项或 schema 的默认配置，且 `should_not_exist=false`。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 只有在 `AgentResponseEvaluator` 接受最终响应且 `NetworkEventEvaluator` 接受所选网络事件、两者均得 `1.0` 时才为 `1.0`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，要求响应匹配 `MUTATE/SUCCESS`，最后一个匹配 CMS 保存端点的 `POST` 具有状态码 `302` 和四个指定 post fields；其表述没有保留对完整归一化配置 URL 及 query 的比较语义。它称两项都通过即成功；响应无效、归一化或比较不匹配、没有合格 POST、最后候选在 endpoint、method、status 或任一 post field 上不符，或 evaluator error 时失败。它把 artifact 未留存且没有现有证据证明失败列为 undecided；非空 stronger condition `persisted_page_title` 另要求 “Post-run shopping-admin CMS page-state capture” 经 fresh read 或 reload 显示目标记录的标题已精确持久化。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_url_semantics_omitted`
- 为什么修改：网络规则仅描述 shopping-admin endpoint/path，未要求选定事件通过发布版针对完整配置 URL 的归一化比较。
- 应如何修改：说明最后一个 path 和 method 候选事件除了匹配 status 和 post data 外，还必须使用 `decode_base64_query=false`、不忽略任何 query 参数且不使用 schema，通过发布版 normalization 以及与预期 URL `__SHOPPING_ADMIN__/cms/page/save/back/edit` 的比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_failure_rules_incomplete`
- 为什么修改：`success_if` 和 `fail_if` 未涵盖这种情况：选定事件与 URL path、method、status 和 post 字段匹配，但未通过 evaluator 的归一化完整 URL/query 比较。
- 应如何修改：在 `success_if` 中加入“通过归一化配置 URL 比较”这一条件，并将未通过该比较视为普通的原生 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantic_omission`
- 为什么修改：尽管 checklist 简洁且没有 run 泄漏，但它遗漏了 NetworkEventEvaluator 比较中与得分相关的部分。
- 应如何修改：保持简洁，同时将配置的归一化 URL/query 语义添加到原生 artifact 问题和 decision rules 中。

## Case 489

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点把 CMS 页面 “Privacy Policy” 的标题改为精确字符串 “No privacy policy is needed in this dystopian world”，task type 为 `MUTATE`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json`，按发布版解析和归一化核对结构化响应的 `task_type=MUTATE`、`status=SUCCESS` 和显式配置的 `retrieved_data=null`；非 `RETRIEVE` 的 `MUTATE` 任务会把该字段归一化为 null。`NetworkEventEvaluator` 检查 `network.har`：按 `POST` 和配置的 `__SHOPPING_ADMIN__/cms/page/save/back/edit` URL 路径过滤，并以 `last_event_only=true` 选择最后一个候选，再比较其完整归一化 URL、方法、`response_status=302` 以及 `title="No privacy policy is needed in this dystopian world"`、`page_id="4"`、`is_active="1"`、`store_id[0]="0"`；query 配置无忽略项、`decode_base64_query=false`，且 `should_not_exist=false`。`TaskEvalResult.score` 仅当两个 evaluator 分数都为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 只有在 `AgentResponseEvaluator` 按解析、归一化和结构比较接受 `MUTATE/SUCCESS`，且 `NetworkEventEvaluator` 接受最后一个路径匹配的保存 `POST`、状态码 `302` 和四个 post-data 值时才为 `1.0`。它以 `agent_response.json` 和 `network.har` 为决定性 artifacts，但没有写出显式配置的 `retrieved_data:null`，也没有说明路径筛选后还要比较完整归一化 URL 及其 query。它称两项均通过时成功；响应失败或报错、无匹配候选、最后候选任一比较字段不符或 evaluator error 时失败，并称任何此类情况都会使 `TaskEvalResult.score` 为 `0.0`。undecided 仅限 artifact 不可用或不完整而无法重建检查；非空 stronger condition `persisted_page_title` 另要求 “Post-run shopping_admin CMS page record or reloaded page-detail capture” 显示 `page_id 4` 已持久化为指定标题。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_retrieved_data_semantics_omitted`
- 为什么修改：响应规则仅描述 MUTATE/SUCCESS，未说明在稀疏任务中明确配置了 `retrieved_data:null`，也未说明发布版非 RETRIEVE normalization 会在结构比较之前将实际的 `retrieved_data` 字段映射为 null。
- 应如何修改：说明三个明确配置的响应字段——`task_type` 为 MUTATE、`status` 为 SUCCESS、`retrieved_data` 为 null——并简要解释此 MUTATE case 会将 `retrieved_data` 归一化为 null；不要将 `error_details` 添加为配置的比较字段。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_comparison_omitted`
- 为什么修改：网络规则仅将配置的 URL 视为 path 选择条件。在按 POST/path 筛选并选择最后一个事件后，evaluator 会对选定事件的完整 URL 进行归一化和结构比较，query 行为由所配置的不忽略参数、无 schema 和不进行 base64 解码的默认设置控制。
- 应如何修改：区分基于 path 的候选项筛选与随后进行的完整归一化 URL 比较，并在 benchmark_success 和网络 artifact 问题中纳入该比较。

## Case 499

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点用 USPS tracking number `13849373987` 更新订单 `#304`，task type 为 `MUTATE`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json`，按发布版提取、解析、归一化和比较核对显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；该非 `RETRIEVE` 任务会把 `retrieved_data` 归一化为 null，而物化默认值 `error_details:null` 不属于显式比较字段。`NetworkEventEvaluator` 检查 `network.har`：按 `POST` 和归一化的 `__SHOPPING_ADMIN__/admin/order_shipment/save/order_id/304/` 路径筛选，以 `last_event_only=true` 选择最后一个候选，再比较配置 URL、方法、`tracking[1][carrier_code]="usps"`、`tracking[1][number]="13849373987"` 和 `response_status=302`；配置为 `decode_base64_query=false`、无 query/post-data 忽略规则且 `should_not_exist=false`。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 只有在 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 响应，且 `NetworkEventEvaluator` 接受订单 `304` 的最后一个匹配 shipment-save `POST`、两个 tracking 字段和状态码 `302` 时才为 `1.0`；它没有写出显式配置的 `retrieved_data:null`。它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并称两项都通过即成功；响应不匹配或 evaluator error、无合格网络事件、最后事件不匹配或网络 evaluator error 时失败，任一项都会使 `TaskEvalResult.score` 为 `0`。它把 artifact 缺失、截断或“uninterpretable”到无法重建检查列为 undecided，但没有明确把该词限定为留存、完整性或 provenance 损失。非空 stronger condition `persisted_order_tracking` 另要求 “Post-run order #304 detail-state capture or state export” 证明订单已实际保存 carrier `USPS` 和 tracking number `13849373987`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing-explicit-response-field`
- 为什么修改：原生响应描述将配置的比较简化为 MUTATE/SUCCESS，并遗漏了明确配置的 `retrieved_data:null`。
- 应如何修改：说明发布版响应 parsing/normalization 会比较 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`；明确非 RETRIEVE normalization 会将 `retrieved_data` 映射为 null，且不会比较采用默认值的 `error_details`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete-and-ambiguous-decision-rules`
- 为什么修改：`success_if` 遗漏了 `retrieved_data:null`，而 `undecided_if` 未明确区分留存损坏与完整但 evaluator-invalid 的输入。
- 应如何修改：在 `success_if` 中涵盖所有三个明确配置的响应字段，并将 undecided 限定为留存、完整性或来源丢失；将完整但无效/null 的响应、缺少网络匹配项、不匹配以及 evaluator 错误归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native-semantic-omission`
- 为什么修改：这份 checklist 虽然简洁，但其可操作的原生语义遗漏了一个配置的响应字段。
- 应如何修改：添加 `retrieved_data:null` 及其非 RETRIEVE normalization 行为，不要添加无关的原始输入特性或 run 信息。

## Case 500

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点更新订单 `#301`，将 DHL 追踪号设为 `239028439840`。任务类型为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`：前者检查响应经解析和非 `RETRIEVE` 归一化后是否满足 `task_type="MUTATE"`、`status="SUCCESS"`、`retrieved_data=null`；后者要求 `should_not_exist=false`，按 `POST` 和 URL `__SHOPPING_ADMIN__/admin/order_shipment/save/order_id/301/` 筛选，并因 `last_event_only=true` 检查最后一个匹配事件。该事件还须满足 `response_status=302`，以及 `post_data` 中 `tracking[1][carrier_code]="dhl"`、`tracking[1][number]="239028439840"`；其余可选约束未启用。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`，即 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 响应，且 `NetworkEventEvaluator` 接受订单 `301` 的最后一个匹配 `POST`，其 URL、`302`、`dhl` 和 `239028439840` 均符合配置。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 `success_if` 要求两项 evaluator 都得 `1.0`，`fail_if` 将响应不被接受、网络事件缺失或字段不符以及 evaluator failure/error 判为失败。其 `undecided_if` 将任一 artifact 缺失、不可读或截断而无法重建两项结果的情况列为未决；原文未排除另一份完整 artifact 已能证明失败的情形。非空 stronger condition `post_run_state_confirms_tracking` 进一步要求“Post-run shopping-admin order #301 detail snapshot or state export”显示订单 `#301` 的 carrier 为 DHL、追踪号为 `239028439840`。

### 需要修改的部分

#### 修改项 1：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_overrides_decisive_failure`
- 为什么修改：undecided 条款将 artifact 留存不完整视为会阻止作出全满足决定，却未排除完整 artifact 已经确定某项必要 evaluator failure 的情况。
- 应如何修改：将 undecided 限定为妨碍确定 success 或任何决定性 failure 的留存、完整性或来源丢失；说明即使另一个 artifact 不可用，根据完整证据确定的非 `1.0` 结果仍为 failure。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`overlapping_failure_and_undecided_rules`
- 为什么修改：当前规则可能同时将同一证据集归类为 failure 和 undecided——例如，一份完整但无效的 agent response 与缺失的网络 HAR 同时存在。
- 应如何修改：明确规定任何 evaluator 可见的非 `1.0` 结果具有优先级，并将 undecided 保留给不存在任何已能证明 failure 的完整证据时发生的证据丢失。

## Case 506

### 原本 case 是什么

原始任务是在 `shopping` 站点购买肉类替代品（`meat substitute`）类别中评分最高且价格在 `$100` 至 `$200` 之间的产品；如果购物车非空，须先丢弃其中商品。任务类型为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和四个 `NetworkEventEvaluator`；响应 evaluator 检查经解析和非 `RETRIEVE` 归一化后的 `task_type="MUTATE"`、`status="SUCCESS"`、`retrieved_data=null`，其中 `performed_operation` 可作为 `task_type` 的旧别名，稀疏配置未显式要求比较 `error_details`。四个网络 evaluator 均为 `should_not_exist=false`、`last_event_only=true`：先按配置的 HTTP 方法和归一化 URL 筛选，再对最后一个匹配事件检查所有启用字段。它们依次要求：(1) `POST` 到 `^__SHOPPING__/checkout/cart/add/uenc/.*/product/22490$`，启用 `decode_base64_query=true`，`post_data.product="22490"` 且 `response_status=200`；(2) `GET __SHOPPING__/rest/default/V1/carts/mine/totals`，忽略名称匹配 `\_` 的查询参数，状态 `200`，并要求 `response_content` 中 `$.items[0].name="Beyond Meat Beef Beefy Crumble, 5 Pound -- 2 per case."`、`items_qty=1`；(3) `POST __SHOPPING__/rest/default/V1/carts/mine/payment-information`，状态 `200` 且 `$.billingAddress.customerId="27"`；(4) `GET __SHOPPING__/checkout/onepage/success`，状态 `200`。四项之间不要求跨 evaluator 的事件顺序；只有全部五个 evaluator 分数均为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求全部五项检查得 `1.0`：响应满足 `MUTATE/SUCCESS`，并通过商品 `22490` 加购、仅含指定商品的一件购物车、customer `27` 的支付信息和结账成功四项最后匹配事件检查，且所查响应状态均为 `200`。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts。其 `success_if` 要求响应 evaluator 和四个网络 evaluator 全部得 `1.0`；`fail_if` 将可评估响应不匹配、任一网络检查缺失或字段不符以及 evaluator error 判为失败。其 `undecided_if` 将 artifact 缺失或截断、导致无法重建并重放全部五项输入的情况列为未决。非空 stronger condition `durable_order_and_catalog_constraints` 另要求 post-run order record 显示一个只含 product `22490`、价格在 `$100` 至 `$200` 的完成订单，且 contemporaneous catalog snapshot 证明它属于 `meat substitute` 并在合格商品中评分最高。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete_active_evaluator_semantics`
- 为什么修改：checklist 将响应检查简化为 MUTATE/SUCCESS，并将网络检查简化为 endpoint/body 摘要，遗漏了可能改变官方得分的实际 parsing 和 URL normalization 行为。
- 应如何修改：说明稀疏响应预期由 `task_type`、`status` 和 `retrieved_data` 构成；解释非 RETRIEVE 的 `retrieved_data` normalization，并说明不比较 `error_details`；还要纳入 eval[1] 的 `decode_base64_query=true`、eval[2] 被忽略的下划线 query-name pattern，以及全部四个网络 evaluator 选择最后一个经 method/URL 筛选的事件这一语义。

## Case 507

### 原本 case 是什么

原始任务是在 `shopping` 站点购买 `Ceiling light` 类别中评分最高且预算高于 `1000` 的产品；若购物车非空，须丢弃原有商品。任务类型为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和四个 `NetworkEventEvaluator`；前者检查响应经解析和非 `RETRIEVE` 归一化后满足 `task_type="MUTATE"`、`status="SUCCESS"`、`retrieved_data=null`，`performed_operation` 可作为旧别名，稀疏配置未显式比较 `error_details`。四个网络检查均使用 `should_not_exist=false`、`last_event_only=true`，即按方法及归一化 URL 过滤后检查最后一个匹配事件。它们要求：(1) 启用 `decode_base64_query=true` 的 `POST ^__SHOPPING__/checkout/cart/add/uenc/.*/product/71506$`，状态 `200` 且 `post_data.product="71506"`；(2) `GET __SHOPPING__/rest/default/V1/carts/mine/totals`，忽略名称匹配 `\_` 的查询参数，状态 `200`、`items_qty=1`，且 `$.items[0].name` 精确为 `40''X138" Hight Ceiling Chandelier Crystal Raindrop Chandeliers Staircase Large Chandelier Villa Entrance Foyer Pendant Light Grand Light Foyer High Ceiling Fixture 15 GU10 Bulb Include Remote Dimming`；(3) `POST __SHOPPING__/rest/default/V1/carts/mine/payment-information`，状态 `200` 且 `$.billingAddress.customerId="27"`；(4) `GET __SHOPPING__/checkout/onepage/success`，状态 `200`。只有五个 evaluator 的分数全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`；任一非 `1.0` 或 evaluation error 都使任务得 `0.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为五个 evaluator 全部得 `1.0`：响应被接受为 `MUTATE/SUCCESS`，并通过 product `71506` 加购、指定名称的一件购物车 totals、customer `27` 的 payment-information 和 checkout-success 四项最后事件检查。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并在 `success_if` 中逐项写出四个 URL/方法、`200`、请求字段及商品名称要求。其 `fail_if` 将响应缺失、无效或结构不符，以及任一网络事件缺失、字段不符或 evaluator error 判为失败。其 `undecided_if` 将 artifact 未保留、不可读或截断而无法重建输入的情况列为未决，同时说明完整但为空或不匹配的输入属于失败。非空 stronger condition `completed_order_contents` 进一步要求 `network.har (including checkout and order response bodies)` 能把完成的 checkout 关联到一个仅含一件 product `71506`、无其他 line item 的订单。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_network_url_controls`
- 为什么修改：原生描述遗漏了 eval[1] 的 `decode_base64_query=true` 和 eval[2] 的 `ignored_query_params_patterns=["\\_"]`，尽管两者都会参与 URL normalization 并可能影响事件匹配。
- 应如何修改：将这些控制项添加到相应的原生 artifact 问题和 success/failure 语义中：对 add-to-cart URL 应用 base64 query 解码，并忽略 totals-event 中名称与配置的 `\_` regex 匹配的 query 参数。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rules`
- 为什么修改：遵循 `success_if` 的审查者无法复现两个网络 evaluator 的发布版 URL 比较，因为其中没有说明配置的 base64 和忽略 query 行为。
- 应如何修改：使 add-to-cart 和 cart-totals 的 success 条件明确纳入各自的 URL normalization 设置，并使 `fail_if` 涵盖应用这些设置后得到的非 `1.0` 结果。

## Case 508

### 原本 case 是什么

原始任务是在 `shopping` 站点购买 `NS switch` 类别中评分最高且价格低于 `60` 的产品；如果购物车非空，须先清空原有商品。任务类型为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和四个 `NetworkEventEvaluator`；响应检查要求经解析和非 `RETRIEVE` 归一化后为 `task_type="MUTATE"`、`status="SUCCESS"`、`retrieved_data=null`，`performed_operation` 可作为旧别名，`error_details` 不是稀疏配置显式比较字段。四个网络 evaluator 均为正向存在检查（`should_not_exist=false`），并以 `last_event_only=true` 检查方法和归一化 URL 所筛出的最后一个事件。四项分别要求：(1) `POST ^__SHOPPING__/checkout/cart/add/uenc/.*/product/40448$`，启用 `decode_base64_query=true`，状态 `200` 且 `post_data.product="40448"`；(2) `GET __SHOPPING__/rest/default/V1/carts/mine/totals`，忽略名称匹配 `\_` 的查询参数，状态 `200`、`items_qty=1`，且 `$.items[0].name="Multi Pouch The Legend of Zelda Breath of the Wild for Nintendo Switch"`；(3) `POST __SHOPPING__/rest/default/V1/carts/mine/payment-information`，状态 `200` 且 `$.billingAddress.customerId="27"`；(4) `GET __SHOPPING__/checkout/onepage/success`，状态 `200`。`TaskEvalResult` 对五项分数取全合取，只有它们全部为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 仅在五项 evaluator 全得 `1.0` 时成立：响应匹配 `MUTATE/SUCCESS`，且 HAR 通过 product `40448` 加购、含指定名称的一件购物车、customer `27` 支付信息和 checkout success page 四项检查。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并列出了四项网络检查的 URL、方法、状态、`post_data` 或 `response_content` 值。其 `success_if` 要求响应与四项网络检查全部得 `1.0`；`fail_if` 将响应缺失、无效或不匹配，以及网络事件不存在、最后匹配事件字段不符或 evaluator error 判为失败。其 `undecided_if` 仅用于 evidence 缺失或明确截断而无法评估的情况，并明确完整 artifact 中的 mismatch 或无匹配事件属于失败。非空 stronger condition `confirmed_order_state` 另要求 `network.har response bodies` 识别一个新完成且唯一 line item 为一件 product `40448` 的订单。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_network_url_modifiers`
- 为什么修改：可操作的网络规则未说明 eval[1] 启用了 `decode_base64_query`，也未说明 eval[2] 会忽略名称与其配置的下划线 pattern 匹配的 query 参数。
- 应如何修改：将这两个 evaluator 特定的 URL normalization modifier 添加到 `checked_by` 和 HAR decision question 中，以便在选择和比较最后一个匹配事件之前应用这些 modifier。

## Case 509

### 原本 case 是什么

原始任务是在 `shopping` 站点购买 `"Men"s shoe"` 类别中评分最佳、至少有 `5` 条评价且价格最低的产品，并任选一个可用 variant。任务类型为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和四个 `NetworkEventEvaluator`；前者检查响应经解析和非 `RETRIEVE` 归一化后是否满足 `task_type="MUTATE"`、`status="SUCCESS"`、`retrieved_data=null`。四个网络 evaluator 均为 `should_not_exist=false`、`last_event_only=true`，按配置的方法和归一化 URL 选择最后一个匹配事件，再检查启用字段。它们要求：(1) 启用 `decode_base64_query=true` 的 `POST ^__SHOPPING__/checkout/cart/add/uenc/.*/product/65885$`，状态 `200` 且 `post_data.product="65885"`；(2) `GET __SHOPPING__/rest/default/V1/carts/mine/totals`，忽略名称匹配 `\_` 的查询参数，状态 `200`、`items_qty=1`，且 `$.items[0].name="Clarks Men's Tunsil Lane Oxford"`；(3) `POST __SHOPPING__/rest/default/V1/carts/mine/payment-information`，状态 `200` 且 `$.billingAddress.customerId="27"`；(4) `GET __SHOPPING__/checkout/onepage/success`，状态 `200`。只有全部五项分数均为 `1.0`，经合取组合的 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求五项检查全部得 `1.0`：响应通过 `MUTATE/SUCCESS` 检查，网络检查则覆盖添加 product `65885`、totals 中仅有一件 `Clarks Men's Tunsil Lane Oxford`、customer `27` 的 payment-information 和 checkout success。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts，并在 `success_if` 中逐项写出响应比较和四个最后匹配事件的 `200`、请求或响应字段。其 `fail_if` 将响应比较失败、任一网络事件不存在或 expected 字段不符，以及 evaluator 或 task-level error 判为失败。其 `undecided_if` 只写了 artifact 未保留或不可读、无法重建比较的情况，并明确已保留但 evaluator-invalid 或 mismatching 的 artifact 属于失败。非空 stronger condition `confirm_completed_order_state` 进一步要求 “Post-run order record or order-confirmation response” 证明本次运行产生的完成订单恰含一件 product `65885`（`Clarks Men's Tunsil Lane Oxford`）并有具体 selected variant。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`complete-native-artifacts`
- 为什么修改：决定性 artifact 条目列出了 `agent_response.json` 和 `network.har`，但未要求完整保留其内容。
- 应如何修改：说明两个 artifact 均须完整且已留存；将妨碍重建的截断或其他完整性丢失视为 undecided，而不是 evaluator 可见的不匹配。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided-integrity-provenance`
- 为什么修改：`undecided_if` 仅限于文件未留存或不可读的情况，排除了妨碍重建的完整性和来源故障。
- 应如何修改：扩展 `undecided_if`，使其涵盖不完整/截断、损坏或无法确定归属的证据，同时对无效/null 响应、完整 trace 中没有所需匹配项、不匹配以及 evaluator 错误继续判定为 failure。

## Case 510

### 原本 case 是什么

原始任务是在 `shopping` 站点购买 `Home Audio Speaker` 类别中评论数至少为 5、评分最高且在符合条件的商品中价格最低的产品，并可选择任一有货变体。task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含 1 个 `AgentResponseEvaluator` 和 4 个 `NetworkEventEvaluator`。前者对 `agent_response.json` 做解析、投影和非 `RETRIEVE` 归一化，比较稀疏配置中明确设置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；缺失或提供的 `retrieved_data` 均归一化为 `null`，物化出的 `error_details: null` 并非稀疏配置中的比较字段。4 个网络检查均为 `last_event_only=true`、`should_not_exist=false` 并要求 `response_status: 200`：最后一个匹配事件须分别为向 `^__SHOPPING__/checkout/cart/add/uenc/.*/product/75640$` 发出的 `POST`（`decode_base64_query=true`，解析后的 `post_data.product` 为字符串 `75640`）、对 `__SHOPPING__/rest/default/V1/carts/mine/totals` 的 `GET`（忽略名称匹配正则 `_` 的查询参数，响应中 `$.items[0].name` 精确为 `Atlantic Technology FS-7.0-GLB 7-channel Surround Bar (Gloss Black) (Discontinued by Manufacturer)` 且顶层 `items_qty=1`）、向 `__SHOPPING__/rest/default/V1/carts/mine/payment-information` 发出的 `POST`（`$.billingAddress.customerId=27`），以及对 `__SHOPPING__/checkout/onepage/success` 的 `GET`。仅当 5 个 evaluator 的分数全为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`，即 `AgentResponseEvaluator` 和全部 4 个 `NetworkEventEvaluator` 都得到 `1.0`；它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并概述了 `MUTATE`/`SUCCESS` 响应以及商品 `75640`、购物车 totals、付款信息和成功页四类网络事件。其 success 规则要求响应检查及四项网络检查全部通过，failure 规则把无效或报错的响应、缺少符合条件的最后事件、字段不匹配或 evaluator 错误视为失败，undecided 仅用于响应或网络 trace 保留得不完整、无法重建 evaluator 输入的情况。该 draft 的网络说明使用了简写，没有写出 add-to-cart 的完整 URL 约束和完整商品名，也没有声明 `decode_base64_query=true` 或 totals 检查的 `ignored_query_params_patterns: ["_"]`。非空 stronger condition `persisted_semantic_purchase` 另行要求用 `Post-run shopping order-state snapshot` 和 `Catalog snapshot retained for the run` 证明持久化订单包含具体可用变体，并以类别、评论数、评分、价格和变体可用性验证其语义上满足选品要求。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_network_normalization_semantics`
- 为什么修改：网络规则未说明 eval[1] 会启用 base64 查询解码，也未说明 eval[2] 会忽略名称匹配 '_' 的查询参数；此外，它还缩写了预期 URL/产品名称的精确约束。
- 应如何修改：说明四项网络检查的确切内容，包括四项检查全部设置 last_event_only=true 和 should_not_exist=false，为加入购物车检查设置 decode_base64_query=true，为总计检查设置 ignored_query_params_patterns=['_']，并给出完整的加入购物车 URL 正则表达式和完整的预期产品名称。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_native_success_rule`
- 为什么修改：要求匹配每个已配置 URL 和字段的通用规定，不足以仅根据检查清单文本应用两个已启用的 URL normalization 选项。
- 应如何修改：使 success_if 明确纳入 base64 解码规则和忽略查询模式规则，并要求精确满足列举的全部四个事件谓词。

## Case 533

### 原本 case 是什么

原始任务是在 `gitlab` 站点关注账号 `convexegg` 和 `yjlou`。task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含 1 个 `AgentResponseEvaluator` 和 2 个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 做提取、解析和归一化，并比较明确配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；由于这是非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 都归一化为 `null`，默认物化的 `error_details: null` 不参与该稀疏配置比较。两个网络 evaluator 分别按 `POST` 和目标 `follow.json` URL 路径筛选事件，因 `last_event_only=true` 而选择最后一个候选，再要求其完整归一化 URL 无查询参数、方法为 `POST`、响应状态为 `302`：目标依次是 `__GITLAB__/users/convexegg/follow.json` 和 `__GITLAB__/users/yjlou/follow.json`；`should_not_exist=false`，且没有活动的请求体、响应内容、header、cookie、schema、base64 解码或忽略参数约束。仅当三个 evaluator 分数全部为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 要求最终响应通过 `MUTATE`/`SUCCESS` 检查，且两个目标各自最后匹配的 `POST` 到 `follow.json` 均返回 HTTP `302`，从而三个 evaluator 分数全为 `1.0`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 规则要求三项检查全通过，failure 包括响应比较失败、任一目标没有通过的最后匹配 `POST`/`302` 事件或 evaluator 报错，undecided 仅用于 artifacts 未保留或不完整而无法重建三项检查；它同时把已保留但 malformed 的 artifact 或官方 evaluator 错误归为失败。该 draft 将响应条件缩写为 `MUTATE`/`SUCCESS`，没有写出明确配置的 `retrieved_data: null`，网络措辞也未清楚区分按路径选候选与随后进行无查询参数的完整归一化 URL 比较。非空 stronger condition `verify_final_follow_state` 要求额外的 `Post-run GitLab follow-state capture` 通过认证 UI 或 API 状态证明执行账号最终同时关注 `convexegg` 和 `yjlou`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_and_network_semantics`
- 为什么修改：草稿仅将响应 evaluator 描述为 MUTATE/SUCCESS，尽管稀疏配置明确设置了 task_type、status 和 retrieved_data: null。它还主要通过 path、method 和 status 描述网络检查，却未明确说明 last_event_only 会先选取最后一个 method/path 候选项，再进行完整的 normalized URL 比较。
- 应如何修改：说明全部三个明确配置的响应字段，指出非 RETRIEVE 情况下的 null normalization，并说明默认的 error_details 未被配置；同时区分网络候选项筛选与针对无查询参数的 normalized 目标 URL、POST 和 status 302 进行的完整比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_and_ambiguous_decision_rules`
- 为什么修改：success_if 未涵盖 retrieved_data: null，而 undecided_if 将完整但对 evaluator 无效的输入与留存 artifact 损坏或截断混为一谈。
- 应如何修改：使 success 取决于完整的响应比较和两项完整的事件比较。仅将 undecided 用于证据缺失、截断、损坏或 provenance 不足的情况；将完整的无效输入、没有匹配项的完整 trace、不匹配和 evaluator 错误归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compactness_dropped_decisive_fields`
- 为什么修改：虽然检查清单简洁且不存在 run 泄漏，但它通过省略已配置的 retrieved_data-null 字段和无歧义的完整 normalized URL 比较来实现紧凑性。
- 应如何修改：使用简洁的替换措辞，在不添加 trajectories 或 run outcomes 的情况下保留这些与评分相关的语义。

## Case 534

### 原本 case 是什么

原始任务是在 `gitlab` 站点关注 `Jakub Klinkovský`、`Koushik` 和 `Vinta Chen`。task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含 1 个 `AgentResponseEvaluator` 和 3 个 `NetworkEventEvaluator`。响应 evaluator 对完整 `agent_response.json` 执行提取、解析和归一化，比较明确配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；非 `RETRIEVE` 归一化会把 `retrieved_data` 置为 `null`，而物化的 `error_details: null` 不是稀疏配置中的比较字段。三个网络 evaluator 均按 `POST` 和配置 URL 路径筛选并取最后一个匹配事件（`last_event_only=true`、`should_not_exist=false`），再要求归一化 URL 分别为 `__GITLAB__/users/lahwaacz/follow.json`、`__GITLAB__/users/koush/follow.json`、`__GITLAB__/users/vinta/follow.json`，方法为 `POST` 且 `response_status: 302`；没有其他活动的请求体、查询参数、header、cookie、响应内容、schema、base64 解码或忽略字段约束。四个 evaluator 分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 仅在四项检查都为 `1.0` 时才是 `1.0`：响应归一化为预期的 `MUTATE`/`SUCCESS`，且三个配置 follow endpoint 各自最后匹配的 `POST` 返回 `302`；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并在 artifact 问题中写出了 `retrieved_data: null`。其 success 规则分别要求响应检查和三个网络检查通过，failure 包括响应缺失、不可解析或不匹配，以及任一 endpoint 无匹配 `POST`、最后匹配事件状态不是 `302` 或 evaluator 报错；undecided 又将实际响应或完整 HAR 未保留、仅有不确定摘录的情况列为无法判定。因而原 draft 对“未保留的响应”同时作出了 failure 与 undecided 的冲突表述，但明确把完整 artifact 中的 malformed 输入或缺少事件归为 failure。非空 stronger condition `final_follow_state` 要求使用 `Post-run GitLab relationship-state snapshot or authenticated UI/API capture` 证明认证用户最终仍关注 `Jakub Klinkovský (lahwaacz)`、`Koushik (koush)` 和 `Vinta Chen (vinta)`，并排除后续取消关注未被 native evaluator 察觉的缺口。

### 需要修改的部分

#### 修改项 1：native.success_if / fail_if / undecided_if

- Finding ID：`ambiguous_missing_response_classification`
- 为什么修改：检查清单既将留存响应缺失归类为 failure，又将响应未被留存归类为 undecided。
- 应如何修改：说明完整且 provenance 有效的 artifact 如果忠实记录了 null、空或无效响应，则为 failure；仅将 undecided 用于留存证据缺失、截断、损坏或 provenance 无法确定的情况。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`internal_decision_rule_conflict`
- 为什么修改：对响应证据缺失的相互矛盾的分类，导致无法作出一致的 post-run 决策。
- 应如何修改：重写 failure 和 undecided 规则，明确区分忠实留存的 null/无效 evaluator 输入与 post-run 留存丢失或完整性损失。

## Case 535

### 原本 case 是什么

原始任务是在 `gitlab` 站点关注 `Jakub K`、`ghost` 和 `Benoît Blanchon`。task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含 1 个 `AgentResponseEvaluator` 和 3 个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 进行提取、解析及非 `RETRIEVE` 归一化，比较稀疏配置中明确设置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；缺失或提供的 `retrieved_data` 都归一化为 `null`，物化的 `error_details: null` 不属于比较字段。网络 evaluator 分别对 `__GITLAB__/users/lahwaacz/follow.json`、`__GITLAB__/users/ghost/follow.json` 和 `__GITLAB__/users/bblanchon/follow.json` 按路径及 `POST` 筛选，选择最后一个匹配事件（`last_event_only=true`），并要求其归一化 URL、`POST` 方法和 `response_status: 302` 全部匹配；`should_not_exist=false`，没有其他活动的请求体、查询参数、header、cookie、响应内容、schema、base64 解码或忽略字段约束。只有全部四个 evaluator 分数均为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 要求 `AgentResponseEvaluator` 接受最终响应，且针对 `lahwaacz`、`ghost`、`bblanchon` 的三个 `NetworkEventEvaluator` 都接受相应事件，使四个分数及 `TaskEvalResult.score` 均为 `1.0`；决定性 artifacts 为 `agent_response.json` 和 `network.har`。其 success 规则要求完整响应及完整 HAR 的四项检查全通过，failure 包括响应被拒绝或 evaluator 报错、没有匹配配置路径的 `POST`、所选事件的归一化 URL 或状态不符；undecided 仅用于 artifact 缺失或保留副本不完整且尚无其他组件已经证明失败的情况，并把完整 malformed 响应或完整 trace 缺少事件归为失败。该 draft 将响应预期简写为 `MUTATE`/`SUCCESS`，没有写出明确配置的 `retrieved_data: null` 及其非 `RETRIEVE` 归一化语义。非空 stronger condition `final_follow_state` 要求额外的 `post-run GitLab follow-state UI or API capture` 证明运行结束时登录账号仍关注 `Jakub K (lahwaacz)`、`ghost` 和 `Benoît Blanchon (bblanchon)`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_explicit_retrieved_data_semantics`
- 为什么修改：原生 AgentResponseEvaluator 描述将配置的预期缩减为 MUTATE/SUCCESS，且未说明 sparse-original 中的 retrieved_data: null 字段。
- 应如何修改：说明明确配置的响应字段为 task_type MUTATE、status SUCCESS 和 retrieved_data null；简要解释非 RETRIEVE normalization 会将缺失或提供的 retrieved_data 映射为 null，而实体化的 error_details 并非明确配置的比较字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_response_success_rule`
- 为什么修改：success_if 提到了获得的 evaluator 分数，但未将所有明确配置的响应字段操作化。
- 应如何修改：使 success_if 要求针对 task_type MUTATE、status SUCCESS 和 retrieved_data null 执行 released parsing 和 normalization，同时保留现有的合取网络事件要求。

## Case 536

### 原本 case 是什么

原始任务是在 `gitlab` 站点关注 `ghost`、`R1kk3r` 和 `Abishek`。task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含 1 个 `AgentResponseEvaluator` 和 3 个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 执行解析、投影和归一化，比较明确配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；因为任务不是 `RETRIEVE`，缺失或提供的 `retrieved_data` 均归一化为 `null`，稀疏配置未设置物化默认字段 `error_details: null`，因此不比较该字段。三个网络 evaluator 分别按 `POST` 和 `__GITLAB__/users/ghost/follow.json`、`__GITLAB__/users/R1kk3r/follow.json`、`__GITLAB__/users/abisubramanya27/follow.json` 筛选事件，选择最后一个匹配事件（`last_event_only=true`），并比较归一化 URL、`POST` 方法及 `response_status: 302`；`should_not_exist=false`，没有活动的 body、独立 query、header、cookie、response-content、schema、ignored-field 或 base64 解码条件。`TaskEvalResult.create` 对四项分数作全合取，只有全部等于 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 仅在 `AgentResponseEvaluator` 和三个 `NetworkEventEvaluator` 都得到 `1.0` 时为 `1.0`；它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts，并要求三个 endpoint 各自所选的最后匹配 `POST` 满足 URL、方法和 `302` 状态。其 success 规则要求响应通过配置的 `MUTATE`/`SUCCESS` 比较且三个网络检查全部通过，failure 包括响应不匹配或 evaluator 报错、无符合条件的 `POST`、所选事件 URL/方法/状态不符，undecided 则用于 artifact 缺失或仅保留部分摘录而无法重建 evaluator 结果；若 malformed 或不完整文件已知就是实际 evaluator 输入，则归为 failure。该 draft 的响应说明省略了明确配置的 `retrieved_data: null` 及非 `RETRIEVE` 归一化行为。非空 stronger condition `persistent_follow_state` 要求通过 `Post-run authenticated GitLab following-state capture` 中的 following-list 或状态/API 导出，证明执行账号最终关注 `ghost`、`R1kk3r` 和由配置目标 `abisubramanya27` 表示的 `Abishek`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：AgentResponseEvaluator 规则仅提及 MUTATE 和 SUCCESS，尽管稀疏任务中还明确配置了 retrieved_data:null。
- 应如何修改：说明 released parsing 和 normalization 会将明确配置的 task_type、status 和 retrieved_data 字段分别与 MUTATE、SUCCESS 和 null 进行比较；解释此非 RETRIEVE 任务会将缺失或提供的 retrieved_data 值 normalization 为 null，并且不比较实体化的 error_details 默认值。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：success_if 将最终响应检查描述为 MUTATE/SUCCESS 比较，这一描述并不完整。
- 应如何修改：在 success_if 和响应 artifact 问题中加入预期的 retrieved_data:null 以及 released 非 RETRIEVE normalization 行为。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：一份原本简洁的检查清单遗漏了一个具有决定性的已配置响应字段。
- 应如何修改：在保持紧凑性的同时，添加 retrieved_data:null 的 normalization/比较语义；不要将 error_details 添加为必需字段。

## Case 538

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：把订单 `#299` 的地址修改为 `456 Oak Avenue, Apartment 5B, New York, NY, 10001`。任务 revision 为 `2`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者对 `agent_response.json` 进行解析和归一化，比较显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；这是非 `RETRIEVE` 任务，`retrieved_data` 的值不另行检查，物化出的 `error_details` 并非显式配置字段。后者从 `network.har` 中按不区分大小写的 `POST` 和归一化路径筛选 `__SHOPPING_ADMIN__/sales/order/addressSave/address_id/598/` 候选，并因 `last_event_only: true` 选择最后一个；随后完整比较归一化 URL（包括不得出现未忽略的额外 query parameters）、`response_status: 302`，以及 `city=New York`、`country_id=US`、`postcode=10001`、`region=New York`、`region_id=43`、`street[0]=456 Oak Avenue`、`street[1]=Apartment 5B`，同时忽略匹配 `^form_key$` 的 POST key，且 `should_not_exist: false` 表示无候选即失败。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 接受预期的 `MUTATE/SUCCESS` 响应，并由 `NetworkEventEvaluator` 接受最后一个匹配地址保存路径、字段和 HTTP `302` 的 POST；它把网络 URL 规则概括成路径匹配，未写出选中事件还须通过完整归一化 URL 比较。它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并规定两项 evaluator 都为 `1.0` 才是 success，响应或网络检查不通过及 evaluator error 为 failure，artifact 缺失、不可读或不完整到无法重建结果时为 undecided。非空 stronger condition `persisted_order_address` 另要求用 `Post-run shopping-admin order #299 address-state capture` 证明订单 `#299` 的持久化地址确为 `456 Oak Avenue, Apartment 5B, New York, NY 10001`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_comparison_omitted`
- 为什么修改：网络 artifact 问题将匹配已配置的 URL path 视为充分条件，并遗漏了随后对所选事件进行的完整 normalized URL 比较。在未配置查询忽略项的情况下，即使 method、path、status 和 POST 字段均匹配，额外的查询部分也可能导致 NetworkEventEvaluator 失败。
- 应如何修改：说明 POST 加 normalized path 比较会筛选候选项，last_event_only 会选择最后一个候选项，然后该候选项必须匹配完整的已配置 normalized URL——包括不存在未被忽略的查询参数——以及 status 和投影后的 POST data。

## Case 540

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：把订单 `#301` 的地址修改为 `321 Birch Boulevard, Suite 200, Dallas, TX, 75201`。任务 revision 为 `2`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者解析并归一化 `agent_response.json`，按显式配置检查 `task_type: MUTATE`、`status: SUCCESS` 和 `retrieved_data: null`；在该非 `RETRIEVE` 任务中，`retrieved_data` 的值不另行检查。后者在 `network.har` 中检查最后一个符合方法和 URL 条件的 `POST`：URL 为 `__SHOPPING_ADMIN__/sales/order/addressSave/address_id/602/`，响应状态为 `302`，POST 数据包含 `city=Dallas`、`country_id=US`、`postcode=75201`、`region=Texas`、`region_id=57`、`street[0]=321 Birch Boulevard`、`street[1]=Suite 200`，并忽略匹配 `^form_key$` 的 key；`last_event_only: true` 使最后一个匹配事件具有决定性，`should_not_exist: false` 使无匹配事件不被接受。`TaskEvalResult.score` 仅在两个 evaluator 分数均为 `1.0` 时为 `1.0`，任一非 `1.0` 结果或 evaluator error 均不能通过。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求最终响应通过归一化的 `MUTATE/SUCCESS` 检查，且 HAR 中最后一个匹配地址保存事件通过 URL、方法、地址 POST 数据和 `302` 状态检查。它把 `agent_response.json` 与 `network.har` 作为决定性 artifacts；success 要求两个官方 evaluator 都为 `1.0`，failure 明列响应缺失、畸形或不匹配，以及无匹配 POST 或最后匹配 POST 的 URL、方法、状态或数据不符，但没有穷尽写明所有 evaluator error 或其他可重建的非 `1.0` 结果。其 undecided 规则限于尚无 artifact 已证明失败、但 `agent_response.json` 或 `network.har` 缺失或不完整到无法重建检查的情况，并明确完整 HAR 中没有匹配事件属于 failure。非空 stronger condition `persisted_order_address` 要求通过 `Post-run shopping-admin order #301 state snapshot or export` 证明订单实际持久化了两行街道、Dallas、Texas/TX、`75201` 和 `US`。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`composition_error_outcomes`
- 为什么修改：虽然存在全部必须通过的规定，但检查清单从未明确说明：evaluator 错误产生非 1.0 分数属于原生 failure。
- 应如何修改：添加一条明确的原生规则：如果可以根据完整证据重建，则任一已配置 evaluator 的任何错误或其他非 1.0 结果都会使 TaskEvalResult.score 为 0，并构成 failure。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_failure_partition`
- 为什么修改：fail_if 涵盖无效响应、缺失事件和比较不匹配，但遗漏了可重建的 evaluator 错误及其他非 1.0 结果。
- 应如何修改：扩展 fail_if，加入兜底规则，以涵盖来自完整留存输入的 evaluator 错误或任何其他低于 1.0 的 evaluator 分数，同时将 undecided 限定为证据留存、完整性或 provenance 丢失的情况。

## Case 541

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：把订单 `#125` 的地址修改为 `654 Elm Drive, Apartment 12, Miami, FL, 33101`。任务 revision 为 `2`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者解析并归一化 `agent_response.json`，比较显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；对于该非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 会归一化为 `null`，而物化默认值 `error_details` 不是显式配置的比较字段。后者在完整 `network.har` 中按 `POST` 和归一化 URL 路径筛选候选，选择最后一个匹配事件，并要求其完整归一化 URL 为 `__SHOPPING_ADMIN__/sales/order/addressSave/address_id/249/`、HTTP 状态为 `302`，POST 数据为 `city=Miami`、`country_id=US`、`postcode=33101`、`region=Florida`、`region_id=18`、`street[0]=654 Elm Drive`、`street[1]=Apartment 12`，同时忽略匹配 `^form_key$` 的 key。`TaskEvalResult.score` 采用合取组合，只有两个 evaluator 分数都等于 `1.0` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 需要 `AgentResponseEvaluator` 接受预期的 `MUTATE/SUCCESS` 响应，并由 `NetworkEventEvaluator` 接受选中的地址更新 POST；其响应说明只笼统提到非 retrieve 的 `retrieved_data` 处理，没有明确写出配置值 `retrieved_data: null`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，success 要求两个 evaluator 均为 `1.0`，failure 包括响应无效或不匹配、无合格 POST、最后选中 POST 字段不符或 evaluator error，undecided 则限于无法取得准确响应和完整 HAR、且没有保留的官方逐 evaluator 结果可补足判断。非空 stronger condition `persisted_order_address` 要求 `Authoritative post-run order #125 state export or fresh order-detail response` 同时标识订单 `#125`，并证明请求地址已持久化；其 rationale 还指出原生检查不能独立证明 `address_id 249` 属于订单 `#125`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_expected_retrieved_data_omitted`
- 为什么修改：AgentResponseEvaluator 规则未明确将 retrieved_data:null 标识为第三个稀疏配置的预期字段；“包括其非 retrieve 的 retrieved_data 处理”在操作层面不够充分。
- 应如何修改：说明 released parsing 和 normalization 必须在结构上匹配 task_type MUTATE、status SUCCESS 和 retrieved_data null；明确此非 RETRIEVE 任务会将缺失或提供的 retrieved_data normalization 为 null，并且不比较实体化的 error_details 默认值。

## Case 544

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：把 `Selene Yoga Hoodie` 的产品描述更新为 `"{count} customer(s) love it!"`，其中 `count` 是四星或以上评论数；若没有此类评论，则使用 `"don't miss out on this amazing product"`。任务 revision 为 `2`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者解析并归一化完整 `agent_response.json`，比较显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`，包括已发布的 `performed_operation` alias 处理；这是非 `RETRIEVE` 任务，`retrieved_data` 归一化为 `null` 且其值不另行比较，`error_details` 未被显式配置。后者以 `POST` 和归一化 URL 筛选 `^__SHOPPING_ADMIN__/catalog/product/save/id/1108/type/configurable/store/0/set/\d+/back/edit$` 的事件，因 `last_event_only: true` 检查最后一个匹配事件，并要求 `product[short_description]` 为 `<p>3 customer(s) love it!</p>`、`response_status` 为 `302`；`should_not_exist: false` 表示完整 trace 中没有合格事件即不通过。`TaskEvalResult.score` 只有在两个 evaluator 分数都为 `1.0` 时才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求最终响应通过 `MUTATE/SUCCESS` 比较，并要求最后一个匹配产品 `1108` 保存 URL 的 POST 携带 `product[short_description] = "<p>3 customer(s) love it!</p>"` 且返回 `302`；它没有写明 `AgentResponseEvaluator` 对显式配置的 `retrieved_data: null` 所做的解析和归一化检查。它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts，success 要求两者分别产生 `1.0`，failure 包括任一 evaluator 低于 `1.0` 或报错、响应不匹配、无合格 POST、最后匹配 POST 的描述或状态不符，undecided 则表述为缺少任一 artifact、无法重建两个 evaluator 结果。非空 stronger condition `persisted_product_description` 要求用 `Post-run shopping-admin product-state snapshot` 证明 `Selene Yoga Hoodie`（product `1108`）持久化的 `short_description` 为 `<p>3 customer(s) love it!</p>`，并渲染为 `3 customer(s) love it!`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_incomplete`
- 为什么修改：AgentResponseEvaluator 仅被描述为 MUTATE/SUCCESS 检查，遗漏了明确配置的 retrieved_data:null，以及 released parsing/normalization 和结构比较行为。
- 应如何修改：说明完整响应必须针对稀疏配置字段 task_type:MUTATE、status:SUCCESS 和 retrieved_data:null 通过 released parsing 和 normalization；明确此 MUTATE 任务会将 retrieved_data normalization 为 null，并且未配置的 error_details 不参与评分。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`response_decision_rule_not_operational`
- 为什么修改：success_if 的响应分支过于简略，无法重建已配置的比较，而且未明确分类常规的完整无效响应情况。
- 应如何修改：使 success_if 在 released parsing/normalization 下应用所有明确配置的响应字段，并使 fail_if 明确包括完整的 null、不可解析或非对象响应、字段不匹配以及 evaluator 错误。将 undecided 限定为留存证据缺失、损坏、不完整或 provenance 有缺陷的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_response_semantics_omitted`
- 为什么修改：虽然检查清单简洁且不存在 run 泄漏，但它通过省略一个已配置响应字段及其与评分相关的 parsing/结构语义来实现紧凑性。
- 应如何修改：以紧凑方式添加缺失的 AgentResponseEvaluator 细节，不要添加 run outcomes、metadata 或 trajectory 要求。

## Case 546

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：把 `Lucia Cross-Fit Bra` 的产品描述更新为 `"{count} customer(s) love it!"`，其中 `count` 是四星或以上评论数；若没有此类评论，则使用 `"don't miss out on this amazing product"`。任务 revision 为 `2`。

### Benchmark 怎么测

依次配置 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者提取、解析并归一化 `agent_response.json`，比较稀疏配置中明确给出的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；对该非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 均映射为 `null`，其内容和顺序不另行比较，而物化默认值 `error_details` 未配置并被忽略。后者按 `POST` 和 URL `^__SHOPPING_ADMIN__/catalog/product/save/id/1668/type/configurable/store/0/set/\d+/back/edit$` 筛选 evaluation events，以 `last_event_only: true` 选择最后一个匹配事件，并要求归一化后的 `product[short_description]` 为 `<p>don't miss out on this amazing product</p>`、`response_status` 为 `302`；`should_not_exist: false` 表示没有匹配事件即失败。`TaskEvalResult.score` 仅在两个 evaluator 分数均为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native score 只有在 `AgentResponseEvaluator` 接受配置的 `MUTATE/SUCCESS` 结构、且 `NetworkEventEvaluator` 接受产品 `1668` 的最后匹配保存 POST、固定描述 HTML 和 `302` 状态时才为 `1.0`；它没有写出显式配置的 `retrieved_data: null` 及相应非 `RETRIEVE` 归一化语义，也未区分该字段与未配置的物化 `error_details`。它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts；两条 success 分别要求两个 evaluator 为 `1.0`，failure 包括响应被拒绝或报错、无合格 POST、最后匹配事件的描述或状态不符及网络 evaluator error，undecided 限于响应或相关 HAR 事件不可用、被截断且无官方逐 evaluator 结果足以确定两项分数。非空 stronger condition `persisted_description_matches_review_count` 另要求用 `Post-run review-record snapshot or export for Lucia Cross-Fit Bra` 计算四星及以上评论数，并用 `Post-run product-record or shopping-admin state snapshot for Lucia Cross-Fit Bra` 验证持久化描述确实符合该数量或零评论 fallback。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent-response-sparse-fields`
- 为什么修改：原生描述将 AgentResponseEvaluator 语义缩减为 MUTATE/SUCCESS 结构比较，却未说明 sparse original 明确配置了 task_type、status 和 retrieved_data:null，也未说明 error_details 只是实体化的默认值，而非明确配置的比较字段。
- 应如何修改：说明 released parsing 必须生成结构化响应，其已配置的 normalized shape 包含 task_type MUTATE、status SUCCESS 和 retrieved_data null；解释非 RETRIEVE 处理会将 retrieved_data 映射为 null，而不进行内容/顺序比较，并且未配置的 error_details 不影响评分。

## Case 548

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：为 `Frankie Sweatshirt` 的 S 和 M 尺码新增蓝色（Blue）选项。任务要求修改该可配置商品的颜色与对应尺码变体。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。前者按已发布的解析与非 `RETRIEVE` 归一化语义比较显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；物化得到的 `error_details` 不属于稀疏配置中的显式比较字段。第一个网络 evaluator 在以 POST 和规范化 URL `__SHOPPING_ADMIN__/catalog/product_attribute/save/attribute_id/93` 过滤后只取最后事件，要求响应为 302，且 `serialized_options` 匹配 `^.*swatchtext%5Bvalue%5D%5Boption_\d+%5D%5B0%5D=Blue.*$`；第二个以 POST 和 URL 正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/110/type/configurable/store/0/set/\d+/back/edit$` 过滤后只取最后事件，要求响应为 302、`product[name]` 为 `Frankie Sweatshirt`，并由 JSONPath `$['configurable-matrix-serialized'][?(@.newProduct == 1)].attributes` 得到按数组 schema 比较的两个无序字符串 `size: s, color: blue`、`size: m, color: blue`。`should_not_exist=false`，且 `TaskEvalResult.score` 仅在三个 evaluator 分数全为 1.0 时为 1.0；决定性输入是 `agent_response.json` 和 `network.har`。

### 原本 draft 是什么

原始 draft 宣称 benchmark success 是三个 evaluator 全部为 1.0：最终响应通过 `MUTATE/SUCCESS` 与 null retrieved data 检查，最后匹配的颜色属性保存 POST 通过 Blue 选项检查，最后匹配的商品保存 POST 通过 S-Blue/M-Blue 检查。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts；`success_if` 要求响应、302 状态、Blue 正则、商品名及恰好两个无序属性字符串均通过，`fail_if` 将任一不为 1.0、缺失或不合规事件及 evaluator/orchestration error 判为失败，`undecided_if` 仅用于留存 artifacts 缺失或截断且无权威结果、因而无法重建全部检查的情形。非空 stronger condition `persisted_variant_state` 另要求通过 “Post-run shopping-admin product-configuration readback” 证明 `Frankie Sweatshirt` 的 S、M 均持久存在 Blue 变体；原 draft 对网络端点只用了属性保存和商品保存的概括性称呼，没有写出两个完整 URL 条件。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_exact_network_urls`
- 为什么修改：两个 NetworkEventEvaluator 的描述都将其配置的 URL 条件替换成了非正式标签，例如“颜色属性保存路径”和“可配置产品保存路径”。
- 应如何修改：说明第一个 evaluator 使用规范化 URL `__SHOPPING_ADMIN__/catalog/product_attribute/save/attribute_id/93`，第二个 evaluator 使用配置的锚定正则表达式 `^__SHOPPING_ADMIN__/catalog/product/save/id/110/type/configurable/store/0/set/\d+/back/edit$`，同时保留 POST、last_event_only、status 和 payload 语义。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`underspecified_success_rule`
- 为什么修改：success_if 未定义哪些 URL/method 事件算作匹配，因此其充分条件存在歧义。
- 应如何修改：在 success_if 中直接包含两个确切的已配置 URL 条件，以及现有的 method、最后事件、status 和 post-data 条件。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_textually_preserved`
- 为什么修改：该检查清单简洁且不泄露运行信息，但其简洁性是通过省略网络 evaluator 的确切 URL 条件实现的。
- 应如何修改：用确切的已配置 URL/path 表达式替换两个端点标签，且不添加运行结果或无关细节。

## Case 549

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：为绿色的 `Minerva LumaTech V-Tee` 新增尺码 XXXL。任务对象是该商品的绿色配置。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。响应 evaluator 按已发布的非 `RETRIEVE` 归一化语义检查显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`，物化默认值 `error_details` 不参与稀疏字段比较。第一个网络 evaluator 先按 POST 和规范化 URL `__SHOPPING_ADMIN__/catalog/product_attribute/save/attribute_id/144` 过滤并取最后事件，要求响应 302，且 `serialized_options` 匹配 `^.*swatchtext%5Bvalue%5D%5Boption_\d+%5D%5B0%5D=XXXL.*$`；第二个按 POST 和 `^__SHOPPING_ADMIN__/catalog/product/save/id/1492/type/configurable/store/0/set/\d+/back/edit$` 过滤并取最后事件，要求响应 302、`product[name]` 为 `Minerva LumaTech&trade; V-Tee`，且 JSONPath `$['configurable-matrix-serialized'][?(@.newProduct == 1)].attributes` 在所配数组 schema 下得到单元素 `size: xxxl, color: green`。两项均为 `last_event_only=true`、`should_not_exist=false`，没有额外 header、query、cookie、response-content、ignore-pattern 或 base64 解码约束；`TaskEvalResult.score` 只有在三个分数均为 1.0 时才为 1.0。

### 原本 draft 是什么

原始 draft 将 native success 定义为 `TaskEvalResult.score == 1.0`，即 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator` 全部得 1.0。它列出 `agent_response.json` 与 `network.har`：前者用于 `MUTATE/SUCCESS/retrieved_data null` 的解析归一化，后者用于最后的 POST/302 属性保存 XXXL 检查，以及 product 1492、名称 `Minerva LumaTech&trade; V-Tee`、属性数组 `["size: xxxl, color: green"]` 的商品保存检查；`success_if` 要求三者全通过，`fail_if` 在 artifacts 均留存时把任一检查失败或报错判为 0.0，`undecided_if` 则把任一 artifact 未留存、无法重放全部检查列为未决。非空 stronger condition `persisted-green-xxxl-configuration` 要求额外的 “Retained post-run shopping-admin product-state export or product edit-page capture” 显示 product 1492 持久存在 XXXL/green 配置；原 draft 没有写出精确的 attribute-save URL、完整商品保存 URL 正则，也未限定 artifacts 的完整性和 provenance。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`B1_exact_network_filters`
- 为什么修改：两个网络检查仅被描述为通用的属性保存事件和产品保存事件，遗漏了配置的 `attribute_id/144` URL 和完整的锚定产品保存 URL 模式；“最后一个匹配项”也未准确说明选择顺序。
- 应如何修改：说明每个已配置的 URL 和 method 过滤器，说明 last_event_only 选择经过 URL/method 过滤后的最后一个事件，并说明所选事件随后必须满足其配置的 status、body、JSONPath 和 schema 比较。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`B2_complete_retained_artifacts`
- 为什么修改：该检查清单列出了正确的文件，但未确定它们是具有可用来源信息的完整捕获。
- 应如何修改：要求完整捕获的 agent response 和完整 HAR，并区分 agent 生成的无效内容与运行后的截断、损坏或来源信息丢失。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`B3_operational_decision_rules`
- 为什么修改：成功规则无法重建确切的 URL 比较，而失败和 undecided 规则未正确处理留存完整性丢失。
- 应如何修改：使 success 取决于确切的三个检查；将不匹配、无效响应、完整 trace 中不存在事件以及 evaluator 错误归类为 failure；仅当证据留存、完整性或来源信息丢失导致无法重建时，才判定为 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`B4_preserve_decisive_semantics`
- 为什么修改：虽然该检查清单简洁且没有运行信息泄露，但其压缩移除了与评分相关的 URL 和证据完整性语义。
- 应如何修改：保留简洁结构，同时添加确切的 URL 过滤器、正确的最后事件语义以及完整捕获限定条件。

## Case 551

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：为 `Diana Tights` 的所有颜色变体新增尺码 30 和 31。目标覆盖该商品的每一种颜色变体。

### Benchmark 怎么测

配置包含依次执行的 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应 evaluator 按已发布的解析及非 `RETRIEVE` 归一化比较显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；`ordered=false` 与 `results_schema` 的 `type:null` 不增加 retrieved-data 条件，物化的 `error_details` 默认值也不是稀疏配置中的显式比较项。网络 evaluator 以 POST 和 `^__SHOPPING_ADMIN__/catalog/product/save/id/1854/type/configurable/store/0/set/\d+/back/edit$` 过滤并只取最后事件，要求响应 302；表单中 size 组 144 必须有 `attribute_id=144`、`code=size`、`position=0`，值 171、172、173、174 均有 `include=1` 及同号 `value_index`，color 组 93 必须有 `code=color`、`position=1`，值 49、50、56 也均有 `include=1` 及同号 `value_index`。该检查为 `last_event_only=true`、`should_not_exist=false`，无额外 header、query、cookie、response-content、schema、ignore-pattern 或 base64 解码条件；仅当两个 evaluator 分数都为 1.0 时，`TaskEvalResult.score` 才为 1.0。

### 原本 draft 是什么

原始 draft 宣称 `TaskEvalResult.score` 仅在两个检查都为 1.0 时成立：最终响应通过 `MUTATE/SUCCESS`，且最后匹配的 product 1854 保存 POST 满足所配 URL、全部表单字段和 302。它把 `agent_response.json` 与 `network.har` 作为决定性 artifacts，并在网络问题中列出 size attribute 144 的 171–174 和 color 的 49、50、56，以及相应 code、position、include、value_index；`success_if` 要求两项全通过，`fail_if` 把任一 0.0 或 error（包括缺失或字段不匹配的最后保存 POST）判为失败。`undecided_if` 声称在没有留存 `TaskEvalResult` 且一个或两个原始 artifacts 不可用或不可读、无法重建两个分数时为未决，同时又说已留存的 evaluator zero/error 属于失败；非空 stronger condition `persisted_variant_state` 另要求 “Post-run Diana Tights catalog-state snapshot or export” 显示每个颜色变体都持久提供尺码 30 和 31。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_retrieved_data_semantics`
- 为什么修改：AgentResponse 规则遗漏了明确配置的 `retrieved_data:null` 预期及其已发布的非 RETRIEVE normalization 行为。
- 应如何修改：说明响应依据 `task_type MUTATE`、`status SUCCESS` 和预期的 `retrieved_data:null` 通过已发布的解析与 normalization；明确 MUTATE normalization 会将 retrieved_data 映射为 null，并且实例化的 error_details 默认值并未被明确配置。

#### 修改项 2：native.checked_by 及 evaluator 组合规则

- Finding ID：`conclusive_failure_can_be_called_undecided`
- 为什么修改：如果一个原始 artifact 缺失，但另一个完整 artifact 能确定 evaluator 可见的不匹配，则当前的 fail_if 和 undecided_if 会同时适用。
- 应如何修改：无论能否重建另一个 evaluator，任何能够确定重建出的 evaluator 不匹配或错误都应属于原生 failure。

#### 修改项 3：native.decisive_artifacts

- Finding ID：`artifact_completeness_not_required`
- 为什么修改：artifact 声明没有明确要求完整且与运行关联的 `agent_response.json` 和完整且与运行关联的 `network.har`，尽管确定最后一个匹配事件依赖 trace 的完整性；undecided 规则还引用了一个未列为决定性证据的 artifact。
- 应如何修改：将 `agent_response.json` 和 `network.har` 限定为完整、完整性得到保留且与运行关联的证据，并以它们为重建依据；从 undecided_if 中移除对未列出的 TaskEvalResult 的依赖。

#### 修改项 4：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_rule_is_overbroad`
- 为什么修改：当前 undecided 规则会在任一原始 artifact 不可用或不可读时触发，即使剩余 artifact 已经证明存在原生 failure；该规则也未处理不完整或来源不明的证据。
- 应如何修改：将 undecided 限制为以下情况：留存、完整性或来源信息丢失导致无法作出整体判定，并且没有任何可用的可信 artifact 已经确定 evaluator 结果不是 `1.0`。

#### 修改项 5：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decision_branches_not_mutually_coherent`
- 为什么修改：重叠的 failure 和 undecided 分支使这个除此之外结构良好的检查清单在内部不一致。
- 应如何修改：重写 fail_if 和 undecided_if，使完整的 evaluator 可见不匹配始终选择 failure，而 undecided 仅适用于证据丢失导致无法得出确定结论的情况。

## Case 557

### 原本 case 是什么

原始任务是在 `gitlab` 和 `wikipedia` 站点执行 `MUTATE`：创建名为 `nolan_old_fans` 的仓库，必要时查阅所提供的 Wikipedia，并用 Web IDE 创建 README。README 只能包含以仓库名为主标题、随后列出 Christopher Nolan 在 2010 年之前院线发行的长片标题的项目符号列表，并提交到默认分支。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：响应检查按已发布的解析与非 `RETRIEVE` 归一化比较 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`。仓库创建检查先按 POST 与配置 URL path 过滤并取最后事件，随后还比较完整规范化 URL `__GITLAB__/projects`，要求响应 302，且 `project[name]`、`project[path]` 均为 `nolan_old_fans`、`project[namespace_id]` 为 `2505`。提交检查同样取 POST/path 过滤后的最后事件并比较完整规范化 URL `__GITLAB__/api/v4/projects/byteblaze%2Fnolan_old_fans/repository/commits`，要求响应 201、`branch=main`、`$.actions[0].action` 匹配 `^(update|create)$`、文件为 `README.md`、`$.actions[1].action=null`；内容按 markdown schema 归一化后须为 `# nolan_old_fans`、一个空行及依次列出的 Following、Memento、Insomnia、Batman Begins、The Prestige、The Dark Knight。两个网络检查均为 `last_event_only=true`、`should_not_exist=false`；只有三个 evaluator 分数全为 1.0 时，`TaskEvalResult.score` 才为 1.0。

### 原本 draft 是什么

原始 draft 宣称 native success 要求三个 evaluator 全为 1.0：响应为 `MUTATE/SUCCESS` 且 retrieved data 为 null，最后的仓库创建事件通过 302 和三个项目字段检查，最后的提交事件通过 201、`main`、README action、文件路径、第二 action 为 null 及六部影片 markdown 检查。它把 `agent_response.json`、`network.har — repository creation check`、`network.har — README commit check` 列为决定性 artifacts，并将三个 conjunct 分列于 `success_if`；`fail_if` 覆盖响应不匹配或错误、过滤后无事件、最后事件字段不匹配以及任何官方 ERROR，`undecided_if` 仅用于响应或 HAR 缺失、不可读或明显不完整且无官方结果可解消的留存问题。两个非空 stronger conditions 分别是 `durable_default_branch_state`，要求 post-run GitLab snapshot/export 证明 `byteblaze/nolan_old_fans` 的实际默认分支 HEAD 上存在仅含指定内容的 README；以及 `web_ide_usage`，要求 browser trace、video 或 screenshots 证明通过 Web IDE 编辑并提交。原 draft 的网络规则只表述为 POST/path 过滤后的状态与 payload 检查，没有写明入选事件还需通过完整规范化 URL 比较。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`full_network_url_semantics`
- 为什么修改：两个网络检查都描述了 URL path 过滤，但遗漏了随后对所选事件的完整规范化 URL 比较。
- 应如何修改：对于每个 NetworkEventEvaluator，说明经过 method/path 过滤后的最后一个事件还必须通过已发布的、针对完整配置 URL 的规范化比较，包括适用的 query normalization，以及 status 和 post data。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_network_decision_rules`
- 为什么修改：success_if 和 fail_if 规则列举了 path、status 和 body 条件，但未以可操作方式涵盖事件选择后出现的规范化 URL/query 不匹配。
- 应如何修改：在两个网络 success 合取条件中添加完整的规范化 URL 一致性，并将所选事件的任何 URL/query 不匹配归类为原生 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`missing_decisive_semantic`
- 为什么修改：这个原本简洁的原生规则遗漏了一个与评分相关的 URL 比较。
- 应如何修改：保留现有的简洁结构，同时将完整的规范化 URL 条件添加到网络 artifact 问题和决策规则中。

## Case 558

### 原本 case 是什么

原始任务是在 `gitlab` 和 `wikipedia` 站点执行 `MUTATE`：创建名为 `nolan_young_fans` 的仓库，必要时查阅所提供的 Wikipedia，并使用 Web IDE 创建 README。README 只能包含以仓库名为主标题、随后列出 Christopher Nolan 在 2010 年之后院线发行的长片标题的项目符号列表，并提交到默认分支。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。响应检查按已发布的非 `RETRIEVE` 归一化语义比较 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`。第一个网络检查对 `__GITLAB__/projects` 的 POST 只取最后匹配事件，要求响应 302，且 `project[name]`、`project[path]` 为 `nolan_young_fans`、`project[namespace_id]` 为 `2505`；第二个对 `__GITLAB__/api/v4/projects/byteblaze%2Fnolan_young_fans/repository/commits` 的 POST 只取最后匹配事件，要求响应 201、`branch=main`、`$.actions[0].action` 匹配 `^(update|create)$`、`$.actions[0].file_path=README.md`、`$.actions[1].action=null`，并按 markdown schema 比较内容 `# nolan_young_fans`、空行及依次排列的 Inception、The Dark Knight Rises、Interstellar、Dunkirk、Tenet、Oppenheimer。两个网络 evaluator 均为 `last_event_only=true`、`should_not_exist=false`；`TaskEvalResult.score` 仅在三个 evaluator 分数都等于 1.0 时为 1.0。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 只有在 `AgentResponseEvaluator`、仓库创建 `NetworkEventEvaluator` 和 README 提交 `NetworkEventEvaluator` 全为 1.0 时才为 1.0。它以 `agent_response.json` 和 `network.har` 为决定性 artifacts，要求响应通过 `MUTATE/SUCCESS/retrieved_data=null`，最后的创建 POST 通过 302 与项目字段，最后的提交 POST 通过 201、`main`、`update|create`、`README.md`、第二 action 为 null 及包含 Inception、The Dark Knight Rises、Interstellar、Dunkirk、Tenet、Oppenheimer 的 markdown；`fail_if` 覆盖任一检查失败或报错，`undecided_if` 仅限评估后留存副本缺失或截断而无法还原原输入。原 draft 有三个非空 stronger conditions：`strict_after_2010_content` 声称应严格排除其所称的 2010 年影片 Inception；`verify_web_ide_use` 要求 `network.har` 或 browser trace 证明使用 Web IDE；`verify_persisted_default_branch_state` 要求 post-run GitLab snapshot/API export 证明仓库仍存在、README 位于实际默认分支 tip。源码口径 review 指出第一个 stronger condition 关于 Inception 发行年份的事实不在 packet 来源边界内，但这确是原 draft 作出的声明。

### 需要修改的部分

#### 修改项 1：case 身份与范围

- Finding ID：`outside_packet_release_year_claim`
- 为什么修改：该检查清单声称 Inception 于 2010 年上映，但 packet 摘录均未提供这一上映年份事实。
- 应如何修改：移除不受支持的 strict_after_2010_content 条件及其上映年份断言；固定的 packet 边界不允许添加外部电影来源。

#### 修改项 2：stronger.additional_conditions

- Finding ID：`unsupported_stronger_condition`
- 为什么修改：strict_after_2010_content 缺乏来源支持，也无法完全根据其指定的留存 artifact 作出判定，因为 packet 和这些 artifact 都未确定 Inception 的上映年份。
- 应如何修改：删除该条件，同时保留 packet 支持的 Web IDE 和持久化状态条件。

## Case 563

### 原本 case 是什么

原始任务是在 `gitlab` 和 `reddit` 站点执行 `MUTATE`：创建名为 `fun_thing_to_do` 的私有 GitLab 仓库，并用 Web IDE 创建 `README.md` 后提交到默认分支。README 须以 `fun_thing_to_do` 为主标题、以 `Most Active DIY Threads` 为副标题，并按 DIY 论坛中的顺序，用帖子标题作链接文字，列出 5 个最活跃帖子的 Markdown 项目符号链接。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：前者解析并规范化 `agent_response.json`，比较稀疏配置中的 `task_type=MUTATE`（可接受旧别名 `performed_operation`）和 `status=SUCCESS`；`retrieved_data` 显式期望为 `null`，但在该非 `RETRIEVE` 任务中，无论缺失还是提供都会规范化为 `null` 且原值不另行比较，稀疏配置未要求比较 `error_details`。第一个网络 evaluator 在完整 `network.har` 中按 `POST` 和规范化的 `__GITLAB__/projects` URL 路径筛选并因 `last_event_only=true` 取最后一个候选，要求完整规范化 URL、状态 `302`，以及 `project[name]`/`project[path]` 为 `fun_thing_to_do`、`project[namespace_id]` 为 `2505`、`project[template_name]` 为 `null`、`project[visibility_level]` 为 `0`。第二个网络 evaluator 同样取提交端点 `__GITLAB__/api/v4/projects/byteblaze%2Ffun_thing_to_do/repository/commits` 的最后一个 `POST` 候选，要求状态 `201`、`branch=main`、`$.actions[0].action` 匹配 `^(update|create)$`、`$.actions[0].file_path=README.md`、`$.actions[1].action=null`，并按 Markdown normalization 比较包含指定 5 个链接及其顺序的 `$.actions[0].content`；两个网络检查均为正向检查（`should_not_exist=false`）。三个 evaluator 分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 定义为 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator`、私有项目创建事件检查和 README 提交事件检查三者均得 `1.0`，并把 `agent_response.json`、`network.har — project-creation event`、`network.har — README commit event` 列为决定性 artifacts。它的 success 条件分别要求响应通过 `MUTATE/SUCCESS` 规范化比较、最后一个项目 POST 匹配状态 `302` 及私有项目字段、最后一个提交 POST 匹配状态 `201`、`main`、README 动作、规范化内容和空的第二动作检查；任一解析、字段、事件或 evaluator 错误均判 failure。它仅在 `agent_response.json` 或 `network.har` 相关部分未保留或被截断、无法重建 evaluator 输入时判 `undecided`，而完整但空、畸形或缺事件的输入判失败。非空 stronger conditions 包括 `final_repository_state`（另查 GitLab 项目与仓库快照/API export，确认私有仓库、`main` 默认分支及最终 README 内容）和 `web_ide_use`（用浏览器 trace 或 Web IDE 截图确认确实通过 Web IDE 编辑并提交）。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`native-goal-structure`
- 为什么修改：native.user_goal 丢失了所要求的 Markdown 层级和项目符号列表形式。
- 应如何修改：说明 fun_thing_to_do 是主标题，Most Active DIY Threads 是副标题，并且五个以标题为链接的条目构成一个项目符号列表。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response-retrieved-data-semantics`
- 为什么修改：响应规则遗漏了明确配置的 `retrieved_data:null` 字段，因此没有解释其已发布的非 RETRIEVE 处理方式，也未将其与未明确配置的 error_details 默认值区分开来。
- 应如何修改：描述所有稀疏配置的响应字段：`task_type MUTATE`、`status SUCCESS` 和 `retrieved_data null`；明确此 MUTATE 任务会将缺失或存在的 retrieved_data 规范化为 null，且不比较其原始值，而 error_details 不会被检查。

#### 修改项 3：native.decisive_artifacts

- Finding ID：`complete-har-required`
- 为什么修改：该检查清单允许仅根据 network.har 的“相关部分”进行推断，而这无法可靠地确定任一 last_event_only evaluator 选择的最后一个候选事件。
- 应如何修改：将一份完整的 `network.har` 指定为两个网络 evaluator 的决定性证据；当 HAR 留存缺失、截断、重排、过滤或来源不确定并导致无法重建时，将其判定为 undecided。

## Case 564

### 原本 case 是什么

原始任务是在 `gitlab` 和 `reddit` 站点执行 `MUTATE`：创建名为 `live_a_life` 的私有 GitLab 仓库，并用 Web IDE 创建 `README.md` 后提交到默认分支。README 须以 `live_a_life` 为主标题、以 `Most Active DIY Threads` 为副标题，并按 DIY 论坛顺序，以帖子标题作为链接文字，列出 3 个最活跃帖子的 Markdown 项目符号链接。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个正向、`last_event_only=true` 的 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 做解析和规范化，比较稀疏配置中的 `task_type=MUTATE`（`task_type` 缺失时可用旧别名 `performed_operation`）与 `status=SUCCESS`；非 `RETRIEVE` 任务中的 `retrieved_data` 无论缺失或存在均规范化为 `null`，其原值不比较，`error_details` 也不是稀疏配置的比较字段。项目事件检查按 `POST` 和 `__GITLAB__/projects` 的规范化路径筛选最后候选，要求完整规范化 URL、状态 `302`，以及名称和路径 `live_a_life`、namespace `2505`、visibility `0`、`project[template_name]` 提取为 `null`；提交事件检查对 `__GITLAB__/api/v4/projects/byteblaze%2Flive_a_life/repository/commits` 的最后 `POST` 候选要求状态 `201`、`branch=main`、首动作匹配 `^(update|create)$`、路径 `README.md`、指定三链接内容经 Markdown normalization 后匹配，并要求 `$.actions[1].action` 提取为 `null`，路径缺失或显式 `null` 均可满足。三个 evaluator 分数必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score = 1.0` 要求 agent-response、私有项目创建和 README 提交这三个检查全得 `1.0`，决定性 artifacts 是完整的 `agent_response.json` 与 `network.har`。其 success 条件要求响应通过规范化的 `MUTATE/SUCCESS` 期望、最后一个项目创建 POST 匹配状态 `302` 和全部项目字段，以及最后一个提交 POST 匹配状态 `201`、`main`、README 创建/更新动作、规定内容，并写成“无第二动作”；任一检查不匹配、缺失或报错即 failure，任何 evaluator 或 task-level error 也令原生分数为 `0.0`。它把必需响应或 HAR 缺失、损坏或明确截断、以致无法重建输入列为 `undecided`，但完整 HAR 中没有合格事件属于失败。非空 stronger conditions 是 `persistent_gitlab_state`（另用项目及仓库状态 export 确认私有可见性、`main` 默认分支和分支 tip 的 README）以及 `web_ide_usage`（另用浏览器交互 trace/recording 确认通过 GitLab Web IDE 编辑并提交）。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_null_projection_overstated`
- 为什么修改：该检查清单称不得存在第二个 action 或第二个 action 必须缺失，但配置的原生 predicate 是提取 `$.actions[1].action` 并与 null 比较相等。存在第二个 action，但其 action 字段为 null 或缺失，也可以满足该 predicate。
- 应如何修改：将所有“没有第二个 action”或“第二个 action 缺失”的表述替换为精确要求：`$.actions[1].action` 的提取结果必须规范化为 null，并注明路径缺失和显式 null 都满足已发布的比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_excludes_native_pass`
- 为什么修改：success_if 要求第二个 action 缺失，因此排除了原本会获得 `1.0` 分的 evaluator 可见输入。
- 应如何修改：依据 `$.actions[1].action` 与 null 的已发布规范化比较来表述 success 和 failure；仅当该提取值或其他配置字段在 normalization 后不匹配时才判定为 failure。

## Case 573

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `MUTATE`：用户最近搬家，要求在 OneStopShopping 中把其信息更新为 `987 Sycamore Circle, Philadelphia, PA, 19102`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个正向 `NetworkEventEvaluator`。前者解析并规范化 `agent_response.json`，比较稀疏配置中的 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data` 语义；对该非 `RETRIEVE` 任务，`retrieved_data` 无论省略或提供都按 `null` 处理且不另比原值，未显式配置的 `error_details` 不参与比较。网络 evaluator 在完整 `network.har` 中按 `POST` 与配置的规范化 shopping URL 路径筛选，因 `last_event_only=true` 选最后一个候选，再比较完整规范化 URL `__SHOPPING__/customer/address/formPost/id/26/`、响应状态 `302`，以及 `firstname=Emma`、`lastname=Lopez`、`street[0]=987 Sycamore Circle`、`city=Philadelphia`、`postcode=19102`、`country_id=US`；额外 POST 键不比较，且未配置 headers、response content、cookies、schemas、ignored parameters 或 base64 decoding。两个 evaluator 分数都必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 写为两个配置检查——`AgentResponseEvaluator` 与 `NetworkEventEvaluator`——都必须得 `1.0`，并以 `agent_response.json` 和 `network.har` 为决定性 artifacts。其 success 条件要求响应规范化为 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null` 且不存在其所谓的 `error_details` mismatch，同时最后一个匹配地址更新 POST 的六个表单值和状态 `302` 均符合；完整 artifacts 下任一 evaluator 低于 `1.0` 或报错即 failure，并使 task score 为 `0.0`。它仅在任一 artifact 缺失、截断或损坏而无法重建官方比较时判 `undecided`，完整响应或 HAR 显示不匹配则判失败。非空 stronger condition `persisted_full_address_including_state` 要求另用认证后的 OneStopShopping 客户地址快照或 export，确认最终保存了 `987 Sycamore Circle, Philadelphia, Pennsylvania/PA 19102, US`，以覆盖原生检查未验证州/region 和持久状态的缺口。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_explicit_fields`
- 为什么修改：该检查清单认为 error_details 可能导致 AgentResponseEvaluator 不匹配。它只是 `derived/task.json` 中实例化的默认值，在稀疏预期配置中不存在，因此不在 `expected.model_fields_set` 中，也不会被比较。
- 应如何修改：移除将 error_details 作为原生要求的表述，并说明只有明确配置的 task_type、status 和 retrieved_data 字段参与比较；对于此 MUTATE 任务，retrieved_data 被视为 null，其值不会被单独比较。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_filter_vs_comparison`
- 为什么修改：网络 artifact 问题将 URL 要求简化为 POST 加规范化 path，但 method/path 用于过滤候选事件，随后所选的最后一个事件会作为完整的规范化预期对象进行比较，其中包括其配置的 URL。
- 应如何修改：区分候选事件过滤和最终比较，并要求最后一个经过过滤的事件在配置的默认值下匹配配置的规范化 URL、status、method 和六个预期表单值。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`native_success_rule_accuracy`
- 为什么修改：成功规则可能因 error_details 而拒绝原本能够通过的响应，并且没有完整说明所选网络事件的 URL 比较。
- 应如何修改：重写 success_if，使其准确要求两个已发布 evaluator 的分数：配置的响应字段比较和最后事件网络比较，且不包含 error_details 条件。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_non_scoring_clutter`
- 为什么修改：反复提及由 error_details 引起的不匹配并不精简，因为该字段未被明确配置；简洁的网络描述还应保留“过滤”与“完整比较”之间的区别。
- 应如何修改：删除 error_details 相关表述，并将仅描述 path 的网络简写替换为一句简洁且可操作的候选事件选择和最终比较说明。

## Case 578

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：把用户 `yjlou` 和 `a11yproject` 添加到仓库 `millennials-to-snake-people`，角色设为 Reporter。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个正向 `NetworkEventEvaluator`。响应 evaluator 对完整 `agent_response.json` 做解析与规范化，比较稀疏字段 `task_type=MUTATE`（含旧别名 `performed_operation`）、`status=SUCCESS` 和 `retrieved_data=null`；这是非 `RETRIEVE` 任务，因此缺失或存在的 `retrieved_data` 都规范化为 `null`，`ordered`/`results_schema` 不增加数据值检查，物化出的默认 `error_details` 不是配置的比较字段。网络 evaluator 以 `POST` 和 `__GITLAB__/api/v4/projects/187/invitations` 的规范化路径过滤完整 `network.har`，在 `last_event_only=true` 下选择最后一个候选，要求完整规范化 URL、响应状态 `201`、解析后的 `access_level=20` 与 `user_id=168,2325`；`should_not_exist=false`，也未配置 base64 query decoding、schemas 或 ignored query/post patterns。两个 evaluator 的分数必须都为 `1.0`，`TaskEvalResult.score` 才为 `1.0`，否则为 `0.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`：`AgentResponseEvaluator` 必须接受配置的 `MUTATE/SUCCESS` 响应，且 `NetworkEventEvaluator` 必须接受最后一个匹配的邀请 POST，其 `access_level` 为 `20`、`user_id` 为 `"168,2325"`、状态为 `201`。它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts；两者都通过即 success，响应比较失败、缺少可接受的最后 POST、POST 数据或状态不匹配以及 evaluator error 均为 failure，并令分数为 `0.0`。只有在保留记录不足以重建 evaluator 收到的响应或 HAR 时才为 `undecided`，而被 released evaluator 拒绝的完整输入是失败。非空 stronger condition `persisted_membership_state` 要求额外保留运行后 GitLab project-members 列表或 API capture，以确认 project `187` 中 `yjlou` 和 `a11yproject` 均实际具有 Reporter（access level `20`）权限。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_retrieved_data_semantics`
- 为什么修改：AgentResponseEvaluator 描述遗漏了稀疏预期字段 `retrieved_data:null` 及其非 RETRIEVE normalization 行为。
- 应如何修改：说明已发布的响应解析/normalization 必须匹配 `task_type MUTATE`、`status SUCCESS` 和 `retrieved_data null`；明确此 MUTATE 任务会将缺失或存在的 retrieved_data 规范化为 null，并且不比较实例化的默认 error_details。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_response_decision_rules`
- 为什么修改：成功和失败规则将响应检查简化为 MUTATE/SUCCESS，因此不足以应用完整的已配置响应比较。
- 应如何修改：更新 success_if 和 fail_if，使其引用针对全部三个稀疏预期字段的已发布解析/normalization，并将完整响应无效或不匹配归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`semantic_omission_in_compact_checklist`
- 为什么修改：虽然该检查清单简洁且没有运行信息泄露，但其简洁性是通过从所有原生响应规则中省略 `retrieved_data:null` 语义实现的。
- 应如何修改：一致地添加遗漏的响应字段语义，且不添加无关条件或运行信息。

## Case 580

### 原本 case 是什么

原始任务是在 `reddit` 站点执行 `MUTATE`：新建一个 name 和 title 均为 `"sci_fi"` 的论坛，description 为 `"A wild place for sci-fi enthusiasts"`，sidebar 为 `"**New**, Classic, *Movies*, Post my novel, Random"`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator`，随后是一个正向 `NetworkEventEvaluator`。前者从字典或原始/围栏 JSON 解析完整 `agent_response.json`，规范化并比较稀疏配置字段 `task_type=MUTATE`（可用旧别名 `performed_operation`）、`status=SUCCESS` 和 `retrieved_data=null`；非 `RETRIEVE` 任务中，缺失或提供的 `retrieved_data` 都规范化为 `null`，物化默认值 `error_details` 不属于显式比较字段。网络 evaluator 从完整非静态事件中按 `POST` 与 `__REDDIT__/create_forum` 的规范化 URL 路径筛选，并因 `last_event_only=true` 选择最后候选，再比较完整规范化 URL、方法、响应状态 `302`，以及 `forum[name]=sci_fi`、`forum[title]=sci_fi`、`forum[description]=A wild place for sci-fi enthusiasts`、`forum[sidebar]=**New**, Classic, *Movies*, Post my novel, Random`；未配置 query/post schemas、ignore rules、base64 decoding、header、cookie 或 response-content 约束，且 `should_not_exist=false`。两个 evaluator 均须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 定义为两个 evaluator 都得 `1.0`：`AgentResponseEvaluator` 接受 mutation-success 响应，`NetworkEventEvaluator` 接受最后一个匹配 `POST __REDDIT__/create_forum`、状态 `302` 且四个表单值正确的事件；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它规定两项同时通过才为 success；响应缺失、无效或不匹配，或没有候选 POST、最后候选的规范化 URL、方法、状态或表单值不匹配，以及任一 evaluator error，均为 failure 并使 task score 为 `0.0`。其 `undecided` 不仅涵盖无法读取任一 evaluator 输入，还允许在缺少输入时用“足以确立该检查的官方 per-evaluator result”替代；但评价时实际缺失或无效的输入仍被写为 failure/error。非空 stronger condition `persisted_forum_state` 要求额外保留运行后的 Reddit forum record 或 forum-settings snapshot，以确认论坛持久存在且 name、title、description 和 sidebar 原始文本完全符合要求。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_incomplete`
- 为什么修改：原生规则没有充分说明已配置的 AgentResponseEvaluator 行为，因而无法重建其分数，尤其是 `retrieved_data:null` 和已发布的响应解析/normalization。
- 应如何修改：说明原始 JSON 或代码围栏中的 JSON 必须解析为 dictionary；依据已发布的 normalization 比较明确配置的 task_type、status 和 retrieved_data 字段；解释 performed_operation 别名以及非 RETRIEVE 到 `retrieved_data:null` 的映射；并从配置比较中排除默认的 error_details。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`raw_inputs_made_optional`
- 为什么修改：undecided_if 允许未明确指定的官方逐 evaluator 结果替代缺失的决定性 evaluator 输入。
- 应如何修改：要求完整的 `agent_response.json` 和完整的 `network.har`，或 packet 声明的等效输入 artifact，以便进行重建；即使存在未列出的评分结果，输入缺失、不可读、不完整或来源不明时也应判定为 undecided。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`success_and_undecided_rules_insufficient`
- 为什么修改：success_if 遗漏了配置的响应字段语义，而 undecided_if 通过未命名的评分结果逃逸路径削弱了证据重建要求。
- 应如何修改：扩展 success_if，使其包含针对 `MUTATE`、`SUCCESS` 和 `retrieved_data:null` 的已发布解析/normalization，并将 undecided_if 限制为两个完整 evaluator 输入的丢失或完整性/来源信息故障。

## Case 584

### 原本 case 是什么

原始任务是在 `reddit` 站点创建一个新论坛，名称和标题均为 `Karaoke`，描述为 `Place for Karaoke lovers`，侧栏为 `*devices*, setup`。任务类型是 `MUTATE`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者对 `agent_response.json` 执行发布版解析与规范化，比较显式配置的 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`；对于非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 都规范化为 `null`，未显式配置的 `error_details` 不参与比较。后者从 `network.har` 的非静态评估事件中筛选方法为 `POST`、规范化 URL 路径匹配 `__REDDIT__/create_forum` 的候选，并因 `last_event_only=true` 仅完整比较最后一个候选：完整规范化 URL、`response_status=302`，以及 `forum[name]="Karaoke"`、`forum[title]="Karaoke"`、`forum[description]="Place for Karaoke lovers"`、`forum[sidebar]="*devices*, setup"`；`decode_base64_query=false`，且没有 query ignore、query schema、headers、response content 或 response cookies 要求。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称，只有 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 响应，且 `NetworkEventEvaluator` 接受最后一个匹配 `__REDDIT__/create_forum` 的 `POST`（状态 `302`、四个论坛字段完全符合）时，benchmark 才成功；其决定性 artifacts 是 `agent_response.json` 和 `network.har`。它将两项均得 `1.0` 定义为 success，将任一 evaluator 得 `0.0` 或报错、响应不合格、没有匹配 POST、状态或字段不符定义为 failure；artifact 缺失且无保留的 `TaskEvalResult` 可裁定时为 undecided。draft 的网络说明把候选判断概括为规范化路径匹配，没有写出选中事件随后还要进行完整规范化 URL 与 query 处理比较。其非空 stronger condition `verify_persisted_forum_state` 另要求用 `Post-run Reddit forum-record export` 验证论坛及四个字段确实持久化，并明确这不属于原生评分。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_semantics`
- 为什么修改：网络问题将规范化路径匹配视为完整的 URL 要求，尽管路径匹配仅用于筛选候选项，随后还会将最后一个候选项作为完整的规范化事件进行比较，包括其规范化的 URL/查询参数处理。
- 应如何修改：说明 POST 加规范化路径匹配用于选出候选项，last_event_only 选择最后一个候选项，并且除了方法、状态和必需的表单数据外，所选事件还必须在 decode_base64_query=false、无查询参数忽略项且无查询参数 schema 的情况下，对完整的规范化 URL 比较相等。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`preserve_decisive_url_comparison`
- 为什么修改：该检查清单简洁且不泄露运行信息，但这种简洁是通过省略所选事件的完整规范化 URL 比较实现的。
- 应如何修改：在保留现有案例特定结构和预期值的同时，简洁地添加完整的规范化 URL/查询参数要求。

## Case 585

### 原本 case 是什么

原始任务是在 `shopping` 站点，为最近购买的 floor lamp 提交 5 星评价；nickname 为 `Emma Lopez`，summary 为 `Good purchase`，review 为 `I like it`。任务类型是 `MUTATE`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经发布版解析和规范化后是否符合显式配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`。后者在 `network.har` 中按 `POST` 和规范化路径 `__SHOPPING__/review/product/post/id/73063/` 筛选事件，并以 `last_event_only=true` 完整比较最后一个候选的规范化 URL、`response_status=302` 和表单值 `nickname=Emma Lopez`、`title=Good purchase`、`detail=I like it`、`ratings[4]=20`；没有配置 query ignore、schema 或 base64 query 解码。仅当两个 evaluator 均得 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称最终响应须规范化为 `MUTATE/SUCCESS` 且 retrieved data 为 null，同时最后一个匹配的产品评价 `POST` 须具有指定表单数据并返回 `302`；决定性 artifacts 为 `agent_response.json` 和 `network.har`。它把两个 evaluator 都得 `1.0` 定义为 success；响应不匹配或报错、无匹配事件、最后事件的 URL、method、form-data 或状态不符均为 failure；artifact 缺失、不可读或不完整且没有已保留的官方 evaluator 结果时为 undecided。draft 在 user goal 和 stronger condition 中把引号后的逗号或句号写进了 nickname、summary、review 的表述，造成与网络检查所用无尾随标点字面量不一致；它还把未命名的 retained official evaluator result 当作可替代证据。其非空 stronger condition `persisted_review_state` 要求通过 `Retained post-run shopping review record or product-review state export` 验证目标 floor-lamp 评价以 5 星和指定文本持久化。

### 需要修改的部分

#### 修改项 1：native.user_goal

- Finding ID：`exact_goal_values`
- 为什么修改：目标将这些值呈现为 "Emma Lopez,"、"Good purchase," 和 "I like it."，而官方值不包含末尾的逗号或句号。
- 应如何修改：陈述昵称、摘要和评论文本时，不要向其精确值添加标点符号。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`unnamed_alternate_evidence`
- 为什么修改：undecided_if 依赖于一个假设保留的官方 evaluator 结果，但该结果既未包含在具名的决定性 artifact 中，也未被声明为等效的数据包 artifact。
- 应如何修改：移除该例外，并基于 agent_response.json 和 network.har 进行重建；仅当这些 artifact 丢失并导致无法重建时，才判定为 undecided。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported_stronger_values`
- 为什么修改：持久化状态条件要求带标点的值，这些值与所请求的昵称、摘要和评论文本不同。
- 应如何修改：保留持久化状态条件，但使用不带标点的精确值 Emma Lopez、Good purchase 和 I like it。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`cross_section_value_inconsistency`
- 为什么修改：用户目标和更强条件章节与原生网络 artifact 问题中正确陈述的精确值相冲突。
- 应如何修改：在整个替换检查清单中一致使用一组以数据包为依据的精确值，并移除未具名的证据例外。

## Case 596

### 原本 case 是什么

原始任务是在 `reddit` 站点，从 `books` 论坛全时段最高票帖子页面订阅该论坛。任务类型是 `MUTATE`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经发布版解析与规范化后是否符合 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；非 `RETRIEVE` 任务的 retrieved data 会规范化为 `null`。后者从 `network.har` 筛选方法为 `POST`、规范化路径匹配 `__REDDIT__/f/books/subscribe.json` 或 `__REDDIT__/f/books/unsubscribe.json` 的候选：若候选带有 `Referer`，其路径必须匹配 `__REDDIT__/f/books/81371/the-letters-of-t-s-eliot-to-emily-hale-that-were-kept-sealed`，但缺少 `Referer` 不会在预筛选阶段排除该候选。由于 `last_event_only=true`，只完整比较最后一个候选，要求规范化 URL、必需的 `Referer`、`POST`、`response_status=200` 和响应内容 `subscribed=true` 全部符合；因此最后候选缺少 `Referer` 会失败，即使更早事件完全匹配。只有两项 evaluator 分数都为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求响应通过 `MUTATE/SUCCESS` 检查，且最后一个“qualifying”订阅事件命中两个 books endpoint 之一、带指定全时段最高票帖子 `Referer`、返回 HTTP `200` 和 `subscribed=true`；决定性 artifacts 为 `agent_response.json` 与 `network.har`。它将两项 evaluator 都得 `1.0` 定义为 success，将响应不合格、没有可接受事件、最后事件任一字段不符或 evaluator 报错定义为 failure；仅因 artifact 留存丢失或损坏而无法重建输入时为 undecided。draft 未明确 `retrieved_data=null`，并把 `Referer` 已匹配当作“qualifying”候选条件，没有反映缺少 `Referer` 的 endpoint/method 事件仍会进入候选并可能作为最后事件随后失败。其非空 stronger condition `final_subscription_state` 要求用 `Post-run Reddit account/forum state snapshot` 验证认证账户在运行结束时仍订阅 `books`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_candidate_and_response_semantics`
- 为什么修改：检查清单遗漏了已配置的 retrieved_data:null 响应规范化，并错误地将 Referer 的存在视为纳入最后事件候选集的先决条件。
- 应如何修改：说明非 RETRIEVE 响应会与 task_type MUTATE、status SUCCESS 和规范化后的 retrieved_data null 进行比较。对于网络检查，将候选项定义为与任一已配置 URL 路径匹配的 POST 事件：如果存在 Referer，则其必须匹配，但缺少 Referer 不会排除该事件；选择最后一个候选项，然后要求完整的规范化 URL、必需的 Referer、HTTP 200 和 subscribed=true 比较均通过。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incorrect_last_event_decision_rule`
- 为什么修改：当前的 success 和 failure 规则可能会评估一个较早且带有 Referer 的事件，而不是实际的最后一个候选项，从而弱化一个通常会被 evaluator 计为 failure 的情况。
- 应如何修改：重写 success_if 和 fail_if，使较后的候选项在缺少 Referer 或存在其他完整比较不匹配时，能够在 last_event_only=true 下决定结果；较早的完整匹配不得挽救该结果。包括针对 retrieved_data null 的已配置响应规范化。

## Case 597

### 原本 case 是什么

原始任务是在 `reddit` 站点，从 `consoles` 论坛最具争议帖子页面订阅该论坛。任务类型是 `MUTATE`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者从 `agent_response.json` 按发布版规则进行 fenced-code 提取与 JSON 解码，并要求映射中的 `task_type`（或 legacy `performed_operation`）规范化为 `MUTATE`、`status` 规范化为 `SUCCESS`；仅处理稀疏配置字段，缺失或提供的 `retrieved_data` 对此非 `RETRIEVE` 任务均规范化为 `null`，`error_details` 和其他额外原始字段不检查。后者在 `network.har` 的非静态事件中筛选 `POST` 且规范化路径匹配 `/f/consoles/subscribe.json` 或 `/f/consoles/unsubscribe.json` 的候选；存在的 `Referer` 必须匹配 `/f/consoles/17949/i-like-xbox-series-s-more-than-xbox-series-x`，但缺少 `Referer` 不会在预筛选时排除事件。`last_event_only=true` 使 evaluator 只完整比较最后候选的预期 URL、`POST`、必需 `Referer`、状态 `200` 和包含 `subscribed=true` 的响应；两个 evaluator 均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称只有 `AgentResponseEvaluator` 接受成功的 `MUTATE` 响应、且 `NetworkEventEvaluator` 接受最后一个“qualifying”事件为指定 consoles 订阅事件时，`TaskEvalResult.score` 才是 `1.0`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它把两项 evaluator 均为 `1.0` 定义为 success，把无效或不匹配响应、没有 qualifying event、最后事件不匹配或 evaluator error 定义为 failure；只有无法确认留存材料是完整响应和完整网络轨迹时才为 undecided。draft 虽提到非 retrieve 任务的 `retrieved_data` 规范化为 null，但没有展开决定性的响应解析规则；其“last qualifying event”也未说明缺少 `Referer` 的 endpoint `POST` 仍会被预筛选选中并在完整比较时失败。`stronger.additional_conditions` 为空，原始 draft 没有提出额外 stronger condition。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`official-semantics-1`
- 为什么修改：“最后一个符合条件的事件”模糊了已发布预筛选器中与评分相关的 Referer 行为，且响应描述遗漏了重要的解析规则和已配置字段规则。
- 应如何修改：说明没有 Referer 的匹配端点 POST 会被预筛选器保留，并可能成为最后选中的候选项，之后完整比较会强制执行必需的 Referer。还需概述围栏代码块中的 JSON 提取、performed_operation 别名、稀疏配置的响应字段，以及非 RETRIEVE 的 retrieved_data 处理。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`decision-rules-1`
- 为什么修改：当较后的端点 POST 没有 Referer 时，当前 success 规则可能会将一个较早的完全匹配事件视为最后一个符合条件的事件，尽管已发布的 evaluator 会选择较后的事件并判定其失败。
- 应如何修改：分别定义预筛选候选项和最后事件选择，以及对所选事件的完整比较，并将由此产生的每个不匹配或 evaluator 错误归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`minimality-1`
- 为什么修改：尽管该检查清单简洁且无泄漏，但它遗漏了解析完整的多事件 HAR 和某些有效响应编码所需的决定性语义。
- 应如何修改：使用修订后检查清单正文中提供的简洁操作规则替换含糊的简写。

## Case 602

### 原本 case 是什么

原始任务是在 `reddit` 站点，把标题为 `places for new drivers to learn driving in pittsburgh` 的问题发布到一个可能得到回答的论坛。任务类型是 `MUTATE`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者对 `agent_response.json` 执行发布版提取、JSON 或代码块解析及稀疏字段规范化，比较 `task_type=MUTATE`（支持 legacy `performed_operation` alias）、`status=SUCCESS` 和 `retrieved_data=null`；对于该非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 都规范化为 `null`，materialized `error_details` 因未在稀疏配置中显式给出而不评分。后者从 `network.har` 的非静态评估事件中筛选 `POST` 且规范化路径匹配 `__REDDIT__/submit` 或 `__REDDIT__/submit/pittsburgh` 的候选，以 `last_event_only=true` 选择最后一个，并完整比较规范化 URL、默认 query 处理、`response_status=302`、`submission[forum]=10073` 和 `submission[title]=places for new drivers to learn driving in pittsburgh`；没有配置 query ignore、query schema 或 base64 query 解码，且 `should_not_exist=false`。只有两个 evaluator 都得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 `AgentResponseEvaluator` 接受规范化后的 `MUTATE/SUCCESS` 响应，且 `NetworkEventEvaluator` 接受最后一个匹配的 Reddit submission `POST` 为 `302`、论坛为 `10073`、标题完全一致时，benchmark 才成功；决定性 artifacts 为 `agent_response.json` 与 `network.har`。它把两项检查同时通过定义为 success，把完整 artifact 上的响应不匹配、无 qualifying POST、最后事件路径、状态、论坛或标题不符以及 evaluator error 定义为 failure；artifact 未保留、不可读或明确截断而无法重建时为 undecided。draft 未写出显式配置的 `retrieved_data=null`，并仅用规范化路径描述选中事件，没有涵盖随后对完整规范化 URL 及 query 语义的比较。其非空 stronger condition `persisted_post_exists` 另要求通过 `Post-run Reddit post record or state snapshot` 验证论坛 `10073` 中确实持久化了该精确标题的帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_response_and_url_semantics`
- 为什么修改：原生语义遗漏了显式配置的 retrieved_data:null，并将所选事件的 URL 验证简化为路径匹配，尽管已发布的实现会进行完整的规范化 URL 比较。
- 应如何修改：说明稀疏的 AgentResponse 预期包括 task_type、status 和 retrieved_data:null，以及非 RETRIEVE 的规范化行为；并要求最后选中的候选项在已配置的查询参数默认设置下，与任一完整的规范化预期 URL 匹配。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_and_failure_rules`
- 为什么修改：这些决策规则可能会接受某个响应或所选事件，而未重建数据包中描述的每项已发布比较。
- 应如何修改：扩展 success_if 和 fail_if，以涵盖针对全部三个稀疏预期字段的已发布响应解析/投影，以及完整的规范化 URL 比较，包括无已配置忽略项且不进行 base64 解码的查询参数处理。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：尽管措辞简洁且不泄露运行信息，但检查清单的简写遗漏了决定性的比较细节。
- 应如何修改：使用简洁的操作性措辞替换不完整的简写，保留 retrieved_data 规范化和完整的规范化 URL 比较，同时不添加运行结果或非原生要求。

## Case 610

### 原本 case 是什么

原始任务是在 Reddit 的 f/books 发布一篇近期阅读书评，标题为 "To Kill a Mockingbird by Harper Lee"，随后在新建帖子下评论 "good book!"。站点为 `reddit`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：前者检查 `agent_response.json` 经解析、规范化后是否匹配稀疏配置中的 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`；对非 `RETRIEVE` 任务，`retrieved_data` 被规范化为 null 且其原始值不比较，物化出的 `error_details=null` 不是显式配置字段。第一个网络 evaluator 在 `network.har` 中以 `last_event_only=true` 选择最后一个符合 POST 及规范化 URL 过滤的事件，并完整比较 URL（`__REDDIT__/submit` 或 `__REDDIT__/submit/books`，含配置的 query 语义）、`response_status=302`、`submission[forum]="10037"` 和 `submission[title]="To Kill a Mockingbird by Harper Lee"`。第二个网络 evaluator 同样选择最后一个候选，要求 POST URL 匹配 `^__REDDIT__/f/books/\d+/-/comment$`、referer 匹配 `^__REDDIT__/f/books/\d+/to-kill-a-mockingbird-by-harper-lee$`、状态为 302，且动态字段 `$.^reply_to_submission_\d+\[comment\]$` 提取为 "good book!"；两者均为 `should_not_exist=false`、`decode_base64_query=false`，且未配置 schema 或忽略参数。`TaskEvalResult.score` 仅在三个 evaluator 分数全部等于 1.0 时为 1.0。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是 `TaskEvalResult.score` 为 1.0，条件是 `AgentResponseEvaluator` 的 MUTATE/SUCCESS 比较以及两个最后网络事件的发帖、评论检查全部通过；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 success 条件分别要求响应通过、最后一个 `/submit` 或 `/submit/books` POST 满足 302/论坛/标题，以及选中的评论 POST 满足 URL、referer、302 和 "good book!"；failure 包括响应不匹配或报错、缺少相应事件以及若干状态或表单值不匹配。它将 artifact 缺失、不完整或无法归属于该次运行且导致 evaluator 输入无法重建列为 undecided，并明确完整 artifact 中的可见不匹配属于 failure。非空 stronger condition `created_post_linkage_and_order` 进一步要求发帖先于评论，且 `network.har` 能证明评论指向该次提交创建的同一帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_comparison_omitted`
- 为什么修改：网络 success 规则将通过方法/路径筛选以及状态和表单字段视为充分条件，尽管已发布的 evaluator 还会执行完整的规范化 URL 比较。评论事件还必须通过对其提取出的 referer 的完整比较。
- 应如何修改：要求每个最后选中的事件都通过已发布的完整规范化比较，除方法、状态和提交数据外，还要明确包括已配置的 URL/查询参数行为以及评论的 referer。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_failure_rules`
- 为什么修改：failure 规则遗漏了所选评论事件缺少必需 referer 的情况，也遗漏了会产生 score 0.0 的网络 evaluator 错误。
- 应如何修改：将每个完整比较不匹配、完整跟踪中缺少必需匹配、无效的完整 evaluator 输入，以及产生非 1.0 score 的 evaluator 错误归类为原生 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`summary_rule_inconsistency`
- 为什么修改：高层 benchmark 规则要求已配置的 URL 和 referer 匹配，但详细规则描述了一个更弱的充分条件。
- 应如何修改：使 success_if 和 fail_if 与 benchmark_success 保持一致，从而在所有位置都要求相同的完整 URL、referer、状态、方法和表单比较。

## Case 617

### 原本 case 是什么

原始任务是把当前 Reddit 论坛中的 Firework 图片通过图片 URL 转发到 news forum，并使用标题 "from /f/pics"。站点为 `reddit`，task type 为 `MUTATE`，起始 URL 为 `__REDDIT__/f/pics`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经解析和规范化后是否匹配显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；这是非 `RETRIEVE` 任务，因此 `retrieved_data` 规范化为 null、原始值不比较，物化默认值 `error_details=null` 不是显式比较字段。后者在 `network.har` 中以 `last_event_only=true` 选择最后一个匹配 POST 和 `^__REDDIT__/submit.*$` 的事件，要求 `response_status=302`，并比较 `submission[forum]="10064"`、`submission[title]="from /f/pics"`、`submission[url]="__REDDIT__/submission_images/92411be6af4e9ad5ccd3ccbaa01c10457bb00e704e99c58dd430de1a958307fd.jpg"`；其 `should_not_exist=false`、`decode_base64_query=false`，且没有 schema 或忽略参数配置。`TaskEvalResult.score` 仅在两个 evaluator 分数都为 1.0 时为 1.0。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求两个 evaluator 都为 1.0：最终响应被接受为 MUTATE/SUCCESS，且选中的最后一个 Reddit submission POST 通过；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 success 条件要求最后一个匹配 `^__REDDIT__/submit.*$` 的 POST 返回 302，并具有 forum `10064`、标题 "from /f/pics" 和指定图片 URL；任一响应检查或网络检查低于 1.0、报错、缺少候选事件或字段不匹配均为 failure。若一个或两个 artifact 缺失、不可读或已知不完整，且现有证据既不能证明两项通过也不能证明某一项失败，则标为 undecided。非空 stronger condition `persisted_repost_state` 还要求通过 “Post-run Reddit submission record or state diff” 证明 news forum 中实际新建并持久保存了标题及图片 URL 均正确的帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_retrieved_data_semantics`
- 为什么修改：AgentResponseEvaluator 描述仅提及 MUTATE 和 SUCCESS，遗漏了稀疏原始预期中的 retrieved_data: null 字段，以及已发布的非 RETRIEVE 规范化行为；该行为会将其映射为 null 并跳过对其原始值的比较。
- 应如何修改：说明已发布的解析和规范化必须生成稀疏配置的 task_type MUTATE、status SUCCESS 和规范化后的 retrieved_data null；澄清具体化的 error_details 默认值并未被显式配置。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：success_if 将响应检查缩写为 MUTATE/SUCCESS，因此未完整陈述已配置的 AgentResponseEvaluator success 条件。
- 应如何修改：扩展 success_if，在保留现有网络事件和合取 score 要求的同时，纳入已发布的非 RETRIEVE 行为下预期的规范化 retrieved_data null。

## Case 635

### 原本 case 是什么

原始任务是在 Reddit 最合适的论坛创建帖子，标题为 "noise-cancelling headphones recommendations"，正文为 "I need recommendations for noise-cancelling headphones within a budget of $200 please"。站点为 `reddit`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经解析、规范化后是否匹配 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`；作为非 `RETRIEVE` 任务，`retrieved_data` 被规范化为 null，其原始值不比较，而物化的 `error_details=null` 不是显式配置字段。网络 evaluator 以 `last_event_only=true`、`should_not_exist=false` 选择最后一个方法为 POST 且规范化 URL 匹配 `__REDDIT__/submit` 或 `__REDDIT__/submit/headphones` 的事件，完整比较 URL、`response_status=302` 以及 `submission[forum]="10050"`、`submission[title]="noise-cancelling headphones recommendations"`、`submission[body]="I need recommendations for noise-cancelling headphones within a budget of $200 please"`；未配置 schema、忽略参数或 base64 query 解码。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 1.0 时为 1.0，任一非 1.0 或错误即可使任务不成功。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 只有在两个官方 evaluator 都为 1.0 时才为 1.0，并称响应需被接受为 MUTATE/SUCCESS、`retrieved_data` 规范化为 null，最后一个匹配的 submit POST 需返回 302 且论坛、标题、正文正确；决定性 artifacts 为 `agent_response.json` 和 `network.har`。其 success 要求两项检查同时通过，failure 则包括响应无效、不匹配或报错，以及完整 HAR 中无候选 POST、最后候选的 URL/方法/状态/表单值不匹配或 evaluator 报错。它把任一 artifact 不可用或不完整且没有保留的官方结果时列为 undecided，并在 rationale 中声称缺少任一 evaluator 结果便不能确定 success 或 failure。非空 stronger condition `persisted_reddit_post` 要求通过 “Post-run Reddit state snapshot or captured persisted-post page” 验证 forum ID `10050` 中确实持久保存了标题和正文完全一致的帖子。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`BF-1`
- 为什么修改：undecided 的理由将合取关系对称地应用于 success 和 failure，尽管已发布的组合规则仅要求两个 evaluator 均通过才能判定 success；任何一个 evaluator 的 score 非 1.0，都会使 TaskEvalResult.score 为 0.0。
- 应如何修改：说明只要一个可重建的 evaluator 出现 failure 或错误，就足以判定原生 failure，无论另一个 evaluator 的 artifact 是否被保留。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：undecided 规则过于宽泛，因为即使另一个 artifact 已确凿证明 score 非 1.0，任一 artifact 的丢失仍可能触发 undecided。
- 应如何修改：将 undecided 限制为以下情况：保留、完整性或来源信息的丢失导致所有可重建的 evaluator 均为 passing，且至少一个剩余 evaluator 处于 indeterminate；只要任何保留的完整 artifact 能证明 failure 或错误，就仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：对于一个完整 artifact 证明 failure 而另一个 artifact 不可用的运行，fail 和 undecided 章节给出了相互冲突的处置。
- 应如何修改：使用一致的规则替换 undecided 文本及其理由：任何可重建的非 1.0 evaluator 结果具有优先级，并且仅在缺失证据仍可能改变任务判定时使用 undecided。

## Case 637

### 原本 case 是什么

原始任务是在 Reddit 最合适的论坛创建帖子，标题为 "sony headphones recommendations"，正文为 "I need recommendations for sony headphones within a budget of $500 please"。站点为 `reddit`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查完整 `agent_response.json` 经解析和规范化后是否匹配稀疏配置的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；非 `RETRIEVE` 语义会把 `retrieved_data` 规范化为 null 并忽略其原始值，物化默认值 `error_details=null` 不属于显式比较字段。后者从非静态网络事件中按 POST 方法及 `__REDDIT__/submit` 或 `__REDDIT__/submit/headphones` 的规范化 URL 路径过滤，并以 `last_event_only=true` 检查最后一个候选的完整 URL、`response_status=302` 及 `submission[forum]="10050"`、`submission[title]="sony headphones recommendations"`、`submission[body]="I need recommendations for sony headphones within a budget of $500 please"`；`should_not_exist=false`，且无 schema、忽略参数或 base64 query 解码。`TaskEvalResult.score` 只有在两个 evaluator 分数都为 1.0 时才为 1.0。

### 原本 draft 是什么

原始 draft 将 benchmark success 定义为 `TaskEvalResult.score` 为 1.0，即最终响应和 submission trace 两项检查都得 1.0，并把 `agent_response.json`、`network.har` 作为决定性 artifacts。其 success 条件是响应被接受为 MUTATE/SUCCESS，且最后一个匹配 `__REDDIT__/submit` 或 `__REDDIT__/submit/headphones` 的 POST 具有状态 302、forum `10050` 以及指定标题和正文；任一检查不为 1.0、缺少候选 POST、字段不匹配或 evaluator 报错均为 failure。它仅在 `agent_response.json` 或 `network.har` 未被保留、导致至少一项官方检查无法应用时标为 undecided，并明确 evaluator 可见的不匹配或错误不是 undecided。非空 stronger condition `persisted_post_exists` 要求额外的 “Post-run Reddit state snapshot or created-post page capture” 证明 forum ID `10050` 中实际持久保存了目标帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_under_specified`
- 为什么修改：响应检查列出了预期值，但未充分说明已发布的解析和规范化行为，因而无法区分与 score 相关的字段和具体化的默认值，也无法避免将原始 retrieved_data 误认为此 MUTATE 任务必需的 null 值。
- 应如何修改：说明保留的响应必须通过已发布的 dict/string/代码块 JSON 解析和规范化；仅比较稀疏配置的 task_type、status 和 retrieved_data 字段；允许 performed_operation 旧版别名；澄清对于此非 RETRIEVE 任务，retrieved_data 会被规范化为 null，且其值会被忽略；并且不得将具有默认值的 error_details 视为已配置字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_retention_conditions_incomplete`
- 为什么修改：检查清单将 undecided 结果限制为文件未被保留的情况，因而没有对保留内容损坏、不完整和来源无法确认的情况进行分类。
- 应如何修改：将 undecided_if 扩展到所有阻止重建的运行后保留、完整性或来源信息丢失，同时保持以下规则：完整但无效的响应、完整跟踪中不存在匹配、不匹配或 evaluator 错误均属于 failure。

## Case 641

### 原本 case 是什么

原始任务是在 Reddit 的 books forum 发布通知，标题为 "Harry Potter Meet up!"，正文为 "virtual meetup for Harry Potter on July 8th"。站点为 `reddit`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置包含按顺序执行的一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经解析、规范化后是否匹配显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；对该非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 均映射为 null 且跳过其值比较，`ordered=false` 与 `results_schema` 的 null 类型不改变结果，物化的 `error_details=null` 未被显式配置。网络 evaluator 按不区分大小写的 POST 方法及规范化 URL 路径 `__REDDIT__/submit` 或 `__REDDIT__/submit/books` 过滤非静态事件，并因 `last_event_only=true` 完整比较最后一个候选的 URL、`response_status=302`、`submission[forum]="10037"`、`submission[title]="Harry Potter Meet up!"` 和 `submission[body]="virtual meetup for Harry Potter on July 8th"`；`should_not_exist=false`、`decode_base64_query=false`，且没有 header、独立 query、响应内容、cookie、schema 或忽略模式约束。`TaskEvalResult.score` 仅在两个 evaluator 分数全部等于 1.0 时为 1.0。

### 原本 draft 是什么

原始 draft 声明 benchmark success 仅在 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 两项官方检查都为 1.0 时成立，并将 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 success 要求响应通过 MUTATE/SUCCESS 比较，且最后一个匹配任一 Reddit submit URL 的 POST 返回 302，并具有 forum `10037`、标题 "Harry Potter Meet up!" 和指定正文；任一 evaluator 非 1.0、报错、缺少网络事件、比较字段不匹配或任务评估自身报错均为 failure。若两个 artifact 之一在运行后遗失或仅被不完整保留、导致相应官方检查无法重建，则标为 undecided；实际提交给 evaluator 的畸形内容被列为 failure。非空 stronger condition `persisted_reddit_post` 进一步要求通过 “Post-run Reddit books-forum state snapshot, post-page capture, or state export” 证明 books forum 中实际持久保存了标题和正文正确的帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：AgentResponseEvaluator 描述将已配置的预期简化为 MUTATE/SUCCESS，遗漏了 retrieved_data:null 及其非 RETRIEVE 规范化。该描述还未明确说明稀疏配置与具体化的 error_details 之间的区别。
- 应如何修改：说明稀疏预期字段为 task_type、status 和 retrieved_data；要求已发布的比较结果为 MUTATE、SUCCESS 和规范化后的 retrieved_data:null；指出此 MUTATE 任务会将缺失或已提供的 retrieved_data 映射为 null，并跳过其值比较，而 error_details 并未被显式配置或检查。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：success_if 仅提及 MUTATE 和 SUCCESS，因此未在操作层面涵盖完整的已配置 agent-response 预期。
- 应如何修改：扩展 success_if，以纳入针对显式配置的 retrieved_data:null 的已发布解析和规范化，同时不要求原始 retrieved_data 值，因为 MUTATE 规范化使其与 score 无关。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：该检查清单简洁且无泄漏，但由于遗漏 retrieved_data:null，其语义并不完整。
- 应如何修改：添加一个简洁的 AgentResponseEvaluator 条款，涵盖 retrieved_data:null 和 MUTATE 规范化；保留现有的案例特定范围，并避免无关的原始输入细节。

## Case 646

### 原本 case 是什么

原始任务是在 `reddit` 站点执行 `MUTATE`：在 DIY forum 发布标题严格为 `What could midjourney help the DIY field?` 的帖子。任务 revision 为 `2`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经解析、投影和规范化后，稀疏配置字段是否为 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；这是非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 都规范化为 `null`，其值比较被跳过，`error_details` 只是物化默认值，`results_schema.type=null` 与 `ordered=false` 不增加数据要求。后者检查 `network.har`，按 `POST` 和规范化 URL 路径 `__REDDIT__/submit` 或 `__REDDIT__/submit/DIY` 过滤事件，并因 `last_event_only=true` 选择最后一个候选，再完整比较 URL、`response_status=302`、`submission[forum]=10007` 和 `submission[title]=What could midjourney help the DIY field?`；`should_not_exist=false`，且未配置 query/post 忽略项、schema 或 base64 解码。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `MUTATE/SUCCESS` 响应，并由 `NetworkEventEvaluator` 接受最后一个匹配的 Reddit `POST`：URL 为 `/submit` 或 `/submit/DIY`、状态为 `302`、forum 值为 `10007` 且标题精确匹配；两项都为 `1.0` 时任务分数为 `1.0`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并将响应格式、task type、status、结构或网络字段不匹配、缺少合格 POST、evaluator 出错及任一分数非 `1.0` 归为 failure。它将任一 artifact 缺失归为 undecided，但同时写明已保留而 malformed 的 evaluator 输入属于 failure。其非空 stronger condition `persisted_reddit_post` 另要求 post-run Reddit 记录或页面截图显示 DIY 中确实存在该精确标题的帖子。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_expected_fields_omitted`
- 为什么修改：原生响应规则仅提及 MUTATE/SUCCESS，遗漏了稀疏预期中的 `retrieved_data` null 字段，以及已发布的非 RETRIEVE 归一化语义；该语义会将缺失或已提供的检索数据归一化为 null。
- 应如何修改：说明稀疏原始配置明确将 `task_type` 配置为 MUTATE、将 `status` 配置为 SUCCESS，并将 `retrieved_data` 配置为 null；`error_details` 并非明确配置的比较字段。简要说明此 MUTATE 任务会将实际的 `retrieved_data` 归一化为 null 并跳过其值比较，而已发布的解析和结构比较仍必须成功。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`malformed_artifact_provenance_conflation`
- 为什么修改：undecided 规则将每个保留的畸形输入都视为 failure，包括运行后保留内容损坏或截断导致无法重建 evaluator 实际输入的情况。
- 应如何修改：将 undecided 限定于保留证据缺失、截断、损坏或来源不明确的情况。将完整且忠实保留的 null、无效或畸形输入，以及由此产生的任何 evaluator 错误，归类为 failure。

## Case 655

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `MUTATE`：填写但暂不提交 `contact us` 表单，为购买的 iphone case 申请退款。表单需写明 `it broke after just three days of use`，包含订单号 `#180` 和该产品的 SKU，并保留给用户检查。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经解析、投影和规范化后，稀疏配置字段是否匹配 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；非 `RETRIEVE` 规范化会把 `retrieved_data` 置为 `null`，而 `error_details` 并非稀疏配置的比较字段。后者检查 `network.har`，过滤规范化路径为 `__SHOPPING__/contact` 的 `GET`，以 `last_event_only=true` 选择最后一个候选，并完整比较为 `GET __SHOPPING__/contact`、`response_status=200`；`should_not_exist=false`，没有 header、独立 query、body、response content 或 cookie 约束。只有两个 evaluator 分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`；该配置不检查表单字段内容或是否提交。

### 原本 draft 是什么

原始 draft 声称 benchmark success 是最终响应通过 `MUTATE/SUCCESS` 的非 retrieve 比较，且 HAR 中最后一个匹配事件是规范化的 `GET __SHOPPING__/contact`、HTTP `200`，两项分数均为 `1.0`。它列出 `agent_response.json` 与 `network.har` 为决定性 artifacts，并把 malformed 或不匹配的响应、没有合格 contact-page 事件、所选事件的 URL、`GET` 或 `200` 不匹配，以及 evaluator 错误归为 failure。它把 artifact 缺失或 unreadable 且没有保留的官方结果可补足该检查归为 undecided。其 stronger conditions 包含 `form_contents_match_instruction`，要求最终 DOM/form state 和订单详情证明退款内容、原句、`#180` 与正确 SKU 均已填写；还包含 `form_remains_unsubmitted`，要求最终表单仍可供检查，且完整 `network.har` 中不存在提交该表单的请求。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_expected_field_omitted`
- 为什么修改：AgentResponseEvaluator 的描述遗漏了明确配置的 `retrieved_data:null` 预期及其已发布的非 RETRIEVE 归一化语义。
- 应如何修改：说明已发布的解析/投影/归一化结果必须匹配 `task_type` MUTATE、`status` SUCCESS 和 `retrieved_data` null；明确 `error_details` 是具体化的默认值，而非明确配置的比较字段。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`artifact_completeness_unspecified`
- 为什么修改：原生证据声明列出了 `agent_response.json` 和 `network.har`，但未要求 artifact 完整且可归属于本次运行。
- 应如何修改：要求提供可归属于本次运行的完整最终 agent 响应和完整 HAR，因为响应重建、最后事件选择和无匹配判定均依赖完整性。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`undecided_rule_too_narrow`
- 为什么修改：`undecided_if` 仅识别文件缺失或不可读的情况，因此未正确处理不完整、损坏或来源不明确的保留证据；`success_if` 也未明确写出 `retrieved_data:null`。
- 应如何修改：让 `success_if` 包含每个已配置的响应字段，并将 undecided 限定于证据缺失、不完整、损坏、不可读或无法归属于本次运行，且因此无法进行重建的情况。明确保留以下 failure 情形：完整但无效的响应，以及完整但没有符合条件的匹配项的 trace。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_rules_not_operationally_complete`
- 为什么修改：尽管该 checklist 简洁且不泄露运行信息，但由于遗漏了响应字段和证据完整性要求，它并未保留所有具有决定性的原生语义。
- 应如何修改：仅补充缺失的 `retrieved_data:null` 以及证据完整性/完好性/来源规则，同时保留当前紧凑的结构以及对更强条件的分离。

## Case 659

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：在用户的 empathy-prompts repo 创建标题为 `Integrating LLMs for better prompts` 的 issue，指派给 Roshanjossey，必要时可邀请该用户加入项目。due date 要设为 Q2 2033 的开始，即任务配置所对应的 `2033-04-01`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。响应 evaluator 检查 `agent_response.json` 经 released parsing/normalization 后，稀疏配置字段为 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；这是非 `RETRIEVE` 任务，`error_details` 不是显式比较字段。第一个网络 evaluator 在 `network.har` 中按 `POST` 和规范化路径筛选并以 `last_event_only=true` 取最后一个候选，然后完整比较 URL `__GITLAB__/api/v4/projects/183/invitations`、`user_id=2264` 和 `response_status=201`；第二个同样处理 `__GITLAB__/byteblaze/empathy-prompts/-/issues`，并要求 `issue[title]=Integrating LLMs for better prompts`、`issue[assignee_ids][]=2264`、`issue[due_date]=2033-04-01`、`response_status=302`。两项网络比较都还要求所选事件的完整规范化 URL 匹配配置；未启用 header、response-content、cookie、schema、ignore-pattern、base64 decoding 或 `should_not_exist` 约束。三个 evaluator 分数必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求三个检查全为 `1.0`：最终响应规范化为 `MUTATE/SUCCESS/null`，最后一个匹配的 invitation `POST` 携带 `user_id=2264` 且返回 `201`，最后一个匹配的 issue `POST` 携带指定 title、assignee `2264`、due date `2033-04-01` 且返回 `302`。它把 `agent_response.json` 与 `network.har` 作为决定性 artifacts，但将网络选择描述为按 path 和 method 匹配，没有明确写出随后还要比较完整规范化 URL。它将响应不匹配、任一所需 POST 缺失或字段/状态不匹配、evaluator 或 task orchestration 出错、任一组件分数非 `1.0` 归为 failure；artifact 缺失、截断或 unreadable 且无保留组件结果时归为 undecided。其 stronger condition `durable_issue_state` 另要求 HAR 中的创建响应与 post-run GitLab issue detail/API snapshot 证明 `byteblaze/empathy-prompts` 中持久存在该 title、Roshanjossey assignee 和 `2033-04-01` due date 的 issue。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_full_normalized_url_semantics`
- 为什么修改：两个 NetworkEventEvaluator 描述均止于按路径和方法进行候选匹配，未说明随后还会将所选事件的完整归一化 URL 与已配置的预期 URL 进行比较。
- 应如何修改：对于每个 network evaluator，区分方法/路径过滤和最后事件选择与完整比较，并要求所选事件的归一化 URL 在已发布的 URL 归一化和查询处理规则下等于其配置的 `__GITLAB__` URL。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_decision_rules_underclaim_failure`
- 为什么修改：当前规则可能仅依据请求体和状态接受最后一个路径匹配的 POST，即使其完整归一化 URL 比较失败。
- 应如何修改：在两个网络 success 规则中加入完整归一化 URL 相等性，并将所选事件的任何 URL 不匹配视为普通的原生 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：遗漏完整归一化 URL 比较，使得原本简洁的 checklist 无法完整用于重建原生结果。
- 应如何修改：保留紧凑结构，同时将缺失的 URL 要求添加到 network artifact 问题以及相应的 success 和 failure 规则中。

## Case 666

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：在当前 `primer/design` repository 提交从 `dialog-component` 合并到 `dialog` 的 merge request，并将 Primer 指定为 reviewer。任务 revision 为 `2`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经提取、解析和规范化后，稀疏配置字段匹配 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；对于非 `RETRIEVE` 任务，缺失的 `retrieved_data` 视为 `null`，任何原始非空值也会规范化为 `null`，且物化的 `error_details` 不参与比较。后者在 `network.har` 中按 `POST` 和 `__GITLAB__/primer/design/-/merge_requests` 的规范化路径过滤，以 `last_event_only=true` 选择最后一个候选，再比较完整规范化 URL、`response_status=302` 以及六个表单值：`merge_request[source_project_id]=180`、`merge_request[target_project_id]=180`、`merge_request[source_branch]=dialog-component`、`merge_request[target_branch]=dialog`、`merge_request[reviewer_ids][]=2367`、`merge_request[assignee_ids][]=0`。只有两个 evaluator 的分数都等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求响应通过 `MUTATE/SUCCESS` 且无 retrieved data 的比较，并且最后一个 URL-and-method-matching 的 merge-request `POST` 返回 `302`、六个表单值全部匹配；两个 evaluator 都为 `1.0`。它列出 `agent_response.json` 和 `network.har` 为决定性 artifacts，其中响应问题写成 `retrieved_data` 必须 absent or null，而不是说明任何原始值都会在非 `RETRIEVE` 规范化中变成 `null`。它将响应不被接受、无合格 POST、最后一个合格 POST 的状态或表单值不符，以及 evaluator error 归为 failure；retention loss、corruption 或 truncation 导致无法重建响应或最后事件时归为 undecided。其 stronger condition `resulting_merge_request_exists` 另要求 post-run GitLab merge-request state snapshot/API export 证明 `primer/design` 中确实存在从 `dialog-component` 到 `dialog`、reviewer 为 Primer 的 merge request。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`response_retrieved_data_normalization`
- 为什么修改：该 checklist 将原始 `retrieved_data` 视为必须不存在或为 null，尽管任务 666 属于非 RETRIEVE 任务，且 evaluator 会在比较前将任何已存在的原始 `retrieved_data` 值归一化为 null。
- 应如何修改：依据已发布的、与预期 `retrieved_data` null 进行的归一化比较来描述 success；说明缺失的 key 被视为 null，而对于此 MUTATE 任务，已存在的值同样会被归一化为 null；避免将具体化的 `error_details` 视为明确配置的字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_response_decision_rule`
- 为什么修改：具有非 null 原始 `retrieved_data` 的完整、可解析 MUTATE/SUCCESS 响应满足已发布的 evaluator，却不满足 checklist 所述的任何 success、failure 或 undecided 分支。
- 应如何修改：修订响应 artifact 问题和 success 规则，使接受条件取决于已发布的三字段归一化比较，而非原始 `retrieved_data` 是否不存在或为 null。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`missing_decisive_normalization_exception`
- 为什么修改：原本紧凑的 checklist 遗漏了一条会改变分数且为本 case 特有的归一化规则，因而对原生 success 施加了过严限制。
- 应如何修改：添加一句简洁说明，描述非 RETRIEVE 的 `retrieved_data` 归一化行为，同时保留当前与具体运行无关的紧凑结构。

## Case 679

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `NAVIGATE`：前往 completed orders 的列表，即把订单列表过滤为已完成状态。任务 revision 为 `2`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经字典输入或 raw/code-block JSON 解析及规范化后，显式字段匹配 `task_type=NAVIGATE`（也接受 legacy `performed_operation` alias）、`status=SUCCESS`、非 `RETRIEVE` 的 `retrieved_data=null`；物化的 `error_details` 不是显式比较字段。后者对 `network.har` 的非静态 evaluation events 应用 navigate-task 规则，选择最后一个被分类为 navigation event 的事件，并要求其为匹配正则 `^__SHOPPING_ADMIN__/mui/index/render/.*$` 的 `GET`、`response_status=200`、referer 为 `__SHOPPING_ADMIN__/sales/order/`，query 包含 `filters[placeholder]=true`、`filters[status]=complete`、`keywordUpdated=false`、`namespace=sales_order_grid`、`search=""`。query 规范化启用 `decode_base64_query=true`，忽略名称匹配 `^paging`、`^sorting` 或 `isAjax` 的参数，其他 query 结构仍须匹配；只有两个 evaluator 都得 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受 `NAVIGATE/SUCCESS` 且 `retrieved_data=null` 的响应，并由 `NetworkEventEvaluator` 接受最后一个 navigation event：它需匹配目标 URL、referer、`GET`、`200` 和 completed-order-grid query，且忽略 paging、sorting 与 `isAjax` 参数。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，但只笼统称按 configured ignore and normalization rules 比较，没有明确写出 `decode_base64_query=true`。它将任一 evaluator 非 `1.0` 或报错、响应被拒、缺少所选 navigation event、事件的 URL、referer、method、status 或非忽略 query 值不匹配归为 failure；artifact 缺失、截断或 unreadable 时归为 undecided。其 stronger condition `final_ui_completed_orders_state` 另要求最终 screenshot 或 DOM/accessibility snapshot 显示 Orders grid 已应用 Completed/Complete filter，且可见行不与该过滤条件冲突。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_base64_query_semantics`
- 为什么修改：NetworkEventEvaluator 描述列出了被忽略的查询模式，却遗漏了 `decode_base64_query=true`；这是传入 URL 比较的一项有效归一化设置。
- 应如何修改：明确说明 URL/查询比较会启用 base64 查询解码，并同时列出三个被忽略的查询参数模式。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_operational_network_rule`
- 为什么修改：success/failure 规则未使已启用的 base64 解码行为具备可操作性，因此审查者可能使用错误的 URL/查询归一化规则比较完整 HAR。
- 应如何修改：将 `decode_base64_query=true` 添加到 `success_if`，并明确指出：在执行该解码并排除已配置的查询名称后，任何不匹配均为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_setting_left_implicit`
- 为什么修改：尽管该 checklist 简洁且无泄漏，但它遗漏了一项具有决定性的已配置 flag，未能紧凑地保留所有原生语义。
- 应如何修改：使用简洁的 base64 解码条款修复该遗漏；不要添加新证据或扩大 benchmark 条件。

## Case 684

### 原本 case 是什么

原始任务是在 `reddit` 和 `gitlab` 站点执行 `MUTATE`：推广 `byteblaze/cloud-to-butt`，在讨论区 `LifeProTips` 创建帖子，并以项目描述作为标题。

### Benchmark 怎么测

配置依次包含 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者检查最终响应经解析、规范化和结构比较后是否满足显式期望 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；非 `RETRIEVE` 任务会把 `retrieved_data` 规范化为 `null`，物化产生的 `error_details=null` 不是显式配置的比较字段。后者在 `network.har` 中按 `POST` 和 URL 模式 `^__REDDIT__/submit/?.*$` 筛选，并因 `last_event_only=true` 只比较最后一个匹配事件，要求响应状态为 `302`，且 `submission[forum]="10016"`、`submission[mediaType]="url"`、`submission[title]="Chrome extension that replaces occurrences of 'the cloud' with 'my butt'"`、`submission[url]="__GITLAB__/byteblaze/cloud-to-butt"`。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是两个检查均得 `1.0`：`AgentResponseEvaluator` 接受 `MUTATE`/`SUCCESS`/`null` 最终响应，`NetworkEventEvaluator` 接受最后一个符合条件的 Reddit 提交事件；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它把两者都通过列为 success，把响应失败或报错、网络事件缺失或任一检查项不匹配列为 failure，并把 artifacts 遗失或保存不完整列为 undecided；其网络 failure 表述没有明确包含 `NetworkEventEvaluator` 自身报错。非空 stronger condition `persisted_post_exists` 另要求 `Post-run Reddit forum-state snapshot or export` 证明 `LifeProTips` 中实际持久化了指定标题及指向 `byteblaze/cloud-to-butt` 的 GitLab 链接。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`network_error_composition_gap`
- 为什么修改：组合说明未完整归类两个已配置 evaluator 的错误：`native.fail_if` 提到了 AgentResponseEvaluator 错误，却遗漏了 NetworkEventEvaluator 错误。
- 应如何修改：说明任一已配置 evaluator 的任何 failure 或 evaluator 错误都会产生非 1.0 的 evaluator 结果和原生任务 failure。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_error_missing_from_fail_rule`
- 为什么修改：导致 NetworkEventEvaluator 报错的完整保留 trace 未被 `fail_if` 覆盖，而 `undecided_if` 已正确限定于证据丢失。
- 应如何修改：扩展 `fail_if`，以包含会产生非 1.0 原生分数的 NetworkEventEvaluator 错误和编排错误；继续将 undecided 仅用于因证据保留、完整性或来源丢失而无法重建的情况。

## Case 689

### 原本 case 是什么

原始任务是在 `shopping` 站点执行 `MUTATE`：在商店联系表单中准备优惠券请求，理由必须是 `"I am a loyal customer, give me a coupon"`，并保持未提交、可供审核。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。响应检查要求经解析与非 `RETRIEVE` 规范化后匹配显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；第一个网络检查因 `last_event_only=true` 选择最后一个匹配 `POST` 与 `^http://.*/dummy_bin$` 的事件，要求 `response_status=-1`，以及 `comment="I am a loyal customer, give me a coupon"`、`email="emma.lopez@gmail.com"`、`form_id="contact-form"`、`name="Emma Lopez"`。第二个网络检查设置 `should_not_exist=true`，要求不存在任何匹配 `POST __SHOPPING__/contact/index/post` 的事件，不取决于其响应状态。`TaskEvalResult.score` 采用逻辑 AND，三个 evaluator 分数必须全部为 `1.0`。

### 原本 draft 是什么

原 draft 声称 native success 要求三个检查都得 `1.0`，决定性 artifacts 是 `agent_response.json` 和 `network.har`：前者用于判断响应是否被接受为 `MUTATE`/`SUCCESS`，后者分别验证最后一个 `dummy_bin` POST 的 `-1` 状态与四个表单字段，以及真实联系提交端点不存在。它把任一检查失败或报错列为 failure，包括响应不被接受、所需 `dummy_bin` 事件缺失或不匹配、以及出现任何 `POST __SHOPPING__/contact/index/post`；仅因保留证据丢失、截断或不可读而无法重建检查时列为 undecided。该 draft 的响应规则没有写出显式配置的 `retrieved_data=null`。非空 stronger condition `final_form_ready_state` 另要求最终浏览器截图或 DOM/accessibility snapshot 显示联系表单仍打开、未提交，并保留 `Emma Lopez`、`emma.lopez@gmail.com` 和精确理由文本。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_agent_response_retrieved_data_semantics`
- 为什么修改：原生响应描述将已配置的预期简化为 MUTATE 和 SUCCESS，遗漏了明确配置的 `retrieved_data:null` 及其已发布的非 RETRIEVE 归一化行为。
- 应如何修改：说明完整响应必须通过已发布的解析、归一化和比较，并匹配稀疏预期 `task_type=MUTATE`、`status=SUCCESS` 和 `retrieved_data=null`；不要将具体化的 `error_details:null` 视为明确配置的字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：`success_if` 未包含完整的已配置 AgentResponseEvaluator 预期。
- 应如何修改：在 `success_if` 中加入已发布的非 RETRIEVE 解析/归一化规则下的 `retrieved_data:null`，并将相应的响应拒绝明确列为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`native_semantics_not_fully_preserved`
- 为什么修改：尽管结构和泄漏控制合理，但紧凑的原生说明遗漏了一个明确配置的响应字段。
- 应如何修改：在简洁的 agent 响应 artifact 问题和决策规则中保留 `retrieved_data:null`。

## Case 695

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：使用适当的 attribute set 新增 simple product `"Energy-Bulk Man Yoga Pant"`，价格为 `$69.99`、库存为 `50` 且在库，size 为 `38`、color 为 yellow。

### Benchmark 怎么测

配置依次为 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。响应检查要求最终响应经解析与规范化后匹配 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`。网络检查因 `last_event_only=true` 只验证最后一个匹配 `POST` 和 `^__SHOPPING_ADMIN__/catalog/product/save/type/simple/store/0/set/\d+/back/edit$` 的事件，忽略查询参数模式 `isAjax`，要求 `response_status=302`，并比较 `product[color]="60"`、`product[name]="Energy-Bulk Man Yoga Pant"`、`product[price]="69.99"`、`product[quantity_and_stock_status][is_in_stock]="1"`、`product[quantity_and_stock_status][qty]="50"`、`product[size]="179"`、`product[status]="1"`。仅当两个 evaluator 分数都为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称两个 evaluator 都得 `1.0` 才算 benchmark success，决定性 artifacts 为 `agent_response.json` 和 `network.har`，分别检查 `MUTATE`/`SUCCESS`/`retrieved_data null` 响应及最后一个产品保存 POST 的 URL、`302`、七个表单值和 `isAjax` 忽略语义。它把两者都通过列为 success，把任一 evaluator 非 `1.0`、响应规范化失败、所需保存事件缺失或任一条件不匹配列为 failure，并原样声称此时 task score 为 `0.0 or ERROR`；只有实际 evaluator 输入未保留或事后损坏且无官方单项结果时才列为 undecided。非空 stronger condition `persisted_product_and_attribute_set` 另要求保留的 shopping-admin 产品状态证明产品确已持久化为启用的 simple product，并具有指定名称、价格、库存、size、color 及适当的 attribute set。

### 需要修改的部分

#### 修改项 1：native.success_if / fail_if / undecided_if

- Finding ID：`score_status_type_confusion`
- 为什么修改：`native.fail_if` 声称任务分数为“0.0 or ERROR”，但 ERROR 是 EvalStatus，而不是可能的分数。
- 应如何修改：说明每个普通不匹配或 evaluator/编排错误都会产生数值型 `TaskEvalResult.score` 0.0；普通不匹配的 status 为 FAILURE，错误的 status 为 ERROR。

## Case 698

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：使用适当的 attribute set 新增 simple product `"Lelelumon Yoga Mat"`，价格为 `$769.99`、库存为 `42` 且在库，size 为 `uni-size`、color 为 black。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`；前者对完整最终响应进行字符串或代码块 JSON 提取、解码和期望字段规范化，检查 `task_type=MUTATE`（可接受旧别名 `performed_operation`）、`status=SUCCESS`，而显式配置的 `retrieved_data=null` 在该非 `RETRIEVE` 任务中规范化为 `null`，物化默认值 `error_details=null` 不参与显式比较。网络检查先从非静态事件中以不区分大小写的 `POST` 方法及规范化路径 `^__SHOPPING_ADMIN__/catalog/product/save/type/simple/store/0/set/\d+/back/edit$` 筛选候选，再因 `last_event_only=true` 仅全面验证最后一个候选；`should_not_exist=false`，因此必须存在候选。该事件须满足 `response_status=302`，以及 `product[color]="49"`、`product[name]="Lelelumon Yoga Mat"`、`product[price]="769.99"`、`product[quantity_and_stock_status][is_in_stock]="1"`、`product[quantity_and_stock_status][qty]="42"`、`product[status]="1"`；只投影这六个 expected post-data key，额外表单字段不影响检查。查询参数名按大小写敏感模式忽略 `isAjax`，`decode_base64_query=false`，其他 URL/query 差异仍按规范化规则比较；`TaskEvalResult.score` 仅在两个 evaluator 分数均为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受最终响应且 `NetworkEventEvaluator` 接受最后一个合格的产品保存事件，决定性 artifacts 是 `agent_response.json` 和 `network.har`。它实际把响应描述为匹配 `MUTATE` 与 `SUCCESS`，把网络成功描述为最后一个 POST 匹配保存 URL、`302` 及六个字段 `name`、`price`、`qty`、`is_in_stock`、`status`、`color`；未写出 `retrieved_data=null`、`isAjax` 忽略、关闭 base64 解码及先筛选后取最后候选的完整语义。任一 evaluator 失败或报错被列为 failure，artifact 缺失或存储不完整导致无法重建两个结果时被列为 undecided。非空 stronger condition `persisted_complete_product` 另要求持久化记录证明产品为启用的 simple product，并具有指定名称、价格、库存状态、black、uni-size 和适当 attribute set。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`BF-1`
- 为什么修改：AgentResponseEvaluator 描述遗漏了明确配置的 `retrieved_data:null`，且未将其与未配置但具体化的 `error_details` 默认值区分开来。NetworkEventEvaluator 描述遗漏了 `ignored_query_params_patterns=[isAjax]`、`decode_base64_query=false`，以及 `last_event_only=true` 的先过滤后选择语义。
- 应如何修改：说明稀疏配置的响应字段和 MUTATE 的检索数据处理方式，将 `error_details` 排除在比较之外，并描述网络候选项过滤、最后一个候选项选择、忽略名为 `isAjax` 的查询参数、禁用 base64 解码、必须存在以及后续完整比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：基于 artifact 的 success 规则不完整，并且由于未落实已发布的最后事件和查询归一化行为，可能错误归类包含多个 POST/路径候选项或查询差异的 trace。
- 应如何修改：重写 `success_if` 和 `fail_if`，使完整响应和完整 HAR 可被直接分类，包括选择最后一个 POST/路径候选项、完整的归一化 URL/查询比较、全部六个投影后的表单字段，以及将完整但无效的证据或 evaluator 错误归为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：尽管该 checklist 简洁且不包含运行结果，但其压缩移除了与分数相关的配置，并使最后事件规则存在歧义。
- 应如何修改：简洁地补充遗漏的语义，同时保留现有的运行前、以来源为依据的范围，并避免声称任何已观察到的结果。

## Case 699

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：创建名为 `"spring sale"` 的新 marketing price rule，面向所有 registered customers，提供全站 `20 percent` 折扣。

### Benchmark 怎么测

配置依次为一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应 evaluator 对最终响应进行提取、必要时 JSON 解码和非 `RETRIEVE` 规范化，要求显式字段 `task_type=MUTATE`（或旧别名 `performed_operation`）、`status=SUCCESS`、`retrieved_data=null`；缺失或提供的 `retrieved_data` 在该任务中均规范化为 `null`，物化默认值 `error_details=null` 不参与比较。网络 evaluator 因 `last_event_only=true` 选择最后一个匹配规范化端点 `__SHOPPING_ADMIN__/sales_rule/promo_quote/save` 的 `POST` 事件，要求 `response_status=302`，并比较 `customer_group_ids=[1]`、`discount_amount=20`、`name="spring sale"`、`simple_action="by_percent"`、`website_ids=[1]`；`should_not_exist=false`，且未配置 header、response content、cookie、schema、ignore pattern 或 base64 约束。`TaskEvalResult.score` 仅在两个 evaluator 分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声称 native benchmark success 是 `TaskEvalResult.score == 1.0`，要求最终响应被接受为 `MUTATE`/`SUCCESS`，且最后一个匹配保存 URL 的 POST 具有 `302` 和五个指定 post-data 值；决定性 artifacts 为 `agent_response.json` 与 `network.har`。它把两个检查都通过列为 success，把响应无效或不匹配、最后保存 POST 缺失或不匹配、以及 evaluator error 列为 failure；只有 artifacts 不可用、不完整或不可读且没有完整官方 `TaskEvalResult` 时列为 undecided。该 draft 的响应说明没有写出显式配置的 `retrieved_data=null` 及相应解析和非 `RETRIEVE` 规范化语义。非空 stronger condition `persisted_rule_matches_intent` 另要求 post-run sales-rule record 或 state export 证明 `"spring sale"` 已持久化，并确实对所有 registered customers 提供全站 `20 percent` 的 `by_percent` 折扣。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_incomplete`
- 为什么修改：原生声明将 AgentResponseEvaluator 描述为仅检查 MUTATE/SUCCESS，未说明明确配置的 `retrieved_data:null` 比较，也未说明已发布的解析和 MUTATE 归一化行为。
- 应如何修改：说明保留的响应必须解析或提取为一个 mapping，其中已配置的 `task_type`（或旧版 alias）和 `status` 会归一化为 MUTATE/SUCCESS；还应说明明确配置的 `retrieved_data:null` 得以满足，是因为对于此非 RETRIEVE 任务，缺失或已提供的 `retrieved_data` 都会归一化为 null。不要将具体化的 `error_details:null` 视为已配置字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_underspecified`
- 为什么修改：`success_if` 将判断委托给 AgentResponseEvaluator，却未说明全部已配置的响应语义，因此不足以依据保留证据应用该原生检查。
- 应如何修改：扩展 `success_if`，加入已配置的 `task_type`、`status` 和 `retrieved_data:null` 解析/归一化比较，同时保留完整的最后事件网络条件。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_claim_drops_native_semantics`
- 为什么修改：尽管该 checklist 简洁且不包含运行结果，但它通过遗漏已配置的 AgentResponseEvaluator 字段集和归一化语义来实现简洁。
- 应如何修改：添加一句紧凑且以来源为依据的响应比较说明，涵盖 `retrieved_data:null` 和已发布的非 RETRIEVE 归一化，同时不要添加运行结果或无关的 evaluator 细节。

## Case 700

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点创建一条名为 `"fall discount"` 的营销价格规则，面向所有已注册客户，并在结账时提供 `$10` 折扣。task type 为 `MUTATE`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 对 `agent_response.json` 进行解析和规范化，只比较 sparse 配置中明确给出的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；缺少 `task_type` 时可使用旧字段 `performed_operation`，非 `RETRIEVE` 任务会把实际 `retrieved_data` 规范化为 `null`，materialized 默认的 `error_details=null` 不构成比较字段。`NetworkEventEvaluator` 从 `network.har` 中按 `POST` 和规范化 URL path `__SHOPPING_ADMIN__/sales_rule/promo_quote/save` 筛选候选，并因 `last_event_only=true` 选择最后一个候选；随后要求完整规范化 URL 相等且没有额外 query，`response_status=302`，并比较 `customer_group_ids=[1]`、`discount_amount=10`、`name="fall discount"`、`simple_action="cart_fixed"`、`website_ids=[1]` 这些配置的 POST 字段，未配置的额外 POST 字段不影响比较。最终 `TaskEvalResult.score` 只有在两个 evaluator 的 score 都等于 `1.0` 时才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 为 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator` 和 `NetworkEventEvaluator` 都得到 `1.0`；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 response 成功规则要求解析后得到 `{task_type: MUTATE, status: SUCCESS, retrieved_data: null}`，并声称额外的规范化 `error_details` 会导致失败；network 成功问题和规则按匹配 path、`302` 及五个 POST 字段判定，但 failure 规则又把完整规范化 URL 不匹配列为失败。draft 将完整 artifact 中的解析、字段、事件或 evaluator 错误归为 failure，将 artifact 未保留或无法证明送评 bytes 且现有证据尚未证明失败归为 undecided。它还提出两个非空 stronger conditions：`persisted_rule_state` 要求保留的后台状态证明规则确已持久化；`mutate_response_contract` 要求原始 `retrieved_data` 缺失或为 JSON `null`，不能仅依靠 evaluator 的 MUTATE 规范化。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_semantics`
- 为什么修改：网络工件问题和成功规则止于规范化路径匹配，尽管路径匹配仅用于选择候选项，随后还会使用所选事件的完整规范化 URL 进行比较。
- 应如何修改：说明最后一个 POST/路径候选项还必须具有与配置 URL 相等的完整规范化 URL；由于未配置查询参数或忽略规则，因此还必须不存在额外的查询参数。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`insufficient_network_success_rule`
- 为什么修改：具有预期路径、状态和 POST 字段但带有额外查询字符串的所选事件，会满足书面定义的 success_if，却无法通过已发布的完整对象比较。
- 应如何修改：使 success_if 要求完整的规范化网络事件比较通过，并明确包括完整 URL/查询相等。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`network_rule_incoherence`
- 为什么修改：success_if 仅引用保存路径，而 fail_if 将任何预期规范化 URL 不匹配视为失败。
- 应如何修改：在决定性工件问题、success_if 和 fail_if 中一致使用相同的完整规范化 URL 标准。

## Case 706

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点显示 Q1 的退款报告，并给定“今天”为 March 15, 2023。task type 为 `NAVIGATE`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 解析并规范化 `agent_response.json`，比较 sparse 配置明确指定的 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；`performed_operation` 可作为旧版 task type 字段，非 `RETRIEVE` 规范化会令缺失或给出的 `retrieved_data` 成为 `null`，`ordered=false` 和 `results_schema.type=null` 不增加数据比较，默认的 `error_details` 不参与评分。`NetworkEventEvaluator` 要求最后一个 evaluator 识别的 navigation event 为对 `__SHOPPING_ADMIN__/reports/report_sales/refunded/filter` 的 `GET`，响应状态为 `200`；其 query 需在 `decode_base64_query=true` 后满足 `report_type=["created_at_order"]`、`from=["01/1/2023"]`、`to=["03/31/2023"]`。`from`、`to` 按 schema 的 date array 规范化，`report_type` 按 string array 规范化，正则 `^(?!report_type$|from$|to$).*$` 忽略除此三者外的 query 名；`last_event_only=true`、`should_not_exist=false`。`TaskEvalResult.score` 仅在两个 evaluator score 均为 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `TaskEvalResult.score` 只有在 `AgentResponseEvaluator` 和 `NetworkEventEvaluator` 都为 `1.0` 时才为 `1.0`，并把 `agent_response.json` 与 `network.har` 作为决定性 artifacts。它描述 response artifact 应通过针对 `NAVIGATE/SUCCESS` 的解析、规范化和结构比较，network artifact 应含最后一个符合 `GET 200`、退款报告 URL 及 Q1 query 值的 navigation event，但只笼统称其遵循“configured normalization and ignored-parameter rules”。draft 把任一组件低于 `1.0`、比较不符、事件缺失或不匹配以及 evaluator error 归为 failure；只有 artifact 保留不完整、无法评估两个组件时才为 undecided，并指出 screenshot 或 page text 不能单独确定 native score。其非空 stronger condition `rendered_report_visible` 要求额外的 final-page screenshot 或 DOM snapshot 显示 Q1 2023 退款报告已实际渲染。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`incomplete-active-normalization-semantics`
- 为什么修改：原生规则未明确指出预期的 retrieved_data:null，也未明确说明当前启用的 decode_base64_query=true、日期 schema 以及精确的查询名称忽略行为，因此证据审查者无法仅根据检查清单措辞完整应用所有会改变评分的已配置语义。
- 应如何修改：说明三个显式配置的响应字段及其非 RETRIEVE 规范化行为，澄清 error_details 未被显式配置，并说明所选的最后一个导航事件在比较时会进行 Base64 查询解码、针对 from/to 的日期感知规范化，并忽略 report_type、from 和 to 之外的所有查询名称。

## Case 707

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点显示上一年的 sales order report；根据给定的 March 15, 2023，该范围是 calendar year 2022。task type 为 `NAVIGATE`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 对 `agent_response.json` 执行字符串或代码块 JSON 解析及规范化，并比较明确配置的 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；非 `RETRIEVE` 任务会把实际 `retrieved_data` 规范化为 `null`。`NetworkEventEvaluator` 要求最后一个 navigation event 为对 `__SHOPPING_ADMIN__/reports/report_sales/sales/filter` 的 `GET` 且响应状态为 `200`；在 `decode_base64_query=true`、忽略除 `report_type`、`from`、`to` 外所有 query 名并按 schema 规范化后，三项必须分别为 `["created_at_order"]`、`["1/1/2022"]`、`["12/31/2022"]`。其中 `from`、`to` 是 date array，`report_type` 是 string array；`last_event_only=true`、`should_not_exist=false`，没有启用 header、body、response-content 或 cookie 约束。两个 evaluator 的 score 必须都为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 是 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator` 和 `NetworkEventEvaluator` 都为 `1.0`，并称任何较低 score 或 evaluator error 都使 task score 为 `0.0`。它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，要求 response 匹配 `NAVIGATE/SUCCESS`，最后一个 navigation event 为访问 `__SHOPPING_ADMIN__/reports/report_sales/sales/filter` 的 `200 GET`，且保留的 `report_type/from/to` 对应 `created_at_order` 和 2022 全年；原文没有明确写出 Base64 query decoding 和 `retrieved_data=null` 的完整语义。draft 把 response 不匹配、事件缺失、method/path/status/query 不匹配或 evaluator error 归为 failure，把送评 response bytes 或 HAR events 因留存丢失、截断而无法确定归为 undecided。其非空 stronger condition `visible_report_state` 要求 `final-page screenshot` 显示 sales order report 内容及 January 1–December 31, 2022 的已应用范围。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_configured_normalization_semantics`
- 为什么修改：响应描述遗漏了预期的 retrieved_data:null，而网络描述遗漏了 decode_base64_query:true。
- 应如何修改：说明已发布的响应解析/规范化结果会与显式配置的 NAVIGATE、SUCCESS 和 retrieved_data:null 字段进行比较，并说明网络 URL/查询比较会在忽略参数过滤和 schema 规范化之前应用已配置的 Base64 查询解码。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：成功规则无法独立重建所有已配置检查，因为它隐含了两个已配置的规范化行为。
- 应如何修改：扩展 success_if 及相应的 fail_if 措辞，以涵盖非 RETRIEVE 规范化后的预期 retrieved_data:null 和已配置的 Base64 查询解码。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_omitted`
- 为什么修改：通过省略可能影响原生结果的已配置语义实现了简洁性。
- 应如何修改：仅添加缺失的 retrieved_data:null 和 Base64 查询条款，同时保留检查清单当前紧凑的运行前形式。

## Case 709

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点显示 May 1, 2021 至 March 31, 2022 的 orders report。task type 为 `NAVIGATE`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 从 `agent_response.json` 按 released JSON/code-block 规则解析对象，并在 sparse 明确字段上比较 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；`performed_operation` 可作为旧字段，非 `RETRIEVE` 任务把 `retrieved_data` 规范化为 `null`，默认的 `error_details` 不参与比较。`NetworkEventEvaluator` 以 `last_event_only=true` 选择 evaluator 识别的最后一个 navigation event，要求它为访问 `__SHOPPING_ADMIN__/reports/report_sales/sales/filter` 的 `GET` 且 `response_status=200`。URL/query 处理启用 `decode_base64_query=true`，用 `^(?!report_type$|from$|to$).*$` 忽略除三项外的 query 名，并按 schema 将 `from/to` 作为 date arrays、`report_type` 作为 string array 规范化，期望值为 `report_type=["created_at_order"]`、`from=["05/1/2021"]`、`to=["03/31/2022"]`；`should_not_exist=false`。只有两个 evaluator score 均为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 response 规范化为 `NAVIGATE`、`SUCCESS`、`null retrieved_data`，且最后一个 evaluator 识别的 navigation event 是访问 `__SHOPPING_ADMIN__/reports/report_sales/sales/filter`、携带指定三项 query 的 `GET 200`；两项 evaluator score 都为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts，但 network 说明没有展开 `decode_base64_query=true`、query-name ignore regex 和 schema/date-array 规范化。draft 将 response 解析、规范化或比较失败，以及最后 navigation event 缺失、endpoint/query/method/status 不符或 evaluator error 归为 failure；若尚无 artifact 证明失败，但两个 artifacts 中任一没有完整保留，则为 undecided。其非空 stronger condition `visible_report_state` 要求 `Final browser screenshot or accessibility/DOM snapshot` 可见地显示 orders report、请求的日期范围及已渲染报告内容。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_normalization_options_omitted`
- 为什么修改：网络描述未说明三个已启用的比较设置：decode_base64_query=true、忽略除 report_type/from/to 之外所有名称的 ignored_query_params_patterns，以及将 from/to 规范化为日期数组并将 report_type 规范化为字符串数组的 query_params_schema。
- 应如何修改：将这些已启用的 URL/查询规范化规则添加到 benchmark_success 和网络工件判定问题中，以便对等的规范化日期和允许的额外查询名称得到与已发布评分完全相同的处理。

## Case 711

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点显示 July 5, 2021 至 May 31, 2023 的 product view report。task type 为 `NAVIGATE`，revision 为 `2`。

### Benchmark 怎么测

`AgentResponseEvaluator` 对 `agent_response.json` 执行原始或 fenced JSON 提取和 mapping 规范化，只比较 sparse 配置的 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；`performed_operation` 可作为旧别名，非 `RETRIEVE` 情况下缺失或提供的 `retrieved_data` 都规范化为 `null`，默认 `error_details` 不参与比较。`NetworkEventEvaluator` 在 HAR 事件中取最后一个 evaluator-visible navigation event，要求其为对 `__SHOPPING_ADMIN__/reports/report_product/viewed/filter` 的 `GET` 且响应状态为 `200`；`decode_base64_query=true`，正则 `^(?!report_type$|from$|to$).*$` 忽略其余 query 名，schema 将保留项规范化为 string/date arrays，期望 `report_type=["created_at_order"]`、`from=["07/5/2021"]`、`to=["05/31/2023"]`。这里 `last_event_only=true`、`should_not_exist=false`；`TaskEvalResult.create` 仅在两个 evaluator score 都为 `1.0` 时产生 `TaskEvalResult.score=1.0`。

### 原本 draft 是什么

原始 draft 声明 native score 仅在两个 evaluator 都为 `1.0` 时为 `1.0`：response 被接受为 `NAVIGATE/SUCCESS`，最后一个 evaluator-visible navigation event 被接受为目标 product-view URL 的 `200 GET`，且非忽略 query 规范化为 `created_at_order` 及指定起止日期。它将 `agent_response.json` 与 `network.har` 作为决定性 artifacts，并提到非 `RETRIEVE` 的 `retrieved_data` 处理，但没有明确写出 `decode_base64_query=true`，也没有清楚区分 sparse 配置的 `retrieved_data=null` 与默认但不比较的 `error_details`。draft 将完整 response 的解析、规范化、结构、task type 或 status 不匹配，以及 HAR 无 navigation event或最后事件的 URL、method、status、非忽略 query 不匹配归为 failure；artifact 缺失或留存副本不完整时为 undecided，存在但解析或比较失败则不是 undecided。其非空 stronger condition `rendered_report_visible` 要求 `Final-page screenshot` 显示 product view report 内容以及 July 5, 2021 至 May 31, 2023 的范围。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`explicit_normalization_semantics`
- 为什么修改：原生文本将已配置的 Base64 查询解码作为隐含行为，并且对 retrieved_data 处理的描述过于笼统，无法区分稀疏的显式 null 预期与具体化的 error_details 默认值。
- 应如何修改：说明 AgentResponseEvaluator 在已发布的提取/规范化之后比较稀疏且显式配置的 task_type、status 和 retrieved_data:null 字段，排除默认填充的 error_details；并说明 NetworkEventEvaluator 在其已配置的查询过滤和 schema 比较之前应用 decode_base64_query=true。

## Case 713

### 原本 case 是什么

原始用户任务是在 `shopping_admin` 站点显示 2022 年 5 月 1 日至 2023 年 5 月 31 日的 Best Sellers 报表，task type 为 `NAVIGATE`。官方指令是 `Show the best sellers report from May 1, 2022 to May 31, 2023.`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json` 经发布版解析与归一化后，显式配置字段是否为 `task_type: NAVIGATE`、`status: SUCCESS`、`retrieved_data: null`；非 `RETRIEVE` 任务中，缺失或提供的 `retrieved_data` 均归一化为 null，而物化默认值 `error_details: null` 不属于显式比较字段。`NetworkEventEvaluator` 检查 `network.har` 中选定的最后一个导航事件：经 URL 渲染/反渲染、`decode_base64_query=true` 和日期 schema 归一化后，须为对 `__SHOPPING_ADMIN__/reports/report_sales/bestsellers/filter` 的 `GET`、响应状态 `200`，且查询数组为 `report_type=[created_at_order]`、`from=[05/1/2022]`、`to=[05/31/2023]`；正则 `^(?!report_type$|from$|to$).*$` 忽略其余查询参数名。配置还规定 `last_event_only=true`、`should_not_exist=false`，null 的 header、body、cookie 和 response-content 约束不生效。两项 evaluator 分数都必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 是 `TaskEvalResult.score = 1.0`，要求 `AgentResponseEvaluator` 的 `NAVIGATE/SUCCESS` 响应检查和 `NetworkEventEvaluator` 的网络检查均得 `1.0`；它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts。其 success 条件要求最终响应通过结构比较，且 HAR 的最后导航事件为目标 Best Sellers filter URL 的 `GET`、返回 `200`，日期及 `report_type=created_at_order` 归一化匹配，并忽略其他查询名；failure 包括任一响应或网络检查为 0 或报错，任一非 `1.0` 分数使任务为 0。它把 artifact 缺失或留存损坏且无官方结果补足列为 undecided，并说明实际交给 evaluator 的畸形 artifact 属于失败或错误。非空 stronger condition `rendered_report_visible` 另要求最终页面截图或 DOM/accessibility snapshot 可见 Best Sellers 报表及所请求日期范围，因为原 draft 认为原生检查没有验证渲染内容。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_under_specified`
- 为什么修改：原生规则将 AgentResponseEvaluator 简化为 NAVIGATE/SUCCESS 比较，却未说明已发布的解析/规范化会针对显式配置的 retrieved_data:null 字段进行，也未说明具体化的 error_details:null 未被显式配置且不参与比较。
- 应如何修改：说明响应必须通过已发布的解析被接受为 dict/JSON 对象，并基于稀疏配置字段规范化为 task_type NAVIGATE（采用已发布的 performed_operation 别名）、status SUCCESS 和 retrieved_data null；说明对于此 NAVIGATE 任务，retrieved_data 会规范化为 null，而 error_details 不是参与比较的已配置字段。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`base64_query_behavior_omitted`
- 为什么修改：已配置的 NetworkEventEvaluator 启用了 Base64 查询解码，但没有任何原生规则说明会在 URL/查询比较之前应用此转换。
- 应如何修改：将 decode_base64_query=true 添加到可操作的网络匹配规则中，同时保留最后一个导航事件选择、GET/200 默认值、日期 schema、忽略名称模式和必需事件语义。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_not_fully_operational`
- 为什么修改：success_if 未提供足够细节，无法根据保留的工件重建两个已配置比较。
- 应如何修改：将 success_if 替换为显式的响应解析/字段规范化条件和网络选择/规范化条件（包括 Base64 查询解码），并要求两个 evaluator 的分数均为 1.0。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：该检查清单虽简洁且无运行信息泄漏，但遗漏了决定性的已发布语义。
- 应如何修改：保留现有的紧凑结构，同时添加缺失的 AgentResponseEvaluator 字段行为和 decode_base64_query 网络行为。

## Case 715

### 原本 case 是什么

原始用户任务是在 `reddit` 站点给 `history` forum 中历史最高的 2 个帖子点踩，task type 为 `MUTATE`。官方指令是 `Thumbs down the top 2 post ever in history.`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json` 经发布版解析和非 `RETRIEVE` 归一化后，显式字段是否比较为 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；缺失或提供的 `retrieved_data` 都归一化为 null，`error_details` 不计分。两个 `NetworkEventEvaluator` 分别检查 `__REDDIT__/sv/58888.json` 和 `__REDDIT__/sv/41616.json`：在按 `POST` 与归一化 URL 过滤后选取最后事件，并比较完整归一化 URL、方法 `POST`、`post_data.choice: "-1"` 和响应状态 `200`；两者均为 `last_event_only=true`、`should_not_exist=false`、`decode_base64_query=false`。一个响应 evaluator 与两个网络 evaluator 的分数必须全部等于 `1.0`，否则 `TaskEvalResult.score` 不为 `1.0`；完整输入上的 evaluator 或编排错误也计失败。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 仅在三个 evaluator 全部得 `1.0` 时为 `1.0`：响应通过 `MUTATE/SUCCESS` 检查，且两个 endpoint 的最后匹配事件都是 `choice "-1"`、响应 `200` 的 downvote `POST`。它将 `agent_response.json` 与 `network.har` 列为决定性 artifacts，并把响应检查失败或报错、任一 endpoint 无匹配 POST，或所选最后事件的 choice/status 不匹配列为 failure。artifact 缺失、不可读或明显截断而无法重建检查时为 undecided，但完整 HAR 中没有匹配事件是 failure。其 `stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_retrieved_data_semantics`
- 为什么修改：响应规则仅指出 MUTATE 和 SUCCESS，遗漏了显式配置的 retrieved_data:null 字段及其非 RETRIEVE 规范化行为。
- 应如何修改：说明 AgentResponseEvaluator 对显式配置的 task_type=MUTATE、status=SUCCESS 和 retrieved_data=null 应用已发布的解析、规范化和结构比较；澄清非 RETRIEVE 规范化会将 retrieved_data 映射为 null，并且具体化的 error_details:null 不参与评分。

#### 修改项 2：native.checked_by 及 evaluator 组合规则

- Finding ID：`incomplete_error_composition_rule`
- 为什么修改：检查清单未明确将完整输入下来自 NetworkEventEvaluator 或任务编排的错误归类为原生失败。
- 应如何修改：添加一条通用的原生失败规则，涵盖任何不等于 1.0 的已配置 evaluator 分数，以及完整输入所引发的任何 evaluator 或编排错误。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_and_failure_rules`
- 为什么修改：success_if 遗漏了规范化后的 retrieved_data:null，而 fail_if 未明确涵盖每个非 1.0 的 evaluator 结果或完整证据下的 evaluator 错误。
- 应如何修改：使响应成功谓词包含所有显式配置的规范化字段，并添加一条针对完整输入下非 1.0 结果/错误的通用失败规则；仅将 undecided 保留用于证据留存、完整性或来源丢失的情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_omitted`
- 为什么修改：尽管检查清单简洁且无运行信息泄漏，但它遗漏了完整陈述已发布比较所需的一个显式配置响应字段。
- 应如何修改：添加 retrieved_data:null 的规范化/比较语义，但不要添加原始输入怪异行为、运行结果或不必要的条件。

## Case 716

### 原本 case 是什么

原始用户任务是在 `reddit` 站点给 `books` forum 中历史最高的 3 个帖子点踩，task type 为 `MUTATE`。官方指令是 `Thumbs down the top 3 post ever in books.`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查 `agent_response.json` 经发布版解析和归一化后是否匹配显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；作为非 `RETRIEVE` 任务，`retrieved_data` 归一化为 null，其内容不单独比较。三个 `NetworkEventEvaluator` 分别面向 `__REDDIT__/sv/81371.json`、`__REDDIT__/sv/59421.json` 和 `__REDDIT__/sv/59447.json`：按 `POST` 与归一化 URL path 筛选事件并选最后候选，然后比较归一化完整 URL、方法 `POST`、归一化 body 字段 `choice: "-1"` 和响应状态 `200`。网络配置为 `decode_base64_query=false`、`last_event_only=true`、`should_not_exist=false`，没有 ignored query 参数或 pattern，也没有 query/post-data schema。四个 evaluator 分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 仅在一个 `AgentResponseEvaluator` 和三个 `NetworkEventEvaluator` 全部得 `1.0` 时为 `1.0`：响应作为成功的 `MUTATE` 通过，且 `/sv/81371.json`、`/sv/59421.json`、`/sv/59447.json` 各自最后匹配的 POST 都有 `choice -1` 和响应状态 `200`。它将 `agent_response.json` 与 `network.har` 列为决定性 artifacts；任何必要输入实际缺失或不可解析、响应不匹配或报错、目标 path 无合格事件，或最后匹配 POST 的 choice/status 不符，均被列为 failure。留存响应或 HAR 缺失、不完整且无官方 evaluator 结果时为 undecided，已确认的运行时缺失或解析失败则不是 undecided。非空 stronger condition `persisted_downvotes` 另要求认证后的 Reddit 状态证明执行账户在帖子 `81371`、`59421`、`59447` 上的 vote choice 均为 `-1`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_url_comparison_omitted`
- 为什么修改：原生描述仅提及 URL 路径、POST 选择和响应状态，遗漏了将每个所选事件的规范化 URL 与配置的预期 URL 进行比较。
- 应如何修改：说明每个 evaluator 按 POST 和规范化 URL 路径进行过滤，因为 last_event_only 为 true，所以选择最后一个候选项，随后在已配置的 URL/查询默认设置下，比较该事件的规范化 URL，以及方法、choice 和状态。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`decision_rules_url_gap`
- 为什么修改：成功和失败规则未将规范化 URL 不匹配设为决定性条件，可能会在事件的规范化 URL 不等于预期 URL 时，仍将具有预期路径、choice 和状态的事件视为充分。
- 应如何修改：向 success_if 添加规范化 URL 相等条件，并向 fail_if 添加任何所选事件的 URL/查询规范化不匹配。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_incomplete`
- 为什么修改：尽管检查清单简洁且无运行信息泄漏，但它通过省略与评分相关的网络比较实现了紧凑性。
- 应如何修改：保留紧凑结构，但在 benchmark_success、HAR 证据问题、success_if 和 fail_if 中纳入规范化完整 URL 匹配。

## Case 721

### 原本 case 是什么

原始用户任务是在 `reddit` 站点点赞 `IAmA` forum 中由 `UniversityofBath` 创建的所有 submissions，task type 为 `MUTATE`。官方指令是 `Like all submissions created by UniversityofBath in forum IAmA`。

### Benchmark 怎么测

`AgentResponseEvaluator` 检查最终 `agent_response.json` 经发布版解析和归一化后，显式配置字段是否为 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；非 `RETRIEVE` 归一化会把缺失或提供的 `retrieved_data` 变为 null，物化默认字段 `error_details` 不参与比较。八个 `NetworkEventEvaluator` 分别检查 `__REDDIT__/sv/119742.json`、`119719.json`、`119714.json`、`55155.json`、`55142.json`、`34032.json`、`13175.json` 和 `13170.json`：每项取对应 endpoint 最后匹配的 `POST`，要求 `post_data.choice: "1"`、响应状态 `200`，并匹配其他已配置事件数据；配置为 `last_event_only=true`、`should_not_exist=false`、`decode_base64_query=false`。一个响应 evaluator 与八个网络 evaluator 共九项，所有分数都必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 `TaskEvalResult.score` 仅在 `AgentResponseEvaluator` 与全部八个 `NetworkEventEvaluator` 均得 `1.0` 时为 `1.0`，并把 `agent_response.json` 和 `network.har` 作为决定性 artifacts。其 success 条件要求响应归一化为 `task_type MUTATE`、`status SUCCESS`、`retrieved_data null`，且八个固定 ID endpoint 的最后匹配 POST 都以 `choice "1"` 和状态 `200` 通过；响应无效或归一化字段不匹配，以及任何 endpoint 缺失或事件比较不匹配，都被写为 failure。留存证据缺失或不完整、无法确定响应或网络比较且无官方结果补足时为 undecided，当前 artifact 被 evaluator 拒绝则为 failure。非空 stronger condition `all_qualifying_submissions_liked_in_final_state` 另要求 post-run Reddit state export 枚举并证明 UniversityofBath 在 IAmA 的每个 submission 均被执行账户点赞，包括八个固定 ID 之外的合格 submission。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_overbroad_semantics`
- 为什么修改：检查清单暗示 retrieved-data 结构不匹配或任何笼统意义上无效的公开响应必然导致 AgentResponseEvaluator 失败。在此非 RETRIEVE 任务中，已提供或缺失的 retrieved_data 都会规范化为 null，并跳过其值；只有稀疏配置的字段参与比较，因此具体化的 error_details 不参与比较。
- 应如何修改：准确说明已发布的已配置字段解析和规范化语义，并移除任何暗示原始 retrieved_data 内容、error_details 或其他被忽略的额外字段本身会导致原生失败的表述。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`agent_response_overbroad_failure_rule`
- 为什么修改：fail_if 在操作语义上并不忠实，因为其未限定的无效响应和 retrieved-data 结构表述可能会将 evaluator 接受的 MUTATE 响应归类为失败。
- 应如何修改：将响应失败限制为：非对象，或以其他方式被已发布的解析/规范化拒绝；缺失或不匹配的规范化 task_type/status；结构比较失败；或 evaluator 错误。明确说明原始 retrieved_data 内容本身在此处不构成失败。

## Case 723

### 原本 case 是什么

原始用户任务是在 `reddit` 站点点赞 `iphone13` forum 中由 `FTorrez81` 创建的所有 submissions；官方配置的 task type 为 `RETRIEVE`。官方指令是 `Like all submissions created by FTorrez81 in forum iphone13`。

### Benchmark 怎么测

该 case 只配置一个 `AgentResponseEvaluator`，它检查完整 `agent_response.json` 是否被发布版解析器接受，并按显式字段归一化和结构比较为 `task_type: RETRIEVE`、`status: NOT_FOUND_ERROR`、`retrieved_data: null`；`results_schema` 为 `{"type":"null"}`，物化默认值 `error_details: null` 不是显式比较字段。没有配置 `NetworkEventEvaluator`，因此 `network.har` 不参与这项原生评分。唯一 evaluator 必须得 `1.0`，`TaskEvalResult.score` 才为 `1.0`；解析后非对象或无效、配置字段缺失或不匹配、`retrieved_data` 未归一化为 null/no data，或 evaluator 报错，都会使该项不为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求唯一的 `AgentResponseEvaluator` 得 `1.0`，即响应归一化为 `task_type RETRIEVE`、`status NOT_FOUND_ERROR` 和 `retrieved_data null/no data`，且无 evaluation error。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并额外声称 trace/evaluation context 必须无错误；响应不可解析、非对象或字段不匹配，以及已证明的 trace、context-validation、evaluator 或 orchestration error 被列为 failure。它将最终响应或所需 trace 未留存、截断或无法绑定到 evaluated run 且无权威 `TaskEvalResult` 的情形列为 undecided。非空 stronger condition `verify_reddit_like_state` 另要求认证 post-run Reddit state 枚举 FTorrez81 在 iphone13 的全部 submissions 并证明均被执行账户点赞；若集合为空，则须由证据证明不存在匹配 submission。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_artifact`
- 为什么修改：network.har 被呈现为决定性工件，但唯一配置的 evaluator 读取的是代理响应，并未配置 NetworkEventEvaluator。
- 应如何修改：从原生决定性工件中移除 network.har，并保留完整的 agent_response.json，作为重建已配置比较所需的最小充分证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：这些规则要求 trace 被接受才能判定成功，并允许缺失 trace 导致原生结果为 undecided。
- 应如何修改：仅依据完整保留的响应或权威 evaluator 结果判定原生 success、failure 和 undecided；将 undecided 限制为该决定性证据丢失、损坏或来源验证失败的情况。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_checklist`
- 为什么修改：与 trace 相关的工件和判定条款为仅配置响应检查增加了冗余的基础设施条件。
- 应如何修改：删除 trace 专属的原生条款，同时保留 AgentResponseEvaluator 语义和单独的更强后置状态条件。

## Case 726

### 原本 case 是什么

原始任务是在 `reddit` 站点的 `earthporn` forum 中，对用户 `jacyanthis` 创建的所有 submissions 执行 DisLike。官方将该任务标为 `RETRIEVE`，revision 为 `2`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它按已发布的解析和归一化逻辑检查 `agent_response.json` 中显式配置的字段：`task_type` 为 `RETRIEVE`、`status` 为 `NOT_FOUND_ERROR`、`retrieved_data` 为 `null`；缺失的 `retrieved_data` 按 `null` 处理，物化配置中的默认 `error_details:null` 不是显式比较字段。没有配置 `NetworkEventEvaluator`，因此 `network.har` 虽是要求保留的运行 artifact，却不参与这个响应比较。唯一 evaluator 的分数必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`；比较、归一化、evaluator 或任务评估错误均不能通过。

### 原本 draft 是什么

原始 draft 声明 benchmark success 是唯一的 `AgentResponseEvaluator` 接受归一化后的 `RETRIEVE`、`NOT_FOUND_ERROR` 和 `null` `retrieved_data`，从而令 `TaskEvalResult.score` 为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts：前者用于响应比较，后者被描述为用于向评估上下文提供可解析的 `NetworkTrace`；success 要求响应匹配且 evaluator 无错误，failure 包括响应无效、字段不匹配、evaluator 或任务评估错误以及分数非 `1.0`。其 undecided 条件是证据不能确立提供给评估的响应和网络 trace，且没有真实 `TaskEvalResult`；同时说明显式 evaluator error 属于 failure。非空 stronger condition `verify_intended_dislikes` 另行要求 `network.har` 证明所有现存的 `jacyanthis` 所著 `earthporn` submissions 均已被 dislike，或证明匹配集合为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native-network-artifact-not-minimal`
- 为什么修改：尽管案例 726 仅配置了 `AgentResponseEvaluator`，且该跟踪记录不参与其响应比较，但 `network.har` 仍被列为原生决定性 artifact。
- 应如何修改：从原生 `decisive_artifacts` 中移除 `network.har`；仅在其内容可提供有关 Reddit 状态变更证据这一明确的更强条件下保留它。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`undecided-depends-on-irrelevant-trace`
- 为什么修改：原生 `undecided` 规则将无法建立网络跟踪记录作为判定为 `undecided` 的理由，即使完整且真实的智能体响应足以重建唯一配置的比较。
- 应如何修改：将 `undecided` 限定为 `agent_response.json` 缺失、不完整、损坏或来源未经证实，并因此无法重建的情况；明确将完整但无效/为 `null` 的响应、不匹配以及 evaluator 错误保留为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove-redundant-native-trace-condition`
- 为什么修改：冗余的原生网络 artifact 及相关跟踪条件使检查清单超出了最小配置声明的范围。
- 应如何修改：将 `agent_response.json` 用作唯一的原生决定性 artifact，并移除原生决策规则对 `network.har` 的依赖，同时不更改单独的更强条件。

## Case 730

### 原本 case 是什么

原始任务是在 `reddit` 站点的 `news` forum 中，对用户 `Hrekires` 创建的所有 submissions 执行 DisLike。官方 task type 为 `MUTATE`，revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和十个 `NetworkEventEvaluator`。响应 evaluator 检查归一化后的 `task_type=MUTATE`、`status=SUCCESS`，并按非 `RETRIEVE` 任务规则处理配置的 `retrieved_data:null`；十个网络 evaluator 分别要求对 `/sv/129816.json`、`/sv/129808.json`、`/sv/129794.json`、`/sv/129783.json`、`/sv/129594.json`、`/sv/129508.json`、`/sv/43839.json`、`/sv/43781.json`、`/sv/43572.json`、`/sv/43558.json` 存在 `POST` 候选。每个网络检查均为 `last_event_only=true`：选取其 URL 路径与方法过滤后的最后一个候选，再要求归一化 URL 等于无 query 的配置 URL、解析后的 `post_data.choice` 为字符串 `"-1"`、`response_status` 为 `200`；未配置 query 忽略规则。全部 11 个 evaluator 分数都必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 与十个 `NetworkEventEvaluator` 全部得 `1.0`，决定性 artifacts 为 `agent_response.json` 和 `network.har`。它将成功写成响应通过 `MUTATE`/`SUCCESS` 归一化比较，且十个指定 `/sv/<ID>.json` endpoint 的最后匹配 `POST` 均满足 `choice=-1` 和响应状态 `200`；任一响应或网络检查失败、缺少匹配事件或 evaluator error 都是 failure。其 undecided 条件是缺少任一 artifact、无法重建检查且没有官方 `TaskEvalResult`，并说明已存在的无效 artifact 或 evaluator error 不属于 undecided。非空 stronger condition `verify_complete_post_run_dislike_state` 要求额外的已认证 Reddit 运行后状态导出证明 `news` 中所有由 `Hrekires` 创建的 submissions 都处于 acting user 已 dislike 的状态。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_url_query_semantics_omitted`
- 为什么修改：网络事件描述将比较简化为端点路径、`POST choice=-1` 和状态 `200`，遗漏了将每个选定事件的 normalization 后 URL 与所配置的不含查询参数的 URL 进行比较。
- 应如何修改：说明每个 evaluator 均按 `POST` 和配置的路径筛选候选事件，选择最后一个候选事件，随后除了检查请求体和状态外，还要求其 normalization 后 URL（包括未配置查询参数忽略规则时的查询处理）等于所配置的不含查询参数的 URL。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`decisive_artifact_completeness_and_fallback`
- 为什么修改：已声明的证据问题并未要求 artifact 完整，而 `undecided_if` 将保留的官方 `TaskEvalResult` 视为缺失的已声明原始证据的替代品，却没有指明或定义该替代品足以重建所有检查。
- 应如何修改：要求使用完整的 `agent_response.json` 和完整的 `network.har` 进行重建，并将任一 artifact 在运行后丢失、截断、损坏或来源无法解析归类为 `undecided`。不得让未指明的仅含分数的记录取代必需的原始证据。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`success_and_undecided_rules_incomplete`
- 为什么修改：`success` 规则遗漏了 normalization 后 URL/查询相等性，而 `undecided_if` 遗漏了保留完整性和来源故障，并包含一个可能导致原始证据缺失时无法分类的例外。
- 应如何修改：在 `success` 和 `failure` 中加入完整的 URL/查询比较，并将 `undecided` 限定为运行后收集、保留、完整性或来源丢失且因此无法重建的情况。明确将按生成时原样保留的无效输入、没有匹配项的完整跟踪记录、不匹配以及 evaluator 或编排错误保留为 `failure`。

## Case 738

### 原本 case 是什么

原始任务是在 `wikipedia` 和 `map` 站点上，查看从 Carnegie Mellon University 到 Philadelphia 76ers 在 70 年代主场馆的地图路线。任务还要求使用 OSRM direction service，通过所提供 wiki 的地点官方页面查找所需信息，并以坐标搜索起点和终点；官方 task type 为 `NAVIGATE`，revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应 evaluator 检查显式配置的 `task_type=NAVIGATE`、`status=SUCCESS` 及 `retrieved_data` 字段结构；对该非 `RETRIEVE` 任务，`retrieved_data` 的值不作比较。网络 evaluator 使用 `last_event_only=true` 选择最后一个符合导航过滤条件的事件，要求其为 `GET`、`response_status=200`，且 URL 匹配 `^.*/route/v1/.*/-75.1712951,39.9042046;-79.9427192,40.4441897.*$`；`ignored_query_params_patterns=[".*"]` 表示所有 query 参数均被忽略。两个 evaluator 的分数都必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求响应被接受为 `NAVIGATE/SUCCESS`，且最后选中的导航事件为返回 `200` 的 `GET`、URL 匹配 `^.*/route/v1/.*/-75.1712951,39.9042046;-79.9427192,40.4441897.*$`，并忽略全部 query 参数；决定性 artifacts 是 `agent_response.json` 和 `network.har`。它将任一 evaluator 得 `0.0`、报错、响应无法解析或归一化、HAR 中没有所选事件或网络字段不匹配列为 failure；仅在 artifact 缺失、存储损坏或 HAR 已知不完整而无法重建检查时列为 undecided。原始 draft 有两个非空 stronger conditions：`correct_route_direction` 要求 HAR 出现按 `-79.9427192,40.4441897;-75.1712951,39.9042046` 排列的成功 OSRM 请求，并声明这是 Carnegie Mellon University 到 70 年代场馆的方向；`prescribed_wiki_coordinate_lookup` 要求 HAR 证明访问了相关 wiki 页面并对两个端点进行了坐标式地图搜索。

### 需要修改的部分

#### 修改项 1：stronger.additional_conditions

- Finding ID：`unsupported_coordinate_entity_mapping`
- 为什么修改：更强条件断言 `(-79.9427192,40.4441897)` 是 Carnegie Mellon University，`(-75.1712951,39.9042046)` 是 1970 年代的体育场，但没有任何数据包摘录提供这些坐标到实体的关联。
- 应如何修改：移除此更强条件，或在不包含无依据坐标指派的情况下重新表述。保留另有依据的条件，即要求执行规定的 wiki 和坐标搜索工作流。

## Case 743

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建一个名为 `"web_arena"` 的新 public project，并将 Abishek 和 Vinta 添加为 members。官方 task type 为 `MUTATE`，revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和三个 `NetworkEventEvaluator`。响应 evaluator 检查显式配置并归一化后的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data:null`；project evaluator 在 `POST` 与归一化 URL `__GITLAB__/api/v4/projects` 的候选中按 `last_event_only=true` 选择最后一个，要求 `response_status=201`、`post_data.name="web_arena"`、`post_data.visibility="public"`。两个 membership evaluator 使用相同的 `POST` 和锚定 URL pattern `^__GITLAB__/api/v4/projects/\d+/members$` 过滤条件，因此都选择同一最后候选事件，再分别比较共同要求的 `response_status=201`、`access_level=30` 以及各自的 `user_id=5` 或 `user_id=278`。四个 evaluator 的分数必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求最终响应、public project 创建和两个 membership 网络检查共四项全部得 `1.0`，并把 `agent_response.json` 与 `network.har` 列为决定性 artifacts。它写明响应须匹配 `MUTATE`、`SUCCESS` 和 `retrieved_data null`，project 的最后匹配 `POST` 须包含 `name=web_arena`、`visibility=public` 并返回 `201`，两个独立配置的 membership 检查则分别要求最后匹配的 numeric-project member `POST` 具有 `access_level=30`、`user_id=5` 或 `278` 并返回 `201`；任一缺少事件、不匹配或报错均为 failure。其 undecided 仅限 `agent_response.json` 或 `network.har` 缺失或截断而无法重建比较，并把已存在 artifact 导致的 evaluator error 或缺少匹配归为 failure。非空 stronger condition `bind_memberships_to_created_project` 要求依据创建响应中的 project ID，证明用户 `5` 和 `278` 的成功 member additions 都指向该新建 project。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_project_url_semantics`
- 为什么修改：项目 `NetworkEventEvaluator` 仅被描述为筛选“项目 `POST`”；其配置的 URL 被遗漏。
- 应如何修改：说明此 evaluator 使用配置的 normalization 后 URL `__GITLAB__/api/v4/projects` 筛选 `POST` 事件，选择最后一个匹配项，随后比较状态和配置的 post-data 字段。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`insufficient_project_success_rule`
- 为什么修改：`success_if` 未要求项目请求匹配配置的端点 URL。
- 应如何修改：将配置的项目 URL 匹配加入项目创建的 `success` 条件及对应的 artifact 问题。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantic_omission`
- 为什么修改：为保持检查清单简洁而移除了会改变分数的 URL 约束。
- 应如何修改：明确保留项目 evaluator 的 URL 约束，同时使其余内容保持简洁且不包含运行结果。

## Case 746

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建一个名为 `"llm_bulk_inference"` 的新 private project，并将 primer、convexegg 和 abishek 添加为 members。官方 task type 为 `MUTATE`，revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator`、一个 project-creation `NetworkEventEvaluator` 和三个 member `NetworkEventEvaluator`。响应 evaluator 检查显式配置的字段，要求 `task_type`（或支持的 `performed_operation` alias）归一化为 `MUTATE`、`status` 为 `SUCCESS`，并按非 `RETRIEVE` 规则将 `retrieved_data` 处理为 `null`；物化默认字段 `error_details:null` 不是额外的显式 expected 字段。project evaluator 选择最后一个匹配 `POST` 和 GitLab `/api/v4/projects` URL 路径的事件，要求 `response_status=201`、`name=llm_bulk_inference`、`visibility=private`。三个 member evaluator 的方法、锚定 URL pattern `^__GITLAB__/api/v4/projects/\d+/members$` 和 `last_event_only=true` 完全相同，因此都比较同一个最后 qualifying member `POST`：均要求 `response_status=201`、`access_level=30`，并分别要求 `user_id=2367`、`43`、`5`；全部五项得分都必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 native success 要求一个 `AgentResponseEvaluator`、一个 project-creation evaluator 和三个 member-add evaluator 共五项全部得 `1.0`，决定性 artifacts 为 `agent_response.json` 和 `network.har`。它写明响应须通过 `MUTATE/SUCCESS` 解析与归一化，project 的最后匹配 `POST` 须返回 `201` 并包含 `name=llm_bulk_inference`、`visibility=private`，三个“独立”的 last-event-only member 检查须分别满足 `access_level=30`、`user_id=2367`、`43`、`5` 和状态 `201`。完整响应或 HAR 中的缺失匹配、不匹配、解析失败或 evaluator error 被列为 failure；artifact 因保留问题缺失或明确截断、且没有官方 `TaskEvalResult` 解决五项检查时被列为 undecided。非空 stronger condition `final_state_and_project_linkage` 要求额外的运行后 GitLab project-and-members 状态快照或 API export，证明同一个 private `llm_bulk_inference` project 的成员列表同时包含 primer、convexegg 和 abishek。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`member_last_event_selection`
- 为什么修改：检查清单将三个成员检查描述为各自独立选择最后一个 `POST`，但未说明它们相同的 URL/方法筛选器会在比较状态和 post-data 之前选择同一个最终符合条件的事件。
- 应如何修改：说明所有三个成员 evaluator 均选择同一个最终匹配 URL/方法的成员 `POST`，并分别将这一个 normalization 后事件与预期 `user_id` 值 `2367`、`43` 和 `5` 进行比较；更早的成员 `POST` 无法各自独立满足这些配置。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_failure_coverage`
- 为什么修改：网络 `fail` 规则仅适用于完整且可解析的 HAR，导致完整、真实但对 evaluator 无效的跟踪记录或网络/编排错误未得到充分分类；`success` 规则也没有在操作层面明确共享的成员事件选择。
- 应如何修改：围绕单个共享的最终成员事件重写 `success` 和 `failure` 规则，并将产生分数 `0` 的完整真实无效跟踪记录以及 evaluator/编排错误归类为 `failure`，同时将 `undecided` 保留给保留、完整性或来源丢失的情况。

## Case 750

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：创建名为 `agi_index` 的私有项目，使用 HTML GitLab Pages 模板，并将 Vinta Chen 添加为成员。任务 revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。前者检查 `agent_response.json` 经发布版解析与规范化后，显式配置字段是否为 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；物化产生的 `error_details` 并非显式比较字段。第一个网络 evaluator 在完整的非静态事件中按 `POST` 和规范化的 `__GITLAB__/projects` 路径筛选并取最后一个候选，随后完整比较规范化 URL/查询状态、`response_status=302`，以及 `project[name]=agi_index`、`project[path]=agi_index`、`project[namespace_id]=2505`、`project[template_name]=plainhtml`、`project[visibility_level]=0`；不忽略任何查询参数。第二个取最后一个匹配 `^__GITLAB__/api/v4/projects/\d+/invitations$` 的 `POST` 候选，要求完整 URL/查询比较通过、`user_id=278`、`response_status=201`，且仅忽略查询参数 `serializer`；两者均为 `last_event_only=true`、`should_not_exist=false`、`decode_base64_query=false`，未配置查询/POST schema 或 POST 忽略模式。`TaskEvalResult.score` 仅在三个 evaluator 分数全部等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求三个检查都得 `1.0`，并称 `AgentResponseEvaluator` 检查保留的响应、两个 `NetworkEventEvaluator` 检查保留的网络轨迹，由 `TaskEvalResult.create` 作 AND 组合。它把 `agent_response.json` 与两项 `network.har` 检查列为决定性 artifacts，并将成功写成响应满足 `MUTATE/SUCCESS/null`、最后一个项目创建 POST 满足五个表单值和 `302`、最后一个邀请 POST 满足 `user_id=278` 和 `201` 且忽略 `serializer`；失败包括响应解析/规范化或比较失败、缺少相应事件、最后事件的所列字段或状态不匹配以及 evaluator 报错。它把保留证据缺失或截断、因而无法重建 evaluator 结果的情形列为 `undecided`。非空 stronger condition `same_project_final_state` 进一步要求用 `network.har` 和 `Post-run GitLab project-state export or snapshot` 证明邀请 URL 中的数字项目 ID 属于该私有 `agi_index` 项目，项目具有 HTML GitLab Pages 模板内容，且成员列表包含 Vinta Chen。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_network_query_semantics`
- 为什么修改：网络规则没有明确说明 normalization 后 URL 比较包含查询处理：项目创建不忽略任何查询参数，而邀请仅忽略 `serializer`。
- 应如何修改：说明每个选定的最后事件都必须通过完整的 normalization 后 URL 比较，其中项目创建不忽略任何查询参数，邀请仅忽略 `serializer`；所有其他查询差异仍会影响分数。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_invitation_failure_rule`
- 为什么修改：邀请 `fail` 规则遗漏了 evaluator 选择最后一个匹配方法/路径的事件之后发生的 normalization 后 URL/查询不匹配。
- 应如何修改：将完整邀请比较中的任何不匹配（包括未被忽略的查询参数）设为原生 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_fully_preserved`
- 为什么修改：这份检查清单虽然在其他方面较为简洁，但因未将所有影响分数的 URL/查询行为落实为可操作规则而并不完整。
- 应如何修改：加入缺失的 URL/查询 `success` 和 `failure` 条件，不添加运行结果或无关细节。

## Case 752

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：创建名为 `web_agent` 的私有空白仓库。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应 evaluator 检查 `agent_response.json` 经发布版解析与规范化后，显式字段是否为 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`；物化默认值 `error_details` 不属于显式比较字段，且非 `RETRIEVE` 任务会把 `retrieved_data` 规范化为 `null`。网络 evaluator 在非静态事件中按不区分大小写的 `POST` 和规范化 GitLab `/projects` 路径筛选，因 `last_event_only=true` 选择最后一个候选，再要求规范化 URL 完整等于 `__GITLAB__/projects`、`response_status=302`，且 `project[name]=web_agent`、`project[path]=web_agent`、`project[namespace_id]=2505`、`project[visibility_level]=0`；`decode_base64_query=false`、`should_not_exist=false`，没有查询参数忽略、查询 schema、POST 忽略模式或 POST schema，未配置的额外事件及表单字段不参与比较。只有两个 evaluator 均得 `1.0` 且无任务级错误时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 都得 `1.0`，否则或发生评估错误时得 `0.0`。它将 `agent_response.json` 和 `network.har` 作为决定性 artifacts，成功条件写为响应解析、规范化并匹配 `MUTATE/SUCCESS` 对象，以及最后选中的 `POST /projects` 事件满足 `302` 和四个项目表单值；任一响应错误、缺少合格事件、所列状态或表单值不匹配、evaluator 或任务级错误均列为失败。若既无保留的官方 `TaskEvalResult`，又因 `agent_response.json` 或 `network.har` 缺失或截断而没有足够完整输入，则列为 `undecided`。非空 stronger condition `verify_persisted_private_blank_project` 要求额外的 `Post-run GitLab project-state capture containing project metadata and repository or branch listing` 证明 namespace `2505` 中持久存在名为且路径为 `web_agent` 的私有项目，并且没有初始化 commit、branch 或 files。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_url_semantics_omitted`
- 为什么修改：原生 `NetworkEventEvaluator` 描述止于基于路径的选择、方法、状态和表单值，遗漏了会影响分数的比较，即将选定事件的 normalization 后 URL 值与 `__GITLAB__/projects` 进行比较。
- 应如何修改：说明候选事件按 `POST` 和 normalization 后的 `/projects` 路径选择，之后最后一个候选事件还必须在已发布的 URL/查询 normalization 规则下与配置的 URL 完全相等；记录 `decode_base64_query=false`，并说明不忽略任何查询参数或模式。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_decision_rule_overclaims`
- 为什么修改：即使 normalization 后 URL/查询不匹配，书面 `success` 规则仍可能宣告 `success`，且 `failure` 规则未将该不匹配归类为 `failure`。
- 应如何修改：在 `success_if` 中加入 normalization 后 URL 相等性，并在 `fail_if` 中加入选定事件的任何 normalization 后 URL 不匹配，同时保留 `last_event_only=true`、必需的匹配行为、响应状态 `302` 和四个配置的表单值。

## Case 756

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `MUTATE`：使用正确模板创建名为 `11711_gitlab` 的私有 JEKYLL 仓库，以加快开发。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查完整 `agent_response.json` 经代码块/JSON 提取及规范化后，显式配置字段是否匹配 `task_type=MUTATE`、`status=SUCCESS` 和非 `RETRIEVE` 任务的 `retrieved_data=null` 语义；可接受旧字段 `performed_operation`，未配置的 `error_details` 和其他原始额外字段不影响该比较。网络 evaluator 按不区分大小写的 `POST` 方法和规范化的 `__GITLAB__/projects` 路径筛选事件，因 `last_event_only=true` 取最后一个候选，再要求其规范化 URL 等于 `__GITLAB__/projects`、`response_status=302`，且投影后的 POST 值为 `project[name]=11711_gitlab`、`project[path]=11711_gitlab`、`project[namespace_id]=2505`、`project[template_name]=nfjekyll`、`project[visibility_level]=0`。`TaskEvalResult.create` 作合取组合，仅当两个 evaluator 分数均为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求两个 evaluator 都得 `1.0`：响应被接受为 `MUTATE/SUCCESS`，且最后一个匹配 GitLab 项目创建的 POST 具有指定五个表单值和 HTTP `302`；它称 `WebArenaVerifiedEvaluator` 依次运行两者，再由 `TaskEvalResult.create` 合取分数。决定性 artifacts 是 `agent_response.json` 和 `network.har`；成功要求两项检查均通过，失败包括响应结构或值不匹配、没有合格 POST、最后所选事件的 HTTP 状态或所列表单值不匹配，以及任一 evaluator 报错。只有保留的响应或 HAR 缺失或已知不完整、导致无法重建检查且没有官方评估结果时，draft 才标为 `undecided`。非空 stronger condition `persisted_project_state` 要求通过 `Post-run GitLab project metadata export or API snapshot` 额外证明 namespace `2505` 中持久存在名称和路径均为 `11711_gitlab` 的私有项目。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_full_url_semantics`
- 为什么修改：网络检查被表述为对 normalization 后 `/projects` 路径的检查，遗漏了随后将选定事件的 normalization 后 URL 与 `__GITLAB__/projects` 进行比较。
- 应如何修改：区分按方法和 URL 路径筛选候选事件与最终比较，并要求选定的最后一个候选事件的 normalization 后 URL 在已发布的 normalization 规则下匹配配置的预期 URL。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`url_decision_rule_gap`
- 为什么修改：`success_if` 可能接受路径匹配但 normalization 后 URL 未通过配置 URL 比较的事件，而 `fail_if` 未指明此类不匹配。
- 应如何修改：在 `success_if` 中加入 normalization 后 URL 相等性，并将选定事件中的任何 normalization 后 URL 不匹配设为原生 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_omission`
- 为什么修改：虽然操作性检查清单的措辞简洁且不存在运行信息泄漏，但由于仅提及路径，它丢失了一项决定性的配置 URL 约束。
- 应如何修改：在 `benchmark_success`、HAR 问题、`success_if` 和 `fail_if` 中，将仅涉及路径的措辞替换为同时保留基于路径的候选事件选择和完整 normalization 后 URL 比较的简洁措辞。

## Case 760

### 原本 case 是什么

原始任务跨 `map` 与 `shopping_admin` 站点执行 `NAVIGATE`：查出电商客户 Amanda Kim 所居住的城市，并在地图上显示从 Allentown, PA 到该城市的路线和驾车时间，同时使用 OSRM direction service。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应 evaluator 检查 `agent_response.json` 经发布版解析与规范化后是否匹配显式字段 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；物化的 `error_details` 默认值不参与显式比较，非 `RETRIEVE` 任务会把实际 `retrieved_data` 规范化为 `null`。网络 evaluator 选择最后一个 navigation event，要求 `http_method=GET`、`response_status=200`、URL 匹配 `^.*/route/v1/.*/-75.4716115,40.6022552;-74.4041622,40.0757384.*$`，且 `Cookie` 匹配 `^(?!.*_osm_directions_engine=fossgis_osrm_(?:bicycle|foot)).*$`；`ignored_query_params_patterns=[".*"]` 表示忽略全部查询参数，且 `last_event_only=true`。只有两个 evaluator 分数均为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 当且仅当响应被接受为 `NAVIGATE/SUCCESS`、导航任务的 `retrieved_data` 规范化为 `null`，并且最后选中的导航事件满足配置的 URL、`Cookie`、`GET` 和 `200` 条件，两个 evaluator 均得 `1.0`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts；成功是两项检查都通过，失败是响应无法解析、规范化或不匹配，或者缺少导航事件、最后事件违反任一 URL、`Cookie`、`GET`、`200` 条件，任何非 `1.0` 分数或 evaluator 错误也使任务得 `0.0`。它仅在一个或两个 artifact 缺失或不可读、且现有 artifact 未已证明某组件失败时标为 `undecided`。非空 stronger condition `visible_route_and_driving_time` 要求额外保留 `Final map screenshot`，可见地显示 Allentown 到 Amanda Kim 所在城市的路线及驾车时间。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`incomplete_artifacts_not_qualified`
- 为什么修改：artifact 问题提到了 `agent_response.json` 和 `network.har`，但未要求它们是完整、完整性得到保留且可归属于该次运行的副本。完整性具有决定性，因为 evaluator 会选择最后一个导航事件。
- 应如何修改：说明所保留的两个 artifact 都必须完整、可读且可归属于被评估案例；不得根据已知保留不完整的证据推断不存在匹配项或响应无效。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`retention_loss_decision_gap`
- 为什么修改：`fail_if` 在未要求跟踪记录完整的情况下将不存在导航事件视为 `failure`，而 `undecided_if` 未涵盖可读但被截断/不完整的证据或来源丢失。
- 应如何修改：将无匹配项的 `failure` 规则限定于完整 HAR，并将 `undecided_if` 扩展到任何导致无法重建的保留、完整性或来源丢失情况，除非其他完整的保留证据已经确定原生 `failure`。

## Case 763

### 原本 case 是什么

原始任务是在 `map` 站点执行 `NAVIGATE`：使用 OSRM direction service，在地图上显示从 401 Shady Ave, Pittsburgh 到最近 Trader Joe's 的步行路线。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者检查完整 `agent_response.json` 经发布版提取、解析与规范化后是否匹配显式配置的 `task_type=NAVIGATE`、`status=SUCCESS`、`retrieved_data=null`；由于这是非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 都会规范化为 `null`，其值不再单独比较。后者检查完整 `network.har` 中最后一个 evaluator 可见的 navigation event，要求规范化 URL 为 `__MAP__`、方法为 `GET`、`response_status=200`；配置为 `last_event_only=true`，且没有查询参数忽略。`TaskEvalResult.create` 合取两个分数，只有二者都为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求两个官方检查都得 `1.0`：响应被接受为 `NAVIGATE` 和 `SUCCESS`，最后一个 evaluator 可见的导航事件匹配预期 map URL、`GET` 和 `200`。它以 `agent_response.json` 和 `network.har` 为决定性 artifacts；成功条件是两项检查都通过，失败条件是响应未通过 `NAVIGATE/SUCCESS`、HAR 缺少可接受的最后导航事件或该事件不匹配 URL、`GET`、`200`，以及任何 evaluator 或任务评估错误。若任一 artifact 未保留或被截断而无法重建 evaluator 可见内容，draft 将其列为 `undecided`，同时说明保留下来的 `null` 或畸形输入若被 evaluator 拒绝则属于失败。非空 stronger condition `verify_requested_route_semantics` 要求用 `Retained final map screenshot or DOM/accessibility snapshot` 与 `network.har` 额外证明地图确实显示从指定地址到最近 Trader Joe's 的步行路线，并且相应 directions request 使用了 OSRM。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_configured_retrieved_data_semantics`
- 为什么修改：原生规则遗漏了明确配置的预期 `retrieved_data: null`，以及已发布的该字段在此 `NAVIGATE` 任务中的行为。
- 应如何修改：说明 `AgentResponseEvaluator` 对明确配置的 `task_type NAVIGATE`、`status SUCCESS` 和 `retrieved_data null` 字段应用已发布的 parsing 与 normalization，同时阐明对于此非 `RETRIEVE` 任务，缺失或提供的 `retrieved_data` 均被 normalization 为 `null`，且其值不会被单独比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：`undecided_if` 将每个 artifact 缺失或截断的情况都视为 `undecided`，即使另一个保留的 artifact 已经确定 evaluator 分数不为 `1.0`。
- 应如何修改：将 `undecided` 限定为导致无法确定结果的保留、完整性或来源丢失，并对其加以限定，使独立确定的 evaluator `failure` 仍归为 `failure`。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`conflicting_failure_and_undecided_branches`
- 为什么修改：当前的 `fail_if` 和 `undecided_if` 分支相互重叠，可能对同一证据状态作出不同判定。
- 应如何修改：通过赋予已确定的 evaluator `failure` 更高优先级，并仅在证据丢失导致 `success` 与 `failure` 确实无法判定时使用 `undecided`，使这些分支保持一致。

## Case 766

### 原本 case 是什么

原始任务是在 `map` 站点执行 `NAVIGATE`：从 `401 Shady Ave, Pittsburgh` 出发，在地图上显示前往最近的 Amazon 旗下杂货店的步行路线，并使用 OSRM direction service。任务 revision 为 `2`。

### Benchmark 怎么测

配置依次运行 `AgentResponseEvaluator` 和 `NetworkEventEvaluator`。前者对 `agent_response.json` 执行已发布的解析和 normalization，并按显式配置比较 `task_type: "NAVIGATE"`、`status: "SUCCESS"`、`retrieved_data: null`；这是非 `RETRIEVE` 任务，`retrieved_data` 会归一化为 `null`，不另行比较其值，物化出的 `error_details: null` 不是显式比较字段。后者从 `network.har` 的非静态 evaluation events 中选择最后一个被 `NetworkEvent.is_navigation_event` 判定为导航事件，并要求其归一化后匹配 URL `__MAP__`、方法 `GET` 和响应状态 `200`；`last_event_only=true`，即使更早事件匹配，也以最后一个导航类事件为准。仅当两个 evaluator 的 score 都为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 描述为响应通过 `NAVIGATE/SUCCESS` 检查，且 HAR 中最后一个 qualifying navigation event 是对 `__MAP__` 的 `GET` 并返回 `200`；它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts。其 `success_if` 要求两项 evaluator 均为 `1.0`，`fail_if` 将响应不匹配、evaluator error、缺少或不匹配的最后 qualifying event 归为 `TaskEvalResult.score = 0.0`，`undecided_if` 仅保留给 artifacts 缺失或截断，并明确完整 artifact 中的畸形响应或缺失事件属于 failure。非空 stronger condition `verify_requested_route` 进一步要求 `final browser-state capture` 显示指定起点、最近的 Amazon-owned grocery、walking mode 和 rendered route，并由 `network.har` 证明相应的成功 OSRM directions request。原 draft 没有写出显式配置的 `retrieved_data: null`，也没有明确所谓最后 qualifying event 是最后一个由 `NetworkEvent.is_navigation_event` 分类的事件。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_retrieved_data_semantics`
- 为什么修改：原生响应描述仅提及 NAVIGATE/SUCCESS，尽管稀疏原始配置中明确配置了 retrieved_data:null。
- 应如何修改：说明 AgentResponseEvaluator 针对 task_type NAVIGATE、status SUCCESS 和 retrieved_data:null 应用已发布的解析与 normalization，同时阐明在已发布语义下，此非 RETRIEVE 任务会映射/忽略 retrieved-data 值。

#### 修改项 2：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`ambiguous_last_navigation_selection`
- 为什么修改：“最后一个符合条件的导航事件”可能被理解为已经匹配 __MAP__/200 的最后一个事件，但已发布代码会先选择 trace 中最后一个被归类为导航的评估事件，然后再对其进行比较。
- 应如何修改：将选择过程描述为：选择最后一个满足 NetworkEvent.is_navigation_event 的非静态评估事件，随后将该选中事件与 URL __MAP__、GET 和 status 200 进行比较。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：对于完整的 AgentResponse 配置或 evaluator 的最后导航事件选择行为，该 success 规则在操作层面并不充分。
- 应如何修改：使 success 要求按照已发布语义比较所有明确配置的响应字段，并要求选中的最后一个被归类为导航的事件本身——而不仅仅是某个符合条件的事件——匹配 __MAP__/GET/200；在 fail_if 中对应涵盖这些情况。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`preserve_decisive_native_semantics`
- 为什么修改：尽管该检查清单简洁且没有 run 泄漏，但它未保留完整且具有决定性的原生比较语义。
- 应如何修改：保留当前紧凑结构，同时加入 retrieved_data:null/非 RETRIEVE 处理以及无歧义的最后导航事件选择。

## Case 768

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：蓝色、尺码 `33` 的 Cronus yoga pants 到货 `5` 件，要求更新库存。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者解析并归一化 `agent_response.json`，比较显式字段 `task_type: "MUTATE"`、`status: "SUCCESS"`、`retrieved_data: null`；非 `RETRIEVE` normalization 会把缺失或给出的 `retrieved_data` 归一化为 `null`，`legacy performed_operation` 可提供 `task_type`，物化默认值 `error_details: null`不参与显式比较。后者在 `network.har` 中按 `POST` 和 URL 正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/872/type/(simple|configurable)/store/0/set/\d+/back/edit$` 过滤事件，因 `last_event_only=true` 选择最后一个匹配项，并比较 `product[quantity_and_stock_status][qty]` 为字符串 `"5"`、响应状态为 `302`；`should_not_exist=false`、`decode_base64_query=false`，且未配置 ignored query/post parameters 或 schemas。两个 evaluator 的 score 必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native benchmark success 要求响应通过 `MUTATE/SUCCESS`，且最后一个匹配 product `872` 保存请求的数量为 `5`、HTTP 状态为 `302`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 `success_if` 要求两项检查均为 `1.0`，`fail_if` 将响应无效或不匹配、无 qualifying POST、最后一个 qualifying POST 数量或状态错误以及 evaluation error 归为总体 `0.0`；`undecided_if` 仅用于保留材料缺失、不可读或截断，完整但畸形的提交属于 failure。非空 stronger condition `persisted_inventory_state` 要求 post-run shopping-admin product or inventory state snapshot 证明蓝色 size `33` 变体的持久化 stock quantity 为 `5`。原 draft 省略了显式配置的 `retrieved_data: null`，并把决定性 URL 正则简写成 product `872` 的保存 URL，未完整写出 `type/(simple|configurable)/store/0/set/\d+/back/edit` 约束。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`official_semantics_underspecified`
- 为什么修改：原生描述遗漏了明确配置的 AgentResponseEvaluator 预期字段 retrieved_data:null，也没有充分说明所配置的 NetworkEventEvaluator URL pattern，因而无法将被评分的路径与其他产品保存请求区分开来。
- 应如何修改：说明稀疏响应预期明确包含 task_type MUTATE、status SUCCESS 和 retrieved_data null，并采用已发布的非 RETRIEVE normalization，且不比较默认添加的 error_details。还应说明完整配置的产品保存 URL regex 或其全部路径约束，同时保留 POST、last_event_only=true、quantity "5"、status 302 以及适用的非活动默认值。

## Case 770

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：收到 `12` 条白色、尺码 `28` 的 Cora parachute pant，以及 `56` 条蓝色、尺码 `29` 的同款裤子，要求更新 inventory。任务 revision 为 `2`。

### Benchmark 怎么测

配置依次包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 做 extraction、解析和 normalization，比较显式配置的 `task_type: "MUTATE"`、`status: "SUCCESS"`、`retrieved_data: null`；非 `RETRIEVE` 语义会将存在或缺失的 `retrieved_data` 归一化为 `null`，不做 retrieved-data ordering 比较，物化默认值 `error_details: null` 不参与比较。第一个网络 evaluator 要求最后一个匹配 `POST` 与正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/1836/type/simple/store/0/set/\d+/back/edit$` 的事件包含 `product[quantity_and_stock_status][qty]: "112"` 且返回 `302`；第二个以相同语义检查 product `1838`、正则 `^__SHOPPING_ADMIN__/catalog/product/save/id/1838/type/simple/store/0/set/\d+/back/edit$`、数量 `"156"` 和状态 `302`。两项网络检查均为 `last_event_only=true`、`should_not_exist=false`，并按 `ignored_post_data_params_patterns: ["^form_key$"]` 排除该 POST 字段；三个 evaluator score 必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 benchmark success 要求三项检查全部为 `1.0`：响应匹配 `MUTATE`、`SUCCESS` 和 null `retrieved_data`，product `1836` 的最后匹配保存 POST 为 quantity `112`/status `302`，product `1838` 的对应值为 `156`/`302`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 `success_if` 要求响应和两项 last-matching POST 检查全部通过，`fail_if` 将任一响应或网络检查缺失、不匹配或报错归为 task score `0.0`，`undecided_if` 用于仅剩 excerpts 或 summaries、无法重建完整 evaluator inputs 且没有保留官方 `TaskEvalResult` 的情况。非空 stronger condition `persisted_inventory_state` 要求 post-run catalog-state snapshot or export 证明 white/28 的 product `1836` 数量为 `112`、blue/29 的 product `1838` 数量为 `156`。原 draft 未说明非 `RETRIEVE` response normalization，并简写了两个 URL 正则、精确 post-data key 和 `^form_key$` 排除语义。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`under_specified_released_comparisons`
- 为什么修改：原生文本没有说明此 MUTATE 响应通过已发布的提取/解析和 normalization 进行判定；在该语义下，无论 retrieved_data 存在还是缺失，都会 normalization 为 null，而具体化的默认 error_details 并未明确配置。文本还用简写替代了两个精确的网络 URL regexps 和精确的表单字段，并遗漏了已配置的 ^form_key$ 排除项。
- 应如何修改：说明仅使用稀疏的明确配置字段进行已发布的非 RETRIEVE 响应 normalization，并说明两个完整的 URL regexps、POST method、精确的 product[quantity_and_stock_status][qty] 字符串值、status 302、last_event_only 行为以及已配置的 form-key 排除项。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_not_fully_operational`
- 为什么修改：success 规则中对响应“通过”以及“相应的 URL、quantity”的引用本身并未定义已发布的 normalization 或完整的网络谓词，因此可能对 retrieved_data 施加过度限制，或接受错误的保存路径/表单字段。
- 应如何修改：使 success_if 要求已发布的响应比较以及两个精确的最后选中网络事件比较；将无效响应、缺少符合条件的事件、不匹配和 evaluator 错误继续视为 failure，并仅在证据丢失时使用 undecided。

## Case 772

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：删除 Circe fleece 的全部 pending negative reviews。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者解析并归一化 `agent_response.json`，比较显式字段 `task_type: "MUTATE"`、`status: "SUCCESS"`、`retrieved_data: null`；`legacy performed_operation` 可作为 `task_type`，非 `RETRIEVE` normalization 会把省略或给出的 `retrieved_data` 归一化为 `null`，物化默认值 `error_details: null` 不参与比较。后者在 evaluation events 中按 `POST` 和归一化 URL `__SHOPPING_ADMIN__/review/product/delete/id/999/` 过滤，因 `last_event_only=true` 选择最后一个 qualifying event，并要求其完整比较结果包含该 URL、`POST` 和响应状态 `302`；`should_not_exist=false`。仅当两个 evaluator score 都等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 写成 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 都得 `1.0`，其中最后一个匹配 `POST` 到 `__SHOPPING_ADMIN__/review/product/delete/id/999/` 且响应为 `302`；决定性 artifacts 为 `agent_response.json` 和 `network.har`。其 `success_if` 要求响应检查与最后匹配删除事件检查通过，`fail_if` 包括响应比较失败、evaluator error，以及最后 qualifying network event 缺失或不匹配，并令 task score 为 `0.0`；`undecided_if` 仅用于 artifacts 缺失、截断或不可读且无等价 evaluator result，明确可见的不匹配属于 failure。非空 stronger condition `all_qualifying_reviews_absent_post_run` 要求完整 post-run review-state export 或 filtered review-list capture 显示 Circe fleece 中同时满足 pending 和 negative 的 review 数量为零。原 draft 的响应规则只提到 `MUTATE` 和 `SUCCESS`，没有写出显式配置的 `retrieved_data: null` 及其非 `RETRIEVE` normalization。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_agent_response_field_semantics`
- 为什么修改：原生响应描述列出了 MUTATE 和 SUCCESS，但遗漏了明确配置的 retrieved_data:null，也没有描述应用该比较所需的已发布解析/normalization。
- 应如何修改：说明完整响应必须解析/normalization 为类似 dict 的比较形式，其中 task_type（或旧版 performed_operation）normalization 为 MUTATE，status normalization 为 SUCCESS，retrieved_data normalization 为 null；阐明此非 RETRIEVE 任务会将 retrieved_data 映射为 null，并且具体化的 error_details 默认值既未明确配置，也未参与比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`circular_agent_response_success_rule`
- 为什么修改：success_if 将响应判定委托给 evaluator score，而不是说明足以从 artifact 可见信息重建该分数的条件。
- 应如何修改：使 success_if 明确要求针对 MUTATE、SUCCESS 和 retrieved_data:null 执行已发布的响应解析/normalization 比较，同时执行具体的 last-event-only 网络检查。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：尽管该检查清单紧凑且没有 run 泄漏，但它遗漏了一个已配置的预期响应字段，因此尚不是完整且可操作的原生检查清单。
- 应如何修改：以紧凑方式将缺失的响应语义添加到响应 artifact 问题和 success 规则中，不添加 run 结果、trajectories 或无关的 evaluator 细节。

## Case 774

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：删除全部 pending 且少于 `4` stars 的 reviews。任务 revision 为 `2`。

### Benchmark 怎么测

配置一个 `AgentResponseEvaluator` 和三个独立的 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 做 extraction 和 normalization，要求 dict-like response 的显式字段匹配 `task_type: "MUTATE"`（也可由 legacy `performed_operation` 提供）、`status: "SUCCESS"`、`retrieved_data: null`；非 `RETRIEVE` normalization 会将省略或给出的 `retrieved_data` 归一化为 `null`，物化默认值 `error_details: null` 不参与比较。三个网络 evaluator 分别按 `POST` 和归一化删除 URL `__SHOPPING_ADMIN__/review/product/delete/id/351/`、`__SHOPPING_ADMIN__/review/product/delete/id/353/`、`__SHOPPING_ADMIN__/review/product/delete/id/349/` 过滤事件，并各自因 `last_event_only=true` 选择最后一个匹配项，要求完整归一化 URL、方法 `POST` 和响应状态 `302` 均匹配；`should_not_exist=false`、`decode_base64_query=false`，没有启用 body、query、header、cookie、content、schema 或 ignore 约束。四个 evaluator score 必须全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声明 native benchmark success 要求响应通过 `MUTATE/SUCCESS` 结构检查，并且 review IDs `{349, 351, 353}` 的三个删除 endpoint 各自最后一个匹配 `POST` 均返回 `302`；决定性 artifacts 是 `agent_response.json` 和 `network.har`。其 `success_if` 要求全部四个 evaluator score 为 `1.0`，`fail_if` 将响应比较失败或报错、任一 ID 缺少匹配 POST、或最后匹配项的 URL、方法、状态不符归为 task score `0.0`，`undecided_if` 仅用于 artifacts 未保留或不可读，并明确完整 HAR 中缺少事件属于 failure。非空 stronger condition `complete_scoped_state_change` 要求 retained pre-run and post-run shopping-admin review inventory snapshots 证明运行前所有 pending 且少于 `4` stars 的 reviews 都在运行后消失，同时 eligibility set 之外的 reviews 仍存在。原 draft 未说明显式配置的 `retrieved_data: null`、非 `RETRIEVE` normalization，以及物化的 `error_details: null` 不参与比较。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`agent_response_semantics_incomplete`
- 为什么修改：原生响应描述遗漏了一个明确配置的预期字段，以及 model_fields_set 所使用的稀疏配置与具体化默认值之间的区别。
- 应如何修改：说明已发布的响应提取和 normalization 必须生成 task_type MUTATE（接受 performed_operation 作为旧版 alias）、status SUCCESS，并依据预期的 null 对 retrieved_data 进行 normalization；阐明此 MUTATE 任务会将 retrieved_data 映射为 null，包括该字段被省略时，并且具体化的 error_details null 未被明确配置且不参与比较。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`response_success_rule_not_operational`
- 为什么修改：success_if 将响应分支委托给已经计算出的 evaluator score，而不是提供可应用于 artifact 的完整谓词。
- 应如何修改：用可操作规则替换循环的响应条件，对 agent_response.json 中明确配置的 task_type、status 和 retrieved_data 字段应用已发布的提取、normalization 和结构比较。

## Case 778

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：将 size 28 的 Sahara leggings 价格降低 `13.5%`。任务 revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和三个 `NetworkEventEvaluator`。前者对 `agent_response.json` 做已发布的解析与归一化，要求显式配置字段归一化为 `task_type: MUTATE`、`status: SUCCESS` 和 `retrieved_data: null`；这是非 `RETRIEVE` 任务，因此缺失或提供的 `retrieved_data` 均归一化为 null，而物化默认值 `error_details` 不是显式比较字段。后三者分别在 `network.har` 中选取最后一个匹配 `POST` 及锚定 URL `^__SHOPPING_ADMIN__/catalog/product/save/id/1841/type/simple/store/0/set/\d+/back/edit$`、对应将 ID 替换为 `1842`、`1843` 的事件，并要求 `product[price]` 按 `currency` 格式归一化为 `64.88`、响应状态为 `302`；URL/query 比较采用 `decode_base64_query=false`，忽略名称匹配 `isAjax` 的查询参数，且 `should_not_exist=false`。`TaskEvalResult.score` 仅在四个 evaluator 分数全部等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 是四个检查全部得 `1.0`：最终响应通过 `MUTATE/SUCCESS`，且产品 ID `1841`、`1842`、`1843` 的最后匹配保存 `POST` 均含 currency-normalized `product[price]=64.88` 并收到 `302`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，分别用于响应检查以及三个 ID 的保存请求检查，并称 `TaskEvalResult.create` 以合取方式组合分数。其 success 条件要求四项全过；failure 包括响应 evaluator 失败或报错，或完整 HAR 中缺少合格请求、最后匹配请求的价格、URL、方法或状态不符；只有必要 artifact 未保留、不完整或损坏而无法区分不匹配与证据丢失时才是 undecided。非空 stronger condition `persisted_target_prices` 另要求保留前后 shopping-admin 状态快照或 diff，证明三个 ID 确为目标记录，且持久化价格均降低 `13.5%` 并舍入至 `64.88`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_and_response_semantics_incomplete`
- 为什么修改：该检查清单隐含了若干已配置的比较：完整的锚定保存 URL patterns、作为被忽略查询参数名称 pattern 的 isAjax、decode_base64_query=false，以及明确预期的 retrieved_data:null 的非 RETRIEVE normalization。
- 应如何修改：说明以 IDs 1841、1842 和 1843 为参数的通用锚定 URL pattern；明确 last_event_only=true、正向存在性、不进行 base64 query 解码，以及 isAjax query-name 忽略 pattern；并描述响应 parser/normalizer 如何为此非 RETRIEVE 任务比较 MUTATE、SUCCESS 和已配置的 retrieved_data:null。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_and_failure_rules_under_specified`
- 为什么修改：原生决策规则无法独立重建全部三个网络结果，因为它们没有明确说明已配置的 URL 以及 query/base64 行为。
- 应如何修改：使 success 要求每个选中的最后 POST 满足其精确的锚定 URL 以及 normalization 后的 URL/query 比较，并将在完整 trace 中缺少任何此类字段或任何此类字段不匹配视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_fully_preserved`
- 为什么修改：尽管该检查清单简洁且没有 run 泄漏，但它对网络 URL 配置的抽象移除了可能改变官方分数的细节。
- 应如何修改：保留检查清单的紧凑结构，同时在原生语义和规则中加入精确的通用 URL pattern，以及明确的 isAjax/不使用 base64 行为。

## Case 779

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：将 Gwyn Endurance 的黄色衬衫中所有小于 L 的尺码价格降低 `15%`。任务 revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和分别面向产品 ID `1559`、`1562`、`1565` 的三个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 做已发布的提取与归一化，比较显式字段 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；在该非 `RETRIEVE` 任务中，缺失或存在的 `retrieved_data` 都归一化为 null，物化默认值 `error_details` 不属于显式比较字段。每个网络 evaluator 从 `network.har` 选取最后一个匹配 `POST` 和相应锚定路径 `^__SHOPPING_ADMIN__/catalog/product/save/id/{ID}/type/simple/store/0/set/\d+/back/edit$` 的事件，要求 `product[price]` 按 `currency` 归一化后等于 `20.4`、响应状态为 `302`，并在 `decode_base64_query=false` 下忽略名称匹配 `isAjax` 的查询参数、拒绝其他 URL/query 不匹配；`should_not_exist=false`。只有四个 evaluator 分数全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 将 benchmark success 写为 `AgentResponseEvaluator` 通过成功的 `MUTATE` 响应，且产品 ID `1559`、`1562`、`1565` 的三个 `NetworkEventEvaluator` 都在最后匹配保存 `POST` 上验证 currency-equivalent `product[price]=20.4` 和状态 `302`，最终四项均得 `1.0`。它将 `agent_response.json` 与 `network.har` 作为决定性 artifacts，并称 `TaskEvalResult.create` 仅在所有 evaluator 得 `1.0` 时判成功。success 条件分别要求响应检查和三个网络检查通过；failure 包括响应不匹配、缺少配置的保存事件、所选最后事件的 URL、方法、价格或状态错误以及 evaluator 报错；只有 artifact 缺失、不可读或截断而无法重建输入时为 undecided。非空 stronger condition `persisted_catalog_state_and_scope` 要求 catalog 前后状态 diff 证明每个目标变体均持久化降低 `15%`，且任何范围外商品价格都未变化。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_configured_comparison_semantics`
- 为什么修改：原生描述遗漏了已配置的 URL/query 行为，也未说明如何处理 MUTATE 响应中明确配置的 retrieved_data:null 字段。
- 应如何修改：说明三个精确的 normalization 后保存路径 patterns，或与其完全等价的内容；明确 last_event_only=true、被忽略的 query-name pattern 为 isAjax、decode_base64_query=false，并且所有其他 normalization 后的 URL/query 内容必须匹配。描述针对 task_type MUTATE、status SUCCESS 和明确配置的 retrieved_data:null 进行的已发布响应解析/normalization，同时将具体化的 error_details 排除在配置字段之外。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：success_if 可能夸大 success，因为其列举的条件遗漏了网络 query 比较和已配置的响应字段 normalization。
- 应如何修改：使 success_if 在应用 all-evaluators-must-score-1.0 组合之前，要求完成已发布的响应比较，并且对于每个选中的最后事件，要求完成全部已配置的 URL/query、method、货币 normalization 后的 post-data 和 response-status 比较。

## Case 780

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：将白色 Ingrid Running 中尺码 L 及以上的价格增加 `$17`。任务 revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator`，以及分别针对产品 ID `1264` 和 `1267` 的两个 `NetworkEventEvaluator`。响应 evaluator 对 `agent_response.json` 进行已发布的解析和归一化，比较显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；非 `RETRIEVE` 语义会把缺失或提供的 `retrieved_data` 归一化为 null，而物化的 `error_details` 默认值不是显式比较字段。每个网络 evaluator 在 `network.har` 中选择最后一个匹配 `POST` 及锚定 URL `^__SHOPPING_ADMIN__/catalog/product/save/id/1264/type/simple/store/0/set/\d+/back/edit$` 或 ID `1267` 对应 URL 的事件，并要求完整归一化 URL/query 匹配、`product[price]` 按 `currency` 归一化为 `101.0`、响应状态为 `302`；查询参数名匹配区分大小写的 `isAjax` 模式时被忽略，且 `decode_base64_query=false`、`should_not_exist=false`。`TaskEvalResult.score` 仅在三个 evaluator 全部得 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原 draft 声称 benchmark success 要求三个 evaluator 全部得 `1.0`：响应通过 `MUTATE/SUCCESS`，产品 ID `1264` 和 `1267` 的最后匹配网络事件分别通过 `POST`、URL、价格 `101.0` 和响应 `302` 的比较。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并为响应、ID `1264`、ID `1267` 各写了一项 success 条件。failure 包括完整响应比较失败或 evaluator 报错，以及任一 ID 无匹配 `POST`、最后匹配事件价格或状态不符或 evaluator 报错；artifact 丢失或截断导致 evaluator 输入无法重建时为 undecided，而已保留但格式错误或缺少所需匹配属于 failure。非空 stronger condition `verify_persistent_catalog_state` 要求前后 catalog-state diff 证明所有符合条件的变体都恰好增加 `$17` 并保持新价格，且 ID `1264`、`1267` 的运行后价格为 `$101.00`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_configured_comparison_semantics`
- 为什么修改：原生描述将 agent response 简化为 MUTATE/SUCCESS，尽管 retrieved_data:null 已被明确配置，而且它没有说明非 RETRIEVE normalization 会将 retrieved_data 映射为 null。它还遗漏了生效的 isAjax query-ignore 行为以及选中事件的完整 normalization 后 URL 比较。
- 应如何修改：说明稀疏响应字段和已发布的非 RETRIEVE normalization，并描述每个网络 evaluator 的精确 URL pattern、method/path 最后事件选择、忽略 isAjax 的完整 normalization 后 URL 比较、货币 normalization 后的 price、status 和缺失事件行为。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_native_decision_rules`
- 为什么修改：success 和 failure 分支没有在遗漏的 retrieved-data 和 URL/query 语义下明确判定保留的响应或网络事件。
- 应如何修改：使 success 要求全部三个完整的已配置比较，并将任何响应不匹配、缺少网络候选事件、选中事件不匹配——包括 normalization 后的 URL/query 不匹配——或 evaluator/orchestration 错误视为原生 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_minimally_complete`
- 为什么修改：尽管该检查清单简洁且不含 run 结果，但它通过省略可能影响证据审查的已配置比较行为来实现紧凑性。
- 应如何修改：仅添加缺失的 retrieved_data normalization 和 URL/query 比较细节，同时保留当前的双 artifact 结构以及原生 verdict 与更强 verdict 之间的空白分隔。

## Case 781

### 原本 case 是什么

原始任务是在 `shopping_admin` 站点执行 `MUTATE`：将 Desiree 的黑色 fitness tshirts 中 XS 尺码的价格提高 `37%`。任务 revision 为 `2`。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。前者解析并归一化 `agent_response.json`，比较显式配置的 `task_type: MUTATE`、`status: SUCCESS`、`retrieved_data: null`；该非 `RETRIEVE` 任务会将实际 `retrieved_data` 归一化为 null，物化默认值 `error_details` 不是显式比较字段。后者从 `network.har` 选择最后一个匹配 `POST` 与锚定 URL `^__SHOPPING_ADMIN__/catalog/product/save/id/1573/type/simple/store/0/set/\d+/back/edit$` 的事件，要求 `product[price]` 按 `currency` 归一化后等于 `32.88`、响应状态为 `302`，并在 `decode_base64_query=false` 下比较归一化 URL/query、忽略名称匹配 `isAjax` 的查询参数；`should_not_exist=false`。只有两个 evaluator 分数均为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 native benchmark success 要求两个检查均得 `1.0`：`AgentResponseEvaluator` 接受归一化的 `MUTATE/SUCCESS` 且无 retrieved data 的响应，`NetworkEventEvaluator` 接受产品 `1573` 的最后匹配 `POST`，其价格为 `32.88`、响应状态为 `302`。它把 `agent_response.json` 与 `network.har` 列为决定性 artifacts，网络 artifact 的问题还提到 id `1573`、数字 set segment 以及 evaluator 的 URL/query normalization。success 是两个 evaluator 同时通过；failure 是任一分数低于 `1.0` 或报错，包括响应不被接受、无合格网络事件或最后匹配事件不符；只有响应或 HAR 缺失、截断或无法解释而不能重建 evaluator 输入时为 undecided。非空 stronger condition `persisted_catalog_price` 要求通过重新加载产品页或 catalog export 等 fresh post-run read，确认产品 `1573` 是目标黑色 Desiree XS fitness T-shirt，且持久化价格为 `32.88`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_isajax_query_ignore_semantics`
- 为什么修改：已配置的 NetworkEventEvaluator 会忽略名称匹配 `isAjax` 的 query-parameter，但检查清单从未指出这一生效的比较规则。
- 应如何修改：在原生网络规则中明确说明 URL/query 比较应用 `ignored_query_params_patterns: ["isAjax"]`，同时保留最后事件、正向存在性、method、path、status 和货币 normalization 后的 post-data 要求。

## Case 784

### 原本 case 是什么

原始任务是在 `gitlab` 站点执行 `RETRIEVE`：取得当前 repository 的 `master` branch 上 commits 数量最多的 contributor 的 email address。起始 repository 为 `__GITLAB__/CellularPrivacy/Android-IMSI-Catcher-Detector`，任务 revision 为 `2`。

### Benchmark 怎么测

唯一配置的 evaluator 是 `AgentResponseEvaluator`，它对 `agent_response.json` 做已发布的解析和归一化，并按 array-of-strings schema 比较显式字段 `task_type: RETRIEVE`、`status: SUCCESS` 和 `retrieved_data`。`retrieved_data` 必须在 `ordered=false` 语义下精确等于无序单元素数组 `["secupwn@users.noreply.github.com"]`，不能缺失、为 null、错误或包含额外元素；物化的 `error_details: null` 默认值未在 sparse 配置中显式指定，因此不参与比较。本 case 没有 `NetworkEventEvaluator`，所以 `network.har` 内容不影响该邮件响应比较。由于仅有一个 evaluator，只有其分数为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原 draft 声称 sole `AgentResponseEvaluator` 必须把响应解析、归一化为 `task_type: RETRIEVE`、`status: SUCCESS`，且 `retrieved_data` 无序精确等于单元素 `secupwn@users.noreply.github.com`，此时 `TaskEvalResult.score=1.0`。它将 `agent_response.json` 列为响应比较的决定性 artifact，同时也把 `network.har` 列为用于重建 evaluation context、避免 trace-loading error 的决定性 artifact，并注明本 case 没有 network-event assertion。success 要求保留输入可求值且唯一 evaluator 得 `1.0`；failure 包括解析、归一化或比较错误，以及 task type/status 错误或 retrieved data 缺失、null、错误、额外数据和 orchestration/context 错误；提交响应或 trace 无法由缺失、不完整 artifact 重建时为 undecided。其非空 stronger condition `public_response_contract` 进一步要求 `agent_response.json` 本身是有效 `FinalAgentResponse` JSON，`retrieved_data` 必须直接编码为 `["secupwn@users.noreply.github.com"]`，且 `error_details` 为 null 或省略，而不能依赖 code-block extraction、scalar coercion 或未检查的 error-details 值。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`nondecisive_network_har`
- 为什么修改：network.har 被标记为具有决定性，尽管没有配置任何 NetworkEventEvaluator，而且其内容不会影响已配置的 email 比较。
- 应如何修改：从原生 decisive_artifacts 中移除 network.har，并将完整的 agent_response.json 作为唯一具有决定性的 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_based_decision_rules`
- 为什么修改：failure 和 undecided 规则依赖 trace 加载或 trace 保留，尽管无需 trace 即可重建已配置的检查。
- 应如何修改：移除 trace 特定的 success、failure 和 undecided 条件。将完整但无效或不匹配的响应视为 failure，并仅在 agent_response.json 丢失或损坏而导致无法重建时使用 undecided。

#### 修改项 3：stronger.additional_conditions

- Finding ID：`unsupported_stronger_format_contract`
- 为什么修改：更强条件强制执行通用 serialization 和 public-schema 严格性，却没有指出官方 email-retrieval 意图与 evaluator 所检查内容之间的 case 特定差距。
- 应如何修改：将 stronger.additional_conditions 设置为空列表。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_checklist`
- 为什么修改：不具有决定性的 HAR 条目和不必要的 public-response-contract 条件增加了超出此 case 所需最小证据范围的审查内容。
- 应如何修改：移除这两项添加内容，仅保留简洁的原生响应比较语义和响应 artifact。

## Case 785

### 原本 case 是什么

原始任务是在 GitLab 当前仓库 `CellularPrivacy/Android-IMSI-Catcher-Detector` 中，取得 `gh-page` 分支提交次数最多的贡献者的电子邮件地址。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`；它对响应进行解析和规范化，并比较稀疏配置明确指定的 `task_type`、`status` 和 `retrieved_data`。期望值分别为 `RETRIEVE`、`SUCCESS` 和无序数组 `['secupwn@users.noreply.github.com']`；`results_schema` 是字符串数组，因此结果必须规范化为恰好这个单元素数组，重复、缺失、错误或额外元素均不匹配，而物化出的 `error_details: null` 不是显式比较字段。没有 last-event evaluator 或过滤语义；唯一 evaluator 必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求唯一的 `AgentResponseEvaluator` 得分 `1.0`，从而使 `TaskEvalResult.score` 为 `1.0`，并要求规范化后的响应精确匹配 `RETRIEVE`、`SUCCESS` 和单元素邮箱结果。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并把响应及 HAR 可解析、可用于重建评估上下文纳入成功条件。draft 将空值、非对象、字段不符、结果缺失/错误/重复/多余及解析、规范化或评估错误列为 failure；若两个 artifacts 缺失、截断或无法关联到 task 785，则列为 undecided，但明确说已保留的 null 或畸形提交属于 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被称为决定性证据，尽管案例 785 唯一配置的检查是 `AgentResponseEvaluator`，且数据包所表示的追踪内容均不影响电子邮件比较。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并保留完整的 `agent_response.json` 作为最小充分的原生 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：这些规则要求存在可求值的 HAR 才能判定 success，将与 HAR 相关的求值错误归类为原生 failure，并将 HAR 缺失或未关联归类为 undecided。
- 应如何修改：围绕对所保留响应进行已发布版本的求值，重写 `success_if`、`fail_if` 和 `undecided_if`；仅在 `agent_response.json` 丢失、截断或溯源失败时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：HAR 条目和依赖 HAR 的规则向原本紧凑且仅涉及响应的检查清单中添加了非决定性材料。
- 应如何修改：移除所有原生 HAR 要求，同时保留响应 evaluator 配置的字段、normalization、比较、组合和证据完整性规则。

## Case 786

### 原本 case 是什么

原始任务是在 GitLab 当前仓库 `vinta/awesome-python` 中，取得 `master` 分支提交次数最多的贡献者的提交数量。站点为 `gitlab`，task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，负责解析并按 schema 规范化响应，然后比较显式配置的 `task_type`、`status` 和 `retrieved_data`。期望值为 `RETRIEVE`、`SUCCESS` 和无序数值数组 `[414]`；`results_schema` 是 number 数组，所以必须规范化为恰好包含数值 `414` 的单元素数组，物化默认值 `error_details: null` 不参与显式比较。没有 last-event evaluator 或过滤语义；唯一 evaluator 得分必须为 `1.0`，任务按 all-evaluators-must-equal-`1.0` 规则组合为 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 是 `TaskEvalResult.score = 1.0`，要求唯一 `AgentResponseEvaluator` 将响应规范化为 `RETRIEVE`、`SUCCESS` 和无序单元素数值结果 `[414]` 并得分 `1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并要求响应与 trace 能让评估无错误完成。draft 将响应不可解析或规范化、类型或状态不符、`retrieved_data` 缺失、为空或不等于数值 `414`，以及响应/trace/context/orchestration 错误列为 failure；将 artifacts 缺失、截断或损坏且无法确定响应或评估上下文列为 undecided，同时说明完整记录所显示的无效输入或评估错误仍属 failure。`stronger.additional_conditions` 为空。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`non_decisive_network_trace`
- 为什么修改：`network.har` 被表述为决定性证据，尽管唯一配置的 evaluator 仅比较 agent 响应。
- 应如何修改：从 `decisive_artifacts` 中移除 `network.har`，并使用完整的 `agent_response.json` 作为该配置检查的最小充分运行后证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`trace_dependent_decision_rules`
- 为什么修改：尽管不存在 `NetworkEventEvaluator`，决策规则仍以追踪的解析或保留情况作为 success、failure 和 undecided 结果的条件。
- 应如何修改：围绕对 `agent_response.json` 进行已发布版本的解析、normalization 和比较来重写规则；仅在该决定性响应证据或其溯源信息丢失时使用 undecided。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_trace_material`
- 为什么修改：追踪 artifact 及相关的通用上下文验证措辞向原本紧凑且仅涉及响应的检查清单中添加了非决定性材料。
- 应如何修改：删除追踪 artifact 和追踪专属条款，同时保留准确的响应谓词和 `all-scores-equal-1.0` 组合方式。

## Case 789

### 原本 case 是什么

原始任务是在 GitLab 的 `huggingface dataset` 仓库创建标题为 `"WebAgent Support Plan"` 的 issue，正文询问团队是否计划在下个季度支持 Webagent。站点为 `gitlab`，尽管任务要求创建 issue，配置中的 task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一配置的 `AgentResponseEvaluator` 只测最终响应：经提取、解析和规范化后，稀疏配置显式指定的 `task_type`、`status`、`retrieved_data` 应分别为 `RETRIEVE`、`NOT_FOUND_ERROR`、`null`；`results_schema` 为 `null`，物化出的 `error_details: null` 不参与比较。已 review 的源码口径还表明可从受支持的 JSON 代码块提取响应，缺少 `task_type` 时可使用 `performed_operation` fallback，缺失或可规范化为空的 `retrieved_data` 与期望 `null` 比较；由于结果为 `null`，`ordered: false` 没有实际排序影响。没有网络事件、filter 或 last-event evaluator，因而该 evaluator 不验证 issue 是否创建；它必须得分 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 要求没有 orchestration error，且唯一 `AgentResponseEvaluator` 将响应匹配为 `RETRIEVE`、`NOT_FOUND_ERROR`、`retrieved_data: null`，使 `TaskEvalResult` 得分 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为 native 决定性 artifacts，并将 HAR 可解析、评估能够到达响应 evaluator 纳入成功判断。draft 将输入或编排/评估错误、畸形响应及任一规范化字段不匹配列为 failure；若未保留实际评估输入且也没有官方结果，则列为 undecided。其非空 stronger condition `verify_requested_issue_creation` 另行要求用 `network.har` 证明在目标仓库成功创建了标题和正文均符合要求的 issue，并明确指出官方响应 evaluator 本身不检查该 GitLab mutation。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_har_not_case_decisive`
- 为什么修改：对于唯一配置的 evaluator 为 `AgentResponseEvaluator` 的案例，`network.har` 被错误地纳入最小原生决定性 artifact 集合。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并根据完整的 `agent_response.json` 重建配置的原生检查。仅在更强的议题创建条件下保留 `network.har`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`har_loss_wrongly_affects_native_decision`
- 为什么修改：这些规则使接受判定和所保留证据的 undecided 状态依赖所有提供的输入，包括非决定性的 HAR。
- 应如何修改：使原生 success 和 failure 取决于对完整响应进行已发布版本的处理，并将 `undecided_if` 限定为 `agent_response.json` 丢失、损坏、不完整或溯源存在歧义的情况。完整但无效或不匹配的响应必须仍判定为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_nonminimal_native_trace_clause`
- 为什么修改：原生部分包含与唯一配置的响应比较无关且多余的追踪/配置验证 artifact 和问题。
- 应如何修改：删除原生 HAR 条款及相关的通用必需输入措辞，同时保留准确的响应解析、normalization、比较、错误和 `all-evaluators` 组合规则。

## Case 792

### 原本 case 是什么

原始任务是在 shopping 站点购买 `Beauty & Personal Care` 类别中评分最高且价格严格低于 `$20` 的商品，并在购物车非空时先丢弃其中所有商品。站点为 `shopping`，配置中的 task type 为 `RETRIEVE`。

### Benchmark 怎么测

配置中只有一个 `AgentResponseEvaluator`，它解析并规范化最终响应，再比较稀疏配置明确指定的 `task_type: RETRIEVE`、`status: ACTION_NOT_ALLOWED_ERROR` 和 `retrieved_data: null`；`results_schema` 为 `null`，物化默认字段 `error_details: null` 不参与比较。源码口径允许解析普通或 fenced JSON，缺少 `task_type` 时可由 `performed_operation` fallback 提供；缺失、null 或符合规则的空 `retrieved_data` 会规范化为 `null`，额外原始字段被忽略，而规范化为非 null 或触发错误的值不匹配。没有购物网络事件、filter 或 last-event evaluator，因此不测清空购物车或实际购买；唯一 evaluator 必须为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 要求唯一 `AgentResponseEvaluator` 将响应结构化匹配为 `RETRIEVE`、`ACTION_NOT_ALLOWED_ERROR`、`retrieved_data: null` 并得分 `1.0`，从而令 `TaskEvalResult.score = 1.0`。它把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，尽管同时注明未配置 task-specific network-event comparison，并把 HAR 解析或 orchestration 错误列为 failure。响应结构或期望字段不匹配也被列为 failure；响应或 HAR 缺失、截断或无法关联到 reviewed run 且没有完整官方结果时列为 undecided。非空 stronger condition `fulfill_stated_shopping_outcome` 要求用 `network.har` 证明清除了所有既有购物车商品，并成功购买严格低于 `$20` 的最高评分 `Beauty & Personal Care` 商品。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`network.har` 被错误地指定为决定性原生证据，尽管未配置 `NetworkEventEvaluator`，且 `AgentResponseEvaluator` 读取的是 `agent_response_raw`。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`，并将完整且绑定溯源信息的 `agent_response.json` 用作重建配置比较的唯一最小 artifact。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：这些规则使原生 success、failure 和 undecided 状态依赖 HAR 的保留或解析。
- 应如何修改：移除原生 HAR 依赖关系。仅在 `agent_response.json` 丢失、截断或溯源失败时使用 undecided；将完整但无效或不匹配的响应以及响应 evaluator 错误归类为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`BF-3`
- 为什么修改：不必要的 HAR artifact 及其相关规则使原生检查清单不再具备最小性。
- 应如何修改：删除冗余的原生 HAR artifact 和 HAR 专属决策措辞，同时保留在单独的更强条件下对购物证据的使用。

## Case 793

### 原本 case 是什么

原始任务是在 shopping 站点购买 `Men clothing` 类别中评分最高、价格严格高于 `$50` 且低于 `$129.99` 的商品，并在购物车非空时丢弃既有商品。站点为 `shopping`，配置中的 task type 为 `RETRIEVE`。

### Benchmark 怎么测

唯一的 `AgentResponseEvaluator` 对最终响应进行提取、解析、规范化和结构比较，只投影稀疏 expected 中显式存在的 `task_type`、`status`、`retrieved_data`；期望分别为 `RETRIEVE`、`ACTION_NOT_ALLOWED_ERROR` 和 `null`，`results_schema` 为 `null`，物化的 `error_details: null` 不比较。源码口径支持 JSON/代码块提取，缺失 `task_type` 时可由 legacy `performed_operation` fallback 补给，缺失或可规范化为空的 `retrieved_data` 与 `null` 匹配；`ordered: false` 对 null 结果无排序作用。没有购物网络事件、filter 或 last-event evaluator，因此不测购物车和购买结果；唯一 evaluator 得分为 `1.0` 时，all-evaluators 组合才产生 `TaskEvalResult.score = 1.0`。

### 原本 draft 是什么

原始 draft 声称 native benchmark success 要求响应解析和规范化为 `RETRIEVE`、`ACTION_NOT_ALLOWED_ERROR`、`retrieved_data: null`，唯一 `AgentResponseEvaluator` 得分 `1.0`，最终任务分为 `1.0`。它把 `agent_response.json` 与 `network.har` 都列为决定性 artifacts，并要求 trace 存在且可解析以构建评估上下文，同时承认购物活动不由唯一 evaluator 比较。draft 将非对象响应、task type/status 缺失或不符、非 null/非空结果、结构不匹配以及 trace/context/evaluator 错误列为 failure；未保留官方结果且无法确定提交给评估的响应和 trace 时列为 undecided。非空 stronger condition `verify_official_shopping_goal` 要求用 `network.har` 证明清空初始购物车，并成功购买价格严格位于 `$50` 与 `$129.99` 之间的最高评分 `Men clothing` 商品。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`unnecessary_native_network_har`
- 为什么修改：`network.har` 被列为原生决定性 artifact，尽管未配置 `NetworkEventEvaluator`，且唯一的 `AgentResponseEvaluator` 从 agent 响应中提取其实际值。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。它可以继续作为明确规定的更强购物结果条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_trace_undecided_rule`
- 为什么修改：原生 undecided 规则将无法确定准确的已提供追踪视为阻碍重建的因素，尽管该案例配置的 evaluator 并不比较追踪内容。
- 应如何修改：将原生 undecided 状态限定为影响准确已提供 agent 响应的丢失、损坏或溯源歧义。明确说明，仅丢失所保留的追踪不会使原生响应比较变得无法判定；完整但无效的响应和已确定的 evaluator 错误仍为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`nonminimal_native_artifact_set`
- 为什么修改：冗余的原生 `network.har` 条目降低了检查清单的紧凑性，并混淆了批量保留与案例决定性证据。
- 应如何修改：将 `agent_response.json` 用作唯一的原生决定性 artifact，并将 `network.har` 限定用于有正当依据的更强条件。

## Case 795

### 原本 case 是什么

原始任务是在 `shopping` 站点把“第二近的一笔订单”的配送地址改为 `6726 McPherson Blvd, Pittsburgh, PA`。这是 task type 为 `MUTATE` 的任务。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`：前者对响应进行解析和非 `RETRIEVE` 归一化，比较显式期望的 `task_type=MUTATE`、`status=ACTION_NOT_ALLOWED_ERROR`、`retrieved_data=null`；物化出的 `error_details=null` 并非稀疏配置中的比较字段。后者在 `network.har` 中筛选匹配渲染后 `__SHOPPING__/sales/order/history/` 路径的 `GET` 候选，并因 `last_event_only=true` 选择最后一个，要求其归一化 URL、方法及 `response_status=200` 均匹配。`TaskEvalResult.score` 仅在两个 evaluator 的分数都等于 `1.0` 时为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求 `AgentResponseEvaluator` 接受归一化后的 `MUTATE/ACTION_NOT_ALLOWED_ERROR` 响应，同时 `NetworkEventEvaluator` 接受最后一个匹配 `__SHOPPING__/sales/order/history/` 的 `GET` 且状态为 `200`；两项均为 `1.0` 时 `TaskEvalResult.score` 才为 `1.0`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并把响应不匹配或报错、没有匹配请求、最后匹配项不符合条件、网络 evaluator 报错及任务级编排错误归为 failure。它把所需 artifact 未保留或无法关联到本次运行、因而不能重建比较的情形归为 undecided，同时称已保留但自身 malformed 的 artifact 属于 failure。非空 stronger condition `actual_delivery_address_change` 另要求 `Post-run shopping order-state snapshot` 证明第二近订单的配送地址确已变为指定地址。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`complete_artifact_requirement`
- 为什么修改：检查清单列出了 `agent_response.json` 和 `network.har`，但从未要求保留完整副本；仅具备可求值性不足以从可能不完整的 HAR 中重建缺失检查和末事件检查。
- 应如何修改：明确规定，这两个 artifact 都必须完整、忠实地保留并与该次运行关联，其内容才能决定原生 success 或 failure。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`integrity_undecided_boundary`
- 为什么修改：undecided 规则排除了运行后的截断或损坏，并且未区分保留过程中的损坏与实际提交给 evaluator 的畸形内容。
- 应如何修改：将已证实且阻碍重建的收集、保留、完整性或溯源损失判定为 undecided；另行明确，完整且忠实的副本中如果 evaluator 输入无效、为 null、格式错误、不匹配或不存在匹配项，则判定为原生 failure。

## Case 796

### 原本 case 是什么

原始任务是在 `shopping` 站点把用户在 2023 年最早的一笔订单的配送地址改为 `155 5th Street, San Francisco, CA`。这是 task type 为 `MUTATE` 的任务。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`：前者经发布版解析和非 `RETRIEVE` 归一化后，比较 `task_type=MUTATE`、`status=ACTION_NOT_ALLOWED_ERROR`、`retrieved_data=null`，而默认物化的 `error_details=null` 未在稀疏配置中显式设置。后者筛选归一化路径匹配 `__SHOPPING__/sales/order/history/` 的 `GET` 事件，因 `last_event_only=true` 取最后一个候选，并要求 URL、`GET` 方法和默认 `response_status=200` 匹配。只有两个 evaluator 都得到 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 `TaskEvalResult.score=1.0` 要求响应归一化为 `task_type=MUTATE`、`status=ACTION_NOT_ALLOWED_ERROR`、`retrieved_data=null`，且最后一个匹配订单历史页的 `GET` 的状态为 `200`。它以 `agent_response.json` 和 `network.har` 为决定性 artifacts；任一 evaluator 非 `1.0` 或报错、响应结构比较失败、HAR 缺少合格事件或最后匹配事件的 URL、方法、状态不符都属于 failure。它把响应或 HAR 缺失、截断或被非等价证据替代且没有保留的 evaluator 结果能确定两项分数的情形列为 undecided，并明确把由缺失或 malformed evaluator 输入产生的已记录非 `1.0` 结果算作 failure。非空 stronger condition `verify_requested_address_change` 要求 `Post-run shopping order-state snapshot or export` 枚举 2023 年订单、识别最早一笔，并证明其配送地址为指定地址。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`BF-1`
- 为什么修改：`native.undecided_if[0]` 允许仅能确定两个分数的已保留 evaluator 结果替代缺失或截断的 `agent_response.json` 或 `network.har`，因此重建不再要求使用指定的决定性证据。
- 应如何修改：移除这种替代方式。原生 success 判定必须具备完整的 `agent_response.json` 和 `network.har`，或真正等效的已保留原始证据；仅在运行后的保留、完整性或溯源损失阻碍重建时使用 undecided。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`BF-2`
- 为什么修改：`undecided_if` 中的 evaluator 结果例外情况削弱了证据规则，允许在决定性 artifact 丢失后仅凭分数判定 success。
- 应如何修改：明确规定，success 要求根据完整的决定性 artifact 重建两项配置的比较。完整但无效或为 null 的响应、不存在所需匹配项的完整追踪、evaluator 可见的不匹配以及 evaluator/任务错误均应判定为 failure，而非 undecided。

## Case 799

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建新群组 `n-lab`，并加入成员 `patou`、`egpast`、`westurner`、`jontutcher`。这是 task type 为 `MUTATE` 的任务。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：响应 evaluator 比较显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`，其中非 `RETRIEVE` 归一化将 `retrieved_data` 置为 `null`，物化默认值 `error_details=null` 不是稀疏配置的比较字段。第一个网络 evaluator 取最后一个匹配 `POST __GITLAB__/groups` 的候选，要求 `group[name]=n-lab`、`group[path]=n-lab` 和 `response_status=302`；第二个取最后一个匹配 `POST ^__GITLAB__/api/v4/groups/\d+/invitations$` 的候选，要求 `user_id="400,443,561,586"` 经 `string_list` schema 归一化后匹配且状态为 `201`。两个网络比较都忽略字面 query 参数 `serializer`，且 `last_event_only=true`；只有三个 evaluator 分数全部为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 benchmark success 要求一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator` 全部得 `1.0`：响应匹配 `MUTATE/SUCCESS`，最后匹配的群组创建 POST 满足 `n-lab`、状态 `302`，最后匹配的邀请 POST 的 `user_id` 为 `400,443,561,586` 并经 `string_list` 归一化、状态为 `201`。它将 `agent_response.json` 和 `network.har` 列为决定性 artifacts，但没有写出显式的 `retrieved_data=null` 比较和忽略 `serializer` query 参数的规则。任一检查得 `0.0` 或报错、响应不匹配、所需最后事件缺失或完整归一化比较失败均被列为 failure；artifact 缺失、不可读或不完整到无法评估全部三项且现有证据尚未确定失败时为 undecided。非空 stronger condition `verify_persisted_group_membership` 要求 `Post-run GitLab group-state snapshot or API export` 证明 `n-lab` 持久存在并包含四名指定用户。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_configured_comparison_details`
- 为什么修改：检查清单将响应检查简化为 `MUTATE`/`SUCCESS`，并将网络检查简化为通用的 normalized 匹配，遗漏了稀疏响应配置中的 `retrieved_data=null`，以及两个网络配置中的 `ignored_query_params=[serializer]`。
- 应如何修改：明确说明，响应比较使用稀疏配置的 `task_type`、`status` 和 `retrieved_data` 字段，同时排除具现化的 `error_details` 默认值；并且每项网络 URL 比较都忽略字面量 `serializer` 查询参数。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_not_fully_operational`
- 为什么修改：success 规则未提供足够细节，无法辨别仅包含被忽略的 `serializer` 查询参数的 URL 是否通过，也无法重建精确的响应字段比较。
- 应如何修改：将稀疏响应字段集合和忽略 `serializer` 的行为直接添加到 `success_if` 中，并使 `fail_if` 仅在应用配置的 normalization 和忽略规则后生效。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_omitted`
- 为什么修改：检查清单虽然紧凑且不存在运行信息泄漏，但这种紧凑性是通过删除会影响分数的有效配置实现的。
- 应如何修改：仅添加缺失的 `retrieved_data`/`error_details` 区分和 `serializer` 查询参数允许规则，同时保留现有紧凑结构。

## Case 800

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建新群组 `x-lab`，并加入成员 `JonasVautherin`、`dilipchandima`、`dawiss1337`、`bmyun`、`DCMJY`。这是 task type 为 `MUTATE` 的任务。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：响应 evaluator 经解析和归一化后比较稀疏显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`，而 `error_details=null` 是未显式配置的物化默认值。群组创建检查选择最后一个匹配 `POST __GITLAB__/groups` 的候选，要求 `group[name]=x-lab`、`group[path]=x-lab`、状态 `302`；邀请检查选择最后一个匹配锚定正则 `^__GITLAB__/api/v4/groups/\d+/invitations$` 的 POST 候选，要求 `user_id="632,64,86,96,340"` 经对象内 `string_list` schema 归一化后匹配、状态 `201`。两个网络 evaluator 均为 `last_event_only=true` 并忽略 query 参数 `serializer`；三个分数必须全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 `TaskEvalResult.score=1.0` 要求 `AgentResponseEvaluator`、`x-lab` 群组创建 `NetworkEventEvaluator` 和成员邀请 `NetworkEventEvaluator` 三项均为 `1.0`。它以 `agent_response.json` 和 `network.har` 为决定性 artifacts，要求响应匹配 `MUTATE/SUCCESS`、最后匹配的创建事件满足 `x-lab` 表单字段与状态 `302`、最后匹配的邀请事件以 `string_list` 归一化匹配 `632,64,86,96,340` 且状态为 `201`；但未写明 `retrieved_data=null`、忽略 `serializer` 及精确的邀请 URL 正则语义。任一结果非 `1.0`，包括响应不匹配或报错、任一最后事件缺失或不匹配，均为 failure；响应或 trace 缺失、不可读或不完整且没有保留的官方评价结果能确定该项时为 undecided。非空 stronger condition `persisted_x_lab_membership` 要求 `Post-run GitLab group-and-members state snapshot or equivalent retained API responses` 证明同一个 `x-lab` 群组持久存在并包含五名指定用户。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_native_evaluator_details`
- 为什么修改：原生描述将响应预期简化为 `MUTATE`/`SUCCESS`，尽管已显式配置 `retrieved_data:null`；它还遗漏了两个 evaluator 的忽略查询参数 `serializer`。此外，它仅笼统地提及邀请 URL，且未明确标识在已发布版本的 URL/方法预筛选之后选中的末事件。
- 应如何修改：明确说明，已发布版本的解析和 normalization 必须匹配稀疏显式字段 `task_type` 为 `MUTATE`、`status` 为 `SUCCESS` 以及预期的 `retrieved_data:null`，且不得将具现化的 `error_details:null` 视为已配置。对于两个网络 evaluator，明确说明在 URL 查询比较期间忽略 `serializer`，标识带锚点和数字捕获组的邀请 URL pattern，并相对于已发布版本的 URL/方法候选过滤器定义 `last_event_only`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`incomplete_success_rule`
- 为什么修改：`success_if` 未完整规定会影响分数的响应比较和 URL 查询比较，因此可能在尚未依据所有配置规则检查证据时错误地宣称 success。
- 应如何修改：扩展 `success_if`，要求对响应的稀疏显式 `retrieved_data:null` 进行 normalization，并执行两项忽略 `serializer` 的网络比较、使用准确的邀请 URL pattern，以及在 URL/方法过滤后进行 `last_event_only` 选择。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_preserved`
- 为什么修改：尽管检查清单紧凑且不包含运行结果，但它通过删除会影响分数的有效语义实现简洁。
- 应如何修改：用简洁措辞替换原生 artifact 问题和 success 规则，在不添加轨迹或运行专属细节的情况下保留 `retrieved_data:null`、排除 `serializer` 查询参数、邀请 URL regex 和精确的末事件选择。

## Case 802

### 原本 case 是什么

原始任务是在 `gitlab` 站点创建新群组 `coding_friends`，并加入成员 `qhduan` 和 `Agnes-U`。这是 task type 为 `MUTATE` 的任务。

### Benchmark 怎么测

配置包含一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：响应 evaluator 比较稀疏显式字段 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`，非 `RETRIEVE` 归一化使缺失或已有的 `retrieved_data` 均归一为 `null`，而物化的 `error_details=null` 未显式配置。群组创建检查选择最后一个匹配 `POST __GITLAB__/groups` 的候选，要求 `group[name]=coding_friends`、`group[path]=coding_friends`、状态 `302`；邀请检查选择最后一个匹配 `POST ^__GITLAB__/api/v4/groups/\d+/invitations$` 的候选，要求 `user_id="196,244"` 经 `string_list` schema 归一化后匹配、状态 `201`。两项网络检查均有 `last_event_only=true`、`should_not_exist=false`，禁用 base64 query 解码并忽略字面 query 参数 `serializer`；只有三个 evaluator 全为 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声称 native success 要求三项 evaluator 全为 `1.0`：`agent_response.json` 通过 `MUTATE/SUCCESS` 及 `retrieved_data=null` 的归一化比较，`network.har — group creation event` 中最后匹配的 `/groups` POST 带有两个 `coding_friends` 字段且状态为 `302`，`network.har — group invitation event` 中最后匹配的数字群组邀请 POST 以 `string_list` 匹配 `196,244` 且状态为 `201`。它没有写明忽略 `serializer` 和禁用 base64 query 解码；任务评价报错、响应比较失败或任一所需最后事件缺失或不匹配均为 failure。它把 `agent_response.json` 或 `network.har` 遗漏、截断且没有保留的官方逐 evaluator 结果足以确定三项分数的情形列为 undecided，并称截图或叙述不能单独决定 native score。非空 stronger condition `same_group_final_membership` 要求 `Post-run GitLab group/member state snapshot or API export` 证明同一个 `coding_friends` 群组最终同时包含 `qhduan` 和 `Agnes-U`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`network_normalization_omitted`
- 为什么修改：两个 `NetworkEventEvaluator` 描述均遗漏了 `serializer` 是被忽略的字面量查询参数，以及 `decode_base64_query` 为 `false`。响应描述也未明确说明稀疏配置字段的边界。
- 应如何修改：说明两个网络检查所配置的查询 normalization，并明确响应比较涵盖稀疏原始配置中的 `task_type`、`status` 和 `retrieved_data`，不涵盖具现化的 `error_details`。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`success_rule_incomplete`
- 为什么修改：`success_if` 无法完整重建两个网络分数，因为它没有说明配置的查询参数和 base64 行为。
- 应如何修改：将 success 的条件规定为：最后一个 URL/方法候选项满足已发布版本的 URL normalization，其中忽略 `serializer`、禁用 base64 解码，并且所有未忽略的查询组成部分仍须进行比较。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`decisive_semantics_not_minimal_complete`
- 为什么修改：尽管检查清单简洁且不存在运行信息泄漏，但它通过删除已配置且会影响分数的查询 normalization 实现紧凑性。
- 应如何修改：添加缺失的查询/base64 语义，不添加无关的原始输入特性或运行声明。

## Case 803

### 原本 case 是什么

原始任务是在 GitLab 新建名为 `webagent` 的群组，并添加成员 `pandey2000, sayakpaul, sayakpaul`，其中 `sayakpaul` 在指令中重复出现。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置了一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`。前者对 `agent_response.json` 进行解析、归一化和比较，要求 `task_type` 为 `MUTATE`、`status` 为 `SUCCESS`、`retrieved_data` 为 `null`；第一个网络检查从 `network.har` 选择归一化 URL 匹配 `__GITLAB__/groups` 的最后一个 `POST` 候选，要求 `group[name]=webagent`、`group[path]=webagent` 且响应状态为 `302`；第二个选择匹配 `^__GITLAB__/api/v4/groups/\d+/invitations$` 的最后一个 `POST` 候选，要求 `user_id` 在 `string_list` 归一化下匹配 `223,224`，且响应状态为 `201`。两个网络 URL 比较都忽略查询参数 `serializer`，并启用 `last_event_only=true`；只有三个 evaluator 分数全部等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 benchmark success 要求三个检查全部为 `1.0`：成功的 `MUTATE` 响应、最后一个匹配的群组创建 `POST` 和最后一个匹配的邀请 `POST`；但它没有写明两个网络检查会忽略查询参数 `serializer`。它把 `agent_response.json` 和 `network.har` 列为决定性 artifacts，并将响应不匹配、所需最后事件缺失或不匹配、以及 evaluator 或任务级错误判为 failure；仅当证据缺失或不完整、无法重建检查且没有完整官方 `TaskEvalResult` 时判为 undecided。非空 stronger condition `members_bound_to_created_group` 还要求额外的 GitLab 群组及成员状态快照或 API capture 证明名为且路径为 `webagent` 的群组存在，并且 `pandey2000` 与 `sayakpaul` 属于同一群组。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_ignored_query_parameter_semantics`
- 为什么修改：两项网络检查描述均未说明，所配置的 URL 规范化会忽略查询参数 `serializer`。由于两个 `NetworkEventEvaluator` 实例都主动配置了此例外情况，因此该检查清单未保留所有与评分相关的比较规则。
- 应如何修改：说明对于两个网络 evaluator，URL 匹配/比较均忽略名为 `serializer` 的查询参数，同时保留现有的 POST、URL、最后事件、请求体 schema 和状态要求。

## Case 804

### 原本 case 是什么

原始任务是在 GitLab 将关于 dialog components 中 flash alerts 的 issue 分配给当前用户，并通过 tag `primer` 使其成为参与者。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置了一个 `AgentResponseEvaluator` 和两个 `NetworkEventEvaluator`：响应检查要求归一化后的 `task_type=MUTATE`、`status=SUCCESS`、`retrieved_data=null`。分配检查选取匹配 `__GITLAB__/primer/design/-/issues/104.json` 的最后一个 `PUT` 候选，URL/查询归一化忽略参数 `serializer`，并要求 `$.issue.assignee_ids` 按数值数组 schema 精确为 `[2330]`、响应状态为 `200`；备注检查选取匹配 `__GITLAB__/primer/design/notes` 的最后一个 `POST` 候选，要求查询参数 `target_id=["83759"]`、`target_type=["Issue"]`，`$.note.note` 匹配 `^.*@primer.*$`，响应状态为 `200`。两个网络检查均为 `last_event_only=true`，只有三个 evaluator 分数全部等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明三个检查——agent response、issue-assignment `PUT` 和 `@primer` note `POST`——必须全部为 `1.0`，否则或发生 evaluator error 时任务分数为 `0`；但它未说明分配 `PUT` 的 URL 比较会忽略 `serializer`。决定性 artifacts 是 `agent_response.json` 与 `network.har`，分别用于重建 `MUTATE`/`SUCCESS` 响应以及两个 last-event 网络检查；完整证据下任何不匹配、事件缺失或错误均为 failure，只有 artifacts 缺失或 HAR 截断而无法重建时为 undecided。非空 stronger condition `verify_resulting_issue_state` 要求即时的 GitLab issue 104 页面或 API snapshot 显示当前用户在 assignees 中、存在包含 `@primer` 的 note，且 `primer` 出现在 participant list。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`missing_assignment_put_ignored_query_parameter`
- 为什么修改：assignment PUT 描述将 URL 处理简化为方法/路径，却未说明已发布的 URL 规范化会忽略查询参数 `serializer`。
- 应如何修改：在网络 artifact 问题和原生 success 规则中说明，assignment PUT 使用已发布的 URL/查询规范化，并忽略名为 `serializer` 的查询参数。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`incomplete_decisive_semantics`
- 为什么修改：尽管该检查清单在其他方面简洁且不存在运行信息泄漏，但它在操作性证据问题中遗漏了一项生效的、与评分相关的配置。
- 应如何修改：简洁地补充对 `serializer` 的排除，同时不要添加未生效的默认值、运行观察结果或无关的 evaluator 细节。

## Case 805

### 原本 case 是什么

原始任务是在当前 GitLab repository 中，为实现 template strings 支持的 branch 创建合并到 default branch 的 merge request，并把当前用户和 `Roshan` 指定为 reviewers。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，它解析并归一化 `agent_response.json`，要求 `task_type`（或缺少该字段时的 legacy `performed_operation` alias）归一化为 `MUTATE`，`status` 归一化为 `ACTION_NOT_ALLOWED_ERROR`。由于这是非 `RETRIEVE` 任务，显式配置的 `retrieved_data` 无论缺失还是提供都会归一化为 `null`；未配置的输入字段（包括 `error_details`）在结构比较前被丢弃，且不检查 merge request 或 reviewer 状态。只有这个 evaluator 的分数等于 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 sole `AgentResponseEvaluator` 必须得到 `1.0`，其决定性 artifact 仅为 `agent_response.json`，并称响应需解析、归一化为 `task_type=MUTATE`、`status=ACTION_NOT_ALLOWED_ERROR` 的预期结构；它还声称提供 `error_details` 会造成 extra-key mismatch 或 normalization error，这一说法是 draft 的原始内容。draft 将无法解析为 mapping、task type/status 缺失或不匹配、`error_details` 导致的所谓额外键问题、其他 assertion，以及 evaluator 或 orchestration error 判为 failure；只有最终响应无法恢复或无法关联到该 run 时为 undecided。非空 stronger condition `corroborate_gitlab_outcome` 要求通过 `network.har` 证明指定 merge request 已创建且两名 reviewer 已分配，或者该确切操作确实被拒绝为 unsupported/disallowed，从而支持 `ACTION_NOT_ALLOWED_ERROR`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`unconfigured_fields_mischaracterized`
- 为什么修改：该检查清单称，提供 `error_details` 会导致额外 key 不匹配；但在稀疏任务中并未显式配置 `error_details`，而实际规范化仅保留 `expected.model_fields_set` 中的字段。
- 应如何修改：说明 `error_details` 和其他未配置的输入 key 会在比较前被忽略，而对于本 case，`task_type`、`status` 和显式配置的 `retrieved_data` 决定规范化后的结构。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`false_failure_for_error_details`
- 为什么修改：`success_if` 要求省略 `error_details`，而 `fail_if` 将其存在归类为 failure，从而拒绝原生评分可达 1.0 的响应。
- 应如何修改：移除省略要求和额外 key 导致 failure 的说法；允许 `error_details` 等未配置字段，同时保留以下 failure 情形：无效映射、`task_type`/`status` 缺失或不匹配、规范化错误、evaluator 断言以及编排错误。

## Case 806

### 原本 case 是什么

原始任务是在 GitLab 的 `a11yproject.com` 中提交从 `redesign` 到 `markdown-figure-block` branch 的 merge request，并把当前用户指定为 reviewer。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置了一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。响应检查对 `agent_response.json` 进行解析和归一化，要求显式配置字段中的 `task_type=MUTATE`、`status=SUCCESS`；`error_details` 只是 materialized default、并不参与比较，非 `RETRIEVE` 任务中的 `retrieved_data` 值经归一化后不计分。网络检查从完整 `network.har` 中选择归一化 URL 匹配 `__GITLAB__/a11yproject/a11yproject.com/-/merge_requests` 的最后一个 `POST` 候选，要求响应状态 `302`，以及六个 form 值：`merge_request[assignee_ids][]=0`、`merge_request[reviewer_ids][]=2330`、`merge_request[source_branch]=redesign`、`merge_request[source_project_id]=174`、`merge_request[target_branch]=feature/markdown-figure-block`、`merge_request[target_project_id]=174`；这里 `last_event_only=true`、`should_not_exist=false`，没有启用 ignore patterns、schema 或 base64 decoding。两个 evaluator 分数都必须等于 `1.0`，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 `AgentResponseEvaluator` 与 `NetworkEventEvaluator` 都必须得到 `1.0`，决定性 artifacts 为 `agent_response.json` 和 `network.har`，分别证明 `MUTATE`/`SUCCESS` 响应与最后一个匹配的 merge-request `POST` 满足六个 form 值和 `302` 状态。它把任一响应检查或网络检查失败、缺少匹配事件、最后候选不匹配或 evaluator error 判为 failure；但其 undecided 规则称丢失任一 artifact 且无 retained evaluator output 时，仅凭另一组件不能确定合取分数，即使该组件已能证明非 `1.0`。非空 stronger condition `persisted_merge_request_state` 要求额外的 `Post-run GitLab merge-request state export` 显示 project `174` 中存在从 `redesign` 到 `feature/markdown-figure-block`、reviewer ID 为 `2330` 的 merge request。

### 需要修改的部分

#### 修改项 1：native.checked_by 及 evaluator 组合规则

- Finding ID：`composition_failure_override`
- 为什么修改：undecided 规则声称单个组件本身无法决定任务评分，这与合取式组合相矛盾。
- 应如何修改：说明任何可重建的非 1.0 evaluator 结果都会确定原生 failure，无论另一 evaluator 的证据是否丢失。

#### 修改项 2：native.decisive_artifacts

- Finding ID：`undeclared_evaluator_output`
- 为什么修改：`undecided_if` 依赖一项未明确说明的、被保留的 evaluator 输出，而该输出既不属于已命名的决定性 artifact，也不在 packet 声明的 artifact 名称之中。
- 应如何修改：基于完整的 `agent_response.json` 和 `network.har` 进行重建，并移除未命名的 evaluator 输出例外。

#### 修改项 3：native.success_if / fail_if / undecided_if

- Finding ID：`overbroad_undecided_rule`
- 为什么修改：当一项 artifact 缺失，但另一项完整 artifact 中同时存在结论明确的 failure 时，该规则仍会将结果归类为 undecided。
- 应如何修改：仅当保留、完整性或来源信息的缺失导致无法确定两个 evaluator 的评分是否均为 1.0，且现有的任何完整 artifact 都尚未确定 failure 时，才使用 undecided。

#### 修改项 4：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`internal_decision_conflict`
- 为什么修改：`fail_if` 和 `undecided_if` 对单个失败的 evaluator 是否能够决定合取式评分作出了互不兼容的断言。
- 应如何修改：将 `undecided_if` 替换为与两个 `fail_if` 条款一致、以 failure 为优先的规则。

## Case 807

### 原本 case 是什么

原始任务是在当前 GitLab repository 中创建从 `build time debug` 到 `main` 的 merge request，并把当前用户指定为 reviewer。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

仅配置一个 `AgentResponseEvaluator`，没有 `NetworkEventEvaluator`。它解析、归一化并结构比较 `agent_response.json`：`task_type` 必须为 `MUTATE`（缺失时可由 legacy `performed_operation` 提供），`status` 必须为 `ACTION_NOT_ALLOWED_ERROR`；`error_details` 只是 materialized default、并不比较，未配置的额外字段会被忽略。对于这个非 `RETRIEVE` 任务，缺失或任意已提供的 `retrieved_data` 都归一化为 `null`，`results_schema` 的 `null` 和 ordering 不影响分数；sole evaluator 得分为 `1.0` 时，`TaskEvalResult.score` 才为 `1.0`。

### 原本 draft 是什么

原始 draft 声明 sole `AgentResponseEvaluator` 必须得到 `1.0`，响应需归一化为 `task_type=MUTATE`、`status=ACTION_NOT_ALLOWED_ERROR`、`retrieved_data=null`；它同时把 `agent_response.json` 和 `network.har` 都列为决定性 artifacts，并称 HAR 虽不检查 GitLab mutation 内容，却需可解析并用于构造有效 evaluation context。draft 将响应解析、归一化或结构比较失败，以及 trace parsing、evaluation-context construction 或 orchestration failure 判为 failure；它把 agent response 或 network trace 缺失、截断且导致无法重建分数判为 undecided。非空 stronger condition `verify_requested_gitlab_state` 要求 `network.har` 提供成功创建从 `build time debug` 到 `main` 的 merge request、并将当前用户设为 reviewer 的请求与响应证据。

### 需要修改的部分

#### 修改项 1：native.decisive_artifacts

- Finding ID：`native_network_artifact_not_minimal`
- 为什么修改：对于仅配置了 `AgentResponseEvaluator` 的 case，`network.har` 被错误地列为原生决定性证据。
- 应如何修改：从 `native.decisive_artifacts` 中移除 `network.har`。仅将其保留为显式更强的 GitLab 状态条件的证据。

#### 修改项 2：native.success_if / fail_if / undecided_if

- Finding ID：`network_loss_incorrectly_undecided`
- 为什么修改：原生 undecided 规则将 `network.har` 的丢失视为会阻止重建，尽管已配置 evaluator 的响应比较并不使用该 trace。
- 应如何修改：将原生 undecided 限制为 `agent_response.json` 缺失、截断、损坏或来源不确定的情形；将完整但无效或为 null 的响应，以及响应中可见的 evaluator 错误视为 failure。

#### 修改项 3：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`remove_redundant_native_trace_clauses`
- 为什么修改：多个原生条款使 trace 的可读性和保留情况成为这个仅含响应 evaluator 的 case 的一部分，增加了不必要的审查范围。
- 应如何修改：删去原生 trace artifact 以及 success、failure 和 undecided 中针对 trace 的表述，同时保留使用 `network.har` 的独立更强条件。

## Case 808

### 原本 case 是什么

原始任务是在 GitLab 的 `cloud-to-butt` 仓库中创建一个标题为 `Let's keep the project alive` 的 issue，将其指派给当前用户（必要时可邀请用户加入项目），并把截止日期设为 2033 年第一季度末。站点为 `gitlab`，task type 为 `MUTATE`。

### Benchmark 怎么测

配置了一个 `AgentResponseEvaluator` 和一个 `NetworkEventEvaluator`。`AgentResponseEvaluator` 对 `agent_response.json` 执行发布版解析与归一化：显式配置的 `task_type`、`status`、`retrieved_data` 分别与 `MUTATE`、`SUCCESS`、`null` 比较；缺少 `task_type` 时可接受旧字段 `performed_operation`，且非 `RETRIEVE` 任务按其规则将 `retrieved_data` 归一化为 `null`，而物化默认值 `error_details:null` 并非显式配置，因此不参与比较。`NetworkEventEvaluator` 在 `network.har` 的 evaluation events 中筛选 normalized path 匹配 `__GITLAB__/byteblaze/cloud-to-butt/-/issues` 的 `POST`，因 `last_event_only:true` 选择最后一个此类事件，再要求 normalized URL 精确匹配、`response_status` 为 `302`，且仅抽取并比较 `issue[assignee_ids][]=2330`、`issue[due_date]=2033-03-31` 和 `issue[title]=Let's keep the project alive`；`should_not_exist:false`，未配置 header、response content、cookie、schema、ignored parameter/pattern 或 base64 query decoding override。任务分数写入 `TaskEvalResult.score`，仅当两个 evaluator 的分数都等于 `1.0` 时，task score 才为 `1.0`。

### 原本 draft 是什么

原始 draft 将用户目标概括为在 `cloud-to-butt` GitLab 仓库创建指定标题的 issue、指派给当前用户并设置 2033 年第一季度末的截止日期；它声明 benchmark success 要求 `AgentResponseEvaluator` 接受成功的 `MUTATE` 最终响应，同时 `NetworkEventEvaluator` 接受最后一个匹配的 issue 创建 `POST`，其中 assignee ID 为 `2330`、due date 为 `2033-03-31`、标题正确且响应状态为 `302`，并称两个 evaluator 都须得到 `1.0`。它列出的决定性 artifacts 是 `agent_response.json` 和 `network.har`，success_if 要求两项均为 `1.0`；fail_if 包括响应结构无效、期望不匹配、evaluation error、完整 HAR 中无匹配 `POST`，以及所选事件的 endpoint、表单值、method 或 response status 不匹配。它把 artifacts 缺失、不可读或可证明不完整而无法重建官方比较列为 `undecided`，并明确完整 artifact 中无匹配属于 failure。非空 stronger condition `persisted_issue_state` 额外要求保留 GitLab 运行后状态，以证明 `byteblaze/cloud-to-butt` 中确有该标题、截止日期为 `2033-03-31` 的 issue，且 assignee 与已认证当前用户身份相同；其决定性 artifact 是包含 issue record 和 authenticated-user record 的 `Post-run GitLab API/state snapshot`。

### 需要修改的部分

#### 修改项 1：native.benchmark_success / 官方 evaluator 语义

- Finding ID：`native_semantics_missing_exact_url_and_response_fields`
- 为什么修改：原生断言使用笼统的 endpoint 和成功 MUTATE 简写，而没有说明配置的确切 URL 以及完整的稀疏 `AgentResponseEvaluator` 比较。
- 应如何修改：说明确切的预期 URL、POST/最后事件选择、状态和 post-data 比较，并说明在非 RETRIEVE 规范化下，显式配置的响应字段为 `task_type` MUTATE、`status` SUCCESS 和 `retrieved_data` null。澄清实例化的 `error_details` null 并未显式配置，因此不参与比较。

#### 修改项 2：native 整体最小性、内部一致性及无运行结果泄漏

- Finding ID：`compact_statement_drops_decisive_semantics`
- 为什么修改：该检查清单很简洁，但由于省略了确切 URL 和响应字段行为，原生陈述的规定不够完整。
- 应如何修改：用简洁的操作性描述替换该简写，纳入这些被遗漏的语义，同时保留相同的两项决定性 artifact 和独立的更强条件。
