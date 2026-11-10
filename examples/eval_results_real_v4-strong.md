# 端到端评测结果（真实模型，v4-strong）

- 模型：`gpt-4.1`
- 运行时间：2026-11-10 21:12，耗时 743s
- 每个用例运行次数：3
- trace 目录：`examples/real/v4-strong/`（文件名 `用例ID_run次数`）
- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误

## 汇总

- 总通过率：24/48（50%）
- 全部运行都通过的用例：4/16
- 失败用例：C01, C02, C03, C04, C05, C07, C08, C10, C11, C13, C14, V05

## 逐用例结果

| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |
|---|---|---|---|---|---|---|---|---|
| C01 | 明确答案 | answered | incomplete / incomplete / answered | 1/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→R:D06→R:D03→R:D03→R:D03→S→S→S→R:D03<br>S→R:D03→R:D06→R:D03→S→S→S→S→S→R:D03<br>S→R:D03→S→S→S→S→S→S→R:D03→F |
| C02 | 改写后的相似问题 | answered | incomplete / answered / need_clarification | 1/3 | 10 / 10 / 9 | —（未完成 finish） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→S→R:D03→S→R:D03→S→S→S→R:D03<br>S→R:D03→S→R:D03→S→S→S→S→R:D03→F<br>S→R:D03→S→R:D03→S→S→R:D03→A→F |
| C03 | 文档冲突 | conflict_need_confirmation | conflict_need_confirmation / conflict_need_confirmation / incomplete | 2/3 | 9 / 10 / 10 | 通过（4 条） / 通过（4 条） / —（未完成 finish） | 0 / 1 / 0 | S→R:D02→R:D01→R:D05→R:D02→R:D01→R:D05→A→F<br>S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→A→F✗→F<br>S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01 |
| C04 | 文档冲突、改写后的相似问题 | conflict_need_confirmation | conflict_need_confirmation / incomplete / conflict_need_confirmation | 2/3 | 10 / 10 / 10 | 通过（4 条） / —（未完成 finish） / 通过（4 条） | 1 / 0 / 1 | S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→A→F✗→F<br>S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→S→S→S<br>S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→A→F✗→F |
| C05 | 文档冲突 | answered | incomplete / incomplete / answered | 1/3 | 10 / 10 / 8 | —（未完成 finish） / —（未完成 finish） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01<br>S→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01<br>S→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01→F |
| C06 | 文档冲突、明确答案 | answered | answered / answered / answered | 3/3 | 6 / 6 / 6 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D07→R:D06→R:D07→R:D06→F<br>S→R:D07→R:D06→R:D07→R:D06→F<br>S→R:D07→R:D06→R:D07→R:D06→F |
| C07 | 资料外问题 | out_of_scope | incomplete / out_of_scope / out_of_scope | 2/3 | 10 / 10 / 10 | —（未完成 finish） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | S→S→S→S→S→S→S→S→S→S<br>S→S→S→S→S→S→S→S→S→F<br>S→S→S→S→S→S→S→S→S→F |
| C08 | 上下文追问 | answered | incomplete / incomplete / incomplete | 0/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→R:D04→R:D03→R:D04→R:D03→R:D04→R:D03→S→S→S<br>S→R:D04→R:D03→R:D04→R:D03→R:D04→R:D03→S→S→R:D08<br>S→R:D04→R:D03→R:D04→R:D03→S→S→S→S→R:D04 |
| C09 | 追问 | need_clarification | need_clarification / need_clarification / need_clarification | 3/3 | 7 / 8 / 3 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 1 / 1 / 0 | S→R:D01→R:D02→R:D05→A→F✗→F<br>S→S→R:D01→R:D02→R:D05→A→F✗→F<br>S→A→F |
| C10 | 工具失败 | failed / answered | incomplete / incomplete / incomplete | 0/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 1 / 0 / 0 | S✗→S✗→R:D01→S✗→R:D02→S✗→R:D03→R:D04→R:D05→F✗<br>S✗→S✗→R:D01→S✗→R:D02→R:D03→R:D04→R:D05→R:D06→R:D07<br>S✗→S✗→S✗→S✗→R:D01→R:D02→R:D03→R:D04→R:D05→R:D06 |
| C11 | 工具失败 | answered | incomplete / incomplete / answered | 1/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / 通过（1 条） | 0 / 0 / 0 | S✗→S→R:D03→R:D03→R:D03→S→S→S→S→R:D03<br>S✗→S→R:D03→R:D03→S→S→S→S→S→R:D03<br>S✗→S→R:D03→R:D03→S→S→R:D03→R:D03→R:D03→F |
| C12 | 步数上限 | incomplete | incomplete / incomplete / incomplete | 3/3 | 2 / 2 / 2 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→R:D02<br>S→R:D02<br>S→R:D02 |
| C13 | 资料外问题 | out_of_scope / answered | answered / incomplete / incomplete | 1/3 | 10 / 10 / 10 | 通过（1 条） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 1 | S→R:D03→S→S→S→S→S→R:D03→S→F<br>S→R:D03→S→S→S→S→R:D03→S→S→R:D03<br>S→R:D03→S→S→R:D08→S→S→S→R:D03→F✗ |
| C14 | 资料外问题 | out_of_scope | incomplete / incomplete / incomplete | 0/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→S→S→S→S→S→S→S→S→R:D09<br>S→S→S→S→S→S→S→S→R:D09→R:D03<br>S→S→S→S→S→S→S→S→S→R:D07 |
| V03 | 替换文档 | answered | answered / answered / answered | 3/3 | 10 / 4 / 10 | 通过（4 条） / 通过（3 条） / 通过（4 条） | 0 / 0 / 0 | S→R:D01→R:D05→R:D05→R:D01→R:D05→R:D01→R:D05→R:D01→F<br>S→R:D01→R:D05→F<br>S→R:D01→R:D05→R:D05→R:D01→R:D05→R:D01→R:D05→R:D01→F |
| V05 | 替换文档、文档冲突 | conflict_need_confirmation | answered / incomplete / conflict_need_confirmation | 1/3 | 10 / 10 / 10 | 通过（2 条） / —（未完成 finish） / 通过（2 条） | 1 / 0 / 0 | S→S→S→S→R:D05→R:D01→R:D01→R:D05→F✗→F<br>S→S→S→S→R:D05→R:D01→R:D01→R:D05→R:D05→R:D01<br>S→R:D05→R:D01→S→S→S→R:D05→R:D01→A→F |

## 未通过的运行

| 用例 | 第几次 | 问题 | trace |
|---|---|---|---|
| C01 | 1 | 状态 incomplete 不在期望 ['answered'] 中 | [C01_run1.md](real/v4-strong/C01_run1.md) |
| C01 | 2 | 状态 incomplete 不在期望 ['answered'] 中 | [C01_run2.md](real/v4-strong/C01_run2.md) |
| C02 | 1 | 状态 incomplete 不在期望 ['answered'] 中 | [C02_run1.md](real/v4-strong/C02_run1.md) |
| C02 | 3 | 状态 need_clarification 不在期望 ['answered'] 中 | [C02_run3.md](real/v4-strong/C02_run3.md) |
| C03 | 3 | 状态 incomplete 不在期望 ['conflict_need_confirmation'] 中 | [C03_run3.md](real/v4-strong/C03_run3.md) |
| C04 | 2 | 状态 incomplete 不在期望 ['conflict_need_confirmation'] 中 | [C04_run2.md](real/v4-strong/C04_run2.md) |
| C05 | 1 | 状态 incomplete 不在期望 ['answered'] 中 | [C05_run1.md](real/v4-strong/C05_run1.md) |
| C05 | 2 | 状态 incomplete 不在期望 ['answered'] 中 | [C05_run2.md](real/v4-strong/C05_run2.md) |
| C07 | 1 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C07_run1.md](real/v4-strong/C07_run1.md) |
| C08 | 1 | 状态 incomplete 不在期望 ['answered'] 中 | [C08_run1.md](real/v4-strong/C08_run1.md) |
| C08 | 2 | 状态 incomplete 不在期望 ['answered'] 中 | [C08_run2.md](real/v4-strong/C08_run2.md) |
| C08 | 3 | 状态 incomplete 不在期望 ['answered'] 中 | [C08_run3.md](real/v4-strong/C08_run3.md) |
| C10 | 1 | 状态 incomplete 不在期望 ['failed', 'answered'] 中 | [C10_run1.md](real/v4-strong/C10_run1.md) |
| C10 | 2 | 状态 incomplete 不在期望 ['failed', 'answered'] 中 | [C10_run2.md](real/v4-strong/C10_run2.md) |
| C10 | 3 | 状态 incomplete 不在期望 ['failed', 'answered'] 中 | [C10_run3.md](real/v4-strong/C10_run3.md) |
| C11 | 1 | 状态 incomplete 不在期望 ['answered'] 中 | [C11_run1.md](real/v4-strong/C11_run1.md) |
| C11 | 2 | 状态 incomplete 不在期望 ['answered'] 中 | [C11_run2.md](real/v4-strong/C11_run2.md) |
| C13 | 2 | 状态 incomplete 不在期望 ['out_of_scope', 'answered'] 中 | [C13_run2.md](real/v4-strong/C13_run2.md) |
| C13 | 3 | 状态 incomplete 不在期望 ['out_of_scope', 'answered'] 中 | [C13_run3.md](real/v4-strong/C13_run3.md) |
| C14 | 1 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run1.md](real/v4-strong/C14_run1.md) |
| C14 | 2 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run2.md](real/v4-strong/C14_run2.md) |
| C14 | 3 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run3.md](real/v4-strong/C14_run3.md) |
| V05 | 1 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [V05_run1.md](real/v4-strong/V05_run1.md) |
| V05 | 2 | 状态 incomplete 不在期望 ['conflict_need_confirmation'] 中 | [V05_run2.md](real/v4-strong/V05_run2.md) |
