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
| 3 | search_docs | {"query": "年假天数与工龄关系", "top_k": 5} | 再次尝试检索，换用更通用的关键词。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 4 | search_docs | {"query": "年假规定", "top_k": 5} | 多次检索失败，尝试用更宽泛的关键词。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | finish |
| 5 | finish | {"status": "failed", "answer": "很抱歉，目前无法检索到相关制度资料，暂时无法回答您的问题。请稍后再试或联系管理员。", "citations": [], "gaps": ["无法访问公司年假相关制度资料"]} | 多次检索均因工具故障无法获取资料，无法完成任务。 | 校验通过，结束 | 结束（failed） |

## 结果

- status：`failed`
- reason：`finish_called`
- steps_used：5
- answer：很抱歉，目前无法检索到相关制度资料，暂时无法回答您的问题。请稍后再试或联系管理员。
- citations：
  - （无）
- gaps：
  - 无法访问公司年假相关制度资料
