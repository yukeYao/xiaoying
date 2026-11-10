# Trace：C03

**真实模型运行**：`gpt-4o-mini`

- question：报销期限多久？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "报销期限", "top_k": 5} | 需要查找公司关于报销期限的相关规定。 | 命中 5 条：D02/P2(6.191)，D01/P3(5.499)，D05/P3(4.962)，D05/P2(3.708)，D01/P2(3.097) | read_doc |
| 2 | read_doc | {"doc_id": "D02", "paragraph_ids": ["P2"]} | 确认报销期限的具体规定。 | D02《员工费用报销操作指引》版本 2024-06-15，段落 P2 | read_doc |
| 3 | read_doc | {"doc_id": "D01", "paragraph_ids": ["P2"]} | 确认报销期限的具体规定。 | D01《财务报销管理办法》版本 2023-03-01，段落 P2 | read_doc |
| 4 | read_doc | {"doc_id": "D05", "paragraph_ids": ["P2"]} | 确认差旅费用报销的期限。 | D05《差旅费用报销补充规定》版本 2024-09-01，段落 P2 | ask_user |
| 5 | ask_user | {"question": "请问您需要了解的是一般报销的期限，还是差旅费用的报销期限？"} | 需要确认用户具体想了解的报销类型。 | 非交互模式，提示模型调用 finish | finish |
| 6 | finish | {"status": "need_clarification", "answer": "请问您需要了解的是一般报销的期限，还是差旅费用的报销期限？", "citations": [], "gaps": []} | 需要确认用户具体想了解的报销类型。 | 校验通过，结束 | 结束（need_clarification） |

## 结果

- status：`need_clarification`
- reason：`finish_called`
- steps_used：6
- answer：请问您需要了解的是一般报销的期限，还是差旅费用的报销期限？
- citations：
  - （无）
- gaps：
  - （无）
