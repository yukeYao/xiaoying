# Trace：C10

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "年假天数", "top_k": 5} | 检索年假制度 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "年休假 工龄", "top_k": 5} | 检索失败，换关键词重试 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | finish |
| 3 | finish | {"status": "failed", "answer": "检索工具连续不可用，无法获取资料，暂时无法回答。", "gaps": ["search_docs 连续两次返回 tool_unavailable"], "citations": []} | 重试仍失败 | 校验通过，结束 | 结束（failed） |

## 结果

- status：`failed`
- reason：`finish_called`
- steps_used：3
- answer：检索工具连续不可用，无法获取资料，暂时无法回答。
- citations：
  - （无）
- gaps：
  - search_docs 连续两次返回 tool_unavailable
