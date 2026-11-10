# 企业知识问答 Agent

小影校招 AI Agent 开发岗笔试项目（企业知识问答 Agent 题）。

帮助员工查找公司制度和产品问题的可靠答案。Agent 用**原生实现的 ReAct 循环**（不使用 LangChain / LangGraph），通过 tool calling 自主选择检索、读原文、追问或结束：
- 回答必须附逐字引用，引用由程序校验；
- 资料冲突时说明冲突并请用户确认，而不是擅自挑选一个答案；
- 资料外问题如实说明缺口；
- 工具失败和步数上限都有明确的状态。

- 需求与验收标准：[docs/01-requirements.md](docs/01-requirements.md)
- 设计与技术取舍：[docs/02-solution.md](docs/02-solution.md)
- 评测结果、失败与限制：[docs/03-evaluation.md](docs/03-evaluation.md)
- AI 使用说明：[docs/04-ai-usage.md](docs/04-ai-usage.md)　复盘：[docs/05-retrospective.md](docs/05-retrospective.md)
- 决策日志（每轮改动、理由和结果）：[docs/decision-log.md](docs/decision-log.md)
- 运行记录索引：[examples/README.md](examples/README.md)

## 环境要求

- Python 3.10+（开发环境为 Python 3.12.7）
- 依赖见 `requirements.txt`（已固定版本）：openai、jieba、python-dotenv、pytest
- 真实模型：任意 OpenAI 兼容接口，模型需支持 tool calling。默认 `gpt-4o-mini`
- 不配置模型也可以运行离线 Mock 和全部测试

## 安装

Windows（PowerShell 或 Git Bash）：

```bash
git clone https://github.com/yukeYao/xiaoying.git
```
```bash
cd xiaoying
```
```bash
python -m venv .venv
```
```bash
.venv/Scripts/python -m pip install -r requirements.txt
```

macOS / Linux：

```bash
git clone https://github.com/yukeYao/xiaoying.git
```
```bash
cd xiaoying
```
```bash
python3 -m venv .venv
```
```bash
.venv/bin/python -m pip install -r requirements.txt
```

下文命令都用 Windows 写法 `.venv/Scripts/python`；macOS / Linux 换成 `.venv/bin/python`。Windows 终端中文乱码时，先设置 `PYTHONIOENCODING=utf-8`（PowerShell：`$env:PYTHONIOENCODING="utf-8"`；Git Bash：`export PYTHONIOENCODING=utf-8`）。

## .env 配置（只有真实模型需要）

复制模板后填写自己的 key：

```bash
cp .env.example .env
```

（PowerShell：`Copy-Item .env.example .env`）

| 变量 | 说明 |
|---|---|
| `AGENT_MODEL` | 模型名，默认 `gpt-4o-mini`。也可以用 `--model` 参数或环境变量临时切换，不用改 .env |
| `AGENT_API_KEY` | API key |
| `AGENT_BASE_URL` | OpenAI 兼容接口地址，例如 `https://api.openai.com/v1` |

`.env` 已被 `.gitignore` 忽略，不会被提交。检查模型是否可用、是否支持 tool calling：

```bash
.venv/Scripts/python scripts/smoke_llm.py
```

## 评审入口

| 目的 | Windows | macOS / Linux |
|---|---|---|
| 运行全部测试（不需要模型） | `.venv/Scripts/python -m pytest -q` | `.venv/bin/python -m pytest -q` |
| **离线 Mock**：全部用例（只验证流程） | `.venv/Scripts/python scripts/run_eval.py --mock` | `.venv/bin/python scripts/run_eval.py --mock` |
| **真实模型单个用例**（冲突用例 C03） | `.venv/Scripts/python -m src.cli --case C03` | `.venv/bin/python -m src.cli --case C03` |
| 真实模型任意问题 | `.venv/Scripts/python -m src.cli "报销期限多久？"` | `.venv/bin/python -m src.cli "报销期限多久？"` |
| **批量评测**（16 个用例 × 3 次） | `.venv/Scripts/python scripts/run_eval.py --real --repeat 3 --tag review` | `.venv/bin/python scripts/run_eval.py --real --repeat 3 --tag review` |
| **交互多轮模式**（保留对话历史，ask_user 会真的提问） | `.venv/Scripts/python -m src.cli --chat` | `.venv/bin/python -m src.cli --chat` |
| 检索评测 | `.venv/Scripts/python scripts/eval_retrieval.py` | `.venv/bin/python scripts/eval_retrieval.py` |

常用参数：
- `--mock`：单个用例也可以离线跑，例如 `-m src.cli --case C03 --mock`。
- `--trace-dir 目录`：保存 trace（JSONL + Markdown）。
- `--max-steps N`：最大步数，默认 10。
- `--fail-tool search_docs --fail-times 1`：故障注入，`--fail-times` 不填表示每次都失败。
- `--model gpt-4.1`：临时换模型。

批量评测的结果写入 `examples/eval_results_real_review.md`，trace 写入 `examples/real/review/`。建议每次用不同的 `--tag`，以免覆盖已有结果。

输出示例：v4 中 C03 的一次真实运行，节选自 [examples/real/v4/C03_run1.md](examples/real/v4/C03_run1.md)，`……` 处有省略。

```json
{
  "status": "conflict_need_confirmation",
  "answer": "报销期限如下：……由于不同文档对报销期限的规定存在冲突，请确认适用哪份制度：\n- 文档 D02（员工费用报销操作指引）规定为15天。\n- 文档 D01（财务报销管理办法）规定为30天。\n- 文档 D05（差旅费用报销补充规定）规定为10天。",
  "citations": [
    {"doc_id": "D02", "paragraph_id": "P2", "quote": "员工须在费用发生后15天内通过报销系统提交报销单，并上传发票影像。",
     "title": "员工费用报销操作指引", "version_date": "2024-06-15"},
    {"doc_id": "D01", "paragraph_id": "P2", "quote": "员工应在费用发生之日起30天内提交报销申请，逾期提交的，财务部有权不予受理。",
     "title": "财务报销管理办法", "version_date": "2023-03-01"},
    "……"
  ],
  "gaps": [],
  "conflict_check": {
    "claims": [{"doc_id": "D02", "claim": "员工须在费用发生后15天内通过报销系统提交报销单。", "scope_quote": "未说明"}, "……"],
    "relations": [{"docs": ["D02", "D01"], "type": "true_conflict", "basis": null}, "……"]
  },
  "reason": "finish_called", "steps_used": 6, "mode": "real", "model": "gpt-4o-mini",
  "trace_file": "examples/real/v4/C03_run1.md"
}
```

这次运行把差旅规定 D05 也列成了冲突的一方。D05 写明它适用于差旅、并且优先于通用规定，所以更准确的写法是只把 D01 与 D02 列为冲突，见 03 的"判为通过但内容有问题"。

## 替换文档测试

文档是 `data/docs/*.md`，格式如下：前几行是元数据，`---` 之后是正文，正文按空行分段，自动编号为 P1、P2……

```text
doc_id: D01
title: 财务报销管理办法
version_date: 2023-03-01
scope:
---
第一条 为规范公司费用报销管理，制定本办法。

第二条 员工应在费用发生之日起30天内提交报销申请，……
```

验证"答案和动作随文档变化"有两种方式：

1. **用现成的替换版**：
   - `data/variant_a/`：删除 D02，D01 改为 20 天。
   - `data/variant_b/`：D05 删除优先级条款，适用范围改为全部费用。
   - 两份的改动说明见各自目录下的 README。

   ```bash
   .venv/Scripts/python -m src.cli "报销期限多久？" --data-dir data/variant_a/docs
   ```

   主数据集下这个问题应返回冲突（D01 30 天 vs D02 15 天）；在 variant_a 下应回答 20 天。

2. **自己修改**：复制 `data/docs` 到一个新目录，修改或删除其中的文档，然后用 `--data-dir 新目录` 重跑同一个问题，对比结果和 trace（加 `--trace-dir` 保存）。
   - 用例 V03 / V05 已固定使用 variant_a / variant_b。
   - 其他用例可以用 `--case C03 --data-dir 新目录` 换数据重跑。
   - `run_eval.py` 按 `data/cases.jsonl` 中每个用例的 data_dir 运行；直接修改 `data/docs` 后重跑批量评测，也能看到变化。

## 结果摘要

逐用例结果和分析见 [docs/03-evaluation.md](docs/03-evaluation.md)，每轮的 trace 见 [examples/README.md](examples/README.md)。

| 轮次 | 主要改动 | gpt-4o-mini | gpt-4.1（对照） |
|---|---|---|---|
| v1（基线） | — | 34/48 | — |
| v2 | read_doc 总是返回全文 | 33/48 | 25/48 |
| v3 | prompt：冲突核对步骤、资料外 / 追问规则；剩余步数、重复调用提示 | 38/48¹ | 35/48¹ |
| **v4（最终）** | finish 增加结构化 conflict_check 及程序校验 | **41/48** | 24/48 |

¹ V05 用修正 variant_b 数据后的重跑结果（v3-dataC0）。不替换时 v3 为 35/48、v3-strong 为 34/48。

- 冲突用例 C03 / C04：gpt-4o-mini 在 v3 为 0/3，v4 为 3/3。
- Mock：16/16（只验证流程）。
- 确定性测试：139 个通过。

## 用时说明

- 开始时间：2026-11-10 17:34。题目建议投入 3 小时。
- **`3h-snapshot` 标签**：指向 17:34 + 3 小时（20:34）之前的最后一次提交 `f8beab3`（20:29）。此时已完成：
  - 数据集与检索；
  - ReAct 循环、Mock、引用校验、故障注入、trace、CLI、批量评测；
  - 真实模型基线（v1）、read_doc 全文（v2）、gpt-4.1 诊断（v2-strong）。
- **之后的延伸改进**：
  - v3：prompt 中的冲突核对步骤，以及剩余步数、重复调用提示；
  - variant_b 数据修正（C0）；
  - v4：结构化 conflict_check；
  - 收尾文档。
- 收尾完成时间与各阶段明细：见 [docs/decision-log.md](docs/decision-log.md) 开头的用时记录（由 Claude Code 实时记录，作者核对）。
- `core-complete` 标签尚未打，由作者决定。

## 未完成部分与已知限制

详见 [docs/03-evaluation.md](docs/03-evaluation.md#已知限制)。

- 逐字校验只能证明引用存在，不能证明引用支持回答。
- 程序无法判断 conflict_check 中 claim / basis 的语义（例如把不同结论标为 consistent，或拿适用范围说明当作 priority 的依据），需要人工审核 trace。
- gpt-4.1 在最终版本中因过度核实循环有 25 次撞到步数上限，所以默认模型用 gpt-4o-mini。
- gpt-4o-mini 始终不能用"废止"说明判定 C06（0/3）；C14 有时把资料外问题当作需要追问。
- 小语料下同义词扩展没有可测量的收益；read_doc 返回全文只适合短文档。
- 自动评测不检查 answer 内容，部分"通过"的运行内容有问题（见 03）。
- 未做：扩大语料重新评估检索、针对 gpt-4.1 循环的改进、答案内容的自动检查。

## 目录

```text
src/        Agent 循环、工具、模型接入、Mock、trace、CLI
scripts/    run_eval.py（批量评测）、eval_retrieval.py（检索评测）、smoke_llm.py（模型连通性）
tests/      pytest（不依赖模型）
data/       docs/（主数据集）、variant_a/、variant_b/、cases.jsonl、synonyms.json、检索评测问题
examples/   评测结果与 trace（real/ 与 mock/ 分开）
docs/       01–05 文档与决策日志
```
