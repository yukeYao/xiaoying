# Trace：C07

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：公司股票期权怎么行权？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "股票期权 行权", "top_k": 5} | 检索股票期权 | 无命中 | search_docs |
| 2 | search_docs | {"query": "期权 股权激励", "top_k": 5} | 无命中，换同义说法再检索 | 无命中 | finish |
| 3 | finish | {"status": "out_of_scope", "answer": "资料库中没有关于股票期权行权的规定，无法回答。", "gaps": ["缺少股权激励 / 期权相关制度文档"], "citations": [], "conflict_check": {"claims": [], "relations": []}} | 两次检索均无相关结果 | 校验通过，结束 | 结束（out_of_scope） |

## 结果

- status：`out_of_scope`
- reason：`finish_called`
- steps_used：3
- answer：资料库中没有关于股票期权行权的规定，无法回答。
- citations：
  - （无）
- gaps：
  - 缺少股权激励 / 期权相关制度文档
- conflict_check：
