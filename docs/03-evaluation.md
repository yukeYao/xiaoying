# 03 评测：测试预期、实际结果、失败和限制

结论都注明了对应的 `examples/` 文件；每轮改动的决策过程见 [decision-log.md](decision-log.md)，examples 的索引见 [examples/README.md](../examples/README.md)。

## 测试与验证手段

| 类型 | 内容 | 结果 |
|---|---|---|
| 确定性测试（不依赖模型） | `pytest`：文档解析、分词与同义词、BM25、read_doc、引用逐字校验各规则、conflict_check 各规则、ask_user、故障注入、步数上限、无工具调用、重复调用提示、API 层重试、输出 schema、trace、CLI、评测检查逻辑 | 139 个全部通过 |
| Mock 流程测试 | 脚本化 Mock 跑 16 个用例，以及"错误引用被拒后修正""错误标 scope_split 被拒后改为 true_conflict""先回文本不调工具"等序列 | 16/16，[eval_results_mock.md](../examples/eval_results_mock.md)。**只验证流程，不证明真实模型的决策效果** |
| 检索评测 | 18 条开发 / 留出问题 + 5 条盲测问题 | 见下节 |
| 真实模型端到端 | 16 个用例 × 3 次（temperature=0 下结果仍有波动，所以重复运行），每轮一个 tag | 见"每轮改动与逐用例对比" |

## 检索评测

结果：[examples/retrieval_eval_results.md](../examples/retrieval_eval_results.md)，脚本：`scripts/eval_retrieval.py`。

| 子集 | 题数 | 模式 | recall@1 | recall@3 | MRR |
|---|---|---|---|---|---|
| 开发 + 留出 | 18 | bm25 / syn_w1.0 / syn_w0.5 | 0.861 | 1.000 | 0.972 |
| 留出集（同义词表定稿后才编写） | 5 | 三种相同 | 0.900 | 1.000 | 1.000 |
| 盲测集（问题由项目作者编写，B05 为资料外、不计入） | 4 | 三种相同 | 0.708 | 1.000 | 1.000 |

结论：
- **在 10 份文档的小语料下，静态同义词扩展没有可测量的收益**，三种模式的指标完全相同。
- 把扩展词降权到 0.5 修好了 R04 的排序（D01 回到第一），但 R03 同时退步（D05 排到第一），净效果为零。
- 根本原因可能是语料太小。计划之一是加入干扰文档后重新评估（未做）。
- 冲突类问题（R03、R04）在 top_k=5 时三种模式都能同时返回 D01 和 D02。
- 盲测 B05（报表导出超时）的前 10 个结果里没有 D09，返回的是 D03 / D02 / D04 等无关文档，需要 Agent 自己判断为资料外。这个问题后来成为用例 C14。

## 每轮改动与逐用例对比

所有轮次都是 16 个用例 × 3 次。

| 轮次 | 主要改动 |
|---|---|
| v1 | 基线。read_doc 按 paragraph_ids 只返回请求的段落 |
| v2 | read_doc 总是返回全文 |
| v2-strong | 代码同 v2，换 gpt-4.1（诊断模型能力） |
| v3 / v3-strong | prompt：冲突核对步骤、资料外与追问规则、连续失败规则；observation 附剩余步数、重复调用提示 |
| v3-dataC0 | 修正 variant_b 的 D05（去掉"差旅"字样），只跑 V05 |
| **v4** / v4-strong | finish 增加结构化 conflict_check 及程序校验 |

逐用例通过次数：

- **v1**：V03、V05 取 v1-variant-split，即替换版数据拆分后、代码不变的重跑。原始 v1 的 V03 用的是未拆分的替换版，为 1/3。
- **v3**：V05 取 v3-dataC0。
- **v3-strong**：V05 取 v3-strong-dataC0。

| 用例 | 验收点 | v1 | v2 | v3 | **v4** | v2-strong | v3-strong | v4-strong |
|---|---|---|---|---|---|---|---|---|
| C01 | 明确答案 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 1/3 |
| C02 | 改写 | 3/3 | 3/3 | 3/3 | 3/3 | 0/3 | 3/3 | 1/3 |
| C03 | 冲突 | 2/3 | 1/3 | 0/3 | **3/3** | 1/3 | 0/3 | 2/3 |
| C04 | 冲突 + 改写 | 2/3 | 0/3 | 0/3 | **3/3** | 0/3 | 0/3 | 2/3 |
| C05 | 表面冲突（优先级） | 0/3 | 0/3 | 3/3 | 2/3 | 2/3 | 3/3 | 1/3 |
| C06 | 表面冲突（废止） | 0/3 | 0/3 | 0/3 | 0/3 | 2/3 | 3/3 | 3/3 |
| C07 | 资料外 | 3/3 | 3/3 | 2/3 | 3/3 | 1/3 | 3/3 | 2/3 |
| C08 | 上下文追问 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/3 |
| C09 | 指代不清 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| C10 | 工具一直失败 | 1/3 | 1/3 | 3/3 | 3/3 | 1/3 | 3/3 | 0/3 |
| C11 | 工具失败后恢复 | 3/3 | 3/3 | 3/3 | 3/3 | 1/3 | 3/3 | 1/3 |
| C12 | 步数上限 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| C13 | 资料外（文档不覆盖） | 3/3 | 2/3 | 3/3 | 3/3 | 0/3 | 0/3 | 1/3 |
| C14 | 资料外（其他产品） | 1/3 | 2/3 | 3/3 | 1/3 | 0/3 | 0/3 | 0/3 |
| V03 | 替换文档 A | 1/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| V05 | 替换文档 B | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 1/3 |
| **合计** | | 34/48 | 33/48 | 38/48 | **41/48** | 25/48 | 35/48 | 24/48 |

结果文件：
- gpt-4o-mini：[v1](../examples/eval_results_real_v1.md)、[v1-variant-split](../examples/eval_results_real_v1-variant-split.md)、[v2](../examples/eval_results_real_v2.md)、[v3](../examples/eval_results_real_v3.md)、[v3-dataC0](../examples/eval_results_real_v3-dataC0.md)、[v4](../examples/eval_results_real_v4.md)
- gpt-4.1：[v2-strong](../examples/eval_results_real_v2-strong.md)、[v3-strong](../examples/eval_results_real_v3-strong.md)、[v3-strong-dataC0](../examples/eval_results_real_v3-strong-dataC0.md)、[v4-strong](../examples/eval_results_real_v4-strong.md)

（各报告文件头部的"总通过率"是该轮自身的结果；上表的 v1、v3 两列为了可比，替换了 V03 / V05 的数据。）

### 每轮的主要发现

**v1 → v2：read_doc 返回全文**
- 证据：[real/v1/C05_run1.md](../examples/real/v1/C05_run1.md)、[real/v2/C05_run1.md](../examples/real/v2/C05_run1.md)。
- v1 中 C05、C06 失败，是因为模型只用 paragraph_ids 读了命中段落，没看到 D05 P3（优先级）、D07 P1（废止）。
- v2 返回全文后，V03 由 1/3 变为 3/3，但 C05、C06 仍是 0/3：模型看到了全文，仍然没有核对这些条款。**看到全文不等于会去核对。**
- C03、C04 出现了更严重的失败形态：把 D01 30 天、D02 15 天并列当作 answered（[real/v2/C03_run2.md](../examples/real/v2/C03_run2.md)）。

**v2-strong（换 gpt-4.1 诊断）**
- C05、C06 由 0/3 变为 2/3，gpt-4.1 会引用优先级和废止条款（[real/v2-strong/C06_run1.md](../examples/real/v2-strong/C06_run1.md)）。所以 C05 / C06 的失败**主要来自模型能力**。
- C03、C04 **不是能力问题**：gpt-4.1 只回答 D02 的 15 天、忽略 D01，写"根据公司最新的……"（[real/v2-strong/C04_run1.md](../examples/real/v2-strong/C04_run1.md)），正是题目参考实例禁止的"擅自回答 15 天"。
- 同时出现了过度核实循环，19 次 incomplete（[real/v2-strong/C01_run1.md](../examples/real/v2-strong/C01_run1.md)：连续 9 次 read_doc D03）。

**v3：prompt 修改**
- 有效：
  - gpt-4o-mini 的 C05 0/3 → 3/3，C13 / C14 3/3。
  - gpt-4.1 在单文档问题上的循环消失（C01、C02、C11 3/3）。
  - C10 两个模型都是 3/3。但 gpt-4o-mini 并没有遵守"连续失败 2 次后换方式"，而是 9 次 search 失败后在第 10 步以 failed 结束（[real/v3/C10_run1.md](../examples/real/v3/C10_run1.md)），更可能是剩余步数提示起了作用。
- 无效：C03、C04 两个模型都是 0/3。gpt-4o-mini 仍把矛盾规定并列，还自行编出"一般费用 15 天，其他费用 30 天"的分工（[real/v3/C03_run1.md](../examples/real/v3/C03_run1.md)）。gpt-4.1 仍只取 D02（[real/v3-strong/C03_run1.md](../examples/real/v3-strong/C03_run1.md)）。
- V05 退步，原因与 variant_b 的 D05 标题和正文仍写"差旅"有关，修正数据后 gpt-4o-mini 3/3（[real/v3-dataC0/V05_run1.md](../examples/real/v3-dataC0/V05_run1.md)）。

**v4：结构化 conflict_check**
- gpt-4o-mini 的 C03、C04 0/3 → 3/3。
- 起作用的是"存在 true_conflict 时 status 必须是 conflict_need_confirmation"这条校验：6 次运行都是先以 answered 提交、同时在 relations 里写了 true_conflict，被拒后改正（[real/v4/C03_run1.md](../examples/real/v4/C03_run1.md)）。模型在结构化字段里能识别冲突，写 status 时却仍倾向 answered；校验把两者对齐了。
- gpt-4.1 完成的 C03 / C04 关系全部标对：D05 与 D01、D02 为 scope_split，D01 与 D02 为 true_conflict（[real/v4-strong/C03_run1.md](../examples/real/v4-strong/C03_run1.md)）。但 gpt-4.1 有 25 次 incomplete，见已知限制。
- v4 finish 被拒合计：gpt-4o-mini 13 次（C03 / C04 各 3 次触发状态一致性规则；C13 / C14 各 3 次漏写读过的文档；C05 1 次），gpt-4.1 8 次。

## 最终版本（v4，gpt-4o-mini）仍失败的运行

| 用例 | 失败次数 | trace | 原因 |
|---|---|---|---|
| C06 | 3/3 | [real/v4/C06_run2.md](../examples/real/v4/C06_run2.md) | 把 D06–D07 标成 true_conflict，没用上 D07 P1 的"2022 版同时废止"，answer 写"根据最新的 2024 版……"再请用户确认。gpt-4.1 在 v3 / v4 均为 3/3，判断为小模型能力问题 |
| C14 | 2/3 | [real/v4/C14_run2.md](../examples/real/v4/C14_run2.md) | 把"报表导出超时"当作剪影Pro 的产品问题，返回 need_clarification 问"您使用的是哪个版本" |
| C05 | 1/3 | [real/v4/C05_run1.md](../examples/real/v4/C05_run1.md) | 读了 D05 和 D02，把两者标成 true_conflict（D05 P3 写明优先于通用规定，应为 priority）；被状态一致性规则改为冲突状态。另外 2 次只读了 D05，单文档回答，正确但没有体现冲突核对 |
| V03 | 1/3 | [real/v4/V03_run1.md](../examples/real/v4/V03_run1.md) | API 超时，重试 1 次后仍超时，`failed / llm_error`，与 Agent 逻辑无关 |

此外，**判为通过但内容有问题**的运行（自动检查发现不了）：

- [real/v4/C14_run1.md](../examples/real/v4/C14_run1.md)：out_of_scope，但 answer 把 D09"检查设备剩余存储空间是否大于视频预估大小的两倍"套用到报表导出上。
- [real/v4/C03_run1.md](../examples/real/v4/C03_run1.md) 等 3 次：状态正确，但 conflict_check 把 D05 与 D01、D02 也标成 true_conflict，冲突说明里多列了差旅规定。

## 已知限制

1. **逐字校验只能证明引用存在，不能证明引用支持回答**。例：C14_run1 引用逐字正确，但用视频导出的建议回答报表导出问题。
2. **程序无法判断 conflict_check 的语义**：
   - 把不同结论标成 consistent，校验拦不住。v4 的 96 次运行中没有出现这种情况。
   - 拿不相关的原文当 basis，校验同样拦不住。这种情况实际出现过：[real/v4-strong/V05_run1.md](../examples/real/v4-strong/V05_run1.md) 把 D05–D01 标成 priority，basis 却是 D05 P1"本规定适用于公司全部费用报销。"，这是适用范围说明，不是优先级说明。随后以"最新且适用全部费用"为由回答 10 天。
   - 这两类都需要人工审核 trace。
3. **gpt-4.1 的过度核实循环**：v4 中 25 次 incomplete，例如 [real/v4-strong/C08_run1.md](../examples/real/v4-strong/C08_run1.md) 反复重读 D04、D03 并检索"适用范围"。重复调用和剩余步数提示没能让它停止。因此默认模型定为 gpt-4o-mini。
4. **C06 在 gpt-4o-mini 上始终失败**（v1–v4 都是 0/3）：模型不会用废止说明判定"已被替代"，只能换更强的模型。
5. **C13 的推断性结论**：gpt-4.1 多次回答"年假未休完不能折现"（[real/v4-strong/C13_run1.md](../examples/real/v4-strong/C13_run1.md)），这是从"逾期作废"推出来的，原文没有，且 gaps 为空。gpt-4o-mini 在 v4 中 3/3 正确地判为 out_of_scope。
6. **"连续失败 2 次后换方式"的规则没有被 gpt-4o-mini 遵守**：C10 每次都检索 9 次，在最后一步以 failed 结束。
7. **模型偏向"版本较新"**：prompt 明确禁止，仍多次出现（v2-strong C04、v3-strong-dataC0 V05、v4-strong V05）。对 C03 / C04 来说，conflict_check 的状态一致性规则能拦住；但如果模型把关系标成 priority 并给出一段不相关的 basis，就拦不住（见第 2 条）。
8. **结果有随机性**：temperature=0 下同一用例 3 次的结果仍可能不同，单次运行的结论不可靠。
9. **检索**：小语料下同义词扩展没有可测量的收益；read_doc 返回全文只适合短文档。
10. **数据与评测本身**：用例和期望由项目作者与 Claude Code 编写，测试集较小（16 个用例）；自动评测只检查状态、引用文档和 gaps 是否为空，不检查 answer 的内容是否正确。

## 未完成

- 加入干扰文档、扩大语料后重新评估检索。
- 针对 gpt-4.1 过度核实循环的改进（例如放宽"读过的文档都要填 scope_quote"），以及改进后的重新评测。
- 答案内容的自动检查（例如检查 answer 中的数字是否都出现在引用里）。

## 人工审核结果

> **说明**：本节是按项目作者要求，由 Claude Code 模拟人工审核完成的，不是作者本人逐条审核的结果。作者核对了结论。

**范围**：v4（gpt-4o-mini，`examples/real/v4/`），每个用例取一次运行，共 16 条。默认取 run1；V03 的 run1 因 API 超时没有 finish，改取 run2。

**判断标准**：
- 引用是否支持回答：**支持**＝回答的每个结论都能由所引原文直接得出；**部分支持**＝所引原文支持回答中的具体数字或条款，但回答的整体结论（如"存在冲突、请确认"）或适用对象超出原文所能支持的范围；**不支持**＝所引原文与问题不对应；**不适用**＝没有引用（无需引用的澄清、拒答、失败或未完成）。
- 引用以外的内容：回答中出现、但所引原文里没有的事实性内容。文档标题、版本日期属于 read_doc 返回的元数据，不算。
- 引用是否逐字存在由程序校验（16 条中 15 条有 finish，均通过；C12 未 finish），本节不重复判断。

| 用例 | 运行 | 状态 | 自动评测 | 引用是否支持回答 | 引用以外的内容 | 说明 |
|---|---|---|---|---|---|---|
| C01 | [run1](../examples/real/v4/C01_run1.md) | answered | 通过 | 支持 | 无 | D03 P1"已满1年不满10年的，年休假5天"，5 年落在区间内 |
| C02 | [run1](../examples/real/v4/C02_run1.md) | answered | 通过 | 部分支持 | 无 | 原文按"累计工作"年限计算，回答写成"您入职满五年，年休假为5天"。入职 5 年不等于累计工作 5 年（有此前工龄时可能已满 10 年），回答没有提示这一前提 |
| C03 | [run1](../examples/real/v4/C03_run1.md) | conflict_need_confirmation | 通过 | 部分支持 | 无 | 三条引用分别支持 15 天、30 天、10 天。但"三份文档存在冲突"不被原文支持：D05 只适用于差旅（P1），且 P3 写明优先于通用规定，D05 与 D01、D02 不是同范围冲突。模型读过 D05 全文，回答没有提到适用范围 |
| C04 | [run1](../examples/real/v4/C04_run1.md) | conflict_need_confirmation | 通过 | 支持 | 无 | D02 P2（15 天，上传发票影像）、D01 P2（30 天）分别支持；回答把 D01 准确表述为"提交报销申请"。本次没有读 D05 |
| C05 | [run1](../examples/real/v4/C05_run1.md) | conflict_need_confirmation | 未通过 | 部分支持 | 无 | 引用支持 10 天和 15 天两个数字，但"请确认适用哪一条"与 D05 P3"优先于公司通用报销规定执行"相矛盾；P3 读过但没有引用 |
| C06 | [run1](../examples/real/v4/C06_run1.md) | conflict_need_confirmation | 未通过 | 部分支持 | 无 | 引用支持 3 年和 4 年，但"请确认您需要了解的是哪个版本"不成立：D07 P1 写明 2022 版同时废止（读过未引用）。另外回答省略了所引 D07 P3 后半句"因故障无法维修的，可随时申请更换" |
| C07 | [run1](../examples/real/v4/C07_run1.md) | out_of_scope | 通过 | 不适用 | 无 | 9 次检索后说明资料库中没有股票期权行权的信息，没有编造流程 |
| C08 | [run1](../examples/real/v4/C08_run1.md) | answered | 通过 | 支持 | 无 | 回答基本是 D04 P3 原文 |
| C09 | [run1](../examples/real/v4/C09_run1.md) | need_clarification | 通过 | 不适用 | 无 | 反问"具体指哪个报销项目或费用"，合理 |
| C10 | [run1](../examples/real/v4/C10_run1.md) | failed | 通过 | 不适用 | 无 | 回答"无法获取年假相关规定的信息"与实际情况一致。但 gaps 写"缺少关于年假规定的资料"不准确：失败原因是检索工具连续报错，不是资料缺失 |
| C11 | [run1](../examples/real/v4/C11_run1.md) | answered | 通过 | 支持 | 无 | 同 C01，表述为"累计工作已满5年"，与原文口径一致 |
| C12 | [run1](../examples/real/v4/C12_run1.md) | incomplete | 通过 | 不适用 | 无（无回答） | 2 步上限内未 finish，符合预期 |
| C13 | [run1](../examples/real/v4/C13_run1.md) | out_of_scope | 通过 | 支持 | 无 | D03 P2 支持"延至次年3月31日、逾期作废"；"文档中没有提到折现"经核对 D03 全文属实，没有推出"不能折现"。小问题：answer 引用了 D03 P2，conflict_check 却把 D03 的 claim 写成"与问题无关" |
| C14 | [run1](../examples/real/v4/C14_run1.md) | out_of_scope | 通过 | 不支持 | 有 | D09 P3 是剪影Pro 的视频导出建议，被套用到"报表导出超时"上；回答最后请用户提供"剪影Pro的技术支持或客服联系方式"，原文没有，且问题与剪影Pro 无关。conflict_check 自己也把 D09 标为"与问题无关"，与 answer 矛盾 |
| V03 | [run2](../examples/real/v4/V03_run2.md) | answered | 通过 | 支持 | 无 | variant_a：D01 P2（20 天）、D05 P2（差旅 10 天）分别支持；回答用"差旅费用"限定了 10 天的适用范围。conflict_check 标 scope_split，basis 为 D05 P3，语义正确 |
| V05 | [run1](../examples/real/v4/V05_run1.md) | conflict_need_confirmation | 通过 | 支持 | 无 | variant_b：D01 20 天与 D05 10 天，D05 适用于全部费用报销且没有优先级条款，属同范围冲突，请用户确认合理 |

**汇总**：支持 7 条（C01、C04、C08、C11、C13、V03、V05），部分支持 4 条（C02、C03、C05、C06），不支持 1 条（C14），不适用 4 条（C07、C09、C10、C12）。回答中出现引用以外内容的只有 C14。

**与自动评测的对比**：
- 一致：C05、C06 自动评测判为未通过，人工审核也认为结论不被原文支持（引用的数字对，但"需要确认"的结论错）。
- 自动评测通过、人工审核发现问题的有 3 条：
  - C14 run1：状态 out_of_scope 正确，但回答内容用了不相关的原文（已在上文"判为通过但内容有问题"中列出）。
  - C03 run1：状态正确，但把 D05 也说成冲突方（已在上文列出）。
  - C02 run1：本次新发现。把"入职年限"等同于"累计工作年限"，属于回答对适用条件的简化，引用校验和状态检查都发现不了。
- C10 run1 的 gaps 描述不准确（把工具失败说成资料缺失），自动评测只检查 gaps 是否非空，发现不了。
- 16 条中没有发现编造引用或编造规则。
