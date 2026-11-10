# Trace：C07

**真实模型运行**：`gpt-4.1`

- question：公司股票期权怎么行权？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "股票期权 行权流程", "top_k": 5} | 用户询问股票期权行权流程，应先检索相关制度或流程说明。 | 命中 4 条：D04/P2(2.635)，D04/P4(2.354)，D04/P3(2.234)，D04/P1(2.179) | search_docs |
| 2 | search_docs | {"query": "期权 行权 操作流程", "top_k": 5} | 上次检索未命中股票期权相关内容，尝试换用同义说法和补充关键词重新检索。 | 命中 5 条：D04/P2(2.635)，D04/P4(2.354)，D02/P1(2.234)，D04/P3(2.234)，D02/P4(2.179) | search_docs |
| 3 | search_docs | {"query": "股票期权 行权 申请", "top_k": 5} | 前两次检索未找到股票期权行权相关内容，尝试进一步补充关键词重新检索。 | 命中 5 条：D03/P3(2.503)，D07/P3(2.214)，D06/P2(1.846)，D04/P1(1.664)，D10/P1(1.549) | search_docs |
| 4 | search_docs | {"query": "员工持股计划 行权", "top_k": 5} | 前几次检索未找到股票期权行权相关内容，尝试用“员工持股计划”作为同义词补充检索。 | 命中 5 条：D02/P1(1.351)，D02/P4(1.327)，D02/P2(1.239)，D03/P4(1.033)，D06/P1(1.033) | search_docs |
| 5 | search_docs | {"query": "股票期权管理制度", "top_k": 5} | 前几次检索均未命中股票期权相关内容，尝试直接检索是否有股票期权管理制度。 | 命中 4 条：D03/P4(2.418)，D03/P3(2.354)，D03/P2(1.747)，D03/P1(1.681) | search_docs |
| 6 | search_docs | {"query": "期权激励 行权", "top_k": 5} | 尝试用“期权激励”作为关键词补充检索，寻找股票期权行权相关内容。 | 无命中 | search_docs |
| 7 | search_docs | {"query": "股票期权 FAQ", "top_k": 5} | 尝试检索是否有股票期权相关的FAQ文档。 | 无命中 | search_docs |
| 8 | search_docs | {"query": "期权 行权 FAQ", "top_k": 5} | 尝试用“期权 行权 FAQ”检索，确认是否有相关常见问题解答。 | 无命中 | search_docs |
| 9 | search_docs | {"query": "股票激励 行权", "top_k": 5} | 尝试用“股票激励”作为关键词补充检索，寻找股票期权行权相关内容。 | 无命中 | search_docs |
| 10 | search_docs | {"query": "期权 行权 规则", "top_k": 5} | 尝试用“期权 行权 规则”检索，确认是否有相关制度或规则说明。 | 无命中 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：10
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 10 仍未完成
