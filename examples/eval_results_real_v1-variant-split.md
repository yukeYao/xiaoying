# 端到端评测结果（真实模型，v1-variant-split）

- 模型：`gpt-4o-mini`
- 运行时间：2026-11-10 19:56，耗时 42s
- 每个用例运行次数：3
- trace 目录：`examples/real/v1-variant-split/`（文件名 `用例ID_run次数`）
- 路径记号：S=search_docs，R:Dxx=read_doc，A=ask_user，F=finish，T=无工具调用的纯文本回复，✗=该步返回错误

## 汇总

- 总通过率：4/6（67%）
- 全部运行都通过的用例：1/2
- 失败用例：V03

## 逐用例结果

| 用例 | 验收点 | 期望状态 | 实际状态（各次） | 通过 | 步数 | 引用校验 | finish 被拒 | 路径（各次） |
|---|---|---|---|---|---|---|---|---|
| V03 | 替换文档 | answered | conflict_need_confirmation / answered / conflict_need_confirmation | 1/3 | 4 / 4 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D01→R:D05→F<br>S→R:D01→R:D05→F<br>S→R:D01→R:D05→F |
| V05 | 替换文档、文档冲突 | conflict_need_confirmation | conflict_need_confirmation / conflict_need_confirmation / conflict_need_confirmation | 3/3 | 4 / 4 / 4 | 通过（2 条） / 通过（2 条） / 通过（2 条） | 0 / 0 / 0 | S→R:D05→R:D01→F<br>S→R:D05→R:D01→F<br>S→R:D05→R:D01→F |

## 未通过的运行

| 用例 | 第几次 | 问题 | trace |
|---|---|---|---|
| V03 | 1 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [V03_run1.md](real/v1-variant-split/V03_run1.md) |
| V03 | 3 | 状态 conflict_need_confirmation 不在期望 ['answered'] 中 | [V03_run3.md](real/v1-variant-split/V03_run3.md) |
