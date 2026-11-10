# Trace：V05

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：出差回来多久内必须报销？
- data_dir：data/variant_b/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "出差 报销 期限", "top_k": 5} | 检索出差费用的报销期限 | 命中 5 条：D01/P3(6.361)，D05/P2(4.421)，D01/P2(3.469)，D05/P1(2.258)，D01/P1(2.127) | read_doc |
| 2 | read_doc | {"doc_id": "D05"} | 读取 D05 全文 | D05《费用报销补充规定》版本 2024-09-01，全文 P1,P2,P3 | read_doc |
| 3 | read_doc | {"doc_id": "D01"} | D01 规定的期限不同，读取查看适用范围 | D01《财务报销管理办法》版本 2023-03-01，全文 P1,P2,P3,P4,P5 | ask_user |
| 4 | ask_user | {"question": "D05 规定 10 天、D01 规定 20 天，请问适用哪份制度？"} | 两份都适用于全部费用，未找到优先级说明，请用户确认 | 非交互模式，提示模型调用 finish | finish |
| 5 | finish | {"status": "conflict_need_confirmation", "answer": "D05《费用报销补充规定》（2024-09-01）规定费用发生之日起10天内，D01《财务报销管理办法》（2023-03-01）规定费用发生之日起20天内，两份文档都适用于全部费用报销，且未写明优先级，请确认适用哪份制度。", "gaps": ["D05 与 D01 之间没有优先级说明"], "citations": [{"doc_id": "D05", "paragraph_id": "P2", "quote": "费用应在发生之日起10天内提交报销申请"}, {"doc_id": "D01", "paragraph_id": "P2", "quote": "员工应在费用发生之日起20天内提交报销申请"}], "conflict_check": {"claims": [{"doc_id": "D05", "claim": "费用发生之日起10天内提交", "scope_quote": "本规定适用于公司全部费用报销"}, {"doc_id": "D01", "claim": "费用发生之日起20天内提交", "scope_quote": "未说明"}], "relations": [{"docs": ["D01", "D05"], "type": "true_conflict", "basis": null}]}} | 信息已足够，结束 | 校验通过，结束 | 结束（conflict_need_confirmation） |

## 结果

- status：`conflict_need_confirmation`
- reason：`finish_called`
- steps_used：5
- answer：D05《费用报销补充规定》（2024-09-01）规定费用发生之日起10天内，D01《财务报销管理办法》（2023-03-01）规定费用发生之日起20天内，两份文档都适用于全部费用报销，且未写明优先级，请确认适用哪份制度。
- citations：
  - D05/P2：「费用应在发生之日起10天内提交报销申请」
  - D01/P2：「员工应在费用发生之日起20天内提交报销申请」
- gaps：
  - D05 与 D01 之间没有优先级说明
- conflict_check：
  - claim D05：费用发生之日起10天内提交（适用范围：本规定适用于公司全部费用报销）
  - claim D01：费用发生之日起20天内提交（适用范围：未说明）
  - relation D01–D05：true_conflict
