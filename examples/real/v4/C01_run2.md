# Trace：C01

**真实模型运行**：`gpt-4o-mini`

- question：工作满5年有几天年假？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假", "top_k": 5} | 查找关于年假的相关规定 | 命中 5 条：D03/P1(12.283)，D06/P2(5.495)，D03/P2(5.445)，D03/P4(4.837)，D03/P3(4.707) | read_doc |
| 2 | read_doc | {"doc_id": "D03"} | 读取年假管理制度以确认年假天数 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | finish |
| 3 | finish | {"status": "answered", "answer": "工作满5年的员工享有5天的年休假。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天；"}], "gaps": [], "conflict_check": {"claims": [{"doc_id": "D03", "claim": "工作满5年的员工享有5天的年休假。", "scope_quote": "未说明"}], "relations": []}} |  | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：工作满5年的员工享有5天的年休假。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天；」
- gaps：
  - （无）
- conflict_check：
  - claim D03：工作满5年的员工享有5天的年休假。（适用范围：未说明）
