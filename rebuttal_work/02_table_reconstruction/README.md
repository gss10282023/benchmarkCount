# 步骤2：五张投稿表的确定性重建

本目录按“先重建投稿打印值、暂不裁决候选修改后来是否应用”的范围，重建论文表2、表3、表6、表9和表13。

计算使用两份已经在步骤1锁定的来源：

- 匿名制品提交 `ffd9ff4e...` 对应的1,282条步骤1记录，负责原始运行、原生标签和证据标签；
- 论文源提交 `35b962c8...` 中的审核台账，负责论文打印口径的非空最终标签、审核条目和表格文字。

这两个提交来自同一历史基点后分叉。匿名制品分支本身没有审核台账，因此这里准确称为“投稿打印口径的双提交冻结重建”，不声称五张表仅靠匿名制品分支就能恢复。

## 一条命令验收

```bash
cd /Users/gss/Downloads/revised_agent_benchmark_paper_package/rebuttal_work/02_table_reconstruction
make verify
```

该命令会重新生成全部产物、运行单元测试、在临时空目录独立重跑一次、逐文件比较字节摘要，最后核验 `SHA256SUMS`。

## 核心产物

- `table_reconstruction_manifest.csv`：1,282条表格重建记录；保留原标签、投稿打印标签、冲突标志、审核条目和原始文件摘要。
- `table2_rebuilt.*`、`table3_rebuilt.*`、`table6_rebuilt.*`、`table9_rebuilt.*`、`table13_rebuilt.*`：五张表的CSV、JSON和可排版的TeX表体。
- `table3_pairwise_details.csv`：表3的12个逐模型对区间判断。
- `audit_review_items.csv`：126个物理审核条目及其133个展开记录关联；表9按物理条目计数。
- `cell_lineage.jsonl`：每个表头和正文单元格的记录键集合、审核条目、筛选条件、公式、来源和输入摘要。
- `printed_vs_rebuilt.csv`：论文打印值与脚本重建值的逐格对照。
- `discrepancies.csv`：未复现单元格；验收通过时只有表头，没有数据行。
- `frozen_input_manifest.json`：全部冻结输入的提交、对象和内容摘要。
- `paper_source_contract_validation.json`：非数值文字与论文源逐格或逐句核验结果。
- `tau3_scope_note.md`：解释 τ³ 的 `212/87/1`、`24` 和 `10` 为什么能同时出现。
- `verification_report.json`：最终自动验收报告。

## 当前范围的含义

五张表的打印值由脚本精确恢复，不把后续复审数字覆盖到投稿表。尤其是 τ³：表2保留 `212/87/1`，表6按硬标签分歧得到 `24`，表9按投稿时的候选计数规则得到 `10`。这一步只恢复历史表格，不在这里判断那10条候选后来是否应该写回表2。
