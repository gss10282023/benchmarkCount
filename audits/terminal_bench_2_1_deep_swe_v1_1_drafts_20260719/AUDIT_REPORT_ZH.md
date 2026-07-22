# Terminal-Bench 2.1 / DeepSWE v1.1 draft 语义审核

## 审核边界

- 每个 case 只读取匹配的 `case_packet.md`、`checklist.yaml` 和冻结审核 prompt。
- 未读取 agent outcome、per-record reward/released label 或 evidence score。
- `accept` 表示九项系统设计检查全部通过；`revise` 表示至少一项阻断问题。
- `revise` 的 proposed revision 只作审计建议；本次未覆盖或修改原始 draft。

## 汇总

- 总 case：202
- accept：70
- revise：132
- 审核运行失败：0
- 无效修订建议：80
- 使用 schema 加固 retry prompt 的 case：10

## 分 benchmark

- `terminal_bench_2_1`：89 cases，accept 23，revise 66，审核失败 0。
- `deep_swe_v1_1`：113 cases，accept 47，revise 66，审核失败 0。

## 阻断项计数

- `decision_rules_sfu`：77
- `decisive_post_run_evidence`：69
- `minimality_and_no_run_leakage`：1
- `native_evaluator_semantics`：69
- `native_user_goal`：34
- `source_support_pointers`：49
- `stronger_conditions`：57

逐 case 结论和 finding 见 `semantic_review_records.jsonl` 与 `semantic_review_report.csv`。
