# Trace：C11

**真实模型运行**：`gpt-4.1`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- fail_times：1
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假天数", "top_k": 5} | 需要查找公司关于工作年限与年假天数的规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "司龄5年 年假", "top_k": 5} | 更换关键词尝试检索工作满5年对应的年假天数。 | 命中 5 条：D03/P1(10.407)，D03/P4(4.837)，D03/P3(4.707)，D03/P2(3.494)，D06/P2(2.418) | read_doc |
| 3 | read_doc | {"doc_id": "D03"} | 需要确认原文关于工作满5年员工年假天数的具体规定。 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | finish |
| 4 | finish | {"status": "answered", "answer": "根据《年假管理制度》（2024-01-01版），员工累计工作已满1年不满10年的，年休假为5天。因此，工作满5年可享受5天年假。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天"}], "gaps": []} | 已找到明确规定工作满5年对应的年假天数的原文。 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：4
- answer：根据《年假管理制度》（2024-01-01版），员工累计工作已满1年不满10年的，年休假为5天。因此，工作满5年可享受5天年假。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天」
- gaps：
  - （无）
