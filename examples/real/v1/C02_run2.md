# Trace：C02

**真实模型运行**：`gpt-4o-mini`

- question：我入职五年了，带薪休假一年能休多少天
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "带薪休假"} | 需要查找关于带薪休假的相关规定。 | 命中 4 条：D03/P4(4.837)，D03/P1(4.788)，D03/P3(4.707)，D03/P2(3.494) | read_doc |
| 2 | read_doc | {"doc_id": "D03", "paragraph_ids": ["P1"]} | 确认带薪休假的具体天数规定。 | D03《年假管理制度》版本 2024-01-01，段落 P1 | finish |
| 3 | finish | {"status": "answered", "answer": "根据公司的年假管理制度，您入职满五年，年休假为5天。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天；"}], "gaps": []} | 根据年假管理制度确认带薪休假的天数。 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：根据公司的年假管理制度，您入职满五年，年休假为5天。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天；」
- gaps：
  - （无）
