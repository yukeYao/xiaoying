# Trace：C10

**真实模型运行**：`gpt-4.1`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假天数", "top_k": 5} | 用户询问工作满5年对应的年假天数，需要检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "司龄5年 年假", "top_k": 5} | 上次工具调用失败，尝试用同义说法重新检索年假天数相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 3 | search_docs | {"query": "年假天数规定", "top_k": 5} | 前两次检索失败，尝试更通用的关键词检索年假天数相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | finish |
| 4 | finish | {"status": "failed", "answer": "很抱歉，目前无法检索到关于工作满5年年假天数的相关规定，因检索工具暂时不可用。如需查询，请稍后再试或联系管理员。", "citations": [], "gaps": ["无法检索年假天数相关规定，因search_docs工具不可用"]} | 连续多次检索工具故障，无法获取所需信息。 | 校验通过，结束 | 结束（failed） |

## 结果

- status：`failed`
- reason：`finish_called`
- steps_used：4
- answer：很抱歉，目前无法检索到关于工作满5年年假天数的相关规定，因检索工具暂时不可用。如需查询，请稍后再试或联系管理员。
- citations：
  - （无）
- gaps：
  - 无法检索年假天数相关规定，因search_docs工具不可用
