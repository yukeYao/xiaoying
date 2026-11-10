# 04 AI 使用说明

> 本文由 Claude Code 根据 [decision-log.md](decision-log.md) 和提交历史起草，项目作者负责核对和补充。初稿中标"待确认"的地方已由作者确认。

## 使用的工具

| 工具 | 用途 |
|---|---|
| Claude Code（Claude Opus 5.5，桌面版 Code 模式） | 编写全部代码、数据、测试、评测脚本和文档初稿；运行测试和评测；分析 trace；提交和推送 |
| 另一个 Claude 对话 | 审核阶段 1 的实现方案（审核意见见决策日志"阶段 1"），也用于审核后续各轮评测结果 |
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
| `docs/01`–`03`、`README.md`、`examples/README.md` | Claude Code 起草 | 作者已核对，未修改 |
| `docs/04`（本文） | Claude Code 起草 | 由作者核对 |
| `docs/05` | **作者本人** | Claude Code 曾按作者要求起草一版，后由作者本人编写的内容整体替换；Claude Code 只做了 Markdown 标题格式化 |

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
- **人工审核 trace**：由 Claude Code 按作者指定的范围和标准模拟审核 v4（gpt-4o-mini）每个用例的一次运行，共 16 条，逐条判断引用是否支持回答、回答中有没有引用以外的内容；作者核对了结论。结果见 [03-evaluation.md](03-evaluation.md#人工审核结果)。
- **可复现性**：在新克隆的目录中按 README 安装、运行测试和 Mock 评测（结果见收尾阶段的决策日志记录）。

## AI 出现的错误与处理

以下错误由 Claude Code 自己报告，或在后续检查中发现，都记录在决策日志里：

- 用 `git add -A` 顺带提交了一份不是本次生成的 Mock trace。之后在 CLAUDE.md 中增加规则：只 add 明确的文件。
- 写决策日志时用了未加引号的 shell heredoc，反引号中的内容被当作命令执行，日志两处文字被替换。原文已恢复，并增加规则：含特殊字符的文本用 Write / Edit 写入。
- 第一版替换数据的设计让 V03 也产生了冲突，修改 D05 时没有考虑到。
- v3 分析中"C10 在 2 次失败后以 failed 结束"的说法与 trace 不符，收尾时已更正。
- 盲测集 B05 最初标注了 D09，由作者改为资料外。

## 个人贡献与修改

> 本节由 Claude Code 按作者要求、根据 [decision-log.md](decision-log.md) 起草，作者已审查。只列决策日志中有记录的事；理由只写日志中作者说明过的，其余写"未说明"。

### 作者本人完成的内容

- 编写检索盲测集 `data/retrieval_eval_blind.jsonl` 的 5 个问题；确认 B01 只标 D05，把 B05 从"D09"改为资料外。
- 用另一个 Claude 对话审核阶段 1 方案和后续评测结果，并决定采纳哪些意见（阶段 1 的 7 条意见全部采纳）。
- 提出用例 C14（由 B05 转来）。
- 设计 finish 的结构化 conflict_check：claims / relations 字段和 5 条校验规则。
- 核对 [03-evaluation.md](03-evaluation.md#人工审核结果) 中由 Claude Code 模拟完成的 16 条人工审核结论。
- 编写复盘 [05-retrospective.md](05-retrospective.md)，替换 Claude Code 起草的版本。

### 对 Claude Code 方案的修改和否决

| 阶段 | Claude Code 的原方案或做法 | 作者的决定 | 理由 |
|---|---|---|---|
| 1 | 取舍 D：引用须来自读过的文档 | 更严格：引用的段落必须在本次运行中由 read_doc 返回过 | 未说明 |
| 1 | 取舍 F：逐字校验忽略空白 | 只忽略空白；另要求每条 quote 至少 8 字，并在文档中说明逐字校验只能证明引用存在、不能证明引用支持回答 | 未说明 |
| 2 | recall@3 无区分度，建议加 recall@1 / MRR 或增加干扰文档、更难的问题 | 不改现有问题和数据；加 recall@1 / MRR；另建盲测集（作者出题）；做同义词降权实验并如实记录 | 未说明 |
| 2 | 两种检索模式都加载同义词词表，使分词一致 | 两种模式改用各自独立的 jieba 分词器，基线不加载同义词 | 保证对比公平，并消除运行顺序依赖 |
| 2 | `syn_weight` 默认值待定 | 保持 1.0，暂停检索调参；结论是小语料下同义词扩展没有可测量收益，降权只是把问题从 R04 挪到 R03 | 作者给出的判断见左 |
| 3 | 模型调用出错不重试 | 超时、连接错误、429 重试 1 次，并在文档中说明这是 API 层重试，和"工具失败由模型决定下一步"是两回事 | 未说明 |
| 3 | read_doc 请求中有一个段落不存在就整体报错 | 返回存在的段落并登记，列出不存在的段落（之后又改为总是返回全文） | 未说明 |
| 3 | V05 期望可能与替换数据不符，待确认 | 改数据不改期望：替换版 D05 改为适用于全部费用报销 | 未说明 |
| 3 | C10 期望 failed | 允许 failed 或 answered（answered 须通过引用校验），评测记录实际路径 | 未说明 |
| 4 | v1 中 V03 失败，提出几类改法 | 先把 v1 归档为基线、加 `--tag`；再把替换数据拆成 variant_a / variant_b，并记录原设计让 V03 也产生冲突的问题 | 未说明 |
| 4 | read_doc 不传 paragraph_ids 时已返回全文，询问具体行为 | 无论是否传 paragraph_ids 都返回全文 | 未说明 |
| 4 | v2 后建议换更强模型对照 | 同意，并决定先诊断、不急于改 prompt；换模型只通过参数，不改 .env 默认值 | 未说明 |
| 4 | 冲突处理写进 prompt | 增加适用条件：只有多份文档对同一问题给出不同结论时才启动核对，单一文档能回答的读完即答；明确"版本较新不代表优先" | 未说明 |
| C0 | 指出 variant_b 的 D05 标题和正文仍写"差旅" | 修正数据，去掉"差旅"字样；第三段住宿费标准保留不改并在 README 注明 | 未说明 |
| C1 | （作者自己的设计）relations 由模型判断"结论是否不同"再决定写不写 | 改为相关文档两两都必须有一条 relation，校验检查缺失的文档对 | 未说明 |
| 5 | — | 默认模型定为 gpt-4o-mini | v4 结果最好 |

### 作者提出或决定的其他事项

> 决策日志中这些条目记为"我决定"或"我要求"，但没有逐条写明最初是谁提出的。

- 真实模型的最小调用测试写成独立脚本（`scripts/smoke_llm.py`），失败时先排查 key / 网络 / 模型，不继续写循环。
- 最终输出增加 `mode` / `model` / `trace_file`；citations 的 `title` / `version_date` 由程序补充，不由模型生成。
- 依赖固定确切版本。
- 第 3 步的具体规则：每次 observation 附剩余步数；完全相同的调用照常执行但注明"与第 N 步调用相同"；"连续失败 2 次后换方式"；问题指代不清才用 ask_user，文档不覆盖时用 out_of_scope；out_of_scope 时不给文档以外的建议。
- 在 v2-strong 诊断后提出计划 C：如果 prompt 改动后冲突类用例仍失败，再加结构化 conflict_check。
- 要求把"程序无法判断 claim 语义是否一致"作为已知限制写入文档。

### 作者设定的工作规则

- 真实模型结果不符合预期时，不修改 system prompt、数据、测试或期望，先停下汇报。
- 提交时只 add 明确的文件，不用 `git add -A`（在 Claude Code 误提交一份 Mock trace 后加入）。
- 含特殊字符的文本用 Write / Edit 写入（在 shell heredoc 事故后加入）。
- 在 CLAUDE.md 中加入用时记录规则；打 `3h-snapshot` 标签。
