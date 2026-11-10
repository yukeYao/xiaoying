# Trace：C06

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：笔记本电脑几年能换？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "笔记本电脑 更换 年限", "top_k": 5} | 检索设备更换年限 | 命中 4 条：D07/P3(5.673)，D06/P2(5.495)，D06/P1(2.418)，D07/P2(2.418) | read_doc |
| 2 | read_doc | {"doc_id": "D06"} | D06 与 D07 年限不同，读取 D06 | D06《办公设备申领规定（2022版）》版本 2022-05-01，全文 P1,P2,P3 | read_doc |
| 3 | read_doc | {"doc_id": "D07"} | 读取 D07 查看是否有替代说明 | D07《办公设备申领规定（2024版）》版本 2024-07-01，全文 P1,P2,P3,P4 | finish |
| 4 | finish | {"status": "answered", "answer": "笔记本电脑使用满3年可申请更换。依据 D07《办公设备申领规定（2024版）》（2024-07-01），该版写明 2022 版同时废止。", "gaps": [], "citations": [{"doc_id": "D07", "paragraph_id": "P3", "quote": "笔记本电脑使用满3年的，员工可申请更换"}, {"doc_id": "D07", "paragraph_id": "P1", "quote": "《办公设备申领规定（2022版）》同时废止"}], "conflict_check": {"claims": [{"doc_id": "D06", "claim": "使用满4年可申请更换", "scope_quote": "未说明"}, {"doc_id": "D07", "claim": "使用满3年可申请更换", "scope_quote": "未说明"}], "relations": [{"docs": ["D06", "D07"], "type": "superseded", "basis": {"doc_id": "D07", "paragraph_id": "P1", "quote": "《办公设备申领规定（2022版）》同时废止"}}]}} | D07 明确废止 D06，可回答 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：4
- answer：笔记本电脑使用满3年可申请更换。依据 D07《办公设备申领规定（2024版）》（2024-07-01），该版写明 2022 版同时废止。
- citations：
  - D07/P3：「笔记本电脑使用满3年的，员工可申请更换」
  - D07/P1：「《办公设备申领规定（2022版）》同时废止」
- gaps：
  - （无）
- conflict_check：
  - claim D06：使用满4年可申请更换（适用范围：未说明）
  - claim D07：使用满3年可申请更换（适用范围：未说明）
  - relation D06–D07：superseded，依据 D07/P1「《办公设备申领规定（2022版）》同时废止」
