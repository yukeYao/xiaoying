# 端到端评测结果（Mock）

> **Mock 运行**：脚本化 Mock 模型按固定脚本行动，只验证流程（循环、工具、校验、步数上限、故障注入），不证明真实模型的决策效果。

- 模型：`mock`
- 运行时间：2026-11-10 20:59，耗时 6s
- 每个用例运行次数：1
- trace 目录：`examples/mock/`（文件名 `用例ID_run次数`）
- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误

## 汇总

- 总通过率：16/16（100%）
- 全部运行都通过的用例：16/16
- 失败用例：无

## 逐用例结果

| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |
|---|---|---|---|---|---|---|---|---|
| C01 | 明确答案 | answered | answered | 1/1 | 3 | 通过（1 条） | 0 | S→R:D03→F |
| C02 | 改写后的相似问题 | answered | answered | 1/1 | 3 | 通过（1 条） | 0 | S→R:D03→F |
| C03 | 文档冲突 | conflict_need_confirmation | conflict_need_confirmation | 1/1 | 6 | 通过（2 条） | 0 | S→R:D01→R:D02→S→A→F |
| C04 | 文档冲突、改写后的相似问题 | conflict_need_confirmation | conflict_need_confirmation | 1/1 | 6 | 通过（2 条） | 0 | S→R:D01→R:D02→S→A→F |
| C05 | 文档冲突 | answered | answered | 1/1 | 3 | 通过（2 条） | 0 | S→R:D05→F |
| C06 | 文档冲突、明确答案 | answered | answered | 1/1 | 4 | 通过（2 条） | 0 | S→R:D06→R:D07→F |
| C07 | 资料外问题 | out_of_scope | out_of_scope | 1/1 | 3 | 通过（无引用） | 0 | S→S→F |
| C08 | 上下文追问 | answered | answered | 1/1 | 3 | 通过（1 条） | 0 | S→R:D04→F |
| C09 | 追问 | need_clarification | need_clarification | 1/1 | 2 | 通过（无引用） | 0 | A→F |
| C10 | 工具失败 | failed / answered | failed | 1/1 | 3 | 通过（无引用） | 0 | S✗→S✗→F |
| C11 | 工具失败 | answered | answered | 1/1 | 4 | 通过（1 条） | 0 | S✗→S→R:D03→F |
| C12 | 步数上限 | incomplete | incomplete | 1/1 | 2 | —（未完成 finish） | 0 | S→R:D01 |
| C13 | 资料外问题 | out_of_scope / answered | out_of_scope | 1/1 | 3 | 通过（1 条） | 0 | S→R:D03→F |
| C14 | 资料外问题 | out_of_scope | out_of_scope | 1/1 | 3 | 通过（无引用） | 0 | S→S→F |
| V03 | 替换文档 | answered | answered | 1/1 | 3 | 通过（1 条） | 0 | S→R:D01→F |
| V05 | 替换文档、文档冲突 | conflict_need_confirmation | conflict_need_confirmation | 1/1 | 5 | 通过（2 条） | 0 | S→R:D05→R:D01→A→F |
