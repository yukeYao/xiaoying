# 04 AI 使用说明

> 本文由 Claude Code 根据 [decision-log.md](decision-log.md) 和提交历史起草，项目作者负责核对和补充。标"**待确认**"的地方需要作者确认或修改。"个人修改与体会"相关内容不由 AI 代写。

## 使用的工具

| 工具 | 用途 |
|---|---|
| Claude Code（Claude Opus 5.5，桌面版 Code 模式） | 编写全部代码、数据、测试、评测脚本和文档初稿；运行测试和评测；分析 trace；提交和推送 |
| 另一个 Claude 对话 | 审核阶段 1 的实现方案（审核意见见决策日志"阶段 1"）。是否也用于审核后续各轮评测结果：**待确认** |
| 评测中被调用的模型（不是开发辅助） | gpt-4o-mini（默认）、gpt-4.1（对照） |

## 工作方式

- 项目约定写在 [CLAUDE.md](../CLAUDE.md)，包括：分阶段工作、每个阶段结束后停下等待确认、不修改测试来迁就失败结果、真实模型结果不符合预期时先报告、提交时只添加明确的文件。
- 每个阶段由 Claude Code 提出方案或给出结果，作者确认、否决或修改后再继续。每次决定都记在 [decision-log.md](decision-log.md)，注明谁提出、最终决定和理由；作者没说明理由的写"未说明"。

## AI 生成的内容

| 内容 | 生成方 | 说明 |
|---|---|---|
| `src/`、`scripts/`、`tests/` 全部代码 | Claude Code | 按作者确认的方案和每轮的修改意见实现 |
| `data/docs/` D01–D10、`data/variant_a/`、`data/variant_b/` | Claude Code | 文档结构和关键冲突（D01/D02、D05 优先级、D06/D07 废止）按作者给定的需求设计；variant 的拆分与 D05 修改按作者决定 |
| `data/synonyms.json`、`data/retrieval_eval.jsonl`（开发集 13 条 + 留出集 5 条） | Claude Code | 先写开发集，再据此写同义词表，词表定稿后才写留出集 |
| `data/retrieval_eval_blind.jsonl` 的 5 个问题 | **作者本人** | Claude Code 只标注期望 doc_id；B01、B05 的标注由作者确认或修改 |
| `data/cases.jsonl`（C01–C14、V03、V05） | Claude Code 起草 | C13 来自外部审核意见（作者采纳），C14 由作者提出；C10、V03、V05 的期望由作者修改 |
| system prompt | Claude Code 起草 | 冲突核对步骤、资料外 / 追问规则、连续失败规则等要点由作者提出 |
| Mock 序列 | Claude Code | "故意错误引用"和"错误标 scope_split"两条序列按作者要求加入 |
| `docs/01`–`03`、`README.md`、`examples/README.md` | Claude Code 起草 | **待确认**：作者是否修改 |
| `docs/04`（本文） | Claude Code 起草 | 由作者核对 |
| `docs/05` | 只有模板和事实列表 | 正文由作者填写 |

## 作者做出的决策（摘自决策日志）

- **方案阶段**：采纳外部审核意见（检索评测与留出集、用例 C13、引用最短 8 字、max_steps=10、temperature=0 与多次运行、无工具调用的处理、--data-dir）；决定取舍 A–H（不加 embedding、ask_user 非交互时提示模型调用 finish、脚本化 Mock、引用段落必须由本次 read_doc 返回过、逐字校验只忽略空白等）。
- **检索**：不改现有问题和数据；增加 recall@1 / MRR、盲测集、降权实验；基线改用独立分词器；同义词无收益的结论；暂停检索调参。
- **数据与用例**：B05 改为资料外并新增 C14；C10 允许 failed 或 answered；V05 改数据不改期望；拆分 variant_a / variant_b；修正 variant_b 的 D05。
- **实现细节**：API 层对临时错误重试 1 次；read_doc 部分段落不存在时返回存在的段落，后来改为总是返回全文；输出增加 mode / model / trace_file，title / version_date 由程序补充；依赖固定版本。
- **评测迭代**：基线归档 v1、用 --tag 区分各轮；先换 gpt-4.1 诊断再改 prompt；冲突核对写成明确步骤；最后改为结构化 conflict_check，并把 relations 要求改为"相关文档两两必须有关系"；默认模型选 gpt-4o-mini。
- **流程与记录**：用时记录、3h-snapshot 标签、提交只 add 明确文件、含特殊字符的文本用 Write / Edit 写入。

## 验证方式

- **自动测试**：139 个确定性测试；Mock 跑全部 16 个用例（只验证流程）。
- **真实模型**：每轮 16 个用例 × 3 次，gpt-4o-mini 和 gpt-4.1 对照，结果和 trace 全部保存在 `examples/`。
- **结果分析**：每轮的失败原因由 Claude Code 从 trace 中查找，作者据此决定下一步改动（见决策日志各轮记录）。
- **人工审核 trace**：**待确认**（作者抽查了哪些 trace、结论如何，填在 [03-evaluation.md](03-evaluation.md#人工审核结果)）。
- **可复现性**：在新克隆的目录中按 README 安装、运行测试和 Mock 评测（结果见收尾阶段的决策日志记录）。

## AI 出现的错误与处理

以下错误由 Claude Code 自己报告，或在后续检查中发现，都记录在决策日志里：

- 用 `git add -A` 顺带提交了一份不是本次生成的 Mock trace。之后在 CLAUDE.md 中增加规则：只 add 明确的文件。
- 写决策日志时用了未加引号的 shell heredoc，反引号中的内容被当作命令执行，日志两处文字被替换。原文已恢复，并增加规则：含特殊字符的文本用 Write / Edit 写入。
- 第一版替换数据的设计让 V03 也产生了冲突，修改 D05 时没有考虑到。
- v3 分析中"C10 在 2 次失败后以 failed 结束"的说法与 trace 不符，收尾时已更正。
- 盲测集 B05 最初标注了 D09，由作者改为资料外。

## 个人贡献与修改

（由项目作者填写。）
