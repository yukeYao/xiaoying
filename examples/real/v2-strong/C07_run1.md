# Trace：C07

**真实模型运行**：`gpt-4.1`

- question：公司股票期权怎么行权？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "股票期权 行权流程", "top_k": 5} | 用户询问股票期权行权流程，应检索相关制度或流程说明。 | 命中 4 条：D04/P2(2.635)，D04/P4(2.354)，D04/P3(2.234)，D04/P1(2.179) | search_docs |
| 2 | search_docs | {"query": "期权 行权 操作流程", "top_k": 5} | 上次检索未命中相关内容，尝试换用同义说法和补充关键词重新检索。 | 命中 5 条：D04/P2(2.635)，D04/P4(2.354)，D02/P1(2.234)，D04/P3(2.234)，D02/P4(2.179) | search_docs |
| 3 | search_docs | {"query": "股票期权制度", "top_k": 5} | 前两次检索未找到相关内容，尝试直接检索股票期权相关制度。 | 无命中 | search_docs |
| 4 | search_docs | {"query": "股权激励 行权流程", "top_k": 5} | 尝试用“股权激励”作为同义词补充检索，扩大覆盖面。 | 命中 4 条：D04/P2(2.635)，D04/P4(2.354)，D04/P3(2.234)，D04/P1(2.179) | search_docs |
| 5 | search_docs | {"query": "期权 行权 指南", "top_k": 5} | 尝试用“指南”作为补充关键词，进一步扩大检索范围。 | 无命中 | search_docs |
| 6 | search_docs | {"query": "股票期权 操作指引", "top_k": 5} | 尝试用“操作指引”作为补充关键词，进一步扩大检索范围。 | 命中 4 条：D02/P1(5.395)，D02/P4(4.358)，D02/P2(3.966)，D02/P3(3.966) | search_docs |
| 7 | search_docs | {"query": "期权 行权 申请", "top_k": 5} | 尝试用“申请”作为补充关键词，进一步扩大检索范围。 | 命中 5 条：D03/P3(2.503)，D07/P3(2.214)，D06/P2(1.846)，D04/P1(1.664)，D10/P1(1.549) | search_docs |
| 8 | search_docs | {"query": "期权激励 行权", "top_k": 5} | 尝试用“期权激励”作为补充关键词，进一步扩大检索范围。 | 无命中 | search_docs |
| 9 | search_docs | {"query": "股票 行权", "top_k": 5} | 尝试用更简化的关键词进行检索，避免遗漏相关内容。 | 无命中 | search_docs |
| 10 | search_docs | {"query": "期权 行权", "top_k": 5} | 尝试用最核心关键词进行检索，确保没有遗漏相关内容。 | 无命中 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：10
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 10 仍未完成
