# 端到端评测结果（真实模型，v3-strong）

- 模型：`gpt-4.1`
- 运行时间：2026-11-10 20:41，耗时 497s
- 每个用例运行次数：3
- trace 目录：`examples/real/v3-strong/`（文件名 `用例ID_run次数`）
- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误

## 汇总

- 总通过率：34/48（71%）
- 全部运行都通过的用例：11/16
- 失败用例：C03, C04, C13, C14, V05

## 逐用例结果

| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |
|---|---|---|---|---|---|---|---|---|
| C01 | 明确答案 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→F<br>S→R:D03→F<br>S→R:D03→F |
| C02 | 改写后的相似问题 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D03→F<br>S→R:D03→F<br>S→R:D03→F |
| C03 | 文档冲突 | conflict_need_confirmation | answered / answered / answered | 0/3 | 5 / 5 / 5 | 通过（3 条） / 通过（3 条） / 通过（3 条） | 0 / 0 / 0 | S→R:D02→R:D01→R:D05→F<br>S→R:D02→R:D01→R:D05→F<br>S→R:D02→R:D01→R:D05→F |
| C04 | 文档冲突、改写后的相似问题 | conflict_need_confirmation | answered / answered / answered | 0/3 | 5 / 10 / 5 | 通过（3 条） / 通过（3 条） / 通过（4 条） | 0 / 0 / 0 | S→R:D02→R:D01→R:D05→F<br>S→R:D02→R:D01→R:D05→R:D05→R:D02→R:D01→R:D02→R:D01→F<br>S→R:D02→R:D01→R:D05→F |
| C05 | 文档冲突 | answered | answered / answered / answered | 3/3 | 8 / 8 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01→F<br>S→R:D05→R:D02→R:D01→R:D05→R:D02→R:D01→F<br>S→R:D05→R:D02→F |
| C06 | 文档冲突、明确答案 | answered | answered / answered / answered | 3/3 | 4 / 4 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D07→R:D06→F<br>S→R:D07→R:D06→F<br>S→R:D07→R:D06→F |
| C07 | 资料外问题 | out_of_scope | out_of_scope / out_of_scope / out_of_scope | 3/3 | 9 / 10 / 10 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | S→S→S→S→S→S→S→S→F<br>S→S→S→S→S→S→S→S→S→F<br>S→S→S→S→S→S→S→S→S→F |
| C08 | 上下文追问 | answered | answered / answered / answered | 3/3 | 3 / 3 / 3 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S→R:D04→F<br>S→R:D04→F<br>S→R:D04→F |
| C09 | 追问 | need_clarification | need_clarification / need_clarification / need_clarification | 3/3 | 2 / 2 / 2 | 通过（无引用） / 通过（无引用） / 通过（无引用） | 0 / 0 / 0 | A→F<br>A→F<br>A→F |
| C10 | 工具失败 | failed / answered | answered / answered / failed | 3/3 | 10 / 10 / 4 | 通过（1 条） / 通过（1 条） / 通过（无引用） | 0 / 0 / 0 | S✗→S✗→R:D01→S✗→R:D02→S✗→R:D03→R:D04→R:D05→F<br>S✗→S✗→S✗→R:D01→R:D02→R:D03→R:D04→R:D05→R:D06→F<br>S✗→S✗→S✗→F |
| C11 | 工具失败 | answered | answered / answered / answered | 3/3 | 4 / 4 / 4 | 通过（1 条） / 通过（1 条） / 通过（1 条） | 0 / 0 / 0 | S✗→S→R:D03→F<br>S✗→S→R:D03→F<br>S✗→S→R:D03→F |
| C12 | 步数上限 | incomplete | incomplete / incomplete / incomplete | 3/3 | 2 / 2 / 2 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→R:D02<br>S→R:D02<br>S→R:D02 |
| C13 | 资料外问题 | out_of_scope / answered | answered / answered / incomplete | 0/3 | 10 / 10 / 10 | 通过（1 条） / 通过（1 条） / —（未完成 finish） | 0 / 0 / 0 | S→R:D03→S→S→S→S→R:D03→S→S→F<br>S→R:D03→S→S→S→R:D03→S→S→S→F<br>S→R:D03→S→S→S→R:D03→S→S→S→R:D03 |
| C14 | 资料外问题 | out_of_scope | incomplete / incomplete / incomplete | 0/3 | 10 / 10 / 10 | —（未完成 finish） / —（未完成 finish） / —（未完成 finish） | 0 / 0 / 0 | S→S→S→S→S→S→R:D09→S→S→R:D02<br>S→S→S→S→S→S→S→R:D09→R:D02→R:D03<br>S→S→S→S→S→S→S→R:D09→R:D01→R:D03 |
| V03 | 替换文档 | answered | answered / answered / answered | 3/3 | 4 / 4 / 4 | 通过（3 条） / 通过（3 条） / 通过（3 条） | 0 / 0 / 0 | S→R:D01→R:D05→F<br>S→R:D01→R:D05→F<br>S→R:D01→R:D05→F |
| V05 | 替换文档、文档冲突 | conflict_need_confirmation | answered / answered / conflict_need_confirmation | 1/3 | 6 / 6 / 10 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D01→R:D05→T→F<br>S→R:D05→R:D01→R:D05→R:D01→F<br>S→R:D05→R:D01→R:D05→R:D01→S→S→R:D05→R:D01→F |

## 未通过的运行

| 用例 | 第几次 | 问题 | trace |
|---|---|---|---|
| C03 | 1 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C03_run1.md](real/v3-strong/C03_run1.md) |
| C03 | 2 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C03_run2.md](real/v3-strong/C03_run2.md) |
| C03 | 3 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C03_run3.md](real/v3-strong/C03_run3.md) |
| C04 | 1 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C04_run1.md](real/v3-strong/C04_run1.md) |
| C04 | 2 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C04_run2.md](real/v3-strong/C04_run2.md) |
| C04 | 3 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [C04_run3.md](real/v3-strong/C04_run3.md) |
| C13 | 1 | gaps 应非空 | [C13_run1.md](real/v3-strong/C13_run1.md) |
| C13 | 2 | gaps 应非空 | [C13_run2.md](real/v3-strong/C13_run2.md) |
| C13 | 3 | 状态 incomplete 不在期望 ['out_of_scope', 'answered'] 中 | [C13_run3.md](real/v3-strong/C13_run3.md) |
| C14 | 1 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run1.md](real/v3-strong/C14_run1.md) |
| C14 | 2 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run2.md](real/v3-strong/C14_run2.md) |
| C14 | 3 | 状态 incomplete 不在期望 ['out_of_scope'] 中 | [C14_run3.md](real/v3-strong/C14_run3.md) |
| V05 | 1 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [V05_run1.md](real/v3-strong/V05_run1.md) |
| V05 | 2 | 状态 answered 不在期望 ['conflict_need_confirmation'] 中 | [V05_run2.md](real/v3-strong/V05_run2.md) |
