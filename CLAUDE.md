# 项目规则
- 这是校招笔试项目：企业知识问答 Agent。Python 3.10+，原生实现 Agent 循环，不使用 LangChain/LangGraph。
- 分阶段工作：每个阶段结束后停下，说明新增/修改的文件、运行方式、已知问题，等我确认后再继续。
- 绝不修改测试来迁就失败的结果；遇到不符合预期的结果，先报告给我。
- 回答中的引用必须逐字存在于原文，不能编造引用。
- 真实模型跑出的 trace 和 Mock 跑出的 trace 分开存放，并明确标注。
- 不提交任何真实密钥；.env 必须在 .gitignore 中。
- docs/04-ai-usage.md 和 docs/05-retrospective.md 只生成模板，内容由我本人填写。
- 代码保持简洁，避免过度工程化。

# 决策日志
- 维护 docs/decision-log.md。每当我确认、否决或修改你的方案，或者我们在调试中发现并解决了问题，追加一条记录：
  - 日期时间、阶段
  - 原方案（谁提出：Claude Code / 我 / 外部 Claude 对话审核）
  - 最终决定及改动内容
  - 理由（如果我说明了理由就照录；没说明就写"未说明"，不要替我编理由）
  - 验证方式（如有）
- 只记录对话中实际发生的事，不推测、不美化我的贡献。

# 常用命令
虚拟环境在项目根目录 `.venv`（已被 .gitignore 忽略）。

| 用途 | Windows (PowerShell / Git Bash) | macOS / Linux |
|---|---|---|
| 创建虚拟环境 | `python -m venv .venv` | `python3 -m venv .venv` |
| 安装依赖 | `.venv/Scripts/python -m pip install -r requirements.txt` | `.venv/bin/python -m pip install -r requirements.txt` |
| 运行测试 | `.venv/Scripts/python -m pytest -q` | `.venv/bin/python -m pytest -q` |
| 检索评测 | `.venv/Scripts/python scripts/eval_retrieval.py` | `.venv/bin/python scripts/eval_retrieval.py` |
| 检索评测（替换版数据） | `.venv/Scripts/python scripts/eval_retrieval.py --data-dir data/variant/docs --out examples/retrieval_eval_variant.md` | `.venv/bin/python scripts/eval_retrieval.py --data-dir data/variant/docs --out examples/retrieval_eval_variant.md` |

Windows 终端输出中文乱码时，先设置 `PYTHONIOENCODING=utf-8`（Git Bash：`export PYTHONIOENCODING=utf-8`；PowerShell：`$env:PYTHONIOENCODING="utf-8"`）。

（运行 CLI、端到端评测 run_eval.py 待阶段 3/4 补充）
