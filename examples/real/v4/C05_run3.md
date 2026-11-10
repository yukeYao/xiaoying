# Trace：C05

**真实模型运行**：`gpt-4o-mini`

- question：出差回来多久内必须报销？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "出差 报销 期限", "top_k": 5} | 查找关于出差报销的相关规定。 | 命中 5 条：D05/P2(6.871)，D02/P2(6.191)，D01/P3(5.499)，D05/P1(5.289)，D05/P3(4.962) | read_doc |
| 2 | read_doc | {"doc_id": "D05"} | 读取差旅费用报销补充规定以确认报销期限。 | D05《差旅费用报销补充规定》版本 2024-09-01，全文 P1,P2,P3,P4 | finish |
| 3 | finish | {"status": "answered", "answer": "出差费用应在出差结束之日起10天内提交报销申请。", "citations": [{"doc_id": "D05", "paragraph_id": "P2", "quote": "差旅费用应在出差结束之日起10天内提交报销申请。"}], "gaps": [], "conflict_check": {"claims": [{"doc_id": "D05", "claim": "出差费用应在出差结束之日起10天内提交报销申请。", "scope_quote": "差旅费用报销"}], "relations": []}} |  | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：出差费用应在出差结束之日起10天内提交报销申请。
- citations：
  - D05/P2：「差旅费用应在出差结束之日起10天内提交报销申请。」
- gaps：
  - （无）
- conflict_check：
  - claim D05：出差费用应在出差结束之日起10天内提交报销申请。（适用范围：差旅费用报销）
