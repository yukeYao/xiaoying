# Trace：V03

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：报销期限多久？
- data_dir：data/variant/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "报销期限", "top_k": 5} | 检索报销期限 | 命中 5 条：D01/P3(6.374)，D05/P2(4.177)，D01/P2(3.48)，D05/P1(2.216)，D01/P1(2.131) | read_doc |
| 2 | read_doc | {"doc_id": "D01"} | 只命中 D01，读取原文确认 | D01《财务报销管理办法》版本 2023-03-01，段落 P1,P2,P3,P4,P5 | finish |
| 3 | finish | {"status": "answered", "answer": "费用发生之日起20天内提交报销申请。依据 D01《财务报销管理办法》（2023-03-01）第二条。", "gaps": [], "citations": [{"doc_id": "D01", "paragraph_id": "P2", "quote": "员工应在费用发生之日起20天内提交报销申请"}]} | 信息已足够，结束 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：费用发生之日起20天内提交报销申请。依据 D01《财务报销管理办法》（2023-03-01）第二条。
- citations：
  - D01/P2：「员工应在费用发生之日起20天内提交报销申请」
- gaps：
  - （无）
