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
| 5 | read_doc | {"doc_id": "D02"} | 假设D02为人事或假期相关制度，尝试直接读取以获取年假规定。 | D02《员工费用报销操作指引》版本 2024-06-15，全文 P1,P2,P3,P4 | search_docs |
| 6 | search_docs | {"query": "年假 司龄", "top_k": 5} | 尝试用不同关键词检索年假与司龄相关的规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 7 | read_doc | {"doc_id": "D03"} | 假设D03为假期或人事相关制度，尝试直接读取以获取年假规定。 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | read_doc |
| 8 | read_doc | {"doc_id": "D04"} | 为确保没有遗漏其他相关规定，读取另一份可能涉及年假的文档。 | D04《请假审批流程》版本 2024-02-01，全文 P1,P2,P3,P4 | read_doc |
| 9 | read_doc | {"doc_id": "D05"} | 进一步确认是否有其他文档对年假天数有补充或不同规定。 | D05《差旅费用报销补充规定》版本 2024-09-01，全文 P1,P2,P3,P4 | finish |
| 10 | finish | {"status": "answered", "answer": "根据《年假管理制度》（2024-01-01版），员工累计工作已满1年不满10年的，年休假为5天。因此，工作满5年时，年假为5天。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天"}], "gaps": [], "conflict_check": {"claims": [{"doc_id": "D03", "claim": "工作满5年年假为5天。", "scope_quote": "未说明"}, {"doc_id": "D04", "claim": "与问题无关", "scope_quote": "未说明"}, {"doc_id": "D05", "claim": "与问题无关", "scope_quote": "差旅费用报销"}], "relations": [{"docs": ["D03", "D04"], "type": "consistent", "basis": null}, {"docs": ["D03", "D05"], "type": "scope_split", "basis": {"doc_id": "D05", "paragraph_id": "P1", "quote": "本规定适用于员工因公出差产生的交通、住宿及出差补助等差旅费用的报销。"}}]}} | 已找到直接规定年假天数的原文，并核查无其他文档冲突。 | 错误 finish_rejected：conflict_check.claims 缺少本次读过的文档：D01, D02（读过的每份文档都要列出；与问题无关时 claim 填“与问题无关”） | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：10
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 10 仍未完成
