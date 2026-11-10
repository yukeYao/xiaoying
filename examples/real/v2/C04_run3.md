# Trace：C04

**真实模型运行**：`gpt-4o-mini`

- question：发票最晚多久内要交上去？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "发票 最晚 交上去"} | 需要查找关于发票提交时间的相关规定。 | 命中 5 条：D05/P2(7.89)，D01/P3(7.818)，D02/P2(7.312)，D01/P2(7.111)，D05/P3(4.962) | read_doc |
| 2 | read_doc | {"doc_id": "D05", "paragraph_ids": ["P2", "P3"]} | 需要确认差旅费用报销的提交期限。 | D05《差旅费用报销补充规定》版本 2024-09-01，全文 P1,P2,P3,P4（请求 P2,P3） | read_doc |
| 3 | read_doc | {"doc_id": "D01", "paragraph_ids": ["P2", "P3"]} | 需要确认财务报销管理办法中关于报销申请的提交期限。 | D01《财务报销管理办法》版本 2023-03-01，全文 P1,P2,P3,P4,P5（请求 P2,P3） | read_doc |
| 4 | read_doc | {"doc_id": "D02", "paragraph_ids": ["P2"]} | 需要确认员工费用报销操作指引中关于报销单提交的期限。 | D02《员工费用报销操作指引》版本 2024-06-15，全文 P1,P2,P3,P4（请求 P2） | ask_user |
| 5 | ask_user | {"question": "请问您是想了解一般费用报销的发票提交期限，还是差旅费用报销的发票提交期限？"} | 需要确认用户具体想了解的发票提交类型。 | 非交互模式，提示模型调用 finish | finish |
| 6 | finish | {"status": "need_clarification", "answer": "请问您是想了解一般费用报销的发票提交期限，还是差旅费用报销的发票提交期限？", "citations": [], "gaps": []} | 需要确认用户具体想了解的发票提交类型。 | 校验通过，结束 | 结束（need_clarification） |

## 结果

- status：`need_clarification`
- reason：`finish_called`
- steps_used：6
- answer：请问您是想了解一般费用报销的发票提交期限，还是差旅费用报销的发票提交期限？
- citations：
  - （无）
- gaps：
  - （无）
