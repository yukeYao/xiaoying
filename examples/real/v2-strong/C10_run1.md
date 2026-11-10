# Trace：C10

**真实模型运行**：`gpt-4.1`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假天数", "top_k": 5} | 需要查找公司关于工作年限与年假天数的规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "司龄5年 年假", "top_k": 5} | 第一次检索失败，尝试用同义说法重新检索。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 3 | search_docs | {"query": "年假天数与工龄关系", "top_k": 5} | 再次尝试检索，换用不同关键词。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 4 | search_docs | {"query": "年假规定", "top_k": 5} | 尝试用更宽泛的关键词检索年假相关制度。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 5 | search_docs | {"query": "年假", "top_k": 5} | 进一步简化关键词，尝试基础检索。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 6 | search_docs | {"query": "带薪年假", "top_k": 5} | 尝试用“带薪年假”关键词检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 7 | search_docs | {"query": "员工年假", "top_k": 5} | 尝试用“员工年假”关键词检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 8 | search_docs | {"query": "年假天数", "top_k": 5} | 尝试用“年假天数”关键词检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 9 | search_docs | {"query": "年假政策", "top_k": 5} | 尝试用“年假政策”关键词检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 10 | search_docs | {"query": "工龄满5年 年假", "top_k": 5} | 尝试用“工龄满5年 年假”关键词检索相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：10
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 10 仍未完成
