# 决策日志

记录规则见 CLAUDE.md「决策日志」一节。只记录对话中实际发生的事。

## 用时记录

这是一个 3 天的项目，题目建议投入 3 小时。核心链路（阶段 3、4）跑通时打 git tag `core-complete`，之后的工作都算延伸改进。各阶段实际用时由我本人填写。

| 阶段 | 内容 | 开始 | 结束 | 实际用时 | 备注 |
|---|---|---|---|---|---|
| 1 | 方案 |  |  |  |  |
| 2 | 数据集 + 检索工具 + 确定性测试 |  |  |  |  |
| 3 | Agent 循环 + 模型接入 + Mock + 步数上限 + 故障注入 + 引用校验 |  |  |  |  |
| 4 | CLI + Trace + 真实模型跑用例 |  |  |  |  |
| — | `core-complete` tag |  |  |  |  |
| 5 | 文档 01–03、README，04/05 模板 |  |  |  |  |
| 延伸 |  |  |  |  |  |

---

## 2026-11-10 阶段 1：实现方案审核（补录，补录时间 2026-11-10 17:51）

**原方案**：Claude Code 提出（模块划分、工具 schema、system prompt 草稿、数据集 D01–D10 与替换版、用例 C01–C12 / V03 / V05，以及待决定的取舍 A–H）。

**审核**：我用另一个 Claude 对话（外部 Claude 对话审核）审核了方案，审核意见包括：
- 增加检索评测和留出集
- 新增用例 C13
- 引用最短长度
- max_steps 改为 10
- temperature=0 加多次运行
- 无工具调用时的处理
- --data-dir 参数

我采纳了以上全部建议。

**最终决定及改动内容**：

取舍决定：
- A：不加 embedding，在 docs 中作为下一步改进。
- B：采用推荐方案（非交互模式下 ask_user 返回提示，由模型调用 finish）。
- C：采用脚本化 Mock，保留"故意给错误引用"的那条序列。
- D：采用，并更严格：引用的段落必须在本次运行中由 read_doc 返回过。
- E：采用（Markdown + 手工解析的元数据头）。
- F：只忽略空白字符差异；另外要求每条 quote 至少 8 个字，并在文档中说明逐字校验只能证明引用存在，不能证明引用支持回答。
- G：max_steps 默认改为 10，CLI 可通过参数修改。
- H：按计划在阶段 3 先做最小调用测试。

新增内容：
1. 检索评测：新建 data/retrieval_eval.jsonl，15–20 条问题，每条标注期望命中的 doc_id；其中留出 5 条作为留出集，设计同义词表时不得参考。scripts 中提供检索评测脚本，对比"只用 BM25"和"BM25 + 同义词扩展"的 recall@3，分别报告全部问题和留出集结果。
2. 新增用例 C13：年假没休完能折现吗？D03 会被检索到但没有折现规则，期望 out_of_scope，或部分回答并在 gaps 中说明缺口，不得编造规则。
3. 模型没有调用工具、直接输出文本时，作为 observation 提醒它必须调用 finish，并计入步数。
4. CLI 支持 --data-dir。
5. 真实模型 temperature=0，run_eval.py 支持 --repeat N，报告每个用例的通过次数。

**理由**：未说明。

**验证方式**：无（方案阶段）。

---

## 2026-11-10 阶段 2：检索基线的分词一致性（实现中发现并修复）

**原方案**：Claude Code 实现。`load_synonyms` 会把同义词注册进 jieba 全局词典；最初只在"BM25 + 同义词"模式下加载，导致"只用 BM25"基线的分词结果取决于两种模式的创建顺序。

**最终决定及改动内容**：Claude Code 修改 `src/tools.py`：两种模式都加载词表（分词一致），`use_synonyms` 只控制是否扩展查询。副作用：基线也享受到"同义词作为整词切分"的好处，对比只反映查询扩展本身的作用。

**理由**：Claude Code 说明的理由是保证对比公平、结果可复现；我尚未就此表态。

**验证方式**：`python scripts/eval_retrieval.py` 两种模式在同一进程内运行，结果不依赖顺序。

---

## 2026-11-10 阶段 2 审核：检索评测与基线分词

**原方案**：Claude Code 在阶段 2 报告中指出 recall@3 两种模式都是 1.000、没有区分度，提出可选改进（增加 recall@1 / MRR，或增加干扰文档、更难的问题）；并报告 R04 加同义词后 D05 排到第一的排序退步。

**最终决定及改动内容**（我决定）：
1. 不改现有问题和数据。
   - `scripts/eval_retrieval.py` 增加 recall@1 和 MRR，三个指标都报告。
   - 新增盲测集 `data/retrieval_eval_blind.jsonl`：5 条问题由我本人编写；Claude Code 只标注期望 doc_id（含标注说明），不据此修改同义词表，结果单独报告。
   - 针对 R04 的排序退步，尝试同义扩展词降权（原词 1.0，同义词 0.5，可配置参数 `syn_weight` / `--syn-weight`），报告改进前后对比，无论是否有效都如实记录。
   - 检查冲突类问题在 top_k=5 时 D01、D02 是否都被返回，单独列出。
2. 基线分词：两种模式改用各自独立的 `jieba.Tokenizer()` 实例，基线不加载同义词词典（替代上一条记录中"两种模式都加载词表"的做法）。
3. 运行命令补到 CLAUDE.md"常用命令"，注明 Windows 和 macOS/Linux 写法。

**理由**：
- 第 2 条：保证对比公平，并消除运行顺序依赖。
- 其他各条：未说明。

**验证方式与结果**（`examples/retrieval_eval_results.md`）：
- 开发集 + 留出集（18 条），三种模式（bm25 / syn_w1.0 / syn_w0.5）平均指标完全相同：recall@1 0.861、recall@3 1.000、MRR 0.972。
- 降权实验：syn_w0.5 修复了 R04（D01 回到第一，RR 0.50 → 1.00），但 R03 同时退步（syn_w1.0 时 D02 第一，降权后 D05 第一，RR 1.00 → 0.50），净效果为零。未改变默认值（`syn_weight` 默认仍为 1.0），待我决定。
- 冲突类问题（R03、R04）在三种模式下 top_k=5 都同时返回 D01 和 D02。
- 盲测集（5 条）三种模式指标也相同：recall@1 0.567、recall@3 0.800、MRR 0.800。B05（报表导出超时）三种模式 top10 都没有 D09，返回的是 D03/D02/D04 等无关文档。
- 改动后 `pytest` 28 个测试全部通过。

---

## 2026-11-10 阶段 2 收尾

**原方案**：Claude Code 在阶段 2 修订报告中给出降权实验结果，保留 `syn_weight` 默认 1.0 待决定；B01、B05 的标注请我确认；指出 `task.txt` 未提交、git 的 LF/CRLF 换行提示。

**最终决定及改动内容**（我决定）：
1. `syn_weight` 默认保持 1.0。检索调参暂停，阶段 3 完成后再回来。
   当前结论：小语料（10 份文档）下静态同义词扩展没有可测量收益，降权只是把排序问题从 R04 挪到了 R03；根本原因可能是语料太小，后续计划扩大语料（加入干扰文档）后重新评估。
2. B01 只标 D05，同意。
3. B05 改为资料外：期望 doc_id 为空，不计入 recall/MRR，报告中单独说明。阶段 3 把它加为用例 C14，期望 out_of_scope。
   改动：`data/retrieval_eval_blind.jsonl` 中 B05 的 `expected_doc_ids` 改为 `[]`；`scripts/eval_retrieval.py` 跳过期望为空的问题，另列"资料外问题"表（各模式 top3 文档和最高分）。
4. `task.txt` 加入 `.gitignore`，不提交。
5. 新增 `.gitattributes`（`* text=auto eol=lf`），重新规范化已有文件。
6. 在本文件开头增加"用时记录"小节，由我本人填写各阶段实际用时；核心链路（阶段 3、4）跑通时打 git tag `core-complete`，之后算延伸改进。

**理由**：
- 第 1 条：结论见上（我给出的判断）。
- 其他各条：未说明。

**验证方式**：
- `git add --renormalize .` 后索引中所有文件均为 LF（规范化前索引已是 LF，无内容变化）；工作区中 3 个 CRLF 文件重新检出为 LF，`git ls-files --eol` 显示全部 `w/lf`。
- `git check-ignore -v task.txt` 确认被忽略。
- 盲测集去掉 B05 后剩 4 条计入指标，三种模式仍相同：recall@1 0.708、recall@3 1.000、MRR 1.000（此前含 B05 时为 0.567 / 0.800 / 0.800）。B05 在三种模式下 top3 均为 D03,D02,D04，最高分约 1.9–2.0。
- `pytest` 28 个测试全部通过。

---

## 2026-11-10 阶段 3 第一步：真实模型最小调用测试

**原方案**：阶段 1 取舍 H（Claude Code 提出，我采纳）：阶段 3 先做最小调用测试。我要求写独立脚本 `scripts/smoke_llm.py`，失败时先排查 key / 网络 / 模型，不继续写循环。

**最终决定及改动内容**：新增 `scripts/smoke_llm.py`（从 .env 读配置，提供假工具 search_docs，检查是否返回 tool call，不打印 key 内容）。我确认 smoke 测试结果，同意进入第二步。

**理由**：未说明。

**验证方式**：运行 3 次，模型 `gpt-4o-mini`（返回 `gpt-4o-mini-2024-07-18`），均返回 `search_docs` tool call，`finish_reason = tool_calls`，耗时 3.73s / 2.57s / 4.13s，temperature=0 下三次参数相同，无错误。

---

## 2026-11-10 阶段 3 第二步：Agent 循环、Mock、引用校验、故障注入、trace

**原方案**：阶段 1 方案 + 阶段 1 审核修改（取舍 B/C/D/F/G、无工具调用处理、--data-dir 等）+ 我在阶段 3 开始时给出的实现清单。按清单实现，未改变已确认的规则。

**最终决定及改动内容**（Claude Code 实现；以下几点是实现中由 Claude Code 自行决定的细节，尚待我审核）：
1. CLI 原计划在阶段 4，为了提供 `--fail-tool` / `--fail-times` / `--data-dir`，阶段 3 先实现了最小 CLI（`src/cli.py`：单问题或 `--case`，`--mock`、`--max-steps`、`--interactive`、`--trace-dir`）。多轮交互模式和批量评测仍留到阶段 4。
2. 模型一次回复中包含多个工具调用时，逐个执行，每个算 1 步。
3. 模型调用本身抛异常（网络、key 等）时，返回 `status=failed, reason=llm_error`，不重试。
4. 故障注入只允许作用于 `search_docs`、`read_doc`。
5. read_doc 请求中只要有一个段落不存在就整体报错，此次读取不登记任何段落。
6. 用例期望 `expected_status` 用列表表示可接受的状态（C13 为 `out_of_scope` 或 `answered`，并要求 gaps 非空）。
7. V05 的期望按阶段 1 方案写为 `conflict_need_confirmation`，但替换版 D05 仍写有适用范围（"本规定适用于员工因公出差产生的…差旅费用的报销"），模型依据适用范围回答 10 天也可能合理。已在 cases.jsonl 的 notes 中标注，期望待我确认。
8. C10（search_docs 一直失败）期望 `failed`；模型若直接 read_doc 猜文档并有依据地回答，也属合理恢复，已在 notes 中说明。

**理由**：未说明（上述细节为 Claude Code 实现时的选择，我尚未表态）。

**验证方式**：`pytest` 共 92 个测试全部通过（新增 tests/test_finish.py 引用校验 / ask_user / 故障注入 / 参数错误，tests/test_agent.py Mock 用例流程 / 步数上限 / 无工具调用 / 错误引用纠正 / trace / CLI）。16 个用例的 Mock 脚本全部得到期望状态。尚未用真实模型跑用例（阶段 4）。

---

## 2026-11-10 阶段 3 第二步审核

**原方案**：Claude Code 在阶段 3 第二步报告中列出待审核事项：V05 期望（替换版 D05 仍写有差旅适用范围）、C10 的另一条可接受路径、CLI 提前实现，以及多个工具调用计步、模型调用出错不重试、read_doc 含不存在段落时整体报错这几个实现细节。

**最终决定及改动内容**（我决定）：
1. V05：修改替换版数据，而不是改期望。`data/variant/docs/D05.md` 的适用范围改为"适用于公司全部费用报销"（元数据 scope 改为 `公司全部费用报销`，第一段改为"本规定适用于公司全部费用报销。"），保持已删除的优先级条款，使它和 D01 构成同一范围的直接冲突。V05 期望保持 `conflict_need_confirmation`。同步更新 `data/variant/README.md`。
2. C10：期望状态允许 `failed` 或 `answered`（answered 必须通过引用校验）。评测时记录模型实际走了哪条路。
3. CLI 提前到阶段 3 实现：同意。
4. 细节：
   - 一次回复中多个工具调用各算 1 步：同意。
   - 模型调用出错：对超时、连接错误、429 这类临时错误，短暂等待后重试 1 次，仍失败再返回 `failed / llm_error`。在文档中说明这是 API 层的重试，和"工具失败由模型决定下一步"是两回事。
   - read_doc：改为返回存在的段落并登记，同时在返回结果中列出不存在的段落编号。

**理由**：未说明。

**Claude Code 实现时的补充（尚待我审核）**：
- C10 去掉了 `expect_gaps`：允许 answered 后，answered 路径的 gaps 可能为空。failed 时是否说明缺口，留到阶段 4 评测时检查。
- 重试实现：`src/llm.py` 关闭 openai SDK 自带的自动重试（`max_retries=0`），只由自己的逻辑重试；等待 2 秒（`retry_wait` 可配置）；401 等其他错误不重试。说明写在 `src/llm.py` 和 `src/agent.py` 的模块注释中，阶段 5 写入 docs/02-solution.md。
- read_doc：请求的段落全部不存在时仍返回 `not_found` 错误、不登记；部分不存在时返回 `missing_paragraphs` 和 `note`。
- 新增 Mock 序列 `C10_READ_DIRECT`（检索失败后直接读取 D03 并回答），用于测试 C10 的 answered 路径。
- 原测试 `test_failed_read_does_not_register`（断言部分段落不存在时整体不登记）与新决定冲突，按新决定替换为 `test_partial_read_registers_existing_paragraphs`。这是需求变更导致的测试修改，不是迁就失败结果。
- 测试中构造 openai 异常需要底层 HTTP 库：openai 3.49 使用 `httpx2`（不再依赖 `httpx`），测试优先导入 `httpx2`，否则回退到 `httpx`。

**验证方式**：`pytest` 共 105 个测试全部通过（新增 tests/test_llm.py：3 类临时错误重试 1 次后成功、连续 2 次失败抛出、401 不重试、SDK 自动重试已关闭、持续失败在 agent 中变为 llm_error；read_doc 部分缺失；替换版 D05 适用范围；C10 answered 路径）。

---

## 2026-11-10 阶段 3 审核确认与阶段 4

**原方案**：Claude Code 在阶段 3 审核修改报告中提出三点实现补充（C10 去掉 expect_gaps、替换旧测试、使用 httpx2），并报告 `git add -A` 误提交了一份 Mock trace。

**最终决定及改动内容**（我决定）：
1. 同意 C10 去掉 expect_gaps、替换旧测试、使用 httpx2。
2. 最终输出增加 `mode`（mock / real）、`model`、`trace_file` 字段；citations 每条的 `title`、`version_date` 由程序根据 doc_id 补充，不由模型生成。
3. requirements.txt 固定所有依赖的确切版本（以当前 venv 实际安装版本为准）。
4. CLAUDE.md 增加规则：提交时只 add 明确要提交的文件，不使用 `git add -A`。
5. 阶段 4：`scripts/run_eval.py`（--mock / --real、--repeat N、--cases；trace 分别存 examples/real/ 与 examples/mock/，文件名含用例 ID 和第几次运行；结果写入 eval_results_real.md / eval_results_mock.md，列出期望状态、每次实际状态、通过次数、步数、引用校验是否通过、finish 被拒次数；C10 为 failed 时 gaps 必须非空；末尾汇总总通过率和失败用例）；用脚本重新生成全部 Mock trace；真实模型 --repeat 3；CLI 增加交互多轮模式。
6. 真实模型结果不符合预期时，不修改 system prompt、数据、测试或期望，先停下汇报。

**理由**：未说明。

**Claude Code 实现时的补充（尚待我审核）**：
- C10 的条件检查写成用例数据字段 `gaps_required_if_status: ["failed"]`，run_eval 按字段检查，而不是在脚本里写死 C10。
- 模型在 citation 中自带的 title / version_date 会被丢弃，以文档库为准（有测试）。
- `trace_file` 指向 Markdown trace（同名 .jsonl 在同一目录）。
- run_eval 全量运行前会清空对应 trace 目录，避免旧文件残留；`--cases` 部分运行不清空，结果写入 `*_subset.md`。
- 报告中增加"路径"列（如 `S→R:D01→R:D02→A→F`），用于记录 C10 等用例实际走的路径。
- `--chat` 不能与 `--mock` 同时使用（脚本化 Mock 无法应对任意输入）；交互模式下对话历史只保留每轮的问题和 answer 文本。
- requirements.txt 包含 `colorama`（pytest 在 Windows 上的依赖）等全部间接依赖。

**验证方式**：`pytest` 115 个测试全部通过；`run_eval.py --mock` 16/16 通过，旧的 `examples/mock/C03.*` 已被新的 `C03_run1.*` 取代。真实模型结果见下一条记录。

---

## 2026-11-10 阶段 4：真实模型首次全量运行（未达预期，待讨论）

**运行**：`scripts/run_eval.py --real --repeat 3`，模型 gpt-4o-mini，temperature=0。结果见 `examples/eval_results_real.md`，trace 在 `examples/real/`。按 CLAUDE.md 规则，未修改 system prompt、数据、测试或期望。

**结果**：总通过率 34/48（71%），全部通过的用例 9/16。失败用例（失败次数）：C05（3/3）、C06（3/3）、C10（2/3）、C14（2/3）、V03（2/3）、C03（1/3）、C04（1/3）。

**Claude Code 从 trace 看到的走偏位置与推测原因（尚待我判断）**：
- C05、C06：都只用 `paragraph_ids` 读了命中段落，没有读全文，因此没看到 D05 P3 的优先级条款、D07 P1 的废止说明，把可查证的表面冲突当成真冲突。system prompt 第 4 条要求"必须读取这些文档全文"，模型没有遵守。
- V03：替换版 D05 在上一轮审核中改为"适用于公司全部费用报销"，此后 D05（10 天）与 D01（20 天）在替换版中也构成冲突；V03 的期望（answered，20 天）是在该数据修改之前定的。模型 3 次都读到了 D05，其中 2 次报冲突。可能是期望与数据不一致，而不是模型错误。
- C10：search_docs 一直失败时，模型反复换关键词重试，没有改用 read_doc 或及时 finish，2/3 次撞到 max_steps 返回 incomplete（步数上限按设计生效）。错误信息没有列出可用文档 ID，模型也无从直接 read_doc。
- C14：2/3 次把资料外问题当成"指代不清"，返回 need_clarification（问"哪个系统"）。第 3 次虽判为 out_of_scope（计为通过），但 answer 把 D09（视频导出、存储空间）的建议套用到报表导出超时上，引用逐字正确但不支持回答——这是逐字校验无法发现的问题，评测脚本也没有检查出来。
- C03、C04 各 1 次：读到 D05 后把问题理解为"一般报销还是差旅报销"，返回 need_clarification；通过的运行中也常把 D05 作为第三种说法列出，同样没有读全文核实 D05 的适用范围。

---

## 2026-11-10 阶段 4 改进第 0、1 步：基线归档与替换版数据拆分

**原方案**：Claude Code 在阶段 4 汇报中指出 V03 失败可能是期望与数据不一致，并提出几类改法，请我决定先处理哪一类。

**最终决定及改动内容**（我决定）：
0. 当前真实模型结果重命名为基线：`examples/eval_results_real_v1.md`，trace 目录改为 `examples/real/v1/`。`run_eval.py` 增加 `--tag` 参数区分每一轮结果，之后每轮结果不覆盖之前的文件。
1. V03 / V05 拆成两份替换版数据：
   - `data/variant_a`：删除 D02，D01 改为 20 天，D05 保持主数据集原样。V03 使用它，期望 answered 20 天、引用 D01。
   - `data/variant_b`：在 variant_a 基础上，D05 改为适用于全部费用报销、删除优先级条款。V05 使用它，期望 conflict_need_confirmation。
   - 更新两份 README 说明各自用途。只重跑 V03、V05（--repeat 3）。
   - **记录**：原替换版设计让 V03 也产生了冲突，这是上一轮（阶段 3 第二步审核）修改 D05 时没有考虑到的。
2. （后续步骤）read_doc 默认返回全文（v2）；prompt 修改与剩余步数（v3）。每一步完成后停下汇报。finish 校验中"冲突时必须读过全文"暂不加，看 v2 效果再决定。

**理由**：未说明。

**Claude Code 实现说明**：
- 基线移动后，同步修正了 `eval_results_real_v1.md` 中的 trace 链接和 v1 trace JSONL 中的 `trace_file` 字段（`examples/real/` → `examples/real/v1/`），trace 内容本身未改。
- 原 `data/variant` 用 `git mv` 改名为 `data/variant_b`（其内容正是 variant_b 的设计）；`data/variant_a` 由它复制后把 D05 换回主数据集版本。
- 本步只重跑 V03、V05，tag 为 `v1-variant-split`（结果 `examples/eval_results_real_v1-variant-split.md`，trace `examples/real/v1-variant-split/`）。Mock trace 因 V03/V05 数据目录变化重新生成。
- 测试中替换版检查拆为 variant_a / variant_b 两个测试，并断言除改动文档外其余文档与基准完全相同。

**验证方式与结果**：
- `pytest` 116 个测试全部通过；`run_eval.py --mock` 16/16。
- 真实模型 `--cases V03 V05 --repeat 3 --tag v1-variant-split`（`examples/eval_results_real_v1-variant-split.md`）：
  - V05（variant_b）：3/3 通过（v1 也是 3/3）。
  - V03（variant_a）：1/3 通过（v1 也是 1/3），仍未达预期。
- Claude Code 从 trace 看到的 V03 情况（尚待我判断）：3 次路径都是 `S→R:D01(P2)→R:D05(P2)→F`，只读了两份文档的第二段。3 次 answer 内容基本一致——"一般费用 20 天内（D01）；差旅费用出差结束后 10 天内（D05）"，内容本身与文档相符；差别只在状态：1 次标 answered，2 次标 conflict_need_confirmation 并请用户确认。模型没有读 D05 第一段（适用范围）和第三段（优先于通用规定），因此没有依据判断二者是"一般 vs 差旅"的分工而非冲突。V03 的失败已不再来自数据设计，和 C05/C06 一样属于"只读片段、不读全文核实"。
