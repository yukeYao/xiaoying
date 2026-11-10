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

（由项目作者填写：抽查了哪些 trace、发现了什么、与自动评测结论是否一致。）
