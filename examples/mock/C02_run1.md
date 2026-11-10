# Trace：C02

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：我入职五年了，带薪休假一年能休多少天
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "带薪休假 年假 天数 工龄", "top_k": 5} | 口语说法，检索年假制度 | 命中 4 条：D03/P4(4.837)，D03/P1(4.788)，D03/P3(4.707)，D03/P2(3.494) | read_doc |
| 2 | read_doc | {"doc_id": "D03", "paragraph_ids": ["P1"]} | 检索命中 D03 第一条，读取原文确认天数 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4（请求 P1） | finish |
| 3 | finish | {"status": "answered", "answer": "工作满5年（已满1年不满10年）年休假为5天。依据 D03《年假管理制度》（2024-01-01）第一条。", "gaps": [], "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天"}]} | 信息已足够，结束 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：3
- answer：工作满5年（已满1年不满10年）年休假为5天。依据 D03《年假管理制度》（2024-01-01）第一条。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天」
- gaps：
  - （无）
