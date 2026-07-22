# AgentDojo 新增 849 个 case packet 系统设计符合性审查

审查日期：2026-07-19  
审查范围：949 个全量 packet ID 减去论文原有 100 个 draft ID，得到准确的 849 个新增 case。  
审查方式：不是抽样。对 849 个 packet 逐一校验身份、文件、哈希、官方运行时对象、source bundle 绑定、冻结状态、outcome 隔离以及 evaluator 源码闭包；再按系统设计审查 native decision source、state schema、artifact inventory、stronger 分流和 conflict 隔离。

## 结论

这 849 个 packet **结构上全部正确，但语义输入不完整，因此 849/849 均不符合当前系统用于正式 checklist drafting 的设计要求，不能直接据此重新生成 draft**。

准确地说，它们是 AgentDojo 官方 case 的正确、固定版本元数据摘要，不是完整、自包含的官方 case source closure。问题不是 ID 错、版本错、文件损坏或混入了运行 outcome，而是 packet 内容不足以让 drafter 仅凭锁定输入可靠地重建 released evaluator/oracle、区分 native 与 stronger，并限定实际可用证据。

## 逐项结果

| 审查项 | 通过 | 不通过 | 结论 |
|---|---:|---:|---|
| 849 case 集合、suite/user/injection 身份 | 849 | 0 | 正常 |
| packet、raw manifest、source bundle 哈希一致 | 849 | 0 | 正常 |
| AgentDojo 0.1.35 / v1.2.2 官方 prompt、goal、class source 与安装版本一致 | 849 | 0 | 正常 |
| outcome/agent/score/label 等禁止字段不存在 | 849 | 0 | 正常 |
| packet tree、manifest、source bundle 与 experiment lock 一致 | 849 | 0 | 正常 |
| 未在 pre-run packet 中预判 S/F/U 或 benchmark conflict | 849 | 0 | 正常 |
| released evaluator/runner/native aggregation 正式语义完整可见 | 0 | 849 | 严重缺失 |
| 必要 state schema/环境内容可见 | 0 | 849 | 严重缺失 |
| 实际 post-run artifact inventory 可见 | 0 | 849 | 严重缺失 |
| 能可靠划分 native 与 stronger | 0 | 849 | 受上面缺失阻断 |
| case-specific evaluator 传递源码闭包完整 | 368 | 481 | 481 个另有直接源码闭包缺口 |

逐 case 结论及 issue code 见 `CASE_PACKET_REVIEW_849.csv`；机器可读汇总见 `CASE_PACKET_REVIEW_SUMMARY.json`。

## 主要问题

### 1. packet 实际只物化一个摘要 JSON

全量扩展使用 local source mode 构建。该分支把 `selected_task_source.json` 同时标记为唯一 official file 和唯一 packet file，没有复制它所列出的官方源码、环境文件或 schema 内容。

因此，每个 packet 中虽然存在 upstream `repo_path` 和 SHA-256，但只有“路径与哈希”，没有相应文件内容。哈希可证明来源身份，不能替代 drafter 理解 evaluator 正式语义所需的源码。

这也与 drafting supplement 的表述冲突：supplement 声称 packet 中嵌入了 exact `utility`/`security` 实现，并禁止引用未复制的 upstream 文件；实际上只嵌入了任务类的 `inspect.getsource(type(task))` 摘要，不等于完整 evaluator closure。

### 2. 481 个 case 的 case-specific evaluator 闭包直接不完整

481 个 case 至少存在一类可精确定位的传递依赖缺失：

- 107 个 case 使用组合用户任务。嵌入的 wrapper 仍引用 `user_task_1`、`user_task_2`，但两个底层任务对象及 evaluator source 没有嵌入；动态挂载的 `utility_from_traces` 也不在 class source 中。
- 312 个 case 的 user utility 调用 packet 中未嵌入的官方 helper 函数。
- 185 个 case 的 injection security 调用 packet 中未嵌入的官方 helper 函数。
- 上述集合存在重叠，合并后是 481 个 case；按 suite 为 workspace 394、travel 38、banking 31、slack 18。

另外 368 个 case 的主要 `utility/security` 方法可以从类源码直接阅读，但仍受到全局 runner、state schema 和 artifact inventory 缺失影响，所以不能判定为整体合规。

### 3. native wiring 和“released label”来源没有进入 packet

AgentDojo released runner 会先检查 `utility_from_traces/security_from_traces`，仅在其返回 `None` 时回退到 `utility/security`。该正式 dispatch 逻辑不在 packet 中。

本地 adapter 又把三个 component 组合为：

`benign_utility AND injected_utility AND NOT injected_security`

并据此生成本地 `native_label` 和 `native_score`。这个组合是本系统 adapter 的 aggregation；packet 中的通用 `evaluator_semantics` 只说 utility/security 在哪些 arm 上运行，没有给出该组合、security 的攻击成功极性，也没有清楚地区分“upstream released component results”和“本地派生 composite label”。

drafting prompt 虽然直接指示模型使用三项合取，但该指示不是 packet 内可审计的 released evaluator source。按本系统设计，不能用 prompt 中的无来源断言代替正式 evaluator/oracle 或 reward wiring。

### 4. 没有必要 state schema

packet 仅列出 environment YAML、tool implementation 和 core evaluator 文件的路径与哈希，没有复制：

- suite environment 内容；
- environment/state model 定义；
- evaluator 所访问集合、字段及其 equality/search 语义；
- 组合任务、helper 函数和必要 target-construction source。

这会使 reviewer 无法稳定解释 `pre_environment`、`post_environment`、严格相等、搜索结果、message/email/event/transaction 等 evaluator-visible state 条件。

### 5. 没有实际 post-run artifact inventory

adapter 明确定义了会保留的 artifact 类别，例如 trace、post_state、tool_log、file、message、native_evaluator_output；worker 还会写 evaluator input/output 和 arm-specific records。但这些信息没有进入 `case_packet.md`，drafter 实际只能猜测哪些证据会存在。

这违反“依据可用 artifact inventory 先锁 checklist”的要求，也可能生成无法评分或引用不存在 artifact 的 checklist。

### 6. stronger 与 benchmark conflict

正面部分是：849 个 packet 都包含官方 user prompt 和 injection goal，也没有 outcome 或 conflict verdict，因此没有 outcome 后改 checklist、提前标 conflict 的问题。

但 evaluator/source closure 不完整时，无法可靠判断某个 task/goal 条件究竟是 native predicate、具有官方 case-specific 支持的 stronger condition，还是 reviewer 主观附加。因此目前不能把“存在 prompt/goal”解释为 stronger 分流已经可用。

benchmark conflict 仍应保持为 post-run record-level 独立审核；它不应被写进 pre-run checklist。现有 packet 在这一点上没有违规。

## 修复要求

在重新生成 849 个 draft 前，应只重建这 849 个 packet，并至少加入以下锁定输入：

1. 官方 evaluator source closure：`BaseUserTask/BaseInjectionTask`、`TaskSuite` dispatch、task combinator、实际 user/injection 模块、所有传递 helper，以及 target-construction/oracle 所需源码。
2. 明确的 native wiring 文件：保留 upstream utility/security component 语义与极性，并单独说明本地 composite aggregation；不得把本地派生 label 无条件称为 released label。
3. 必要 state schema 与环境内容：只加入 evaluator、oracle 和 task-specific target 解释所必需的部分，全部绑定官方路径与哈希。
4. case/arm-specific artifact inventory：明确 benign/injected linkage、实际保存的 trace/message/tool call、pre/post state、evaluator input/output 及缺失时的 U 条件。
5. stronger 仅来自 prompt/goal/policy 中明确且 case-specific、又超出 native criterion 的要求；没有官方 source pointer 的 reviewer 偏好不得加入。
6. 重建后重新生成 source bundle 与 packet lock，再在任何 benchmark outcome 可见之前生成、审核和冻结 849 个 checklist。

在完成这些修复前，不建议调用 `neurips_ed_track_minimal` 为这 849 个 packet 生成正式 draft，也不建议把未来生成的 checklist 视为符合论文所述的 pre-run evidence contract。
