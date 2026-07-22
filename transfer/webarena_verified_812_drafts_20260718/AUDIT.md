# WebArena-Verified 全量 812 个 draft 审计报告

总体内容结论：**需要修改**。case packet、draft 生成运行时、传输、Schema 和来源证明均有效，但逐 case 语义审核最终判定 486 份 draft 可接受、326 份需要修改。尚未调用 `neurips_ed_track_minimal` checklist score。

## 运行时和输入边界

- VPS 上的 draft 执行路径与本地 `neurips_ed_track_minimal` 实现逐字节一致，覆盖 guardrail、validator、drafter、批处理 runner、prompt、template、Schema 和三个部署 wrapper。
- 812 个 case packet 共包含 13,648 个文件。所有 packet、index、manifest 和原始来源哈希均通过校验；本地到 VPS 的 checksum dry-run 差异为 0。
- 每次 draft 调用均使用 `codex_cli`、`gpt-5.6-sol`、max reasoning、medium verbosity、只读 sandbox、临时且忽略用户配置，并禁用了 shell/unified-exec 工具。
- 每个密封 draft 输入只包含 draft 指令、template、该 case 的 `case_packet.md` 和输出 Schema；不包含 benchmark 运行输出、agent arm 结果、evidence 目录或 score 输入。

## Draft 批处理结果

- Job：`webarena_v123_812_claimonly_20260718`
- 并发调整历史：12 → 36 → 60 → 72，均通过同一 job 的安全停止和恢复完成。
- 最终状态：812/812 份 checklist 完成，0 失败，0 warning。
- 最后一次恢复新增完成 348 个 case，并跳过 464 个已经存在且有效的 case。被跳过的文件均由 runner 重新验证，并非遗漏任务。
- 从 VPS 拉回本地的 draft 生成文件：11,459 个，共 58,622,499 字节。

## 确定性和来源证明审核

- 812/812 通过 JSON Schema、确定性 guardrail，以及相对于对应 packet 源文件的 support pointer 解析。
- YAML/JSON 不一致、身份或 domain 错误、最终 sidecar 缺失、promotion/provenance 错误、密封输入错误和 packet 哈希不一致均为 0。
- 812/812 均为 `phase=draft`，且 Codex 调用使用预期模型和设置并正常完成。
- Draft 尝试次数分布：799 个一次成功、11 个两次成功、2 个三次成功。只有验证通过的 attempt 才会提升为最终文件。
- 冻结数据划分一致：325 个 RETRIEVE、113 个 NAVIGATE、374 个 MUTATE；每个 case 的评估器数量覆盖 1 至 11 个。
- 全文泄漏扫描未发现任何真实 Agent A/B/C 结果、已观察 benchmark 结果、score、运行输出、result namespace 或执行模型结果进入 draft。

## 逐 case 语义内容审核

812 份 draft 均已分别对照各自的 `case_packet.md` 审核。每次 reviewer 的密封输入只包含审核 prompt、该 case packet 和 draft，不包含 benchmark 实际运行产物。Reviewer 使用 `gpt-5.6-sol`、`xhigh` reasoning，最高 72 并发，最终 812/812 完成，0 失败。

- 独立模型初判：467 份可接受，345 份需修改。
- 按官方 evaluator 源码复核后的最终结果：486 份可接受，326 份需修改。
- 处理分布：467 个模型通过项经复核确认；326 个模型修改项经复核确认；19 个模型修改项经复核推翻。
- 19 个推翻项都只涉及非 RETRIEVE 任务省略无影响的 `retrieved_data: null`。发布版本 parser 会把字段缺失和显式 null 都归一化为相同值，因此该省略不可能改变 native result。
- 326 个修改结论属于 draft 内容缺陷，而不是文件完整性或生成失败。问题类别允许重叠，同一个 case 可能同时包含多类问题。

主要已确认问题如下：

- 287 个 case 的成功、失败、无法判定规则不完整或不正确。
- 250 个 case 存在最小性或内部一致性问题。
- 199 个 case 错误地把非决定性产物设为必要条件，或允许其替代官方决定性产物。
- 128 个 case 存在 response 归一化或期望值错误。
- 106 个 case 对 network evaluator 语义描述不完整。
- 76 个 case 存在 response parser 或稀疏字段语义错误。
- 另有 17 个 stronger condition 问题、10 个 evaluator 组合错误、7 个 user goal 范围或格式错误，以及 1 个无来源支持的 claim。

代表性缺陷包括：仅依赖 response 的 case 却错误要求 `network.har`；遗漏旧版 `performed_operation` alias；遗漏或改写用户明确要求的 key、单位、所有权或格式；缺少 URL normalization、base64 query、忽略参数等语义；错误理解 last-event 组合；以及在 stronger condition 中加入没有 packet 来源支持的外部事实。Case 319 还暴露了官方 sparse-field evaluator 路径，而对应 draft 错误声称该路径存在可达到的成功结果。

逐 case 最终裁决见 `semantic_reviews_gpt56_xhigh_v1/SEMANTIC_ADJUDICATION.md`、`semantic_review_adjudication.csv` 和 `.json`。326 个需修改 case 的完整中文说明见 `semantic_reviews_gpt56_xhigh_v1/zh_revision_report_v1/DRAFT_REVISION_DETAILS_ZH.md`；每个 case 均包含原始任务、benchmark 的 evaluator/判分方式、原始 draft 声明，以及逐 finding 修改位置、原因和改法。每个 case 目录还保留完整的 `review.json`、API response、调用元数据、reasoning-summary sidecar、attempt 记录、状态和日志。Markdown 报告使用中文；原始 reviewer 输出和机器可读技术字段保留英文，以维持原始证据不变。

## 独立 benchmark 运行产物

Benchmark 执行是独立流程，不是此次 draft 语义审核的输入。在之前的运行产物审计快照中，预期 2,436 个 canonical slot 里已有 232 个完成密封。全部 232 个均通过 receipt/manifest 哈希绑定、task/agent 身份、官方 evaluator 完成状态、必要产物清单、安全 gate 和 score/status 一致性检查。ledger 当时有 17 个基础设施问题，但 settled-invalid slot 为 0。该快照不能说明全量 benchmark 已经完成。

## Score 边界

本批 draft **尚未调用** `neurips_ed_track_minimal` checklist score。按照系统设计，应先修正并冻结这 326 份标记为“需修改”的 draft；benchmark 执行完成后，再把每份冻结 checklist 与对应的保留运行产物关联，并运行 score 判断产物能否支持其 claim。

机器可读总表位于 `_audit_report.json`；draft 生成摘要位于 `_batch_summary.json`；语义审核结果位于 `semantic_reviews_gpt56_xhigh_v1/`；本轮实际修改内容及修改原因见 `CHANGES_AND_RATIONALE_ZH.md`。
