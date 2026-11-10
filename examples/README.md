# examples 索引

本目录保存所有评测结果和运行记录（trace）。真实模型和 Mock 的记录分开存放：

- `real/<tag>/`：真实模型 trace，每轮一个子目录，文件名 `用例ID_run次数.jsonl / .md`
- `mock/`：脚本化 Mock 的 trace。**Mock 按固定脚本行动，只验证流程（循环、工具、校验、步数上限、故障注入），不证明真实模型的决策效果。**
- `eval_results_*.md`：每轮评测报告（期望状态、各次实际状态、通过次数、步数、引用校验、finish 被拒次数、动作路径）
- `retrieval_eval_results.md`：检索评测（BM25 / BM25+同义词）

每个 trace 的 `.md` 是可读版本（步骤、参数、决策依据 reason、返回摘要、下一步、最终结果和 conflict_check），`.jsonl` 是同一内容的结构化版本（第一行 meta，中间每步一行，最后一行 result）。

路径记号：`S`=search_docs，`R:Dxx`=read_doc，`A`=ask_user，`F`=finish，`T`=未调用工具的纯文本回复，`✗`=该步返回错误（含 finish 被拒）。

## 每轮评测结果

每轮 16 个用例 × 3 次 = 48 次运行。通过率由 `scripts/run_eval.py` 按 `data/cases.jsonl` 的期望自动判定。

| 轮次 | 模型 | 结果文件 | trace 目录 | 通过率 | 本轮改动 |
|---|---|---|---|---|---|
| v1（基线） | gpt-4o-mini | [eval_results_real_v1.md](eval_results_real_v1.md) | `real/v1/` | 34/48 | 首次全量运行。read_doc 按 paragraph_ids 只返回请求段落 |
| v1-variant-split | gpt-4o-mini | [eval_results_real_v1-variant-split.md](eval_results_real_v1-variant-split.md) | `real/v1-variant-split/` | 4/6（只跑 V03、V05） | 替换版数据拆成 variant_a（V03）和 variant_b（V05），代码不变 |
| v2 | gpt-4o-mini | [eval_results_real_v2.md](eval_results_real_v2.md) | `real/v2/` | 33/48 | read_doc 总是返回全文 |
| v2-strong | gpt-4.1 | [eval_results_real_v2-strong.md](eval_results_real_v2-strong.md) | `real/v2-strong/` | 25/48 | 诊断：代码同 v2，只换更强模型 |
| v3 | gpt-4o-mini | [eval_results_real_v3.md](eval_results_real_v3.md) | `real/v3/` | 35/48 | prompt：冲突核对步骤（范围分工 / 已被替代 / 真冲突）、资料外与追问规则、连续失败规则；observation 附剩余步数和重复调用提示 |
| v3-strong | gpt-4.1 | [eval_results_real_v3-strong.md](eval_results_real_v3-strong.md) | `real/v3-strong/` | 34/48 | 代码同 v3 |
| v3-dataC0 | gpt-4o-mini | [eval_results_real_v3-dataC0.md](eval_results_real_v3-dataC0.md) | `real/v3-dataC0/` | 3/3（只跑 V05） | variant_b 的 D05 去掉"差旅"字样，代码同 v3 |
| v3-strong-dataC0 | gpt-4.1 | [eval_results_real_v3-strong-dataC0.md](eval_results_real_v3-strong-dataC0.md) | `real/v3-strong-dataC0/` | 2/3（只跑 V05） | 同上 |
| **v4（最终）** | **gpt-4o-mini** | [eval_results_real_v4.md](eval_results_real_v4.md) | `real/v4/` | **41/48** | finish 增加必填的结构化 conflict_check 及校验 |
| v4-strong | gpt-4.1 | [eval_results_real_v4-strong.md](eval_results_real_v4-strong.md) | `real/v4-strong/` | 24/48 | 代码同 v4（25 次因过度核实循环撞到步数上限） |
| Mock | 脚本化 Mock | [eval_results_mock.md](eval_results_mock.md) | `mock/` | 16/16 | 随最终代码重新生成；只验证流程 |

各轮详细对比和分析见 [docs/03-evaluation.md](../docs/03-evaluation.md)，每轮的决策过程见 [docs/decision-log.md](../docs/decision-log.md)。

## 验收点代表性 trace（v4，gpt-4o-mini）

| 验收点 | 用例 | trace | 路径 | 结果 |
|---|---|---|---|---|
| 正常回答（明确答案） | C01 工作满5年有几天年假？ | [real/v4/C01_run1.md](real/v4/C01_run1.md) | S→R:D03→F | answered，5 天，引用 D03 P1 |
| 文档冲突（真冲突） | C03 报销期限多久？ | [real/v4/C03_run1.md](real/v4/C03_run1.md) | S→R:D02→R:D01→R:D05→F✗→F | 第一次 finish 以 answered 提交但 conflict_check 中有 true_conflict，被拒后改为 conflict_need_confirmation，引用 D01 30 天、D02 15 天 |
| 文档冲突（可查证的表面冲突） | C05 出差回来多久内必须报销？ | [real/v4/C05_run2.md](real/v4/C05_run2.md) | S→R:D05→F | answered，10 天，引用 D05 P2。注意：这次只读了 D05，没有接触 D01/D02，答案正确但没有体现冲突核对 |
| 文档冲突（已被替代，gpt-4.1 对照） | C06 笔记本电脑几年能换？ | [real/v4-strong/C06_run1.md](real/v4-strong/C06_run1.md) | S→R:D07→R:D06→R:D07→R:D06→F | answered 3 年；conflict_check 标 D06–D07 为 superseded，basis 为 D07 P1"《办公设备申领规定（2022版）》同时废止"。gpt-4o-mini 在 v4 中此用例 0/3 |
| 资料外 | C07 公司股票期权怎么行权？ | [real/v4/C07_run1.md](real/v4/C07_run1.md) | 9×S→F | out_of_scope，gaps 说明缺少期权制度 |
| 资料外（文档被检索到但不覆盖） | C13 年假没休完能折现吗？ | [real/v4/C13_run2.md](real/v4/C13_run2.md) | S→R:D03→A→F✗→F | out_of_scope，说明 D03 没有折现规定（第一次 finish 漏写 conflict_check.claims 被拒） |
| 改写问题 | C02 我入职五年了，带薪休假一年能休多少天 | [real/v4/C02_run1.md](real/v4/C02_run1.md) | S→R:D03→F | answered，与 C01 一致 |
| 上下文追问 | C08 （历史：请假3天要谁审批）那超过3天呢？ | [real/v4/C08_run2.md](real/v4/C08_run2.md) | S→R:D04→F | answered，引用 D04 P3 |
| 指代不清追问 | C09 这个能报吗？ | [real/v4/C09_run1.md](real/v4/C09_run1.md) | A→F | need_clarification |
| 工具失败（恢复） | C11 search_docs 第 1 次失败 | [real/v4/C11_run1.md](real/v4/C11_run1.md) | S✗→S→R:D03→F | 重试后 answered |
| 工具失败（持续） | C10 search_docs 一直失败 | [real/v4/C10_run1.md](real/v4/C10_run1.md) | 9×S✗→F | failed，gaps 说明缺口（注意：模型重试了 9 次，没有遵守"连续失败 2 次后换方式"） |
| 步数上限 | C12 max_steps=2 | [real/v4/C12_run1.md](real/v4/C12_run1.md) | S→R:D02 | incomplete，reason=max_steps_reached |
| 替换文档 A | V03 报销期限多久？（variant_a：删除 D02，D01 改为 20 天） | [real/v4/V03_run2.md](real/v4/V03_run2.md) | S→R:D01→R:D05→F | answered 20 天（对比 C03 的冲突） |
| 替换文档 B | V05 出差回来多久内必须报销？（variant_b：D05 无优先级、适用全部费用） | [real/v4/V05_run1.md](real/v4/V05_run1.md) | S→R:D01→R:D05→F | conflict_need_confirmation（对比 C05 的 answered） |

## 两条明显不同的执行路径

1. **一次检索直接回答**：[real/v4/C01_run1.md](real/v4/C01_run1.md)
   `search_docs → read_doc(D03) → finish(answered)`，3 步。单一文档能直接回答，conflict_check 只有一条 claim。
2. **检索 → 读多份文档 → finish 被拒 → 修正为冲突**：[real/v4/C03_run1.md](real/v4/C03_run1.md)
   `search_docs → read_doc(D02) → read_doc(D01) → read_doc(D05) → finish(answered) 被拒 → finish(conflict_need_confirmation)`，6 步。被拒原因：relations 中有 true_conflict 而 status 是 answered。模型根据校验错误修改了状态。

其他可对比的路径：
- 工具失败后重试：[real/v4/C11_run1.md](real/v4/C11_run1.md)（`S✗→S→R→F`）
- 只问不查：[real/v4/C09_run1.md](real/v4/C09_run1.md)（`A→F`）
- 替换文档后动作和答案改变：[C03_run1](real/v4/C03_run1.md)（冲突）→ [V03_run2](real/v4/V03_run2.md)（answered 20 天）；[C05_run2](real/v4/C05_run2.md)（answered 10 天）→ [V05_run1](real/v4/V05_run1.md)（冲突）

## 需要注意的记录

- [real/v4/C14_run1.md](real/v4/C14_run1.md) 被判为通过（out_of_scope），但 answer 中把 D09（视频导出、存储空间）的说法套到了报表导出上。逐字校验和状态检查都发现不了这类问题，见 docs/03-evaluation.md 的已知限制。
- [real/v4/V03_run1.md](real/v4/V03_run1.md) 为 `failed / llm_error`（API 超时，重试 1 次后仍超时），与 Agent 逻辑无关。
