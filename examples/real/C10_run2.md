# Trace：C10

**真实模型运行**：`gpt-4o-mini`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假", "top_k": 5} | 检索关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "年假 规定", "top_k": 5} | 检索关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 3 | search_docs | {"query": "年假", "top_k": 5} | 检索关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 4 | search_docs | {"query": "员工年假", "top_k": 5} | 检索关于员工年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 5 | search_docs | {"query": "年假 5年", "top_k": 5} | 检索关于工作满5年的年假规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 6 | search_docs | {"query": "年假 规定", "top_k": 5} | 检索关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 7 | search_docs | {"query": "年假", "top_k": 5} | 检索关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 8 | search_docs | {"query": "员工年假", "top_k": 5} | 检索关于员工年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 9 | search_docs | {"query": "年假 5年", "top_k": 5} | 检索关于工作满5年的年假规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | finish |
| 10 | finish | {"status": "failed", "answer": "无法完成检索年假相关规定的问题，系统出现故障。", "citations": [], "gaps": ["年假规定的具体内容"]} | 检索服务不可用，无法获取相关信息。 | 校验通过，结束 | 结束（failed） |

## 结果

- status：`failed`
- reason：`finish_called`
- steps_used：10
- answer：无法完成检索年假相关规定的问题，系统出现故障。
- citations：
  - （无）
- gaps：
  - 年假规定的具体内容
