# GPT Pro Review: Step 1

## Blocking Issues

未发现需要阻断 Step 2 的 Step 1 spec gap。本审查只基于提供的 `step01_spec_freeze_review_packet.md`，不假设或审查项目其他文件。

## Non-Blocking Issues

1. **artifact path / artifact id 可能隐含 agent identity**
   spec 已要求 verdict_engine 不接收 agent_id、model/provider identity，并使用 sanitized artifact-manifest projection；但建议进一步明确：传给 verdict_engine 的 artifact path、artifact id、directory name、run_id projection 不得编码 agent/model/provider 信息，或必须被 canonicalized/opaque 化。否则理论上可以通过路径字符串间接泄漏 agent identity。

2. **`unresolve_level` 的取值未完全冻结**
   R1-R7 reason taxonomy 已冻结且语义充分，但 result schema 多处要求 `unresolve_level`。packet 没有定义该字段的 legal enum、层级含义或是否只是辅助字段。建议在 Step 2 schema 前明确：如果该字段保留，必须有固定枚举和值域；如果 R1-R7 已足够，应移除或设为派生字段。

3. **audit human time 是否进入 `tab:cost` 仍需一句话明确**
   packet 已正确禁止 LLM/VPS/benchmark compute 进入 `tab:cost`，并规定 `tab:cost` 来自 human-time logs。但 audit/review timing 是否计入 `tab:cost` 或仅进入 final report/supporting logs，最好显式冻结，避免后续表格口径漂移。

4. **paper_mapping coverage 是“声明式充分”，但不是逐行可核验**
   packet 列出了 required labels，并声明全部 covered；这足以作为 Step 1 packet 级别审查依据。但建议后续 review packet 附一个 compact mapping table：label → source artifact → formal gate → mock/dry-run exclusion rule，以便未来审查不依赖“covered”声明。

5. **native evaluator missing-provenance 的 R6 vs validation-failure 分界建议实现前再固化**
   当前规则允许“validation failure 或 UNRESOLVE R6，取决于 discovery point 和 locked contract rules”。这在规格层面可接受，但 Step 7 前应把 discovery-point 条件写成可测试规则，避免实现者自由选择更有利的分类。

6. **freeze 对 uncommitted code drift 的约束可再硬化**
   packet 已冻结 `code_git_commit`、`scorer_code_hash` 等。建议增加 `git_tree_clean=true` 或 `repo_tree_hash`，防止同一 commit 上有未提交改动影响 scorer、aggregation 或 paper-output code。

## Alignment Evidence

1. **adapter/scorer 边界正确**
   adapter 被限制为运行 official benchmark/diagnostic runner 并保存 raw evidence；它只能输出 `raw_run_record/v1`，必须声明 `contains_final_evidence_label=false`，不能产出 SUCCESS/FAIL/UNRESOLVE。scorer 是唯一能产出 final evidence label 的组件。该边界足以阻止 adapter、monitor、collector、runner 或 paper-output code 直接制造 evidence verdict。

2. **scorer forbidden-input 防护基本完整**
   packet 将 scorer 分为 `verdict_engine` 与 `provenance_binder`：前者只读 locked contract、raw artifacts、sanitized artifact manifest、schema/taxonomy/freeze metadata 和不含 agent identity 的 case metadata；后者才绑定 agent_id 与 aggregation metadata。Forbidden list 覆盖 native_label、native_score、native evaluator scalar、outcome_label、prior outcome、previous scored/evidence label、runner/adapter summary verdict、judge-only label、alternate view verdict、paper-output values、agent family/model/provider/version 等。
   结论：没有明显 native label、outcome 或 agent identity 偷看的正式路径；上面提到的 path/id 隐式泄漏属于 hardening，不是当前 packet 的 blocker。

3. **native evaluator decisive-evidence rule 对齐论文和工程要求**
   packet 要求 native evaluator artifact 必须同时满足 locked contract artifact mapping、path、sha256、official runner/evaluator provenance、direct artifact/verified object read。仅有 `raw_run.native_label` 或 summary scalar 时 scorer 必须拒绝 decisive use。sha mismatch 直接拒绝 scoring。该规则足够阻止 native scalar shortcut。

4. **UNRESOLVE R1-R7 已被冻结且语义足够具体**
   R1-R7 每个 reason 都有定义、适用边界、正反例和 overlap priority。packet 还规定每个 UNRESOLVE completed record 必须 exactly one category，多重适用时按 upstream-priority rule 选择。fail-closed validation 在 taxonomy assignment 前执行，避免把 unlocked contract、hash mismatch、artifact sha mismatch、INFRA_EXCLUDED 等错误塞进 UNRESOLVE。

5. **prediction freeze 足以阻止事后改规则**
   freeze 输入覆盖 manifest、paper mapping、official splits、eligible set、smoke exclusions、case selection order、hash function/salt、source bundle、agent/infra config、locked contracts、contract template/prompt、prediction registry、taxonomy/schema、scorer version/hash、code commit、bootstrap plan/seed/resample count、audit/rerun plans、P1-P4 predictions、pairwise tolerance、threshold boundary rule。
   Post-lock clarification 只能进入 superseded/clarification contract 和 sensitivity report，明确不得进入 native-aligned main result。

6. **LLM cost、人类时间、manifest hash、contract hash 覆盖充分**
   LLM call logging 包含 token categories、cost provenance、pricing source/hash、visible_input_hash、hidden_input_assertion_hash、prompt version/hash、config/manifest hash，并要求 locked contract back-reference exact `call_id` 和 `contract_draft_id`。Human review timing 要求 review start/finish/duration、reviewer、source_bundle_hash、visible_input_hash、contract_hash、manifest_hash，并冻结 `locked_at < first_scoring_started_at`。`tab:cost` 明确只能来自 human-time logs，不得混入 LLM/VPS/benchmark runtime。

7. **preflight/full run gate 严格**
   preflight 10 case units/domain 只能在 frozen P0 manifest 中预声明后进入 formal scored records；failed formal preflight validation blocks full run；恢复只能 retry/resume 同一 frozen manifest、record_slot、case_unit_id、contract hash、config hash、taxonomy version 和 deterministic order；不得替换、cherry-pick、移到 appendix 或静默丢弃。

8. **mock/smoke/dry-run 污染风险被明确阻断**
   packet 多处规定 smoke/dry_run/mock output 只能用于工程自检或 synthetic fixture，不能进入 formal scored records、metrics、tables、figures、appendix empirical outputs、final report 或 paper mapping。Step 5 也被禁止生成 formal `results/manifests/pre_scoring_freeze.json`。

9. **acceptance tests 足以防止明显错误实现进入 Step 2-12**
   tests/gates 覆盖 schema invalid fixtures、contract/freeze ordering、native evaluator decisive-evidence 条件、adapter/scorer boundary、agent identity rejection、R1-R7 golden/overlap fixtures、INFRA_EXCLUDED exclusion、COUNTED_ONLY_SCORE null behavior、stronger_measurement sidecar、stats/paper gates、audit/rerun rules、model hardcoding ban、paper-output fallback ban。作为 Step 1 spec freeze 的 acceptance surface 是足够的。

10. **P1/P2/P3 appendix、audit/rerun、release、stronger_measurement sidecar 覆盖充分**
    packet 覆盖 denominator audit、case-cluster bootstrap、pairwise margins、rerun subset、blinded audit、per-agent envelopes、AndroidWorld/WorkArena/OSWorld appendix、judge-only diagnostic、maintenance update、matched-budget controls、release/rescorer、macro contract、stronger_measurement sidecar exclusion。

11. **硬编码模型 ID 与 INFRA_EXCLUDED 规则明确**
    packet 禁止在 code、tests、runner、scorer、paper generation、review packets 中硬编码 Agent A-D、contract_drafter、judge_only 的 concrete model id/version pin/temperature/prompt hash/API-key env value，除非是无法进入 formal run 的 synthetic config fixture。INFRA_EXCLUDED 必须 `evidence_label=null`，不进入 evidence envelope denominator，但进入 denominator audit。

12. **paper_mapping coverage 与 missing-label blocking 充分**
    packet 列出 required labels，并规定 missing、unmapped、fallback/manual empirical data、mock/smoke/dry_run mapping、undeclared non-formal appendix/diagnostic mapping 都 fail closed；唯一例外是 paper text 与 manifest 同步更新。这满足 Step 1 冻结要求。

13. **canonical domain/phase/type、record_slot、native_label、OSWorld、pairwise tolerance、Agent probe rationale 均已前置冻结或标记为 locked-manifest blocker**
    canonical domain id 与 display name 被分离；phase/experiment_type/priority 被固定；record_slot、attempt、final_attempt、completed_record、infra_exclusion_record 语义明确；native_label 只能作 diagnostic metadata，除非 artifact-backed；OSWorld evaluator_failure/evaluator_unstable 不得映射为 evidence UNRESOLVE；pairwise tolerance 若未设置会 block aggregation/paper outputs；Agent A-D probe rationale 与 concrete config 均必须从 locked manifest 确认。

## Required Fixes

无阻断 Step 2 的必需修复。

建议在 Step 2/Step 7 前落实以下 hardening：

* 明确禁止 verdict_engine 可见 artifact path/id 中编码 agent/model/provider identity，或规定必须使用 opaque/canonical artifact references。
* 固定 `unresolve_level` 的枚举和值域，或删除该字段。
* 明确 audit human time 是否进入 `tab:cost`。
* 将 native evaluator missing-provenance 的 “validation failure vs R6” 分界写成可执行规则。
* 增加 repo clean/tree hash gate，防止 freeze 后 uncommitted code drift。

## Decision

ALLOW_NEXT_STEP
