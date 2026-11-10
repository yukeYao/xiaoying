# 决策日志

记录规则见 CLAUDE.md「决策日志」一节。只记录对话中实际发生的事。

## 用时记录

这是一个 3 天的项目，题目建议投入 3 小时。核心链路（阶段 3、4）跑通时打 git tag `core-complete`，之后的工作都算延伸改进。用时记录由 Claude Code 维护（阶段开始、结束时运行 `date` 记录），我负责核对。备注列标明时间来源。

| 阶段 | 内容 | 开始 | 结束 | 实际用时 | 备注 |
|---|---|---|---|---|---|
| 1 | 方案 | 2026-11-10 17:34 | 17:51 | 约 17 分钟 | 根据提交时间推算：开始时间由我提供；结束取阶段 1 审核补录时间 17:51 |
| 2 | 数据集 + 检索工具 + 确定性测试 | 17:51 | 18:39 | 约 48 分钟 | 根据提交时间推算：开始取阶段 1 补录时间；结束取提交 ce4500f |
| 3 | Agent 循环 + 模型接入 + Mock + 步数上限 + 故障注入 + 引用校验 | 18:39 | 19:39 | 约 60 分钟 | 根据提交时间推算：开始取 ce4500f；结束取提交 1e03d6a；含推送 GitHub 和 smoke 测试（7760cd2 19:22） |
| 4 | CLI + Trace + 真实模型跑用例 | 19:39 | 进行中 | — | 根据提交时间推算：开始取 1e03d6a；已提交 6b1145f（19:51）、f09fed6（19:56）；20:00 起实时记录。第 2 步（v2）结束 20:08（实时记录，`date`；提交 0e92d41）。诊断 A（v2-strong）20:19–20:28（实时记录）。第 3 步（v3 / v3-strong）20:31–20:42（实时记录）。计划 C0 20:48–20:50（实时记录）。计划 C1（v4 / v4-strong）20:55–21:12（实时记录） |
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

---

## 2026-11-10 阶段 4 改进第 2 步：read_doc 总是返回全文（v2）

**原方案**：我决定"read_doc 默认返回全文，paragraph_ids 保留为可选参数，更新工具 description"。Claude Code 指出原实现已经是"不传 paragraph_ids 就返回全文"，而 v1 中模型每次都主动传了 paragraph_ids，因此询问具体行为。

**最终决定及改动内容**（我选择）：总是返回全文——无论是否传 paragraph_ids 都返回整篇文档；传入的段落在结果中标注为 `requested_paragraphs`，不存在的列为 `missing_paragraphs`（附 note，不再报错）；引用登记覆盖全文所有段落。工具 description 改为"读取文档全文……总是返回整篇文档，便于核对适用范围、优先级、废止/替代说明"。finish 校验中"冲突时必须读过全文"暂不加。

**理由**：未说明。

**测试修改**（需求变更导致，不是迁就失败结果）：以下 6 个测试断言的是旧行为"只返回请求的段落 / 不存在段落时报错"，按新决定改写：`test_reading_other_paragraph_does_not_count` → `test_read_doc_registers_whole_document` + `test_reading_other_document_does_not_count`；`test_partial_read_registers_existing_paragraphs`、`test_read_with_no_existing_paragraph_registers_nothing` → `test_read_with_missing_paragraph_ids_still_registers_full_text` + `test_failed_read_registers_nothing`；`test_read_doc_selected_paragraphs` → `test_read_doc_always_returns_full_text`；`test_read_doc_unknown_paragraph`、`test_read_doc_partially_missing_paragraphs` → `test_read_doc_unknown_paragraph_returns_full_text_with_note` + `test_read_doc_without_paragraph_ids_has_no_request_fields`。

**验证方式与结果**：`pytest` 117 个通过；Mock 16/16。真实模型 `--repeat 3 --tag v2`（`examples/eval_results_real_v2.md`）：总通过率 33/48（v1 为 34/48，其中 V03/V05 按 v1-variant-split 计）。

| 用例 | v1 | v2 |
|---|---|---|
| V03 | 1/3 | 3/3 |
| C14 | 1/3 | 2/3 |
| C03 | 2/3 | 1/3 |
| C04 | 2/3 | 0/3 |
| C13 | 3/3 | 2/3 |
| C05、C06 | 0/3 | 0/3 |
| C10 | 1/3 | 1/3 |
| 其余 9 个 | 全部 3/3 | 全部 3/3 |

**Claude Code 从 trace 看到的情况（尚待我判断）**：
- V03 变为通过：3 次都标 answered，其中 2 次引用了 D05 P3（优先于通用规定）——全文让模型看到了适用关系。
- C05、C06 仍 0/3：全文已返回（trace 显示 D05 的 P1–P4、D07 的 P1–P4 都在 observation 中），但模型仍按自己请求的段落作答，忽略了 D05 P3 的优先级条款和 D07 P1 的废止说明，报 conflict。说明"能看到"不等于"会去核对"。
- C03、C04 变差，出现新的失败形态：4 次标 answered，把 D01 30 天、D02 15 天、D05 10 天并列列出而不指出 D01 与 D02 冲突——这比 v1 的 need_clarification 更严重（相互矛盾的规定被当成答案）。另 1 次（C04 run3）仍问"一般还是差旅"。是否由全文变长导致无法确定，也可能是随机波动。
- C13 run2：answer 内容正确（未提到折现、逾期作废），但状态标 need_clarification 而不是 out_of_scope。
- C14：run1 仍为 need_clarification；run2 虽通过，但 answer 中仍有文档以外的建议（"检查设备存储空间、联系技术支持"）且无引用。
- C10：不变，仍反复重试检索直到步数上限（第 3 步的 prompt 修改针对此问题）。

---

## 2026-11-10 阶段 4 诊断 A：换更强模型（v2-strong）

**原方案**：Claude Code 在 v2 汇报中提出 gpt-4o-mini 可能是能力上限，建议换更强模型对照。

**最终决定及改动内容**（我决定）：先不进第 3 步。代码不变，用比 gpt-4o-mini 更强的模型跑全部用例（先确认账户可用模型，选一个并告知），--repeat 3，tag 为 v2-strong；模型名通过参数或环境变量切换，不改 .env 默认值。之后第 3 步在原计划基础上增加"冲突处理明确步骤"（范围分工 / 已被替代 / 真冲突，只有真冲突才用 conflict_need_confirmation，绝不把互相矛盾的规定并列作为答案），用 gpt-4o-mini 跑 v3；若 v3 中 C03–C06 仍失败，再讨论 finish 增加结构化 conflict_check 字段。CLAUDE.md 中我加的用时规则一并提交（提交 f31c92f）。

**理由**：未说明。

**Claude Code 实现说明**：
- 账户可用模型（models.list）包括 gpt-4.1、gpt-4o、gpt-5 / 5.x 系列、o3 等。选择 **gpt-4.1**：支持 temperature=0 与 tool calling，可保持与 gpt-4o-mini 相同的调用参数，只改变模型本身；gpt-5.x / o 系列推理模型多数不接受非默认 temperature，会同时改变采样设置。smoke 测试通过（返回 gpt-4.1-2025-04-14）。
- `scripts/run_eval.py` 和 `src/cli.py` 增加 `--model` 参数；`OpenAIChat(model=...)` 优先于 .env；也可用环境变量 `AGENT_MODEL=...`（load_dotenv 不覆盖已存在的环境变量）。.env 未修改。

**验证方式与结果**：`pytest` 117 个通过。`--real --model gpt-4.1 --repeat 3 --tag v2-strong`（`examples/eval_results_real_v2-strong.md`）：总通过率 **25/48**（v2 gpt-4o-mini 为 33/48）。

| 用例 | v2（4o-mini） | v2-strong（4.1） |
|---|---|---|
| C05 | 0/3 | 2/3 |
| C06 | 0/3 | 2/3 |
| C03 | 1/3 | 1/3 |
| C04 | 0/3 | 0/3 |
| C01 | 3/3 | 2/3 |
| C02 | 3/3 | 0/3 |
| C07 | 3/3 | 1/3 |
| C11 | 3/3 | 1/3 |
| C13 | 2/3 | 0/3 |
| C14 | 2/3 | 0/3 |
| C10 | 1/3 | 1/3 |
| C08、C09、C12、V03、V05 | 3/3 | 3/3 |

**Claude Code 从 trace 看到的情况（尚待我判断）**：
- C05、C06：gpt-4.1 完成的运行都读全文后正确引用了 D05 P3（优先于通用规定）、D07 P1（2022 版废止），给出 answered。gpt-4o-mini 看到全文仍忽略这些条款。→ C05、C06 的失败**主要来自模型能力**。（gpt-4.1 各有 1 次因循环撞到步数上限。）
- C03、C04：**不是模型能力问题**。gpt-4.1 读了 D01、D02、D05 全文后，5/6 次标 answered，只回答 D02 的 15 天 + 差旅 10 天，**完全没提 D01 的 30 天**（C04 run1 答案写"根据公司最新的《员工费用报销操作指引》"）——这正是题目参考实例中明确禁止的"擅自回答 15 天"，属关键缺陷。推测模型按"版本较新优先"选择，尽管 prompt 第 4 条禁止。
- 新问题——循环：gpt-4.1 有 19 次 incomplete，11 次运行中同一调用重复 ≥3 次（v2 只有 1 次）。例如 C01 run1 连续 9 次 read_doc D03，reason 为"再次确认全文，确保没有遗漏"；C13、C14、C07 不断换关键词检索直到步数上限；C02 去检索"年假制度适用范围"，最后以"制度未写明适用范围，请问您是正式员工吗"返回 need_clarification。推测是 prompt 中"查找适用范围、优先级"的要求被更强（更谨慎）的模型泛化到了所有问题，且模型不知道剩余步数。第 3 步的"剩余步数"和"不要重复相同调用"可能针对此问题。
- 结论（Claude Code 的判断）：换更强模型能解决"看到但不核对"（C05/C06），但解决不了"冲突时偏向较新版本"（C03/C04），还引入了过度核实导致的循环。C03/C04 需要第 3 步的冲突处理步骤或结构化 conflict_check。

用时：本步 20:19 开始，20:28 结束（实时记录）。

**记录事故（Claude Code）**：写入本条记录时，Claude Code 用了未加引号的 shell heredoc，正文中反引号包裹的内容被 shell 当作命令执行（尝试把 scripts/run_eval.py、src/cli.py、结果 md 当 shell 脚本运行，均在首行报错退出；还用系统 Python 运行了一次 pytest，因缺依赖在导入阶段失败），未修改任何项目文件，但本条记录的两处文字被替换为空或命令输出，并随提交 6d17fef 推送。已在后续提交中恢复原文。之后写入含反引号的文本改用带引号的 heredoc 或 Edit。

---

## 2026-11-10 阶段 4 改进第 3 步：循环防护、冲突核对步骤、资料外规则（v3 / v3-strong）

**原方案**：原第 3 步计划（剩余步数、连续失败规则、ask_user 与 out_of_scope 区分、事实需引用）+ 我在诊断 A 后增加的冲突核对步骤。

**最终决定及改动内容**（我决定）：
1. 循环防护：每次工具 observation 附上"剩余步数：N"；与之前完全相同的工具调用（工具名和参数都相同）照常执行，但在 observation 中注明"与第 N 步调用相同，结果未变"；prompt 增加"同一工具连续失败 2 次后，改用其他方式或以 failed 结束并说明缺口；不要重复相同的调用"。
2. 冲突核对写成明确步骤，注意适用条件：只有多份文档对同一问题给出不同结论时才启动；单一文档能直接回答的问题读完原文即可回答，不额外查找适用范围。核对时逐份查找适用范围、优先级、替代或废止说明，判断"范围分工 / 已被替代 / 真冲突"；前两种须引用说明依据的原文作答，只有真冲突才用 conflict_need_confirmation。明确：版本日期更新不代表优先适用，除非原文写明替代或优先关系；不得只采用其中一份而忽略另一份的不同说法；不得把互相矛盾的规定并列作为答案。
3. 资料外与追问：问题本身指代不清才用 ask_user；问题清楚但文档不覆盖（如讲的是其他产品或功能）以 out_of_scope 结束。answer 中每个事实性陈述都必须有引用支持；out_of_scope 时不提供文档以外的建议。
4. gpt-4o-mini 与 gpt-4.1 各跑 --repeat 3，tag 分别为 v3、v3-strong。
5. CLAUDE.md 增加规则：写入含反引号或特殊字符的文本时，使用 Write 或 Edit 工具，不使用 shell heredoc。

**理由**：未说明。

**Claude Code 实现说明**：
- 剩余步数以 observation 字段"剩余步数"附加；无工具调用时的提醒文本末尾也附上剩余步数。
- 重复调用的判断不含 reason 字段。参数相同但结果不同时（如故障注入恢复后），只注明"与第 N 步调用相同"，不写"结果未变"，以免与事实不符。trace 摘要中同样标注。
- prompt 中的示例用通用表述（"一份是通用规定，另一份写明只适用于某类费用并优先适用"），未写入具体用例的问题文本。
- 测试修改（需求变更导致）：test_text_reply_is_reminded_and_counted（提醒文本附剩余步数）、test_chat_ask_user_reads_input（observation 增加"剩余步数"字段）。新增 5 个测试（剩余步数递减、重复调用标注与照常执行、结果变化时不写"结果未变"、trace 标注、prompt 包含关键规则）。共 122 个通过；Mock 16/16。

**验证方式与结果**（逐用例通过次数，由 trace 结果按 run_eval 的检查逻辑重算）：

| 用例 | v2（4o-mini） | v3（4o-mini） | v2-strong（4.1） | v3-strong（4.1） |
|---|---|---|---|---|
| C01 | 3/3 | 3/3 | 2/3 | 3/3 |
| C02 | 3/3 | 3/3 | 0/3 | 3/3 |
| C03 | 1/3 | 0/3 | 1/3 | 0/3 |
| C04 | 0/3 | 0/3 | 0/3 | 0/3 |
| C05 | 0/3 | 3/3 | 2/3 | 3/3 |
| C06 | 0/3 | 0/3 | 2/3 | 3/3 |
| C07 | 3/3 | 2/3 | 1/3 | 3/3 |
| C08 | 3/3 | 3/3 | 3/3 | 3/3 |
| C09 | 3/3 | 3/3 | 3/3 | 3/3 |
| C10 | 1/3 | 3/3 | 1/3 | 3/3 |
| C11 | 3/3 | 3/3 | 1/3 | 3/3 |
| C12 | 3/3 | 3/3 | 3/3 | 3/3 |
| C13 | 2/3 | 3/3 | 0/3 | 0/3 |
| C14 | 2/3 | 3/3 | 0/3 | 0/3 |
| V03 | 3/3 | 3/3 | 3/3 | 3/3 |
| V05 | 3/3 | 0/3 | 3/3 | 1/3 |
| 合计 | 33/48 | 35/48 | 25/48 | 34/48 |

**Claude Code 从 trace 看到的情况（尚待我判断）**：
- 有效的改动：
  - 连续失败规则：C10 两个模型都变为 3/3。**（2026-11-10 21:2x 收尾时更正，Claude Code：原写"search 失败 2 次后以 failed 结束"不准确。重查 trace：gpt-4o-mini 3 次都是连续 9 次 search_docs 失败后在第 10 步以 failed 结束，并没有遵守"连续失败 2 次后改用其他方式"；通过更可能是因为剩余步数提示让它在最后一步调用了 finish。gpt-4.1 在 2–3 次失败后改用 read_doc 逐份读取文档，2 次在第 10 步找到 D03 并 answered，1 次 3 次失败后以 failed 结束，较接近该规则。v4 中 gpt-4o-mini 的 C10 仍是同样的 9 次失败后 failed。）**
  - "单一文档读完即答"：gpt-4.1 在 C01、C02、C11 上的循环消失（均 3/3）。
  - 冲突核对步骤：gpt-4o-mini 的 C05 0/3 → 3/3（引用 D05 优先级条款）；gpt-4.1 的 C06 3/3。
  - 资料外规则：gpt-4o-mini 的 C13、C14 均 3/3。
- C03、C04（两个模型均 0/3，未解决）：
  - gpt-4o-mini：6 次都标 answered，把 D02 15 天和 D01 30 天（及 D05 10 天）并列作为答案——prompt 明确禁止的情形仍然发生。C03 run1 还自行编出"一般费用 15 天，其他费用 30 天"的分工，原文没有依据。
  - gpt-4.1：6 次都标 answered。5 次把 D02 当作"一般费用"规定、把 D05 当作差旅规定，完全不提 D01 的 30 天（读了 D01 却未引用）；C04 run3 提到 D01 时编出"如未特别说明，最晚不得超过 30 天"的调和说法。两个模型都没有把 D01 与 D02 识别为同一范围的真冲突，注意力被 D05 的"范围分工"吸引。
- V05（v2 时两模型都 3/3，v3 退步为 0/3、1/3）：
  - gpt-4o-mini：3 次都只引用 D05 P2 回答 10 天，读了 D01 却忽略其 20 天的说法（违反"不得只采用其中一份"）。推测新 prompt 的"范围分工"示例让模型按 D05 标题（差旅费用报销补充规定）把它当作差旅专项规定，没有看 scope 和第一段已改为"适用于公司全部费用报销"。
  - gpt-4.1：2 次引用 D05 P1"适用于公司全部费用报销"后回答 10 天，理由是"原文未说明被替代或废止"（run1 还写"公司最新的"），即在无优先说明时选了 D05；1 次正确判为真冲突。
  - 另：variant_b 的 D05 标题与第二段仍写"差旅"，而 scope 写"全部费用报销"，文档本身存在内部不一致，可能加重了误判。
- C06（gpt-4o-mini 仍 0/3）：只读 D07、D06 后报冲突，答案写"根据最新的 2024 版……"，未引用 D07 P1 废止说明；gpt-4.1 在 v3 为 3/3。仍判断为模型能力问题。
- C13、C14（gpt-4.1 均 0/3）：
  - C13：2 次标 answered，结论"年假未休一般不能折现，逾期作废"——"不能折现"是从"逾期作废"推出的，原文没有，且 gaps 为空；1 次连续检索撞到步数上限。
  - C14：3 次都连续检索 7 次以上、换不同关键词，撞到步数上限（重复调用提示只对参数完全相同的调用生效，不同关键词不会触发；剩余步数提示也没有让它及时停止）。
- C07（gpt-4o-mini 1 次失败）：连续 10 次不同关键词检索，撞到步数上限。
- 结论（Claude Code 的判断）：prompt 修改解决了循环、工具失败、单文档过度核实和资料外判断的大部分问题，但冲突类（C03/C04/V05）仅靠 prompt 两个模型都无法稳定处理：模型会被"范围分工"吸引，忽略另一份同范围文档或编出不存在的分工。这符合原计划 C 的触发条件（v3 中 C03–C06 仍有失败），可以讨论在 finish 中增加结构化 conflict_check 字段。

用时：本步 20:31 开始，20:42 运行与分析结束（实时记录）。

---

## 2026-11-10 计划 C0：修正 variant_b 数据，3h-snapshot 标签

**原方案**：Claude Code 在 v3 汇报中指出 variant_b 的 D05 标题和第二段仍写"差旅"、而 scope 写"全部费用报销"，文档内部不一致，可能加重 V05 误判，是否调整数据由我决定。

**最终决定及改动内容**（我决定）：
- C0：修正 variant_b 数据，D05 的标题和正文中去掉"差旅"相关字样，使其与"适用于公司全部费用报销"一致，优先级条款仍保持删除。更新 README。只重跑 V05（两个模型各 --repeat 3，tag 为 v3-dataC0 和 v3-strong-dataC0）。
- C1（待我确认后再做）：finish 增加必填字段 conflict_check（claims / relations）及 5 条校验规则。
- 找出 20:34 前最后一次提交，打 tag 3h-snapshot 并推送。

**理由**：未说明。

**Claude Code 实现说明**：
- 3h-snapshot：20:34 前最后一次提交为 f8beab3（20:29:31，"决策日志：修复诊断 A 记录中被 shell 误替换的文字"），已打附注标签并推送。
- variant_b/D05：标题"差旅费用报销补充规定"改为"费用报销补充规定"；第二段"差旅费用应在出差结束之日起10天内提交报销申请。"改为"费用应在发生之日起10天内提交报销申请。"——起算点随之从"出差结束之日"变为"发生之日"，与 D01 一致。第三段（住宿费标准）未改，它不含"差旅"字样，但内容与出差相关。
- Mock 的 V05 序列按新原文修改引用；test_variant_b_differs_as_documented 增加"D05 标题和正文不含差旅"的断言。122 个测试通过，Mock 16/16。

**验证方式与结果**（V05，--repeat 3）：

| 模型 | v3（旧数据） | C0 后 |
|---|---|---|
| gpt-4o-mini | 0/3 | 3/3（tag v3-dataC0） |
| gpt-4.1 | 1/3 | 2/3（tag v3-strong-dataC0） |

**Claude Code 从 trace 看到的情况（尚待我判断）**：
- gpt-4o-mini：3 次都读 D05、D01 后判为 conflict_need_confirmation。v3 时它只引用 D05 回答 10 天，数据修正后不再出现，说明之前的失败与 D05 标题和正文中的"差旅"字样有关。
- gpt-4.1 run2 失败：读了 D05、D01 全文（各读两次），finish 理由为"D05 为最新且适用全部费用报销的规定"，answer 写"根据公司最新的《费用报销补充规定》（2024-09-01版）……该时限为当前有效规定"，只引用 D05——即按版本日期选择，正是 prompt 明确禁止的情形；answer 末尾还有文档以外的建议（"建议及时与财务部联系"）。这与 v3-strong 中 C03/C04 的失败形态一致，属于计划 C1 要处理的问题。

用时：本步 20:48 开始，20:50 结束（实时记录）。

---

## 2026-11-10 计划 C1：finish 增加结构化 conflict_check（v4 / v4-strong）

**原方案**：计划 C（我在 v2-strong 诊断后提出）：v3 中 C03–C06 仍失败时，讨论在 finish 中增加结构化 conflict_check。我给出了 claims / relations 字段和 5 条校验规则的设计。

**最终决定及改动内容**（我决定）：
- C0 确认；variant_b 的 D05 第三段（住宿费标准）保留不改，在 README 中注明（README 已有此说明）。
- finish 增加必填字段 conflict_check：
  - claims：本次用 read_doc 读过的每一份文档都要列出（doc_id、claim、scope_quote；无关写"与问题无关"，没有适用范围原文填"未说明"）。
  - relations：**修改**为——claims 中所有 claim 不是"与问题无关"的文档，必须两两都有一条 relation（不再由模型判断"结论是否不同"再决定写不写）；校验检查是否有缺失的文档对。字段 docs、type（consistent / scope_split / superseded / priority / true_conflict）、basis。
  - 校验：claims 必须覆盖本次读过的全部文档；scope_split / superseded / priority 必须有通过逐字校验、来自这两份文档之一的 basis；scope_split 时两份文档的 scope_quote 不能都是"未说明"，非"未说明"的 scope_quote 须逐字存在；存在 true_conflict 时 status 必须是 conflict_need_confirmation。
  - 更新工具 schema、prompt、Mock 序列（新增"先错误地标 scope_split 被拒，再修正为 true_conflict"）和测试。
- 两个模型跑全部用例，各 --repeat 3，tag 为 v4、v4-strong。

**理由**：未说明。

**已知限制**（我要求记录，并写入后续文档）：程序无法判断 claim 在语义上是否一致，模型把不同结论标为 consistent 时校验拦不住，需靠人工审核 trace 发现。

**Claude Code 实现说明**：
- 非"未说明"的 scope_quote 对所有 claims 都做逐字校验（不仅限于 scope_split 涉及的文档），可匹配文档的 scope 元数据字段或任一正文段落。
- 引用逐字校验抽成 `check_quote`，citations 与 basis 共用（basis 同样要求至少 8 字、段落在本次 read_doc 中读过）。
- 最终输出和 trace 中增加 conflict_check；未调用 finish 时（incomplete / llm_error）为 null。
- 测试：test_finish.py 的 finish 辅助函数在不传 conflict_check 时自动为读过的文档生成"与问题无关"的 claims，使原有引用校验测试只关注引用；conflict_check 规则新增 16 个测试，含"不同结论标为 consistent 仍会通过"的限制测试。test_agent.py 按新字段调整 5 处，新增 SCOPE_SPLIT_WRONG 序列测试。共 139 个通过，Mock 16/16。

**验证方式与结果**（逐用例通过次数；V05 的 v3 / v3-strong 列取 dataC0 结果）：

| 用例 | v3（4o-mini） | v4（4o-mini） | v3-strong（4.1） | v4-strong（4.1） |
|---|---|---|---|---|
| C01 | 3/3 | 3/3 | 3/3 | 1/3 |
| C02 | 3/3 | 3/3 | 3/3 | 1/3 |
| C03 | 0/3 | 3/3 | 0/3 | 2/3 |
| C04 | 0/3 | 3/3 | 0/3 | 2/3 |
| C05 | 3/3 | 2/3 | 3/3 | 1/3 |
| C06 | 0/3 | 0/3 | 3/3 | 3/3 |
| C07 | 2/3 | 3/3 | 3/3 | 2/3 |
| C08 | 3/3 | 3/3 | 3/3 | 0/3 |
| C09 | 3/3 | 3/3 | 3/3 | 3/3 |
| C10 | 3/3 | 3/3 | 3/3 | 0/3 |
| C11 | 3/3 | 3/3 | 3/3 | 1/3 |
| C12 | 3/3 | 3/3 | 3/3 | 3/3 |
| C13 | 3/3 | 3/3 | 0/3 | 1/3 |
| C14 | 3/3 | 1/3 | 0/3 | 0/3 |
| V03 | 3/3 | 2/3 | 3/3 | 3/3 |
| V05 | 3/3 | 3/3 | 2/3 | 1/3 |
| 合计 | 38/48 | **41/48** | 35/48 | **24/48** |

finish 被拒次数合计：v4 13 次、v4-strong 8 次；incomplete：v4 3 次（全部是 C12，按设计）、v4-strong 25 次。

**Claude Code 从 trace 看到的情况（尚待我判断）**：
- gpt-4o-mini 的 C03、C04 由 0/3 变为 3/3，起作用的是规则 4：6 次运行都先以 answered 提交、同时在 relations 中写了 true_conflict，被拒后改为 conflict_need_confirmation。即模型在结构化字段里能识别冲突，但写 status 时仍倾向 answered，校验把二者对齐了。不过 C03 的 3 次把 D05 与 D01、D02 也都标成 true_conflict（D05 P3 写明优先于通用规定，应为 priority / scope_split），状态正确，但冲突说明多列了 D05。
- gpt-4.1 的 C03、C04 完成的 4 次都标得完全正确：D05 与 D01、D02 为 scope_split，D01 与 D02 为 true_conflict。
- gpt-4o-mini 新出现的 finish 被拒，主要来自规则 1：C13、C14 共 6 次漏写读过的 D03 / D09，被拒后补上。
- gpt-4.1 的 25 次 incomplete：过度核实循环再次出现，且比 v3 严重。例如 C01 读了无关的 D06 后，连续 4 次重读 D03"确认适用范围"，再检索"年假管理制度 适用范围"；C08 同样反复重读 D04、D03 并检索"适用范围"，3 次都撞到步数上限。重复调用提示（"与第 N 步调用相同，结果未变"）出现在 observation 中，但模型没有停止。推测：conflict_check 要求每份读过的文档都填 scope_quote，使 gpt-4.1 认为必须找到"适用范围"原文。C10 中它在检索不可用时逐份读取 D01–D07 寻找年假规定，也撞到上限。
- 仍失败的其他用例：
  - C06（gpt-4o-mini 0/3）：3 次都把 D06–D07 标成 true_conflict，未用 D07 P1 的废止说明，仍判断为模型能力问题。
  - C05（gpt-4o-mini run1）：把 D05–D02 标成 true_conflict（D05 P3 写明优先），被规则 4 强制改为冲突状态。
  - C14（gpt-4o-mini 2 次）：need_clarification，问"您使用的是剪影Pro 的哪个版本"，仍把报表导出当作 D09 的产品问题。
  - C13（gpt-4.1 run1）：answered，结论"年假未休完不能折现"，是从"逾期作废"推出的，原文没有，gaps 为空。
  - V03（gpt-4o-mini run1）：status=failed、reason=llm_error（APITimeoutError，API 层重试 1 次后仍超时），属于接口问题，与 Agent 逻辑无关。
- **把不同结论标成 consistent 的情况：没有出现**（v4、v4-strong 的 96 次运行中没有任何 relation 标为 consistent）。但出现了一次**同类限制**：gpt-4.1 的 V05 run1 把 D05–D01 标成 priority，basis 是 D05 P1"本规定适用于公司全部费用报销。"——这句是适用范围说明，不是优先级说明。basis 逐字存在且来自其中一份文档，校验通过，最终 answered 回答 10 天，finish 理由为"D05 为最新且适用范围覆盖全部费用报销，应优先适用"。程序同样无法判断 basis 的语义是否真的支持所标的关系类型。该运行中模型还先提交过 status="priority"（被枚举校验拒绝）。

用时：本步 20:55 开始，21:12 运行与分析结束（实时记录）。
