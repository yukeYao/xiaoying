# Trace：C04

**真实模型运行**：`gpt-4o-mini`

- question：发票最晚多久内要交上去？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "发票 最晚 交上去"} | 需要查找关于发票提交时间的相关规定。 | 命中 5 条：D05/P2(7.89)，D01/P3(7.818)，D02/P2(7.312)，D01/P2(7.111)，D05/P3(4.962) | read_doc |
| 2 | read_doc | {"doc_id": "D02", "paragraph_ids": ["P2"]} | 需要确认员工费用报销的提交时间规定。 | D02《员工费用报销操作指引》版本 2024-06-15，段落 P2 | read_doc |
| 3 | read_doc | {"doc_id": "D01", "paragraph_ids": ["P2"]} | 需要确认财务报销管理办法中关于报销申请的提交时间。 | D01《财务报销管理办法》版本 2023-03-01，段落 P2 | ask_user |
| 4 | ask_user | {"question": "请问您是想了解一般费用报销的发票提交时间，还是差旅费用的报销时间？"} | 需要确认具体是哪个类型的费用报销，以便提供准确的信息。 | 非交互模式，提示模型调用 finish | finish |
| 5 | finish | {"status": "need_clarification", "answer": "请问您是想了解一般费用报销的发票提交时间，还是差旅费用的报销时间？", "citations": [], "gaps": []} | 需要确认具体是哪个类型的费用报销，以便提供准确的信息。 | 校验通过，结束 | 结束（need_clarification） |

## 结果

- status：`need_clarification`
- reason：`finish_called`
- steps_used：5
- answer：请问您是想了解一般费用报销的发票提交时间，还是差旅费用的报销时间？
- citations：
  - （无）
- gaps：
  - （无）
