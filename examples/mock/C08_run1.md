# Trace：C08

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：那超过3天呢？
- history：[{"role": "user", "content": "请假3天要谁审批？"}, {"role": "assistant", "content": "根据 D04《请假审批流程》（2024-02-01）：请假3天及以内的，由直属主管审批。"}]
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "请假 超过3天 审批", "top_k": 5} | 结合上文，用户问请假超过3天的审批 | 命中 5 条：D04/P3(11.715)，D04/P2(8.052)，D04/P4(5.811)，D04/P1(5.48)，D03/P4(4.612) | read_doc |
| 2 | read_doc | {"doc_id": "D04", "paragraph_ids": ["P3"]} | 读取 D04 第三段 | D04《请假审批流程》版本 2024-02-01，全文 P1,P2,P3,P4（请求 P3） | finish |
| 3 | finish | {"status": "answered", "answer": "请假超过3天的，由直属主管审批后，再报部门负责人和人力资源部审批。依据 D04《请假审批流程》（2024-02-01）。", "gaps": [], "citations": [{"doc_id": "D04", "paragraph_id": "P3", "quote": "请假超过3天的，由直属主管审批后，报部门负责人和人力资源部审批"}]} | 信息已足够，结束 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：请假超过3天的，由直属主管审批后，再报部门负责人和人力资源部审批。依据 D04《请假审批流程》（2024-02-01）。
- citations：
  - D04/P3：「请假超过3天的，由直属主管审批后，报部门负责人和人力资源部审批」
- gaps：
  - （无）
