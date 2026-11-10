# Trace：C10

**真实模型运行**：`gpt-4.1`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假天数", "top_k": 5} | 需要查找公司关于工作年限与年假天数的具体规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "司龄5年 年假", "top_k": 5} | 更换关键词尝试检索工作满5年对应的年假天数。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 3 | read_doc | {"doc_id": "D01"} | 假设D01为公司假期相关制度，尝试直接读取以获取年假规定。 | D01《财务报销管理办法》版本 2023-03-01，全文 P1,P2,P3,P4,P5 | search_docs |
| 4 | search_docs | {"query": "年假天数规定", "top_k": 5} | 直接检索年假天数的相关规定，以获取准确答案。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 5 | read_doc | {"doc_id": "D02"} | 假设D02可能为假期或人事相关制度，尝试读取获取年假规定。 | D02《员工费用报销操作指引》版本 2024-06-15，全文 P1,P2,P3,P4 | search_docs |
| 6 | search_docs | {"query": "年假", "top_k": 5} | 尝试用最直接关键词检索年假相关制度。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 7 | read_doc | {"doc_id": "D03"} | 假设D03为人事或假期相关制度，尝试读取获取年假规定。 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | read_doc |
| 8 | read_doc | {"doc_id": "D04"} | 确认是否有其他年假相关规定，避免遗漏或冲突。 | D04《请假审批流程》版本 2024-02-01，全文 P1,P2,P3,P4 | read_doc |
| 9 | read_doc | {"doc_id": "D05"} | 确认是否有其他年假或假期相关规定，确保答案准确。 | D05《差旅费用报销补充规定》版本 2024-09-01，全文 P1,P2,P3,P4 | finish |
| 10 | finish | {"status": "answered", "answer": "根据《年假管理制度》（2024-01-01版），员工累计工作已满1年不满10年的，年休假为5天。因此，工作满5年时，年假为5天。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天；已满10年不满20年的，年休假10天；已满20年的，年休假15天。"}], "gaps": []} | 已找到明确规定工作满5年对应的年假天数，无需进一步检索。 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：10
- answer：根据《年假管理制度》（2024-01-01版），员工累计工作已满1年不满10年的，年休假为5天。因此，工作满5年时，年假为5天。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天；已满10年不满20年的，年休假10天；已满20年的，年休假15天。」
- gaps：
  - （无）
