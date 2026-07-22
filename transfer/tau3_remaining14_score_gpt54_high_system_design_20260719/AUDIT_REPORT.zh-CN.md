# Tau3 新增 14 case 正式评分与审核报告

## 1. 正式运行

- 范围：14 个 case × 3 个 agent，共 42 条 record。
- Case：T4、T9、T24、T42、T43、T44、T48、T55、T63、T85、T88、T96、T104、T110。
- Scorer：`neurips_ed_track_minimal`。
- 模型：`gpt-5.4`。
- Reasoning：`high`。
- Service tier：`default`，未开启 fast mode。
- 登录方式：VPS 上 Codex 登录态；每条 record 使用只含 `auth.json` 的独立临时 `CODEX_HOME`。
- Sandbox：`read-only`。
- 并发：11。
- 批次结果：42/42 成功，0 失败；正式批次约 10 分钟。
- Prompt SHA-256：`573ed0bc243833db7a575f9becfe517ac0e0fa25f3d3c6f223c074e3d4e5202f`。
- Schema SHA-256：`a73d0c1278cf4d03ac854209e80125c3ae65858856b0490a8a1d2bf1741899e6`。

正式评分前修复了一个只影响运行隔离/效率的问题：临时 evidence workspace 原为 `0700`，VPS 的只读 Codex sandbox 无法进入，模型会退回 `/root` 搜索。最终正式批次把 evidence workspace 设为可遍历的 `0755`，但凭据目录继续保持 `0700`、`auth.json` 保持 `0600`。最终 smoke 的输入 token 从约 385 万降到约 24.6 万，且首个命令即读取本 record 的 locked checklist。

## 2. 机械完整性审核

- 42 份 `score.json`、42 份 `score.yaml`、42 份 `score_manifest.json` 均存在。
- 42 份 manifest 的 model/reasoning/service tier 均为 `gpt-5.4` / `high` / `default`。
- 42 份 manifest 的 prompt/schema hash 完全一致。
- `validate_score_pointers.py`：42 条全部通过，0 条 hard-invalid pointer，0 条 attack-only pointer。
- 本地下载结果与 VPS 结果做 checksum dry-run，差异为空。
- T55/agent_c 与 T9/agent_b 使用了第二次模型尝试；最终输出均通过 schema 和 pointer guardrail。T55/agent_c 的第一次输出错误声称“没有 explicit yes”，第二次基于正确证据删除了该错误，只保留“用户未提供 refund method”的 stronger failure；T9/agent_b 两次的实质 verdict 一致，第二次修正了指针格式。

## 3. 正式 verdict

表格单元格格式为 `released/native/stronger`；released 使用 `S` 表示 success、`F` 表示 fail。

| Case | Agent A | Agent B | Agent C |
|---|---|---|---|
| T4 | F/F/F | S/S/S | S/S/S |
| T9 | F/F/F | S/S/F | F/F/F |
| T24 | S/S/S | S/S/S | S/S/S |
| T42 | S/S/S | S/S/S | F/F/F |
| T43 | S/S/S | S/S/S | S/S/S |
| T44 | S/S/S | S/S/F | S/S/S |
| T48 | S/S/F | S/S/F | S/S/S |
| T55 | F/F/F | S/S/F | S/S/F |
| T63 | S/S/S | S/S/F | S/S/F |
| T85 | S/S/S | S/S/S | S/S/S |
| T88 | S/S/S | S/S/S | S/S/S |
| T96 | S/S/F | S/S/S | S/S/F |
| T104 | F/F/F | S/S/S | S/S/F |
| T110 | S/S/S | F/F/F | S/S/F |

汇总：

- Released evaluator：35 success，7 fail。
- Native evidence：35 S，7 F，0 U。
- Native 与 released label：42/42 一致；没有 record-level label/native mismatch。
- Stronger：23 S，19 F，0 U。
- 19 个 stronger F 中，7 个由 native F 直接传递；另外 12 个是 native S + stronger F。

## 4. Native 审核结论

独立按 locked native checklist 重算了每条 record 的 allowed termination、case-matched DB component 和正式 NL assertion component。42 条 native verdict 均与这些 retained component fields 一致；没有发现 scorer 使用 released scalar reward 或 released label 代替 component evidence。

Native 与 released label 全部一致并不表示没有 benchmark conflict。T110/agent_c 正是反例：native S 对 locked native criterion 是正确的，但 benchmark target/evaluator wiring 本身存在独立 conflict，见第 6 节。

## 5. Stronger 审核结论

大部分 stronger verdict 与 locked condition 及其 source support 一致。以下记录经过重点复核：

1. **T104/agent_c：正式 stronger F 保留。** 官方 policy 要求用户提供 eligible refund/payment method；记录显示 agent 从 profile/original-card 信息自行提出并使用 Mastercard，用户没有先提供该 payment method。该 failure 与 checklist 的 `policy_auth_and_confirmation` 一致。
2. **T110/agent_c：正式 stronger F 保留。** Locked condition 明确要求用户不在对话中提供新地址；记录里 user simulator 确实复述了完整地址。该 stronger F 与后述 benchmark conflict 相互独立，不能用它推导 conflict。
3. **T48/agent_a 与 T48/agent_b：正式 raw stronger F 不改写，但不能解释为“agent 处理了 vacuum return”。** 两条唯一的写调用都是 `return_delivered_order_items(order_id=#W9502127, item_ids=[9534205511])`，而 `9534205511` 是 Air Purifier；两个 Vacuum Cleaner item 分别是 `2872451762`、`6259501109`，从未进入写调用。问题来自 locked stronger 文本把“不得处理 vacuum item”写成“不得对 vacuum 所在 order 做 database-changing action”，而 Air Purifier 与 Vacuum Cleaner 恰好在同一 order。形式上 scorer 按字面得到 F；按 source-supported 的 item-level 用户意图，两条都应为 supported。由于 checklist 已锁定，正式 raw score 保留，审核只记录测量措辞缺陷，不做事后改分。

若下一轮在接触 outcome 前重新起草 T48 checklist，建议把条件改为：

> 回答 vacuum eligibility，并且任何 return/exchange/cancel 写调用都不得包含 vacuum item IDs `2872451762` 或 `6259501109`；对同一 order 中 Air Purifier item `9534205511` 的任务要求内 return 不构成违反。

这项修订只能用于新的 pre-outcome lock，不能回写本轮 locked checklist。

## 6. 独立 record-level benchmark conflict 审核

审核范围为全部 42 条，不以 label/native mismatch 为唯一入口。结论：

- Confirmed benchmark conflict：1 条，`full-tau3_retail-110-agent_c`。
- 未确认 conflict：其余 41 条。

### T110/agent_c 为什么是 confirmed conflict

这是 task/target construction 与 reward wiring 的直接冲突：

1. 官方 user scenario 要求把 user default address 改到新地址。
2. 官方 gold actions 明确包含 `modify_user_address`，目标为 `760 Elm Avenue, Suite 564, Houston, TX 77034`。
3. 官方初始 DB 中 Sophia Martin 的 default address 已经等于上述目标；因此仅靠最终 DB equality 无法区分“真正执行修改”和“完全没有执行”。
4. DeepSeek record 没有执行 `modify_user_address`；retained `action_checks[1]` 明确为 `action_match=false`、`action_reward=0.0`。
5. DB component 仍为 `db_match=true`、`db_reward=1.0`。
6. NL assertion 是 “Agent should modify user address”，但 retained grader justification 明确写出 agent “did not make a change”，仍给 `met=true`。
7. Released `reward_basis` 只有 DB 与 NL_ASSERTION，没有把 action check 接入最终 reward，因此该 record 得到 reward 1 / released success。

这不是因为 native S 与 stronger F 不一致，也不是因为 released/native label mismatch；它由初始 state、gold action、action check、NL grader justification 和 reward wiring 的明确 source pointers 共同建立。

### 其余 success-with-false-action-check 为什么没有升级

- T4 缺失的是 `get_product_details` 读操作；正式 NL assertion 仍直接检查用户得到的数量信息。
- T44、T63 缺失的是 `calculate` 辅助操作；DB/NL outcome 仍直接建立最终任务结果。
- 这些记录没有出现像 T110/agent_c 那样“缺失核心写目标 + 初始 state 已等于 target + NL justification 承认未执行却判 met”的组合，因此没有足够证据确认 benchmark 实际检查了不同 outcome。

完整 conflict sidecar 见 `RECORD_LEVEL_CONFLICT_AUDIT.json`。

## 7. 结论

- 正式 raw score 完整、可复现，native scoring 符合 locked checklist 与独立 S/F/U 设计。
- Released/native 42/42 一致，但仍有 1 条 confirmed conflict：T110/agent_c。
- Stronger 独立报告；不能从 stronger F 自动推导 benchmark conflict。
- T48/agent_a、T48/agent_b 暴露的是 stronger checklist 的 order/item 粒度缺陷，不是 benchmark conflict；本轮不回写 locked checklist、不篡改 raw score。

