# AgentDojo 新增 849 个 draft 定义符合性审核报告

生成时间（UTC）：`2026-07-18T21:02:18.784734+00:00`

## 结论

共审核 **849** 个 draft：**389 个符合**系统对 draft 的定义，**460 个不符合**，未留下 unresolved 项。

本结论只审核预运行、结果盲的 checklist/draft 定义，不读取任何 agent outcome、benchmark label、score 或运行产物，不推断实际 S/F/U，也不判定 benchmark conflict。审核过程没有修改任何 draft。

逐 case 结论见 `FINAL_AUDIT_849.csv`；包含两轮理由、来源指针和 hash 的机器可读记录见 `FINAL_AUDIT_849.jsonl`；所有不符合项的中文索引见 `NONCOMPLIANT_CASES_ZH.md`。

## 审核方法

1. 对 849 个 packet/checklist 做确定性结构与来源约束检查，包括 case 身份、结果盲、artifact inventory 精确值、来源文件和 SHA256 一致性。
2. 对每个 case 独立检查八项设计要求：锁定与结果盲、native user goal、released evaluator 权威性、S/F/U 优先级、证据与 inventory、stronger 条件、来源最小性、conflict/reporting 分离。
3. 第一轮指出的问题不直接定案；每个 allegation 再以同一 packet 的官方 goal/task/policy、released evaluator/oracle、schema 和 inventory 逐条裁决。只有能被精确来源证明的 substantive finding 才保留。
4. 最终不符合 = 存在确定性 blocking finding，或第二轮维持至少一个语义 finding。仅有措辞差异、主观偏好、重复要求或无官方依据的更强要求均不构成失败。

## 审核完整性

- packet 数：849；packet hash 全部与确定性审核输入一致。
- 第一轮逐 case 审核：378 pass，471 个进入第二轮。
- 第二轮：11 个 allegation set 全部驳回，460 个至少保留一项。
- 第一轮 finding：共 716 项；第二轮维持 693 项，驳回 23 项。
- 被维持 finding 的来源指针文件检查：3573 个存在，0 个缺失。
- 实际 agent outcomes 读取：否；draft 修改：否；未决项：0。

## 按 suite 的最终结果

| Suite | 符合 | 不符合 | 合计 |
|---|---:|---:|---:|
| banking | 74 | 52 | 126 |
| slack | 48 | 42 | 90 |
| travel | 53 | 74 | 127 |
| workspace | 214 | 292 | 506 |

## 按系统设计维度统计被维持问题

以下是 finding 数量，不是 case 数量；同一 case 可以有多项问题。

| 设计维度 | Finding 数量 |
|---|---:|
| stronger 条件的官方依据、语义 gap、完整性或独立性 | 441 |
| released evaluator/oracle 语义及 native S/F/U 规则 | 152 |
| decisive evidence、artifact inventory 与可判定性 | 53 |
| native user goal 的官方任务忠实度与角色分离 | 47 |

## 被维持问题的主要类型

下表按精确 finding code 聚合。code 是逐 case 审核记录的稳定索引；具体语义、官方来源与裁决理由必须以 JSONL 和不符合项明细为准。

| Finding code | 数量 |
|---|---:|
| `native_security_predicate_misstated` | 19 |
| `incomplete_native_user_goal` | 10 |
| `incorrect_evaluator_source_pointer` | 8 |
| `reversed_stronger_security_polarity` | 5 |
| `invented_email_body_requirement` | 5 |
| `missing_self_email_recipient_condition` | 5 |
| `omitted_concrete_attack_goal_gap` | 4 |
| `omitted_reviewable_attack_goal_gap` | 4 |
| `unsupported_stronger_semantic_gap` | 4 |
| `misstated_released_security_predicate` | 3 |
| `omitted_reviewable_user_goal_gap` | 3 |
| `unsupported_post_state_artifact` | 3 |
| `native_security_predicate_narrowed` | 3 |
| `missing_reviewable_official_recipient_condition` | 3 |
| `incorrect_trace_inventory_index` | 3 |
| `official_user_goal_requirement_omitted` | 3 |
| `omitted_concrete_user_task_gap` | 3 |
| `unsupported_no_extra_text_requirement` | 3 |
| `inexact_injection_security_fallback` | 3 |
| `incorrect_evaluator_source_pointers` | 3 |

这里只展示数量最高的 20 个 code；其余 561 个低频 code 的完整计数保存在 `AUDIT_SUMMARY.json`。

## 重要解释

- 不符合表示 checklist/draft 本身没有忠实、完整地锁定该 case 的证据规则；不表示对应 benchmark run 一定失败。
- stronger 条件的不符合独立于 native label，不自动构成 benchmark conflict。
- 本审核不会用运行结果反向修订 checklist，因此满足 outcome-blind 锁定要求。
- 确定性审核中的非 blocking 语义正则 flag 仅用于把内容送入逐项语义审核，不单独计为失败。

## 产物

- `FINAL_AUDIT_849.csv`：每个 case 一行的最终结论。
- `FINAL_AUDIT_849.jsonl`：每个 case 的完整审核收据。
- `NONCOMPLIANT_CASES_ZH.md`：所有不符合 case 及其被维持 finding。
- `AUDIT_SUMMARY.json`：聚合统计、模型配置和不可变性声明。
