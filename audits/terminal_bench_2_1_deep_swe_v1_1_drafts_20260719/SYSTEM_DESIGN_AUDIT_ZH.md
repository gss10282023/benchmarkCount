# Terminal-Bench 2.1 / DeepSWE v1.1 draft 系统设计逐案审查

## 结论

- 已逐案审查 **202** 份冻结 draft：Terminal-Bench 2.1 为 89，DeepSWE v1.1 为 113。
- **70 / 202** 份 draft 当前符合这版系统设计；**132 / 202** 份需要在进入 evidence scoring 前修订并重新锁定。
- 这不是对 benchmark record 的 S/F/U 判断，也不是 benchmark conflict 判断。它只判断 pre-run evidence checklist 是否符合设计。
- 全部 202 份当前 draft 的哈希均与 draft lock manifest 一致，draft prompt/schema/supplement 与冻结哈希一致；本次审查没有改写任何原始 draft。

## 审查边界

本次审查只读取每个 case 的 packet、冻结 `checklist.yaml`、draft provenance/lock、确定性审核记录，以及只读、outcome-blind 的逐案语义审核 receipt。每个 packet 都声明排除 prior-run records、released evaluator results、oracle bytes 和 per-record artifact values。没有读取 agent outcome、trajectory 内容、实际运行 artifact 内容、per-record reward/result/released label、evidence-scoring S/F/U 或 benchmark-conflict 记录。

因此，结果直接回答“draft 是否可作为进入运行前锁定的 checklist”，而不依赖 benchmark 原始 label。

## 系统设计条款到逐案检查的映射

| 你的设计要求 | 对应逐案检查 |
| --- | --- |
| 在接触 outcome/label 前锁定、不得随 outcome 修改 | lock-manifest 哈希、draft/review provenance、`identity_and_scope`、标签/运行特定语言扫描 |
| 官方 user goal/task | `native_user_goal` |
| released evaluator/oracle 的正式 native 语义 | `native_evaluator_semantics` |
| 必要的 state schema 与 artifact inventory | case packet 中的 evaluator/report-state 语义与 `artifact_inventory`，并以 `decisive_post_run_evidence` 检查 artifact 是否真的能证明对应事实 |
| 独立的非标签 S/F/U | `decisive_post_run_evidence` + `decision_rules_sfu`；静态检查禁止把 reward/result/label 当 decisive evidence |
| source support、禁止主观加码 | `source_support_pointers` |
| stronger 独立、须有 case-specific 官方支持和明确 gap | `stronger_conditions` |
| 不从 stronger F 或 native S + stronger F 推出 conflict | `stronger_conflict_separation`，并静态禁止 draft 声称 benchmark conflict |

这里的“state schema”是功能性含义：packet 没有字面字段 `state_schema`，故以每案 evaluator 的报告状态/聚合语义和 retained artifact inventory 为准。DeepSWE 是 CTRF `suite.name` 节点、状态和聚合投影；Terminal-Bench 是任务特定 verifier/test 语义与 report artifact。

## 汇总

| Benchmark | cases | 符合 | 需修订 | 预运行/标签边界通过 |
| --- | ---: | ---: | ---: | ---: |
| Terminal-Bench 2.1 | 89 | 23 | 66 | 89 |
| DeepSWE v1.1 | 113 | 47 | 66 | 113 |
| **总计** | **202** | **70** | **132** | **202** |

所有 202 个 case packet 均在 lock 前声明 artifact inventory 和 case-specific evaluator/report-state source；所有 202 个 draft 的 named artifact 都与该 inventory 机械匹配。该结构事实不取代语义审核：某 artifact 即使在 inventory 中，仍可能不足以独立证明 checklist 声称的事实，因而会在 `decisive_post_run_evidence` 下要求修订。

## 需修订的设计条款计数

- `identity_and_scope`（身份与预运行 scope）：0
- `native_user_goal`（官方 user goal/task）：34
- `native_evaluator_semantics`（native evaluator/oracle 语义）：69
- `decisive_post_run_evidence`（决定性非标签运行证据）：69
- `decision_rules_sfu`（native S/F/U 规则）：77
- `source_support_pointers`（source support pointers）：49
- `stronger_conditions`（stronger 条件的官方支持与 gap）：57
- `minimality_and_no_run_leakage`（最小性/无运行泄漏）：1
- `stronger_conflict_separation`（stronger/conflict 分离）：0


`stronger_conflict_separation` 没有逐案失败；这意味着现有 drafts 没有把 stronger 结果写成 benchmark conflict 结论。它不构成任何 record-level conflict 判定。

## 逐案台账

- 适合筛选和复核的表格：`system_design_case_ledger.csv`
- 包含每个 review item 证据和所有 finding 的可机读台账：`system_design_case_ledger.jsonl`
- 汇总：`system_design_audit_summary.json`

台账中 `符合` 仅表示 draft 已通过本次严格的 pre-run 设计审查；`需修订` 的 finding 是针对 draft 本身的修改要求。审查建议未自动写回，因此不会违反“锁定后不得根据 outcome 修改”的约束；如后续采纳，必须将修订版本当作新的、在任何具体 outcome/label 可见之前重新冻结的 checklist。
