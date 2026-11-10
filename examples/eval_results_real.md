# 端到端评测结果（真实模型）

- 模型：`gpt-4o-mini`
- 运行时间：2026-11-10 19:50，耗时 346s
- 每个用例运行次数：3
- trace 目录：`examples/real/`（文件名 `用例ID_run次数`）
- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误

## 汇总

- 总通过率：34/48（71%）
- 全部运行都通过的用例：9/16
- 失败用例：C03, C04, C05, C06, C10, C14, V03

## 逐用例结果

| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |
|---|---|---|---|---|---|---|---|---|
| C01 | 明确答案 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→F<br>S→R:D03→F<br>S→R:D03→F |
| C02 | 改写后的相似问题 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→F<br>S→R:D03→F<br>S→R:D03→F |
| C03 | 文档冲突 | conflict_need_confirmation | conflict_need_confirmation / need_clarification / conflict_need_confirmation | 2/3 | 5 / 6 / 5 | 通过（3 条） / 通过（无引用） / 通过（3 条） | 0 / 0 / 0 | S→R:D02→R:D01→R:D05→F<br>S→R:D02→R:D01→R:D05→A→F<br>S→R:D02→R:D01→R:D05→F |
| C04 | 文档冲突、改写后的相似问题 | conflict_need_confirmation | conflict_need_confirmation / need_clarification / conflict_need_confirmation | 2/3 | 5 / 5 / 5 | 通过（2 条） / 通过（无引用） / 通过（3 条） | 0 / 0 / 0 | S→R:D02→R:D01→A→F<br>S→R:D02→R:D01→A→F<br>S→R:D05→R:D02→R:D01→F |
| C05 | 文档冲突 | answered | conflict_need_confirmation / conflict_need_confirmation / conflict_need_confirmation | 0/3 | 4 / 4 / 5 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D02→F<br>S→R:D05→R:D02→F<br>S→R:D05→R:D02→A→F |
| C06 | 文档冲突、明确答案 | answered | conflict_need_confirmation / conflict_need_confirmation / conflict_need_confirmation | 0/3 | 5 / 5 / 5 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D07→R:D06→A→F<br>S→R:D07→R:D06→A→F<br>S→R:D07→R:D06→A→F |
| C07 | 资料外问题 | out_of_scope | out_of_scope / out_of_scope / out_of_scope | 3/3 | 4 / 3 / 7 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | S→S→S→F<br>S→S→F<br>S→S→S→S→S→S→F |
| C08 | 上下文追问 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D04→F<br>S→R:D04→F<br>S→R:D04→F |
| C09 | 追问 | need_clarification | need_clarification / need_clarification / need_clarification | 3/3 | 2 / 2 / 2 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | A→F<br>A→F<br>A→F |
| C10 | 工具失败 | failed / answered | incomplete / failed / incomplete | 1/3 | 10 / 10 / 10 | —（未完成 finish） / 通过（无引用） / —（未完成 finish） | 0 / 0 / 0 | S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗<br>S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→F<br>S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗→S✗ |
| C11 | 工具失败 | answered | answered / answered / answered | 3/3 | 4 / 4 / 4 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S✗→S→R:D03→F<br>S✗→S→R:D03→F<br>S✗→S→R:D03→F |
| C12 | 步数上限 | incomplete | incomplete / incomplete / incomplete | 3/3 | 2 / 2 / 2 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→R:D02<br>S→R:D02<br>S→R:D02 |
| C13 | 资料外问题 | out_of_scope / answered | out_of_scope / out_of_scope / out_of_scope | 3/3 | 6 / 6 / 6 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | S→R:D03→S→R:D03→A→F<br>S→R:D03→S→R:D03→A→F<br>S→R:D03→S→R:D03→A→F |
| C14 | 资料外问题 | out_of_scope | need_clarification / need_clarification / out_of_scope | 1/3 | 5 / 5 / 5 | 通过（无引用） / 通过（无引用） / 通过（1 条） | 0 / 0 / 0 | S→S→R:D09→A→F<br>S→S→S→A→F<br>S→S→R:D09→A→F |
| V03 | 替换文档 | answered | conflict_need_confirmation / answered / conflict_need_confirmation | 1/3 | 4 / 4 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D01→R:D05→F<br>S→R:D01→R:D05→F<br>S→R:D01→R:D05→F |
| V05 | 替换文档、文档冲突 | conflict_need_confirmation | conflict_need_confirmation / conflict_need_confirmation / conflict_need_confirmation | 3/3 | 4 / 4 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D01→F<br>S→R:D05→R:D01→F<br>S→R:D05→R:D01→F |

## 未通过的运行

| 用例 | 第几次 | 问题 | trace |
|---|---|---|---|
| C03 | 2 | 状态 need_clarification 不在期望 ['conflict_need_confirmation'] 中 | [C03_run2.md](real/C03_run2.md) |
| C04 | 2 | 状态 need_clarification 不在期望 ['conflict_need_confirmation'] 中 | [C04_run2.md](real/C04_run2.md) |
| C05 | 1 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C05_run1.md](real/C05_run1.md) |
| C05 | 2 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C05_run2.md](real/C05_run2.md) |
| C05 | 3 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C05_run3.md](real/C05_run3.md) |
| C06 | 1 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C06_run1.md](real/C06_run1.md) |
| C06 | 2 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C06_run2.md](real/C06_run2.md) |
| C06 | 3 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [C06_run3.md](real/C06_run3.md) |
| C10 | 1 | 状态 incomplete 不在期望 ['failed', 'answered'] 中 | [C10_run1.md](real/C10_run1.md) |
| C10 | 3 | 状态 incomplete 不在期望 ['failed', 'answered'] 中 | [C10_run3.md](real/C10_run3.md) |
| C14 | 1 | 状态 need_clarification 不在期望 ['out_of_scope'] 中；gaps 应非空 | [C14_run1.md](real/C14_run1.md) |
| C14 | 2 | 状态 need_clarification 不在期望 ['out_of_scope'] 中；gaps 应非空 | [C14_run2.md](real/C14_run2.md) |
| V03 | 1 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [V03_run1.md](real/V03_run1.md) |
| V03 | 3 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [V03_run3.md](real/V03_run3.md) |
