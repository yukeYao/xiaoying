# Trace：C02

**真实模型运行**：`gpt-4o-mini`

- question：我入职五年了，带薪休假一年能休多少天
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "带薪休假"} | 查询关于带薪休假的相关规定 | 命中 4 条：D03/P4(4.837)，D03/P1(4.788)，D03/P3(4.707)，D03/P2(3.494) | read_doc |
| 2 | read_doc | {"doc_id": "D03"} | 读取年假管理制度以获取详细信息 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | finish |
| 3 | finish | {"status": "answered", "answer": "根据《年假管理制度》，您入职满五年，年休假为5天。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天；"}], "gaps": [], "conflict_check": {"claims": [{"doc_id": "D03", "claim": "员工入职满五年，年休假为5天。", "scope_quote": "未说明"}], "relations": []}} |  | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：根据《年假管理制度》，您入职满五年，年休假为5天。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天；」
- gaps：
  - （无）
- conflict_check：
  - claim D03：员工入职满五年，年休假为5天。（适用范围：未说明）
