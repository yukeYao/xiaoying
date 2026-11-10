# 01 需求：用户、目标、范围和成功标准

## 用户与目标

- **用户**：公司员工，遇到报销、请假、年假、设备申领等制度问题，或公司产品（虚构的剪影Pro）的功能问题。
- **目标**：给出**有原文依据**的可靠答案；资料冲突时说明冲突并请用户确认，资料没有覆盖时如实说明缺口，而不是编造或擅自挑选答案。

## 输入与输出

**输入**：问题，可选的对话历史（多轮追问）。

**资料**：`data/docs/` 下 10 份合成文档（D01–D10），每份有文档 ID、标题、版本日期、适用范围（可为空）和带编号的段落。另有两份替换版数据集 `data/variant_a/`、`data/variant_b/`，用于验证"文档内容变化后答案和动作随之改变"。

**输出**（`src/cli.py` 打印的 JSON）：

| 字段 | 说明 |
|---|---|
| `status` | `answered` / `conflict_need_confirmation` / `need_clarification` / `out_of_scope` / `failed` / `incomplete` |
| `answer` | 回答；需要确认或澄清时写明要问用户的问题 |
| `citations` | 引用：`doc_id`、`paragraph_id`、`quote`（逐字原文），以及程序按 doc_id 补充的 `title`、`version_date` |
| `gaps` | 资料缺口 |
| `conflict_check` | 读过的每份文档的结论（claims）和文档两两关系（relations），见 [02-solution.md](02-solution.md) |
| `reason` | `finish_called` / `max_steps_reached` / `llm_error` |
| `steps_used`、`mode`、`model`、`trace_file` | 步数、mock 或 real、模型名、trace 文件路径 |

## 范围

**在范围内**：
- 原生实现的 ReAct 循环（不使用 LangChain / LangGraph 等框架），OpenAI 兼容接口的 tool calling。
- 4 个工具：`search_docs`（BM25 + 同义词检索）、`read_doc`（读取全文）、`ask_user`（追问 / 确认）、`finish`（结构化结果 + 校验）。
- 步数上限、故障注入、离线 Mock、trace（JSONL + Markdown）、CLI（单问题、按用例、交互多轮）、批量评测脚本。

**不在范围内**：界面、线上部署、多 Agent、向量检索（embedding）、长文档切分、生产级运行时。

## 成功标准（可检查）

每条标准对应 `data/cases.jsonl` 中的用例，由 `scripts/run_eval.py` 自动判定。

| 验收点 | 用例 | 可检查的标准 |
|---|---|---|
| ① 明确答案 | C01、C06 | `status=answered`；引用覆盖期望文档（C01→D03；C06→D07，需依据 D07 写明的"2022 版同时废止"） |
| ② 文档冲突 | C03、C04（真冲突）；C05、C06（可查证的表面冲突） | 真冲突：`status=conflict_need_confirmation`，引用同时包含 D01 和 D02，不得只回答其中一个期限；表面冲突：`status=answered`，依据写明优先级 / 废止的原文 |
| ③ 资料外问题 | C07、C13、C14 | `status=out_of_scope`（C13 也可 answered），`gaps` 非空；不得编造规则 |
| ④ 改写后的相似问题 | C02（C01 的改写）、C04（C03 的改写） | 与原问题的状态和引用文档一致 |
| ⑤ 上下文追问 | C08（带对话历史）；C09（指代不清） | C08：结合历史回答并引用 D04；C09：`status=need_clarification` |
| ⑥ 工具失败 | C10（检索一直失败）、C11（第 1 次失败后恢复） | C10：`failed` 且 gaps 非空，或绕过检索后有依据地 `answered`；C11：重试后 `answered` |
| 步数上限 | C12（max_steps=2） | `status=incomplete`，`reason=max_steps_reached` |
| 替换文档 | V03（variant_a）、V05（variant_b） | V03：删除 D02、D01 改为 20 天后，由冲突变为 `answered` 20 天；V05：D05 删除优先级、范围改为全部费用后，由 `answered` 变为 `conflict_need_confirmation` |

所有 `answered` / `conflict_need_confirmation` 的引用必须通过逐字校验（见 02）。

### 参考实例的对应关系

题目参考实例：D01 写"报销期限 30 天"，D02 写"15 天"，未给适用范围与优先级。问"报销期限多久"时应列出冲突与引用、请求确认适用制度，不能擅自回答 15 天；只检索到 D01 且无冲突时可依据 D01 回答。

- 前半部分对应 **C03**（主数据集）。
- 后半部分对应 **V03**（variant_a 删除了 D02）。
